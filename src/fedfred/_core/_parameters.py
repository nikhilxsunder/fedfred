# filepath: /src/fedfred/_core/_parameters.py
#
# Copyright (c) 2025–2026 Nikhil Sunder
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
"""fedfred._core._parameters

This module provides internal helper functions and data structures for preparing API request parameters for the FRED, GeoFRED, and FRASER APIs. 
It defines a ParameterSpec dataclass to specify how to convert and validate parameters, and provides functions to prepare parameters according 
to these specifications. This module is intended for internal use within the fedfred package and is not part of the public API.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Dict
from ..exceptions import ValueValidationError, ParameterServiceError
from ._converters import (
    ParameterConverter,
    _semicolon_list_converter,
    _date_parameter_converter,
    _time_parameter_converter,
    _comma_date_list_converter,
)
from ._validators import (
    ParameterValidator,
    _validate_nonnegative_int,
    _validate_nonempty_str,
    _validate_str,
    _validate_str_choice,
    _validate_choice,
    _validate_bool,
    _validate_yyyy_mm_dd,
    _validate_hh_mm,
    _validate_series_id,
    _validate_semicolon_list_string,
    _validate_comma_date_list_string
)

__all__ = [
    # Specs
    "ParameterSpec",
    # Parameter Maps
    "FRED_PARAMETER_SPECS",
    "GEOFRED_PARAMETER_SPECS",
    "FRASER_PARAMETER_SPECS",
    "FRED_FREQUENCIES",
    "FRED_UNITS",
    "SORT_ORDERS",
    "AGGREGATION_METHODS",
    "OUTPUT_TYPES",
    "FRED_ORDER_BY",
    "GEOFRED_REGION_TYPES",
    # Preparation Functions
    "_prepare_fred_parameters",
    "_prepare_geofred_parameters",
    "_prepare_fraser_parameters",
    # Service Resolution
    "_resolve_preparation_function",
]

@dataclass(frozen=True, slots=True)
class ParameterSpec:
    """Specification for preparing a single API request parameter.

    Attributes:
        converter: Optional function used to normalize Python values into API-ready values.
        validator: Optional function used to validate the normalized value.
        required: Whether the parameter must be present and non-None.

    Examples:
        >>> # Internal use
        >>> from ._core import ParameterSpec
        >>> spec = ParameterSpec(converter=str, validator=lambda n, v: isinstance(v, str), required=True)
        >>> spec.converter("example_param", 123)
        '123'
    """

    converter: Optional[ParameterConverter] = None
    """Optional function to convert raw parameter values into API-ready formats. Used for normalization before validation and request preparation."""

    validator: Optional[ParameterValidator] = None
    """Optional function to validate parameter values after conversion. Should raise an exception if validation fails."""

    required: bool = False
    """Indicates whether this parameter is required. If True, the parameter must be present and non-None after conversion, or a ValueValidationError will be raised."""

def _prepare_parameters(parameters: Optional[Mapping[str, Any]], specs: Mapping[str, ParameterSpec],
                        *, service: str, allow_unknown: bool = False) -> Dict[str, Any]:
    """Internal helper function to prepare API request parameters based on provided specifications.

    Args:
        parameters: Raw parameter dictionary.
        specs: Parameter specification map.
        service: Service name used for error context.
        allow_unknown: Whether unknown parameters should be passed through.

    Returns:
        Dict[str, Any]: Prepared parameters ready for API requests.

    Raises:
        TypeConversionError: If conversion fails.
        TypeValidationError: If type validation fails.
        ValueValidationError: If value validation fails.

    Examples:
        >>> from ._core import _prepare_parameters, ParameterSpec
        >>> specs = {
        ...     "param1": ParameterSpec(converter=int, validator=lambda n, v: v > 0, required=True),
        ...     "param2": ParameterSpec(converter=str, validator=lambda n, v: v in {"option1", "option2"}, required=False),
        ... }
        >>> _prepare_parameters({"param1": "123", "param2": "option1"}, specs=specs, service="TestService")
    """

    if parameters is None:
        parameters = {}

    prepared: Dict[str, Any] = {}

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
    "d", "w", "bw", "m", "q", "sa", "a",
    "wef", "weth", "wew", "wetu", "wem", "wesu", "wesa",
    "bwew", "bwem",
}
"""Set of valid frequency values for FRED API parameters."""

FRED_UNITS = {
    "lin", "chg", "ch1", "pch", "pc1", "pca", "cch", "cca", "log",
}
"""Set of valid units values for FRED API parameters."""

SORT_ORDERS = {"asc", "desc"}
"""Set of valid sort order values for FRED API parameters."""

AGGREGATION_METHODS = {"sum", "avg", "eop"}
"""Set of valid aggregation method values for FRED API parameters."""

OUTPUT_TYPES = {1, 2, 3, 4}
"""Set of valid output type values for FRED API parameters."""

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
"""Set of valid order by values for FRED API parameters."""

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
"""Set of valid region type values for GeoFRED API parameters."""

FRED_PARAMETER_SPECS: Dict[str, ParameterSpec] = {
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
"""Mapping of parameter names to their specifications for FRED API parameters. Each entry defines how to convert and validate the parameter values when preparing API requests."""

GEOFRED_PARAMETER_SPECS: Dict[str, ParameterSpec] = {
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
"""Mapping of parameter names to their specifications for GeoFRED API parameters. Each entry defines how to convert and validate the parameter values when preparing API requests."""

FRASER_PARAMETER_SPECS: Dict[str, ParameterSpec] = {
    "limit": ParameterSpec(validator=_validate_nonnegative_int),
    "page": ParameterSpec(validator=_validate_nonnegative_int),
    "format": ParameterSpec(validator=_validate_str_choice({"json"})),
    "role": ParameterSpec(
        validator=_validate_str_choice(
            {"creator", "contributor", "editor", "repository", "uncertain", "subject"}
        )
    ),
}
"""Mapping of parameter names to their specifications for FRASER API parameters. Each entry defines how to convert and validate the parameter values when preparing API requests."""

def _prepare_fred_parameters(parameters: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Prepare FRED API request parameters by converting and validating them according to the defined specifications.
    
    Args:
        parameters: Raw parameter dictionary to prepare.
    
    Returns:
        Dict[str, Any]: A dictionary of prepared FRED API request parameters.
    
    Raises:
        TypeConversionError: If any parameter value fails to convert properly.
        TypeValidationError: If any parameter value fails type validation.
        ValueValidationError: If any parameter value fails value validation, or if required parameters are missing.

    Examples:
        >>> from ._core import _prepare_fred_parameters
        >>> _prepare_fred_parameters({"limit": "100", "sort_order": "asc"})
        {'limit': 100, 'sort_order': 'asc'}
    """

    return _prepare_parameters(
        parameters,
        FRED_PARAMETER_SPECS,
        service="FRED",
        allow_unknown=True,
    )

