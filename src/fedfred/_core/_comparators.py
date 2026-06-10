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

Pure numpy predicates that test observation columns for equality. They are the
comparison side of the columnar core: rather than materialize element objects to
answer membership or equality, these operate directly on the parallel column
arrays, which is what keeps ``_ObservationSequence.__contains__`` and
``__eq__`` cheap at ALFRED scale.

Both treat missing data consistently with the rest of the model — a ``NaN`` cell
in a float column matches a ``None`` target or another positionally-aligned
``NaN`` — so the object-layer ``None`` and the column-layer ``NaN`` compare equal
across the boundary. The module is named for what its functions do (compare), not
the type they operate on; it holds no state, performs no I/O, and depends only on
numpy.

Functions:
    _row_match_mask: Per-row equality mask of an element against every row.
    _columns_equal: Whole-column equality between two column mappings.

See Also:
    - :class:`fedfred._internals._models._ObservationSequence`: Consumes these in
      ``__contains__`` (via :func:`_row_match_mask`) and ``__eq__`` (via
      :func:`_columns_equal`).

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from collections.abc import Mapping
from datetime import date
from typing import cast

import numpy as np


def _row_match_mask(
    columns: dict[str, np.ndarray],
    targets: Mapping[str, object],
) -> np.ndarray:
    """Per-row boolean mask of rows that equal an element across every column.

    Tests one observation element against the columns by reading the attribute
    named for each column (``date``, ``value``, and for vintage data
    ``realtime_start`` / ``realtime_end``) and AND-ing the per-column equality
    masks. Backs membership tests (``element in sequence``) without materializing
    any row objects.

    Comparison is dtype-aware: datetime columns compare against
    ``numpy.datetime64(target, "D")``; a ``None`` target matches ``NaN`` cells
    (missing observations); every other column compares with ``==``.

    Args:
        columns (dict[str, numpy.ndarray]): Ordered ``name -> array`` mapping
            (all columns equal length); each key must name an attribute on
            the target element.
        targets (Mapping[str, object]): The element to match — typically a ``PointObservation`` or
            ``VintageObservation`` whose attributes correspond to the column
            names.

    Returns:
        numpy.ndarray: A 1-D boolean mask, ``True`` at each row whose every
        column equals the corresponding attribute of ``value``.

    Examples:
        >>> import numpy as np
        >>> from datetime import date
        >>> from types import SimpleNamespace
        >>> from fedfred._core._comparators import _row_match_mask
        >>> columns = {
        ...     "date": np.array(["2020-01-01", "2020-02-01"], dtype="datetime64[D]"),
        ...     "value": np.array([1.5, np.nan]),
        ... }
        >>> _row_match_mask(columns, SimpleNamespace(date=date(2020, 1, 1), value=1.5)).tolist()
        [True, False]
        >>> _row_match_mask(columns, SimpleNamespace(date=date(2020, 2, 1), value=None)).tolist()
        [False, True]
    """
    n = len(next(iter(columns.values())))

    mask = np.ones(n, dtype=bool)

    for name, arr in columns.items():
        target = targets[name]                       # object, not Any

        if arr.dtype.kind == "M":
            mask &= arr == np.datetime64(cast(date, target), "D")

        elif target is None:
            mask &= np.isnan(arr)

        else:
            mask &= arr == target

    return mask

def _columns_equal(
    a: dict[str, np.ndarray],
    b: dict[str, np.ndarray]
) -> bool:
    """Whether two column mappings hold equal data, NaN-aware.

    Compares two ``name -> array`` mappings for equality: identical keys, and
    equal arrays per key. Float columns are compared with ``equal_nan=True`` so
    positionally-aligned missing observations (``NaN``) count as equal — without
    which two otherwise-identical observation sets would compare unequal whenever
    either holds a missing value.

    Args:
        a (dict[str, numpy.ndarray]): The first column mapping.
        b (dict[str, numpy.ndarray]): The second column mapping.

    Returns:
        bool: ``True`` if both mappings have the same keys and every
        corresponding array is element-wise equal (treating aligned ``NaN`` as
        equal in float columns); ``False`` otherwise.

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
