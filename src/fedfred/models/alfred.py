# filepath: /src/fedfred/models/alfred.py
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

from __future__ import annotations
from datetime import date
import asyncio
from typing import Any, Dict, Iterable, Iterator, Optional, Union, overload
from collections.abc import Sequence

class VintageDate(date):
    """A FRED/ALFRED vintage date that *is* a ``datetime.date``.

    Drops into anything expecting a date (comparisons, ``strftime``, pandas
    indexes, fedfred's own date params) and renders as a bare ISO string in
    notebooks instead of ``datetime.date(2024, 3, 28)``.
    """

    __slots__ = ()

    @classmethod
    def _from_iso(cls, value: str) -> "VintageDate":
        d = date.fromisoformat(value)          # strict 'YYYY-MM-DD'
        return cls(d.year, d.month, d.day)     # 3-arg == date.__new__; mypy-clean

    @property
    def vintage_date(self) -> str:
        """v3 compatibility: the ISO string callers used to read off the dataclass."""
        return self.isoformat()

    def __repr__(self) -> str:
        return self.isoformat()

class VintageDates(Sequence[VintageDate]):
    """Immutable, notebook-friendly sequence of ALFRED vintage dates."""

    __slots__ = ("_dates", "series_id")

    def __init__(self, dates: Iterable[VintageDate], series_id: Optional[str] = None) -> None:
        self._dates: tuple[VintageDate, ...] = tuple(dates)
        self.series_id = series_id

    @overload
    def __getitem__(self, index: int) -> VintageDate: ...
    @overload
    def __getitem__(self, index: slice) -> "VintageDates": ...
    def __getitem__(self, index: Union[int, slice]) -> Union[VintageDate, "VintageDates"]:
        if isinstance(index, slice):
            return VintageDates(self._dates[index], series_id=self.series_id)
        return self._dates[index]

    def __len__(self) -> int:
        return len(self._dates)

    def __iter__(self) -> Iterator[VintageDate]:
        return iter(self._dates)

    def __contains__(self, value: object) -> bool:
        return value in self._dates

    def __reversed__(self) -> Iterator[VintageDate]:
        return reversed(self._dates)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, VintageDates):
            return self._dates == other._dates
        return NotImplemented

    def __hash__(self) -> int:
        return hash((type(self).__name__, self._dates))

    def __repr__(self) -> str:
        if not self._dates:
            return f"VintageDates(series_id={self.series_id!r}, n=0)"
        return (f"VintageDates(series_id={self.series_id!r}, n={len(self._dates)}, "
                f"{self._dates[0].isoformat()} … {self._dates[-1].isoformat()})")

    def _repr_html_(self) -> str:
        sid = self.series_id or "—"
        if not self._dates:
            return f"<b>VintageDates</b> <code>{sid}</code> — empty"
        return (f"<b>VintageDates</b> <code>{sid}</code> — {len(self._dates)} vintages, "
                f"{self._dates[0].isoformat()} → {self._dates[-1].isoformat()}")

    @classmethod
    def to_object(cls, response: Dict[str, Any], series_id: Optional[str] = None) -> "VintageDates":
        if not isinstance(response, dict) or "vintage_dates" not in response:
            raise ValueError("Invalid API response: missing 'vintage_dates' field")
        raw = response["vintage_dates"]
        if not isinstance(raw, list):
            raise ValueError("Invalid API response: 'vintage_dates' must be a list")
        return cls((VintageDate._from_iso(v) for v in raw), series_id=series_id)

    @classmethod
    async def to_object_async(cls, response: Dict[str, Any], series_id: Optional[str] = None) -> "VintageDates":
        return await asyncio.to_thread(cls.to_object, response, series_id)