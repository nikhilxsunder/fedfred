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
"""Value, frame, and cache-key converters for the fedfred core package.

Read-agnostic transformation helpers that sit between the wire and the model. Four families
live here, grouped by what they convert:

Parameter (wire) converters
    Normalize caller-supplied Python values into the string forms FRED expects on the wire —
    :func:`_date_parameter_converter`, :func:`_time_parameter_converter`,
    :func:`_semicolon_list_converter`, :func:`_comma_date_list_converter`, and the no-op
    :func:`_identity_converter`. All share the ``(parameter, value)`` signature so the
    preparation layer can dispatch them uniformly, and all raise
    :class:`~fedfred.exceptions.TypeConversionError` on an unsupported input type. Strings are
    trusted and passed through unvalidated; format validation is a separate concern.

Frame materializers
    Turn the observation columns (parallel numpy arrays) into a chosen return type:
    :func:`_columns_to_pandas` (reference backend and the intermediate the others build on),
    :func:`_columns_to_polars`, :func:`_columns_to_dask`, :func:`_columns_to_cudf`,
    :func:`_columns_to_arrow`, the univariate :func:`_columns_to_series`, and the vintage
    :func:`_vintage_matrix` (a ``date x realtime_start`` pivot). Backend selection is resolved
    upstream from the package settings; each optional backend is imported lazily via
    :func:`_require_module` and raises
    :class:`~fedfred.exceptions.OptionalDependencyError` when absent. Two helpers,
    :func:`_freq_aware_index` and :func:`_pandas_frequency_converter`, support the
    date-indexed cases by attaching a pandas frequency when the axis permits.

Cache-key converters
    Round-trip a parameter dict to a hashable, key-sorted tuple and back
    (:func:`_hashable_type_converter` / :func:`_dict_type_converter`) so cached request
    functions can key on parameters regardless of insertion order.

Model-payload converters
    Normalize decoded response fields before they populate model objects —
    :func:`_coerce_lower`, which lowercases FRED short codes to match the model's lowercase
    controlled vocabularies.

Only pandas and numpy are hard dependencies; every other frame backend is optional and
loaded on demand. GeoFRED/GeoDataFrame materialization is not handled here — it lives in the
geo-specific converter module.

See Also:
    - :mod:`fedfred._core._choices`: The controlled vocabularies :func:`_coerce_lower` targets.
    - :mod:`fedfred._core._loaders`: Provides :func:`_require_module` for the lazy backends.
    - :mod:`fedfred._core._preparers`: Dispatches the parameter converters when building requests.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from ..exceptions import (
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

    Frequency is a property of the observation-date interval, independent of revisions, so
    this backs every date-indexed conversion. Two candidates are tried in order: the mapped
    FRED alias (authoritative), then :func:`pandas.infer_freq` as a fallback. Each candidate is
    only *proposed* — it is applied by reconstructing the index with ``freq=candidate``, and a
    candidate the axis does not actually conform to raises ``ValueError`` internally and is
    skipped rather than forced. Attachment is attempted only on a unique, monotonic-increasing
    axis, so calling this on a vintage series' non-unique dates is safe: it returns ``freq=None``
    rather than raising.

    Args:
        dates (numpy.ndarray): A ``datetime64`` array of observation dates.
        frequency (str | None): The FRED frequency code (e.g. ``"m"``, ``"q"``), or ``None`` to
            rely on inference alone.

    Returns:
        pandas.DatetimeIndex: The date index (named ``"date"``), with ``.freq`` set when the
        axis is unique, monotonic-increasing, and conforms to a determinable frequency;
        otherwise ``.freq`` is ``None``.

    Notes:
        FRED returns period-start dates, so the mapped alias is start-anchored
        (``MS`` / ``QS`` / ``YS``); a non-conforming candidate — a gapped series, or ``D``
        against business-daily data — is skipped, not forced. Inference is attempted only with
        at least three points (:func:`pandas.infer_freq` needs three to establish an interval),
        so for one- or two-point axes only the mapped alias can supply a frequency; with
        ``frequency=None`` and fewer than three points, the result is unavoidably ``freq=None``.

    See Also:
        - :func:`_pandas_frequency_converter`: Maps the FRED code to the pandas offset alias
          tried first.
        - :func:`_columns_to_pandas`: Primary caller, for the ``index="date"`` case.
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
    """Materialize observation columns as a pandas DataFrame.

    The reference backend and the intermediate that :func:`_columns_to_dask` builds on. Index
    handling has three cases: ``"date"`` builds a frequency-aware
    :class:`pandas.DatetimeIndex` (see :func:`_freq_aware_index`) and drops the date column
    from the body; any other name is set as a plain index; ``None`` keeps a default
    ``RangeIndex`` with every column retained.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping.
        index (str | None): Column to set as the index. ``"date"`` yields a frequency-aware
            ``DatetimeIndex``; any other name is set as a plain index; ``None`` keeps a default
            ``RangeIndex`` with all columns retained.
        frequency (str | None): The FRED frequency code, used only when ``index == "date"`` to
            attach the index frequency; ignored otherwise.

    Returns:
        pandas.DataFrame: The observations as a pandas frame.

    Notes:
        A pandas ``DatetimeIndex`` is ``datetime64[ns]``, so day-resolution dates widen to
        midnight timestamps. For a non-unique date axis (vintage data), ``index="date"``
        produces a non-unique index with ``freq=None`` — a single frequency cannot be inferred
        from repeated dates.

    See Also:
        - :func:`_freq_aware_index`: Builds the frequency-aware index for the ``"date"`` case.
    """
    if index == "date":
        data = {k: v for k, v in columns.items() if k != "date"}

        return pd.DataFrame(data, index=_freq_aware_index(columns["date"], frequency))

    df = pd.DataFrame(columns)

    return df.set_index(index) if index is not None else df


def _columns_to_polars(columns: dict[str, np.ndarray]) -> pl.DataFrame:
    """Materialize observation columns as a Polars DataFrame.

    Polars has no notion of a frequency-aware or datetime index, so this takes no ``index`` or
    ``frequency`` argument — the date is an ordinary column like any other.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping.

    Returns:
        polars.DataFrame: The observations as a Polars frame.

    Raises:
        OptionalDependencyError: If ``polars`` is not installed.

    Notes:
        Polars adopts the numpy buffers directly; no Arrow round-trip or pyarrow dependency is
        involved.
    """
    pl = _require_module("polars", "to_polars")

    return pl.DataFrame({k: v for k, v in columns.items()})


def _columns_to_dask(
    columns: dict[str, np.ndarray],
    npartitions: int = 1,
    index: str | None = None,
    frequency: str | None = None,
) -> dd.DataFrame:
    """Materialize observation columns as a Dask DataFrame.

    Built by partitioning the pandas frame from :func:`_columns_to_pandas`, so ``index`` and
    ``frequency`` carry the same semantics as there (``"date"`` yields a frequency-aware
    ``DatetimeIndex``, etc.). The partitioning is a post-hoc split of an already-materialized
    pandas frame — this does not stream or lazily construct the data.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping.
        npartitions (int): Number of Dask partitions. Defaults to ``1``.
        index (str | None): Forwarded to :func:`_columns_to_pandas` (e.g. ``"date"``).
        frequency (str | None): FRED frequency code, forwarded for the index frequency.

    Returns:
        dask.dataframe.DataFrame: The observations as a Dask frame, built from the intermediate
        pandas frame.

    Raises:
        OptionalDependencyError: If ``dask`` is not installed.

    See Also:
        - :func:`_columns_to_pandas`: The intermediate frame this partitions.
    """
    dd = _require_module("dask.dataframe", "to_dask", extra="dask")

    return dd.from_pandas(
        _columns_to_pandas(columns, index=index, frequency=frequency),
        npartitions=npartitions,
    )


def _columns_to_cudf(columns: dict[str, np.ndarray], index: str | None = None) -> cudf.DataFrame:
    """Materialize observation columns as a cuDF (GPU) DataFrame.

    Mirrors :func:`_columns_to_pandas`'s index handling but takes no ``frequency``: a cuDF
    ``DatetimeIndex`` carries no pandas ``freq`` attribute, which is a CPU/statsmodels concern.
    ``"date"`` sets a cuDF ``DatetimeIndex`` named ``"date"`` and drops the date column; any
    other name is set as the index; ``None`` retains all columns under a default index.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping.
        index (str | None): ``"date"`` sets a cuDF ``DatetimeIndex`` (no ``freq``); any other
            name is set as the index; ``None`` retains all columns under a default index.

    Returns:
        cudf.DataFrame: The observations as a GPU frame.

    Raises:
        OptionalDependencyError: If ``cudf`` is not installed.

    Notes:
        GPU frames are for bulk device-side compute; the pandas ``freq`` attribute is
        intentionally not attached. The one-time host-to-device copy happens as cuDF ingests
        the numpy buffers.
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
    """Materialize observation columns as a PyArrow Table.

    The interchange form: a date is an ordinary column (no index concept in Arrow), so this
    takes neither ``index`` nor ``frequency``.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping.

    Returns:
        pyarrow.Table: The observations as an Arrow table — the interchange form behind
        ``__arrow_c_stream__`` and Arrow-native consumers.

    Raises:
        OptionalDependencyError: If ``pyarrow`` is not installed.
    """
    pa = _require_module("pyarrow", "to_arrow", extra="arrow")

    return pa.table(columns)


