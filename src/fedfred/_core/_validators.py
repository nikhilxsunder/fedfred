# filepath: /src/fedfred/_core/_validators.py
#
# Copyright (c) 2025-2026 Nikhil Sunder
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

from __future__ import annotations
from typing import Callable, Any
from datetime import datetime
from ..exceptions import ValueValidationError, TypeValidationError

__all__ = [
    # Typing Aliases
    "ParameterValidator",
    # Scalar Validators
    "_validate_type",
    "_validate_str",
    "_validate_nonempty_str",
    "_validate_bool",
    "_validate_nonnegative_int",
    "_validate_choice",
    "_validate_str_choice",
    "_validate_yyyy_mm_dd",
    "_validate_hh_mm",
    "_validate_semicolon_list_string",
    "_validate_comma_date_list_string",
    "_validate_series_id",
]

ParameterValidator = Callable[[str, Any], None]
"""Typing alias for parameter validator functions. These functions take a parameter name and a value, and raise an exception if the value is invalid."""

# Scalar Validators
def _validate_type(parameter: str, value: Any, expected_type: type | tuple[type, ...]) -> None:
    """Internal validator function to check if a parameter value is of the expected type.
    
    Args:
        parameter (str): The name of the parameter being validated.
        value (Any): The value of the parameter to validate.
        expected_type (type | tuple[type, ...]): The expected type or tuple of types for the parameter.

    Raises:
        TypeValidationError: If the value is not of the expected type.

    Examples:
        >>> # Internal use
        >>> from ._core import _validate_type
        >>> _validate_type("limit", 100, int)  # Valid case
        >>> _validate_type("limit", -5, int)   # Valid case (type is correct, value validation is separate)
        >>> _validate_type("limit", "100", int) # Invalid case (raises TypeValidationError)
    """

    if not isinstance(value, expected_type):
        if isinstance(expected_type, tuple):
            expected = " | ".join(t.__name__ for t in expected_type)
        else:
            expected = expected_type.__name__

        raise TypeValidationError(
            message=f"Invalid type for parameter {parameter!r}.",
            parameter=parameter,
            reason="Type mismatch",
            expected=expected,
            received=type(value).__name__,
        )

def _validate_nonnegative_int(parameter: str, value: Any) -> None:
    """Internal validator function to check if a parameter value is a non-negative integer.
    
    Args:
        parameter (str): The name of the parameter being validated.
        value (Any): The value of the parameter to validate.
    
    Raises:
        TypeValidationError: If the value is not an integer.
        ValueValidationError: If the value is a negative integer.

    Examples:
        >>> # Internal use
        >>> from ._core import _validate_nonnegative_int
        >>> _validate_nonnegative_int("limit", 100)  # Valid case
        >>> _validate_nonnegative_int("limit", 0)    # Valid case
        >>> _validate_nonnegative_int("limit", -5)   # Invalid case (raises ValueValidationError)
        >>> _validate_nonnegative_int("limit", "100") # Invalid case (raises TypeValidationError)
    """

    _validate_type(parameter, value, int)

    if isinstance(value, bool):
        raise TypeValidationError(
            message=f"Invalid type for parameter {parameter!r}.",
            parameter=parameter,
            reason="Boolean is not accepted where integer is required.",
            expected="int",
            received="bool",
        )

    if value < 0:
        raise ValueValidationError(
            message=f"Invalid value for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected non-negative integer.",
            details={"value": value},
        )

def _validate_bool(parameter: str, value: Any) -> None:
    """Internal validator function to check if a parameter value is a boolean.
    
    Args:
        parameter (str): The name of the parameter being validated.
        value (Any): The value of the parameter to validate.
    
    Raises:
        TypeValidationError: If the value is not a boolean.

    Examples:
        >>> # Internal use
        >>> from ._core import _validate_bool
        >>> _validate_bool("flag", True)  # Valid case
        >>> _validate_bool("flag", False) # Valid case
        >>> _validate_bool("flag", "True") # Invalid case (raises TypeValidationError)
    """

    _validate_type(parameter, value, bool)

