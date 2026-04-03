# filepath: /src/fedfred/_core/_transport.py
#
# Copyright (c) 2025–2026 Nikhil Sunder
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""fedfred._core._transport

This module provides internal transport functions for the fedfred core package.
"""

from typing import  Optional, Dict, Union, Tuple, Any
import httpx
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type
from cachetools import cached
from asyncache import cached as async_cached
from ._converters import _dict_type_converter, _dict_type_converter_async
from ._rate_limit import _rate_limiter, _rate_limiter_async
from ._caching import _CACHE
from ._endpoints import _resolve_endpoint, _resolve_endpoint_async
from ..exceptions.transport import (
    TransportError,
    RequestPreparationError,
    TransportRequestError,
    TransportConnectionError,
    TransportTimeoutError,
    ConnectTimeoutError,
    ReadTimeoutError,
    WriteTimeoutError,
    PoolTimeoutError,
    TransportReadError,
    TransportWriteError,
    TransportProtocolError,
    ProxyTransportError,
    UnsupportedProtocolError,
    TooManyRedirectsError,
    ResponseDecodingError,
    TransportRetryError,
    HTTPResponseError,
    HTTPClientError,
    BadRequestError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    MethodNotAllowedError,
    ConflictError,
    GoneError,
    UnprocessableEntityError,
    RateLimitError,
    HTTPServerError,
    InternalServerError,
    BadGatewayError,
    ServiceUnavailableError,
    GatewayTimeoutError,
    UnexpectedHTTPStatusError
)

__all__ = [
    "_get_request", "_get_request_async",
    "_cached_get_request", "_cached_get_request_async"
]

_HTTP_EXCEPTION_MAP: Dict = {
    httpx.ConnectTimeout: ConnectTimeoutError,
    httpx.ReadTimeout: ReadTimeoutError,
    httpx.WriteTimeout: WriteTimeoutError,
    httpx.PoolTimeout: PoolTimeoutError,
    httpx.ConnectError: TransportConnectionError,
    httpx.ReadError: TransportReadError,
    httpx.WriteError: TransportWriteError,
    httpx.RemoteProtocolError: TransportProtocolError,
    httpx.LocalProtocolError: TransportProtocolError,
    httpx.ProxyError: ProxyTransportError,
    httpx.UnsupportedProtocol: UnsupportedProtocolError,
    httpx.TooManyRedirects: TooManyRedirectsError,
    httpx.DecodingError: ResponseDecodingError,
    httpx.RequestError: TransportRequestError,
}
"""Exception mapping from httpx exceptions to fedfred transport exceptions. Each key is an httpx exception class, and the corresponding value is the fedfred transport exception class to map to."""

_HTTP_STATUS_MAP: Dict = {
    400: BadRequestError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    405: MethodNotAllowedError,
    409: ConflictError,
    410: GoneError,
    422: UnprocessableEntityError,
    429: RateLimitError,
    500: InternalServerError,
    502: BadGatewayError,
    503: ServiceUnavailableError,
    504: GatewayTimeoutError,
}
"""Mapping of HTTP status codes to fedfred HTTP response exceptions. Each key is an HTTP status code, and the corresponding value is the fedfred exception class to map to."""

def _request_url(exception: httpx.HTTPError) -> Optional[str]:
    """Extract the request URL from an httpx exception, if available.
    
    Args:
        exception (httpx.HTTPError): The raised httpx exception.

    Returns:
        Optional[str]: The request URL if available, otherwise None.

    Notes:
        This function attempts to access the 'request' attribute of the exception and extract the URL. If the 'request' attribute is not present, or if the URL cannot be extracted, it returns None.
    """

    request = getattr(exception, "request", None)
    return None if request is None else str(request.url)

def _request_method(exception: httpx.HTTPError) -> Optional[str]:
    """Extract the request method from an httpx exception, if available.
    
    Args:
        exception (httpx.HTTPError): The raised httpx exception.

    Returns:
        Optional[str]: The request method if available, otherwise None.

    Notes:
        This function attempts to access the 'request' attribute of the exception and extract the HTTP method (e.g., GET, POST). If the 'request' attribute is not present, or if the
        method cannot be extracted, it returns None.
    """

    request = getattr(exception, "request", None)
    return None if request is None else request.method

def _safe_response_text(exception: httpx.HTTPStatusError) -> Optional[str]:
    """Safely extract decoded response text from an HTTP status error.

    Args:
        exception (httpx.HTTPStatusError): The raised HTTP status exception.

    Returns:
        Optional[str]: The decoded response text if available, otherwise None.

    Notes:
        This function attempts to access the 'response' attribute of the exception and extract the decoded text. If the 'response' attribute is not present, or if the text cannot be extracted, 
        it returns None.
    """

    try:
        return exception.response.text
    except (AttributeError, UnicodeDecodeError):
        return None

def _map_http_status_error(exception: httpx.HTTPStatusError) -> HTTPResponseError:
    """Map an ``httpx.HTTPStatusError`` to the appropriate fedfred HTTP exception.

    Args:
        exception (httpx.HTTPStatusError): The raised HTTP status exception.

    Returns:
        HTTPResponseError: The mapped fedfred HTTP exception instance.
    """

    status_code: int = exception.response.status_code
    url: Optional[str] = _request_url(exception)
    method: Optional[str] = _request_method(exception)
    response_text: Optional[str] = _safe_response_text(exception)

    exception_cls: type[HTTPResponseError]

    mapped = _HTTP_STATUS_MAP.get(status_code)
    if mapped is not None:
        exception_cls = mapped
    elif 400 <= status_code < 500:
        exception_cls = HTTPClientError
    elif 500 <= status_code < 600:
        exception_cls = HTTPServerError
    else:
        exception_cls = UnexpectedHTTPStatusError

    return exception_cls(
        f"HTTP error response received: {status_code}.",
        status_code=status_code,
        url=url,
        method=method,
        response_text=response_text,
    )

def _resolve_httpx_exception_class(exception: httpx.HTTPError) -> type[TransportError]:
    """Resolve the fedfred exception class corresponding to an ``httpx`` exception.

    Args:
        exception (httpx.HTTPError): The raised ``httpx`` exception.

    Returns:
        type[TransportError]: The fedfred exception class to instantiate.

    Notes:
        Resolution walks the exception MRO so that specific exception classes are preferred before broader parent classes.
    """

    for cls in type(exception).__mro__:
        mapped = _HTTP_EXCEPTION_MAP.get(cls)
        if mapped is not None:
            return mapped

    return TransportError

def _map_httpx_exception(exception: httpx.HTTPError) -> TransportError:
    """Map an ``httpx`` exception to the appropriate fedfred transport exception.

    Args:
        exception (httpx.HTTPError): The raised ``httpx`` exception.

    Returns:
        TransportError: The mapped fedfred exception instance.
    """

    if isinstance(exception, httpx.HTTPStatusError):
        return _map_http_status_error(exception)

    exception_cls = _resolve_httpx_exception_class(exception)

    return exception_cls(
        str(exception),
        url=_request_url(exception),
        method=_request_method(exception),
    )

@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), retry=retry_if_exception_type(TransportTimeoutError), reraise=False, retry_error_cls=TransportRetryError)
def _get_request(url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
    """Perform a GET request without caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        TransportError: If the request fails due to transport-level issues, including connection failures, timeouts, protocol errors, or unsuccessful HTTP responses.
        ResponseDecodingError: If the response body cannot be decoded as valid JSON.
        RequestPreparationError: If there is an error preparing the request, such as resolving the endpoint specification.
        TransportRetryError: If the request fails after retrying the specified number of times due to transport timeouts.
    """

    _rate_limiter()

    try:
        spec = _resolve_endpoint(url_endpoint)
    except Exception as exc:
        raise RequestPreparationError(
            f"Failed to resolve endpoint: {url_endpoint}",
            url=None,
            method="GET",
        ) from exc

    params: Dict[str, Any] = {
        **spec.default_params,
        **(data or {}),
    }

    headers = dict(spec.default_headers or {})
    request_url = spec.base_url + url_endpoint

    with httpx.Client() as client:
        try:
            response = client.get(request_url, params=params, headers=headers or None, timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise _map_httpx_exception(exc) from exc
        except ValueError as exc:
            raise ResponseDecodingError(
                "Response body could not be decoded as valid JSON.",
                url=request_url,
                method="GET",
            ) from exc

@cached(cache=_CACHE)
def _cached_get_request(url_endpoint: str, hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]=None) -> Dict[str, Any]:
    """Perform a GET request with caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]], optional): The hashable representation of the data. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        TransportError: If the request fails due to transport-level issues, including connection failures, timeouts, protocol errors, or unsuccessful HTTP responses.
        ResponseDecodingError: If the response body cannot be decoded as valid JSON.
        RequestPreparationError: If there is an error preparing the request, such as resolving the endpoint specification.
        TransportRetryError: If the request fails after retrying the specified number of times due to transport timeouts.
    """

    return _get_request(url_endpoint, _dict_type_converter(hashable_data))

@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), retry=retry_if_exception_type(TransportTimeoutError), reraise=False, retry_error_cls=TransportRetryError)
async def _get_request_async(url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
    """Perform a GET request without caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        TransportError: If the request fails due to transport-level issues, including connection failures, timeouts, protocol errors, or unsuccessful HTTP responses.
        ResponseDecodingError: If the response body cannot be decoded as valid JSON.
        RequestPreparationError: If there is an error preparing the request, such as resolving the endpoint specification.
        TransportRetryError: If the request fails after retrying the specified number of times due to transport timeouts.
    """

    await _rate_limiter_async()

    try:
        spec = await _resolve_endpoint_async(url_endpoint)
    except Exception as exc:
        raise RequestPreparationError(
            f"Failed to resolve endpoint: {url_endpoint}",
            url=None,
            method="GET",
        ) from exc

    params: Dict[str, Any] = {
        **spec.default_params,
        **(data or {}),
    }

    headers = dict(spec.default_headers or {})
    request_url = spec.base_url + url_endpoint

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(request_url, params=params, headers=headers or None, timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise _map_httpx_exception(exc) from exc
        except ValueError as exc:
            raise ResponseDecodingError(
                "Response body could not be decoded as valid JSON.",
                url=request_url,
                method="GET",
            ) from exc

@async_cached(cache=_CACHE)
async def _cached_get_request_async(url_endpoint: str, hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]=None) -> Dict[str, Any]:
    """Perform a GET request with caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]], optional): The hashable representation of the data. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        TransportError: If the request fails due to transport-level issues, including connection failures, timeouts, protocol errors, or unsuccessful HTTP responses.
        ResponseDecodingError: If the response body cannot be decoded as valid JSON.
        RequestPreparationError: If there is an error preparing the request, such as resolving the endpoint specification.
        TransportRetryError: If the request fails after retrying the specified number of times due to transport timeouts.
    """

    return await _get_request_async(url_endpoint, await _dict_type_converter_async(hashable_data))
