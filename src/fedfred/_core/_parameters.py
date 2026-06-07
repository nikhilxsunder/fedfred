# filepath: /src/fedfred/_core/_parameters.py
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
"""Request-parameter preparation for the FRED, GeoFRED, and FRASER APIs.

This module is the single place where caller-supplied parameters are turned into
API-ready request parameters. A :class:`ParameterSpec` pairs an optional
converter (Python value -> wire value) with an optional validator and a
required flag; per-service spec maps (:data:`FRED_PARAMETER_SPECS`,
:data:`GEOFRED_PARAMETER_SPECS`, :data:`FRASER_PARAMETER_SPECS`) declare the
handling for every known parameter. :func:`_prepare_parameters` applies a spec
map to a parameter mapping, and :func:`_resolve_preparation_function` dispatches
to the correct per-service preparer by service name. All names here are internal.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..exceptions import ParameterServiceError, ValueValidationError
from ._converters import (
    ParameterConverter,
    _comma_date_list_converter,
    _date_parameter_converter,
    _semicolon_list_converter,
    _time_parameter_converter,
)
from ._validators import (
    ParameterValidator,
    _validate_bool,
    _validate_choice,
    _validate_comma_date_list_string,
    _validate_hh_mm,
    _validate_nonempty_str,
    _validate_nonnegative_int,
    _validate_semicolon_list_string,
    _validate_series_id,
    _validate_str,
    _validate_str_choice,
    _validate_yyyy_mm_dd,
)

__all__ = [
    "_resolve_preparation_function",
]

@dataclass(frozen=True, slots=True)
class ParameterSpec:
    """Specification for preparing a single API request parameter.

    Pairs an optional converter (run first, to normalize a Python value into its
    wire form) with an optional validator (run on the converted value) and a
    required flag.

    Attributes:
        converter (ParameterConverter | None): Optional ``(name, value) -> value`` callable that normalizes a raw value into its API form. Run before validation.
        validator (ParameterValidator | None): Optional ``(name, value) -> None`` callable that raises on an invalid value. Run after conversion.
        required (bool): Whether the parameter must be present and non-``None`` after preparation.

    Examples:
        >>> from fedfred._core._parameters import ParameterSpec
        >>> from fedfred._core._validators import _validate_nonnegative_int
        >>> spec = ParameterSpec(validator=_validate_nonnegative_int, required=True)
        >>> spec.required
        True
    """

    converter: ParameterConverter | None = None
    """Optional ``(name, value) -> value`` converter, run before validation to normalize raw values into their API form."""

    validator: ParameterValidator | None = None
    """Optional ``(name, value) -> None`` validator, run after conversion; raises on an invalid value."""

    required: bool = False
    """Whether the parameter must be present and non-``None`` after preparation; if so, a missing value raises :class:`~fedfred.exceptions.ValueValidationError`."""


def _prepare_parameters(
    parameters: Mapping[str, Any] | None,
    specs: Mapping[str, ParameterSpec],
    *,
    service: str,
    allow_unknown: bool = False
) -> dict[str, Any]:
    """Convert and validate a parameter mapping against a spec map.

    Skips ``None`` values, applies each parameter's converter then validator,
    handles unknown parameters per ``allow_unknown``, and enforces required
    parameters after processing.

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters, or ``None`` (treated as empty).
        specs (Mapping[str, ParameterSpec]): The per-parameter specifications.
        service (str): The service name, used only for error context.
        allow_unknown (bool): If ``True``, parameters with no spec are passed through unchanged; if ``False``, they raise. Defaults to ``False``.

    Returns:
        dict[str, Any]: The prepared parameters, ready to send.

    Raises:
        TypeConversionError: If a converter fails to normalize a value.
        TypeValidationError: If a validator rejects a value's type.
        ValueValidationError: If a value is invalid, an unknown parameter is encountered with ``allow_unknown=False``, or a required parameter is missing.

    Examples:
        >>> from fedfred._core._parameters import _prepare_parameters, ParameterSpec
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

            raise ValueValidationError(
                message=f"Unknown parameter {name!r} for {service}.",
                parameter=name,
                reason="Unknown parameter.",
                details={
                    "parameter": name,
                    "service": service,
                    "known_parameters": tuple(sorted(specs)),
                },
            )

        if spec.converter is not None:
            value = spec.converter(name, value)

        if spec.validator is not None:
            spec.validator(name, value)

        prepared[name] = value

    for name, spec in specs.items():
        if spec.required and name not in prepared:
            raise ValueValidationError(
                message=f"Missing required parameter {name!r} for {service}.",
                parameter=name,
                reason="Required parameter missing.",
                details={"service": service},
            )

    return prepared

FRED_FREQUENCIES = {
    "d",
    "w",
    "bw",
    "m",
    "q",
    "sa",
    "a",
    "wef",
    "weth",
    "wew",
    "wetu",
    "wem",
    "wesu",
    "wesa",
    "bwew",
    "bwem",
}
"""Valid ``frequency`` values for FRED API parameters."""

