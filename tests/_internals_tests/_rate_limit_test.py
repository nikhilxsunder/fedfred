# filepath: /tests/_internals_tests/_rate_limit_test.py
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

import asyncio
from collections import deque

import pytest

import fedfred._internals._rate_limit as rl
from fedfred._internals._rate_limit import (
    _BUCKET_STATE,
    AdjustableLimiter,
    LimiterSpec,
    _evict_stale,
    _rate_limiter,
    _rate_limiter_async,
    _resolve_limiter,
    _semaphore_updater,
)
from fedfred.exceptions import (
    LimiterLimitError,
    LimiterLoopError,
    LimiterReleaseError,
    LimiterServiceError,
    LimiterWakeError,
    RateLimiterConfigurationError,
    RateLimiterStateError,
)


class TestAdjustableLimiter:
    def test_post_init(self):
        lim = AdjustableLimiter(limit=5)
        assert lim.limit == 5
        assert lim._in_use == 0
        assert isinstance(lim._cond, asyncio.Condition)
        assert lim._background_tasks == set()

        with pytest.raises(LimiterLimitError):
            AdjustableLimiter(limit=0)

    @pytest.mark.asyncio
    async def test_aenter(self):
        lim = AdjustableLimiter(limit=2)
        result = await lim.__aenter__()
        assert result is lim  # returns self for `async with ... as`
        assert lim._in_use == 1
        await lim.release()

    @pytest.mark.asyncio
    async def test_aexit(self):
        lim = AdjustableLimiter(limit=2)
        async with lim:
            assert lim._in_use == 1
        assert lim._in_use == 0  # __aexit__ released the slot

    def test_notify(self):
        lim = AdjustableLimiter(limit=2)

        # no running loop -> create_task fails -> LimiterWakeError
        with pytest.raises(LimiterWakeError):
            lim._notify()

        # with a running loop -> schedules and tracks a wake task, then discards it
        async def _inner():
            lim._notify()
            assert len(lim._background_tasks) == 1
            await asyncio.sleep(0.01)
            assert len(lim._background_tasks) == 0  # done-callback discarded it

        asyncio.run(_inner())

    @pytest.mark.asyncio
    async def test_wake_waiters(self):
        lim = AdjustableLimiter(limit=1)
        await lim.acquire()

        # a task blocked in acquire() is released once limit is bumped and we wake
        waiter = asyncio.create_task(lim.acquire())
        await asyncio.sleep(0.01)
        assert not waiter.done()

        lim.limit = 2
        await lim._wake_waiters()
        await asyncio.wait_for(waiter, timeout=1.0)
        assert lim._in_use == 2

        await lim.release()
        await lim.release()

    def test_set_limit(self):
        lim = AdjustableLimiter(limit=5)

        # new_limit < 1 -> LimiterLimitError (before any loop logic)
        with pytest.raises(LimiterLimitError):
            lim.set_limit(0)

        # no running loop -> LimiterLoopError (the cap is still updated first)
        with pytest.raises(LimiterLoopError):
            lim.set_limit(3)
        assert lim.limit == 3

        # with a running loop -> updates the cap and schedules a notify
        async def _inner():
            lim.set_limit(7)
            assert lim.limit == 7
            await asyncio.sleep(0.05)  # flush the scheduled notify/wake tasks

        asyncio.run(_inner())

    @pytest.mark.asyncio
    async def test_acquire(self):
        lim = AdjustableLimiter(limit=1)
        await lim.acquire()
        assert lim._in_use == 1

        # a second acquire blocks until a slot frees up
        task = asyncio.create_task(lim.acquire())
        await asyncio.sleep(0.01)
        assert not task.done()

        await lim.release()
        await asyncio.wait_for(task, timeout=1.0)
        assert lim._in_use == 1
        await lim.release()

    @pytest.mark.asyncio
    async def test_release(self):
        lim = AdjustableLimiter(limit=2)
        await lim.acquire()
        await lim.release()
        assert lim._in_use == 0

        # releasing with nothing held -> LimiterReleaseError
        with pytest.raises(LimiterReleaseError):
            await lim.release()


