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

from datetime import date, datetime, time
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from ..exceptions import (
    ConversionError,
    TypeConversionError,
)
from ._loaders import _require_module
from ._mappings import _FRED_TO_PANDAS_FREQ
from ._types import CacheKey, CacheParameters

if TYPE_CHECKING:
    import cudf  # pragma: no cover
    import dask.dataframe as dd  # pragma: no cover
    import polars as pl  # pragma: no cover
    import pyarrow as pa  # pragma: no cover


def _freq_aware_index(dates: np.ndarray, frequency: str | None) -> pd.DatetimeIndex:
    """Build a :class:`pandas.DatetimeIndex`, attaching ``freq`` when determinable.

    Frequency is a property of the observation-date interval and is independent of
    revisions, so this backs every date-indexed conversion. The mapped FRED alias
    is tried first (authoritative), then :func:`pandas.infer_freq` as a fallback;
    attachment is attempted only on a unique, monotonic-increasing axis, so the
    function is safe to call on a vintage series' non-unique dates — it returns
    ``freq=None`` there rather than raising.

    Args:
        dates (numpy.ndarray): A ``datetime64`` array of observation dates.
        frequency (str | None): The FRED frequency code (e.g. ``"m"``, ``"q"``),
            or ``None`` to rely on inference.

    Returns:
        pandas.DatetimeIndex: The date index, with ``.freq`` set when the axis is
        unique, monotonic, and conforms to a determinable frequency; otherwise
        ``.freq`` is ``None``.

    Notes:
        FRED returns period-start dates, so the mapping yields start-anchored
        aliases (``MS``/``QS``/``YS``); a non-conforming candidate (a gapped
        series, or ``D`` against business-daily data) is skipped, not forced.
    """
    idx = pd.DatetimeIndex(dates, name="date")

    if not (idx.is_monotonic_increasing and idx.is_unique):
        return idx

    mapped = _pandas_frequency_converter(frequency)

    inferred = pd.infer_freq(idx) if len(idx) >= 3 else None

    for candidate in (mapped, inferred):
        if candidate:
            try:
                return pd.DatetimeIndex(dates, freq=candidate, name="date")

            except ValueError:
                continue

    return idx


def _columns_to_pandas(
    columns: dict[str, np.ndarray], index: str | None = None, frequency: str | None = None
) -> pd.DataFrame:
    """Build a pandas DataFrame from observation columns.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping.
        index (str | None): Column to set as the index. ``"date"`` yields a
            frequency-aware :class:`pandas.DatetimeIndex` (see
            :func:`_freq_aware_index`); any other name is set as a plain index;
            ``None`` keeps a default ``RangeIndex`` with all columns retained.
        frequency (str | None): The FRED frequency code, used only when
            ``index == "date"`` to attach the index frequency.

    Returns:
        pandas.DataFrame: The observations as a pandas frame.

    Notes:
        A pandas ``DatetimeIndex`` is ``datetime64[ns]``; day-resolution dates
        widen to midnight timestamps. For a non-unique date axis (vintage data),
        ``index="date"`` produces a non-unique index with ``freq=None``.
    """
    if index == "date":
        data = {k: v for k, v in columns.items() if k != "date"}

        return pd.DataFrame(data, index=_freq_aware_index(columns["date"], frequency))

    df = pd.DataFrame(columns)

    return df.set_index(index) if index is not None else df


def _columns_to_polars(columns: dict[str, np.ndarray]) -> pl.DataFrame:
    """Build a Polars DataFrame from observation columns.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping.

    Returns:
        polars.DataFrame: The observations as a Polars frame.

    Raises:
        OptionalDependencyError: If ``polars`` is not installed.

    Notes:
        Polars adopts the numpy buffers directly; no Arrow round-trip or pyarrow
        dependency is involved.
    """
    pl = _require_module("polars", "to_polars")

    return pl.DataFrame({k: v for k, v in columns.items()})


