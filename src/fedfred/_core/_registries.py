# filepath: /src/fedfred/_core/_registries.py
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
"""Runtime registries and global state for the fedfred core package.

The authoritative catalogs and mutable state the request path consults — distinct from the raw
lookup tables in :mod:`._mappings`, which are *input* to construction. Three kinds live here,
and they do **not** share a lifecycle:

Endpoint registry
    :data:`_ENDPOINT_REGISTRY` — service-keyed endpoint specifications, assembled once at import
    time from the URL atoms, defaults, and endpoint maps via :mod:`._builders` (FRED/ALFRED) and
    the GeoFRED/FRASER comprehensions below, and validated at build time by
    :meth:`EndpointSpec.__post_init__`. Resolution is a pure two-key lookup.

Parameter-spec registries
    :data:`FRED_PARAMETER_SPECS` / :data:`GEOFRED_PARAMETER_SPECS` /
    :data:`FRASER_PARAMETER_SPECS` — per-service, per-parameter converter/validator specs,
    likewise built once at import and consulted by :mod:`._preparers`. Immutable reference data,
    like the endpoint registry.

Mutable global state
    :data:`_GLOBAL_KEYS`, :data:`_GLOBAL_DATAFRAME_BACKEND`, :data:`_GLOBAL_GEODATAFRAME_BACKEND`
    — the process-global API keys and backend selections, initialized empty and **reassigned or
    mutated at runtime** by :mod:`._mutators`, read by :mod:`._accessors` and :mod:`._resolvers`.
    Unlike the two registries above, these change after import; this module owns the canonical
    binding.

The two registries make the request path lookup-only (nothing is rebuilt per request). The
global state is not on the request path in the write direction — it is mutated only by explicit
configuration calls — but is read on every request to resolve keys and backends. A critical
access rule follows from that split: :data:`_GLOBAL_KEYS` is a dict mutated in place and is
safe to import by name, but the two scalar backend globals are **reassigned** by their setters
and must be read as module attributes (``_registries._GLOBAL_DATAFRAME_BACKEND``), never
imported by name — a name import binds the import-time ``None`` and never observes a later set.

Constants:
    _ENDPOINT_REGISTRY: Service -> endpoint name -> EndpointSpec (immutable, built at import).
    FRED_PARAMETER_SPECS: FRED/ALFRED parameter name -> ParameterSpec (immutable).
    GEOFRED_PARAMETER_SPECS: GeoFRED parameter name -> ParameterSpec (immutable).
    FRASER_PARAMETER_SPECS: FRASER parameter name -> ParameterSpec (immutable).
    _GLOBAL_KEYS: Service -> API key or ``None`` (mutable; dict, mutated in place).
    _GLOBAL_DATAFRAME_BACKEND: Selected DataFrame backend or ``None`` (mutable; scalar, reassigned).
    _GLOBAL_GEODATAFRAME_BACKEND: Selected GeoDataFrame backend or ``None`` (mutable; scalar,
        reassigned).

See Also:
    - :mod:`fedfred._core._builders`: Constructs the endpoint specs registered here.
    - :mod:`fedfred._core._resolvers`: Looks up :data:`_ENDPOINT_REGISTRY` and reads the globals.
    - :mod:`fedfred._core._preparers`: Consumes the ``*_PARAMETER_SPECS``.
    - :mod:`fedfred._core._mutators`: Writes the mutable global state.
    - :mod:`fedfred._core._accessors`: Reads the mutable global state.

References:
    - FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from ._builders import _build_fred_style_specs
from ._choices import (
    AGGREGATION_METHODS,
    FRED_FREQUENCIES,
    FRED_ORDER_BY,
    FRED_UNITS,
    GEOFRED_REGION_TYPES,
    OUTPUT_TYPES,
    SORT_ORDERS,
)
from ._converters import (
    _comma_date_list_converter,
    _date_parameter_converter,
    _semicolon_list_converter,
    _time_parameter_converter,
)
from ._defaults import _FRASER_BASE_PARAMETERS, _GEOFRED_BASE_PARAMETERS
from ._mappings import _FRASER_ENDPOINT_MAP, _GEOFRED_ENDPOINT_MAP
from ._specs import EndpointSpec, ParameterSpec
from ._types import DataFrameBackend, GeoDataFrameBackend, Service
from ._urls import _FRASER_PATH, _GEOFRED_PATH, _ST_LOUIS_FED_BASE_URL
from ._validators import (
    _validate_bool,
    _validate_choice,
    _validate_comma_date_list_string,
    _validate_hh_mm,
    _validate_nonempty_str,
    _validate_nonnegative_int,
    _validate_semicolon_list_string,
    _validate_series_id,
    _validate_str,
    _validate_str_choice,
    _validate_yyyy_mm_dd,
)

_ENDPOINT_REGISTRY: dict[Service, dict[str, EndpointSpec]] = {
    "fred": _build_fred_style_specs("fred"),
    "alfred": _build_fred_style_specs("alfred"),
    "geofred": {
        name: EndpointSpec(
            service="geofred",
            url=f"{_ST_LOUIS_FED_BASE_URL}{_GEOFRED_PATH}{path}",
            auth="api_key_param",
            params=_GEOFRED_BASE_PARAMETERS,
        )
        for name, path in _GEOFRED_ENDPOINT_MAP.items()
    },
    "fraser": {
        name: EndpointSpec(
            service="fraser",
            url=f"{_ST_LOUIS_FED_BASE_URL}{_FRASER_PATH}{path}",
            auth="api_key_header",
            params=None if name.startswith("post_") else _FRASER_BASE_PARAMETERS,
            payload=_FRASER_BASE_PARAMETERS if name.startswith("post_") else None,
        )
        for name, path in _FRASER_ENDPOINT_MAP.items()
    },
}
"""Service-keyed registry of pre-instantiated endpoint specifications.

