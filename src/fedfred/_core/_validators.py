# filepath: /src/fedfred/_core/_validators.py
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
"""Parameter validation for FRED, GeoFRED, and FRASER API requests.

This module provides the internal validators that endpoint methods run over
their arguments before a request is issued, enforcing expected types, string
formats (dates, times, delimited lists, series identifiers), and value
constraints. Validators share a uniform contract: each takes a parameter name
and a value and either returns ``None`` or raises
:class:`~fedfred.exceptions.TypeValidationError` /
:class:`~fedfred.exceptions.ValueValidationError`. Validators that depend on a
runtime-configured allowed set (:func:`_validate_choice`,
:func:`_validate_str_choice`) are produced by factory functions returning a
callable conforming to :data:`ParameterValidator`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from ..exceptions import TypeValidationError, ValueValidationError

ParameterValidator = Callable[[str, object], None]
"""Type alias for a parameter validator: takes a parameter name and a value, returns ``None``, and raises on invalid input."""

@dataclass(frozen=True, slots=True)
class _ChoiceValidator:
    """Validate that a parameter value is one of an allowed set of choices.

    Constructed by :func:`_validate_choice`; instances are callable with the
    :data:`ParameterValidator` signature.

    Attributes:
        choices (frozenset[object]): The allowed values for the parameter.
    """

    choices: frozenset[object]
    """The allowed values for the parameter."""

    def __call__(
        self,
        parameter: str,
        value: object
    ) -> None:
        """Validate ``value`` against the allowed choices.

        Args:
            parameter (str): The name of the parameter being validated.
            value (object): The value of the parameter to validate.

        Raises:
            ValueValidationError: If ``value`` is not one of the allowed choices.
        """
        if value not in self.choices:
            raise ValueValidationError(
                message=f"Invalid value for parameter {parameter!r}.",
                parameter=parameter,
                reason="Value is not one of the allowed choices.",
                details={
                    "value": value,
                    "choices": tuple(sorted(self.choices, key=str)),
                },
            )


@dataclass(frozen=True, slots=True)
class _StrChoiceValidator:
    """Validate that a parameter value is a string in an allowed set of choices.

    Constructed by :func:`_validate_str_choice`; instances are callable with the
    :data:`ParameterValidator` signature.

    Attributes:
        choices (frozenset[str]): The allowed string values for the parameter.
    """

    choices: frozenset[str]
    """The allowed string values for the parameter."""

    def __call__(
        self,
        parameter: str,
        value: object
    ) -> None:
        """Validate ``value`` is a string and one of the allowed choices.

        Args:
            parameter (str): The name of the parameter being validated.
            value (object): The value of the parameter to validate.

        Raises:
            TypeValidationError: If ``value`` is not a string.
            ValueValidationError: If ``value`` is not one of the allowed choices.
        """
        _validate_str(parameter, value)

        if value not in self.choices:
            raise ValueValidationError(
                message=f"Invalid value for parameter {parameter!r}.",
                parameter=parameter,
                reason="Value is not one of the allowed choices.",
                details={
                    "value": value,
                    "choices": tuple(sorted(self.choices)),
                },
            )

# Scalar Validators
def _validate_type(
    parameter: str,
    value: object,
    expected_type: type | tuple[type, ...]
) -> None:
    """Validate that a parameter value is of an expected type.

    Args:
        parameter (str): The name of the parameter being validated.
        value (object): The value of the parameter to validate.
        expected_type (type | tuple[type, ...]): The expected type, or a tuple of acceptable types.

    Raises:
        TypeValidationError: If ``value`` is not an instance of ``expected_type``.

    Examples:
        >>> from fedfred._core._validators import _validate_type
        >>> _validate_type("limit", 100, int)
        >>> _validate_type("limit", "100", int)  # doctest: +SKIP
    """
    if not isinstance(value, expected_type):
        expected = (
            " | ".join(t.__name__ for t in expected_type)
            if isinstance(expected_type, tuple)
            else expected_type.__name__
        )

        raise TypeValidationError(
            message=f"Invalid type for parameter {parameter!r}.",
            parameter=parameter,
            reason="Type mismatch",
            expected=expected,
            received=type(value).__name__,
        )

def _validate_nonnegative_int(
    parameter: str,
    value: object
) -> None:
    """Validate that a parameter value is a non-negative integer.

    Booleans are rejected even though ``bool`` is a subclass of ``int``, since a
    boolean is never a valid integer parameter.

    Args:
        parameter (str): The name of the parameter being validated.
        value (object): The value of the parameter to validate.

    Raises:
        TypeValidationError: If ``value`` is not an integer, or is a boolean.
        ValueValidationError: If ``value`` is a negative integer.

    Examples:
        >>> from fedfred._core._validators import _validate_nonnegative_int
        >>> _validate_nonnegative_int("limit", 100)
        >>> _validate_nonnegative_int("limit", 0)
        >>> _validate_nonnegative_int("limit", -5)     # doctest: +SKIP
        >>> _validate_nonnegative_int("limit", "100")  # doctest: +SKIP
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

    value_int = cast(int, value)

    if value_int < 0:
        raise ValueValidationError(
            message=f"Invalid value for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected non-negative integer.",
            details={"value": value_int},
        )