def _columns_to_series(
    values: np.ndarray, dates: np.ndarray, frequency: str | None, name: str
) -> pd.Series:
    """Materialize a value/date column pair as a single frequency-aware pandas Series.

    The point-series analogue of :func:`_columns_to_pandas`: values become the Series data,
    dates become a frequency-aware :class:`pandas.DatetimeIndex` (see :func:`_freq_aware_index`),
    and ``name`` labels the Series — yielding a statsmodels-ready univariate series.

    Args:
        values (numpy.ndarray): The ``float64`` value column, aligned to ``dates`` (``NaN`` is
            a missing observation).
        dates (numpy.ndarray): The ``datetime64`` date column, aligned to ``values``; must be
            unique for a frequency to attach to the index.
        frequency (str | None): The FRED frequency code, used for the index frequency.
        name (str): The Series name (typically the series id).

    Returns:
        pandas.Series: The observations as a frequency-aware Series.

    See Also:
        - :func:`_freq_aware_index`: Builds the frequency-aware index.
        - :func:`_columns_to_pandas`: The multi-column (DataFrame) analogue.
    """
    return pd.Series(values, index=_freq_aware_index(dates, frequency), name=name)


def _vintage_matrix(
    dates: np.ndarray, values: np.ndarray, realtime_start: np.ndarray, frequency: str | None
) -> pd.DataFrame:
    """Pivot vintage observations into a real-time (date x vintage) data matrix.

    Produces a ``date x realtime_start`` matrix: rows are the unique observation dates (a
    frequency-aware :class:`pandas.DatetimeIndex`), columns are the vintage realtime-start
    dates, and each cell is the value current as of that vintage. The ragged upper-right
    (``NaN``) is the expected real-time structure — a vintage cannot carry observation dates
    first released after it.

    The three arrays are parallel and positionally aligned: element ``i`` of each describes one
    vintage observation. Each ``(date, realtime_start)`` pair must be unique, which holds by
    construction for a well-formed vintage sequence; a duplicated pair makes the pivot
    ambiguous and raises (see Raises).

    Args:
        dates (numpy.ndarray): The ``datetime64`` observation-date column.
        values (numpy.ndarray): The ``float64`` value column, aligned to ``dates``.
        realtime_start (numpy.ndarray): The ``datetime64`` realtime-start column identifying
            each row's vintage, aligned to ``dates``.
        frequency (str | None): The FRED frequency code, used to attach a frequency to the
            (now unique) date index of the pivoted matrix. ``None`` or an unrecognized code
            leaves the index without an inferred frequency (see
            :func:`_pandas_frequency_converter`).

    Returns:
        pandas.DataFrame: The real-time data matrix — indexed by observation date, one column
        per vintage realtime-start, cells holding the value current at that vintage and
        ``NaN`` where a vintage had not yet observed a date.

    Raises:
        ValueError: If any ``(date, realtime_start)`` pair repeats; :meth:`pandas.DataFrame.pivot`
            rejects duplicate index/column combinations.

    Examples:
        >>> import numpy as np
        >>> from fedfred._core._converters import _vintage_matrix
        >>> dates = np.array(["2020-01-01", "2020-02-01", "2020-01-01"], dtype="datetime64[D]")
        >>> rt = np.array(["2020-02-15", "2020-02-15", "2020-03-15"], dtype="datetime64[D]")
        >>> vals = np.array([1.0, 2.0, 1.5])
        >>> matrix = _vintage_matrix(dates, vals, rt, "m")
        >>> matrix.shape
        (2, 2)
        >>> bool(np.isnan(matrix.iloc[1, 1]))  # 2020-02-01 unseen by the 2020-03-15 vintage
        True

    See Also:
        - :func:`_freq_aware_index`: Attaches the frequency-aware index to the pivoted rows.
        - :func:`_pandas_frequency_converter`: Maps ``frequency`` to the pandas offset alias.
    """
    wide = pd.DataFrame({"date": dates, "realtime_start": realtime_start, "value": values}).pivot(
        index="date", columns="realtime_start", values="value"
    )
    wide.index = _freq_aware_index(wide.index.values, frequency)
    return wide


