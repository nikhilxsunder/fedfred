# filepath: /src/fedfred/exceptions/internals/caching.py
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
"""Caching-layer exceptions for the fedfred internals package.

The error hierarchy for :mod:`fedfred._internals._caching`. Two families under the
module base :class:`CachingError`: configuration failures
(:class:`CacheConfigurationError` — an invalid ``maxsize``) carrying the offending
parameter and value, and operation failures (:class:`CacheOperationError` — a get,
set, or delete that went wrong) carrying the offending key.

Classes:
    CachingError: Base for any caching failure.
    CacheConfigurationError: A cache was configured with an invalid value.
    CacheInitializationError: Construction-time invalid ``maxsize``.
    CacheResizeError: Resize-time invalid ``maxsize``.
    CacheOperationError: Base for get/set/delete failures.
    CacheKeyError: A key was not present in the cache.
    CacheBackendError: An unexpected backend error during a cache operation.
    CacheSetError: Storing an item failed.
    CacheDeleteError: Deleting an item failed.

See Also:
    - :mod:`fedfred._internals._caching`: Raises these.
    - :class:`fedfred.exceptions.internals.base.InternalsError`: The internals-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import InternalsError

__all__ = [
    "CacheBackendError",
    "CacheConfigurationError",
    "CacheDeleteError",
    "CacheInitializationError",
    "CacheKeyError",
    "CacheOperationError",
    "CachePopError",
    "CacheResizeError",
    "CacheSetError",
    "CachingError",
]


@dataclass(frozen=True, slots=True)
class CachingError(InternalsError):
    """Base class for caching-layer failures.

    The module catch-all for :mod:`fedfred._internals._caching`. Adds no fields;
    inherits the structured payload from :class:`InternalsError`.
    """


@dataclass(frozen=True, slots=True)
class CacheConfigurationError(CachingError):
    """Base class for cache configuration failures.

    Raised when a cache capacity is invalid; carries the offending parameter and
    value.

    Attributes:
        parameter (str): The configuration parameter that was invalid
            (``"maxsize"`` or ``"new_maxsize"``).
        value (object): The invalid value supplied.
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error (inherited).
    """

    parameter: str = ""
    """The configuration parameter that was invalid."""

    value: object = None
    """The invalid value supplied."""

    def __str__(self) -> str:
        """Return the message, suffixed with parameter/value when known.

        Returns:
            str: :attr:`message` with ``(parameter=…, value=…)`` appended when
            :attr:`parameter` is set; the bare :attr:`message` otherwise.
        """
        if self.parameter:
            return f"{self.message} (parameter={self.parameter!r}, value={self.value!r})"
        return self.message


@dataclass(frozen=True, slots=True)
class CacheInitializationError(CacheConfigurationError):
    """Raised when a cache is constructed with a ``maxsize`` less than 1."""


@dataclass(frozen=True, slots=True)
class CacheResizeError(CacheConfigurationError):
    """Raised when a cache is resized to a ``maxsize`` less than 1."""


@dataclass(frozen=True, slots=True)
class CacheOperationError(CachingError):
    """Base class for cache operation (get/set/delete) failures.

    Carries the offending key, shared by every operation subclass.

    Attributes:
        key (object): The cache key involved in the failed operation.
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying backend error, if
            any (inherited).
    """

    key: object = None
    """The cache key involved in the failed operation."""

    def __str__(self) -> str:
        """Return the message, suffixed with the key when known.

        Returns:
            str: :attr:`message` with ``(key=…)`` appended when :attr:`key` is not
            ``None``; the bare :attr:`message` otherwise.
        """
        if self.key is not None:
            return f"{self.message} (key={self.key!r})"
        return self.message


@dataclass(frozen=True, slots=True)
class CacheKeyError(CacheOperationError):
    """Raised when a key is not present in the cache.

    Deliberately does *not* subclass :class:`KeyError`: callers catch
    :class:`CacheKeyError` (or :class:`CacheOperationError` / :class:`CachingError`),
    and keeping it out of the ``KeyError`` MRO removes the translate-ordering hazard
    in the cache's operation guard — a raw backend ``KeyError`` and an
    already-translated ``CacheKeyError`` can no longer be confused.
    """


@dataclass(frozen=True, slots=True)
class CachePopError(CacheOperationError):
    """Raised when popping an item from the cache fails."""


@dataclass(frozen=True, slots=True)
class CacheBackendError(CacheOperationError):
    """Raised on an unexpected backend error during a cache operation."""


@dataclass(frozen=True, slots=True)
class CacheSetError(CacheOperationError):
    """Raised when storing an item in the cache fails."""


@dataclass(frozen=True, slots=True)
class CacheDeleteError(CacheOperationError):
    """Raised when deleting an item from the cache fails."""