def _columns_to_dask(
    columns: dict[str, np.ndarray],
    npartitions: int = 1,
    index: str | None = None,
    frequency: str | None = None,
) -> dd.DataFrame:
    """Build a Dask DataFrame from observation columns.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping.
        npartitions (int): Number of Dask partitions. Defaults to ``1``.
        index (str | None): Forwarded to :func:`_columns_to_pandas` (e.g. ``"date"``).
        frequency (str | None): FRED frequency code, forwarded for index freq.

    Returns:
        dask.dataframe.DataFrame: The observations as a Dask frame, built from the
        intermediate pandas frame.

    Raises:
        OptionalDependencyError: If ``dask`` is not installed.
    """
    dd = _require_module("dask.dataframe", "to_dask", extra="dask")

    return dd.from_pandas(
        _columns_to_pandas(columns, index=index, frequency=frequency),
        npartitions=npartitions,
    )


def _columns_to_cudf(columns: dict[str, np.ndarray], index: str | None = None) -> cudf.DataFrame:
    """Build a cuDF (GPU) DataFrame from observation columns.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping.
        index (str | None): ``"date"`` sets a cuDF ``DatetimeIndex`` (without
            ``freq`` — a CPU/statsmodels concern); any other name is set as the
            index; ``None`` retains all columns under a default index.

    Returns:
        cudf.DataFrame: The observations as a GPU frame.

    Raises:
        OptionalDependencyError: If ``cudf`` is not installed.

    Notes:
        GPU frames are for bulk device-side compute; the pandas ``freq`` attribute
        is intentionally not attached.
    """
    cudf = _require_module("cudf", "to_cudf")

    if index == "date":
        data = {k: v for k, v in columns.items() if k != "date"}

        df = cudf.DataFrame(data)

        df.index = cudf.DatetimeIndex(columns["date"])

        df.index.name = "date"

        return df

    df = cudf.DataFrame(columns)

    return df.set_index(index) if index is not None else df


def _columns_to_arrow(columns: dict[str, np.ndarray]) -> pa.Table:
    """Build a PyArrow Table from observation columns.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping.

    Returns:
        pyarrow.Table: The observations as an Arrow table — the interchange form
        behind ``__arrow_c_stream__`` and Arrow-native consumers.

    Raises:
        OptionalDependencyError: If ``pyarrow`` is not installed.
    """
    pa = _require_module("pyarrow", "to_arrow", extra="arrow")

    return pa.table(columns)


def _columns_to_series(
    values: np.ndarray, dates: np.ndarray, frequency: str | None, name: str
) -> pd.Series:
    """Build a single frequency-aware pandas Series from a value/date column pair.

    The point-series analogue of :func:`_columns_to_pandas`: values become the
    Series data, dates become a frequency-aware :class:`pandas.DatetimeIndex`
    (see :func:`_freq_aware_index`), and ``name`` labels the Series — yielding a
    statsmodels-ready univariate series.

    Args:
        values (numpy.ndarray): The ``float64`` value column (``NaN`` is missing).
        dates (numpy.ndarray): The ``datetime64`` date column; should be unique
            for ``.freq`` to attach.
        frequency (str | None): The FRED frequency code, used for the index freq.
        name (str): The Series name (typically the series id).

    Returns:
        pandas.Series: The observations as a freq-aware Series.
    """
    return pd.Series(values, index=_freq_aware_index(dates, frequency), name=name)


