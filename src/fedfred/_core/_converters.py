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

This module provides converter methods for the FRED API.
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
        >>> response = {
        >>>     "observations": [
        >>>         {"date": "2020-01-01", "value": "100"},
        >>>         {"date": "2020-02-01", "value": "200"},
        >>>         {"date": "2020-03-01", "value": "300"},
        >>>     ]
        >>> }
        >>> df = _pandas_dataframe_converter(response)
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
    """Internal converter method to convert a FRED observation dictionary to a Polars DataFrame.

    Args:
        data (Dict[str, list]): FRED observation dictionary.

    Returns:
        polars.DataFrame: Converted Polars DataFrame.

    Raises:
        OptionalDependencyError: If Polars is not installed.
        DataFrameConversionError: If 'observations' key is not in the data.

    Examples:
        >>> response = {
        >>>     "observations": [
        >>>         {"date": "2020-01-01", "value": "100"},
        >>>         {"date": "2020-02-01", "value": "200"},
        >>>         {"date": "2020-03-01", "value": "300"},
        >>>     ]
        >>> }
        >>> df = _polars_dataframe_converter(response)
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
    """Internal converter method to convert a FRED observation dictionary to a Dask DataFrame.

    Args:
        data (Dict[str, list]): FRED observation dictionary.

    Returns:
        dask.dataframe.DataFrame: Converted Dask DataFrame.

    Raises:
        OptionalDependencyError: If Dask is not installed.
        DataFrameConversionError: If 'observations' key is not in the data.

    Examples:
        >>> response = {
        >>>     "observations": [
        >>>         {"date": "2020-01-01", "value": "100"},
        >>>         {"date": "2020-02-01", "value": "200"},
        >>>         {"date": "2020-03-01", "value": "300"},
        >>>     ]
        >>> }
        >>> df = _dask_dataframe_converter(response)
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
        raise OptionalDependencyError(
            message=f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method.",
            package="dask-geopandas",
            feature="Helpers.to_dd_gpd_gdf",
            install_hint="pip install dask-geopandas"
        ) from e

    gdf = _geopandas_geodataframe_converter(shapefile, meta_data)
    return dd_gpd.from_geopandas(gdf, npartitions=1)

