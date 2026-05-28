# filepath: /src/fedfred/_internals/_clients.py
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
"""fedfred._core._clients

This module provides internal helper classes for the fedfred package's client implementations.
"""

from typing import Optional, Any, Union, KeysView, Dict
from types import TracebackType, NotImplementedType
from ..settings import _resolve_api_key, set_api_key
from ._caching import set_cache_maxsize, get_cache_maxsize
from .._core import _hashable_type_converter, _hashable_type_converter_async
from ._transport import _get_request, _cached_get_request, _get_request_async, _cached_get_request_async

# TODO: Fix all docstrings post error design.

__all__ = ["_BaseClient", "_AsyncBaseClient", "_ClientModel"]

class _ClientModel:

    _service_key: str
    _base_url: str
    _service_path: str
    _max_requests_per_minute: int

        # Dunder Methods
    def __init__(self, api_key: Optional[str]=None, caching_enabled: bool=True, cache_size: int=256) -> None:
        """Initialize the Fred class that provides functions which query FRED data.

        Args:
            api_key (str, optional): Your FRED API key.
            caching_enabled (bool, optional): Whether to enable caching for API responses. Defaults to True.
            cache_size (int, optional): The maximum number of items to store in the cache if caching is enabled. Defaults to 256.

        Raises:
            RuntimeError: If no API key can be resolved from the explicit argument, global setting, or environment variable.

        Examples:
            >>> import fedfred as fd
            >>> fd.set_api_key("your_api_key")  # optional global
            >>> fred = fd.Fred()             # uses global/env key

            Or explicitly:

            >>> fred = fd.Fred(api_key="your_api_key")

        Notes:
            API keys can be set globally using `fedfred.set_api_key(...)`, or can be provided explicitly
            when instantiating the `Fred` class. If neither is provided, the class will attempt to
            resolve the API key from the environment variable `FRED_API_KEY`.

        See Also:
            - :func:`fedfred.set_api_key`: Function to set the global FRED API key.
            - :class:`fedfred.GeoFred`: GeoFred client for geospatial data from the FRED Maps API.
        """

        if api_key:
            set_api_key(api_key, service=self._service_key) # TODO: Typing alias logic rewrite origination point.

        if caching_enabled:
            set_cache_maxsize(cache_size)

        self.caching_enabled: bool = caching_enabled
        self.cache_size: int = get_cache_maxsize() if caching_enabled else cache_size

    def __repr__(self) -> str:
        """Developer facing string representation of the Fred class.

        Returns:
            str: A string representation of the Fred class for developers.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> repr(fred)
            Fred(api_key='<set>', caching_enabled=True, cache_size=256)
        """

        try:
            has_key = bool(_resolve_api_key(service=self._service_key)) # TODO: Typing alias logic rewrite origination point.
        except RuntimeError:                        # TODO: Add custom exception for missing API key and catch that instead.
            has_key = False

        auth = "<set>" if has_key else "None"

                                                    # TODO: include size of instance object in the repr string for debugging purposes (can use sys.getsizeof() for that).

        return (
            f"{type(self).__name__}("
            f"api_key={auth}, "
            f"caching_enabled={self.caching_enabled}, "
            f"cache_size={self.cache_size}"
            f")"
        )

    def __str__(self) -> str:
        """Human-readable summary string representation of the Fred class instance's configuration.

        Returns:
            str: A user-friendly string representation of the Fred instance.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> print(fred)
            Fred Instance:
              Service: FRED (https://api.stlouisfed.org/fred)
              API Key: configured
              Cache: enabled (FIFO, maxsize=256)
              Rate Limit: 120 req/min
        """

        try:
            has_key = bool(_resolve_api_key(service=self._service_key)) # TODO: Typing alias logic rewrite origination point.
        except RuntimeError:                           # TODO: Add custom exception for missing API key and catch that instead.
            has_key = False

        auth_line = "configured" if has_key else "not configured"

        cache_line = (
            f"enabled (FIFO, maxsize={self.cache_size})"
            if self.caching_enabled
            else "disabled"
        )

        return (
            f"{type(self).__name__} Instance:\n"
            f"  Service: {type(self).__name__} ({self._base_url}{self._service_path})\n"
            f"  API Key: {auth_line}\n"
            f"  Cache: {cache_line}\n"
            f"  Rate Limit: {self._max_requests_per_minute} req/min\n"
        )

    def __eq__(self, other: object) -> Union[bool, NotImplementedType]:
        """Equality comparison for the Fred class against another object's observable configuration.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
            NotImplemented: If the other object is not an instance of AsyncFred.

        Notes:
            This method compares two Fred instances based on their attributes. If the other object is not a Fred 
            instance, it returns NotImplemented.

        Examples:
            >>> import fedfred as fd
            >>> fred1 = fd.Fred('your_api_key')
            >>> fred2 = fd.Fred('your_api_key')
            >>> fred1 == fred2
            True
        """

        try:
            assert isinstance(other, type(self))
        except AssertionError:
            return NotImplemented

        return (
            self.caching_enabled == other.caching_enabled
            and self.cache_size == other.cache_size
        )

    def __hash__(self) -> int:
        """Hash function for the Fred class.

        Returns:
            int: A hash value for the Fred instance.

        Notes:
            This method generates a hash based on the Fred instance's attributes.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> hashed_fred = hash(fred)
            >>> print(hashed_fred)
            1234567890 # Example hash value
        """

        return hash((type(self).__name__, self.caching_enabled, self.cache_size))

    def __len__(self) -> int:
        """Get the number of cached items in the Fred instance.

        Returns:
            int: The number of cached items in the Fred instance.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> cache_length = len(fred)
            >>> print(cache_length)
            256 # Example length of the cache
        """

        return len(_CACHE) if self.caching_enabled else 0 # TODO: Needs service based cache implementations and cache resolvers.

    def __contains__(self, key: str) -> bool:
        """Check if a specific item exists in the cache.

        Args:
            key (str): The name of the attribute to check.

        Returns:
            bool: True if the attribute exists, False otherwise.

        Notes:
            This method checks for the existence of a key in the cache if caching is enabled.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> print('some_key' in fred)
            True # Example output if 'some_key' exists in the cache
        """

        return self.caching_enabled and key in _CACHE # TODO: Needs service based cache implementations and cache resolvers.

    def __getitem__(self, key: str) -> Any:
        """Get a specific item from the cache.

        Args:
            key (str): The name of the attribute to get.

        Returns:
            Any: The value of the attribute.

        Raises:
            AttributeError: If the key does not exist.

        Notes:
            This method allows access to cached items using the indexing syntax.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred['some_key']
            'some_value'
        """

        if not self.caching_enabled:
            raise KeyError(key)         # TODO: Add custom exception for cache disabled and catch that instead.

        return _CACHE.cache[key] # TODO: Needs service based cache implementations and cache resolvers.

    # Properties
    @property
    def keys(self) -> Optional[KeysView[tuple[Any, ...]]]:
        """List of keys in the cache."""

        return _CACHE.keys() if self.caching_enabled else None # TODO: Needs service based cache implementations and cache resolvers.

