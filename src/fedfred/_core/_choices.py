# filepath: /src/fedfred/_core/_choices.py
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
"""Controlled vocabularies for request-parameter and configuration validation.

Each constant is the set of permitted values for one field — the vocabulary a validator
checks membership against. Naming the module ``_choices`` keeps the data paired with the
validators that enforce it: a value is valid iff it is a member of the corresponding set.
Three families live here:

API-parameter choices
    The permitted values for FRED, ALFRED, and GeoFRED request parameters
    (``frequency``, ``units``, ``sort_order``, ``aggregation_method``, ``output_type``,
    ``order_by``, ``region_type``). Consulted by the choice validators
    (``_ChoiceValidator`` / ``_StrChoiceValidator``). :data:`FRED_FREQUENCIES` is derived
    from the keys of :data:`fedfred._core._mappings._FRED_TO_PANDAS_FREQ` so the accepted
    codes and their pandas-alias mapping cannot drift; the rest are authored from the FRED
    and GeoFRED API documentation.

Backend choices
    The permitted DataFrame/GeoDataFrame backend names
    (:data:`_VALID_DATAFRAME_BACKENDS`, :data:`_VALID_GEODATAFRAME_BACKENDS`), consulted by
    the backend validators. Ordered tuples rather than sets: registration order is
    meaningful and the membership sets are tiny.

Type-derived validation sets
    :data:`_VALID_SERVICES` and :data:`_VALID_AUTH_STYLES`, computed from the
    :data:`Service` and :data:`AuthStyle` PEP 695 ``type`` aliases via
    ``get_args(alias.__value__)`` so the runtime check and the static type cannot drift.
    The ``.__value__`` unwrap is required — :func:`typing.get_args` returns ``()`` on a
    ``type`` alias itself.

The public API-parameter sets are plain :class:`set` instances, chosen for O(1) membership
over :class:`enum.Enum`; all constants here are reference data and are never mutated at
runtime.

Constants:
    FRED_FREQUENCIES: Permitted ``frequency`` codes (derived from the freq-alias map).
    FRED_UNITS: Permitted ``units`` transforms.
    SORT_ORDERS: Permitted ``sort_order`` values.
    AGGREGATION_METHODS: Permitted ``aggregation_method`` values.
    OUTPUT_TYPES: Permitted ``output_type`` values.
    FRED_ORDER_BY: Permitted ``order_by`` fields.
    GEOFRED_REGION_TYPES: Permitted GeoFRED ``region_type`` values.
    _VALID_DATAFRAME_BACKENDS: Permitted DataFrame backend names.
    _VALID_GEODATAFRAME_BACKENDS: Permitted GeoDataFrame backend names.
    _VALID_SERVICES: Service identities, derived from :data:`Service`.
    _VALID_AUTH_STYLES: Auth styles, derived from :data:`AuthStyle`.

See Also:
    - :mod:`fedfred._core._validators`: The validators that consult these sets.
    - :mod:`fedfred._core._types`: The :data:`Service` / :data:`AuthStyle` aliases the
      type-derived sets are computed from.
    - :mod:`fedfred._core._registries`: The parameter specs that bind each choice set to a
      parameter.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from typing import get_args

from ._mappings import _FRED_TO_PANDAS_FREQ
from ._types import AuthStyle, DataFrameBackend, GeoDataFrameBackend, Service

FRED_FREQUENCIES: set[str] = set(_FRED_TO_PANDAS_FREQ.keys())
"""Permitted ``frequency`` codes for FRED requests (e.g. ``"d"``, ``"w"``, ``"m"``, ``"q"``).

Derived from the keys of :data:`fedfred._core._mappings._FRED_TO_PANDAS_FREQ` so the accepted
codes and their pandas-alias mapping cannot drift apart."""

FRED_UNITS: set[str] = {
    "lin",
    "chg",
    "ch1",
    "pch",
    "pc1",
    "pca",
    "cch",
    "cca",
    "log",
}
"""Permitted ``units`` transforms for FRED requests.

The FRED data-value transformations: levels (``lin``), change (``chg``, ``ch1``), percent
change (``pch``, ``pc1``, ``pca``), compounded change (``cch``, ``cca``), and natural log
(``log``)."""

SORT_ORDERS: set[str] = {"asc", "desc"}
"""Permitted ``sort_order`` values for FRED requests: ascending or descending."""

AGGREGATION_METHODS: set[str] = {"sum", "avg", "eop"}
"""Permitted ``aggregation_method`` values for FRED requests: sum, average, or end-of-period,
applied when a series is frequency-aggregated."""

OUTPUT_TYPES: set[int] = {1, 2, 3, 4}
"""Permitted ``output_type`` values for FRED observation requests.

Selects the vintage layout: observations by realtime period (``1``), initial release plus
current (``2``), all vintages (``3``), or initial release only (``4``)."""

FRED_ORDER_BY: set[str] = {
    "series_id",
    "title",
    "units",
    "frequency",
    "seasonal_adjustment",
    "realtime_start",
    "realtime_end",
    "last_updated",
    "observation_start",
    "observation_end",
    "popularity",
    "group_popularity",
    "series_count",
    "created",
    "name",
    "release_id",
    "press_release",
    "group_id",
    "search_rank",
}
"""Permitted ``order_by`` fields for FRED requests.

The union of orderable fields across FRED endpoints; not every field is valid for every
endpoint, so the per-endpoint spec narrows this set further."""

GEOFRED_REGION_TYPES: set[str] = {
    "bea",
    "msa",
    "frb",
    "necta",
    "state",
    "country",
    "county",
    "censusregion",
    "censusdivision",
}
"""Permitted ``region_type`` values for GeoFRED requests.

The geographic aggregation levels GeoFRED supports, from national (``country``) down to
``county``, plus statistical regions (``bea``, ``msa``, ``frb``, ``necta``,
``censusregion``, ``censusdivision``)."""

_VALID_DATAFRAME_BACKENDS: frozenset[str] = frozenset(get_args(DataFrameBackend.__value__))
"""Permitted DataFrame backend names, validated against by :func:`_validate_dataframe_backend`.

Kept in registration order; ``"fedfred"`` selects the package's native columnar return type."""

_VALID_GEODATAFRAME_BACKENDS: frozenset[str] = frozenset(get_args(GeoDataFrameBackend.__value__))
"""Permitted GeoDataFrame backend names, validated against by
:func:`_validate_geodataframe_backend`.

Kept in registration order; ``"fedfred"`` selects the package's native columnar return type."""

_VALID_AUTH_STYLES: frozenset[str] = frozenset(get_args(AuthStyle.__value__))
"""Runtime validation set for :attr:`EndpointSpec.auth`.

Derived from :data:`AuthStyle` via ``get_args(AuthStyle.__value__)`` so the accepted auth
styles and the type alias cannot drift. Note the ``.__value__``: :data:`AuthStyle` is a PEP 695
``type`` alias, and :func:`typing.get_args` returns ``()`` on the alias itself — it must be
unwrapped first."""

_VALID_SERVICES: frozenset[str] = frozenset(get_args(Service.__value__))
"""Runtime validation set for :attr:`EndpointSpec.service`.

Derived from :data:`Service` via ``get_args(Service.__value__)`` so the accepted service
identities and the type alias cannot drift. As with :data:`_VALID_AUTH_STYLES`, the
``.__value__`` unwrap is required because :func:`typing.get_args` returns ``()`` on a PEP 695
``type`` alias."""
