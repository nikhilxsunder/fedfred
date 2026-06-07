# filepath: /src/fedfred/_core/_converters.py
#
# Copyright (c) 2026 Nikhil Sunder
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
"""Value and DataFrame converters for the fedfred core package.

This module holds three families of converters. Scalar parameter converters
(``_date_parameter_converter``, ``_semicolon_list_converter``, etc.) normalize
caller-supplied Python values into the string forms FRED expects on the wire.
DataFrame and GeoDataFrame converters turn FRED/GeoFRED observation payloads
into the configured backend's frame type (pandas, polars, dask; geopandas,
dask-geopandas, polars-st), resolved per the package backend settings. Cache-key
converters round-trip a parameter dict to a hashable tuple and back so cached
request functions can key on it. Optional backends are imported lazily and raise
:class:`~fedfred.exceptions.OptionalDependencyError` when absent.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time
from typing import TYPE_CHECKING

import geopandas as gpd
import pandas as pd

from ..exceptions import (
    DataFrameConversionError,
    GeoDataFrameConversionError,
    OptionalDependencyError,
    TypeConversionError,
)
from ..settings import _resolve_dataframe_backend, _resolve_geodataframe_backend

if TYPE_CHECKING:
    import dask.dataframe as dd  # pragma: no cover
    import dask_geopandas as dd_gpd  # pragma: no cover
    import polars as pl  # pragma: no cover
    import polars_st as st  # pragma: no cover

__all__ = [
    "_dict_type_converter",
    "_hashable_type_converter",
]

# Typing Aliases
ParameterConverter = Callable[[str, object], object]
"""Type alias for a scalar parameter converter: takes a parameter name and a raw value, returns the API-ready value."""

# DataFrame Converters
def _pandas_dataframe_converter(data: dict[str, list]) -> pd.DataFrame:
    """Convert a FRED observations payload to a pandas DataFrame.

    Args:
        data (dict[str, list]): A FRED response containing an ``observations`` list.

    Returns:
        pandas.DataFrame: The observations, with a ``date`` ``DatetimeIndex`` and a numeric ``value`` column.

    Raises:
        DataFrameConversionError: If ``data`` has no ``observations`` key.

    Examples:
        >>> from fedfred._core._converters import _pandas_dataframe_converter  # doctest: +SKIP
        >>> _pandas_dataframe_converter({"observations": [{"date": "2020-01-01", "value": "100"}]})  # doctest: +SKIP

    Notes:
        ``date`` becomes a ``DatetimeIndex``; ``value`` is coerced to numeric with
        non-numeric entries set to ``NaN``.
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

def _polars_dataframe_converter(data: dict[str, list]) -> pl.DataFrame:
    """Convert a FRED observations payload to a Polars DataFrame.

    Args:
        data (dict[str, list]): A FRED response containing an ``observations`` list.

    Returns:
        polars.DataFrame: The observations, with ``value`` cast to ``Float64``.

    Raises:
        OptionalDependencyError: If Polars is not installed.
        DataFrameConversionError: If ``data`` has no ``observations`` key.

    Examples:
        >>> from fedfred._core._converters import _polars_dataframe_converter  # doctest: +SKIP
        >>> _polars_dataframe_converter({"observations": [{"date": "2020-01-01", "value": "100"}]})  # doctest: +SKIP

    Notes:
        ``value`` is cast to ``Float64`` with ``'NA'`` strings mapped to ``None``.
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

def _dask_dataframe_converter(data: dict[str, list]) -> dd.DataFrame:
    """Convert a FRED observations payload to a Dask DataFrame.

    Args:
        data (dict[str, list]): A FRED response containing an ``observations`` list.

    Returns:
        dask.dataframe.DataFrame: The observations as a single-partition Dask DataFrame.

    Raises:
        OptionalDependencyError: If Dask is not installed.
        DataFrameConversionError: If ``data`` has no ``observations`` key.

    Examples:
        >>> from fedfred._core._converters import _dask_dataframe_converter  # doctest: +SKIP
        >>> _dask_dataframe_converter({"observations": [{"date": "2020-01-01", "value": "100"}]})  # doctest: +SKIP

    Notes:
        Built by converting to pandas first (:func:`_pandas_dataframe_converter`),
        then wrapping in a single-partition Dask DataFrame.
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

