


import asyncio
from dataclasses import dataclass, field
import time
from collections import deque
from typing import Tuple, Any

@dataclass(slots=True)
class AdjustableLimiter:
    """
    Capacity limiter with runtime-adjustable limit.

    Semantics:
      - At most `limit` concurrent holders.
      - `set_limit()` adjusts the cap; existing holders keep their slots.
    """
    limit: int
    _in_use: int = field(init=False)
    _cond: asyncio.Condition = field(init=False)

    def __post_init__(self) -> None:
        """Initialize the limiter with the specified limit and set up internal state."""

        if self.limit < 1:
            raise ValueError("limit must be >= 1")
        self._in_use = 0
        self._cond = asyncio.Condition()

    async def acquire(self) -> None:
        """Acquire a slot, waiting if necessary until one is available."""

        async with self._cond:
            while self._in_use >= self.limit:
                await self._cond.wait()
            self._in_use += 1

    async def release(self) -> None:
        """Release a slot, notifying any waiters."""

        async with self._cond:
            if self._in_use <= 0:
                raise RuntimeError("release() called too many times")
            self._in_use -= 1
            self._cond.notify_all()

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
        asyncio.get_running_loop().call_soon_threadsafe(self._notify)

    async def _wake_waiters(self) -> None:
        """Wake tasks waiting on the condition."""

        async with self._cond:
            self._cond.notify_all()

    def _notify(self) -> None:
        """Notify all waiters that the limit has changed."""

        asyncio.create_task(self._wake_waiters())

    async def __aenter__(self) -> 'AdjustableLimiter':
        """Enter the asynchronous context manager, acquiring a slot."""

        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Exit the asynchronous context manager, releasing the slot."""

        await self.release()

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
