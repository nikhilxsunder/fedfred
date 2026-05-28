# filepath: /src/fedfred/clients/alfred.py
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
"""
"""

from datetime import datetime, date
from typing import Optional, Union, Any, TYPE_CHECKING, Dict, List
from types import TracebackType, NotImplementedType
import pandas as pd
from .._internals import _BaseClient, _AsyncBaseClient
from ..models import Series


if TYPE_CHECKING:
    import polars as pl # pragma: no cover
    import dask.dataframe as dd # pragma: no cover

__all__ = [
    "Alfred",
    "AsyncAlfred"
]

# TODO: Fix all docstrings post error design.

class Alfred(_BaseClient):
    """Client for the Federal Reserve FRED API's ALFRED endpoints.

    The Alfred class contains methods for interacting with the Federal Reserve Bank of St. Louis
    ALFRED® API and provides synchronous endpoints with intuitive handling of vintage dates and data revisions.

    Attributes:
        caching_enabled (bool): Whether caching is enabled for API responses.
        cache_size (int): The maximum number of items to store in the cache if caching is enabled.
        keys (List[str] | None): A list of keys currently stored in the cache if caching is enabled, otherwise None.

    Args:
        api_key (str, optional): Your FRED API key. Can also be set globally.
        caching_enabled (bool, optional): Whether caching is enabled for API responses. Defaults to True.
        cache_size (int, optional): The maximum number of items to store in the cache if caching is enabled. Defaults to 256.
    """

    # Public Methods
    def get_series_vintage_dates(self, series_id: str, realtime_start: Optional[Union[str, datetime, date]]=None,
                                 realtime_end: Optional[Union[str, datetime, date]]=None, limit: Optional[int]=None,
                                 offset: Optional[int]=None, sort_order: Optional[str]=None):
        """Get the vintage dates for an ALFRED series.

        Returns the dates on which new releases or revisions of a series became
        available — the answer to "when was this series revised?". The result is a
        :class:`fedfred.VintageDates` object that behaves like a sequence of
        ``datetime.date`` and renders as a compact summary in Jupyter.

        By default FRED returns the full vintage history (real-time window
        1776-07-04 to 9999-12-31); pass ``realtime_start``/``realtime_end`` to
        restrict the window.

        Args:
            series_id (str): The ID for the FRED series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results. Used for pagination.
            sort_order (str, optional): Sort order of results. Options: 'asc' or 'desc'.

        Returns:
            VintageDates: A notebook-friendly sequence of vintage dates for the series.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> alfred = fd.Alfred('your_api_key')
            >>> vintages = alfred.get_series_vintage_dates('GDPC1')
            >>> vintages[-1]
            datetime.date(2024, 3, 28)

        See Also:
            - :class:`fedfred.VintageDates`: The returned sequence object.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
        """

        endpoint_name = 'get_series_vintagedates'

        data: Dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        pass

    def get_series_info_as_of_date(self,):
        pass

    def get_series_observations_first_release(self,):

        pass

    def get_series_observations_latest_release(self,):

        pass

    def get_series_observations_as_of_date(self,):
        pass

    def get_series_observations_all_releases(self,):
        pass

    def get_series_observations_vintage_matrix(self,):
        pass

    def get_series_observations_revisions(self,):
        pass

    def get_series_observations_new_and_revised(self,):
        pass

    def get_series_observations(self,):
        pass

