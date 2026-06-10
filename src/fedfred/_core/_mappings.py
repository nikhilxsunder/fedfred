# filepath: /src/fedfred/_core/_mappings.py
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
"""Static lookup tables for the fedfred core package.

Raw ``key -> value`` mappings consumed as *input* by the builders and converters —
distinct from the runtime catalogs in :mod:`._registries`, which are looked up to
resolve a request. Two kinds live here: endpoint ``name -> URL path fragment``
tables, composed from the path atoms in :mod:`._urls` and fed to the spec builders
to construct :class:`EndpointSpec` instances; and the FRED frequency-code ->
pandas offset-alias table consulted by the frequency converter.

These are data, not behavior — read to build or convert other objects, never
invoked on the request path themselves.

Constants:
    _FRED_ENDPOINT_MAP: FRED/ALFRED endpoint name -> path fragment.
    _GEOFRED_ENDPOINT_MAP: GeoFRED endpoint name -> path fragment.
    _FRASER_ENDPOINT_MAP: FRASER endpoint name -> path fragment (``{}`` = path param).
    _FRED_TO_PANDAS_FREQ: FRED frequency code -> pandas period-start offset alias.

See Also:
    - :mod:`fedfred._core._urls`: The path atoms the endpoint maps compose.
    - :mod:`fedfred._core._builders`: Consumes the endpoint maps to build specs.
    - :mod:`fedfred._core._converters`: Consumes :data:`_FRED_TO_PANDAS_FREQ` for
      frequency-aware index construction.

References:
    - FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""
from __future__ import annotations

from ._urls import (
    _AUTHOR_PATH,
    _CATEGORY_PATH,
    _DATA_PATH,
    _DATES_PATH,
    _ITEM_PATH,
    _OBSERVATIONS_PATH,
    _RECORD_PATH,
    _RELATED_PATH,
    _RELEASE_PATH,
    _SEARCH_PATH,
    _SERIES_PATH,
    _SOURCE_PATH,
    _SUBJECT_PATH,
    _TAG_PATH,
    _THEME_PATH,
    _TIMELINE_PATH,
    _TITLE_PATH,
    _TOC_PATH,
)

_FRED_ENDPOINT_MAP: dict[str, str] = {
    # Category endpoints
    "get_category": _CATEGORY_PATH,
    "get_category_children": f"{_CATEGORY_PATH}/children",
    "get_category_related": f"{_CATEGORY_PATH}{_RELATED_PATH}",
    "get_category_series": f"{_CATEGORY_PATH}{_SERIES_PATH}",
    "get_category_tags": f"{_CATEGORY_PATH}{_TAG_PATH}",
    "get_category_related_tags": f"{_CATEGORY_PATH}{_RELATED_PATH}_{_TAG_PATH[1:]}",
    # Release Endpoints
    "get_releases": f"{_RELEASE_PATH}s",
    "get_releases_dates": f"{_RELEASE_PATH}s{_DATES_PATH}",
    "get_release": f"{_RELEASE_PATH}",
    "get_release_dates": f"{_RELEASE_PATH}{_DATES_PATH}",
    "get_release_series": f"{_RELEASE_PATH}{_SERIES_PATH}",
    "get_release_sources": f"{_RELEASE_PATH}{_SOURCE_PATH}s",
    "get_release_tags": f"{_RELEASE_PATH}{_TAG_PATH}",
    "get_release_related_tags": f"{_RELEASE_PATH}{_RELATED_PATH}_{_TAG_PATH[1:]}",
    "get_release_tables": f"{_RELEASE_PATH}/tables",
    "get_release_observations": f"/v2{_RELEASE_PATH}{_OBSERVATIONS_PATH}",
    # Series Endpoints
    "get_series": f"{_SERIES_PATH}",
    "get_series_categories": f"{_SERIES_PATH}{_CATEGORY_PATH[:-1]}ies",
    "get_series_observations": f"{_SERIES_PATH}{_OBSERVATIONS_PATH}",
    "get_series_release": f"{_SERIES_PATH}{_RELEASE_PATH}",
    "get_series_search": f"{_SERIES_PATH}{_SEARCH_PATH}",
    "get_series_search_tags": f"{_SERIES_PATH}{_SEARCH_PATH}{_TAG_PATH}",
    "get_series_search_related_tags": f"{_SERIES_PATH}{_SEARCH_PATH}{_RELATED_PATH}_{_TAG_PATH[1:]}",
    "get_series_tags": f"{_SERIES_PATH}{_TAG_PATH}",
    "get_series_updates": f"{_SERIES_PATH}/updates",
    "get_series_vintagedates": f"{_SERIES_PATH}/vintagedates",
    # Source Endpoints
    "get_sources": f"{_SOURCE_PATH}s",
    "get_source": f"{_SOURCE_PATH}",
    "get_source_releases": f"{_SOURCE_PATH}{_RELEASE_PATH}s",
    # Tag Endpoints
    "get_tags": f"{_TAG_PATH}",
    "get_related_tags": f"{_TAG_PATH}{_RELATED_PATH}",
    "get_tags_series": f"{_TAG_PATH}{_SERIES_PATH}",
}
"""Mapping of FRED endpoint names to their corresponding URL path fragments.

