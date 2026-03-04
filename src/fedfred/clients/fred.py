# filepath: /src/fedfred/clients/fred.py
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
"""fedfred.clients.fred

This module defines the Fred client for interacting with the Federal Reserve FRED/ALFRED API.

It provides synchronous and asynchronous methods to access various endpoints of the FRED API, including 
categories, series, tags, releases, and more. The client includes features such as automatic parameter conversion,
unified response objects, rate limiting, retries, and typed results.

Classes:
    Fred: Client for the Federal Reserve FRED/ALFRED API.
    AsyncFred: Asynchronous client for the Federal Reserve FRED/ALFRED API.
    GeoFred: Client for FRED Maps API endpoints.
    AsyncGeoFred: Asynchronous client for FRED Maps API endpoints.

Examples:
    >>> import fedfred as fd
    >>> fred = fd.Fred('your_api_key')
    >>> category = fred.get_category(125)
    >>> print(category[0].name)
    'Trade Balance'

Notes:
    API keys can be set globally using `fedfred.set_api_key`, or can be provided explicitly
    when instantiating the `Fred` class. If neither is provided, the class will attempt to
    resolve the API key from the environment variable `FRED_API_KEY`.

Warnings:
    Make sure to handle your API key securely and avoid hardcoding it in your source code.

See Also:
    :class:`fedfred.set_api_key`: Function to set the global FRED API key.
    :class:`fedfred.Helpers`: Helper functions for parameter validation and conversion.

References:
    fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
    Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
"""

import asyncio
from datetime import datetime
import time
from collections import deque
from typing import TYPE_CHECKING, Optional, Dict, Union, List, Tuple, Any
import httpx
import pandas as pd
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type
from cachetools import FIFOCache, cached
from asyncache import cached as async_cached
from ..__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__
from ..settings import _resolve_api_key, set_api_key
from .._core import (
    # Converters
    _dict_type_converter, _dict_type_converter_async,
    _hashable_type_converter, _hashable_type_converter_async,
    _datetime_converter, _datetime_converter_async,
    _liststring_converter, _liststring_converter_async,
    _vintage_dates_type_converter, _vintage_dates_type_converter_async,
    _pandas_dataframe_converter, _pandas_dataframe_converter_async,
    _polars_dataframe_converter, _polars_dataframe_converter_async,
    _dask_dataframe_converter, _dask_dataframe_converter_async,
    _datetime_hh_mm_converter, _datetime_hh_mm_converter_async,
    # Validators
    _fred_parameter_validator, _fred_parameter_validator_async,
)
from ..models import BulkRelease, Category, Series, Tag, Release, ReleaseDate, Source, Element, VintageDate

if TYPE_CHECKING:
    import polars as pl # pragma: no cover
    import dask.dataframe as dd # pragma: no cover

