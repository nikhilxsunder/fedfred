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
from collections.abc import Sequence
from typing import Any, ClassVar, Dict, Iterable, Iterator, Optional, Self, Tuple, Union, overload
from .._core import _require_list
from ._clients import _ClientModel  # pragma: no cover

# TODO: Fix all docstrings post error design.

__all__ = ["_ModelSequence", "_ModelBase"]

@dataclass
class _ModelBase:
    """Base class for FRED model objects. This class is not meant to be instantiated directly, but provides common functionality for all FRED model classes, such as storing a reference to the client instance for lazy loading of related data when accessing attributes of the model objects. """

    client: Optional[_ClientModel] = field(default=None, repr=False, compare=False)


    _response_key: ClassVar[str]


    @classmethod
    def _from_dict(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> "_ModelBase":

        raise NotImplementedError

    @classmethod
    def to_object(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None) -> "_ModelBase":

        raw = _require_list(response, cls._response_key)

        if not raw:
            raise ModelError(f"No {cls._response_key} found in the response") # TODO: Define ModelError
        
        return cls._from_dict(raw[0], client=client)

    @classmethod
    async def to_object_async(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None) -> "_ModelBase":

        return await asyncio.to_thread(cls.to_object, response, client)

    def _require_client(self) -> "_ClientModel":

        if self.client is None:
            raise ModelError("Client not set for this instance.") # TODO: Define ModelError
        
        return self.client

class _ModelSequence(Sequence[_ModelBase]):
    """Immutable, notebook-friendly sequence of FRED model objects.
    
    This class is used for attributes of FRED model objects that return multiple related objects, such as the ``observations`` attribute 
    of a ``Series``. It provides list-like behavior (indexing, slicing, iteration) but is immutable and has a custom repr for better
    display in notebooks. The ``to_object`` and ``to_object_async`` class methods are used to create instances of this class from raw 
    FRED API response dictionaries, using the appropriate parser for the specific model type.

    Attributes:
        _items (Tuple[_ModelBase, ...]): The underlying tuple of model objects.
        client (Optional[Fred]): The Fred client instance used to fetch additional data for related objects, if necessary. This is stored to allow lazy loading of related data when accessing attributes of the model objects in the sequence.
    
    
    """

    __slots__ = ("_items", "client", "_response_key")
    """Since this class is designed to hold a sequence of model objects, it is likely that many instances of this class will be created, so using ``__slots__`` can help reduce memory usage. """

    _response_key: ClassVar[str]
    """The key in the raw FRED API response dictionary where the list of items for this model type can be found."""

    def __init__(self, items: Iterable[_ModelBase], client: Optional[_ClientModel] = None) -> None:

        self._items: Tuple[_ModelBase, ...] = tuple(items)
        self.client: Optional[_ClientModel] = client

    @classmethod
    def _parse_item(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> _ModelBase:

        raise NotImplementedError

    @overload
    def __getitem__(self, index: int) -> _ModelBase: ...
    @overload
    def __getitem__(self, index: slice) -> Self: ...
    def __getitem__(self, index: Union[int, slice]) -> Union[_ModelBase, Self]:

        if isinstance(index, slice):
            return type(self)(self._items[index], client=self.client)
        return self._items[index]

    def __len__(self) -> int:

        return len(self._items)

    def __iter__(self) -> Iterator[_ModelBase]:

        return iter(self._items)

    def __contains__(self, value: object) -> bool:

        return value in self._items

    def __reversed__(self) -> Iterator[_ModelBase]:

        return reversed(self._items)

    def __eq__(self, other: object) -> bool:

        if isinstance(other, type(self)):
            return self._items == other._items
        return NotImplemented
    # __eq__ defined => __hash__ is None => unhashable (mirrors list; non-frozen dataclass elements are unhashable)

    def __repr__(self) -> str:

        return f"{type(self).__name__}(n={len(self._items)})"

    def _repr_html_(self) -> str:

        return f"<b>{type(self).__name__}</b> — {len(self._items)} items"

    @classmethod
    def to_object(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None) -> Self:

        raw = _require_list(response, cls._response_key)
        return cls((cls._parse_item(item, client=client) for item in raw), client=client)

    @classmethod
    async def to_object_async(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None) -> Self:

        return await asyncio.to_thread(cls.to_object, response, client=client)
