
from typing import Optional
from ..fred.clients import Fred
from ..utils.config import resolve_api_key

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
        