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

This module provides the concurrency and request-pacing primitives shared by
the synchronous and asynchronous clients. :class:`AdjustableLimiter` is a
capacity limiter whose cap can be changed at runtime; :class:`LimiterSpec`
binds a service to its module-global request-time deque, lock, semaphore, and
per-minute limit. Separate buckets are maintained for the FRED group
(FRED, ALFRED, GeoFRED) and for FRASER, reflecting their different rate limits.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

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

__all__ = [
    "_rate_limiter",
    "_rate_limiter_async",
]


@dataclass(slots=True)
class AdjustableLimiter:
    """Capacity limiter with a runtime-adjustable limit.

    Permits at most ``limit`` concurrent holders. Used as an asynchronous
    context manager (``async with``) or via explicit :meth:`acquire` /
    :meth:`release`. :meth:`set_limit` changes the cap at runtime; holders
    that already own a slot keep it until they release.

    Attributes:
        limit (int): The maximum number of concurrent holders allowed.

    Examples:
        >>> from fedfred._internals._rate_limit import AdjustableLimiter
        >>> limiter = AdjustableLimiter(limit=5)
        >>> limiter.limit
        5

    Notes:
        Instances are constructed at module import to back the FRED and FRASER
        semaphores. GeoFRED and ALFRED share the FRED limiter.
    """

    limit: int
    """The maximum number of concurrent holders allowed."""

    _in_use: int = field(init=False)
    """The current number of holders using the limiter."""

    _cond: asyncio.Condition = field(init=False)
    """Condition variable for managing waiters."""

    _background_tasks: set[asyncio.Task[None]] = field(init=False)
    """Strong references to scheduled wake-up tasks, preventing premature garbage collection."""

    # Dunder methods

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

        Examples:
            >>> from fedfred._internals._rate_limit import AdjustableLimiter  # doctest: +SKIP
            >>> async with AdjustableLimiter(limit=5) as limiter:  # doctest: +SKIP
            ...     ...  # the slot is released automatically on exit

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
            exc_type (Optional[Type[BaseException]]): The exception type, if any.
            exc (Optional[BaseException]): The exception instance, if any.
            tb (Optional[TracebackType]): The traceback, if any.

        Raises:
            LimiterReleaseError: If the limiter is released more times than it was acquired.

        Examples:
            >>> from fedfred._internals._rate_limit import AdjustableLimiter  # doctest: +SKIP
            >>> async with AdjustableLimiter(limit=5) as limiter:  # doctest: +SKIP
            ...     ...

        Notes:
            The slot is released whether or not an exception occurred within the context.
        """
        await self.release()

    # Protected methods
    def _notify(self) -> None:
        """Schedule a task to wake all waiters after a limit change.

        Raises:
            LimiterWakeError: If the wake-up task cannot be scheduled because no event loop is running.

        Examples:
            >>> from fedfred._internals._rate_limit import AdjustableLimiter  # doctest: +SKIP
            >>> limiter = AdjustableLimiter(limit=5)  # doctest: +SKIP
            >>> limiter._notify()  # requires a running event loop  # doctest: +SKIP

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

        Examples:
            >>> from fedfred._internals._rate_limit import AdjustableLimiter  # doctest: +SKIP
            >>> limiter = AdjustableLimiter(limit=5)  # doctest: +SKIP
            >>> await limiter._wake_waiters()  # doctest: +SKIP

        Notes:
            Acquires the condition and calls ``notify_all`` so waiters re-check the limit.
        """
        async with self._cond:
            self._cond.notify_all()

    # Public methods
    def set_limit(self, new_limit: int) -> None:
        """Change the maximum number of concurrent holders at runtime.

        Args:
            new_limit (int): The new maximum number of concurrent holders. Must be >= 1.

        Raises:
            LimiterLimitError: If ``new_limit`` is less than 1.
            LimiterLoopError: If no event loop is running to notify waiters.

        Examples:
            >>> from fedfred._internals._rate_limit import AdjustableLimiter  # doctest: +SKIP
            >>> limiter = AdjustableLimiter(limit=5)  # doctest: +SKIP
            >>> limiter.set_limit(10)  # requires a running event loop  # doctest: +SKIP

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

        Examples:
            >>> from fedfred._internals._rate_limit import AdjustableLimiter  # doctest: +SKIP
            >>> limiter = AdjustableLimiter(limit=5)  # doctest: +SKIP
            >>> await limiter.acquire()  # doctest: +SKIP

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
            LimiterReleaseError: If called when no slot is currently held (more releases than acquires).

        Examples:
            >>> from fedfred._internals._rate_limit import AdjustableLimiter  # doctest: +SKIP
            >>> limiter = AdjustableLimiter(limit=5)  # doctest: +SKIP
            >>> await limiter.acquire()  # doctest: +SKIP
            >>> await limiter.release()  # doctest: +SKIP

        Notes:
            Decrements the holder count and wakes all waiters so they can re-attempt acquisition.
        """
        async with self._cond:
            if self._in_use <= 0:
                raise LimiterReleaseError("release() called too many times")

            self._in_use -= 1

            self._cond.notify_all()


_FRED_MAX_REQUESTS_PER_MINUTE: int = 120
"""Maximum requests per minute for the FRED API, shared by GeoFRED and ALFRED."""

_FRASER_MAX_REQUESTS_PER_MINUTE: int = 30
"""Maximum requests per minute for the FRASER API."""

_FRED_REQUEST_TIMES: deque = deque()
"""Deque tracking timestamps of recent FRED-group requests (FRED, GeoFRED, ALFRED)."""

_FRASER_REQUEST_TIMES: deque = deque()
"""Deque tracking timestamps of recent FRASER requests."""

_FRED_LOCK: asyncio.Lock = asyncio.Lock()
"""Lock synchronizing access to the FRED-group request times and semaphore."""

_FRASER_LOCK: asyncio.Lock = asyncio.Lock()
"""Lock synchronizing access to the FRASER request times and semaphore."""

_FRED_SEMAPHORE: AdjustableLimiter = AdjustableLimiter(limit=_FRED_MAX_REQUESTS_PER_MINUTE // 10)
"""Semaphore limiting concurrent requests to the FRED group."""

_FRASER_SEMAPHORE: AdjustableLimiter = AdjustableLimiter(
    limit=_FRASER_MAX_REQUESTS_PER_MINUTE // 10
)
"""Semaphore limiting concurrent requests to FRASER."""


@dataclass(slots=True)
class LimiterSpec:
    """Resolved rate-limiting configuration for a single service.

    Binds a service to its module-global request-time deque, per-minute limit,
    lock, and semaphore. Constructed via :func:`_resolve_limiter`.

    Attributes:
        service (Service): The target service. ``"fred"``, ``"geofred"``, and ``"alfred"`` share the FRED bucket; ``"fraser"`` uses its own.
        request_times (deque): Deque tracking timestamps of recent requests to the service's bucket.
        max_requests_per_minute (int): The per-minute request ceiling for the service's bucket.
        lock (asyncio.Lock): Lock synchronizing access to the bucket's request times and semaphore.
        semaphore (AdjustableLimiter): Adjustable limiter controlling concurrent access to the bucket.

    Examples:
        >>> from fedfred._internals._rate_limit import LimiterSpec
        >>> LimiterSpec(service="fred").max_requests_per_minute
        120

    Notes:
        GeoFRED and ALFRED resolve to the same bucket as FRED, since they share its rate limits.
    """

    service: Service
    """The target service for which the limiter is resolved."""

    request_times: deque = field(init=False)
    """Deque tracking timestamps of recent requests to the service's bucket."""

    max_requests_per_minute: int = field(init=False)
    """The per-minute request ceiling for the service's bucket."""

    lock: asyncio.Lock = field(init=False)
    """Lock synchronizing access to the bucket's request times and semaphore."""

    semaphore: AdjustableLimiter = field(init=False)
    """Adjustable limiter controlling concurrent access to the bucket."""

    def __post_init__(self) -> None:
        """Resolve the service to its module-global bucket.

        Raises:
            LimiterServiceError: If ``service`` is not a known rate-limited service.

        Examples:
            >>> from fedfred._internals._rate_limit import LimiterSpec
            >>> LimiterSpec(service="fraser").max_requests_per_minute
            30
            >>> LimiterSpec(service="unknown")  # doctest: +SKIP
            LimiterServiceError: Unknown rate-limited service: unknown
        """
        if self.service in {"fred", "geofred", "alfred"}:
            self.request_times = _FRED_REQUEST_TIMES

            self.max_requests_per_minute = _FRED_MAX_REQUESTS_PER_MINUTE

            self.lock = _FRED_LOCK

            self.semaphore = _FRED_SEMAPHORE

        elif self.service == "fraser":
            self.request_times = _FRASER_REQUEST_TIMES

            self.max_requests_per_minute = _FRASER_MAX_REQUESTS_PER_MINUTE

            self.lock = _FRASER_LOCK

            self.semaphore = _FRASER_SEMAPHORE

        else:
            raise LimiterServiceError(f"Unknown rate-limited service: {self.service}")


