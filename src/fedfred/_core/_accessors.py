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
"""Read-side accessors for the core layer.

Functions that read a value out of the core without mutating it — the "get"
half of the package's read/write split. Two families live here, unified by what
they *do* (access a value) rather than the type they touch, which is why the
module is named ``_accessors`` rather than for any one data structure:

Columnar observation accessors
    Pure functions over the parallel ``datetime64[D]`` and ``float64`` numpy
    arrays backing an ``_ObservationSequence``. The sequence never materializes
    per-row objects up front, so these synthesize one Python-native scalar — or
    locate one row — on demand. They own no state, perform no I/O, depend only on
    numpy, and leave domain error handling to the calling model layer (see
    :func:`_first_date_index`).

Configuration accessors
    Functions that report current global configuration — the active API key and
    the DataFrame/GeoDataFrame backends. They are the read half of the
    set/clear/get triad (the write half lives in :mod:`fedfred._core._mutators`)
    and back the public ``get_*`` shims re-exported from :mod:`fedfred.settings`.
    They read the process-global state *owned by* :mod:`fedfred._core._registries`
    and validate service identity via :mod:`fedfred._core._validators`; unlike the
    ``_resolve_*`` functions they apply no explicit override, no environment
    fallback, and no re-validation of already-validated values.

The module owns no mutable state of its own: the columnar accessors are pure, and
the configuration accessors only read state that :mod:`fedfred._core._registries`
holds. Mutation and full precedence resolution are deliberately elsewhere
(``_mutators`` and ``_resolvers`` respectively), keeping this module strictly
read-only.

Functions:
    _cell_date: Materialize the observation date at a row index.
    _cell_value: Materialize the observation value at a row index (``NaN`` -> ``None``).
    _first_date_index: Locate the first row index matching an ISO date key.
    _get_api_key: Read the stored API key for a service, or ``None`` if unset.
    _get_dataframe_backend: Read the effective global DataFrame backend.
    _get_geodataframe_backend: Read the effective global GeoDataFrame backend.

See Also:
    - :class:`fedfred._internals._models._ObservationSequence`: The columnar
      container whose ``_make`` and ``_lookup_iso`` consume the observation accessors.
    - :mod:`fedfred._core._mutators`: The write half of the config triad
    (``_set_*`` / ``_clear_*``).
    - :mod:`fedfred._core._resolvers`: Full precedence resolution over the same globals.
    - :mod:`fedfred._core._registries`: Owns the process-global config state read here.

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

    Reads one cell of a ``datetime64[D]`` column and returns it as a native Python
    date. The day-resolution unit round-trips exactly: ``numpy.datetime64[D].item()``
    yields a :class:`datetime.date` (not a :class:`datetime.datetime`), so no spurious
    midnight time component is introduced and no timezone is attached.

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

    See Also:
        - :meth:`fedfred._internals._models._ObservationSequence._make`: Materializes a
          row and calls this accessor for its date field.
    """
    return dates[i].item()


def _cell_value(values: np.ndarray, i: int) -> float | None:
    """Materialize the observation value at row ``i`` as ``float`` or ``None``.

    Reads one cell of a ``float64`` column and maps the missing sentinel to ``None``.
    ``NaN`` is the column-layer encoding of a missing observation (FRED ``"."``);
    ``None`` is the object-layer encoding. Translating here is what keeps the two-layer
    contract intact: a materialized element never carries ``NaN``, so element equality
    and hashing stay sound — ``None == None`` holds, whereas ``NaN != NaN`` would
    silently break both.

    Args:
        values (numpy.ndarray): A 1-D ``float64`` column of observation values.
        i (int): The row index to read.

    Returns:
        float | None: The value at row ``i`` as a native ``float``, or ``None`` when
        that cell is ``NaN``.

    Examples:
        >>> import numpy as np
        >>> from fedfred._core._accessors import _cell_value
        >>> _cell_value(np.array([1.5, np.nan]), 0)
        1.5
        >>> _cell_value(np.array([1.5, np.nan]), 1) is None
        True

    See Also:
        - :meth:`fedfred._internals._models._ObservationSequence._make`: Materializes a
          row and calls this accessor for its value field.
    """
    v = values[i]

    return None if np.isnan(v) else float(v)