def _geopandas_geodataframe_converter(
    shapefile: gpd.GeoDataFrame,
    meta_data: dict
) -> gpd.GeoDataFrame:
    """Attach GeoFRED observation values to a shapefile GeoDataFrame.

    Args:
        shapefile (geopandas.GeoDataFrame): The region geometries, with a ``name`` column.
        meta_data (dict): The GeoFRED response metadata containing a ``data`` section.

    Returns:
        geopandas.GeoDataFrame: ``shapefile`` indexed by ``name`` with ``value`` and ``series_id`` columns populated from the metadata.

    Raises:
        GeoDataFrameConversionError: If ``meta_data`` has no ``data`` section.

    Examples:
        >>> from fedfred._core._converters import _geopandas_geodataframe_converter  # doctest: +SKIP
        >>> _geopandas_geodataframe_converter(shapefile, meta_data)  # doctest: +SKIP

    Notes:
        Matches observation rows to geometries by region name; geometries with no
        matching observation keep ``None`` for ``value`` and ``series_id``.
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

def _dask_geopandas_geodataframe_converter(
    shapefile: gpd.GeoDataFrame,
    meta_data: dict
) -> dd_gpd.GeoDataFrame:
    """Attach GeoFRED observation values to a shapefile as a Dask GeoPandas GeoDataFrame.

    Args:
        shapefile (geopandas.GeoDataFrame): The region geometries, with a ``name`` column.
        meta_data (dict): The GeoFRED response metadata containing a ``data`` section.

    Returns:
        dask_geopandas.GeoDataFrame: The populated GeoDataFrame as a single-partition Dask GeoPandas frame.

    Raises:
        OptionalDependencyError: If dask-geopandas is not installed.
        GeoDataFrameConversionError: If ``meta_data`` has no ``data`` section.

    Examples:
        >>> from fedfred._core._converters import _dask_geopandas_geodataframe_converter  # doctest: +SKIP
        >>> _dask_geopandas_geodataframe_converter(shapefile, meta_data)  # doctest: +SKIP

    Notes:
        Built by populating a geopandas GeoDataFrame first
        (:func:`_geopandas_geodataframe_converter`), then wrapping it in a
        single-partition Dask GeoPandas frame.
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

