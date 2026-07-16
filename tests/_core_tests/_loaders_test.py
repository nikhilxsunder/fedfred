# filepath: /tests/_core_tests/_loaders_test.py
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

import importlib

import pytest

from fedfred._core._loaders import _require_module
from fedfred.exceptions import DependencyLoadingError


def test_require_module():
    # --- success: a present module is imported and returned -------------------
    assert _require_module("json", "example") is importlib.import_module("json")
    assert _require_module("json", "example").__name__ == "json"
    # a dotted module resolves to the submodule, not the top-level package
    assert _require_module("collections.abc", "example").__name__ == "collections.abc"

    # --- missing, extra=None: install hint defaults to the package name -------
    with pytest.raises(DependencyLoadingError) as exc:
        _require_module("fedfred_missing_backend_zzz", "to_something")

    err = exc.value
    assert err.package == "fedfred_missing_backend_zzz"
    assert err.feature == "to_something"
    assert err.install_hint == "pip install fedfred[fedfred_missing_backend_zzz]"
    assert err.message == "Optional dependency 'fedfred_missing_backend_zzz' is not installed."
    # the underlying ImportError is both chained and carried on the payload
    assert isinstance(err.original_exception, ImportError)
    assert err.__cause__ is err.original_exception

    # --- missing, dotted + extra override -------------------------------------
    # dotted module -> package is the FIRST segment; extra overrides the hint
    # (the dask.dataframe -> dask case that motivates the override)
    with pytest.raises(DependencyLoadingError) as exc:
        _require_module("fedfred_missing_backend_zzz.frame", "to_dask", extra="dask")

    err = exc.value
    assert err.package == "fedfred_missing_backend_zzz"       # first dotted segment
    assert err.feature == "to_dask"
    assert err.install_hint == "pip install fedfred[dask]"    # extra, not package
    assert isinstance(err.original_exception, ImportError)