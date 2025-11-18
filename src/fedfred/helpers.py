# filepath: /src/fedfred/helpers.py
#
# Copyright (c) 2025 Nikhil Sunder
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
This module defines helper methods for the fedfred package.
"""

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional, Union
import pandas as pd
import geopandas as gpd
from .__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__
if TYPE_CHECKING:
    import dask.dataframe as dd # pragma: no cover
    import dask_geopandas as dd_gpd # pragma: no cover
    import polars as pl # pragma: no cover
    import polars_st as st # pragma: no cover

class FredHelpers:
    """
    A class that provides helper methods for the FRED API.
    """
    # Synchronous methods
    @staticmethod
    def to_pd_df(data: Dict[str, list]) -> pd.DataFrame:
        """
        Helper method to convert a fred observation dictionary to a Pandas DataFrame.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            pandas.DataFrame: Converted Pandas DataFrame.

        Raises:
            ValueError: If 'observations' key is not in the data.
        """
        if 'observations' not in data:
            raise ValueError("Data must contain 'observations' key")
        df = pd.DataFrame(data['observations'])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df['value'] = pd.to_numeric(df['value'], errors = 'coerce')
        return df
    @staticmethod
    def to_pl_df(data: Dict[str, list]) -> 'pl.DataFrame':
        """
        Helper method to convert a fred observation dictionary to a Polars DataFrame.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            polars.DataFrame: Converted Polars DataFrame.

        Raises:
            ImportError: If Polars is not installed.
            ValueError: If 'observations' key is not in the data.
        """
        try:
            import polars as pl
        except ImportError as e:
            raise ImportError(
                f"{e}: Polars is not installed. Install it with `pip install polars` to use this method."
        ) from e
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
    @staticmethod
    def to_dd_df(data: Dict[str, list]) -> 'dd.DataFrame':
        """
        Helper method to convert a FRED observation dictionary to a Dask DataFrame.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            dask.dataframe.DataFrame: Converted Dask DataFrame.

        Raises:
            ImportError: If Dask is not installed.
            ValueError: If 'observations' key is not in the data.
        """
        try:
            import dask.dataframe as dd
        except ImportError as e:
            raise ImportError(
                f"{e}: Dask is not installed. Install it with `pip install dask` to use this method."
            ) from e
        df = FredHelpers.to_pd_df(data)
        return dd.from_pandas(df, npartitions=1)
    @staticmethod
    def to_gpd_gdf(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> gpd.GeoDataFrame:
        """
        Helper method to convert a fred observation dictionary to a GeoPandas GeoDataFrame.

        Args:
            shapefile (gpd.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            gpd.GeoDataFrame: Converted GeoPandas GeoDataFrame.

        Raises:
            ValueError: If no data section is found in the response.
        """
        shapefile.set_index('name', inplace=True)
        shapefile['value'] = None
        shapefile['series_id'] = None
        data_section = meta_data.get('data', {})
        if not data_section:
            raise ValueError("No data section found in the response")
        data_key = next(iter(data_section))
        items = data_section[data_key]
        for item in items:
            if item['region'] in shapefile.index:
                shapefile.loc[item['region'], 'value'] = item['value']
                shapefile.loc[item['region'], 'series_id'] = item['series_id']
        return shapefile
    @staticmethod
    def to_dd_gpd_gdf(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'dd_gpd.GeoDataFrame':
        """
        Helper method to convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame.

        Args:
            shapefile (gpd.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            dask_geopandas.GeoDataFrame: Converted Dask GeoPandas GeoDataFrame.

        Raises:
            ImportError: If Dask GeoPandas is not installed.
            ValueError: If no data section is found in the response.
        """
        try:
            import dask_geopandas as dd_gpd
        except ImportError as e:
            raise ImportError(
                f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method."
            ) from e
        gdf = FredHelpers.to_gpd_gdf(shapefile, meta_data)
        return dd_gpd.from_geopandas(gdf, npartitions=1)
    @staticmethod
    def to_pl_st_gdf(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'st.GeoDataFrame':
        """
        Helper method to convert a FRED observation dictionary to a Polars GeoDataFrame.

        Args:
            shapefile (gpd.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            polars_st.GeoDataFrame: Converted Polars GeoDataFrame.

        Raises:
            ImportError: If Polars with geospatial support is not installed.
            ValueError: If no data section is found in the response.
        """
        try:
            import polars_st as st
        except ImportError as e:
            raise ImportError(
                f"{e}: Polars with geospatial support is not installed. Install it with `pip install polars-st` to use this method."
            ) from e
        gdf = FredHelpers.to_gpd_gdf(shapefile, meta_data)
        return st.from_geopandas(gdf)
    @staticmethod
    def extract_region_type(response: Dict) -> str:
        """
        Helper method to extract the region type from a GeoFred response dict.

        Args:
            response (Dict): FRED GeoFred response dictionary.

        Returns:
            str: Extracted region type.

        Raises:
            ValueError: If no meta data or region type is found in the response.
        """
        meta_data = response.get('meta', {})
        if not meta_data:
            raise ValueError("No meta data found in the response")
        region_type = meta_data.get('region')
        if not region_type:
            raise ValueError("No region type found in the response")
        return region_type
    @staticmethod
    def liststring_conversion(param: list[str]) -> str:
        """
        Helper method to convert a list of strings to a semicolon-separated string.

        Args:
            param (list[str]): List of strings to convert.

        Returns:
            str: Semicolon-separated string.

        Raises:
            ValueError: If param is not a list of strings.
        """
        if not isinstance(param, list):
            raise ValueError("Parameter must be a list")
        if any(not isinstance(i, str) for i in param):
            raise ValueError("All elements in the list must be strings")
        return ';'.join(param)
    @staticmethod
    def vintage_dates_type_conversion(param: Union[str, datetime, list[Optional[Union[str, datetime]]]]) -> str:
        """
        Helper method to convert a vintage_dates parameter to a string.

        Args:
            param (str | datetime | list[Optional[str | datetime]]]): vintage_dates parameter to convert.

        Returns:
            str: Converted vintage_dates string.

        Raises:
            ValueError: If param is not a string, datetime object, or list of strings/datetime objects.
        """
        if isinstance(param, str):
            return param
        elif isinstance(param, datetime):
            return FredHelpers.datetime_conversion(param)
        elif isinstance(param, list):
            converted_list = [
                FredHelpers.datetime_conversion(i) if isinstance(i, datetime) else i
                for i in param
                if i is not None
            ]
            if not all(isinstance(i, str) for i in converted_list):
                raise ValueError("All elements in the list must be strings or datetime objects")
            return ','.join(converted_list)
        else:
            raise ValueError("Parameter must be a string, datetime object, or list of strings/datetime objects")
    @staticmethod
    def datetime_conversion(param: datetime) -> str:
        """
        Helper method to convert a datetime object to a string in YYYY-MM-DD format.

        Args:
            param (datetime): Datetime object to convert.

        Returns:
            str: Formatted date string.

        Raises:
            ValueError: If param is not a datetime object.
        """
        if not isinstance(param, datetime):
            raise ValueError("Parameter must be a datetime object")
        return param.strftime("%Y-%m-%d")
    @staticmethod
    def datetime_hh_mm_conversion(param: datetime) -> str:
        """
        Helper method to convert a datetime object to a string in HH:MM format.

        Args:
            param (datetime): Datetime object to convert.

        Returns:
            str: Formatted time string.

        Raises:
            ValueError: If param is not a datetime object.
        """
        if not isinstance(param, datetime):
            raise ValueError("Parameter must be a datetime object")
        return param.strftime("%H:%M")
    @staticmethod
    def datestring_validation(param: str) -> Optional[ValueError]:
        """
        Helper method to validate date-string formatted parameters.

        Args:
            param (str): Date string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid date string in YYYY-MM-DD format.
        """
        try:
            datetime.strptime(param, "%Y-%m-%d")
            return None
        except ValueError as e:
            raise ValueError(f"Value Error: {e}" ) from e
    @staticmethod
    def liststring_validation(param: str) -> Optional[ValueError]:
        """
        Helper method to validate list-string formatted parameters.

        Args:
            param (str): Semicolon-separated string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid semicolon-separated string.
        """
        if not isinstance(param, str):
            raise ValueError("Parameter must be a string")
        terms = param.split(';')
        if any(term == '' for term in terms):
            raise ValueError("Semicolon-separated list cannot contain empty terms")
        if not all(term.isalnum() for term in terms):
            raise ValueError("Each term must be alphanumeric and contain no whitespace")
        else:
            return None
    @staticmethod
    def vintage_dates_validation(param: str) -> Optional[ValueError]:
        """
        Helper method to validate vintage_dates parameters.

        Args:
            param (str): Comma-separated string of vintage dates.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid vintage_dates string.
        """
        if not isinstance(param, str):
            raise ValueError("Parameter must be a string")
        if param == '':
            raise ValueError("vintage_dates cannot be empty")
        terms = param.split(',')
        for term in terms:
            try:
                datetime.strptime(term, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(f"Value Error: {e}" ) from e
        return None
    @staticmethod
    def hh_mm_datestring_validation(param: str) -> Optional[ValueError]:
        """
        Helper method to validate hh:mm formatted parameters.

        Args:
            param (str): Time string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid time string in HH:MM format.
        """
        if not isinstance(param, str):
            raise ValueError("Parameter must be a string")
        try:
            datetime.strptime(param, "%H:%M")
            return None
        except ValueError as e:
            raise ValueError(f"Value Error: {e}" ) from e
    @staticmethod
    def parameter_validation(params: Dict[str, Optional[Union[str, int]]]) -> Optional[ValueError]:
        """
        Helper method to validate parameters prior to making a get request.

        Args:
            params (Dict[str, Optional[str | int]]): Dictionary of parameters to validate.

        Returns:
            None

        Raises:
            ValueError: If any parameter is invalid.
        """
        for k, v in params.items():
            if k == 'category_id':
                if not isinstance(v, int) or v < 0:
                    raise ValueError("category_id must be a non-negative integer")
            elif k == 'realtime_start':
                if not isinstance(v, str):
                    raise ValueError("realtime_start must be a string in YYYY-MM-DD format")
                try:
                    FredHelpers.datestring_validation(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'realtime_end':
                if not isinstance(v, str):
                    raise ValueError("realtime_end must be a string in YYYY-MM-DD format")
                try:
                    FredHelpers.datestring_validation(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'limit':
                if not isinstance(v, int) or v < 0:
                    raise ValueError("limit must be a non-negative integer")
            elif k == 'offset':
                if not isinstance(v, int) or v < 0:
                    raise ValueError("offset must be a non-negative integer")
            elif k == 'sort_order':
                if not isinstance(v, str) or v not in ['asc', 'desc']:
                    raise ValueError("sort_order must be 'asc' or 'desc'")
            elif k == 'order_by':
                if not isinstance(v, str) or v not in ['series_id', 'title', 'units', 'frequency', 'seasonal_adjustment',
                                                       'realtime_start', 'realtime_end', 'last_updated', 'observation_start',
                                                       'observation_end', 'popularity', 'group_popularity', 'series_count',
                                                       'created', 'name', 'release_id', 'press_release', 'group_id',
                                                       'search_rank', 'title']:
                    raise ValueError("order_by must be one of the valid options")
            elif k == 'filter_variable':
                if not isinstance(v, str) or v not in ['frequency', 'units', 'seasonal_adjustment']:
                    raise ValueError("filter_variable must be one of the valid options")
            elif k == 'filter_value':
                if not isinstance(v, str):
                    raise ValueError("filter_value must be a string")
            elif k == 'tag_names':
                if not isinstance(v, str):
                    raise ValueError("tag_names must be a string")
                try:
                    FredHelpers.liststring_validation(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'exclude_tag_names':
                if not isinstance(v, str):
                    raise ValueError("exclude_tag_names must be a string")
                try:
                    FredHelpers.liststring_validation(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'tag_group_id':
                if not (isinstance(v, int) and v >= 0) and not isinstance(v, str):
                    raise ValueError("tag_group_id must be a non-negative integer or a string")
            elif k == 'search_text':
                if not isinstance(v, str):
                    raise ValueError("search_text must be a string")
            elif k == 'file_type':
                if not isinstance(v, str) or v != 'json':
                    raise ValueError("file_type must be 'json'")
            elif k == 'api_key':
                if not isinstance(v, str):
                    raise ValueError("api_key must be a string")
            elif k == 'include_releases_dates_with_no_data':
                if not isinstance(v, bool):
                    raise ValueError("include_releases_dates_with_no_data must be a boolean")
            elif k == 'release_id':
                if not isinstance(v, int) or v < 0:
                    raise ValueError("release_id must be a non-negative integer")
            elif k == 'series_id':
                if not isinstance(v, str):
                    raise ValueError("series_id must be a string")
                if v == '':
                    raise ValueError("series_id cannot be empty")
                if ' ' in v:
                    raise ValueError("series_id cannot contain whitespace")
                if not v.isalnum():
                    raise ValueError("series_id must be alphanumeric")
            elif k == 'frequency':
                if not isinstance(v, str):
                    raise ValueError("frequency must be a string")
                if v not in ['d', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem']:
                    raise ValueError("frequency must be one of the valid options")
            elif k == 'units':
                if not isinstance(v, str):
                    raise ValueError("units must be a string")
                if v not in ['lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log']:
                    raise ValueError("units must be one of the valid options")
            elif k == 'aggregation_method':
                if not isinstance(v, str):
                    raise ValueError("aggregation_method must be a string")
                if v not in ['sum', 'avg', 'eop']:
                    raise ValueError("aggregation_method must be one of the valid options")
            elif k == 'output_type':
                if not isinstance(v, int):
                    raise ValueError("output_type must be an integer")
                if v not in [1, 2, 3, 4]:
                    raise ValueError("output_type must be '1', '2', '3', or '4'")
            elif k == 'vintage_dates':
                if not isinstance(v, str):
                    raise ValueError("vintage_dates must be a string")
                try:
                    FredHelpers.vintage_dates_validation(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'search_type':
                if not isinstance(v, str):
                    raise ValueError("search_type must be a string")
                if v not in ['full_text', 'series_id']:
                    raise ValueError("search_type must be 'full_text' or 'series_id'")
            elif k == 'tag_search_text':
                if not isinstance(v, str):
                    raise ValueError("tag_search_text must be a string")
            elif k == 'start_time':
                if not isinstance(v, str):
                    raise ValueError("start_time must be a string")
                try:
                    FredHelpers.hh_mm_datestring_validation(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'end_time':
                if not isinstance(v, str):
                    raise ValueError("end_time must be a string")
                try:
                    FredHelpers.hh_mm_datestring_validation(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'season':
                if not isinstance(v, str):
                    raise ValueError("season must be a string")
                if v not in ['seasonally_adjusted', 'not_seasonally_adjusted']:
                    raise ValueError("season must be 'seasonally_adjusted' or 'not_seasonally_adjusted'")
        return None
    @staticmethod
    def geo_parameter_validation(params: Dict[str, Optional[Union[str, int]]]) -> Optional[ValueError]:
        """
        Helper method to validate parameters prior to making a get request.

        Args:
            params (Dict[str, Optional[str | int]]): Dictionary of parameters to validate

        Returns:
            None

        Raises:
            ValueError: If any parameter is invalid.
        """
        for k, v in params.items():
            if k == 'api_key':
                if not isinstance(v, str):
                    raise ValueError("api_key must be a string")
            elif k == 'file_type':
                if not isinstance(v, str) or v != 'json':
                    raise ValueError("file_type must be 'json'")
            elif k == 'shape':
                if not isinstance(v, str):
                    raise ValueError("shape must be a string")
                if v not in ['bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision']:
                    raise ValueError("shape must be 'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', or 'censusdivision'")
            elif k == 'series_id':
                if not isinstance(v, str):
                    raise ValueError("series_id must be a string")
                if v == '':
                    raise ValueError("series_id cannot be empty")
                if ' ' in v:
                    raise ValueError("series_id cannot contain whitespace")
                if not v.isalnum():
                    raise ValueError("series_id must be alphanumeric")
            elif k == 'date':
                if not isinstance(v, str):
                    raise ValueError("date must be a string")
                try:
                    FredHelpers.datestring_validation(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'start_date':
                if not isinstance(v, str):
                    raise ValueError("start_date must be a string")
                try:
                    FredHelpers.datestring_validation(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'series_group':
                if not isinstance(v, str):
                    raise ValueError("series_group must be a string")
            elif k == 'region_type':
                if not isinstance(v, str):
                    raise ValueError("region_type must be a string")
                if v not in ['bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision']:
                    raise ValueError("region_type must be 'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', or 'censusdivision'")
            elif k == 'aggregation_method':
                if not isinstance(v, str):
                    raise ValueError("aggregation_method must be a string")
                if v not in ['sum', 'avg', 'eop']:
                    raise ValueError("aggregation_method must be 'sum', 'avg', or 'eop'")
            elif k == 'units':
                if not isinstance(v, str):
                    raise ValueError("units must be a string")
            elif k == 'season':
                if not isinstance(v, str):
                    raise ValueError("season must be a string")
                if v not in ['NSA', 'SA', 'SSA', 'SAAR', 'NSAAR']:
                    raise ValueError("season must be 'NSA', 'SA', 'SSA', 'SAAR', or 'NSAAR'")
            elif k == 'transformation':
                if not isinstance(v, str):
                    raise ValueError("transformation must be a string")
                if v not in ['lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log']:
                    raise ValueError("transformation must be 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', or 'log'")
        return None
    @staticmethod
    def pd_frequency_conversion(frequency: str) -> str:
        """
        Convert fedfred native frequency strings to pandas compatible ones.

        Args:
            frequency (str): Input frequency string.

        Returns:
            str: Coerced frequency string compatible with pandas.

        Raises:
            None
        """
        frequency = frequency.upper()
        # Passthrough compatible frequencies
        if frequency in {'D', 'M', 'Q', 'W'}:
            return frequency
        # Annual -> Yearly
        elif frequency == 'A':
            return 'Y'
        # Weekly End variants
        elif frequency == 'WEF':
            return 'W-FRI'
        elif frequency == 'WETH':
            return 'W-THU'
        elif frequency == 'WEW':
            return 'W-WED'
        elif frequency == 'WETU':
            return 'W-TUE'
        elif frequency == 'WEM':
            return 'W-MON'
        elif frequency == 'WESU':
            return 'W-SUN'
        elif frequency == 'WESA':
            return 'W-SAT'
        # Biweekly -> 2 x Weekly
        elif frequency == 'BW':
            return '2W'
        # Biweekly End variants
        elif frequency == 'BWEW':
            return '2W-WED'
        elif frequency == 'BWEM':
            return '2W-MON'
        # Semiannual -> 2 x Quarterly
        elif frequency == 'SA':
            return '2Q'
        # Logically unreachable but prevents mypy warning
        return frequency
    @staticmethod
    def to_pd_series(data: Union[pd.Series, pd.DataFrame], name: str) -> pd.Series:
        """
        Accepts a Series or a DataFrame with 'date' and 'value' columns and returns a float Series with DatetimeIndex and the given name.

        Args:
            data (pd.Series | pd.DataFrame): Input data to be converted.
            name (str): Name to assign to the resulting Series.

        Returns:
            pandas.Series: A float Series with DatetimeIndex and the given `name`.

        Raises:
            TypeError: If the input is neither a pd.Series nor a pd.DataFrame.
        """
        if isinstance(data, pd.Series):
            s = data.copy()
            s.index = pd.to_datetime(s.index)
            s = s.astype(float)
            s.name = name
            return s

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input must be a pd.Series or pd.DataFrame")

        df: pd.DataFrame = data.copy()
        assert isinstance(df.index.name, str)
        if df.index.name and df.index.name.lower() == "date":
            idx: Union[pd.DatetimeIndex, pd.Series] = pd.to_datetime(df.index)
        elif "date" in df.columns:
            idx = pd.to_datetime(df["date"])
        else:
            cand = next((c for c in df.columns if "date" in c.lower()), None)
            if cand is not None:
                idx = pd.to_datetime(df[cand])
            else:
                idx = pd.to_datetime(df.index)
        if "value" in df.columns:
            vals = pd.to_numeric(df["value"], errors="coerce")
        else:
            num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if not num_cols:
                vals = pd.to_numeric(df.iloc[:, -1], errors="coerce")
            else:
                vals = pd.to_numeric(df[num_cols[0]], errors="coerce")

        s = pd.Series(vals.values, index=idx, name=name).astype(float)
        s = s[~s.index.duplicated(keep="last")].sort_index()
        s.index = pd.to_datetime(s.index)
        return s
    # Asynchronous methods
    @staticmethod
    async def to_pd_df_async(data: Dict[str, list]) -> pd.DataFrame:
        """
        Helper method to convert a FRED observation dictionary to a Pandas DataFrame asynchronously.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            pandas.DataFrame: Converted Pandas DataFrame.

        Raises:
            ValueError: If 'observations' key is not in the data.
        """
        return await asyncio.to_thread(FredHelpers.to_pd_df, data)
    @staticmethod
    async def to_pl_df_async(data: Dict[str, list]) -> 'pl.DataFrame':
        """
        Helper method to convert a FRED observation dictionary to a Polars DataFrame asynchronously.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            pandas.DataFrame: Converted Polars DataFrame.

        Raises:
            ImportError: If Polars is not installed.
            ValueError: If 'observations' key is not in the data.
        """
        return await asyncio.to_thread(FredHelpers.to_pl_df, data)
    @staticmethod
    async def to_dd_df_async(data: Dict[str, list]) -> 'dd.DataFrame':
        """
        Helper method to convert a FRED observation dictionary to a Dask DataFrame asynchronously.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            dask.dataframe.DataFrame: Converted Dask DataFrame.

        Raises:
            ImportError: If Dask is not installed.
            ValueError: If 'observations' key is not in the data.
        """
        try:
            import dask.dataframe as dd
        except ImportError as e:
            raise ImportError(
                f"{e}: Dask is not installed. Install it with `pip install dask` to use this method."
            ) from e
        df = await FredHelpers.to_pd_df_async(data)
        return await asyncio.to_thread(dd.from_pandas, df, npartitions=1)
    @staticmethod
    async def to_gpd_gdf_async(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> gpd.GeoDataFrame:
        """
        Helper method to convert a FRED observation dictionary to a GeoPandas GeoDataFrame asynchronously.

        Args:
            shapefile (gpd.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            gpd.GeoDataFrame: Converted GeoPandas GeoDataFrame.

        Raises:
            ValueError: If no data section is found in the response.
        """
        return await asyncio.to_thread(FredHelpers.to_gpd_gdf, shapefile, meta_data)
    @staticmethod
    async def to_dd_gpd_gdf_async(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'dd_gpd.GeoDataFrame':
        """
        Helper method to convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame asynchronously.

        Args:
            shapefile (gpd.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            dask_geopandas.GeoDataFrame: Converted Dask GeoPandas GeoDataFrame

        Raises:
            ImportError: If Dask GeoPandas is not installed.
            ValueError: If no data section is found in the response.
        """
        try:
            import dask_geopandas as dd_gpd
        except ImportError as e:
            raise ImportError(
                f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method."
            ) from e
        gdf = await FredHelpers.to_gpd_gdf_async(shapefile, meta_data)
        return await asyncio.to_thread(dd_gpd.from_geopandas, gdf, npartitions=1)
    @staticmethod
    async def to_pl_st_gdf_async(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'st.GeoDataFrame':
        """
        Helper method to convert a FRED observation dictionary to a Polars GeoDataFrame asynchronously.

        Args:
            shapefile (gpd.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            polars_st.GeoDataFrame: Converted Polars GeoDataFrame.

        Raises:
            ImportError: If Polars with geospatial support is not installed.
            ValueError: If no data section is found in the response.
        """
        try:
            import polars_st as st
        except ImportError as e:
            raise ImportError(
                f"{e}: Polars with geospatial support is not installed. Install it with `pip install polars-st` to use this method."
            ) from e
        gdf = await FredHelpers.to_gpd_gdf_async(shapefile, meta_data)
        return await asyncio.to_thread(st.from_geopandas, gdf)
    @staticmethod
    async def extract_region_type_async(response: Dict) -> str:
        """
        Helper method to extract the region type from a GeoFred response dictionary asynchronously.

        Args:
            response (Dict): FRED GeoFred response dictionary.

        Returns:
            str: Extracted region type.

        Raises:
            ValueError: If no meta data or region type is found in the response.
        """
        return await asyncio.to_thread(FredHelpers.extract_region_type, response)
    @staticmethod
    async def liststring_conversion_async(param: list[str]) -> str:
        """
        Helper method to convert a list of strings to a semicolon-separated string asynchronously.

        Args:
            param (list[str]): List of strings to convert.

        Returns:
            str: Semicolon-separated string.

        Raises:
            ValueError: If param is not a list of strings.
        """
        return await asyncio.to_thread(FredHelpers.liststring_conversion, param)
    @staticmethod
    async def vintage_dates_type_conversion_async(param: Union[str, datetime, list[Optional[Union[str, datetime]]]]) -> str:
        """
        Helper method to convert a vintage_dates parameter to a string asynchronously.

        Args:
            param (str | datetime | list[Optional[str | datetime]]]): vintage_dates parameter to convert.

        Returns:
            str: Converted vintage_dates string.

        Raises:
            ValueError: If param is not a string, datetime object, or list of strings/datetime objects.
        """
        return await asyncio.to_thread(FredHelpers.vintage_dates_type_conversion, param)
    @staticmethod
    async def datetime_conversion_async(param: datetime) -> str:
        """
        Helper method to convert a datetime object to a string in YYYY-MM-DD format asynchronously.

        Args:
            param (datetime): Datetime object to convert.

        Returns:
            str: Formatted date string.

        Raises:
            ValueError: If param is not a datetime object.
        """
        return await asyncio.to_thread(FredHelpers.datetime_conversion, param)
    @staticmethod
    async def datetime_hh_mm_conversion_async(param: datetime) -> str:
        """
        Helper method to convert a datetime object to a string in HH:MM format asynchronously.

        Args:
            param (datetime): Datetime object to convert.

        Returns:
            str: Formatted time string.

        Raises:
            ValueError: If param is not a datetime object.
        """
        return await asyncio.to_thread(FredHelpers.datetime_hh_mm_conversion, param)
    @staticmethod
    async def datestring_validation_async(param: str) -> Optional[ValueError]:
        """
        Helper method to validate date-string formatted parameter asynchronously.

        Args:
            param (str): Date string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid date string in YYYY-MM-DD format.
        """
        return await asyncio.to_thread(FredHelpers.datestring_validation, param)
    @staticmethod
    async def liststring_validation_async(param: str) -> Optional[ValueError]:
        """
        Helper method to validate list-string formatted parameters asynchronously.

        Args:
            param (str): Semicolon-separated string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid semicolon-separated string.
        """
        return await asyncio.to_thread(FredHelpers.liststring_validation, param)
    @staticmethod
    async def vintage_dates_validation_async(param: str) -> Optional[ValueError]:
        """
        Helper method to validate vintage_dates parameters asynchronously.

        Args:
            param (str): Comma-separated string of vintage dates.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid vintage_dates string.
        """
        return await asyncio.to_thread(FredHelpers.vintage_dates_validation, param)
    @staticmethod
    async def hh_mm_datestring_validation_async(param: str) -> Optional[ValueError]:
        """
        Helper method to validate hh:mm formatted parameters asynchronously.

        Args:
            param (str): Time string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid time string in HH:MM format.
        """
        return await asyncio.to_thread(FredHelpers.hh_mm_datestring_validation, param)
    @staticmethod
    async def parameter_validation_async(params: Dict[str, Optional[Union[str, int]]]) -> Optional[ValueError]:
        """
        Helper method to validate parameters prior to making a get request asynchronously.

        Args:
            params (Dict[str, Optional[str | int]]): Dictionary of parameters to validate.

        Returns:
            None

        Raises:
            ValueError: If any parameter is invalid.
        """
        for k, v in params.items():
            if k == 'category_id':
                if not isinstance(v, int) or v < 0:
                    raise ValueError("category_id must be a non-negative integer")
            elif k == 'realtime_start':
                if not isinstance(v, str):
                    raise ValueError("realtime_start must be a string in YYYY-MM-DD format")
                try:
                    await FredHelpers.datestring_validation_async(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'realtime_end':
                if not isinstance(v, str):
                    raise ValueError("realtime_end must be a string in YYYY-MM-DD format")
                try:
                    await FredHelpers.datestring_validation_async(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'limit':
                if not isinstance(v, int) or v < 0:
                    raise ValueError("limit must be a non-negative integer")
            elif k == 'offset':
                if not isinstance(v, int) or v < 0:
                    raise ValueError("offset must be a non-negative integer")
            elif k == 'sort_order':
                if not isinstance(v, str) or v not in ['asc', 'desc']:
                    raise ValueError("sort_order must be 'asc' or 'desc'")
            elif k == 'order_by':
                if not isinstance(v, str) or v not in ['series_id', 'title', 'units', 'frequency', 'seasonal_adjustment',
                                                       'realtime_start', 'realtime_end', 'last_updated', 'observation_start',
                                                       'observation_end', 'popularity', 'group_popularity', 'series_count',
                                                       'created', 'name', 'release_id', 'press_release', 'group_id',
                                                       'search_rank', 'title']:
                    raise ValueError("order_by must be one of the valid options")
            elif k == 'filter_variable':
                if not isinstance(v, str) or v not in ['frequency', 'units', 'seasonal_adjustment']:
                    raise ValueError("filter_variable must be one of the valid options")
            elif k == 'filter_value':
                if not isinstance(v, str):
                    raise ValueError("filter_value must be a string")
            elif k == 'tag_names':
                if not isinstance(v, str):
                    raise ValueError("tag_names must be a string")
                try:
                    await FredHelpers.liststring_validation_async(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'exclude_tag_names':
                if not isinstance(v, str):
                    raise ValueError("exclude_tag_names must be a string")
                try:
                    await FredHelpers.liststring_validation_async(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'tag_group_id':
                if not (isinstance(v, int) and v >= 0) and not isinstance(v, str):
                    raise ValueError("tag_group_id must be a non-negative integer or a string")
            elif k == 'search_text':
                if not isinstance(v, str):
                    raise ValueError("search_text must be a string")
            elif k == 'file_type':
                if not isinstance(v, str) or v != 'json':
                    raise ValueError("file_type must be 'json'")
            elif k == 'api_key':
                if not isinstance(v, str):
                    raise ValueError("api_key must be a string")
            elif k == 'include_releases_dates_with_no_data':
                if not isinstance(v, bool):
                    raise ValueError("include_releases_dates_with_no_data must be a boolean")
            elif k == 'release_id':
                if not isinstance(v, int) or v < 0:
                    raise ValueError("release_id must be a non-negative integer")
            elif k == 'series_id':
                if not isinstance(v, str):
                    raise ValueError("series_id must be a string")
                if ' ' in v:
                    raise ValueError("series_id cannot contain whitespace")
                if v == '':
                    raise ValueError("series_id cannot be empty")
                if not v.isalnum():
                    raise ValueError("series_id must be alphanumeric")
            elif k == 'frequency':
                if not isinstance(v, str):
                    raise ValueError("frequency must be a string")
                if v not in ['d', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem']:
                    raise ValueError("frequency must be one of the valid options")
            elif k == 'units':
                if not isinstance(v, str):
                    raise ValueError("units must be a string")
                if v not in ['lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log']:
                    raise ValueError("units must be one of the valid options")
            elif k == 'aggregation_method':
                if not isinstance(v, str):
                    raise ValueError("aggregation_method must be a string")
                if v not in ['sum', 'avg', 'eop']:
                    raise ValueError("aggregation_method must be one of the valid options")
            elif k == 'output_type':
                if not isinstance(v, int):
                    raise ValueError("output_type must be an integer")
                if v not in [1, 2, 3, 4]:
                    raise ValueError("output_type must be '1', '2', '3', or '4'")
            elif k == 'vintage_dates':
                if not isinstance(v, str):
                    raise ValueError("vintage_dates must be a string")
                try:
                    await FredHelpers.vintage_dates_validation_async(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'search_type':
                if not isinstance(v, str):
                    raise ValueError("search_type must be a string")
                if v not in ['full_text', 'series_id']:
                    raise ValueError("search_type must be 'full_text' or 'series_id'")
            elif k == 'tag_search_text':
                if not isinstance(v, str):
                    raise ValueError("tag_search_text must be a string")
            elif k == 'start_time':
                if not isinstance(v, str):
                    raise ValueError("start_time must be a string")
                try:
                    await FredHelpers.hh_mm_datestring_validation_async(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'end_time':
                if not isinstance(v, str):
                    raise ValueError("end_time must be a string")
                try:
                    await FredHelpers.hh_mm_datestring_validation_async(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'season':
                if not isinstance(v, str):
                    raise ValueError("season must be a string")
                if v not in ['seasonally_adjusted', 'not_seasonally_adjusted']:
                    raise ValueError("season must be 'seasonally_adjusted' or 'not_seasonally_adjusted'")
        return None
    @staticmethod
    async def geo_parameter_validation_async(params: Dict[str, Optional[Union[str, int]]]) -> Optional[ValueError]:
        """
        Helper method to validate parameters prior to making a get request.

        Args:
            params (Dict[str, Optional[str | int]]): Dictionary of parameters to validate

        Returns:
            None

        Raises:
            ValueError: If any parameter is invalid.
        """
        for k, v in params.items():
            if k == 'api_key':
                if not isinstance(v, str):
                    raise ValueError("api_key must be a string")
            elif k == 'file_type':
                if not isinstance(v, str) or v != 'json':
                    raise ValueError("file_type must be 'json'")
            elif k == 'shape':
                if not isinstance(v, str):
                    raise ValueError("shape must be a string")
                if v not in ['bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision']:
                    raise ValueError("shape must be 'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', or 'censusdivision'")
            elif k == 'series_id':
                if not isinstance(v, str):
                    raise ValueError("series_id must be a string")
                if ' ' in v:
                    raise ValueError("series_id cannot contain whitespace")
                if v == '':
                    raise ValueError("series_id cannot be empty")
                if not v.isalnum():
                    raise ValueError("series_id must be alphanumeric")
            elif k == 'date':
                if not isinstance(v, str):
                    raise ValueError("date must be a string")
                try:
                    await FredHelpers.datestring_validation_async(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'start_date':
                if not isinstance(v, str):
                    raise ValueError("start_date must be a string")
                try:
                    await FredHelpers.datestring_validation_async(v)
                except ValueError as e:
                    raise ValueError(f"{e}") from e
            elif k == 'series_group':
                if not isinstance(v, str):
                    raise ValueError("series_group must be a string")
            elif k == 'region_type':
                if not isinstance(v, str):
                    raise ValueError("region_type must be a string")
                if v not in ['bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision']:
                    raise ValueError("region_type must be 'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', or 'censusdivision'")
            elif k == 'aggregation_method':
                if not isinstance(v, str):
                    raise ValueError("aggregation_method must be a string")
                if v not in ['sum', 'avg', 'eop']:
                    raise ValueError("aggregation_method must be 'sum', 'avg', or 'eop'")
            elif k == 'units':
                if not isinstance(v, str):
                    raise ValueError("units must be a string")
            elif k == 'season':
                if not isinstance(v, str):
                    raise ValueError("season must be a string")
                if v not in ['NSA', 'SA', 'SSA', 'SAAR', 'NSAAR']:
                    raise ValueError("season must be 'NSA', 'SA', 'SSA', 'SAAR', or 'NSAAR'")
            elif k == 'transformation':
                if not isinstance(v, str):
                    raise ValueError("transformation must be a string")
                if v not in ['lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log']:
                    raise ValueError("transformation must be 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', or 'log'")
        return None
    @staticmethod
    async def pd_frequency_conversion_async(frequency: str) -> str:
        """
        Asynchronously convert fedfred native frequency strings to pandas compatible ones.

        Args:
            frequency (str): Input frequency string.

        Returns:
            str: Coerced frequency string compatible with pandas.

        Raises:
            None
        """
        return await asyncio.to_thread(FredHelpers.pd_frequency_conversion, frequency)
    @staticmethod
    async def to_pd_series_async(data: Union[pd.Series, pd.DataFrame], name: str) -> pd.Series:
        """
        Asynchronously accepts a Series or a DataFrame with 'date' and 'value' columns (fedfred style) and returns a float Series with DatetimeIndex and the given name.

        Args:
            data (pd.Series | pd.DataFrame): Input data to be converted.
            name (str): Name to assign to the resulting Series.

        Returns:
            pd.Series: A float Series with DatetimeIndex and the given `name`.

        Raises:
            TypeError: If the input is neither a pd.Series nor a pd.DataFrame.
        """
        return await asyncio.to_thread(FredHelpers.to_pd_series, data, name)
