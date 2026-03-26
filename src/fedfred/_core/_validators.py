# filepath: /src/fedfred/_core/_validators.py
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
"""fedfred._core._validators

This module provides internal validation methods for request parameters sent to the FRED, GeoFRED, and FRASER API. These methods are used to validate 
parameters passed to the various API endpoint methods, ensuring that they conform to expected types, formats, 
and value constraints before being sent in API requests.
"""

from typing import Optional, Dict, Union, Callable, Any
from datetime import datetime
import asyncio
from ..exceptions import ValueValidationError, TypeValidationError

# Single Parameter Validators
def _datestring_validator(parameter: str, value: str) -> None:
    """Internal validator function to validate date-string formatted parameters.

    Args:
        parameter (str): Name of the parameter being validated (for error messages).
        value (str): Date string to validate.
    Returns:
        None

    Raises:
        TypeValidationError: If parameter is not a string.
        ValueValidationError: If parameter is not a valid date string in YYYY-MM-DD format.

    Examples:
        >>> import fedfred as fd
        >>> param = "2020-01-01"
        >>> result = fd.__datestring_validation("param", param)
        >>> print(result)
        None
    """

    if not isinstance(value, str):
        raise TypeValidationError(
            message="Invalid parameter type. Expected a date string in 'YYYY-MM-DD' format.",
            parameter=parameter,
            reason="Type mismatch",
            expected="str",
            received=type(value).__name__,
        )

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueValidationError(
            message="Invalid date string. Expected format YYYY-MM-DD.",
            parameter=parameter,
            reason="Invalid ISO date format",
            details={
                "value": value,
                "expected_format": "YYYY-MM-DD",
            },
            original_exception=exc,
        ) from exc

def _liststring_validator(parameter: str, value: str) -> None:
    """Helper method to validate list-string formatted parameters.

    Args:
        parameter (str): Name of the parameter being validated (for error messages).
        value (str): Semicolon-separated string to validate.

    Returns:
        None

    Raises:
        ValueValidationError: If param is not a valid semicolon-separated string.

    Examples:
        >>> import fedfred as fd
        >>> param = "tag1;tag2;tag3"
        >>> result = fd.__liststring_validation(param)
        >>> print(result)
        None

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.____liststring_validation.html

    See Also:
        - :meth:`__liststring_conversion`: Convert a list of strings to a semicolon-separated string.
    """

    if not isinstance(value, str):
        raise TypeValidationError(
            message="Invalid parameter type. Expected a semicolon-separated string.",
            parameter=parameter,
            reason="Type mismatch",
            expected="str",
            received=type(value).__name__,
        )

    terms = value.split(';')

    for term in terms:
        if term == '':
            raise ValueValidationError(
                message="Invalid semicolon-separated list-string: empty terms are not permitted.",
                parameter=parameter,
                reason="Empty term(s) present",
                details={
                    "invalid-term": term,
                    "value": value,
                    "separator": ";",
                    "example": "tag1;tag2;tag3",
                },
            )
        if not term.isalnum():
            raise ValueValidationError(
                message="Invalid semicolon-separated list-string: each term must be alphanumeric with no whitespace.",
                parameter=parameter,
                reason="Non-alphanumeric term(s) present",
                details={
                    "invalid-term": term,
                    "value": value,
                    "rule": "isalnum()==True for every term",
                },
            )

