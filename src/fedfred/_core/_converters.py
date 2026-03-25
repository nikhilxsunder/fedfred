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

import asyncio
from typing import TYPE_CHECKING, Dict, Optional, Union, Tuple
from datetime import datetime
import pandas as pd
import geopandas as gpd

from fedfred.exceptions.conversion import TypeConversionError
from ..exceptions import DataFrameConversionError, GeoDataFrameConversionError, OptionalDependencyError

if TYPE_CHECKING:
    import dask.dataframe as dd # pragma: no cover
    import dask_geopandas as dd_gpd # pragma: no cover
    import polars as pl # pragma: no cover
    import polars_st as st # pragma: no cover

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

# Single Parameter Converters
def _liststring_converter(parameter: list[str]) -> str:
    """Internal converter function to convert a list of strings to a semicolon-separated string.

    Args:
        parameter (list[str]): List of strings to convert.

    Returns:
        str: Semicolon-separated string.

    Raises:
        TypeConversionError: If parameter is not a list of strings.

    Examples:
        >>> # Internal use
        >>> from ._core import _liststring_converter
        >>> parameter = ["tag1", "tag2", "tag3"]
        >>> result = _liststring_converter(parameter)
        >>> # Test output dataframe
        >>> print(result)
        tag1;tag2;tag3

    Notes:
        This method joins the elements of the list with semicolons.
    """

    if not isinstance(parameter, list):
        raise TypeConversionError(
            message="Type conversion failed: Parameter must be a list of strings",
            expected="list[str]",
            received=type(parameter).__name__,
        )

    if any(not isinstance(i, str) for i in parameter):
        raise TypeConversionError(
            message="Type conversion failed: All elements in the list must be strings",
            expected="list[str]",
            received=", ".join(type(i).__name__ for i in parameter if not isinstance(i, str)),
        )

    return ';'.join(parameter)

def _vintage_dates_type_converter(parameter: Union[str, datetime, list[Optional[Union[str, datetime]]]]) -> str:
    """Internal converter function to convert a vintage_dates or list of vintage_dates parameter to a string in YYYY-MM-DD format.

    Args:
        parameter (str | datetime | list[Optional[str | datetime]]): vintage_dates parameter to convert.

    Returns:
        str: Converted vintage_dates string.

    Raises:
        TypeConversionError: If parameter is not a string, datetime object, or list of strings/datetime objects.

    Examples:
        >>> # Internal use
        >>> from datetime import datetime
        >>> from ._core import _vintage_dates_type_converter
        >>> parameter = datetime(2020, 1, 1)
        >>> result1 = _vintage_dates_type_converter(parameter)
        >>> # Test output dataframe
        >>> print(result1)
        2020-01-01

    Notes:
        This method handles single strings, datetime objects, and lists of strings/datetime objects.
    """

    if isinstance(parameter, str):
        return parameter

    if isinstance(parameter, datetime):
        return _datetime_converter(parameter)

    if isinstance(parameter, list):
        converted_list = [
            _datetime_converter(i) if isinstance(i, datetime) else i
            for i in parameter
            if i is not None
        ]

        if not all(isinstance(i, str) for i in converted_list):
            raise TypeConversionError(
                message="Type conversion failed: All elements in the list must be strings or datetime objects",
                expected="list[Optional[str | datetime]]",
                received=", ".join(type(i).__name__ for i in converted_list if not isinstance(i, str)),
            )

        return ','.join(converted_list)

    else:
        raise TypeConversionError(
            message="Type conversion failed: Parameter must be a string, datetime object, or list of strings/datetime objects",
            expected="str | datetime | list[Optional[str | datetime]]",
            received=type(parameter).__name__,
        )

def _datetime_converter(parameter: datetime) -> str:
    """Internal converter function to convert a datetime object to a string in YYYY-MM-DD format.

    Args:
        parameter (datetime): Datetime object to convert.

    Returns:
        str: Formatted date string.

    Raises:
        TypeConversionError: If parameter is not a datetime object.

    Examples:
        >>> # Internal use
        >>> from datetime import datetime
        >>> from ._core import _datetime_converter
        >>> parameter = datetime(2020, 1, 1)
        >>> result = _datetime_converter(parameter)
        >>> # Test output dataframe
        >>> print(result)
        2020-01-01
    """

    if not isinstance(parameter, datetime):
        raise TypeConversionError(
            message="Type conversion failed: Parameter must be a datetime object",
            expected="datetime",
            received=type(parameter).__name__,
        )

    return parameter.strftime("%Y-%m-%d")

