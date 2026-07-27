# filepath: /src/fedfred/_core/_defaults.py
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
"""Default request parameters for FRED, ALFRED, GeoFRED, and FRASER.

Each constant is the baseline parameter set every request to that service starts
from — the values an :class:`~fedfred._core._specs.EndpointSpec` carries by
default, onto which the parameter-preparation layer merges the per-call params.
Named by role (defaults) rather than container type (dict): reference data, not a
lookup table.

Design notes:
    Immutability by convention. Each dict is shared by every spec for its service
    and must never be mutated through the spec. The transport/preparation layer
    *reads* it and composes a fresh per-request parameter set; it never writes
    through to the default. Treat these as frozen.

    Distinct object per service. ``_FRED_BASE_PARAMETERS``,
    ``_GEOFRED_BASE_PARAMETERS``, and ``_FRASER_BASE_PARAMETERS`` are separate
    objects even where their contents coincide, so an accidental write-through in
    one service can never corrupt another. Object *identity* matters here as much
    as value.

    Auth is not a default. ``api_key`` / authorization is deliberately absent from
    every dict; it is injected at request time by the transport layer per
    :attr:`EndpointSpec.auth`, so the on-the-wire credential never lives in shared
    module state.

    v1 vs v2 spelling. FRED v1, ALFRED, and GeoFRED use ``file_type``; FRED v2
    (``/v2/`` endpoints) and FRASER use ``format``. The split constants capture
    that wire difference.

Constants:
    _FRED_BASE_PARAMETERS: Defaults for FRED v1 and ALFRED.
    _FRED_VERSION_TWO_BASE_PARAMETERS: Defaults for FRED v2 (``/v2/``) endpoints.
    _GEOFRED_BASE_PARAMETERS: Defaults for GeoFRED.
    _FRASER_BASE_PARAMETERS: Defaults for FRASER — query params for GET endpoints,
        POST body for ``post_key_request``.

See Also:
    - :class:`fedfred._core._specs.EndpointSpec`: Carries one of these as its
      default ``params`` (or ``payload`` for FRASER POST endpoints).
    - :mod:`fedfred._core._builders`: Stamps the right default set onto each spec.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from ._types import DataFrameBackend, GeoDataFrameBackend

_FRED_BASE_PARAMETERS: dict[str, str] = {
    "file_type": "json",
}
"""Default query parameters for FRED v1 and ALFRED requests.

Shared across every :class:`EndpointSpec` built for those services. ``api_key`` is deliberately
absent — the transport layer injects it at request time per :attr:`EndpointSpec.auth`. This is
a distinct dict object per service (see :data:`_GEOFRED_BASE_PARAMETERS`) and must never be
mutated through a spec; specs are expected to copy before adding request-specific parameters."""

_FRED_VERSION_TWO_BASE_PARAMETERS: dict[str, str] = {
    "format": "json",
}
"""Default query parameters for FRED v2 requests (endpoints under ``/v2/``).

Distinct from :data:`_FRED_BASE_PARAMETERS` because v2 names the response-format parameter
``format`` rather than ``file_type``. v2 authenticates with a bearer token, injected at request
time per :attr:`EndpointSpec.auth`; ``api_key`` is not a query parameter here."""

_GEOFRED_BASE_PARAMETERS: dict[str, str] = {
    "file_type": "json",
}
"""Default query parameters for GeoFRED requests.

A distinct dict object from :data:`_FRED_BASE_PARAMETERS` by design, even though the contents
are identical: sharing one dict across services would invite cross-service corruption if the
transport layer ever wrote through a spec. ``api_key`` is injected at request time per
:attr:`EndpointSpec.auth`."""

_FRASER_BASE_PARAMETERS: dict[str, str] = {
    "format": "json",
}
"""Default parameters for FRASER requests.

Used as query parameters for GET endpoints and as the POST body for the ``post_key_request``
endpoint. A distinct dict object from :data:`_FRED_VERSION_TWO_BASE_PARAMETERS` by design —
identical contents, but a shared dict would risk cross-service corruption. Authentication is
injected at request time per :attr:`EndpointSpec.auth`."""

_FRED_MAX_REQUESTS_PER_MINUTE: int = 120
"""FRED's documented per-minute request ceiling, in requests per minute.

Shared by GeoFRED and ALFRED because all three are served by the same St. Louis Fed backend
under one API key and count against a single limit. Seeds the FRED/GeoFRED/ALFRED rate-limit
bucket."""

_FRASER_MAX_REQUESTS_PER_MINUTE: int = 30
"""FRASER's per-minute request ceiling, in requests per minute.

Lower than FRED's; FRASER is a separate service with its own limit and its own rate-limit
bucket."""

_WINDOW_SECONDS: float = 60.0
"""Length of the rolling rate-limit window, in seconds.

The denominator the per-minute ceilings are measured against; a bucket admits at most its
``max_requests_per_minute`` within any trailing :data:`_WINDOW_SECONDS` span."""

_CONCURRENCY_DIVISOR: int = 10
"""Divisor mapping a bucket's per-minute ceiling to its baseline concurrency cap.

``max_requests_per_minute // _CONCURRENCY_DIVISOR`` gives the default number of in-flight
requests a bucket permits — e.g. 120/10 = 12 for FRED, 30/10 = 3 for FRASER. Caps concurrency
proportionally to the rate limit so a burst cannot immediately exhaust the window."""

_DEFAULT_DATAFRAME_BACKEND: DataFrameBackend = "pandas"
"""Default DataFrame backend when none is set via :func:`_set_dataframe_backend`.

The fallback returned by :func:`_get_dataframe_backend` / :func:`_resolve_dataframe_backend`
when no global backend and no explicit override is supplied. ``"pandas"`` is the only
non-optional frame backend, so it is always importable."""

_DEFAULT_GEODATAFRAME_BACKEND: GeoDataFrameBackend = "geopandas"
"""Default GeoDataFrame backend when none is set via :func:`_set_geodataframe_backend`.

The fallback returned by :func:`_get_geodataframe_backend` / :func:`_resolve_geodataframe_backend`
when no global backend and no explicit override is supplied."""
