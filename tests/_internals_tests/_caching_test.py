# filepath: /tests/_internals_tests/_caching_test.py
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

import pytest
from cachetools import FIFOCache

from fedfred._internals._caching import (
    _CACHE,
    AdjustableFIFOCache,
    _retrieve_cache_instance,
    get_cache_maxsize,
    set_cache_maxsize,
)
from fedfred.exceptions import (
    CacheBackendError,
    CacheInitializationError,
    CachePopError,
    CacheResizeError,
    CachingError,
)


class TestAdjustableFIFOCache:

    def test_post_init(self):
        c = AdjustableFIFOCache(maxsize=10)
        assert c.maxsize == 10
        assert isinstance(c._cache, FIFOCache)
        assert len(c) == 0

        # maxsize < 1 -> CacheInitializationError (raised directly, not via _guard)
        with pytest.raises(CacheInitializationError) as exc:
            AdjustableFIFOCache(maxsize=0)
        assert exc.value.parameter == "maxsize"
        assert exc.value.value == 0

    def test_iter(self):
        c = AdjustableFIFOCache(maxsize=10)
        c[1] = "a"
        c[2] = "b"
        c[3] = "c"
        assert list(iter(c)) == [1, 2, 3]        # FIFO order over a snapshot

    def test_contains(self):
        c = AdjustableFIFOCache(maxsize=10)
        c[1] = "a"
        assert 1 in c
        assert 99 not in c

    def test_getitem(self):
        c = AdjustableFIFOCache(maxsize=10)
        c[1] = "a"
        assert c[1] == "a"
        # a miss now raises a *plain* KeyError (not a typed CachingError)
        with pytest.raises(KeyError) as exc:
            _ = c[99]
        assert not isinstance(exc.value, CachingError)

    def test_setitem(self):
        c = AdjustableFIFOCache(maxsize=2)
        c["x"] = 1
        assert c["x"] == 1
        # storing beyond capacity evicts the oldest entry (FIFO)
        c["y"] = 2
        c["z"] = 3
        assert list(c.keys()) == ["y", "z"]

    def test_delitem(self):
        c = AdjustableFIFOCache(maxsize=10)
        c[1] = "a"
        del c[1]
        assert 1 not in c
        # deleting a missing key raises a plain KeyError
        with pytest.raises(KeyError) as exc:
            del c[99]
        assert not isinstance(exc.value, CachingError)

    def test_len(self):
        c = AdjustableFIFOCache(maxsize=10)
        assert len(c) == 0
        c[1] = "a"
        c[2] = "b"
        assert len(c) == 2

    def test_cache(self):
        c = AdjustableFIFOCache(maxsize=10)
        assert isinstance(c.cache, FIFOCache)
        assert c.cache is c._cache

    def test_currsize(self):
        c = AdjustableFIFOCache(maxsize=10)
        assert c.currsize == 0
        c[1] = "a"
        c[2] = "b"
        assert c.currsize == 2

    def test_guard(self):
        c = AdjustableFIFOCache(maxsize=10)

        # non-KeyError backend failure -> translated to the supplied error_cls
        with pytest.raises(CacheBackendError):
            with c._guard(CacheBackendError, "backend boom"):
                raise ValueError("x")

        # KeyError passes through untranslated (MutableMapping contract)
        with pytest.raises(KeyError) as exc:
            with c._guard(CacheBackendError, "backend boom"):
                raise KeyError("k")
        assert not isinstance(exc.value, CachingError)

        # the error_cls is honored per call site
        with pytest.raises(CachePopError):
            with c._guard(CachePopError, "pop boom"):
                raise RuntimeError("y")

    def test_get(self):
        c = AdjustableFIFOCache(maxsize=10)
        c[1] = "a"
        assert c.get(1) == "a"
        assert c.get(2) is None                  # default default
        assert c.get(2, "b") == "b"              # explicit default

    def test_pop(self):
        c = AdjustableFIFOCache(maxsize=10)
        c[1] = "a"
        assert c.pop(1) == "a"
        assert 1 not in c                        # removed
        assert c.pop(2, "b") == "b"              # miss + default -> default
        with pytest.raises(KeyError):            # miss + no default -> plain KeyError
            c.pop(99)

    def test_clear(self):
        c = AdjustableFIFOCache(maxsize=10)
        c[1] = "a"
        c[2] = "b"
        c.clear()
        assert len(c) == 0

    def test_resize(self):
        c = AdjustableFIFOCache(maxsize=3)
        c[1], c[2], c[3] = "a", "b", "c"

        # grow: contents preserved, maxsize updated
        c.resize(5)
        assert c.maxsize == 5
        assert list(c.keys()) == [1, 2, 3]

        # shrink: oldest evicted first, FIFO order preserved
        c.resize(2)
        assert c.maxsize == 2
        assert list(c.keys()) == [2, 3]

        # same-size resize is a no-op (early return)
        c.resize(2)
        assert c.maxsize == 2
        assert list(c.keys()) == [2, 3]

        # < 1 -> CacheResizeError (checked before the no-op path)
        with pytest.raises(CacheResizeError) as exc:
            c.resize(0)
        assert exc.value.parameter == "new_maxsize"
        assert exc.value.value == 0

    def test_keys(self):
        c = AdjustableFIFOCache(maxsize=10)
        c[1] = "a"
        c[2] = "b"
        assert list(c.keys()) == [1, 2]

    def test_values(self):
        c = AdjustableFIFOCache(maxsize=10)
        c[1] = "a"
        c[2] = "b"
        assert list(c.values()) == ["a", "b"]

    def test_items(self):
        c = AdjustableFIFOCache(maxsize=10)
        c[1] = "a"
        c[2] = "b"
        assert list(c.items()) == [(1, "a"), (2, "b")]

    def test_snapshot(self):
        c = AdjustableFIFOCache(maxsize=10)
        c[1] = "a"
        c[2] = "b"
        snap = c.snapshot()
        assert snap == {1: "a", 2: "b"}
        # snapshot is a detached copy
        snap[3] = "c"
        assert 3 not in c


def test_set_cache_maxsize():
    original = get_cache_maxsize()
    try:
        set_cache_maxsize(256)
        assert _CACHE.maxsize == 256
        # invalid target propagates from the underlying resize
        with pytest.raises(CacheResizeError):
            set_cache_maxsize(0)
    finally:
        set_cache_maxsize(original)          # restore global state

def test_get_cache_maxsize():
    original = get_cache_maxsize()
    try:
        set_cache_maxsize(256)
        assert get_cache_maxsize() == 256
    finally:
        set_cache_maxsize(original)

def test_retrieve_cache_instance():
    assert _retrieve_cache_instance() is _CACHE
