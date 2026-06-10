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
"""Runtime registries for the fedfred core package.

The authoritative, pre-built catalogs the request path looks up — distinct from the
raw lookup tables in :mod:`._mappings`, which are *input* to construction. Two kinds
live here, both assembled once at import time and read (never rebuilt) per request:

* :data:`_ENDPOINT_REGISTRY` — service-keyed endpoint specifications, built from the
  URL atoms, defaults, and endpoint maps via :mod:`._builders` (FRED/ALFRED) and the
  GeoFRED/FRASER comprehensions below. Resolution is a pure two-key lookup.
* :data:`FRED_PARAMETER_SPECS` / :data:`GEOFRED_PARAMETER_SPECS` /
  :data:`FRASER_PARAMETER_SPECS` — per-service, per-parameter converter/validator
  specifications, consulted by :mod:`._preparers` to convert and validate request
  parameters.

Everything here is data assembled from the lower vocabulary and validated at build
time (:meth:`EndpointSpec.__post_init__`, :class:`ParameterSpec`), so the request
path is lookup-only.

Constants:
    _ENDPOINT_REGISTRY: Service -> endpoint name -> EndpointSpec.
    FRED_PARAMETER_SPECS: FRED/ALFRED parameter name -> ParameterSpec.
    GEOFRED_PARAMETER_SPECS: GeoFRED parameter name -> ParameterSpec.
    FRASER_PARAMETER_SPECS: FRASER parameter name -> ParameterSpec.

See Also:
    - :mod:`fedfred._core._builders`: Constructs the endpoint specs registered here.
    - :mod:`fedfred._core._resolvers`: Looks up :data:`_ENDPOINT_REGISTRY` at request time.
    - :mod:`fedfred._core._preparers`: Consumes the ``*_PARAMETER_SPECS``.

References:
    - FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from typing import Any

from ..settings import Service
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
from ._preparers import (
    _prepare_fraser_parameters,
    _prepare_fred_parameters,
    _prepare_geofred_parameters,
)
from ._specs import EndpointSpec, ParameterSpec
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

Built (and therefore validated by :meth:`EndpointSpec.__post_init__`) once
at import time. Resolution via :func:`_resolve_endpoint` is a pure two-key
lookup; no :class:`EndpointSpec` is ever constructed on the request path.

Layout::

    _ENDPOINT_REGISTRY[<service>][<endpoint_name>] -> EndpointSpec

Endpoint names are unique per service, not globally. The same name (for
example ``"get_series_observations"``) deliberately resolves under both
``"fred"`` and ``"alfred"`` — the spec it returns will carry the correct
``service`` field so the rest of the stack can branch on it.
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
"""Per-parameter specifications for FRED API requests, mapping each known parameter name to its
converter/validator handling."""

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
"""Per-parameter specifications for GeoFRED API requests, mapping each known parameter name to its
converter/validator handling."""

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
"""Per-parameter specifications for FRASER API requests, mapping each known parameter name to its
converter/validator handling."""

FRED_PREPARATION_FUNCTIONS: dict[str, Any] = {  # TODO: refactor to avoid import cycle
    "fred": _prepare_fred_parameters,
    "geofred": _prepare_geofred_parameters,
    "fraser": _prepare_fraser_parameters,
}
"""Mapping of lowercase service name to its parameter-preparation function."""
