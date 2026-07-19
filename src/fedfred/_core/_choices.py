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
"""Allowed-value sets for FRED, ALFRED, and GeoFRED request parameters.

Each constant is the set of permitted values for one API parameter — the
controlled vocabulary that the choice validators (``_ChoiceValidator`` /
``_StrChoiceValidator``) check membership against. Naming the data ``_choices``
keeps it paired with the validators that enforce it: a value is valid iff it is
a member of the corresponding set.

The sets are plain :class:`set` instances, chosen for O(1) membership rather than
:class:`enum.Enum`; they are reference data and are never mutated at runtime.
:data:`FRED_FREQUENCIES` is derived from the keys of
:data:`fedfred._core._mappings._FRED_TO_PANDAS_FREQ`, so the accepted frequency
codes and their pandas-alias mapping cannot drift apart; the remaining sets are
authored directly from the FRED and GeoFRED API documentation.

Constants:
    FRED_FREQUENCIES: Valid ``frequency`` codes (derived from the freq-alias map).
    FRED_UNITS: Valid ``units`` transforms.
    SORT_ORDERS: Valid ``sort_order`` values.
    AGGREGATION_METHODS: Valid ``aggregation_method`` values.
    OUTPUT_TYPES: Valid ``output_type`` values.
    FRED_ORDER_BY: Valid ``order_by`` fields.
    GEOFRED_REGION_TYPES: Valid GeoFRED region-type values.2

See Also:
    - :mod:`fedfred._core._validators`: The choice validators that consult these sets.
    - :mod:`fedfred._core._registries`: The parameter specs that bind each set to a parameter.

References:
    - FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from typing import get_args

from ._mappings import _FRED_TO_PANDAS_FREQ
from ._types import AuthStyle, Service

FRED_FREQUENCIES: set[str] = set(_FRED_TO_PANDAS_FREQ.keys())
"""Valid ``frequency`` values for FRED API parameters."""

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
"""Valid ``units`` values for FRED API parameters."""

SORT_ORDERS: set[str] = {"asc", "desc"}
"""Valid ``sort_order`` values for FRED API parameters."""

AGGREGATION_METHODS: set[str] = {"sum", "avg", "eop"}
"""Valid ``aggregation_method`` values for FRED API parameters."""

OUTPUT_TYPES: set[int] = {1, 2, 3, 4}
"""Valid ``output_type`` values for FRED API parameters."""

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
"""Valid ``order_by`` values for FRED API parameters."""

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
"""Valid region-type values for GeoFRED API parameters."""

_VALID_DATAFRAME_BACKENDS = ("pandas", "polars", "dask", "fedfred")
"""Valid dataframe backend options for the fedfred package."""

_VALID_GEODATAFRAME_BACKENDS = ("geopandas", "polars-st", "dask-geopandas", "fedfred")
"""Valid geodataframe backend options for the fedfred package."""

_VALID_AUTH_STYLES: frozenset[str] = frozenset(get_args(AuthStyle.__value__))
"""Runtime validation set for :attr:`EndpointSpec.auth`, derived from :data:`AuthStyle` so the two
cannot drift."""

_VALID_SERVICES: frozenset[str] = frozenset(get_args(Service.__value__))
"""Runtime validation set for :attr:`EndpointSpec.service`, derived from
:data:`fedfred.settings.Service` so the two cannot drift."""
