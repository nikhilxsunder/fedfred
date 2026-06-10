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
from typing import TYPE_CHECKING, Any

import geopandas as gpd
import numpy as np
import pandas as pd

from ..exceptions import (
    GeoDataFrameConversionError,
    OptionalDependencyError,
    TypeConversionError,
)
from ..settings import _resolve_geodataframe_backend
from ._dependencies import _require_module

if TYPE_CHECKING:
    import dask_geopandas as dd_gpd  # pragma: no cover
    import polars_st as st  # pragma: no cover

__all__ = [
    "_coerce_lower",
    "_dict_type_converter",
    "_hashable_type_converter",
    "_pandas_frequency_converter",
]

def _freq_aware_index(dates: np.ndarray, frequency: str | None) -> pd.DatetimeIndex:
    """DatetimeIndex with freq attached when the date axis is unique & regular."""
    idx = pd.DatetimeIndex(dates, name="date")
    if not (idx.is_monotonic_increasing and idx.is_unique):
        return idx
    mapped = _pandas_frequency_converter(frequency)
    inferred = pd.infer_freq(idx) if len(idx) >= 3 else None
    for candidate in (mapped, inferred):
        if candidate:
            try:
                idx.freq = candidate
                break
            except ValueError:
                continue
    return idx

def _columns_to_pandas(columns: dict[str, np.ndarray], *,
                       index: str | None = None, frequency: str | None = None) -> pd.DataFrame:
    if index == "date":
        data = {k: v for k, v in columns.items() if k != "date"}
        return pd.DataFrame(data, index=_freq_aware_index(columns["date"], frequency))
    df = pd.DataFrame(columns)
    return df.set_index(index) if index is not None else df

def _columns_to_polars(columns: dict[str, np.ndarray]) -> Any:
    pl = _require_module("polars", "to_polars")
    return pl.DataFrame({k: v for k, v in columns.items()})

def _columns_to_dask(columns: dict[str, np.ndarray], *,
                     npartitions: int = 1, index: str | None = None,
                     frequency: str | None = None) -> Any:
    dd = _require_module("dask.dataframe", "to_dask", extra="dask")
    return dd.from_pandas(
        _columns_to_pandas(columns, index=index, frequency=frequency),
        npartitions=npartitions,
    )

def _columns_to_cudf(columns: dict[str, np.ndarray], *, index: str | None = None) -> Any:
    cudf = _require_module("cudf", "to_cudf")
    if index == "date":
        data = {k: v for k, v in columns.items() if k != "date"}
        df = cudf.DataFrame(data)
        df.index = cudf.DatetimeIndex(columns["date"])
        df.index.name = "date"
        return df
    df = cudf.DataFrame(columns)
    return df.set_index(index) if index is not None else df

def _columns_to_arrow(columns: dict[str, np.ndarray]) -> Any:
    pa = _require_module("pyarrow", "to_arrow", extra="arrow")
    return pa.table(columns)

def _columns_to_series(values: np.ndarray, dates: np.ndarray,
                       frequency: str | None, name: str) -> pd.Series:
    return pd.Series(values, index=_freq_aware_index(dates, frequency), name=name)

def _vintage_matrix(dates: np.ndarray, values: np.ndarray,
                    realtime_start: np.ndarray, frequency: str | None) -> pd.DataFrame:
    wide = pd.DataFrame(
        {"date": dates, "realtime_start": realtime_start, "value": values}
    ).pivot(index="date", columns="realtime_start", values="value")
    wide.index = _freq_aware_index(wide.index.values, frequency)
    return wide

# Typing Aliases
ParameterConverter = Callable[[str, object], object]
"""Type alias for a scalar parameter converter: takes a parameter name and a raw value, returns the API-ready value."""

# DataFrame Converters
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
GEODATAFRAME_CONVERTER_MAP: dict[str, Callable] = {
    'geopandas': _geopandas_geodataframe_converter,
    'dask': _dask_geopandas_geodataframe_converter,
    'polars': _polars_geodataframe_converter,
}
"""Mapping of geodataframe backend name to its observation converter."""

# Dataframe Resolvers
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

# Converter Mappings
_FRED_TO_PANDAS_FREQ: dict[str, str] = {
        "d": "D",
        "w": "W",
        "bw": "2W",
        "m": "MS",
        "q": "QS",
        "sa": "6MS",
        "a": "YS",
        "wef": "W-FRI",
        "weth": "W-THU",
        "wew": "W-WED",
        "wetu": "W-TUE",
        "wem": "W-MON",
        "wesu": "W-SUN",
        "wesa": "W-SAT",
        "bwew": "2W-WED",
        "bwem": "2W-MON",
    }

def _pandas_frequency_converter(frequency: str | None):
    """
    """
    return _FRED_TO_PANDAS_FREQ.get(frequency or "")

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
