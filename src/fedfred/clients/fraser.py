# filepath: /src/fedfred/clients/fraser.py
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
"""fedfred.clients.fraser

This module defines the Fraser client for interacting with the Federal Reserve Fraser API.
"""

from typing import Any, Dict, Optional, Tuple, Union
from collections import deque
import time
from cachetools import FIFOCache, cached
import httpx
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type
from .._core._parsers import Helpers
from ..config import resolve_api_key

class Fraser:
    """Client for the Federal Reserve FRASER API.

    The Fraser class contains methods for interacting with the Federal Reserve FRASER API, 
    and provides synchronous endpoints with automatic parameter conversion, unified response 
    objects, rate limiting, retries, and typed results.

    Attributes:
        api_key (Optional[str]): The API key for accessing the Fraser API.
        base_url (str): The base URL for the Fraser API.
        cache_mode (bool): Whether to enable caching for GET requests.
        cache_size (int): The maximum size of the cache for GET requests.
        cache (FIFOCache): The cache object for storing GET request responses.
        max_requests_per_minute (int): The maximum number of requests allowed per minute.
        request_times (deque): A deque to track the timestamps of recent requests for rate limiting.

    Args:
        api_key (Optional[str]): The API key for accessing the Fraser API. If None, it will be resolved from configuration.
        cache_mode (bool): Whether to enable caching for GET requests. Default is True.
        cache_size (int): The maximum size of the cache for GET requests. Default is 256.

    Raises:
        RuntimeError: If the API key is not provided for GET requests.

    Notes:
        API keys can be set globally using the :class:`set_api_key` function or provided per-client during initialization.
        The FRASER API uses a different API key then the FRED API.

    Examples:
        >>> import fedfred as fd
        >>> fraser_client = fd.Fraser(api_key="your_fraser_api_key")

    See Also:
        - :func:`fedfred.set_api_key`
        - :func:`fedfred.get_api_key`
    
    """

    # Dunder Methods
    def __init__(self, api_key: Optional[str]=None, cache_mode: bool=True, cache_size: int=256) -> None:
        """Initialize the Fraser class that provides functions which query FRASER data.

        Args:
            api_key (Optional[str]): The API key for accessing the Fraser API. If None, it will be resolved from configuration.
            cache_mode (bool): Whether to enable caching for GET requests. Default is True.
            cache_size (int): The maximum size of the cache for GET requests. Default is 256.

        Raises:
            RuntimeError: If the API key is not provided for GET requests.

        Examples:
            >>> import fedfred as fd
            >>> fraser_client = fd.Fraser(api_key="your_fraser_api_key")

        Notes:
            API keys can be set globally using the :class:`set_api_key` function or provided per-client during initialization.
            The FRASER API uses a different API key then the FRED API.

        See Also:
            - :func:`fedfred.set_api_key`
            - :func:`fedfred.get_api_key`
        """
        
        self.api_key: Optional[str] = resolve_api_key(api_key, service="fraser")
        self.base_url: str = "https://fraser.stlouisfed.org/api"
        self.cache_mode: bool = cache_mode
        self.cache_size: int = cache_size
        self.cache: FIFOCache = FIFOCache(maxsize=self.cache_size)
        self.max_requests_per_minute: int = 30
        self.request_times: deque = deque()

    def __repr__(self) -> str:
        """String representation of the Fraser class

        Returns:
            str: String representation of the Fraser class

        Notes:
            Displays whether the API key is set, cache mode, and cache size.

        Examples:
            >>> import fedfred as fd
            >>> fraser_client = fd.Fraser(api_key="your_fraser_api_key")
            >>> print(fraser_client)
            'Fraser(api_key='your_fraser_api_key', cache_mode=True, cache_size=256)'
        """
        return f"Fraser(api_key={'SET' if self.api_key else 'NOT SET'}, cache_mode={self.cache_mode}, cache_size={self.cache_size})"
    
    def __str__(self) -> str:
        """String representation of the Fraser class

        Returns:
            str: A user-friendly string representation of the Fraser class

        Notes:
            This method provides a detailed summary of the Fraser instance's configuration.

        Examples:
            >>> import fedfred as fd
            >>> fraser_client = fd.Fraser(api_key="your_fraser_api_key")
            >>> str(fraser_client)
            'Fraser Instance:'
            '  API Key: ***_key'
            '  Cache Mode: Enabled'
            '  Cache Size: 256'
            'Max Requests Per Minute: 30'
        """
        return (
            f"Fraser Instance:\n"
            f"  API Key: {'***' + self.api_key[-4:] if self.api_key else 'Not Provided'}\n"
            f"  Cache Mode: {'Enabled' if self.cache_mode else 'Disabled'}\n"
            f"  Cache Size: {self.cache_size}\n"
            f"  Max Requests Per Minute: {self.max_requests_per_minute}"
        )
    
    def __eq__(self, other:object) -> bool:
        """Equality comparison for the Fraser class.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.

        Notes:
            This method compares two Fraser instances based on their attributes. If the other object is not a Fraser instance, it return NotImplemented.
        
        Examples:
            >>> import fedfred as fd
            >>> fraser_client1 = fd.Fraser(api_key="key1")
            >>> fraser_client2 = fd.Fraser(api_key="key1")
            >>> fraser_client1 == fraser_client2
            True
        """

        if not isinstance(other, Fraser):
            return NotImplemented
        return (
            self.api_key == other.api_key and
            self.cache_mode == other.cache_mode and
            self.cache_size == other.cache_size
        )
    
    def __hash__(self) -> int:
        """Hash function for the Fraser class.

        Returns:
            int: A hash value for the Fraser instance.

        Notes:
            This method generates a hash based on the Fraser instance's attributes, allowing it to be used in hash-based collections.

        Examples:
            >>> import fedfred as fd
            >>> fraser_client = fd.Fraser(api_key="your_fraser_api_key")
            >>> hash_value = hash(fraser_client)        
        """

        return hash((self.api_key, self.cache_mode, self.cache_size))
    
    def __del__(self) -> None:
        """Destructor for the Fraser class. Clears the cache when the instance is deleted.

        Notes:
            This method ensures that the cache is cleared when the Fraser instance is deleted.

        Warnings:
            Avoid relying on destructors for critical resource management, as theie execution timing
            is not guaranteed.
        
        Examples:
            >>> import fedfred as fd
            >>> fraser_client = fd.Fraser(api_key="your_fraser_api_key")
            >>> del fraser_client
            # Cache is cleared when fraser is deleted
        """

        if hasattr(self, "cache"):
            self.cache.clear()

    def __len__(self) -> int:
        """Get the number of cached items in the Fraser instance.

        Returns:
            int: The number of cached items in the Fraser instance.

        Notes:
            This method returns the size of the cache if caching is enabled.

        Examples:
            >>> import fedfred as fd
            >>> fraser_client = fd.Fraser(api_key="your_fraser_api_key")
            >>> len(fraser_client)
            0
        """

        return len(self.cache) if self.cache_mode else 0
    
    def __contains__(self, key: str) -> bool:
        """Check if a specific item exists in the cache.

        Args:
            key (str): The key to check in the cache.

        Returns:
            bool: True if the attribute exists, False otherwise.

        Notes:
            This method checks for the existence of a key in the cache if caching is enabled. 
        """

        return key in self.cache.keys() if self.cache_mode else False
    
    def __getitem__(self, key:str) -> Any:
        """Get a cached item by key.

        Args:
            key (str): The key of the item to retrieve from the cache.

        Returns:
            Any: The cached item associated with the given key.

        Raises:
            KeyError: If the key is not found in the cache.

        Notes:
            This method retrieves an item from the cache by its key if caching is enabled. 
            If caching is disabled or the key is not found, it raises a KeyError.
        """

        if key in self.cache.keys():
            return self.cache[key]
        else:
            raise AttributeError(f"'{key}' not found in cache.")
        
    def __setitem__(self, key:str, value:Any) -> None:
        """Set a cached item by key.

        Args:
            key (str): The key of the item to store in the cache.
            value (Any): The value of the item to store in the cache.

        Notes:
            This method stores an item in the cache with the given key if caching is enabled. 
            If caching is disabled, it does nothing.
        """

        self.cache[key] = value

    def __delitem__(self, key:str) -> None:
        """Delete a cached item by key.

        Args:
            key (str): The key of the item to delete from the cache.

        Raises:
            KeyError: If the key is not found in the cache.

        Notes:
            This method deletes an item from the cache by its key if caching is enabled. 
            If caching is disabled or the key is not found, it raises a KeyError.
        """

        if key in self.cache.keys():
            del self.cache[key]
        else:
            raise AttributeError(f"'{key}' not found in cache.")
        
    def __call__(self)-> str:
        """Call method for the Fraser class. Returns a summary of the instance's configuration.

        Returns:
            str: A summary of the Fraser instance's configuration.

        Notes:
            This method provides a quick summary of the Fraser instance's configuration when called.

        Examples:
            >>> import fedfred as fd
            >>> fraser_client = fd.Fraser(api_key="your_fraser_api_key")
            >>> print(fraser_client())
            'Fraser Instance: API Key: ***_key, Cache Mode: Enabled, Cache Size: 256, Max Requests Per Minute: 30'
        """

        return (
            f"Fraser Instance:\n"
            f"  Base URL: {self.base_url}\n"
            f"  Cache Mode: {'Enabled' if self.cache_mode else 'Disabled'}\n"
            f"  Cache Size: {len(self.cache)} items\n"
            f"  API Key: {'****' + self.api_key[-4:] if self.api_key else 'Not Set'}\n"
        )

    # Private Methods
    def __rate_limited(self) -> None:
        now = time.time()
        self.request_times.append(now)
        while self.request_times and self.request_times[0] < now - 60:
            self.request_times.popleft()
        if len(self.request_times) >= self.max_requests_per_minute:
            time.sleep(60 - (now - self.request_times[0]))

    def __fraser_post_request(self, url_endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

        self.__rate_limited()
        payload = {
            **(data or {}),
        }
        with httpx.Client() as client:
            try:
                response = client.post(self.base_url + url_endpoint, json=payload, timeout=10)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise ValueError(f"HTTP Error occurred: {e}") from e

    def __fraser_get_request(self, url_endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        @retry(wait=wait_fixed(1),
               stop=stop_after_attempt(3),
               retry=retry_if_exception_type(httpx.HTTPError),
               reraise=True)
        def __get_request(url_endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            
            self.__rate_limited()
            params = {
                **(data or {}),
                "format": "json"
            }
            assert self.api_key is not None, "API key must be provided for GET requests."
            headers: Dict[str, str] = {
                "X-API-Key": self.api_key
            }
            with httpx.Client() as client:
                try:
                    response = client.get(self.base_url + url_endpoint, params=params, headers=headers, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError as e:
                    raise ValueError(f"HTTP Error occurred: {e}") from e
                
        @cached(cache=self.cache)
        def __cached_get_request(url_endpoint: str, hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]=None) -> Dict[str, Any]:

            return __get_request(url_endpoint, Helpers.to_dict(hashable_data))

        if data:
            Helpers.parameter_validation(data)
        if self.cache_mode:
            return __cached_get_request(url_endpoint, Helpers.to_hashable(data))
        else:
            return __get_request(url_endpoint, data)
    
    # Public Methods
    ## API-Key
    def post_key_request(self, email: str, description: str) -> None:

        url_endpoint = "/api-key"
        data = {
            "email": email,
            "description": description,
        }
        self.__fraser_post_request(url_endpoint, data)
        return None

    ## Titles
    def get_single_title(self, title_id: int, limit: Optional[int]=None, page: Optional[int]=None):

        url_endpoint = f'/title/{title_id}'
        data = {}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page
        response = self.__fraser_get_request(url_endpoint, data)

    def get_all_title_items(self, title_id: int, limit: Optional[int]=None, page: Optional[int]=None):

        url_endpoint = f'/title/{title_id}/items'
        data = {}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page
        response = self.__fraser_get_request(url_endpoint, data)
        
    def get_single_title_table_of_contents(self, title_id: int):

        url_endpoint = f'/title/{title_id}/toc'
        response = self.__fraser_get_request(url_endpoint)

    ## Items
    def get_single_item(self, item_id: int):

        url_endpoint = f'/item/{item_id}'
        response = self.__fraser_get_request(url_endpoint)

    def get_single_item_table_of_contents(self, item_id: int, limit: Optional[int]=None, page: Optional[int]=None):

        url_endpoint = f'/item/{item_id}/toc'
        data = {}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page
        response = self.__fraser_get_request(url_endpoint, data)

    ## Table of Contents
    def get_table_of_contents(self, toc_id: int, limit: Optional[int]=None, page: Optional[int]=None):

        url_endpoint = f'/toc/{toc_id}'
        data = {}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page
        response = self.__fraser_get_request(url_endpoint, data)

    ## Authors
    def get_all_authors(self, limit: Optional[int]=None, page: Optional[int]=None):

        url_endpoint = '/author'
        data = {}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page
        response = self.__fraser_get_request(url_endpoint, data)

    def get_single_author(self, author_id: int):
        
        url_endpoint = f'/author/{author_id}'
        response = self.__fraser_get_request(url_endpoint)

    def get_all_author_records(self, author_id: int, role: Optional[str]=None):

        url_endpoint = f'/author/{author_id}/records'
        data = {}
        if role:
            data['role'] = role
        response = self.__fraser_get_request(url_endpoint, data)

    ## Subjects
    def get_single_subject(self, subject_id: int):

        url_endpoint = f'/subject/{subject_id}'
        response = self.__fraser_get_request(url_endpoint)

    def get_all_subjects(self, limit: Optional[int]=None, page: Optional[int]=None):

        url_endpoint = '/subject'
        data = {}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page
        response = self.__fraser_get_request(url_endpoint, data)

    def get_all_subject_records(self, subject_id: int, limit: Optional[int]=None, page: Optional[int]=None):
        
        url_endpoint = f'/subject/{subject_id}/records'
        data = {}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page
        response = self.__fraser_get_request(url_endpoint, data)

    ## Themes
    def get_all_themes(self, limit: Optional[int]=None, page: Optional[int]=None):

        url_endpoint = '/theme'
        data = {}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page
        response = self.__fraser_get_request(url_endpoint, data)

    def get_single_theme(self, theme_id: int):
        
        url_endpoint = f'/theme/{theme_id}'
        response = self.__fraser_get_request(url_endpoint)

    def get_all_theme_records(self, theme_id: int):
        url_endpoint = f'/theme/{theme_id}/records'
        response = self.__fraser_get_request(url_endpoint)

    ## Timelines
    def get_single_timeline(self, timeline_id: int):

        url_endpoint = f'/timeline/{timeline_id}'
        response = self.__fraser_get_request(url_endpoint)

    def get_all_timelines(self, limit: Optional[int]=None, page: Optional[int]=None):
        
        url_endpoint = '/timeline'
        data = {}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page
        response = self.__fraser_get_request(url_endpoint, data)

    def get_all_timeline_events(self, timeline_id: int, limit: Optional[int]=None, page: Optional[int]=None):

        url_endpoint = f'/timeline/{timeline_id}/events'
        data = {}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page
        response = self.__fraser_get_request(url_endpoint, data)