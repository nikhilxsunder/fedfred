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
""""""

from __future__ import annotations

from . import _registries
from ._choices import _VALID_DATAFRAME_BACKENDS, _VALID_GEODATAFRAME_BACKENDS
from ._types import DataFrameBackend, GeoDataFrameBackend, Service
from ._validators import _validate_dataframe_backend, _validate_geodataframe_backend, _validate_service


def _set_api_key(api_key: str, service: Service = "fred") -> None:
    """Set the global API key for the fedfred package.

    Args:
        api_key (str): API key string.
        service (Service): The service for which to set the API key. Defaults to "fred".

    Raises:
        TypeValidationError:
        ValueValidationError:
    """
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("api_key must be a non-empty string.")

    _validate_service(service)

    _registries._GLOBAL_KEYS[service] = api_key.strip()


def _clear_api_key(service: Service = "fred") -> None:
    """Clear the global API key for a service.

    Args:
        service (Service): The service for which to clear the API key. Defaults to "fred".

    Raises:
        TypeValidationError:
        ValueValidationError:
    """
    _validate_service(service)

    _registries._GLOBAL_KEYS[service] = None


def _set_dataframe_backend(backend: DataFrameBackend) -> None:
    """Set the global dataframe backend used for FRED observation conversions.

    Validates ``backend`` against :data:`_VALID_DATAFRAME_BACKENDS` and rebinds the
    process-global :data:`fedfred._core._registries._GLOBAL_DATAFRAME_BACKEND`.
    The setting is read back by :func:`_get_dataframe_backend` and applied per
    request by :func:`_resolve_dataframe_backend`.

    Args:
        backend (DataFrameBackend): The dataframe backend to activate. One of ``"pandas"``,
            ``"polars"``, ``"dask"``, or ``"fedfred"``.

    Raises:
        ValueError: If ``backend`` is not one of :data:`_VALID_DATAFRAME_BACKENDS`.

    Examples:
        >>> from fedfred._core._mutators import _set_dataframe_backend
        >>> from fedfred._core._accessors import _get_dataframe_backend
        >>> _set_dataframe_backend("polars")
        >>> _get_dataframe_backend()
        'polars'
        >>> _set_dataframe_backend("numpy")  # doctest: +SKIP
        ValueError: backend must be one of ('pandas', 'polars', 'dask', 'fedfred'), got 'numpy'.

    Notes:
        Private mutator; the public entry point is
        :func:`fedfred.settings.set_dataframe_backend`, which re-exports it. The
        state lives in :mod:`fedfred._core._registries`, so the assignment rebinds
        that module's attribute rather than using a ``global`` statement.
    """
    _validate_dataframe_backend(backend)

    _registries._GLOBAL_DATAFRAME_BACKEND = backend


def _set_geodataframe_backend(backend: GeoDataFrameBackend) -> None:
    """Set the global geodataframe backend used for GeoFRED observation conversions.

    Validates ``backend`` against :data:`_VALID_GEODATAFRAME_BACKENDS` and rebinds
    the process-global
    :data:`fedfred._core._registries._GLOBAL_GEODATAFRAME_BACKEND`. The setting is
    read back by :func:`_get_geodataframe_backend` and applied per request by
    :func:`_resolve_geodataframe_backend`.

    Args:
        backend (GeoDataFrameBackend): The geodataframe backend to activate. One of
            ``"geopandas"``, ``"polars-st"``, ``"dask-geopandas"``, or ``"fedfred"``.

    Raises:
        ValueError: If ``backend`` is not one of :data:`_VALID_GEODATAFRAME_BACKENDS`.

    Examples:
        >>> from fedfred._core._mutators import _set_geodataframe_backend
        >>> from fedfred._core._accessors import _get_geodataframe_backend
        >>> _set_geodataframe_backend("polars-st")
        >>> _get_geodataframe_backend()
        'polars-st'
        >>> _set_geodataframe_backend("shapely")  # doctest: +SKIP
        ValueError: backend must be one of ('geopandas', 'polars-st', 'dask-geopandas', 'fedfred'),
        got 'shapely'.

    Notes:
        Private mutator; the public entry point is
        :func:`fedfred.settings.set_geodataframe_backend`, which re-exports it. The
        state lives in :mod:`fedfred._core._registries`, so the assignment rebinds
        that module's attribute rather than using a ``global`` statement.
    """
    _validate_geodataframe_backend(backend)

    _registries._GLOBAL_GEODATAFRAME_BACKEND = backend
