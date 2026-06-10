# filepath: /src/fedfred/_core/_urls.py
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
"""URL component constants for the fedfred core package.

The atomic pieces from which St. Louis Fed API request URLs are composed: the shared
host origin, the per-service path prefixes (FRED/ALFRED, GeoFRED, FRASER), and the
per-resource path segments. The endpoint maps in :mod:`._mappings` concatenate these
into endpoint path fragments, and the builders prepend the host to form absolute
URLs.

The lowest-level request vocabulary — pure constants, no logic — imported upward and
importing nothing themselves. Composite or endpoint-specific fragments (e.g.
``/category/related_tags``) are assembled by the consumers from these atoms rather
than defined here.

Constants:
    _ST_LOUIS_FED_BASE_URL: The shared host origin for every service.
    _FRED_PATH / _GEOFRED_PATH / _FRASER_PATH: Per-service path prefixes.
    _CATEGORY_PATH, _RELEASE_PATH, _SERIES_PATH, …: Per-resource path segments.

See Also:
    - :mod:`fedfred._core._mappings`: Composes these atoms into endpoint path maps.
    - :mod:`fedfred._core._builders`: Prepends the host to form absolute endpoint URLs.

References:
    - FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

_ST_LOUIS_FED_BASE_URL: str = "https://api.stlouisfed.org"
"""Host portion of every St. Louis Fed API URL. All endpoints under FRED, ALFRED, GeoFRED, and
FRASER share this base."""

_FRED_PATH: str = "/fred"
"""URL path prefix for FRED endpoints (also used by ALFRED, which shares the FRED endpoint surface).
"""

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