def _vintage_matrix(
    dates: np.ndarray, values: np.ndarray, realtime_start: np.ndarray, frequency: str | None
) -> pd.DataFrame:
    """Pivot vintage observations into a real-time data matrix.

    Produces a ``date x realtime_start`` matrix: rows are the unique observation
    dates (a frequency-aware :class:`pandas.DatetimeIndex`), columns are the
    vintage realtime-start dates, and each cell is the value current at that
    vintage. The ragged upper-right (``NaN``) is the expected real-time
    structure — a vintage has not observed dates released after it.

    Args:
        dates (numpy.ndarray): The ``datetime64`` observation-date column.
        values (numpy.ndarray): The ``float64`` value column.
        realtime_start (numpy.ndarray): The ``datetime64`` realtime-start column
            identifying each row's vintage.
        frequency (str | None): The FRED frequency code, used to attach freq to
            the (now unique) date index of the pivoted matrix.

    Returns:
        pandas.DataFrame: The real-time data matrix, indexed by date with one
        column per vintage.
    """
    wide = pd.DataFrame({"date": dates, "realtime_start": realtime_start, "value": values}).pivot(
        index="date", columns="realtime_start", values="value"
    )
    wide.index = _freq_aware_index(wide.index.values, frequency)
    return wide


def _pandas_frequency_converter(frequency: str | None) -> str | None:
    """Map a FRED frequency code to its pandas period-start offset alias.

    Args:
        frequency (str | None): A FRED frequency code (e.g. ``"m"``, ``"q"``,
            ``"wef"``), or ``None``.

    Returns:
        str | None: The pandas offset alias (``"MS"``, ``"QS"``, ``"W-FRI"``, …),
        or ``None`` if ``frequency`` is ``None`` or unrecognized.

    Notes:
        Monthly/quarterly/annual map to start-anchored aliases (``MS``/``QS``/``YS``)
        because FRED dates are period starts. Daily maps to ``D``; business-daily
        series are resolved by inference downstream (see :func:`_freq_aware_index`).

    Examples:
        >>> from fedfred._core._converters import _pandas_frequency_converter
        >>> _pandas_frequency_converter("m")
        'MS'
        >>> _pandas_frequency_converter(None) is None
        True
    """
    return _FRED_TO_PANDAS_FREQ.get(frequency or "")


def _identity_converter(
    parameter: str, value: object
) -> object:  # TODO: Do something with parameter input.
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
        value (object): A ``str``, ``date``, ``datetime``, or a list of those (``None`` entries are
            skipped).

    Returns:
        str: The original string, or a comma-separated string of ISO 8601 dates.

    Raises:
        TypeConversionError: If ``value`` (or any list element) is not a string, date, or datetime.

    Examples:
        >>> from datetime import date, datetime
        >>> from fedfred._core._converters import _comma_date_list_converter
        >>> _comma_date_list_converter("date_list_param", "2020-01-01")
        '2020-01-01'
        >>> _comma_date_list_converter(
        ...     "date_list_param",
        ...     [
        ...         datetime(2020, 1, 1),
        ...         date(2020, 2, 1),
        ...         "2020-03-01"
        ...     ]
        ... )
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


def _hashable_type_converter(data: CacheParameters | None) -> CacheKey | None:
    """Convert a parameter dict to a hashable, sorted tuple of items for use as a cache key.

    Args:
        data (CacheParameters | None): The request parameters, or ``None``.

    Returns:
        CacheKey | None: The items as a key-sorted tuple, or ``None`` if ``data`` is ``None``.

    Examples:
        >>> from fedfred._core._converters import _hashable_type_converter
        >>> _hashable_type_converter(
        ...     {
        ...         "param1": "value1",
        ...         "param2": 123,
        ...         "param3": None
        ...     }
        ... )
        (('param1', 'value1'), ('param2', 123), ('param3', None))

    Notes:
        Items are sorted by key so that dicts differing only in insertion order
        produce the same cache key.
    """
    if data is None:
        return None

    return tuple(sorted(data.items()))


def _dict_type_converter(hashable_data: CacheKey | None) -> CacheParameters | None:
    """Convert a hashable cache-key tuple back into a parameter dict.

    Args:
        hashable_data (CacheKey | None): The key-sorted item tuple, or ``None``.

    Returns:
        CacheParameters | None: The reconstructed dict, or ``None`` if ``hashable_data`` is
            ``None``.

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
        raise ConversionError(
            message="Expected string or None for short-code field.",
            parameter=value,
            expected="str | None",
            received=type(value).__name__,
        )

    return value.lower()
