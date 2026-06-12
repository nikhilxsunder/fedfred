# filepath: /src/fedfred/exceptions/internals/transport.py
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
"""Transport-layer exceptions for the fedfred internals package.

The error hierarchy for :mod:`fedfred._internals._transport`. Everything carries the
request ``url`` and ``method`` via the base :class:`TransportError`. Two families sit
under it: request-execution failures (:class:`TransportRequestError` — connection,
timeout, protocol, decoding) raised before a valid HTTP response is processed, and
HTTP response failures (:class:`HTTPResponseError` — 4xx/5xx, adding ``status_code``
and ``response_text``). :class:`RequestPreparationError` covers failures building the
request.

:class:`TransportRetryError` is the deliberate exception: it subclasses tenacity's
:class:`~tenacity.RetryError`, not :class:`TransportError`, because it is the retry
decorator's ``retry_error_cls`` and is constructed by tenacity.

Classes:
    TransportError: Base for any transport failure (carries url, method).
    RequestPreparationError: A request could not be constructed.
    TransportRequestError: Base for request-execution failures.
    TransportConnectionError: A connection could not be established.
    TransportTimeoutError: Base for request timeouts.
    ConnectTimeoutError / ReadTimeoutError / WriteTimeoutError / PoolTimeoutError: Specific
        timeouts.
    TransportReadError / TransportWriteError: Read/write failures.
    TransportProtocolError / ProxyTransportError / UnsupportedProtocolError / TooManyRedirectsError.
    ResponseDecodingError: A response body could not be decoded.
    HTTPResponseError: Base for unsuccessful HTTP responses (adds status_code, response_text).
    HTTPClientError / HTTPServerError: 4xx / 5xx bases, with their per-status leaves.
    UnexpectedHTTPStatusError: An unmapped non-success status.
    TransportRetryError: Retries exhausted (a tenacity RetryError).

See Also:
    - :mod:`fedfred._internals._transport`: Raises these.
    - :class:`fedfred.exceptions.internals.base.InternalsError`: The internals-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from tenacity import RetryError

from .base import InternalsError

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "BadGatewayError",
    "BadRequestError",
    "ConflictError",
    "ConnectTimeoutError",
    "GatewayTimeoutError",
    "GoneError",
    "HTTPClientError",
    "HTTPResponseError",
    "HTTPServerError",
    "InternalServerError",
    "MethodNotAllowedError",
    "NotFoundError",
    "PoolTimeoutError",
    "ProxyTransportError",
    "RateLimitError",
    "ReadTimeoutError",
    "RequestPreparationError",
    "ResponseDecodingError",
    "ServiceUnavailableError",
    "TooManyRedirectsError",
    "TransportConnectionError",
    "TransportError",
    "TransportProtocolError",
    "TransportReadError",
    "TransportRequestError",
    "TransportRetryError",
    "TransportTimeoutError",
    "TransportWriteError",
    "UnexpectedHTTPStatusError",
    "UnprocessableEntityError",
    "UnsupportedProtocolError",
    "WriteTimeoutError",
]


@dataclass(frozen=True, slots=True)
class TransportError(InternalsError):
    """Base class for transport-layer failures.

    The module catch-all for :mod:`fedfred._internals._transport`. Carries the request
    URL and method (when known); HTTP-response failures add status/body via
    :class:`HTTPResponseError`. ``message`` is supplied positionally by the mappers.

    Attributes:
        url (str | None): The request URL associated with the failure, if available.
        method (str | None): The HTTP method associated with the failure, if available.
        message (str): Human-readable message (inherited from :class:`InternalsError`).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying ``httpx`` error, if
            any (inherited).
    """

    url: str | None = None
    """The request URL associated with the failure, if available."""

    method: str | None = None
    """The HTTP method associated with the failure, if available."""

    def __str__(self) -> str:
        """Return the message, suffixed with method/url when known.

        Returns:
            str: :attr:`message` with ``(method=…, url=…)`` appended for whichever
            are set; the bare :attr:`message` otherwise.
        """
        extra = [
            f"{name}={value!r}"
            for name, value in (("method", self.method), ("url", self.url))
            if value
        ]
        return f"{self.message} ({', '.join(extra)})" if extra else self.message


@dataclass(frozen=True, slots=True)
class RequestPreparationError(TransportError):
    """Raised when a request cannot be constructed correctly (e.g. endpoint resolution)."""


@dataclass(frozen=True, slots=True)
class TransportRequestError(TransportError):
    """Base for request-execution failures, raised before a valid HTTP response is processed."""


@dataclass(frozen=True, slots=True)
class TransportConnectionError(TransportRequestError):
    """Raised when a connection to the remote service cannot be established."""


@dataclass(frozen=True, slots=True)
class TransportTimeoutError(TransportRequestError):
    """Base exception for request timeout failures."""


@dataclass(frozen=True, slots=True)
class ConnectTimeoutError(TransportTimeoutError):
    """Raised when connecting to the remote service times out."""


@dataclass(frozen=True, slots=True)
class ReadTimeoutError(TransportTimeoutError):
    """Raised when reading the response from the remote service times out."""


@dataclass(frozen=True, slots=True)
class WriteTimeoutError(TransportTimeoutError):
    """Raised when writing request data to the remote service times out."""


@dataclass(frozen=True, slots=True)
class PoolTimeoutError(TransportTimeoutError):
    """Raised when acquiring a connection from the pool times out."""


@dataclass(frozen=True, slots=True)
class TransportReadError(TransportRequestError):
    """Raised when reading from the remote service fails."""


@dataclass(frozen=True, slots=True)
class TransportWriteError(TransportRequestError):
    """Raised when writing to the remote service fails."""


@dataclass(frozen=True, slots=True)
class TransportProtocolError(TransportRequestError):
    """Raised when an HTTP protocol error occurs."""


@dataclass(frozen=True, slots=True)
class ProxyTransportError(TransportRequestError):
    """Raised when proxy communication fails."""


@dataclass(frozen=True, slots=True)
class UnsupportedProtocolError(TransportRequestError):
    """Raised when an unsupported URL protocol is used."""


@dataclass(frozen=True, slots=True)
class TooManyRedirectsError(TransportRequestError):
    """Raised when the request exceeds the allowed redirect limit."""


@dataclass(frozen=True, slots=True)
class ResponseDecodingError(TransportRequestError):
    """Raised when a response body cannot be decoded or parsed as expected."""


@dataclass(frozen=True, slots=True)
class HTTPResponseError(TransportError):
    """Base class for unsuccessful HTTP responses.

    Adds the response status and body to the request URL/method inherited from
    :class:`TransportError`.

    Attributes:
        status_code (int | None): The HTTP status code associated with the failure.
        response_text (str | None): The decoded response text, if available.
        url (str | None): The request URL (inherited).
        method (str | None): The HTTP method (inherited).
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error (inherited).
    """

    status_code: int | None = None
    """The HTTP status code associated with the failure."""

    response_text: str | None = None
    """The decoded response text, if available."""

    def __str__(self) -> str:
        """Return the message, suffixed with status/method/url when known.

        Returns:
            str: :attr:`message` with ``(status=…, method=…, url=…)`` appended for
            whichever are set; the bare :attr:`message` otherwise. ``response_text``
            is omitted (it may be large) but remains available as an attribute.
        """
        extra: list[str] = []
        if self.status_code is not None:
            extra.append(f"status={self.status_code}")
        if self.method:
            extra.append(f"method={self.method!r}")
        if self.url:
            extra.append(f"url={self.url!r}")
        return f"{self.message} ({', '.join(extra)})" if extra else self.message


@dataclass(frozen=True, slots=True)
class HTTPClientError(HTTPResponseError):
    """Raised for 4xx HTTP response errors."""


@dataclass(frozen=True, slots=True)
class BadRequestError(HTTPClientError):
    """Raised for HTTP 400 responses."""


@dataclass(frozen=True, slots=True)
class AuthenticationError(HTTPClientError):
    """Raised for HTTP 401 or equivalent authentication failures."""


@dataclass(frozen=True, slots=True)
class AuthorizationError(HTTPClientError):
    """Raised for HTTP 403 responses."""


@dataclass(frozen=True, slots=True)
class NotFoundError(HTTPClientError):
    """Raised for HTTP 404 responses."""


@dataclass(frozen=True, slots=True)
class MethodNotAllowedError(HTTPClientError):
    """Raised for HTTP 405 responses."""


@dataclass(frozen=True, slots=True)
class ConflictError(HTTPClientError):
    """Raised for HTTP 409 responses."""


@dataclass(frozen=True, slots=True)
class GoneError(HTTPClientError):
    """Raised for HTTP 410 responses."""


@dataclass(frozen=True, slots=True)
class UnprocessableEntityError(HTTPClientError):
    """Raised for HTTP 422 responses."""


@dataclass(frozen=True, slots=True)
class RateLimitError(HTTPClientError):
    """Raised for HTTP 429 responses."""


@dataclass(frozen=True, slots=True)
class HTTPServerError(HTTPResponseError):
    """Raised for 5xx HTTP response errors."""


@dataclass(frozen=True, slots=True)
class InternalServerError(HTTPServerError):
    """Raised for HTTP 500 responses."""


@dataclass(frozen=True, slots=True)
class BadGatewayError(HTTPServerError):
    """Raised for HTTP 502 responses."""


@dataclass(frozen=True, slots=True)
class ServiceUnavailableError(HTTPServerError):
    """Raised for HTTP 503 responses."""


@dataclass(frozen=True, slots=True)
class GatewayTimeoutError(HTTPServerError):
    """Raised for HTTP 504 responses."""


@dataclass(frozen=True, slots=True)
class UnexpectedHTTPStatusError(HTTPResponseError):
    """Raised for unexpected or unmapped non-success HTTP status codes."""


class TransportRetryError(RetryError):
    """Raised when transport retry attempts are exhausted.

    Tenacity-native: subclasses :class:`tenacity.RetryError` (not
    :class:`TransportError`), because it is the retry decorator's ``retry_error_cls``
    and is constructed by tenacity with the final attempt. It therefore carries
    tenacity's ``last_attempt`` rather than the fedfred structured payload, and is
    *not* caught by ``except TransportError`` / ``except InternalsError`` — catch it as
    :class:`TransportRetryError` or :class:`tenacity.RetryError`.

    Attributes:
        last_attempt (tenacity.Future): The final, failed retry attempt (from
            :class:`tenacity.RetryError`).
    """
