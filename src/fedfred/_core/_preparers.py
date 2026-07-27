# filepath: /src/fedfred/_core/_preparers.py
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
"""Parameter preparation for FRED, ALFRED, GeoFRED, and FRASER requests.

The top of the parameter subsystem: the orchestrators that turn raw, caller-supplied
parameters into validated, request-ready ones. :func:`_prepare_parameters` is the engine —
for each parameter it skips ``None``, runs the spec's converter then its validator, admits or
rejects unknowns per ``allow_unknown``, and finally enforces that every required parameter is
present. The three per-service wrappers bind that engine to each service's parameter-spec
registry, all with ``allow_unknown=True``, so an unspecced parameter passes through untouched
rather than raising (forward-compatible with FRED parameters this package hasn't modeled yet).

"Prepare" is orchestration, not operation: this layer *composes* the converters and validators
rather than performing either itself, which is why it sits above them and is consumed directly
by the clients. It is the request-side sibling of :mod:`._resolvers` — one prepares the
parameters, the other resolves the endpoint, and a request needs both.

Failures surface as the typed errors the composed layers raise (:class:`TypeConversionError`,
:class:`TypeValidationError`, :class:`ValueValidationError`) plus the two this layer raises
itself: :class:`UnknownParameterError` (an unspecced parameter when ``allow_unknown=False``)
and :class:`MissingParameterError` (a required parameter absent after processing).

Functions:
    _prepare_parameters: Convert + validate a parameter mapping against a spec map.
    _prepare_fred_parameters: Prepare FRED/ALFRED request parameters.
    _prepare_geofred_parameters: Prepare GeoFRED request parameters.
    _prepare_fraser_parameters: Prepare FRASER request parameters.

See Also:
    - :mod:`fedfred._core._registries`: Provides the per-service ``*_PARAMETER_SPECS``.
    - :class:`fedfred._core._specs.ParameterSpec`: The per-parameter converter/validator spec.
    - :mod:`fedfred._core._converters`: The converters this layer composes.
    - :mod:`fedfred._core._validators`: The validators this layer composes.
    - :mod:`fedfred._core._resolvers`: The endpoint-side sibling; a request needs both.

References:
    - FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..exceptions import MissingParameterError, UnknownParameterError
from ._registries import (
    FRASER_PARAMETER_SPECS,
    FRED_PARAMETER_SPECS,
    GEOFRED_PARAMETER_SPECS,
)
from ._specs import ParameterSpec


def _prepare_parameters(
    parameters: Mapping[str, Any] | None,
    specs: Mapping[str, ParameterSpec],
    service: str,
    allow_unknown: bool = False,
) -> dict[str, Any]:
    """Convert and validate a parameter mapping against a spec map.

    Processes each supplied parameter in turn: a ``None`` value is skipped entirely (treated as
    absent), a known parameter is run through its converter and then its validator, and an
    unknown parameter is either passed through verbatim or rejected per ``allow_unknown``. After
    all inputs are processed, every spec marked required must be present in the result or the
    call raises.

    Two edges worth noting: an unknown parameter admitted under ``allow_unknown=True`` is
    **not** converted or validated — it is trusted as-is — and a required parameter supplied
    explicitly as ``None`` is skipped by the ``None`` filter and therefore fails the
    required-check as if it had been omitted.

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters, or ``None`` (treated as
            empty).
        specs (Mapping[str, ParameterSpec]): The per-parameter specifications.
        service (str): The service name, used only for error context.
        allow_unknown (bool): If ``True``, parameters with no spec pass through unchanged
            (unconverted, unvalidated); if ``False``, an unknown parameter raises. Defaults to
            ``False``.

    Returns:
        dict[str, Any]: The prepared parameters — converter outputs for known values, verbatim
        values for admitted unknowns — ready to send.

    Raises:
        UnknownParameterError: If an unrecognized parameter is seen with ``allow_unknown=False``.
        TypeConversionError: If a parameter's converter fails to normalize its value.
        TypeValidationError: If a validator rejects a value's type.
        ValueValidationError: If a validator rejects a value.
        MissingParameterError: If a required parameter is absent after processing (including when
            it was supplied as ``None``).

    Examples:
        >>> from fedfred._core._specs import ParameterSpec
        >>> from fedfred._core._preparers import _prepare_parameters
        >>> from fedfred._core._validators import _validate_nonnegative_int
        >>> specs = {"limit": ParameterSpec(validator=_validate_nonnegative_int)}
        >>> _prepare_parameters({"limit": 100}, specs, service="Test")
        {'limit': 100}
    """
    if parameters is None:
        parameters = {}

    prepared: dict[str, Any] = {}

    for name, value in parameters.items():
        if value is None:
            continue

        spec = specs.get(name)

        if spec is None:
            if allow_unknown:
                prepared[name] = value
                continue

            raise UnknownParameterError(
                message=f"Unknown parameter {name!r} for {service}.",
                parameter=name,
                service=service,
                known_parameters=tuple(sorted(specs)),
            )

        if spec.converter is not None:
            value = spec.converter(name, value)

        if spec.validator is not None:
            spec.validator(name, value)

        prepared[name] = value

    for name, spec in specs.items():
        if spec.required and name not in prepared:
            raise MissingParameterError(
                message=f"Missing required parameter {name!r} for {service}.",
                parameter=name,
                service=service,
            )

    return prepared


def _prepare_fred_parameters(parameters: Mapping[str, Any] | None) -> dict[str, Any]:
    """Prepare FRED request parameters against :data:`FRED_PARAMETER_SPECS`.

    Thin wrapper over :func:`_prepare_parameters` with ``allow_unknown=True``, so any parameter
    without a spec is passed through unconverted and unvalidated rather than rejected.

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters to prepare.

    Returns:
        dict[str, Any]: The prepared FRED request parameters.

    Raises:
        TypeConversionError: If a converter fails to normalize a value.
        TypeValidationError: If a validator rejects a value's type.
        ValueValidationError: If a validator rejects a value.
        MissingParameterError: If a required parameter is missing after processing.

    Examples:
        >>> from fedfred._core._preparers import _prepare_fred_parameters
        >>> _prepare_fred_parameters({"limit": 100, "sort_order": "asc"})
        {'limit': 100, 'sort_order': 'asc'}

    Notes:
        Unknown parameters pass through unchanged (``allow_unknown=True``); they are neither
        converted nor validated, so a caller-supplied typo reaches the API rather than raising.
    """
    return _prepare_parameters(
        parameters,
        FRED_PARAMETER_SPECS,
        service="FRED",
        allow_unknown=True,
    )


def _prepare_geofred_parameters(parameters: Mapping[str, Any] | None) -> dict[str, Any]:
    """Prepare GeoFRED request parameters against :data:`GEOFRED_PARAMETER_SPECS`.

    Thin wrapper over :func:`_prepare_parameters` with ``allow_unknown=True``, so any parameter
    without a spec is passed through unconverted and unvalidated rather than rejected.

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters to prepare.

    Returns:
        dict[str, Any]: The prepared GeoFRED request parameters.

    Raises:
        TypeConversionError: If a converter fails to normalize a value.
        TypeValidationError: If a validator rejects a value's type.
        ValueValidationError: If a validator rejects a value.
        MissingParameterError: If a required parameter is missing after processing.

    Examples:
        >>> from fedfred._core._preparers import _prepare_geofred_parameters
        >>> _prepare_geofred_parameters({"shape": "state", "file_type": "geojson"})
        {'shape': 'state', 'file_type': 'geojson'}

    Notes:
        Unknown parameters pass through unchanged (``allow_unknown=True``); they are neither
        converted nor validated.
    """
    return _prepare_parameters(
        parameters,
        GEOFRED_PARAMETER_SPECS,
        service="GeoFRED",
        allow_unknown=True,
    )


def _prepare_fraser_parameters(parameters: Mapping[str, Any] | None) -> dict[str, Any]:
    """Prepare FRASER request parameters against :data:`FRASER_PARAMETER_SPECS`.

    Thin wrapper over :func:`_prepare_parameters` with ``allow_unknown=True``, so any parameter
    without a spec is passed through unconverted and unvalidated rather than rejected.

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters to prepare.

    Returns:
        dict[str, Any]: The prepared FRASER request parameters.

    Raises:
        TypeConversionError: If a converter fails to normalize a value.
        TypeValidationError: If a validator rejects a value's type.
        ValueValidationError: If a validator rejects a value.
        MissingParameterError: If a required parameter is missing after processing.

    Examples:
        >>> from fedfred._core._preparers import _prepare_fraser_parameters
        >>> _prepare_fraser_parameters({"limit": 100, "page": 1})
        {'limit': 100, 'page': 1}

    Notes:
        Unknown parameters pass through unchanged (``allow_unknown=True``); they are neither
        converted nor validated.
    """
    return _prepare_parameters(
        parameters,
        FRASER_PARAMETER_SPECS,
        service="FRASER",
        allow_unknown=True,
    )
