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
"""This module defines the Fred client for interacting with the Federal Reserve FRED/ALFRED API.

It provides synchronous and asynchronous methods to access various endpoints of the FRED API, including
categories, series, tags, releases, and more. The client includes features such as automatic parameter conversion,
unified response objects, rate limiting, retries, and typed results.

Classes:
    Fred: Client for the Federal Reserve FRED/ALFRED API.
    AsyncFred: Asynchronous client for the Federal Reserve FRED/ALFRED API.

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

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Any

import pandas as pd

from .._internals import _AsyncBaseClient, _BaseClient
from ..models import (
    Categories,
    Category,
    Elements,
    Release,
    ReleaseDates,
    Releases,
    Series,
    Seriess,
    Source,
    Sources,
    Tags,
    VintageDates,
)

if TYPE_CHECKING:
    import dask.dataframe as dd  # pragma: no cover
    import polars as pl  # pragma: no cover

# TODO: Fix all docstrings post error design.

__all__ = [
    "AsyncFred",
    "Fred",
]

class Fred(_BaseClient):
    """Client for the Federal Reserve FRED/ALFRED API.

    The Fred class contains methods for interacting with the Federal Reserve Bank of St. Louis
    FRED® API and provides synchronous endpoints with automatic parameter conversion, unified
    response objects, rate limiting, retries, and typed results.

    Attributes:
        caching_enabled (bool): Whether caching is enabled for API responses.
        cache_size (int): The maximum number of items to store in the cache if caching is enabled.
        keys (list[str]): list of keys in the cache if caching is enabled.

    Args:
        api_key (str, optional): Your FRED API key.
        caching_enabled (bool, optional): Whether to enable caching for API responses. Defaults to False.
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
        - :class:`fedfred.GeoFred`: GeoFred client for geospatial data from the FRED Maps API.
    """

    service_key: str = 'fred'

    # Public Methods
    ## Categories
    def get_category(self,
                     category_id: int
                     ) -> Category:
        """Get a FRED Category.

        Retrieve information about a specific category from the FRED API.

        Args:
            category_id (int): The ID of the category to retrieve.

        Returns:
            Category: The requested Category object.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> category = fred.get_category(125)
            >>> print(category.name)
            'Trade Balance'

        See Also:
            - :class:`fedfred.Category`: The Category object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_category.html
        """
        endpoint_name = 'get_category'

        data: dict[str, Any] = {
            'category_id': category_id,
        }

        response = self._client_get_request(endpoint_name, data)

        category = Category.to_object(response, client=self)

        return category

    def get_category_children(self,
                              category_id: int,
                              realtime_start: str | datetime | date | None = None,
                              realtime_end: str | datetime | date | None = None
                              ) -> Categories:
        """Get a FRED Category's Child Categories.

        Get the child categories for a specified category ID from the FRED API.

        Args:
            category_id (int): The ID for the category whose children are to be retrieved.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            Categories: A Categories object containing the child Category objects.

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
        endpoint_name = 'get_category_children'

        data: dict[str, Any] = {
            'category_id': category_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
        }

        response = self._client_get_request(endpoint_name, data)

        categories = Categories.to_object(response, client=self)

        return categories

    def get_category_related(self,
                             category_id: int,
                             realtime_start: str | datetime | date | None = None,
                             realtime_end: str | datetime | date | None = None
                             ) -> Categories:
        """Get a FRED Category's Related Categories.

        Get related categories for a given category ID from the FRED API.

        Args:
            category_id (int): The ID for the category.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime| date, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            list[Category]: A list of related Category objects.

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
        endpoint_name = 'get_category_related'

        data: dict[str, Any] = {
            'category_id': category_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = self._client_get_request(endpoint_name, data)

        categories = Categories.to_object(response, client=self)

        return categories

    def get_category_series(self,
                            category_id: int,
                            realtime_start: str | datetime | date | None = None,
                            realtime_end: str | datetime | date | None = None,
                            limit: int | None = None,
                            offset: int | None = None,
                            order_by: str | None = None,
                            sort_order: str | None = None,
                            filter_variable: str | None = None,
                            filter_value: str | None = None,
                            tag_names: str | list[str] | None = None,
                            exclude_tag_names: str | list[str] | None = None
                            ) -> Seriess:
        """Get a FRED Category's FRED Series.

        Get the series info for all series in a category from the FRED API.

        Args:
            category_id (int): The ID for a category.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 'last_updated', 'observation_start', 'observation_end', 'popularity', 'group_popularity'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'.
            filter_variable (str, optional): The attribute to filter results by. Options are 'frequency', 'units', 'seasonal_adjustment'.
            filter_value (str, optional): The value of the filter_variable to filter results by.
            tag_names (str | list, optional): A semicolon-separated list of tag names to filter results by.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude results by.

        Returns:
            list[Series]: If multiple series are returned.

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
        endpoint_name = 'get_category_series'

        data: dict[str, Any] = {
            'category_id': category_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order,
            'filter_variable': filter_variable,
            'filter_value': filter_value,
            'tag_names': tag_names,
            'exclude_tag_names': exclude_tag_names
        }

        response = self._client_get_request(endpoint_name, data)

        series = Seriess.to_object(response, client=self)

        return series

    def get_category_tags(self,
                          category_id: int,
                          realtime_start: str | datetime | date | None = None,
                          realtime_end: str | datetime | date | None = None,
                          tag_names: str | list[str] | None = None,
                          tag_group_id: int | None = None,
                          search_text: str | None = None,
                          limit: int | None = None,
                          offset: int | None = None,
                          order_by: str | None = None,
                          sort_order: str | None = None
                          ) -> Tags:
        """Get a FRED Category's Tags.

        Get the all the tags for a category from the FRED API.

        Args:
            category_id (int): The ID for a category.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names to filter tags by.
            tag_group_id (int, optional): A tag group ID to filter tags by type.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name'. Default is 'series_count'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc', 'desc'. Default is 'desc'.

        Returns:
            Tags: If multiple tags are returned.

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
        endpoint_name = 'get_category_tags'

        data: dict[str, Any] = {
            'category_id': category_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        tags = Tags.to_object(response, client=self)

        return tags

    def get_category_related_tags(self,
                                  category_id: int,
                                  realtime_start: str | datetime | date | None = None,
                                  realtime_end: str | datetime | date | None = None,
                                  tag_names: str | list[str] | None = None,
                                  exclude_tag_names: str | list[str] | None = None,
                                  tag_group_id: str | None = None,
                                  search_text: str | None = None,
                                  limit: int | None = None,
                                  offset: int | None = None,
                                  order_by: str | None = None,
                                  sort_order: str | None = None
                                  ) -> Tags:
        """Get a FRED Category's Related Tags.

        Retrieve all tags related to a specified category from the FRED API.

        Args:
            category_id (int): The ID for the category.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to include.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude.
            tag_group_id (str, optional): The ID for a tag group.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
            sort_order (str, optional): Sort order, either 'asc' or 'desc'.

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_category_related_tags'

        data: dict[str, Any] = {
            'category_id': category_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'exclude_tag_names': exclude_tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        tags = Tags.to_object(response, client=self)

        return tags

    ## Releases
    def get_releases(self,
                     realtime_start: str | datetime | date | None = None,
                     realtime_end: str | datetime | date | None = None,
                     limit: int | None = None,
                     offset: int | None = None,
                     order_by: str | None = None,
                     sort_order: str | None = None
                     ) -> Releases:
        """Get FRED releases.

        Get all economic data releases from the FRED API.

        Args:
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is None.
            offset (int, optional): The offset for the results. Default is None.
            order_by (str, optional): Order results by values such as 'release_id', 'name', 'press_release', 'realtime_start', 'realtime_end'. Default is None.
            sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order. Default is None.

        Returns:
            Releases: If multiple Releases are returned.

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
        endpoint_name = 'get_releases'

        data: dict[str, Any] = {
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        releases = Releases.to_object(response, client=self)

        return releases

    def get_releases_dates(self,
                           realtime_start: str | datetime | date | None = None,
                           realtime_end: str | datetime | date | None = None,
                           limit: int | None = None,
                           offset: int | None = None,
                           order_by: str | None = None,
                           sort_order: str | None = None,
                           include_releases_dates_with_no_data: bool | None = None
                           ) -> ReleaseDates:
        """Get FRED releases dates.

        Get all release dates for economic data releases from the FRED API.

        Args:
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is None.
            offset (int, optional): The offset for the results. Default is None.
            order_by (str, optional): Order results by values. Options include 'release_id', 'release_name', 'release_date', 'realtime_start', 'realtime_end'. Default is None.
            sort_order (str, optional): Sort order of results. Options include 'asc' (ascending) or 'desc' (descending). Default is None.
            include_releases_dates_with_no_data (bool, optional): Whether to include release dates with no data. Default is None.

        Returns:
            ReleaseDates: If multiple release dates are returned.

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
        endpoint_name = 'get_releases_dates'

        data: dict[str, Any] = {
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order,
            'include_releases_dates_with_no_data': include_releases_dates_with_no_data
        }

        response = self._client_get_request(endpoint_name, data)

        return ReleaseDates.to_object(response)

    def get_release(self,
                    release_id: int,
                    realtime_start: str | datetime | date | None = None,
                    realtime_end: str | datetime | date | None = None
                    ) -> Release:
        """Get a FRED release.

        Get the release for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            Release: If a single release is returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> release = fred.get_release(53)
            >>> print(release[0].name)
            'Gross Domestic Product'

        See Also:
            - :class:`fedfred.Releases`: The Releases object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/release.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_release.html
        """
        endpoint_name = 'get_release'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = self._client_get_request(endpoint_name, data)

        release = Release.to_object(response, client=self)

        return release

    def get_release_dates(self,
                          release_id: int,
                          realtime_start: str | datetime | date | None = None,
                          realtime_end: str | datetime | date | None = None,
                          limit: int | None = None,
                          offset: int | None = None,
                          sort_order: str | None = None,
                          include_releases_dates_with_no_data: bool | None = None
                          ) -> ReleaseDates:
        """Get FRED release dates.

        Get the release dates for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            sort_order (str, optional): The order of the results. Possible values are 'asc' or 'desc'.
            include_releases_dates_with_no_data (bool, optional): Whether to include release dates with no data.

        Returns:
            list[ReleaseDate]: If multiple release dates are returned.

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
        endpoint_name = 'get_release_dates'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'sort_order': sort_order,
            'include_releases_dates_with_no_data': include_releases_dates_with_no_data
        }

        response = self._client_get_request(endpoint_name, data)

        return ReleaseDates.to_object(response)

    def get_release_series(self,
                           release_id: int,
                           realtime_start: str | datetime | date | None = None,
                           realtime_end: str | datetime | date | None = None,
                           limit: int | None = None,
                           offset: int | None = None,
                           sort_order: str | None = None,
                           filter_variable: str | None = None,
                           filter_value: str | None = None,
                           exclude_tag_names: str | list[str] | None = None
                           ) -> Seriess:
        """Get FRED release series.

        Get the series in a release.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            sort_order (str, optional): Order results by values. Options are 'asc' or 'desc'.
            filter_variable (str, optional): The attribute to filter results by.
            filter_value (str, optional): The value of the filter variable.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude.

        Returns:
            list[Series]: If multiple series are returned.

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
        endpoint_name = 'get_release_series'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'sort_order': sort_order,
            'filter_variable': filter_variable,
            'filter_value': filter_value,
            'exclude_tag_names': exclude_tag_names
        }

        response = self._client_get_request(endpoint_name, data)

        seriess = Seriess.to_object(response, client=self)

        return seriess

    def get_release_sources(self,
                            release_id: int,
                            realtime_start: str | datetime | date | None = None,
                            realtime_end: str | datetime | date | None = None
                            ) -> Sources:
        """Get FRED release sources.

        Retrieve the sources for a specified release from the FRED API.

        Args:
            release_id (int): The ID of the release for which to retrieve sources.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str| datetime, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.

        Returns:
            list[Series]: If multiple sources are returned.

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
        endpoint_name = 'get_release_sources'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = self._client_get_request(endpoint_name, data)

        sources = Sources.to_object(response, client=self)

        return sources

    def get_release_tags(self,
                         release_id: int,
                         realtime_start: str | datetime | date | None = None,
                         realtime_end: str | datetime | date | None = None,
                         tag_names: str | list[str] | None = None,
                         tag_group_id: int | None = None,
                         search_text: str | None = None,
                         limit: int | None = None,
                         offset: int | None = None,
                         order_by: str | None = None
                         ) -> Tags:
        """Get FRED release tags.

        Get the release tags for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names.
            tag_group_id (int, optional): The ID for a tag group.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'. Default is 'series_count'.

        Returns:
            Tags: If multiple tags are returned.

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
        endpoint_name = 'get_release_tags'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by
        }

        response = self._client_get_request(endpoint_name, data)

        tags = Tags.to_object(response, client=self)

        return tags

    def get_release_related_tags(self,
                                 release_id: int,
                                 realtime_start: str | datetime | date | None = None,
                                 realtime_end: str | datetime | date | None = None,
                                 tag_names: str | list[str] | None = None,
                                 exclude_tag_names: str | list[str] | None = None,
                                 tag_group_id: str | None = None,
                                 search_text: str | None = None,
                                 limit: int | None = None,
                                 offset: int | None = None,
                                 order_by: str | None = None,
                                 sort_order: str | None = None
                                 ) -> Tags:
        """Get FRED release related tags.

        Get release related tags for a given series search text.

        Args:
            release_id (int): The ID for the release.
            series_search_text (str, optional): The text to match against economic data series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names to match.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude results by.
            tag_group_id (str, optional): A tag group id to filter tags by type.
            search_text (str, optional): The text to match against tags.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options: 'asc', 'desc'.

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_release_related_tags'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'exclude_tag_names': exclude_tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        tags = Tags.to_object(response, client=self)

        return tags

    def get_release_tables(self,
                           release_id: int,
                           element_id: int | None = None,
                           include_observation_values: bool | None = None,
                           observation_date: str | datetime | date | None = None
                           ) -> Elements:
        """Get FRED release tables.

        Fetches release tables from the FRED API.

        Args:
            release_id (int): The ID for the release.
            element_id (int, optional): The ID for the element. Defaults to None.
            include_observation_values (bool, optional): Whether to include observation values. Defaults to None.
            observation_date (str | datetime | date, optional): The observation date in YYYY-MM-DD string format. Defaults to None.

        Returns:
            Elements: If multiple elements are returned.

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

        data: dict[str, Any] = {
            'release_id': release_id,
            'element_id': element_id,
            'include_observation_values': include_observation_values,
            'observation_date': observation_date
        }

        response = self._client_get_request(url_endpoint, data)

        return Elements.to_object(response, client=self)

    def get_release_observations(self, release_id: int, limit: int | None = None) -> list[BulkRelease]: # TODO: needs complete implementation/redesign
        """Get FRED release observations in bulk.

        Fetches release observations in bulk from the FRED API.

        Args:
            release_id (int): The ID for the release.
            limit (int, optional): The maximum number of results to return per request.1

        Returns:
            list[BulkRelease]: If multiple bulk release observations are returned.

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
        endpoint_name = 'get_release_observations'

        return_list = []

        has_more = True

        data: dict[str, Any] = {
            'release_id': release_id,
            'limit': limit
        }

        while has_more:
            response = self._client_get_request(endpoint_name, data)

            converted = BulkRelease.to_object(response, client=self)

            return_list.append(converted)

            if response['has_more']:
                data['next_cursor'] = response['next_cursor']

            else:
                has_more = False

        return return_list

    ## Series
    def get_series(self,
                   series_id: str,
                   realtime_start: str | datetime | date | None = None,
                   realtime_end: str | datetime | date | None = None
                   ) -> Series:
        """Get a FRED series.

        Retrieve economic data series information from the FRED API.

        Args:
            series_id (str): The ID for the economic data series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            Series: If a single series is returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> series = fred.get_series('GNPCA')
            >>> print(series.title)
            'Real Gross National Product'

        See Also:
            - :class:`fedfred.Series`: The Series object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series.html
        """
        endpoint_name = 'get_series'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = self._client_get_request(endpoint_name, data)

        series = Series.to_object(response, client=self)

        return series

    def get_series_categories(self,
                              series_id: str,
                              realtime_start: str | datetime | date | None = None,
                              realtime_end: str | datetime | date | None = None
                              ) -> Categories:
        """Get FRED series categories.

        Get the categories for a specified series.

        Args:
            series_id (str): The ID for the series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            Categories: If multiple categories are returned.

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
        endpoint_name = 'get_series_categories'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = self._client_get_request(endpoint_name, data)

        categories = Categories.to_object(response, client=self)

        return categories

    def get_series_observations(self,
                                series_id: str,
                                dataframe_method: str | None = None,
                                realtime_start: str | datetime | date | None = None,
                                realtime_end: str | datetime | date | None = None,
                                limit: int | None = None,
                                offset: int | None = None,
                                sort_order: str | None = None,
                                observation_start: str | datetime | date | None = None,
                                observation_end: str | datetime | date | None = None,
                                units: str | None = None,
                                frequency: str | None = None,
                                aggregation_method: str | None = None,
                                output_type: int | None = None,
                                vintage_dates: str | datetime | date | list[str | datetime | date | None] | None = None
                                ) -> pd.DataFrame | 'pl.DataFrame' | 'dd.DataFrame':
        """Get FRED series observations.

        Get observations for a FRED series as a pandas or polars DataFrame.

        Args:
            series_id (str): The ID for a series.
            dataframe_method (str, optional): The method to use to convert the response to a DataFrame. Options: 'pandas', 'polars', or 'dask'. Default is 'pandas'.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 100000.
            offset (int, optional): The offset for the results. Used for pagination.
            sort_order (str, optional): Sort results by observation date. Options: 'asc', 'desc'.
            observation_start (str | datetime | date, optional): The start of the observation period. String format: YYYY-MM-DD.
            observation_end (str | datetime | date, optional): The end of the observation period. String format: YYYY-MM-DD.
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
        endpoint_name = 'get_series_observations'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'sort_order': sort_order,
            'observation_start': observation_start,
            'observation_end': observation_end,
            'units': units,
            'frequency': frequency,
            'aggregation_method': aggregation_method,
            'output_type': output_type,
            'vintage_dates': vintage_dates
        }

        response = self._client_get_request(endpoint_name, data)

        df_method = _resolve_dataframe_converter(dataframe_method)

        return df_method(response)

    def get_series_release(self,
                           series_id: str,
                           realtime_start: str | datetime | date | None = None,
                           realtime_end: str | datetime | date | None = None
                           ) -> Release:
        """Get FRED series release.

        Get the release for a specified series from the FRED API.

        Args:
            series_id (str): The ID for the series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.

        Returns:
            Releases: If multiple releases are returned.

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
        endpoint_name = 'get_series_release'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = self._client_get_request(endpoint_name, data)

        release = Release.to_object(response, client=self)

        return release

    def get_series_search(self,
                          search_text: str,
                          search_type: str | None = None,
                          realtime_start: str | datetime | date | None = None,
                          realtime_end: str | datetime | date | None = None,
                          limit: int | None = None,
                          offset: int | None = None,
                          order_by: str | None = None,
                          sort_order: str | None = None,
                          filter_variable: str | None = None,
                          filter_value: str | None = None,
                          tag_names: str | list[str] | None = None,
                          exclude_tag_names: str | list[str] | None = None
                          ) -> Seriess:
        """Get FRED series search.

        Searches for economic data series based on text queries.

        Args:
            search_text (str): The text to search for in economic data series. if 'search_type'='series_id', it's possible to put an '*' in the middle of a string. 'm*sl' finds any series starting with 'm' and ending with 'sl'.
            search_type (str, optional): The type of search to perform. Options include 'full_text' or 'series_id'. Defaults to None.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            limit (int, optional): The maximum number of results to return. Defaults to None.
            offset (int, optional): The offset for the results. Defaults to None.
            order_by (str, optional): The attribute to order results by. Options include 'search_rank', 'series_id', 'title', etc. Defaults to None.
            sort_order (str, optional): The order to sort results. Options include 'asc' or 'desc'. Defaults to None.
            filter_variable (str, optional): The variable to filter results by. Defaults to None.
            filter_value (str, optional): The value to filter results by. Defaults to None.
            tag_names (str | list, optional): A comma-separated list of tag names to include in the search. Defaults to None.
            exclude_tag_names (str | list, optional): A comma-separated list of tag names to exclude from the search. Defaults to None.

        Returns:
            Seriess: If multiple series are returned.

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
        endpoint_name = 'get_series_search'

        data: dict[str, Any] = {
            'search_text': search_text,
            'search_type': search_type,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order,
            'filter_variable': filter_variable,
            'filter_value': filter_value,
            'tag_names': tag_names,
            'exclude_tag_names': exclude_tag_names
        }

        response = self._client_get_request(endpoint_name, data)

        seriess = Seriess.to_object(response, client=self)

        return seriess

    def get_series_search_tags(self,
                               series_search_text: str,
                               realtime_start: str | datetime | date | None = None,
                               realtime_end: str | datetime | date | None = None,
                               tag_names: str | list[str] | None = None,
                               tag_group_id: str | None = None,
                               tag_search_text: str | None = None,
                               limit: int | None = None,
                               offset: int | None = None,
                               order_by: str | None = None,
                               sort_order: str | None = None
                               ) -> Tags:
        """Get FRED series search tags.

        Get the tags for a series search.

        Args:
            series_search_text (str): The words to match against economic data series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to match.
            tag_group_id (str, optional): A tag group id to filter tags by type.
            tag_search_text (str, optional): The words to match against tags.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values of the specified attribute. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'. Default is 'asc'.

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_series_search_tags'

        data: dict[str, Any] = {
            'series_search_text': series_search_text,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'tag_group_id': tag_group_id,
            'tag_search_text': tag_search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        tags = Tags.to_object(response, client=self)

        return tags

    def get_series_search_related_tags(self,
                                       series_search_text: str,
                                       tag_names: str | list[str] | None = None,
                                       realtime_start: str | datetime | date | None = None,
                                       realtime_end: str | datetime | date | None = None,
                                       exclude_tag_names: str | list[str] | None = None,
                                       tag_group_id: str | None = None,
                                       tag_search_text: str | None = None,
                                       limit: int | None = None,
                                       offset: int | None = None,
                                       order_by: str | None = None,
                                       sort_order: str | None = None
                                       ) -> Tags:
        """Get FRED series search related tags.

        Get related tags for a series search text.

        Args:
            series_search_text (str): The text to search for series.
            tag_names (str | list): A semicolon-delimited list of tag names to include.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude.
            tag_group_id (str, optional): The tag group id to filter tags by type.
            tag_search_text (str, optional): The text to search for tags.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options are 'asc' (ascending) or 'desc' (descending).

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_series_search_related_tags'

        data: dict[str, Any] = {
            'series_search_text': series_search_text,
            'tag_names': tag_names,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'exclude_tag_names': exclude_tag_names,
            'tag_group_id': tag_group_id,
            'tag_search_text': tag_search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order

        }

        response = self._client_get_request(endpoint_name, data)

        tags = Tags.to_object(response, client=self)

        return tags

    def get_series_tags(self,
                        series_id: str,
                        realtime_start: str | datetime | date | None = None,
                        realtime_end: str | datetime | date | None = None,
                        order_by: str | None = None,
                        sort_order: str | None = None
                        ) -> Tags:
        """Get FRED series tags.

        Get the tags for a series.

        Args:
            series_id (str): The ID for a series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            order_by (str, optional): Order results by values such as 'series_id', 'name', 'popularity', etc.
            sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order.

        Returns:
            list[Tag]: If multiple tags are returned.

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
            - :class:`fedfred.Tags`: The Tags object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_tags.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series_tags.html
        """
        endpoint_name = 'get_series_tags'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        tags = Tags.to_object(response, client=self)

        return tags

    def get_series_updates(self,                                                    # TODO: Consider rechecking response schema and changing return model.
                           realtime_start: str | datetime | date | None = None,
                           realtime_end: str | datetime | date | None = None,
                           limit: int | None = None,
                           offset: int | None = None,
                           filter_value: str | None = None,
                           start_time: str | datetime | time | None = None,
                           end_time: str | datetime | time | None = None
                           ) -> Seriess:
        """Get FRED series updates.

        Retrieves updates for a series from the FRED API.

        Args:
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            filter_value (str, optional): Filter results by this value.
            start_time (str | datetime | time, optional): The start time for the updates. String format: HH:MM.
            end_time (str | datetime | time, optional): The end time for the updates. String format: HH:MM.

        Returns:
            list[Series]: If multiple series are returned.

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
            - :class:`fedfred.Seriess`: The Seriess object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_updates.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_series_updates.html
        """
        endpoint_name = 'get_series_updates'

        data: dict[str, Any] = {
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'filter_value': filter_value,
            'start_time': start_time,
            'end_time': end_time
        }

        response = self._client_get_request(endpoint_name, data)

        seriess = Seriess.to_object(response, client=self)

        return seriess

    def get_series_vintagedates(self,
                                series_id: str,
                                realtime_start: str | datetime | date | None = None,
                                realtime_end: str | datetime | date | None = None,
                                limit: int | None = None,
                                offset: int | None = None,
                                sort_order: str | None = None
                                ) -> VintageDates:
        """Get FRED series vintage dates.

        Get the vintage dates for a given FRED series.

        Args:
            series_id (str): The ID for the FRED series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            sort_order (str, optional): The order of the results. Possible values: 'asc' or 'desc'.

        Returns:
            VintageDates: If multiple vintage dates are returned.

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
        endpoint_name = 'get_series_vintagedates'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        return VintageDates.to_object(response)

    ## Sources
    def get_sources(self,
                    realtime_start: str | datetime | date | None = None,
                    realtime_end: str | datetime | date | None = None,
                    limit: int | None = None,
                    offset: int | None = None,
                    order_by: str | None = None,
                    sort_order: str | None = None
                    ) -> Sources:
        """Get FRED sources.

        Retrieve sources of economic data from the FRED API.

        Args:
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000, maximum is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'source_id', 'name', 'realtime_start', 'realtime_end'.
            sort_order (str, optional): Sort order of results. Options are 'asc' (ascending) or 'desc' (descending).

        Returns:
            Sources: If multiple sources are returned.

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
        endpoint_name = 'get_sources'

        data: dict[str, Any] = {
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        sources = Sources.to_object(response, client=self)

        return sources

    def get_source(self,
                   source_id: int,
                   realtime_start: str | datetime | date | None = None,
                   realtime_end: str | datetime | date | None = None
                   ) -> Source:
        """Get a FRED source.

        Retrieves information about a source from the FRED API.

        Args:
            source_id (int): The ID for the source.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.

        Returns:
            Source: If a single source is returned.

        Raises:
            ValueError: If the request to the FRED API fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> source = fred.get_source(1)
            >>> print(source.name)
            'Board of Governors of the Federal Reserve System'

        See Also:
            - :class:`fedfred.Source`: The Source object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/source.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Fred.get_source.html
        """
        endpoint_name = 'get_source'

        data: dict[str, Any] = {
            'source_id': source_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = self._client_get_request(endpoint_name, data)

        source = Source.to_object(response, client=self)

        return source

    def get_source_releases(self,
                            source_id: int,
                            realtime_start: str | datetime | date | None = None,
                            realtime_end: str | datetime | date | None = None,
                            limit: int | None = None,
                            offset: int | None = None,
                            order_by: str | None = None,
                            sort_order: str | None = None
                            ) -> Releases:
        """Get FRED source releases.

        Get the releases for a specified source from the FRED API.

        Args:
            source_id (int): The ID for the source.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values such as 'release_id', 'name', etc.
            sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for descending.

        Returns:
            list[Release]: If multiple Releases are returned.

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
        endpoint_name = 'get_source_releases'

        data: dict[str, Any] = {
            'source_id': source_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        releases = Releases.to_object(response, client=self)

        return releases

    ## Tags
    def get_tags(self,
                 realtime_start: str | datetime | date | None = None,
                 realtime_end: str | datetime | date | None = None,
                 tag_names: str | list[str] | None = None,
                 tag_group_id: str | None = None,
                 search_text: str | None = None,
                 limit: int | None = None,
                 offset: int | None = None,
                 order_by: str | None = None,
                 sort_order: str | None = None
                 ) -> Tags:
        """Get FRED tags.

        Retrieve FRED tags based on specified parameters.

        Args:
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to filter results.
            tag_group_id (str, optional): A tag group ID to filter results.
            search_text (str, optional): The words to match against tag names and descriptions.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
            sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for descending.

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_tags'

        data: dict[str, Any] = {
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        tags = Tags.to_object(response, client=self)

        return tags

    def get_related_tags(self,
                         tag_names: str | list[str],
                         realtime_start: str | datetime | date | None = None,
                         realtime_end: str | datetime | date | None = None,
                         exclude_tag_names: str | list[str] | None = None,
                         tag_group_id: str | None = None,
                         search_text: str | None = None,
                         limit: int | None = None,
                         offset: int | None = None,
                         order_by: str | None = None,
                         sort_order: str | None = None
                         ) -> Tags:
        """Get FRED related tags.

        Retrieve related tags for a given set of tags from the FRED API.

        Args:
            tag_names (str | list): A semicolon-delimited list of tag names to include in the search.
            realtime_start (str | datetime | date, optional): The start of the real-time period. Strinng format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude from the search.
            tag_group_id (str, optional): A tag group ID to filter tags by group.
            search_text (str, optional): The words to match against tag names and descriptions.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options: 'asc' (ascending), 'desc' (descending). Default is 'asc'.

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_related_tags'

        data: dict[str, Any] = {
            'tag_names': tag_names,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'exclude_tag_names': exclude_tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        tags = Tags.to_object(response, client=self)

        return tags

    def get_tags_series(self,
                        tag_names: str | list[str],
                        exclude_tag_names: str | list[str] | None = None,
                        realtime_start: str | datetime | date | None = None,
                        realtime_end: str | datetime | date | None = None,
                        limit: int | None = None,
                        offset: int | None = None,
                        order_by: str | None = None,
                        sort_order: str | None = None
                        ) -> Seriess:
        """Get FRED tags series.

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
            list[Series]: If multiple series are returned.

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
        endpoint_name = 'get_tags_series'

        data: dict[str, Any] = {
            'tag_names': tag_names,
            'exclude_tag_names': exclude_tag_names,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = self._client_get_request(endpoint_name, data)

        seriess = Seriess.to_object(response, client=self)

        return seriess

class AsyncFred(_AsyncBaseClient):
    """Asynchronous client for the Federal Reserve FRED/ALFRED API.

    The AsyncFred class contains methods for interacting with the Federal Reserve Bank of St. Louis
    FRED® API and provides asynchronous endpoints with automatic parameter conversion, unified
    response objects, rate limiting, retries, and typed results.

    Attributes:
        caching_enabled (bool): Whether caching is enabled for API responses.
        cache_size (int): The maximum number of items to store in the cache if caching is enabled.
        keys (str): list of keys in the cache if caching is enabled.

    Args:
        api_key (str, optional): Your FRED API key.
        caching_enabled (bool, optional): Whether to enable caching for API responses. Defaults to False.
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
        >>> fred = fd.AsyncFred(api_key='your_api_key')

    Warnings:
        Ensure that the parent Fred instance is properly configured before using AsyncFred.

    See Also:
        - :class:`fedfred.AsyncGeoFred`: The asynchronous client for the FRED Maps API.
        - :func:`fedfred.set_api_key`: Function to set the global FRED API key.
    """

    service_key = 'fred'

    # Public Methods
    ## Categories
    async def get_category(self,
                           category_id: int
                           ) -> Category:
        """Get a FRED Category.

        Retrieve information about a specific category from the FRED API.

        Args:
            category_id (int): The ID of the category to retrieve.

        Returns:
            list[Category]: If multiple categories are returned.

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
        endpoint_name = 'get_category'

        data: dict[str, Any] = {
            'category_id': category_id
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Category.to_object_async(response)

    async def get_category_children(self,
                                    category_id: int,
                                    realtime_start: str | datetime | date | None = None,
                                    realtime_end: str | datetime | date | None = None
                                    ) -> Categories:
        """Get a FRED Category's Child Categories.

        Get the child categories for a specified category ID from the FRED API.

        Args:
            category_id (int): The ID for the category whose children are to be retrieved.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            list[Category]: If multiple categories are returned.

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
        endpoint_name = 'get_category_children'

        data: dict[str, Any] = {
            'category_id': category_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Categories.to_object_async(response)

    async def get_category_related(self,
                                   category_id: int,
                                   realtime_start: str | datetime | date | None = None,
                                   realtime_end: str | datetime | date | None = None
                                   ) -> Categories:
        """Get a FRED Category's Related Categories.

        Get related categories for a given category ID from the FRED API.

        Args:
            category_id (int): The ID for the category.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            list[Category]: If multiple categories are returned.

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
        endpoint_name = 'get_category_related'

        data: dict[str, Any] = {
            'category_id': category_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Categories.to_object_async(response)

    async def get_category_series(self,
                                  category_id: int,
                                  realtime_start: str | datetime | date | None = None,
                                  realtime_end: str | datetime | date | None = None,
                                  limit: int | None = None,
                                  offset: int | None = None,
                                  order_by: str | None = None,
                                  sort_order: str | None = None,
                                  filter_variable: str | None = None,
                                  filter_value: str | None = None,
                                  tag_names: str | list[str] | None = None,
                                  exclude_tag_names: str | list[str] | None = None
                                  ) -> Seriess:
        """Get a FRED Category's FRED Series.

        Get the series info for all series in a category from the FRED API.

        Args:
            category_id (int): The ID for a category.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 'last_updated', 'observation_start', 'observation_end', 'popularity', 'group_popularity'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'.
            filter_variable (str, optional): The attribute to filter results by. Options are 'frequency', 'units', 'seasonal_adjustment'.
            filter_value (str, optional): The value of the filter_variable to filter results by.
            tag_names (str | list, optional): A semicolon-separated list of tag names to filter results by.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude results by.

        Returns:
            list[Series]: If multiple series are returned.

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
            - :class:`fedfred.Seriess`: The Seriess object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/category_series.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncFred.get_category_series.html
        """
        endpoint_name = 'get_category_series'

        data: dict[str, Any] = {
            'category_id': category_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order,
            'filter_variable': filter_variable,
            'filter_value': filter_value,
            'tag_names': tag_names,
            'exclude_tag_names': exclude_tag_names
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Seriess.to_object_async(response)

    async def get_category_tags(self,
                                category_id: int,
                                realtime_start: str | datetime | date | None = None,
                                realtime_end: str | datetime | date | None = None,
                                tag_names: str | list[str] | None = None,
                                tag_group_id: int | None = None,
                                search_text: str | None = None,
                                limit: int | None = None,
                                offset: int | None = None,
                                order_by: str | None = None,
                                sort_order: str | None = None
                                ) -> Tags:
        """Get a FRED Category's Tags.

        Get the all the tags for a category from the FRED API.

        Args:
            category_id (int): The ID for a category.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names to filter tags by.
            tag_group_id (int, optional): A tag group ID to filter tags by type.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name'. Default is 'series_count'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc', 'desc'. Default is 'desc'.

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_category_tags'

        data: dict[str, Any] = {
            'category_id': category_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Tags.to_object_async(response)

    async def get_category_related_tags(self,
                                        category_id: int,
                                        realtime_start: str | datetime | date | None = None,
                                        realtime_end: str | datetime | date | None = None,
                                        tag_names: str | list[str] | None = None,
                                        exclude_tag_names: str | list[str] | None = None,
                                        tag_group_id: str | None = None,
                                        search_text: str | None = None,
                                        limit: int | None = None,
                                        offset: int | None = None,
                                        order_by: str | None = None,
                                        sort_order: str | None = None
                                        ) -> Tags:
        """Get a FRED Category's Related Tags.

        Retrieve all tags related to a specified category from the FRED API.

        Args:
            category_id (int): The ID for the category.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to include.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude.
            tag_group_id (str, optional): The ID for a tag group.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
            sort_order (str, optional): Sort order, either 'asc' or 'desc'.

        Returns:
            Tags: If multiple tags are returned.

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
        endpoint_name = 'get_category_related_tags'

        data: dict[str, Any] = {
            'category_id': category_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'exclude_tag_names': exclude_tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Tags.to_object_async(response)

    ## Releases
    async def get_releases(self,
                           realtime_start: str | datetime | date | None = None,
                           realtime_end: str | datetime | date | None = None,
                           limit: int | None = None,
                           offset: int | None = None,
                           order_by: str | None = None,
                           sort_order: str | None = None
                           ) -> Releases:
        """Get FRED releases.

        Get all economic data releases from the FRED API.

        Args:
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is None.
            offset (int, optional): The offset for the results. Default is None.
            order_by (str, optional): Order results by values such as 'release_id', 'name', 'press_release', 'realtime_start', 'realtime_end'. Default is None.
            sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order. Default is None.

        Returns:
            list[Release]: If multiple Releases are returned.

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
        endpoint_name = 'get_releases'

        data: dict[str, Any] = {
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Releases.to_object_async(response)

    async def get_releases_dates(self,
                                 realtime_start: str | datetime | date | None = None,
                                 realtime_end: str | datetime | date | None = None,
                                 limit: int | None = None,
                                 offset: int | None = None,
                                 order_by: str | None = None,
                                 sort_order: str | None = None,
                                 include_releases_dates_with_no_data: bool | None = None
                                 ) -> ReleaseDates:
        """Get FRED releases dates.

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
            list[ReleaseDate]: If multiple release dates are returned.

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
        endpoint_name = 'get_releases_dates'

        data: dict[str, Any] = {
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order,
            'include_releases_dates_with_no_data': include_releases_dates_with_no_data
        }

        response = await self._client_get_request(endpoint_name, data)

        return await ReleaseDates.to_object_async(response)

    async def get_release(self,
                          release_id: int,
                          realtime_start: str | datetime | date | None = None,
                          realtime_end: str | datetime | date | None = None
                          ) -> Release:
        """Get a FRED release.

        Get the release for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            list[Release]: If multiple releases are returned.

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
        endpoint_name = 'get_release'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Release.to_object_async(response)

    async def get_release_dates(self,
                                release_id: int,
                                realtime_start: str | datetime | date | None = None,
                                realtime_end: str | datetime | date | None = None,
                                limit: int | None = None,
                                offset: int | None = None,
                                sort_order: str | None = None,
                                include_releases_dates_with_no_data: bool | None = None
                                ) -> ReleaseDates:
        """Get FRED release dates.

        Get the release dates for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            sort_order (str, optional): The order of the results. Possible values are 'asc' or 'desc'.
            include_releases_dates_with_no_data (bool, optional): Whether to include release dates with no data.

        Returns:
            ReleaseDates: If multiple release dates are returned.

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
        endpoint_name = 'get_release_dates'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'sort_order': sort_order,
            'include_releases_dates_with_no_data': include_releases_dates_with_no_data
        }

        response = await self._client_get_request(endpoint_name, data)

        return await ReleaseDates.to_object_async(response)

    async def get_release_series(self,
                                 release_id: int,
                                 realtime_start: str | datetime | date | None = None,
                                 realtime_end: str | datetime | date | None = None,
                                 limit: int | None = None,
                                 offset: int | None = None,
                                 sort_order: str | None = None,
                                 filter_variable: str | None = None,
                                 filter_value: str | None = None,
                                 exclude_tag_names: str | list[str] | None = None
                                 ) -> Seriess:
        """Get FRED release series.

        Get the series in a release.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            sort_order (str, optional): Order results by values. Options are 'asc' or 'desc'.
            filter_variable (str, optional): The attribute to filter results by.
            filter_value (str, optional): The value of the filter variable.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude.

        Returns:
            list[Series]: If multiple series are returned.

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
        endpoint_name = 'get_release_series'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'sort_order': sort_order,
            'filter_variable': filter_variable,
            'filter_value': filter_value,
            'exclude_tag_names': exclude_tag_names
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Seriess.to_object_async(response)

    async def get_release_sources(self,
                                  release_id: int,
                                  realtime_start: str | datetime | date | None = None,
                                  realtime_end: str | datetime | date | None = None
                                  ) -> Sources:
        """Get FRED release sources.

        Retrieve the sources for a specified release from the FRED API.

        Args:
            release_id (int): The ID of the release for which to retrieve sources.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str| datetime, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.

        Returns:
            list[Series]: If multiple sources are returned.

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
        endpoint_name = 'get_release_sources'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Sources.to_object_async(response)

    async def get_release_tags(self,
                               release_id: int,
                               realtime_start: str | datetime | date | None = None,
                               realtime_end: str | datetime | date | None = None,
                               tag_names: str | list[str] | None = None,
                               tag_group_id: int | None = None,
                               search_text: str | None = None,
                               limit: int | None = None,
                               offset: int | None = None,
                               order_by: str | None = None
                               ) -> Tags:
        """Get FRED release tags.

        Get the release tags for a given release ID from the FRED API.

        Args:
            release_id (int): The ID for the release.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names.
            tag_group_id (int, optional): The ID for a tag group.
            search_text (str, optional): The words to find matching tags with.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'. Default is 'series_count'.

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_release_tags'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Tags.to_object_async(response)

    async def get_release_related_tags(self,
                                       release_id: int,
                                       realtime_start: str | datetime | date | None = None,
                                       realtime_end: str | datetime | date | None = None,
                                       tag_names: str | list[str] | None = None,
                                       exclude_tag_names: str | list[str] | None = None,
                                       tag_group_id: str | None = None,
                                       search_text: str | None = None,
                                       limit: int | None = None,
                                       offset: int | None = None,
                                       order_by: str | None = None,
                                       sort_order: str | None = None
                                       ) -> Tags:
        """Get FRED release related tags.

        Get release related tags for a given series search text.

        Args:
            release_id (int): The ID for the release.
            search_text (str, optional): The text to match against economic data series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon delimited list of tag names to match.
            exclude_tag_names (str | list, optional): A semicolon-separated list of tag names to exclude results by.
            tag_group_id (str, optional): A tag group id to filter tags by type.
            tag_search_text (str, optional): The text to match against tags.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options: 'asc', 'desc'.

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_release_related_tags'

        data: dict[str, Any] = {
            'release_id': release_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'exclude_tag_names': exclude_tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Tags.to_object_async(response)

    async def get_release_tables(self,
                                 release_id: int,
                                 element_id: int | None = None,
                                 include_observation_values: bool | None = None,
                                 observation_date: str | datetime | date | None = None
                                 ) -> Elements:
        """Get FRED release tables.

        Fetches release tables from the FRED API.

        Args:
            release_id (int): The ID for the release.
            element_id (int, optional): The ID for the element. Defaults to None.
            include_observation_values (bool, optional): Whether to include observation values. Defaults to None.
            observation_date (str | datetime | date, optional): The observation date in YYYY-MM-DD string format. Defaults to None.

        Returns:
            Elements: If multiple elements are returned.

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
        endpoint_name = 'get_release_tables'

        data: dict[str, Any] = {
            'release_id': release_id,
            'element_id': element_id,
            'include_observation_values': include_observation_values,
            'observation_date': observation_date
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Elements.to_object_async(response)

    async def get_release_observations(self, release_id: int, limit: int | None = None) -> list[BulkRelease]:
        """Get FRED release observations in bulk.

        Fetches release observations in bulk from the FRED API.

        Args:
            release_id (int): The ID for the release.
            limit (int, optional): The maximum number of results to return per request.

        Returns:
            list[BulkRelease]: If multiple bulk release observations are returned.

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
        endpoint_name = 'get_release_observations'

        return_list = []

        has_more = True

        data: dict[str, Any] = {
            'release_id': release_id,
            'limit': limit
        }

        while has_more:

            response = await self._client_get_request(endpoint_name, data)

            converted = await BulkRelease.to_object_async(response)

            return_list.append(converted)

            if response['has_more']:
                data['next_cursor'] = response['next_cursor']

            else:
                has_more = False

        return return_list

    ## Series
    async def get_series(self,
                         series_id: str,
                         realtime_start: str | datetime | date | None = None,
                         realtime_end: str | datetime | date | None = None
                         ) -> Series:
        """Get a FRED series.

        Retrieve economic data series information from the FRED API.

        Args:
            series_id (str): The ID for the economic data series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            Series: If a single series is returned.

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
        endpoint_name = 'get_series'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Series.to_object_async(response)

    async def get_series_categories(self,
                                    series_id: str,
                                    realtime_start: str | datetime | date | None = None,
                                    realtime_end: str | datetime | date | None = None
                                    ) -> Categories:
        """Get FRED series categories.

        Get the categories for a specified series.

        Args:
            series_id (str): The ID for the series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.

        Returns:
            Categories: If multiple categories are returned.

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
        endpoint_name = 'get_series_categories'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Categories.to_object_async(response)

    async def get_series_observations(self,
                                      series_id: str,
                                      dataframe_method: str | None = None,
                                      realtime_start: str | datetime | date | None = None,
                                      realtime_end: str | datetime | date | None = None,
                                      limit: int | None = None,
                                      offset: int | None = None,
                                      sort_order: str | None = None,
                                      observation_start: str | datetime | date | None = None,
                                      observation_end: str | datetime | date | None = None,
                                      units: str | None = None,
                                      frequency: str | None = None,
                                      aggregation_method: str | None = None,
                                      output_type: int | None = None,
                                      vintage_dates: str | datetime | date | list[str | datetime | date | None] | None = None
                                      ) -> pd.DataFrame | 'pl.DataFrame' | 'dd.DataFrame':
        """Get FRED series observations.

        Get observations for a FRED series as a pandas or polars DataFrame.

        Args:
            series_id (str): The ID for a series.
            dataframe_method (str, optional): The method to use to convert the response to a DataFrame. Options: 'pandas', 'polars', or 'dask'. Default is 'pandas'.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 100000.
            offset (int, optional): The offset for the results. Used for pagination.
            sort_order (str, optional): Sort results by observation date. Options: 'asc', 'desc'.
            observation_start (str | datetime | date, optional): The start of the observation period. String format: YYYY-MM-DD.
            observation_end (str | datetime | date, optional): The end of the observation period. String format: YYYY-MM-DD.
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
        endpoint_name = 'get_series_observations'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'sort_order': sort_order,
            'observation_start': observation_start,
            'observation_end': observation_end,
            'units': units,
            'frequency': frequency,
            'aggregation_method': aggregation_method,
            'output_type': output_type,
            'vintage_dates': vintage_dates
        }

        response = await self._client_get_request(endpoint_name, data)

        df_method = await _resolve_dataframe_converter_async(dataframe_method)

        return await df_method(response)

    async def get_series_release(self,
                                 series_id: str,
                                 realtime_start: str | datetime | date | None = None,
                                 realtime_end: str | datetime | date | None = None
                                 ) -> Release:
        """Get FRED series release.

        Get the release for a specified series from the FRED API.

        Args:
            series_id (str): The ID for the series.
            realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. Defaults to None.
            realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. Defaults to None.

        Returns:
            Release: If a single release is returned.

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
        endpoint_name = 'get_series_release'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Release.to_object_async(response)

    async def get_series_search(self,
                                search_text: str,
                                search_type: str | None = None,
                                realtime_start: str | datetime | date | None = None,
                                realtime_end: str | datetime | date | None = None,
                                limit: int | None = None,
                                offset: int | None = None,
                                order_by: str | None = None,
                                sort_order: str | None = None,
                                filter_variable: str | None = None,
                                filter_value: str | None = None,
                                tag_names: str | list[str] | None = None,
                                exclude_tag_names: str | list[str] | None = None
                                ) -> Seriess:
        """Get FRED series search.

        Searches for economic data series based on text queries.

        Args:
            search_text (str): The text to search for in economic data series. if 'search_type'='series_id', it's possible to put an '*' in the middle of a string. 'm*sl' finds any series starting with 'm' and ending with 'sl'.
            search_type (str, optional): The type of search to perform. Options include 'full_text' or 'series_id'. Defaults to None.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            limit (int, optional): The maximum number of results to return. Defaults to None.
            offset (int, optional): The offset for the results. Defaults to None.
            order_by (str, optional): The attribute to order results by. Options include 'search_rank', 'series_id', 'title', etc. Defaults to None.
            sort_order (str, optional): The order to sort results. Options include 'asc' or 'desc'. Defaults to None.
            filter_variable (str, optional): The variable to filter results by. Defaults to None.
            filter_value (str, optional): The value to filter results by. Defaults to None.
            tag_names (str | list, optional): A comma-separated list of tag names to include in the search. Defaults to None.
            exclude_tag_names (str | list, optional): A comma-separated list of tag names to exclude from the search. Defaults to None.

        Returns:
            list[Series]: If multiple series are returned.

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
        endpoint_name = 'get_series_search'

        data: dict[str, Any] = {
            'search_text': search_text,
            'search_type': search_type,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order,
            'filter_variable': filter_variable,
            'filter_value': filter_value,
            'tag_names': tag_names,
            'exclude_tag_names': exclude_tag_names
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Seriess.to_object_async(response)

    async def get_series_search_tags(self,
                                     series_search_text: str,
                                     realtime_start: str | datetime | date | None = None,
                                     realtime_end: str | datetime | date | None = None,
                                     tag_names: str | list[str] | None = None,
                                     tag_group_id: str | None = None,
                                     tag_search_text: str | None = None,
                                     limit: int | None = None,
                                     offset: int | None = None,
                                     order_by: str | None = None,
                                     sort_order: str | None = None
                                     ) -> Tags:
        """Get FRED series search tags.

        Get the tags for a series search.

        Args:
            series_search_text (str): The words to match against economic data series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.r
            tag_names (str | list, optional): A semicolon-delimited list of tag names to match.
            tag_group_id (str, optional): A tag group id to filter tags by type.
            tag_search_text (str, optional): The words to match against tags.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Default is 0.
            order_by (str, optional): Order results by values of the specified attribute. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort results in ascending or descending order. Options are 'asc' or 'desc'. Default is 'asc'.

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_series_search_tags'

        data: dict[str, Any] = {
            'series_search_text': series_search_text,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'tag_group_id': tag_group_id,
            'tag_search_text': tag_search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Tags.to_object_async(response)

    async def get_series_search_related_tags(self,
                                             series_search_text: str,
                                             tag_names: str | list[str],
                                             realtime_start: str | datetime | date | None = None,
                                             realtime_end: str | datetime | date | None = None,
                                             exclude_tag_names: str | list[str] | None = None,
                                             tag_group_id: str | None = None,
                                             tag_search_text: str | None = None,
                                             limit: int | None = None,
                                             offset: int | None = None,
                                             order_by: str | None = None,
                                             sort_order: str | None = None
                                             ) -> Tags:
        """Get FRED series search related tags.

        Get related tags for a series search text.

        Args:
            series_search_text (str): The text to search for series.
            tag_names (str | list): A semicolon-delimited list of tag names to include.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude.
            tag_group_id (str, optional): The tag group id to filter tags by type.
            tag_search_text (str, optional): The text to search for tags.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options are 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options are 'asc' (ascending) or 'desc' (descending).

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_series_search_related_tags'

        data: dict[str, Any] = {
            'series_search_text': series_search_text,
            'tag_names': tag_names,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'exclude_tag_names': exclude_tag_names,
            'tag_group_id': tag_group_id,
            'tag_search_text': tag_search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Tags.to_object_async(response)

    async def get_series_tags(self,
                              series_id: str,
                              realtime_start: str | datetime | date | None = None,
                              realtime_end: str | datetime | date | None = None,
                              order_by: str | None = None,
                              sort_order: str | None = None
                              ) -> Tags:
        """Get FRED series tags.

        Get the tags for a series.

        Args:
            series_id (str): The ID for a series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            order_by (str, optional): Order results by values such as 'series_id', 'name', 'popularity', etc.
            sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order.

        Returns:
            Tags: If multiple tags are returned.

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
        endpoint_name = 'get_series_tags'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Tags.to_object_async(response)

    async def get_series_updates(self,
                                 realtime_start: str | datetime | date | None = None,
                                 realtime_end: str | datetime | date | None = None,
                                 limit: int | None = None,
                                 offset: int | None = None,
                                 filter_value: str | None = None,
                                 start_time: str | datetime | time | None = None,
                                 end_time: str | datetime | time | None = None
                                 ) -> Seriess:
        """Get FRED series updates.

        Retrieves updates for a series from the FRED API.

        Args:
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            filter_value (str, optional): Filter results by this value.
            start_time (str | datetime | time, optional): The start time for the updates. String format: HH:MM.
            end_time (str | datetime | time, optional): The end time for the updates. String format: HH:MM.

        Returns:
            list[Series]: If multiple series are returned.

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
        endpoint_name = 'get_series_updates'

        data: dict[str, Any] = {
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'filter_value': filter_value,
            'start_time': start_time,
            'end_time': end_time
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Seriess.to_object_async(response)

    async def get_series_vintagedates(self,
                                      series_id: str,
                                      realtime_start: str | datetime | date | None = None,
                                      realtime_end: str | datetime | date | None = None,
                                      limit: int | None = None,
                                      offset: int | None = None,
                                      sort_order: str | None = None
                                      ) -> VintageDates:
        """Get FRED series vintage dates.

        Get the vintage dates for a given FRED series.

        Args:
            series_id (str): The ID for the FRED series.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            sort_order (str, optional): The order of the results. Possible values: 'asc' or 'desc'.

        Returns:
            list[VintageDate]: If multiple vintage dates are returned.

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
        endpoint_name = 'get_series_vintagedates'

        data: dict[str, Any] = {
            'series_id': series_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await VintageDates.to_object_async(response)

    ## Sources
    async def get_sources(self,
                          realtime_start: str | datetime | date | None = None,
                          realtime_end: str | datetime | date | None = None,
                          limit: int | None = None,
                          offset: int | None = None,
                          order_by: str | None = None,
                          sort_order: str | None = None
                          ) -> Sources:
        """Get FRED sources.

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
            Sources: If multiple sources are returned.

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
        endpoint_name = 'get_sources'

        data: dict[str, Any] = {
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Sources.to_object_async(response)

    async def get_source(self,
                         source_id: int,
                         realtime_start: str | datetime | date | None = None,
                         realtime_end: str | datetime | date | None = None
                         ) -> Source:
        """Get a FRED source.

        Retrieves information about a source from the FRED API.

        Args:
            source_id (int): The ID for the source.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD. Defaults to None.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD. Defaults to None.

        Returns:
            Source: If a single source is returned.

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
        endpoint_name = 'get_source'

        data: dict[str, Any] = {
            'source_id': source_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Source.to_object_async(response)

    async def get_source_releases(self,
                                  source_id: int,
                                  realtime_start: str | datetime | date | None = None,
                                  realtime_end: str | datetime | date | None = None,
                                  limit: int | None = None,
                                  offset: int | None = None,
                                  order_by: str | None = None,
                                  sort_order: str | None = None
                                  ) -> Releases:
        """Get FRED source releases.

        Get the releases for a specified source from the FRED API.

        Args:
            source_id (int): The ID for the source.
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            limit (int, optional): The maximum number of results to return.
            offset (int, optional): The offset for the results.
            order_by (str, optional): Order results by values such as 'release_id', 'name', etc.
            sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for descending.

        Returns:
            Releases: If multiple Releases are returned.

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
        url_endpoint = 'get_source_releases'

        data: dict[str, Any] = {
            'source_id': source_id,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(url_endpoint, data)

        return await Releases.to_object_async(response)

    ## Tags
    async def get_tags(self,
                       realtime_start: str | datetime | date | None = None,
                       realtime_end: str | datetime | date | None = None,
                       tag_names: str | list[str] | None = None,
                       tag_group_id: str | None = None,
                       search_text: str | None = None,
                       limit: int | None = None,
                       offset: int | None = None,
                       order_by: str | None = None,
                       sort_order: str | None = None
                       ) -> Tags:
        """Get FRED tags.

        Retrieve FRED tags based on specified parameters.

        Args:
            realtime_start (str | datetime | date, optional): The start of the real-time period. String format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to filter results.
            tag_group_id (str, optional): A tag group ID to filter results.
            search_text (str, optional): The words to match against tag names and descriptions.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
            sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for descending.

        Returns:
            Tags: If multiple tags are returned.

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
        endpoint_name = 'get_tags'

        data: dict[str, Any] = {
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Tags.to_object_async(response)

    async def get_related_tags(self,
                               realtime_start: str | datetime | date | None = None,
                               realtime_end: str | datetime | date | None = None,
                               tag_names: str | list[str] | None = None,
                               exclude_tag_names: str | list[str] | None = None,
                               tag_group_id: str | None = None,
                               search_text: str | None = None,
                               limit: int | None = None,
                               offset: int | None = None,
                               order_by: str | None = None,
                               sort_order: str | None = None
                               ) -> Tags:
        """Get FRED related tags.

        Retrieve related tags for a given set of tags from the FRED API.

        Args:
            realtime_start (str | datetime | date, optional): The start of the real-time period. Strinng format: YYYY-MM-DD.
            realtime_end (str | datetime | date, optional): The end of the real-time period. String format: YYYY-MM-DD.
            tag_names (str | list, optional): A semicolon-delimited list of tag names to include in the search.
            exclude_tag_names (str | list, optional): A semicolon-delimited list of tag names to exclude from the search.
            tag_group_id (str, optional): A tag group ID to filter tags by group.
            search_text (str, optional): The words to match against tag names and descriptions.
            limit (int, optional): The maximum number of results to return. Default is 1000.
            offset (int, optional): The offset for the results. Used for pagination.
            order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 'created', 'name', 'group_id'.
            sort_order (str, optional): Sort order of results. Options: 'asc' (ascending), 'desc' (descending). Default is 'asc'.

        Returns:
            list[Tag]: If multiple tags are returned.

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
        endpoint_name = 'get_related_tags'

        data: dict[str, Any] = {
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'tag_names': tag_names,
            'exclude_tag_names': exclude_tag_names,
            'tag_group_id': tag_group_id,
            'search_text': search_text,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Tags.to_object_async(response)

    async def get_tags_series(self,
                              tag_names: str | list[str] | None = None,
                              exclude_tag_names: str | list[str] | None = None,
                              realtime_start: str | datetime | date | None = None,
                              realtime_end: str | datetime | date | None = None,
                              limit: int | None = None,
                              offset: int | None = None,
                              order_by: str | None = None,
                              sort_order: str | None = None
                              ) -> Seriess:
        """Get FRED tags series.

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
            list[Series]: If multiple series are returned.

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
        endpoint_name = 'get_tags/series'

        data: dict[str, Any] = {
            'tag_names': tag_names,
            'exclude_tag_names': exclude_tag_names,
            'realtime_start': realtime_start,
            'realtime_end': realtime_end,
            'limit': limit,
            'offset': offset,
            'order_by': order_by,
            'sort_order': sort_order
        }

        response = await self._client_get_request(endpoint_name, data)

        return await Seriess.to_object_async(response)
