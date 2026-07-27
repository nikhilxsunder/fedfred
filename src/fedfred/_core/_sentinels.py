# filepath: /src/fedfred/_core/_sentinels.py
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
"""Singleton sentinels for the fedfred core package.

Distinct marker objects for the places where ``None`` is itself a valid value and a function
must distinguish "no argument supplied" from "argument supplied as ``None``" — most notably
default-bearing accessors like :meth:`AdjustableFIFOCache.pop`. Implemented as a single-member
:class:`enum.Enum` so each sentinel is a unique, identity-comparable singleton with a real
member type that static checkers can narrow on (``value is MISSING`` refines the non-sentinel
branch) — the property a bare ``object()`` sentinel cannot give.

Constants:
    MISSING: The "no value supplied" sentinel, distinct from an explicit ``None``.

See Also:
    - :class:`fedfred._internals._caching.AdjustableFIFOCache`: Uses :data:`MISSING` to
      distinguish an omitted ``pop`` default from an explicit ``None``.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from enum import Enum


class _Sentinel(Enum):
    """Enumeration of the package's singleton sentinel values.

    Each member is a unique singleton whose **identity** (``is``) is the comparison contract.
    Deriving the sentinels from an :class:`enum.Enum` gives three things for free: guaranteed
    singleton identity, a distinct member type (:class:`_Sentinel`) that a caller can use to
    annotate a parameter as ``T | _Sentinel`` and narrow with ``value is MISSING``, and a clean
    ``repr``. The string member values are arbitrary labels used only for that ``repr``; only
    object identity is ever significant, never the value.

    Members:
        MISSING: Marks the absence of a supplied value, distinct from ``None``.
    """

    MISSING = "MISSING"
    """The "no value supplied" sentinel — distinct from an explicit ``None``."""


MISSING = _Sentinel.MISSING
"""Sentinel distinguishing "no value supplied" from an explicit ``None`` default.

Re-exported at module level for ergonomic import (``from ..._sentinels import MISSING``).
Enables the "``None`` is a valid value" pattern: a parameter defaults to :data:`MISSING`, so the
callee can tell "argument omitted" from "argument explicitly ``None``". Compare by identity
(``value is MISSING``), and annotate the parameter as ``T | _Sentinel`` so a type checker
narrows the non-sentinel branch.

Examples:
    >>> from fedfred._core._sentinels import MISSING, _Sentinel
    >>> def f(x: int | None | _Sentinel = MISSING) -> str:
    ...     if x is MISSING:
    ...         return "omitted"
    ...     return f"got {x!r}"
    >>> f()
    'omitted'
    >>> f(None)
    'got None'
    >>> f(5)
    'got 5'
"""
