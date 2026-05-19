# filepath: /src/fedfred/_core/_converters.py
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
"""fedfred._core._converters

This module provides internal converter functions for the fedfred core package.
"""

from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Dict, Optional, Union, Tuple, Any, Callable
from datetime import datetime, date, time
import pandas as pd
import geopandas as gpd
from ..exceptions import DataFrameConversionError, GeoDataFrameConversionError, OptionalDependencyError,  TypeConversionError

if TYPE_CHECKING:
    import dask.dataframe as dd # pragma: no cover
    import dask_geopandas as dd_gpd # pragma: no cover
    import polars as pl # pragma: no cover
    import polars_st as st # pragma: no cover

__all__ = [
    # Typing Aliases
    "ParameterConverter",
    # DataFrame Converters
    "_pandas_dataframe_converter", "_pandas_dataframe_converter_async",
    "_polars_dataframe_converter", "_polars_dataframe_converter_async",
    "_dask_dataframe_converter", "_dask_dataframe_converter_async",
    "_geopandas_geodataframe_converter", "_geopandas_geodataframe_converter_async",
    "_dask_geopandas_geodataframe_converter", "_dask_geopandas_geodataframe_converter_async",
    "_polars_geodataframe_converter", "_polars_geodataframe_converter_async",
    # DataFrame Converter Maps
    "DATAFRAME_CONVERTER_MAP", "GEODATAFRAME_CONVERTER_MAP",
    "ASYNC_DATAFRAME_CONVERTER_MAP", "ASYNC_GEODATAFRAME_CONVERTER_MAP",
    # Scalar Converters
    "_identity_converter", "_date_parameter_converter", "_time_parameter_converter", 
    "_semicolon_list_converter", "_comma_date_list_converter",
    # Cache Key Converters
    "_hashable_type_converter", "_hashable_type_converter_async",
    "_dict_type_converter", "_dict_type_converter_async",
]

# Typing Aliases
ParameterConverter = Callable[[str, Any], Any]
"""Typing alias for parameter converter functions. These functions take a parameter name and a value, and return a converted value suitable for API requests or caching."""