def _vintage_dates_validator(parameter: str, value: str) -> None:
    """Helper method to validate vintage_dates parameters.

    Args:
        parameter (str): Name of the parameter being validated (for error messages).
        value (str): Comma-separated string of vintage dates.

    Returns:
        None

    Raises:
        ValueValidationError: If param is not a valid vintage_dates string.

    Examples:
        >>> import fedfred as fd
        >>> param = "2020-01-01"
        >>> result = fd.__vintage_dates_validation(param)
        >>> print(result)
        None

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.____vintage_dates_validation.html

    See Also:
        - :meth:`__vintage_dates_type_conversion`: Convert a vintage_dates parameter to a string.
    """

    if not isinstance(value, str):
        raise TypeValidationError(
            message="Invalid parameter type. Expected a comma-separated date string.",
            parameter=parameter,
            reason="Type mismatch",
            expected="str",
            received=type(value).__name__,
        )

    if value == '':
        raise ValueValidationError(
            message="Invalid vintage_dates: value cannot be empty.",
            parameter=parameter,
            reason="Empty string",
            details={
                "value": value,
                "expected_format": "YYYY-MM-DD or YYYY-MM-DD,YYYY-MM-DD,...",
                "separator": ",",
            },
        )

    terms = value.split(',')

    if any(t == "" for t in terms):
        raise ValueValidationError(
            message="Invalid vintage_dates: empty date term(s) are not permitted.",
            parameter=parameter,
            reason="Empty term(s) present",
            details={
                "value": value,
                "separator": ",",
                "example": "2020-01-01,2020-02-01",
            },
        )

    invalid_terms: list[str] = []
    for term in terms:
        try:
            datetime.strptime(term, "%Y-%m-%d")
        except ValueError:
            invalid_terms.append(term)

    if invalid_terms:
        raise ValueValidationError(
            message="Invalid vintage_dates: one or more dates are not valid YYYY-MM-DD values.",
            parameter=parameter,
            reason="Invalid date term(s)",
            details={
                "value": value,
                "invalid_terms": tuple(invalid_terms),
                "expected_format": "YYYY-MM-DD",
                "separator": ",",
            },
        )

def _hh_mm_datestring_validator(parameter: str, value: str) -> None:
    """Helper method to validate hh:mm formatted parameters.

    Args:
        parameter (str): Name of the parameter being validated (for error messages).
        value (str): Time string to validate.

    Returns:
        None

    Raises:
        TypeValidationError: If param is not a valid time string in HH:MM format.

    Examples:
        >>> import fedfred as fd
        >>> param = "15:30"
        >>> result = fd.__hh_mm_datestring_validation(param)
        >>> print(result)
        None

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.____hh_mm_datestring_validation.html

    See Also:
        - :meth:`__datetime_hh_mm_conversion`: Convert a datetime object to a string in HH:MM format.
    """

    if not isinstance(value, str):
        raise TypeValidationError(
            message="Invalid parameter type. Expected HH:MM time string.",
            parameter=parameter,
            reason="Type mismatch",
            expected="str",
            received=type(value).__name__,
        )
    try:
        datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValueValidationError(
            message=f"Invalid time format for parameter '{parameter}'. Expected HH:MM (24-hour).",
            parameter=parameter,
            reason="Invalid time format",
            details={
                "value": value,
                "expected_format": "HH:MM",
                "range": "00:00-23:59",
                "example": "15:30",
            },
            original_exception=exc,
        ) from exc

async def _datestring_validator_async(parameter: str, value: str) -> None:
    """Helper method to validate date-string formatted parameter asynchronously.

    Args:
        parameter (str): Name of the parameter being validated (for error messages).
        value (str): Date string to validate.

    Returns:
        None

    Raises:
        TypeValidationError: If param is not a valid date string in YYYY-MM-DD format.

    Examples:
        >>> import asyncio
        >>> import fedfred as fd
        >>> param = "2020-01-01"
        >>> async def main():
        >>>     result = await fd.AsyncHelpers.datestring_validation(param)
        >>>     print(result)
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        None

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.datestring_validation.html

    See Also:
        - :meth:`AsyncHelpers.datetime_conversion`: Convert a datetime object to a string in YYYY-MM-DD format asynchronously.
    """

    return await asyncio.to_thread(_datestring_validator, parameter, value)

async def _liststring_validator_async(parameter: str, value: str) -> None:
    """Helper method to validate list-string formatted parameters asynchronously.

    Args:
        parameter (str): Name of the parameter being validated (for error messages).
        value (str): Semicolon-separated string to validate.

    Returns:
        None

    Raises:
        TypeValidationError: If param is not a valid semicolon-separated string.

    Examples:
        >>> import asyncio
        >>> import fedfred as fd
        >>> param = "GDP;CPI;UNRATE"
        >>> async def main():
        >>>     result = await fd.AsyncHelpers.liststring_validation(param)
        >>>     print(result)
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        None
    
    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.liststring_validation.html

    See Also:
        - :meth:`AsyncHelpers.liststring_conversion`: Convert a list of strings to a semicolon-separated string asynchronously.
    """

    return await asyncio.to_thread(_liststring_validator, parameter, value)