def _validate_bool(
    parameter: str,
    value: object
) -> None:
    """Validate that a parameter value is a boolean.

    Args:
        parameter (str): The name of the parameter being validated.
        value (object): The value of the parameter to validate.

    Raises:
        TypeValidationError: If ``value`` is not a boolean.

    Examples:
        >>> from fedfred._core._validators import _validate_bool
        >>> _validate_bool("flag", True)
        >>> _validate_bool("flag", False)
        >>> _validate_bool("flag", "True")  # doctest: +SKIP
    """
    _validate_type(parameter, value, bool)

def _validate_str(
    parameter: str,
    value: object
) -> None:
    """Validate that a parameter value is a string.

    Args:
        parameter (str): The name of the parameter being validated.
        value (object): The value of the parameter to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.

    Examples:
        >>> from fedfred._core._validators import _validate_str
        >>> _validate_str("name", "GDP")
        >>> _validate_str("name", "")
        >>> _validate_str("name", 123)  # doctest: +SKIP
    """
    _validate_type(parameter, value, str)

def _validate_nonempty_str(
    parameter: str,
    value: object
) -> None:
    """Validate that a parameter value is a non-empty string.

    Args:
        parameter (str): The name of the parameter being validated.
        value (object): The value of the parameter to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.
        ValueValidationError: If ``value`` is an empty string.

    Examples:
        >>> from fedfred._core._validators import _validate_nonempty_str
        >>> _validate_nonempty_str("name", "GDP")
        >>> _validate_nonempty_str("name", "")   # doctest: +SKIP
        >>> _validate_nonempty_str("name", 123)  # doctest: +SKIP
    """
    _validate_str(parameter, value)

    if not value:
        raise ValueValidationError(
            message=f"Invalid value for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected non-empty string.",
            details={"value": value},
        )

def _validate_choice(choices: set[int]) -> ParameterValidator:
    """Create a validator that checks a parameter value against allowed choices.

    Args:
        choices (set[int]): The allowed values for the parameter.

    Returns:
        ParameterValidator: A validator that raises if a value is not in ``choices``.

    Examples:
        >>> from fedfred._core._validators import _validate_choice
        >>> validate_sort_order = _validate_choice({1, 2, 3})
        >>> validate_sort_order("sort_order", 1)
        >>> validate_sort_order("sort_order", 4)  # doctest: +SKIP
    """
    return _ChoiceValidator(frozenset(choices))

def _validate_str_choice(choices: set[str]) -> ParameterValidator:
    """Create a validator that checks a parameter value is a string in allowed choices.

    Args:
        choices (set[str]): The allowed string values for the parameter.

    Returns:
        ParameterValidator: A validator that raises if a value is not a string or not in ``choices``.

    Examples:
        >>> from fedfred._core._validators import _validate_str_choice
        >>> validate_sort_order = _validate_str_choice({"asc", "desc"})
        >>> validate_sort_order("sort_order", "asc")
        >>> validate_sort_order("sort_order", "ascending")  # doctest: +SKIP
    """
    return _StrChoiceValidator(frozenset(choices))

def _validate_yyyy_mm_dd(
    parameter: str,
    value: object
) -> None:
    """Validate that a parameter value is a string in ``YYYY-MM-DD`` date format.

    Args:
        parameter (str): The name of the parameter being validated.
        value (object): The value of the parameter to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.
        ValueValidationError: If ``value`` is not a valid ``YYYY-MM-DD`` date string.

    Examples:
        >>> from fedfred._core._validators import _validate_yyyy_mm_dd
        >>> _validate_yyyy_mm_dd("realtime_start", "2020-01-01")
        >>> _validate_yyyy_mm_dd("realtime_start", "2020-13-01")  # doctest: +SKIP
        >>> _validate_yyyy_mm_dd("realtime_start", "01-01-2020")  # doctest: +SKIP
        >>> _validate_yyyy_mm_dd("realtime_start", 20200101)      # doctest: +SKIP
    """
    _validate_str(parameter, value)

    value_str = cast(str, value)

    try:
        datetime.strptime(value_str, "%Y-%m-%d")

    except ValueError as exc:
        raise ValueValidationError(
            message=f"Invalid date string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected YYYY-MM-DD date string.",
            details={
                "value": value_str,
                "expected_format": "YYYY-MM-DD",
            },
            original_exception=exc,
        ) from exc

