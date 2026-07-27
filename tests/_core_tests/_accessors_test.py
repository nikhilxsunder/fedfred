# filepath: /tests/_core_tests/_accessors_test.py
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

from datetime import date, datetime

import numpy as np
import pytest

from fedfred._core import _accessors, _registries
from fedfred._core._accessors import (
    _cell_date,
    _cell_value,
    _first_date_index,
    _get_api_key,
    _get_dataframe_backend,
    _get_geodataframe_backend,
)
from fedfred._core._defaults import (
    _DEFAULT_DATAFRAME_BACKEND,
    _DEFAULT_GEODATAFRAME_BACKEND,
)
from fedfred.exceptions import ValueValidationError

def test_cell_date() -> None:
    dates = np.array(["2020-01-01", "2020-06-15", "2020-12-31"], dtype="datetime64[D]")

    # --- value + type contract at row 0 -------------------------------------
    result = _cell_date(dates, 0)
    assert result == date(2020, 1, 1)
    # [D] resolution must materialize a *pure* date. datetime subclasses date,
    # so an identity check is required: isinstance(result, date) would also pass
    # for a datetime and let a spurious time component slip through.
    assert type(result) is date
    assert not isinstance(result, datetime)

    # --- reads the requested row, not always row 0 --------------------------
    assert _cell_date(dates, 1) == date(2020, 6, 15)
    assert _cell_date(dates, 2) == date(2020, 12, 31)

    # --- numpy negative indexing is honored (dates[-1] -> last row) ---------
    assert _cell_date(dates, -1) == date(2020, 12, 31)

    # --- single-element column (mirrors the docstring doctest) --------------
    assert _cell_date(np.array(["2020-01-01"], dtype="datetime64[D]"), 0) == date(2020, 1, 1)

    # --- edge dates round-trip exactly, all as pure dates -------------------
    # leap day, unix epoch, pre-epoch (negative day offset), max representable.
    edge = np.array(
        ["2020-02-29", "1970-01-01", "1969-12-31", "9999-12-31"],
        dtype="datetime64[D]",
    )
    expected = [
        date(2020, 2, 29),
        date(1970, 1, 1),
        date(1969, 12, 31),
        date(9999, 12, 31),
    ]
    for i, exp in enumerate(expected):
        cell = _cell_date(edge, i)
        assert cell == exp
        assert type(cell) is date

    # --- out-of-range index surfaces numpy's IndexError (no silent failure) -
    # The accessor deliberately delegates bounds/domain handling to the caller
    # (see the module docstring), so a bad index must propagate, not be masked.
    with pytest.raises(IndexError):
        _cell_date(dates, 99)


def test_cell_value() -> None:
    values = np.array([1.5, np.nan, -2.0, 0.0])

    # --- non-missing branch: exact value, materialized as a builtin float ---
    result = _cell_value(values, 0)
    assert result == 1.5
    # must be a Python float, not np.float64, so the object layer stays clean.
    assert type(result) is float

    # --- missing branch: NaN -> None (the two-layer contract) ---------------
    assert _cell_value(values, 1) is None

    # --- negative values and the requested row are read correctly -----------
    assert _cell_value(values, 2) == -2.0

    # --- 0.0 is a real observation, NOT missing -----------------------------
    # Guards against a `return None if not v` regression: 0.0 is falsy but is a
    # valid value; only NaN maps to None.
    zero = _cell_value(values, 3)
    assert zero == 0.0
    assert zero is not None
    assert type(zero) is float

    # --- numpy negative indexing is honored ---------------------------------
    assert _cell_value(values, -1) == 0.0
    assert _cell_value(values, -3) is None

    # --- infinities are values, not missing (only NaN is the sentinel) ------
    infs = np.array([np.inf, -np.inf])
    assert _cell_value(infs, 0) == float("inf")
    assert _cell_value(infs, 1) == float("-inf")

    # --- out-of-range index propagates IndexError ---------------------------
    with pytest.raises(IndexError):
        _cell_value(values, 99)