class Fred:
    """Client for the Federal Reserve FRED/ALFRED API.
    
    The Fred class contains methods for interacting with the Federal Reserve Bank of St. Louis
    FRED® API and provides synchronous endpoints with automatic parameter conversion, unified 
    response objects, rate limiting, retries, and typed results.

    Attributes:
        base_url (str): The base URL for the FRED API.
        api_key (str): Your FRED API key.
        cache_mode (bool): Whether caching is enabled for API responses.
        cache_size (int): The maximum number of items to store in the cache if caching is enabled.
        cache (FIFOCache): The cache object for storing API responses.
        max_requests_per_minute (int): The maximum number of requests allowed per minute.
        request_times (deque): A deque to track the timestamps of recent requests for rate limiting.
        lock (asyncio.Lock): An asyncio lock for synchronizing access to shared resources.
        semaphore (asyncio.Semaphore): An asyncio semaphore for limiting concurrent requests.
        keys (List[str]): List of keys in the cache.
        GeoFred (GeoFred): Attached instance for FRED Maps API endpoints.
        AsyncFred (AsyncFred): Attached instance for asynchronous FRED API endpoints.

    Args:
        api_key (str, optional): Your FRED API key.
        cache_mode (bool, optional): Whether to enable caching for API responses. Defaults to False.
        cache_size (int, optional): The maximum number of items to store in the cache if caching is enabled. Defaults to 256.

    Raises:
        RuntimeError: If no API key can be resolved from the explicit argument, global setting, or environment variable.

    Notes:
        API keys can be set globally using `fedfred.set_api_key(...)`, or can be provided explicitly
        when instantiating the `Fred` class. If neither is provided, the class will attempt to
        resolve the API key from the environment variable `FRED_API_KEY`.
    
    Examples:
        >>> import fedfred as fd
        >>> fd.set_api_key("your_api_key") # optional global
        >>> fred = fd.Fred() # uses global/env key
        >>> # or explicitly:
        >>> fred = fd.Fred(api_key="your_api_key")

    Warnings: 
        Make sure to handle your API key securely and avoid hardcoding it in your source code.

    See Also:
        - :func:`fedfred.set_api_key`: Function to set the global FRED API key.
        - :class:`fedfred.Helpers`: Helper functions for parameter validation and conversion.
    """

    # Dunder Methods
    def __init__(self, api_key: Optional[str]=None, cache_mode: bool=True, cache_size: int=256) -> None:
        """Initialize the Fred class that provides functions which query FRED data.

        Args:
            api_key (str, optional): Your FRED API key.
            cache_mode (bool, optional): Whether to enable caching for API responses. Defaults to True.
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
            - :class:`fedfred.Helpers`: Helper functions for parameter validation and conversion.
        """

        self.base_url: str = 'https://api.stlouisfed.org/fred'

        if api_key:
            set_api_key(api_key, service="fred")

        self.__api_key: Optional[str] = _resolve_api_key(service="fred")
        self.cache_mode: bool = cache_mode
        self.cache_size: int = cache_size
        self.cache: FIFOCache = FIFOCache(maxsize=cache_size)
        self.max_requests_per_minute: int = 120
        self.request_times: deque = deque()
        self.lock: asyncio.Lock = asyncio.Lock()
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(self.max_requests_per_minute // 10)

    def __repr__(self) -> str:
        """String representation of the Fred class.

        Returns:
            str: A string representation of the Fred class.

        Notes:
            This method provides a concise representation of the Fred instance.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> repr(fred)
            'Fred(api_key='your_api_key', cache_mode=True, cache_size=256)'
        """

        return f"Fred(api_key='{self.api_key}', cache_mode={self.cache_mode}, cache_size={self.cache_size})"

    def __str__(self) -> str:
        """String representation of the Fred class.

        Returns:
            str: A user-friendly string representation of the Fred instance.

        Notes: 
            This method provides a detailed summary of the Fred instance's configuration.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> print(fred)
            'Fred Instance:'
            '  Base URL: https://api.stlouisfed.org/fred'
            '  API Key: ****your_api_key'
            '  Cache Mode: Enabled'
            '  Cache Size: 256 items'
            '  Max Requests per Minute: 120'
        """

        return (
            f"Fred Instance:\n"
            f"  Base URL: {self.base_url}\n"
            f"  API Key: {'***' + self.api_key[-4:] if self.api_key else 'Not Provided'}\n"
            f"  Cache Mode: {'Enabled' if self.cache_mode else 'Disabled'}\n"
            f"  Cache Size: {self.cache_size}\n"
            f"  Max Requests Per Minute: {self.max_requests_per_minute}"
        )

    def __eq__(self, other: object) -> bool:
        """Equality comparison for the Fred class.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.

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

        if not isinstance(other, Fred):
            return NotImplemented
        return (
            self.api_key == other.api_key and
            self.cache_mode == other.cache_mode and
            self.cache_size == other.cache_size
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
            >>> hash(fred)
            1234567890 # Example hash value
        """

        return hash((self.api_key, self.cache_mode, self.cache_size))

    def __del__(self) -> None:
        """Destructor for the Fred class. Clears the cache when the instance is deleted.

        Notes:
            This method ensures that the cache is cleared when the Fred instance is deleted.

        Warnings:
            Avoid relying on destructors for critical resource management, as their execution timing 
            is not guaranteed.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> del fred
            >>> # Cache is cleared when fred is deleted
        """

        if hasattr(self, "cache"):
            self.cache.clear()

    def __len__(self) -> int:
        """Get the number of cached items in the Fred instance.

        Returns:
            int: The number of cached items in the Fred instance.

        Notes:
            This method returns the size of the cache if caching is enabled.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> print(len(fred))
            256 # Example length of the cache
        """

        return len(self.cache) if self.cache_mode else 0

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

        return key in self.cache.keys() if self.cache_mode else False

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

        if key in self.cache.keys():
            return self.cache[key]
        else:
            raise AttributeError(f"'{key}' not found in cache.")

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a specific item in the cache.

        Args:
            key (str): The name of the attribute to set.
            value (Any): The value to set.

        Notes:
            This method allows setting cached items using the indexing syntax.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred['some_key'] = 'some_value'
            >>> print(fred['some_key'])
            'some_value'
        """

        self.cache[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete a specific item from the cache.

        Args:
            key (str): The name of the attribute to delete.

        Raises:
            AttributeError: If the key does not exist.

        Notes:
            This method allows deletion of cached items using the indexing syntax.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> del fred['some_key']
            >>> print('some_key' in fred)
            False
        """

        if key in self.cache.keys():
            del self.cache[key]
        else:
            raise AttributeError(f"'{key}' not found in cache.")

    def __call__(self) -> str:
        """Call the Fred instance to get a summary of its configuration.

        Returns:
            str: A string representation of the Fred instance's configuration.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> print(fred())
            'Fred Instance:'
            '  Base URL: https://api.stlouisfed.org/fred'
            '  Cache Mode: Enabled'
            '  Cache Size: 256 items'
            '  API Key: ****your_api_key'
        """
        return (
            f"Fred Instance:\n"
            f"  Base URL: {self.base_url}\n"
            f"  Cache Mode: {'Enabled' if self.cache_mode else 'Disabled'}\n"
            f"  Cache Size: {len(self.cache)} items\n"
            f"  API Key: {'****' + self.api_key[-4:] if self.api_key else 'Not Set'}\n"
        )

    # Properties
    @property
    def keys(self) -> List[str]:
        """List of keys in the cache."""

        return list(self.cache.keys()) if self.cache_mode else []

    # Private Methods
    def __rate_limited(self) -> None:
        """Ensures synchronous requests comply with rate limits.

        Notes:
            This method tracks the timestamps of requests and enforces rate limiting by sleeping when the maximum 
            number of requests per minute is reached.

        Warnings:
            This method uses time.sleep(), which blocks the current thread. Avoid using it in asynchronous contexts.
        """

        now = time.time()
        self.request_times.append(now)
        while self.request_times and self.request_times[0] < now - 60:
            self.request_times.popleft()
        if len(self.request_times) >= self.max_requests_per_minute:
            time.sleep(60 - (now - self.request_times[0]))

    def __fred_get_request(self, url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
        """Helper method to perform a synchronous GET request to the FRED API.

        Args:
            url_endpoint (str): The FRED API endpoint to query.
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

        @retry(wait=wait_fixed(1),
               stop=stop_after_attempt(3),
               retry=retry_if_exception_type(httpx.HTTPError),
               reraise=True,)
        def __get_request(url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
            """Perform a GET request without caching.

            Args:
                url_endpoint (str): The FRED API endpoint to query.
                data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

            Returns:
                Dict[str, Any]: The JSON response from the FRED API.

            Raises:
                httpx.HTTPError: If the HTTP request fails.

            Notes:
                This method handles rate limiting and caching for synchronous GET requests to the FRED API.
            """

            self.__rate_limited()
            params = {
                **(data or {}),
                'api_key': self.api_key,
                'file_type': 'json'
            }
            with httpx.Client() as client:
                try:
                    if "/v2/" in url_endpoint:
                        headers = {
                            'Authorization': f'Bearer {self.api_key}'
                        }
                        params = {
                            **(data or {}),
                            'format': 'json'
                        }
                        response = client.get(self.base_url + url_endpoint, headers=headers, params=params, timeout=10)
                        response.raise_for_status()
                        return response.json()
                    else:
                        response = client.get(self.base_url + url_endpoint, params=params, timeout=10)
                        response.raise_for_status()
                    return response.json()
                except httpx.HTTPError as e:
                    raise ValueError(f"HTTP Error occurred: {e}") from e

        @cached(cache=self.cache)
        def __cached_get_request(url_endpoint: str, hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]=None) -> Dict[str, Any]:
            """Perform a GET request with caching.

            Args:
                url_endpoint (str): The FRED API endpoint to query.
                hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]], optional): The hashable representation of the data. Defaults to None.

            Returns:
                Dict[str, Any]: The JSON response from the FRED API.

            Raises:
                httpx.HTTPError: If the HTTP request fails.
            """

            return __get_request(url_endpoint, _dict_type_converter(hashable_data))

        if data:
            _fred_parameter_validator(data)
        if self.cache_mode:
            return __cached_get_request(url_endpoint, _hashable_type_converter(data))
        else:
            return __get_request(url_endpoint, data)

    # Public Methods
    ## Categories
    def get_category(self, category_id: int) -> List[Category]:
        """Get a FRED Category

        Retrieve information about a specific category from the FRED API.

        Args:
            category_id (int): The ID of the category to retrieve.

        Returns:
            List[Category]: A list containing the requested Category objects.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> category = fred.get_category(125)
            >>> print(category[0].name)
            'Trade Balance'

        See Also:
            - :class:`fedfred.Category`: The Category object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_category.html
        """

        url_endpoint = '/category'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id,
        }
        response = self.__fred_get_request(url_endpoint, data)
        categories = Category.to_object(response, client=self)
        return categories

    def get_category_children(self, category_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                              realtime_end: Optional[Union[str, datetime]]=None) -> List[Category]:
        """Get a FRED Category's Child Categories

        Get the child categories for a specified category ID from the FRED API.

        Args:
            category_id (int): The ID for the category whose children are to be retrieved.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            List[Category]: A list of child Category objects.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = Fred('your_api_key')
            >>> children = fred.get_category_children(13)
            >>> for child in children:
            >>>     print(child.name)
            'Exports'
            'Imports'
            'Income Payments & Receipts'
            'U.S. International Finance'

        See Also:
            - :class:`fedfred.Category`: The Category object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category_children.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_category_children.html
        """

        url_endpoint = '/category/children'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id,
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        categories = Category.to_object(response, client=self)
        return categories

    def get_category_related(self, category_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                             realtime_end: Optional[Union[str, datetime]]=None) -> List[Category]:
        """Get a FRED Category's Related Categories

        Get related categories for a given category ID from the FRED API.

        Args:
            category_id (int): The ID for the category.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            List[Category]: A list of related Category objects.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = Fred('your_api_key')
            >>> related = fred.get_category_related(32073)
            >>> for category in related:
            >>>     print(category.name)
            'Arkansas'
            'Illinois'
            'Indiana'
            'Kentucky'
            'Mississippi'
            'Missouri'
            'Tennessee'

        See Also:
            - :class:`fedfred.Category`: The Category object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category_related.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_category_related.html
        """

        url_endpoint = '/category/related'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id,
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        categories = Category.to_object(response, client=self)
        return categories

    def get_category_series(self, category_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                            realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                            offset: Optional[int]=None, order_by: Optional[str]=None,
                            sort_order: Optional[str]=None, filter_variable: Optional[str]=None,
                            filter_value: Optional[str]=None, tag_names: Optional[Union[str, list[str]]]=None,
                            exclude_tag_names: Optional[Union[str, list[str]]]=None) -> List[Series]:
        """Get a FRED Category's FRED Series

        Get the series info for all series in a category from the FRED API.

        Args:
            category_id (int): The ID for a category.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 'last_updated', 'observation_start', 'observation_end', 'popularity', 'group_popularity'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'.
            filter_variable (str, optional): The attribute to filter results by. Options are 'frequency', 'units', 'seasonal_adjustment'.
            filter_value (str, optional): The value of the filter_variable to filter results by.
            tag_names (str | list, optional): A semicolon-separated list of tag names to filter results by.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude results by.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> series = fred.get_category_series(125)
            >>> for s in series:
            >>>     print(s.frequency)
            'Quarterly'
            'Annual'
            'Quarterly'...

        See Also:
            - :class:`fedfred.Series`: The Series object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category_series.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_category_series.html
        """

        if not isinstance(category_id, int) or category_id < 0:
            raise ValueError("category_id must be a non-negative integer")
        url_endpoint = '/category/series'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id,
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        if filter_variable:
            data['filter_variable'] = filter_variable
        if filter_value:
            data['filter_value'] = filter_value
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = _liststring_converter(tag_names)
            data['tag_names'] = tag_names
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = _liststring_converter(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        response = self.__fred_get_request(url_endpoint, data)
        seriess = Series.to_object(response, client=self)
        return seriess

    def get_category_tags(self, category_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                          realtime_end: Optional[Union[str, datetime]]=None, tag_names: Optional[Union[str, list[str]]]=None,
                          tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                          limit: Optional[int]=None, offset: Optional[int]=None,
                          order_by: Optional[int]=None, sort_order: Optional[str]=None) -> List[Tag]:
        """Get a FRED Category's Tags

        Get the all the tags for a category from the FRED API.

        Args:
            category_id (int): The ID for a category.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names to filter tags by.
            tag_group_id (int, optional): A tag group ID to filter tags by type.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name'. Default is 'series_count'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc', 'desc'. Default is 'desc'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> tags = fred.get_category_tags(125)
            >>> for tag in tags:
            >>>     print(tag.notes)
            'U.S. Department of Commerce: Bureau of Economic Analysis'
            'Country Level'
            'United States of America'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_category_tags.html
        """

        url_endpoint = '/category/tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = _liststring_converter(tag_names)
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        tags = Tag.to_object(response, client=self)
        return tags

    def get_category_related_tags(self, category_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                                  realtime_end: Optional[Union[str, datetime]]=None, tag_names: Optional[Union[str, list[str]]]=None,
                                  exclude_tag_names: Optional[Union[str, list[str]]]=None,
                                  tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                                  limit: Optional[int]=None, offset: Optional[int]=None,
                                  order_by: Optional[int]=None, sort_order: Optional[int]=None) -> List[Tag]:
        """Get a FRED Category's Related Tags

        Retrieve all tags related to a specified category from the FRED API.

        Args:
            category_id (int): The ID for the category.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to include.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude.
            tag_group_id (int, optional): The ID for a tag group.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
            sort_order (str, optional): Sort order, either 'asc' or 'desc'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> tags = fred.get_category_related_tags(125)
            >>> for tag in tags:
            >>>     print(tag.name)
            'balance'
            'bea'
            'nation'
            'usa'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category_related_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_category_related_tags.html
        """

        url_endpoint = '/category/related_tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = _liststring_converter(tag_names)
            data['tag_names'] = tag_names
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = _liststring_converter(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        tags = Tag.to_object(response, client=self)
        return tags

    ## Releases
    def get_releases(self, realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str, datetime]]=None,
                     limit: Optional[int]=None, offset: Optional[int]=None,
                     order_by: Optional[str]=None, sort_order: Optional[str]=None) -> List[Release]:
        """Get FRED releases

        Get all economic data releases from the FRED API.

        Args:
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is None.
            offset (int, optional): The offset for the results. Default is None.
            order_by (str, optional): Order results by values such as 'release_id', 'name', 'press_release', 'realtime_start', 'realtime_end'. Default is None.
            sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order. Default is None.

        Returns:
            List[Releases]: If multiple Releases are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> releases = fred.get_releases()
            >>> for release in releases:
            >>>     print(release.name)
            'Advance Monthly Sales for Retail and Food Services'
            'Consumer Price Index'
            'Employment Cost Index'...

        See Also:
            - :class:`fedfred.Release`: The Release object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/releases.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_releases.html
        """

        url_endpoint = '/releases'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        releases = Release.to_object(response, client=self)
        return releases

    def get_releases_dates(self, realtime_start: Optional[Union[str, datetime]]=None,
                           realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                           offset: Optional[int]=None, order_by: Optional[str]=None,
                           sort_order: Optional[str]=None,
                           include_releases_dates_with_no_data: Optional[bool]=None) -> List[ReleaseDate]:
        """Get FRED releases dates

        Get all release dates for economic data releases from the FRED API.

        Args:
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is None.
            offset (int, optional): The offset for the results. Default is None.
            order_by (str, optional): Order results by values. Options include 'release_id', 'release_name', 'release_date', 'realtime_start', 'realtime_end'. Default is None.
            sort_order (str, optional): Sort order of results. Options include 'asc' (ascending) or 'desc' (descending). Default is None.
            include_releases_dates_with_no_data (bool, optional): Whether to include release dates with no data. Default is None.

        Returns:
            List[ReleaseDate]: If multiple release dates are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> release_dates = fred.get_releases_dates()
            >>> for release_date in release_dates:
            >>>     print(release_date.release_name)
            'Advance Monthly Sales for Retail and Food Services'
            'Failures and Assistance Transactions'
            'Manufacturing and Trade Inventories and Sales'...

        See Also:
            - :class:`fedfred.ReleaseDate`: The ReleaseDate object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/releases_dates.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_releases_dates.html
        """

        url_endpoint = '/releases/dates'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        if include_releases_dates_with_no_data:
            data['include_releases_dates_with_no_data'] = include_releases_dates_with_no_data
        response = self.__fred_get_request(url_endpoint, data)
        return ReleaseDate.to_object(response)

    def get_release(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                    realtime_end: Optional[Union[str, datetime]]=None) -> List[Release]:
        """Get a FRED release

        Get the release for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            List[Release]: If multiple releases are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> release = fred.get_release(53)
            >>> print(release[0].name)
            'Gross Domestic Product'

        See Also:
            - :class:`fedfred.Release`: The Release object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_release.html
        """

        url_endpoint = '/release/'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        releases = Release.to_object(response, client=self)
        return releases

    def get_release_dates(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                          realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                          offset: Optional[int]=None, sort_order: Optional[str]=None,
                          include_releases_dates_with_no_data: Optional[bool]=None) -> List[ReleaseDate]:
        """Get FRED release dates

        Get the release dates for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            sort_order (str, optional): The order of the results. Possible values are 'asc' or 'desc'.
            include_releases_dates_with_no_data (bool, optional): Whether to include release dates with no data.

        Returns:
            List[ReleaseDate]: If multiple release dates are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> release_dates = fred.get_release_dates(82)
            >>> for release_date in release_dates:
            >>>     print(release_date.date)
            '1997-02-10'
            '1998-02-10'
            '1999-02-04'...

        See Also:
            - :class:`fedfred.ReleaseDate`: The ReleaseDate object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_dates.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_release_dates.html
        """

        url_endpoint = '/release/dates'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        if include_releases_dates_with_no_data:
            data['include_releases_dates_with_no_data'] = include_releases_dates_with_no_data
        response = self.__fred_get_request(url_endpoint, data)
        return ReleaseDate.to_object(response)

    def get_release_series(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                           realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                           offset: Optional[int]=None, sort_order: Optional[str]=None,
                           filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                           exclude_tag_names: Optional[Union[str, list[str]]]=None) -> List[Series]:
        """Get FRED release series

        Get the series in a release.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            sort_order (str, optional): Order results by values. Options are 'asc' or 'desc'.
            filter_variable (str, optional): The attribute to filter results by.
            filter_value (str, optional): The value of the filter variable.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> series = fred.get_release_series(51)
            >>> for s in series:
            >>>     print(s.id)
            'BOMTVLM133S'
            'BOMVGMM133S'
            'BOMVJMM133S'...

        See Also:
            - :class:`fedfred.Series`: The Series object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_series.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_release_series.html
        """

        if not isinstance(release_id, int) or release_id < 0:
            raise ValueError("release_id must be a non-negative integer")
        url_endpoint = '/release/series'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id,
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        if filter_variable:
            data['filter_variable'] = filter_variable
        if filter_value:
            data['filter_value'] = filter_value
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = _liststring_converter(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        response = self.__fred_get_request(url_endpoint, data)
        seriess = Series.to_object(response, client=self)
        return seriess

    def get_release_sources(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                            realtime_end: Optional[Union[str, datetime]]=None) -> List[Source]:
        """Get FRED release sources

        Retrieve the sources for a specified release from the FRED API.

        Args:
            release_id (int): The ID of the release for which to retrieve sources.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str| datetime, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.

        Returns:
            List[Series]: If multiple sources are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> sources = fred.get_release_sources(51)
            >>> for source in sources:
            >>>     print(source.name)
                'U.S. Department of Commerce: Bureau of Economic Analysis'
                'U.S. Department of Commerce: Census Bureau'

        See Also:
            - :class:`fedfred.Source`: The Source object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_sources.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_release_sources.html
        """

        url_endpoint = '/release/sources'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        sources = Source.to_object(response, client=self)
        return sources

    def get_release_tags(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                         realtime_end: Optional[Union[str, datetime]]=None, tag_names: Optional[Union[str, list[str]]]=None,
                         tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                         limit: Optional[int]=None, offset: Optional[int]=None,
                         order_by: Optional[str]=None) -> List[Tag]:
        """Get FRED release tags

        Get the release tags for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names.
            tag_group_id (int, optional): The ID for a tag group.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'. Default is 'series_count'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> tags = fred.get_release_tags(86)
            >>> for tag in tags:
            >>>     print(tag.name)
            'commercial paper'
            'frb'
            'nation'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_release_tags.html
        """

        url_endpoint = '/release/tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = _liststring_converter(tag_names)
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        response = self.__fred_get_request(url_endpoint, data)
        tags = Tag.to_object(response, client=self)
        return tags

    def get_release_related_tags(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                                 realtime_end: Optional[Union[str, datetime]]=None, tag_names: Optional[Union[str, list[str]]]=None,
                                 exclude_tag_names: Optional[Union[str, list[str]]]=None, tag_group_id: Optional[str]=None,
                                 search_text: Optional[str]=None, limit: Optional[int]=None,
                                 offset: Optional[int]=None, order_by: Optional[str]=None,
                                 sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED release related tags

        Get release related tags for a given series search text.

        Args:
            series_search_text (str, optional): The text to match against economic data series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names to match.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude results by.
            tag_group_id (str, optional): A tag group id to filter tags by type.
            tag_search_text (str, optional): The text to match against tags.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options: 'asc', 'desc'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> tags = fred.get_release_related_tags('86')
            >>> for tag in tags:
            >>>     print(tag.name)
            'commercial paper'
            'frb'
            'nation'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_related_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_release_related_tags.html
        """

        url_endpoint = '/release/related_tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = _liststring_converter(tag_names)
            data['tag_names'] = tag_names
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = _liststring_converter(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        tags = Tag.to_object(response, client=self)
        return tags

    def get_release_tables(self, release_id: int, element_id: Optional[int]=None,
                           include_observation_values: Optional[bool]=None,
                           observation_date: Optional[Union[str, datetime]]=None) -> List[Element]:
        """Get FRED release tables

        Fetches release tables from the FRED API.

        Args:
            release_id (int): The ID for the release.
            element_id (int, optional): The ID for the element. Defaults to None.
            include_observation_values (bool, optional): Whether to include observation values. Defaults to None.
            observation_date (str | datetime, optional): The observation date in YYYY-MM-DD string format. Defaults to None.

        Returns:
            List[Element]: If multiple elements are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> elements = fred.get_release_tables(53)
            >>> for element in elements:
            >>>     print(element.series_id)
            'DGDSRL1A225NBEA'
            'DDURRL1A225NBEA'
            'DNDGRL1A225NBEA'...

        See Also:
            - :class:`fedfred.Element`: Class representing FRED elements.

        References:
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_release_tables.html
            - FRED API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_tables.html
        """

        url_endpoint = '/release/tables'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if element_id:
            data['element_id'] = element_id
        if include_observation_values:
            data['include_observation_values'] = include_observation_values
        if observation_date:
            if isinstance(observation_date, datetime):
                observation_date = _datetime_converter(observation_date)
            data['observation_date'] = observation_date
        response = self.__fred_get_request(url_endpoint, data)
        return Element.to_object(response, client=self)

    def get_release_observations(self, release_id: int, limit: Optional[int]=None) -> List[BulkRelease]:
        """Get FRED release observations in bulk

        Fetches release observations in bulk from the FRED API.

        Args:
            release_id (int): The ID for the release.
            limit (int, optional): The maximum number of results to return per request.

        Returns:
            List[BulkRelease]: If multiple bulk release observations are returned.

        Raises:
            ValueError: If the API request fails or returns an error.
            
        Example:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> bulk_releases = fred.get_release_observations(53)
            >>> for bulk_release in bulk_releases:
            >>>     for release in bulk_release.releases:
            >>>         print(bulk_release.release_id)
            '53'
            '58'
            '59'...

        References:
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_release_observations.html
            - FRED API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_observations.html

        Notes:
            This method handles pagination to retrieve all observations for the specified release ID. 
            It continues to make requests until all data has been fetched, appending each batch of results to 
            a list which is then returned.

        See Also:
            - :class:`fedfred.BulkRelease`: Class representing bulk release observations.
        """

        url_endpoint = '/v2/release/observations'
        return_list = []
        has_more = True
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if limit:
            data['limit'] = limit
        while has_more:
            response = self.__fred_get_request(url_endpoint, data)
            converted = BulkRelease.to_object(response, client=self)
            return_list.append(converted)
            if response['has_more']:
                data['next_cursor'] = response['next_cursor']
            else:
                has_more = False
        return return_list

    ## Series
    def get_series(self, series_id: str, realtime_start: Optional[Union[str, datetime]]=None,
                   realtime_end: Optional[Union[str, datetime]]=None) -> List[Series]:
        """Get a FRED series

        Retrieve economic data series information from the FRED API.

        Args:
            series_id (str): The ID for the economic data series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> series = fred.get_series('GNPCA')
            >>> print(series[0].title)
            'Real Gross National Product'

        See Also:
            - :class:`fedfred.Series`: The Series object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series.html
        """

        url_endpoint = '/series'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        seriess = Series.to_object(response, client=self)
        return seriess

    def get_series_categories(self, series_id: str, realtime_start: Optional[Union[str, datetime]]=None,
                              realtime_end: Optional[Union[str, datetime]]=None) -> List[Category]:
        """Get FRED series categories

        Get the categories for a specified series.

        Args:
            series_id (str): The ID for the series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            List[Category]: If multiple categories are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> categories = fred.get_series_categories('EXJPUS')
            >>> for category in categories:
            >>>     print(category.id)
            '95'
            '275'

        See Also:
            - :class:`fedfred.Category`: The Category object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_categories.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series_categories.html
        """

        url_endpoint = '/series/categories'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        categories = Category.to_object(response, client=self)
        return categories

    def get_series_observations(self, series_id: str, dataframe_method: str = 'pandas',
                                realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str, datetime]]=None,
                                limit: Optional[int]=None, offset: Optional[int]=None,
                                sort_order: Optional[str]=None,
                                observation_start: Optional[Union[str, datetime]]=None,
                                observation_end: Optional[Union[str, datetime]]=None, units: Optional[str]=None,
                                frequency: Optional[str]=None,
                                aggregation_method: Optional[str]=None,
                                output_type: Optional[int]=None, vintage_dates: Optional[Union[str, datetime, list[Optional[Union[str, datetime]]]]]=None) -> Union[pd.DataFrame, 'pl.DataFrame', 'dd.DataFrame']:
        """Get FRED series observations

        Get observations for a FRED series as a pandas or polars DataFrame.

        Args:
            series_id (str): The ID for a series.
            dataframe_method (str, optional): The method to use to convert the response to a DataFrame. Options: 'pandas', 'polars', or 'dask'. Default is 'pandas'.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 100000.
            offset (int, optional): The offset for the results. Used for pagination.
            sort_order (str, optional): Sort results by observation date. Options: 'asc', 'desc'.
            observation_start (str | datetime, optional): The start of the observation period. String format: YYYY-MM-DD.
            observation_end (str | datetime, optional): The end of the observation period. String format: YYYY-MM-DD.
            units (str, optional): A key that indicates a data transformation. Options: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'.
            frequency (str, optional): An optional parameter to change the frequency of the observations. Options: 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'.
            aggregation_method (str, optional): A key that indicates the aggregation method used for frequency aggregation. Options: 'avg', 'sum', 'eop'.
            output_type (int, optional): An integer indicating the type of output. Options: 1 (observations by realtime period), 2 (observations by vintage date, all observations), 3 (observations by vintage date, new and revised observations only), 4 (observations by initial release only).
            vintage_dates (str | list, optional): A comma-separated string of vintage dates. String format: YYYY-MM-DD.

        Returns:
            pandas.DataFrame | polars.DataFrame | dask.DataFrame: Depending on the dataframe_method selected. Default is pandas.DataFrame.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> observations = fred.get_series_observations('GNPCA')
            >>> print(observations.head())
            date       realtime_start realtime_end     value
            1929-01-01     2025-02-13   2025-02-13  1202.659
            1930-01-01     2025-02-13   2025-02-13  1100.670
            1931-01-01     2025-02-13   2025-02-13  1029.038
            1932-01-01     2025-02-13   2025-02-13   895.802
            1933-01-01     2025-02-13   2025-02-13   883.847

        See Also:
            - :class:`fedfred.Helpers`: Helper methods for the fedfred package.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series_observations.html
        """

        url_endpoint = '/series/observations'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        if observation_start:
            if isinstance(observation_start, datetime):
                observation_start = _datetime_converter(observation_start)
            data['observation_start'] = observation_start
        if observation_end:
            if isinstance(observation_end, datetime):
                observation_end = _datetime_converter(observation_end)
            data['observation_end'] = observation_end
        if units:
            data['units'] = units
        if frequency:
            data['frequency'] = frequency
        if aggregation_method:
            data['aggregation_method'] = aggregation_method
        if output_type:
            data['output_type'] = output_type
        if vintage_dates:
            vintage_dates = _vintage_dates_type_converter(vintage_dates)
            data['vintage_dates'] = vintage_dates
        response = self.__fred_get_request(url_endpoint, data)
        if dataframe_method == 'pandas':
            return _pandas_dataframe_converter(response)
        elif dataframe_method == 'polars':
            return _polars_dataframe_converter(response)
        elif dataframe_method == 'dask':
            return _dask_dataframe_converter(response)
        else:
            raise ValueError("dataframe_method must be a string, options are: 'pandas', 'polars', or 'dask'")

    def get_series_release(self, series_id: str, realtime_start: Optional[Union[str, datetime]]=None,
                           realtime_end: Optional[Union[str, datetime]]=None) -> List[Release]:
        """Get FRED series release

        Get the release for a specified series from the FRED API.

        Args:
            series_id (str): The ID for the series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.

        Returns:
            List[Release]: If multiple releases are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> release = fred.get_series_release('GNPCA')
            >>> print(release[0].name)
            'Gross National Product'

        See Also:
            - :class:`fedfred.Release`: The Release object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_release.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series_release.html
        """

        url_endpoint = '/series/release'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        releases = Release.to_object(response, client=self)
        for release in releases:
            release.client = self
        return releases

    def get_series_search(self, search_text: str, search_type: Optional[str]=None,
                          realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str, datetime]]=None,
                          limit: Optional[int]=None, offset: Optional[int]=None,
                          order_by: Optional[str]=None, sort_order: Optional[str]=None,
                          filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                          tag_names: Optional[Union[str, list[str]]]=None, exclude_tag_names: Optional[Union[str, list[str]]]=None) -> List[Series]:
        """Get FRED series search

        Searches for economic data series based on text queries.

        Args:
            search_text (str): The text to search for in economic data series. if 'search_type'='series_id', it's possible to put an '*' in the middle of a string. 'm*sl' finds any series starting with 'm' and ending with 'sl'.
            search_type (str, optional): The type of search to perform. Options include 'full_text' or 'series_id'. Defaults to None.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            limit (int, optional): The maximum number of results to return. Defaults to None.
            offset (int, optional): The offset for the results. Defaults to None.
            order_by (str, optional): The attribute to order results by. Options include 'search_rank', 'series_id', 'title', etc. Defaults to None.
            sort_order (str, optional): The order to sort results. Options include 'asc' or 'desc'. Defaults to None.
            filter_variable (str, optional): The variable to filter results by. Defaults to None.
            filter_value (str, optional): The value to filter results by. Defaults to None.
            tag_names (str | list, optional): A comma-separated list of tag names to include in the search. Defaults to None.
            exclude_tag_names (str | list, optional): A comma-separated list of tag names to exclude from the search. Defaults to None.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> series = fred.get_series_search('monetary services index')
            >>> for s in series:
            >>>     print(s.id)
            'MSIM2'
            'MSIM1P'
            'OCM1P'...

        See Also:
            - :class:`fedfred.Series`: The Series object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_search.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series_search.html
        """

        url_endpoint = '/series/search'
        data: Dict[str, Optional[Union[str, int]]] = {
            'search_text': search_text
        }
        if search_type:
            data['search_type'] = search_type
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        if filter_variable:
            data['filter_variable'] = filter_variable
        if filter_value:
            data['filter_value'] = filter_value
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = _liststring_converter(tag_names)
            data['tag_names'] = tag_names
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = _liststring_converter(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        response = self.__fred_get_request(url_endpoint, data)
        seriess = Series.to_object(response, client=self)
        return seriess

    def get_series_search_tags(self, series_search_text: str, realtime_start: Optional[Union[str, datetime]]=None,
                               realtime_end: Optional[Union[str, datetime]]=None, tag_names: Optional[Union[str, list[str]]]=None,
                               tag_group_id: Optional[str]=None,
                               tag_search_text: Optional[str]=None, limit: Optional[int]=None,
                               offset: Optional[int]=None, order_by: Optional[str]=None,
                               sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED series search tags

        Get the tags for a series search.

        Args:
            series_search_text (str): The words to match against economic data series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to match.
            tag_group_id (str, optional): A tag group id to filter tags by type.
            tag_search_text (str, optional): The words to match against tags.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values of the specified attribute. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'. Default is 'asc'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> tags = fred.get_series_search_tags('monetary services index')
            >>> for tag in tags:
            >>>     print(tag.name)
            'academic data'
            'anderson & jones'
            'divisia'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_search_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series_search_tags.html
        """

        url_endpoint = '/series/search/tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_search_text': series_search_text
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = _liststring_converter(tag_names)
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if tag_search_text:
            data['tag_search_text'] = tag_search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        tags = Tag.to_object(response, client=self)
        return tags

    def get_series_search_related_tags(self, series_search_text: str, tag_names: Union[str,list[str]],
                                       realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str,datetime]]=None,
                                       exclude_tag_names: Optional[Union[str, list[str]]]=None,tag_group_id: Optional[str]=None,
                                       tag_search_text: Optional[str]=None, limit: Optional[int]=None,
                                       offset: Optional[int]=None, order_by: Optional[str]=None,
                                       sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED series search related tags

        Get related tags for a series search text.

        Args:
            series_search_text (str): The text to search for series.
            tag_names (str | list): A semicolon-delimited list of tag names to include.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude.
            tag_group_id (str, optional): The tag group id to filter tags by type.
            tag_search_text (str, optional): The text to search for tags.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options are 'asc' (ascending) or 'desc' (descending).

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> tags = fred.get_series_search_related_tags('mortgage rate')
            >>> for tag in tags:
            >>>     print(tag.name)
            'conventional'
            'h15'
            'interest rate'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_search_related_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series_search_related_tags.html
        """
        url_endpoint = '/series/search/related_tags'
        if isinstance(tag_names, list):
            tag_names = _liststring_converter(tag_names)
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_search_text': series_search_text,
            'tag_names': tag_names
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = _liststring_converter(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if tag_search_text:
            data['tag_search_text'] = tag_search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        tags = Tag.to_object(response, client=self)
        return tags

    def get_series_tags(self, series_id: str, realtime_start: Optional[Union[str, datetime]]=None,
                        realtime_end: Optional[Union[str, datetime]]=None, order_by: Optional[str]=None,
                        sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED series tags

        Get the tags for a series.

        Args:
            series_id (str): The ID for a series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            order_by (str, optional): Order results by values such as 'series_id', 'name', 'popularity', etc.
            sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> tags = fred.get_series_tags('GNPCA')
            >>> for tag in tags:
            >>>     print(tag.name)
            'nation'
            'nsa'
            'usa'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series_tags.html
        """

        url_endpoint = '/series/tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        tags = Tag.to_object(response, client=self)
        return tags

    def get_series_updates(self, realtime_start: Optional[Union[str, datetime]]=None,
                           realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                           offset: Optional[int]=None, filter_value: Optional[str]=None,
                           start_time: Optional[Union[str, datetime]]=None, end_time: Optional[Union[str, datetime]]=None) -> List[Series]:
        """Get FRED series updates

        Retrieves updates for a series from the FRED API.

        Args:
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            filter_value (str, optional): Filter results by this value.
            start_time (str | datetime, optional): The start time for the updates. String format: HH:MM.
            end_time (str | datetime, optional): The end time for the updates. String format: HH:MM.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> series = fred.get_series_updates()
            >>> for s in series:
            >>>     print(s.id)
            'PPIITM'
            'PPILFE'
            'PPIFGS'...

        See Also:
            - :class:`fedfred.Series`: The Series object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_updates.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series_updates.html
        """

        url_endpoint = '/series/updates'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if filter_value:
            data['filter_value'] = filter_value
        if start_time:
            if isinstance(start_time, datetime):
                start_time = _datetime_hh_mm_converter(start_time)
            data['start_time'] = start_time
        if end_time:
            if isinstance(end_time, datetime):
                end_time = _datetime_hh_mm_converter(end_time)
            data['end_time'] = end_time
        response = self.__fred_get_request(url_endpoint, data)
        seriess = Series.to_object(response, client=self)
        return seriess

    def get_series_vintagedates(self, series_id: str, realtime_start: Optional[Union[str, datetime]]=None,
                                realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                                offset: Optional[int]=None, sort_order: Optional[str]=None) -> List[VintageDate]:
        """Get FRED series vintage dates

        Get the vintage dates for a given FRED series.

        Args:
            series_id (str): The ID for the FRED series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            sort_order (str, optional): The order of the results. Possible values: 'asc' or 'desc'.

        Returns:
            List[VintageDate]: If multiple vintage dates are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> vintage_dates = fred.get_series_vintagedates('GNPCA')
            >>> for vintage_date in vintage_dates:
            >>>     print(vintage_date.vintage_date)
            '1958-12-21'
            '1959-02-19'
            '1959-07-19'...

        See Also:
            - :class:`fedfred.VintageDate`: The VintageDate object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series_vintagedates.html
        """

        if not isinstance(series_id, str) or series_id == '':
            raise ValueError("series_id must be a non-empty string")
        url_endpoint = '/series/vintagedates'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        return VintageDate.to_object(response)

    ## Sources
    def get_sources(self, realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str, datetime]]=None,
                    limit: Optional[int]=None, offset: Optional[int]=None,
                    order_by: Optional[str]=None, sort_order: Optional[str]=None) -> List[Source]:
        """Get FRED sources

        Retrieve sources of economic data from the FRED API.

        Args:
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000, maximum is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'source_id', 'name', 'realtime_start', 'realtime_end'.
            sort_order (str, optional): Sort order of results. Options are 'asc' (ascending) or 'desc' (descending).

        Returns:
            List[Source]: If multiple sources are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> sources = fred.get_sources()
            >>> for source in sources:
            >>>     print(source.name)
            'Board of Governors of the Federal Reserve System'
            'Federal Reserve Bank of Philadelphia'
            'Federal Reserve Bank of St. Louis'...

        See Also:
            - :class:`fedfred.Source`: The Source object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/sources.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_sources.html
        """

        url_endpoint = '/sources'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        sources = Source.to_object(response, client=self)
        return sources

    def get_source(self, source_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                   realtime_end: Optional[Union[str, datetime]]=None) -> List[Source]:
        """Get a FRED source

        Retrieves information about a source from the FRED API.

        Args:
            source_id (int): The ID for the source.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.

        Returns:
            List[Source]: If multiple sources are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> source = fred.get_source(1)
            >>> print(source[0].name)
            'Board of Governors of the Federal Reserve System'

        See Also:
            - :class:`fedfred.Source`: The Source object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/source.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_source.html
        """

        url_endpoint = '/source'
        data: Dict[str, Optional[Union[str, int]]] = {
            'source_id': source_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        sources = Source.to_object(response, client=self)
        return sources

    def get_source_releases(self, source_id: int , realtime_start: Optional[Union[str, datetime]]=None,
                            realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                            offset: Optional[int]=None, order_by: Optional[str]=None,
                            sort_order: Optional[str]=None) -> List[Release]:
        """Get FRED source releases

        Get the releases for a specified source from the FRED API.

        Args:
            source_id (int): The ID for the source.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values such as 'release_id', 'name', etc.
            sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for descending.

        Returns:
            List[Release]: If multiple Releases are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> releases = fred.get_source_releases(1)
            >>> for release in releases:
            >>>     print(release.name)
            'G.17 Industrial Production and Capacity Utilization'
            'G.19 Consumer Credit'
            'G.5 Foreign Exchange Rates'...

        See Also:
            - :class:`fedfred.Release`: The Release object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/source_releases.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_source_releases.html
        """

        url_endpoint = '/source/releases'
        data: Dict[str, Optional[Union[str, int]]] = {
            'source_id': source_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        releases = Release.to_object(response, client=self)
        return releases

    ## Tags
    def get_tags(self, realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str,datetime]]=None,
                 tag_names: Optional[Union[str, list[str]]]=None, tag_group_id: Optional[str]=None,
                 search_text: Optional[str]=None, limit: Optional[int]=None,
                 offset: Optional[int]=None, order_by: Optional[str]=None,
                 sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED tags

        Retrieve FRED tags based on specified parameters.

        Args:
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to filter results.
            tag_group_id (str, optional): A tag group ID to filter results.
            search_text (str, optional): The words to match against tag names and descriptions.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
            sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for descending.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> tags = fred.get_tags()
            >>> for tag in tags:
            >>>     print(tag.name)
            'nation'
            'nsa'
            'oecd'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_tags.html
        """

        url_endpoint = '/tags'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = _liststring_converter(tag_names)
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        tags = Tag.to_object(response, client=self)
        return tags

    def get_related_tags(self, tag_names: Union[str, list[str]], realtime_start: Optional[Union[str, datetime]]=None,
                         realtime_end: Optional[Union[str, datetime]]=None, exclude_tag_names: Optional[Union[str, list[str]]]=None,
                         tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                         limit: Optional[int]=None, offset: Optional[int]=None,
                         order_by: Optional[str]=None, sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED related tags

        Retrieve related tags for a given set of tags from the FRED API.

        Args:
            tag_names (str | list): A semicolon-delimited list of tag names to include in the search.
            realtime_start (str | datetime, optional): The start of the real-time period. Strinng format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude from the search.
            tag_group_id (str, optional): A tag group ID to filter tags by group.
            search_text (str, optional): The words to match against tag names and descriptions.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options: 'asc' (ascending), 'desc' (descending). Default is 'asc'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> tags = fred.get_related_tags()
            >>> for tag in tags:
            >>>     print(tag.name)
            'nation'
            'usa'
            'frb'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/related_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_related_tags.html
        """

        url_endpoint = '/related_tags'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if isinstance(tag_names, list):
            tag_names = _liststring_converter(tag_names)
        data['tag_names'] = tag_names
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = _liststring_converter(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        tags = Tag.to_object(response, client=self)
        return tags

    def get_tags_series(self, tag_names: Union[str, list[str]], exclude_tag_names: Optional[Union[str, list[str]]]=None,
                        realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str, datetime]]=None,
                        limit: Optional[int]=None, offset: Optional[int]=None,
                        order_by: Optional[str]=None, sort_order: Optional[str]=None) -> List[Series]:
        """Get FRED tags series

        Get the series matching tags.

        Args:
            tag_names (str | list): A semicolon delimited list of tag names to include in the search.
            exclude_tag_names (str | list, optional): A semicolon delimited list of tag names to exclude in the search.
            realtime_start (str, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values. Options: 'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 'last_updated', 'observation_start', 'observation_end', 'popularity', 'group_popularity'.
            sort_order (str, optional): Sort results in ascending or descending order. Options: 'asc', 'desc'.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> series = fred.get_tags_series('slovenia')
            >>> for s in series:
            >>>     print(s.id)
            'CPGDFD02SIA657N'
            'CPGDFD02SIA659N'
            'CPGDFD02SIM657N'...

        See Also:
            - :class:`fedfred.Series`: The Series object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/tags_series.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_tags_series.html
        """

        url_endpoint = '/tags/series'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if isinstance(tag_names, list):
            tag_names = _liststring_converter(tag_names)
        data['tag_names'] = tag_names
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = _liststring_converter(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = _datetime_converter(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = _datetime_converter(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        seriess = Series.to_object(response, client=self)
        return seriess

class AsyncFred:
    """Asynchronous client for the Federal Reserve FRED/ALFRED API.

    The AsyncFred class contains methods for interacting with the Federal Reserve Bank of St. Louis
    FRED® API and provides asynchronous endpoints with automatic parameter conversion, unified 
    response objects, rate limiting, retries, and typed results.
    
    Attributes:
        cache_mode (bool): Whether caching is enabled for API responses.
        cache (FIFOCache): The cache object for storing API responses.
        base_url (str): The base URL for the FRED API.
        AsyncGeoFred (AsyncGeoFred): Attached instance for asynchronous FRED Maps API endpoints.
    
    Args:
        parent (Fred): The parent Fred instance.

    Raises:
        ValueError: If the provided parent is not an instance of Fred.

    Notes:
        This class is designed to be used as part of the fedfred package and should be accessed
        through an instance of the Fred class.

    Examples:
        >>> import fedfred as fd
        >>> import asyncio
        >>> async def main():
        >>>     fred = fd.Fred('your_api_key')
        >>>     # Use AsyncFred property to access asynchronous endpoints
        >>>     async_fred = fred.AsyncFred
        >>>     # Also acceptable to initialize directly with a Fred instance
        >>>     async_fred = fd.AsyncFred(fred)
        >>> asyncio.run(main())

    Warnings:
        Ensure that the parent Fred instance is properly configured before using AsyncFred.

    See Also:
        - :class:`fedfred.Fred`: The main synchronous client for the FRED API.
        - :func:`fedfred.set_api_key`: Function to set the global FRED API key.
    """

    # Dunder Methods
    def __init__(self, parent: 'Fred') -> None:
        """Initialize the AsyncFred class with a reference to the parent Fred instance.

        Args:
            parent (Fred): The parent Fred instance.

        Raises:
            ValueError: If the provided parent is not an instance of Fred.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key')
            >>>     async_fred = fred.AsyncFred
            >>>     # Also acceptable to initialize directly with a Fred instance
            >>>     async_fred = fd.AsyncFred(fred)
            >>> asyncio.run(main())

        Notes:
            This constructor sets up the AsyncFred instance with references to the parent Fred's
            configuration, including caching and base URL.

        See Also:
            - :class:`fedfred.Fred`: The main synchronous client for the FRED API.
            - :func:`fedfred.set_api_key`: Function to set the global FRED API key.
        """

        if not isinstance(parent, Fred):
            raise ValueError("parent must be an instance of Fred")

        self._parent: Fred = parent
        self.cache_mode: bool = parent.cache_mode
        self.cache: FIFOCache = parent.cache
        self.base_url: str = parent.base_url

    def __repr__(self) -> str:
        """String representation of the AsyncFred class.

        Returns:
            str: A string representation of the AsyncFred class.

        Notes:
            This method provides a detailed representation of the AsyncFred instance, including its parent Fred instance.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> fred = fd.Fred('your_api_key')
            >>> async_fred = fred.AsyncFred
            >>> print(repr(async_fred))
            'Fred(api_key=****your_api_key, cache_mode=True, cache_size=256).AsyncFred'
        """

        return f"{self._parent.__repr__()}.AsyncFred"

    def __str__(self) -> str:
        """String representation of the AsyncFred class.

        Returns:
            str: A user-friendly string representation of the AsyncFred class.

        Notes:
            This method provides a detailed string representation of the AsyncFred instance, including 
            its parent Fred instance.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> async_fred = fred.AsyncFred
            >>> print(str(async_fred))
            'Fred Instance:'
            '  Base URL: https://api.stlouisfed.org/fred'
            '  API Key: ****your_api_key'
            '  Cache Mode: Enabled'
            '  Cache Size: 256 items'
            '  Max Requests per Minute: 120'
            '  AsyncFred Instance:'
            '    Base URL: https://api.stlouisfed.org/fred'
        """

        return (
            f"{self._parent.__str__()}"
            f"  AsyncFred Instance:\n"
            f"    Base URL: {self.base_url}\n"
        )

    def __eq__(self, other: object) -> bool:
        """Equality comparison for the AsyncFred class.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.

        Notes:
            This method compares two AsyncFred instances based on their attributes. If the other object is not an AsyncFred 
            instance, it returns NotImplemented.

        Examples:
            >>> import fedfred as fd
            >>> fred1 = fd.Fred('your_api_key')
            >>> async_fred1 = fred1.AsyncFred
            >>> fred2 = fd.Fred('your_api_key')
            >>> async_fred2 = fred2.AsyncFred
            >>> print(async_fred1 == async_fred2)
            True
        """

        if not isinstance(other, AsyncFred):
            return NotImplemented
        return self._parent == other._parent

    def __hash__(self) -> int:
        """Hash function for the AsyncFred Class.

        Returns:
            int: A hash value for the AsyncFred instance.

        Notes:
            This method generates a hash based on the AsyncFred instance's attributes.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> async_fred = fred.AsyncFred
            >>> print(hash(async_fred))
            1234567890 # Example hash value
        """
        return hash((self._parent.api_key, self._parent.cache_mode, self._parent.cache_size))

    def __del__(self) -> None:
        """Destructor for the AsyncFred class. Clears the cache when the instance is deleted.

        Notes:
            This method ensures that the cache is cleared when the AsyncFred instance is deleted.

        Warnings:
            Avoid relying on destructors for critical resource management, as their execution timing 
            is not guaranteed.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> async_fred = fred.AsyncFred
            >>> del async_fred
            >>> # Cache is cleared when async_fred is deleted
        """

        if hasattr(self, "cache"):
            self.cache.clear()

    def __len__(self) -> int:
        """Get the number of cached items in the AsyncFred instance.

        Returns:
            int: The number of cached items in the AsyncFred instance.

        Notes:
            This method returns the size of the cache if caching is enabled for the parent Fred instance.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> async_fred = fred.AsyncFred
            >>> print(len(async_fred))
            256 # Example length of the cache
        """

        return len(self.cache)

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

        return key in self.cache.keys()

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

        if key in self.cache.keys():
            return self.cache[key]
        else:
            raise AttributeError(f"'{key}' not found in cache.")

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a specific item in the cache.

        Args:
            key (str): The name of the attribute to set.
            value (Any): The value to set.

        Notes:
            This method allows setting cached items using the indexing syntax.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> async_fred = fred.AsyncFred
            >>> async_fred['some_key'] = 'some_value'
            >>> print(async_fred['some_key'])
            'some_value'
        """

        self.cache[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete a specific item from the cache.

        Args:
            key (str): The name of the attribute to delete.

        Raises:
            AttributeError: If the key does not exist.

        Notes:
            This method allows deletion of cached items using the indexing syntax.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> async_fred = fred.AsyncFred
            >>> del async_fred['some_key']
            >>> print('some_key' in async_fred)
            False
        """

        if key in self.cache.keys():
            del self.cache[key]
        else:
            raise AttributeError(f"'{key}' not found in cache.")

    def __call__(self) -> str:
        """Call the AsyncFred instance to get a summary of its configuration.

        Returns:
            str: A string representation of the AsyncFred instance's configuration.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> async_fred = fred.AsyncFred
            >>> print(async_fred())
            'Fred Instance:'
            '  AsyncFred Instance:'
            '    Base URL: https://api.stlouisfed.org/fred'
            '    Cache Mode: Enabled'
            '    Cache Size: 256 items'
            '    API Key: ****your_api_key'
        """

        return (
            f"Fred Instance:\n"
            f"  AsyncFred Instance:\n"
            f"    Base URL: {self.base_url}\n"
            f"    Cache Mode: {'Enabled' if self.cache_mode else 'Disabled'}\n"
            f"    Cache Size: {len(self.cache)} items\n"
            f"    API Key: {'****' + self._parent.api_key[-4:] if self._parent.api_key else 'Not Set'}\n"
        )

    # Properties
    @property
    def keys(self) -> List[str]:
        """List of keys in the cache."""

        return list(self.cache.keys()) if self.cache_mode else []

    # Private Methods
    async def __update_semaphore(self) -> Tuple[Any, float]:
        """Dynamically adjusts the semaphore based on requests left in the minute.

        Returns:
            Tuple[Any, float]: A tuple containing the number of requests left and the time left in seconds.

        Notes:
            This method updates the semaphore limit based on the number of requests made in the last minute, allowing for dynamic rate limiting.

        Warnings:
            This method should be used within an asynchronous context to ensure proper locking and timing.
        """

        async with self._parent.lock:
            now = time.time()
            while self._parent.request_times and self._parent.request_times[0] < now - 60:
                self._parent.request_times.popleft()
            requests_made = len(self._parent.request_times)
            requests_left = max(0, self._parent.max_requests_per_minute - requests_made)
            time_left = max(1, 60 - (now - (self._parent.request_times[0] if self._parent.request_times else now)))
            new_limit = max(1, min(self._parent.max_requests_per_minute // 10, requests_left // 2))
            self._parent.semaphore = asyncio.Semaphore(new_limit)
            return requests_left, time_left

    async def __rate_limited(self) -> None:
        """Ensures asynchronous requests comply with rate limits.

        Notes:
            This method ensures that API requests adhere to the rate limit by dynamically adjusting the wait time based on the 
            number of requests left and the time remaining in the current minute.

        Warnings:
            This method should be used within an asynchronous context to ensure proper locking and timing.
        """

        async with self._parent.semaphore:
            requests_left, time_left = await self.__update_semaphore()
            if requests_left > 0:
                sleep_time = time_left / max(1, requests_left)
                await asyncio.sleep(sleep_time)
            else:
                await asyncio.sleep(60)
            async with self._parent.lock:
                self._parent.request_times.append(time.time())

    async def __fred_get_request(self, url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
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

        @retry(wait=wait_fixed(1),
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type(httpx.HTTPError),
            reraise=True,)
        async def __get_request(url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
            """Perform a GET request without caching.

            Args:
                url_endpoint (str): The FRED API endpoint to query.
                data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

            Returns:
                Dict[str, Any]: The JSON response from the FRED API.

            Raises:
                httpx.HTTPError: If the HTTP request fails.

            Notes:
                This method handles rate limiting and caching for synchronous GET requests to the FRED API.
            """

            await self.__rate_limited()
            params = {
                **(data or {}),
                'api_key': self._parent.api_key,
                'file_type': 'json'
            }
            async with httpx.AsyncClient() as client:
                try:
                    if "/v2/" in url_endpoint:
                        headers = {
                            'Authorization': f'Bearer {self._parent.api_key}'
                        }
                        params = {
                            **(data or {}),
                            'format': 'json'
                        }
                        response = await client.get(self.base_url + url_endpoint, headers=headers, params=params, timeout=10)
                        response.raise_for_status()
                        return response.json()
                    response = await client.get(self.base_url + url_endpoint, params=params, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError as e:
                    raise ValueError(f"HTTP Error occurred: {e}") from e

        @async_cached(cache=self.cache)
        async def __cached_get_request(url_endpoint: str, hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]=None) -> Dict[str, Any]:
            """Perform a GET request with caching.

            Args:
                url_endpoint (str): The FRED API endpoint to query.
                hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]], optional): The hashable representation of the data. Defaults to None.

            Returns:
                Dict[str, Any]: The JSON response from the FRED API.

            Raises:
                httpx.HTTPError: If the HTTP request fails.
            """

            return await __get_request(url_endpoint, await _dict_type_converter_async(hashable_data))

        if data:
            await _fred_parameter_validator_async(data)
        if self.cache_mode:
            return await __cached_get_request(url_endpoint, await _hashable_type_converter_async(data))
        else:
            return await __get_request(url_endpoint, data)

    # Public Methods
    ## Categories
    async def get_category(self, category_id: int) -> List[Category]:
        """Get a FRED Category

        Retrieve information about a specific category from the FRED API.

        Args:r
            category_id (int): The ID of the category to retrieve.

        Returns:
            List[Category]: If multiple categories are returned.

        Raises:
            ValueError: If the response from the FRED API indicates an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     category = await fred.get_category(125)
            >>>     for c in category:
            >>>         print(category[0].name)
            >>> asyncio.run(main())
            'Trade Balance'

        See Also:
            - :class:`fedfred.Category`: The Category object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_category.html
        """

        url_endpoint = '/category'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id
        }
        response = await self.__fred_get_request(url_endpoint, data)
        return await Category.to_object_async(response)

    async def get_category_children(self, category_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                                    realtime_end: Optional[Union[str, datetime]]=None) -> List[Category]:
        """Get a FRED Category's Child Categories

        Get the child categories for a specified category ID from the FRED API.

        Args:
            category_id (int): The ID for the category whose children are to be retrieved.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            List[Category]: If multiple categories are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     children = await fred.get_category_children(13)
            >>>     for child in children:
            >>>         print(child.name)
            >>> asyncio.run(main())
            'Exports'
            'Imports'
            'Income Payments & Receipts'
            'U.S. International Finance'

        See Also:
            - :class:`fedfred.Category`: The Category object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category_children.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_category_children.html
        """

        url_endpoint = '/category/children'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        response = await self.__fred_get_request(url_endpoint, data)
        return await Category.to_object_async(response)

    async def get_category_related(self, category_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                                   realtime_end: Optional[Union[str, datetime]]=None) -> List[Category]:
        """Get a FRED Category's Related Categories

        Get related categories for a given category ID from the FRED API.

        Args:
            category_id (int): The ID for the category.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            List[Category]: If multiple categories are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     related = await fred.get_category_related(32073)
            >>>     for category in related:
            >>>         print(category.name)
            >>> asyncio.run(main())
            'Arkansas'
            'Illinois'
            'Indiana'
            'Kentucky'
            'Mississippi'
            'Missouri'
            'Tennessee'

        See Also:
            - :class:`fedfred.Category`: The Category object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category_related.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_category_related.html
        """

        url_endpoint = '/category/related'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        response = await self.__fred_get_request(url_endpoint, data)
        return await Category.to_object_async(response)

    async def get_category_series(self, category_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                                  realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                                  offset: Optional[int]=None, order_by: Optional[str]=None,
                                  sort_order: Optional[str]=None, filter_variable: Optional[str]=None,
                                  filter_value: Optional[str]=None, tag_names: Optional[Union[str, list[str]]]=None,
                                  exclude_tag_names: Optional[Union[str, list[str]]]=None) -> List[Series]:
        """Get a FRED Category's FRED Series

        Get the series info for all series in a category from the FRED API.

        Args:
            category_id (int): The ID for a category.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 'last_updated', 'observation_start', 'observation_end', 'popularity', 'group_popularity'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'.
            filter_variable (str, optional): The attribute to filter results by. Options are 'frequency', 'units', 'seasonal_adjustment'.
            filter_value (str, optional): The value of the filter_variable to filter results by.
            tag_names (str | list, optional): A semicolon-separated list of tag names to filter results by.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude results by.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     series = await fred.get_category_series(125)
            >>>     for s in series:
            >>>         print(s.frequency)
            >>> asyncio.run(main())
            'Quarterly'
            'Annual'
            'Quarterly'...

        See Also:
            - :class:`fedfred.Series`: The Series object representation.
            
        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category_series.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_category_series.html
        """

        url_endpoint = '/category/series'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        if filter_variable:
            data['filter_variable'] = filter_variable
        if filter_value:
            data['filter_value'] = filter_value
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = await _liststring_converter_async(tag_names)
            data['tag_names'] = tag_names
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = await _liststring_converter_async(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        response = await self.__fred_get_request(url_endpoint, data)
        return await Series.to_object_async(response)

    async def get_category_tags(self, category_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                                realtime_end: Optional[Union[str, datetime]]=None, tag_names: Optional[Union[str, list[str]]]=None,
                                tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                                limit: Optional[int]=None, offset: Optional[int]=None,
                                order_by: Optional[int]=None, sort_order: Optional[str]=None) -> List[Tag]:
        """Get a FRED Category's Tags

        Get the all the tags for a category from the FRED API.

        Args:
            category_id (int): The ID for a category.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names to filter tags by.
            tag_group_id (int, optional): A tag group ID to filter tags by type.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name'. Default is 'series_count'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc', 'desc'. Default is 'desc'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     tags = await fred.get_category_tags(125)
            >>>     for tag in tags:
            >>>         print(tag.notes)
            >>> asyncio.run(main())
            'U.S. Department of Commerce: Bureau of Economic Analysis'
            'Country Level'
            'United States of America'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_category_tags.html
        """

        url_endpoint = '/category/tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = await _liststring_converter_async(tag_names)
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Tag.to_object_async(response)

    async def get_category_related_tags(self, category_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                                        realtime_end: Optional[Union[str, datetime]]=None, tag_names: Optional[Union[str, list[str]]]=None,
                                        exclude_tag_names: Optional[Union[str, list[str]]]=None,
                                        tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                                        limit: Optional[int]=None, offset: Optional[int]=None,
                                        order_by: Optional[int]=None, sort_order: Optional[int]=None) -> List[Tag]:
        """Get a FRED Category's Related Tags

        Retrieve all tags related to a specified category from the FRED API.

        Args:
            category_id (int): The ID for the category.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to include.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude.
            tag_group_id (int, optional): The ID for a tag group.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
            sort_order (str, optional): Sort order, either 'asc' or 'desc'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     tags = await fred.get_category_related_tags(125)
            >>>     for tag in tags:
            >>>         print(tag.name)
            >>> asyncio.run(main())
            'balance'
            'bea'
            'nation'
            'usa'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category_related_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_category_related_tags.html
        """

        url_endpoint = '/category/related_tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'category_id': category_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = await _liststring_converter_async(tag_names)
            data['tag_names'] = tag_names
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = await _liststring_converter_async(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Tag.to_object_async(response)

    ## Releases
    async def get_releases(self, realtime_start: Optional[Union[str, datetime]]=None,
                           realtime_end: Optional[Union[str, datetime]]=None,
                           limit: Optional[int]=None, offset: Optional[int]=None, order_by: Optional[str]=None,
                           sort_order: Optional[str]=None) -> List[Release]:
        """Get FRED releases

        Get all economic data releases from the FRED API.

        Args:
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is None.
            offset (int, optional): The offset for the results. Default is None.
            order_by (str, optional): Order results by values such as 'release_id', 'name', 'press_release', 'realtime_start', 'realtime_end'. Default is None.
            sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order. Default is None.

        Returns:
            List[Releases]: If multiple Releases are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     releases = await fred.get_releases()
            >>>     for release in releases:
            >>>         print(release.name)
            >>> asyncio.run(main())
            'Advance Monthly Sales for Retail and Food Services'
            'Consumer Price Index'
            'Employment Cost Index'...

        See Also:
            - :class:`fedfred.Release`: The Release object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/releases.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_releases.html
        """

        url_endpoint = '/releases'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Release.to_object_async(response)

    async def get_releases_dates(self, realtime_start: Optional[Union[str, datetime]]=None,
                                 realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                                 offset: Optional[int]=None, order_by: Optional[str]=None,
                                 sort_order: Optional[str]=None,
                                 include_releases_dates_with_no_data: Optional[bool]=None) -> List[ReleaseDate]:
        """Get FRED releases dates

        Get all release dates for economic data releases from the FRED API.

        Args:
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is None.
            offset (int, optional): The offset for the results. Default is None.
            order_by (str, optional): Order results by values. Options include 'release_id', 'release_name', 'release_date', 'realtime_start', 'realtime_end'. Default is None.
            sort_order (str, optional): Sort order of results. Options include 'asc' (ascending) or 'desc' (descending). Default is None.
            include_releases_dates_with_no_data (bool, optional): Whether to include release dates with no data. Default is None.

        Returns:
            List[ReleaseDate]: If multiple release dates are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     release_dates = await fred.get_releases_dates()
            >>>     for release_date in release_dates:
            >>>         print(release_date.release_name)
            >>> asyncio.run(main())
            'Advance Monthly Sales for Retail and Food Services'
            'Failures and Assistance Transactions'
            'Manufacturing and Trade Inventories and Sales'...

        See Also:
            - :class:`fedfred.ReleaseDate`: The ReleaseDate object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/releases_dates.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_releases_dates.html
        """

        url_endpoint = '/releases/dates'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        if include_releases_dates_with_no_data:
            data['include_releases_dates_with_no_data'] = include_releases_dates_with_no_data
        response = await self.__fred_get_request(url_endpoint, data)
        return await ReleaseDate.to_object_async(response)

    async def get_release(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                          realtime_end: Optional[Union[str, datetime]]=None) -> List[Release]:
        """Get a FRED release

        Get the release for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            List[Release]: If multiple releases are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     release = await fred.get_release(53)
            >>>     print(release.name)
            >>> asyncio.run(main())
            'Gross Domestic Product'

        See Also:
            - :class:`fedfred.Release`: The Release object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_release.html
        """

        url_endpoint = '/release/'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        response = await self.__fred_get_request(url_endpoint, data)
        return await Release.to_object_async(response)

    async def get_release_dates(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                                realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                                offset: Optional[int]=None, sort_order: Optional[str]=None,
                                include_releases_dates_with_no_data: Optional[bool]=None) -> List[ReleaseDate]:
        """Get FRED release dates

        Get the release dates for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            sort_order (str, optional): The order of the results. Possible values are 'asc' or 'desc'.
            include_releases_dates_with_no_data (bool, optional): Whether to include release dates with no data.

        Returns:
            List[ReleaseDate]: If multiple release dates are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     release_dates = await fred.get_release_dates(82)
            >>>     for release_date in release_dates:
            >>>         print(release_date.date)
            >>> asyncio.run(main())
            '1997-02-10'
            '1998-02-10'
            '1999-02-04'...

        See Also:
            - :class:`fedfred.ReleaseDate`: The ReleaseDate object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_dates.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_release_dates.html
        """

        url_endpoint = '/release/dates'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if not isinstance(release_id, int) or release_id < 0:
            raise ValueError("category_id must be a non-negative integer")
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        if include_releases_dates_with_no_data:
            data['include_releases_dates_with_no_data'] = include_releases_dates_with_no_data
        response = await self.__fred_get_request(url_endpoint, data)
        return await ReleaseDate.to_object_async(response)

    async def get_release_series(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                                 realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                                 offset: Optional[int]=None, sort_order: Optional[str]=None,
                                 filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                                 exclude_tag_names: Optional[Union[str, list[str]]]=None) -> List[Series]:
        """Get FRED release series

        Get the series in a release.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            sort_order (str, optional): Order results by values. Options are 'asc' or 'desc'.
            filter_variable (str, optional): The attribute to filter results by.
            filter_value (str, optional): The value of the filter variable.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     series = await fred.get_release_series(51)
            >>>     for s in series:
            >>>         print(s.id)
            >>> asyncio.run(main())
            'BOMTVLM133S'
            'BOMVGMM133S'
            'BOMVJMM133S'...

        See Also:
            - :class:`fedfred.Series`: The Series object representation.
            
        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_series.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_release_series.html
        """

        url_endpoint = '/release/series'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        if filter_variable:
            data['filter_variable'] = filter_variable
        if filter_value:
            data['filter_value'] = filter_value
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = await _liststring_converter_async(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        response = await self.__fred_get_request(url_endpoint, data)
        return await Series.to_object_async(response)

    async def get_release_sources(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                                  realtime_end: Optional[Union[str, datetime]]=None) -> List[Source]:
        """Get FRED release sources

        Retrieve the sources for a specified release from the FRED API.

        Args:
            release_id (int): The ID of the release for which to retrieve sources.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str| datetime, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.

        Returns:
            List[Series]: If multiple sources are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     sources = await fred.get_release_sources(51)
            >>>     for source in sources:
            >>>         print(source.name)
            >>> asyncio.run(main())
                'U.S. Department of Commerce: Bureau of Economic Analysis'
                'U.S. Department of Commerce: Census Bureau'

        See Also:
            - :class:`fedfred.Source`: The Source object representation.
            
        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_sources.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_release_sources.html
        """

        url_endpoint = '/release/sources'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        response = await self.__fred_get_request(url_endpoint, data)
        return await Source.to_object_async(response)

    async def get_release_tags(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                               realtime_end: Optional[Union[str, datetime]]=None, tag_names: Optional[Union[str, list[str]]]=None,
                               tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                               limit: Optional[int]=None, offset: Optional[int]=None,
                               order_by: Optional[str]=None) -> List[Tag]:
        """Get FRED release tags

        Get the release tags for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names.
            tag_group_id (int, optional): The ID for a tag group.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'. Default is 'series_count'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     tags = await fred.get_release_tags(86)
            >>>     for tag in tags:
            >>>         print(tag.name)
            >>> asyncio.run(main())
            'commercial paper'
            'frb'
            'nation'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_release_tags.html
        """

        url_endpoint = '/release/tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = await _liststring_converter_async(tag_names)
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        response = await self.__fred_get_request(url_endpoint, data)
        return await Tag.to_object_async(response)

    async def get_release_related_tags(self, release_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                                       realtime_end: Optional[Union[str, datetime]]=None, tag_names: Optional[Union[str, list[str]]]=None,
                                       exclude_tag_names: Optional[Union[str, list[str]]]=None, tag_group_id: Optional[str]=None,
                                       search_text: Optional[str]=None, limit: Optional[int]=None,
                                       offset: Optional[int]=None, order_by: Optional[str]=None,
                                       sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED release related tags

        Get release related tags for a given series search text.

        Args:
            series_search_text (str, optional): The text to match against economic data series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names to match.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude results by.
            tag_group_id (str, optional): A tag group id to filter tags by type.
            tag_search_text (str, optional): The text to match against tags.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options: 'asc', 'desc'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     tags = await fred.get_release_related_tags('86')
            >>>     for tag in tags:
            >>>         print(tag.name)
            'commercial paper'
            'frb'
            'nation'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_related_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_release_related_tags.html
        """

        url_endpoint = '/release/related_tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = await _liststring_converter_async(tag_names)
            data['tag_names'] = tag_names
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = await _liststring_converter_async(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Tag.to_object_async(response)

    async def get_release_tables(self, release_id: int, element_id: Optional[int]=None,
                                 include_observation_values: Optional[bool]=None,
                                 observation_date: Optional[Union[str, datetime]]=None) -> List[Element]:
        """Get FRED release tables

        Fetches release tables from the FRED API.

        Args:
            release_id (int): The ID for the release.
            element_id (int, optional): The ID for the element. Defaults to None.
            include_observation_values (bool, optional): Whether to include observation values. Defaults to None.
            observation_date (str | datetime, optional): The observation date in YYYY-MM-DD string format. Defaults to None.

        Returns:
            List[Element]: If multiple elements are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     elements = await fred.get_release_tables(53)
            >>>     for element in elements:
            >>>         print(element.series_id)
            >>> asyncio.run(main())
            'DGDSRL1A225NBEA'
            'DDURRL1A225NBEA'
            'DNDGRL1A225NBEA'...

        See Also:
            - :class:`fedfred.Element`: The Element object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_tables.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_release_tables.html
        """

        url_endpoint = '/release/tables'
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if element_id:
            data['element_id'] = element_id
        if include_observation_values:
            data['include_observation_values'] = include_observation_values
        if observation_date:
            if isinstance(observation_date, datetime):
                observation_date = await _datetime_converter_async(observation_date)
            data['observation_date'] = observation_date
        response = await self.__fred_get_request(url_endpoint, data)
        return await Element.to_object_async(response)

    async def get_release_observations(self, release_id: int, limit: Optional[int]=None) -> List[BulkRelease]:
        """Get FRED release observations in bulk

        Fetches release observations in bulk from the FRED API.

        Args:
            release_id (int): The ID for the release.
            limit (int, optional): The maximum number of results to return per request.

        Returns:
            List[BulkRelease]: If multiple bulk release observations are returned.

        Raises:
            ValueError: If the API request fails or returns an error.
            
        Example:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> bulk_releases = fred.get_release_observations(53)
            >>> for bulk_release in bulk_releases:
            >>>     print(bulk_release.release_id)
            '53'
            '58'
            '59'...

        References:
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_release_observations.html
            - FRED API Documentation: https://fred.stlouisfed.org/docs/api/fred/release_observations.html

        Notes:
            This method handles pagination to retrieve all observations for the specified release ID. 
            It continues to make requests until all data has been fetched, appending each batch of results to 
            a list which is then returned.

        See Also:
            - :class:`fedfred.BulkRelease`: Class representing bulk release observations.
        """

        url_endpoint = '/v2/release/observations'
        return_list = []
        has_more = True
        data: Dict[str, Optional[Union[str, int]]] = {
            'release_id': release_id
        }
        if limit:
            data['limit'] = limit
        while has_more:
            response = await self.__fred_get_request(url_endpoint, data)
            converted = await BulkRelease.to_object_async(response)
            return_list.append(converted)
            if response['has_more']:
                data['next_cursor'] = response['next_cursor']
            else:
                has_more = False
        return return_list

    ## Series
    async def get_series(self, series_id: str, realtime_start: Optional[Union[str, datetime]]=None,
                         realtime_end: Optional[Union[str, datetime]]=None) -> List[Series]:
        """Get a FRED series

        Retrieve economic data series information from the FRED API.

        Args:
            series_id (str): The ID for the economic data series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     series = await fred.get_series('GNPCA')
            >>>     print(series.title)
            >>> asyncio.run(main())
            'Real Gross National Product'

        See Also:
            - :class:`fedfred.Series`: The Series object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_series.html
        """

        url_endpoint = '/series'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        response = await self.__fred_get_request(url_endpoint, data)
        return await Series.to_object_async(response)

    async def get_series_categories(self, series_id: str, realtime_start: Optional[Union[str, datetime]]=None,
                                    realtime_end: Optional[Union[str, datetime]]=None) -> List[Category]:
        """Get FRED series categories

        Get the categories for a specified series.

        Args:
            series_id (str): The ID for the series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            List[Category]: If multiple categories are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     categories = await fred.get_series_categories('EXJPUS')
            >>>     for category in categories:
            >>>         print(category.id)
            >>> asyncio.run(main())
            95
            275

        See Also:
            - :class:`fedfred.Category`: The Category object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_categories.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_series_categories.html
        """

        url_endpoint = '/series/categories'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        response = await self.__fred_get_request(url_endpoint, data)
        return await Category.to_object_async(response)

    async def get_series_observations(self, series_id: str, dataframe_method: str = 'pandas',
                                      realtime_start: Optional[Union[str, datetime]]=None,
                                      realtime_end: Optional[Union[str, datetime]]=None,
                                      limit: Optional[int]=None, offset: Optional[int]=None,
                                      sort_order: Optional[str]=None,
                                      observation_start: Optional[Union[str, datetime]]=None,
                                      observation_end: Optional[Union[str, datetime]]=None,
                                      units: Optional[str]=None, frequency: Optional[str]=None,
                                      aggregation_method: Optional[str]=None,
                                      output_type: Optional[int]=None,
                                      vintage_dates: Optional[Union[str, datetime, list[Optional[Union[str, datetime]]]]]=None
                                      ) -> Union[pd.DataFrame, 'pl.DataFrame', 'dd.DataFrame']:
        """Get FRED series observations

        Get observations for a FRED series as a pandas or polars DataFrame.

        Args:
            series_id (str): The ID for a series.
            dataframe_method (str, optional): The method to use to convert the response to a DataFrame. Options: 'pandas', 'polars', or 'dask'. Default is 'pandas'.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 100000.
            offset (int, optional): The offset for the results. Used for pagination.
            sort_order (str, optional): Sort results by observation date. Options: 'asc', 'desc'.
            observation_start (str | datetime, optional): The start of the observation period. String format: YYYY-MM-DD.
            observation_end (str | datetime, optional): The end of the observation period. String format: YYYY-MM-DD.
            units (str, optional): A key that indicates a data transformation. Options: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'.
            frequency (str, optional): An optional parameter to change the frequency of the observations. Options: 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'.
            aggregation_method (str, optional): A key that indicates the aggregation method used for frequency aggregation. Options: 'avg', 'sum', 'eop'.
            output_type (int, optional): An integer indicating the type of output. Options: 1 (observations by realtime period), 2 (observations by vintage date, all observations), 3 (observations by vintage date, new and revised observations only), 4 (observations by initial release only).
            vintage_dates (str | list, optional): A comma-separated string of vintage dates. String format: YYYY-MM-DD.

        Returns:
            pandas.DataFrame | polars.DataFrame | dask.DataFrame: Depending on the dataframe_method selected. Default is pandas.DataFrame.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     observations = fred.get_series_observations('GNPCA')
            >>>     print(observations.head())
            >>> asyncio.run(main())
            date       realtime_start realtime_end     value
            1929-01-01     2025-02-13   2025-02-13  1202.659
            1930-01-01     2025-02-13   2025-02-13  1100.670
            1931-01-01     2025-02-13   2025-02-13  1029.038
            1932-01-01     2025-02-13   2025-02-13   895.802
            1933-01-01     2025-02-13   2025-02-13   883.847

        See Also:
            - :class:`fedfred.AsyncHelpers`: Asynchronous helper methods for the fedfred package.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_series_observations.html
        """

        url_endpoint = '/series/observations'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        if observation_start:
            if isinstance(observation_start, datetime):
                observation_start = await _datetime_converter_async(observation_start)
            data['observation_start'] = observation_start
        if observation_end:
            if isinstance(observation_end, datetime):
                observation_end = await _datetime_converter_async(observation_end)
            data['observation_end'] = observation_end
        if units:
            data['units'] = units
        if frequency:
            data['frequency'] = frequency
        if aggregation_method:
            data['aggregation_method'] = aggregation_method
        if output_type:
            data['output_type'] = output_type
        if vintage_dates:
            vintage_dates = await _vintage_dates_type_converter_async(vintage_dates)
            data['vintage_dates'] = vintage_dates
        response = await self.__fred_get_request(url_endpoint, data)
        if dataframe_method == 'pandas':
            return await _pandas_dataframe_converter_async(response)
        elif dataframe_method == 'polars':
            return await _polars_dataframe_converter_async(response)
        elif dataframe_method == 'dask':
            return await _dask_dataframe_converter_async(response)
        else:
            raise ValueError("dataframe_method must be a string, options are: 'pandas', 'polars', or 'dask'")

    async def get_series_release(self, series_id: str, realtime_start: Optional[Union[str, datetime]]=None,
                                 realtime_end: Optional[Union[str, datetime]]=None) -> List[Release]:
        """Get FRED series release

        Get the release for a specified series from the FRED API.

        Args:
            series_id (str): The ID for the series.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. Defaults to None.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. Defaults to None.

        Returns:
            List[Release]: If multiple releases are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     release = await fred.get_series_release('GNPCA')
            >>>     print(release.name)
            >>> asyncio.run(main())
            'Gross National Product'

        See Also:
            - :class:`fedfred.Release`: The Release object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_release.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_series_release.html
        """

        url_endpoint = '/series/release'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        response = await self.__fred_get_request(url_endpoint, data)
        return await Release.to_object_async(response)

    async def get_series_search(self, search_text: str, search_type: Optional[str]=None,
                                realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str, datetime]]=None,
                                limit: Optional[int]=None, offset: Optional[int]=None,
                                order_by: Optional[str]=None, sort_order: Optional[str]=None,
                                filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                                tag_names: Optional[Union[str, list[str]]]=None, exclude_tag_names: Optional[Union[str, list[str]]]=None) -> List[Series]:
        """Get FRED series search

        Searches for economic data series based on text queries.

        Args:
            search_text (str): The text to search for in economic data series. if 'search_type'='series_id', it's possible to put an '*' in the middle of a string. 'm*sl' finds any series starting with 'm' and ending with 'sl'.
            search_type (str, optional): The type of search to perform. Options include 'full_text' or 'series_id'. Defaults to None.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            limit (int, optional): The maximum number of results to return. Defaults to None.
            offset (int, optional): The offset for the results. Defaults to None.
            order_by (str, optional): The attribute to order results by. Options include 'search_rank', 'series_id', 'title', etc. Defaults to None.
            sort_order (str, optional): The order to sort results. Options include 'asc' or 'desc'. Defaults to None.
            filter_variable (str, optional): The variable to filter results by. Defaults to None.
            filter_value (str, optional): The value to filter results by. Defaults to None.
            tag_names (str | list, optional): A comma-separated list of tag names to include in the search. Defaults to None.
            exclude_tag_names (str | list, optional): A comma-separated list of tag names to exclude from the search. Defaults to None.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     series = await fred.get_series_search('monetary services index')
            >>>     for s in series:
            >>>         print(s.id)
            >>> asyncio.run(main())
            'MSIM2'
            'MSIM1P'
            'OCM1P'...

        See Also:
            - :class:`fedfred.Series`: The Series object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_search.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_series_search.html
        """

        url_endpoint = '/series/search'
        data: Dict[str, Optional[Union[str, int]]] = {
            'search_text': search_text
        }
        if search_type:
            data['search_type'] = search_type
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        if filter_variable:
            data['filter_variable'] = filter_variable
        if filter_value:
            data['filter_value'] = filter_value
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = await _liststring_converter_async(tag_names)
            data['tag_names'] = tag_names
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = await _liststring_converter_async(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        response = await self.__fred_get_request(url_endpoint, data)
        return await Series.to_object_async(response)

    async def get_series_search_tags(self, series_search_text: str, realtime_start: Optional[Union[str, datetime]]=None,
                                     realtime_end: Optional[Union[str, datetime]]=None, tag_names: Optional[Union[str, list[str]]]=None,
                                     tag_group_id: Optional[str]=None,
                                     tag_search_text: Optional[str]=None, limit: Optional[int]=None,
                                     offset: Optional[int]=None, order_by: Optional[str]=None,
                                     sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED series search tags

        Get the tags for a series search.

        Args:
            series_search_text (str): The words to match against economic data series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to match.
            tag_group_id (str, optional): A tag group id to filter tags by type.
            tag_search_text (str, optional): The words to match against tags.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values of the specified attribute. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'. Default is 'asc'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     tags = await fred.get_series_search_tags('monetary services index')
            >>>     for tag in tags:
            >>>         print(tag.name)
            >>> asyncio.run(main())
            'academic data'
            'anderson & jones'
            'divisia'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_search_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_series_search_tags.html
        """

        url_endpoint = '/series/search/tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_search_text': series_search_text
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = await _liststring_converter_async(tag_names)
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if tag_search_text:
            data['tag_search_text'] = tag_search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Tag.to_object_async(response)

    async def get_series_search_related_tags(self, series_search_text: str, tag_names: Union[str, list[str]],
                                             realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str,datetime]]=None,
                                             exclude_tag_names: Optional[Union[str, list[str]]]=None,tag_group_id: Optional[str]=None,
                                             tag_search_text: Optional[str]=None, limit: Optional[int]=None,
                                             offset: Optional[int]=None, order_by: Optional[str]=None,
                                             sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED series search related tags

        Get related tags for a series search text.

        Args:
            series_search_text (str): The text to search for series.
            tag_names (str | list): A semicolon-delimited list of tag names to include.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude.
            tag_group_id (str, optional): The tag group id to filter tags by type.
            tag_search_text (str, optional): The text to search for tags.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options are 'asc' (ascending) or 'desc' (descending).

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     tags = await fred.get_series_search_related_tags('mortgage rate')
            >>>     for tag in tags:
            >>>         print(tag.name)
            >>> asyncio.run(main())
            'conventional'
            'h15'
            'interest rate'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_search_related_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_series_search_related_tags.html
        """

        url_endpoint = '/series/search/related_tags'
        if isinstance(tag_names, list):
            tag_names = await _liststring_converter_async(tag_names)
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_search_text': series_search_text,
            'tag_names': tag_names
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = await _liststring_converter_async(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if tag_search_text:
            data['tag_search_text'] = tag_search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Tag.to_object_async(response)

    async def get_series_tags(self, series_id: str, realtime_start: Optional[Union[str, datetime]]=None,
                              realtime_end: Optional[Union[str, datetime]]=None, order_by: Optional[str]=None,
                              sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED series tags

        Get the tags for a series.

        Args:
            series_id (str): The ID for a series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            order_by (str, optional): Order results by values such as 'series_id', 'name', 'popularity', etc.
            sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     tags = await fred.get_series_tags('GNPCA')
            >>>     for tag in tags:
            >>>         print(tag.name)
            >>> asyncio.run(main())
            'nation'
            'nsa'
            'usa'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_series_tags.html
        """

        url_endpoint = '/series/tags'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Tag.to_object_async(response)

    async def get_series_updates(self, realtime_start: Optional[Union[str, datetime]]=None,
                                 realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                                 offset: Optional[int]=None, filter_value: Optional[str]=None,
                                 start_time: Optional[Union[str, datetime]]=None, end_time: Optional[Union[str, datetime]]=None) -> List[Series]:
        """Get FRED series updates

        Retrieves updates for a series from the FRED API.

        Args:
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            filter_value (str, optional): Filter results by this value.
            start_time (str| datetime, optional): The start time for the updates. String format: HH:MM.
            end_time (str | datetime, optional): The end time for the updates. String format: HH:MM.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     series = await fred.get_series_updates()
            >>>     for s in series:
            >>>         print(s.id)
            >>> asyncio.run(main())
            'PPIITM'
            'PPILFE'
            'PPIFGS'...

        See Also:
            - :class:`fedfred.Series`: The Series object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_updates.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_series_updates.html
        """

        url_endpoint = '/series/updates'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if filter_value:
            data['filter_value'] = filter_value
        if start_time:
            if isinstance(start_time, datetime):
                start_time = await _datetime_hh_mm_converter_async(start_time)
            data['start_time'] = start_time
        if end_time:
            if isinstance(end_time, datetime):
                end_time = await _datetime_hh_mm_converter_async(end_time)
            data['end_time'] = end_time
        response = await self.__fred_get_request(url_endpoint, data)
        return await Series.to_object_async(response)

    async def get_series_vintagedates(self, series_id: str, realtime_start: Optional[Union[str, datetime]]=None,
                                      realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                                      offset: Optional[int]=None, sort_order: Optional[str]=None) -> List[VintageDate]:
        """Get FRED series vintage dates

        Get the vintage dates for a given FRED series.

        Args:
            series_id (str): The ID for the FRED series.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            sort_order (str, optional): The order of the results. Possible values: 'asc' or 'desc'.

        Returns:
            List[VintageDate]: If multiple vintage dates are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     vintage_dates = await fred.get_series_vintagedates('GNPCA')
            >>>     for vintage_date in vintage_dates:
            >>>         print(vintage_date.vintage_date)
            >>> asyncio.run(main())
            '1958-12-21'
            '1959-02-19'
            '1959-07-19'...

        See Also:
            - :class:`fedfred.VintageDate`: The VintageDate object representation.

        References: 
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_series_vintagedates.html
        """

        if not isinstance(series_id, str) or series_id == '':
            raise ValueError("series_id must be a non-empty string")
        url_endpoint = '/series/vintagedates'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await VintageDate.to_object_async(response)

    ## Sources
    async def get_sources(self, realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str, datetime]]=None,
                          limit: Optional[int]=None, offset: Optional[int]=None,
                          order_by: Optional[str]=None, sort_order: Optional[str]=None) -> List[Source]:
        """Get FRED sources

        Retrieve sources of economic data from the FRED API.

        Args:
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000, maximum is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'source_id', 'name', 'realtime_start', 'realtime_end'.
            sort_order (str, optional): Sort order of results. Options are 'asc' (ascending) or 'desc' (descending).
            file_type (str, optional): The format of the returned data. Default is 'json'. Options are 'json', 'xml'.

        Returns:
            List[Source]: If multiple sources are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     sources = await fred.get_sources()
            >>>     for source in sources:
            >>>         print(source.name)
            >>> asyncio.run(main())
            'Board of Governors of the Federal Reserve System'
            'Federal Reserve Bank of Philadelphia'
            'Federal Reserve Bank of St. Louis'...

        See Also:
            - :class:`fedfred.Source`: The Source object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/sources.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_sources.html
        """

        url_endpoint = '/sources'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Source.to_object_async(response)

    async def get_source(self, source_id: int, realtime_start: Optional[Union[str, datetime]]=None,
                         realtime_end: Optional[Union[str, datetime]]=None) -> List[Source]:
        """Get a FRED source

        Retrieves information about a source from the FRED API.

        Args:
            source_id (int): The ID for the source.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.

        Returns:
            List[Source]: If multiple sources are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     source = await fred.get_source(1)
            >>>     print(source.name)
            >>> asyncio.run(main())
            'Board of Governors of the Federal Reserve System'

        See Also:
            - :class:`fedfred.Source`: The Source object representation.
            
        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/source.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_source.html
        """

        url_endpoint = '/source'
        data: Dict[str, Optional[Union[str, int]]] = {
            'source_id': source_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        response = await self.__fred_get_request(url_endpoint, data)
        return await Source.to_object_async(response)

    async def get_source_releases(self, source_id: int , realtime_start: Optional[Union[str, datetime]]=None,
                                  realtime_end: Optional[Union[str, datetime]]=None, limit: Optional[int]=None,
                                  offset: Optional[int]=None, order_by: Optional[str]=None,
                                  sort_order: Optional[str]=None) -> List[Release]:
        """Get FRED source releases

        Get the releases for a specified source from the FRED API.

        Args:
            source_id (int): The ID for the source.
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values such as 'release_id', 'name', etc.
            sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for descending.

        Returns:
            List[Release]: If multiple Releases are returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     releases = await fred.get_source_releases(1)
            >>>     for release in releases:
            >>>         print(release.name)
            >>> asyncio.run(main())
            'G.17 Industrial Production and Capacity Utilization'
            'G.19 Consumer Credit'
            'G.5 Foreign Exchange Rates'...

        See Also:
            - :class:`fedfred.Release`: The Release object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/source_releases.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_source_releases.html
        """

        url_endpoint = '/source/releases'
        data: Dict[str, Optional[Union[str, int]]] = {
            'source_id': source_id
        }
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Release.to_object_async(response)

    ## Tags
    async def get_tags(self, realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str,datetime]]=None,
                       tag_names: Optional[Union[str, list[str]]]=None, tag_group_id: Optional[str]=None,
                       search_text: Optional[str]=None, limit: Optional[int]=None,
                       offset: Optional[int]=None, order_by: Optional[str]=None,
                       sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED tags

        Retrieve FRED tags based on specified parameters.

        Args:
            realtime_start (str | datetime, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to filter results.
            tag_group_id (str, optional): A tag group ID to filter results.
            search_text (str, optional): The words to match against tag names and descriptions.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
            sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for descending.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     tags = await fred.get_tags()
            >>>     for tag in tags:
            >>>         print(tag.name)
            >>> asyncio.run(main())
            'nation'
            'nsa'
            'oecd'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_tags.html
        """

        url_endpoint = '/tags'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = await _liststring_converter_async(tag_names)
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Tag.to_object_async(response)

    async def get_related_tags(self, realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str, datetime]]=None,
                               tag_names: Optional[Union[str, list[str]]]=None, exclude_tag_names: Optional[Union[str, list[str]]]=None,
                               tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                               limit: Optional[int]=None, offset: Optional[int]=None,
                               order_by: Optional[str]=None, sort_order: Optional[str]=None) -> List[Tag]:
        """Get FRED related tags

        Retrieve related tags for a given set of tags from the FRED API.

        Args:
            realtime_start (str | datetime, optional): The start of the real-time period. Strinng format: YYYY-MM-DD.
            realtime_end (str | datetime, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to include in the search.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude from the search.
            tag_group_id (str, optional): A tag group ID to filter tags by group.
            search_text (str, optional): The words to match against tag names and descriptions.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options: 'asc' (ascending), 'desc' (descending). Default is 'asc'.

        Returns:
            List[Tag]: If multiple tags are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').Async
            >>>     tags = await fred.get_related_tags()
            >>>     for tag in tags:
            >>>         print(tag.name)
            >>> asyncio.run(main())
            'nation'
            'usa'
            'frb'...

        See Also:
            - :class:`fedfred.Tag`: The Tag object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/related_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_related_tags.html
        """

        url_endpoint = '/related_tags'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = await _liststring_converter_async(tag_names)
            data['tag_names'] = tag_names
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = await _liststring_converter_async(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Tag.to_object_async(response)

    async def get_tags_series(self, tag_names: Optional[Union[str, list[str]]]=None, exclude_tag_names: Optional[Union[str, list[str]]]=None,
                              realtime_start: Optional[Union[str, datetime]]=None, realtime_end: Optional[Union[str, datetime]]=None,
                              limit: Optional[int]=None, offset: Optional[int]=None,
                              order_by: Optional[str]=None, sort_order: Optional[str]=None) -> List[Series]:
        """Get FRED tags series

        Get the series matching tags.

        Args:
            tag_names (str, optional): A semicolon delimited list of tag names to include in the search.
            exclude_tag_names (str, optional): A semicolon delimited list of tag names to exclude in the search.
            realtime_start (str, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values. Options: 'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 'last_updated', 'observation_start', 'observation_end', 'popularity', 'group_popularity'.
            sort_order (str, optional): Sort results in ascending or descending order. Options: 'asc', 'desc'.

        Returns:
            List[Series]: If multiple series are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     series = await fred.get_tags_series('slovenia')
            >>>     for s in series:
            >>>         print(s.id)
            >>> asyncio.run(main())
            'CPGDFD02SIA657N'
            'CPGDFD02SIA659N'
            'CPGDFD02SIM657N'...

        See Also:
            - :class:`fedfred.Series`: The Series object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/tags_series.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_tags_series.html
        """

        url_endpoint = '/tags/series'
        data: Dict[str, Optional[Union[str, int]]] = {}
        if tag_names:
            if isinstance(tag_names, list):
                tag_names = await _liststring_converter_async(tag_names)
            data['tag_names'] = tag_names
        if exclude_tag_names:
            if isinstance(exclude_tag_names, list):
                exclude_tag_names = await _liststring_converter_async(exclude_tag_names)
            data['exclude_tag_names'] = exclude_tag_names
        if realtime_start:
            if isinstance(realtime_start, datetime):
                realtime_start = await _datetime_converter_async(realtime_start)
            data['realtime_start'] = realtime_start
        if realtime_end:
            if isinstance(realtime_end, datetime):
                realtime_end = await _datetime_converter_async(realtime_end)
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = await self.__fred_get_request(url_endpoint, data)
        return await Series.to_object_async(response)
