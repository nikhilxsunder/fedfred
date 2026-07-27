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

The "resolve" layer: functions that compute an effective value at request time by consulting
the registries, the process-global config, and the defaults, validating the result before
returning it. Two groups live here.

Request routing
    :func:`_resolve_endpoint` maps a ``(service, endpoint_name)`` pair to its pre-built
    :class:`EndpointSpec` (a pure registry lookup — no construction on the request path), and
    :func:`_resolve_preparation_function` dispatches a service to its parameter-preparation
    function and applies it, returning request-ready parameters. Together they resolve the
    *where* (endpoint) and the *what* (prepared params).

Configuration resolution
    :func:`_resolve_dataframe_backend`, :func:`_resolve_geodataframe_backend`, and
    :func:`_resolve_api_key` each apply the same precedence idiom — an explicit per-call value,
    then the process-global setting, then the compiled-in default (or, for the API key, the
    environment variable) — and validate the winner. These are the *resolve* counterparts to the
    read-only ``_get_*`` accessors: where a getter reports current state and may return ``None``,
    a resolver computes the value actually used and raises when nothing resolves.

Everything here reads state, never writes it; mutation lives in :mod:`._mutators`. The layer
sits above the registries, preparers, and globals it consults, and is the request-side surface
the client calls.

Functions:
    _resolve_endpoint: Resolve a (service, endpoint name) to its EndpointSpec.
    _resolve_preparation_function: Dispatch a service to its preparer and apply it.
    _resolve_dataframe_backend: Resolve the effective DataFrame backend.
    _resolve_geodataframe_backend: Resolve the effective GeoDataFrame backend.
    _resolve_api_key: Resolve a service's API key (global, then environment).

See Also:
    - :mod:`fedfred._core._registries`: Provides :data:`_ENDPOINT_REGISTRY` and the config globals.
    - :mod:`fedfred._core._preparers`: Provides the preparation functions dispatched here.
    - :mod:`fedfred._core._accessors`: The read-only ``_get_*`` counterparts to the config
    resolvers.
    - :mod:`fedfred._core._mutators`: Writes the global state these resolvers read.
    - :mod:`fedfred._core._defaults`: The compiled-in fallbacks the config resolvers use.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from ..exceptions import MissingAPIKeyError, UnsupportedEndpointError
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

    Two dict lookups, no allocation. ``endpoint_name`` is normalized with ``.strip().lower()``
    before the second lookup, so callers may pass whitespace-padded or differently-cased names
    without each call site defending the registry shape.

    Args:
        service (Service): The calling client's service identity (``"fred"``, ``"alfred"``,
            ``"geofred"``, or ``"fraser"``).
        endpoint_name (str): The endpoint name to resolve, e.g. ``"get_series_observations"``.
            Whitespace is trimmed and the name is lowercased before lookup.

    Returns:
        EndpointSpec: The immutable, import-time-validated specification.

    Raises:
        TypeValidationError: If ``service`` is not a string (from :func:`_validate_service`).
        ValueValidationError: If ``service`` is not a recognized service (from
            :func:`_validate_service`).
        UnsupportedEndpointError: If ``endpoint_name`` is not in the resolved service's registry.

    Examples:
        >>> from fedfred._core._resolvers import _resolve_endpoint
        >>> spec = _resolve_endpoint("fred", "get_series_observations")
        >>> spec.url
        'https://api.stlouisfed.org/fred/series/observations'
        >>> # FRED and ALFRED return separate specs that share most fields
        >>> # but carry different `service` identities.
        >>> spec is _resolve_endpoint("alfred", "get_series_observations")
        False

    Notes:
        Endpoint names are unique per service, not globally; the same name may resolve under
        multiple services by design (FRED and ALFRED share endpoint names, differing only in
        vintage-parameter handling at the parameter-preparation layer).
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
    "alfred": _prepare_fred_parameters,
}
"""Service -> parameter-preparation function dispatch, backing
:func:`_resolve_preparation_function`.

Total over every :data:`Service`: ``"alfred"`` maps to the same preparer as ``"fred"`` because
ALFRED reuses FRED's parameter surface (they differ only in vintage-parameter handling, applied
within that shared preparer). Keeping all four services keyed here means
:func:`_resolve_preparation_function` never dispatches a service that passed
:func:`_validate_service` into a missing key."""


