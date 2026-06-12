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

_FRED_BASE_PARAMETERS: dict[str, str] = {
    "file_type": "json",
}
"""Default query parameters for FRED v1 and ALFRED requests.

Shared across every :class:`EndpointSpec` built for those services. The
``api_key`` parameter is deliberately absent and is injected by the
transport layer at request time per :attr:`EndpointSpec.auth`. Must never
be mutated through the spec — see the module-level design notes.
"""

_FRED_VERSION_TWO_BASE_PARAMETERS: dict[str, str] = {
    "format": "json",
}
"""Default query parameters for FRED v2 requests (endpoints under ``/v2/``).

Distinct from :data:`_FRED_BASE_PARAMETERS` because v2 uses ``format``
rather than ``file_type``. Bearer authorization is injected at request
time per :attr:`EndpointSpec.auth`.
"""

_GEOFRED_BASE_PARAMETERS: dict[str, str] = {
    "file_type": "json",
}
"""Default query parameters for GeoFRED requests.

Distinct object from :data:`_FRED_BASE_PARAMETERS` by design — sharing
parameter dicts across services would invite cross-service corruption if
the transport layer ever wrote through the spec. The ``api_key``
parameter is injected at request time per :attr:`EndpointSpec.auth`.
"""

_FRASER_BASE_PARAMETERS: dict[str, str] = {
    "format": "json",
}
"""Default parameters for FRASER requests.

Used as query parameters for GET endpoints and as the POST body for the
``post_key_request`` endpoint. Distinct object from
:data:`_FRED_VERSION_TWO_BASE_PARAMETERS` by design — shared dicts across
services invite cross-service corruption.
"""

_FRED_MAX_REQUESTS_PER_MINUTE: int = 120
"""Maximum requests per minute for the FRED API, shared by GeoFRED and ALFRED."""

_FRASER_MAX_REQUESTS_PER_MINUTE: int = 30
"""Maximum requests per minute for the FRASER API."""

_WINDOW_SECONDS: float = 60.0
"""Length of the rolling rate-limit window, in seconds."""

_CONCURRENCY_DIVISOR: int = 10
"""Divisor mapping a bucket's per-minute ceiling to its baseline concurrency cap."""