def _datetime_hh_mm_converter(parameter: datetime) -> str:
    """Internal converter function to convert a datetime object to a string in HH:MM format.

    Args:
        parameter (datetime): Datetime object to convert.

    Returns:
        str: Formatted time string.

    Raises:
        TypeConversionError: If parameter is not a datetime object.

    Examples:
        >>> # Internal use
        >>> from datetime import datetime
        >>> from ._core import _datetime_hh_mm_converter
        >>> parameter = datetime(2020, 1, 1, 15, 30)
        >>> result = _datetime_hh_mm_converter(parameter)
        >>> # Test output dataframe
        >>> print(result)
        15:30
    """

    if not isinstance(parameter, datetime):
        raise TypeConversionError(
            message="Type conversion failed: Parameter must be a datetime object",
            expected="datetime",
            received=type(parameter).__name__,
        )

    return parameter.strftime("%H:%M")

async def _liststring_converter_async(parameter: list[str]) -> str:
    """Internal asynchronous converter function to convert a list of strings to a semicolon-separated string.

    Args:
        parameter (list[str]): List of strings to convert.

    Returns:
        str: Semicolon-separated string.

    Raises:
        TypeConversionError: If parameter is not a list of strings.

    Examples:
        >>> # Internal use
        >>> from _core import _liststring_converter_async
        >>> parameters = ["GDP", "CPI", "UNRATE"]
        >>> async def main():
        >>>     result = await _liststring_converter_async(param)
        >>>     print(result)
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context. 
        >>> # For documentation purposes, the following pattern can be used to check the output data:
        >>> import asyncio
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        GDP;CPI;UNRATE

    Notes:
        This method joins the list elements with a semicolon (';') separator.
    """

    return await asyncio.to_thread(_liststring_converter, parameter)

async def _vintage_dates_type_converter_async(parameter: Union[str, datetime, list[Optional[Union[str, datetime]]]]) -> str:
    """Internal asynchronous converter function to convert a vintage_dates parameter to a string.

    Args:
        parameter (str | datetime | list[Optional[str | datetime]]]): vintage_dates parameter to convert.

    Returns:
        str: Converted vintage_dates string.

    Raises:
        TypeConversionError: If parameter is not a string, datetime object, or list of strings/datetime objects.

    Examples:
        >>> # Internal use
        >>> from datetime import datetime
        >>> from ._core import _vintage_dates_type_converter_async
        >>> parameter = datetime(2020, 1, 1)
        >>> async def main():
        >>>     result = await _vintage_dates_type_converter_async(parameter)
        >>>     print(result)
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context. 
        >>> # For documentation purposes, the following pattern can be used to check the output data:
        >>> import asyncio
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        2020-01-01

    Notes:
        This method handles single strings, datetime objects, and lists of strings/datetime objects, converting them to a comma-separated string.
    """

    return await asyncio.to_thread(_vintage_dates_type_converter, parameter)

async def _datetime_converter_async(parameter: datetime) -> str:
    """Internal asynchronous converter function to convert a datetime object to a string in YYYY-MM-DD format.

    Args:
        parameter (datetime): Datetime object to convert.

    Returns:
        str: Formatted date string.

    Raises:
        TypeConversionError: If parameter is not a datetime object.

    Examples:
        >>> # Internal use
        >>> from datetime import datetime
        >>> from ._core import _datetime_converter_async
        >>> param = datetime(2020, 1, 1)
        >>> async def main():
        >>>     result = await _datetime_converter_async(param)
        >>>     print(result)
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context. 
        >>> # For documentation purposes, the following pattern can be used to check the output data:
        >>> import asyncio
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        2020-01-01
    """

    return await asyncio.to_thread(_datetime_converter, parameter)

async def _datetime_hh_mm_converter_async(parameter: datetime) -> str:
    """Internal asynchronous converter function to convert a datetime object to a string in HH:MM format.

    Args:
        parameter (datetime): Datetime object to convert.

    Returns:
        str: Formatted time string.

    Raises:
        TypeConversionError: If parameter is not a datetime object.

    Examples:
        >>> # Internal use
        >>> from datetime import datetime
        >>> from ._core import _datetime_hh_mm_converter_async
        >>> param = datetime(2020, 1, 1, 14, 30)
        >>> async def main():
        >>>     result = await _datetime_hh_mm_converter_async(param)
        >>>     print(result)
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context. 
        >>> # For documentation purposes, the following pattern can be used to check the output data:
        >>> import asyncio
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.datetime_hh_mm_conversion.html

    See Also:
        - :meth:`AsyncHelpers.datetime_conversion`: Convert a datetime object to a string in YYYY-MM-DD format asynchronously.
        - :meth:`AsyncHelpers.datetime_hh_mm_conversion`: Validate hh:mm formatted parameters asynchronously.
    """

    return await asyncio.to_thread(_datetime_hh_mm_converter, parameter)

# Collective Parameter Converters
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
