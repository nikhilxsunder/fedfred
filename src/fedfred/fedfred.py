"""
fedfred: A feature-rich python package for interacting with the Federal Reserve Bank of St. Louis Economic Database: FRED® API.
"""
import asyncio
import time
from collections import deque
from typing import Optional, Dict, Union
import httpx
import pandas as pd
import geopandas as gpd
import polars as pl
from tenacity import retry, wait_fixed, stop_after_attempt
from cacheout import Cache
from .fred_data import Category, Series, Tag, Release, ReleaseDate, Source, Element, VintageDate, SeriesGroup

class FredAPI:
    """
    The FredAPI class contains methods for interacting with the Federal Reserve Bank of St. Louis
    FRED® API.
    """
    # Dunder Methods
    def __init__(self, api_key, cache_mode=False):
        """
        Initialize the FredAPI class that provides functions which query FRED data.

        Args:
            api_key (str): Your FRED API key.
            async_mode (bool): Whether to use asynchronous (True) or synchronous (False) requests. Default is False (synchronous).

        Returns:
            FredAPI: An instance of the FredAPI class.

        Raises:
            ValueError: If the API key is not provided.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
        """
        self.base_url = 'https://api.stlouisfed.org/fred'
        self.api_key = api_key
        self.cache_mode = cache_mode
        self.cache = Cache(maxsize=256, ttl=3600) if cache_mode else None
        self.max_requests_per_minute = 120
        self.request_times = deque()
        self.lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(self.max_requests_per_minute // 10)
        self.Maps = self.MapsAPI(self)
        self.Async = self.AsyncAPI(self)
    # Private Methods
    def __to_pd_df(self, data: Dict) -> pd.DataFrame:
        """
        Helper method to convert a fred observation dictionary to a Pandas DataFrame.
        """
        if 'observations' not in data:
            raise ValueError("Data must contain 'observations' key")
        df = pd.DataFrame(data['observations'])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df['value'] = pd.to_numeric(df['value'], errors = 'coerce')
        return df
    def __to_pl_df(self, data: Dict) -> pl.DataFrame:
        """
        Helper method to convert a fred observation dictionary to a Polars DataFrame.
        """
        if 'observations' not in data:
            raise ValueError("Data must contain 'observations' key")
        df = pl.DataFrame(data['observations'])
        df = df.with_columns(
            pl.when(pl.col('value') == 'NA')
            .then(None)
            .otherwise(pl.col('value').cast(pl.Float64))
            .alias('value')
        )
        return df
    @retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
    def __rate_limited(self):
        """
        Ensures synchronous requests comply with rate limits.
        """
        now = time.time()
        self.request_times.append(now)
        while self.request_times and self.request_times[0] < now - 60:
            self.request_times.popleft()
        if len(self.request_times) >= self.max_requests_per_minute:
            time.sleep(60 - (now - self.request_times[0]))
    @retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
    def __fred_get_request(self, url_endpoint, data=None):
        """
        Helper method to perform a synchronous GET request to the FRED API.
        """
        key = url_endpoint + str(data) if self.cache_mode else None
        if self.cache_mode and key and self.cache.has(key):
            return self.cache.get(key)
        self.__rate_limited()
        params = {
            **(data or {}),
            'api_key': self.api_key
        }
        with httpx.Client() as client:
            response = client.get(self.base_url + url_endpoint, params=params, timeout=10)
            response.raise_for_status()
            response_json = response.json()
        if self.cache_mode and key:
            self.cache.set(key, response_json)
        return response_json
    # Public Methods
    ## Categories
    def get_category(self, category_id: int, file_type: str = 'json'):
        """Get a FRED Category

        Retrieve information about a specific category from the FRED API.

        Args:
            category_id (int): The ID of the category to retrieve.
            file_type (str, optional): The format of the response. Defaults to 'json'.

        Returns:
            Category: If only one category is returned.
            List[Category]: If multiple categories are returned.
            None: If no child categories exist.

        Raises:
            ValueError: If the response from the FRED API indicates an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> category = fred.get_category(125)
            >>> print(category.name)
            'Trade Balance'

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/category.html
        """
        if not isinstance(category_id, int) or category_id < 0:
            raise ValueError("category_id must be a non-negative integer")
        url_endpoint = '/category'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        response = self.__fred_get_request(url_endpoint, data)
        return Category.from_api_response(response)
    def get_category_children(self, category_id: int, realtime_start: Optional[str]=None,
                              realtime_end: Optional[str]=None, file_type: str ='json'):
        """Get a FRED Category's Child Categories

        Get the child categories for a specified category ID from the FRED API.

        Args:
            category_id (int): The ID for the category whose children are to be retrieved.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            file_type (str, optional): The format of the response. Default is 'json'. Other
            options include 'xml'.

        Returns:
            Category: If only one category is returned.
            List[Category]: If multiple categories are returned.
            None: If no child categories exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = FredAPI('your_api_key')
            >>> children = fred.get_category_children(13)
            >>> for child in children:
            >>>     print(child.name)
            'Exports'
            'Imports'
            'Income Payments & Receipts'
            'U.S. International Finance

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/category_children.html
        """
        if not isinstance(category_id, int) or category_id < 0:
            raise ValueError("category_id must be a non-negative integer")
        url_endpoint = '/category/children'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        return Category.from_api_response(response)
    def get_category_related(self, category_id: int, realtime_start: Optional[str]=None,
                             realtime_end: Optional[str]=None, file_type: str = 'json'):
        """Get a FRED Category's Related Categories

        Get related categories for a given category ID from the FRED API.

        Args:
            category_id (int): The ID for the category.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            file_type (str, optional): The format of the response. Default is 'json'. Options are 'json', 'xml'.

        Returns:
            Category: If only one category is returned.
            List[Category]: If multiple categories are returned.
            None: If no child categories exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = FredAPI('your_api_key')
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

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/category_related.html
        """
        if not isinstance(category_id, int) or category_id < 0:
            raise ValueError("category_id must be a non-negative integer")
        url_endpoint = '/category/related'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        return Category.from_api_response(response)
    def get_category_series(self, category_id: int, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, limit: Optional[int]=None,
                            offset: Optional[int]=None, order_by: Optional[str]=None,
                            sort_order: Optional[str]=None, filter_variable: Optional[str]=None,
                            filter_value: Optional[str]=None, tag_names: Optional[str]=None,
                            exclude_tag_names: Optional[str]=None, file_type: str ='json'):
        """ Get a FRED Category's FRED Series

        Get the series info for all series in a category from the FRED API.

        Args:
            category_id (int): The ID for a category.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 'last_updated', 'observation_start', 'observation_end', 'popularity', 'group_popularity'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'.
            filter_variable (str, optional): The attribute to filter results by. Options are 'frequency', 'units', 'seasonal_adjustment'.
            filter_value (str, optional): The value of the filter_variable to filter results by.
            tag_names (str, optional): A semicolon-separated list of tag names to filter results by.
            exclude_tag_names (str, optional): A semicolon-separated list of tag names to exclude results by.
            file_type (str, optional): The type of file to return. Default is 'json'. Options are 'json', 'xml'.

        Returns:
            Series: If only one series is returned.
            List[Series]: If multiple series are returned.
            None: If no series exist.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> series = fred.get_category_series(125)
            >>> for s in series:
            >>>     print(s.frequency)
            'Quarterly'
            'Annual'
            'Quarterly'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/category_series.html
        """
        if not isinstance(category_id, int) or category_id < 0:
            raise ValueError("category_id must be a non-negative integer")
        url_endpoint = '/category/series'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
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
            data['tag_names'] = tag_names
        if exclude_tag_names:
            data['exclude_tag_names'] = exclude_tag_names
        response = self.__fred_get_request(url_endpoint, data)
        return Series.from_api_response(response)
    def get_category_tags(self, category_id: int, realtime_start: Optional[str]=None,
                          realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                          tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                          limit: Optional[int]=None, offset: Optional[int]=None,
                          order_by: Optional[int]=None, sort_order: Optional[str]=None,
                          file_type: str ='json'):
        """Get a FRED Category's Tags

        Get the all the tags for a category from the FRED API.

        Args:
            category_id (int): The ID for a category.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            tag_names (str, optional): A semicolon delimited list of tag names to filter tags by.
            tag_group_id (int, optional): A tag group ID to filter tags by type.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name'. Default is 'series_count'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc', 'desc'. Default is 'desc'.
            file_type (str, optional): A key that indicates the type of file to send. Default is 'json'.

        Returns:
            Tag: If only one tag is returned.
            List[Tag]: If multiple tags are returned.
            None: If no tag exist.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> tags = fred.get_category_tags(125)
            >>> for tag in tags:
            >>>     print(tag.notes)
            'U.S. Department of Commerce: Bureau of Economic Analysis'
            'Country Level'
            'United States of America'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/category_tags.html
        """
        if not isinstance(category_id, int) or category_id < 0:
            raise ValueError("category_id must be a non-negative integer")
        url_endpoint = '/category/tags'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
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
        return Tag.from_api_response(response)
    def get_category_related_tags(self, category_id: int, realtime_start: Optional[str]=None,
                                  realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                  exclude_tag_names: Optional[str]=None,
                                  tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                                  limit: Optional[int]=None, offset: Optional[int]=None,
                                  order_by: Optional[int]=None, sort_order: Optional[int]=None,
                                  file_type: str = 'json'):
        """Get a FRED Category's Related Tags

        Retrieve all tags related to a specified category from the FRED API.

        Args:
            category_id (int): The ID for the category.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            tag_names (str, optional): A semicolon-delimited list of tag names to include.
            exclude_tag_names (str, optional): A semicolon-delimited list of tag names to exclude.
            tag_group_id (int, optional): The ID for a tag group.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
            sort_order (str, optional): Sort order, either 'asc' or 'desc'.
            file_type (str, optional): The type of file to return. Default is 'json'.

        Returns:
            Tag: If only one tag is returned.
            List[Tag]: If multiple tags are returned.
            None: If no series exist.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> tags = fred.get_category_related_tags(125)
            >>> for tag in tags:
            >>>     print(tag.name)
            'balance'
            'bea'
            'nation'
            'usa'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/category_related_tags.html
        """
        if not isinstance(category_id, int) or category_id < 0:
            raise ValueError("category_id must be a non-negative integer")
        url_endpoint = '/category/related_tags'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if exclude_tag_names:
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
        return Tag.from_api_response(response)
    ## Releases
    def get_releases(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                     limit: Optional[int]=None, offset: Optional[int]=None,
                     order_by: Optional[str]=None, sort_order: Optional[str]=None,
                     file_type: str ='json'):
        """Get FRED releases

        Get all economic data releases from the FRED API.

        Args:
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is None.
            offset (int, optional): The offset for the results. Default is None.
            order_by (str, optional): Order results by values such as 'release_id', 'name', 'press_release', 'realtime_start', 'realtime_end'. Default is None.
            sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order. Default is None.
            file_type (str, optional): The format of the response. Default is 'json'.

        Returns:
            Release: If only one release is returned.
            List[Releases]: If multiple Releases are returned.
            None: If no release exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> releases = fred.get_releases()
            >>> for release in releases:
            >>>     print(release.name)
            'Advance Monthly Sales for Retail and Food Services'
            'Consumer Price Index'
            'Employment Cost Index'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/releases.html
        """
        url_endpoint = '/releases'
        data: Dict[str, Union[str, int]] = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
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
        return Release.from_api_response(response)
    def get_releases_dates(self, realtime_start: Optional[str]=None,
                           realtime_end: Optional[str]=None, limit: Optional[int]=None,
                           offset: Optional[int]=None, order_by: Optional[str]=None,
                           sort_order: Optional[str]=None,
                           include_releases_dates_with_no_data: Optional[bool]=None,
                           file_type: str = 'json'):
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
            file_type (str, optional): The format of the response. Options include 'json', 'xml'. Default is 'json'.

        Returns:
            ReleaseDate: If only one release date is returned.
            List[ReleaseDate]: If multiple release dates are returned.
            None: If no release dates exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> release_dates = fred.get_releases_dates()
            >>> for release_date in release_dates:
            >>>     print(release_date.release_name)
            'Advance Monthly Sales for Retail and Food Services'
            'Failures and Assistance Transactions'
            'Manufacturing and Trade Inventories and Sales'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/releases_dates.html
        """
        url_endpoint = '/releases/dates'
        data: Dict[str, Union[str, int]] = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
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
        return ReleaseDate.from_api_response(response)
    def get_release(self, release_id: int, realtime_start: Optional[str]=None,
                    realtime_end: Optional[str]=None, file_type: str = 'json'):
        """Get a FRED release

        Get the release for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            file_type (str, optional): A key indicating the file type of the response. Default is 'json'.

        Returns:
            Release: If only one release is returned.
            List[Release]: If multiple releases are returned.
            None: If no releases exist.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> release = fred.get_release(53)
            >>> print(release.name)
            'Gross Domestic Product'

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/release.html
        """
        if not isinstance(release_id, int) or release_id < 0:
            raise ValueError("release_id must be a non-negative integer")
        url_endpoint = '/release/'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        return Release.from_api_response(response)
    def get_release_dates(self, release_id: int, realtime_start: Optional[str]=None,
                          realtime_end: Optional[str]=None, limit: Optional[int]=None,
                          offset: Optional[int]=None, sort_order: Optional[str]=None,
                          include_releases_dates_with_no_data: Optional[bool]=None,
                          file_type: str = 'json'):
        """Get FRED release dates

        Get the release dates for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            sort_order (str, optional): The order of the results. Possible values are 'asc' or 'desc'.
            include_releases_dates_with_no_data (bool, optional): Whether to include release dates with no data.
            file_type (str, optional): The type of file to return. Default is 'json'.

        Returns:
            ReleaseDate: If only one release date is returned.
            List[ReleaseDate]: If multiple release dates are returned.
            None: If no release dates exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> release_dates = fred.get_release_dates(82)
            >>> for release_date in release_dates:
            >>>     print(release_date.date)
            '1997-02-10'
            '1998-02-10'
            '1999-02-04'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/release_dates.html
        """
        url_endpoint = '/release/dates'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if not isinstance(release_id, int) or release_id < 0:
            raise ValueError("category_id must be a non-negative integer")
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
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
        return ReleaseDate.from_api_response(response)
    def get_release_series(self, release_id: int, realtime_start: Optional[str]=None,
                           realtime_end: Optional[str]=None, limit: Optional[int]=None,
                           offset: Optional[int]=None, sort_order: Optional[str]=None,
                           filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                           exclude_tag_names: Optional[str]=None, file_type: str = 'json'):
        """Get FRED release series

        Get the series in a release.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            sort_order (str, optional): Order results by values. Options are 'asc' or 'desc'.
            filter_variable (str, optional): The attribute to filter results by.
            filter_value (str, optional): The value of the filter variable.
            exclude_tag_names (str, optional): A semicolon-separated list of tag names to exclude.
            file_type (str, optional): The type of file to return. Default is 'json'.

        Returns:
            Series: If only one series is returned.
            List[Series]: If multiple series are returned.
            None: If no series exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> series = fred.get_release_series(51)
            >>> for s in series:
            >>>     print(s.id)
            'BOMTVLM133S'
            'BOMVGMM133S'
            'BOMVJMM133S'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/release_series.html
        """
        if not isinstance(release_id, int) or release_id < 0:
            raise ValueError("release_id must be a non-negative integer")
        url_endpoint = '/release/series'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
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
            data['exclude_tag_names'] = exclude_tag_names
        response = self.__fred_get_request(url_endpoint, data)
        return Series.from_api_response(response)
    def get_release_sources(self, release_id: int, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, file_type: str = 'json'):
        """Get FRED release sources

        Retrieve the sources for a specified release from the FRED API.

        Args:
            release_id (int): The ID of the release for which to retrieve sources.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. Defaults to None.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. Defaults to None.
            file_type (str, optional): The format of the response. Options are 'json' or 'xml'. Defaults to 'json'.

        Returns:
            Source: If only one source is returned.
            List[Series]: If multiple sources are returned.
            None: If no source exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> sources = fred.get_release_sources(51)
            >>> for source in sources:
            >>>     print(source.name)
                'U.S. Department of Commerce: Bureau of Economic Analysis'
                'U.S. Department of Commerce: Census Bureau'

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/release_sources.html
        """
        if not isinstance(release_id, int) or release_id < 0:
            raise ValueError("release_id must be a non-negative integer")
        url_endpoint = '/release/sources'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        return Source.from_api_response(response)
    def get_release_tags(self, release_id: int, realtime_start: Optional[str]=None,
                         realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                         tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                         limit: Optional[int]=None, offset: Optional[int]=None,
                         order_by: Optional[str]=None, file_type: str = 'json'):
        """Get FRED release tags

        Get the release tags for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            tag_names (str, optional): A semicolon delimited list of tag names.
            tag_group_id (int, optional): The ID for a tag group.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'. Default is 'series_count'.
            file_type (str, optional): The type of file to return. Default is 'json'.

        Returns:
            Tag: If only one tag is returned.
            List[Tag]: If multiple tags are returned.
            None: If no source exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> tags = fred.get_release_tags(86)
            >>> for tag in tags:
            >>>     print(tag.name)
            'commercial paper'
            'frb'
            'nation'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/release_tags.html
        """
        if not isinstance(release_id, int) or release_id < 0:
            raise ValueError("release_id must be a non-negative integer")
        url_endpoint = '/release/tags'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
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
        return Tag.from_api_response(response)
    def get_release_related_tags(self, release_id: int, realtime_start: Optional[str]=None,
                                 realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                 exclude_tag_names: Optional[str]=None, tag_group_id: Optional[str]=None,
                                 search_text: Optional[str]=None, limit: Optional[int]=None,
                                 offset: Optional[int]=None, order_by: Optional[str]=None,
                                 sort_order: Optional[str]=None, file_type: str = 'json'):
        """Get FRED release related tags

        Get release related tags for a given series search text.

        Args:
            series_search_text (str, optional): The text to match against economic data series.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            tag_names (str, optional): A semicolon delimited list of tag names to match.
            tag_group_id (str, optional): A tag group id to filter tags by type.
            tag_search_text (str, optional): The text to match against tags.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options: 'asc', 'desc'.
            file_type (str, optional): The type of file to return. Default is 'json'.

        Returns:
            Tag: If only one tag is returned.
            List[Tag]: If multiple tags are returned.
            None: If no source exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> tags = fred.get_release_related_tags('86')
            >>> for tag in tags:
            >>>     print(tag.name)
            'commercial paper'
            'frb'
            'nation'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/release_related_tags.html
        """
        if not isinstance(release_id, int) or release_id < 0:
            raise ValueError("release_id must be a non-negative integer")
        url_endpoint = '/release/related_tags'
        data: Dict[str, Union[str, int]] = {
            'release_id': release_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if exclude_tag_names:
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
        return Tag.from_api_response(response)
    def get_release_tables(self, release_id: int, element_id: Optional[int]=None,
                           include_observation_values: Optional[bool]=None,
                           observation_date: Optional[str]=None, file_type: str = 'json'):
        """Get FRED release tables

        Fetches release tables from the FRED API.

        Args:
            release_id (int): The ID for the release.
            element_id (int, optional): The ID for the element. Defaults to None.
            include_observation_values (bool, optional): Whether to include observation values. Defaults to None.
            observation_date (str, optional): The observation date in YYYY-MM-DD format. Defaults to None.
            file_type (str, optional): The format of the returned data. Defaults to 'json'.

        Returns:
            Element: If only one element is returned.
            List[Element]: If multiple elements are returned.
            None: If no element exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> elements = fred.get_release_tables(53)
            >>> for element in elements:
            >>>     print(element.series_id)
            'DGDSRL1A225NBEA'
            'DDURRL1A225NBEA'
            'DNDGRL1A225NBEA'...


        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/release_tables.html
        """
        if not isinstance(release_id, int) or release_id < 0:
            raise ValueError("release_id must be a non-negative integer")
        url_endpoint = '/release/tables'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if element_id:
            data['element_id'] = element_id
        if include_observation_values:
            data['include_observation_values'] = include_observation_values
        if observation_date:
            data['observation_date'] = observation_date
        response = self.__fred_get_request(url_endpoint, data)
        return Element.from_api_response(response)
    ## Series
    def get_series(self, series_id: str, realtime_start: Optional[str]=None,
                   realtime_end: Optional[str]=None, file_type: str = 'json'):
        """Get a FRED series

        Retrieve economic data series information from the FRED API.

        Args:
            series_id (str): The ID for the economic data series.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            file_type (str, optional): The format of the returned data. Default is 'json'. Options are 'json' and 'xml'.

        Returns:
            Series: If only one series is returned.
            List[Series]: If multiple series are returned.
            None: If no series exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> series = fred.get_series('GNPCA')
            >>> print(series.title)
            'Real Gross National Product'

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/series.html
        """
        if not isinstance(series_id, str) or series_id == '':
            raise ValueError("series_id must be a non-empty string")
        url_endpoint = '/series'
        data = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        return Series.from_api_response(response)
    def get_series_categories(self, series_id: str, realtime_start: Optional[str]=None,
                              realtime_end: Optional[str]=None, file_type: str = 'json'):
        """Get FRED series categories

        Get the categories for a specified series.

        Args:
            series_id (str): The ID for the series.
            realtime_start (str, optional): The start of the real-time period. Defaults to None.
            realtime_end (str, optional): The end of the real-time period. Defaults to None.
            file_type (str, optional): The type of file to return. Defaults to 'json'.

        Returns:
            Category: If only one category is returned.
            List[Category]: If multiple categories are returned.
            None: If no categories exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> categories = fred.get_series_categories('EXJPUS')
            >>> for category in categories:
            >>>     print(category.id)
            95
            275

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/series_categories.html
        """
        if not isinstance(series_id, str) or series_id == '':
            raise ValueError("series_id must be a non-empty string")
        url_endpoint = '/series/categories'
        data = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        return Category.from_api_response(response)
    def get_series_observations(self, series_id: str, dataframe_method: str = 'pandas',
                               realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                               limit: Optional[int]=None, offset: Optional[int]=None,
                               sort_order: Optional[str]=None,
                               observation_start: Optional[str]=None,
                               observation_end: Optional[str]=None, units: Optional[str]=None,
                               frequency: Optional[str]=None,
                               aggregation_method: Optional[str]=None,
                               output_type: Optional[int]=None, vintage_dates: Optional[str]=None,
                               file_type: str = 'json'):
        """Get FRED series observations

        Get observations for a FRED series as a pandas or polars DataFrame.

        Args:
            series_id (str): The ID for a series.
            dataframe_method (str, optional): The method to use to convert the response to a DataFrame. Options: 'pandas' or 'polars. Default is 'pandas'.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 100000.
            offset (int, optional): The offset for the results. Used for pagination.
            sort_order (str, optional): Sort results by observation date. Options: 'asc', 'desc'.
            observation_start (str, optional): The start of the observation period. Format: YYYY-MM-DD.
            observation_end (str, optional): The end of the observation period. Format: YYYY-MM-DD.
            units (str, optional): A key that indicates a data transformation. Options: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'.
            frequency (str, optional): An optional parameter to change the frequency of the observations. Options: 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'.
            aggregation_method (str, optional): A key that indicates the aggregation method used for frequency aggregation. Options: 'avg', 'sum', 'eop'.
            output_type (int, optional): An integer indicating the type of output. Options: 1 (observations by realtime period), 2 (observations by vintage date), 3 (observations by vintage date and realtime period).
            vintage_dates (str, optional): A comma-separated string of vintage dates. Format: YYYY-MM-DD.
            file_type (str, optional): A key that indicates the file type of the response. Default is 'json'. Options: 'json', 'xml'.

        Returns:
            Pandas Dataframe: dataframe_method='pandas' or is left blank.
            Polars Dataframe: If dataframe_method='polars'.
            None: If no observations exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> observations = fred.get_series_observations('GNPCA')
            >>> print(observations.head())
            date       realtime_start realtime_end     value
            1929-01-01     2025-02-13   2025-02-13  1202.659
            1930-01-01     2025-02-13   2025-02-13  1100.670
            1931-01-01     2025-02-13   2025-02-13  1029.038
            1932-01-01     2025-02-13   2025-02-13   895.802
            1933-01-01     2025-02-13   2025-02-13   883.847

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/series_observations.html
        """
        if not isinstance(series_id, str) or series_id == '':
            raise ValueError("series_id must be a non-empty string")
        if dataframe_method not in ['pandas', 'polars']:
            raise ValueError("dataframe_method must be 'pandas' or 'polars'")
        url_endpoint = '/series/observations'
        data: Dict[str, Union[str, int]] = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        if observation_start:
            data['observation_start'] = observation_start
        if observation_end:
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
            data['vintage_dates'] = vintage_dates
        response = self.__fred_get_request(url_endpoint, data)
        if dataframe_method == 'pandas':
            return self.__to_pd_df(response)
        elif dataframe_method == 'polars':
            return self.__to_pl_df(response)
    def get_series_release(self, series_id: str, realtime_start: Optional[str]=None,
                           realtime_end: Optional[str]=None, file_type: str = 'json'):
        """Get FRED series release

        Get the release for a specified series from the FRED API.

        Args:
            series_id (str): The ID for the series.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. Defaults to None.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. Defaults to None.
            file_type (str, optional): The format of the response. Options are 'json', 'xml'. Defaults to 'json'.

        Returns:
            Release: If only one release is returned.
            List[Release]: If multiple releases are returned.
            None: If no release exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> release = fred.get_series_release('GNPCA')
            >>> print(release.name)
            'Gross National Product'

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/series_release.html
        """
        if not isinstance(series_id, str) or series_id == '':
            raise ValueError("series_id must be a non-empty string")
        url_endpoint = '/series/release'
        data = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        return Release.from_api_response(response)
    def get_series_search(self, search_text: str, search_type: Optional[str]=None,
                          realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                          limit: Optional[int]=None, offset: Optional[int]=None,
                          order_by: Optional[str]=None, sort_order: Optional[str]=None,
                          filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                          tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                          file_type: str = 'json'):
        """Get FRED series search

        Searches for economic data series based on text queries.

        Args:
            search_text (str): The text to search for in economic data series.
            search_type (str, optional): The type of search to perform. Options include 'full_text' or 'series_id'. Defaults to None.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. Defaults to None.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. Defaults to None.
            limit (int, optional): The maximum number of results to return. Defaults to None.
            offset (int, optional): The offset for the results. Defaults to None.
            order_by (str, optional): The attribute to order results by. Options include 'search_rank', 'series_id', 'title', etc. Defaults to None.
            sort_order (str, optional): The order to sort results. Options include 'asc' or 'desc'. Defaults to None.
            filter_variable (str, optional): The variable to filter results by. Defaults to None.
            filter_value (str, optional): The value to filter results by. Defaults to None.
            tag_names (str, optional): A comma-separated list of tag names to include in the search. Defaults to None.
            exclude_tag_names (str, optional): A comma-separated list of tag names to exclude from the search. Defaults to None.
            file_type (str, optional): The format of the response. Options include 'json', 'xml'. Defaults to 'json'.

        Returns:
            Series: If only one series is returned.
            List[Series]: If multiple series are returned.
            None: If no series exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> series = fred.get_series_search('monetary services index')
            >>> for s in series:
            >>>     print(s.id)
            'MSIM2'
            'MSIM1P'
            'OCM1P'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/series_search.html
        """
        if not isinstance(search_text, str) or search_text == '':
            raise ValueError("search_text must be a non-empty string")
        url_endpoint = '/series/search'
        data: Dict[str, Union[str, int]] = {
            'search_text': search_text,
            'file_type': file_type
        }
        if search_type:
            data['search_type'] = search_type
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
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
            data['tag_names'] = tag_names
        if exclude_tag_names:
            data['exclude_tag_names'] = exclude_tag_names
        response = self.__fred_get_request(url_endpoint, data)
        return Series.from_api_response(response)
    def get_series_search_tags(self, series_search_text: str, realtime_start: Optional[str]=None,
                               realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                               tag_group_id: Optional[str]=None,
                               tag_search_text: Optional[str]=None, limit: Optional[int]=None,
                               offset: Optional[int]=None, order_by: Optional[str]=None,
                               sort_order: Optional[str]=None, file_type: str = 'json'):
        """Get FRED series search tags

        Get the tags for a series search.

        Args:
            series_search_text (str): The words to match against economic data series.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            tag_names (str, optional): A semicolon-delimited list of tag names to match.
            tag_group_id (str, optional): A tag group id to filter tags by type.
            tag_search_text (str, optional): The words to match against tags.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values of the specified attribute. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'. Default is 'asc'.
            file_type (str, optional): The type of file to return. Default is 'json'.

        Returns:
            Tag: If only one tag is returned.
            List[Tag]: If multiple tags are returned.
            None: If no tags exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> tags = fred.get_series_search_tags('monetary services index')
            >>> for tag in tags:
            >>>     print(tag.name)
            'academic data'
            'anderson & jones'
            'divisia'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/series_search_tags.html
        """
        if not isinstance(series_search_text, str) or series_search_text == '':
            raise ValueError("series_search_text must be a non-empty string")
        url_endpoint = '/series/search/tags'
        data: Dict[str, Union[str, int]] = {
            'series_search_text': series_search_text,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
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
        return Tag.from_api_response(response)
    def get_series_search_related_tags(self, series_search_text: str,
                                       realtime_start: Optional[str]=None,
                                       realtime_end: Optional[str]=None,
                                       tag_names: Optional[str]=None,
                                       exclude_tag_names: Optional[str]=None,
                                       tag_group_id: Optional[str]=None,
                                       tag_search_text: Optional[str]=None,
                                       limit: Optional[int]=None, offset: Optional[int]=None,
                                       order_by: Optional[str]=None, sort_order: Optional[str]=None,
                                       file_type: str = 'json'):
        """Get FRED series search related tags

        Get related tags for a series search text.

        Args:
            series_search_text (str): The text to search for series.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            tag_names (str, optional): A semicolon-delimited list of tag names to include.
            exclude_tag_names (str, optional): A semicolon-delimited list of tag names to exclude.
            tag_group_id (str, optional): The tag group id to filter tags by type.
            tag_search_text (str, optional): The text to search for tags.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options are 'asc' (ascending) or 'desc' (descending).
            file_type (str, optional): The type of file to return. Default is 'json'.

        Returns:
            Tag: If only one tag is returned.
            List[Tag]: If multiple tags are returned.
            None: If no tags exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> tags = fred.get_series_search_related_tags('mortgage rate')
            >>> for tag in tags:
            >>>     print(tag.name)
            'conventional'
            'h15'
            'interest rate'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/series_search_related_tags.html
        """
        if not isinstance(series_search_text, str) or series_search_text == '':
            raise ValueError("series_search_text must be a non-empty string")
        url_endpoint = '/series/search/related_tags'
        data: Dict[str, Union[str, int]] = {
            'series_search_text': series_search_text,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if exclude_tag_names:
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
        return Tag.from_api_response(response)
    def get_series_tags(self, series_id: str, realtime_start: Optional[str]=None,
                        realtime_end: Optional[str]=None, order_by: Optional[str]=None,
                        sort_order: Optional[str]=None, file_type: str ='json'):
        """Get FRED series tags

        Get the tags for a series.

        Args:
            series_id (str): The ID for a series.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            order_by (str, optional): Order results by values such as 'series_id', 'name', 'popularity', etc.
            sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order.
            file_type (str, optional): A key that indicates the type of file to download. Default is 'json'.

        Returns:
            Tag: If only one tag is returned.
            List[Tag]: If multiple tags are returned.
            None: If no tags exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> tags = fred.get_series_tags('GNPCA')
            >>> for tag in tags:
            >>>     print(tag.name)
            'nation'
            'nsa'
            'usa'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/series_tags.html
        """
        if not isinstance(series_id, str) or series_id == '':
            raise ValueError("series_id must be a non-empty string")
        url_endpoint = '/series/tags'
        data = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        return Tag.from_api_response(response)
    def get_series_updates(self, realtime_start: Optional[str]=None,
                           realtime_end: Optional[str]=None, limit: Optional[int]=None,
                           offset: Optional[int]=None, filter_value: Optional[str]=None,
                           start_time: Optional[str]=None, end_time: Optional[str]=None,
                           file_type: str = 'json'):
        """Get FRED series updates

        Retrieves updates for a series from the FRED API.

        Args:
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            filter_value (str, optional): Filter results by this value.
            start_time (str, optional): The start time for the updates. Format: HH:MM.
            end_time (str, optional): The end time for the updates. Format: HH:MM.
            file_type (str, optional): The format of the returned data. Default is 'json'. Options are 'json' or 'xml'.

        Returns:
            Series: If only one series is returned.
            List[Series]: If multiple series are returned.
            None: If no series exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> series = fred.get_series_updates()
            >>> for s in series:
            >>>     print(s.id)
            'PPIITM'
            'PPILFE'
            'PPIFGS'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/series_updates.html
        """
        url_endpoint = '/series/updates'
        data: Dict[str, Union[str, int]] = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if filter_value:
            data['filter_value'] = filter_value
        if start_time:
            data['start_time'] = start_time
        if end_time:
            data['end_time'] = end_time
        response = self.__fred_get_request(url_endpoint, data)
        return Series.from_api_response(response)
    def get_series_vintagedates(self, series_id: str, realtime_start: Optional[str]=None,
                                realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                offset: Optional[int]=None, sort_order: Optional[str]=None,
                                file_type: str = 'json'):
        """Get FRED series vintage dates

        Get the vintage dates for a given FRED series.

        Args:
            series_id (str): The ID for the FRED series.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            sort_order (str, optional): The order of the results. Possible values: 'asc' or 'desc'.
            file_type (str, optional): The format of the returned data. Default is 'json'.

        Returns:
            VintageDate: If only one vintage date is returned.
            List[VintageDate]: If multiple vintage dates are returned.
            None: If no vintage dates exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> vintage_dates = fred.get_series_vintagedates('GNPCA')
            >>> for vintage_date in vintage_dates:
            >>>     print(vintage_date.vintage_date)
            '1958-12-21'
            '1959-02-19'
            '1959-07-19'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
        """
        if not isinstance(series_id, str) or series_id == '':
            raise ValueError("series_id must be a non-empty string")
        url_endpoint = '/series/vintagedates'
        data: Dict[str, Union[str, int]] = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        response = self.__fred_get_request(url_endpoint, data)
        return VintageDate.from_api_response(response)
    ## Sources
    def get_sources(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                    limit: Optional[int]=None, offset: Optional[int]=None,
                    order_by: Optional[str]=None, sort_order: Optional[str]=None,
                    file_type: str = 'json'):
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
            Source: If only one source is returned.
            List[Source]: If multiple sources are returned.
            None: If no sources exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> sources = fred.get_sources()
            >>> for source in sources:
            >>>     print(source.name)
            'Board of Governors of the Federal Reserve System'
            'Federal Reserve Bank of Philadelphia'
            'Federal Reserve Bank of St. Louis'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/sources.html
        """
        url_endpoint = '/sources'
        data: Dict[str, Union[str, int]] = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
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
        return Source.from_api_response(response)
    def get_source(self, source_id: int, realtime_start: Optional[str]=None,
                   realtime_end: Optional[str]=None, file_type: str = 'json'):
        """Get a FRED source

        Retrieves information about a source from the FRED API.

        Args:
            source_id (int): The ID for the source.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. Defaults to None.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. Defaults to None.
            file_type (str, optional): The format of the file to be returned. Options are 'json', 'xml'. Defaults to 'json'.

        Returns:
            Source: If only one source is returned.
            List[Source]: If multiple sources are returned.
            None: If no sources exist.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> source = fred.get_source(1)
            >>> print(source.name)
            'Board of Governors of the Federal Reserve System'

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/source.html
        """
        if not isinstance(source_id, int) or source_id < 0:
            raise ValueError("source_id must be a non-negative integer")
        url_endpoint = '/source'
        data = {
            'source_id': source_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        response = self.__fred_get_request(url_endpoint, data)
        return Source.from_api_response(response)
    def get_source_releases(self, source_id: int , realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, limit: Optional[int]=None,
                            offset: Optional[int]=None, order_by: Optional[str]=None,
                            sort_order: Optional[str]=None, file_type: str = 'json'):
        """Get FRED source releases

        Get the releases for a specified source from the FRED API.

        Args:
            source_id (int): The ID for the source.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values such as 'release_id', 'name', etc.
            sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for
            descending.
            file_type (str, optional): The format of the response. Default is 'json'.

        Returns:
            Release: If only one release is returned.
            List[Releases]: If multiple Releases are returned.
            None: If no release exist.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> releases = fred.get_source_releases(1)
            >>> for release in releases:
            >>>     print(release.name)
            'G.17 Industrial Production and Capacity Utilization'
            'G.19 Consumer Credit'
            'G.5 Foreign Exchange Rates'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/source_releases.html
        """
        if not isinstance(source_id, int) or source_id < 0:
            raise ValueError("source_id must be a non-negative integer")
        url_endpoint = '/source/releases'
        data = {
            'source_id': source_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
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
        return Release.from_api_response(response)
    ## Tags
    def get_tags(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                 tag_names: Optional[str]=None, tag_group_id: Optional[str]=None,
                search_text: Optional[str]=None, limit: Optional[int]=None,
                offset: Optional[int]=None, order_by: Optional[str]=None,
                sort_order: Optional[str]=None, file_type: str = 'json'):
        """Get FRED tags

        Retrieve FRED tags based on specified parameters.

        Args:
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            tag_names (str, optional): A semicolon-delimited list of tag names to filter results.
            tag_group_id (str, optional): A tag group ID to filter results.
            search_text (str, optional): The words to match against tag names and descriptions.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
            sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for descending.
            file_type (str, optional): The format of the returned data. Default is 'json'.

        Returns:
            Tag: If only one tag is returned.
            List[Tag]: If multiple tags are returned.
            None: If no tags exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> tags = fred.get_tags()
            >>> for tag in tags:
            >>>     print(tag.name)
            'nation'
            'nsa'
            'oecd'...


        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/tags.html
        """
        url_endpoint = '/tags'
        data: Dict[str, Union[str, int]] = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
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
        return Tag.from_api_response(response)
    def get_related_tags(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                         tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                         tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                         limit: Optional[int]=None, offset: Optional[int]=None,
                         order_by: Optional[str]=None, sort_order: Optional[str]=None,
                         file_type: str = 'json'):
        """Get FRED related tags

        Retrieve related tags for a given set of tags from the FRED API.

        Args:
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            tag_names (str, optional): A semicolon-delimited list of tag names to include in the search.
            exclude_tag_names (str, optional): A semicolon-delimited list of tag names to exclude from the search.
            tag_group_id (str, optional): A tag group ID to filter tags by group.
            search_text (str, optional): The words to match against tag names and descriptions.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options: 'asc' (ascending), 'desc' (descending). Default is 'asc'.
            file_type (str, optional): The type of file to return. Default is 'json'.

        Returns:
            Tag: If only one tag is returned.
            List[Tag]: If multiple tags are returned.
            None: If no tags exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> tags = fred.get_related_tags()
            >>> for tag in tags:
            >>>     print(tag.name)
            'nation'
            'usa'
            'frb'...

        FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/related_tags.html
        """
        url_endpoint = '/related_tags'
        data: Dict[str, Union[str, int]] = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if exclude_tag_names:
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
        return Tag.from_api_response(response)
    def get_tags_series(self, tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                        realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                        limit: Optional[int]=None, offset: Optional[int]=None,
                        order_by: Optional[str]=None, sort_order: Optional[str]=None,
                        file_type: str = 'json'):
        """Get FRED tags series

        Get the series matching tags.

        Args:
            tag_names (str, optional): A semicolon delimited list of tag names to include in the search.
            exclude_tag_names (str, optional): A semicolon delimited list of tag names to exclude in the search.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values. Options: 'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 'last_updated', 'observation_start', 'observation_end', 'popularity', 'group_popularity'.
            sort_order (str, optional): Sort results in ascending or descending order. Options: 'asc', 'desc'.
            file_type (str, optional): The type of file to return. Default is 'json'. Options: 'json', 'xml'.

        Returns:
            Series: If only one series is returned.
            List[Series]: If multiple series are returned.
            None: If no series exist.

        Raises:
            ValueError: If the API request fails or returns an error.

        Example:
            >>> import fedfred as fd
            >>> fred = fd.FredAPI('your_api_key')
            >>> series = fred.get_tags_series('slovenia')
            >>> for s in series:
            >>>     print(s.id)
            'CPGDFD02SIA657N'
            'CPGDFD02SIA659N'
            'CPGDFD02SIM657N'...

        FRED API Documentation:
        https://fred.stlouisfed.org/docs/api/fred/tags_series.html
        """
        url_endpoint = '/tags/series'
        data: Dict[str, Union[str, int]] = {
            'file_type': file_type
        }
        if tag_names:
            data['tag_names'] = tag_names
        if exclude_tag_names:
            data['exclude_tag_names'] = exclude_tag_names
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
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
        return Series.from_api_response(response)
    class MapsAPI:
        """
        The Maps sub-class contains methods for interacting with the FRED® Maps API and GeoFRED
        endpoints.
        """
        # Dunder Methods
        def __init__(self, parent):
            """
            Initialize with a reference to the parent FredAPI instance.
            """
            self._parent = parent
            self.cache_mode = parent.cache_mode
            self.cache = parent.cache
            self.base_url = 'https://api.stlouisfed.org/geofred'
        # Private Methods
        def __to_gpd_gdf(self, data):
            """
            Helper method to convert a fred observation dictionary to a GeoPandas GeoDataFrame.
            """
            meta_data = data.get('meta', {})
            if not meta_data:
                return None
            region_type = meta_data.get('region')
            if not region_type:
                return None
            shapefile = self.get_shape_files(region_type)
            shapefile.set_index('name', inplace=True)
            shapefile['value'] = None
            shapefile['series_id'] = None
            data_section = meta_data.get('data', {})
            if not data_section:
                return shapefile
            date_key = next(iter(data_section))
            items = data_section[date_key]
            for item in items:
                if item['region'] in shapefile.index:
                    shapefile.loc[item['region'], 'value'] = item['value']
                    shapefile.loc[item['region'], 'series_id'] = item['series_id']
            return shapefile
        @retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
        def __rate_limited(self):
            """
            Ensures synchronous requests comply with rate limits.
            """
            now = time.time()
            self._parent.request_times.append(now)
            while self._parent.request_times and self._parent.request_times[0] < now - 60:
                self._parent.request_times.popleft()
            if len(self._parent.request_times) >= self._parent.max_requests_per_minute:
                time.sleep(60 - (now - self._parent.request_times[0]))
        @retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
        def __fred_get_request(self, url_endpoint, data=None):
            """
            Helper method to perform a synchronous GET request to the FRED Maps API.
            """
            key = url_endpoint + str(data) if self.cache_mode else None
            if self.cache_mode and key and self.cache.has(key):
                return self.cache.get(key)
            self.__rate_limited()
            params = {
                **(data or {}),
                'api_key': self._parent.api_key
            }
            with httpx.Client() as client:
                response = client.get(self.base_url + url_endpoint, params=params, timeout=10)
                response.raise_for_status()
                response_json = response.json()
            if self.cache_mode and key:
                self.cache.set(key, response_json)
            return response_json
        # Public Methods
        def get_shape_files(self, shape: str):
            """Get GeoFRED shape files

            This request returns shape files from FRED in GeoJSON format.

            Args:
                shape (str, required): The type of shape you want to pull GeoJSON data for. Available Shape Types: 'bea' (Bureau of Economic Anaylis Region), 'msa' (Metropolitan Statistical Area), 'frb' (Federal Reserve Bank Districts), 'necta' (New England City and Town Area), 'state', 'country', 'county' (USA Counties), 'censusregion' (US Census Regions), 'censusdivision' (US Census Divisons).

            Returns:
                GeoDataframe: If GeoJSON shape file exists.
                None: If no shapefiles exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> fred = fd.FredAPI('your_api_key').Maps
                >>> shapefile = fred.get_shape_files('state')
                >>> print(shapefile.head())
                                                            geometry  ...   type
                0  MULTIPOLYGON (((9727 7650, 10595 7650, 10595 7...  ...  State
                1  MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...  ...  State
                2  POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...  ...  State
                3  POLYGON ((-50 7955, -833 8186, -851 8223, -847...  ...  State
                4  MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...  ...  State
                [5 rows x 20 columns]

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/geofred/shapes.html
            """
            if not isinstance(shape, str) or shape == '':
                raise ValueError("shape must be a non-empty string")
            url_endpoint = '/shapes/file'
            data = {
                'shape': shape
            }
            response = self.__fred_get_request(url_endpoint, data)
            return gpd.GeoDataFrame.from_features(response['features'])
        def get_series_group(self, series_id: str, file_type: str = 'json'):
            """Get a GeoFRED series group

            This request returns the meta information needed to make requests for FRED data. Minimum
            and maximum date are also supplied for the data range available.

            Args:
                series_id (str, required): The FRED series id you want to request maps meta information for. Not all series that are in FRED have geographical data.
                filetype (str, optional): A key or file extension that indicates the type of file to send. One of the following values: 'xml', 'json'. Default is 'json'.

            Returns:
                SeriesGroup: If only one series group is returned.
                List[SeriesGroup]: If multiple series groups are returned.
                None: If no series groups exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> fred = fd.FredAPI('your_api_key').Maps
                >>> series_group = fred.get_series_group('SMU56000000500000001')
                >>> print(series_group.title)
                'State Personal Income'

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/geofred/series_group.html
            """
            if not isinstance(series_id, str) or series_id == '':
                raise ValueError("series_id must be a non-empty string")
            url_endpoint = '/series/group'
            data = {
                'series_id': series_id,
                'file_type': file_type
            }
            response = self.__fred_get_request(url_endpoint, data)
            return SeriesGroup.from_api_response(response)
        def get_series_data(self, series_id: str, date: Optional[str]=None,
                            start_date: Optional[str]=None, file_type: str = 'json'):
            """Get GeoFRED series data

            This request returns a cross section of regional data for a specified release date. If no
            date is specified, the most recent data available are returned.

            Args:
                series_id (string, required): The FRED series_id you want to request maps data for. Not all
                series that are in FRED have geographical data.
                date (string, optional): The date you want to request series group data from. Format: YYYY-MM-DD
                start_date (string, optional): The start date you want to request series group data from. This allows you to pull a range of dataFormat: YYYY-MM-DD
                file_type (string, optional): A key or file extension that indicates the type of file to send.One of the following values: 'xml', 'json'. Default is 'json'.

            Returns:
                GeoDataframe: If GeoJSON shape file exists.
                None: If no series exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> fred = fd.FredAPI('your_api_key').Maps
                >>> series_data = fred.get_series_data('SMU56000000500000001')
                >>> print(series_data.head())
                name                                                    geometry  ...             series_id
                Washington     MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...  ...  SMU53000000500000001
                California     POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...  ...  SMU06000000500000001
                Oregon         POLYGON ((-50 7955, -833 8186, -851 8223, -847...  ...  SMU41000000500000001
                Wisconsin      MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...  ...  SMU55000000500000001

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/geofred/series_data.html
            """
            if not isinstance(series_id, str) or series_id == '':
                raise ValueError("series_id must be a non-empty string")
            url_endpoint = '/series/data'
            data = {
                'series_id': series_id,
                'file_type': file_type
            }
            if date:
                data['date'] = date
            if start_date:
                data['start_date'] = start_date
            response = self.__fred_get_request(url_endpoint, data)
            return self.__to_gpd_gdf(response)
        def get_regional_data(self, series_group: str, region_type: str, date: str, season: str,
                            units: str, start_date: Optional[str]=None,
                            transformation: Optional[str]=None, frequency: Optional[str]=None,
                            aggregation_method: Optional[str]=None,
                            file_type: str = 'json'):
            """Get GeoFRED regional data

            Retrieve regional data for a specified series group and date from the FRED Maps API.

            Args:
                series_group (str): The series group for which you want to request regional data.
                region_type (str): The type of region for which you want to request data. Examples include 'state', 'county', 'msa', etc.
                date (str): The date for which you want to request regional data. Format: YYYY-MM-DD.
                season (str): The seasonality of the data. Options include 'seasonally_adjusted' or 'not_seasonally_adjusted'.
                units (str): The units of the data. Examples include 'lin', 'chg', 'pch', etc.
                start_date (str, optional): The start date for the range of data you want to request. Format: YYYY-MM-DD.
                transformation (str, optional): The data transformation to apply. Examples include 'lin', 'chg', 'pch', etc.
                frequency (str, optional): The frequency of the data. Examples include 'd', 'w', 'm', 'q', 'a'.
                aggregation_method (str, optional): The aggregation method to use. Examples include 'avg', 'sum', 'eop'.
                file_type (str, optional): The format of the response. Options are 'json' or 'xml'. Default is 'json'.

            Returns:
                GeoDataframe: If GeoJSON shape file exists.
                None: If no series exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> fred = fd.FredAPI('your_api_key').Maps
                >>> regional_data = fred.get_regional_data(series_group='882', date='2013-01-01', region_type='state', units='Dollars', frequency='a', season='NSA')
                >>> print(regional_data.head())
                name                                                    geometry hc-group  ...  value  series_id
                Massachusetts  MULTIPOLYGON (((9727 7650, 10595 7650, 10595 7...   admin1  ...  56119     MAPCPI
                Washington     MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...   admin1  ...  47448     WAPCPI
                California     POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...   admin1  ...  48074     CAPCPI
                Oregon         POLYGON ((-50 7955, -833 8186, -851 8223, -847...   admin1  ...  39462     ORPCPI
                Wisconsin      MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...   admin1  ...  42685     WIPCPI
                [5 rows x 21 columns]

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/geofred/regional_data.html
            """
            if not isinstance(series_group, str) or series_group == '':
                raise ValueError("series_group must be a non-empty string")
            if not isinstance(region_type, str) or region_type == '':
                raise ValueError("region_type must be a non-empty string")
            if not isinstance(date, str) or date == '':
                raise ValueError("date must be a non-empty string")
            if not isinstance(season, str) or season == '':
                raise ValueError("season must be a non-empty string")
            url_endpoint = '/regional/data'
            data = {
                'series_group': series_group,
                'region_type': region_type,
                'date': date,
                'season': season,
                'units': units,
                'file_type': file_type
            }
            if start_date:
                data['start_date'] = start_date
            if transformation:
                data['transformation'] = transformation
            if frequency:
                data['frequency'] = frequency
            if aggregation_method:
                data['aggregation_method'] = aggregation_method
            response = self.__fred_get_request(url_endpoint, data)
            return self.__to_gpd_gdf(response)

    class AsyncAPI:
        """
        The Async sub-class contains async methods for interacting with the Federal Reserve Bank of St. Louis
        FRED® API.
        """
        # Dunder Methods
        def __init__(self, parent):
            """
            Initialize with a reference to the parent FredAPI instance.
            """
            self._parent = parent
            self.cache_mode = parent.cache_mode
            self.cache = parent.cache
            self.Maps = self.AsyncMapsAPI(self)
        # Private Methods
        async def __to_pd_df(self, data: Dict) -> pd.DataFrame:
            """
            Helper method to convert a fred observation dictionary to a Pandas DataFrame.
            """
            df = pd.DataFrame(data['observations'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df['value'] = pd.to_numeric(df['value'], errors = 'coerce')
            return df
        async def __to_pl_df(self, data: Dict) -> pl.DataFrame:
            """
            Helper method to convert a fred observation dictionary to a Polars DataFrame.
            """
            if 'observations' not in data:
                raise ValueError("Data must contain 'observations' key")
            df = pl.DataFrame(data['observations'])
            df = df.with_columns(
                pl.when(pl.col('value') == 'NA')
                .then(None)
                .otherwise(pl.col('value').cast(pl.Float64))
                .alias('value')
            )
            return df
        async def __update_semaphore(self):
            """
            Dynamically adjusts the semaphore based on requests left in the minute.
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
        @retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
        async def __rate_limited(self):
            """
            Enforces the rate limit dynamically based on requests left.
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
        @retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
        async def __fred_get_request(self, url_endpoint, data=None):
            """
            Helper method to perform an asynchronous GET request to the FRED API.
            """
            cache_key = f"{url_endpoint}:{str(data)}"
            if self.cache_mode:
                cached_response = await asyncio.to_thread(self.cache.get, cache_key)
                if cached_response:
                    return cached_response
            await self.__rate_limited()
            params = {
                **(data or {}),
                'api_key': self._parent.api_key
            }
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(self._parent.base_url + url_endpoint, params=params, timeout=10)
                    response.raise_for_status()
                    response_json = response.json()
                    if self.cache_mode:
                        await asyncio.to_thread(self.cache.set, cache_key, response_json)
                    return response_json
                except httpx.HTTPStatusError as e:
                    raise ValueError(f"HTTP Error occurred: {e}") from e
                except httpx.RequestError as e:
                    raise ValueError(f"Request Error occurred: {e}") from e
        # Public Methods
        ## Categories
        async def get_category(self, category_id: int, file_type: str = 'json'):
            """Get a FRED Category

            Retrieve information about a specific category from the FRED API.

            Args:
                category_id (int): The ID of the category to retrieve.
                file_type (str, optional): The format of the response. Defaults to 'json'.

            Returns:
                Category: If only one category is returned.
                List[Category]: If multiple categories are returned.
                None: If no child categories exist.

            Raises:
                ValueError: If the response from the FRED API indicates an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     category = await fred.get_category(125)
                >>>     print(category.name)
                >>> asyncio.run(main())
                'Trade Balance'

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/category.html
            """
            if not isinstance(category_id, int) or category_id < 0:
                raise ValueError("category_id must be a non-negative integer")
            url_endpoint = '/category'
            data = {
                'category_id': category_id,
                'file_type': file_type
            }
            response = await self.__fred_get_request(url_endpoint, data)
            return Category.from_api_response(response)
        async def get_category_children(self, category_id: int, realtime_start: Optional[str]=None,
                                        realtime_end: Optional[str]=None, file_type: str ='json'):
            """Get a FRED Category's Child Categories

            Get the child categories for a specified category ID from the FRED API.

            Args:
                category_id (int): The ID for the category whose children are to be retrieved.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                file_type (str, optional): The format of the response. Default is 'json'. Other
                options include 'xml'.

            Returns:
                Category: If only one category is returned.
                List[Category]: If multiple categories are returned.
                None: If no child categories exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = FredAPI('your_api_key').Async
                >>>     children = await fred.get_category_children(13)
                >>>     for child in children:
                >>>         print(child.name)
                >>> asyncio.run(main())
                'Exports'
                'Imports'
                'Income Payments & Receipts'
                'U.S. International Finance

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/category_children.html
            """
            if not isinstance(category_id, int) or category_id < 0:
                raise ValueError("category_id must be a non-negative integer")
            url_endpoint = '/category/children'
            data = {
                'category_id': category_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            response = await self.__fred_get_request(url_endpoint, data)
            return Category.from_api_response(response)
        async def get_category_related(self, category_id: int, realtime_start: Optional[str]=None,
                                       realtime_end: Optional[str]=None, file_type: str = 'json'):
            """Get a FRED Category's Related Categories

            Get related categories for a given category ID from the FRED API.

            Args:
                category_id (int): The ID for the category.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                file_type (str, optional): The format of the response. Default is 'json'. Options are 'json', 'xml'.

            Returns:
                Category: If only one category is returned.
                List[Category]: If multiple categories are returned.
                None: If no child categories exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = FredAPI('your_api_key').Async
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

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/category_related.html
            """
            if not isinstance(category_id, int) or category_id < 0:
                raise ValueError("category_id must be a non-negative integer")
            url_endpoint = '/category/related'
            data = {
                'category_id': category_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            response = await self.__fred_get_request(url_endpoint, data)
            return Category.from_api_response(response)
        async def get_category_series(self, category_id: int, realtime_start: Optional[str]=None,
                                      realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                      offset: Optional[int]=None, order_by: Optional[str]=None,
                                      sort_order: Optional[str]=None, filter_variable: Optional[str]=None,
                                      filter_value: Optional[str]=None, tag_names: Optional[str]=None,
                                      exclude_tag_names: Optional[str]=None, file_type: str ='json'):
            """ Get a FRED Category's FRED Series

            Get the series info for all series in a category from the FRED API.

            Args:
                category_id (int): The ID for a category.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                limit (int, optional): The maximum number of results to return. Default is 1000.
                offset (int, optional): The offset for the results. Used for pagination.
                order_by (str, optional): Order results by values. Options are 'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 'last_updated', 'observation_start', 'observation_end', 'popularity', 'group_popularity'.
                sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'.
                filter_variable (str, optional): The attribute to filter results by. Options are 'frequency', 'units', 'seasonal_adjustment'.
                filter_value (str, optional): The value of the filter_variable to filter results by.
                tag_names (str, optional): A semicolon-separated list of tag names to filter results by.
                exclude_tag_names (str, optional): A semicolon-separated list of tag names to exclude results by.
                file_type (str, optional): The type of file to return. Default is 'json'. Options are 'json', 'xml'.

            Returns:
                Series: If only one series is returned.
                List[Series]: If multiple series are returned.
                None: If no series exist.

            Raises:
                ValueError: If the request to the FRED API fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     series = await fred.get_category_series(125)
                >>>     for s in series:
                >>>         print(s.frequency)
                >>> asyncio.run(main())
                'Quarterly'
                'Annual'
                'Quarterly'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/category_series.html
            """
            if not isinstance(category_id, int) or category_id < 0:
                raise ValueError("category_id must be a non-negative integer")
            url_endpoint = '/category/series'
            data = {
                'category_id': category_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
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
                data['tag_names'] = tag_names
            if exclude_tag_names:
                data['exclude_tag_names'] = exclude_tag_names
            response = await self.__fred_get_request(url_endpoint, data)
            return Series.from_api_response(response)
        async def get_category_tags(self, category_id: int, realtime_start: Optional[str]=None,
                                    realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                    tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                                    limit: Optional[int]=None, offset: Optional[int]=None,
                                    order_by: Optional[int]=None, sort_order: Optional[str]=None,
                                    file_type: str ='json'):
            """Get a FRED Category's Tags

            Get the all the tags for a category from the FRED API.

            Args:
                category_id (int): The ID for a category.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                tag_names (str, optional): A semicolon delimited list of tag names to filter tags by.
                tag_group_id (int, optional): A tag group ID to filter tags by type.
                search_text (str, optional): The words to find matching tags with.
                limit (int, optional): The maximum number of results to return. Default is 1000.
                offset (int, optional): The offset for the results. Used for pagination.
                order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name'. Default is 'series_count'.
                sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc', 'desc'. Default is 'desc'.
                file_type (str, optional): A key that indicates the type of file to send. Default is 'json'.

            Returns:
                Tag: If only one tag is returned.
                List[Tag]: If multiple tags are returned.
                None: If no tag exist.

            Raises:
                ValueError: If the request to the FRED API fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     tags = await fred.get_category_tags(125)
                >>>     for tag in tags:
                >>>         print(tag.notes)
                >>> asyncio.run(main())
                'U.S. Department of Commerce: Bureau of Economic Analysis'
                'Country Level'
                'United States of America'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/category_tags.html
            """
            if not isinstance(category_id, int) or category_id < 0:
                raise ValueError("category_id must be a non-negative integer")
            url_endpoint = '/category/tags'
            data = {
                'category_id': category_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if tag_names:
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
            return Tag.from_api_response(response)
        async def get_category_related_tags(self, category_id: int, realtime_start: Optional[str]=None,
                                            realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                            exclude_tag_names: Optional[str]=None,
                                            tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                                            limit: Optional[int]=None, offset: Optional[int]=None,
                                            order_by: Optional[int]=None, sort_order: Optional[int]=None,
                                            file_type: str = 'json'):
            """Get a FRED Category's Related Tags

            Retrieve all tags related to a specified category from the FRED API.

            Args:
                category_id (int): The ID for the category.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                tag_names (str, optional): A semicolon-delimited list of tag names to include.
                exclude_tag_names (str, optional): A semicolon-delimited list of tag names to exclude.
                tag_group_id (int, optional): The ID for a tag group.
                search_text (str, optional): The words to find matching tags with.
                limit (int, optional): The maximum number of results to return.
                offset (int, optional): The offset for the results.
                order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
                sort_order (str, optional): Sort order, either 'asc' or 'desc'.
                file_type (str, optional): The type of file to return. Default is 'json'.

            Returns:
                Tag: If only one tag is returned.
                List[Tag]: If multiple tags are returned.
                None: If no series exist.

            Raises:
                ValueError: If the request to the FRED API fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     tags = await fred.get_category_related_tags(125)
                >>>     for tag in tags:
                >>>         print(tag.name)
                >>> asyncio.run(main())
                'balance'
                'bea'
                'nation'
                'usa'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/category_related_tags.html
            """
            if not isinstance(category_id, int) or category_id < 0:
                raise ValueError("category_id must be a non-negative integer")
            url_endpoint = '/category/related_tags'
            data = {
                'category_id': category_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if tag_names:
                data['tag_names'] = tag_names
            if exclude_tag_names:
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
            return Tag.from_api_response(response)
        ## Releases
        async def get_releases(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                               limit: Optional[int]=None, offset: Optional[int]=None,
                               order_by: Optional[str]=None, sort_order: Optional[str]=None,
                               file_type: str ='json'):
            """Get FRED releases

            Get all economic data releases from the FRED API.

            Args:
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                limit (int, optional): The maximum number of results to return. Default is None.
                offset (int, optional): The offset for the results. Default is None.
                order_by (str, optional): Order results by values such as 'release_id', 'name', 'press_release', 'realtime_start', 'realtime_end'. Default is None.
                sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order. Default is None.
                file_type (str, optional): The format of the response. Default is 'json'.

            Returns:
                Release: If only one release is returned.
                List[Releases]: If multiple Releases are returned.
                None: If no release exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     releases = await fred.get_releases()
                >>>     for release in releases:
                >>>         print(release.name)
                >>> asyncio.run(main())
                'Advance Monthly Sales for Retail and Food Services'
                'Consumer Price Index'
                'Employment Cost Index'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/releases.html
            """
            url_endpoint = '/releases'
            data: Dict[str, Union[str, int]] = {
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
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
            return Release.from_api_response(response)
        async def get_releases_dates(self, realtime_start: Optional[str]=None,
                                     realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                     offset: Optional[int]=None, order_by: Optional[str]=None,
                                     sort_order: Optional[str]=None,
                                     include_releases_dates_with_no_data: Optional[bool]=None,
                                     file_type: str = 'json'):
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
                file_type (str, optional): The format of the response. Options include 'json', 'xml'. Default is 'json'.

            Returns:
                ReleaseDate: If only one release date is returned.
                List[ReleaseDate]: If multiple release dates are returned.
                None: If no release dates exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     release_dates = await fred.get_releases_dates()
                >>>     for release_date in release_dates:
                >>>         print(release_date.release_name)
                >>> asyncio.run(main())
                'Advance Monthly Sales for Retail and Food Services'
                'Failures and Assistance Transactions'
                'Manufacturing and Trade Inventories and Sales'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/releases_dates.html
            """
            url_endpoint = '/releases/dates'
            data: Dict[str, Union[str, int]] = {
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
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
            return ReleaseDate.from_api_response(response)
        async def get_release(self, release_id: int, realtime_start: Optional[str]=None,
                              realtime_end: Optional[str]=None, file_type: str = 'json'):
            """Get a FRED release

            Get the release for a given release ID from the FRED API.

            Args:
                release_id (int): The ID for the release.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                file_type (str, optional): A key indicating the file type of the response. Default is 'json'.

            Returns:
                Release: If only one release is returned.
                List[Release]: If multiple releases are returned.
                None: If no releases exist.

            Raises:
                ValueError: If the request to the FRED API fails or returns an error.

            Example:
                >>> >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     release = await fred.get_release(53)
                >>>     print(release.name)
                >>> asyncio.run(main())
                'Gross Domestic Product'

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/release.html
            """
            if not isinstance(release_id, int) or release_id < 0:
                raise ValueError("release_id must be a non-negative integer")
            url_endpoint = '/release/'
            data = {
                'release_id': release_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            response = await self.__fred_get_request(url_endpoint, data)
            return Release.from_api_response(response)
        async def get_release_dates(self, release_id: int, realtime_start: Optional[str]=None,
                                    realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                    offset: Optional[int]=None, sort_order: Optional[str]=None,
                                    include_releases_dates_with_no_data: Optional[bool]=None,
                                    file_type: str = 'json'):
            """Get FRED release dates

            Get the release dates for a given release ID from the FRED API.

            Args:
                release_id (int): The ID for the release.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                limit (int, optional): The maximum number of results to return.
                offset (int, optional): The offset for the results.
                sort_order (str, optional): The order of the results. Possible values are 'asc' or 'desc'.
                include_releases_dates_with_no_data (bool, optional): Whether to include release dates with no data.
                file_type (str, optional): The type of file to return. Default is 'json'.

            Returns:
                ReleaseDate: If only one release date is returned.
                List[ReleaseDate]: If multiple release dates are returned.
                None: If no release dates exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     release_dates = await fred.get_release_dates(82)
                >>>     for release_date in release_dates:
                >>>         print(release_date.date)
                >>> asyncio.run(main())
                '1997-02-10'
                '1998-02-10'
                '1999-02-04'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/release_dates.html
            """
            url_endpoint = '/release/dates'
            data = {
                'release_id': release_id,
                'file_type': file_type
            }
            if not isinstance(release_id, int) or release_id < 0:
                raise ValueError("category_id must be a non-negative integer")
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
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
            return ReleaseDate.from_api_response(response)
        async def get_release_series(self, release_id: int, realtime_start: Optional[str]=None,
                                     realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                     offset: Optional[int]=None, sort_order: Optional[str]=None,
                                     filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                                     exclude_tag_names: Optional[str]=None, file_type: str = 'json'):
            """Get FRED release series

            Get the series in a release.

            Args:
                release_id (int): The ID for the release.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            sort_order (str, optional): Order results by values. Options are 'asc' or 'desc'.
            filter_variable (str, optional): The attribute to filter results by.
            filter_value (str, optional): The value of the filter variable.
            exclude_tag_names (str, optional): A semicolon-separated list of tag names to exclude.
            file_type (str, optional): The type of file to return. Default is 'json'.

            Returns:
                Series: If only one series is returned.
                List[Series]: If multiple series are returned.
                None: If no series exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     series = await fred.get_release_series(51)
                >>>     for s in series:
                >>>         print(s.id)
                >>> asyncio.run(main())
                'BOMTVLM133S'
                'BOMVGMM133S'
                'BOMVJMM133S'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/release_series.html
            """
            if not isinstance(release_id, int) or release_id < 0:
                raise ValueError("release_id must be a non-negative integer")
            url_endpoint = '/release/series'
            data = {
                'release_id': release_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
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
                data['exclude_tag_names'] = exclude_tag_names
            response = await self.__fred_get_request(url_endpoint, data)
            return Series.from_api_response(response)
        async def get_release_sources(self, release_id: int, realtime_start: Optional[str]=None,
                                      realtime_end: Optional[str]=None, file_type: str = 'json'):
            """Get FRED release sources

            Retrieve the sources for a specified release from the FRED API.

            Args:
                release_id (int): The ID of the release for which to retrieve sources.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. Defaults to None.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. Defaults to None.
                file_type (str, optional): The format of the response. Options are 'json' or 'xml'. Defaults to 'json'.

            Returns:
                Source: If only one source is returned.
                List[Series]: If multiple sources are returned.
                None: If no source exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     sources = await fred.get_release_sources(51)
                >>>     for source in sources:
                >>>         print(source.name)
                >>> asyncio.run(main())
                    'U.S. Department of Commerce: Bureau of Economic Analysis'
                    'U.S. Department of Commerce: Census Bureau'

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/release_sources.html
            """
            if not isinstance(release_id, int) or release_id < 0:
                raise ValueError("release_id must be a non-negative integer")
            url_endpoint = '/release/sources'
            data = {
                'release_id': release_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            response = await self.__fred_get_request(url_endpoint, data)
            return Source.from_api_response(response)
        async def get_release_tags(self, release_id: int, realtime_start: Optional[str]=None,
                                   realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                   tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                                   limit: Optional[int]=None, offset: Optional[int]=None,
                                   order_by: Optional[str]=None, file_type: str = 'json'):
            """Get FRED release tags

            Get the release tags for a given release ID from the FRED API.

            Args:
                release_id (int): The ID for the release.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                tag_names (str, optional): A semicolon delimited list of tag names.
                tag_group_id (int, optional): The ID for a tag group.
                search_text (str, optional): The words to find matching tags with.
                limit (int, optional): The maximum number of results to return. Default is 1000.
                offset (int, optional): The offset for the results. Default is 0.
                order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'. Default is 'series_count'.
                file_type (str, optional): The type of file to return. Default is 'json'.

            Returns:
                Tag: If only one tag is returned.
                List[Tag]: If multiple tags are returned.
                None: If no source exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     tags = await fred.get_release_tags(86)
                >>>     for tag in tags:
                >>>         print(tag.name)
                >>> asyncio.run(main())
                'commercial paper'
                'frb'
                'nation'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/release_tags.html
            """
            if not isinstance(release_id, int) or release_id < 0:
                raise ValueError("release_id must be a non-negative integer")
            url_endpoint = '/release/tags'
            data = {
                'release_id': release_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if tag_names:
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
            return Tag.from_api_response(response)
        async def get_release_related_tags(self, release_id: int, realtime_start: Optional[str]=None,
                                           realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                           exclude_tag_names: Optional[str]=None, tag_group_id: Optional[str]=None,
                                           search_text: Optional[str]=None, limit: Optional[int]=None,
                                           offset: Optional[int]=None, order_by: Optional[str]=None,
                                           sort_order: Optional[str]=None, file_type: str = 'json'):
            """Get FRED release related tags

            Get release related tags for a given series search text.

            Args:
                series_search_text (str, optional): The text to match against economic data series.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                tag_names (str, optional): A semicolon delimited list of tag names to match.
                tag_group_id (str, optional): A tag group id to filter tags by type.
                tag_search_text (str, optional): The text to match against tags.
                limit (int, optional): The maximum number of results to return.
                offset (int, optional): The offset for the results.
                order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
                sort_order (str, optional): Sort order of results. Options: 'asc', 'desc'.
                file_type (str, optional): The type of file to return. Default is 'json'.

            Returns:
                Tag: If only one tag is returned.
                List[Tag]: If multiple tags are returned.
                None: If no source exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     tags = await fred.get_release_related_tags('86')
                >>>     for tag in tags:
                >>>         print(tag.name)
                'commercial paper'
                'frb'
                'nation'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/release_related_tags.html
            """
            if not isinstance(release_id, int) or release_id < 0:
                raise ValueError("release_id must be a non-negative integer")
            url_endpoint = '/release/related_tags'
            data: Dict[str, Union[str, int]] = {
                'release_id': release_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if tag_names:
                data['tag_names'] = tag_names
            if exclude_tag_names:
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
            return Tag.from_api_response(response)
        async def get_release_tables(self, release_id: int, element_id: Optional[int]=None,
                                     include_observation_values: Optional[bool]=None,
                                     observation_date: Optional[str]=None, file_type: str = 'json'):
            """Get FRED release tables

            Fetches release tables from the FRED API.

            Args:
                release_id (int): The ID for the release.
                element_id (int, optional): The ID for the element. Defaults to None.
                include_observation_values (bool, optional): Whether to include observation values. Defaults to None.
                observation_date (str, optional): The observation date in YYYY-MM-DD format. Defaults to None.
                file_type (str, optional): The format of the returned data. Defaults to 'json'.

            Returns:
                Element: If only one element is returned.
                List[Element]: If multiple elements are returned.
                None: If no element exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     elements = await fred.get_release_tables(53)
                >>>     for element in elements:
                >>>         print(element.series_id)
                >>> asyncio.run(main())
                'DGDSRL1A225NBEA'
                'DDURRL1A225NBEA'
                'DNDGRL1A225NBEA'...


            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/release_tables.html
            """
            if not isinstance(release_id, int) or release_id < 0:
                raise ValueError("release_id must be a non-negative integer")
            url_endpoint = '/release/tables'
            data = {
                'release_id': release_id,
                'file_type': file_type
            }
            if element_id:
                data['element_id'] = element_id
            if include_observation_values:
                data['include_observation_values'] = include_observation_values
            if observation_date:
                data['observation_date'] = observation_date
            response = await self.__fred_get_request(url_endpoint, data)
            return Element.from_api_response(response)
        ## Series
        async def get_series(self, series_id: str, realtime_start: Optional[str]=None,
                             realtime_end: Optional[str]=None, file_type: str = 'json'):
            """Get a FRED series

            Retrieve economic data series information from the FRED API.

            Args:
                series_id (str): The ID for the economic data series.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                file_type (str, optional): The format of the returned data. Default is 'json'. Options are 'json' and 'xml'.

            Returns:
                Series: If only one series is returned.
                List[Series]: If multiple series are returned.
                None: If no series exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     series = await fred.get_series('GNPCA')
                >>>     print(series.title)
                >>> asyncio.run(main())
                'Real Gross National Product'

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/series.html
            """
            if not isinstance(series_id, str) or series_id == '':
                raise ValueError("series_id must be a non-empty string")
            url_endpoint = '/series'
            data = {
                'series_id': series_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            response = await self.__fred_get_request(url_endpoint, data)
            return Series.from_api_response(response)
        async def get_series_categories(self, series_id: str, realtime_start: Optional[str]=None,
                                        realtime_end: Optional[str]=None, file_type: str = 'json'):
            """Get FRED series categories

            Get the categories for a specified series.

            Args:
                series_id (str): The ID for the series.
                realtime_start (str, optional): The start of the real-time period. Defaults to None.
                realtime_end (str, optional): The end of the real-time period. Defaults to None.
                file_type (str, optional): The type of file to return. Defaults to 'json'.

            Returns:
                Category: If only one category is returned.
                List[Category]: If multiple categories are returned.
                None: If no categories exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     categories = await fred.get_series_categories('EXJPUS')
                >>>     for category in categories:
                >>>         print(category.id)
                >>> asyncio.run(main())
                95
                275

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/series_categories.html
            """
            if not isinstance(series_id, str) or series_id == '':
                raise ValueError("series_id must be a non-empty string")
            url_endpoint = '/series/categories'
            data = {
                'series_id': series_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            response = await self.__fred_get_request(url_endpoint, data)
            return Category.from_api_response(response)
        async def get_series_observations(self, series_id: str, dataframe_method: str = 'pandas',
                                          realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                                          limit: Optional[int]=None, offset: Optional[int]=None,
                                          sort_order: Optional[str]=None,
                                          observation_start: Optional[str]=None,
                                          observation_end: Optional[str]=None, units: Optional[str]=None,
                                          frequency: Optional[str]=None,
                                          aggregation_method: Optional[str]=None,
                                          output_type: Optional[int]=None, vintage_dates: Optional[str]=None,
                                          file_type: str = 'json'):
            """Get FRED series observations

            Get observations for a FRED series as a pandas or polars DataFrame.

            Args:
                series_id (str): The ID for a series.
                dataframe_method (str, optional): The method to use to convert the response to a DataFrame. Options: 'pandas' or 'polars. Default is 'pandas'.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                limit (int, optional): The maximum number of results to return. Default is 100000.
                offset (int, optional): The offset for the results. Used for pagination.
                sort_order (str, optional): Sort results by observation date. Options: 'asc', 'desc'.
                observation_start (str, optional): The start of the observation period. Format: YYYY-MM-DD.
                observation_end (str, optional): The end of the observation period. Format: YYYY-MM-DD.
                units (str, optional): A key that indicates a data transformation. Options: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'.
                frequency (str, optional): An optional parameter to change the frequency of the observations. Options: 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'.
                aggregation_method (str, optional): A key that indicates the aggregation method used for frequency aggregation. Options: 'avg', 'sum', 'eop'.
                output_type (int, optional): An integer indicating the type of output. Options: 1 (observations by realtime period), 2 (observations by vintage date), 3 (observations by vintage date and realtime period).
                vintage_dates (str, optional): A comma-separated string of vintage dates. Format: YYYY-MM-DD.
                file_type (str, optional): A key that indicates the file type of the response. Default is 'json'. Options: 'json', 'xml'.

            Returns:
                Pandas Dataframe: dataframe_method='pandas' or is left blank.
                Polars Dataframe: If dataframe_method='polars'.
                None: If no observations exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     observations = fred.get_series_observations('GNPCA')
                >>>     print(observations.head())
                >>> asyncio.run(main())
                date       realtime_start realtime_end     value
                1929-01-01     2025-02-13   2025-02-13  1202.659
                1930-01-01     2025-02-13   2025-02-13  1100.670
                1931-01-01     2025-02-13   2025-02-13  1029.038
                1932-01-01     2025-02-13   2025-02-13   895.802
                1933-01-01     2025-02-13   2025-02-13   883.847

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/series_observations.html
            """
            if not isinstance(series_id, str) or series_id == '':
                raise ValueError("series_id must be a non-empty string")
            if dataframe_method not in ['pandas', 'polars']:
                raise ValueError("dataframe_method must be 'pandas' or 'polars'")
            url_endpoint = '/series/observations'
            data: Dict[str, Union[str, int]] = {
                'series_id': series_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if limit:
                data['limit'] = limit
            if offset:
                data['offset'] = offset
            if sort_order:
                data['sort_order'] = sort_order
            if observation_start:
                data['observation_start'] = observation_start
            if observation_end:
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
                data['vintage_dates'] = vintage_dates
            response = await self.__fred_get_request(url_endpoint, data)
            if dataframe_method == 'pandas':
                return await self.__to_pd_df(response)
            elif dataframe_method == 'polars':
                return await self.__to_pl_df(response)
        async def get_series_release(self, series_id: str, realtime_start: Optional[str]=None,
                                     realtime_end: Optional[str]=None, file_type: str = 'json'):
            """Get FRED series release

            Get the release for a specified series from the FRED API.

            Args:
                series_id (str): The ID for the series.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. Defaults to None.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. Defaults to None.
                file_type (str, optional): The format of the response. Options are 'json', 'xml'. Defaults to 'json'.

            Returns:
                Release: If only one release is returned.
                List[Release]: If multiple releases are returned.
                None: If no release exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     release = await fred.get_series_release('GNPCA')
                >>>     print(release.name)
                >>> asyncio.run(main())
                'Gross National Product'

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/series_release.html
            """
            if not isinstance(series_id, str) or series_id == '':
                raise ValueError("series_id must be a non-empty string")
            url_endpoint = '/series/release'
            data = {
                'series_id': series_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            response = await self.__fred_get_request(url_endpoint, data)
            return Release.from_api_response(response)
        async def get_series_search(self, search_text: str, search_type: Optional[str]=None,
                                    realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                                    limit: Optional[int]=None, offset: Optional[int]=None,
                                    order_by: Optional[str]=None, sort_order: Optional[str]=None,
                                    filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                                    tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                                    file_type: str = 'json'):
            """Get FRED series search

            Searches for economic data series based on text queries.

            Args:
                search_text (str): The text to search for in economic data series.
                search_type (str, optional): The type of search to perform. Options include 'full_text' or 'series_id'. Defaults to None.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. Defaults to None.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. Defaults to None.
                limit (int, optional): The maximum number of results to return. Defaults to None.
                offset (int, optional): The offset for the results. Defaults to None.
                order_by (str, optional): The attribute to order results by. Options include 'search_rank', 'series_id', 'title', etc. Defaults to None.
                sort_order (str, optional): The order to sort results. Options include 'asc' or 'desc'. Defaults to None.
                filter_variable (str, optional): The variable to filter results by. Defaults to None.
                filter_value (str, optional): The value to filter results by. Defaults to None.
                tag_names (str, optional): A comma-separated list of tag names to include in the search. Defaults to None.
                exclude_tag_names (str, optional): A comma-separated list of tag names to exclude from the search. Defaults to None.
                file_type (str, optional): The format of the response. Options include 'json', 'xml'. Defaults to 'json'.

            Returns:
                Series: If only one series is returned.
                List[Series]: If multiple series are returned.
                None: If no series exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     series = await fred.get_series_search('monetary services index')
                >>>     for s in series:
                >>>         print(s.id)
                >>> asyncio.run(main())
                'MSIM2'
                'MSIM1P'
                'OCM1P'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/series_search.html
            """
            if not isinstance(search_text, str) or search_text:
                raise ValueError("search_text must be a non-empty string")
            url_endpoint = '/series/search'
            data: Dict[str, Union[str, int]] = {
                'search_text': search_text,
                'file_type': file_type
            }
            if search_type:
                data['search_type'] = search_type
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
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
                data['tag_names'] = tag_names
            if exclude_tag_names:
                data['exclude_tag_names'] = exclude_tag_names
            response = await self.__fred_get_request(url_endpoint, data)
            return Series.from_api_response(response)
        async def get_series_search_tags(self, series_search_text: str, realtime_start: Optional[str]=None,
                                         realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                         tag_group_id: Optional[str]=None,
                                         tag_search_text: Optional[str]=None, limit: Optional[int]=None,
                                         offset: Optional[int]=None, order_by: Optional[str]=None,
                                         sort_order: Optional[str]=None, file_type: str = 'json'):
            """Get FRED series search tags

            Get the tags for a series search.

            Args:
                series_search_text (str): The words to match against economic data series.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                tag_names (str, optional): A semicolon-delimited list of tag names to match.
                tag_group_id (str, optional): A tag group id to filter tags by type.
                tag_search_text (str, optional): The words to match against tags.
                limit (int, optional): The maximum number of results to return. Default is 1000.
                offset (int, optional): The offset for the results. Default is 0.
                order_by (str, optional): Order results by values of the specified attribute. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
                sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'. Default is 'asc'.
                file_type (str, optional): The type of file to return. Default is 'json'.

            Returns:
                Tag: If only one tag is returned.
                List[Tag]: If multiple tags are returned.
                None: If no tags exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     tags = await fred.get_series_search_tags('monetary services index')
                >>>     for tag in tags:
                >>>         print(tag.name)
                >>> asyncio.run(main())
                'academic data'
                'anderson & jones'
                'divisia'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/series_search_tags.html
            """
            if not isinstance(series_search_text, str) or series_search_text == '':
                raise ValueError("series_search_text must be a non-empty string")
            url_endpoint = '/series/search/tags'
            data: Dict[str, Union[str, int]] = {
                'series_search_text': series_search_text,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if tag_names:
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
            return Tag.from_api_response(response)
        async def get_series_search_related_tags(self, series_search_text: str,
                                                 realtime_start: Optional[str]=None,
                                                 realtime_end: Optional[str]=None,
                                                 tag_names: Optional[str]=None,
                                                 exclude_tag_names: Optional[str]=None,
                                                 tag_group_id: Optional[str]=None,
                                                 tag_search_text: Optional[str]=None,
                                                 limit: Optional[int]=None, offset: Optional[int]=None,
                                                 order_by: Optional[str]=None, sort_order: Optional[str]=None,
                                                 file_type: str = 'json'):
            """Get FRED series search related tags

            Get related tags for a series search text.

            Args:
                series_search_text (str): The text to search for series.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                tag_names (str, optional): A semicolon-delimited list of tag names to include.
                exclude_tag_names (str, optional): A semicolon-delimited list of tag names to exclude.
                tag_group_id (str, optional): The tag group id to filter tags by type.
                tag_search_text (str, optional): The text to search for tags.
                limit (int, optional): The maximum number of results to return. Default is 1000.
                offset (int, optional): The offset for the results. Used for pagination.
                order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
                sort_order (str, optional): Sort order of results. Options are 'asc' (ascending) or 'desc' (descending).
                file_type (str, optional): The type of file to return. Default is 'json'.

            Returns:
                Tag: If only one tag is returned.
                List[Tag]: If multiple tags are returned.
                None: If no tags exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     tags = await fred.get_series_search_related_tags('mortgage rate')
                >>>     for tag in tags:
                >>>         print(tag.name)
                >>> asyncio.run(main())
                'conventional'
                'h15'
                'interest rate'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/series_search_related_tags.html
            """
            if not isinstance(series_search_text, str) or series_search_text == '':
                raise ValueError("series_search_text must be a non-empty string")
            url_endpoint = '/series/search/related_tags'
            data: Dict[str, Union[str, int]] = {
                'series_search_text': series_search_text,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if tag_names:
                data['tag_names'] = tag_names
            if exclude_tag_names:
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
            return Tag.from_api_response(response)
        async def get_series_tags(self, series_id: str, realtime_start: Optional[str]=None,
                                  realtime_end: Optional[str]=None, order_by: Optional[str]=None,
                                  sort_order: Optional[str]=None, file_type: str ='json'):
            """Get FRED series tags

            Get the tags for a series.

            Args:
                series_id (str): The ID for a series.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                order_by (str, optional): Order results by values such as 'series_id', 'name', 'popularity', etc.
                sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order.
                file_type (str, optional): A key that indicates the type of file to download. Default is 'json'.

            Returns:
                Tag: If only one tag is returned.
                List[Tag]: If multiple tags are returned.
                None: If no tags exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     tags = await fred.get_series_tags('GNPCA')
                >>>     for tag in tags:
                >>>         print(tag.name)
                >>> asyncio.run(main())
                'nation'
                'nsa'
                'usa'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/series_tags.html
            """
            if not isinstance(series_id, str) or series_id == '':
                raise ValueError("series_id must be a non-empty string")
            url_endpoint = '/series/tags'
            data = {
                'series_id': series_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if order_by:
                data['order_by'] = order_by
            if sort_order:
                data['sort_order'] = sort_order
            response = await self.__fred_get_request(url_endpoint, data)
            return Tag.from_api_response(response)
        async def get_series_updates(self, realtime_start: Optional[str]=None,
                                     realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                     offset: Optional[int]=None, filter_value: Optional[str]=None,
                                     start_time: Optional[str]=None, end_time: Optional[str]=None,
                                     file_type: str = 'json'):
            """Get FRED series updates

            Retrieves updates for a series from the FRED API.

            Args:
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                limit (int, optional): The maximum number of results to return. Default is 1000.
                offset (int, optional): The offset for the results. Used for pagination.
                filter_value (str, optional): Filter results by this value.
                start_time (str, optional): The start time for the updates. Format: HH:MM.
                end_time (str, optional): The end time for the updates. Format: HH:MM.
                file_type (str, optional): The format of the returned data. Default is 'json'. Options are 'json' or 'xml'.

            Returns:
                Series: If only one series is returned.
                List[Series]: If multiple series are returned.
                None: If no series exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     series = await fred.get_series_updates()
                >>>     for s in series:
                >>>         print(s.id)
                >>> asyncio.run(main())
                'PPIITM'
                'PPILFE'
                'PPIFGS'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/series_updates.html
            """
            url_endpoint = '/series/updates'
            data: Dict[str, Union[str, int]] = {
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if limit:
                data['limit'] = limit
            if offset:
                data['offset'] = offset
            if filter_value:
                data['filter_value'] = filter_value
            if start_time:
                data['start_time'] = start_time
            if end_time:
                data['end_time'] = end_time
            response = await self.__fred_get_request(url_endpoint, data)
            return Series.from_api_response(response)
        async def get_series_vintagedates(self, series_id: str, realtime_start: Optional[str]=None,
                                          realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                          offset: Optional[int]=None, sort_order: Optional[str]=None,
                                          file_type: str = 'json'):
            """Get FRED series vintage dates

            Get the vintage dates for a given FRED series.

            Args:
                series_id (str): The ID for the FRED series.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                limit (int, optional): The maximum number of results to return.
                offset (int, optional): The offset for the results.
                sort_order (str, optional): The order of the results. Possible values: 'asc' or 'desc'.
                file_type (str, optional): The format of the returned data. Default is 'json'.

            Returns:
                VintageDate: If only one vintage date is returned.
                List[VintageDate]: If multiple vintage dates are returned.
                None: If no vintage dates exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     vintage_dates = await fred.get_series_vintagedates('GNPCA')
                >>>     for vintage_date in vintage_dates:
                >>>         print(vintage_date.vintage_date)
                >>> asyncio.run(main())
                '1958-12-21'
                '1959-02-19'
                '1959-07-19'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
            """
            if not isinstance(series_id, str) or series_id == '':
                raise ValueError("series_id must be a non-empty string")
            url_endpoint = '/series/vintagedates'
            data: Dict[str, Union[str, int]] = {
                'series_id': series_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if limit:
                data['limit'] = limit
            if offset:
                data['offset'] = offset
            if sort_order:
                data['sort_order'] = sort_order
            response = await self.__fred_get_request(url_endpoint, data)
            return VintageDate.from_api_response(response)
        ## Sources
        async def get_sources(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                              limit: Optional[int]=None, offset: Optional[int]=None,
                              order_by: Optional[str]=None, sort_order: Optional[str]=None,
                              file_type: str = 'json'):
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
                Source: If only one source is returned.
                List[Source]: If multiple sources are returned.
                None: If no sources exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     sources = await fred.get_sources()
                >>>     for source in sources:
                >>>         print(source.name)
                >>> asyncio.run(main())
                'Board of Governors of the Federal Reserve System'
                'Federal Reserve Bank of Philadelphia'
                'Federal Reserve Bank of St. Louis'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/sources.html
            """
            url_endpoint = '/sources'
            data: Dict[str, Union[str, int]] = {
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
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
            return Source.from_api_response(response)
        async def get_source(self, source_id: int, realtime_start: Optional[str]=None,
                             realtime_end: Optional[str]=None, file_type: str = 'json'):
            """Get a FRED source

            Retrieves information about a source from the FRED API.

            Args:
                source_id (int): The ID for the source.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. Defaults to None.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. Defaults to None.
                file_type (str, optional): The format of the file to be returned. Options are 'json', 'xml'. Defaults to 'json'.

            Returns:
                Source: If only one source is returned.
                List[Source]: If multiple sources are returned.
                None: If no sources exist.

            Raises:
                ValueError: If the request to the FRED API fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     source = await fred.get_source(1)
                >>>     print(source.name)
                >>> asyncio.run(main())
                'Board of Governors of the Federal Reserve System'

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/source.html
            """
            if not isinstance(source_id, int):
                raise ValueError("source_id must be an integer")
            url_endpoint = '/source'
            data = {
                'source_id': source_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            response = await self.__fred_get_request(url_endpoint, data)
            return Source.from_api_response(response)
        async def get_source_releases(self, source_id: int , realtime_start: Optional[str]=None,
                                      realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                      offset: Optional[int]=None, order_by: Optional[str]=None,
                                      sort_order: Optional[str]=None, file_type: str = 'json'):
            """Get FRED source releases

            Get the releases for a specified source from the FRED API.

            Args:
                source_id (int): The ID for the source.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                limit (int, optional): The maximum number of results to return.
                offset (int, optional): The offset for the results.
                order_by (str, optional): Order results by values such as 'release_id', 'name', etc.
                sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for
                descending.
                file_type (str, optional): The format of the response. Default is 'json'.

            Returns:
                Release: If only one release is returned.
                List[Releases]: If multiple Releases are returned.
                None: If no release exist.

            Raises:
                ValueError: If the request to the FRED API fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key')
                >>>     releases = await fred.get_source_releases(1)
                >>>     for release in releases:
                >>>         print(release.name)
                >>> asyncio.run(main())
                'G.17 Industrial Production and Capacity Utilization'
                'G.19 Consumer Credit'
                'G.5 Foreign Exchange Rates'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/source_releases.html
            """
            if not isinstance(source_id, int):
                raise ValueError("source_id must be an integer")
            url_endpoint = '/source/releases'
            data = {
                'source_id': source_id,
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
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
            return Release.from_api_response(response)
        ## Tags
        async def get_tags(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                           tag_names: Optional[str]=None, tag_group_id: Optional[str]=None,
                           search_text: Optional[str]=None, limit: Optional[int]=None,
                           offset: Optional[int]=None, order_by: Optional[str]=None,
                           sort_order: Optional[str]=None, file_type: str = 'json'):
            """Get FRED tags

            Retrieve FRED tags based on specified parameters.

            Args:
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                tag_names (str, optional): A semicolon-delimited list of tag names to filter results.
                tag_group_id (str, optional): A tag group ID to filter results.
                search_text (str, optional): The words to match against tag names and descriptions.
                limit (int, optional): The maximum number of results to return. Default is 1000.
                offset (int, optional): The offset for the results. Used for pagination.
                order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
                sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for descending.
                file_type (str, optional): The format of the returned data. Default is 'json'.

            Returns:
                Tag: If only one tag is returned.
                List[Tag]: If multiple tags are returned.
                None: If no tags exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     tags = await fred.get_tags()
                >>>     for tag in tags:
                >>>         print(tag.name)
                >>> asyncio.run(main())
                'nation'
                'nsa'
                'oecd'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/tags.html
            """
            url_endpoint = '/tags'
            data: Dict[str, Union[str, int]] = {
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if tag_names:
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
            return Tag.from_api_response(response)
        async def get_related_tags(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                                   tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                                   tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                                   limit: Optional[int]=None, offset: Optional[int]=None,
                                   order_by: Optional[str]=None, sort_order: Optional[str]=None,
                                   file_type: str = 'json'):
            """Get FRED related tags

            Retrieve related tags for a given set of tags from the FRED API.

            Args:
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                tag_names (str, optional): A semicolon-delimited list of tag names to include in the search.
                exclude_tag_names (str, optional): A semicolon-delimited list of tag names to exclude from the search.
                tag_group_id (str, optional): A tag group ID to filter tags by group.
                search_text (str, optional): The words to match against tag names and descriptions.
                limit (int, optional): The maximum number of results to return. Default is 1000.
                offset (int, optional): The offset for the results. Used for pagination.
                order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
                sort_order (str, optional): Sort order of results. Options: 'asc' (ascending), 'desc' (descending). Default is 'asc'.
                file_type (str, optional): The type of file to return. Default is 'json'.

            Returns:
                Tag: If only one tag is returned.
                List[Tag]: If multiple tags are returned.
                None: If no tags exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     tags = await fred.get_related_tags()
                >>>     for tag in tags:
                >>>         print(tag.name)
                >>> asyncio.run(main())
                'nation'
                'usa'
                'frb'...

            FRED API Documentation:
                https://fred.stlouisfed.org/docs/api/fred/related_tags.html
            """
            url_endpoint = '/related_tags'
            data: Dict[str, Union[str, int]] = {
                'file_type': file_type
            }
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
                data['realtime_end'] = realtime_end
            if tag_names:
                data['tag_names'] = tag_names
            if exclude_tag_names:
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
            return Tag.from_api_response(response)
        async def get_tags_series(self, tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                                  realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                                  limit: Optional[int]=None, offset: Optional[int]=None,
                                  order_by: Optional[str]=None, sort_order: Optional[str]=None,
                                  file_type: str = 'json'):
            """Get FRED tags series

            Get the series matching tags.

            Args:
                tag_names (str, optional): A semicolon delimited list of tag names to include in the search.
                exclude_tag_names (str, optional): A semicolon delimited list of tag names to exclude in the search.
                realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
                realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
                limit (int, optional): The maximum number of results to return. Default is 1000.
                offset (int, optional): The offset for the results. Default is 0.
                order_by (str, optional): Order results by values. Options: 'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 'last_updated', 'observation_start', 'observation_end', 'popularity', 'group_popularity'.
                sort_order (str, optional): Sort results in ascending or descending order. Options: 'asc', 'desc'.
                file_type (str, optional): The type of file to return. Default is 'json'. Options: 'json', 'xml'.

            Returns:
                Series: If only one series is returned.
                List[Series]: If multiple series are returned.
                None: If no series exist.

            Raises:
                ValueError: If the API request fails or returns an error.

            Example:
                >>> import fedfred as fd
                >>> import asyncio
                >>> async def main():
                >>>     fred = fd.FredAPI('your_api_key').Async
                >>>     series = await fred.get_tags_series('slovenia')
                >>>     for s in series:
                >>>         print(s.id)
                >>> asyncio.run(main())
                'CPGDFD02SIA657N'
                'CPGDFD02SIA659N'
                'CPGDFD02SIM657N'...

            FRED API Documentation:
            https://fred.stlouisfed.org/docs/api/fred/tags_series.html
            """
            url_endpoint = '/tags/series'
            data: Dict[str, Union[str, int]] = {
                'file_type': file_type
            }
            if tag_names:
                data['tag_names'] = tag_names
            if exclude_tag_names:
                data['exclude_tag_names'] = exclude_tag_names
            if realtime_start:
                data['realtime_start'] = realtime_start
            if realtime_end:
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
            return Series.from_api_response(response)
        class AsyncMapsAPI:
            """
            The Async.Maps sub-class contains async methods for interacting with the FRED® Maps API and GeoFRED
            endpoints.
            """
            # Dunder Methods
            def __init__(self, parent):
                """
                Initialize with a reference to the parent Async instance and the grandparent FredAPI instance.
                """
                self._parent = parent
                self._grandparent = parent._parent
                self.cache_mode = self._grandparent.cache_mode
                self.cache = self._grandparent.cache
                self.base_url = 'https://api.stlouisfed.org/geofred'
            # Private Methods
            async def __to_gpd_gdf(self, data):
                """
                Helper method to convert a fred observation dictionary to a GeoPandas GeoDataFrame.
                """
                meta_data = data.get('meta', {})
                if not meta_data:
                    return None
                region_type = meta_data.get('region')
                if not region_type:
                    return None
                shapefile = await self.get_shape_files(region_type)
                shapefile.set_index('name', inplace=True)
                shapefile['value'] = None
                shapefile['series_id'] = None
                data_section = meta_data.get('data', {})
                if not data_section:
                    return shapefile
                date_key = next(iter(data_section))
                items = data_section[date_key]
                for item in items:
                    if item['region'] in shapefile.index:
                        shapefile.loc[item['region'], 'value'] = item['value']
                        shapefile.loc[item['region'], 'series_id'] = item['series_id']
                return shapefile
            async def __update_semaphore(self):
                """
                Dynamically adjusts the semaphore based on requests left in the minute.
                """
                async with self._grandparent.lock:
                    now = time.time()
                    while self._grandparent.request_times and self._grandparent.request_times[0] < now - 60:
                        self._grandparent.request_times.popleft()
                    requests_made = len(self._grandparent.request_times)
                    requests_left = max(0, self._grandparent.max_requests_per_minute - requests_made)
                    time_left = max(1, 60 - (now - (self._grandparent.request_times[0] if self._grandparent.request_times else now)))
                    new_limit = max(1, min(self._grandparent.max_requests_per_minute // 10, requests_left // 2))
                    self._grandparent.semaphore = asyncio.Semaphore(new_limit)
                    return requests_left, time_left
            @retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
            async def __rate_limited(self):
                """
                Enforces the rate limit dynamically based on requests left.
                """
                async with self._grandparent.semaphore:
                    requests_left, time_left = await self.__update_semaphore()
                    if requests_left > 0:
                        sleep_time = time_left / max(1, requests_left)
                        await asyncio.sleep(sleep_time)
                    else:
                        await asyncio.sleep(60)
                    async with self._grandparent.lock:
                        self._grandparent.request_times.append(time.time())
            @retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
            async def __fred_get_request(self, url_endpoint, data=None):
                """
                Helper method to perform an asynchronous GET request to the Maps FRED API.
                """
                cache_key = f"{url_endpoint}:{str(data)}"
                if self.cache_mode:
                    cached_response = await asyncio.to_thread(self.cache.get, cache_key)
                    if cached_response:
                        return cached_response
                await self.__rate_limited()
                params = {
                    **(data or {}),
                    'api_key': self._parent.api_key
                }
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.get(self._parent.base_url + url_endpoint, params=params, timeout=10)
                        response.raise_for_status()
                        response_json = response.json()
                        if self.cache_mode:
                            await asyncio.to_thread(self.cache.set, cache_key, response_json)
                        return response_json
                    except httpx.HTTPStatusError as e:
                        raise ValueError(f"HTTP Error occurred: {e}") from e
                    except httpx.RequestError as e:
                        raise ValueError(f"Request Error occurred: {e}") from e
            # Public Methods
            async def get_shape_files(self, shape: str):
                """Get GeoFRED shape files

                This request returns shape files from FRED in GeoJSON format.

                Args:
                    shape (str, required): The type of shape you want to pull GeoJSON data for. Available Shape Types: 'bea' (Bureau of Economic Anaylis Region), 'msa' (Metropolitan Statistical Area), 'frb' (Federal Reserve Bank Districts), 'necta' (New England City and Town Area), 'state', 'country', 'county' (USA Counties), 'censusregion' (US Census Regions), 'censusdivision' (US Census Divisons).

                Returns:
                    GeoDataframe: If GeoJSON shape file exists.
                    None: If no shapefiles exist.

                Raises:
                    ValueError: If the API request fails or returns an error.

                Example:
                    >>> import fedfred as fd
                    >>> import asyncio
                    >>> async def main():
                    >>>     fred = fd.FredMapsAPI('your_api_key').Async.Maps
                    >>>     shapefile = fred.get_shape_files('state')
                    >>>     print(shapefile.head())
                    >>> asyncio.run(main())
                                                                geometry  ...   type
                    0  MULTIPOLYGON (((9727 7650, 10595 7650, 10595 7...  ...  State
                    1  MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...  ...  State
                    2  POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...  ...  State
                    3  POLYGON ((-50 7955, -833 8186, -851 8223, -847...  ...  State
                    4  MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...  ...  State
                    [5 rows x 20 columns]

                FRED API Documentation:
                    https://fred.stlouisfed.org/docs/api/geofred/shapes.html
                """
                if not isinstance(shape, str) or shape == '':
                    raise ValueError("shape must be a non-empty string")
                url_endpoint = '/shapes/file'
                data = {
                    'shape': shape
                }
                response = await self.__fred_get_request(url_endpoint, data)
                return gpd.GeoDataFrame.from_features(response['features'])
            async def get_series_group(self, series_id: str, file_type: str = 'json'):
                """Get a GeoFRED series group

                This request returns the meta information needed to make requests for FRED data. Minimum
                and maximum date are also supplied for the data range available.

                Args:
                    series_id (str, required): The FRED series id you want to request maps meta information for. Not all series that are in FRED have geographical data.
                    filetype (str, optional): A key or file extension that indicates the type of file to send. One of the following values: 'xml', 'json'. Default is 'json'.

                Returns:
                    SeriesGroup: If only one series group is returned.
                    List[SeriesGroup]: If multiple series groups are returned.
                    None: If no series groups exist.

                Raises:
                    ValueError: If the API request fails or returns an error.

                Example:
                    >>> import fedfred as fd
                    >>> import asyncio
                    >>> async def main():
                    >>>     fred = fd.FredMapsAPI('your_api_key').Async.Maps
                    >>>     series_group = await fred.get_series_group('SMU56000000500000001')
                    >>>     print(series_group)
                    >>> asyncio.run(main())
                    'State Personal Income'

                FRED API Documentation:
                    https://fred.stlouisfed.org/docs/api/geofred/series_group.html
                """
                if not isinstance(series_id, str) or series_id == '':
                    raise ValueError("series_id must be a string")
                url_endpoint = '/series/group'
                data = {
                    'series_id': series_id,
                    'file_type': file_type
                }
                response = await self.__fred_get_request(url_endpoint, data)
                return SeriesGroup.from_api_response(response)
            async def get_series_data(self, series_id: str, date: Optional[str]=None,
                                start_date: Optional[str]=None, file_type: str = 'json'):
                """Get GeoFRED series data

                This request returns a cross section of regional data for a specified release date. If no
                date is specified, the most recent data available are returned.

                Args:
                    series_id (string, required): The FRED series_id you want to request maps data for. Not all
                    series that are in FRED have geographical data.
                    date (string, optional): The date you want to request series group data from. Format: YYYY-MM-DD
                    start_date (string, optional): The start date you want to request series group data from. This allows you to pull a range of dataFormat: YYYY-MM-DD
                    file_type (string, optional): A key or file extension that indicates the type of file to send.One of the following values: 'xml', 'json'. Default is 'json'.

                Returns:
                    GeoDataframe: If GeoJSON shape file exists.
                    None: If no series exist.

                Raises:
                    ValueError: If the API request fails or returns an error.

                Example:
                    >>> import fedfred as fd
                    >>> import asyncio
                    >>> async def main():
                    >>>     fred = fd.FredMapsAPI('your_api_key').Async.Maps
                    >>>     series_data = fred.get_series_data('SMU56000000500000001')
                    >>>     print(series_data.head())
                    >>> asyncio.run(main())
                    name                                                    geometry  ...             series_id
                    Washington     MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...  ...  SMU53000000500000001
                    California     POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...  ...  SMU06000000500000001
                    Oregon         POLYGON ((-50 7955, -833 8186, -851 8223, -847...  ...  SMU41000000500000001
                    Wisconsin      MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...  ...  SMU55000000500000001

                FRED API Documentation:
                    https://fred.stlouisfed.org/docs/api/geofred/series_data.html
                """
                if not isinstance(series_id, str) or series_id == '':
                    raise ValueError("series_id must be a string")
                url_endpoint = '/series/data'
                data = {
                    'series_id': series_id,
                    'file_type': file_type
                }
                if date:
                    data['date'] = date
                if start_date:
                    data['start_date'] = start_date
                response = await self.__fred_get_request(url_endpoint, data)
                return await self.__to_gpd_gdf(response)
            async def get_regional_data(self, series_group: str, region_type: str, date: str, season: str,
                                units: str, start_date: Optional[str]=None,
                                transformation: Optional[str]=None, frequency: Optional[str]=None,
                                aggregation_method: Optional[str]=None,
                                file_type: str = 'json'):
                """Get GeoFRED regional data

                Retrieve regional data for a specified series group and date from the FRED Maps API.

                Args:
                    series_group (str): The series group for which you want to request regional data.
                    region_type (str): The type of region for which you want to request data. Examples include 'state', 'county', 'msa', etc.
                    date (str): The date for which you want to request regional data. Format: YYYY-MM-DD.
                    season (str): The seasonality of the data. Options include 'seasonally_adjusted' or 'not_seasonally_adjusted'.
                    units (str): The units of the data. Examples include 'lin', 'chg', 'pch', etc.
                    start_date (str, optional): The start date for the range of data you want to request. Format: YYYY-MM-DD.
                    transformation (str, optional): The data transformation to apply. Examples include 'lin', 'chg', 'pch', etc.
                    frequency (str, optional): The frequency of the data. Examples include 'd', 'w', 'm', 'q', 'a'.
                    aggregation_method (str, optional): The aggregation method to use. Examples include 'avg', 'sum', 'eop'.
                    file_type (str, optional): The format of the response. Options are 'json' or 'xml'. Default is 'json'.

                Returns:
                    GeoDataframe: If GeoJSON shape file exists.
                    None: If no series exist.

                Raises:
                    ValueError: If the API request fails or returns an error.

                Example:
                    >>> import fedfred as fd
                    >>> import asyncio
                    >>> async def main():
                    >>>     fred = fd.FredMapsAPI('your_api_key').Async.Maps
                    >>>     regional_data = fred.get_regional_data(series_group='882', date='2013-01-01', region_type='state', units='Dollars', frequency='a', season='NSA')
                    >>>     print(regional_data.head())
                    >>> asyncio.run(main())
                    name                                                    geometry hc-group  ...  value  series_id
                    Massachusetts  MULTIPOLYGON (((9727 7650, 10595 7650, 10595 7...   admin1  ...  56119     MAPCPI
                    Washington     MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...   admin1  ...  47448     WAPCPI
                    California     POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...   admin1  ...  48074     CAPCPI
                    Oregon         POLYGON ((-50 7955, -833 8186, -851 8223, -847...   admin1  ...  39462     ORPCPI
                    Wisconsin      MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...   admin1  ...  42685     WIPCPI
                    [5 rows x 21 columns]

                FRED API Documentation:
                    https://fred.stlouisfed.org/docs/api/geofred/regional_data.html
                """
                if not isinstance(series_group, str) or series_group == '':
                    raise ValueError("series_group must be a string")
                if not isinstance(region_type, str) or region_type == '':
                    raise ValueError("region_type must be a string")
                if not isinstance(date, str) or date == '':
                    raise ValueError("date must be a string")
                if not isinstance(season, str) or season == '':
                    raise ValueError("season must be a string")
                if not isinstance(units, str) or units == '':
                    raise ValueError("units must be a string")
                url_endpoint = '/regional/data'
                data = {
                    'series_group': series_group,
                    'region_type': region_type,
                    'date': date,
                    'season': season,
                    'units': units,
                    'file_type': file_type
                }
                if start_date:
                    data['start_date'] = start_date
                if transformation:
                    data['transformation'] = transformation
                if frequency:
                    data['frequency'] = frequency
                if aggregation_method:
                    data['aggregation_method'] = aggregation_method
                response = await self.__fred_get_request(url_endpoint, data)
                return await self.__to_gpd_gdf(response)