async def _vintage_dates_validator_async(parameter: str, value: str) -> None:
    """Helper method to validate vintage_dates parameters asynchronously.

    Args:
        param (str): Comma-separated string of vintage dates.

    Returns:
        None

    Raises:
        TypeValidationError: If param is not a valid vintage_dates string.

    Examples:
        >>> import asyncio
        >>> import fedfred as fd
        >>> param = "2020-01-01"
        >>> async def main():
        >>>     result = await fd.AsyncHelpers.vintage_dates_validation(param)
        >>>     print(result)
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        None

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.vintage_dates_validation.html

    See Also:
        - :meth:`AsyncHelpers.vintage_dates_type_conversion`: Convert a vintage_dates parameter to a string asynchronously.
    """

    return await asyncio.to_thread(_vintage_dates_validator, parameter, value)

async def _hh_mm_datestring_validator_async(parameter: str, value: str) -> None:
    """Helper method to validate hh:mm formatted parameters asynchronously.

    Args:
        parameter (str): Name of the parameter being validated (for error messages).
        value (str): Time string to validate.

    Returns:
        None

    Raises:
        TypeValidationError: If param is not a valid time string in HH:MM format.

    Examples:
        >>> import asyncio
        >>> import fedfred as fd
        >>> param = "14:30"
        >>> async def main():
        >>>     result = await fd.AsyncHelpers.hh_mm_datestring_validation(param)
        >>>     print(result)
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        None

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.hh_mm_datestring_validation.html

    See Also:
        - :meth:`AsyncHelpers.datetime_hh_mm_conversion`: Convert a datetime object to a string in HH:MM format asynchronously.
    """

    return await asyncio.to_thread(_hh_mm_datestring_validator, parameter, value)

