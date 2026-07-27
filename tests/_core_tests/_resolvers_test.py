# filepath: /tests/_core_tests/_resolvers_test.py
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

from fedfred._core._choices import _VALID_SERVICES
from fedfred._core._resolvers import _resolve_endpoint, _resolve_preparation_function
from fedfred._core._specs import EndpointSpec
from fedfred.exceptions import UnknownServiceError, UnsupportedEndpointError, ValueValidationError


def test_resolve_endpoint() -> None:
    # --- happy path: a pre-built, service-stamped spec is returned -----------
    spec = _resolve_endpoint("fred", "get_series_observations")
    assert isinstance(spec, EndpointSpec)
    assert spec.service == "fred"
    assert spec.url == "https://api.stlouisfed.org/fred/series/observations"

    # --- name normalization: whitespace trimmed, case-folded before lookup ---
    assert _resolve_endpoint("fred", "  GET_SERIES_OBSERVATIONS  ") is spec

    # --- FRED and ALFRED share endpoint names but yield distinct specs -------
    alfred_spec = _resolve_endpoint("alfred", "get_series_observations")
    assert alfred_spec is not spec
    assert alfred_spec.service == "alfred"

    # --- unknown service -> UnknownServiceError with the accepted set --------
    with pytest.raises(ValueValidationError) as exc:
        _resolve_endpoint("bogus", "get_series_observations")
        assert exc.value.message == "Unknown service: 'bogus'."
        assert exc.value.parameter == "service"
        assert exc.value.reason == f"Expected: {sorted(_VALID_SERVICES)}."
        assert exc.value.context == {"value": "bogus"}

    # --- known service, unknown endpoint -> UnsupportedEndpointError ---------
    with pytest.raises(UnsupportedEndpointError) as exc:
        _resolve_endpoint("fred", "no_such_endpoint")
    assert exc.value.service == "fred"
    assert exc.value.endpoint_name == "no_such_endpoint"
    assert isinstance(exc.value.original_exception, KeyError)
    assert exc.value.__cause__ is exc.value.original_exception


def test_resolve_preparation_function() -> None:
    # --- dispatch + apply for each service in the table ----------------------
    assert _resolve_preparation_function({"limit": 100}, service="fred") == {"limit": 100}
    assert _resolve_preparation_function(
        {"shape": "state"}, service="geofred"
    ) == {"shape": "state"}
    assert _resolve_preparation_function({"page": 1}, service="fraser") == {"page": 1}

    # --- service is lower-cased before dispatch ------------------------------
    assert _resolve_preparation_function({"limit": 100}, service="FRED") == {"limit": 100}

    # --- None parameters flow through the preparer to an empty dict ----------
    assert _resolve_preparation_function(None, service="fred") == {}

    # --- unknown service -> UnknownServiceError with the dispatch's own set --
    with pytest.raises(UnknownServiceError) as exc:
        _resolve_preparation_function({"limit": 1}, service="bogus")
    assert exc.value.service == "bogus"
    assert exc.value.known_services == ("fraser", "fred", "geofred")   # note: no "alfred"
    assert isinstance(exc.value.original_exception, KeyError)
    assert exc.value.__cause__ is exc.value.original_exception
