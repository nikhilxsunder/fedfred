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
from cachetools import FIFOCache, cached
from asyncache import cached as async_cached
from ._converters import _dict_type_converter, _dict_type_converter_async
from ._rate_limit import _rate_limiter, _rate_limiter_async
from ._endpoints import _resolve_endpoint, _resolve_endpoint_async
from ..exceptions.transport import (
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ConnectTimeoutError,
    NotFoundError,
    PoolTimeoutError,
    ProxyTransportError,
    RateLimitError,
    ReadTimeoutError,
    ResponseDecodingError,
    TooManyRedirectsError,
    TransportConnectionError,
    TransportError,
    TransportProtocolError,
    TransportReadError,
    TransportWriteError,
    TransportRequestError,
    WriteTimeoutError,
    UnsupportedProtocolError,
    HTTPClientError,
    HTTPServerError,
    HTTPResponseError,
)

__all__ = [
    "_get_request", "_cached_get_request_async",
    "_cached_get_request", "_get_request_async"
]

_CACHE: FIFOCache = FIFOCache(maxsize=256) # fix cache size resolution, refactor resolution logic to settings module.
"""Global cache instance for caching GET request responses."""

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

_HTTP_STATUS_MAP: Dict = {
    400: BadRequestError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    429: RateLimitError,
}

def _request_url(exc: httpx.HTTPError) -> Optional[str]:
    request = getattr(exc, "request", None)
    return None if request is None else str(request.url)


def _request_method(exc: httpx.HTTPError) -> Optional[str]:
    request = getattr(exc, "request", None)
    return None if request is None else request.method

def _safe_response_text(exc: httpx.HTTPStatusError) -> Optional[str]:
    try:
        return exc.response.text
    except Exception:
        return None

def _map_http_status_error(exc: httpx.HTTPStatusError) -> HTTPResponseError:
    status_code: int = exc.response.status_code
    url: Optional[str] = _request_url(exc)
    method: Optional[str] = _request_method(exc)
    response_text: Optional[str] = _safe_response_text(exc)

    exception_cls = _HTTP_STATUS_MAP.get(status_code)

    if exception_cls is None:
        if 400 <= status_code < 500:
            exception_cls = HTTPClientError
        elif 500 <= status_code < 600:
            exception_cls = HTTPServerError
        else:
            exception_cls = HTTPResponseError

    return exception_cls(
        f"HTTP error response received: {status_code}.",
        status_code=status_code,
        url=url,
        method=method,
        response_text=response_text,
    )

def _resolve_httpx_exception_class(
    exc: httpx.HTTPError,
) -> type[TransportError]:
    for cls in type(exc).__mro__:
        mapped = _HTTP_EXCEPTION_MAP.get(cls)
        if mapped is not None:
            return mapped
    return TransportError

def _map_httpx_exception(exc: httpx.HTTPError) -> TransportError:
    if isinstance(exc, httpx.HTTPStatusError):
        return _map_http_status_error(exc)

    exception_cls = _resolve_httpx_exception_class(exc)

    return exception_cls(
        str(exc),
        url=_request_url(exc),
        method=_request_method(exc),
    )

@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), retry=retry_if_exception_type(httpx.HTTPError),reraise=True,)
def _get_request(url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
    """Perform a GET request without caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        httpx.HTTPError: If the HTTP request fails.

    Notes:
        This method handles rate limiting and caching for synchronous GET requests to the FRED API.
    """

    _rate_limiter()

    spec = _resolve_endpoint(url_endpoint)

    params: Dict[str, Any] = {
        **spec.default_params,
        **(data or {}),
    }

    headers = dict(spec.default_headers or {})

    with httpx.Client() as client:
        try:
            response = client.get(spec.base_url + url_endpoint, params=params, headers=headers or None, timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise ValueError(f"HTTP Error occurred: {exc}") from exc

@cached(cache=_CACHE)
def _cached_get_request(url_endpoint: str, hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]=None) -> Dict[str, Any]:
    """Perform a GET request with caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]], optional): The hashable representation of the data. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        httpx.HTTPError: If the HTTP request fails.
    """

    return _get_request(url_endpoint, _dict_type_converter(hashable_data))

@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), retry=retry_if_exception_type(httpx.HTTPError), reraise=True)
async def _get_request_async(url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
    """Perform a GET request without caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        httpx.HTTPError: If the HTTP request fails.

    Notes:
        This method handles rate limiting and caching for synchronous GET requests to the FRED API.
    """

    await _rate_limiter_async()
    
    spec = await _resolve_endpoint_async(url_endpoint)

    params: Dict[str, Any] = {
        **spec.default_params,
        **(data or {}),
    }

    headers = dict(spec.default_headers or {})

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(spec.base_url + url_endpoint, params=params, headers=headers or None, timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise ValueError(f"HTTP Error occurred: {exc}") from exc

@async_cached(cache=_CACHE)
async def _cached_get_request_async(url_endpoint: str, hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]=None) -> Dict[str, Any]:
    """Perform a GET request with caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]], optional): The hashable representation of the data. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        httpx.HTTPError: If the HTTP request fails.
    """

    return await _get_request_async(url_endpoint, await _dict_type_converter_async(hashable_data))