

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, get_args

from ..settings import Service

AuthStyle = Literal[
    "api_key_param",
    "bearer_header",
    "api_key_header",
    "none"
]
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
"""Runtime validation set for :attr:`EndpointSpec.auth`, derived from :data:`AuthStyle` so the two
cannot drift."""

_VALID_SERVICES: frozenset[str] = frozenset(get_args(Service))
"""Runtime validation set for :attr:`EndpointSpec.service`, derived from :data:
`fedfred.settings.Service` so the two cannot drift."""

ParameterConverter = Callable[[str, object], object]
"""Type alias for a scalar parameter converter: takes a parameter name and a raw value, returns the
API-ready value."""

_ResponseShape = Literal[
    "list",
    "dict_or_list"
]
