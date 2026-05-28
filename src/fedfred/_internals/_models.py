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

This module provides internal helper classes for the fedfred package's return models.
"""

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import date, timedelta, datetime
from collections.abc import Sequence
from typing import Any, ClassVar, Dict, Iterable, Iterator, Optional, Self, Tuple, Union, overload, TypeVar, Never, SupportsIndex
from .._core import _require_list
from ._clients import _ClientModel  # pragma: no cover

# TODO: Fix all docstrings post error design.

__all__ = ["_ModelSequence", "_ModelBase"]

@dataclass(slots=True, kw_only=True)
class _ModelBase:
    """Base class for FRED model objects. This class is not meant to be instantiated directly, but provides common functionality for all FRED model classes, such as storing a reference to the client instance for lazy loading of related data when accessing attributes of the model objects. """

    client: Optional[_ClientModel] = field(default=None, repr=False, compare=False)


    _response_key: ClassVar[str]


    @classmethod
    def _from_dict(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> Self:

        raise NotImplementedError

    @classmethod
    def to_object(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None) -> Self:

        raw = _require_list(response, cls._response_key)

        if not raw:
            raise ModelError(f"No {cls._response_key} found in the response") # TODO: Define ModelError
        
        return cls._from_dict(raw[0], client=client)

    @classmethod
    async def to_object_async(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None) -> Self:

        return await asyncio.to_thread(cls.to_object, response, client)

    def _require_client(self) -> _ClientModel:

        if self.client is None:
            raise ModelError("Client not set for this instance.") # TODO: Define ModelError

        return self.client

T = TypeVar("T", bound="_ModelBase")

class _ModelSequence(Sequence[T]):
    """Immutable, notebook-friendly sequence of FRED model objects.
    
    This class is used for attributes of FRED model objects that return multiple related objects, such as the ``observations`` attribute 
    of a ``Series``. It provides list-like behavior (indexing, slicing, iteration) but is immutable and has a custom repr for better
    display in notebooks. The ``to_object`` and ``to_object_async`` class methods are used to create instances of this class from raw 
    FRED API response dictionaries, using the appropriate parser for the specific model type.

    Attributes:
        _items (Tuple[_ModelBase, ...]): The underlying tuple of model objects.
        client (Optional[Fred]): The Fred client instance used to fetch additional data for related objects, if necessary. This is stored to allow lazy loading of related data when accessing attributes of the model objects in the sequence.
    
    
    """

    __slots__ = ("_items", "client")
    """Since this class is designed to hold a sequence of model objects, it is likely that many instances of this class will be created, so using ``__slots__`` can help reduce memory usage. """

    _response_key: ClassVar[str] = ""
    """The key in the raw FRED API response dictionary where the list of items for this model type can be found."""

    _element_cls: ClassVar[type] = object


    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Auto-wire ``_response_key`` and ``_element_cls`` from ``Generic[T]``.

        For ``class Categories(_ModelSequence[Category])``, sets
        ``Categories._response_key = Category._response_key`` and
        ``Categories._element_cls = Category``. Each is skipped if the
        subclass set it explicitly in its body, so manual overrides win.
        Intermediate subclasses without a generic parameter
        (``class _Mid(_ModelSequence): ...``) are a no-op.
        """
        super().__init_subclass__(**kwargs)
        for base in getattr(cls, "__orig_bases__", ()):
            if getattr(base, "__origin__", None) is _ModelSequence:
                args = getattr(base, "__args__", ())
                if args:
                    element_cls = args[0]
                    if "_response_key" not in cls.__dict__:
                        # getattr (not direct ._private access) keeps Pylint W0212 quiet
                        key = getattr(element_cls, "_response_key", None)
                        if isinstance(key, str):
                            cls._response_key = key
                    if "_element_cls" not in cls.__dict__:
                        cls._element_cls = element_cls
                break

    def __init__(self, items: Iterable[T], client: Optional[_ClientModel] = None) -> None:

        self._items: Tuple[T, ...] = tuple(items)
        self.client: Optional[_ClientModel] = client

    @classmethod
    def _parse_item(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> T:

        factory = getattr(cls._element_cls, "_from_dict")  # getattr quiets Pylint W0212
        return factory(data, client=client)

    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> Self: ...
    def __getitem__(self, index: Union[int, slice]) -> Union[T, Self]:
        if isinstance(index, slice):
            return type(self)(self._items[index], client=self.client)
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


    @classmethod
    def to_object(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None, ) -> Self:

        raw = _require_list(response, cls._response_key)

        return cls((cls._parse_item(item, client=client) for item in raw), client=client)

    @classmethod
    async def to_object_async(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None) -> Self:

        return await asyncio.to_thread(cls.to_object, response, client=client)

class _DateBase(date):
    """Base for FRED date elements that *are* ``datetime.date`` subclasses.

    Subclasses pass ``isinstance(date)``, drop into any API expecting a date,
    and render their ISO string in notebooks. Two flavours:

    * Pure date elements (e.g. ``VintageDate``) — no metadata, trivial subclass.
    * Metadata-bearing elements (e.g. ``ReleaseDate``) — override ``__new__``
      to attach kw-only metadata to ``__slots__``.

    Arithmetic returns a plain ``datetime.date`` (loses the subclass and any
    metadata) to avoid two footguns: silent metadata stripping under positional
    args, and ``TypeError`` from kw-only ``__new__`` signatures when CPython's
    arithmetic tries ``type(self)(year, month, day)``. If you need to walk a
    date forward, do it on the underlying date and rebuild the metadata record
    explicitly.
    """

    __slots__ = ()
    _response_key: ClassVar[str] = ""

    def _with_date(self, year: int, month: int, day: int) -> Self:
        """Rebuild ``self`` at a new (year, month, day), preserving any
        subclass-specific state. Default implementation works for subclasses
        whose ``__new__`` accepts only ``(cls, year, month, day)``."""
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

    def replace(self, year: Optional[SupportsIndex] = None, month: Optional[SupportsIndex] = None, day: Optional[SupportsIndex] = None) -> Self:

        return self._with_date(
            self.year if year is None else int(year),
            self.month if month is None else int(month),
            self.day if day is None else int(day),
        )

    @classmethod
    def _parse_value(cls, raw: Any) -> Self:
        """Build one element from its raw payload.

        Subclass hook. Implementations decide whether ``raw`` is a string
        (ISO date) or a dict (date plus metadata).
        """

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

K = TypeVar("K", bound=_DateBase)

class _DateSequence(Sequence[K]):
    """Generic sequence of date-subclass elements. Hashable, since its
    elements are hashable (dates are). ``_response_key`` and ``_element_cls``
    auto-wire from the ``Generic[K]`` parameter."""

    __slots__ = ("_items",)
    _response_key: ClassVar[str] = ""
    _element_cls: ClassVar[type] = object

    def __init_subclass__(cls, **kwargs: Any) -> None:

        super().__init_subclass__(**kwargs)
        for base in getattr(cls, "__orig_bases__", ()):
            if getattr(base, "__origin__", None) is _DateSequence:
                args = getattr(base, "__args__", ())
                if args:
                    element_cls = args[0]
                    if "_response_key" not in cls.__dict__:
                        key = getattr(element_cls, "_response_key", None)
                        if isinstance(key, str):
                            cls._response_key = key
                    if "_element_cls" not in cls.__dict__:
                        cls._element_cls = element_cls
                break

    def __init__(self, items: Iterable[K]) -> None:

        self._items: Tuple[K, ...] = tuple(items)

    @classmethod
    def _parse_value(cls, raw: Any) -> K:

        return getattr(cls._element_cls, "_parse_value")(raw)

    @overload
    def __getitem__(self, index: int) -> K: ...
    @overload
    def __getitem__(self, index: slice) -> Self: ...
    def __getitem__(self, index: Union[int, slice]) -> Union[K, Self]:
        if isinstance(index, slice):
            return type(self)(self._items[index])
        return self._items[index]

    def __len__(self) -> int:

        return len(self._items)
    def __iter__(self) -> Iterator[K]: 

        return iter(self._items)
    def __contains__(self, value: object) -> bool: 

        return value in self._items
    def __reversed__(self) -> Iterator[K]:

        return reversed(self._items)

    def __eq__(self, other: object) -> bool:

        if isinstance(other, type(self)):
            return self._items == other._items
        return NotImplemented

    def __hash__(self) -> int:

        return hash((type(self).__name__, self._items))

    def __repr__(self) -> str:
        if not self._items:
            return f"{type(self).__name__}(n=0)"
        return (f"{type(self).__name__}(n={len(self._items)}, "
                f"{self._items[0].isoformat()} … {self._items[-1].isoformat()})")

    def _repr_html_(self) -> str:

        if not self._items:
            return f"<b>{type(self).__name__}</b> — empty"
        return (f"<b>{type(self).__name__}</b> — {len(self._items)} items, "
                f"{self._items[0].isoformat()} → {self._items[-1].isoformat()}")

    @classmethod
    def to_object(cls, response: Dict[str, Any]) -> Self:

        raw = _require_list(response, cls._response_key)
        return cls(cls._parse_value(item) for item in raw)

    @classmethod
    async def to_object_async(cls, response: Dict[str, Any]) -> Self:

        return await asyncio.to_thread(cls.to_object, response)
