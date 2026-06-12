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

Distinct marker objects for the places where ``None`` is itself a valid value and a
function must tell "no argument supplied" from "argument supplied as ``None``" — most
notably default-bearing accessors like ``AdjustableFIFOCache.pop``. Implemented as a
single-member :class:`enum.Enum` so each sentinel is a unique, identity-comparable
singleton with a real member type that static checkers can narrow on, unlike a bare
``object()``.

Constants:
    MISSING: The "no value supplied" sentinel.

See Also:
    - :class:`fedfred._internals._caching.AdjustableFIFOCache`: Uses :data:`MISSING`
      to distinguish an omitted ``pop`` default from an explicit ``None``.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from enum import Enum


class _Sentinel(Enum):
    """Enumeration of the package's singleton sentinel values.

    Each member is a unique singleton whose **identity** (``is``) is the comparison
    contract, and whose member type — :class:`_Sentinel` — lets a caller annotate a
    parameter as ``T | _Sentinel`` and narrow with ``value is MISSING``. The string
    member values are arbitrary labels used only for ``repr``; only object identity is
    significant, never the value.

    Members:
        MISSING: Marks the absence of a supplied value, distinct from ``None``.
    """

    MISSING = "MISSING"
    """The "no value supplied" sentinel — distinct from an explicit ``None``."""


MISSING = _Sentinel.MISSING
"""Sentinel distinguishing "no value supplied" from an explicit ``None`` default.

Re-exported at module level for ergonomic import (``from ..._sentinels import MISSING``).
Compare by identity (``value is MISSING``); annotate the surrounding parameter as
``T | _Sentinel`` so the checker can narrow it.
"""
