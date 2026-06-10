


# URL Components
_ST_LOUIS_FED_BASE_URL: str = "https://api.stlouisfed.org"
"""Host portion of every St. Louis Fed API URL. All endpoints under FRED, ALFRED, GeoFRED, and FRASER share this base."""

_FRED_PATH: str = "/fred"
"""URL path prefix for FRED endpoints (also used by ALFRED, which shares the FRED endpoint surface)."""

_GEOFRED_PATH: str = "/geofred"
"""URL path prefix for GeoFRED endpoints."""

_FRASER_PATH: str = "/fraser"
"""URL path prefix for FRASER endpoints."""

_CATEGORY_PATH: str = "/category"
"""URL path segment for FRED category endpoints."""

_RELEASE_PATH: str = "/release"
"""URL path segment for FRED release endpoints."""

_SERIES_PATH: str = "/series"
"""URL path segment for FRED series endpoints."""

_SOURCE_PATH: str = "/source"
"""URL path segment for FRED source endpoints."""

_TAG_PATH: str = "/tags"
"""URL path segment for FRED tag endpoints."""

_RELATED_PATH: str = "/related"
"""URL path segment for FRED related-resource endpoints (category-related, related tags)."""

_DATES_PATH: str = "/dates"
"""URL path segment for FRED release-dates endpoints."""

_OBSERVATIONS_PATH: str = "/observations"
"""URL path segment for FRED observation endpoints."""

_SEARCH_PATH: str = "/search"
"""URL path segment for FRED search endpoints."""

_DATA_PATH: str = "/data"
"""URL path segment for GeoFRED data-retrieval endpoints."""

_TITLE_PATH: str = "/title"
"""URL path segment for FRASER title endpoints."""

_ITEM_PATH: str = "/item"
"""URL path segment for FRASER item endpoints."""

_TOC_PATH: str = "/toc"
"""URL path segment for FRASER table-of-contents endpoints."""

_AUTHOR_PATH: str = "/author"
"""URL path segment for FRASER author endpoints."""

_SUBJECT_PATH: str = "/subject"
"""URL path segment for FRASER subject endpoints."""

_THEME_PATH: str = "/theme"
"""URL path segment for FRASER theme endpoints."""

_TIMELINE_PATH: str = "/timeline"
"""URL path segment for FRASER timeline endpoints."""

_RECORD_PATH: str = "/records"
"""URL path segment for FRASER record endpoints (author/subject/theme records)."""