class _BaseClient(_ClientModel):

    # Dunder Methods
    def __enter__(self) -> "_BaseClient":
        """Enter the runtime context.

        Returns:
            Fred: The Fred instance itself.

        Notes:
            The Fred client does not currently own per-instance resources requiring explicit cleanup — transport opens and closes httpx.Client per request,
            and the cache and rate-limit buckets are module-global. The context manager exists for ergonomic parity with httpx/requests and as a
            forward-compatible seam for future per-instance connection pooling.

        Examples:
            >>> import fedfred as fd
            >>> with fd.Fred("your_api_key") as fred:
            ...     categories = fred.get_category(125)
        """

        return self

    def __exit__(self, exc_type: Optional[type[BaseException]], exc: Optional[BaseException], tb: Optional[TracebackType]) -> None:
        """Exit the runtime context. No-op.

        Args:
            exc_type: Exception type if one was raised in the with-block.
            exc: Exception instance, if any.
            tb: Traceback, if any.

        Notes:
            Does not clear the cache or rate-limit buckets — those are shared
            across all live Fred and AsyncFred instances. Clearing them here
            would corrupt other clients.
        """

        return None

    # Private Methods
    def _client_get_request(self, endpoint_name: str, data: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        """Helper method to perform a synchronous GET request to the FRED API.

        Args:
            endpoint_name (str): The FRED API endpoint to query.
            data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

        Returns:
            Dict[str, Any]: The JSON response from the FRED API.

        Raises:
            httpx.HTTPError: If the HTTP request fails.

        Notes:
            This method handles rate limiting and caching for synchronous GET requests to the FRED API.

        Warnings:
            Caching is only applied if `cache_mode` is enabled. Ensure that the `data` parameter is hashable for 
            caching to work correctly.
        """

        if self.caching_enabled:
            return _cached_get_request(endpoint_name, _hashable_type_converter(data))

        else:
            return _get_request(endpoint_name, data)

    def _client_post_request(self):

        pass

class _AsyncBaseClient(_ClientModel):

    # Dunder Methods
    async def __aenter__(self) -> "_AsyncBaseClient":
        """Enter the asynchronous runtime context.

        Returns:
            AsyncAlfred: The AsyncAlfred instance itself.

        Notes:
            AsyncAlfred does not currently own per-instance resources requiring explicit cleanup — transport opens and closes httpx.AsyncClient per
            request, and the cache and rate-limit buckets are module-global. The context manager exists for ergonomic parity with httpx and as a
            forward-compatible seam for future per-instance connection pooling.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            ...     async with fd.AsyncAlfred("your_api_key") as fred:
            ...         categories = await fred.get_category(125)
            >>> asyncio.run(main())
        """

        return self

    async def __aexit__(self, exc_type: Optional[type[BaseException]], exc: Optional[BaseException], tb: Optional[TracebackType]) -> None:
        """Exit the asynchronous runtime context. No-op.

        Args:
            exc_type: Exception type if one was raised in the async-with-block.
            exc: Exception instance, if any.
            tb: Traceback, if any.

        Notes:
            Does not clear the cache or rate-limit buckets — those are shared
            across all live Fred and AsyncFred instances.
        """

        return None

    # Private Methods
    async def _client_get_request(self, url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
        """Helper method to perform an asynchronous GET request to the FRED API.

        Args:
            url_endpoint (str): The endpoint URL to send the GET request to.
            data (Dict[str, Optional[Union[str, int]]], optional): The query parameters for the GET request.
            
        Returns:
            Dict[str, Any]: The JSON response from the FRED API.

        Raises:
            ValueError: If the response from the FRED API indicates an error.

        Notes:
            This method handles rate limiting and caching for asynchronous GET requests to the FRED API.

        Warnings:
            Caching is only applied if `cache_mode` is enabled in the parent Fred instance. Ensure that the `data` parameter is hashable for 
            caching to work correctly.
        """

        if self.caching_enabled:
            return await _cached_get_request_async(url_endpoint, await _hashable_type_converter_async(data))

        else:
            return await _get_request_async(url_endpoint, data)

    async def _client_post_request(self):

        pass
