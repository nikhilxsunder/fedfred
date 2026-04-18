"""fedfred.exceptions.caching

Exception hierarchy for the caching module.
"""

from dataclasses import dataclass
from typing import Optional, Any

from fedfred.exceptions.base import FedFredError

@dataclass(frozen=True, slots=True)
class CachingError(FedFredError):
    """Base exception for all caching-related errors in fedfred."""

    message: str = "An unspecified caching error occurred."

    def __str__(self) -> str:
        return self.message

@dataclass(frozen=True, slots=True)
class CacheConfigurationError(CachingError):
    """Raised when cache configuration values are invalid."""

    parameter: Optional[str] = None
    value: Optional[Any] = None

    def __str__(self) -> str:
        if self.parameter is not None:
            return (
                f"{self.message} "
                f"(parameter={self.parameter!r}, value={self.value!r})"
            )
        return self.message

@dataclass(frozen=True, slots=True)
class CacheInitializationError(CacheConfigurationError):
    """Raised when the cache cannot be initialized correctly."""

@dataclass(frozen=True, slots=True)
class CacheResizeError(CacheConfigurationError):
    """Raised when a cache resize operation is invalid or fails."""

@dataclass(frozen=True, slots=True)
class CacheOperationError(CachingError):
    """Base exception for cache mutation and operational failures."""

    key: Optional[Any] = None

    def __str__(self) -> str:
        if self.key is not None:
            return f"{self.message} (key={self.key!r})"
        return self.message

@dataclass(frozen=True, slots=True)
class CacheSetError(CacheOperationError):
    """Raised when setting a cache item fails."""

@dataclass(frozen=True, slots=True)
class CacheDeleteError(CacheOperationError):
    """Raised when deleting a cache item fails."""

@dataclass(frozen=True, slots=True)
class CacheClearError(CacheOperationError):
    """Raised when clearing the cache fails."""

@dataclass(frozen=True, slots=True)
class CachePopError(CacheOperationError):
    """Raised when popping a cache item fails."""

@dataclass(frozen=True, slots=True)
class CacheAccessError(CachingError):
    """Base exception for cache lookup and retrieval failures."""

    key: Optional[Any] = None

    def __str__(self) -> str:
        if self.key is not None:
            return f"{self.message} (key={self.key!r})"
        return self.message

@dataclass(frozen=True, slots=True)
class CacheKeyError(CacheAccessError, KeyError):
    """Raised when a requested cache key is not present."""

@dataclass(frozen=True, slots=True)
class CacheBackendError(CachingError):
    """Raised when the underlying cache backend behaves unexpectedly."""

    backend: str = "cachetools.FIFOCache"

    def __str__(self) -> str:
        return f"{self.message} (backend={self.backend!r})"