# Parameter Specification Maps
_FRED_PARAMETERS_MAP: Dict[str, Dict[str, Optional[Union[Callable, str]]]] = {
    'category_id': 
    {
        'type_condition': lambda x: isinstance(x, int),
        'value_condition': lambda x: x >= 0,
        'error_message': "category_id must be a non-negative integer"
    },
    'realtime_start': 
    {
        'functional_condition': _datestring_validator,
        'async_functional_condition': _datestring_validator_async,
        'error_message': "realtime_start must be a valid date string in 'YYYY-MM-DD' format"
    },
    'realtime_end':
    {
        'functional_condition': _datestring_validator,
        'async_functional_condition': _datestring_validator_async,
        'error_message': "realtime_end must be a valid date string in 'YYYY-MM-DD' format"
    },
    'limit': 
    {
        'type_condition': lambda x: isinstance(x, int), 
        'value_condition': lambda x: x >= 0,
        'error_message': "limit must be a non-negative integer"
    },
    'page': 
    {
        'type_condition': lambda x: isinstance(x, int), 
        'value_condition': lambda x: x >= 0,
        'error_message': "page must be a non-negative integer"
    },
    'format':
    {
        'type_condition': lambda x: isinstance(x, str), 
        'value_condition': lambda x: x == 'json', 
        'error_message': "format must be 'json'"
    },
    'offset': 
    {
        'type_condition': lambda x: isinstance(x, int), 
        'value_condition': lambda x: x >= 0,
        'error_message': "offset must be a non-negative integer"
    },
    'sort_order': 
    {
        'type_condition': lambda x: isinstance(x, str), 
        'value_condition': lambda x: x in {'asc', 'desc'},
        'error_message': "sort_order must be 'asc' or 'desc'"
    },
    'order_by': 
    {
        'type_condition': lambda x: isinstance(x, str), 
        'value_condition': lambda x: x in {'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment',
                                            'realtime_start', 'realtime_end', 'last_updated', 'observation_start',
                                            'observation_end', 'popularity', 'group_popularity', 'series_count',
                                            'created', 'name', 'release_id', 'press_release', 'group_id',
                                            'search_rank'},
        'error_message': "order_by must be one of the valid options"
    },
    'filter_variable':
    {
        'type_condition': lambda x: isinstance(x, str), 
        'value_condition': lambda x: x in {'frequency', 'units', 'seasonal_adjustment'},
        'error_message': "filter_variable must be one of the valid options: 'frequency', 'units', 'seasonal_adjustment'"
    },
    'filter_value': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: len(x) > 0,
        'error_message': "filter_value must be a non-empty string"
    },
    'tag_names': 
    {
        'type_condition': lambda x: isinstance(x, str), 
        'functional_condition': _liststring_validator,
        'async_functional_condition': _liststring_validator_async,
        'error_message': "tag_names must be a valid semicolon-separated string"
    },
    'exclude_tag_names': 
    {
        'type_condition': lambda x: isinstance(x, str), 
        'functional_condition':_liststring_validator,
        'async_functional_condition': _liststring_validator_async,
        'error_message': "exclude_tag_names must be a valid semicolon-separated string"
    },
    'tag_group_id': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'complex_condition': lambda x: isinstance(x, int) and x >= 0,
        'error_message': "tag_group_id must be a non-negative integer or a valid string"
    },
    'search_text': 
    {
        'type_condition': lambda x: isinstance(x, str),
    },
    'file_type': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x == 'json',
        'error_message': "file_type must be 'json'"
    },
    'api_key': 
    {
        'type_condition': lambda x: isinstance(x, str)
    },
    'include_releases_dates_with_no_data': 
    {
        'type_condition': lambda x: isinstance(x, bool)
    },
    'release_id': 
    {
        'type_condition': lambda x: isinstance(x, int),
        'value_condition': lambda x: x >= 0,
        'error_message': "release_id must be a non-negative integer"
    },
    'series_id': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: len(x) > 0 and ' ' not in x and x.isalnum(),
        'error_message': "series_id must be a non-empty alphanumeric string without spaces"
    },
    'frequency': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'d', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'},
        'error_message': "frequency must be one of the valid options: 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'"
    },
    'units': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'},
        'error_message': "units must be one of the valid options: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'"
    },
    'aggregation_method': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'sum', 'avg', 'eop'},
        'error_message': "aggregation_method must be one of the valid options: 'avg', 'sum', 'end_of_period', 'max', 'min'"
    },
    'output_type': 
    {
        'type_condition': lambda x: isinstance(x, int),
        'value_condition': lambda x: x in {1,2,3,4},
        'error_message': "output_type must be one of the valid options: 1, 2, 3, 4"
    },
    'vintage_dates': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'functional_condition': _vintage_dates_validator,
        'async_functional_condition': _vintage_dates_validator_async,
        'error_message': "vintage_dates must be a valid semicolon-separated string"
    },
    'search_type': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'full_text', 'series_id'},
        'error_message': "search_type must be one of the valid options: 'full_text', 'series_id'"
    },
    'tag_search_text':
    {
        'type_condition': lambda x: isinstance(x, str),
        'error_message': "tag_search_text must be a string"
    },
    'start_time':
    {
        'type_condition': lambda x: isinstance(x, str),
        'functional_condition': _hh_mm_datestring_validator,
        'async_functional_condition': _hh_mm_datestring_validator_async,
        'error_message': "start_time must be a valid time string in 'HH:MM' format"
    },
    'end_time':
    {
        'type_condition': lambda x: isinstance(x, str),
        'functional_condition': _hh_mm_datestring_validator,
        'async_functional_condition': _hh_mm_datestring_validator_async,
        'error_message': "end_time must be a valid time string in 'HH:MM' format"
    },
    'season':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'seasonally_adjusted', 'not_seasonally_adjusted'},
        'error_message': "season must be one of the valid options: 'seasonally_adjusted', 'not_seasonally_adjusted'"
    }
}