def _resolve_limiter(service: Service) -> LimiterSpec:
    """Resolve the limiter specification for a service.

    Args:
        service (Service): The service to resolve.

    Returns:
        LimiterSpec: The resolved request times, per-minute limit, lock, and semaphore for the service's bucket.

    Raises:
        LimiterServiceError: If ``service`` is not a known rate-limited service.

    Examples:
        >>> from fedfred._internals._rate_limit import _resolve_limiter
        >>> _resolve_limiter("fred").max_requests_per_minute
        120
        >>> _resolve_limiter("unknown")  # doctest: +SKIP
        LimiterServiceError: Unknown rate-limited service: unknown
    """
    return LimiterSpec(service)


async def _semaphore_updater(
    request_times: deque[float],
    max_requests_per_minute: int,
    lock: asyncio.Lock,
    semaphore: AdjustableLimiter,
) -> tuple[Any, float]:
    """Recompute the semaphore limit from the requests remaining this minute.

    Args:
        request_times (deque[float]): Timestamps of recent requests; entries older than 60 seconds are evicted.
        max_requests_per_minute (int): The per-minute request ceiling for the bucket.
        lock (asyncio.Lock): Lock guarding the request-time deque and semaphore.
        semaphore (AdjustableLimiter): The limiter whose cap is updated in place.

    Returns:
        tuple[Any, float]: The number of requests remaining this minute and the seconds left in the current window.

    Raises:
        RateLimiterConfigurationError: If ``max_requests_per_minute`` is less than 1.
        RateLimiterStateError: If the semaphore limit is below 1, or if the request-time queue is inconsistent with the computed request volume.
        LimiterLimitError: If the recomputed limit is rejected by :meth:`AdjustableLimiter.set_limit`.
        LimiterLoopError: If no event loop is running to notify waiters during the limit update.

    Examples:
        >>> from fedfred._internals._rate_limit import _semaphore_updater, AdjustableLimiter  # doctest: +SKIP
        >>> import asyncio, time  # doctest: +SKIP
        >>> request_times = deque([time.time() - 30, time.time() - 10])  # doctest: +SKIP
        >>> left, remaining = await _semaphore_updater(  # doctest: +SKIP
        ...     request_times, 60, asyncio.Lock(), AdjustableLimiter(limit=10)
        ... )

    Notes:
        Evicts stale timestamps, then narrows the semaphore toward the remaining headroom so
        concurrency tapers as the per-minute budget is consumed.

    Warnings:
        Must be awaited within a running event loop; it acquires ``lock`` and may adjust the semaphore.
    """
    if max_requests_per_minute < 1:
        raise RateLimiterConfigurationError(
            f"max_requests_per_minute must be >= 1, got {max_requests_per_minute}"
        )

    if semaphore.limit < 1:
        raise RateLimiterStateError(
            f"Limiter semaphore is in an invalid state: limit={semaphore.limit}"
        )

    async with lock:
        now = time.time()

        while request_times and request_times[0] < now - 60:
            request_times.popleft()

        requests_made = len(request_times)

        if requests_made > max_requests_per_minute and not request_times:
            raise RateLimiterStateError(
                "Request time queue state is inconsistent with computed request volume."
            )

        requests_left = max(0, max_requests_per_minute - requests_made)

        time_left = max(1, 60 - (now - (request_times[0] if request_times else now)))

        new_limit = max(1, min(max_requests_per_minute // 10, requests_left // 2))

        semaphore.set_limit(new_limit)

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
        LimiterServiceError: Unknown rate-limited service: unknown

    Notes:
        Evicts timestamps older than 60 seconds and, if the window is full, sleeps until the
        oldest request ages out before recording the new request.

    Warnings:
        Uses ``time.sleep()``, which blocks the calling thread. Do not call from asynchronous code;
        use :func:`_rate_limiter_async` instead.
    """
    spec = _resolve_limiter(service)

    now = time.time()

    while spec.request_times and spec.request_times[0] < now - 60:
        spec.request_times.popleft()

    if len(spec.request_times) >= spec.max_requests_per_minute:
        sleep_for = 60 - (now - spec.request_times[0])

        if sleep_for > 0:
            time.sleep(sleep_for)

        now = time.time()

        while spec.request_times and spec.request_times[0] < now - 60:
            spec.request_times.popleft()

    spec.request_times.append(now)


async def _rate_limiter_async(service: Service) -> None:
    """Pace an asynchronous request to comply with the service's rate limit.

    Args:
        service (Service): The service whose bucket governs pacing.

    Raises:
        LimiterServiceError: If ``service`` is not a known rate-limited service.
        RateLimiterConfigurationError: If the bucket's ``max_requests_per_minute`` is less than 1.
        RateLimiterStateError: If the semaphore is in an invalid state or the request-time queue is inconsistent with the computed request volume.
        LimiterLimitError: If a recomputed semaphore limit is rejected during the update.
        LimiterLoopError: If no event loop is running to acquire the lock or notify waiters.

    Examples:
        >>> from fedfred._internals._rate_limit import _rate_limiter_async  # doctest: +SKIP
        >>> import asyncio  # doctest: +SKIP
        >>> await _rate_limiter_async("fred")  # doctest: +SKIP

    Notes:
        Holds the bucket semaphore for the duration, recomputes the per-request spacing from the
        requests remaining and time left in the window, sleeps accordingly, then records the request.

    Warnings:
        Must be awaited within a running event loop.
    """
    spec = _resolve_limiter(service)

    async with spec.semaphore:
        requests_left, time_left = await _semaphore_updater(
            spec.request_times, spec.max_requests_per_minute, spec.lock, spec.semaphore
        )

        if requests_left > 0:
            sleep_time = time_left / max(1, requests_left)

            await asyncio.sleep(sleep_time)

        else:
            await asyncio.sleep(60)

        async with spec.lock:
            spec.request_times.append(time.time())
