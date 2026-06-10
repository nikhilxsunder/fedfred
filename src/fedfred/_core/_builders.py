# filepath: /src/fedfred/_core/_builders.py
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
"""Endpoint-spec builders for the fedfred core package.

Import-time factory functions that assemble :class:`~fedfred._core._specs.EndpointSpec`
instances from the lower-level request vocabulary — URL atoms (:mod:`._urls`),
default params/headers (:mod:`._defaults`), and the endpoint ``name -> path``
tables (:mod:`._mappings`) — and return them as per-service registries.

Builders *construct*; they do not resolve. Each runs once at import time to
populate the endpoint registry in :mod:`._registries`, so request-time
resolution is a pure lookup and never a fresh build. The dependency arrow is
one-way: a builder imports the vocabulary and the spec type, and its output is
consumed by the registry that the resolvers read — nothing here is invoked on
the request path.

Functions:
    _build_fred_style_specs: Build the endpoint-spec registry shared by the FRED
        and ALFRED services (identical specs, stamped with the service identity).

See Also:
    - :mod:`fedfred._core._specs`: The :class:`EndpointSpec` type assembled here.
    - :mod:`fedfred._core._registries`: The registry these builders populate.
    - :mod:`fedfred._core._resolvers`: The request-time consumer of that registry.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from ..settings import Service
from ._defaults import _FRED_BASE_PARAMETERS, _FRED_VERSION_TWO_BASE_PARAMETERS
from ._mappings import _FRED_ENDPOINT_MAP
from ._specs import EndpointSpec
from ._urls import _FRED_PATH, _ST_LOUIS_FED_BASE_URL


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
        service (Service): The service identity to stamp onto each spec — either ``"fred"`` or
            ``"alfred"``.

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