_GEOFRED_PARAMETERS_MAP: Dict[str, Dict[str, Optional[Union[Callable, str]]]] = {
    'api_key': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'error_message': "api_key must be a string"
    },
    'file_type': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x == 'json',
        'error_message': "file_type must be one of the valid options: 'geojson', 'shp', 'kml', 'gdb', 'gpkg'"
    },
    'shape':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision'},
        'error_message': "shape must be one of the valid options: 'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision'"
    },
    'series_id':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: len(x) > 0 and ' ' not in x and x.isalnum(),
        'error_message': "series_id must be a non-empty alphanumeric string without spaces"
    },
    'date':
    {
        'functional_condition': _datestring_validator,
        'async_functional_condition': _datestring_validator_async,
        'error_message': "date must be a valid date string in 'YYYY-MM-DD' format"
    },
    'start_date':
    {
        'functional_condition': _datestring_validator,
        'async_functional_condition': _datestring_validator_async,
        'error_message': "start_date must be a valid date string in 'YYYY-MM-DD' format"
    },
    'series_group':
    {
        'type_condition': lambda x: isinstance(x, str),
        'error_message': "series_group must be a string"
    },
    'region_type':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision'},
        'error_message': "region_type must be one of the valid options: 'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision'"
    },
    'aggregation_method':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'sum', 'avg', 'eop'},
        'error_message': "aggregation_method must be one of the valid options: 'avg', 'sum', 'end_of_period', 'max', 'min'"
    },
    'units':
    {
        'type_condition': lambda x: isinstance(x, str),
        'error_message': "units must be a valid string"
    },
    'season':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'NSA', 'SA', 'SSA', 'SAAR', 'NSAAR'},
        'error_message': "season must be one of the valid options: 'NSA', 'SA', 'SSA', 'SAAR', 'NSAAR'"
    },
    'transformation':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'},
        'error_message': "transformation must be one of the valid options: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'"
    }
}

_FRASER_PARAMETERS_MAP: Dict[str, Dict[str, Optional[Union[Callable, str]]]] = {
    'limit':
    {
        'type_condition': lambda x: isinstance(x, int),
        'value_condition': lambda x: x >= 0,
        'error_message': "limit must be a non-negative integer"
    },
    'page':
    {
        'type_condition': lambda x: isinstance(x, int),
        'value_condition': lambda x: x >= 0,
        'error_message': "page must be a non-negative integer"
    },
    'format':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x == 'json',
        'error_message': "format must be 'json'"
    },
    'role':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'creator', 'contributor', 'editor', 'repository', 'uncertain', 'subject'},
        'error_message': "role must be one of the valid options: 'creator', 'contributor', 'editor', 'repository', 'uncertain', 'subject'"
    },
}

# Collective Parameter Validators
def _fred_parameter_validator(parameters: Dict[str, Any]) -> None:
    """Helper method to validate parameters prior to making a get request.

    Args:
        parameters (Dict[str, Optional[str | int | bool]]): Dictionary of parameters to validate.

    Returns:
        None

    Raises:
        ValueError: If any parameter is invalid.

    Examples:
        >>> import fedfred as fd
        >>> params = {
        >>>     "category_id": 125,
        >>>     "realtime_start": "2020-01-01",
        >>>     "limit": 100,
        >>>     "sort_order": "asc",
        >>> }
        >>> result = fd.Helpers.parameter_validation(params)
        >>> print(result)
        None

    Notes:
        This method checks each parameter against expected types and formats, raising a ValueError for any invalid parameters.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.parameter_validation.html

    See Also:
        - :meth:`Helpers.datestring_validation`: Validate date-string formatted parameters.
        - :meth:`Helpers.liststring_validation`: Validate list-string formatted parameters.
        - :meth:`Helpers.hh_mm_datestring_validation`: Validate hh:mm formatted parameters.
        - :meth:`Helpers.vintage_dates_validation`: Validate vintage_dates parameters.
    """

    for key, value in parameters.items():
        spec = _FRED_PARAMETERS_MAP.get(key)
        assert spec is None or isinstance(spec, dict)
        if spec is None:
            continue

        type_pred = spec.get("type_condition")
        if callable(type_pred):
            ok = bool(type_pred(value))
            if not ok:
                expected = spec.get("expected_type", "valid type")
                raise TypeValidationError(
                    message=f"Invalid type for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Type validation failed")),
                    expected=str(expected),
                    received=type(value).__name__,
                )

        value_pred = spec.get("value_condition")
        if callable(value_pred):
            ok = bool(value_pred(value))
            if not ok:
                raise ValueValidationError(
                    message=f"Invalid value for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Value validation failed")),
                    details={"value": value},
                )

        func = spec.get("functional_condition")
        if callable(func):
            func(key, value)

        complex_pred = spec.get("complex_condition")
        if callable(complex_pred):
            ok = bool(complex_pred(value, parameters))
            if not ok:
                raise ValueValidationError(
                    message=f"Invalid value for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Complex validation failed")),
                    details={"value": value, "params": dict(parameters)},
                )

