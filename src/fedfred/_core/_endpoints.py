# filepath: /src/fedfred/_core/_endpoints.py
#
# Copyright (c) 2025-2026 Nikhil Sunder
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
"""Internal endpoint resolution for the fedfred core package.

Endpoint specifications are immutable value objects (:class:`EndpointSpec`)
pre-instantiated into a service-keyed registry (:data:`_ENDPOINT_REGISTRY`)
at import time. Every spec is validated once in
:meth:`EndpointSpec.__post_init__`; resolution
(:func:`_resolve_endpoint`) is a total, typed, two-key lookup with no
per-request construction. Two design rules govern the module:

1. **Specs are pure data.** They carry the absolute URL, the default
   parameters/payload/headers, and the auth *style* (an enum-like
   :data:`AuthStyle` literal). They never carry secrets. The transport
   layer reads ``spec.auth`` at request time and pulls the corresponding
   API key from :mod:`fedfred.settings`, so :func:`fedfred.set_api_key`
   takes effect immediately and importing fedfred never requires a
   configured key.

2. **Default parameter dicts are shared and immutable by convention.**
   Multiple endpoint specs reference the same base-parameter dict
   (``_FRED_BASE_PARAMETERS``, ``_FRED_VERSION_TWO_BASE_PARAMETERS``,
   etc.). The dataclass is ``frozen=True`` but Python does not deep-freeze
   container fields; the transport layer must always copy-merge
   (``{**spec.params, **request_params}``) and never write through the
   spec, or one service's request will corrupt every other request
   targeting an endpoint that shares the same defaults.

Classes:
    EndpointSpec: Immutable request specification for a single API endpoint.

Functions:
    _resolve_endpoint: Two-key lookup resolving a service and endpoint name
        to its pre-built :class:`EndpointSpec`.

Notes:
    The endpoint name registry is populated from the per-service maps
    (:data:`_FRED_ENDPOINT_MAP`, :data:`_GEOFRED_ENDPOINT_MAP`,
    :data:`_FRASER_ENDPOINT_MAP`). FRED and ALFRED share host, paths, and
    auth style; they differ only in vintage-parameter handling, which lives
    in the parameter-preparation layer rather than at the endpoint level.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    Literal,
    get_args,
)

from ..exceptions import (
    # EndpointAuthError,
    EndpointHeadersError,
    EndpointParametersError,
    EndpointPayloadError,
    EndpointServiceError,
    EndpointUnsupportedError,
    EndpointURLError,
)
from ..settings import Service

__all__ = ["_resolve_endpoint",]

# Typing Aliases
AuthStyle = Literal["api_key_param", "bearer_header", "api_key_header", "none"]
"""How the transport layer injects the API key for an endpoint.

One of:

- ``"api_key_param"``: append ``api_key=<key>`` as a query parameter
  (FRED, ALFRED, GeoFRED v1 endpoints).
- ``"bearer_header"``: send ``Authorization: Bearer <key>`` (FRED v2
  endpoints under ``/v2/``).
- ``"api_key_header"``: send the key in a service-specific header (FRASER).
- ``"none"``: no auth (public endpoints).

The literal values double as the :class:`EndpointSpec.auth` field type.
"""

_VALID_AUTH_STYLES: frozenset[str] = frozenset(get_args(AuthStyle))
"""Runtime validation set for :attr:`EndpointSpec.auth`, derived from :data:`AuthStyle` so the two cannot drift."""

_VALID_SERVICES: frozenset[str] = frozenset(get_args(Service))
"""Runtime validation set for :attr:`EndpointSpec.service`, derived from :data:`fedfred.settings.Service` so the two cannot drift."""

# Endpoint Registry


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
