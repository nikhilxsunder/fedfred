# Service Components
## FRED (shared by ALFRED — same host, paths, and auth; ALFRED differs only in vintage parameters, handled by the parameter-preparation layer)
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

## GeoFRED
_GEOFRED_ENDPOINT_MAP: dict[str, str] = {
    "get_shape_files": "/shapes/file",
    "get_series_group": f"{_SERIES_PATH}/group",
    "get_series_data": f"{_SERIES_PATH}{_DATA_PATH}",
    "get_regional_data": f"/regional{_DATA_PATH}",
}
"""Mapping of GeoFRED endpoint names to their corresponding URL path fragments."""

## FRASER
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