def _geofred_parameter_validator(parameters: Dict[str, Any]) -> None:
    """Helper method to validate geo-parameters prior to making a maps get request.

    Args:
        parameters (Dict[str, Optional[str | int | bool]]): Dictionary of parameters to validate

    Returns:
        None

    Raises:
        ValueError: If any parameter is invalid.

    Examples:
        >>> import fedfred as fd
        >>> params = {
        >>>     "api_key": "your_api_key",
        >>>     "file_type": "json",
        >>>     "shape": "state",
        >>>     "series_id": "GDP",
        >>>     "date": "2020-01-01",
        >>>     "start_date": "2010-01-01",
        >>>     "series_group": "group1",
        >>>     "region_type": "state",
        >>>     "aggregation_method": "sum",
        >>>     "units": "lin",
        >>>     "season": "SA",
        >>>     "transformation": "chg",
        >>> }
        >>> result = fd.Helpers.geo_parameter_validation(params)
        >>> print(result)
        None

    Notes:
        This method checks for valid types and values for geo-related parameters.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.geo_parameter_validation.html

    See Also:
        - :meth:`Helpers.datestring_validation`: Validate date-string formatted parameters.
        - :meth:`Helpers.liststring_validation`: Validate list-string formatted parameters.
        - :meth:`Helpers.hh_mm_datestring_validation`: Validate hh:mm formatted parameters.
        - :meth:`Helpers.vintage_dates_validation`: Validate vintage_dates parameters.
    """

    for key, value in parameters.items():
        spec = _GEOFRED_PARAMETERS_MAP.get(key)
        assert spec is None or isinstance(spec, dict)
        if spec is None:
            continue

        type_pred = spec.get("type_condition")
        if callable(type_pred):
            ok = bool(type_pred(value))
            if not ok:
                expected = spec.get("expected_type", "valid type")
                raise TypeValidationError(
                    message=f"Invalid type for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Type validation failed")),
                    expected=str(expected),
                    received=type(value).__name__,
                )

        value_pred = spec.get("value_condition")
        if callable(value_pred):
            ok = bool(value_pred(value))
            if not ok:
                raise ValueValidationError(
                    message=f"Invalid value for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Value validation failed")),
                    details={"value": value},
                )

        func = spec.get("functional_condition")
        if callable(func):
            func(key, value)

