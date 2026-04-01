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
from typing import Tuple, Any
from ..exceptions import (
    LimiterLimitError,
    LimiterReleaseError,
    LimiterLoopError,
    LimiterWakeError,
)

__all__ = [
    "_rate_limiter", "_rate_limiter_async"
]

@dataclass(slots=True)
class AdjustableLimiter:
    """Capacity limiter with runtime-adjustable limit.

    Attributes:
        limit (int): The maximum number of concurrent holders allowed.

    Notes: At most `limit` concurrent holders. `set_limit()` adjusts the cap; existing holders keep their slots.
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
        """

        if self.limit < 1:
            raise LimiterLimitError("limit must be >= 1")
        self._in_use = 0
        self._cond = asyncio.Condition()

    async def __aenter__(self) -> 'AdjustableLimiter':
        """Enter the asynchronous context manager, acquiring a slot.
        
        Returns:
            AdjustableLimiter: The instance of the limiter for use within the context.
        """

        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Exit the asynchronous context manager, releasing the slot.
        
        Args:
            exc_type (Optional[Type[BaseException]]): The exception type, if any.
            exc (Optional[BaseException]): The exception instance, if any.
            tb (Optional[TracebackType]): The traceback, if any.

        Notes:
            This method ensures that the slot is released regardless of whether an exception occurred within the context.
        """

        await self.release()

    # Protected methods
    def _notify(self) -> None:
        """Notify all waiters that the limit has changed.
        
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

        Notes:
            This method notifies all tasks waiting on the condition variable, allowing them to attempt to acquire a slot.
        """

        async with self._cond:
            self._cond.notify_all()

    # Public methods
    def set_limit(self, new_limit: int) -> None:
        """Set a new limit for the semaphore.

        Args:
            new_limit (int): The new limit for the semaphore.
        """

        if new_limit < 1:
            new_limit = 1
        # no await; just update and wake waiters via a task-safe notify
        self.limit = new_limit
        # notifying requires the condition; schedule it
        try:
            asyncio.get_running_loop().call_soon_threadsafe(self._notify)
        except RuntimeError as exc:
            raise LimiterLoopError(
                "set_limit() requires a running event loop to notify waiters."
            ) from exc

    async def acquire(self) -> None:
        """Acquire a slot, waiting if necessary until one is available.
        
        Notes:
            This method waits asynchronously until a slot becomes available, ensuring that the number of concurrent holders does not exceed the limit.
        """

        async with self._cond:
            while self._in_use >= self.limit:
                await self._cond.wait()
            self._in_use += 1

    async def release(self) -> None:
        """Release a slot, notifying any waiters.
        
        Notes:
            This method decreases the count of active holders and notifies all waiting tasks, allowing them to attempt to acquire a slot.
        """

        async with self._cond:
            if self._in_use <= 0:
                raise LimiterReleaseError("release() called too many times")
            self._in_use -= 1
            self._cond.notify_all()

_MAX_REQUESTS_PER_MINUTE: int = 120
_REQUEST_TIMES: deque = deque()
_LOCK: asyncio.Lock = asyncio.Lock()
_SEMAPHORE: AdjustableLimiter = AdjustableLimiter(limit=_MAX_REQUESTS_PER_MINUTE // 10)

async def _semaphore_updater() -> Tuple[Any, float]:
    """Dynamically adjusts the semaphore based on requests left in the minute.

    Returns:
        Tuple[Any, float]: A tuple containing the number of requests left and the time left in seconds.

    Notes:
        This method updates the semaphore limit based on the number of requests made in the last minute, allowing for dynamic rate limiting.

    Warnings:
        This method should be used within an asynchronous context to ensure proper locking and timing.
    """

    async with _LOCK:
        now = time.time()
        while _REQUEST_TIMES and _REQUEST_TIMES[0] < now - 60:
            _REQUEST_TIMES.popleft()
        requests_made = len(_REQUEST_TIMES)
        requests_left = max(0, _MAX_REQUESTS_PER_MINUTE - requests_made)
        time_left = max(1, 60 - (now - (_REQUEST_TIMES[0] if _REQUEST_TIMES else now)))
        new_limit = max(1, min(_MAX_REQUESTS_PER_MINUTE // 10, requests_left // 2))
        _SEMAPHORE.set_limit(new_limit)
        return requests_left, time_left

def _rate_limiter() -> None:
    """Ensures synchronous requests comply with rate limits.

    Notes:
        This method tracks the timestamps of requests and enforces rate limiting by sleeping when the maximum 
        number of requests per minute is reached.

    Warnings:
        This method uses time.sleep(), which blocks the current thread. Avoid using it in asynchronous contexts.
    """

    now = time.time()
    _REQUEST_TIMES.append(now)
    while _REQUEST_TIMES and _REQUEST_TIMES[0] < now - 60:
        _REQUEST_TIMES.popleft()
    if len(_REQUEST_TIMES) >= _MAX_REQUESTS_PER_MINUTE:
        time.sleep(60 - (now - _REQUEST_TIMES[0]))

async def _rate_limiter_async() -> None:
    """Ensures asynchronous requests comply with rate limits.

    Notes:
        This method ensures that API requests adhere to the rate limit by dynamically adjusting the wait time based on the 
        number of requests left and the time remaining in the current minute.

    Warnings:
        This method should be used within an asynchronous context to ensure proper locking and timing.
    """

    async with _SEMAPHORE:
        requests_left, time_left = await _semaphore_updater()
        if requests_left > 0:
            sleep_time = time_left / max(1, requests_left)
            await asyncio.sleep(sleep_time)
        else:
            await asyncio.sleep(60)
        async with _LOCK:
            _REQUEST_TIMES.append(time.time())