FRED_UNITS = {
    "lin",
    "chg",
    "ch1",
    "pch",
    "pc1",
    "pca",
    "cch",
    "cca",
    "log",
}
"""Valid ``units`` values for FRED API parameters."""

SORT_ORDERS = {"asc", "desc"}
"""Valid ``sort_order`` values for FRED API parameters."""

AGGREGATION_METHODS = {"sum", "avg", "eop"}
"""Valid ``aggregation_method`` values for FRED API parameters."""

OUTPUT_TYPES = {1, 2, 3, 4}
"""Valid ``output_type`` values for FRED API parameters."""

FRED_ORDER_BY = {
    "series_id",
    "title",
    "units",
    "frequency",
    "seasonal_adjustment",
    "realtime_start",
    "realtime_end",
    "last_updated",
    "observation_start",
    "observation_end",
    "popularity",
    "group_popularity",
    "series_count",
    "created",
    "name",
    "release_id",
    "press_release",
    "group_id",
    "search_rank",
}
"""Valid ``order_by`` values for FRED API parameters."""

GEOFRED_REGION_TYPES = {
    "bea",
    "msa",
    "frb",
    "necta",
    "state",
    "country",
    "county",
    "censusregion",
    "censusdivision",
}
"""Valid region-type values for GeoFRED API parameters."""

FRED_PARAMETER_SPECS: dict[str, ParameterSpec] = {
    "category_id": ParameterSpec(validator=_validate_nonnegative_int),
    "release_id": ParameterSpec(validator=_validate_nonnegative_int),
    "limit": ParameterSpec(validator=_validate_nonnegative_int),
    "offset": ParameterSpec(validator=_validate_nonnegative_int),
    "page": ParameterSpec(validator=_validate_nonnegative_int),
    "api_key": ParameterSpec(validator=_validate_nonempty_str),
    "search_text": ParameterSpec(validator=_validate_str),
    "tag_search_text": ParameterSpec(validator=_validate_str),
    "filter_value": ParameterSpec(validator=_validate_nonempty_str),
    "format": ParameterSpec(validator=_validate_str_choice({"json"})),
    "file_type": ParameterSpec(validator=_validate_str_choice({"json"})),
    "sort_order": ParameterSpec(validator=_validate_str_choice(SORT_ORDERS)),
    "order_by": ParameterSpec(validator=_validate_str_choice(FRED_ORDER_BY)),
    "filter_variable": ParameterSpec(
        validator=_validate_str_choice({"frequency", "units", "seasonal_adjustment"})
    ),
    "tag_names": ParameterSpec(
        converter=_semicolon_list_converter,
        validator=_validate_semicolon_list_string,
    ),
    "exclude_tag_names": ParameterSpec(
        converter=_semicolon_list_converter,
        validator=_validate_semicolon_list_string,
    ),
    "realtime_start": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "realtime_end": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "observation_start": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "observation_end": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "vintage_dates": ParameterSpec(
        converter=_comma_date_list_converter,
        validator=_validate_comma_date_list_string,
    ),

    "start_time": ParameterSpec(
        converter=_time_parameter_converter,
        validator=_validate_hh_mm,
    ),
    "end_time": ParameterSpec(
        converter=_time_parameter_converter,
        validator=_validate_hh_mm,
    ),
    "series_id": ParameterSpec(validator=_validate_series_id),
    "frequency": ParameterSpec(validator=_validate_str_choice(FRED_FREQUENCIES)),
    "units": ParameterSpec(validator=_validate_str_choice(FRED_UNITS)),
    "aggregation_method": ParameterSpec(validator=_validate_str_choice(AGGREGATION_METHODS)),
    "output_type": ParameterSpec(validator=_validate_choice(OUTPUT_TYPES)),
    "search_type": ParameterSpec(validator=_validate_str_choice({"full_text", "series_id"})),
    "include_releases_dates_with_no_data": ParameterSpec(validator=_validate_bool),
    "season": ParameterSpec(
        validator=_validate_str_choice({"seasonally_adjusted", "not_seasonally_adjusted"})
    ),
}
"""Per-parameter specifications for FRED API requests, mapping each known parameter name to its converter/validator handling."""

GEOFRED_PARAMETER_SPECS: dict[str, ParameterSpec] = {
    "api_key": ParameterSpec(validator=_validate_nonempty_str),
    "file_type": ParameterSpec(
        validator=_validate_str_choice({"json", "geojson", "shp", "kml", "gdb", "gpkg"})
    ),
    "shape": ParameterSpec(validator=_validate_str_choice(GEOFRED_REGION_TYPES)),
    "region_type": ParameterSpec(validator=_validate_str_choice(GEOFRED_REGION_TYPES)),
    "series_id": ParameterSpec(validator=_validate_series_id),
    "series_group": ParameterSpec(validator=_validate_nonempty_str),
    "date": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "start_date": ParameterSpec(
        converter=_date_parameter_converter,
        validator=_validate_yyyy_mm_dd,
    ),
    "aggregation_method": ParameterSpec(validator=_validate_str_choice(AGGREGATION_METHODS)),
    "units": ParameterSpec(validator=_validate_nonempty_str),
    "season": ParameterSpec(
        validator=_validate_str_choice({"NSA", "SA", "SSA", "SAAR", "NSAAR"})
    ),
    "transformation": ParameterSpec(validator=_validate_str_choice(FRED_UNITS)),
}
"""Per-parameter specifications for GeoFRED API requests, mapping each known parameter name to its converter/validator handling."""

