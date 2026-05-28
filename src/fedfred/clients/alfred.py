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