def _validate_str(parameter: str, value: Any) -> None:
    """Internal validator function to check if a parameter value is a string.
    
    Args:
        parameter (str): The name of the parameter being validated.
        value (Any): The value of the parameter to validate.
    
    Raises:
        TypeValidationError: If the value is not a string.

    Examples:
        >>> # Internal use
        >>> from ._core import _validate_str
        >>> _validate_str("name", "GDP")  # Valid case
        >>> _validate_str("name", "")     # Valid case (empty string is still a string)
        >>> _validate_str("name", 123)  # Invalid case (raises TypeValidationError)
    """

    _validate_type(parameter, value, str)

def _validate_nonempty_str(parameter: str, value: Any) -> None:
    """Internal validator function to check if a parameter value is a non-empty string.
    
    Args:
        parameter (str): The name of the parameter being validated.
        value (Any): The value of the parameter to validate.

    Raises:
        TypeValidationError: If the value is not a string.
        ValueValidationError: If the value is an empty string.

    Examples:
        >>> # Internal use
        >>> from ._core import _validate_nonempty_str
        >>> _validate_nonempty_str("name", "GDP")  # Valid case
        >>> _validate_nonempty_str("name", "")     # Invalid case (raises ValueValidationError)
        >>> _validate_nonempty_str("name", 123)  # Invalid case (raises TypeValidationError)
    """

    _validate_str(parameter, value)

    if not value:
        raise ValueValidationError(
            message=f"Invalid value for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected non-empty string.",
            details={"value": value},
        )

def _validate_choice(choices: set[Any]) -> ParameterValidator:
    """Internal factory function to create a validator that checks if a parameter value is one of a set of allowed choices.
    
    Args:
        choices (set[Any]): A set of allowed values for the parameter.

    Returns:
        ParameterValidator: A validator function that checks if a parameter value is in the specified set of choices.

    Raises:
        ValueValidationError: If the value is not one of the allowed choices.

    Examples:
        >>> # Internal use
        >>> from ._core import _validate_choice
        >>> validate_sort_order = _validate_choice({"asc", "desc"})
        >>> validate_sort_order("sort_order", "asc")  # Valid case
        >>> validate_sort_order("sort_order", "desc") # Valid case
        >>> validate_sort_order("sort_order", "ascending") # Invalid case (raises ValueValidationError)
    """

    def validator(parameter: str, value: Any) -> None:
        """Validator function to check if a parameter value is one of the allowed choices.
        
        Args:
            parameter (str): The name of the parameter being validated.
            value (Any): The value of the parameter to validate.

        Raises:
            ValueValidationError: If the value is not one of the allowed choices.

        Examples:
            >>> # Internal use
            >>> from ._core import _validate_choice
            >>> validate_sort_order = _validate_choice({"asc", "desc"})
            >>> validate_sort_order("sort_order", "asc")  # Valid case
            >>> validate_sort_order("sort_order", "desc") # Valid case
            >>> validate_sort_order("sort_order", "ascending") # Invalid case (raises ValueValidationError)
        """

        if value not in choices:
            raise ValueValidationError(
                message=f"Invalid value for parameter {parameter!r}.",
                parameter=parameter,
                reason="Value is not one of the allowed choices.",
                details={
                    "value": value,
                    "choices": tuple(sorted(choices)),
                },
            )

    return validator