def _resolve_preparation_function(
    parameters: Mapping[str, Any] | None, service: Service
) -> dict[str, Any]:
    """Prepare parameters using the preparer registered for ``service``.

    Validates ``service``, then dispatches to its preparer in :data:`_PREPARATION_FUNCTIONS`.
    The dispatch table is keyed over every service, so any service that passes validation has a
    preparer (``"alfred"`` shares ``"fred"``'s).

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters to prepare.
        service (Service): The service whose preparer to use — ``"fred"``, ``"alfred"``,
            ``"geofred"``, or ``"fraser"``.

    Returns:
        dict[str, Any]: The prepared parameters from the resolved service preparer.

    Raises:
        TypeValidationError: If ``service`` is not a string, or a value's type is rejected by a
            validator.
        ValueValidationError: If ``service`` is not a recognized service, or a value is rejected
            by a validator.
        TypeConversionError: If a converter fails to normalize a value.
        MissingParameterError: If a required parameter is missing after processing.

    Examples:
        >>> from fedfred._core._resolvers import _resolve_preparation_function
        >>> _resolve_preparation_function({"limit": 100}, service="fred")
        {'limit': 100}
    """
    _validate_service(service)

    return _PREPARATION_FUNCTIONS[service](parameters)


def _resolve_dataframe_backend(explicit: DataFrameBackend | None = None) -> DataFrameBackend:
    """Resolve the effective DataFrame backend from an explicit choice, global, or default.

    Precedence: ``explicit`` if given, else the process-global set via
    :func:`_set_dataframe_backend`, else :data:`_DEFAULT_DATAFRAME_BACKEND`. The winner is
    validated before return, so callers always receive a member of
    :data:`_VALID_DATAFRAME_BACKENDS`.

    Args:
        explicit (DataFrameBackend | None): A per-call backend override, or ``None`` to fall
            through to the global setting and then the default.

    Returns:
        DataFrameBackend: The resolved, validated backend.

    Raises:
        TypeValidationError: If the resolved backend is not a string.
        ValueValidationError: If the resolved backend is not a valid DataFrame backend.

    Examples:
        >>> from fedfred._core._resolvers import _resolve_dataframe_backend
        >>> _resolve_dataframe_backend("polars")
        'polars'
    """
    backend = explicit or _GLOBAL_DATAFRAME_BACKEND or _DEFAULT_DATAFRAME_BACKEND

    _validate_dataframe_backend(backend)

    return backend


def _resolve_geodataframe_backend(
    explicit: GeoDataFrameBackend | None = None,
) -> GeoDataFrameBackend:
    """Resolve the effective GeoDataFrame backend from an explicit choice, global, or default.

    Precedence: ``explicit`` if given, else the process-global set via
    :func:`_set_geodataframe_backend`, else :data:`_DEFAULT_GEODATAFRAME_BACKEND`. The winner is
    validated before return, so callers always receive a member of
    :data:`_VALID_GEODATAFRAME_BACKENDS`.

    Args:
        explicit (GeoDataFrameBackend | None): A per-call backend override, or ``None`` to fall
            through to the global setting and then the default.

    Returns:
        GeoDataFrameBackend: The resolved, validated backend.

    Raises:
        TypeValidationError: If the resolved backend is not a string.
        ValueValidationError: If the resolved backend is not a valid GeoDataFrame backend.

    Examples:
        >>> from fedfred._core._resolvers import _resolve_geodataframe_backend
        >>> _resolve_geodataframe_backend("polars-st")
        'polars-st'
    """
    backend = explicit or _GLOBAL_GEODATAFRAME_BACKEND or _DEFAULT_GEODATAFRAME_BACKEND

    _validate_geodataframe_backend(backend)

    return backend


def _resolve_api_key(
    service: Service = "fred",
    env_var: str | None = None,
) -> str:
    """Resolve a service's API key from the global setting, then the environment.

    Precedence: the key stored via :func:`_set_api_key` for ``service`` if set and non-blank,
    else the environment variable (``env_var`` if given, otherwise the service's default from
    :data:`ENV_VARS`). Raises if neither yields a usable key. Both candidates are stripped;
    a whitespace-only value is treated as unset.

    Args:
        service (Service): The service to resolve a key for. Defaults to ``"fred"``.
        env_var (str | None): Environment-variable name overriding the service default from
            :data:`ENV_VARS`. ``None`` uses the default.

    Returns:
        str: The resolved API key, stripped of surrounding whitespace.

    Raises:
        TypeValidationError: If ``service`` is not a string (from :func:`_validate_service`).
        ValueValidationError: If ``service`` is not a recognized service (from
            :func:`_validate_service`).
        MissingAPIKeyError: If no key can be resolved from either the global store or the
            environment.

    Notes:
        This is the resolver, not an accessor: unlike :func:`_get_api_key` (which returns
        ``None`` for an unconfigured service), it insists on a usable key and raises when none
        is found. It takes no explicit-``api_key`` argument — a caller-supplied key is applied
        upstream, before this fallback resolution runs.
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

    raise MissingAPIKeyError(
        message=f"No API key could be resolved for service={service!r}.",
        service=service,
        env_var=env_name,
        context={
            "remedies": (
                "Provide api_key=...",
                f"call set_api_key(..., service={service!r})",
                f"set the environment variable {env_name}",
            ),
        },
    )
