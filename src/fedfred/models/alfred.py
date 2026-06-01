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

import asyncio
from typing import Dict, ClassVar, Any, Optional, Iterable
from datetime import date
from .._internals import _DateBase, _DateSequence
from .._core import _require_list

# TODO: Fix all docstrings post error design.

class VintageDate(_DateBase):
    """A FRED/ALFRED vintage date that *is* a ``datetime.date`` subclass.

    Drops into any API expecting a date (comparisons, ``strftime``, pandas
    indexes, fedfred's own date params) and renders as a bare ISO string in
    notebooks instead of ``datetime.date(2024, 3, 28)``.

    Attributes:
        vintage_date (str): v3-compat alias for the ISO string.

    Examples:
        >>> import fedfred as fd
        >>> alfred = fd.Alfred('your_api_key')
        >>> vintages = alfred.get_series_vintage_dates('GDPC1')
        >>> vintages[-1]
        2024-03-28

    See Also:
        - :class:`fedfred.VintageDates`: The plural container.

    References:
        - Fred API Documentation: https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
    """

    __slots__ = ()

    _response_key: ClassVar[str] = "vintage_dates"

    @classmethod
    def _parse_value(cls, raw: Any) -> "VintageDate":
        """Build a single VintageDate from one raw ISO-string payload."""

        if not isinstance(raw, str):
            raise ModelError("Invalid vintage_date payload: expected an ISO string")
        d = date.fromisoformat(raw)
        return cls(d.year, d.month, d.day)

    @property
    def vintage_date(self) -> str:
        """v3-compat alias for the ISO string (matches the old ``vintage_date`` attribute)."""

        return self.isoformat()

    def __repr__(self) -> str:

        return self.isoformat()


class VintageDates(_DateSequence[VintageDate]):
    __slots__ = ("series_id",)

    series_id: Optional[str]

    def __init__(
        self, items: Iterable[VintageDate], series_id: Optional[str] = None
    ) -> None:
        super().__init__(items)
        self.series_id = series_id

    def _clone(self, items: Iterable[VintageDate]) -> Self:
        return type(self)(items, series_id=self.series_id)

    @classmethod
    def to_object(
        cls, response: Dict[str, Any], series_id: Optional[str] = None
    ) -> "VintageDates":
        raw = _require_list(response, cls._response_key)
        return cls((cls._parse_value(v) for v in raw), series_id=series_id)

    @classmethod
    async def to_object_async(
        cls, response: Dict[str, Any], series_id: Optional[str] = None
    ) -> "VintageDates":
        return await asyncio.to_thread(cls.to_object, response, series_id)

    def _lookup_value(self, item: VintageDate) -> str:
        return item.isoformat()
