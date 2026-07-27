# filepath: /src/fedfred/_core/_comparators.py
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
"""Column comparison primitives for the observation model.

Pure numpy predicates that answer equality questions about observation columns without
materializing any element objects. They are the comparison side of the columnar core: to
answer membership or whole-sequence equality, they operate directly on the parallel column
arrays, which is what keeps ``_ObservationSequence.__contains__`` and ``__eq__`` cheap at
ALFRED scale (thousands of vintage rows per series).

Both honor the two-layer missing-data contract used across the model: a ``NaN`` cell in a
float column matches a ``None`` target (:func:`_row_match_mask`) or a positionally-aligned
``NaN`` in the other column (:func:`_columns_equal`), so the object-layer ``None`` and the
column-layer ``NaN`` compare equal across the boundary. The module is named for what its
functions do (compare), not the type they touch; it owns no state, performs no I/O, and
depends only on numpy.

Functions:
    _row_match_mask: Per-row equality mask of one target element against every row.
    _columns_equal: Whole-column equality between two column mappings (NaN-aware for floats).

See Also:
    - :class:`fedfred._internals._models._ObservationSequence`: Consumes these in
      ``__contains__`` (via :func:`_row_match_mask`) and ``__eq__`` (via
      :func:`_columns_equal`).
    - :mod:`fedfred._core._accessors`: The read-side counterpart — single-cell reads rather
      than whole-column predicates.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import cast

import numpy as np


def _row_match_mask(
    columns: dict[str, np.ndarray],
    targets: Mapping[str, object],
) -> np.ndarray:
    """Per-row boolean mask of rows equal to a target element across every column.

    Tests one candidate element — supplied as a ``name -> value`` mapping — against the
    columns by looking up each column's name in ``targets`` and AND-ing the per-column
    equality masks. Backs membership tests (``element in sequence``) without materializing
    any row objects.

    Comparison is dtype-aware: datetime columns (dtype kind ``"M"``) compare against
    ``numpy.datetime64(target, "D")``; a ``None`` target matches ``NaN`` cells (missing
    observations); every other column compares with ``==``.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping; all arrays
            share one length, and every key must also be present in ``targets``.
        targets (Mapping[str, object]): The element to match, as a ``name -> value`` mapping
            keyed by the same column names — one target scalar per column.

    Returns:
        numpy.ndarray: A 1-D boolean mask, ``True`` at each row whose value in every column
        equals the corresponding entry in ``targets``.

    Examples:
        >>> import numpy as np
        >>> from datetime import date
        >>> from fedfred._core._comparators import _row_match_mask
        >>> columns = {
        ...     "date": np.array(["2020-01-01", "2020-02-01"], dtype="datetime64[D]"),
        ...     "value": np.array([1.5, np.nan]),
        ... }
        >>> _row_match_mask(columns, {"date": date(2020, 1, 1), "value": 1.5}).tolist()
        [True, False]
        >>> _row_match_mask(columns, {"date": date(2020, 2, 1), "value": None}).tolist()
        [False, True]
    """
    n = len(next(iter(columns.values())))

    mask = np.ones(n, dtype=bool)

    for name, arr in columns.items():
        target = targets[name]  # object, not Any

        if arr.dtype.kind == "M":
            mask &= arr == np.datetime64(cast(date, target), "D")

        elif target is None:
            mask &= np.isnan(arr)

        else:
            mask &= arr == target

    return mask


def _columns_equal(a: dict[str, np.ndarray], b: dict[str, np.ndarray]) -> bool:
    """Whether two column mappings hold equal data, NaN-aware for float columns.

    Compares two ``name -> array`` mappings for equality: identical keys, and an
    element-wise-equal array under each key. Float columns are compared with
    ``equal_nan=True`` so positionally-aligned missing observations (``NaN``) count as
    equal — without which two otherwise-identical observation sets would compare unequal
    whenever either holds a missing value. Non-float columns use ``equal_nan=False``, which
    is also required: ``numpy.array_equal(..., equal_nan=True)`` rejects non-floating dtypes,
    so the per-column dtype guard is load-bearing, not cosmetic.

    Args:
        a (dict[str, numpy.ndarray]): The first column mapping.
        b (dict[str, numpy.ndarray]): The second column mapping.

    Returns:
        bool: ``True`` if both mappings have the same keys and every corresponding array is
        element-wise equal (treating aligned ``NaN`` as equal in float columns); ``False``
        otherwise, including when the key sets differ.

    Examples:
        >>> import numpy as np
        >>> from fedfred._core._comparators import _columns_equal
        >>> a = {"value": np.array([1.5, np.nan])}
        >>> _columns_equal(a, {"value": np.array([1.5, np.nan])})
        True
        >>> _columns_equal(a, {"value": np.array([1.5, 2.0])})
        False
        >>> _columns_equal(a, {"date": np.array([1.5, np.nan])})
        False
    """
    if a.keys() != b.keys():
        return False

    return all(np.array_equal(a[k], b[k], equal_nan=(a[k].dtype.kind == "f")) for k in a)