def _polars_geodataframe_converter(
    shapefile: gpd.GeoDataFrame,
    meta_data: dict
) -> st.GeoDataFrame:
    """Attach GeoFRED observation values to a shapefile as a Polars-ST GeoDataFrame.

    Args:
        shapefile (geopandas.GeoDataFrame): The region geometries, with a ``name`` column.
        meta_data (dict): The GeoFRED response metadata containing a ``data`` section.

    Returns:
        polars_st.GeoDataFrame: The populated GeoDataFrame converted to Polars-ST.

    Raises:
        OptionalDependencyError: If polars-st is not installed.
        GeoDataFrameConversionError: If ``meta_data`` has no ``data`` section.

    Examples:
        >>> from fedfred._core._converters import _polars_geodataframe_converter  # doctest: +SKIP
        >>> _polars_geodataframe_converter(shapefile, meta_data)  # doctest: +SKIP

    Notes:
        Built by populating a geopandas GeoDataFrame first
        (:func:`_geopandas_geodataframe_converter`), then converting it to
        Polars-ST.
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

# DataFrame Converter Maps
DATAFRAME_CONVERTER_MAP: dict[str, Callable] = {
    'pandas': _pandas_dataframe_converter,
    'polars': _polars_dataframe_converter,
    'dask': _dask_dataframe_converter,
}
"""Mapping of dataframe backend name to its observation converter."""

GEODATAFRAME_CONVERTER_MAP: dict[str, Callable] = {
    'geopandas': _geopandas_geodataframe_converter,
    'dask': _dask_geopandas_geodataframe_converter,
    'polars': _polars_geodataframe_converter,
}
"""Mapping of geodataframe backend name to its observation converter."""

# Dataframe Resolvers
def _resolve_dataframe_converter(backend: str | None = None) -> Callable:
    """Return the dataframe converter for a backend.

    Args:
        backend (str | None): The backend name (``"pandas"``, ``"polars"``, or ``"dask"``). If ``None``, the configured default backend is used.

    Returns:
        Callable: The observation converter for the resolved backend.

    Examples:
        >>> from fedfred._core._converters import _resolve_dataframe_converter
        >>> _resolve_dataframe_converter("pandas").__name__
        '_pandas_dataframe_converter'
    """
    if backend is None:
        backend = _resolve_dataframe_backend()

    return DATAFRAME_CONVERTER_MAP[backend]

def _resolve_geodataframe_converter(backend: str | None = None) -> Callable:
    """Return the geodataframe converter for a backend.

    Args:
        backend (str | None): The backend name (``"geopandas"``, ``"dask"``, or ``"polars"``). If ``None``, the configured default backend is used.

    Returns:
        Callable: The observation converter for the resolved backend.

    Examples:
        >>> from fedfred._core._converters import _resolve_geodataframe_converter
        >>> _resolve_geodataframe_converter("geopandas").__name__
        '_geopandas_geodataframe_converter'
    """
    if backend is None:
        backend = _resolve_geodataframe_backend()

    return GEODATAFRAME_CONVERTER_MAP[backend]

# Scalar Converters
def _identity_converter(parameter: str, value: object) -> object: # TODO: Do something with parameter input.
    """Return the value unchanged.

    Args:
        parameter (str): The name of the parameter (currently unused).
        value (object): The value to pass through.

    Returns:
        object: ``value``, unchanged.

    Examples:
        >>> from fedfred._core._converters import _identity_converter
        >>> _identity_converter("example_parameter", "test_value")
        'test_value'
    """
    return value

def _date_parameter_converter(parameter: str, value: object) -> str:
    """Convert a string, ``date``, or ``datetime`` to a ``YYYY-MM-DD`` string.

    Args:
        parameter (str): The name of the parameter, used for error context.
        value (object): A ``str``, ``date``, or ``datetime`` value.

    Returns:
        str: The ISO 8601 date string. Strings are passed through unchanged.

    Raises:
        TypeConversionError: If ``value`` is not a string, date, or datetime.

    Examples:
        >>> from datetime import date, datetime
        >>> from fedfred._core._converters import _date_parameter_converter
        >>> _date_parameter_converter("date_param", datetime(2020, 1, 1, 14, 30))
        '2020-01-01'
        >>> _date_parameter_converter("date_param", date(2020, 1, 1))
        '2020-01-01'
        >>> _date_parameter_converter("date_param", "2020-01-01")
        '2020-01-01'
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

def _time_parameter_converter(parameter: str, value: object) -> str:
    """Convert a string, ``time``, or ``datetime`` to an ``HH:MM`` string.

    Args:
        parameter (str): The name of the parameter, used for error context.
        value (object): A ``str``, ``time``, or ``datetime`` value.

    Returns:
        str: The ``HH:MM`` time string. Strings are passed through unchanged.

    Raises:
        TypeConversionError: If ``value`` is not a string, time, or datetime.

    Examples:
        >>> from datetime import datetime, time
        >>> from fedfred._core._converters import _time_parameter_converter
        >>> _time_parameter_converter("time_param", datetime(2020, 1, 1, 14, 30))
        '14:30'
        >>> _time_parameter_converter("time_param", time(14, 30))
        '14:30'
        >>> _time_parameter_converter("time_param", "14:30")
        '14:30'
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

def _semicolon_list_converter(parameter: str, value: object) -> str:
    """Convert a string or list of strings to a semicolon-separated string.

    Args:
        parameter (str): The name of the parameter, used for error context.
        value (object): A ``str`` (passed through) or ``list[str]`` (joined on ``;``).

    Returns:
        str: The original string, or the list joined with semicolons.

    Raises:
        TypeConversionError: If ``value`` is not a string or a list of strings.

    Examples:
        >>> from fedfred._core._converters import _semicolon_list_converter
        >>> _semicolon_list_converter("list_param", "single_value")
        'single_value'
        >>> _semicolon_list_converter("list_param", ["value1", "value2", "value3"])
        'value1;value2;value3'
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