def test_first_date_index() -> None:
    dates = np.array(
        ["2020-01-01", "2020-02-01", "2020-02-01", "2020-03-01"],
        dtype="datetime64[D]",
    )

    # --- exact match returns a builtin int index ----------------------------
    idx = _first_date_index(dates, "2020-01-01")
    assert idx == 0
    assert type(idx) is int

    # --- first-match-wins when a date recurs across vintage brackets ---------
    # "2020-02-01" appears at rows 1 and 2; the accessor must return the first.
    assert _first_date_index(dates, "2020-02-01") == 1

    # --- match at the last row (boundary) -----------------------------------
    assert _first_date_index(dates, "2020-03-01") == 3

    # --- no match returns None, not -1 or an exception ----------------------
    assert _first_date_index(dates, "1999-12-31") is None

    # --- empty column returns None ------------------------------------------
    empty = np.array([], dtype="datetime64[D]")
    assert _first_date_index(empty, "2020-01-01") is None

    # --- unparseable key raises ValueError (from numpy), left to the caller --
    # The accessor stays free of model-domain exceptions; the model layer maps
    # this ValueError to its own ModelError.
    with pytest.raises(ValueError):
        _first_date_index(dates, "not-a-date")

    # --- a valid but non-ISO-shaped key that numpy rejects also raises -------
    with pytest.raises(ValueError):
        _first_date_index(dates, "2020-13-01")

def test_get_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full-branch coverage for :func:`_get_api_key`.

    Exercises every path: the unknown-service guard (raise), a service with a
    configured key (return the string), and a known service with no key set
    (return ``None``). State is mutated through ``monkeypatch.setitem`` on the
    registry dict so no global key leaks into other tests.
    """
    # Known service, key configured -> returns the stored value.
    monkeypatch.setitem(_registries._GLOBAL_KEYS, "fred", "test_fred_key")
    assert _get_api_key("fred") == "test_fred_key"

    # Default argument resolves to "fred".
    assert _get_api_key() == "test_fred_key"

    # Known service, no key configured -> returns None (not a raise).
    monkeypatch.setitem(_registries._GLOBAL_KEYS, "fraser", None)
    assert _get_api_key("fraser") is None

    # Unknown service -> ValueValidationError with the enumerated-services message.
    with pytest.raises(ValueValidationError, match=r"Unknown service: 'bogus'\."):
        _get_api_key("bogus")  # type: ignore[arg-type]

def test_get_dataframe_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full-branch coverage for :func:`_get_dataframe_backend`.

    Covers both arms of the ``_GLOBAL_DATAFRAME_BACKEND or _DEFAULT_DATAFRAME_BACKEND``
    expression: a set global (returned as-is) and an unset global (falls through to
    the package default).
    """
    # Global set -> returned in preference to the default.
    monkeypatch.setattr(_accessors, "_GLOBAL_DATAFRAME_BACKEND", "polars")
    assert _get_dataframe_backend() == "polars"

    # Global unset (None) -> falls through to _DEFAULT_DATAFRAME_BACKEND.
    monkeypatch.setattr(_accessors, "_GLOBAL_DATAFRAME_BACKEND", None)
    assert _get_dataframe_backend() == _DEFAULT_DATAFRAME_BACKEND


def test_get_geodataframe_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full-branch coverage for :func:`_get_geodataframe_backend`.

    Covers both arms of the
    ``_GLOBAL_GEODATAFRAME_BACKEND or _DEFAULT_GEODATAFRAME_BACKEND`` expression: a
    set global (returned as-is) and an unset global (falls through to the package
    default).
    """
    # Global set -> returned in preference to the default.
    monkeypatch.setattr(_accessors, "_GLOBAL_GEODATAFRAME_BACKEND", "polars-st")
    assert _get_geodataframe_backend() == "polars-st"

    # Global unset (None) -> falls through to _DEFAULT_GEODATAFRAME_BACKEND.
    monkeypatch.setattr(_accessors, "_GLOBAL_GEODATAFRAME_BACKEND", None)
    assert _get_geodataframe_backend() == _DEFAULT_GEODATAFRAME_BACKEND
