
from typing import Optional
from .base import FedfredError

class RateLimitError(FedfredError):
    """Base exception for all rate-limiting related errors."""


class RateLimiterConfigurationError(RateLimitError):
    """Raised when the rate limiter is configured with invalid values."""


class RateLimiterStateError(RateLimitError):
    """Raised when the rate limiter enters or detects an invalid internal state."""


class RateLimiterContextError(RateLimitError):
    """Raised when the rate limiter is used in an invalid runtime or event-loop context."""


class RateLimitExceededError(RateLimitError):
    """Raised when a request would exceed the configured rate limit."""

    def __init__(self, message: str = "Rate limit exceeded.", *, requests_left: Optional[int] = None,
                 retry_after: Optional[float] = None, max_requests_per_minute: Optional[int] = None) -> None:

        super().__init__(message)
        self.requests_left = requests_left
        self.retry_after = retry_after
        self.max_requests_per_minute = max_requests_per_minute


class LimiterLimitError(RateLimiterConfigurationError):
    """Raised when the limiter limit is invalid."""


class LimiterReleaseError(RateLimiterStateError):
    """Raised when release() is called without a matching acquire()."""


class LimiterLoopError(RateLimiterContextError):
    """Raised when limiter notification or scheduling fails due to event-loop issues."""


class LimiterWakeError(RateLimiterContextError):
    """Raised when waiter notification fails."""