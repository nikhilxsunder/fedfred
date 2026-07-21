# filepath: /tests/_core_tests/_builders_test.py
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

import fedfred._core._builders as builders
from fedfred._core._builders import _build_fred_style_specs
from fedfred._core._defaults import (
    _FRED_BASE_PARAMETERS,
    _FRED_VERSION_TWO_BASE_PARAMETERS,
)
from fedfred._core._mappings import _FRED_ENDPOINT_MAP
from fedfred._core._specs import EndpointSpec
from fedfred._core._urls import _FRED_PATH, _ST_LOUIS_FED_BASE_URL
from fedfred.exceptions import EndpointSpecBuildError


def test_build_fred_style_specs(monkeypatch: pytest.MonkeyPatch) -> None:
    # --- happy path: both FRED-style services build the full endpoint set ----
    for service in ("fred", "alfred"):
        specs = _build_fred_style_specs(service)

        assert isinstance(specs, dict)
        # exactly the mapped endpoints — nothing dropped, nothing extra
        assert specs.keys() == _FRED_ENDPOINT_MAP.keys()

        for name, spec in specs.items():
            assert isinstance(spec, EndpointSpec)
            assert spec.service == service                       # stamped identity
            # url = host + /fred + endpoint path fragment
            assert spec.url == f"{_ST_LOUIS_FED_BASE_URL}{_FRED_PATH}{_FRED_ENDPOINT_MAP[name]}"
            assert spec.payload is None                          # GET endpoints
            assert spec.headers is None

    fred = _build_fred_style_specs("fred")

    # --- else-branch: a non-v2 endpoint -> api_key_param + v1 base params -----
    obs = fred["get_series_observations"]
    assert obs.url == "https://api.stlouisfed.org/fred/series/observations"
    assert obs.auth == "api_key_param"
    # the spec carries the SHARED default object, not a copy (identity matters:
    # a copy-per-spec would silently break the module's shared-dict contract)
    assert obs.params is _FRED_BASE_PARAMETERS

    # --- if-branch: the sole /v2/ endpoint -> bearer_header + v2 base params ---
    v2 = fred["get_release_observations"]
    assert v2.url == "https://api.stlouisfed.org/fred/v2/release/observations"
    assert v2.auth == "bearer_header"
    assert v2.params is _FRED_VERSION_TWO_BASE_PARAMETERS

    # --- the branch predicate holds for EVERY endpoint, not just the two above -
    for name, spec in fred.items():
        if _FRED_ENDPOINT_MAP[name].startswith("/v2/"):
            assert spec.auth == "bearer_header"
            assert spec.params is _FRED_VERSION_TWO_BASE_PARAMETERS
        else:
            assert spec.auth == "api_key_param"
            assert spec.params is _FRED_BASE_PARAMETERS

    # --- FRED and ALFRED differ ONLY by the stamped service ------------------
    alfred = _build_fred_style_specs("alfred")
    assert fred.keys() == alfred.keys()
    for name in fred:
        assert fred[name].url == alfred[name].url
        assert fred[name].auth == alfred[name].auth
        assert fred[name].service == "fred"
        assert alfred[name].service == "alfred"

    # --- failure path: a spec that fails to construct is wrapped with context -
    # A real EndpointSpec never fails here, so force the except-branch by
    # replacing the constructor the builder looks up (module global).
    sentinel = RuntimeError("spec construction blew up")

    def _raising_endpoint_spec(**kwargs: None) -> None:
        raise sentinel

    monkeypatch.setattr(builders, "EndpointSpec", _raising_endpoint_spec)

    with pytest.raises(EndpointSpecBuildError) as excinfo:
        _build_fred_style_specs("fred")

    err = excinfo.value
    assert err.service == "fred"
    # the loop fails on the first endpoint in insertion order
    assert err.endpoint_name == next(iter(_FRED_ENDPOINT_MAP))
    # the underlying error is both chained (raise ... from) and carried on payload
    assert err.original_exception is sentinel
    assert err.__cause__ is sentinel
