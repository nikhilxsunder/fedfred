# filepath: /src/fedfred/_core/_schemas.py
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
"""Column dtype schemas for the fedfred observation model.

The declared ``column name -> numpy dtype kind`` contract for the columnar observation core —
the single source of truth for which observation columns are datetime (``"M"``) and which are
float (``"f"``). Centralizing it here keeps that dtype knowledge from being duplicated across
the validator, comparator, and accessor layers that all reason about column types, so the
check at construction and the branches at read time cannot disagree.

Pure data, no logic: consumed by :mod:`._validators` to check column dtypes at construction,
and treated as authoritative by the columnar operations in :mod:`._comparators` and
:mod:`._accessors` when they branch on ``arr.dtype.kind``. A column that passes validation is
therefore guaranteed to satisfy the kind those branches assume.

Constants:
    _EXPECTED_KIND: Observation column name -> expected numpy dtype kind.

See Also:
    - :mod:`fedfred._core._validators`: Validates observation columns against this schema.
    - :mod:`fedfred._core._comparators`: Branches on ``dtype.kind`` for the columns keyed here.
    - :mod:`fedfred._core._accessors`: Reads cells from the columns keyed here.
    - :class:`fedfred._internals._models._ObservationSequence`: Stores the columns this schema
      governs.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

_EXPECTED_KIND: dict[str, str] = {
    "date": "M",
    "realtime_start": "M",
    "realtime_end": "M",
    "value": "f",
}
"""Expected :attr:`numpy.dtype.kind` for each observation column.

Maps an observation column name to the single-character dtype kind it must carry:
``"M"`` (datetime64) for ``date`` and the ALFRED realtime brackets
(``realtime_start`` / ``realtime_end``), ``"f"`` (float64) for ``value``. Consulted by
:func:`_validate_observation_columns` to reject a mistyped column at construction, and the
authoritative source the columnar comparators and accessors rely on when they branch on
``arr.dtype.kind`` — so a column that passed validation is guaranteed to satisfy the kind
those branches assume."""
