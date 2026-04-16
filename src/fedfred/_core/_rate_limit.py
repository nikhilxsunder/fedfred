# filepath: /src/fedfred/_core/_rate_limit.py
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
"""fedfred._core._rate_limit

This module provides an adjustable capacity limiter for managing concurrent access to resources. The AdjustableLimiter class allows for 
runtime adjustment of the maximum number of concurrent holders, ensuring that resource usage can be controlled dynamically.
"""

import asyncio
from dataclasses import dataclass, field
import time
from collections import deque
from types import TracebackType
from typing import Tuple, Any, Optional
from ..exceptions import(
    LimiterLimitError,
    LimiterWakeError,
    LimiterLoopError,
    LimiterReleaseError,
    LimiterServiceError,
    RateLimiterConfigurationError,
    RateLimiterStateError,
)

__all__ = [
    "_rate_limiter", "_rate_limiter_async"
]

@dataclass(slots=True)
class AdjustableLimiter:
    """Capacity limiter with runtime-adjustable limit.

    Attributes:
        limit (int): The maximum number of concurrent holders allowed.

    Examples:
        >>> # Internal use
        >>> from ._core import AdjustableLimiter
        >>> limiter = AdjustableLimiter(limit=5)
        >>> _FRED_SEMAPHORE = limiter(max_requests_per_minute=60)

    Notes:
        At most `limit` concurrent holders. `set_limit()` adjusts the cap; existing holders keep their slots.
    """

    limit: int
    """The maximum number of concurrent holders allowed."""

    _in_use: int = field(init=False)
    """The current number of holders using the limiter."""

    _cond: asyncio.Condition = field(init=False)
    """Condition variable for managing waiters."""

    # Dunder methods
    def __post_init__(self) -> None:
        """Initialize the limiter with the specified limit and set up internal state.
        
        Raises:
            LimiterLimitError: If the limit is less than 1.
            LimiterLoopError: If there is no running event loop to notify waiters when the limit is adjusted.

        Examples:
            >>> # Internal use
            >>> from ._core import AdjustableLimiter
            >>> limiter = AdjustableLimiter(limit=5)  # Initializes successfully
            >>> bad_limiter = AdjustableLimiter(limit=0)  # Raises LimiterLimitError
            LimiterLimitError: limit must be >= 1
        """

        if self.limit < 1:
            raise LimiterLimitError("limit must be >= 1")
        self._in_use = 0
        self._cond = asyncio.Condition()

    async def __aenter__(self) -> 'AdjustableLimiter':
        """Enter the asynchronous context manager, acquiring a slot.
        
        Returns:
            AdjustableLimiter: The instance of the limiter for use within the context.

        Raises:
            LimiterLimitError: If the limit is less than 1.
            LimiterLoopError: If there is no running event loop to notify waiters when the limit is adjusted.

        Examples:
            >>> # Internal use
            >>> from ._core import AdjustableLimiter
            >>> async with AdjustableLimiter(limit=5) as limiter:
            ...     # Use limiter within this block
            ...     # Exiting the block will automatically release the slot
        """

        await self.acquire()
        return self

    async def __aexit__(self, exc_type: Optional[type[BaseException]], exc: Optional[BaseException], tb: Optional[TracebackType]) -> None:
        """Exit the asynchronous context manager, releasing the slot.
        
        Args:
            exc_type (Optional[Type[BaseException]]): The exception type, if any.
            exc (Optional[BaseException]): The exception instance, if any.
            tb (Optional[TracebackType]): The traceback, if any.

        Raises:
            LimiterReleaseError: If release() is called more times than acquire(), indicating an imbalance in the number of holders.

        Examples:
            >>> # Internal use
            >>> from ._core import AdjustableLimiter
            >>> async with AdjustableLimiter(limit=5) as limiter:
            ...     # Use limiter within this block
            ...     # Exiting the block will automatically release the slot
            
        Notes:
            This method ensures that the slot is released regardless of whether an exception occurred within the context.
        """

        await self.release()

    # Protected methods
    def _notify(self) -> None:
        """Notify all waiters that the limit has changed.

        Raises:
            LimiterWakeError: If the wake-up task cannot be scheduled due to the absence of a running event loop.

        Examples:
            >>> # Internal use
            >>> from ._core import AdjustableLimiter
            >>> limiter = AdjustableLimiter(limit=5)
            >>> limiter._notify()  # Schedules a wake-up task for waiters
        
        Notes:
            This method is called in a thread-safe manner to wake up any tasks waiting on the condition variable when the limit is adjusted.
        """

        try:
            asyncio.create_task(self._wake_waiters())
        except RuntimeError as exc:
            raise LimiterWakeError(
                "Failed to schedule waiter wake-up task."
            ) from exc

    async def _wake_waiters(self) -> None:
        """Wake tasks waiting on the condition.

        Examples:
            >>> # Internal use
            >>> from ._core import AdjustableLimiter
            >>> limiter = AdjustableLimiter(limit=5)
            >>> await limiter._wake_waiters()  # Notifies all waiters to attempt acquiring a slot

        Notes:
            This method notifies all tasks waiting on the condition variable, allowing them to attempt to acquire a slot.
        """

        async with self._cond:
            self._cond.notify_all()

    # Public methods
    def set_limit(self, new_limit: int) -> None:
        """Set a new limit for the number of concurrent holders.
        
        Args:
            new_limit (int): The new maximum number of concurrent holders allowed.

        Raises:
            LimiterLimitError: If the new limit is less than 1.
            LimiterLoopError: If there is no running event loop to notify waiters.

        Examples:
            >>> # Internal use
            >>> from ._core import AdjustableLimiter
            >>> limiter = AdjustableLimiter(limit=5)
            >>> limiter.set_limit(10)  # Updates the limit to 10 and notifies waiters
            >>> limiter.set_limit(0)  # Raises LimiterLimitError
            LimiterLimitError: new_limit must be >= 1, got 0

        Notes:
            This method allows for dynamic adjustment of the concurrency limit. When the limit is changed, it notifies all waiting 
            tasks so they can attempt to acquire a slot under the new limit. Existing holders are not affected by the change in limit and will keep their slots until they release them.
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
        """Acquire a slot, waiting if necessary until one is available.
        
        Raises:
            LimiterLoopError: If there is no running event loop to wait on the condition variable.
            LimiterLimitError: If the limit is less than 1, indicating an invalid state for acquiring a slot.

        Examples:
            >>> # Internal use
            >>> from ._core import AdjustableLimiter
            >>> limiter = AdjustableLimiter(limit=5)
            >>> await limiter.acquire()  # Acquires a slot, waiting if necessary
            >>> limiter.set_limit(0)  # Updates the limit to 0, making it
            >>> await limiter.acquire()  # Raises LimiterLimitError due to invalid limit

        Notes:
            This method waits asynchronously until a slot becomes available, ensuring that the number of concurrent holders does not exceed the limit.
        """

        async with self._cond:
            while self._in_use >= self.limit:
                await self._cond.wait()
            self._in_use += 1

    async def release(self) -> None:
        """Release a slot, notifying any waiters.

        Raises:
            LimiterReleaseError: If release() is called more times than acquire(), indicating an imbalance in the number of holders.
            LimiterLoopError: If there is no running event loop to notify waiters.

        Examples:
            >>> # Internal use
            >>> from ._core import AdjustableLimiter
            >>> limiter = AdjustableLimiter(limit=5)
            >>> await limiter.acquire()  # Acquires a slot
            >>> await limiter.release()  # Releases the slot, notifying waiters

        Notes:
            This method decreases the count of active holders and notifies all waiting tasks, allowing them to attempt to acquire a slot.
        """

        async with self._cond:
            if self._in_use <= 0:
                raise LimiterReleaseError("release() called too many times")
            self._in_use -= 1
            self._cond.notify_all()

_FRED_MAX_REQUESTS_PER_MINUTE: int = 120
"""Maximum requests per minute for the FRED API, including GeoFRED."""

_FRASER_MAX_REQUESTS_PER_MINUTE: int = 30
"""Maximum requests per minute for the FRASER API."""

_FRED_REQUEST_TIMES: deque = deque()
"""Deque to track timestamps of requests made to the FRED API, including GeoFRED."""

_FRASER_REQUEST_TIMES: deque = deque()
"""Deque to track timestamps of requests made to the FRASER API."""

_FRED_LOCK: asyncio.Lock = asyncio.Lock()
"""Lock for synchronizing access to the FRED request times and semaphore."""

_FRASER_LOCK: asyncio.Lock = asyncio.Lock()
"""Lock for synchronizing access to the FRASER request times and semaphore."""

_FRED_SEMAPHORE: AdjustableLimiter = AdjustableLimiter(limit=_FRED_MAX_REQUESTS_PER_MINUTE // 10)
"""Semaphore for limiting concurrent requests to the FRED API."""

_FRASER_SEMAPHORE: AdjustableLimiter = AdjustableLimiter(limit=_FRASER_MAX_REQUESTS_PER_MINUTE // 10)
"""Semaphore for limiting concurrent requests to the FRASER API."""

@dataclass(slots=True)
class LimiterSpec:
    """Specification for rate limiter configuration based on the target service.
    
    Attributes:
        service (str): The name of the service for which the limiter is being configured. Options include "fred", and "fraser".
        request_times (deque): A deque to track the timestamps of requests made to the service.
        max_requests_per_minute (int): The maximum number of requests allowed per minute for the service.
        lock (asyncio.Lock): A lock to synchronize access to the request times and semaphore for the service.
        semaphore (AdjustableLimiter): An adjustable limiter to control concurrent access to the service based on the rate limits.

    Examples:
        >>> # Internal use
        >>> from ._core import LimiterSpec
        >>> limiter_spec = LimiterSpec(service="fred")  # Initializes with FRED API configuration

    Notes: 
        GeoFRED shares the same rate limits as FRED, so it is included in the "fred" service configuration. The limiter specification is 
        resolved based on the service name, allowing for centralized management of rate-limiting parameters for different services.
    """

    service: str
    """The name of the service for which the limiter is being configured."""

    request_times: deque = field(init=False)
    """A deque to track the timestamps of requests made to the service."""

    max_requests_per_minute: int = field(init=False)
    """The maximum number of requests allowed per minute for the service."""

    lock: asyncio.Lock = field(init=False)
    """A lock to synchronize access to the request times and semaphore for the service."""

    semaphore: AdjustableLimiter = field(init=False)
    """An adjustable limiter to control concurrent access to the service based on the rate limits."""

    def __post_init__(self) -> None:
        """Initialize the limiter specification based on the target service.
        
        Raises:
            LimiterServiceError: If the specified service is unknown or unsupported.
            LimiterLimitError: If the maximum requests per minute for the service is invalid (e.g., less than 1).
            LimiterLoopError: If there is no running event loop to manage timing for rate limiting.

        Examples:
            >>> # Internal use
            >>> from ._core import LimiterSpec
            >>> limiter_spec = LimiterSpec(service="fred")  # Initializes with FRED API configuration
            >>> bad_limiter_spec = LimiterSpec(service="unknown")  # Raises LimiterServiceError
            LimiterServiceError: Unknown rate-limited service: unknown
        """

        if self.service in {"fred", "geofred"}:
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

def _resolve_limiter(service: str) -> LimiterSpec:
    """Resolve the limiter specification for the given service.
    
    Args:
        service (str): The name of the service for which to resolve the limiter specification.

    Raises:
        LimiterServiceError: If the specified service is unknown or unsupported.

    Returns:
        LimiterSpec: The limiter specification containing the request times, maximum requests per minute, lock, and semaphore for the specified service.

    Examples:
        >>> # Internal use
        >>> from ._core import _resolve_limiter
        >>> limiter_spec = _resolve_limiter(service="fred")  # Resolves limiter specification for FRED API
        >>> bad_limiter_spec = _resolve_limiter(service="unknown")  # Raises LimiterServiceError
        LimiterServiceError: Unknown rate-limited service: unknown
    """

    return LimiterSpec(service)

async def _resolve_limiter_async(service: str) -> LimiterSpec:
    """Asynchronously resolve the limiter specification for the given service.
    
    Args:
        service (str): The name of the service for which to resolve the limiter specification.

    Raises:
        LimiterServiceError: If the specified service is unknown or unsupported.
        LimiterLoopError: If there is no running event loop to manage timing for rate limiting.
        LimiterLimitError: If the maximum requests per minute for the service is invalid (e.g., less than 1).

    Returns:
        LimiterSpec: The limiter specification containing the request times, maximum requests per minute, lock, and semaphore for the specified service.
        RateLimiterConfigurationError: If max_requests_per_minute is less than 1, indicating an invalid configuration for rate limiting.
        RateLimiterStateError: If the semaphore is in an invalid state (e.g., limit less than 1) or if the request time queue state is inconsistent with the computed request volume.
        LimiterLoopError: If there is no running event loop to acquire the lock.
        LimiterLimitError: If the semaphore limit is invalid, indicating that it cannot be updated based on the current request volume.

    Examples:
        >>> # Internal use
        >>> from ._core import _resolve_limiter_async
        >>> limiter_spec = await _resolve_limiter_async(service="fred")  # Asynchronously resolves limiter specification for FRED API
        >>> bad_limiter_spec = await _resolve_limiter_async(service="unknown")  # Raises LimiterServiceError
        LimiterServiceError: Unknown rate-limited service: unknown
    """

    return await asyncio.to_thread(_resolve_limiter, service)

async def _semaphore_updater(request_times: deque, max_requests_per_minute: int, lock: asyncio.Lock, semaphore: AdjustableLimiter) -> Tuple[Any, float]:
    """Dynamically adjusts the semaphore based on requests left in the minute.

    Returns:
        Tuple[Any, float]: A tuple containing the number of requests left and the time left in seconds.

    Raises:
        RateLimiterConfigurationError: If max_requests_per_minute is less than 1, indicating an invalid configuration for rate limiting.
        RateLimiterStateError: If the semaphore is in an invalid state (e.g., limit less than 1) or if the request time queue state is inconsistent with the computed request volume.
        LimiterLoopError: If there is no running event loop to acquire the lock.
        LimiterLimitError: If the semaphore limit is invalid, indicating that it cannot be updated based on the current request volume.

    Examples:
        >>> # Internal use
        >>> from ._core import _semaphore_updater
        >>> import asyncio
        >>> request_times = deque([time.time() - 30, time.time() - 10])  # Simulate 2 requests made in the last minute
        >>> lock = asyncio.Lock()
        >>> semaphore = AdjustableLimiter(limit=10)
        >>> max_requests_per_minute = 60
        >>> requests_left, time_left = await _semaphore_updater(request_times, max_requests_per_minute, lock, semaphore)

    Notes:
        This method updates the semaphore limit based on the number of requests made in the last minute, allowing for dynamic rate limiting.

    Warnings:
        This method should be used within an asynchronous context to ensure proper locking and timing.
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