FRASER_PARAMETER_SPECS: dict[str, ParameterSpec] = {
    "limit": ParameterSpec(validator=_validate_nonnegative_int),
    "page": ParameterSpec(validator=_validate_nonnegative_int),
    "format": ParameterSpec(validator=_validate_str_choice({"json"})),
    "role": ParameterSpec(
        validator=_validate_str_choice(
            {"creator", "contributor", "editor", "repository", "uncertain", "subject"}
        )
    ),
}
"""Per-parameter specifications for FRASER API requests, mapping each known parameter name to its converter/validator handling."""

def _prepare_fred_parameters(parameters: Mapping[str, Any] | None) -> dict[str, Any]:
    """Prepare FRED API request parameters against :data:`FRED_PARAMETER_SPECS`.

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters to prepare.

    Returns:
        dict[str, Any]: The prepared FRED request parameters.

    Raises:
        TypeConversionError: If a converter fails to normalize a value.
        TypeValidationError: If a validator rejects a value's type.
        ValueValidationError: If a value is invalid or a required parameter is missing.

    Examples:
        >>> from fedfred._core._parameters import _prepare_fred_parameters
        >>> _prepare_fred_parameters({"limit": 100, "sort_order": "asc"})
        {'limit': 100, 'sort_order': 'asc'}

    Notes:
        Unknown parameters are passed through unchanged (``allow_unknown=True``).
    """
    return _prepare_parameters(
        parameters,
        FRED_PARAMETER_SPECS,
        service="FRED",
        allow_unknown=True,
    )

def _prepare_geofred_parameters(parameters: Mapping[str, Any] | None) -> dict[str, Any]:
    """Prepare GeoFRED API request parameters against :data:`GEOFRED_PARAMETER_SPECS`.

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters to prepare.

    Returns:
        dict[str, Any]: The prepared GeoFRED request parameters.

    Raises:
        TypeConversionError: If a converter fails to normalize a value.
        TypeValidationError: If a validator rejects a value's type.
        ValueValidationError: If a value is invalid or a required parameter is missing.

    Examples:
        >>> from fedfred._core._parameters import _prepare_geofred_parameters
        >>> _prepare_geofred_parameters({"shape": "state", "file_type": "geojson"})
        {'shape': 'state', 'file_type': 'geojson'}

    Notes:
        Unknown parameters are passed through unchanged (``allow_unknown=True``).
    """
    return _prepare_parameters(
        parameters,
        GEOFRED_PARAMETER_SPECS,
        service="GeoFRED",
        allow_unknown=True,
    )

def _prepare_fraser_parameters(parameters: Mapping[str, Any] | None) -> dict[str, Any]:
    """Prepare FRASER API request parameters against :data:`FRASER_PARAMETER_SPECS`.

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters to prepare.

    Returns:
        dict[str, Any]: The prepared FRASER request parameters.

    Raises:
        TypeConversionError: If a converter fails to normalize a value.
        TypeValidationError: If a validator rejects a value's type.
        ValueValidationError: If a value is invalid or a required parameter is missing.

    Examples:
        >>> from fedfred._core._parameters import _prepare_fraser_parameters
        >>> _prepare_fraser_parameters({"limit": 100, "page": 1})
        {'limit': 100, 'page': 1}

    Notes:
        Unknown parameters are passed through unchanged (``allow_unknown=True``).
    """
    return _prepare_parameters(
        parameters,
        FRASER_PARAMETER_SPECS,
        service="FRASER",
        allow_unknown=True,
    )

FRED_PREPARATION_FUNCTIONS: dict[str, Any] = {
    "fred": _prepare_fred_parameters,
    "geofred": _prepare_geofred_parameters,
    "fraser": _prepare_fraser_parameters,
}
"""Mapping of lowercase service name to its parameter-preparation function."""

def _resolve_preparation_function(
    parameters: Mapping[str, Any] | None,
    service: str
) -> dict[str, Any]:
    """Prepare parameters using the preparer for ``service``.

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters to prepare.
        service (str): The service name (case-insensitive): ``"fred"``, ``"geofred"``, or ``"fraser"``.

    Returns:
        dict[str, Any]: The prepared parameters from the resolved service preparer.

    Raises:
        ParameterServiceError: If ``service`` is not a recognized service.
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
        raise ParameterServiceError(
            message=f"Unknown service {service!r} for parameter preparation.",
            service=service,
            reason="Unrecognized service name.",
            details={"service": service, "expected_services": tuple(FRED_PREPARATION_FUNCTIONS)},
        ) from exc
