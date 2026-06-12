# filepath: /src/fedfred/exceptions/core/loading.py
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
"""Loading-layer exceptions for the fedfred core package.

The error hierarchy for :mod:`fedfred._core._loaders`, which imports optional
third-party backends on demand. A missing backend surfaces as
:class:`DependencyLoadingError`, carrying the package name and an install hint so
the user gets an actionable message rather than a bare ``ImportError``.

Classes:
    DependencyLoadingError: An optional dependency is required but not installed.

See Also:
    - :func:`fedfred._core._loaders._require_module`: Raises this.
    - :class:`fedfred.exceptions.core.base.CoreError`: The core-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import CoreError

__all__ = [
    "DependencyLoadingError"
]


@dataclass(frozen=True, slots=True)
class DependencyLoadingError(CoreError):
    """Raised when an optional third-party dependency is required but not installed.

    Raised by the loader when a feature depends on an external backend (pandas,
    polars, dask, pyarrow, cudf, …) that is not part of fedfred's required
    installation set. The base ``message`` is supplied by the loader; the install
    hint and version constraint are appended by ``__str__``.

    Attributes:
        package (str): Name of the missing package.
        feature (str | None): The fedfred feature that required it, if known.
        install_hint (str | None): A suggested installation command.
        version_spec (str | None): A required version constraint, if any.
        message (str): Human-readable message (inherited from :class:`CoreError`).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying ``ImportError``,
            if any (inherited).

    Examples:
        >>> exc = DependencyLoadingError(
        ...     message="Optional dependency 'polars' is not installed.",
        ...     package="polars",
        ...     feature="to_polars",
        ...     install_hint="pip install fedfred[polars]",
        ... )
        >>> str(exc)
        "Optional dependency 'polars' is not installed."
        "(install with `pip install fedfred[polars]`)"
    """

    package: str = ""
    """Name of the missing package."""

    feature: str | None = None
    """The fedfred feature that required the dependency, if known."""

    install_hint: str | None = None
    """A suggested installation command, surfaced in ``__str__``."""

    version_spec: str | None = None
    """A required version constraint, if any."""

    def __str__(self) -> str:
        """Return the message, suffixed with version and install-hint context.

        Returns:
            str: :attr:`message`, with ``(required version …; install with `…`)``
            appended for whichever of :attr:`version_spec` / :attr:`install_hint`
            are set; the bare :attr:`message` otherwise.
        """
        extras: list[str] = []
        if self.version_spec:
            extras.append(f"required version {self.version_spec}")
        if self.install_hint:
            extras.append(f"install with `{self.install_hint}`")
        if not extras:
            return self.message
        return f"{self.message} (" + "; ".join(extras) + ")"
