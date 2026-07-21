# filepath: /tests/_core_tests/_converters_test.py
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

from datetime import date, datetime, time

import numpy as np
import pandas as pd
import pytest

import fedfred._core._converters as converters
from fedfred._core._converters import (
    _coerce_lower,
    _columns_to_arrow,
    _columns_to_cudf,
    _columns_to_dask,
    _columns_to_pandas,
    _columns_to_polars,
    _columns_to_series,
    _comma_date_list_converter,
    _date_parameter_converter,
    _dict_type_converter,
    _freq_aware_index,
    _hashable_type_converter,
    _identity_converter,
    _pandas_frequency_converter,
    _semicolon_list_converter,
    _time_parameter_converter,
    _vintage_matrix,
)
from fedfred.exceptions import ConversionError, TypeConversionError

_M3 = np.array(["2020-01-01", "2020-02-01", "2020-03-01"], dtype="datetime64[D]")
_V3 = np.array([1.0, 2.0, 3.0])


# --------------------------------------------------------------------------- #
# Frequency / index                                                            #
# --------------------------------------------------------------------------- #
def test_pandas_frequency_converter() -> None:
    assert _pandas_frequency_converter("m") == "MS"
    assert _pandas_frequency_converter("wef") == "W-FRI"
    assert _pandas_frequency_converter(None) is None      # None -> "" -> miss
    assert _pandas_frequency_converter("") is None
    assert _pandas_frequency_converter("not_a_code") is None


def test_freq_aware_index() -> None:
    # mapped alias conforms -> freq attached
    assert _freq_aware_index(_M3, "m").freqstr == "MS"
    # mapped alias ("D") does NOT conform -> ValueError -> fall back to infer_freq
    assert _freq_aware_index(_M3, "d").freqstr == "MS"
    # no code -> mapped is None -> inference supplies the freq (len >= 3)
    assert _freq_aware_index(_M3, None).freqstr == "MS"
    # non-unique axis (vintage) -> early return, no freq
    nonunique = np.array(["2020-01-01", "2020-01-01"], dtype="datetime64[D]")
    assert _freq_aware_index(nonunique, "m").freq is None
    # non-monotonic axis -> early return, no freq
    nonmono = np.array(["2020-02-01", "2020-01-01"], dtype="datetime64[D]")
    assert _freq_aware_index(nonmono, "m").freq is None
    # < 3 points: inference is skipped; a non-conforming mapped alias -> no freq
    len2 = np.array(["2020-01-01", "2020-01-15"], dtype="datetime64[D]")
    assert _freq_aware_index(len2, "m").freq is None


# --------------------------------------------------------------------------- #
# pandas frame / series builders                                               #
# --------------------------------------------------------------------------- #
def test_columns_to_pandas() -> None:
    cols = {"date": _M3, "value": _V3}

    # index="date": drops the date column, sets a freq-aware DatetimeIndex
    d = _columns_to_pandas(cols, index="date", frequency="m")
    assert list(d.columns) == ["value"]
    assert d.index.name == "date"
    assert d.index.freqstr == "MS"

    # index=None: default RangeIndex, every column retained
    n = _columns_to_pandas(cols)
    assert isinstance(n.index, pd.RangeIndex)
    assert list(n.columns) == ["date", "value"]

    # index=<other>: plain set_index on that column
    v = _columns_to_pandas(cols, index="value")
    assert v.index.name == "value"
    assert list(v.columns) == ["date"]


def test_columns_to_series() -> None:
    s = _columns_to_series(_V3, _M3, "m", "GDP")
    assert isinstance(s, pd.Series)
    assert s.name == "GDP"
    assert s.index.freqstr == "MS"
    assert s.tolist() == [1.0, 2.0, 3.0]


