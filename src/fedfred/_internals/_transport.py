# filepath: /src/fedfred/_internals/_transport.py
#
# Copyright (c) 2026 Nikhil Sunder
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
"""HTTP transport layer for the fedfred internals package.

This module owns the network boundary: it maintains a pooled synchronous client and a
per-event-loop asynchronous client, paces requests through the rate limiter, decodes
JSON with orjson, and translates every ``httpx`` failure into the corresponding fedfred
exception via :data:`_HTTP_EXCEPTION_MAP` and :data:`_HTTP_STATUS_MAP`. It exposes
cached and uncached GET/POST entry points in both synchronous and asynchronous
flavours. Cache entries are keyed on resolved request identity (see
:func:`_request_cache_key`) so byte-identical wire requests are shared across services
and client instances.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import httpx
import orjson
from asyncache import cached as async_cached
from cachetools import cached
from cachetools.keys import hashkey
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from .._core import (
    CacheKey,
    CacheParameters,
    EndpointSpec,
    Service,
    _dict_type_converter,
    _resolve_endpoint,
    _resolve_preparation_function,
)
from ..exceptions import (
    AuthenticationError,
    AuthorizationError,
    BadGatewayError,
    BadRequestError,
    ConflictError,
    ConnectTimeoutError,
    GatewayTimeoutError,
    GoneError,
    HTTPClientError,
    HTTPResponseError,
    HTTPServerError,
    InternalServerError,
    MethodNotAllowedError,
    NotFoundError,
    PoolTimeoutError,
    ProxyTransportError,
    RateLimitError,
    ReadTimeoutError,
    RequestPreparationError,
    ResponseDecodingError,
    ServiceUnavailableError,
    TooManyRedirectsError,
    TransportConnectionError,
    TransportError,
    TransportProtocolError,
    TransportReadError,
    TransportRequestError,
    TransportRetryError,
    TransportTimeoutError,
    TransportWriteError,
    UnexpectedHTTPStatusError,
    UnprocessableEntityError,
    UnsupportedProtocolError,
    WriteTimeoutError,
)
from ._caching import _CACHE
from ._rate_limit import _rate_limiter, _rate_limiter_async

_HTTP_CLIENT: httpx.Client = httpx.Client(
    timeout=httpx.Timeout(10.0),
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20,
        keepalive_expiry=60.0,
    ),
)
"""Process-global pooled synchronous client, closed at interpreter exit via :func:`atexit`."""

_ASYNC_CLIENT_STATE: tuple[asyncio.AbstractEventLoop, httpx.AsyncClient] | None = None
"""Cached ``(event_loop, async_client)`` pair, or ``None`` before first use. See
:func:`_get_async_client`."""


def _get_async_client() -> httpx.AsyncClient:
    """Return the shared async client bound to the running event loop.

    Returns:
        httpx.AsyncClient: A pooled client owned by the current event loop.

    Raises:
        RuntimeError: If called outside a running event loop.

    Notes:
        httpx connections are bound to the loop that created them, so the client
        is cached per loop: the same loop reuses one pooled client across all
        clients and calls; a different loop evicts the cached state and creates a
        fresh client. The previously cached client is dropped without being
        closed here, so callers needing deterministic cleanup should use
        :func:`_aclose_async_client`.
    """
    global _ASYNC_CLIENT_STATE

    loop = asyncio.get_running_loop()

    state = _ASYNC_CLIENT_STATE  # single atomic read

    if state is not None:
        state_loop, client = state

        if state_loop is loop and not client.is_closed:
            return client

    client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0),
        limits=httpx.Limits(
            max_connections=100, max_keepalive_connections=20, keepalive_expiry=60.0
        ),
    )

    _ASYNC_CLIENT_STATE = (loop, client)  # single atomic store

    return client


async def _aclose_async_client() -> None:
    """Close the running loop's shared async client and clear the cached state.

    Notes:
        Intended as a test-teardown hook so pooled connections do not leak
        between event loops created during testing. Closing is idempotent: the
        cached state is cleared first, and an already-closed client is skipped.
    """
    global _ASYNC_CLIENT_STATE

    state = _ASYNC_CLIENT_STATE

    _ASYNC_CLIENT_STATE = None

    if state is not None and not state[1].is_closed:
        await state[1].aclose()


_HTTP_EXCEPTION_MAP: dict[type[httpx.HTTPError], type[TransportError]] = {
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
"""Maps httpx request-error classes to fedfred transport exceptions. Resolved most-specific-first
via the exception MRO; see :func:`_resolve_httpx_exception_class`."""

_HTTP_STATUS_MAP: dict[int, type[HTTPResponseError]] = {
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
"""Maps HTTP status codes to fedfred HTTP response exceptions. Unmapped codes fall back to the
4xx/5xx family class; see :func:`_map_http_status_error`."""


def _request_url(exception: httpx.HTTPError) -> str | None:
    """Extract the request URL from an httpx exception, if available.

    Args:
        exception (httpx.HTTPError): The raised httpx exception.

    Returns:
        str | None: The request URL, or ``None`` if the exception carries no request.

    Examples:
        >>> import httpx
        >>> from fedfred._internals._transport import _request_url
        >>> try:
        ...     httpx.get("https://api.stlouisfed.org/missing").raise_for_status()
        ... except httpx.HTTPError as exc:
        ...     print(_request_url(exc))
        https://api.stlouisfed.org/missing

    Notes:
        Reads the exception's ``request`` attribute defensively; returns ``None``
        when it is absent (e.g. for errors raised before the request was built).
    """
    request = getattr(exception, "request", None)

    return None if request is None else str(request.url)


def _request_method(exception: httpx.HTTPError) -> str | None:
    """Extract the HTTP request method from an httpx exception, if available.

    Args:
        exception (httpx.HTTPError): The raised httpx exception.

    Returns:
        str | None: The request method (e.g. ``"GET"``), or ``None`` if unavailable.

    Examples:
        >>> import httpx
        >>> from fedfred._internals._transport import _request_method
        >>> try:
        ...     httpx.get("https://api.stlouisfed.org/missing").raise_for_status()
        ... except httpx.HTTPError as exc:
        ...     print(_request_method(exc))
        GET

    Notes:
        Reads the exception's ``request`` attribute defensively; returns ``None``
        when it is absent.
    """
    request = getattr(exception, "request", None)

    return None if request is None else request.method


def _safe_response_text(exception: httpx.HTTPStatusError) -> str | None:
    """Safely extract the decoded response body from an HTTP status error.

    Args:
        exception (httpx.HTTPStatusError): The raised HTTP status exception.

    Returns:
        str | None: The decoded response text, or ``None`` if it is missing or undecodable.

    Examples:
        >>> import httpx
        >>> from fedfred._internals._transport import _safe_response_text
        >>> try:
        ...     httpx.get("https://api.stlouisfed.org/missing").raise_for_status()
        ... except httpx.HTTPStatusError as exc:
        ...     print(_safe_response_text(exc))
        Not Found

    Notes:
        Swallows ``AttributeError`` (no response attached) and
        ``UnicodeDecodeError`` (undecodable body), returning ``None`` in both cases.
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
        HTTPResponseError: A fedfred exception carrying the status code, URL, method, and response
            text.

    Examples:
        >>> import httpx
        >>> from fedfred._internals._transport import _map_http_status_error
        >>> try:
        ...     httpx.get("https://api.stlouisfed.org/missing").raise_for_status()
        ... except httpx.HTTPStatusError as exc:
        ...     print(type(_map_http_status_error(exc)))
        <class 'fedfred.exceptions.NotFoundError'>

    Notes:
        Uses :data:`_HTTP_STATUS_MAP` for known codes, falling back to
        :class:`HTTPClientError` (4xx), :class:`HTTPServerError` (5xx), or
        :class:`UnexpectedHTTPStatusError` for anything else.
    """
    status_code: int = exception.response.status_code

    url: str | None = _request_url(exception)

    method: str | None = _request_method(exception)

    response_text: str | None = _safe_response_text(exception)

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
    """Resolve the fedfred transport exception class for a (non-status) httpx error.

    Args:
        exception (httpx.HTTPError): The raised httpx exception.

    Returns:
        type[TransportError]: The fedfred exception class to instantiate, or :class:`TransportError`
            if unmapped.

    Examples:
        >>> import httpx
        >>> from fedfred._internals._transport import _resolve_httpx_exception_class
        >>> try:
        ...     httpx.get("https://api.stlouisfed.org/slow", timeout=0.001)
        ... except httpx.HTTPError as exc:
        ...     print(_resolve_httpx_exception_class(exc))
        <class 'fedfred.exceptions.ConnectTimeoutError'>

    Notes:
        Walks the exception's MRO so a specific class (e.g. ``ConnectTimeout``) is
        matched before a broader parent (e.g. ``RequestError``).
    """
    for cls in type(exception).__mro__:
        mapped = _HTTP_EXCEPTION_MAP.get(cls)

        if mapped is not None:
            return mapped

    return TransportError


def _map_httpx_exception(exception: httpx.HTTPError) -> TransportError:
    """Map any ``httpx`` exception to the appropriate fedfred transport exception.

    Args:
        exception (httpx.HTTPError): The raised httpx exception.

    Returns:
        TransportError: The mapped fedfred exception instance.

    Examples:
        >>> import httpx
        >>> from fedfred._internals._transport import _map_httpx_exception
        >>> try:
        ...     httpx.get("https://api.stlouisfed.org/slow", timeout=0.001)
        ... except httpx.HTTPError as exc:
        ...     print(type(_map_httpx_exception(exc)))
        <class 'fedfred.exceptions.ConnectTimeoutError'>

    Notes:
        Status errors are routed to :func:`_map_http_status_error`; all other
        request errors are resolved via :func:`_resolve_httpx_exception_class`.
    """
    if isinstance(exception, httpx.HTTPStatusError):
        return _map_http_status_error(exception)

    exception_cls = _resolve_httpx_exception_class(exception)

    return exception_cls(
        str(exception),
        url=_request_url(exception),
        method=_request_method(exception),
    )


def _request_cache_key(
    service_name: Service,
    endpoint_name: str,
    hashable_data: CacheKey | None = None,
    path_injection: str | None = None,
) -> tuple:
    """Build a cache key from resolved request identity rather than caller identity.

    Args:
        service_name (Service): The service used to resolve the endpoint.
        endpoint_name (str): The endpoint to resolve.
        hashable_data (CacheKey | None, optional): Canonical,
            hashable request parameters. Defaults to None.
        path_injection (str | None, optional): A value substituted into the URL path; included in
            the key so path variants are cached separately. Defaults to None.

    Returns:
        tuple: A ``cachetools`` hash key over the resolved URL, parameters, and path injection.

    Raises:
        RequestPreparationError: If the endpoint cannot be resolved. Note this is
            raised during key computation, i.e. before the cached function body runs.

    Notes:
        Keys on ``(resolved URL, canonical params, path injection)`` so
        byte-identical wire requests share a single cache entry regardless of the
        issuing client — FRED and ALFRED resolve shared endpoints to the same URL.
        ``service_name`` is deliberately excluded from the key. Used as the ``key``
        argument to the ``@cached`` / ``@async_cached`` decorators, so its
        positional signature mirrors that of the wrapped request functions.
    """
    try:
        spec = _resolve_endpoint(
            service_name, endpoint_name
        )  # -> (service_name, endpoint_name) once service-first lands
    except Exception as exc:
        raise RequestPreparationError(
            f"Failed to resolve endpoint: {endpoint_name}",
            url=None,
            method="GET",
        ) from exc
    return hashkey(spec.url, hashable_data, path_injection)


_with_retry = retry(
    wait=wait_fixed(1),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(TransportTimeoutError),
    reraise=False,
    retry_error_cls=TransportRetryError,
)
"""Shared tenacity retry policy for the request entry points.