def _pandas_frequency_converter(frequency: str | None) -> str | None:
    """Map a FRED frequency code to its pandas period-start offset alias.

    Looks the code up in :data:`_FRED_TO_PANDAS_FREQ`. ``None`` and unrecognized codes both
    yield ``None`` — the lookup collapses "no frequency requested" and "frequency not in the
    map" into a single miss, so callers that need to tell them apart must check ``frequency``
    themselves before calling.

    Args:
        frequency (str | None): A FRED frequency code (e.g. ``"m"``, ``"q"``, ``"wef"``), or
            ``None``.

    Returns:
        str | None: The pandas offset alias (``"MS"``, ``"QS"``, ``"W-FRI"``, …), or ``None``
        if ``frequency`` is ``None`` or not a recognized code.

    Notes:
        Monthly/quarterly/annual map to start-anchored aliases (``MS`` / ``QS`` / ``YS``)
        because FRED observation dates are period starts, not period ends — using the
        end-anchored aliases would shift every timestamp to the wrong boundary. Daily maps to
        ``D``; business-daily series are resolved by inference downstream (see
        :func:`_freq_aware_index`).

    Examples:
        >>> from fedfred._core._converters import _pandas_frequency_converter
        >>> _pandas_frequency_converter("m")
        'MS'
        >>> _pandas_frequency_converter(None) is None
        True

    See Also:
        - :data:`fedfred._core._mappings._FRED_TO_PANDAS_FREQ`: The code-to-alias map this
          consults, and the source of :data:`FRED_FREQUENCIES`.
    """
    return _FRED_TO_PANDAS_FREQ.get(frequency or "")