def _rate_limiter(service: str) -> None:
    """Ensures synchronous requests comply with rate limits.

    Raises:
        LimiterServiceError: If the specified service is unknown or unsupported.
        LimiterLimitError: If the rate limiter is configured with an invalid maximum requests per minute value.
        LimiterLoopError: If there is no running event loop to manage timing for rate limiting.

    Examples:
        >>> # Internal use
        >>> from ._core import _rate_limiter
        >>> _rate_limiter(service="fred")  # Ensures compliance with FRED API rate limits
        >>> _rate_limiter(service="unknown")  # Raises LimiterServiceError

    Notes:
        This method tracks the timestamps of requests and enforces rate limiting by sleeping when the maximum 
        number of requests per minute is reached.

    Warnings:
        This method uses time.sleep(), which blocks the current thread. Avoid using it in asynchronous contexts.
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

async def _rate_limiter_async(service: str) -> None:
    """Ensures asynchronous requests comply with rate limits.

    Raises:
        LimiterServiceError: If the specified service is unknown or unsupported.
        LimiterLimitError: If the rate limiter is configured with an invalid maximum requests per minute value.
        RateLimiterConfigurationError: If max_requests_per_minute is less than 1, indicating an invalid configuration for rate limiting.
        RateLimiterStateError: If the semaphore is in an invalid state (e.g., limit less than 1) or if the request time queue state is inconsistent with the computed request volume.
        LimiterLoopError: If there is no running event loop to manage timing for rate limiting or to acquire the lock.
        LimiterLimitError: If the semaphore limit is invalid, indicating that it cannot be updated based on the current request volume.

    Examples:
        >>> # Internal use
        >>> from ._core import _rate_limiter_async
        >>> import asyncio
        >>> await _rate_limiter_async(service="fred")  # Ensures compliance with FRED API rate limits
        >>> await _rate_limiter_async(service="unknown")  # Raises LimiterServiceError

    Notes:
        This method ensures that API requests adhere to the rate limit by dynamically adjusting the wait time based on the 
        number of requests left and the time remaining in the current minute.

    Warnings:
        This method should be used within an asynchronous context to ensure proper locking and timing.
    """

    spec = await _resolve_limiter_async(service)

    async with spec.semaphore:
        requests_left, time_left = await _semaphore_updater(spec.request_times, spec.max_requests_per_minute, spec.lock, spec.semaphore)
        if requests_left > 0:
            sleep_time = time_left / max(1, requests_left)
            await asyncio.sleep(sleep_time)
        else:
            await asyncio.sleep(60)
        async with spec.lock:
            spec.request_times.append(time.time())