def _prepare_geofred_parameters(parameters: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Prepare GeoFRED API request parameters by converting and validating them according to the defined specifications.
    
    Args:
        parameters: Raw parameter dictionary to prepare.
    
    Returns:
        Dict[str, Any]: A dictionary of prepared GeoFRED API request parameters.

    Raises:
        TypeConversionError: If any parameter value fails to convert properly.
        TypeValidationError: If any parameter value fails type validation.
        ValueValidationError: If any parameter value fails value validation, or if required parameters are missing.

    Examples:
        >>> from ._core import _prepare_geofred_parameters
        >>> _prepare_geofred_parameters({"shape": "state", "file_type": "geojson"})
        {'shape': 'state', 'file_type': 'geojson'}
    """

    return _prepare_parameters(
        parameters,
        GEOFRED_PARAMETER_SPECS,
        service="GeoFRED",
        allow_unknown=True,
    )

def _prepare_fraser_parameters(parameters: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Prepare FRASER API request parameters by converting and validating them according to the defined specifications.
    
    Args:
        parameters: Raw parameter dictionary to prepare.
    
    Returns:
        Dict[str, Any]: A dictionary of prepared FRASER API request parameters.
    
    Raises:
        TypeConversionError: If any parameter value fails to convert properly.
        TypeValidationError: If any parameter value fails type validation.
        ValueValidationError: If any parameter value fails value validation, or if required parameters are missing.
    
    Examples:
        >>> from ._core import _prepare_fraser_parameters
        >>> _prepare_fraser_parameters({"limit": "100", "page": "1"})
        {'limit': 100, 'page': 1}
    """

    return _prepare_parameters(
        parameters,
        FRASER_PARAMETER_SPECS,
        service="FRASER",
        allow_unknown=True,
    )

FRED_PREPERATION_FUNCTIONS: Dict[str, Any] = {
    "fred": _prepare_fred_parameters,
    "geofred": _prepare_geofred_parameters,
    "fraser": _prepare_fraser_parameters,
}
"""Mapping of service names to their respective parameter preparation functions."""

def _resolve_preparation_function(parameters: Optional[Mapping[str, Any]], service: str) -> Optional[Dict[str, Any]]:
    """Internal helper function to resolve the appropriate parameter preparation function based on the service name.

    Args:
        service: The name of the service (e.g., "FRED", "GeoFRED", "FRASER").

    Returns:
        Optional[Dict[str, Any]]: The prepared parameters dictionary, or None if the service is unrecognized.

    Raises:
        TypeConversionError: If any parameter value fails to convert properly.
        TypeValidationError: If any parameter value fails type validation.
        ValueValidationError: If any parameter value fails value validation, or if required parameters are missing.
    
    Examples:
        >>> from ._core import _resolve_preparation_function
        >>> _resolve_preparation_function({"limit": "100"}, service="fred")
        {'limit': 100}
    """

    service = service.lower()

    try:
        return FRED_PREPERATION_FUNCTIONS[service](parameters)
    except KeyError as exc:
        raise ParameterServiceError(
            message=f"Unknown service {service!r} for parameter preparation.",
            service=service,
            reason="Unrecognized service name.",
            details={"service": service, "expected_services": tuple(FRED_PREPERATION_FUNCTIONS)},
        ) from exc