def test_vintage_matrix() -> None:
    # full matrix: 2 dates x 2 vintages, no missing cells
    dates = np.array(["2020-01-01", "2020-02-01", "2020-01-01", "2020-02-01"], dtype="datetime64[D]")
    rt = np.array(["2020-01-05", "2020-01-05", "2020-02-05", "2020-02-05"], dtype="datetime64[D]")
    vm = _vintage_matrix(dates, np.array([1.0, 2.0, 1.1, 2.1]), rt, "m")
    assert vm.shape == (2, 2)
    assert vm.index.name == "date"
    assert vm.columns.name == "realtime_start"
    assert vm.index.freqstr == "MS"            # pivoted axis is now unique
    assert np.array_equal(vm.to_numpy(), np.array([[1.0, 1.1], [2.0, 2.1]]))

    # ragged: a vintage that has not observed a later date -> one NaN cell
    d2 = np.array(["2020-01-01", "2020-01-01", "2020-02-01"], dtype="datetime64[D]")
    rt2 = np.array(["2020-01-05", "2020-02-05", "2020-02-05"], dtype="datetime64[D]")
    vm2 = _vintage_matrix(d2, np.array([1.0, 1.1, 2.1]), rt2, "m")
    assert vm2.shape == (2, 2)
    assert int(vm2.isna().sum().sum()) == 1


