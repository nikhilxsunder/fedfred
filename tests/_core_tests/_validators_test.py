# filepath: /tests/_core_tests/_validators_test.py
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

import numpy as np
import pytest

from fedfred._core._validators import (
    _validate_bool,
    _validate_choice,
    _validate_comma_date_list_string,
    _validate_hh_mm,
    _validate_nonempty_str,
    _validate_nonnegative_int,
    _validate_observation_columns,
    _validate_semicolon_list_string,
    _validate_series_id,
    _validate_str,
    _validate_str_choice,
    _validate_type,
    _validate_yyyy_mm_dd,
)
from fedfred.exceptions import TypeValidationError, ValueValidationError


def test_validate_observation_columns() -> None:
    date = np.array(["2020-01-01", "2020-02-01"], dtype="datetime64[D]")
    value = np.array([1.0, 2.0])

    # valid: ndarray, 1-D, correct dtype kinds, equal length -> None
    assert _validate_observation_columns(date=date, value=value) is None

    # empty call: no columns -> trivially valid
    assert _validate_observation_columns() is None

    # a column name not in the schema skips the dtype check (kind is None)
    assert _validate_observation_columns(unknown=np.array([1, 2, 3])) is None

    # not an ndarray -> TypeValidationError
    with pytest.raises(TypeValidationError) as exc:
        _validate_observation_columns(value=[1.0, 2.0])
    assert "must be a numpy.ndarray" in str(exc.value)

    # not 1-D -> ValueValidationError
    with pytest.raises(ValueValidationError) as exc:
        _validate_observation_columns(value=np.array([[1.0], [2.0]]))
    assert "must be 1-D" in str(exc.value)

    # wrong dtype kind for a schema column ("value" expects "f", got "U")
    with pytest.raises(TypeValidationError) as exc:
        _validate_observation_columns(value=np.array(["x", "y"]))
    assert "dtype kind" in str(exc.value)

    # unequal lengths -> ValueValidationError
    with pytest.raises(ValueValidationError) as exc:
        _validate_observation_columns(date=date, value=np.array([1.0]))
    assert "equal length" in str(exc.value)


def test_validate_type() -> None:
    assert _validate_type("p", 100, int) is None
    assert _validate_type("p", "x", (int, str)) is None      # tuple, matches

    # single expected type mismatch
    with pytest.raises(TypeValidationError) as exc:
        _validate_type("p", "x", int)
    assert exc.value.parameter == "p"
    assert exc.value.reason == "Type mismatch"
    assert exc.value.expected == "int"
    assert exc.value.received == "str"

    # tuple expected type mismatch -> expected joined with " | "
    with pytest.raises(TypeValidationError) as exc:
        _validate_type("p", 1.5, (int, str))
    assert exc.value.expected == "int | str"
    assert exc.value.received == "float"


def test_validate_nonnegative_int() -> None:
    assert _validate_nonnegative_int("limit", 100) is None
    assert _validate_nonnegative_int("limit", 0) is None

    # non-int -> TypeValidationError (via _validate_type)
    with pytest.raises(TypeValidationError) as exc:
        _validate_nonnegative_int("limit", "100")
    assert exc.value.received == "str"

    # bool rejected even though bool is a subclass of int
    with pytest.raises(TypeValidationError) as exc:
        _validate_nonnegative_int("limit", True)
    assert exc.value.expected == "int"
    assert exc.value.received == "bool"

    # negative -> ValueValidationError
    with pytest.raises(ValueValidationError) as exc:
        _validate_nonnegative_int("limit", -5)
    assert exc.value.reason == "Expected non-negative integer."
    assert exc.value.context["value"] == -5


def test_validate_bool() -> None:
    assert _validate_bool("flag", True) is None
    assert _validate_bool("flag", False) is None

    # 1 is an int, not a bool -> TypeValidationError
    with pytest.raises(TypeValidationError) as exc:
        _validate_bool("flag", 1)
    assert exc.value.expected == "bool"
    assert exc.value.received == "int"


def test_validate_str() -> None:
    assert _validate_str("name", "GDP") is None
    assert _validate_str("name", "") is None          # empty string IS a valid str

    with pytest.raises(TypeValidationError) as exc:
        _validate_str("name", 123)
    assert exc.value.received == "int"


def test_validate_nonempty_str() -> None:
    assert _validate_nonempty_str("name", "GDP") is None

    # empty string -> ValueValidationError
    with pytest.raises(ValueValidationError) as exc:
        _validate_nonempty_str("name", "")
    assert exc.value.reason == "Expected non-empty string."

    # wrong type -> TypeValidationError (via _validate_str)
    with pytest.raises(TypeValidationError):
        _validate_nonempty_str("name", 123)