def _identity_converter(parameter: str, value: object) -> object:
    """Return ``value`` unchanged — the no-op member of the converter family.

    Every parameter converter shares the ``(parameter, value)`` signature so the preparation
    layer can dispatch them uniformly; identity is the case where a parameter needs no
    transformation and is passed through verbatim. ``parameter`` is accepted only to satisfy
    that shared signature and is deliberately ignored.

    Args:
        parameter (str): The parameter name. Unused; present for signature uniformity with the
            other converters.
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
    """Convert a ``str``, ``date``, or ``datetime`` to a ``YYYY-MM-DD`` string.

    A ``datetime`` is truncated to its date and a ``date`` is formatted as ISO 8601; a ``str``
    is trusted and passed through **unvalidated**, so a malformed string reaches the API
    as-is. ``datetime`` time-of-day components are discarded.

    Args:
        parameter (str): The parameter name, used only for error context.
        value (object): A ``str``, ``date``, or ``datetime`` value.

    Returns:
        str: The ISO 8601 date string. Strings pass through unchanged.

    Raises:
        TypeConversionError: If ``value`` is not a ``str``, ``date``, or ``datetime``.

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
    """Convert a ``str``, ``time``, or ``datetime`` to an ``HH:MM`` string.

    A ``datetime`` or ``time`` is formatted as 24-hour ``HH:MM`` (seconds and microseconds
    discarded); a ``str`` is trusted and passed through **unvalidated**.

    Args:
        parameter (str): The parameter name, used only for error context.
        value (object): A ``str``, ``time``, or ``datetime`` value.

    Returns:
        str: The ``HH:MM`` time string. Strings pass through unchanged.

    Raises:
        TypeConversionError: If ``value`` is not a ``str``, ``time``, or ``datetime``.

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
    """Convert a ``str`` or ``list[str]`` to a semicolon-separated string.

    A ``str`` is passed through unchanged; a ``list`` is joined on ``;`` after confirming
    every element is a ``str``. An empty list yields the empty string.

    Args:
        parameter (str): The parameter name, used only for error context.
        value (object): A ``str`` (passed through) or ``list[str]`` (joined on ``;``).

    Returns:
        str: The original string, or the list joined with semicolons.

    Raises:
        TypeConversionError: If ``value`` is neither a ``str`` nor a ``list``, or if any list
            element is not a ``str``. For a bad list, ``received`` reports the element types.

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

    A ``str`` is passed through; a single ``date``/``datetime`` is delegated to
    :func:`_date_parameter_converter`; a ``list`` is converted element-wise through the same
    helper, with ``None`` entries skipped. A list that is empty or all-``None`` yields the
    empty string. Backs FRED/ALFRED vintage-date parameters, which accept one or many dates.

    Args:
        parameter (str): The parameter name, used only for error context.
        value (object): A ``str``, ``date``, ``datetime``, or a list of those (``None`` entries
            are skipped).

    Returns:
        str: The original string, or a comma-separated string of ISO 8601 dates.

    Raises:
        TypeConversionError: If ``value`` is not a ``str``, ``date``, ``datetime``, or ``list``,
            or if any non-``None`` list element is not date-like (propagated from
            :func:`_date_parameter_converter`).

    Examples:
        >>> from datetime import date, datetime
        >>> from fedfred._core._converters import _comma_date_list_converter
        >>> _comma_date_list_converter("date_list_param", "2020-01-01")
        '2020-01-01'
        >>> _comma_date_list_converter(
        ...     "date_list_param",
        ...     [datetime(2020, 1, 1), date(2020, 2, 1), "2020-03-01"]
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
    """Convert a parameter dict into a hashable, key-sorted tuple for use as a cache key.

    Turns request parameters into a canonical ``((key, value), ...)`` tuple so equal
    parameter sets map to the same cache key regardless of insertion order. ``None`` passes
    through unchanged, representing an absent parameter set.

    Args:
        data (CacheParameters | None): The request parameters, or ``None``.

    Returns:
        CacheKey | None: The items as a tuple sorted by key, or ``None`` when ``data`` is
        ``None``.

    Examples:
        >>> from fedfred._core._converters import _hashable_type_converter
        >>> _hashable_type_converter({"param1": "value1", "param2": 123, "param3": None})
        (('param1', 'value1'), ('param2', 123), ('param3', None))

    Notes:
        Canonicalizing by sorted key is what makes the key order-independent: two dicts
        differing only in insertion order produce the same tuple. The result is hashable only
        if every value is itself hashable — parameter values are expected to be scalars
        (``str``, ``int``, ``None``); a non-hashable value would build a tuple that then
        fails when used as a cache key.

    See Also:
        - :func:`_dict_type_converter`: The inverse, reconstructing a dict from the tuple.
    """
    if data is None:
        return None

    return tuple(sorted(data.items()))


def _dict_type_converter(hashable_data: CacheKey | None) -> CacheParameters | None:
    """Reconstruct a parameter dict from a hashable cache-key tuple.

    The inverse of :func:`_hashable_type_converter`: rebuilds the ``key -> value`` mapping
    from the canonical tuple form. ``None`` passes through unchanged.

    Args:
        hashable_data (CacheKey | None): The key-sorted item tuple, or ``None``.

    Returns:
        CacheParameters | None: The reconstructed dict, or ``None`` when ``hashable_data`` is
        ``None``.

    Examples:
        >>> from fedfred._core._converters import _dict_type_converter
        >>> _dict_type_converter((('param1', 'value1'), ('param2', 123), ('param3', None)))
        {'param1': 'value1', 'param2': 123, 'param3': None}

    Notes:
        Round-trip is content-preserving but not order-preserving:
        ``_dict_type_converter(_hashable_type_converter(d))`` equals ``d`` by content, but its
        keys are in sorted order rather than ``d``'s original insertion order. Since dict
        equality ignores order, the two compare equal — the canonicalization is intentional.

    See Also:
        - :func:`_hashable_type_converter`: The inverse, producing the tuple from a dict.
    """
    if hashable_data is None:
        return None

    return dict(hashable_data)


# Model Converters
def _coerce_lower(value: str | None) -> str | None:
    """Normalize a short-code string to lowercase, passing ``None`` through unchanged.

    Used on FRED short-code payload fields (``sort_order``, ``units``, and similar) where the
    API may return mixed-case values but the model's controlled vocabularies are lowercase.
    ``None`` is a valid field value (absent/optional) and is preserved, so this can be applied
    uniformly to optional fields without a prior presence check.

    Args:
        value (str | None): A short-code payload field, or ``None`` if absent.

    Returns:
        str | None: ``value`` lowercased, or ``None`` when ``value`` is ``None``.

    Raises:
        TypeConversionError: If ``value`` is neither a ``str`` nor ``None``.

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
        raise TypeConversionError(
            message="Expected string or None for short-code field.",
            parameter=value,
            expected="str | None",
            received=type(value).__name__,
        )

    return value.lower()
