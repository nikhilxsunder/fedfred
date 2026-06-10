
from datetime import date
import numpy as np

# ---- scalar cell access (used by leaf _make) -------------------------------

def _cell_date(dates: np.ndarray, i: int) -> date:
    return dates[i].item()

def _cell_value(values: np.ndarray, i: int) -> float | None:
    v = values[i]
    return None if np.isnan(v) else float(v)

def _first_date_index(dates: np.ndarray, key: str) -> int | None:
    """First row index whose date equals the ISO ``key``; None if absent.

    Raises ValueError on an unparseable key (the caller maps it to a domain error).
    """
    target = np.datetime64(key, "D")          # ValueError on bad ISO string
    idx = np.flatnonzero(dates == target)
    return int(idx[0]) if idx.size else None