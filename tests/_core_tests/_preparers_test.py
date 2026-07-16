# filepath: /tests/_core_tests/_preparers_test.py
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

import pytest

import fedfred._core._preparers as preparers
from fedfred._core._preparers import (
    _prepare_fraser_parameters,
    _prepare_fred_parameters,
    _prepare_geofred_parameters,
    _prepare_parameters,
)
from fedfred._core._registries import (
    FRASER_PARAMETER_SPECS,
    FRED_PARAMETER_SPECS,
    GEOFRED_PARAMETER_SPECS,
)
from fedfred._core._specs import ParameterSpec
from fedfred.exceptions import MissingParameterError, UnknownParameterError


def test_prepare_parameters():
    # None parameters -> treated as empty mapping -> {}
    assert _prepare_parameters(None, {}, service="S") == {}

    # None values are skipped entirely
    assert _prepare_parameters({"a": None}, {"a": ParameterSpec()}, service="S") == {}

    # spec with neither converter nor validator -> value passes through unchanged
    assert _prepare_parameters({"a": 5}, {"a": ParameterSpec()}, service="S") == {"a": 5}

    # converter-only: value is transformed
    assert _prepare_parameters(
        {"a": 3}, {"a": ParameterSpec(converter=lambda n, v: v + 1)}, service="S"
    ) == {"a": 4}

    # converter runs BEFORE the validator, which sees the converted value
    seen = {}

    def _conv(name, value):
        return value * 2

    def _val(name, value):
        seen["value"] = value      # records what the validator received

    out = _prepare_parameters(
        {"a": 5}, {"a": ParameterSpec(converter=_conv, validator=_val)}, service="S"
    )
    assert out == {"a": 10}
    assert seen["value"] == 10     # validator saw the CONVERTED value

    # a rejecting validator propagates its error
    def _bad(name, value):
        raise ValueError("nope")

    with pytest.raises(ValueError):
        _prepare_parameters({"a": 1}, {"a": ParameterSpec(validator=_bad)}, service="S")

    # unknown parameter, allow_unknown=True -> passed through unchanged
    assert _prepare_parameters({"x": 9}, {}, service="S", allow_unknown=True) == {"x": 9}

    # unknown parameter, allow_unknown=False (default) -> raise with sorted known set
    with pytest.raises(UnknownParameterError) as exc:
        _prepare_parameters(
            {"x": 9}, {"b": ParameterSpec(), "a": ParameterSpec()}, service="SVC"
        )
    assert exc.value.parameter == "x"
    assert exc.value.service == "SVC"
    assert exc.value.known_parameters == ("a", "b")   # tuple(sorted(specs))

    # required parameter present -> ok
    assert _prepare_parameters(
        {"r": 1}, {"r": ParameterSpec(required=True)}, service="S"
    ) == {"r": 1}

    # required parameter absent -> MissingParameterError
    with pytest.raises(MissingParameterError) as exc:
        _prepare_parameters({}, {"r": ParameterSpec(required=True)}, service="SVC")
    assert exc.value.parameter == "r"
    assert exc.value.service == "SVC"

    # required parameter present but None (skipped) still counts as missing
    with pytest.raises(MissingParameterError):
        _prepare_parameters({"r": None}, {"r": ParameterSpec(required=True)}, service="S")


def test_prepare_fred_parameters(monkeypatch):
    # real integration: valid known params pass through unchanged
    assert _prepare_fred_parameters({"limit": 100, "sort_order": "asc"}) == {
        "limit": 100,
        "sort_order": "asc",
    }
    # unknown params pass through (allow_unknown=True)
    assert _prepare_fred_parameters({"unknown_x": "v"}) == {"unknown_x": "v"}

    # delegation: correct specs object, service label, and allow_unknown flag
    captured = {}

    def _capture(parameters, specs, service, allow_unknown=False):
        captured.update(
            parameters=parameters, specs=specs, service=service, allow_unknown=allow_unknown
        )
        return {}

    monkeypatch.setattr(preparers, "_prepare_parameters", _capture)
    _prepare_fred_parameters({"limit": 1})
    assert captured["parameters"] == {"limit": 1}
    assert captured["specs"] is FRED_PARAMETER_SPECS
    assert captured["service"] == "FRED"
    assert captured["allow_unknown"] is True


def test_prepare_geofred_parameters(monkeypatch):
    assert _prepare_geofred_parameters({"shape": "state", "file_type": "geojson"}) == {
        "shape": "state",
        "file_type": "geojson",
    }
    assert _prepare_geofred_parameters({"unknown_x": "v"}) == {"unknown_x": "v"}

    captured = {}

    def _capture(parameters, specs, service, allow_unknown=False):
        captured.update(specs=specs, service=service, allow_unknown=allow_unknown)
        return {}

    monkeypatch.setattr(preparers, "_prepare_parameters", _capture)
    _prepare_geofred_parameters({"shape": "state"})
    assert captured["specs"] is GEOFRED_PARAMETER_SPECS
    assert captured["service"] == "GeoFRED"
    assert captured["allow_unknown"] is True


def test_prepare_fraser_parameters(monkeypatch):
    assert _prepare_fraser_parameters({"limit": 100, "page": 1}) == {"limit": 100, "page": 1}
    assert _prepare_fraser_parameters({"unknown_x": "v"}) == {"unknown_x": "v"}

    captured = {}

    def _capture(parameters, specs, service, allow_unknown=False):
        captured.update(specs=specs, service=service, allow_unknown=allow_unknown)
        return {}

    monkeypatch.setattr(preparers, "_prepare_parameters", _capture)
    _prepare_fraser_parameters({"limit": 1})
    assert captured["specs"] is FRASER_PARAMETER_SPECS
    assert captured["service"] == "FRASER"
    assert captured["allow_unknown"] is True