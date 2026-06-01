# filepath: /src/fedfred/_internals/_models.py
#
# Copyright (c) 2025-2026 Nikhil Sunder
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
"""fedfred._internals._models

Internal helper classes for fedfred return models. Three-layer hierarchy:

    _Sequence[T]                    — generic mechanics
    ├── _ModelSequence[T: _ModelBase]   — adds client, _parse_item
    └── _DateSequence[T: _DateBase]     — adds date-aware repr, hashability
"""

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import date, timedelta, datetime
from collections.abc import Sequence
from typing import (
    Any, ClassVar, Dict, Iterable, Iterator, Optional, Self, Tuple,
    Union, overload, TypeVar, Never, SupportsIndex,
)
from .._core import _require_list
from ._clients import _ClientModel  # pragma: no cover

# TODO: Fix all docstrings post error design.

__all__ = ["_Sequence", "_ModelSequence", "_ModelBase", "_DateBase", "_DateSequence"]


@dataclass(slots=True, kw_only=True)
class _ModelBase:
    """Base for FRED model objects. Provides common parsing and client storage."""

    client: Optional[_ClientModel] = field(default=None, repr=False, compare=False)

    _response_key: ClassVar[str]

    @classmethod
    def _from_dict(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> Self:
        raise NotImplementedError

    @classmethod
    def to_object(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None) -> Self:
        raw = _require_list(response, cls._response_key)
        if not raw:
            raise ModelError(f"No {cls._response_key} found in the response")  # TODO: ModelError
        return cls._from_dict(raw[0], client=client)

    @classmethod
    async def to_object_async(
        cls, response: Dict[str, Any], client: Optional[_ClientModel] = None
    ) -> Self:
        return await asyncio.to_thread(cls.to_object, response, client)

    def _require_client(self) -> _ClientModel:
        if self.client is None:
            raise ModelError("Client not set for this instance.")  # TODO: ModelError
        return self.client


# Type variables: one per layer so bounds stay tight where they matter.
T = TypeVar("T")
MT = TypeVar("MT", bound="_ModelBase")
DT = TypeVar("DT", bound="_DateBase")


class _Sequence(Sequence[T]):
    """Generic immutable sequence base for FRED response collections.

    Provides shared mechanics: indexing (int/str/slice), iteration, equality,
    string-key lookup via ``_lookup_key`` or ``_lookup_value`` override, and
    IPython tab completion. Payload parsing, ``to_object`` construction, and
    sidecar state (client, series_id) live in the specialized subclasses
    ``_ModelSequence`` / ``_DateSequence`` / future siblings.
    """

    __slots__ = ("_items",)

    _response_key: ClassVar[str] = ""
    _element_cls: ClassVar[type] = object
    _lookup_key: ClassVar[Optional[str]] = None
    """Attribute on items used for the default ``_lookup_value`` implementation.
    Subclasses with computed keys should override ``_lookup_value`` instead."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Auto-wire ``_response_key`` and ``_element_cls`` from the generic
        parameter, matching any base in ``__orig_bases__`` whose origin is a
        ``_Sequence`` subclass. TypeVars (``MT``, ``DT``) are skipped so the
        intermediate ``_ModelSequence`` / ``_DateSequence`` definitions don't
        spuriously rewrite their own class vars."""
        super().__init_subclass__(**kwargs)
        for base in getattr(cls, "__orig_bases__", ()):
            origin = getattr(base, "__origin__", None)
            if isinstance(origin, type) and issubclass(origin, _Sequence):
                args = getattr(base, "__args__", ())
                if args:
                    element_cls = args[0]
                    if isinstance(element_cls, type):
                        if "_response_key" not in cls.__dict__:
                            key = getattr(element_cls, "_response_key", None)
                            if isinstance(key, str):
                                cls._response_key = key
                        if "_element_cls" not in cls.__dict__:
                            cls._element_cls = element_cls
                break

    def __init__(self, items: Iterable[T]) -> None:
        self._items: Tuple[T, ...] = tuple(items)

    def _clone(self, items: Iterable[T]) -> Self:
        """Construct a new instance of ``type(self)`` holding ``items``.

        Used by slicing. Default suits subclasses whose ``__init__`` accepts
        only items. Subclasses carrying sidecar state (client, series_id)
        override this to forward that state."""
        return type(self)(items)

    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: str) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> Self: ...
    def __getitem__(self, index: Union[int, str, slice]) -> Union[T, Self]:
        if isinstance(index, slice):
            return self._clone(self._items[index])
        if isinstance(index, str):
            return self._lookup_by_key(index)
        return self._items[index]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __contains__(self, value: object) -> bool:
        return value in self._items

    def __reversed__(self) -> Iterator[T]:
        return reversed(self._items)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, type(self)):
            return self._items == other._items
        return NotImplemented

    def __repr__(self) -> str:
        return f"{type(self).__name__}(n={len(self._items)})"

    def _repr_html_(self) -> str:
        return f"<b>{type(self).__name__}</b> — {len(self._items)} items"

    def _lookup_value(self, item: T) -> Optional[str]:
        """Extract the string lookup key for an item, or ``None`` to exclude it.

        Default reads ``_lookup_key`` as an attribute and stringifies. Override
        for computed keys such as ``return item.isoformat()``. Returning
        ``None`` excludes the item from completions and from key-based lookup.
        """
        key = self._lookup_key
        if key is None:
            return None
        value = getattr(item, key, None)
        return None if value is None else str(value)

    @classmethod
    def _supports_lookup(cls) -> bool:
        """True if string-key lookup is enabled, either via ``_lookup_key``
        or by overriding ``_lookup_value``."""
        return (
            cls._lookup_key is not None
            or cls._lookup_value is not _Sequence._lookup_value
        )

    def _lookup_by_key(self, key: str) -> T:
        if not type(self)._supports_lookup():
            raise ModelError(
                f"{type(self).__name__} does not support string indexing; "
                f"use positional indexing or iterate"
            )
        for item in self._items:
            if self._lookup_value(item) == key:
                return item
        raise ModelError(key)

    def _ipython_key_completions_(self) -> list[str]:
        if not type(self)._supports_lookup():
            return []
        seen: dict[str, None] = {}
        for item in self._items:
            v = self._lookup_value(item)
            if v is not None and v not in seen:
                seen[v] = None
        return list(seen)