Built — and therefore validated by :meth:`EndpointSpec.__post_init__` — once at import time.
FRED and ALFRED share :func:`_build_fred_style_specs`; GeoFRED and FRASER are built inline here,
with FRASER's ``post_``-prefixed endpoints carrying their base parameters as ``payload`` (POST
body) rather than ``params`` (query string). Resolution via :func:`_resolve_endpoint` is a pure
two-key lookup — no :class:`EndpointSpec` is constructed on the request path.

Layout::

    _ENDPOINT_REGISTRY[<service>][<endpoint_name>] -> EndpointSpec

Endpoint names are unique per service, not globally. The same name (e.g.
``"get_series_observations"``) deliberately resolves under both ``"fred"`` and ``"alfred"``;
the returned spec carries the correct ``service`` field so the rest of the stack can branch on
it.
"""

FRED_PARAMETER_SPECS: dict[str, ParameterSpec] = {
    "category_id": ParameterSpec(validator=_validate_nonnegative_int),
    "release_id": ParameterSpec(validator=_validate_nonnegative_int),
    "limit": ParameterSpec(validator=_validate_nonnegative_int),
    "offset": ParameterSpec(validator=_validate_nonnegative_int),
    "page": ParameterSpec(validator=_validate_nonnegative_int),
    "api_key": ParameterSpec(validator=_validate_nonempty_str),
    "search_text": ParameterSpec(validator=_validate_str),
    "tag_search_text": ParameterSpec(validator=_validate_str),
    "filter_value": ParameterSpec(validator=_validate_nonempty_str),
    "format": ParameterSpec(validator=_validate_str_choice({"json"})),
    "file_type": ParameterSpec(validator=_validate_str_choice({"json"})),
    "sort_order": ParameterSpec(validator=_validate_str_choice(SORT_ORDERS)),
    "order_by": ParameterSpec(validator=_validate_str_choice(FRED_ORDER_BY)),
    "filter_variable": ParameterSpec(
        validator=_validate_str_choice({"frequency", "units", "seasonal_adjustment"})
    ),
    "tag_names": ParameterSpec(
        converter=_semicolon_list_converter,
        validator=_validate_semicolon_list_string,
    ),
    "exclude_tag_names": ParameterSpec(
        converter=_semicolon_list_converter,
        validator=_validate_semicolon_list_string,
    ),
    "realtime_start": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "realtime_end": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "observation_start": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "observation_end": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "vintage_dates": ParameterSpec(
        converter=_comma_date_list_converter,
        validator=_validate_comma_date_list_string,
    ),
    "start_time": ParameterSpec(
        converter=_time_parameter_converter,
        validator=_validate_hh_mm,
    ),
    "end_time": ParameterSpec(
        converter=_time_parameter_converter,
        validator=_validate_hh_mm,
    ),
    "series_id": ParameterSpec(validator=_validate_series_id),
    "frequency": ParameterSpec(validator=_validate_str_choice(FRED_FREQUENCIES)),
    "units": ParameterSpec(validator=_validate_str_choice(FRED_UNITS)),
    "aggregation_method": ParameterSpec(validator=_validate_str_choice(AGGREGATION_METHODS)),
    "output_type": ParameterSpec(validator=_validate_choice(OUTPUT_TYPES)),
    "search_type": ParameterSpec(validator=_validate_str_choice({"full_text", "series_id"})),
    "include_releases_dates_with_no_data": ParameterSpec(validator=_validate_bool),
    "season": ParameterSpec(
        validator=_validate_str_choice({"seasonally_adjusted", "not_seasonally_adjusted"})
    ),
}
"""Per-parameter specifications for FRED (and ALFRED) requests.

