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



_GEOFRED_BASE_PARAMETERS: dict[str, str] = {
    'file_type': 'json',
}
"""Default query parameters for GeoFRED requests.

Distinct object from :data:`_FRED_BASE_PARAMETERS` by design — sharing
parameter dicts across services would invite cross-service corruption if
the transport layer ever wrote through the spec. The ``api_key``
parameter is injected at request time per :attr:`EndpointSpec.auth`.
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