def _fraser_parameter_validator(parameters: Dict[str, Any]) -> None:
    """Helper method to validate fraser-parameters prior to making a fraser get request.

    Args:
        parameters (Dict[str, Optional[str | int]]): Dictionary of parameters to validate

    Raises:
        ValueError: If any parameter is invalid.

    Examples:
        >>> import fedfred as fd
        >>> parameters = {
        >>>     "limit": 100,
        >>>     "page": 1,
        >>>     "role": "creator",
        >>> }
        >>> result = fd.Helpers.fraser_parameter_validation(parameters)
        >>> print(result)
        None

    Notes:
        This method checks for valid types and values for fraser-related parameters.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.fraser_parameter_validation.html

    See Also:
        - :meth:`Helpers.parameter_validation`: Validate parameters for standard FRED API requests.
    """

    for key, value in parameters.items():
        spec = _FRASER_PARAMETERS_MAP.get(key)
        assert spec is None or isinstance(spec, dict)
        if spec is None:
            continue

        type_pred = spec.get("type_condition")
        if callable(type_pred):
            ok = bool(type_pred(value))
            if not ok:
                expected = spec.get("expected_type", "valid type")
                raise TypeValidationError(
                    message=f"Invalid type for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Type validation failed")),
                    expected=str(expected),
                    received=type(value).__name__,
                )

        value_pred = spec.get("value_condition")
        if callable(value_pred):
            ok = bool(value_pred(value))
            if not ok:
                raise ValueValidationError(
                    message=f"Invalid value for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Value validation failed")),
                    details={"value": value},
                )

async def _fred_parameter_validator_async(parameters: Dict[str, Any]) -> None:
    """Helper method to validate parameters prior to making a get request asynchronously.

    Args:
        parameters (Dict[str, Optional[str | int | bool ]]): Dictionary of parameters to validate.

    Returns:
        None

    Raises:
        ValueError: If any parameter is invalid.

    Examples:
        >>> import asyncio
        >>> import fedfred as fd
        >>> params = {
        >>>     "category_id": 125,
        >>>     "realtime_start": "2020-01-01",
        >>>     "realtime_end": "2020-12-31",
        >>>     "limit": 100,
        >>>     "offset": 0,
        >>>     "sort_order": "asc",
        >>>     "order_by": "series_id",
        >>>     "filter_variable": "frequency",
        >>>     "filter_value": "m",
        >>>     "tag_names": "GDP;CPI",
        >>>     "exclude_tag_names": "UNRATE",
        >>>     "tag_group_id": 123,
        >>>     "search_text": "economic",
        >>>     "file_type": "json",
        >>>     "api_key": "your_api_key",
        >>>     "include_releases_dates_with_no_data": True,
        >>>     "release_id": 10,
        >>>     "series_id": "GDP",
        >>>     "frequency": "m",
        >>>     "units": "lin",
        >>>     "aggregation_method": "avg",
        >>>     "output_type": 1
        >>> }
        >>> async def main():
        >>>     result = await fd.AsyncHelpers.parameter_validation(params)
        >>>     print(result)
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        None

    Notes:
        This method checks each parameter for correct type and value, raising a ValueError if any parameter is invalid.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.parameter_validation.html

    See Also:
        - :meth:`AsyncHelpers.datestring_validation`: Validate date-string formatted parameters asynchronously.
        - :meth:`AsyncHelpers.liststring_validation`: Validate list-string formatted parameters asynchronously.
        - :meth:`AsyncHelpers.vintage_dates_validation`: Validate vintage_dates parameters asynchronously.
        - :meth:`AsyncHelpers.hh_mm_datestring_validation`: Validate hh:mm formatted parameters asynchronously.
    """

    for key, value in parameters.items():
        spec = _FRED_PARAMETERS_MAP.get(key)
        assert spec is None or isinstance(spec, dict)
        if spec is None:
            continue

        type_pred = spec.get("type_condition")
        if callable(type_pred):
            ok = bool(type_pred(value))
            if not ok:
                expected = spec.get("expected_type", "valid type")
                raise TypeValidationError(
                    message=f"Invalid type for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Type validation failed")),
                    expected=str(expected),
                    received=type(value).__name__,
                )

        value_pred = spec.get("value_condition")
        if callable(value_pred):
            ok = bool(value_pred(value))
            if not ok:
                raise ValueValidationError(
                    message=f"Invalid value for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Value validation failed")),
                    details={"value": value},
                )

        func = spec.get("async_functional_condition")
        if callable(func):
            await func(key, value)

        complex_pred = spec.get("complex_condition")
        if callable(complex_pred):
            ok = bool(complex_pred(value, parameters))
            if not ok:
                raise ValueValidationError(
                    message=f"Invalid value for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Complex validation failed")),
                    details={"value": value, "params": dict(parameters)},
                )

