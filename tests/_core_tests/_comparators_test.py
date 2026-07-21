# filepath: /tests/_core_tests/_comparators_test.py
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

from datetime import date

import numpy as np

from fedfred._core._comparators import _columns_equal, _row_match_mask


def test_row_match_mask() -> None:
    columns = {
        "date": np.array(
            ["2020-01-01", "2020-02-01", "2020-03-01"], dtype="datetime64[D]"
        ),
        "value": np.array([1.5, np.nan, 3.0]),
    }

    # --- M-branch + else-branch, all columns must match (logical AND) --------
    mask = _row_match_mask(columns, {"date": date(2020, 1, 1), "value": 1.5})
    assert isinstance(mask, np.ndarray)
    assert mask.dtype == np.bool_
    assert len(mask) == 3                       # length of the first column
    assert mask.tolist() == [True, False, False]

    # --- None target matches a NaN cell (missing observation) ----------------
    # None is tested only on non-datetime columns: the M-branch is checked
    # first, so a None here lands in the `target is None` branch via `value`.
    assert _row_match_mask(
        columns, {"date": date(2020, 2, 1), "value": None}
    ).tolist() == [False, True, False]

    # a None target must NOT match a present (non-NaN) value
    assert _row_match_mask(
        {"value": np.array([1.5, np.nan])}, {"value": None}
    ).tolist() == [False, True]

    # --- else-branch in isolation (plain == on a float column) ---------------
    assert _row_match_mask(
        {"value": np.array([1.5, 2.0])}, {"value": 2.0}
    ).tolist() == [False, True]

    # --- AND semantics: right date but wrong value => no match ---------------
    assert _row_match_mask(
        columns, {"date": date(2020, 1, 1), "value": 999.0}
    ).tolist() == [False, False, False]

    # --- multiple datetime columns (vintage: date + realtime brackets) -------
    vintage = {
        "date": np.array(["2020-01-01", "2020-01-01"], dtype="datetime64[D]"),
        "realtime_start": np.array(["2020-01-05", "2020-02-05"], dtype="datetime64[D]"),
    }
    assert _row_match_mask(
        vintage, {"date": date(2020, 1, 1), "realtime_start": date(2020, 1, 5)}
    ).tolist() == [True, False]

    # --- no row matches -> all False -----------------------------------------
    assert _row_match_mask(
        columns, {"date": date(1999, 1, 1), "value": 1.5}
    ).tolist() == [False, False, False]


def test_columns_equal() -> None:
    # --- equal keys + equal float arrays, aligned NaN treated as equal -------
    a = {"value": np.array([1.5, np.nan, 3.0])}
    assert _columns_equal(a, {"value": np.array([1.5, np.nan, 3.0])}) is True

    # --- float mismatch (non-NaN cell differs) -> False ----------------------
    assert _columns_equal(a, {"value": np.array([1.5, np.nan, 999.0])}) is False

    # --- misaligned NaN -> False (equal_nan only helps aligned positions) ----
    assert _columns_equal(a, {"value": np.array([np.nan, 1.5, 3.0])}) is False

    # --- key sets differ -> early False --------------------------------------
    assert _columns_equal({"value": np.array([1.0])}, {"date": np.array([1.0])}) is False

    # --- datetime columns exercise the equal_nan=False branch of the ternary -
    d1 = {"date": np.array(["2020-01-01", "2020-02-01"], dtype="datetime64[D]")}
    assert _columns_equal(
        d1,
        {
            "date": np.array(["2020-01-01", "2020-02-01"], dtype="datetime64[D]")
        }
    ) is True
    assert _columns_equal(
        d1,
        {
            "date": np.array(["2020-01-01", "2020-03-01"], dtype="datetime64[D]")
        }
    ) is False

    # --- different-length arrays under the same key -> False -----------------
    assert _columns_equal({"value": np.array([1.0, 2.0])}, {"value": np.array([1.0])}) is False

    # --- multi-key mapping, one key differs -> False (all() short-circuits) ---
    assert _columns_equal(
        {"date": d1["date"], "value": np.array([1.0, 2.0])},
        {"date": d1["date"], "value": np.array([1.0, 9.0])},
    ) is False

    # --- key-order independence: same keys, different insertion order --------
    assert _columns_equal(
        {"date": d1["date"], "value": np.array([1.0, 2.0])},
        {"value": np.array([1.0, 2.0]), "date": d1["date"]},
    ) is True

    # --- both empty -> True (no keys to disagree on) -------------------------
    assert _columns_equal({}, {}) is True
