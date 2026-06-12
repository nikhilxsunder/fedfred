# filepath: /src/fedfred/exceptions/internals/base.py
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
"""Base exception for the fedfred internals layer.

Defines :class:`InternalsError`, the independent root of every exception raised by
the ``fedfred._internals`` modules (caching, transport, rate-limiting, …). It
subclasses :class:`Exception` directly — it is *not* a
:class:`~fedfred.exceptions.base.FedFredError` — so the internals layer's error
hierarchy stands on its own and carries its own structured payload
(:attr:`message`, :attr:`context`, :attr:`original_exception`) mirroring the package
root rather than inheriting it. The internals-side counterpart of
:class:`~fedfred.exceptions.core.base.CoreError`.

Catch breadth within the internals layer:

- ``except InternalsError`` — any failure originating in the internals layer.
- ``except CachingError`` (etc.) — a specific internals module's failures.

Classes:
    InternalsError: Independent base class for all internals-layer exceptions.

See Also:
    - :class:`fedfred.exceptions.core.base.CoreError`: The sibling base for the core layer.
    - :mod:`fedfred.exceptions.internals.caching`: An internals module hierarchy under this base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class InternalsError(Exception):
    """Independent base class for exceptions raised by the fedfred internals layer.

    The common ancestor of every ``fedfred._internals`` exception — caching,
    transport, rate-limiting, and their siblings. Subclasses :class:`Exception`
    directly, so the internals hierarchy is self-contained and parallel to (not
    nested under) :class:`FedFredError`, exactly like :class:`CoreError` on the core
    side. Declares the structured payload itself rather than inheriting it;
    ``frozen=True, slots=True`` keeps the whole internals chain frozen-consistent,
    which the dataclass subclasses require.

    Attributes:
        message (str): Human-readable error message. Returned by ``__str__``.
        context (Mapping[str, Any]): Optional structured context for the error.
            Defaults to an empty mapping.
        original_exception (BaseException | None): The underlying exception this
            error wraps, if any. Defaults to ``None``; complements ``raise … from``
            chaining with programmatic access to the cause.

    Examples:
        >>> from fedfred.exceptions.internals.base import InternalsError
        >>> try:
        ...     raise InternalsError("internals layer failed")
        ... except InternalsError as exc:
        ...     print(exc)
        internals layer failed
        >>> from fedfred.exceptions.base import FedFredError
        >>> issubclass(InternalsError, FedFredError)   # deliberately independent
        False
    """

    message: str
    """Human-readable error message. Returned by :meth:`__str__`."""

    context: Mapping[str, Any] = field(default_factory=dict)
    """Optional structured context attached to the error; defaults to an empty mapping."""

    original_exception: BaseException | None = None
    """The underlying exception this error wraps, or ``None``. Complements
    ``raise … from`` chaining by keeping the cause available for programmatic
    inspection."""

    def __str__(self) -> str:
        """Return the human-readable message.

        Returns:
            str: :attr:`message`, unchanged. The structured fields
            (:attr:`context`, :attr:`original_exception`) are available for
            inspection but intentionally excluded from the string form; subclasses
            that surface extra context override this.
        """
        return self.message
