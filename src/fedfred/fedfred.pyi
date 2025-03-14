from typing import Optional, Dict, Union, List, Any, Deque
import asyncio
import pandas as pd
import polars as pl
import geopandas as gpd
from cacheout import Cache
from .fred_data import Category, Series, Tag, Release, ReleaseDate, Source, Element, VintageDate, SeriesGroup

class FredAPI:
    base_url: str
    api_key: str
    cache_mode: bool
    cache: Cache
    max_requests_per_minute: int
    request_times: Deque[float]
    lock: asyncio.Lock
    semaphore: asyncio.Semaphore
    Maps: 'FredAPI.MapsAPI'
    Async: 'FredAPI.AsyncAPI'
    def __init__(self, api_key: str, cache_mode: bool = False) -> None: ...
    # Category Methods
    def get_category(self, category_id: int, file_type: str = 'json') -> Category: ...
    def get_category_children(self, category_id: int, realtime_start: Optional[str]=None,
                              realtime_end: Optional[str]=None, file_type: str ='json') -> List[Category]: ...
    def get_category_related(self, category_id: int, realtime_start: Optional[str]=None,
                             realtime_end: Optional[str]=None, file_type: str = 'json') -> Union[Category, List[Category]]: ...
    def get_category_series(self, category_id: int, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, limit: Optional[int]=None,
                            offset: Optional[int]=None, order_by: Optional[str]=None,
                            sort_order: Optional[str]=None, filter_variable: Optional[str]=None,
                            filter_value: Optional[str]=None, tag_names: Optional[str]=None,
                            exclude_tag_names: Optional[str]=None, file_type: str ='json') -> Union[Series, List[Series]]: ...
    def get_category_tags(self, category_id: int, realtime_start: Optional[str]=None,
                          realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                          tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                          limit: Optional[int]=None, offset: Optional[int]=None,
                          order_by: Optional[int]=None, sort_order: Optional[str]=None,
                          file_type: str ='json') -> Union[Tag, List[Tag]]: ...
    def get_category_related_tags(self, category_id: int, realtime_start: Optional[str]=None,
                                  realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                  exclude_tag_names: Optional[str]=None,
                                  tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                                  limit: Optional[int]=None, offset: Optional[int]=None,
                                  order_by: Optional[int]=None, sort_order: Optional[int]=None,
                                  file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
    # Release Methods
    def get_releases(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                     limit: Optional[int]=None, offset: Optional[int]=None,
                     order_by: Optional[str]=None, sort_order: Optional[str]=None,
                     file_type: str ='json') -> Union[Release, List[Release]]: ...
    def get_releases_dates(self, realtime_start: Optional[str]=None,
                           realtime_end: Optional[str]=None, limit: Optional[int]=None,
                           offset: Optional[int]=None, order_by: Optional[str]=None,
                           sort_order: Optional[str]=None,
                           include_releases_dates_with_no_data: Optional[bool]=None,
                           file_type: str = 'json') -> Union[ReleaseDate, List[ReleaseDate]]: ...
    def get_release(self, release_id: int, realtime_start: Optional[str]=None,
                    realtime_end: Optional[str]=None, file_type: str = 'json') -> Release: ...
    def get_release_dates(self, release_id: int, realtime_start: Optional[str]=None,
                          realtime_end: Optional[str]=None, limit: Optional[int]=None,
                          offset: Optional[int]=None, sort_order: Optional[str]=None,
                          include_releases_dates_with_no_data: Optional[bool]=None,
                          file_type: str = 'json') -> Union[ReleaseDate, List[ReleaseDate]]: ...
    def get_release_series(self, release_id: int, realtime_start: Optional[str]=None,
                           realtime_end: Optional[str]=None, limit: Optional[int]=None,
                           offset: Optional[int]=None, sort_order: Optional[str]=None,
                           filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                           exclude_tag_names: Optional[str]=None, file_type: str = 'json') -> Union[Series, List[Series]]: ...
    def get_release_sources(self, release_id: int, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, file_type: str = 'json') -> Union[Source, List[Source]]: ...
    def get_release_tags(self, release_id: int, realtime_start: Optional[str]=None,
                         realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                         tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                         limit: Optional[int]=None, offset: Optional[int]=None,
                         order_by: Optional[str]=None, file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
    def get_release_related_tags(self, release_id: int, realtime_start: Optional[str]=None,
                                 realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                 exclude_tag_names: Optional[str]=None, tag_group_id: Optional[str]=None,
                                 search_text: Optional[str]=None, limit: Optional[int]=None,
                                 offset: Optional[int]=None, order_by: Optional[str]=None,
                                 sort_order: Optional[str]=None, file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
    def get_release_tables(self, release_id: int, element_id: Optional[int]=None,
                           include_observation_values: Optional[bool]=None,
                           observation_date: Optional[str]=None, file_type: str = 'json') -> Union[Element, List[Element]]: ...
    # Series Methods
    def get_series(self, series_id: str, realtime_start: Optional[str]=None,
                   realtime_end: Optional[str]=None, file_type: str = 'json') -> Series: ...
    def get_series_categories(self, series_id: str, realtime_start: Optional[str]=None,
                              realtime_end: Optional[str]=None, file_type: str = 'json') -> Union[Category, List[Category]]: ...
    def get_series_observations(self, series_id: str, dataframe_method: str = 'pandas',
                               realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                               limit: Optional[int]=None, offset: Optional[int]=None,
                               sort_order: Optional[str]=None,
                               observation_start: Optional[str]=None,
                               observation_end: Optional[str]=None, units: Optional[str]=None,
                               frequency: Optional[str]=None,
                               aggregation_method: Optional[str]=None,
                               output_type: Optional[int]=None, vintage_dates: Optional[str]=None,
                               file_type: str = 'json') -> Union[pd.DataFrame, pl.DataFrame, None]: ...
    def get_series_release(self, series_id: str, realtime_start: Optional[str]=None,
                           realtime_end: Optional[str]=None, file_type: str = 'json') -> Release: ...
    def get_series_search(self, search_text: str, search_type: Optional[str]=None,
                          realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                          limit: Optional[int]=None, offset: Optional[int]=None,
                          order_by: Optional[str]=None, sort_order: Optional[str]=None,
                          filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                          tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                          file_type: str = 'json') -> Union[Series, List[Series]]: ...
    def get_series_search_tags(self, series_search_text: str, realtime_start: Optional[str]=None,
                               realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                               tag_group_id: Optional[str]=None,
                               tag_search_text: Optional[str]=None, limit: Optional[int]=None,
                               offset: Optional[int]=None, order_by: Optional[str]=None,
                               sort_order: Optional[str]=None, file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
    def get_series_search_related_tags(self, series_search_text: str,
                                       realtime_start: Optional[str]=None,
                                       realtime_end: Optional[str]=None,
                                       tag_names: Optional[str]=None,
                                       exclude_tag_names: Optional[str]=None,
                                       tag_group_id: Optional[str]=None,
                                       tag_search_text: Optional[str]=None,
                                       limit: Optional[int]=None, offset: Optional[int]=None,
                                       order_by: Optional[str]=None, sort_order: Optional[str]=None,
                                       file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
    def get_series_tags(self, series_id: str, realtime_start: Optional[str]=None,
                        realtime_end: Optional[str]=None, order_by: Optional[str]=None,
                        sort_order: Optional[str]=None, file_type: str ='json') -> Union[Tag, List[Tag]]: ...
    def get_series_updates(self, realtime_start: Optional[str]=None,
                           realtime_end: Optional[str]=None, limit: Optional[int]=None,
                           offset: Optional[int]=None, filter_value: Optional[str]=None,
                           start_time: Optional[str]=None, end_time: Optional[str]=None,
                           file_type: str = 'json') -> Union[Series, List[Series]]: ...
    def get_series_vintagedates(self, series_id: str, realtime_start: Optional[str]=None,
                                realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                offset: Optional[int]=None, sort_order: Optional[str]=None,
                                file_type: str = 'json') -> Union[VintageDate, List[VintageDate]]: ...
    # Source Methods
    def get_sources(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                    limit: Optional[int]=None, offset: Optional[int]=None,
                    order_by: Optional[str]=None, sort_order: Optional[str]=None,
                    file_type: str = 'json') -> Union[Source, List[Source]]: ...
    def get_source(self, source_id: int, realtime_start: Optional[str]=None,
                   realtime_end: Optional[str]=None, file_type: str = 'json') -> Source: ...
    def get_source_releases(self, source_id: int , realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, limit: Optional[int]=None,
                            offset: Optional[int]=None, order_by: Optional[str]=None,
                            sort_order: Optional[str]=None, file_type: str = 'json') -> Union[Release, List[Release]]: ...
    # Tag Methods
    def get_tags(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                 tag_names: Optional[str]=None, tag_group_id: Optional[str]=None,
                search_text: Optional[str]=None, limit: Optional[int]=None,
                offset: Optional[int]=None, order_by: Optional[str]=None,
                sort_order: Optional[str]=None, file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
    def get_related_tags(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                         tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                         tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                         limit: Optional[int]=None, offset: Optional[int]=None,
                         order_by: Optional[str]=None, sort_order: Optional[str]=None,
                         file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
    def get_tags_series(self, tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                        realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                        limit: Optional[int]=None, offset: Optional[int]=None,
                        order_by: Optional[str]=None, sort_order: Optional[str]=None,
                        file_type: str = 'json') -> Union[Series, List[Series]]: ...
    class MapsAPI:
        base_url: str
        parent: FredAPI
        cache_mode: bool
        cache: Cache
        def __init__(self, parent) -> None: ...
        def get_shape_files(self, shape: str) -> gpd.GeoDataFrame: ...
        def get_series_group(self, series_id: str, file_type: str = 'json') -> SeriesGroup: ...
        def get_series_data(self, series_id: str, date: Optional[str]=None,
                            start_date: Optional[str]=None, file_type: str = 'json') -> gpd.GeoDataFrame: ...
        def get_regional_data(self, series_group: str, region_type: str, date: str, season: str,
                            units: str, start_date: Optional[str]=None,
                            transformation: Optional[str]=None, frequency: Optional[str]=None,
                            aggregation_method: Optional[str]=None,
                            file_type: str = 'json') -> gpd.GeoDataFrame: ...
    class AsyncAPI:
        parent: FredAPI
        cache_mode: bool
        cache: Cache
        Maps: 'FredAPI.AsyncAPI.MapsAPI'
        def __init__(self, parent) -> None: ...
        # Category Methods
        def get_category(self, category_id: int, file_type: str = 'json') -> Category: ...
        def get_category_children(self, category_id: int, realtime_start: Optional[str]=None,
                                realtime_end: Optional[str]=None, file_type: str ='json') -> List[Category]: ...
        def get_category_related(self, category_id: int, realtime_start: Optional[str]=None,
                                realtime_end: Optional[str]=None, file_type: str = 'json') -> Union[Category, List[Category]]: ...
        def get_category_series(self, category_id: int, realtime_start: Optional[str]=None,
                                realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                offset: Optional[int]=None, order_by: Optional[str]=None,
                                sort_order: Optional[str]=None, filter_variable: Optional[str]=None,
                                filter_value: Optional[str]=None, tag_names: Optional[str]=None,
                                exclude_tag_names: Optional[str]=None, file_type: str ='json') -> Union[Series, List[Series]]: ...
        def get_category_tags(self, category_id: int, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                            tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                            limit: Optional[int]=None, offset: Optional[int]=None,
                            order_by: Optional[int]=None, sort_order: Optional[str]=None,
                            file_type: str ='json') -> Union[Tag, List[Tag]]: ...
        def get_category_related_tags(self, category_id: int, realtime_start: Optional[str]=None,
                                    realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                    exclude_tag_names: Optional[str]=None,
                                    tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                                    limit: Optional[int]=None, offset: Optional[int]=None,
                                    order_by: Optional[int]=None, sort_order: Optional[int]=None,
                                    file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
        # Release Methods
        def get_releases(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                        limit: Optional[int]=None, offset: Optional[int]=None,
                        order_by: Optional[str]=None, sort_order: Optional[str]=None,
                        file_type: str ='json') -> Union[Release, List[Release]]: ...
        def get_releases_dates(self, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, limit: Optional[int]=None,
                            offset: Optional[int]=None, order_by: Optional[str]=None,
                            sort_order: Optional[str]=None,
                            include_releases_dates_with_no_data: Optional[bool]=None,
                            file_type: str = 'json') -> Union[ReleaseDate, List[ReleaseDate]]: ...
        def get_release(self, release_id: int, realtime_start: Optional[str]=None,
                        realtime_end: Optional[str]=None, file_type: str = 'json') -> Release: ...
        def get_release_dates(self, release_id: str, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, limit: Optional[int]=None,
                            offset: Optional[int]=None, sort_order: Optional[str]=None,
                            include_releases_dates_with_no_data: Optional[bool]=None,
                            file_type: str = 'json') -> Union[ReleaseDate, List[ReleaseDate]]: ...
        def get_release_series(self, release_id: int, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, limit: Optional[int]=None,
                            offset: Optional[int]=None, sort_order: Optional[str]=None,
                            filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                            exclude_tag_names: Optional[str]=None, file_type: str = 'json') -> Union[Series, List[Series]]: ...
        def get_release_sources(self, release_id: int, realtime_start: Optional[str]=None,
                                realtime_end: Optional[str]=None, file_type: str = 'json') -> Union[Source, List[Source]]: ...
        def get_release_tags(self, release_id: int, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                            tag_group_id: Optional[int]=None, search_text: Optional[str]=None,
                            limit: Optional[int]=None, offset: Optional[int]=None,
                            order_by: Optional[str]=None, file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
        def get_release_related_tags(self, release_id: int, realtime_start: Optional[str]=None,
                                    realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                    exclude_tag_names: Optional[str]=None, tag_group_id: Optional[str]=None,
                                    search_text: Optional[str]=None, limit: Optional[int]=None,
                                    offset: Optional[int]=None, order_by: Optional[str]=None,
                                    sort_order: Optional[str]=None, file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
        def get_release_tables(self, release_id: int, element_id: Optional[int]=None,
                            include_observation_values: Optional[bool]=None,
                            observation_date: Optional[str]=None, file_type: str = 'json') -> Union[Element, List[Element]]: ...
        # Series Methods
        def get_series(self, series_id: str, realtime_start: Optional[str]=None,
                    realtime_end: Optional[str]=None, file_type: str = 'json') -> Series: ...
        def get_series_categories(self, series_id: str, realtime_start: Optional[str]=None,
                                realtime_end: Optional[str]=None, file_type: str = 'json') -> Union[Category, List[Category]]: ...
        def get_series_observations(self, series_id: str, dataframe_method: str = 'pandas',
                                realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                                limit: Optional[int]=None, offset: Optional[int]=None,
                                sort_order: Optional[str]=None,
                                observation_start: Optional[str]=None,
                                observation_end: Optional[str]=None, units: Optional[str]=None,
                                frequency: Optional[str]=None,
                                aggregation_method: Optional[str]=None,
                                output_type: Optional[int]=None, vintage_dates: Optional[str]=None,
                                file_type: str = 'json') -> Union[pd.DataFrame, pl.DataFrame, None]: ...
        def get_series_release(self, series_id: str, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, file_type: str = 'json') -> Release: ...
        def get_series_search(self, search_text: str, search_type: Optional[str]=None,
                            realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                            limit: Optional[int]=None, offset: Optional[int]=None,
                            order_by: Optional[str]=None, sort_order: Optional[str]=None,
                            filter_variable: Optional[str]=None, filter_value: Optional[str]=None,
                            tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                            file_type: str = 'json') -> Union[Series, List[Series]]: ...
        def get_series_search_tags(self, series_search_text: str, realtime_start: Optional[str]=None,
                                realtime_end: Optional[str]=None, tag_names: Optional[str]=None,
                                tag_group_id: Optional[str]=None,
                                tag_search_text: Optional[str]=None, limit: Optional[int]=None,
                                offset: Optional[int]=None, order_by: Optional[str]=None,
                                sort_order: Optional[str]=None, file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
        def get_series_search_related_tags(self, series_search_text: str,
                                        realtime_start: Optional[str]=None,
                                        realtime_end: Optional[str]=None,
                                        tag_names: Optional[str]=None,
                                        exclude_tag_names: Optional[str]=None,
                                        tag_group_id: Optional[str]=None,
                                        tag_search_text: Optional[str]=None,
                                        limit: Optional[int]=None, offset: Optional[int]=None,
                                        order_by: Optional[str]=None, sort_order: Optional[str]=None,
                                        file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
        def get_series_tags(self, series_id: str, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, order_by: Optional[str]=None,
                            sort_order: Optional[str]=None, file_type: str ='json') -> Union[Tag, List[Tag]]: ...
        def get_series_updates(self, realtime_start: Optional[str]=None,
                            realtime_end: Optional[str]=None, limit: Optional[int]=None,
                            offset: Optional[int]=None, filter_value: Optional[str]=None,
                            start_time: Optional[str]=None, end_time: Optional[str]=None,
                            file_type: str = 'json') -> Union[Series, List[Series]]: ...
        def get_series_vintagedates(self, series_id: str, realtime_start: Optional[str]=None,
                                    realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                    offset: Optional[int]=None, sort_order: Optional[str]=None,
                                    file_type: str = 'json') -> Union[VintageDate, List[VintageDate]]: ...
        # Source Methods
        def get_sources(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                        limit: Optional[int]=None, offset: Optional[int]=None,
                        order_by: Optional[str]=None, sort_order: Optional[str]=None,
                        file_type: str = 'json') -> Union[Source, List[Source]]: ...
        def get_source(self, source_id: int, realtime_start: Optional[str]=None,
                    realtime_end: Optional[str]=None, file_type: str = 'json') -> Source: ...
        def get_source_releases(self, source_id: int , realtime_start: Optional[str]=None,
                                realtime_end: Optional[str]=None, limit: Optional[int]=None,
                                offset: Optional[int]=None, order_by: Optional[str]=None,
                                sort_order: Optional[str]=None, file_type: str = 'json') -> Union[Release, List[Release]]: ...
        # Tag Methods
        def get_tags(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                    tag_names: Optional[str]=None, tag_group_id: Optional[str]=None,
                    search_text: Optional[str]=None, limit: Optional[int]=None,
                    offset: Optional[int]=None, order_by: Optional[str]=None,
                    sort_order: Optional[str]=None, file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
        def get_related_tags(self, realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                            tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                            tag_group_id: Optional[str]=None, search_text: Optional[str]=None,
                            limit: Optional[int]=None, offset: Optional[int]=None,
                            order_by: Optional[str]=None, sort_order: Optional[str]=None,
                            file_type: str = 'json') -> Union[Tag, List[Tag]]: ...
        def get_tags_series(self, tag_names: Optional[str]=None, exclude_tag_names: Optional[str]=None,
                            realtime_start: Optional[str]=None, realtime_end: Optional[str]=None,
                            limit: Optional[int]=None, offset: Optional[int]=None,
                            order_by: Optional[str]=None, sort_order: Optional[str]=None,
                            file_type: str = 'json') -> Union[Series, List[Series]]: ...
        class MapsAPI:
            base_url: str
            parent: FredAPI.AsyncAPI
            grandparent: FredAPI
            cache_mode: bool
            cache: Cache
            def __init__(self, parent) -> None: ...
            def get_shape_files(self, shape: str) -> gpd.GeoDataFrame: ...
            def get_series_group(self, series_id: str, file_type: str = 'json') -> SeriesGroup: ...
            def get_series_data(self, series_id: str, date: Optional[str]=None,
                                start_date: Optional[str]=None, file_type: str = 'json') -> gpd.GeoDataFrame: ...
            def get_regional_data(self, series_group: str, region_type: str, date: str, season: str,
                                units: str, start_date: Optional[str]=None,
                                transformation: Optional[str]=None, frequency: Optional[str]=None,
                                aggregation_method: Optional[str]=None,
                                file_type: str = 'json') -> gpd.GeoDataFrame: ...