Retries up to three times, one second apart, on :class:`TransportTimeoutError`,
re-raising the final failure as :class:`TransportRetryError`. Applied as a decorator to
the GET/POST request functions.
"""


@contextmanager
def _translating_httpx(url: str, method: str) -> Iterator[None]:
    """Translate httpx and JSON-decode failures inside the block into fedfred errors.

    Wraps the whole HTTP interaction — send, ``raise_for_status``, and decode — so a
    connection or timeout error from the *send* is translated too, not just status or
    decode errors. A synchronous context manager that never awaits, so it is used with a
    plain ``with`` in both the sync and async request helpers.

    Args:
        url (str): The request URL, attached to a decoding error for context.
        method (str): The HTTP method, attached to a decoding error for context.

    Yields:
        None: Control to the guarded HTTP operation.

    Raises:
        TransportError: For any ``httpx`` failure, mapped via :func:`_map_httpx_exception`.
        ResponseDecodingError: If the response body is not valid JSON.
    """
    try:
        yield

    except httpx.HTTPError as exc:
        raise _map_httpx_exception(exc) from exc

    except ValueError as exc:
        raise ResponseDecodingError(
            "Response body could not be decoded as valid JSON.",
            url=url,
            method=method,
        ) from exc


def _request_sync(
    spec: EndpointSpec,
    url: str,
    method: str,
    params: dict[str, Any] | None = None,
    content: bytes | None = None,
) -> dict[str, Any]:
    """Send one synchronous HTTP request and return the decoded JSON.

    The shared send-and-finish path for the sync GET/POST entry points: issues the
    request on the process-global pooled client, raises for status, decodes with orjson,
    and translates any failure via :func:`_translating_httpx`. Pass ``params`` for GET
    and ``content`` for POST; leave the other ``None``.

    Args:
        spec (EndpointSpec): The resolved endpoint spec (supplies the headers).
        url (str): The fully-formed request URL.
        method (str): The HTTP method (``"GET"`` / ``"POST"``).
        params (dict[str, Any] | None): Query parameters, for GET requests.
        content (bytes | None): The serialized request body, for POST requests.

    Returns:
        dict[str, Any]: The decoded JSON response.

    Raises:
        TransportError: For transport-level failures (connection, protocol, HTTP status).
        ResponseDecodingError: If the response body is not valid JSON.
    """
    with _translating_httpx(url, method):
        response = _HTTP_CLIENT.request(
            method,
            url,
            params=params,
            content=content,
            headers=spec.headers or None,
            timeout=10,
        )

        response.raise_for_status()

        return orjson.loads(response.content)


async def _request_async(
    spec: EndpointSpec,
    url: str,
    method: str,
    params: dict[str, Any] | None = None,
    content: bytes | None = None,
) -> dict[str, Any]:
    """Send one asynchronous HTTP request and return the decoded JSON.

    The async analogue of :func:`_request_sync`: issues the request on the per-loop
    client from :func:`_get_async_client`, raises for status, decodes with orjson, and
    translates failures via :func:`_translating_httpx`. Pass ``params`` for GET and
    ``content`` for POST; leave the other ``None``.

    Args:
        spec (EndpointSpec): The resolved endpoint spec (supplies the headers).
        url (str): The fully-formed request URL.
        method (str): The HTTP method (``"GET"`` / ``"POST"``).
        params (dict[str, Any] | None): Query parameters, for GET requests.
        content (bytes | None): The serialized request body, for POST requests.

    Returns:
        dict[str, Any]: The decoded JSON response.

    Raises:
        TransportError: For transport-level failures (connection, protocol, HTTP status).
        ResponseDecodingError: If the response body is not valid JSON.
    """
    client = _get_async_client()

    with _translating_httpx(url, method):
        response = await client.request(
            method,
            url,
            params=params,
            content=content,
            headers=spec.headers or None,
            timeout=10,
        )

        response.raise_for_status()

        return orjson.loads(response.content)


@_with_retry
def _get_request(
    service_name: Service,
    endpoint_name: str,
    data: CacheParameters | None = None,
    path_injection: str | None = None,
) -> dict[str, Any]:
    """Perform a synchronous GET request without caching.

    Args:
        service_name (Service): The service to query.
        endpoint_name (str): The endpoint to query.
        data (CacheParameters | None, optional): Query parameters. Defaults to None.
        path_injection (str | None, optional): A value to substitute into the URL path when the
            endpoint spec includes a placeholder. Defaults to None.

    Returns:
        dict[str, Any]: The decoded JSON response.

    Raises:
        RequestPreparationError: If the endpoint specification cannot be resolved.
        TransportError: For transport-level failures, including connection errors, protocol errors,
            and unsuccessful HTTP responses.
        TransportRetryError: If the request still times out after the configured retries.
        ResponseDecodingError: If the response body is not valid JSON.
        LimiterServiceError: If the service is unknown to the rate limiter.
        LimiterLimitError: If the rate limiter is misconfigured.
        LimiterLoopError: If rate limiting requires a running event loop that is absent.

    Examples:
        >>> from fedfred._internals._transport import _get_request
        >>> _get_request("fred", "series_observations", {"series_id": "GNPCA"})
        {...}

    Notes:
        Retries up to three times on :class:`TransportTimeoutError`, then raises
        :class:`TransportRetryError`. Uses the process-global pooled client.
    """
    spec = _resolve_endpoint(service_name, endpoint_name)

    params = {**(spec.params or {}), **(_resolve_preparation_function(data, spec.service) or {})}

    url = spec.url.format(path_injection) if path_injection else spec.url

    _rate_limiter(service_name)

    return _request_sync(spec, url, "GET", params=params)


@cached(cache=_CACHE, key=_request_cache_key)
def _cached_get_request(
    service_name: Service,
    url_endpoint: str,
    hashable_data: CacheKey | None = None,
    path_injection: str | None = None,
) -> dict[str, Any]:
    """Perform a synchronous GET request, caching the result.

    Args:
        service_name (Service): The service to query.
        url_endpoint (str): The endpoint to query.
        hashable_data (tuple[tuple[str, str | int | None], ...] | None, optional): A hashable
            representation of the query parameters, used for caching. Defaults to None.
        path_injection (str | None, optional): A value to substitute into the URL path when the
            endpoint spec includes a placeholder. Defaults to None.

    Returns:
        dict[str, Any]: The decoded JSON response (possibly served from cache).

    Raises:
        RequestPreparationError: If the endpoint specification cannot be resolved (including during
            cache-key computation).
        TransportError: For transport-level failures, including connection errors, protocol errors,
            and unsuccessful HTTP responses.
        TransportRetryError: If the request still times out after the configured retries.
        ResponseDecodingError: If the response body is not valid JSON.
        LimiterServiceError: If the service is unknown to the rate limiter.
        LimiterLimitError: If the rate limiter is misconfigured.
        LimiterLoopError: If rate limiting requires a running event loop that is absent.

    Examples:
        >>> from fedfred._internals._transport import _cached_get_request
        >>> _cached_get_request(
        ...     "fred",
        ...     "series_observations",
        ...     (("series_id", "GNPCA"), ("realtime_start", "2020-01-01")),
        ... )
        {...}

    Notes:
        Cache keys are computed by :func:`_request_cache_key` on resolved request
        identity, so equivalent requests issued through different services share a
        cache entry. Wraps :func:`_get_request`; ``hashable_data`` is converted
        back to a dict before the underlying call.
    """
    return _get_request(
        service_name, url_endpoint, _dict_type_converter(hashable_data), path_injection
    )


@_with_retry
async def _get_request_async(
    service_name: Service,
    endpoint_name: str,
    data: CacheParameters | None = None,
    path_injection: str | None = None,
) -> dict[str, Any]:
    """Perform an asynchronous GET request without caching.

    Args:
        service_name (Service): The service to query.
        endpoint_name (str): The endpoint to query.
        data (CacheParameters | None, optional): Query parameters. Defaults to None.
        path_injection (str | None, optional): A value to substitute into the URL path when the
            endpoint spec includes a placeholder. Defaults to None.

    Returns:
        dict[str, Any]: The decoded JSON response.

    Raises:
        RequestPreparationError: If the endpoint specification cannot be resolved.
        TransportError: For transport-level failures, including connection errors, protocol errors,
            and unsuccessful HTTP responses.
        TransportRetryError: If the request still times out after the configured retries.
        ResponseDecodingError: If the response body is not valid JSON.
        LimiterServiceError: If the service is unknown to the rate limiter.
        LimiterLimitError: If the rate limiter or its semaphore is misconfigured.
        RateLimiterConfigurationError: If the per-minute limit is less than 1.
        RateLimiterStateError: If the rate limiter's internal state is inconsistent.
        LimiterLoopError: If rate limiting cannot acquire its lock for lack of a running event loop.

    Examples:
        >>> from fedfred._internals._transport import _get_request_async
        >>> await _get_request_async("fred", "series_observations", {"series_id": "GNPCA"})
        {...}

    Notes:
        Uses the per-loop client from :func:`_get_async_client`. Retries up to
        three times on :class:`TransportTimeoutError`, then raises
        :class:`TransportRetryError`.
    """
    spec = _resolve_endpoint(service_name, endpoint_name)

    params = {**(spec.params or {}), **(_resolve_preparation_function(data, spec.service) or {})}

    url = spec.url.format(path_injection) if path_injection else spec.url

    await _rate_limiter_async(service_name)

    return await _request_async(spec, url, "GET", params=params)


@async_cached(cache=_CACHE, key=_request_cache_key)
async def _cached_get_request_async(
    service_name: Service,
    url_endpoint: str,
    hashable_data: CacheKey | None = None,
    path_injection: str | None = None,
) -> dict[str, Any]:
    """Perform an asynchronous GET request, caching the result.

    Args:
        service_name (Service): The service to query.
        url_endpoint (str): The endpoint to query.
        hashable_data (tuple[tuple[str, str | int | None], ...] | None, optional): A hashable
            representation of the query parameters, used for caching. Defaults to None.
        path_injection (str | None, optional): A value to substitute into the URL path when the
            endpoint spec includes a placeholder. Defaults to None.

    Returns:
        dict[str, Any]: The decoded JSON response (possibly served from cache).

    Raises:
        RequestPreparationError: If the endpoint specification cannot be resolved (including during
            cache-key computation).
        TransportError: For transport-level failures, including connection errors, protocol errors,
            and unsuccessful HTTP responses.
        TransportRetryError: If the request still times out after the configured retries.
        ResponseDecodingError: If the response body is not valid JSON.
        LimiterServiceError: If the service is unknown to the rate limiter.
        LimiterLimitError: If the rate limiter or its semaphore is misconfigured.
        RateLimiterConfigurationError: If the per-minute limit is less than 1.
        RateLimiterStateError: If the rate limiter's internal state is inconsistent.
        LimiterLoopError: If rate limiting cannot acquire its lock for lack of a running event loop.

    Examples:
        >>> from fedfred._internals._transport import _cached_get_request_async
        >>> await _cached_get_request_async(
        ...     "fred",
        ...     "series_observations",
        ...     (("series_id", "GNPCA"), ("realtime_start", "2020-01-01")),
        ... )
        {...}

    Notes:
        Cache keys are computed by :func:`_request_cache_key`. Wraps
        :func:`_get_request_async` with an async-aware cache; ``hashable_data`` is
        converted back to a dict before the underlying call.
    """
    return await _get_request_async(
        service_name, url_endpoint, _dict_type_converter(hashable_data), path_injection
    )


@_with_retry
def _post_request(
    service_name: Service, endpoint_name: str, data: CacheParameters | None = None
) -> dict[str, Any]:
    """Perform a synchronous POST request without caching.

    Args:
        service_name (Service): The service to query.
        endpoint_name (str): The endpoint to query.
        data (CacheParameters | None, optional): The JSON payload, merged over the
            endpoint spec's default payload. Defaults to None.

    Returns:
        dict[str, Any]: The decoded JSON response.

    Raises:
        RequestPreparationError: If the endpoint specification cannot be resolved.
        TransportError: For transport-level failures, including connection errors, protocol errors,
            and unsuccessful HTTP responses.
        TransportRetryError: If the request still times out after the configured retries.
        ResponseDecodingError: If the response body is not valid JSON.
        LimiterServiceError: If the service is unknown to the rate limiter.
        LimiterLimitError: If the rate limiter is misconfigured.
        LimiterLoopError: If rate limiting requires a running event loop that is absent.

    Examples:
        >>> from fedfred._internals._transport import _post_request
        >>> _post_request("fred", "some_endpoint", {"param": "value"})
        {...}

    Notes:
        The payload is serialized with orjson and sent as the request body; the
        endpoint spec's headers must set ``Content-Type: application/json``.
    """
    spec = spec = _resolve_endpoint(service_name, endpoint_name)

    _rate_limiter(service_name)

    payload = {**(spec.payload or {}), **(data or {})}

    return _request_sync(spec, spec.url, "POST", content=orjson.dumps(payload))


@_with_retry
async def _post_request_async(
    service_name: Service, endpoint_name: str, data: CacheParameters | None = None
) -> dict[str, Any]:
    """Perform an asynchronous POST request without caching.

    Args:
        service_name (Service): The service to query.
        endpoint_name (str): The endpoint to query.
        data (CacheParameters | None, optional): The JSON payload, merged over the
            endpoint spec's default payload. Defaults to None.

    Returns:
        dict[str, Any]: The decoded JSON response.

    Raises:
        RequestPreparationError: If the endpoint specification cannot be resolved.
        TransportError: For transport-level failures, including connection errors, protocol errors,
            and unsuccessful HTTP responses.
        TransportRetryError: If the request still times out after the configured retries.
        ResponseDecodingError: If the response body is not valid JSON.
        LimiterServiceError: If the service is unknown to the rate limiter.
        LimiterLimitError: If the rate limiter or its semaphore is misconfigured.
        RateLimiterConfigurationError: If the per-minute limit is less than 1.
        RateLimiterStateError: If the rate limiter's internal state is inconsistent.
        LimiterLoopError: If rate limiting requires a running event loop that is absent.

    Examples:
        >>> from fedfred._internals._transport import _post_request_async
        >>> await _post_request_async("fred", "some_endpoint", {"param": "value"})
        {...}

    Notes:
        The payload is serialized with orjson and sent as the request body; the
        endpoint spec's headers must set ``Content-Type: application/json``. Uses
        the per-loop client from :func:`_get_async_client`.
    """
    spec = _resolve_endpoint(service_name, endpoint_name)

    await _rate_limiter_async(service_name)

    payload = {**(spec.payload or {}), **(data or {})}

    return await _request_async(spec, spec.url, "POST", content=orjson.dumps(payload))
