# filepath: /src/fedfred/_core/_accessors.py
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
"""Columnar accessors for the observation model.

Pure functions that extract a single value or row position out of the numpy
column arrays backing an ``_ObservationSequence``. They are the read side of the
columnar core: the sequence stores parallel ``datetime64[D]`` and ``float64``
arrays and never materializes per-row objects up front, so these accessors
synthesize one Python-native scalar — or locate one row — on demand.

The module is named for what its functions *do* (access a value out of a column)
rather than the type they operate on. It holds no state, performs no I/O, and
depends only on numpy; domain error handling is deliberately left to the calling
model layer (see :func:`_first_date_index`).

Functions:
    _cell_date: Materialize the observation date at a row index.
    _cell_value: Materialize the observation value at a row index (``NaN`` -> ``None``).
    _first_date_index: Locate the first row index matching an ISO date key.

See Also:
    - :class:`fedfred._internals._models._ObservationSequence`: The columnar
      container whose ``_make`` and ``_lookup_iso`` consume these accessors.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""
from __future__ import annotations

from datetime import date

import numpy as np

from ._defaults import _DEFAULT_DATAFRAME_BACKEND, _DEFAULT_GEODATAFRAME_BACKEND
from ._registries import (
    _GLOBAL_DATAFRAME_BACKEND,
    _GLOBAL_GEODATAFRAME_BACKEND,
    _GLOBAL_KEYS,
)
from ._types import DataFrameBackend, GeoDataFrameBackend, Service
from ._validators import _validate_service


def _cell_date(dates: np.ndarray, i: int) -> date:
    """Materialize the observation date at row ``i`` as a :class:`datetime.date`.

    Reads one cell of a ``datetime64[D]`` column and converts it to a native
    Python date. Day-resolution storage round-trips exactly: numpy's ``.item()``
    yields a :class:`datetime.date` (not a :class:`datetime.datetime`) for the
    ``[D]`` unit, so no spurious time component is introduced.

    Args:
        dates (numpy.ndarray): A 1-D ``datetime64[D]`` column of observation dates.
        i (int): The row index to read.

    Returns:
        datetime.date: The date stored at row ``i``.

    Examples:
        >>> import numpy as np
        >>> from fedfred._core._accessors import _cell_date
        >>> _cell_date(np.array(["2020-01-01"], dtype="datetime64[D]"), 0)
        datetime.date(2020, 1, 1)
    """
    return dates[i].item()


def _cell_value(values: np.ndarray, i: int) -> float | None:
    """Materialize the observation value at row ``i`` as ``float`` or ``None``.

    Reads one cell of a ``float64`` column and maps the missing sentinel to
    ``None``. ``NaN`` is the column-layer encoding of a missing observation
    (FRED ``"."``); ``None`` is the object-layer encoding. Translating here is
    what keeps the two-layer contract intact — a materialized element never
    carries ``NaN``, so element equality and hashing stay sound (``None ==
    None`` holds, whereas ``NaN != NaN`` would silently break both).

    Args:
        values (numpy.ndarray): A 1-D ``float64`` column of observation values.
        i (int): The row index to read.

    Returns:
        float | None: The value at row ``i``, or ``None`` if that cell is ``NaN``.

    Examples:
        >>> import numpy as np
        >>> from fedfred._core._accessors import _cell_value
        >>> _cell_value(np.array([1.5, np.nan]), 0)
        1.5
        >>> _cell_value(np.array([1.5, np.nan]), 1) is None
        True
    """
    v = values[i]

    return None if np.isnan(v) else float(v)


def _first_date_index(dates: np.ndarray, key: str) -> int | None:
    """Locate the first row whose date equals the ISO ``key``.

    Backs string indexing on ``_ObservationSequence`` (``obs["2020-01-01"]``)
    and date-keyed lookups. For a vintage sequence — where a date recurs across
    realtime brackets — this returns the *first* matching row.

    Parsing and lookup are kept separate from domain error handling: an
    unparseable ``key`` raises :class:`ValueError` (from numpy), which the
    calling model layer maps to its own ``ModelError``, so this accessor stays
    free of model-domain exceptions.

    Args:
        dates (numpy.ndarray): A 1-D ``datetime64[D]`` column of observation dates.
        key (str): An ISO ``YYYY-MM-DD`` date string.

    Returns:
        int | None: The first row index whose date equals ``key``, or ``None``
        if no row matches.

    Raises:
        ValueError: If ``key`` is not a parseable ISO date.

    Examples:
        >>> import numpy as np
        >>> from fedfred._core._accessors import _first_date_index
        >>> dates = np.array(["2020-01-01", "2020-02-01"], dtype="datetime64[D]")
        >>> _first_date_index(dates, "2020-02-01")
        1
        >>> _first_date_index(dates, "2019-01-01") is None
        True
    """
    target = np.datetime64(key, "D")

    idx = np.flatnonzero(dates == target)

    return int(idx[0]) if idx.size else None


def _get_api_key(service: Service = "fred") -> str | None:
    """Get the currently configured global API key for a given service, if any.

    Args:
        service (Service): The service for which to get the API key. Defaults to "fred".

    Returns:
        Optional[str]: The resolved API key, or None if not configured.

    Raises:
        TypeValidationError: If the service is not a valid type.
        ValueValidationError: If the service is not recognized.
    """
    _validate_service(service)

    return _GLOBAL_KEYS[service]


def _get_dataframe_backend() -> DataFrameBackend:
    """Get the currently configured global dataframe backend. e.g. "pandas".

    Returns:
        DataFrameBackend: The resolved dataframe backend service.
    """
    return _GLOBAL_DATAFRAME_BACKEND or _DEFAULT_DATAFRAME_BACKEND


def _get_geodataframe_backend() -> GeoDataFrameBackend:
    """Get the currently configured global geodataframe backend e.g. "geopandas".

    Returns:
        GeoDataFrameBackend: The resolved geodataframe backend service.
    """
    return _GLOBAL_GEODATAFRAME_BACKEND or _DEFAULT_GEODATAFRAME_BACKEND
