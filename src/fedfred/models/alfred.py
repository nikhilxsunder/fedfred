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

from collections.abc import Iterable
from datetime import date
from typing import Any, ClassVar, Self

from .._internals import _DateBase, _DateSequence


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

    _response_keys: ClassVar[tuple[str, ...]] = ("vintage_dates",)
    """Payload key(s) under which FRED returns the vintage-date list."""

    @classmethod
    def _parse_value(
        cls,
        raw: object
    ) -> VintageDate:
        """Build a single :class:`VintageDate` from one raw ISO-string payload.

        Args:
            raw (object): The raw payload entry. Expected to be an ISO ``YYYY-MM-DD`` string.

        Returns:
            VintageDate: The parsed vintage date.

        Raises:
            ModelError: If ``raw`` is not a string.
        """
        if not isinstance(raw, str):
            raise ModelError("Invalid vintage_date payload: expected an ISO string")  # TODO: ModelError

        d = date.fromisoformat(raw)

        return cls(d.year, d.month, d.day)

    @property
    def vintage_date(self) -> str:
        """v3-compat alias for the ISO string (matches the old ``vintage_date`` attribute).

        Returns:
            str: The ISO 8601 representation of the date.
        """
        return self.isoformat()

    def __repr__(self) -> str:
        """Return the bare ISO date string.

        Returns:
            str: The ISO 8601 representation of the date.
        """
        return self.isoformat()


class VintageDates(_DateSequence[VintageDate]):
    """An immutable, notebook-friendly sequence of :class:`VintageDate` objects.

    Carries an optional ``series_id`` sidecar (the series these vintages belong
    to), forwarded through slicing via :meth:`_clone`. String-keyed by ISO date
    via :meth:`_lookup_value`.

    Attributes:
        series_id (str, optional): The series these vintage dates belong to.

    See Also:
        - :class:`fedfred.VintageDate`: The element type.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.VintageDates.html
    """

    __slots__ = ("series_id",)

    series_id: str | None
    """The series these vintage dates belong to, or ``None`` if unattached."""

    def __init__(
        self,
        items: Iterable[VintageDate],
        series_id: str | None = None
    ) -> None:
        """Materialize ``items`` and attach an optional ``series_id``.

        Args:
            items (Iterable[VintageDate]): The vintage dates to store.
            series_id (str, optional): The owning series id. Forwarded to sliced copies by :meth:`_clone`. Defaults to ``None``.
        """
        super().__init__(items)
        self.series_id = series_id

    def _clone(
        self,
        items: Iterable[VintageDate]
    ) -> Self:
        """Construct a new :class:`VintageDates` forwarding the ``series_id``.

        Args:
            items (Iterable[VintageDate]): The elements for the new sequence.

        Returns:
            VintageDates: A new sequence carrying the same ``series_id``.
        """
        return type(self)(items, series_id=self.series_id)

    @classmethod
    def _from_response(
        cls,
        response: dict[str, Any],
        series_id: str | None = None
    ) -> VintageDates:
        """Build a :class:`VintageDates` from a FRED/ALFRED response payload.

        Args:
            response (dict[str, Any]): The raw FRED/ALFRED response payload.
            series_id (str, optional): The owning series id to attach. Defaults to ``None``.

        Returns:
            VintageDates: A sequence of :class:`VintageDate` objects.

        Raises:
            ParsingError: If the response lacks the ``vintage_dates`` key or it is not a list.
        """
        raw = cls._extract(response)

        return cls((cls._parse_value(v) for v in raw), series_id=series_id)

    def _lookup_value(self, item: VintageDate) -> str:
        """Compute the lookup key for an item as its ISO date string.

        Args:
            item (VintageDate): The element to compute a lookup key for.

        Returns:
            str: The ISO 8601 representation of the date.
        """
        return item.isoformat()
