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

The atomic pieces from which St. Louis Fed API request URLs are composed: the shared host origin
(:data:`_ST_LOUIS_FED_BASE_URL`), the per-service path prefixes (FRED/ALFRED, GeoFRED, FRASER),
and the per-resource path segments. The endpoint maps in :mod:`._mappings` concatenate the
segments into path fragments, and the spec builders (:mod:`._builders`, and the GeoFRED/FRASER
comprehensions in :mod:`._registries`) prepend the host and service prefix to form absolute
``https://`` URLs.

The lowest-level request vocabulary — pure constants, no logic, importing nothing. Composite and
endpoint-specific fragments (e.g. ``/category/related_tags``, ``/categories``) are assembled by
the consumers from these atoms, not defined here.

The segment atoms are inconsistently singular vs. plural (``/category`` and ``/source`` singular;
``/tags``, ``/series``, ``/records`` plural), so a few consumers re-stem them with string slicing
(``_CATEGORY_PATH[:-1] + "ies"``, ``_TAG_PATH[1:]``) or inline pluralization (``+ "s"``). Those
constructions are coupled to the exact spelling here: editing a segment can silently break a URL
built two modules away, with the failure surfacing only as a request-time 404. See the per-atom
notes.

Constants:
    _ST_LOUIS_FED_BASE_URL: The shared scheme + host for every service.
    _FRED_PATH / _GEOFRED_PATH / _FRASER_PATH: Per-service path prefixes.
    _CATEGORY_PATH, _RELEASE_PATH, _SERIES_PATH, …: Per-resource path segments.

See Also:
    - :mod:`fedfred._core._mappings`: Composes these atoms into endpoint path maps.
    - :mod:`fedfred._core._builders`: Prepends host + prefix to form absolute FRED/ALFRED URLs.
    - :mod:`fedfred._core._registries`: Forms absolute GeoFRED/FRASER URLs from these atoms.

References:
    - FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

_ST_LOUIS_FED_BASE_URL: str = "https://api.stlouisfed.org"
"""Scheme + host shared by every St. Louis Fed API URL.

The common prefix under which FRED, ALFRED, GeoFRED, and FRASER all live; the endpoint maps in
:mod:`._mappings` prepend it (via the service path) to each path fragment."""

_FRED_PATH: str = "/fred"
"""Service path prefix for FRED endpoints, also used by ALFRED (which shares the FRED endpoint
surface). Follows :data:`_ST_LOUIS_FED_BASE_URL`."""

_GEOFRED_PATH: str = "/geofred"
"""Service path prefix for GeoFRED endpoints. Follows :data:`_ST_LOUIS_FED_BASE_URL`."""

_FRASER_PATH: str = "/fraser"
"""Service path prefix for FRASER endpoints. Follows :data:`_ST_LOUIS_FED_BASE_URL`."""

_CATEGORY_PATH: str = "/category"
"""Path segment for FRED category endpoints.

Note: :mod:`._mappings` re-stems this by slicing (``_CATEGORY_PATH[:-1] + "ies"`` →
``/categories``); changing its spelling silently breaks that construction."""

_RELEASE_PATH: str = "/release"
"""Path segment for FRED release endpoints. Pluralized inline (``+ "s"``) for the ``releases``
listing endpoints in :mod:`._mappings`."""

_SERIES_PATH: str = "/series"
"""Path segment for FRED series endpoints (already plural; no pluralization applied)."""

_SOURCE_PATH: str = "/source"
"""Path segment for FRED source endpoints. Pluralized inline (``+ "s"``) for the ``sources``
listing endpoints."""

_TAG_PATH: str = "/tags"
"""Path segment for FRED tag endpoints (plural).

Note: :mod:`._mappings` slices off the leading ``/`` (``_TAG_PATH[1:]``) to build the
``related_tags`` suffixes; changing its spelling silently breaks that construction."""

_RELATED_PATH: str = "/related"
"""Path segment for FRED related-resource endpoints (category-related, related tags)."""

_DATES_PATH: str = "/dates"
"""Path segment for FRED release-dates endpoints."""

_OBSERVATIONS_PATH: str = "/observations"
"""Path segment for FRED observation endpoints."""

_SEARCH_PATH: str = "/search"
"""Path segment for FRED search endpoints."""

_DATA_PATH: str = "/data"
"""Path segment for GeoFRED data-retrieval endpoints."""

_TITLE_PATH: str = "/title"
"""Path segment for FRASER title endpoints."""

_ITEM_PATH: str = "/item"
"""Path segment for FRASER item endpoints."""

_TOC_PATH: str = "/toc"
"""Path segment for FRASER table-of-contents endpoints."""

_AUTHOR_PATH: str = "/author"
"""Path segment for FRASER author endpoints."""

_SUBJECT_PATH: str = "/subject"
"""Path segment for FRASER subject endpoints."""

_THEME_PATH: str = "/theme"
"""Path segment for FRASER theme endpoints."""

_TIMELINE_PATH: str = "/timeline"
"""Path segment for FRASER timeline endpoints."""

_RECORD_PATH: str = "/records"
"""Path segment for FRASER record endpoints (author/subject/theme records; plural)."""