def _first_date_index(dates: np.ndarray, key: str) -> int | None:
    """Locate the first row whose date equals the ISO ``key``.

    Backs string indexing on ``_ObservationSequence`` (``obs["2020-01-01"]``) and
    date-keyed lookups. In a vintage sequence — where a single date recurs across
    realtime brackets — this returns the *first* matching row, in storage order.

    Parsing and domain error handling are kept separate: an unparseable ``key`` raises
    :class:`ValueError` from numpy's ``datetime64`` constructor, which the calling model
    layer maps to its own ``ModelError``. Keeping the translation upstream leaves this
    accessor free of model-domain exceptions.

    Args:
        dates (numpy.ndarray): A 1-D ``datetime64[D]`` column of observation dates.
        key (str): An ISO ``YYYY-MM-DD`` date string.

    Returns:
        int | None: The first row index whose date equals ``key``, or ``None`` if no
        row matches.

    Raises:
        ValueError: If ``key`` is not a parseable ISO date (propagated from
            :class:`numpy.datetime64`).

    Examples:
        >>> import numpy as np
        >>> from fedfred._core._accessors import _first_date_index
        >>> dates = np.array(["2020-01-01", "2020-02-01"], dtype="datetime64[D]")
        >>> _first_date_index(dates, "2020-02-01")
        1
        >>> _first_date_index(dates, "2019-01-01") is None
        True

    See Also:
        - :meth:`fedfred._internals._models._ObservationSequence._lookup_iso`: Consumes
          this index for string/date-keyed access.
    """
    target = np.datetime64(key, "D")

    idx = np.flatnonzero(dates == target)

    return int(idx[0]) if idx.size else None


def _get_api_key(service: Service = "fred") -> str | None:
    """Return the API key currently stored for a service, or ``None`` if unset.

    Reports only the in-memory global configured via :func:`_set_api_key`; unlike
    :func:`_resolve_api_key` it does **not** consult environment variables and does
    **not** raise when no key is present — an unconfigured service returns ``None``.
    This is the read half of the set/clear/get triad and backs the public
    :func:`fedfred.settings.get_api_key`. Service identity is validated first, so an
    unrecognized service is rejected rather than silently missing from the store.

    Args:
        service (Service): The service whose key to read. Defaults to ``"fred"``.

    Returns:
        str | None: The stored API key for ``service``, or ``None`` if none is set.

    Raises:
        TypeValidationError: If ``service`` is not a string.
        ValueValidationError: If ``service`` is not one of the recognized services.

    Examples:
        >>> from fedfred._core._mutators import _set_api_key, _clear_api_key
        >>> from fedfred._core._accessors import _get_api_key
        >>> _get_api_key("fred") is None  # doctest: +SKIP
        True
        >>> _set_api_key("my_key", "fred")  # doctest: +SKIP
        >>> _get_api_key("fred")  # doctest: +SKIP
        'my_key'
        >>> _clear_api_key("fred")  # doctest: +SKIP

    See Also:
        - :func:`_set_api_key`: Sets the value read here.
        - :func:`_clear_api_key`: Resets the value to ``None``.
        - :func:`_resolve_api_key`: Full precedence resolution (global, then env), which raises when
        nothing is configured.
    """
    _validate_service(service)

    return _GLOBAL_KEYS[service]


def _get_dataframe_backend() -> DataFrameBackend:
    """Return the effective global DataFrame backend, e.g. ``"pandas"``.

    Reports the process-global backend set via :func:`_set_dataframe_backend`,
    falling back to :data:`_DEFAULT_DATAFRAME_BACKEND` when none has been set. This is
    a plain read of current configuration — it applies no per-call override and
    performs no validation (the value was already validated when set) — and backs the
    public :func:`fedfred.settings.get_dataframe_backend`.

    Returns:
        DataFrameBackend: The active backend, or the package default if unset.

    Examples:
        >>> from fedfred._core._mutators import _set_dataframe_backend
        >>> from fedfred._core._accessors import _get_dataframe_backend
        >>> _get_dataframe_backend()  # doctest: +SKIP
        'pandas'
        >>> _set_dataframe_backend("polars")  # doctest: +SKIP
        >>> _get_dataframe_backend()  # doctest: +SKIP
        'polars'

    See Also:
        - :func:`_set_dataframe_backend`: Sets the value read here.
        - :func:`_resolve_dataframe_backend`: Resolves with an explicit override and validates the
        result.
    """
    return _GLOBAL_DATAFRAME_BACKEND or _DEFAULT_DATAFRAME_BACKEND


def _get_geodataframe_backend() -> GeoDataFrameBackend:
    """Return the effective global GeoDataFrame backend, e.g. ``"geopandas"``.

    Reports the process-global backend set via :func:`_set_geodataframe_backend`,
    falling back to :data:`_DEFAULT_GEODATAFRAME_BACKEND` when none has been set. This
    is a plain read of current configuration — it applies no per-call override and
    performs no validation (the value was already validated when set) — and backs the
    public :func:`fedfred.settings.get_geodataframe_backend`.

    Returns:
        GeoDataFrameBackend: The active backend, or the package default if unset.

    Examples:
        >>> from fedfred._core._mutators import _set_geodataframe_backend
        >>> from fedfred._core._accessors import _get_geodataframe_backend
        >>> _get_geodataframe_backend()  # doctest: +SKIP
        'geopandas'
        >>> _set_geodataframe_backend("polars-st")  # doctest: +SKIP
        >>> _get_geodataframe_backend()  # doctest: +SKIP
        'polars-st'

    See Also:
        - :func:`_set_geodataframe_backend`: Sets the value read here.
        - :func:`_resolve_geodataframe_backend`: Resolves with an explicit override and validates
        the result.
    """
    return _GLOBAL_GEODATAFRAME_BACKEND or _DEFAULT_GEODATAFRAME_BACKEND
