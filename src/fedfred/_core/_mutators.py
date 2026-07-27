# filepath: /src/fedfred/_core/_mutators.py
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
"""Write-side mutators for the core layer.

Functions that change process-global configuration — the "set/clear" half of the package's
read/write split, mirroring the read-side accessors in :mod:`._accessors`. Two groups live
here: API-key mutators (:func:`_set_api_key`, :func:`_clear_api_key`) and backend mutators
(:func:`_set_dataframe_backend`, :func:`_set_geodataframe_backend`). Each validates its input
through :mod:`._validators` before writing, so an invalid value never reaches the global state.

The state itself is owned by :mod:`._registries`; nothing is stored in this module. That
ownership is why the module is imported as ``from . import _registries`` and written as
``_registries._GLOBAL_X = ...`` rather than pulling the globals in by name: rebinding the
registry module's attribute is what lets the accessors and resolvers see the update. Importing
a scalar global by name would bind an import-time copy and silently drop every mutation — the
``_GLOBAL_KEYS`` dict is mutated in place, but the scalar backend globals must be rebound
through the module.

These are private; the public ``set_*`` / ``clear_*`` entry points are thin re-exports in
:mod:`fedfred.settings`. Full precedence resolution (explicit override, then global, then
environment/default) is a separate concern in :mod:`._resolvers`, and the read-only getters are
in :mod:`._accessors` — this module only writes.

Functions:
    _set_api_key: Store a service's API key in the global registry.
    _clear_api_key: Reset a service's API key to ``None``.
    _set_dataframe_backend: Set the global DataFrame backend.
    _set_geodataframe_backend: Set the global GeoDataFrame backend.

See Also:
    - :mod:`fedfred._core._accessors`: The read half (``_get_*``) of the set/clear/get triad.
    - :mod:`fedfred._core._resolvers`: Full precedence resolution over the same globals.
    - :mod:`fedfred._core._registries`: Owns the process-global state these mutate.
    - :mod:`fedfred._core._validators`: Validates every input before it is written.
    - :mod:`fedfred.settings`: Public re-exports of these mutators.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from . import _registries
from ._types import DataFrameBackend, GeoDataFrameBackend, Service
from ._validators import (
    _validate_api_key,
    _validate_dataframe_backend,
    _validate_geodataframe_backend,
    _validate_service,
)


def _set_api_key(api_key: str, service: Service = "fred") -> None:
    """Set the process-global API key for a service.

    Validates ``api_key`` and ``service``, then stores the key (stripped of surrounding
    whitespace) in the global registry. Read back by :func:`_resolve_api_key` and
    :func:`_get_api_key`.

    Args:
        api_key (str): A non-empty API key string. Stored stripped of leading/trailing
            whitespace.
        service (Service): The service to set the key for. Defaults to ``"fred"``. Note FRED,
            GeoFRED, and ALFRED authenticate with the same key but are keyed separately here.

    Raises:
        TypeValidationError: If ``api_key`` is not a ``str``, or ``service`` is not a ``str``.
        ValueValidationError: If ``api_key`` is empty/whitespace-only, or ``service`` is not a
            recognized service.

    Notes:
        Private mutator; the public entry point is :func:`fedfred.settings.set_api_key`, which
        re-exports it. State lives in :mod:`fedfred._core._registries`; the key is written into
        the ``_GLOBAL_KEYS`` dict in place.

    See Also:
        - :func:`_clear_api_key`: Resets a service's key to ``None``.
        - :func:`_resolve_api_key`: Full resolution (global, then environment) at request time.
    """
    _validate_api_key(api_key)

    _validate_service(service)

    _registries._GLOBAL_KEYS[service] = api_key.strip()


def _clear_api_key(service: Service = "fred") -> None:
    """Reset a service's process-global API key to ``None``.

    Validates ``service`` and clears its entry in the global registry, so a subsequent
    :func:`_resolve_api_key` falls through to the environment variable (or raises if none is
    set).

    Args:
        service (Service): The service to clear. Defaults to ``"fred"``.

    Raises:
        TypeValidationError: If ``service`` is not a ``str``.
        ValueValidationError: If ``service`` is not a recognized service.

    Notes:
        Private mutator; the public entry point is :func:`fedfred.settings.clear_api_key`, which
        re-exports it. State lives in :mod:`fedfred._core._registries`; the entry is set to
        ``None`` in the ``_GLOBAL_KEYS`` dict in place.

    See Also:
        - :func:`_set_api_key`: Sets the value cleared here.
    """
    _validate_service(service)

    _registries._GLOBAL_KEYS[service] = None


def _set_dataframe_backend(backend: DataFrameBackend) -> None:
    """Set the global DataFrame backend used for FRED observation conversions.

    Validates ``backend`` against :data:`_VALID_DATAFRAME_BACKENDS` and rebinds the
    process-global :data:`fedfred._core._registries._GLOBAL_DATAFRAME_BACKEND`. Read back by
    :func:`_get_dataframe_backend` and applied per request by :func:`_resolve_dataframe_backend`.

    Args:
        backend (DataFrameBackend): The backend to activate — one of ``"pandas"``,
            ``"polars"``, ``"dask"``, or ``"fedfred"``.

    Raises:
        TypeValidationError: If ``backend`` is not a ``str``.
        ValueValidationError: If ``backend`` is not one of :data:`_VALID_DATAFRAME_BACKENDS`.

    Examples:
        >>> from fedfred._core._mutators import _set_dataframe_backend
        >>> from fedfred._core._accessors import _get_dataframe_backend
        >>> _set_dataframe_backend("polars")  # doctest: +SKIP
        >>> _get_dataframe_backend()  # doctest: +SKIP
        'polars'

    Notes:
        Private mutator; the public entry point is
        :func:`fedfred.settings.set_dataframe_backend`, which re-exports it. State lives in
        :mod:`fedfred._core._registries`, so the assignment rebinds that module's attribute
        rather than using a ``global`` statement.

    See Also:
        - :func:`_get_dataframe_backend`: Reads the value set here.
        - :func:`_resolve_dataframe_backend`: Applies it (with optional override) per request.
    """
    _validate_dataframe_backend(backend)

    _registries._GLOBAL_DATAFRAME_BACKEND = backend


def _set_geodataframe_backend(backend: GeoDataFrameBackend) -> None:
    """Set the global GeoDataFrame backend used for GeoFRED observation conversions.

    Validates ``backend`` against :data:`_VALID_GEODATAFRAME_BACKENDS` and rebinds the
    process-global :data:`fedfred._core._registries._GLOBAL_GEODATAFRAME_BACKEND`. Read back by
    :func:`_get_geodataframe_backend` and applied per request by
    :func:`_resolve_geodataframe_backend`.

    Args:
        backend (GeoDataFrameBackend): The backend to activate — one of ``"geopandas"``,
            ``"polars-st"``, ``"dask-geopandas"``, or ``"fedfred"``.

    Raises:
        TypeValidationError: If ``backend`` is not a ``str``.
        ValueValidationError: If ``backend`` is not one of :data:`_VALID_GEODATAFRAME_BACKENDS`.

    Examples:
        >>> from fedfred._core._mutators import _set_geodataframe_backend
        >>> from fedfred._core._accessors import _get_geodataframe_backend
        >>> _set_geodataframe_backend("polars-st")  # doctest: +SKIP
        >>> _get_geodataframe_backend()  # doctest: +SKIP
        'polars-st'

    Notes:
        Private mutator; the public entry point is
        :func:`fedfred.settings.set_geodataframe_backend`, which re-exports it. State lives in
        :mod:`fedfred._core._registries`, so the assignment rebinds that module's attribute
        rather than using a ``global`` statement.

    See Also:
        - :func:`_get_geodataframe_backend`: Reads the value set here.
        - :func:`_resolve_geodataframe_backend`: Applies it (with optional override) per request.
    """
    _validate_geodataframe_backend(backend)

    _registries._GLOBAL_GEODATAFRAME_BACKEND = backend
