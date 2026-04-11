

from dataclasses import dataclass
from .base import FedFredError



@dataclass(frozen=True, slots=True)
class EndpointError(FedFredError):
    """Base exception for all endpoint-resolution related errors."""

@dataclass(frozen=True, slots=True)
class EndpointConfigurationError(EndpointError):
    """Raised when internal endpoint configuration is invalid or incomplete."""

@dataclass(frozen=True, slots=True)
class EndpointResolutionError(EndpointError):
    """Raised when an endpoint name cannot be resolved."""

@dataclass(frozen=True, slots=True)
class EndpointSpecError(EndpointError):
    """Raised when a resolved endpoint specification is invalid."""

@dataclass(frozen=True, slots=True)
class EndpointContextError(EndpointError):
    """Raised when endpoint resolution fails due to runtime context issues."""

@dataclass(frozen=True, slots=True)
class EndpointNameTypeError(EndpointResolutionError):
    """Raised when an endpoint name is not a string."""

@dataclass(frozen=True, slots=True)
class EndpointNameValueError(EndpointResolutionError):
    """Raised when an endpoint name is empty or otherwise invalid."""

@dataclass(frozen=True, slots=True)
class EndpointUnsupportedError(EndpointResolutionError):
    """Raised when an endpoint name is not supported by the registry."""

@dataclass(frozen=True, slots=True)
class EndpointMapError(EndpointConfigurationError):
    """Raised when an endpoint map is invalid or malformed."""

@dataclass(frozen=True, slots=True)
class EndpointBaseURLError(EndpointConfigurationError):
    """Raised when a configured base URL is invalid."""

@dataclass(frozen=True, slots=True)
class EndpointParametersError(EndpointConfigurationError):
    """Raised when default endpoint parameters are invalid."""

@dataclass(frozen=True, slots=True)
class EndpointPayloadError(EndpointConfigurationError):
    """Raised when default endpoint payload is invalid."""

@dataclass(frozen=True, slots=True)
class EndpointHeadersError(EndpointConfigurationError):
    """Raised when default endpoint headers are invalid."""

@dataclass(frozen=True, slots=True)
class EndpointServiceError(EndpointSpecError):
    """Raised when a resolved endpoint spec contains an invalid service name."""

@dataclass(frozen=True, slots=True)
class EndpointURLError(EndpointSpecError):
    """Raised when a resolved endpoint spec contains an invalid URL."""