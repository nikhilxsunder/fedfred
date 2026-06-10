# filepath: /src/fedfred/_core/_resolvers.py
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
"""Request-time resolution for the fedfred core package.

The two lookups a client performs to turn a request into something executable:
:func:`_resolve_endpoint` maps a ``(service, endpoint_name)`` pair to its pre-built
:class:`EndpointSpec` — a pure registry lookup, no construction on the request path —
and :func:`_resolve_preparation_function` dispatches a service to its
parameter-preparation function and applies it, returning request-ready parameters.

Both sit above the registries and preparers they consult — they resolve the *where*
(endpoint) and the *what* (prepared params) — and form the request-side surface the
client calls.

Functions:
    _resolve_endpoint: Resolve a (service, endpoint name) to its EndpointSpec.
    _resolve_preparation_function: Dispatch a service to its preparer and apply it.

See Also:
    - :mod:`fedfred._core._registries`: Provides :data:`_ENDPOINT_REGISTRY`.
    - :mod:`fedfred._core._preparers`: Provides the preparation functions dispatched here.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..exceptions import UnknownServiceError, UnsupportedEndpointError
from ..settings import Service
from ._registries import _ENDPOINT_REGISTRY, FRED_PREPARATION_FUNCTIONS
from ._specs import EndpointSpec


def _resolve_endpoint(service: Service, endpoint_name: str) -> EndpointSpec:
    """Resolve a ``(service, endpoint_name)`` pair to its pre-built specification.

    Two dict lookups, no allocation. The endpoint name is normalized by
    ``.strip().lower()`` before the second lookup so callers can pass
    whitespace-padded or differently cased names without each call site
    needing to defend the registry shape.

    Args:
        service (Service): The calling client's service identity (``"fred"``, ``"alfred"``,
            ``"geofred"``, or ``"fraser"``).
        endpoint_name (str): The endpoint name to resolve, e.g., ``"get_series_observations"``.
            `Whitespace is trimmed and the name is lowercased before lookup.

    Returns:
        EndpointSpec: The immutable, import-time-validated specification.

    Raises:
        UnknownServiceError: If ``service`` is not a recognized service.
        UnsupportedEndpointError: If ``endpoint_name`` is not in the resolved service's
            registry.

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
        raise UnknownServiceError(
            message=f"Unknown service {service!r}.",
            service=service,
            known_services=tuple(sorted(_ENDPOINT_REGISTRY)),
            original_exception=exc,
        ) from exc

    try:
        return service_registry[endpoint_name.strip().lower()]
    except KeyError as exc:
        raise UnsupportedEndpointError(
            message=f"Unsupported endpoint {endpoint_name!r} for service {service!r}.",
            service=service,
            endpoint_name=endpoint_name,
            original_exception=exc,
        ) from exc


def _resolve_preparation_function(
    parameters: Mapping[str, Any] | None, service: str
) -> dict[str, Any]:
    """Prepare parameters using the preparer for ``service``.

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters to prepare.
        service (str): The service name (case-insensitive): ``"fred"``, ``"geofred"``, or
            ``"fraser"``.

    Returns:
        dict[str, Any]: The prepared parameters from the resolved service preparer.

    Raises:
        UnknownServiceError: If ``service`` is not a recognized service.
        TypeConversionError: If a converter fails to normalize a value.
        TypeValidationError: If a validator rejects a value's type.
        ValueValidationError: If a value is invalid or a required parameter is missing.

    Examples:
        >>> from fedfred._core._parameters import _resolve_preparation_function
        >>> _resolve_preparation_function({"limit": 100}, service="fred")
        {'limit': 100}
    """
    service = service.lower()

    try:
        return FRED_PREPARATION_FUNCTIONS[service](parameters)

    except KeyError as exc:
        raise UnknownServiceError(
            message=f"Unknown service {service!r} for parameter preparation.",
            service=service,
            known_services=tuple(sorted(FRED_PREPARATION_FUNCTIONS)),
            original_exception=exc,
        ) from exc
