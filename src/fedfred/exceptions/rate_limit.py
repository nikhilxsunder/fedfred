
from dataclasses import dataclass
from typing import Optional
from .base import FedFredError

@dataclass(frozen=True, slots=True)
class RateLimitError(FedFredError):
    """Base exception for all rate-limiting related errors."""

@dataclass(frozen=True, slots=True)
class RateLimiterConfigurationError(RateLimitError):
    """Raised when the rate limiter is configured with invalid values."""

@dataclass(frozen=True, slots=True)
class RateLimiterStateError(RateLimitError):
    """Raised when the rate limiter enters or detects an invalid internal state."""

@dataclass(frozen=True, slots=True)
class RateLimiterContextError(RateLimitError):
    """Raised when the rate limiter is used in an invalid runtime or event-loop context."""

@dataclass(frozen=True, slots=True)
class RateLimitExceededError(RateLimitError):
    """Raised when a request would exceed the configured rate limit."""

    requests_left: Optional[int] = None
    retry_after: Optional[float] = None
    max_requests_per_minute: Optional[int] = None

    def __init__(self, message: str = "Rate limit exceeded.", *, requests_left: Optional[int] = None, retry_after: Optional[float] = None,
                 max_requests_per_minute: Optional[int] = None) -> None:
        super().__init__(message)
        object.__setattr__(self, "requests_left", requests_left)
        object.__setattr__(self, "retry_after", retry_after)
        object.__setattr__(self, "max_requests_per_minute", max_requests_per_minute)

@dataclass(frozen=True, slots=True)
class LimiterLimitError(RateLimiterConfigurationError):
    """Raised when the limiter limit is invalid."""

@dataclass(frozen=True, slots=True)
class LimiterReleaseError(RateLimiterStateError):
    """Raised when release() is called without a matching acquire()."""

@dataclass(frozen=True, slots=True)
class LimiterLoopError(RateLimiterContextError):
    """Raised when limiter notification or scheduling fails due to event-loop issues."""

@dataclass(frozen=True, slots=True)
class LimiterWakeError(RateLimiterContextError):
    """Raised when waiter notification fails."""

@dataclass(frozen=True, slots=True)
class LimiterSpecError(RateLimiterConfigurationError):
    """Raised when a limiter spec contains invalid configuration."""

@dataclass(frozen=True, slots=True)
class LimiterServiceError(LimiterSpecError):
    """Raised when an unknown or unsupported service is requested."""

@dataclass(frozen=True, slots=True)
class LimiterQueueStateError(RateLimiterStateError):
    """Raised when request timestamp state is malformed."""