def _comma_date_list_converter(parameter: str, value: object) -> str:
    """Convert a date-like value or list of them to a comma-separated ``YYYY-MM-DD`` string.

    Args:
        parameter (str): The name of the parameter, used for error context.
        value (object): A ``str``, ``date``, ``datetime``, or a list of those (``None`` entries are skipped).

    Returns:
        str: The original string, or a comma-separated string of ISO 8601 dates.

    Raises:
        TypeConversionError: If ``value`` (or any list element) is not a string, date, or datetime.

    Examples:
        >>> from datetime import date, datetime
        >>> from fedfred._core._converters import _comma_date_list_converter
        >>> _comma_date_list_converter("date_list_param", "2020-01-01")
        '2020-01-01'
        >>> _comma_date_list_converter("date_list_param", [datetime(2020, 1, 1), date(2020, 2, 1), "2020-03-01"])
        '2020-01-01,2020-02-01,2020-03-01'
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
def _hashable_type_converter(data: dict[str, str | int | None] | None) -> tuple[tuple[str, str | int | None], ...] | None:
    """Convert a parameter dict to a hashable, sorted tuple of items for use as a cache key.

    Args:
        data (dict[str, str | int | None] | None): The request parameters, or ``None``.

    Returns:
        tuple[tuple[str, str | int | None], ...] | None: The items as a key-sorted tuple, or ``None`` if ``data`` is ``None``.

    Examples:
        >>> from fedfred._core._converters import _hashable_type_converter
        >>> _hashable_type_converter({"param1": "value1", "param2": 123, "param3": None})
        (('param1', 'value1'), ('param2', 123), ('param3', None))

    Notes:
        Items are sorted by key so that dicts differing only in insertion order
        produce the same cache key.
    """
    if data is None:
        return None

    return tuple(sorted(data.items()))

def _dict_type_converter(hashable_data: tuple[tuple[str, str | int | None], ...] | None) -> dict[str, str | int | None] | None:
    """Convert a hashable cache-key tuple back into a parameter dict.

    Args:
        hashable_data (tuple[tuple[str, str | int | None], ...] | None): The key-sorted item tuple, or ``None``.

    Returns:
        dict[str, str | int | None] | None: The reconstructed dict, or ``None`` if ``hashable_data`` is ``None``.

    Examples:
        >>> from fedfred._core._converters import _dict_type_converter
        >>> _dict_type_converter((('param1', 'value1'), ('param2', 123), ('param3', None)))
        {'param1': 'value1', 'param2': 123, 'param3': None}

    Notes:
        Inverse of :func:`_hashable_type_converter`.
    """
    if hashable_data is None:
        return None

    return dict(hashable_data)

# Model Converters
def _coerce_lower(value: str | None) -> str | None:
    """Lowercase a string value, preserving ``None``.

    Args:
        value (str | None): A string payload field, or ``None``.

    Returns:
        str | None: The lowercased string, or ``None`` if ``value`` is ``None``.

    Raises:
        TypeConversionError: If ``value`` is neither a string nor ``None``.

    Examples:
        >>> from fedfred._core._converters import _coerce_lower
        >>> _coerce_lower("ASC")
        'asc'
        >>> _coerce_lower(None) is None
        True
    """
    if value is None:
        return None

    if not isinstance(value, str):
        raise ConverterError(
            message="Expected string or None for short-code field.",
            parameter=value,
            expected="str | None",
            received=type(value).__name__
        )

    return value.lower()