Maps each modeled parameter name to its :class:`ParameterSpec` — the converter that normalizes
the value and the validator that checks it. Consumed by :func:`_prepare_fred_parameters` via
:func:`_prepare_parameters`. A name absent from this map is an *unknown* parameter: since the
FRED preparer runs with ``allow_unknown=True``, it passes through unconverted and unvalidated
rather than raising, so this map is the allowlist of parameters the package actively validates,
not the set it will accept."""

GEOFRED_PARAMETER_SPECS: dict[str, ParameterSpec] = {
    "api_key": ParameterSpec(validator=_validate_nonempty_str),
    "file_type": ParameterSpec(
        validator=_validate_str_choice({"json", "geojson", "shp", "kml", "gdb", "gpkg"})
    ),
    "shape": ParameterSpec(validator=_validate_str_choice(GEOFRED_REGION_TYPES)),
    "region_type": ParameterSpec(validator=_validate_str_choice(GEOFRED_REGION_TYPES)),
    "series_id": ParameterSpec(validator=_validate_series_id),
    "series_group": ParameterSpec(validator=_validate_nonempty_str),
    "date": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "start_date": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "aggregation_method": ParameterSpec(validator=_validate_str_choice(AGGREGATION_METHODS)),
    "units": ParameterSpec(validator=_validate_nonempty_str),
    "season": ParameterSpec(validator=_validate_str_choice({"NSA", "SA", "SSA", "SAAR", "NSAAR"})),
    "transformation": ParameterSpec(validator=_validate_str_choice(FRED_UNITS)),
}
"""Per-parameter specifications for GeoFRED requests.

Maps each modeled parameter name to its :class:`ParameterSpec` (converter + validator).
Consumed by :func:`_prepare_geofred_parameters` via :func:`_prepare_parameters`. As with the
FRED specs, names absent here pass through unvalidated under ``allow_unknown=True``. Note
GeoFRED's ``season`` vocabulary (``NSA`` / ``SA`` / ``SSA`` / ``SAAR`` / ``NSAAR``) differs from
FRED's, and both ``shape`` and ``region_type`` validate against the same
:data:`GEOFRED_REGION_TYPES` set."""

FRASER_PARAMETER_SPECS: dict[str, ParameterSpec] = {
    "limit": ParameterSpec(validator=_validate_nonnegative_int),
    "page": ParameterSpec(validator=_validate_nonnegative_int),
    "format": ParameterSpec(validator=_validate_str_choice({"json"})),
    "role": ParameterSpec(
        validator=_validate_str_choice(
            {"creator", "contributor", "editor", "repository", "uncertain", "subject"}
        )
    ),
}
"""Per-parameter specifications for FRASER requests.

Maps each modeled parameter name to its :class:`ParameterSpec` (converter + validator).
Consumed by :func:`_prepare_fraser_parameters` via :func:`_prepare_parameters`. The smallest of
the three spec maps — FRASER's request surface is mostly path-parameterized (see
:data:`_FRASER_ENDPOINT_MAP`), so few query parameters need modeling; names absent here pass
through unvalidated under ``allow_unknown=True``."""

_GLOBAL_KEYS: dict[Service, str | None] = {
    "fred": None,
    "fraser": None,
    "geofred": None,
    "alfred": None,
}
"""Process-global API-key store, one slot per service (``None`` when unset).

Mutated in place by :func:`_set_api_key` / :func:`_clear_api_key` and read by
:func:`_get_api_key` / :func:`_resolve_api_key`. Because it is a *dict* mutated in place (not
reassigned), importing the name into another module (`from ._registries import _GLOBAL_KEYS`)
is safe — the imported reference and this binding are the same object, so writes are visible
everywhere. Contrast the scalar backend globals below, which must be accessed as module
attributes."""

_GLOBAL_DATAFRAME_BACKEND: DataFrameBackend | None = None
"""Process-global selected DataFrame backend (``None`` = use :data:`_DEFAULT_DATAFRAME_BACKEND`).

Rebound by :func:`_set_dataframe_backend` and read by :func:`_get_dataframe_backend` /
:func:`_resolve_dataframe_backend`. Because it is a *scalar* that setters **reassign**, it must
be read as a module attribute — ``_registries._GLOBAL_DATAFRAME_BACKEND`` — never imported by
name. ``from ._registries import _GLOBAL_DATAFRAME_BACKEND`` binds the import-time value (``None``)
permanently and will never observe a later set; that is a live-bug trap, not a style choice."""

_GLOBAL_GEODATAFRAME_BACKEND: GeoDataFrameBackend | None = None
"""Process-global selected GeoDataFrame backend
(``None`` = use :data:`_DEFAULT_GEODATAFRAME_BACKEND`).

Rebound by :func:`_set_geodataframe_backend` and read by :func:`_get_geodataframe_backend` /
:func:`_resolve_geodataframe_backend`. Like :data:`_GLOBAL_DATAFRAME_BACKEND`, it is a scalar
the setter reassigns, so it must be accessed as ``_registries._GLOBAL_GEODATAFRAME_BACKEND`` —
importing the name binds the initial ``None`` and never sees updates."""
