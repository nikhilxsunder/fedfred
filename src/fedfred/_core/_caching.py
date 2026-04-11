from cachetools import FIFOCache

__all__ =["_CACHE"]

_CACHE: FIFOCache = FIFOCache(maxsize=256) # fix cache size resolution, refactor resolution logic to settings module.
"""Global cache instance for caching GET request responses."""
