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

import os
from collections.abc import Mapping
from typing import Any

from ..exceptions import UnsupportedEndpointError
from ._defaults import _DEFAULT_DATAFRAME_BACKEND, _DEFAULT_GEODATAFRAME_BACKEND
from ._mappings import ENV_VARS
from ._preparers import (
    _prepare_fraser_parameters,
    _prepare_fred_parameters,
    _prepare_geofred_parameters,
)
from ._registries import (
    _ENDPOINT_REGISTRY,
    _GLOBAL_DATAFRAME_BACKEND,
    _GLOBAL_GEODATAFRAME_BACKEND,
    _GLOBAL_KEYS,
)
from ._specs import EndpointSpec
from ._types import DataFrameBackend, GeoDataFrameBackend, Service
from ._validators import (
    _validate_dataframe_backend,
    _validate_geodataframe_backend,
    _validate_service,
)


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
    _validate_service(service)

    service_registry = _ENDPOINT_REGISTRY[service]

    try:
        return service_registry[endpoint_name.strip().lower()]
    except KeyError as exc:
        raise UnsupportedEndpointError(
            message=f"Unsupported endpoint {endpoint_name!r} for service {service!r}.",
            service=service,
            endpoint_name=endpoint_name,
            original_exception=exc,
        ) from exc


_PREPARATION_FUNCTIONS: dict[Service, Any] = {
    "fred": _prepare_fred_parameters,
    "geofred": _prepare_geofred_parameters,
    "fraser": _prepare_fraser_parameters,
}
"""Service -> parameter-preparation function dispatch, backing
:func:`_resolve_preparation_function`."""


def _resolve_preparation_function(
    parameters: Mapping[str, Any] | None, service: Service
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
    _validate_service(service)

    return _PREPARATION_FUNCTIONS[service](parameters)


def _resolve_dataframe_backend(explicit: DataFrameBackend | None = None) -> DataFrameBackend:
    """
    """
    backend = explicit or _GLOBAL_DATAFRAME_BACKEND or _DEFAULT_DATAFRAME_BACKEND

    _validate_dataframe_backend(backend)

    return backend


def _resolve_geodataframe_backend(explicit: GeoDataFrameBackend | None = None) -> GeoDataFrameBackend:
    """
    """
    backend = explicit or _GLOBAL_GEODATAFRAME_BACKEND or _DEFAULT_GEODATAFRAME_BACKEND

    _validate_geodataframe_backend(backend)

    return backend


def _resolve_api_key(
    service: Service = "fred",
    env_var: str | None = None,
) -> str:
    """Resolve an API key from an explicit argument, the global setting, or the environment variable.

    Args:
        service (Service): The service for which to resolve the API key. Defaults to "fred".
        env_var (Optional[str]): Optional environment variable name to override the default for the service.

    Returns:
        str: The resolved API key.

    Raises:
        RuntimeError: If no API key can be resolved.
        ValueError: If an unknown service is specified.
    """
    _validate_service(service)

    # 2) global
    global_key = _GLOBAL_KEYS.get(service)

    if isinstance(global_key, str) and global_key.strip():
        return global_key.strip()

    # 3) environment
    env_name = env_var or ENV_VARS[service]

    env_value = os.getenv(env_name)

    if isinstance(env_value, str) and env_value.strip():
        return env_value.strip()

    raise RuntimeError( # TODO: Chnage this to an internal exception type.
        f"No API key could be resolved for service={service!r}. "
        f"Provide api_key=..., call set_api_key(..., service={service!r}), "
        f"or set the environment variable {env_name}."
    )