def test_validate_choice() -> None:
    validate = _validate_choice({1, 2, 3})
    assert validate("sort", 1) is None

    with pytest.raises(ValueValidationError) as exc:
        validate("sort", 4)
    assert exc.value.parameter == "sort"
    assert exc.value.reason == "Value is not one of the allowed choices."
    assert exc.value.context["value"] == 4
    assert exc.value.context["choices"] == (1, 2, 3)


def test_validate_str_choice() -> None:
    validate = _validate_str_choice({"asc", "desc"})
    assert validate("order", "asc") is None

    # right type, disallowed value -> ValueValidationError
    with pytest.raises(ValueValidationError) as exc:
        validate("order", "ascending")
    assert exc.value.context["choices"] == ("asc", "desc")   # sorted

    # not a string -> TypeValidationError (str check runs first)
    with pytest.raises(TypeValidationError) as exc:
        validate("order", 123)
    assert exc.value.received == "int"


def test_validate_yyyy_mm_dd() -> None:
    assert _validate_yyyy_mm_dd("realtime_start", "2020-01-01") is None

    # not a string -> TypeValidationError
    with pytest.raises(TypeValidationError):
        _validate_yyyy_mm_dd("realtime_start", 20200101)

    # impossible calendar date -> ValueValidationError, chaining the ValueError
    with pytest.raises(ValueValidationError) as exc:
        _validate_yyyy_mm_dd("realtime_start", "2020-13-01")
    assert exc.value.reason == "Expected YYYY-MM-DD date string."
    assert isinstance(exc.value.original_exception, ValueError)
    assert exc.value.__cause__ is exc.value.original_exception

    # wrong format -> ValueValidationError
    with pytest.raises(ValueValidationError):
        _validate_yyyy_mm_dd("realtime_start", "01-01-2020")


def test_validate_hh_mm() -> None:
    assert _validate_hh_mm("start_time", "14:30") is None

    with pytest.raises(TypeValidationError):
        _validate_hh_mm("start_time", 1430)

    for bad in ("25:00", "14:60", "2:30 PM"):
        with pytest.raises(ValueValidationError):
            _validate_hh_mm("start_time", bad)


def test_validate_semicolon_list_string() -> None:
    assert _validate_semicolon_list_string("tag_names", "tag1;tag2;tag3") is None
    assert _validate_semicolon_list_string("tag_names", "single") is None

    with pytest.raises(TypeValidationError):
        _validate_semicolon_list_string("tag_names", 123)

    # empty string
    with pytest.raises(ValueValidationError) as exc:
        _validate_semicolon_list_string("tag_names", "")
    assert exc.value.reason == "Value cannot be empty."

    # empty interior/edge terms
    for bad in ("tag1;;tag3", ";tag", "tag;"):
        with pytest.raises(ValueValidationError) as exc:
            _validate_semicolon_list_string("tag_names", bad)
        assert exc.value.reason == "Empty terms are not permitted."


def test_validate_comma_date_list_string() -> None:
    assert (
        _validate_comma_date_list_string("vintage_dates", "2020-01-01,2020-02-01,2020-03-01")
        is None
    )

    with pytest.raises(TypeValidationError):
        _validate_comma_date_list_string("vintage_dates", 123)

    # empty string
    with pytest.raises(ValueValidationError) as exc:
        _validate_comma_date_list_string("vintage_dates", "")
    assert exc.value.reason == "Value cannot be empty."

    # empty term between commas
    with pytest.raises(ValueValidationError) as exc:
        _validate_comma_date_list_string("vintage_dates", "2020-01-01,,2020-03-01")
    assert exc.value.reason == "Empty date terms are not permitted."

    # a non-empty but invalid date term -> collected into invalid_terms
    with pytest.raises(ValueValidationError) as exc:
        _validate_comma_date_list_string("vintage_dates", "2020-01-01,2020-13-01")
    assert exc.value.reason == "One or more date terms are invalid."
    assert exc.value.context["invalid_terms"] == ("2020-13-01",)


def test_validate_series_id() -> None:
    assert _validate_series_id("series_id", "GDP") is None
    assert _validate_series_id("series_id", "GDP2020") is None

    # empty -> ValueValidationError (via _validate_nonempty_str)
    with pytest.raises(ValueValidationError) as exc:
        _validate_series_id("series_id", "")
    assert exc.value.reason == "Expected non-empty string."

    # non-string -> TypeValidationError (via _validate_str)
    with pytest.raises(TypeValidationError):
        _validate_series_id("series_id", 12345)

    # whitespace -> ValueValidationError
    with pytest.raises(ValueValidationError) as exc:
        _validate_series_id("series_id", "GDP 2020")
    assert exc.value.reason == "Series ID cannot contain whitespace."