class AsyncAlfred:

    # Dunder Methods
    def __init__(self, api_key: str, caching_enabled: bool = True, cache_size: int = 256) -> None:
        """Initialize the AsyncFred class with an API key and optional caching.

        Args:
            api_key (str, optional): Your FRED API key.
            caching_enabled (bool, optional): Whether to enable caching for API responses. Defaults to True.
            cache_size (int, optional): The maximum number of items to store in the cache if caching is enabled. Defaults to 256.

        Raises:
            RuntimeError: If no API key can be resolved from the explicit argument, global setting, or environment variable.

        Notes:
            API keys can be set globally using `fedfred.set_api_key(...)`, or can be provided explicitly
            when instantiating the `Fred` class. If neither is provided, the class will attempt to
            resolve the API key from the environment variable `FRED_API_KEY`.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async_fred = fd.AsyncFred(api_key='your_api_key')

        See Also:
            - :class:`fedfred.AsyncGeoFred`: The main asynchronous client for the FRED Maps API.
            - :func:`fedfred.set_api_key`: Function to set the global FRED API key.
        """

        if api_key:
            set_api_key(api_key, service="alfred")

        if caching_enabled:
            set_cache_maxsize(cache_size)

        self.caching_enabled: bool = caching_enabled
        self.cache_size: int = get_cache_maxsize() if caching_enabled else cache_size

    def __repr__(self) -> str:
        """Developer facing string representation of the Fred class.

        Returns:
            str: A string representation of the AsyncFred class for developers.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async_fred = fd.AsyncFred('your_api_key')
            >>> print(repr(async_fred))
            AsyncFred(api_key='<set>', caching_enabled=True, cache_size=256)
        """

        try:
            has_key = bool(_resolve_api_key(service="alfred"))
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
        """Human-readable summary string representation of the AsyncFred class instance's configuration.

        Returns:
            str: A user-friendly string representation of the AsyncFred class.

        Examples:
            >>> import fedfred as fd
            >>> async_fred = fd.AsyncFred('your_api_key')
            >>> print(async_fred)
            AsyncFred Instance:
              Service: FRED (https://api.stlouisfed.org/fred/)
              API Key: configured
              Cache: enabled (FIFO, maxsize=256)
              Rate Limit: 120 req/min
        """

        try:
            has_key = bool(_resolve_api_key(service="alfred"))
        except RuntimeError:
            has_key = False

        auth_line = "configured" if has_key else "not configured"

        cache_line = (
            f"enabled (FIFO, maxsize={self.cache_size})"
            if self.caching_enabled
            else "disabled"
        )

        return (
            f"{type(self).__name__} Instance:\n"
            f"  Service: ALFRED ({_ST_LOUIS_FED_BASE_URL}{_FRED_PATH})\n"
            f"  API Key: {auth_line}\n"
            f"  Cache: {cache_line}\n"
            f"  Rate Limit: {_FRED_MAX_REQUESTS_PER_MINUTE} req/min\n"
        )

    def __eq__(self, other: object) -> Union[bool, NotImplementedType]:
        """Equality comparison for the AsyncFred class against another object's observable configuration.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
            NotImplemented: If the other object is not an instance of AsyncFred.

        Notes:
            This method compares two AsyncFred instances based on their attributes. If the other object is not an AsyncFred 
            instance, it returns NotImplemented.

        Examples:
            >>> import fedfred as fd
            >>> async_fred1 = fd.AsyncFred('your_api_key')
            >>> async_fred2 = fd.AsyncFred('your_api_key')
            >>> print(async_fred1 == async_fred2)
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
        """Hash function for the AsyncFred Class.

        Returns:
            int: A hash value for the AsyncFred instance.

        Notes:
            This method generates a hash based on the AsyncFred instance's attributes.

        Examples:
            >>> import fedfred as fd
            >>> async_fred = fd.AsyncFred('your_api_key')
            >>> hashed_async_fred = hash(async_fred)
            >>> print(hashed_async_fred)
            1234567890 # Example hash value
        """

        return hash((type(self).__name__, self.caching_enabled, self.cache_size))

    def __len__(self) -> int:
        """Get the number of cached items in the AsyncFred instance.

        Returns:
            int: The number of cached items in the AsyncFred instance.

        Examples:
            >>> import fedfred as fd
            >>> async_fred = fd.AsyncFred('your_api_key')
            >>> cache_length = len(async_fred)
            >>> print(cache_length)
            256 # Example length of the cache
        """

        return len(_CACHE) if self.caching_enabled else 0

    def __contains__(self, key: str) -> bool:
        """Check if a specific item exists in the cache.

        Args:
            key (str): The name of the attribute to check.

        Returns:
            bool: True if the attribute exists, False otherwise.

        Notes:
            This method checks for the existence of a key in the cache of the AsyncFred instance if caching is enabled for the parent Fred instance.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> async_fred = fred.AsyncFred
            >>> print('some_key' in async_fred)
            True # Example output if 'some_key' exists in the cache
        """

        return self.caching_enabled and key in _CACHE

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
            >>> async_fred = fred.AsyncFred
            >>> value = async_fred['some_key']
            >>> print(value)
            'some_value'
        """

        if not self.caching_enabled:
            raise KeyError(key)         # TODO: Add custom exception for cache disabled and catch that instead.

        return _CACHE.cache[key]

    async def __aenter__(self) -> "AsyncAlfred":
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

    # Properties
    @property
    def keys(self):
        """List of keys in the cache."""

        return _CACHE.keys() if self.caching_enabled else None

    # Public Methods
    async def get_series_vintage_dates(self, series_id: str, realtime_start: Optional[Union[str, datetime, date]]=None,
                                       realtime_end: Optional[Union[str, datetime, date]]=None, limit: Optional[int]=None,
                                       offset: Optional[int]=None, sort_order: Optional[str]=None) -> VintageDates:
        """Asynchronously get the vintage dates for an ALFRED series.

        Args:
            series_id (str): The ID for the FRED series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results. Used for pagination.
            sort_order (str, optional): Sort order of results. Options: 'asc' or 'desc'.

        Returns:
            VintageDates: A notebook-friendly sequence of vintage dates for the series.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            ...     alfred = fd.AsyncAlfred('your_api_key')
            ...     vintages = await alfred.get_series_vintage_dates('GDPC1')
            ...     print(vintages[-1])
            >>> asyncio.run(main())
            2024-03-28

        See Also:
            - :class:`fedfred.VintageDates`: The returned sequence object.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
        """

        endpoint_name = 'get_series_vintagedates'

        data: Dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await VintageDates.to_object_async(response, series_id=series_id)

    async def get_series_info_as_of_date(self,):
        pass

    async def get_series_observations_first_release(self,):

        pass

    async def get_series_observations_latest_release(self,):

        pass

    async def get_series_observations_as_of_date(self,):
        pass

    async def get_series_observations_all_releases(self,):
        pass

    async def get_series_observations_vintage_matrix(self,):
        pass

    async def get_series_observations_revisions(self,):
        pass

    async def get_series_observations_new_and_revised(self,):
        pass

    async def get_series_observations(self,):
        pass