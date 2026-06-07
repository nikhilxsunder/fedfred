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


# Endpoint Specification Model
@dataclass(frozen=True, slots=True)
class EndpointSpec:
    """Immutable request specification for a single FRED-family API endpoint.

    Instances are pre-built into :data:`_ENDPOINT_REGISTRY` at import time
    and shared across all requests and threads for the life of the
    process. The dataclass is ``frozen=True`` so accidental field
    reassignment raises :class:`dataclasses.FrozenInstanceError`;
    ``slots=True`` cuts the per-instance memory cost and provides a small
    attribute-access speedup since the spec is read on every request.

    Attributes:
        service (Service): The owning service (``"fred"``, ``"alfred"``, ``"geofred"``, or ``"fraser"``).
        url (str): The absolute URL for the endpoint. FRASER endpoints with path parameters contain positional ``{}`` placeholders filled at request time via :meth:`str.format`.
        auth (AuthStyle): How the transport layer injects the API key at request time. Secrets are never stored on the spec itself.
        params (dict[str, str] | None): Default query parameters merged (copy-merge, never mutated) into each request. ``None`` when the endpoint takes no defaults.
        payload (dict[str, Any] | None): Default POST payload. ``None`` for GET endpoints.
        headers (dict[str, str] | None): Default headers, if any. ``None`` when the endpoint takes no custom headers.

    Examples:
        >>> from ._endpoints import _resolve_endpoint
        >>> spec = _resolve_endpoint("fred", "get_series_observations")
        >>> spec.service
        'fred'
        >>> spec.url
        'https://api.stlouisfed.org/fred/series/observations'
        >>> spec.params
        {'file_type': 'json'}
        >>> spec.auth
        'api_key_param'

    Notes:
        The ``params``/``payload``/``headers`` dicts are shared between
        specs built from the same base-parameter constants. ``frozen=True``
        does *not* deep-freeze them: consumers must copy-merge
        (``{**spec.params, ...}``) and never write through the spec. A
        single mutation in the transport layer would corrupt every other
        endpoint sharing the same default dict.
    """

    service: Service
    """The owning service identifier (``"fred"``, ``"alfred"``, ``"geofred"``, or ``"fraser"``)."""

    url: str
    """The absolute URL for the endpoint. May contain positional ``{}`` placeholders for FRASER path parameters filled at request time."""

    auth: AuthStyle = "api_key_param"
    """API-key injection style applied by the transport layer at request time. Defaults to ``"api_key_param"`` (FRED v1 / GeoFRED convention)."""

    params: dict[str, str] | None = None
    """Default query parameters copy-merged into each request to this endpoint, or ``None`` for endpoints with no defaults."""

    payload: dict[str, Any] | None = None
    """Default POST payload for endpoints that take a body, or ``None`` for GET endpoints."""

    headers: dict[str, str] | None = None
    """Default headers for requests to this endpoint, or ``None`` for endpoints that take no custom headers."""

    def __post_init__(self) -> None:
        """Validate the endpoint specification at construction time.

        Runs once per spec, at import time, because every instance lives
        in :data:`_ENDPOINT_REGISTRY` and is built during module load. A
        malformed spec therefore fails at ``import fedfred`` rather than
        on first request, which keeps the call-site code paths free of
        defensive shape checks.

        Raises:
            EndpointServiceError: If :attr:`service` is not a known :data:`fedfred.settings.Service` value.
            EndpointURLError: If :attr:`url` is empty, non-string, or does not start with ``https://``.
            EndpointAuthError: If :attr:`auth` is not a known :data:`AuthStyle` value.
            EndpointParametersError: If :attr:`params` is set but is not a :class:`dict`.
            EndpointPayloadError: If :attr:`payload` is set but is not a :class:`dict`.
            EndpointHeadersError: If :attr:`headers` is set but is not a :class:`dict`.

        Examples:
            >>> from ._endpoints import EndpointSpec
            >>> try:
            ...     EndpointSpec(service="frd", url="https://api.stlouisfed.org/fred")
            ... except Exception as exc:
            ...     print(type(exc).__name__)
            EndpointServiceError
        """
        if self.service not in _VALID_SERVICES:
            raise EndpointServiceError(
                f"EndpointSpec.service must be one of {sorted(_VALID_SERVICES)}, got {self.service!r}."
            )

        if not isinstance(self.url, str) or not self.url.strip():
            raise EndpointURLError("EndpointSpec.url must be a non-empty string.")

        if not self.url.startswith("https://"):
            raise EndpointURLError("EndpointSpec.url must start with 'https://'.")

        if self.auth not in _VALID_AUTH_STYLES:
            raise EndpointAuthError(
                f"EndpointSpec.auth must be one of {sorted(_VALID_AUTH_STYLES)}, got {self.auth!r}."
            )

        if self.params is not None and not isinstance(self.params, dict):
            raise EndpointParametersError("EndpointSpec.params must be a dictionary or None.")

        if self.payload is not None and not isinstance(self.payload, dict):
            raise EndpointPayloadError("EndpointSpec.payload must be a dictionary or None.")

        if self.headers is not None and not isinstance(self.headers, dict):
            raise EndpointHeadersError("EndpointSpec.headers must be a dictionary or None.")


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

# NOTE: base-parameter dicts are shared across all specs built from them and
# across the life of the process. Never mutate them; transport copy-merges.
# API keys are deliberately absent — injected at request time per spec.auth.
_FRED_BASE_PARAMETERS: dict[str, str] = {
    'file_type': 'json',
}
"""Default query parameters for FRED v1 and ALFRED requests.

Shared across every :class:`EndpointSpec` built for those services. The
``api_key`` parameter is deliberately absent and is injected by the
transport layer at request time per :attr:`EndpointSpec.auth`. Must never
be mutated through the spec — see the module-level design notes.
"""