Used by :func:`_build_fred_style_specs` to construct :class:`EndpointSpec`
instances for both FRED and ALFRED (which share the FRED endpoint surface).
Entries whose path begins with ``/v2/`` use bearer-header auth and the v2
base parameters; all other entries use query-parameter auth and the v1
base parameters.
"""

_GEOFRED_ENDPOINT_MAP: dict[str, str] = {
    "get_shape_files": "/shapes/file",
    "get_series_group": f"{_SERIES_PATH}/group",
    "get_series_data": f"{_SERIES_PATH}{_DATA_PATH}",
    "get_regional_data": f"/regional{_DATA_PATH}",
}
"""Mapping of GeoFRED endpoint names to their corresponding URL path fragments.

Consumed when building the GeoFRED :class:`EndpointSpec` registry: each fragment
is appended to the GeoFRED base URL to form the endpoint URL. All GeoFRED
endpoints use query-parameter (``api_key``) auth and
:data:`_GEOFRED_BASE_PARAMETERS`. Fragments reuse the shared path atoms from
:mod:`._urls` where applicable (``_SERIES_PATH``, ``_DATA_PATH``); endpoint-specific
segments (``/shapes/file``, ``/group``, ``/regional``) are spelled inline.
"""

_FRASER_ENDPOINT_MAP: dict[str, str] = {
    # API key endpoints
    "post_key_request": "/api-key",
    # Titles endpoints - requires title_id
    "get_single_title": f"{_TITLE_PATH}/{{}}",
    "get_all_title_items": f"{_TITLE_PATH}/{{}}{_ITEM_PATH}s",
    "get_single_title_table_of_contents": f"{_TITLE_PATH}/{{}}{_TOC_PATH}",
    # Items endpoints - requires item_id
    "get_single_item": f"{_ITEM_PATH}/{{}}",
    "get_single_item_table_of_contents": f"{_ITEM_PATH}/{{}}{_TOC_PATH}",
    # Table of contents endpoints - requires toc_id
    "get_table_of_contents": f"{_TOC_PATH}/{{}}",
    # Author endpoints - requires author_id
    "get_all_authors": f"{_AUTHOR_PATH}",
    "get_single_author": f"{_AUTHOR_PATH}/{{}}",
    "get_all_author_records": f"{_AUTHOR_PATH}/{{}}{_RECORD_PATH}",
    # Subjects endpoints - requires subject_id
    "get_single_subject": f"{_SUBJECT_PATH}/{{}}",
    "get_all_subjects": f"{_SUBJECT_PATH}",
    "get_all_subject_records": f"{_SUBJECT_PATH}/{{}}{_RECORD_PATH}",
    # Themes endpoints - requires theme_id
    "get_all_themes": f"{_THEME_PATH}",
    "get_single_theme": f"{_THEME_PATH}/{{}}",
    "get_all_theme_records": f"{_THEME_PATH}/{{}}{_RECORD_PATH}",
    # Timeline endpoints - requires timeline_id
    "get_single_timeline": f"{_TIMELINE_PATH}/{{}}",
    "get_all_timelines": f"{_TIMELINE_PATH}",
    "get_all_timeline_events": f"{_TIMELINE_PATH}/{{}}/events",
}
"""Mapping of FRASER endpoint names to their corresponding URL path fragments.

Positional ``{}`` placeholders are filled with path parameters
(``title_id``, ``item_id``, ``toc_id``, ``author_id``, ``subject_id``,
``theme_id``, ``timeline_id``) by the transport layer at request time via
:meth:`str.format`. Endpoints whose name begins with ``post_`` are POST
requests and use :data:`_FRASER_BASE_PARAMETERS` as the payload rather
than as query parameters.
"""

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
"""Mapping of FRED frequency codes to pandas period-start offset aliases.

Consulted by :func:`._converters._pandas_frequency_converter` (and through it
:func:`._converters._freq_aware_index`) to attach a frequency to a date index, and
by :data:`._choices.FRED_FREQUENCIES`, whose accepted-frequency set is derived from
these keys so the two cannot drift.

Monthly, quarterly, and annual map to start-anchored aliases (``MS``/``QS``/``YS``)
because FRED returns period-start dates; weekly "ending" codes map to anchored
weekly aliases (``wef`` -> ``W-FRI``); daily maps to ``D`` (business-daily series
are resolved by inference downstream). Unrecognized or ``None`` codes yield no
alias.
"""
