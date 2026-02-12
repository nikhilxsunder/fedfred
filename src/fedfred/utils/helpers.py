# filepath: /src/fedfred/utils/helpers.py
#
# Copyright (c) 2025–2026 Nikhil Sunder
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
"""fedfred.utils.helpers

This module provides helper methods for the FRED API.

Classes:
    Helpers: A class that provides helper methods for the FRED API.

Examples:
    >>> from fedfred import Helpers
    >>> data = {
    >>>     "observations": [
    >>>         {"date": "2020-01-01", "value": "100
    >>>         {"date": "2020-02-01", "value": "200"},
    >>>         {"date": "2020-03-01", "value": "300"},
    >>>     ]
    >>> }
    >>> df = Helpers.to_pd_df(data)
    >>> print(df)
                value
    date
    2020-01-01  100.0
    2020-02-01  200.0
    2020-03-01  300.0

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
    - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
"""

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional, Union, Tuple
import pandas as pd
import geopandas as gpd
from .maps import FRED_PARAMETERS_MAP, GEOFRED_PARAMETERS_MAP, FREQUENCIES_MAP, FRASER_PARAMETERS_MAP
from ..__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__

if TYPE_CHECKING:
    import dask.dataframe as dd # pragma: no cover
    import dask_geopandas as dd_gpd # pragma: no cover
    import polars as pl # pragma: no cover
    import polars_st as st # pragma: no cover

