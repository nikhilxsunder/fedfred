# filepath: /src/fedfred/_internals/_rate_limit.py
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
"""Rolling-window rate limiting for the FRED family of services.

Provides the concurrency and request-pacing primitives shared by the synchronous and
asynchronous clients. :class:`AdjustableLimiter` is a capacity limiter whose cap can be
changed at runtime; :class:`LimiterSpec` owns a bucket's rolling-window state (request-time
deque, lock, semaphore, per-minute limit). The bucket grouping and per-minute limits are
defined in :mod:`fedfred._core` (:data:`~fedfred._core.RATE_LIMIT_BUCKET`,
:data:`~fedfred._core.RATE_LIMIT_RPM`); this module binds that data to live asyncio state.
Two buckets are maintained: the FRED group (FRED, ALFRED, GeoFRED) and FRASER.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from types import TracebackType

from .._core import (
    _CONCURRENCY_DIVISOR,
    _WINDOW_SECONDS,
    RATE_LIMIT_BUCKET,
    RATE_LIMIT_RPM,
    RateLimitBucket,
)
from ..exceptions import (
    LimiterLimitError,
    LimiterLoopError,
    LimiterReleaseError,
    LimiterServiceError,
    LimiterWakeError,
    RateLimiterConfigurationError,
    RateLimiterStateError,
)
from ..settings import Service


@dataclass(slots=True)
class AdjustableLimiter:
    """Capacity limiter with a runtime-adjustable limit.

    Permits at most ``limit`` concurrent holders. Used as an asynchronous context
    manager (``async with``) or via explicit :meth:`acquire` / :meth:`release`.
    :meth:`set_limit` changes the cap at runtime; holders that already own a slot keep
    it until they release.

    Attributes:
        limit (int): The maximum number of concurrent holders allowed.

    Examples:
        >>> from fedfred._internals._rate_limit import AdjustableLimiter
        >>> limiter = AdjustableLimiter(limit=5)
        >>> limiter.limit
        5

    Notes:
        Instances are constructed at module import to back each bucket's semaphore.
    """

    limit: int
    """The maximum number of concurrent holders allowed."""

    _in_use: int = field(init=False)
    """The current number of holders using the limiter."""

    _cond: asyncio.Condition = field(init=False)
    """Condition variable for managing waiters."""

    _background_tasks: set[asyncio.Task[None]] = field(init=False)
    """Strong references to scheduled wake-up tasks, preventing premature garbage collection."""

    def __post_init__(self) -> None:
        """Validate the limit and initialize internal state.

        Raises:
            LimiterLimitError: If ``limit`` is less than 1.

        Examples:
            >>> from fedfred._internals._rate_limit import AdjustableLimiter
            >>> AdjustableLimiter(limit=5).limit
            5
            >>> AdjustableLimiter(limit=0)  # doctest: +SKIP
            LimiterLimitError: limit must be >= 1
        """
        if self.limit < 1:
            raise LimiterLimitError("limit must be >= 1")

        self._in_use = 0

        self._cond = asyncio.Condition()

        self._background_tasks = set()

    async def __aenter__(self) -> AdjustableLimiter:
        """Enter the asynchronous context manager, acquiring a slot.

        Returns:
            AdjustableLimiter: This limiter instance, for use within the ``async with`` block.

        Notes:
            Blocks until a slot is available; see :meth:`acquire`.
        """
        await self.acquire()

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit the asynchronous context manager, releasing the slot.

        Args:
            exc_type (type[BaseException] | None): The exception type, if any.
            exc (BaseException | None): The exception instance, if any.
            tb (TracebackType | None): The traceback, if any.

        Raises:
            LimiterReleaseError: If the limiter is released more times than it was acquired.

        Notes:
            The slot is released whether or not an exception occurred within the context.
        """
        await self.release()

    def _notify(self) -> None:
        """Schedule a task to wake all waiters after a limit change.

        Raises:
            LimiterWakeError: If the wake-up task cannot be scheduled because no event
                loop is running.

        Notes:
            Invoked via ``call_soon_threadsafe`` from :meth:`set_limit`, so it may run on
            the event-loop thread in response to a cross-thread limit change. The scheduled
            task is held in ``_background_tasks`` until completion to prevent it from being
            garbage-collected mid-flight.
        """
        try:
            task = asyncio.create_task(self._wake_waiters())

        except RuntimeError as exc:
            raise LimiterWakeError("Failed to schedule waiter wake-up task.") from exc

        self._background_tasks.add(task)

        task.add_done_callback(self._background_tasks.discard)

    async def _wake_waiters(self) -> None:
        """Wake every task waiting on the condition variable.

        Notes:
            Acquires the condition and calls ``notify_all`` so waiters re-check the limit.
        """
        async with self._cond:
            self._cond.notify_all()

    def set_limit(self, new_limit: int) -> None:
        """Change the maximum number of concurrent holders at runtime.

        Args:
            new_limit (int): The new maximum number of concurrent holders. Must be >= 1.

        Raises:
            LimiterLimitError: If ``new_limit`` is less than 1.
            LimiterLoopError: If no event loop is running to notify waiters.

        Notes:
            Existing holders keep their slots; only newly waiting tasks observe the new cap.
            Waiters are notified via a thread-safe callback so the limit may be adjusted
            from a thread other than the event-loop thread.
        """
        if new_limit < 1:
            raise LimiterLimitError(f"new_limit must be >= 1, got {new_limit}")

        self.limit = new_limit

        try:
            asyncio.get_running_loop().call_soon_threadsafe(self._notify)

        except RuntimeError as exc:
            raise LimiterLoopError(
                "set_limit() requires a running event loop to notify waiters."
            ) from exc

    async def acquire(self) -> None:
        """Acquire a slot, waiting until one is available.

        Notes:
            Suspends on the condition variable until ``_in_use`` falls below ``limit``,
            then claims a slot. Must be called from within a running event loop.
        """
        async with self._cond:
            while self._in_use >= self.limit:
                await self._cond.wait()

            self._in_use += 1

    async def release(self) -> None:
        """Release a held slot and notify waiters.

        Raises:
            LimiterReleaseError: If called when no slot is currently held (more releases
                than acquires).

        Notes:
            Decrements the holder count and wakes all waiters so they can re-attempt acquisition.
        """
        async with self._cond:
            if self._in_use <= 0:
                raise LimiterReleaseError("release() called too many times")

            self._in_use -= 1

            self._cond.notify_all()