# --------------------------------------------------------------------------- #
# optional-backend builders (backend import mocked via _require_module)        #
# --------------------------------------------------------------------------- #
def test_columns_to_polars(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    class _FakePolars:
        @staticmethod
        def DataFrame(data: tuple) -> str:
            captured["data"] = data
            return "POLARS_FRAME"

    def _fake_require(module: str, purpose: str, extra: object = None) -> _FakePolars:
        captured["require"] = (module, purpose, extra)
        return _FakePolars

    monkeypatch.setattr(converters, "_require_module", _fake_require)

    cols = {"date": _M3, "value": _V3}
    assert _columns_to_polars(cols) == "POLARS_FRAME"
    assert captured["require"] == ("polars", "to_polars", None)
    # the columns are handed over (shallow copy: same arrays, no Arrow round-trip)
    assert list(captured["data"]) == ["date", "value"]
    assert captured["data"]["value"] is _V3


def test_columns_to_dask(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    class _FakeDask:
        @staticmethod
        def from_pandas(df, npartitions):
            captured["df"] = df
            captured["npartitions"] = npartitions
            return "DASK_FRAME"

    def _fake_require(module, purpose, extra=None):
        captured["require"] = (module, purpose, extra)
        return _FakeDask

    monkeypatch.setattr(converters, "_require_module", _fake_require)

    cols = {"date": _M3, "value": _V3}
    # index/frequency are forwarded to the (real) pandas builder
    assert _columns_to_dask(cols, npartitions=2, index="date", frequency="m") == "DASK_FRAME"
    assert captured["require"] == ("dask.dataframe", "to_dask", "dask")
    assert captured["npartitions"] == 2
    assert isinstance(captured["df"], pd.DataFrame)
    assert captured["df"].index.name == "date"     # forwarding proven
    assert captured["df"].index.freqstr == "MS"


def test_columns_to_cudf(monkeypatch) -> None:
    class _FakeIndex:
        def __init__(self, data):
            self.data = data
            self.name = None

    class _FakeDataFrame:
        def __init__(self, data):
            self.data = data
            self.index = None

        def set_index(self, key):
            self.set_key = key
            return self

    class _FakeCudf:
        DataFrame = _FakeDataFrame
        DatetimeIndex = _FakeIndex

    monkeypatch.setattr(converters, "_require_module", lambda *a, **k: _FakeCudf)

    cols = {"date": _M3, "value": _V3}

    # index="date": date dropped from columns, set as a (freq-less) DatetimeIndex
    dfd = _columns_to_cudf(cols, index="date")
    assert "date" not in dfd.data
    assert dfd.index.data is _M3
    assert dfd.index.name == "date"

    # index=None: all columns retained, no set_index
    dfn = _columns_to_cudf(cols)
    assert list(dfn.data) == ["date", "value"]
    assert not hasattr(dfn, "set_key")

    # index=<other>: plain set_index
    dfv = _columns_to_cudf(cols, index="value")
    assert dfv.set_key == "value"


def test_columns_to_arrow(monkeypatch) -> None:
    captured = {}

    class _FakeArrow:
        @staticmethod
        def table(columns):
            captured["columns"] = columns
            return "ARROW_TABLE"

    def _fake_require(module, purpose, extra=None):
        captured["require"] = (module, purpose, extra)
        return _FakeArrow

    monkeypatch.setattr(converters, "_require_module", _fake_require)

    cols = {"date": _M3, "value": _V3}
    assert _columns_to_arrow(cols) == "ARROW_TABLE"
    assert captured["require"] == ("pyarrow", "to_arrow", "arrow")
    assert captured["columns"] is cols


# --------------------------------------------------------------------------- #
# scalar parameter converters                                                  #
# --------------------------------------------------------------------------- #
def test_identity_converter() -> None:
    sentinel = object()
    assert _identity_converter("param", sentinel) is sentinel


def test_date_parameter_converter() -> None:
    # datetime is checked before date (datetime subclasses date) -> time dropped
    assert _date_parameter_converter("p", datetime(2020, 1, 1, 14, 30)) == "2020-01-01"
    assert _date_parameter_converter("p", date(2020, 1, 1)) == "2020-01-01"
    assert _date_parameter_converter("p", "2020-01-01") == "2020-01-01"  # passthrough
    with pytest.raises(TypeConversionError) as exc:
        _date_parameter_converter("p", 123)
    assert exc.value.received == "int"


def test_time_parameter_converter() -> None:
    assert _time_parameter_converter("p", datetime(2020, 1, 1, 14, 30)) == "14:30"
    assert _time_parameter_converter("p", time(9, 5)) == "09:05"
    assert _time_parameter_converter("p", "14:30") == "14:30"           # passthrough
    with pytest.raises(TypeConversionError) as exc:
        _time_parameter_converter("p", 5)
    assert exc.value.received == "int"


def test_semicolon_list_converter() -> None:
    assert _semicolon_list_converter("p", "single") == "single"          # passthrough
    assert _semicolon_list_converter("p", ["a", "b", "c"]) == "a;b;c"
    # list with a non-str element -> raise, listing the offending types
    with pytest.raises(TypeConversionError) as exc:
        _semicolon_list_converter("p", ["a", 2])
    assert exc.value.received == "str, int"
    # wholly wrong type -> raise
    with pytest.raises(TypeConversionError) as exc:
        _semicolon_list_converter("p", 5)
    assert exc.value.received == "int"


def test_comma_date_list_converter() -> None:
    assert _comma_date_list_converter("p", "2020-01-01") == "2020-01-01"  # passthrough
    assert _comma_date_list_converter("p", date(2020, 2, 1)) == "2020-02-01"
    assert _comma_date_list_converter("p", datetime(2020, 2, 1, 9)) == "2020-02-01"
    # list mixes types and skips None entries
    assert _comma_date_list_converter(
        "p", [datetime(2020, 1, 1), date(2020, 2, 1), "2020-03-01", None]
    ) == "2020-01-01,2020-02-01,2020-03-01"
    # all-None / empty list -> empty string
    assert _comma_date_list_converter("p", [None]) == ""
    assert _comma_date_list_converter("p", []) == ""
    # wrong top-level type -> raise
    with pytest.raises(TypeConversionError) as exc:
        _comma_date_list_converter("p", 5)
    assert exc.value.received == "int"
    # bad element propagates the element converter's raise
    with pytest.raises(TypeConversionError):
        _comma_date_list_converter("p", [1])


# --------------------------------------------------------------------------- #
# cache-key round-trip                                                          #
# --------------------------------------------------------------------------- #
def test_hashable_type_converter() -> None:
    # sorted by key so insertion order can't change the cache key
    assert _hashable_type_converter({"b": 2, "a": 1, "c": None}) == (
        ("a", 1),
        ("b", 2),
        ("c", None),
    )
    assert _hashable_type_converter(None) is None


def test_dict_type_converter() -> None:
    assert _dict_type_converter((("a", 1), ("b", 2), ("c", None))) == {
        "a": 1,
        "b": 2,
        "c": None,
    }
    assert _dict_type_converter(None) is None


def test_hashable_dict_round_trip() -> None:
    # the two are documented inverses
    data = {"param1": "value1", "param2": 123, "param3": None}
    assert _dict_type_converter(_hashable_type_converter(data)) == data


# --------------------------------------------------------------------------- #
# model converters                                                             #
# --------------------------------------------------------------------------- #
def test_coerce_lower() -> None:
    assert _coerce_lower("ASC") == "asc"
    assert _coerce_lower(None) is None
    with pytest.raises(ConversionError) as exc:
        _coerce_lower(5)
    assert exc.value.received == "int"