class Helpers:
    """A class that provides helper methods.

    This class contains static methods that assist in data conversion and validation
    for interacting with the FRED API. It includes methods for converting FRED
    observation dictionaries to various DataFrame formats (Pandas, Polars, Dask,
    GeoPandas, Dask GeoPandas, Polars GeoDataFrame) as well as methods for validating
    and converting parameters used in FRED API requests.

    Notes:
        Some methods require additional libraries (Polars, Dask, Dask GeoPandas, Polars GeoDataFrame). Ensure these libraries 
        are installed to use the corresponding methods.

    Examples:
        >>> import fedfred as fd
        >>> data = {
        >>>     "observations": [
        >>>         {"date": "2020-01-01", "value": "100"},
        >>>         {"date": "2020-02-01", "value": "200"},
        >>>         {"date": "2020-03-01", "value": "300"},
        >>>     ]
        >>> }
        >>> df = fd.Helpers.to_pd_df(data)
        >>> print(df)
                    value
        date
        2020-01-01  100.0
        2020-02-01  200.0
        2020-03-01  300.0

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.html
    """

    # Synchronous methods
    @staticmethod
    def to_pd_df(data: Dict[str, list]) -> pd.DataFrame:
        """Helper method to convert a fred observation dictionary to a Pandas DataFrame.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            pandas.DataFrame: Converted Pandas DataFrame.

        Raises:
            ValueError: If 'observations' key is not in the data.

        Examples:
            >>> import fedfred as fd
            >>> data = {
            >>>     "observations": [
            >>>         {"date": "2020-01-01", "value": "100"},
            >>>         {"date": "2020-02-01", "value": "200"},
            >>>         {"date": "2020-03-01", "value": "300"},
            >>>     ]
            >>> }
            >>> df = fd.Helpers.to_pd_df(data)
            >>> print(df)
                        value
            date
            2020-01-01  100.0
            2020-02-01  200.0
            2020-03-01  300.0

        Notes:
            The 'date' column is converted to a DatetimeIndex and set as the DataFrame index and the 'value' column is converted to numeric, with non-numeric values coerced to NaN.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_pd_df.html

        See Also:
            - :meth:`Helpers.to_pl_df`: Convert a FRED observation dictionary to a Polars DataFrame.
            - :meth:`Helpers.to_dd_df`: Convert a FRED observation dictionary to a Dask DataFrame.
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
        """Helper method to convert a fred observation dictionary to a Polars DataFrame.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            polars.DataFrame: Converted Polars DataFrame.

        Raises:
            ImportError: If Polars is not installed.
            ValueError: If 'observations' key is not in the data.

        Examples:
            >>> import fedfred as fd
            >>> data = {
            >>>     "observations": [
            >>>         {"date": "2020-01-01", "value": "100"},
            >>>         {"date": "2020-02-01", "value": "200"},
            >>>         {"date": "2020-03-01", "value": "300"},
            >>>     ]
            >>> }
            >>> df = fd.Helpers.to_pl_df(data)
            >>> print(df)
            shape: (3, 2)
            ┌────────────┬───────┐
            │ date       ┆ value │
            │ ---        ┆ ---   │
            │ date       ┆ f64   │
            ╞════════════╪═══════╡
            │ 2020-01-01 ┆ 100.0 │
            │ 2020-02-01 ┆ 200.0 │
            │ 2020-03-01 ┆ 300.0 │
            └────────────┴───────┘

        Notes:
            The 'value' column is converted to Float64, with 'NA' values replaced with None.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_pl_df.html

        See Also:
            - :meth:`Helpers.to_pd_df`: Convert a FRED observation dictionary to a Pandas DataFrame.
            - :meth:`Helpers.to_dd_df`: Convert a FRED observation dictionary to a Dask DataFrame.
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
        """Helper method to convert a FRED observation dictionary to a Dask DataFrame.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            dask.dataframe.DataFrame: Converted Dask DataFrame.

        Raises:
            ImportError: If Dask is not installed.
            ValueError: If 'observations' key is not in the data.

        Examples:
            >>> import fedfred as fd
            >>> data = {
            >>>     "observations": [
            >>>         {"date": "2020-01-01", "value": "100"},
            >>>         {"date": "2020-02-01", "value": "200"},
            >>>         {"date": "2020-03-01", "value": "300"},
            >>>     ]
            >>> }
            >>> df = fd.Helpers.to_dd_df(data)
            >>> print(df.compute())
                        value
            date
            2020-01-01  100.0
            2020-02-01  200.0
            2020-03-01  300.0

        Notes:
            This method first converts the data to a Pandas DataFrame and then to a Dask DataFrame with a single partition.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_dd_df.html

        See Also:
            - :meth:`Helpers.to_pd_df`: Convert a FRED observation dictionary to a Pandas DataFrame.
            - :meth:`Helpers.to_pl_df`: Convert a FRED observation dictionary to a Polars DataFrame.
        """

        try:
            import dask.dataframe as dd
        except ImportError as e:
            raise ImportError(
                f"{e}: Dask is not installed. Install it with `pip install dask` to use this method."
            ) from e
        df = Helpers.to_pd_df(data)
        return dd.from_pandas(df, npartitions=1)

    @staticmethod
    def to_gpd_gdf(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> gpd.GeoDataFrame:
        """Helper method to convert a FRED observation dictionary to a GeoPandas GeoDataFrame.

        Args:
            shapefile (geopandas.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            geopandas.GeoDataFrame: Converted GeoPandas GeoDataFrame.

        Raises:
            ValueError: If no data section is found in the response.

        Examples:
            >>> import fedfred as fd
            >>> import geopandas as gpd
            >>> shapefile = gpd.read_file("path_to_shapefile.shp")
            >>> meta_data = {
            >>>     "data": {
            >>>         "observations": [
            >>>             {"region": "Region1", "value": 100, "series_id": "S1"},
            >>>             {"region": "Region2", "value": 200, "series_id": "S2"},
            >>>         ]
            >>>     }
            >>> }
            >>> gdf = fd.Helpers.to_gpd_gdf(shapefile, meta_data)
            >>> print(gdf)
                name  value series_id                     geometry
            0  Region1  100.0        S1  POLYGON ((...))
            1  Region2  200.0        S2  POLYGON ((...))

        Notes:
            This method adds 'value' and 'series_id' columns to the GeoDataFrame based on the provided metadata.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_gpd_gdf.html

        See Also:
            - :meth:`Helpers.to_dd_gpd_gdf`: Convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame.
            - :meth:`Helpers.to_pl_st_gdf`: Convert a FRED observation dictionary to a Polars GeoDataFrame.
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
        """Helper method to convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame.

        Args:
            shapefile (geopandas.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            dask_geopandas.GeoDataFrame: Converted Dask GeoPandas GeoDataFrame.

        Raises:
            ImportError: If Dask GeoPandas is not installed.
            ValueError: If no data section is found in the response.

        Examples:
            >>> import fedfred as fd
            >>> import geopandas as gpd
            >>> shapefile = gpd.read_file("path_to_shapefile.shp")
            >>> meta_data = {
            >>>     "data": {
            >>>         "observations": [
            >>>             {"region": "Region1", "value": 100, "series_id": "S1"},
            >>>             {"region": "Region2", "value": 200, "series_id": "S2"},
            >>>         ]
            >>>     }
            >>> }
            >>> gdf = fd.Helpers.to_dd_gpd_gdf(shapefile, meta_data)
            >>> print(gdf.compute())
                name  value series_id                     geometry
            0  Region1  100.0        S1  POLYGON ((...))
            1  Region2  200.0        S2  POLYGON ((...))

        Notes:
            This method first converts the data to a GeoPandas GeoDataFrame and then to a Dask GeoPandas GeoDataFrame with a single partition.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_dd_gpd_gdf.html

        See Also:
            - :meth:`Helpers.to_gpd_gdf`: Convert a FRED observation dictionary to a GeoPandas GeoDataFrame.
            - :meth:`Helpers.to_pl_st_gdf`: Convert a FRED observation dictionary to a Polars GeoDataFrame.
        """

        try:
            import dask_geopandas as dd_gpd
        except ImportError as e:
            raise ImportError(
                f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method."
            ) from e
        gdf = Helpers.to_gpd_gdf(shapefile, meta_data)
        return dd_gpd.from_geopandas(gdf, npartitions=1)

    @staticmethod
    def to_pl_st_gdf(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'st.GeoDataFrame':
        """Helper method to convert a FRED observation dictionary to a Polars GeoDataFrame.

        Args:
            shapefile (geopandas.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            polars_st.GeoDataFrame: Converted Polars GeoDataFrame.

        Raises:
            ImportError: If Polars with geospatial support is not installed.
            ValueError: If no data section is found in the response.
            
        Examples:
            >>> import fedfred as fd
            >>> import geopandas as gpd
            >>> shapefile = gpd.read_file("path_to_shapefile.shp")
            >>> meta_data = {
            >>>     "data": {
            >>>         "observations": [
            >>>             {"region": "Region1", "value": 100, "series_id": "S1"},
            >>>             {"region": "Region2", "value": 200, "series_id": "S2"},
            >>>         ]
            >>>     }
            >>> }
            >>> gdf = fd.Helpers.to_pl_st_gdf(shapefile, meta_data)
            >>> print(gdf)
            shape: (2, 3)
            ┌─────────┬───────┬───────────┬────────────────────────┐
            │ name    ┆ value ┆ series_id ┆ geometry               │
            │ ---     ┆ ---   ┆ ---       ┆ ---                    │
            │ str     ┆ f64   ┆ str       ┆ geo                    │
            ╞═════════╪═══════╪═══════════╪════════════════════════╡
            │ Region1 ┆ 100.0 ┆ S1        ┆ POLYGON ((...))        │
            │ Region2 ┆ 200.0 ┆ S2        ┆ POLYGON ((...))        │
            └─────────┴───────┴───────────┴────────────────────────┘

        Notes:
            This method first converts the data to a GeoPandas GeoDataFrame and then to a Polars GeoDataFrame.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_pl_st_gdf.html

        See Also:
            - :meth:`Helpers.to_gpd_gdf`: Convert a FRED observation dictionary to a GeoPandas GeoDataFrame.
            - :meth:`Helpers.to_dd_gpd_gdf`: Convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame.
        """

        try:
            import polars_st as st
        except ImportError as e:
            raise ImportError(
                f"{e}: Polars with geospatial support is not installed. Install it with `pip install polars-st` to use this method."
            ) from e
        gdf = Helpers.to_gpd_gdf(shapefile, meta_data)
        return st.from_geopandas(gdf)

    @staticmethod
    def extract_region_type(response: Dict) -> str:
        """Helper method to extract the region type from a GeoFred response dict.

        Args:
            response (Dict): FRED GeoFred response dictionary.

        Returns:
            str: Extracted region type.

        Raises:
            ValueError: If no meta data or region type is found in the response.
        
        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "meta": {
            >>>         "region_type": "state"
            >>>     },
            >>>     "data": {
            >>>         "observations": []
            >>>     }
            >>> }
            >>> region_type = fd.Helpers.extract_region_type(response)
            >>> print(region_type)
            state

        Notes:
            This method looks for the 'region' key in the 'meta' section of the response dictionary.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.extract_region_type.html

        See Also:
            - :meth:`Helpers.to_gpd_gdf`: Convert a FRED observation dictionary to a GeoPandas GeoDataFrame.
            - :meth:`Helpers.to_dd_gpd_gdf`: Convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame.
            - :meth:`Helpers.to_pl_st_gdf`: Convert a FRED observation dictionary to a Polars GeoDataFrame.
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
        """Helper method to convert a list of strings to a semicolon-separated string.

        Args:
            param (list[str]): List of strings to convert.

        Returns:
            str: Semicolon-separated string.

        Raises:
            ValueError: If param is not a list of strings.

        Examples:
            >>> import fedfred as fd
            >>> param = ["tag1", "tag2", "tag3"]
            >>> result = fd.Helpers.liststring_conversion(param)
            >>> print(result)
            tag1;tag2;tag3

        Notes:
            This method joins the elements of the list with semicolons.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.liststring_conversion.html

        See Also:
            - :meth:`Helpers.liststring_validation`: Validate a semicolon-separated string.
        """

        if not isinstance(param, list):
            raise ValueError("Parameter must be a list")
        if any(not isinstance(i, str) for i in param):
            raise ValueError("All elements in the list must be strings")
        return ';'.join(param)

    @staticmethod
    def vintage_dates_type_conversion(param: Union[str, datetime, list[Optional[Union[str, datetime]]]]) -> str:
        """Helper method to convert a vintage_dates parameter to a string.

        Args:
            param (str | datetime | list[Optional[str | datetime]]): vintage_dates parameter to convert.

        Returns:
            str: Converted vintage_dates string.

        Raises:
            ValueError: If param is not a string, datetime object, or list of strings/datetime objects.

        Examples:
            >>> import fedfred as fd
            >>> param1 = "2020-01-01"
            >>> result1 = fd.Helpers.vintage_dates_type_conversion(param1)
            >>> print(result1)
            2020-01-01

        Notes:
            This method handles single strings, datetime objects, and lists of strings/datetime objects.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.vintage_dates_type_conversion.html

        See Also:
            - :meth:`Helpers.datetime_conversion`: Convert a datetime object to a string in YYYY-MM-DD format.
            - :meth:`Helpers.vintage_dates_validation`: Validate vintage_dates parameters.
        """

        if isinstance(param, str):
            return param
        elif isinstance(param, datetime):
            return Helpers.datetime_conversion(param)
        elif isinstance(param, list):
            converted_list = [
                Helpers.datetime_conversion(i) if isinstance(i, datetime) else i
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
        """Helper method to convert a datetime object to a string in YYYY-MM-DD format.

        Args:
            param (datetime): Datetime object to convert.

        Returns:
            str: Formatted date string.

        Raises:
            ValueError: If param is not a datetime object.

        Examples:
            >>> import fedfred as fd
            >>> from datetime import datetime
            >>> param = datetime(2020, 1, 1)
            >>> result = fd.Helpers.datetime_conversion(param)
            >>> print(result)
            2020-01-01

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.datetime_conversion.html

        See Also:
            - :meth:`Helpers.datetime_hh_mm_conversion`: Convert a datetime object to a string in HH:MM format.
            - :meth:`Helpers.datestring_validation`: Validate date-string formatted parameters.
        """

        if not isinstance(param, datetime):
            raise ValueError("Parameter must be a datetime object")
        return param.strftime("%Y-%m-%d")

    @staticmethod
    def datetime_hh_mm_conversion(param: datetime) -> str:
        """Helper method to convert a datetime object to a string in HH:MM format.

        Args:
            param (datetime): Datetime object to convert.

        Returns:
            str: Formatted time string.

        Raises:
            ValueError: If param is not a datetime object.

        Examples:
            >>> import fedfred as fd
            >>> from datetime import datetime
            >>> param = datetime(2020, 1, 1, 15, 30)
            >>> result = fd.Helpers.datetime_hh_mm_conversion(param)
            >>> print(result)
            15:30

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.datetime_hh_mm_conversion.html

        See Also:
            - :meth:`Helpers.datetime_conversion`: Convert a datetime object to a string in YYYY-MM-DD format.
            - :meth:`Helpers.hh_mm_datestring_validation`: Validate hh:mm formatted parameters.
        """

        if not isinstance(param, datetime):
            raise ValueError("Parameter must be a datetime object")
        return param.strftime("%H:%M")

    @staticmethod
    def parameter_validation(params: Dict[str, Optional[Union[str, int]]]) -> Optional[ValueError]:
        """Helper method to validate parameters prior to making a get request.

        Args:
            params (Dict[str, Optional[str | int]]): Dictionary of parameters to validate.

        Returns:
            None

        Raises:
            ValueError: If any parameter is invalid.

        Examples:
            >>> import fedfred as fd
            >>> params = {
            >>>     "category_id": 125,
            >>>     "realtime_start": "2020-01-01",
            >>>     "limit": 100,
            >>>     "sort_order": "asc",
            >>> }
            >>> result = fd.Helpers.parameter_validation(params)
            >>> print(result)
            None

        Notes:
            This method checks each parameter against expected types and formats, raising a ValueError for any invalid parameters.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.parameter_validation.html

        See Also:
            - :meth:`Helpers.datestring_validation`: Validate date-string formatted parameters.
            - :meth:`Helpers.liststring_validation`: Validate list-string formatted parameters.
            - :meth:`Helpers.hh_mm_datestring_validation`: Validate hh:mm formatted parameters.
            - :meth:`Helpers.vintage_dates_validation`: Validate vintage_dates parameters.
        """
        
        for k, v in params.items():
            if k in FRED_PARAMETERS_MAP:
                validator = FRED_PARAMETERS_MAP[k]
                assert isinstance(validator, dict)
                if 'type_condition' in validator.keys():
                    type_func = validator['type_condition']
                    assert callable(type_func)
                    try:
                        type_func(v)
                    except ValueError as e:
                        raise ValueError(f"Parameter '{k}' failed type validation: {e}: {validator['error_message']}") from e
                if 'value_condition' in validator.keys():
                    value_func = validator['value_condition']
                    assert callable(value_func)
                    try:
                        value_func(v)
                    except ValueError as e:
                        raise ValueError(f"Parameter '{k}' failed value validation: {e}: {validator['error_message']}") from e
                if 'complex_condition' in validator.keys():
                    complex_func = validator['complex_condition']
                    assert callable(complex_func)
                    try:
                        complex_func(v, params)
                    except ValueError as e:
                        raise ValueError(f"Parameter '{k}' failed complex validation: {e}: {validator['error_message']}") from e
        return None

    @staticmethod
    def geo_parameter_validation(params: Dict[str, Optional[Union[str, int]]]) -> Optional[ValueError]:
        """Helper method to validate geo-parameters prior to making a maps get request.

        Args:
            params (Dict[str, Optional[str | int]]): Dictionary of parameters to validate

        Returns:
            None

        Raises:
            ValueError: If any parameter is invalid.

        Examples:
            >>> import fedfred as fd
            >>> params = {
            >>>     "api_key": "your_api_key",
            >>>     "file_type": "json",
            >>>     "shape": "state",
            >>>     "series_id": "GDP",
            >>>     "date": "2020-01-01",
            >>>     "start_date": "2010-01-01",
            >>>     "series_group": "group1",
            >>>     "region_type": "state",
            >>>     "aggregation_method": "sum",
            >>>     "units": "lin",
            >>>     "season": "SA",
            >>>     "transformation": "chg",
            >>> }
            >>> result = fd.Helpers.geo_parameter_validation(params)
            >>> print(result)
            None

        Notes:
            This method checks for valid types and values for geo-related parameters.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.geo_parameter_validation.html

        See Also:
            - :meth:`Helpers.datestring_validation`: Validate date-string formatted parameters.
            - :meth:`Helpers.liststring_validation`: Validate list-string formatted parameters.
            - :meth:`Helpers.hh_mm_datestring_validation`: Validate hh:mm formatted parameters.
            - :meth:`Helpers.vintage_dates_validation`: Validate vintage_dates parameters.
        """

        for k, v in params.items():
            if k in GEOFRED_PARAMETERS_MAP:
                validator = GEOFRED_PARAMETERS_MAP[k]
                assert isinstance(validator, dict)
                if 'type_condition' in validator.keys():
                    type_func = validator['type_condition']
                    assert callable(type_func)
                    try:
                        type_func(v)
                    except ValueError as e:
                        raise ValueError(f"Geo Parameter '{k}' failed type validation: {e}: {validator['error_message']}") from e
                if 'value_condition' in validator.keys():
                    value_func = validator['value_condition']
                    assert callable(value_func)
                    try:
                        value_func(v)
                    except ValueError as e:
                        raise ValueError(f"GeoParameter '{k}' failed value validation: {e}: {validator['error_message']}") from e
                if 'complex_condition' in validator.keys():
                    complex_func = validator['complex_condition']
                    assert callable(complex_func)
                    try:
                        complex_func(v, params)
                    except ValueError as e:
                        raise ValueError(f"Geo Parameter '{k}' failed complex validation: {e}: {validator['error_message']}") from e
        return None

    @staticmethod
    def fraser_parameter_validation(params: Dict[str, Optional[Union[str, int]]]) -> None:
        """Helper method to validate fraser-parameters prior to making a fraser get request.

        Args:
            params (Dict[str, Optional[str | int]]): Dictionary of parameters to validate

        Raises:
            ValueError: If any parameter is invalid.

        Examples:
            >>> import fedfred as fd
            >>> params = {
            >>>     "limit": 100,
            >>>     "page": 1,
            >>>     "role": "creator",
            >>> }
            >>> result = fd.Helpers.fraser_parameter_validation(params)
            >>> print(result)
            None

        Notes:
            This method checks for valid types and values for fraser-related parameters.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.fraser_parameter_validation.html

        See Also:
            - :meth:`Helpers.parameter_validation`: Validate parameters for standard FRED API requests.
        """

        for k,v in params.items():
            if k in FRASER_PARAMETERS_MAP:
                validator = FRASER_PARAMETERS_MAP[k]
                assert isinstance(validator, dict)
                if 'type_condition' in validator.keys():
                    type_func = validator['type_condition']
                    assert callable(type_func)
                    try:
                        type_func(v)
                    except ValueError as e:
                        raise ValueError(f"Fraser Parameter '{k}' failed type validation: {e}: {validator['error_message']}") from e
                if 'value_condition' in validator.keys():
                    value_func = validator['value_condition']
                    assert callable(value_func)
                    try:
                        value_func(v)
                    except ValueError as e:
                        raise ValueError(f"Fraser Parameter '{k}' failed value validation: {e}: {validator['error_message']}") from e
                if 'complex_condition' in validator.keys():
                    complex_func = validator['complex_condition']
                    assert callable(complex_func)
                    try:
                        complex_func(v, params)
                    except ValueError as e:
                        raise ValueError(f"Fraser Parameter '{k}' failed complex validation: {e}: {validator['error_message']}") from e
        return None

    @staticmethod
    def pd_frequency_conversion(frequency: str) -> str:
        """Convert FRED native frequency strings to pandas compatible ones.

        Args:
            frequency (str): Input frequency string.

        Returns:
            str: Coerced frequency string compatible with pandas.

        Raises:
            ValueError: If the input frequency is not recognized.

        Examples:
            >>> import fedfred as fd
            >>> freq = "a"
            >>> pd_freq = fd.Helpers.pd_frequency_conversion(freq)
            >>> print(pd_freq)
            Y

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.pd_frequency_conversion.html

        See Also:
            - :meth:`Helpers.to_pd_series`: Convert a Series or DataFrame to a pandas Series with DatetimeIndex.
        """

        frequency = frequency.upper()
        if frequency in FREQUENCIES_MAP:
            return FREQUENCIES_MAP[frequency]
        else:
            raise ValueError(f"Frequency '{frequency}' is not recognized.")
    
    @staticmethod
    def to_pd_series(data: Union[pd.Series, pd.DataFrame], name: str) -> pd.Series:
        """Accepts a Series or a DataFrame with 'date' and 'value' columns and returns a float Series with DatetimeIndex and the given name.

        Args:
            data (pandas.Series | pandas.DataFrame): Input data to be converted.
            name (str): Name to assign to the resulting Series.

        Returns:
            pandas.Series: A float Series with DatetimeIndex and the given `name`.

        Raises:
            TypeError: If the input is neither a pandas.Series nor a pandas.DataFrame.

        Examples:
            >>> import fedfred as fd
            >>> import pandas as pd
            >>> data = pd.DataFrame({
            >>>     "date": ["2020-01-01", "2020-02-01"],
            >>>     "value": [100, 200]
            >>> })
            >>> series = fd.Helpers.to_pd_series(data, name="My Series")
            >>> print(series)
            2020-01-01    100.0
            2020-02-01    200.0
            Name: My Series, dtype: float64

        Notes:
            This method handles both Series and DataFrame inputs, ensuring the output is a properly formatted pandas Series.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_pd_series.html

        See Also:
            - :meth:`Helpers.pd_frequency_conversion`: Convert FRED native frequency strings to pandas compatible ones.
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

    @staticmethod
    def to_pl_series(self, data: Union[pl.Series, pl.DataFrame], name:str) -> pl.Series: # Add this helpers logic before release
        """Accepts a Polars Series or a DataFrame with 'date' and 'value' columns and returns a float Series with DatetimeIndex and the given name.
        
        Args:
            data (polars.Series | polars.DataFrame): Input data to be converted.
            name (str): Name to assign to the resulting Series.

        Returns:
            polars.Series: A float Series with DatetimeIndex and the given `name`.

        Raises:
            TypeError: If the input is neither a polars.Series nor a polars.DataFrame

        Examples:

        Notes:

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_pl_series.html
        
        See Also:
            - :meth:`Helpers.to_pd_series`: Convert a Series or DataFrame to a pandas Series with DatetimeIndex.
        """

        return None

    @staticmethod
    def to_hashable(data: Optional[Dict[str, Optional[Union[str, int]]]]) -> Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]:
        """Helper function to make the data dictionary hashable for caching.

        Args:
            data (Dict[str, Optional[str | int]], optional): The query parameters for the request.

        Returns:
            Optional[Tuple[Tuple[str, Optional[str | int]], ...]]: A hashable representation of the data dictionary.

        Notes:
            This function converts the data dictionary into a sorted tuple of key-value pairs, making it suitable 
            for use as a cache key.

        Warnings:
            Caching is only applied if `cache_mode` is enabled. Ensure that the `data` parameter is hashable for 
            caching to work correctly.
        """

        if data is None:
            return None
        return tuple(sorted(data.items()))

    @staticmethod
    def to_dict(hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]) -> Optional[Dict[str, Optional[Union[str, int]]]]:
        """Helper function to convert hashable data back to a dictionary.
        
        Args:
            hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]]): The hashable representation of the data.

        Returns:
            Optional[Dict[str, Optional[str | int]]]: The original data dictionary.

        Notes:
            This function converts the hashable sorted tuple of key-value pairs back into a standard dictionary.

        Warnings:
            Caching is only applied if `cache_mode` is enabled. Ensure that the `data` parameter is hashable for 
            caching to work correctly.
        """

        if hashable_data is None:
            return None
        return dict(hashable_data)

class AsyncHelpers:
    """A class that provides asynchronous helper methods.
    
    This class contains asynchronous static methods that assist in data conversion and validation
    for interacting with the FRED API. It includes methods for converting FRED
    observation dictionaries to various DataFrame formats (Pandas, Polars, Dask,
    GeoPandas, Dask GeoPandas, Polars GeoDataFrame) as well as methods for validating
    and converting parameters used in FRED API requests.

    Notes:
        This class is designed to provide asynchronous versions of helper methods for the fedfred package,
        enabling non-blocking data processing and validation. Some methods require additional libraries 
        (Polars, Dask, Dask GeoPandas, Polars GeoDataFrame). Ensure these libraries are installed to use the corresponding methods.

    Examples:
        >>> import asyncio
        >>> import fedfred as fd
        >>> data = {
        >>>     "observations": [
        >>>         {"date": "2020-01-01", "value": "100"},
        >>>         {"date": "2020-02-01", "value": "200"},
        >>>         {"date": "2020-03-01", "value": "300"},
        >>>     ]
        >>> }
        >>> async def main():
        >>>     df = await fd.AsyncHelpers.to_pd_df(data)
        >>>     print(df)
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
                    value
        date
        2020-01-01  100.0
        2020-02-01  200.0
        2020-03-01  300.0

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.html
    """
    # Asynchronous methods
    @staticmethod
    async def to_pd_df(data: Dict[str, list]) -> pd.DataFrame:
        """Helper method to convert a FRED observation dictionary to a Pandas DataFrame asynchronously.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            pandas.DataFrame: Converted Pandas DataFrame.

        Raises:
            ValueError: If 'observations' key is not in the data.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> data = {
            >>>     "observations": [
            >>>         {"date": "2020-01-01", "value": "100"},
            >>>         {"date": "2020-02-01", "value": "200"},
            >>>         {"date": "2020-03-01", "value": "300"},
            >>>     ]
            >>> }
            >>> async def main():
            >>>     df = await fd.AsyncHelpers.to_pd_df(data)
            >>>     print(df)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
                        value
            date
            2020-01-01  100.0
            2020-02-01  200.0
            2020-03-01  300.0

        Notes:
            The 'date' column is converted to a DatetimeIndex and set as the DataFrame index and the 'value' column is converted to numeric, with non-numeric values coerced to NaN.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.to_pd_df.html

        See Also:
            - :meth:`AsyncHelpers.to_pl_df`: Asynchronously convert a FRED observation dictionary to a Polars DataFrame.
            - :meth:`AsyncHelpers.to_dd_df`: Asynchronously convert a FRED observation dictionary to a Dask DataFrame.    
        """

        return await asyncio.to_thread(Helpers.to_pd_df, data)

    @staticmethod
    async def to_pl_df(data: Dict[str, list]) -> 'pl.DataFrame':
        """Helper method to convert a FRED observation dictionary to a Polars DataFrame asynchronously.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            polars.DataFrame: Converted Polars DataFrame.

        Raises:
            ImportError: If Polars is not installed.
            ValueError: If 'observations' key is not in the data.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> data = {
            >>>     "observations": [
            >>>         {"date": "2020-01-01", "value": "100"},
            >>>         {"date": "2020-02-01", "value": "200"},
            >>>         {"date": "2020-03-01", "value": "300"},
            >>>     ]
            >>> }
            >>> async def main():
            >>>     df = await fd.AsyncHelpers.to_pl_df(data)
            >>>     print(df)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            shape: (3, 2)
            ┌────────────┬───────┐
            │ date       ┆ value │
            │ ---        ┆ ---   │
            │ date       ┆ f64   │
            ╞════════════╪═══════╡
            │ 2020-01-01 ┆ 100.0 │
            │ 2020-02-01 ┆ 200.0 │
            │ 2020-03-01 ┆ 300.0 │
            └────────────┴───────┘

        Notes:
            The 'value' column is converted to Float64, with 'NA' values replaced with None.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.to_pl_df.html

        See Also:
            - :meth:`AsyncHelpers.to_pd_df`: Asynchronously convert a FRED observation dictionary to a Pandas DataFrame.
            - :meth:`AsyncHelpers.to_dd_df`: Asynchronously convert a FRED observation dictionary to a Dask DataFrame.    
        """

        return await asyncio.to_thread(Helpers.to_pl_df, data)

    @staticmethod
    async def to_dd_df(data: Dict[str, list]) -> 'dd.DataFrame':
        """Helper method to convert a FRED observation dictionary to a Dask DataFrame asynchronously.

        Args:
            data (Dict[str, list]): FRED observation dictionary.

        Returns:
            dask.dataframe.DataFrame: Converted Dask DataFrame.

        Raises:
            ImportError: If Dask is not installed.
            ValueError: If 'observations' key is not in the data.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> data = {
            >>>     "observations": [
            >>>         {"date": "2020-01-01", "value": "100"},
            >>>         {"date": "2020-02-01", "value": "200
            >>>         {"date": "2020-03-01", "value": "300"},
            >>>     ]
            >>> }
            >>> async def main():
            >>>     df = await fd.AsyncHelpers.to_dd_df(data)
            >>>     print(df.compute())
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
                        value
            date
            2020-01-01  100.0
            2020-02-01  200.0
            2020-03-01  300.0

        Notes:
            This method first converts the data to a Pandas DataFrame and then to a Dask DataFrame with a single partition.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.to_dd_df.html

        See Also:
            - :meth:`AsyncHelpers.to_pd_df`: Asynchronously convert a FRED observation dictionary to a Pandas DataFrame.
            - :meth:`AsyncHelpers.to_pl_df`: Asynchronously convert a FRED observation dictionary to a Polars DataFrame.
        """

        try:
            import dask.dataframe as dd
        except ImportError as e:
            raise ImportError(
                f"{e}: Dask is not installed. Install it with `pip install dask` to use this method."
            ) from e
        df = await AsyncHelpers.to_pd_df(data)
        return await asyncio.to_thread(dd.from_pandas, df, npartitions=1)

    @staticmethod
    async def to_gpd_gdf(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> gpd.GeoDataFrame:
        """Helper method to convert a FRED observation dictionary to a GeoPandas GeoDataFrame asynchronously.

        Args:
            shapefile (geopandas.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            geopandas.GeoDataFrame: Converted GeoPandas GeoDataFrame.

        Raises:
            ValueError: If no data section is found in the response.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> import geopandas as gpd
            >>> shapefile = gpd.read_file("path_to_shapefile.shp")
            >>> meta_data = {
            >>>     "data": {
            >>>         "observations": [
            >>>             {"region": "Region1", "value": 100, "series_id": "S1"},
            >>>             {"region": "Region2", "value": 200, "series_id": "S2"},
            >>>         ]
            >>>     }
            >>> }
            >>> async def main():
            >>>     gdf = await fd.AsyncHelpers.to_gpd_gdf(shapefile, meta_data)
            >>>     print(gdf)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
                name  value series_id                     geometry
            0  Region1  100.0        S1  POLYGON ((...))
            1  Region2  200.0        S2  POLYGON ((...))

        Notes:
            This method adds 'value' and 'series_id' columns to the GeoDataFrame based on the provided metadata.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.to_gpd_gdf.html

        See Also:
            - :meth:`AsyncHelpers.to_dd_gpd_gdf`: Asynchronously convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame.
            - :meth:`AsyncHelpers.to_pl_st_gdf`: Asynchronously convert a FRED observation dictionary to a Polars GeoDataFrame.
        """

        return await asyncio.to_thread(Helpers.to_gpd_gdf, shapefile, meta_data)

    @staticmethod
    async def to_dd_gpd_gdf(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'dd_gpd.GeoDataFrame':
        """Helper method to convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame asynchronously.

        Args:
            shapefile (geopandas.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            dask_geopandas.GeoDataFrame: Converted Dask GeoPandas GeoDataFrame

        Raises:
            ImportError: If Dask GeoPandas is not installed.
            ValueError: If no data section is found in the response.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> import geopandas as gpd
            >>> shapefile = gpd.read_file("path_to_shapefile.shp")
            >>> meta_data = {
            >>>     "data": {
            >>>         "observations": [
            >>>             {"region": "Region1", "value": 100, "series_id": "S1"},
            >>>             {"region": "Region2", "value": 200, "series_id": "S2"},
            >>>         ]
            >>>     }
            >>> }
            >>> async def main():
            >>>     dd_gdf = await fd.AsyncHelpers.to_dd_gpd_gdf(shapefile, meta_data)
            >>>     print(dd_gdf.compute())
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
                name  value series_id                     geometry
            0  Region1  100.0        S1  POLYGON ((...))
            1  Region2  200.0        S2  POLYGON ((...))

        Notes:
            This method first converts the data to a GeoPandas GeoDataFrame and then to a Dask GeoPandas GeoDataFrame with a single partition.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.to_dd_gpd_gdf.html

        See Also:
            - :meth:`AsyncHelpers.to_gpd_gdf`: Asynchronously convert a FRED observation dictionary to a GeoPandas GeoDataFrame.
            - :meth:`AsyncHelpers.to_pl_st_gdf`: Asynchronously convert a FRED observation dictionary to a Polars GeoDataFrame.
        """

        try:
            import dask_geopandas as dd_gpd
        except ImportError as e:
            raise ImportError(
                f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method."
            ) from e
        gdf = await AsyncHelpers.to_gpd_gdf(shapefile, meta_data)
        return await asyncio.to_thread(dd_gpd.from_geopandas, gdf, npartitions=1)

    @staticmethod
    async def to_pl_st_gdf(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'st.GeoDataFrame':
        """Helper method to convert a FRED observation dictionary to a Polars GeoDataFrame asynchronously.

        Args:
            shapefile (geopandas.GeoDataFrame): FRED shapefile GeoDataFrame.
            meta_data (Dict): FRED response metadata dictionary.

        Returns:
            polars_st.GeoDataFrame: Converted Polars GeoDataFrame.

        Raises:
            ImportError: If Polars with geospatial support is not installed.
            ValueError: If no data section is found in the response.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> import geopandas as gpd
            >>> shapefile = gpd.read_file("path_to_shapefile.shp")
            >>> meta_data = {
            >>>     "data": {
            >>>         "observations": [
            >>>             {"region": "Region1", "value": 100, "series_id": "S1"},
            >>>             {"region": "Region2", "value": 200, "series_id": "S2"},
            >>>         ]
            >>>     }
            >>> }
            >>> async def main():
            >>>     st_gdf = await fd.AsyncHelpers.to_pl_st_gdf(shapefile, meta_data)
            >>>     print(st_gdf)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            shape: (2, 3)
            ┌─────────┬───────┬───────────┬────────────────────────┐
            │ name    ┆ value ┆ series_id ┆ geometry               │
            │ ---     ┆ ---   ┆ ---       ┆ ---                    │
            │ str     ┆ f64   ┆ str       ┆ geo                    │
            ╞═════════╪═══════╪═══════════╪════════════════════════╡
            │ Region1 ┆ 100.0 ┆ S1        ┆ POLYGON ((...))        │
            │ Region2 ┆ 200.0 ┆ S2        ┆ POLYGON ((...))        │
            └─────────┴───────┴───────────┴────────────────────────┘

        Notes:
            This method first converts the data to a GeoPandas GeoDataFrame and then to a Polars GeoDataFrame.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.to_pl_st_gdf.html

        See Also:
            - :meth:`AsyncHelpers.to_gpd_gdf`: Asynchronously convert a FRED observation dictionary to a GeoPandas GeoDataFrame.
            - :meth:`AsyncHelpers.to_dd_gpd_gdf`: Asynchronously convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame.
        """

        try:
            import polars_st as st
        except ImportError as e:
            raise ImportError(
                f"{e}: Polars with geospatial support is not installed. Install it with `pip install polars-st` to use this method."
            ) from e
        gdf = await AsyncHelpers.to_gpd_gdf(shapefile, meta_data)
        return await asyncio.to_thread(st.from_geopandas, gdf)

    @staticmethod
    async def extract_region_type(response: Dict) -> str:
        """Helper method to extract the region type from a GeoFred response dictionary asynchronously.

        Args:
            response (Dict): FRED GeoFred response dictionary.

        Returns:
            str: Extracted region type.

        Raises:
            ValueError: If no meta data or region type is found in the response.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> response = {
            >>>     "meta": {
            >>>         "region_type": "state"
            >>>     },
            >>>     "data": {
            >>>         "observations": []
            >>>     }
            >>> }
            >>> async def main():
            >>>     region_type = await fd.AsyncHelpers.extract_region_type(response)
            >>>     print(region_type)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            state

        Notes:
            This method looks for the 'region_type' key in the 'meta' section of the response.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.extract_region_type.html

        See Also:
            - :meth:`AsyncHelpers.to_gpd_gdf`: Asynchronously convert a FRED observation dictionary to a GeoPandas GeoDataFrame.
            - :meth:`AsyncHelpers.to_dd_gpd_gdf`: Asynchronously convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame.
            - :meth:`AsyncHelpers.to_pl_st_gdf`: Asynchronously convert a FRED observation dictionary to a Polars GeoDataFrame.
        """

        return await asyncio.to_thread(Helpers.extract_region_type, response)

    @staticmethod
    async def liststring_conversion(param: list[str]) -> str:
        """Helper method to convert a list of strings to a semicolon-separated string asynchronously.

        Args:
            param (list[str]): List of strings to convert.

        Returns:
            str: Semicolon-separated string.

        Raises:
            ValueError: If param is not a list of strings.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> param = ["GDP", "CPI", "UNRATE"]
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.liststring_conversion(param)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            GDP;CPI;UNRATE

        Notes:
            This method joins the list elements with a semicolon (';') separator.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.liststring_conversion.html

        See Also:
            - :meth:`AsyncHelpers.liststring_validation`: Validate list-string formatted parameters asynchronously.
        """

        return await asyncio.to_thread(Helpers.liststring_conversion, param)

    @staticmethod
    async def vintage_dates_type_conversion(param: Union[str, datetime, list[Optional[Union[str, datetime]]]]) -> str:
        """Helper method to convert a vintage_dates parameter to a string asynchronously.

        Args:
            param (str | datetime | list[Optional[str | datetime]]]): vintage_dates parameter to convert.

        Returns:
            str: Converted vintage_dates string.

        Raises:
            ValueError: If param is not a string, datetime object, or list of strings/datetime objects.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> param1 = "2020-01-01"
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.vintage_dates_type_conversion(param1)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            2020-01-01

        Notes:
            This method handles single strings, datetime objects, and lists of strings/datetime objects, converting them to a comma-separated string.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.vintage_dates_type_conversion.html

        See Also:
            - :meth:`AsyncHelpers.datetime_conversion`: Convert a datetime object to a string in YYYY-MM-DD format asynchronously.
            - :meth:`AsyncHelpers.vintage_dates_validation`: Validate vintage_dates parameters asynchronously.
        """

        return await asyncio.to_thread(Helpers.vintage_dates_type_conversion, param)

    @staticmethod
    async def datetime_conversion(param: datetime) -> str:
        """Helper method to convert a datetime object to a string in YYYY-MM-DD format asynchronously.

        Args:
            param (datetime): Datetime object to convert.

        Returns:
            str: Formatted date string.

        Raises:
            ValueError: If param is not a datetime object.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> from datetime import datetime
            >>> param = datetime(2020, 1, 1)
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.datetime_conversion(param)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            2020-01-01

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.datetime_conversion.html

        See Also:
            - :meth:`AsyncHelpers.datetime_hh_mm_conversion`: Convert a datetime object to a string in HH:MM format asynchronously.
            - :meth:`AsyncHelpers.datestring_validation`: Validate date-string formatted parameters asynchronously.
        """

        return await asyncio.to_thread(Helpers.datetime_conversion, param)

    @staticmethod
    async def datetime_hh_mm_conversion(param: datetime) -> str:
        """Helper method to convert a datetime object to a string in HH:MM format asynchronously.

        Args:
            param (datetime): Datetime object to convert.

        Returns:
            str: Formatted time string.

        Raises:
            ValueError: If param is not a datetime object.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> from datetime import datetime
            >>> param = datetime(2020, 1, 1, 14, 30)
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.datetime_hh_mm_conversion(param)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.datetime_hh_mm_conversion.html

        See Also:
            - :meth:`AsyncHelpers.datetime_conversion`: Convert a datetime object to a string in YYYY-MM-DD format asynchronously.
            - :meth:`AsyncHelpers.datetime_hh_mm_conversion`: Validate hh:mm formatted parameters asynchronously.
        """

        return await asyncio.to_thread(Helpers.datetime_hh_mm_conversion, param)

    @staticmethod
    async def parameter_validation(params: Dict[str, Optional[Union[str, int]]]) -> Optional[ValueError]:
        """Helper method to validate parameters prior to making a get request asynchronously.

        Args:
            params (Dict[str, Optional[str | int]]): Dictionary of parameters to validate.

        Returns:
            None

        Raises:
            ValueError: If any parameter is invalid.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> params = {
            >>>     "category_id": 125,
            >>>     "realtime_start": "2020-01-01",
            >>>     "realtime_end": "2020-12-31",
            >>>     "limit": 100,
            >>>     "offset": 0,
            >>>     "sort_order": "asc",
            >>>     "order_by": "series_id",
            >>>     "filter_variable": "frequency",
            >>>     "filter_value": "m",
            >>>     "tag_names": "GDP;CPI",
            >>>     "exclude_tag_names": "UNRATE",
            >>>     "tag_group_id": 123,
            >>>     "search_text": "economic",
            >>>     "file_type": "json",
            >>>     "api_key": "your_api_key",
            >>>     "include_releases_dates_with_no_data": True,
            >>>     "release_id": 10,
            >>>     "series_id": "GDP",
            >>>     "frequency": "m",
            >>>     "units": "lin",
            >>>     "aggregation_method": "avg",
            >>>     "output_type": 1
            >>> }
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.parameter_validation(params)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            None

        Notes:
            This method checks each parameter for correct type and value, raising a ValueError if any parameter is invalid.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.parameter_validation.html

        See Also:
            - :meth:`AsyncHelpers.datestring_validation`: Validate date-string formatted parameters asynchronously.
            - :meth:`AsyncHelpers.liststring_validation`: Validate list-string formatted parameters asynchronously.
            - :meth:`AsyncHelpers.vintage_dates_validation`: Validate vintage_dates parameters asynchronously.
            - :meth:`AsyncHelpers.hh_mm_datestring_validation`: Validate hh:mm formatted parameters asynchronously.
        """

        for k, v in params.items():
            if k in PARAMETERS_MAP:
                validator = PARAMETERS_MAP[k]
                assert isinstance(validator, dict)
                if 'type_condition' in validator.keys():
                    type_func = validator['type_condition']
                    assert callable(type_func)
                    try:
                        type_func(v)
                    except ValueError as e:
                        raise ValueError(f"Parameter '{k}' failed type validation: {e}: {validator['error_message']}") from e
                if 'async_value_condition' in validator.keys():
                    value_func = validator['async_value_condition']
                    assert callable(value_func)
                    try:
                        await value_func(v)
                    except ValueError as e:
                        raise ValueError(f"Parameter '{k}' failed value validation: {e}: {validator['error_message']}") from e
                if 'complex_condition' in validator.keys():
                    complex_func = validator['complex_condition']
                    assert callable(complex_func)
                    try:
                        complex_func(v, params)
                    except ValueError as e:
                        raise ValueError(f"Parameter '{k}' failed complex validation: {e}: {validator['error_message']}") from e
        return None

    @staticmethod
    async def geo_parameter_validation(params: Dict[str, Optional[Union[str, int]]]) -> Optional[ValueError]:
        """Helper method to validate parameters prior to making a get request.

        Args:
            params (Dict[str, Optional[str | int]]): Dictionary of parameters to validate

        Returns:
            None

        Raises:
            ValueError: If any parameter is invalid.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> params = {
            >>>     "api_key": "your_api_key",
            >>>     "file_type": "json",
            >>>     "shape": "state",
            >>>     "series_id": "GDP",
            >>>     "date": "2020-01-01",
            >>>     "start_date": "2020-01-01",
            >>>     "series_group": "group1",
            >>>     "region_type": "state",
            >>>     "aggregation_method": "avg",
            >>>     "units": "lin",
            >>>     "season": "SA",
            >>>     "transformation": "chg"
            >>> }
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.geo_parameter_validation(params)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            None

        Notes:
            This method checks each parameter for correct type and value, raising a ValueError if any parameter is invalid.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.geo_parameter_validation.html

        See Also:
            - :meth:`AsyncHelpers.datestring_validation`: Validate date-string formatted parameters asynchronously.
            - :meth:`AsyncHelpers.liststring_validation`: Validate list-string formatted parameters asynchronously.
            - :meth:`AsyncHelpers.vintage_dates_validation`: Validate vintage_dates parameters asynchronously.
            - :meth:`AsyncHelpers.hh_mm_datestring_validation`: Validate hh:mm formatted parameters asynchronously.
        """

        for k, v in params.items():
            if k in GEO_PARAMETERS_MAP:
                validator = GEO_PARAMETERS_MAP[k]
                assert isinstance(validator, dict)
                if 'type_condition' in validator.keys():
                    type_func = validator['type_condition']
                    assert callable(type_func)
                    try:
                        type_func(v)
                    except ValueError as e:
                        raise ValueError(f"Parameter '{k}' failed type validation: {e}: {validator['error_message']}") from e
                if 'async_value_condition' in validator.keys():
                    value_func = validator['async_value_condition']
                    assert callable(value_func)
                    try:
                        await value_func(v)
                    except ValueError as e:
                        raise ValueError(f"Parameter '{k}' failed value validation: {e}: {validator['error_message']}") from e
                if 'complex_condition' in validator.keys():
                    complex_func = validator['complex_condition']
                    assert callable(complex_func)
                    try:
                        complex_func(v, params)
                    except ValueError as e:
                        raise ValueError(f"Parameter '{k}' failed complex validation: {e}: {validator['error_message']}") from e
        return None

    @staticmethod
    async def fraser_parameter_validation(params: Dict[str, Optional[Union[str, int]]]) -> Optional[ValueError]:
        """Helper method to validate parameters for GeoFred requests asynchronously.

        Args:
            params (Dict[str, Optional[str | int]]): Dictionary of parameters to validate.

        Raises:
            ValueError: If any parameter is invalid.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> params = {
            >>>     "limit": 100,
            >>>     "page": 1,
            >>>     "role": "creator",
            >>> }
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.fraser_parameter_validation(params)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            None
        """

    @staticmethod
    async def pd_frequency_conversion(frequency: str) -> str:
        """Asynchronously convert FRED native frequency strings to pandas compatible ones.

        Args:
            frequency (str): Input frequency string.

        Returns:
            str: Coerced frequency string compatible with pandas.

        Raises:
            None

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> frequency = "WEF"
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.pd_frequency_conversion(frequency)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            W-FRI

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.pd_frequency_conversion.html

        See Also:
            - :meth:`AsyncHelpers.pd_frequency_conversion`: Convert FRED native frequency strings to pandas compatible ones asynchronously.
        """

        return await asyncio.to_thread(Helpers.pd_frequency_conversion, frequency)

    @staticmethod
    async def to_pd_series(data: Union[pd.Series, pd.DataFrame], name: str) -> pd.Series:
        """Asynchronously accepts a Series or a DataFrame with 'date' and 'value' columns (fedfred style) and returns a float Series with DatetimeIndex and the given name.

        Args:
            data (pandas.Series | pandas.DataFrame): Input data to be converted.
            name (str): Name to assign to the resulting Series.

        Returns:
            pandas.Series: A float Series with DatetimeIndex and the given `name`.

        Raises:
            TypeError: If the input is neither a pandas.Series nor a pandas.DataFrame.

        Examples:
            >>> import asyncio
            >>> import pandas as pd
            >>> import fedfred as fd
            >>> data = pd.DataFrame({
            >>>     "date": ["2020-01-01", "2020-02-01"],
            >>>     "value": [100, 200]
            >>> })
            >>> async def main():
            >>>     series = await fd.AsyncHelpers.to_pd_series(data, name="My Series")
            >>>     print(series)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            2020-01-01    100.0
            2020-02-01    200.0
            Name: My Series, dtype: float64

        Notes:
            This method handles both Series and DataFrame inputs, ensuring the output is a properly formatted pandas Series.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.to_pd_series.html

        See Also:
            - :meth:`AsyncHelpers.pd_frequency_conversion`: Asynchronously convert FRED native frequency strings to pandas compatible ones.
        """

        return await asyncio.to_thread(Helpers.to_pd_series, data, name)

    @staticmethod
    async def to_pl_series(self, data: Union[pl.Series, pl.DataFrame], name:str) -> pl.Series: # Add this helpers logic before release
        """Asynchronously accepts a Polars Series or a DataFrame with 'date' and 'value' columns and returns a float Series with DatetimeIndex and the given name.
        
        Args:
            data (polars.Series | polars.DataFrame): Input data to be converted.
            name (str): Name to assign to the resulting Series.

        Returns:
            polars.Series: A float Series with DatetimeIndex and the given `name`.

        Raises:
            TypeError: If the input is neither a polars.Series nor a polars.DataFrame

        Examples:

        Notes:

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_pl_series.html
        
        See Also:
            - :meth:`AsyncHelpers.to_pd_series`: Convert a Series or DataFrame to a pandas Series with DatetimeIndex.
        """

        return None

    @staticmethod
    async def to_hashable(data: Optional[Dict[str, Optional[Union[str, int]]]]) -> Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]:
        """Asynchronous helper function to make the data dictionary hashable for caching.

        Args:
            data (Dict[str, Optional[str | int]], optional): The query parameters for the request.

        Returns:
            Optional[Tuple[Tuple[str, Optional[str | int]], ...]]: A hashable representation of the data dictionary.

        Notes:
            This function converts the data dictionary into a sorted tuple of key-value pairs, making it suitable 
            for use as a cache key.

        Warnings:
            Caching is only applied if `cache_mode` is enabled. Ensure that the `data` parameter is hashable for 
            caching to work correctly.
        """

        return await asyncio.to_thread(Helpers.to_hashable, data)

    @staticmethod
    async def to_dict(hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]) -> Optional[Dict[str, Optional[Union[str, int]]]]:
        """Asynchronous helper function to convert hashable data back to a dictionary.
        
        Args:
            hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]]): The hashable representation of the data.

        Returns:
            Optional[Dict[str, Optional[str | int]]]: The original data dictionary.

        Notes:
            This function converts the hashable sorted tuple of key-value pairs back into a standard dictionary.

        Warnings:
            Caching is only applied if `cache_mode` is enabled. Ensure that the `data` parameter is hashable for 
            caching to work correctly.
        """

        return await asyncio.to_thread(Helpers.to_dict, hashable_data)
