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

from fedfred._core import _resolvers
from fedfred._core._choices import _VALID_SERVICES
from fedfred._core._defaults import (
    _DEFAULT_DATAFRAME_BACKEND,
    _DEFAULT_GEODATAFRAME_BACKEND,
)
from fedfred._core._resolvers import (
    _resolve_api_key,
    _resolve_dataframe_backend,
    _resolve_endpoint,
    _resolve_geodataframe_backend,
    _resolve_preparation_function,
)
from fedfred._core._specs import EndpointSpec
from fedfred.exceptions import MissingAPIKeyError, UnsupportedEndpointError, ValueValidationError


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
    assert _resolve_preparation_function({"shape": "state"}, service="geofred") == {
        "shape": "state"
    }
    assert _resolve_preparation_function({"page": 1}, service="fraser") == {"page": 1}

    # --- service is lower-cased before dispatch ------------------------------
    with pytest.raises(ValueValidationError) as exc:
        _resolve_preparation_function({"limit": 100}, service="FRED")
    assert exc.value.message == "Unknown service: 'FRED'."
    assert exc.value.parameter == "service"
    assert exc.value.reason == f"Expected: {sorted(_VALID_SERVICES)}."
    assert exc.value.context == {"value": "FRED"}

    # --- None parameters flow through the preparer to an empty dict ----------
    assert _resolve_preparation_function(None, service="fred") == {}

    # --- unknown service -> UnknownServiceError with the dispatch's own set --
    with pytest.raises(ValueValidationError) as exc:
        _resolve_preparation_function({"limit": 1}, service="bogus")
    assert exc.value.message == "Unknown service: 'bogus'."
    assert exc.value.parameter == "service"
    assert exc.value.reason == f"Expected: {sorted(_VALID_SERVICES)}."
    assert exc.value.context == {"value": "bogus"}


def test_resolve_dataframe_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full-branch coverage for :func:`_resolve_dataframe_backend`.

    Covers all three precedence arms (explicit, global, default) and the invalid-backend guard.
    """
    # Arm 1: explicit override wins, regardless of global/default.
    monkeypatch.setattr(_resolvers, "_GLOBAL_DATAFRAME_BACKEND", "dask")
    assert _resolve_dataframe_backend("polars") == "polars"

    # Arm 2: no explicit -> the process-global setting.
    monkeypatch.setattr(_resolvers, "_GLOBAL_DATAFRAME_BACKEND", "polars")
    assert _resolve_dataframe_backend() == "polars"

    # Arm 3: no explicit, no global -> the compiled-in default.
    monkeypatch.setattr(_resolvers, "_GLOBAL_DATAFRAME_BACKEND", None)
    assert _resolve_dataframe_backend() == _DEFAULT_DATAFRAME_BACKEND

    # Invalid resolved backend -> ValueValidationError.
    with pytest.raises(ValueValidationError, match="Unknown DataFrame backend"):
        _resolve_dataframe_backend("numpy")  # type: ignore[arg-type]


def test_resolve_geodataframe_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full-branch coverage for :func:`_resolve_geodataframe_backend`.

    Covers all three precedence arms (explicit, global, default) and the invalid-backend guard.
    """
    # Arm 1: explicit override wins.
    monkeypatch.setattr(_resolvers, "_GLOBAL_GEODATAFRAME_BACKEND", "dask-geopandas")
    assert _resolve_geodataframe_backend("polars-st") == "polars-st"

    # Arm 2: no explicit -> the process-global setting.
    monkeypatch.setattr(_resolvers, "_GLOBAL_GEODATAFRAME_BACKEND", "polars-st")
    assert _resolve_geodataframe_backend() == "polars-st"

    # Arm 3: no explicit, no global -> the default.
    monkeypatch.setattr(_resolvers, "_GLOBAL_GEODATAFRAME_BACKEND", None)
    assert _resolve_geodataframe_backend() == _DEFAULT_GEODATAFRAME_BACKEND

    # Invalid resolved backend -> ValueValidationError.
    with pytest.raises(ValueValidationError, match="Unknown GeoDataFrame backend"):
        _resolve_geodataframe_backend("shapely")  # type: ignore[arg-type]


def test_resolve_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full-branch coverage for :func:`_resolve_api_key`.

    Covers: invalid service; global key (stripped) preferred; whitespace-only global treated as
    unset; environment fallback via default var and via ``env_var`` override; whitespace-only env
    treated as unset; and the exhausted-resolution raise.
    """
    # Invalid service -> ValueValidationError from _validate_service.
    with pytest.raises(ValueValidationError, match="Unknown service"):
        _resolve_api_key("bogus")  # type: ignore[arg-type]

    # Global set and non-blank -> returned, stripped (env is not consulted).
    monkeypatch.setitem(_resolvers._GLOBAL_KEYS, "fred", "  global_key  ")
    monkeypatch.setenv("FRED_API_KEY", "env_should_be_ignored")
    assert _resolve_api_key("fred") == "global_key"

    # Whitespace-only global -> treated as unset -> falls through to the environment.
    monkeypatch.setitem(_resolvers._GLOBAL_KEYS, "fred", "   ")
    monkeypatch.setenv("FRED_API_KEY", "  env_key  ")
    assert _resolve_api_key("fred") == "env_key"

    # No global, environment via the service default var (ENV_VARS["fred"] == "FRED_API_KEY").
    monkeypatch.setitem(_resolvers._GLOBAL_KEYS, "fred", None)
    monkeypatch.setenv("FRED_API_KEY", "default_var_key")
    assert _resolve_api_key("fred") == "default_var_key"

    # env_var override consulted instead of the service default.
    monkeypatch.setitem(_resolvers._GLOBAL_KEYS, "fred", None)
    monkeypatch.setenv("CUSTOM_KEY_VAR", "custom_key")
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    assert _resolve_api_key("fred", env_var="CUSTOM_KEY_VAR") == "custom_key"

    # Whitespace-only env -> treated as unset -> nothing resolves -> raise.
    monkeypatch.setitem(_resolvers._GLOBAL_KEYS, "fred", None)
    monkeypatch.setenv("FRED_API_KEY", "   ")
    with pytest.raises(MissingAPIKeyError, match="No API key could be resolved") as exc:
        _resolve_api_key("fred")
    assert exc.value.service == "fred"
    assert exc.value.env_var == "FRED_API_KEY"

    # No global, no env at all -> raise.
    monkeypatch.setitem(_resolvers._GLOBAL_KEYS, "fred", None)
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError):
        _resolve_api_key("fred")
