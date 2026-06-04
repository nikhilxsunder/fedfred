# filepath: /src/fedfred/_internals/_caching.py
#
# Copyright (c) 2025-2026 Nikhil Sunder
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
"""fedfred._internals._caching

This module provides adjustable cache abstractions for the fedfred core package.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from threading import RLock
from collections.abc import Hashable, MutableMapping, Iterator
from typing import Generic, TypeVar, ItemsView, KeysView, ValuesView, Tuple, overload
from cachetools import FIFOCache
from ..exceptions import (
    CacheInitializationError,
    CacheResizeError,
    CacheKeyError,
    CacheBackendError,
    CacheSetError,
    CacheDeleteError,
)

__all__ = [
    # Typing Aliases
    "K", "V", "T",
    # Sentinel
    "_MISSING",
    # Cache Abstractions
    "AdjustableFIFOCache",
    # Global Cache Interface
    "set_cache_maxsize", "get_cache_maxsize", 
    "_CACHE",
]

# Typing aliases
K = TypeVar("K", bound=Hashable)
"""Type variable for cache keys, bounded to hashable types."""

V = TypeVar("V")
"""Type variable for cache values."""

T = TypeVar("T")
"""Generic type variable for cache entries."""

_MISSING = object()
"""Sentinel value for missing cache entries."""

# Cache Abstractions
@dataclass(slots=True)
class AdjustableFIFOCache(MutableMapping[K, V], Generic[K, V]):
    """Runtime-adjustable FIFO cache wrapper.

    This class wraps :class:`cachetools.FIFOCache` and provides an explicit, validated API for runtime cache resizing.

    Attributes:
        maxsize (int): Maximum number of entries allowed in the cache.
        cache (FIFOCache): The underlying FIFO cache instance used to store entries.

    Examples:
        >>> # Internal usage
        >>> cache = AdjustableFIFOCache(maxsize=10)
        >>> cache[1] = "a"
        >>> cache[1]
        'a'

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
            CacheInitializationError: If ``maxsize`` is less than 1.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache[1]
            'a'
        """
        if self.maxsize < 1:
            raise CacheInitializationError(
                message="Cache maxsize must be greater than or equal to 1.",
                parameter="maxsize",
                value=self.maxsize,
            )

        self._cache = FIFOCache(maxsize=self.maxsize)
        self._lock = RLock()

    def __iter__(self) -> Iterator[K]:
        """Return an iterator over cache keys in FIFO order.
        
        Returns:
            Iterator[K]: An iterator over the cache keys in FIFO order.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache[2] = "b"
            >>> list(cache)
            [1, 2]
        """

        with self._lock:

            return iter(list(self._cache.keys()))

    def __contains__(self, key: object) -> bool:
        """Return whether a key exists in the cache.
        
        Args:
            key (object): Key to check in the cache.

        Returns:
            bool: True if the key exists in the cache, False otherwise.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> 1 in cache
            True
        """

        with self._lock:
            return key in self._cache

    def __getitem__(self, key: K) -> V:
        """Return the cached value for a key.

        Args:
            key (K): Cache key.

        Returns:
            V: Cached value.

        Raises:
            CacheKeyError: If the key is not present in the cache.
            CacheBackendError: If an unexpected backend error occurs during retrieval.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache[1]
            'a'
        """

        with self._lock:
            try:
                return self._cache[key]
            except KeyError as exc:
                raise CacheKeyError(
                    message="Cache key was not found.",
                    key=key,
                ) from exc
            except Exception as exc:
                raise CacheBackendError(
                    message="Unexpected backend error occurred during cache retrieval.",
                ) from exc

    def __setitem__(self, key: K, value: V) -> None:
        """Store a key-value pair in the cache.

        Args:
            key (K): Cache key.
            value (V): Value to cache.

        Raises:
            CacheSetError: If storing the item in the cache fails.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache[1]
            'a'
        """

        with self._lock:
            try:
                self._cache[key] = value
            except Exception as exc:
                raise CacheSetError(
                    message="Failed to store item in cache.",
                    key=key,
                ) from exc

    def __delitem__(self, key: K) -> None:
        """Delete a key from the cache.

        Args:
            key (K): Cache key.

        Raises:
            CacheKeyError: If the key is not present in the cache.
            CacheDeleteError: If deleting the item from the cache fails.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> del cache[1]
            >>> 1 in cache
            False
        """

        with self._lock:
            try:
                del self._cache[key]
            except KeyError as exc:
                raise CacheKeyError(
                    message="Cache key was not found for deletion.",
                    key=key,
                ) from exc
            except Exception as exc:
                raise CacheDeleteError(
                    message="Failed to delete item from cache.",
                    key=key,
                ) from exc

    def __len__(self) -> int:
        """Return the number of cached entries.
        
        Returns:
            int: Number of entries currently in the cache.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> len(cache)
            1
        """

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

    @overload
    def get(self, key: K, /) -> V | None:
        ...

    @overload
    def get(self, key: K, /, default: V | T) -> V | T:
        ...

    def get(self, key: K, /, default: V | T | None = None) -> V | T | None:
        """Return a cached value if present.

        Args:
            key: Cache key.
            default: Value to return if key is absent.

        Returns:
            Cached value or ``default``.

        Examples:
            >>> cache = AdjustableFIFOCache[int, str](maxsize=10)
            >>> cache[1] = "a"
            >>> cache.get(1)
            'a'
            >>> cache.get(2, default="b")
            'b'
        """

        with self._lock:
            return self._cache.get(key, default)

    @overload
    def pop(self, key: K, /) -> V:
        ...

    @overload
    def pop(self, key: K, /, default: V) -> V:
        ...

    @overload
    def pop(self, key: K, /, default: T) -> V | T:
        ...

    def pop(self, key: K, /, default: object = _MISSING) -> V | object:
        """Remove and return a cached value.

        Args:
            key (K): Cache key.
            default (Optional[V]): Value to return if key is absent.

        Returns:
            Optional[V]: Removed cached value or ``default``.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache.pop(1)
            >>> cache.pop(2, default="b")
            'a'
            'b'
        """
        with self._lock:
            if default is _MISSING:
                return self._cache.pop(key)

            return self._cache.pop(key, default)

    def clear(self) -> None:
        """Remove all cached entries.
        
        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache.clear()
            >>> len(cache)
            0
        """

        with self._lock:
            self._cache.clear()

    def resize(self, new_maxsize: int) -> None:
        """Resize the cache capacity at runtime.

        Args:
            new_maxsize (int): New maximum cache size.

        Raises:
            CacheResizeError: If ``new_maxsize`` is less than 1.

        Notes:
            If the cache is shrunk below the current size, the oldest entries are
            evicted first until the cache fits within the new capacity.
        
        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache.resize(5)
            >>> cache.maxsize
            5
        """

        if new_maxsize < 1:
            raise CacheResizeError(
                message="Cache resize target must be greater than or equal to 1.",
                parameter="new_maxsize",
                value=new_maxsize,
            )

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
        """Return a dynamic view of cache keys.

        Returns:
            KeysView[K]: A dynamic view of the cache keys.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> list(cache.keys())
            [1]
        """

        with self._lock:
            return self._cache.keys()

    def values(self) -> ValuesView[V]:
        """Return a dynamic view of cache values.
        
        Returns:
            ValuesView[V]: A dynamic view of the cache values.
    
        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> list(cache.values())
            ['a']
        """

        with self._lock:
            return self._cache.values()

    def items(self) -> ItemsView[K, V]:
        """Return a dynamic view of cache items.
        
        Returns:
            ItemsView[K, V]: A dynamic view of the cache items.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> list(cache.items())
            [(1, 'a')]
        """

        with self._lock:
            return self._cache.items()

    def snapshot(self) -> dict[K, V]:
        """Return a shallow snapshot of the cache contents.

        Returns:
            dict[K, V]: Snapshot of current cache contents in FIFO order.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache.snapshot()
            {1: 'a'}
        """

        with self._lock:
            return dict(self._cache.items())

_CACHE: AdjustableFIFOCache[Tuple, object] = AdjustableFIFOCache(maxsize=128)
"""Global adjustable FIFO cache instance used for transport caching in the fedfred core package. Initialized with a default maximum size of 128 entries."""

def set_cache_maxsize(maxsize: int) -> None:
    """Set the global transport cache maximum size.

    Args:
        maxsize (int): New cache maximum size.

    Raises:
        CacheResizeError: If ``maxsize`` is less than 1.

    Examples:
        >>> set_cache_maxsize(256)
        >>> get_cache_maxsize()
        256
    """

    _CACHE.resize(new_maxsize=maxsize)

def get_cache_maxsize() -> int:
    """Return the global transport cache maximum size.

    Returns:
        int: Current global cache maximum size.

    Examples:
        >>> set_cache_maxsize(256)
        >>> get_cache_maxsize()
        256
    """

    return _CACHE.maxsize