# DataFrame Converters
def _pandas_dataframe_converter(data: Dict[str, list]) -> pd.DataFrame:
    """Internal converter function to convert a FRED observation dictionary to a Pandas DataFrame.

    Args:
        data (Dict[str, list]): FRED observation dictionary.

    Returns:
        pandas.DataFrame: Converted Pandas DataFrame.

    Raises:
        DataFrameConversionError: If 'observations' key is not in the data or if conversion fails.

    Examples:
        >>> # Internal use
        >>> from ._core import _pandas_dataframe_converter
        >>> response = {
        >>>     "observations": [
        >>>         {"date": "2020-01-01", "value": "100"},
        >>>         {"date": "2020-02-01", "value": "200"},
        >>>         {"date": "2020-03-01", "value": "300"},
        >>>     ]
        >>> }
        >>> df = _pandas_dataframe_converter(response)
        >>> # Test output dataframe
        >>> print(df)
                    value
        date
        2020-01-01  100.0
        2020-02-01  200.0
        2020-03-01  300.0

    Notes:
        The 'date' column is converted to a DatetimeIndex and set as the DataFrame index and the 'value' column is converted to 
        numeric, with non-numeric values coerced to NaN.
    """

    if 'observations' not in data:
        raise DataFrameConversionError(
            message="DataFrame conversion failed: 'observations' key not found in data",
            backend='pandas',
            missing_fields=('observations',),
            details="Data must contain 'observations' key"
        )

    df = pd.DataFrame(data['observations'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df['value'] = pd.to_numeric(df['value'], errors = 'coerce')
    return df

def _polars_dataframe_converter(data: Dict[str, list]) -> 'pl.DataFrame':
    """Internal converter function to convert a FRED observation dictionary to a Polars DataFrame.

    Args:
        data (Dict[str, list]): FRED observation dictionary.

    Returns:
        polars.DataFrame: Converted Polars DataFrame.

    Raises:
        OptionalDependencyError: If Polars is not installed.
        DataFrameConversionError: If 'observations' key is not in the data.

    Examples:
        >>> # Internal use
        >>> from ._core import _polars_dataframe_converter
        >>> response = {
        >>>     "observations": [
        >>>         {"date": "2020-01-01", "value": "100"},
        >>>         {"date": "2020-02-01", "value": "200"},
        >>>         {"date": "2020-03-01", "value": "300"},
        >>>     ]
        >>> }
        >>> df = _polars_dataframe_converter(response)
        >>> # Test output dataframe
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
    """

    try:
        import polars as pl
    except ImportError as e:
        raise OptionalDependencyError(
            message=f"{e}: Polars is not installed. Install it with `pip install polars` to use this method.",
            package="polars",
            feature="Helpers.to_pl_df",
            install_hint="pip install polars",
        ) from e

    if 'observations' not in data:
        raise DataFrameConversionError(
            message="DataFrame conversion failed: 'observations' key not found in data",
            backend='polars',
            missing_fields=('observations',),
            details="Data must contain 'observations' key"
        )

    df = pl.DataFrame(data['observations'])
    df = df.with_columns(
        pl.when(pl.col('value') == 'NA')
        .then(None)
        .otherwise(pl.col('value').cast(pl.Float64))
        .alias('value')
    )
    return df

def _dask_dataframe_converter(data: Dict[str, list]) -> 'dd.DataFrame':
    """Internal converter function to convert a FRED observation dictionary to a Dask DataFrame.

    Args:
        data (Dict[str, list]): FRED observation dictionary.

    Returns:
        dask.dataframe.DataFrame: Converted Dask DataFrame.

    Raises:
        OptionalDependencyError: If Dask is not installed.
        DataFrameConversionError: If 'observations' key is not in the data.

    Examples:
        >>> # Internal use
        >>> from ._core import _dask_dataframe_converter
        >>> response = {
        >>>     "observations": [
        >>>         {"date": "2020-01-01", "value": "100"},
        >>>         {"date": "2020-02-01", "value": "200"},
        >>>         {"date": "2020-03-01", "value": "300"},
        >>>     ]
        >>> }
        >>> df = _dask_dataframe_converter(response)
        >>> # Test output dataframe
        >>> print(df.compute())
                    value
        date
        2020-01-01  100.0
        2020-02-01  200.0
        2020-03-01  300.0

    Notes:
        This method first converts the data to a Pandas DataFrame and then to a Dask DataFrame with a single partition.
    """

    try:
        import dask.dataframe as dd
    except ImportError as e:
        raise OptionalDependencyError(
            message=f"{e}: Dask is not installed. Install it with `pip install dask` to use this method.",
            package="dask",
            feature="Helpers.to_dd_df",
            install_hint="pip install dask",
        ) from e

    df = _pandas_dataframe_converter(data)
    return dd.from_pandas(df, npartitions=1)

def _geopandas_geodataframe_converter(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> gpd.GeoDataFrame:
    """Internal converter function to convert a GeoFRED observation dictionary to a GeoPandas GeoDataFrame.

    Args:
        shapefile (geopandas.GeoDataFrame): GeoFRED shapefile GeoDataFrame.
        meta_data (Dict): GeoFRED response metadata dictionary.

    Returns:
        geopandas.GeoDataFrame: Converted GeoPandas GeoDataFrame.

    Raises:
        GeoDataFrameConversionError: If no data section is found in the response.

    Examples:
        >>> # Internal use
        >>> from ._core import _geopandas_geodataframe_converter
        >>> shapefile = {
        ...     "type": "FeatureCollection",
        ...     "features": [
        ...         {
        ...             "type": "Feature",
        ...             "id": "US.MA",
        ...             "properties": {"name": "Massachusetts"},
        ...             "geometry": {
        ...                 "type": "MultiPolygon",
        ...                 "coordinates": [[[[9727, 7650], ...]]]
        ...             }
        ...         }
        ...     ]
        ... }
        >>> meta_data = {
        ...     "meta": {
        ...         "title": "2012 Per Capita Personal Income by State (Dollars)",
        ...         "region": "state",
        ...         "seasonality": "Not Seasonally Adjusted",
        ...         "units": "Dollars",
        ...         "frequency": "Annual",
        ...         "date": "2012-01-01",
        ...         "data":{"2013-01-01":[{
        ...             "region": "Massachusetts",
        ...             "code": "25",
        ...             "value": "56713",
        ...             "series_id": "MAPCPI"
        ...             },]
        ...         }
        ...     }
        ... }
        >>> gdf = _geopandas_geodataframe_converter(shapefile, meta_data)
        >>> # Test output dataframe
        >>> print(gdf)
            name  value series_id                     geometry
        0  Region1  100.0        S1  POLYGON ((...))
        1  Region2  200.0        S2  POLYGON ((...))

    Notes:
        This method adds 'value' and 'series_id' columns to the GeoDataFrame based on the provided metadata.
    """

    shapefile.set_index('name', inplace=True)
    shapefile['value'] = None
    shapefile['series_id'] = None
    data_section = meta_data.get('data', {})

    if not data_section:
        raise GeoDataFrameConversionError(
            message="GeoDataFrame conversion failed: No data section found in metadata",
            backend='geopandas',
            missing_fields=('data',),
            details="Metadata must contain 'data' section with observations"
        )

    data_key = next(iter(data_section))
    items = data_section[data_key]

    for item in items:
        if item['region'] in shapefile.index:
            shapefile.loc[item['region'], 'value'] = item['value']
            shapefile.loc[item['region'], 'series_id'] = item['series_id']
    return shapefile

def _dask_geopandas_geodataframe_converter(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'dd_gpd.GeoDataFrame':
    """Internal converter function to convert a GeoFRED observation dictionary to a Dask GeoPandas GeoDataFrame.

    Args:
        shapefile (geopandas.GeoDataFrame): GeoFRED shapefile GeoDataFrame.
        meta_data (Dict): GeoFRED response metadata dictionary.

    Returns:
        dask_geopandas.GeoDataFrame: Converted Dask GeoPandas GeoDataFrame.

    Raises:
        OptionalDependencyError: If Dask GeoPandas is not installed.
        GeoDataFrameConverterError: If no data section is found in the response.

    Examples:
        >>> # Internal use
        >>> from ._core import _dask_geopandas_geodataframe_converter
        >>> shapefile = {
        ...     "type": "FeatureCollection",
        ...     "features": [
        ...         {
        ...             "type": "Feature",
        ...             "id": "US.MA",
        ...             "properties": {"name": "Massachusetts"},
        ...             "geometry": {
        ...                 "type": "MultiPolygon",
        ...                 "coordinates": [[[[9727, 7650], ...]]]
        ...             }
        ...         }
        ...     ]
        ... }
        >>> meta_data = {
        ...     "meta": {
        ...         "title": "2012 Per Capita Personal Income by State (Dollars)",
        ...         "region": "state",
        ...         "seasonality": "Not Seasonally Adjusted",
        ...         "units": "Dollars",
        ...         "frequency": "Annual",
        ...         "date": "2012-01-01",
        ...         "data":{"2013-01-01":[{
        ...             "region": "Massachusetts",
        ...             "code": "25",
        ...             "value": "56713",
        ...             "series_id": "MAPCPI"
        ...             },]
        ...         }
        ...     }
        ... }
        >>> gdf = _dask_geopandas_geodataframe_converter(shapefile, meta_data)
        >>> # Test output dataframe
        >>> print(gdf.compute())
            name  value series_id                     geometry
        0  Region1  100.0        S1  POLYGON ((...))
        1  Region2  200.0        S2  POLYGON ((...))

    Notes:
        This method first converts the data to a GeoPandas GeoDataFrame and then to a Dask GeoPandas GeoDataFrame with a single partition.
    """

    try:
        import dask_geopandas as dd_gpd
    except ImportError as e:
        raise OptionalDependencyError(
            message=f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method.",
            package="dask-geopandas",
            feature="Helpers.to_dd_gpd_gdf",
            install_hint="pip install dask-geopandas"
        ) from e

    gdf = _geopandas_geodataframe_converter(shapefile, meta_data)
    return dd_gpd.from_geopandas(gdf, npartitions=1)

def _polars_geodataframe_converter(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'st.GeoDataFrame':
    """Internal converter function to convert a GeoFRED observation dictionary to a Polars GeoDataFrame.

    Args:
        shapefile (geopandas.GeoDataFrame): GeoFRED shapefile GeoDataFrame.
        meta_data (Dict): GeoFRED response metadata dictionary.

    Returns:
        polars_st.GeoDataFrame: Converted Polars GeoDataFrame.

    Raises:
        OptionalDependencyError: If Polars with geospatial support is not installed.
        GeoDataFrameConversionError: If no data section is found in the response.
        
    Examples:
        >>> from ._core import _polars_geodataframe_converter
        >>> shapefile = {
        ...     "type": "FeatureCollection",
        ...     "features": [
        ...         {
        ...             "type": "Feature",
        ...             "id": "US.MA",
        ...             "properties": {"name": "Massachusetts"},
        ...             "geometry": {
        ...                 "type": "MultiPolygon",
        ...                 "coordinates": [[[[9727, 7650], ...]]]
        ...             }
        ...         }
        ...     ]
        ... }
        >>> meta_data = {
        ...     "meta": {
        ...         "title": "2012 Per Capita Personal Income by State (Dollars)",
        ...         "region": "state",
        ...         "seasonality": "Not Seasonally Adjusted",
        ...         "units": "Dollars",
        ...         "frequency": "Annual",
        ...         "date": "2012-01-01",
        ...         "data":{"2013-01-01":[{
        ...             "region": "Massachusetts",
        ...             "code": "25",
        ...             "value": "56713",
        ...             "series_id": "MAPCPI"
        ...             },]
        ...         }
        ...     }
        ... }
        >>> gdf = _polars_geodataframe_converter(shapefile, meta_data)
        >>> # Test output dataframe
        >>> print(gdf)
        shape: (1, 3)
        ┌───────────────┬─────────┬───────────┬────────────────────────┐
        │ name          ┆ value   ┆ series_id ┆ geometry               │
        │ ---           ┆ ---     ┆ ---       ┆ ---                    │
        │ str           ┆ f64     ┆ str       ┆ geo                    │
        ╞═══════════════╪═════════╪═══════════╪════════════════════════╡
        │ Massachusetts ┆ 56713.0 ┆ MAPCPI    ┆ POLYGON ((...))        │
        └───────────────┴─────────┴───────────┴────────────────────────┘

    Notes:
        This method first converts the data to a GeoPandas GeoDataFrame and then to a Polars GeoDataFrame.
    """

    try:
        import polars_st as st
    except ImportError as e:
        raise OptionalDependencyError(
            message=f"{e}: Polars with geospatial support is not installed. Install it with `pip install polars-st` to use this method.",
            package="polars-st",
            feature="Helpers.to_pl_st_gdf",
            install_hint="pip install polars-st"
        ) from e

    gdf = _geopandas_geodataframe_converter(shapefile, meta_data)
    return st.from_geopandas(gdf)

async def _pandas_dataframe_converter_async(data: Dict[str, list]) -> pd.DataFrame:
    """Internal asynchronous converter function to convert a FRED observation dictionary to a Pandas DataFrame.

    Args:
        data (Dict[str, list]): FRED observation dictionary.

    Returns:
        pandas.DataFrame: Converted Pandas DataFrame.

    Raises:
        DataFrameConversionError: If 'observations' key is not in the data.

    Examples:
        >>> # Internal use
        >>> from ._core import _pandas_dataframe_converter_async
        >>> data = {
        >>>     "observations": [
        >>>         {"date": "2020-01-01", "value": "100"},
        >>>         {"date": "2020-02-01", "value": "200"},
        >>>         {"date": "2020-03-01", "value": "300"},
        >>>     ]
        >>> }
        >>> async def main():
        >>>     df = await _pandas_dataframe_converter_async(data)
        >>>     print(df)
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context. 
        >>> # For documentation purposes, the following pattern can be used to check the output dataframe:
        >>> import asyncio
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
                    value
        date
        2020-01-01  100.0
        2020-02-01  200.0
        2020-03-01  300.0

    Notes:
        The 'date' column is converted to a DatetimeIndex and set as the DataFrame index and the 'value' column is converted to numeric, with non-numeric values coerced to NaN. 
    """

    return await asyncio.to_thread(_pandas_dataframe_converter, data)

async def _polars_dataframe_converter_async(data: Dict[str, list]) -> 'pl.DataFrame':
    """Internal asynchronous converter function to convert a FRED observation dictionary to a Polars DataFrame.

    Args:
        data (Dict[str, list]): FRED observation dictionary.

    Returns:
        polars.DataFrame: Converted Polars DataFrame.

    Raises:
        OptionalDependencyError: If Polars is not installed.
        DataFrameConversionError: If 'observations' key is not in the data.

    Examples:
        >>> # Internal use
        >>> import fedfred as fd
        >>> data = {
        >>>     "observations": [
        >>>         {"date": "2020-01-01", "value": "100"},
        >>>         {"date": "2020-02-01", "value": "200"},
        >>>         {"date": "2020-03-01", "value": "300"},
        >>>     ]
        >>> }
        >>> async def main():
        >>>     df = await _polars_dataframe_converter_async(data)
        >>>     print(df)
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context. 
        >>> # For documentation purposes, the following pattern can be used to check the output dataframe:
        import asyncio
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
    """

    return await asyncio.to_thread(_polars_dataframe_converter, data)

async def _dask_dataframe_converter_async(data: Dict[str, list]) -> 'dd.DataFrame':
    """Internal asynchronous converter function to convert a FRED observation dictionary to a Dask DataFrame.

    Args:
        data (Dict[str, list]): FRED observation dictionary.

    Returns:
        dask.dataframe.DataFrame: Converted Dask DataFrame.

    Raises:
        OptionalDependencyError: If Dask is not installed.
        DataFrameConversionError: If 'observations' key is not in the data.

    Examples:
        >>> # Internal use
        >>> from ._core import _dask_dataframe_converter_async
        >>> data = {
        >>>     "observations": [
        >>>         {"date": "2020-01-01", "value": "100"},
        >>>         {"date": "2020-02-01", "value": "200
        >>>         {"date": "2020-03-01", "value": "300"},
        >>>     ]
        >>> }
        >>> async def main():
        >>>     df = await _dask_dataframe_converter_async(data)
        >>>     print(df.compute())
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context. 
        >>> # For documentation purposes, the following pattern can be used to check the output dataframe:
        >>> import asyncio
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
                    value
        date
        2020-01-01  100.0
        2020-02-01  200.0
        2020-03-01  300.0

    Notes:
        This method first converts the data to a Pandas DataFrame and then to a Dask DataFrame with a single partition.
    """

    try:
        import dask.dataframe as dd
    except ImportError as e:
        raise OptionalDependencyError(
            message=f"{e}: Dask is not installed. Install it with `pip install dask` to use this method.",
            package="dask",
            feature="_dask_dataframe_converter_async",
            install_hint="pip install dask"
        ) from e

    df = await _pandas_dataframe_converter_async(data)
    return await asyncio.to_thread(dd.from_pandas, df, npartitions=1)

async def _geopandas_geodataframe_converter_async(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> gpd.GeoDataFrame:
    """Internal asynchronous converter function to convert a GeoFRED observation dictionary to a GeoPandas GeoDataFrame.

    Args:
        shapefile (geopandas.GeoDataFrame): GeoFRED shapefile GeoDataFrame.
        meta_data (Dict): GeoFRED response metadata dictionary.

    Returns:
        geopandas.GeoDataFrame: Converted GeoPandas GeoDataFrame.

    Raises:
        GeoDataFrameConversionError: If no data section is found in the response.

    Examples:
        >>> # Internal use
        >>> from ._core import _geopandas_geodataframe_converter_async
        >>> shapefile = {
        ...     "type": "FeatureCollection",
        ...     "features": [
        ...         {
        ...             "type": "Feature",
        ...             "id": "US.MA",
        ...             "properties": {"name": "Massachusetts"},
        ...             "geometry": {
        ...                 "type": "MultiPolygon",
        ...                 "coordinates": [[[[9727, 7650], ...]]]
        ...             }
        ...         }
        ...     ]
        ... }
        >>> meta_data = {
        ...     "meta": {
        ...         "title": "2012 Per Capita Personal Income by State (Dollars)",
        ...         "region": "state",
        ...         "seasonality": "Not Seasonally Adjusted",
        ...         "units": "Dollars",
        ...         "frequency": "Annual",
        ...         "date": "2012-01-01",
        ...         "data":{"2013-01-01":[{
        ...             "region": "Massachusetts",
        ...             "code": "25",
        ...             "value": "56713",
        ...             "series_id": "MAPCPI"
        ...             },]
        ...         }
        ...     }
        ... }
        >>> async def main():
        >>>     gdf = await _geopandas_geodataframe_converter_async(shapefile, meta_data)
        >>>     print(gdf)
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context. 
        >>> # For documentation purposes, the following pattern can be used to check the output geodataframe:
        >>> import asyncio
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
            name  value series_id                     geometry
        0  Region1  100.0        S1  POLYGON ((...))
        1  Region2  200.0        S2  POLYGON ((...))

    Notes:
        This method adds 'value' and 'series_id' columns to the GeoDataFrame based on the provided metadata.
    """

    return await asyncio.to_thread(_geopandas_geodataframe_converter, shapefile, meta_data)

async def _dask_geopandas_geodataframe_converter_async(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'dd_gpd.GeoDataFrame':
    """Internal asynchronous converter function to convert a GeoFRED observation dictionary to a Dask GeoPandas GeoDataFrame.

    Args:
        shapefile (geopandas.GeoDataFrame): GeoFRED shapefile GeoDataFrame.
        meta_data (Dict): GeoFRED response metadata dictionary.

    Returns:
        dask_geopandas.GeoDataFrame: Converted Dask GeoPandas GeoDataFrame

    Raises:
        OptionalDependencyError: If Dask GeoPandas is not installed.
        GeoDataFrameConversionError: If no data section is found in the response.

    Examples:
        >>> # Internal use
        >>> from ._core import _dask_geopandas_geodataframe_converter_async
        >>> shapefile = {
        ...     "type": "FeatureCollection",
        ...     "features": [
        ...         {
        ...             "type": "Feature",
        ...             "id": "US.MA",
        ...             "properties": {"name": "Massachusetts"},
        ...             "geometry": {
        ...                 "type": "MultiPolygon",
        ...                 "coordinates": [[[[9727, 7650], ...]]]
        ...             }
        ...         }
        ...     ]
        ... }
        >>> meta_data = {
        ...     "meta": {
        ...         "title": "2012 Per Capita Personal Income by State (Dollars)",
        ...         "region": "state",
        ...         "seasonality": "Not Seasonally Adjusted",
        ...         "units": "Dollars",
        ...         "frequency": "Annual",
        ...         "date": "2012-01-01",
        ...         "data":{"2013-01-01":[{
        ...             "region": "Massachusetts",
        ...             "code": "25",
        ...             "value": "56713",
        ...             "series_id": "MAPCPI"
        ...             },]
        ...         }
        ...     }
        ... }
        >>> async def main():
        >>>     dd_gdf = await _dask_geopandas_geodataframe_converter_async(shapefile, meta_data)
        >>>     print(dd_gdf.compute())
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context. 
        >>> # For documentation purposes, the following pattern can be used to check the output geodataframe:
        >>> import asyncio
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
            name  value series_id                     geometry
        0  Region1  100.0        S1  POLYGON ((...))
        1  Region2  200.0        S2  POLYGON ((...))

    Notes:
        This method first converts the data to a GeoPandas GeoDataFrame and then to a Dask GeoPandas GeoDataFrame with a single partition.
    """

    try:
        import dask_geopandas as dd_gpd
    except ImportError as e:
        raise OptionalDependencyError(
            message=f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method.",
            package="dask-geopandas",
            feature="Helpers.to_dd_gpd_gdf",
            install_hint="pip install dask-geopandas"
        ) from e

    gdf = await _geopandas_geodataframe_converter_async(shapefile, meta_data)
    return await asyncio.to_thread(dd_gpd.from_geopandas, gdf, npartitions=1)

async def _polars_geodataframe_converter_async(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'st.GeoDataFrame':
    """Internal asynchronous converter function to convert a GeoFRED observation dictionary to a Polars GeoDataFrame asynchronously.

    Args:
        shapefile (geopandas.GeoDataFrame): GeoFRED shapefile GeoDataFrame.
        meta_data (Dict): GeoFRED response metadata dictionary.

    Returns:
        polars_st.GeoDataFrame: Converted Polars GeoDataFrame.

    Raises:
        OptionalDependencyError: If Polars with geospatial support is not installed.
        GeoDataFrameConversionError: If no data section is found in the response.

    Examples:
        >>> from ._core import _polars_geodataframe_converter_async
        >>> shapefile = {
        ...     "type": "FeatureCollection",
        ...     "features": [
        ...         {
        ...             "type": "Feature",
        ...             "id": "US.MA",
        ...             "properties": {"name": "Massachusetts"},
        ...             "geometry": {
        ...                 "type": "MultiPolygon",
        ...                 "coordinates": [[[[9727, 7650], ...]]]
        ...             }
        ...         }
        ...     ]
        ... }
        >>> meta_data = {
        ...     "meta": {
        ...         "title": "2012 Per Capita Personal Income by State (Dollars)",
        ...         "region": "state",
        ...         "seasonality": "Not Seasonally Adjusted",
        ...         "units": "Dollars",
        ...         "frequency": "Annual",
        ...         "date": "2012-01-01",
        ...         "data":{"2013-01-01":[{
        ...             "region": "Massachusetts",
        ...             "code": "25",
        ...             "value": "56713",
        ...             "series_id": "MAPCPI"
        ...             },]
        ...         }
        ...     }
        ... }
        >>> async def main():
        >>>     st_gdf = await _polars_geodataframe_converter_async(shapefile, meta_data)
        >>>     print(st_gdf)
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context. 
        >>> # For documentation purposes, the following pattern can be used to check the output geodataframe:
        >>> import asyncio
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
    """

    try:
        import polars_st as st
    except ImportError as e:
        raise OptionalDependencyError(
            message=f"{e}: Polars with geospatial support is not installed. Install it with `pip install polars-st` to use this method.",
            package="polars-st",
            feature="Helpers.to_pl_st_gdf",
            install_hint="pip install polars-st"
        ) from e

    gdf = await _geopandas_geodataframe_converter_async(shapefile, meta_data)
    return await asyncio.to_thread(st.from_geopandas, gdf)

# DataFrame Converter Maps
DATAFRAME_CONVERTER_MAP: Dict[str, Callable] = {
    'pandas': _pandas_dataframe_converter,
    'polars': _polars_dataframe_converter,
    'dask': _dask_dataframe_converter,
}
"""Mapping of dataframe converter functions for different backends."""

ASYNC_DATAFRAME_CONVERTER_MAP: Dict[str, Callable] = {
    'pandas': _pandas_dataframe_converter_async,
    'polars': _polars_dataframe_converter_async,
    'dask': _dask_dataframe_converter_async,
}
"""Mapping of asynchronous dataframe converter functions for different backends."""

GEODATAFRAME_CONVERTER_MAP: Dict[str, Callable] = {
    'geopandas': _geopandas_geodataframe_converter,
    'dask': _dask_geopandas_geodataframe_converter,
    'polars': _polars_geodataframe_converter,
}
"""Mapping of geodataframe converter functions for different backends."""

ASYNC_GEODATAFRAME_CONVERTER_MAP: Dict[str, Callable] = {
    'geopandas': _geopandas_geodataframe_converter_async,
    'dask': _dask_geopandas_geodataframe_converter_async,
    'polars': _polars_geodataframe_converter_async,
}
"""Mapping of asynchronous geodataframe converter functions for different backends."""

# Scalar Converters
def _identity_converter(parameter: str, value: Any) -> Any: # TODO: Do something with parameter input.
    """Internal converter function that returns the value as-is.
    
    Args:
        parameter (str): The name of the parameter.
        value (Any): The value of the parameter.

    Returns:
        Any: The original value without any conversion.

    Examples:
        >>> # Internal use        
        >>> from ._core import _identity_converter
        >>> result = _identity_converter("example_parameter", "test_value")
        >>> print(result)
        test_value
    """

    return value

def _date_parameter_converter(parameter: str, value: Any) -> str:
    """Internal converter function to convert str, date, or datetime to ISO 8601 date string (YYYY-MM-DD).
    
    Args:
        parameter (str): The name of the parameter.
        value (Any): The value of the parameter, which can be a string, date, or datetime.

    Returns:
        str: The converted date string in ISO 8601 format (YYYY-MM-DD).

    Raises:
        TypeConversionError: If the value cannot be converted to a date string.

    Examples:
        >>> # Internal use
        >>> from ._core import _date_parameter_converter
        >>> from datetime import datetime, date
        >>> result1 = _date_parameter_converter("date_param", datetime(2020, 1, 1))
        >>> result2 = _date_parameter_converter("date_param", date(2020, 1, 1))
        >>> result3 = _date_parameter_converter("date_param", "2020-01-01")
        >>> print(result1)  # Output: 2020-01-01
        >>> print(result2)  # Output: 2020-01-01
        >>> print(result3)  # Output: 2020-01-01
    """

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, str):
        return value

    raise TypeConversionError(
        message="Date parameter conversion failed.",
        parameter=parameter,
        expected="str | date | datetime",
        received=type(value).__name__,
    )

def _time_parameter_converter(parameter: str, value: Any) -> str:
    """Internal converter function to convert str, time, or datetime to ISO 8601 time string (HH:MM).
    
    Args:
        parameter (str): The name of the parameter.
        value (Any): The value of the parameter, which can be a string, time, or datetime.

    Returns:
        str: The converted time string in ISO 8601 format (HH:MM).

    Raises:
        TypeConversionError: If the value cannot be converted to a time string.

    Examples:
        >>> # Internal use
        >>> from ._core import _time_parameter_converter
        >>> from datetime import datetime, time
        >>> result1 = _time_parameter_converter("time_param", datetime(2020, 1, 1, 14, 30))
        >>> result2 = _time_parameter_converter("time_param", time(14, 30))
        >>> result3 = _time_parameter_converter("time_param", "14:30")
        >>> print(result1)  # Output: 14:30
        >>> print(result2)  # Output: 14:30
        >>> print(result3)  # Output: 14:30
    """

    if isinstance(value, datetime):
        return value.strftime("%H:%M")

    if isinstance(value, time):
        return value.strftime("%H:%M")

    if isinstance(value, str):
        return value

    raise TypeConversionError(
        message="Time parameter conversion failed.",
        parameter=parameter,
        expected="str | time | datetime",
        received=type(value).__name__,
    )

def _semicolon_list_converter(parameter: str, value: Any) -> str:
    """Internal converter function to convert str or list[str] to a semicolon-separated string.
    
    Args:
        parameter (str): The name of the parameter.
        value (Any): The value of the parameter, which can be a string or a list of strings.

    Returns:
        str: The converted string, which is either the original string or a semicolon-separated string if the input was a list of strings.

    Raises:
        TypeConversionError: If the value cannot be converted to a semicolon-separated string.
    
    Examples:
        >>> # Internal use
        >>> from ._core import _semicolon_list_converter
        >>> result1 = _semicolon_list_converter("list_param", "single_value")
        >>> result2 = _semicolon_list_converter("list_param", ["value1", "value2", "value3"])
        >>> print(result1)  # Output: single_value
        >>> print(result2)  # Output: value1;value2;value3
    """

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        if not all(isinstance(item, str) for item in value):
            raise TypeConversionError(
                message="List-string parameter conversion failed.",
                parameter=parameter,
                expected="str | list[str]",
                received=", ".join(type(item).__name__ for item in value),
            )

        return ";".join(value)

    raise TypeConversionError(
        message="List-string parameter conversion failed.",
        parameter=parameter,
        expected="str | list[str]",
        received=type(value).__name__,
    )

def _comma_date_list_converter(parameter: str, value: Any) -> str:
    """Internal converter function to convert str, date, datetime, or list of these types to a comma-separated string of ISO 8601 date strings.
    
    Args:
        parameter (str): The name of the parameter.
        value (Any): The value of the parameter, which can be a string, date, datetime, or a list of these types.

    Returns:
        str: The converted string, which is either the original string or a comma-separated string of ISO 8601 date strings if the input was a list of dates.

    Raises:
        TypeConversionError: If the value cannot be converted to a comma-separated string of date strings.

    Examples:
        >>> # Internal use
        >>> from ._core import _comma_date_list_converter
        >>> from datetime import datetime, date
        >>> result1 = _comma_date_list_converter("date_list_param", "2020-01-01")
        >>> result2 = _comma_date_list_converter("date_list_param", [datetime(2020, 1, 1), date(2020, 2, 1), "2020-03-01"])
        >>> print(result1)  # Output: 2020-01-01
        >>> print(result2)  # Output: 2020-01-01,2020-02-01,2020-03-01
    """

    if isinstance(value, str):
        return value

    if isinstance(value, (date, datetime)):
        return _date_parameter_converter(parameter, value)

    if isinstance(value, list):
        converted: list[str] = []

        for item in value:
            if item is None:
                continue

            converted.append(_date_parameter_converter(parameter, item))

        return ",".join(converted)

    raise TypeConversionError(
        message="Vintage dates parameter conversion failed.",
        parameter=parameter,
        expected="str | date | datetime | list[str | date | datetime | None]",
        received=type(value).__name__,
    )

# Cache Key Converters
def _hashable_type_converter(data: Optional[Dict[str, Optional[Union[str, int]]]]) -> Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]:
    """Internal converter function to make the data dictionary hashable for caching.

    Args:
        data (Dict[str, Optional[str | int]], optional): The query parameters for the request.

    Returns:
        Optional[Tuple[Tuple[str, Optional[str | int]], ...]]: A hashable representation of the data dictionary.

    Examples:
        >>> # Internal use
        >>> from ._core import _hashable_type_converter
        >>> data = {"param1": "value1", "param2": 123, "param3": None}
        >>> result = _hashable_type_converter(data)
        >>> # Test output
        >>> print(result)
        (('param1', 'value1'), ('param2', 123), ('param3', None))

    Notes:
        This function converts the data dictionary into a sorted tuple of key-value pairs, making it suitable for use as a cache key.

    Warnings:
        Caching is only applied if `cache_mode` is enabled. Ensure that the `data` parameter is hashable for caching to work correctly.
    """

    if data is None:
        return None

    return tuple(sorted(data.items()))

def _dict_type_converter(hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]) -> Optional[Dict[str, Optional[Union[str, int]]]]:
    """Internal converter function to convert hashable data back to a dictionary.
    
    Args:
        hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]]): The hashable representation of the data.

    Returns:
        Optional[Dict[str, Optional[str | int]]]: The original data dictionary.

    Examples:
        >>> # Internal use
        >>> from ._core import _dict_type_converter
        >>> hashable_data = (('param1', 'value1'), ('param2', 123), ('param3', None))
        >>> result = _dict_type_converter(hashable_data)
        >>> # Test output
        >>> print(result)
        {'param1': 'value1', 'param2': 123, 'param3': None}

    Notes:
        This function converts the hashable sorted tuple of key-value pairs back into a standard dictionary.

    Warnings:
        Caching is only applied if `cache_mode` is enabled. Ensure that the `data` parameter is hashable for caching to work correctly.
    """

    if hashable_data is None:
        return None

    return dict(hashable_data)

async def _hashable_type_converter_async(data: Optional[Dict[str, Optional[Union[str, int]]]]) -> Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]:
    """Internal asynchronous converter function to make the data dictionary hashable for caching.

    Args:
        data (Dict[str, Optional[str | int]], optional): The query parameters for the request.

    Returns:
        Optional[Tuple[Tuple[str, Optional[str | int]], ...]]: A hashable representation of the data dictionary.

    Examples:
        >>> # Internal use
        >>> from ._core import _hashable_type_converter_async
        >>> data = {"param1": "value1", "param2": 123, "param3": None}
        >>> async def main():
        >>>     result = await _hashable_type_converter_async(data)
        >>>     print(result)
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context.
        >>> # For documentation purposes, the following pattern can be used to check the output data:
        >>> import asyncio
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        (('param1', 'value1'), ('param2', 123), ('param3', None))

    Notes:
        This function converts the data dictionary into a sorted tuple of key-value pairs, making it suitable for use as a cache key.

    Warnings:
        Caching is only applied if `cache_mode` is enabled. Ensure that the `data` parameter is hashable for caching to work correctly.
    """

    return await asyncio.to_thread(_hashable_type_converter, data)

async def _dict_type_converter_async(hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]) -> Optional[Dict[str, Optional[Union[str, int]]]]:
    """Internal asynchronous converter function to convert hashable data back to a dictionary.
    
    Args:
        hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]]): The hashable representation of the data.

    Returns:
        Optional[Dict[str, Optional[str | int]]]: The original data dictionary.

    Examples:
        >>> # Internal use
        >>> from ._core import _dict_type_converter_async
        >>> hashable_data = (('param1', 'value1'), ('param2', 123), ('param3', None))
        >>> async def main():
        >>>     result = await _dict_type_converter_async(hashable_data)
        >>>     print(result)
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context.
        >>> # For documentation purposes, the following pattern can be used to check the output data:
        >>> import asyncio
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        (('param1', 'value1'), ('param2', 123), ('param3', None))

    Notes:
        This function converts the hashable sorted tuple of key-value pairs back into a standard dictionary.

    Warnings:
        Caching is only applied if `cache_mode` is enabled. Ensure that the `data` parameter is hashable for caching to work correctly.
    """

    return await asyncio.to_thread(_dict_type_converter, hashable_data)
