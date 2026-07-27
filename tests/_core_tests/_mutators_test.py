# filepath: /tests/_core_tests/_mutators_test.py
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

from fedfred._core import _registries
from fedfred._core._mutators import (
    _clear_api_key,
    _set_api_key,
    _set_dataframe_backend,
    _set_geodataframe_backend,
)


def test_set_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full-branch coverage for :func:`_set_api_key`.

    Covers the success path (stripped key stored under the resolved service, default
    and explicit), both arms of the non-empty-string guard (non-``str`` and
    whitespace-only), and the invalid-service guard delegated to
    :func:`_validate_service`.
    """
    monkeypatch.setitem(_registries._GLOBAL_KEYS, "fred", None)
    monkeypatch.setitem(_registries._GLOBAL_KEYS, "fraser", None)

    # Success, default service, surrounding whitespace stripped.
    _set_api_key("  my_key  ")
    assert _registries._GLOBAL_KEYS["fred"] == "my_key"

    # Success, explicit service.
    _set_api_key("fraser_key", "fraser")
    assert _registries._GLOBAL_KEYS["fraser"] == "fraser_key"

    # Guard arm 1: not a str.
    with pytest.raises(ValueError, match="api_key must be a non-empty string"):
        _set_api_key(123)  # type: ignore[arg-type]

    # Guard arm 2: str but blank after strip.
    with pytest.raises(ValueError, match="api_key must be a non-empty string"):
        _set_api_key("   ")

    # Invalid service -> propagated from _validate_service.
    with pytest.raises(ValueError):
        _set_api_key("k", "bogus")  # type: ignore[arg-type]


def test_clear_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full-branch coverage for :func:`_clear_api_key`.

    Covers the success path (a configured key reset to ``None``) and the
    invalid-service guard delegated to :func:`_validate_service`.
    """
    monkeypatch.setitem(_registries._GLOBAL_KEYS, "fred", "preset_key")

    # Success: configured key is cleared to None.
    _clear_api_key("fred")
    assert _registries._GLOBAL_KEYS["fred"] is None

    # Invalid service -> propagated from _validate_service.
    with pytest.raises(ValueError):
        _clear_api_key("bogus")  # type: ignore[arg-type]


def test_set_dataframe_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full-branch coverage for :func:`_set_dataframe_backend`.

    Covers the success path (validated backend rebinds the registry global) and the
    invalid-backend guard delegated to :func:`_validate_dataframe_backend`, asserting
    the global is left unmutated when validation fails.
    """
    monkeypatch.setattr(_registries, "_GLOBAL_DATAFRAME_BACKEND", None)

    # Success: registry global rebound to the validated backend.
    _set_dataframe_backend("polars")
    assert _registries._GLOBAL_DATAFRAME_BACKEND == "polars"

    # Invalid backend -> raise, and the global is not mutated past the guard.
    monkeypatch.setattr(_registries, "_GLOBAL_DATAFRAME_BACKEND", None)
    with pytest.raises(ValueError):
        _set_dataframe_backend("numpy")  # type: ignore[arg-type]
    assert _registries._GLOBAL_DATAFRAME_BACKEND is None


def test_set_geodataframe_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full-branch coverage for :func:`_set_geodataframe_backend`.

    Covers the success path (validated backend rebinds the registry global) and the
    invalid-backend guard delegated to :func:`_validate_geodataframe_backend`,
    asserting the global is left unmutated when validation fails.
    """
    monkeypatch.setattr(_registries, "_GLOBAL_GEODATAFRAME_BACKEND", None)

    # Success: registry global rebound to the validated backend.
    _set_geodataframe_backend("polars-st")
    assert _registries._GLOBAL_GEODATAFRAME_BACKEND == "polars-st"

    # Invalid backend -> raise, and the global is not mutated past the guard.
    monkeypatch.setattr(_registries, "_GLOBAL_GEODATAFRAME_BACKEND", None)
    with pytest.raises(ValueError):
        _set_geodataframe_backend("shapely")  # type: ignore[arg-type]
    assert _registries._GLOBAL_GEODATAFRAME_BACKEND is None
