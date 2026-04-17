# filepath: /src/fedfred/_core/_caching.py
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
"""fedfred._core._caching

This module provides adjustable cache abstractions for the fedfred core package.
"""

from dataclasses import dataclass, field
from threading import RLock
from collections.abc import Hashable
from typing import Generic, Optional, TypeVar, ItemsView, KeysView, ValuesView, Tuple,
from cachetools import FIFOCache

__all__ = [
    "_CACHE"
]

K = TypeVar("K", bound=Hashable)
"""Type variable for cache keys, bounded to hashable types."""

V = TypeVar("V")
"""Type variable for cache values."""

@dataclass(slots=True)
class AdjustableFIFOCache(Generic[K, V]):
    """Runtime-adjustable FIFO cache wrapper.

    This class wraps :class:`cachetools.FIFOCache` and provides an explicit, validated API for runtime cache resizing.

    Attributes:
        maxsize (int): Maximum number of entries allowed in the cache.
        cache (FIFOCache): The underlying FIFO cache instance used to store entries.

    Notes:
        When the cache is shrunk, the oldest items are evicted first to preserve FIFO semantics.
    """

    maxsize: int
    """Maximum number of entries allowed in the cache."""

    _cache: FIFOCache = field(init=False, repr=False)
    """Underlying FIFO cache instance."""

    _lock: RLock = field(init=False, repr=False)
    """Re-entrant lock protecting cache operations."""

    def __post_init__(self) -> None:
        """Initialize the adjustable FIFO cache.

        Raises:
            ValueError: If ``maxsize`` is less than 1.
        """
        if self.maxsize < 1:
            raise ValueError("maxsize must be >= 1")

        self._cache = FIFOCache(maxsize=self.maxsize)
        self._lock = RLock()

    def __contains__(self, key: object) -> bool:
        """Return whether a key exists in the cache."""
        with self._lock:
            return key in self._cache

    def __getitem__(self, key: K) -> V:
        """Return the cached value for a key.

        Args:
            key (K): Cache key.

        Returns:
            V: Cached value.

        Raises:
            KeyError: If the key is not present.
        """
        with self._lock:
            return self._cache[key]

    def __setitem__(self, key: K, value: V) -> None:
        """Store a key-value pair in the cache.

        Args:
            key (K): Cache key.
            value (V): Value to cache.
        """
        with self._lock:
            self._cache[key] = value

    def __delitem__(self, key: K) -> None:
        """Delete a key from the cache.

        Args:
            key (K): Cache key.

        Raises:
            KeyError: If the key is not present.
        """
        with self._lock:
            del self._cache[key]

    def __len__(self) -> int:
        """Return the number of cached entries."""
        with self._lock:
            return len(self._cache)

    @property
    def cache(self) -> FIFOCache:
        """Return the underlying FIFO cache instance."""
        with self._lock:
            return self._cache

    @property
    def currsize(self) -> float:
        """Return the current number of cached entries."""
        with self._lock:
            return self._cache.currsize

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Return a cached value if present.

        Args:
            key (K): Cache key.
            default (Optional[V]): Value to return if key is absent.

        Returns:
            Optional[V]: Cached value or ``default``.
        """
        with self._lock:
            return self._cache.get(key, default)

    def pop(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Remove and return a cached value.

        Args:
            key (K): Cache key.
            default (Optional[V]): Value to return if key is absent.

        Returns:
            Optional[V]: Removed cached value or ``default``.
        """
        with self._lock:
            return self._cache.pop(key, default)

    def clear(self) -> None:
        """Remove all cached entries."""
        with self._lock:
            self._cache.clear()

    def resize(self, new_maxsize: int) -> None:
        """Resize the cache capacity at runtime.

        Args:
            new_maxsize (int): New maximum cache size.

        Raises:
            ValueError: If ``new_maxsize`` is less than 1.

        Notes:
            If the cache is shrunk below the current size, the oldest entries are
            evicted first until the cache fits within the new capacity.
        """
        if new_maxsize < 1:
            raise ValueError("new_maxsize must be >= 1")

        with self._lock:
            if new_maxsize == self.maxsize:
                return

            # Rebuild deterministically to avoid depending on backend resize behavior.
            items = list(self._cache.items())

            if len(items) > new_maxsize:
                items = items[-new_maxsize:]

            self._cache = FIFOCache(maxsize=new_maxsize)
            for key, value in items:
                self._cache[key] = value

            self.maxsize = new_maxsize

    def keys(self) -> KeysView[K]:
        """Return a dynamic view of cache keys."""
        with self._lock:
            return self._cache.keys()

    def values(self) -> ValuesView[V]:
        """Return a dynamic view of cache values."""
        with self._lock:
            return self._cache.values()

    def items(self) -> ItemsView[K, V]:
        """Return a dynamic view of cache items."""
        with self._lock:
            return self._cache.items()

    def snapshot(self) -> dict[K, V]:
        """Return a shallow snapshot of the cache contents.

        Returns:
            dict[K, V]: Snapshot of current cache contents in FIFO order.
        """
        with self._lock:
            return dict(self._cache.items())

_CACHE: AdjustableFIFOCache[Tuple, object] = AdjustableFIFOCache(maxsize=128)

def _set_cache_maxsize(maxsize: int) -> None:

    """Set the global transport cache maximum size.

    Args:

        maxsize (int): New cache maximum size.

    Raises:

        ValueError: If ``maxsize`` is less than 1.

    """

    _CACHE.resize(new_maxsize=maxsize)

def _get_cache_maxsize() -> int:

    """Return the global transport cache maximum size.

    Returns:

        int: Current global cache maximum size.

    """

    return _CACHE.maxsize