def test_limiter_spec():
    fred = LimiterSpec(bucket="fred")
    assert fred.max_requests_per_minute == 120
    assert isinstance(fred.lock, asyncio.Lock)
    assert isinstance(fred.request_times, deque) and len(fred.request_times) == 0
    assert fred.semaphore.limit == max(1, 120 // rl._CONCURRENCY_DIVISOR)

    assert LimiterSpec(bucket="fraser").max_requests_per_minute == 30

    # a bucket with no RPM entry -> configuration error
    with pytest.raises(RateLimiterConfigurationError):
        LimiterSpec(bucket="bogus")


def test_evict_stale():
    dq = deque([100.0, 150.0, 200.0])
    _evict_stale(dq, now=210.0, window=60.0)  # threshold 150 -> drop 100 (150 kept: not < 150)
    assert list(dq) == [150.0, 200.0]

    _evict_stale(dq, now=210.0, window=100.0)  # threshold 110 -> nothing stale
    assert list(dq) == [150.0, 200.0]

    empty: deque[float] = deque()
    _evict_stale(empty, now=1.0)  # empty deque is a no-op
    assert list(empty) == []


def test_resolve_limiter():
    # every service in a bucket resolves to the same shared spec
    assert _resolve_limiter("fred") is _BUCKET_STATE["fred"]
    assert _resolve_limiter("geofred") is _BUCKET_STATE["fred"]
    assert _resolve_limiter("alfred") is _BUCKET_STATE["fred"]
    assert _resolve_limiter("fraser") is _BUCKET_STATE["fraser"]

    with pytest.raises(LimiterServiceError):
        _resolve_limiter("unknown")


@pytest.mark.asyncio
async def test_semaphore_updater():
    spec = LimiterSpec(bucket="fred")

    # success: empty window -> all requests remain, full window time left
    requests_left, time_left = await _semaphore_updater(spec)
    assert requests_left == spec.max_requests_per_minute
    assert time_left == rl._WINDOW_SECONDS
    assert spec.semaphore.limit >= 1
    await asyncio.sleep(0.05)  # flush the set_limit notify

    # max_requests_per_minute < 1 -> configuration error
    bad_rpm = LimiterSpec(bucket="fred")
    bad_rpm.max_requests_per_minute = 0
    with pytest.raises(RateLimiterConfigurationError):
        await _semaphore_updater(bad_rpm)

    # semaphore in an invalid state -> state error
    bad_state = LimiterSpec(bucket="fred")
    bad_state.semaphore.limit = 0  # bypass set_limit validation via direct set
    with pytest.raises(RateLimiterStateError):
        await _semaphore_updater(bad_state)


def test_rate_limiter(monkeypatch):
    # unknown service -> LimiterServiceError (real resolver)
    with pytest.raises(LimiterServiceError):
        _rate_limiter("unknown")

    class _FakeTime:
        def __init__(self, t):
            self._t = t
            self.slept: list[float] = []

        def time(self):
            return self._t

        def sleep(self, s):
            self.slept.append(s)

    # window not full -> just records the request, no sleep
    spec = LimiterSpec(bucket="fred")
    spec.max_requests_per_minute = 5
    ft = _FakeTime(1000.0)
    monkeypatch.setattr(rl, "time", ft)
    monkeypatch.setattr(rl, "_resolve_limiter", lambda s: spec)
    _rate_limiter("fred")
    assert list(spec.request_times) == [1000.0]
    assert ft.slept == []

    # window full, oldest is recent -> sleep until it ages out
    spec2 = LimiterSpec(bucket="fred")
    spec2.max_requests_per_minute = 2
    spec2.request_times = deque([1000.0, 1000.0])
    ft2 = _FakeTime(1000.0)
    monkeypatch.setattr(rl, "time", ft2)
    monkeypatch.setattr(rl, "_resolve_limiter", lambda s: spec2)
    _rate_limiter("fred")
    assert ft2.slept == [rl._WINDOW_SECONDS]  # 60 - (1000 - 1000)
    assert list(spec2.request_times)[-1] == 1000.0

    # window full but oldest exactly one window old -> sleep_for == 0 -> no sleep
    spec3 = LimiterSpec(bucket="fred")
    spec3.max_requests_per_minute = 1
    spec3.request_times = deque([940.0])
    ft3 = _FakeTime(1000.0)
    monkeypatch.setattr(rl, "time", ft3)
    monkeypatch.setattr(rl, "_resolve_limiter", lambda s: spec3)
    _rate_limiter("fred")
    assert ft3.slept == []
    assert 1000.0 in spec3.request_times


@pytest.mark.asyncio
async def test_rate_limiter_async(monkeypatch):
    # unknown service -> LimiterServiceError
    with pytest.raises(LimiterServiceError):
        await _rate_limiter_async("unknown")

    spec = LimiterSpec(bucket="fred")
    slept: list[float] = []

    async def _fake_sleep(s):
        slept.append(s)

    monkeypatch.setattr(rl.asyncio, "sleep", _fake_sleep)
    monkeypatch.setattr(rl, "_resolve_limiter", lambda s: spec)

    # requests_left > 0 -> per-request spacing = time_left / requests_left
    async def _upd_pos(sp):
        return (10, 20.0)

    monkeypatch.setattr(rl, "_semaphore_updater", _upd_pos)
    await _rate_limiter_async("fred")
    assert slept == [20.0 / 10]
    assert len(spec.request_times) == 1

    # requests_left == 0 -> sleep the full window
    slept.clear()

    async def _upd_zero(sp):
        return (0, 5.0)

    monkeypatch.setattr(rl, "_semaphore_updater", _upd_zero)
    await _rate_limiter_async("fred")
    assert slept == [rl._WINDOW_SECONDS]
    assert len(spec.request_times) == 2