async def _geofred_parameter_validator_async(parameters: Dict[str, Any]) -> None:
    """Helper method to validate parameters prior to making a get request.

    Args:
        parameters (Dict[str, Optional[Union[str, int, bool]]]): Dictionary of parameters to validate

    Returns:
        None

    Raises:
        ValueError: If any parameter is invalid.

    Examples:
        >>> import asyncio
        >>> import fedfred as fd
        >>> params = {
        >>>     "api_key": "your_api_key",
        >>>     "file_type": "json",
        >>>     "shape": "state",
        >>>     "series_id": "GDP",
        >>>     "date": "2020-01-01",
        >>>     "start_date": "2020-01-01",
        >>>     "series_group": "group1",
        >>>     "region_type": "state",
        >>>     "aggregation_method": "avg",
        >>>     "units": "lin",
        >>>     "season": "SA",
        >>>     "transformation": "chg"
        >>> }
        >>> async def main():
        >>>     result = await fd.AsyncHelpers.geo_parameter_validation(params)
        >>>     print(result)
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        None

    Notes:
        This method checks each parameter for correct type and value, raising a ValueError if any parameter is invalid.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.geo_parameter_validation.html

    See Also:
        - :meth:`AsyncHelpers.datestring_validation`: Validate date-string formatted parameters asynchronously.
        - :meth:`AsyncHelpers.liststring_validation`: Validate list-string formatted parameters asynchronously.
        - :meth:`AsyncHelpers.vintage_dates_validation`: Validate vintage_dates parameters asynchronously.
        - :meth:`AsyncHelpers.hh_mm_datestring_validation`: Validate hh:mm formatted parameters asynchronously.
    """

    for key, value in parameters.items():
        spec = _GEOFRED_PARAMETERS_MAP.get(key)
        assert spec is None or isinstance(spec, dict)
        if spec is None:
            continue

        type_pred = spec.get("type_condition")
        if callable(type_pred):
            ok = bool(type_pred(value))
            if not ok:
                expected = spec.get("expected_type", "valid type")
                raise TypeValidationError(
                    message=f"Invalid type for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Type validation failed")),
                    expected=str(expected),
                    received=type(value).__name__,
                )

        value_pred = spec.get("value_condition")
        if callable(value_pred):
            ok = bool(value_pred(value))
            if not ok:
                raise ValueValidationError(
                    message=f"Invalid value for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Value validation failed")),
                    details={"value": value},
                )

        func = spec.get("async_functional_condition")
        if callable(func):
            await func(key, value)

async def _fraser_parameter_validator_async(parameters: Dict[str, Any]) -> None:
    """Helper method to validate parameters for GeoFred requests asynchronously.

    Args:
        parameters (Dict[str, Any]): Dictionary of parameters to validate.

    Raises:
        ValueError: If any parameter is invalid.

    Examples:
        >>> import asyncio
        >>> import fedfred as fd
        >>> params = {
        >>>     "limit": 100,
        >>>     "page": 1,
        >>>     "role": "creator",
        >>> }
        >>> async def main():
        >>>     result = await fd.AsyncHelpers.fraser_parameter_validation(params)
        >>>     print(result)
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        None
    """

    for key, value in parameters.items():
        spec = _FRASER_PARAMETERS_MAP.get(key)
        assert spec is None or isinstance(spec, dict)
        if spec is None:
            continue

        type_pred = spec.get("type_condition")
        if callable(type_pred):
            ok = bool(type_pred(value))
            if not ok:
                expected = spec.get("expected_type", "valid type")
                raise TypeValidationError(
                    message=f"Invalid type for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Type validation failed")),
                    expected=str(expected),
                    received=type(value).__name__,
                )

        value_pred = spec.get("value_condition")
        if callable(value_pred):
            ok = bool(value_pred(value))
            if not ok:
                raise ValueValidationError(
                    message=f"Invalid value for parameter '{key}'.",
                    parameter=key,
                    reason=str(spec.get("error_message", "Value validation failed")),
                    details={"value": value},
                )