def _validate_str_choice(choices: set[str]) -> ParameterValidator:
    """Internal factory function to create a validator that checks if a parameter value is a string and one of a set of allowed choices.
    
    Args:
        choices (set[str]): A set of allowed string values for the parameter.

    Returns:
        ParameterValidator: A validator function that checks if a parameter value is a string and in the specified set of choices.

    Raises:
        TypeValidationError: If the value is not a string.
        ValueValidationError: If the value is not one of the allowed choices.

    Examples:
        >>> # Internal use
        >>> from ._core import _validate_str_choice
        >>> validate_sort_order = _validate_str_choice({"asc", "desc"})
        >>> validate_sort_order("sort_order", "asc")  # Valid case
        >>> validate_sort_order("sort_order", "desc") # Valid case
        >>> validate_sort_order("sort_order", "ascending") # Invalid case (raises ValueValidationError)
    """

    def validator(parameter: str, value: Any) -> None:
        """Validator function to check if a parameter value is a string and one of the allowed choices.
        
        Args:
            parameter (str): The name of the parameter being validated.
            value (Any): The value of the parameter to validate.

        Raises:
            TypeValidationError: If the value is not a string.
            ValueValidationError: If the value is not one of the allowed choices.

        Examples:
            >>> # Internal use
            >>> from ._core import _validate_str_choice
            >>> validate_sort_order = _validate_str_choice({"asc", "desc"})
            >>> validate_sort_order("sort_order", "asc")  # Valid case
            >>> validate_sort_order("sort_order", "desc") # Valid case
            >>> validate_sort_order("sort_order", "ascending") # Invalid case (raises ValueValidationError)
        """

        _validate_str(parameter, value)

        if value not in choices:
            raise ValueValidationError(
                message=f"Invalid value for parameter {parameter!r}.",
                parameter=parameter,
                reason="Value is not one of the allowed choices.",
                details={
                    "value": value,
                    "choices": tuple(sorted(choices)),
                },
            )

    return validator

def _validate_yyyy_mm_dd(parameter: str, value: Any) -> None:
    """Internal validator function to check if a parameter value is a string in YYYY-MM-DD date format.
    
    Args:
        parameter (str): The name of the parameter being validated.
        value (Any): The value of the parameter to validate.

    Raises:
        TypeValidationError: If the value is not a string.
        ValueValidationError: If the value is not a valid YYYY-MM-DD date string.

    Examples:
        >>> # Internal use
        >>> from ._core import _validate_yyyy_mm_dd
        >>> _validate_yyyy_mm_dd("realtime_start", "2020-01-01")  # Valid case
        >>> _validate_yyyy_mm_dd("realtime_start", "2020-13-01")  # Invalid case (raises ValueValidationError)
        >>> _validate_yyyy_mm_dd("realtime_start", "01-01-2020")  # Invalid case (raises ValueValidationError)
        >>> _validate_yyyy_mm_dd("realtime_start", 20200101)      # Invalid case (raises TypeValidationError)
    """

    _validate_str(parameter, value)

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueValidationError(
            message=f"Invalid date string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected YYYY-MM-DD date string.",
            details={
                "value": value,
                "expected_format": "YYYY-MM-DD",
            },
            original_exception=exc,
        ) from exc

def _validate_hh_mm(parameter: str, value: Any) -> None:
    """Internal validator function to check if a parameter value is a string in HH:MM time format.
    
    Args:
        parameter (str): The name of the parameter being validated.
        value (Any): The value of the parameter to validate.

    Raises:
        TypeValidationError: If the value is not a string.
        ValueValidationError: If the value is not a valid HH:MM time string.

    Examples:
        >>> # Internal use
        >>> from ._core import _validate_hh_mm
        >>> _validate_hh_mm("start_time", "14:30")  # Valid case
        >>> _validate_hh_mm("start_time", "25:00")  # Invalid case (raises ValueValidationError)
        >>> _validate_hh_mm("start_time", "14:60")  # Invalid case (raises ValueValidationError)
        >>> _validate_hh_mm("start_time", "2:30 PM") # Invalid case (raises ValueValidationError)
        >>> _validate_hh_mm("start_time", 1430)      # Invalid case (raises TypeValidationError)
    """

    _validate_str(parameter, value)

    try:
        datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValueValidationError(
            message=f"Invalid time string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected HH:MM time string.",
            details={
                "value": value,
                "expected_format": "HH:MM",
            },
            original_exception=exc,
        ) from exc

