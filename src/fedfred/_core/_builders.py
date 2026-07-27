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
instances from the lower-level request vocabulary — URL atoms (:mod:`._urls`), base
parameter sets (:mod:`._defaults`), and the endpoint ``name -> path`` tables
(:mod:`._mappings`) — and return them as per-service registries.

Builders *construct*; they do not resolve. Each runs once at import time to populate the
endpoint registry in :mod:`._registries`, so request-time resolution is a pure lookup and
never a fresh build. The dependency arrow is strictly one-way: a builder imports the
vocabulary and the spec type, its output is consumed by the registry the resolvers read,
and nothing here is called on the request path.

Functions:
    _build_fred_style_specs: Build the endpoint-spec registry shared by the FRED and ALFRED
        services (identical specs, stamped with the service identity).

See Also:
    - :mod:`fedfred._core._specs`: The :class:`EndpointSpec` type assembled here.
    - :mod:`fedfred._core._registries`: The registry these builders populate.
    - :mod:`fedfred._core._resolvers`: The request-time consumer of that registry.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from ..exceptions import EndpointSpecBuildError
from ._defaults import _FRED_BASE_PARAMETERS, _FRED_VERSION_TWO_BASE_PARAMETERS
from ._mappings import _FRED_ENDPOINT_MAP
from ._specs import EndpointSpec
from ._types import Service
from ._urls import _FRED_PATH, _ST_LOUIS_FED_BASE_URL


def _build_fred_style_specs(service: Service) -> dict[str, EndpointSpec]:
    """Build the per-endpoint :class:`EndpointSpec` registry for a FRED-style service.

    FRED and ALFRED share host, paths, and auth style, differing only in vintage-parameter
    handling — and that difference lives in the parameter-preparation layer, not at the
    endpoint level. So this helper produces the identical spec set for either, stamped with
    the given ``service`` so endpoint resolution reports the calling client's identity.

    Auth and base parameters are selected per endpoint by path: endpoints under ``/v2/`` use
    bearer-header auth with :data:`_FRED_VERSION_TWO_BASE_PARAMETERS`; all others use
    query-parameter auth with :data:`_FRED_BASE_PARAMETERS`.

    Args:
        service (Service): The service identity stamped onto each spec — ``"fred"`` or
            ``"alfred"``.

    Returns:
        dict[str, EndpointSpec]: Endpoint name to a fully constructed, validated
        :class:`EndpointSpec`, ready for registration into :data:`_ENDPOINT_REGISTRY`.

    Raises:
        EndpointSpecBuildError: If any endpoint's :class:`EndpointSpec` fails to construct or
            validate. The offending ``service`` and ``endpoint_name`` are attached and the
            underlying error is chained via ``raise ... from``.

    Notes:
        Called once per FRED-style service at module import time to populate the endpoint
        registry; it is not part of the request path.

    See Also:
        - :class:`fedfred._core._specs.EndpointSpec`: The spec object constructed here.
        - :data:`fedfred._core._registries._ENDPOINT_REGISTRY`: Where the returned specs are
          registered.
        - :func:`fedfred._core._resolvers._resolve_endpoint`: Reads the registry these specs
          populate.
    """
    specs: dict[str, EndpointSpec] = {}

    for name, path in _FRED_ENDPOINT_MAP.items():
        url = f"{_ST_LOUIS_FED_BASE_URL}{_FRED_PATH}{path}"

        try:
            if path.startswith("/v2/"):
                specs[name] = EndpointSpec(
                    service=service,
                    url=url,
                    auth="bearer_header",
                    params=_FRED_VERSION_TWO_BASE_PARAMETERS,
                )

            else:
                specs[name] = EndpointSpec(
                    service=service,
                    url=url,
                    auth="api_key_param",
                    params=_FRED_BASE_PARAMETERS,
                )

        except Exception as exc:
            raise EndpointSpecBuildError(
                message=(
                    f"Failed to build EndpointSpec for endpoint {name!r} in service {service!r}."
                ),
                service=service,
                endpoint_name=name,
                original_exception=exc,
            ) from exc

    return specs
