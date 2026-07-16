# filepath: /tests/_core_tests/_parsers_test.py
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

from fedfred._core._parsers import (
    _date_column,
    _extract_objects,
    _objects_iter_dict_or_list,
    _observation_columns,
    _region_type_parser,
    _require_first_list,
)
from fedfred.exceptions import MissingFieldError, ResponseShapeError


def test_region_type_parser():
    # happy path
    assert _region_type_parser({"meta": {"region": "state"}, "data": {}}) == "state"

    # meta absent -> falsy get({}, {}) -> field="meta"
    with pytest.raises(MissingFieldError) as exc:
        _region_type_parser({"data": {}})
    assert exc.value.field == "meta"

    # meta present but empty also hits the "meta" branch
    with pytest.raises(MissingFieldError) as exc:
        _region_type_parser({"meta": {}})
    assert exc.value.field == "meta"

    # meta present, region key absent -> field="region"
    with pytest.raises(MissingFieldError) as exc:
        _region_type_parser({"meta": {"other": 1}})
    assert exc.value.field == "region"

    # region present but empty string -> still the "region" branch
    with pytest.raises(MissingFieldError) as exc:
        _region_type_parser({"meta": {"region": ""}})
    assert exc.value.field == "region"


def test_require_first_list():
    # non-mapping response -> ResponseShapeError at the root
    with pytest.raises(ResponseShapeError) as exc:
        _require_first_list([], ("seriess",))
    assert exc.value.expected == "mapping"
    assert exc.value.received == "list"

    # first present key wins, and its list is returned
    assert _require_first_list({"seriess": [{"id": "GDP"}]}, ("seriess", "series")) == [{"id": "GDP"}]
    # when both are present, the earlier key in `keys` takes precedence
    assert _require_first_list({"seriess": [1], "series": [2]}, ("seriess", "series")) == [1]
    # falls through to a later key when the first is absent
    assert _require_first_list({"series": [2]}, ("seriess", "series")) == [2]

    # key present but value is not a list -> ResponseShapeError with field context
    with pytest.raises(ResponseShapeError) as exc:
        _require_first_list({"seriess": "nope"}, ("seriess", "series"))
    assert exc.value.field == "seriess"
    assert exc.value.expected == "list"
    assert exc.value.received == "str"

    # none of the candidate keys present -> MissingFieldError carrying the set
    with pytest.raises(MissingFieldError) as exc:
        _require_first_list({"other": []}, ("seriess", "series"))
    assert exc.value.candidates == ("seriess", "series")


def test_objects_iter_dict_or_list():
    # id-keyed dict -> values() as a list (keys discarded, insertion order kept)
    assert _objects_iter_dict_or_list(
        {"elements": {"1": {"id": 1}, "2": {"id": 2}}}, "elements"
    ) == [{"id": 1}, {"id": 2}]

    # already a list -> returned unchanged
    assert _objects_iter_dict_or_list({"elements": [{"id": 1}]}, "elements") == [{"id": 1}]

    # non-mapping response -> missing field (first clause of the guard)
    with pytest.raises(MissingFieldError) as exc:
        _objects_iter_dict_or_list([], "elements")
    assert exc.value.field == "elements"

    # key absent -> missing field
    with pytest.raises(MissingFieldError) as exc:
        _objects_iter_dict_or_list({"other": 1}, "elements")
    assert exc.value.field == "elements"

    # value neither dict nor list -> ResponseShapeError
    with pytest.raises(ResponseShapeError) as exc:
        _objects_iter_dict_or_list({"elements": "scalar"}, "elements")
    assert exc.value.field == "elements"
    assert exc.value.expected == "dict or list"
    assert exc.value.received == "str"


def test_extract_objects():
    # shape="dict_or_list" routes to the dict-or-list backend, using keys[0]
    assert _extract_objects(
        {"elements": {"1": {"id": 1}}}, ("elements", "ignored"), "dict_or_list"
    ) == [{"id": 1}]

    # shape="list" routes to the first-list backend, honoring the full key tuple
    assert _extract_objects(
        {"series": [{"id": "GDP"}]}, ("seriess", "series"), "list"
    ) == [{"id": "GDP"}]

    # routing preserves the backends' error contracts
    with pytest.raises(MissingFieldError):
        _extract_objects({"other": {}}, ("elements",), "dict_or_list")
    with pytest.raises(MissingFieldError):
        _extract_objects({"other": []}, ("seriess", "series"), "list")


def test_date_column():
    dates = _date_column([{"date": "2020-01-01"}, {"date": "2020-02-01"}], "date")
    assert dates.dtype == np.dtype("datetime64[D]")
    assert dates.tolist() == [__import__("datetime").date(2020, 1, 1), __import__("datetime").date(2020, 2, 1)]

    # the key is parameterized (used for realtime_start / realtime_end too)
    rt = _date_column([{"realtime_start": "2021-06-01"}], "realtime_start")
    assert rt.tolist() == [__import__("datetime").date(2021, 6, 1)]

    # a row missing the key -> MissingFieldError wrapping the KeyError
    with pytest.raises(MissingFieldError) as exc:
        _date_column([{"value": "1.5"}], "date")
    assert exc.value.field == "date"
    assert isinstance(exc.value.original_exception, KeyError)
    assert exc.value.__cause__ is exc.value.original_exception


def test_observation_columns():
    dates, values = _observation_columns(
        [{"date": "2020-01-01", "value": "1.5"}, {"date": "2020-02-01", "value": "."}]
    )
    assert dates.dtype == np.dtype("datetime64[D]")
    assert values.dtype == np.dtype("float64")
    assert values[0] == 1.5
    assert np.isnan(values[1])                 # FRED "." sentinel -> NaN
    assert len(dates) == len(values) == 2

    # missing "date" surfaces via _date_column
    with pytest.raises(MissingFieldError) as exc:
        _observation_columns([{"value": "1.5"}])
    assert exc.value.field == "date"

    # missing "value" surfaces via the value-parse except block
    with pytest.raises(MissingFieldError) as exc:
        _observation_columns([{"date": "2020-01-01"}])
    assert exc.value.field == "value"
    assert isinstance(exc.value.original_exception, KeyError)
    assert exc.value.__cause__ is exc.value.original_exception