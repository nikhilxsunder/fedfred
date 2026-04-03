
from dataclasses import dataclass
from typing import Optional
from tenacity import RetryError
from .base import FedfredError

@dataclass(frozen=True, slots=True)
class TransportError(FedfredError):
    """
    Base exception for transport-layer failures in fedfred.

    Attributes:
        url (Optional[str]):
            The request URL associated with the failure, if available.
        method (Optional[str]):
            The HTTP method associated with the failure, if available.
    """

    def __init__(self, message: str, *, url: Optional[str] = None, method: Optional[str] = None,
                 status_code: Optional[int] = None, response_text: Optional[str] = None) -> None:

        super().__init__(message)
        self.url: Optional[str] = url
        self.method: Optional[str] = method
        self.status_code: Optional[int] = status_code
        self.response_text: Optional[str] = response_text

@dataclass(frozen=True, slots=True, init=False)
class RequestPreparationError(TransportError):
    """Raised when a request cannot be constructed correctly."""

@dataclass(frozen=True, slots=True, init=False)
class TransportRequestError(TransportError):
    """Base exception for request execution failures before a valid HTTP error response is processed."""

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

@dataclass(frozen=True, slots=True, init=False)
class ResponseDecodingError(TransportRequestError):
    """Raised when a response body cannot be decoded or parsed as expected."""

@dataclass(frozen=True, slots=True, init=False)
class TransportRetryError(RetryError):
    """
    Raised when transport retry attempts are exhausted.

    Attributes:
        attempts (Optional[int]):
            The number of retry attempts performed, if known.
    """

@dataclass(frozen=True, slots=True, init=False)
class HTTPResponseError(TransportError):
    """
    Base exception for unsuccessful HTTP responses.

    Attributes:
        status_code (Optional[int]):
            The HTTP status code associated with the failure.
        response_text (Optional[str]):
            The decoded response text, if available.
    """

@dataclass(frozen=True, slots=True, init=False)
class HTTPClientError(HTTPResponseError):
    """Raised for 4xx HTTP response errors."""


@dataclass(frozen=True, slots=True, init=False)
class BadRequestError(HTTPClientError):
    """Raised for HTTP 400 responses."""


@dataclass(frozen=True, slots=True, init=False)
class AuthenticationError(HTTPClientError):
    """Raised for HTTP 401 or equivalent authentication failures."""


@dataclass(frozen=True, slots=True, init=False)
class AuthorizationError(HTTPClientError):
    """Raised for HTTP 403 responses."""


@dataclass(frozen=True, slots=True, init=False)
class NotFoundError(HTTPClientError):
    """Raised for HTTP 404 responses."""


@dataclass(frozen=True, slots=True, init=False)
class MethodNotAllowedError(HTTPClientError):
    """Raised for HTTP 405 responses."""


@dataclass(frozen=True, slots=True, init=False)
class ConflictError(HTTPClientError):
    """Raised for HTTP 409 responses."""


@dataclass(frozen=True, slots=True, init=False)
class GoneError(HTTPClientError):
    """Raised for HTTP 410 responses."""


@dataclass(frozen=True, slots=True, init=False)
class UnprocessableEntityError(HTTPClientError):
    """Raised for HTTP 422 responses."""


@dataclass(frozen=True, slots=True, init=False)
class RateLimitError(HTTPClientError):
    """Raised for HTTP 429 responses."""


@dataclass(frozen=True, slots=True, init=False)
class HTTPServerError(HTTPResponseError):
    """Raised for 5xx HTTP response errors."""


@dataclass(frozen=True, slots=True, init=False)
class InternalServerError(HTTPServerError):
    """Raised for HTTP 500 responses."""


@dataclass(frozen=True, slots=True, init=False)
class BadGatewayError(HTTPServerError):
    """Raised for HTTP 502 responses."""


@dataclass(frozen=True, slots=True, init=False)
class ServiceUnavailableError(HTTPServerError):
    """Raised for HTTP 503 responses."""


@dataclass(frozen=True, slots=True, init=False)
class GatewayTimeoutError(HTTPServerError):
    """Raised for HTTP 504 responses."""


@dataclass(frozen=True, slots=True, init=False)
class UnexpectedHTTPStatusError(HTTPResponseError):
    """Raised for unexpected or unmapped non-success HTTP status codes."""