def _polars_geodataframe_converter(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'st.GeoDataFrame':
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
        raise OptionalDependencyError(
            message=f"{e}: Polars with geospatial support is not installed. Install it with `pip install polars-st` to use this method.",
            package="polars-st",
            feature="Helpers.to_pl_st_gdf",
            install_hint="pip install polars-st"
        ) from e

    gdf = _geopandas_geodataframe_converter(shapefile, meta_data)
    return st.from_geopandas(gdf)

async def _pandas_dataframe_converter_async(data: Dict[str, list]) -> pd.DataFrame:
    """Helper method to convert a FRED observation dictionary to a Pandas DataFrame asynchronously.

    Args:
        data (Dict[str, list]): FRED observation dictionary.

    Returns:
        pandas.DataFrame: Converted Pandas DataFrame.

    Raises:
        DataFrameConversionError: If 'observations' key is not in the data.

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
        >>>     df = await fd.AsyncHelpers._pandas_dataframe_converter_async(data)
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
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers._pandas_dataframe_converter_async.html

    See Also:
        - :meth:`AsyncHelpers._polars_dataframe_converter_async`: Asynchronously convert a FRED observation dictionary to a Polars DataFrame.
        - :meth:`AsyncHelpers._dask_dataframe_converter_async`: Asynchronously convert a FRED observation dictionary to a Dask DataFrame.    
    """

    return await asyncio.to_thread(_pandas_dataframe_converter, data)

async def _polars_dataframe_converter_async(data: Dict[str, list]) -> 'pl.DataFrame':
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

    return await asyncio.to_thread(_polars_dataframe_converter, data)

async def _dask_dataframe_converter_async(data: Dict[str, list]) -> 'dd.DataFrame':
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
        raise OptionalDependencyError(
            message=f"{e}: Dask is not installed. Install it with `pip install dask` to use this method.",
            package="dask",
            feature="Helpers.to_dd_df",
            install_hint="pip install dask"
        ) from e
    
    df = await _pandas_dataframe_converter_async(data)
    return await asyncio.to_thread(dd.from_pandas, df, npartitions=1)

async def _geopandas_geodataframe_converter_async(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> gpd.GeoDataFrame:
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

    return await asyncio.to_thread(_geopandas_geodataframe_converter, shapefile, meta_data)

async def _dask_geopandas_geodataframe_converter_async(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'dd_gpd.GeoDataFrame':
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
        raise OptionalDependencyError(
            message=f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method.",
            package="dask-geopandas",
            feature="Helpers.to_dd_gpd_gdf",
            install_hint="pip install dask-geopandas"
        ) from e
    
    gdf = await _geopandas_geodataframe_converter_async(shapefile, meta_data)
    return await asyncio.to_thread(dd_gpd.from_geopandas, gdf, npartitions=1)

async def _polars_geodataframe_converter_async(shapefile: gpd.GeoDataFrame, meta_data: Dict) -> 'st.GeoDataFrame':
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
    """Helper method to convert a list of strings to a semicolon-separated string.

    Args:
        parameter (list[str]): List of strings to convert.

    Returns:
        str: Semicolon-separated string.

    Raises:
        ValueError: If parameter is not a list of strings.

    Examples:
        >>> import fedfred as fd
        >>> parameter = ["tag1", "tag2", "tag3"]
        >>> result = fd.Helpers.liststring_conversion(parameter)
        >>> print(result)
        tag1;tag2;tag3

    Notes:
        This method joins the elements of the list with semicolons.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.liststring_conversion.html

    See Also:
        - :meth:`Helpers.liststring_validation`: Validate a semicolon-separated string.
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

def _vintage_dates_type_converter(param: Union[str, datetime, list[Optional[Union[str, datetime]]]]) -> str:
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

    if isinstance(param, datetime):
        return _datetime_converter(param)

    if isinstance(param, list):
        converted_list = [
            _datetime_converter(i) if isinstance(i, datetime) else i
            for i in param
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
            received=type(param).__name__,
        )

def _datetime_converter(param: datetime) -> str:
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
        raise TypeConversionError(
            message="Type conversion failed: Parameter must be a datetime object",
            expected="datetime",
            received=type(param).__name__,
        )

    return param.strftime("%Y-%m-%d")

def _datetime_hh_mm_converter(param: datetime) -> str:
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
        raise TypeConversionError(
            message="Type conversion failed: Parameter must be a datetime object",
            expected="datetime",
            received=type(param).__name__,
        )
    
    return param.strftime("%H:%M")

async def _liststring_converter_async(param: list[str]) -> str:
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
        >>>     result = await fd.AsyncHelpers._liststring_converter_async(param)
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

    return await asyncio.to_thread(_liststring_converter, param)

async def _vintage_dates_type_converter_async(param: Union[str, datetime, list[Optional[Union[str, datetime]]]]) -> str:
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

    return await asyncio.to_thread(_vintage_dates_type_converter, param)

async def _datetime_converter_async(param: datetime) -> str:
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

    return await asyncio.to_thread(_datetime_converter, param)

async def _datetime_hh_mm_converter_async(param: datetime) -> str:
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

    return await asyncio.to_thread(_datetime_hh_mm_converter, param)

# Collective Parameter Converters
def _hashable_type_converter(data: Optional[Dict[str, Optional[Union[str, int]]]]) -> Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]:
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

def _dict_type_converter(hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]) -> Optional[Dict[str, Optional[Union[str, int]]]]:
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

async def _hashable_type_converter_async(data: Optional[Dict[str, Optional[Union[str, int]]]]) -> Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]:
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

    return await asyncio.to_thread(_hashable_type_converter, data)

async def _dict_type_converter_async(hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]) -> Optional[Dict[str, Optional[Union[str, int]]]]:
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

    return await asyncio.to_thread(_dict_type_converter, hashable_data)