def _validate_semicolon_list_string(parameter: str, value: Any) -> None:
    """Internal validator function to check if a parameter value is a string that represents a list of terms separated by semicolons.

    Args:
        parameter (str): The name of the parameter being validated.
        value (Any): The value of the parameter to validate.

    Raises:
        TypeValidationError: If the value is not a string.
        ValueValidationError: If the value is an empty string or contains empty terms.

    Examples:
        >>> # Internal use
        >>> from ._core import _validate_semicolon_list_string
        >>> _validate_semicolon_list_string("tag_names", "tag1;tag2;tag3")  # Valid case
        >>> _validate_semicolon_list_string("tag_names", "")  # Invalid case (raises ValueValidationError)
        >>> _validate_semicolon_list_string("tag_names", "tag1;;tag3")  # Invalid case (raises ValueValidationError)
    """

    _validate_str(parameter, value)

    if value == "":
        raise ValueValidationError(
            message=f"Invalid list-string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Value cannot be empty.",
            details={"value": value},
        )

    terms = value.split(";")

    if any(term == "" for term in terms):
        raise ValueValidationError(
            message=f"Invalid list-string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Empty terms are not permitted.",
            details={"value": value, "separator": ";"},
        )

def _validate_comma_date_list_string(parameter: str, value: Any) -> None:
    """Internal validator function to check if a parameter value is a string that represents a list of date terms separated by commas, where each term is in YYYY-MM-DD format.
    
    Args:
        parameter (str): The name of the parameter being validated.
        value (Any): The value of the parameter to validate.

    Raises:
        TypeValidationError: If the value is not a string.
        ValueValidationError: If the value is an empty string, contains empty terms, or if any term is not a valid YYYY-MM-DD date string.

    Examples:   
        >>> # Internal use
        >>> from ._core import _validate_comma_date_list_string
        >>> _validate_comma_date_list_string("vintage_dates", "2020-01-01,2020-02-01,2020-03-01")  # Valid case
        >>> _validate_comma_date_list_string("vintage_dates", "")  # Invalid case (raises ValueValidationError)
        >>> _validate_comma_date_list_string("vintage_dates", "2020-01-01,,2020-03-01")  # Invalid case (raises ValueValidationError)
    """

    _validate_str(parameter, value)

    if value == "":
        raise ValueValidationError(
            message=f"Invalid vintage_dates for parameter {parameter!r}.",
            parameter=parameter,
            reason="Value cannot be empty.",
            details={"value": value},
        )

    terms = value.split(",")

    if any(term == "" for term in terms):
        raise ValueValidationError(
            message=f"Invalid vintage_dates for parameter {parameter!r}.",
            parameter=parameter,
            reason="Empty date terms are not permitted.",
            details={"value": value, "separator": ","},
        )

    invalid_terms: list[str] = []

    for term in terms:
        try:
            datetime.strptime(term, "%Y-%m-%d")
        except ValueError:
            invalid_terms.append(term)

    if invalid_terms:
        raise ValueValidationError(
            message=f"Invalid vintage_dates for parameter {parameter!r}.",
            parameter=parameter,
            reason="One or more date terms are invalid.",
            details={
                "value": value,
                "invalid_terms": tuple(invalid_terms),
                "expected_format": "YYYY-MM-DD",
            },
        )

def _validate_series_id(parameter: str, value: Any) -> None:
    """Internal validator function to check if a parameter value is a valid series_id string (non-empty, alphanumeric, no spaces).
    
    Args:
        parameter (str): The name of the parameter being validated.
        value (Any): The value of the parameter to validate.

    Raises:
        TypeValidationError: If the value is not a string.
        ValueValidationError: If the value is an empty string, contains spaces, or is not alphanumeric.

    Examples:
        >>> # Internal use
        >>> from ._core import _validate_series_id
        >>> _validate_series_id("series_id", "GDP")  # Valid case
        >>> _validate_series_id("series_id", "GDP2020")  # Valid case
        >>> _validate_series_id("series_id", "")  # Invalid case (raises ValueValidationError)
        >>> _validate_series_id("series_id", "GDP 2020")  # Invalid case (raises ValueValidationError)
        >>> _validate_series_id("series_id", "GDP-2020")  # Invalid case (raises ValueValidationError)
        >>> _validate_series_id("series_id", 12345)  # Invalid case (raises TypeValidationError)
    """

    _validate_nonempty_str(parameter, value)

    if " " in value:
        raise ValueValidationError(
            message=f"Invalid series_id for parameter {parameter!r}.",
            parameter=parameter,
            reason="Series ID cannot contain whitespace.",
            details={"value": value},
        )
