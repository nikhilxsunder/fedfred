import numpy as np
from typing import Any


def _row_match_mask(columns: dict[str, np.ndarray], value: Any) -> np.ndarray:
    """Boolean mask of rows whose every column equals the element's attributes."""
    n = len(next(iter(columns.values())))
    mask = np.ones(n, dtype=bool)
    for name, arr in columns.items():
        target = getattr(value, name)
        if arr.dtype.kind == "M":
            mask &= arr == np.datetime64(target, "D")
        elif target is None:
            mask &= np.isnan(arr)
        else:
            mask &= arr == target
    return mask


def _columns_equal(a: dict[str, np.ndarray], b: dict[str, np.ndarray]) -> bool:
    if a.keys() != b.keys():
        return False
    return all(np.array_equal(a[k], b[k], equal_nan=(a[k].dtype.kind == "f")) for k in a)