def _validate_hh_mm(
    parameter: str,
    value: object
) -> None:
    """Validate that a parameter value is a string in ``HH:MM`` 24-hour time format.

    Args:
        parameter (str): The name of the parameter being validated.
        value (object): The value of the parameter to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.
        ValueValidationError: If ``value`` is not a valid ``HH:MM`` time string.

    Examples:
        >>> from fedfred._core._validators import _validate_hh_mm
        >>> _validate_hh_mm("start_time", "14:30")
        >>> _validate_hh_mm("start_time", "25:00")    # doctest: +SKIP
        >>> _validate_hh_mm("start_time", "14:60")    # doctest: +SKIP
        >>> _validate_hh_mm("start_time", "2:30 PM")  # doctest: +SKIP
        >>> _validate_hh_mm("start_time", 1430)       # doctest: +SKIP
    """
    _validate_str(parameter, value)

    value_str = cast(str, value)

    try:
        datetime.strptime(value_str, "%H:%M")

    except ValueError as exc:
        raise ValueValidationError(
            message=f"Invalid time string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected HH:MM time string.",
            details={
                "value": value_str,
                "expected_format": "HH:MM",
            },
            original_exception=exc,
        ) from exc

def _validate_semicolon_list_string(
    parameter: str,
    value: object
) -> None:
    """Validate that a parameter value is a semicolon-separated list of non-empty terms.

    Args:
        parameter (str): The name of the parameter being validated.
        value (object): The value of the parameter to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.
        ValueValidationError: If ``value`` is an empty string or contains empty terms.

    Examples:
        >>> from fedfred._core._validators import _validate_semicolon_list_string
        >>> _validate_semicolon_list_string("tag_names", "tag1;tag2;tag3")
        >>> _validate_semicolon_list_string("tag_names", "")          # doctest: +SKIP
        >>> _validate_semicolon_list_string("tag_names", "tag1;;tag3")  # doctest: +SKIP
    """
    _validate_str(parameter, value)

    value_str = cast(str, value)

    if value_str == "":
        raise ValueValidationError(
            message=f"Invalid list-string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Value cannot be empty.",
            details={"value": value_str},
        )

    terms = value_str.split(";")

    if any(term == "" for term in terms):
        raise ValueValidationError(
            message=f"Invalid list-string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Empty terms are not permitted.",
            details={"value": value_str, "separator": ";"},
        )

def _validate_comma_date_list_string(
    parameter: str,
    value: object
) -> None:
    """Validate that a parameter value is a comma-separated list of ``YYYY-MM-DD`` dates.

    Args:
        parameter (str): The name of the parameter being validated.
        value (object): The value of the parameter to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.
        ValueValidationError: If ``value`` is empty, contains empty terms, or contains any term that is not a valid ``YYYY-MM-DD`` date.

    Examples:
        >>> from fedfred._core._validators import _validate_comma_date_list_string
        >>> _validate_comma_date_list_string("vintage_dates", "2020-01-01,2020-02-01,2020-03-01")
        >>> _validate_comma_date_list_string("vintage_dates", "")                      # doctest: +SKIP
        >>> _validate_comma_date_list_string("vintage_dates", "2020-01-01,,2020-03-01")  # doctest: +SKIP
    """
    _validate_str(parameter, value)

    value_str = cast(str, value)

    if value_str == "":
        raise ValueValidationError(
            message=f"Invalid vintage_dates for parameter {parameter!r}.",
            parameter=parameter,
            reason="Value cannot be empty.",
            details={"value": value_str},
        )

    terms = value_str.split(",")

    if any(term == "" for term in terms):
        raise ValueValidationError(
            message=f"Invalid vintage_dates for parameter {parameter!r}.",
            parameter=parameter,
            reason="Empty date terms are not permitted.",
            details={"value": value_str, "separator": ","},
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
                "value": value_str,
                "invalid_terms": tuple(invalid_terms),
                "expected_format": "YYYY-MM-DD",
            },
        )

def _validate_series_id(
    parameter: str,
    value: object
) -> None:
    """Validate that a parameter value is a non-empty series identifier without whitespace.

    Args:
        parameter (str): The name of the parameter being validated.
        value (object): The value of the parameter to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.
        ValueValidationError: If ``value`` is an empty string or contains whitespace.

    Examples:
        >>> from fedfred._core._validators import _validate_series_id
        >>> _validate_series_id("series_id", "GDP")
        >>> _validate_series_id("series_id", "GDP2020")
        >>> _validate_series_id("series_id", "")         # doctest: +SKIP
        >>> _validate_series_id("series_id", "GDP 2020")  # doctest: +SKIP
        >>> _validate_series_id("series_id", 12345)       # doctest: +SKIP
    """
    _validate_nonempty_str(parameter, value)

    value_str = cast(str, value)

    if " " in value_str:
        raise ValueValidationError(
            message=f"Invalid series_id for parameter {parameter!r}.",
            parameter=parameter,
            reason="Series ID cannot contain whitespace.",
            details={"value": value_str},
        )
