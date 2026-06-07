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
"""Thread-safe, runtime-adjustable caching for the fedfred core package.

This module provides :class:`AdjustableFIFOCache`, a ``MutableMapping`` wrapper
around :class:`cachetools.FIFOCache` whose capacity can be resized at runtime
under an internal re-entrant lock, and the module-global ``_CACHE`` instance
that backs transport-layer request caching. The :func:`set_cache_maxsize` and
:func:`get_cache_maxsize` helpers expose the global cache's capacity as the
public, ergonomic surface; :func:`_retrieve_cache_instance` returns the
instance itself for internal use.
"""

from __future__ import annotations

from collections.abc import ItemsView, Iterator, KeysView, MutableMapping, ValuesView
from dataclasses import dataclass, field
from threading import RLock
from typing import TypeVar, overload

from cachetools import FIFOCache

from ..exceptions import (
    CacheBackendError,
    CacheDeleteError,
    CacheInitializationError,
    CacheKeyError,
    CacheResizeError,
    CacheSetError,
)

__all__ = [
    "AdjustableFIFOCache",
    "_retrieve_cache_instance",
    "get_cache_maxsize",
    "set_cache_maxsize",
]

# Typing aliases
T = TypeVar("T")
"""Generic type variable for caller-supplied default values."""

_MISSING = object()
"""Sentinel distinguishing "no default supplied" from an explicit ``None`` default."""

# Cache Abstractions
@dataclass(slots=True)
class AdjustableFIFOCache[K, V](MutableMapping[K, V]):
    """Thread-safe FIFO cache with a runtime-adjustable capacity.

    Wraps :class:`cachetools.FIFOCache` behind the full ``MutableMapping``
    protocol, adding an explicit, validated :meth:`resize` for changing the
    capacity at runtime. All operations are guarded by an internal re-entrant
    lock, so a single instance may be shared across threads.

    Attributes:
        maxsize (int): Maximum number of entries allowed in the cache.
        cache (FIFOCache): The underlying FIFO cache instance (read-only property).

    Examples:
        >>> cache = AdjustableFIFOCache(maxsize=10)
        >>> cache[1] = "a"
        >>> cache[1]
        'a'

    Notes:
        When the cache is shrunk, the oldest entries are evicted first to
        preserve FIFO semantics. ``resize`` rebuilds the backing cache
        deterministically rather than relying on the backend's own resize.
    """

    maxsize: int
    """Maximum number of entries allowed in the cache."""

    _cache: FIFOCache = field(init=False, repr=False)
    """Underlying FIFO cache instance."""

    _lock: RLock = field(init=False, repr=False)
    """Re-entrant lock protecting all cache operations."""

    def __post_init__(self) -> None:
        """Validate ``maxsize`` and initialize the backing cache and lock.

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
        """Return an iterator over the cache keys in FIFO order.

        Returns:
            Iterator[K]: Iterator over the cache keys, oldest first.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache[2] = "b"
            >>> list(cache)
            [1, 2]

        Notes:
            Iterates over a snapshot of the keys taken under the lock, so the
            iterator is safe against concurrent mutation of the cache.
        """
        with self._lock:

            return iter(list(self._cache.keys()))

    def __contains__(self, key: object) -> bool:
        """Return whether a key is present in the cache.

        Args:
            key (object): Key to test for membership.

        Returns:
            bool: ``True`` if the key is present, otherwise ``False``.

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
            V: The cached value.

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
        """Store a key-value pair, evicting the oldest entry if at capacity.

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
        """The underlying FIFO cache instance.

        Returns:
            FIFOCache: The wrapped cache. Intended for inspection; mutating it
            directly bypasses this wrapper's locking and validation.
        """
        with self._lock:
            return self._cache

    @property
    def currsize(self) -> float:
        """The current size of the cache.

        Returns:
            float: The current total size as reported by the backend (the entry
            count, since each entry has unit size).
        """
        with self._lock:
            return self._cache.currsize

    @overload
    def get(self, key: K, /) -> V | None:
        ...

    @overload
    def get(self, key: K, /, default: V | T) -> V | T:
        ...

    def get(self, key: K, /, default: V | T | None = None) -> V | T | None:
        """Return a cached value if present, otherwise a default.

        Args:
            key (K): Cache key.
            default (V | T | None, optional): Value to return if the key is absent. Defaults to ``None``.

        Returns:
            V | T | None: The cached value, or ``default`` if the key is absent.

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
        """Remove a key and return its value, or a default if absent.

        Args:
            key (K): Cache key.
            default (V | T, optional): Value to return if the key is absent. If
                omitted, a missing key raises :class:`KeyError`.

        Returns:
            V | T: The removed value, or ``default`` if the key was absent.

        Raises:
            KeyError: If the key is absent and no ``default`` is supplied.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache.pop(1)
            'a'
            >>> cache.pop(2, default="b")
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
        """Change the cache capacity at runtime.

        Args:
            new_maxsize (int): New maximum number of entries. Must be >= 1.

        Raises:
            CacheResizeError: If ``new_maxsize`` is less than 1.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache.resize(5)
            >>> cache.maxsize
            5

        Notes:
            If the cache currently holds more than ``new_maxsize`` entries, the
            oldest entries are evicted first until it fits. The backing cache is
            rebuilt deterministically rather than relying on backend resize
            behavior, preserving FIFO order across the resize.
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
        """Return a view of the cache keys.

        Returns:
            KeysView[K]: A view of the cache keys.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> list(cache.keys())
            [1]
        """
        with self._lock:
            return self._cache.keys()

    def values(self) -> ValuesView[V]:
        """Return a view of the cache values.

        Returns:
            ValuesView[V]: A view of the cache values.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> list(cache.values())
            ['a']
        """
        with self._lock:
            return self._cache.values()

    def items(self) -> ItemsView[K, V]:
        """Return a view of the cache items.

        Returns:
            ItemsView[K, V]: A view of the cache (key, value) pairs.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> list(cache.items())
            [(1, 'a')]
        """
        with self._lock:
            return self._cache.items()

    def snapshot(self) -> dict[K, V]:
        """Return a shallow copy of the cache contents.

        Returns:
            dict[K, V]: A new dict of the current contents in FIFO order. Safe to
            iterate without holding the lock, unlike the live ``keys``/``values``/
            ``items`` views.

        Examples:
            >>> cache = AdjustableFIFOCache(maxsize=10)
            >>> cache[1] = "a"
            >>> cache.snapshot()
            {1: 'a'}
        """
        with self._lock:
            return dict(self._cache.items())

_CACHE: AdjustableFIFOCache[tuple, object] = AdjustableFIFOCache(maxsize=128)
"""Module-global cache backing transport-layer request caching, defaulting to 128 entries."""

def set_cache_maxsize(maxsize: int) -> None:
    """Set the global transport cache's maximum size.

    Args:
        maxsize (int): New maximum number of entries. Must be >= 1.

    Raises:
        CacheResizeError: If ``maxsize`` is less than 1.

    Examples:
        >>> set_cache_maxsize(256)
        >>> get_cache_maxsize()
        256
    """
    _CACHE.resize(new_maxsize=maxsize)

def get_cache_maxsize() -> int:
    """Return the global transport cache's maximum size.

    Returns:
        int: The current global cache capacity.

    Examples:
        >>> set_cache_maxsize(256)
        >>> get_cache_maxsize()
        256
    """
    return _CACHE.maxsize

def _retrieve_cache_instance() -> AdjustableFIFOCache[tuple, object]:
    """Return the module-global cache instance.

    Returns:
        AdjustableFIFOCache[tuple, object]: The global cache backing transport caching.
    """
    return _CACHE
