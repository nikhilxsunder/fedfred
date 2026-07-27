# filepath: /src/fedfred/_core/_loaders.py
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
"""Optional-dependency loading for the fedfred core package.

A single helper that imports an optional third-party backend (polars, dask, pyarrow, cudf, …)
on demand and, when it is absent, raises a typed
:class:`~fedfred.exceptions.DependencyLoadingError` carrying the package name and a
``pip install fedfred[...]`` install hint. Centralizing this keeps the conversion and model
layers free of repeated ``try/except ImportError`` blocks — every optional backend is reached
through one consistent failure path, so a missing backend produces the same actionable error
regardless of which feature triggered it.

Functions:
    _require_module: Import an optional module, or raise
        :class:`~fedfred.exceptions.DependencyLoadingError` if it is absent.

See Also:
    - :mod:`fedfred._core._converters`: Loads the optional DataFrame backends behind
      ``to_polars`` / ``to_dask`` / ``to_cudf`` / ``to_arrow`` through this helper.
    - :class:`fedfred.exceptions.DependencyLoadingError`: The raised error type.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

import importlib
from types import ModuleType

from ..exceptions import DependencyLoadingError


def _require_module(module: str, feature: str, extra: str | None = None) -> ModuleType:
    """Import an optional dependency, or raise a typed error if it is absent.

    Resolves ``module`` via :func:`importlib.import_module` and returns it. On
    :class:`ImportError`, raises :class:`DependencyLoadingError` carrying the top-level package
    name and a ``pip install fedfred[...]`` hint, so the caller and the user get a consistent,
    actionable message instead of a bare ``ImportError`` surfacing from deep in a conversion
    method.

    Args:
        module (str): The importable module name (e.g. ``"polars"``, ``"dask.dataframe"``). The
            reported package name is its first dotted segment.
        feature (str): The fedfred feature requiring the module, surfaced in the error message
            (e.g. ``"to_polars"``).
        extra (str | None): The extras-group name for the install hint
            (``pip install fedfred[<extra>]``). Defaults to the reported package name when
            ``None``. Override it when the extras-group name differs from the import package
            name — e.g. importing ``"pyarrow"`` but installing ``fedfred[arrow]`` needs
            ``extra="arrow"``. A dotted module whose first segment already equals the extra
            (``"dask.dataframe"`` → ``dask``) does *not* need it.

    Returns:
        ModuleType: The imported module.

    Raises:
        DependencyLoadingError: If ``module`` cannot be imported.

    Notes:
        Any :class:`ImportError` is reported as "not installed", including the case where the
        module *is* installed but fails to import (a broken or incompatible transitive
        dependency). That misattributes an environment problem as a missing package; if that
        distinction matters, inspect the chained ``original_exception``.

    Examples:
        >>> from fedfred._core._loaders import _require_module
        >>> _require_module("json", "example").__name__
        'json'
    """
    try:
        return importlib.import_module(module)

    except ImportError as exc:
        pkg = module.split(".")[0]

        raise DependencyLoadingError(
            message=f"Optional dependency '{pkg}' is not installed.",
            package=pkg,
            feature=feature,
            install_hint=f"pip install fedfred[{extra or pkg}]",
            original_exception=exc,
        ) from exc