_FRED_VERSION_TWO_BASE_PARAMETERS: dict[str, str] = {
    'format': 'json',
}
"""Default query parameters for FRED v2 requests (endpoints under ``/v2/``).

Distinct from :data:`_FRED_BASE_PARAMETERS` because v2 uses ``format``
rather than ``file_type``. Bearer authorization is injected at request
time per :attr:`EndpointSpec.auth`.
"""

## GeoFRED
_GEOFRED_ENDPOINT_MAP: dict[str, str] = {
    "get_shape_files": "/shapes/file",
    "get_series_group": f"{_SERIES_PATH}/group",
    "get_series_data": f"{_SERIES_PATH}{_DATA_PATH}",
    "get_regional_data": f"/regional{_DATA_PATH}",
}
"""Mapping of GeoFRED endpoint names to their corresponding URL path fragments."""

_GEOFRED_BASE_PARAMETERS: dict[str, str] = {
    'file_type': 'json',
}
"""Default query parameters for GeoFRED requests.

Distinct object from :data:`_FRED_BASE_PARAMETERS` by design — sharing
parameter dicts across services would invite cross-service corruption if
the transport layer ever wrote through the spec. The ``api_key``
parameter is injected at request time per :attr:`EndpointSpec.auth`.
"""

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

_FRASER_BASE_PARAMETERS: dict[str, str] = {
    'format': 'json',
}
"""Default parameters for FRASER requests.

Used as query parameters for GET endpoints and as the POST body for the
``post_key_request`` endpoint. Distinct object from
:data:`_FRED_VERSION_TWO_BASE_PARAMETERS` by design — shared dicts across
services invite cross-service corruption.
"""

# Endpoint Registry
def _build_fred_style_specs(service: Service) -> dict[str, EndpointSpec]:
    """Build the per-endpoint :class:`EndpointSpec` registry for a FRED-style service.

    FRED and ALFRED share host, paths, and auth style; they differ only in
    vintage-parameter handling, which lives in the parameter-preparation
    layer rather than at the endpoint level. This helper produces the same
    set of specs for both, stamped with the appropriate ``service`` value
    so resolution returns the calling client's service identity.

    Endpoints whose path begins with ``/v2/`` use bearer-header auth and
    :data:`_FRED_VERSION_TWO_BASE_PARAMETERS`; all other endpoints use
    query-parameter auth and :data:`_FRED_BASE_PARAMETERS`.

    Args:
        service (Service): The service identity to stamp onto each spec — either ``"fred"`` or ``"alfred"``.

    Returns:
        dict[str, EndpointSpec]: Mapping of endpoint names to fully
        constructed, validated :class:`EndpointSpec` instances ready for
        registration into :data:`_ENDPOINT_REGISTRY`.

    Notes:
        Called once per FRED-style service at module import time. Not
        intended to be invoked at request time.
    """
    specs: dict[str, EndpointSpec] = {}

    for name, path in _FRED_ENDPOINT_MAP.items():
        if path.startswith("/v2/"):
            specs[name] = EndpointSpec(
                service=service,
                url=f"{_ST_LOUIS_FED_BASE_URL}{_FRED_PATH}{path}",
                auth="bearer_header",
                params=_FRED_VERSION_TWO_BASE_PARAMETERS,
            )
        else:
            specs[name] = EndpointSpec(
                service=service,
                url=f"{_ST_LOUIS_FED_BASE_URL}{_FRED_PATH}{path}",
                auth="api_key_param",
                params=_FRED_BASE_PARAMETERS,
            )

    return specs

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

# Endpoint Resolution
def _resolve_endpoint(service: Service, endpoint_name: str) -> EndpointSpec:
    """Resolve a ``(service, endpoint_name)`` pair to its pre-built specification.

    Two dict lookups, no allocation. The endpoint name is normalized by
    ``.strip().lower()`` before the second lookup so callers can pass
    whitespace-padded or differently cased names without each call site
    needing to defend the registry shape.

    Args:
        service (Service): The calling client's service identity (``"fred"``, ``"alfred"``, ``"geofred"``, or ``"fraser"``).
        endpoint_name (str): The endpoint name to resolve, e.g., ``"get_series_observations"``. Whitespace is trimmed and the name is lowercased before lookup.

    Returns:
        EndpointSpec: The immutable, import-time-validated specification.

    Raises:
        EndpointServiceError: If ``service`` is not a key in :data:`_ENDPOINT_REGISTRY`.
        EndpointUnsupportedError: If ``endpoint_name`` is not recognized within the resolved service's registry.

    Examples:
        >>> from ._endpoints import _resolve_endpoint
        >>> spec = _resolve_endpoint("fred", "get_series_observations")
        >>> spec.url
        'https://api.stlouisfed.org/fred/series/observations'
        >>> # FRED and ALFRED return separate specs that share most fields
        >>> # but carry different `service` identities.
        >>> spec is _resolve_endpoint("alfred", "get_series_observations")
        False

    Notes:
        Endpoint names are unique per service, not globally; the same name
        may resolve under multiple services by design (FRED and ALFRED
        share endpoint names, differing only in vintage-parameter handling
        at the parameter-preparation layer).
    """
    try:
        service_registry = _ENDPOINT_REGISTRY[service]
    except KeyError as exc:
        raise EndpointServiceError(
            f"Unknown service: {service!r}. Expected one of {sorted(_ENDPOINT_REGISTRY)}."
        ) from exc

    try:
        return service_registry[endpoint_name.strip().lower()]
    except KeyError as exc:
        raise EndpointUnsupportedError(
            f"Unsupported endpoint {endpoint_name!r} for service {service!r}."
        ) from exc