@dataclass(slots=True)
class LimiterSpec:
    """Rolling-window rate-limiting state for a single bucket.

    Owns the request-time deque, lock, semaphore, and per-minute limit for one bucket.
    The per-minute limit is read from :data:`~fedfred._core.RATE_LIMIT_RPM`; the live
    state (deque, lock, semaphore) is created fresh per spec. Exactly one spec per bucket
    is constructed at import and held in :data:`_BUCKET_STATE`; callers reach it via
    :func:`_resolve_limiter`.

    Attributes:
        bucket (RateLimitBucket): The bucket this spec governs (``"fred"`` or ``"fraser"``).
        max_requests_per_minute (int): The per-minute request ceiling for the bucket.
        request_times (deque[float]): Timestamps of recent requests to the bucket.
        lock (asyncio.Lock): Lock synchronizing the request-time deque and semaphore.
        semaphore (AdjustableLimiter): Adjustable limiter controlling concurrent access.

    Examples:
        >>> from fedfred._internals._rate_limit import LimiterSpec
        >>> LimiterSpec(bucket="fred").max_requests_per_minute
        120
    """

    bucket: RateLimitBucket
    """The bucket this spec governs."""

    max_requests_per_minute: int = field(init=False)
    """The per-minute request ceiling for the bucket."""

    request_times: deque[float] = field(init=False)
    """Timestamps of recent requests to the bucket."""

    lock: asyncio.Lock = field(init=False)
    """Lock synchronizing the request-time deque and semaphore."""

    semaphore: AdjustableLimiter = field(init=False)
    """Adjustable limiter controlling concurrent access to the bucket."""

    def __post_init__(self) -> None:
        """Bind the bucket's per-minute limit and create fresh window state.

        Raises:
            RateLimiterConfigurationError: If ``bucket`` has no entry in
                :data:`~fedfred._core.RATE_LIMIT_RPM` (a packaging/wiring error).

        Examples:
            >>> from fedfred._internals._rate_limit import LimiterSpec
            >>> LimiterSpec(bucket="fraser").max_requests_per_minute
            30
        """
        try:
            self.max_requests_per_minute = RATE_LIMIT_RPM[self.bucket]

        except KeyError as exc:
            raise RateLimiterConfigurationError(
                f"No per-minute limit configured for bucket: {self.bucket!r}"
            ) from exc

        self.request_times = deque()

        self.lock = asyncio.Lock()

        self.semaphore = AdjustableLimiter(
            limit=max(1, self.max_requests_per_minute // _CONCURRENCY_DIVISOR)
        )


_BUCKET_STATE: dict[RateLimitBucket, LimiterSpec] = {
    bucket: LimiterSpec(bucket) for bucket in RATE_LIMIT_RPM
}
"""The one live :class:`LimiterSpec` per bucket, constructed at import."""


def _evict_stale(request_times: deque[float], now: float, window: float = _WINDOW_SECONDS) -> None:
    """Drop timestamps older than ``window`` seconds from the left of the deque.

    Args:
        request_times (deque[float]): The deque to prune, modified in place.
        now (float): The current time, as ``time.time()``.
        window (float): The window length in seconds. Defaults to :data:`_WINDOW_SECONDS`.

    Notes:
        Mutates ``request_times`` in place; callers holding a lock should call it inside
        the critical section.
    """
    while request_times and request_times[0] < now - window:
        request_times.popleft()


def _resolve_limiter(service: Service) -> LimiterSpec:
    """Resolve a service to its bucket's live limiter spec.

    Args:
        service (Service): The service to resolve.

    Returns:
        LimiterSpec: The shared spec for the service's bucket.

    Raises:
        LimiterServiceError: If ``service`` is not a known rate-limited service.

    Examples:
        >>> from fedfred._internals._rate_limit import _resolve_limiter
        >>> _resolve_limiter("fred").max_requests_per_minute
        120
        >>> _resolve_limiter("unknown")  # doctest: +SKIP
        LimiterServiceError: Unknown rate-limited service: 'unknown'

    Notes:
        Returns the same spec instance for every service in a bucket (FRED, GeoFRED, and
        ALFRED all return the FRED spec), so callers share one rolling window per bucket.
    """
    try:
        bucket = RATE_LIMIT_BUCKET[service]

    except KeyError as exc:
        raise LimiterServiceError(f"Unknown rate-limited service: {service!r}") from exc

    return _BUCKET_STATE[bucket]


async def _semaphore_updater(spec: LimiterSpec) -> tuple[int, float]:
    """Recompute the semaphore limit from the requests remaining this minute.

    Args:
        spec (LimiterSpec): The bucket spec whose window and semaphore are updated.

    Returns:
        tuple[int, float]: The number of requests remaining this minute and the seconds
            left in the current window.

    Raises:
        RateLimiterConfigurationError: If the bucket's ``max_requests_per_minute`` is less than 1.
        RateLimiterStateError: If the semaphore limit is below 1.
        LimiterLimitError: If the recomputed limit is rejected by
            :meth:`AdjustableLimiter.set_limit`.
        LimiterLoopError: If no event loop is running to notify waiters during the update.

    Notes:
        Evicts stale timestamps, then narrows the semaphore toward the remaining headroom
        so concurrency tapers as the per-minute budget is consumed.

    Warnings:
        Must be awaited within a running event loop; it acquires ``spec.lock`` and may
        adjust ``spec.semaphore``.
    """
    if spec.max_requests_per_minute < 1:
        raise RateLimiterConfigurationError(
            f"max_requests_per_minute must be >= 1, got {spec.max_requests_per_minute}"
        )

    if spec.semaphore.limit < 1:
        raise RateLimiterStateError(
            f"Limiter semaphore is in an invalid state: limit={spec.semaphore.limit}"
        )

    async with spec.lock:
        now = time.time()

        _evict_stale(spec.request_times, now)

        requests_made = len(spec.request_times)

        requests_left = max(0, spec.max_requests_per_minute - requests_made)

        oldest = spec.request_times[0] if spec.request_times else now

        time_left = max(1.0, _WINDOW_SECONDS - (now - oldest))

        new_limit = max(
            1, min(spec.max_requests_per_minute // _CONCURRENCY_DIVISOR, requests_left // 2)
        )

        spec.semaphore.set_limit(new_limit)

        return requests_left, time_left


def _rate_limiter(service: Service) -> None:
    """Pace a synchronous request to comply with the service's rate limit.

    Args:
        service (Service): The service whose bucket governs pacing.

    Raises:
        LimiterServiceError: If ``service`` is not a known rate-limited service.

    Examples:
        >>> from fedfred._internals._rate_limit import _rate_limiter
        >>> _rate_limiter("fred")
        >>> _rate_limiter("unknown")  # doctest: +SKIP
        LimiterServiceError: Unknown rate-limited service: 'unknown'

    Notes:
        Evicts timestamps older than the window and, if the window is full, sleeps until
        the oldest request ages out before recording the new request.

    Warnings:
        Uses ``time.sleep()``, which blocks the calling thread. Do not call from
        asynchronous code; use :func:`_rate_limiter_async` instead.
    """
    spec = _resolve_limiter(service)

    now = time.time()

    _evict_stale(spec.request_times, now)

    if len(spec.request_times) >= spec.max_requests_per_minute:
        sleep_for = _WINDOW_SECONDS - (now - spec.request_times[0])

        if sleep_for > 0:
            time.sleep(sleep_for)

        now = time.time()

        _evict_stale(spec.request_times, now)

    spec.request_times.append(now)


async def _rate_limiter_async(service: Service) -> None:
    """Pace an asynchronous request to comply with the service's rate limit.

    Args:
        service (Service): The service whose bucket governs pacing.

    Raises:
        LimiterServiceError: If ``service`` is not a known rate-limited service.
        RateLimiterConfigurationError: If the bucket's ``max_requests_per_minute`` is less than 1.
        RateLimiterStateError: If the semaphore is in an invalid state.
        LimiterLimitError: If a recomputed semaphore limit is rejected during the update.
        LimiterLoopError: If no event loop is running to acquire the lock or notify waiters.

    Notes:
        Holds the bucket semaphore for the duration, recomputes the per-request spacing
        from the requests remaining and time left in the window, sleeps accordingly, then
        records the request.

    Warnings:
        Must be awaited within a running event loop.
    """
    spec = _resolve_limiter(service)

    async with spec.semaphore:
        requests_left, time_left = await _semaphore_updater(spec)

        if requests_left > 0:
            await asyncio.sleep(time_left / max(1, requests_left))

        else:
            await asyncio.sleep(_WINDOW_SECONDS)

        async with spec.lock:
            spec.request_times.append(time.time())
