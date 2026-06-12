# filepath: /src/fedfred/exceptions/internals/rate_limit.py
# <standard MIT header>
"""Rate-limiting exceptions for the fedfred internals package.

The error hierarchy for :mod:`fedfred._internals._rate_limit`. The base
:class:`RateLimiterError` splits into three failure axes — configuration
(:class:`RateLimiterConfigurationError`), internal state
(:class:`RateLimiterStateError`), and runtime/event-loop context
(:class:`RateLimiterContextError`) — plus the request-pacing outcome
:class:`RateLimitExceededError`, which carries structured retry metadata.

The name distinction from transport's
:class:`~fedfred.exceptions.internals.transport.RateLimitError` (HTTP 429) is deliberate:
that is a *server* response telling the client it sent too many requests, whereas these
are the *client-side* limiter's own failures.

Classes:
    RateLimiterError: Base for all limiter failures.
    RateLimiterConfigurationError: Invalid limiter configuration.
    LimiterLimitError: Invalid concurrency limit.
    LimiterSpecError: Invalid limiter spec.
    LimiterServiceError: Unknown/unsupported service.
    RateLimiterStateError: Invalid internal state.
    LimiterReleaseError: release() without a matching acquire().
    LimiterQueueStateError: Malformed request-timestamp state.
    RateLimiterContextError: Invalid runtime/event-loop context.
    LimiterLoopError: Missing event loop for notification/scheduling.
    LimiterWakeError: Waiter wake-up scheduling failed.
    RateLimitExceededError: A request would exceed the configured limit.

See Also:
    - :mod:`fedfred._internals._rate_limit`: Raises these.
    - :class:`fedfred.exceptions.internals.base.InternalsError`: The internals-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import InternalsError

__all__ = [
    "LimiterLimitError",
    "LimiterLoopError",
    "LimiterQueueStateError",
    "LimiterReleaseError",
    "LimiterServiceError",
    "LimiterSpecError",
    "LimiterWakeError",
    "RateLimitExceededError",
    "RateLimiterConfigurationError",
    "RateLimiterContextError",
    "RateLimiterError",
    "RateLimiterStateError",
]


@dataclass(frozen=True, slots=True)
class RateLimiterError(InternalsError):
    """Base class for client-side rate-limiter failures.

    The module catch-all for :mod:`fedfred._internals._rate_limit`: catch this to handle
    any limiter failure regardless of axis (configuration, state, context, or
    limit-exceeded). Adds no fields; inherits the structured payload (:attr:`message`,
    :attr:`context`, :attr:`original_exception`) from :class:`InternalsError`.

    Note:
        Distinct from :class:`~fedfred.exceptions.internals.transport.RateLimitError`,
        which represents an HTTP 429 *response* from the server.
    """


@dataclass(frozen=True, slots=True)
class RateLimiterConfigurationError(RateLimiterError):
    """Raised when the rate limiter is configured with invalid values.

    Base of the configuration-failure axis. Raised via its subclasses, or directly by
    :func:`~fedfred._internals._rate_limit._semaphore_updater` when a bucket's
    ``max_requests_per_minute`` is below 1.
    """


@dataclass(frozen=True, slots=True)
class LimiterLimitError(RateLimiterConfigurationError):
    """Raised when a limiter concurrency limit is invalid (below 1).

    Raised by :class:`~fedfred._internals._rate_limit.AdjustableLimiter` on construction
    and by its ``set_limit`` when given a limit less than 1.
    """


@dataclass(frozen=True, slots=True)
class LimiterSpecError(RateLimiterConfigurationError):
    """Raised when a limiter spec contains invalid configuration."""


@dataclass(frozen=True, slots=True)
class LimiterServiceError(LimiterSpecError):
    """Raised when an unknown or unsupported service is requested.

    Raised by :func:`~fedfred._internals._rate_limit._resolve_limiter` when the service
    has no entry in the core rate-limit bucket mapping.
    """


@dataclass(frozen=True, slots=True)
class RateLimiterStateError(RateLimiterError):
    """Raised when the rate limiter enters or detects an invalid internal state.

    Base of the state-failure axis. Raised via its subclasses, or directly by
    :func:`~fedfred._internals._rate_limit._semaphore_updater` when the semaphore's limit
    has fallen below 1.
    """


@dataclass(frozen=True, slots=True)
class LimiterReleaseError(RateLimiterStateError):
    """Raised when ``release()`` is called without a matching ``acquire()``.

    Raised by :meth:`~fedfred._internals._rate_limit.AdjustableLimiter.release` when the
    holder count is already zero.
    """


@dataclass(frozen=True, slots=True)
class LimiterQueueStateError(RateLimiterStateError):
    """Raised when request-timestamp state is malformed.

    Reserved for inconsistencies in a bucket's request-time deque (e.g. a recorded volume
    that cannot reconcile with the window contents).

    Note:
        Currently has no raiser — the previous inconsistency check was removed as dead
        code. Either wire it to a real invariant or keep it as forward-looking API.
    """


@dataclass(frozen=True, slots=True)
class RateLimiterContextError(RateLimiterError):
    """Raised when the rate limiter is used in an invalid runtime or event-loop context.

    Base of the context-failure axis: failures stemming from the absence of a running
    event loop rather than from bad configuration or corrupt state.
    """


@dataclass(frozen=True, slots=True)
class LimiterLoopError(RateLimiterContextError):
    """Raised when limiter notification or scheduling fails for lack of an event loop.

    Raised by :meth:`~fedfred._internals._rate_limit.AdjustableLimiter.set_limit` when no
    event loop is running to notify waiters.
    """


@dataclass(frozen=True, slots=True)
class LimiterWakeError(RateLimiterContextError):
    """Raised when scheduling the waiter wake-up task fails.

    Raised by the limiter's internal ``_notify`` when ``asyncio.create_task`` cannot be
    scheduled because no event loop is running.
    """


@dataclass(frozen=True, slots=True)
class RateLimitExceededError(RateLimiterError):
    """Raised when a request would exceed the configured rate limit.

    The structured, caller-facing limiter rejection: rather than blocking, the limiter
    signals that the per-minute budget is spent and surfaces the metadata a caller needs
    to back off. Distinct from the transport HTTP 429
    :class:`~fedfred.exceptions.internals.transport.RateLimitError`, which is the
    *server's* response — this is raised by the *client-side* limiter.

    Attributes:
        requests_left (int | None): Requests remaining in the current window, if known.
        retry_after (float | None): Seconds to wait before retrying, if known.
        max_requests_per_minute (int | None): The bucket's per-minute ceiling, if known.
        message (str): Human-readable message (inherited from :class:`InternalsError`).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error, if any (inherited).

    Note:
        The hand-written keyword-only ``__init__`` is the justified exception to the
        hierarchy's "no manual ``__init__``" rule: a default message *and* keyword-only
        metadata can't be expressed by redeclaring the inherited, slotted ``message``
        field without risking a slot conflict. ``object.__setattr__`` is required because
        the dataclass is frozen.
    """

    requests_left: int | None = None
    """Requests remaining in the current window, if known."""

    retry_after: float | None = None
    """Seconds to wait before retrying, if known."""

    max_requests_per_minute: int | None = None
    """The bucket's per-minute ceiling, if known."""

    def __init__(
        self,
        message: str = "Rate limit exceeded.",
        *,
        requests_left: int | None = None,
        retry_after: float | None = None,
        max_requests_per_minute: int | None = None,
    ) -> None:
        """Initialize the error with optional structured retry metadata.

        Args:
            message (str): Human-readable message. Defaults to ``"Rate limit exceeded."``.
            requests_left (int | None): Requests remaining in the window. Keyword-only.
            retry_after (float | None): Seconds to wait before retrying. Keyword-only.
            max_requests_per_minute (int | None): The bucket's per-minute ceiling. Keyword-only.
        """
        super().__init__(message)
        object.__setattr__(self, "requests_left", requests_left)
        object.__setattr__(self, "retry_after", retry_after)
        object.__setattr__(self, "max_requests_per_minute", max_requests_per_minute)

    def __str__(self) -> str:
        """Return the message, suffixed with retry metadata when known.

        Returns:
            str: :attr:`message` with ``(retry_after=…, requests_left=…)`` appended for
            whichever are set; the bare :attr:`message` otherwise.
        """
        extra = [
            f"{name}={value}"
            for name, value in (
                ("retry_after", self.retry_after),
                ("requests_left", self.requests_left),
            )
            if value is not None
        ]
        return f"{self.message} ({', '.join(extra)})" if extra else self.message