class _ModelSequence(_Sequence[MT]):
    """Sequence of FRED model objects. Carries an optional client for lazy
    relation resolution on items."""

    __slots__ = ("client",)

    def __init__(self, items: Iterable[MT], client: Optional[_ClientModel] = None) -> None:
        super().__init__(items)
        self.client: Optional[_ClientModel] = client

    def _clone(self, items: Iterable[MT]) -> Self:
        return type(self)(items, client=self.client)

    @classmethod
    def _parse_item(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> MT:
        factory = getattr(cls._element_cls, "_from_dict")
        return factory(data, client=client)

    @classmethod
    def to_object(
        cls, response: Dict[str, Any], client: Optional[_ClientModel] = None
    ) -> Self:
        raw = _require_list(response, cls._response_key)
        return cls(
            (cls._parse_item(item, client=client) for item in raw),
            client=client,
        )

    @classmethod
    async def to_object_async(
        cls, response: Dict[str, Any], client: Optional[_ClientModel] = None
    ) -> Self:
        return await asyncio.to_thread(cls.to_object, response, client)


class _DateBase(date):
    """Base for FRED date elements that *are* ``datetime.date`` subclasses.
    [body unchanged from your current version — copy verbatim]"""

    __slots__ = ()
    _response_key: ClassVar[str] = ""

    def _with_date(self, year: int, month: int, day: int) -> Self:
        return type(self)(year, month, day)

    def __add__(self, other: timedelta) -> Self:
        d = date(self.year, self.month, self.day) + other
        return self._with_date(d.year, d.month, d.day)

    @overload
    def __sub__(self, other: datetime) -> Never: ...
    @overload
    def __sub__(self, other: Self) -> timedelta: ...
    @overload
    def __sub__(self, other: timedelta) -> Self: ...
    def __sub__(self, other):
        if isinstance(other, timedelta):
            d = date(self.year, self.month, self.day) - other
            return self._with_date(d.year, d.month, d.day)
        return date(self.year, self.month, self.day) - other

    def __radd__(self, other: timedelta) -> Self:
        return self.__add__(other)

    def replace(
        self,
        year: Optional[SupportsIndex] = None,
        month: Optional[SupportsIndex] = None,
        day: Optional[SupportsIndex] = None,
    ) -> Self:
        return self._with_date(
            self.year if year is None else int(year),
            self.month if month is None else int(month),
            self.day if day is None else int(day),
        )

    @classmethod
    def _parse_value(cls, raw: Any) -> Self:
        raise NotImplementedError

    @classmethod
    def to_object(cls, response: Dict[str, Any]) -> Self:
        raw = _require_list(response, cls._response_key)
        if not raw:
            raise ModelError(f"No {cls._response_key!r} found in the response")
        return cls._parse_value(raw[0])

    @classmethod
    async def to_object_async(cls, response: Dict[str, Any]) -> Self:
        return await asyncio.to_thread(cls.to_object, response)


class _DateSequence(_Sequence[DT]):
    """Sequence of date-subclass elements. Hashable, since items are dates."""

    __slots__ = ()

    @classmethod
    def _parse_value(cls, raw: Any) -> DT:
        return getattr(cls._element_cls, "_parse_value")(raw)

    def __hash__(self) -> int:
        return hash((type(self).__name__, self._items))

    def __repr__(self) -> str:
        if not self._items:
            return f"{type(self).__name__}(n=0)"
        return (
            f"{type(self).__name__}(n={len(self._items)}, "
            f"{self._items[0].isoformat()} … {self._items[-1].isoformat()})"
        )

    def _repr_html_(self) -> str:
        if not self._items:
            return f"<b>{type(self).__name__}</b> — empty"
        return (
            f"<b>{type(self).__name__}</b> — {len(self._items)} items, "
            f"{self._items[0].isoformat()} → {self._items[-1].isoformat()}"
        )

    @classmethod
    def to_object(cls, response: Dict[str, Any]) -> Self:
        raw = _require_list(response, cls._response_key)
        return cls(cls._parse_value(item) for item in raw)

    @classmethod
    async def to_object_async(cls, response: Dict[str, Any]) -> Self:
        return await asyncio.to_thread(cls.to_object, response)