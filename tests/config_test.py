# filepath: /test/config_test.py
#
# Copyright (c) 2025 Nikhil Sunder
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
"""
Comprehensive unit tests for the config module.
"""

import importlib
import pytest
from fedfred import config
from fedfred.__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__

class TestConfigFunctions:
    def test_set_api_key(self, monkeypatch):
        # Ensure a clean module state for this test
        importlib.reload(config)

        # 1) Valid key: sets stripped value under lock
        config.set_api_key("  my-key  ")
        # Access the module-level _API_KEY to verify
        assert getattr(config, "_API_KEY") == "my-key"

        # 2) Invalid types / values raise ValueError
        with pytest.raises(ValueError, match="api_key must be a non-empty string."):
            config.set_api_key("")  # empty string

        with pytest.raises(ValueError, match="api_key must be a non-empty string."):
            config.set_api_key("   ")  # whitespace-only string

        with pytest.raises(ValueError, match="api_key must be a non-empty string."):
            config.set_api_key(None)  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="api_key must be a non-empty string."):
            config.set_api_key(123)  # type: ignore[arg-type]

    def test_get_api_key(self, monkeypatch):
        # Start from a clean module state
        importlib.reload(config)

        # ---- set_api_key + get_api_key (global wins over env) ----
        monkeypatch.setenv("FRED_API_KEY", "  from-env  ")
        config.set_api_key("  from-set  ")
        # _API_KEY should be stripped and used by get_api_key
        assert getattr(config, "_API_KEY") == "from-set"
        assert config.get_api_key() == "from-set"

        # ---- set_api_key invalid inputs ----
        with pytest.raises(ValueError, match="api_key must be a non-empty string."):
            config.set_api_key("")  # empty
        with pytest.raises(ValueError, match="api_key must be a non-empty string."):
            config.set_api_key("   ")  # whitespace
        with pytest.raises(ValueError, match="api_key must be a non-empty string."):
            config.set_api_key(None)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="api_key must be a non-empty string."):
            config.set_api_key(123)  # type: ignore[arg-type]

        # ---- get_api_key: fallback to env var, then None ----
        # Clear global and re-set env
        config._API_KEY = None  # type: ignore[attr-defined]
        monkeypatch.setenv("FRED_API_KEY", "  env-key  ")
        assert config.get_api_key() == "env-key"

        # No global, no env -> None
        config._API_KEY = None  # type: ignore[attr-defined]
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        assert config.get_api_key() is None

        # ---- resolve_api_key explicit argument branch ----
        # explicit non-empty wins over everything
        monkeypatch.setenv("FRED_API_KEY", "ignored-env")
        config._API_KEY = "ignored-global"  # type: ignore[attr-defined]
        assert config.resolve_api_key("  explicit-key  ") == "explicit-key"

        # explicit empty / whitespace -> ValueError
        with pytest.raises(ValueError, match="explicit API key must be a non-empty string."):
            config.resolve_api_key("   ")

        # ---- resolve_api_key using global / env / error ----
        # Use global when explicit is None
        config._API_KEY = "from-global"  # type: ignore[attr-defined]
        monkeypatch.setenv("FRED_API_KEY", "from-env")
        assert config.resolve_api_key() == "from-global"

        # No global but env set -> env used via get_api_key
        config._API_KEY = None  # type: ignore[attr-defined]
        monkeypatch.setenv("FRED_API_KEY", "  env-only  ")
        assert config.resolve_api_key() == "env-only"

        # Neither global nor env -> RuntimeError
        config._API_KEY = None  # type: ignore[attr-defined]
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="No FRED API key configured"):
            config.resolve_api_key()

    def test_resolve_api_key_full_coverage(self, monkeypatch):
        # Fresh module state
        importlib.reload(config)

        # 1) explicit non-empty key wins, is stripped
        assert config.resolve_api_key("  explicit-key  ") == "explicit-key"

        # 2) explicit key provided but empty/whitespace -> ValueError
        with pytest.raises(ValueError, match="explicit API key must be a non-empty string."):
            config.resolve_api_key("   ")

        # 3) explicit is None, get_api_key returns value -> that value is used
        monkeypatch.setattr("fedfred.config.get_api_key", lambda: "from-get")
        assert config.resolve_api_key() == "from-get"

        # 4) explicit is None, get_api_key returns None -> RuntimeError
        monkeypatch.setattr("fedfred.config.get_api_key", lambda: None)
        with pytest.raises(RuntimeError, match="No FRED API key configured."):
            config.resolve_api_key()
