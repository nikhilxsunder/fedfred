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

from typing import Optional
from .fred import Fred
from ..config import resolve_api_key

class Alfred:

    def __init__(self, api_key: Optional[str]=None, cache_mode: bool=True, cache_size: int=256) -> None:
        self.__client: Optional[Fred] = None
        self.api_key = resolve_api_key(api_key, service="fred")
        self.cache_mode = cache_mode
        self.cache_size = cache_size

    @property
    def __fred(self) -> Fred:
        if self.__client is None:
            self.__client = Fred(api_key=self.api_key, cache_mode=self.cache_mode, cache_size=self.cache_size)
        return self.__client

    @property
    def keys(self):
        return self.__fred.keys

    def get_series_observations_first_release(self, series_id: str, units: Optional[str]=None,
                                              observation_start: Optional[str]=None, observation_end: Optional[str]=None,
                                              frequency: Optional[str]=None, aggregation_method: Optional[str]=None):
        realtime_start_ext = '1776-07-04'
        realtime_end_ext = '9999-12-31'

        result = self.__fred.get_series_observations(
            series_id=series_id,
            units=units,
            observation_start=observation_start,
            observation_end=observation_end,
            frequency=frequency,
            aggregation_method=aggregation_method,
            realtime_start=realtime_start_ext,
            realtime_end=realtime_end_ext
        )

    def get_series_observations_latest_release(self, series_id: str, units: Optional[str]=None, observation_start: Optional[str]=None, observation_end: Optional[str]=None,
                                              frequency: Optional[str]=None, aggregation_method: Optional[str]=None):
        
        realtime_end_ext = '9999-12-31'

        result = self.__fred.get_series_observations(
            series_id=series_id,
            units=units,
            observation_start=observation_start,
            observation_end=observation_end,
            frequency=frequency,
            aggregation_method=aggregation_method,
            realtime_end=realtime_end_ext
        )

    def get_series_observations_as_of_date(self, series_id: str, units: Optional[str]=None, observation_start: Optional[str]=None, observation_end: Optional[str]=None,
                                              frequency: Optional[str]=None, aggregation_method: Optional[str]=None):
        realtime_start_ext = observation_start

        result = self.__fred.get_series_observations(
            series_id=series_id,
            units=units,
            observation_start=observation_start,
            observation_end=observation_end,
            frequency=frequency,
            aggregation_method=aggregation_method,
            realtime_start=realtime_start_ext,
        )
        