# filepath: /src/fedfred/_internals/_models.py
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
"""Internal scaffolding for the fedfred response model hierarchy.

This module defines the abstract bases that the public model classes in
:mod:`fedfred.models.fred` and :mod:`fedfred.models.alfred` inherit from.
The hierarchy is three layers deep::

    _Sequence[T]                            — generic sequence mechanics
    ├── _ModelSequence[MT: _ModelBase]      — adds client, _parse_item, payload _from_response
    └── _DateSequence[DT: _DateBase]        — adds date-aware repr, hashability, parse delegation

And two parallel singleton bases::

    _ModelBase                              — dataclass response objects with optional client
    _DateBase                               — datetime.date subclass for FRED date elements

:class:`_Sequence` carries the shared mechanics every response container needs:
positional indexing, slicing (delegated through :meth:`_Sequence._clone` so
subclasses preserve sidecar state), string-key lookup via ``_lookup_key`` or a
:meth:`_Sequence._lookup_value` override, IPython tab completion, equality
against same-typed siblings, and the Jupyter rich-display support via
:meth:`_Sequence._repr_html_`. Payload parsing, ``_from_response`` shape, and
sidecar fields (``client`` on :class:`_ModelSequence`, future ``series_id``
on tabular subclasses) live in the specialized layers below.

Classes:
    _ModelBase: Base for dataclass-style FRED response objects.
    _Sequence: Generic immutable sequence base.
    _ModelSequence: Sequence specialization carrying a client reference.
    _DateBase: ``datetime.date`` subclass base for FRED date elements.
    _DateSequence: Sequence specialization for date-subclass elements.

Notes:
    All classes in this module are private internals. The names are exported
    only so that the public model modules can subclass them; downstream users
    should depend on the concrete model classes (``Category``, ``Series``,
    etc.) and on the public ``fedfred`` package surface.

See Also:
    - :mod:`fedfred.models.fred`: Concrete FRED response classes.
    - :mod:`fedfred.models.alfred`: Concrete ALFRED response classes.
    - :mod:`fedfred._internals._clients`: The ``_ClientModel`` typing
      contract referenced by :class:`_ModelBase` and :class:`_ModelSequence`.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import (
    Any,
    ClassVar,
    Never,
    Self,
    SupportsIndex,
    TypeVar,
    cast,
    overload,
)

from .._core import _extract_objects, _ResponseShape
from ._clients import _ClientModel

# TODO: Fix all docstrings post error design.

__all__ = [
    "_DateBase",
    "_DateSequence",
    "_ModelBase",
    "_ModelSequence",
]

type JSON = (
    str | int | float | bool | None | Mapping[str, JSON] | Sequence[JSON] # TODO: Consider refactoring to core types module and reusing across the package.
)

@dataclass(slots=True, kw_only=True)
class _ModelBase:
    """Base for FRED response model objects.

    Provides common parsing entry points and an optional ``client`` reference
    that concrete subclasses use to lazily resolve related resources from
    their property accessors. Marked ``kw_only=True`` so that subclasses
    composing fields ahead of ``client`` (the universal trailing field) do
    not need to reorder.

    Attributes:
        client (_ClientModel, optional): The FRED client instance attached
            to this object for lazy relation traversal. Excluded from
            ``repr`` and from dataclass equality.
        _response_key (ClassVar[str]): Subclass-declared key under which
            FRED returns the list of objects of this type in a response
            payload (e.g., ``"categories"``, ``"seriess"``).

    Notes:
        Direct construction is supported for tests and manual round-trips;
        property accessors that depend on a client will raise
        :class:`ModelError` if invoked without one attached.

    See Also:
        - :class:`_ModelSequence`: The plural-container counterpart.
        - :class:`_DateBase`: The date-flavored singleton base.
    """

    client: _ClientModel | None = field(default=None, repr=False, compare=False)
    """The FRED client instance attached to this object, or ``None`` if unattached. Excluded from ``repr`` and dataclass equality."""

    _response_keys: ClassVar[tuple[str, ...]]
    """Payload key(s) under which FRED returns the list of objects of this type; tried in order."""

    _response_shape: ClassVar[_ResponseShape] = "list"
    """Response container shape: ``"list"`` for a plain list, ``"dict_or_list"`` for id-keyed-dict element payloads."""

    # Class Methods
    @classmethod
    def _from_dict(
        cls,
        data: dict[str, Any],
        client: _ClientModel | None = None
    ) -> Self:
        """Build a single instance from one raw FRED payload mapping.

        Subclass hook. Implementations validate required fields, normalize
        FRED's inconsistent key shapes (e.g., ``id`` vs ``series_id``), and
        thread the optional ``client`` into the constructed instance.

        Args:
            data (dict[str, Any]): The raw object payload from the FRED API.
            client (_ClientModel, optional): The FRED client to attach to the resulting instance for lazy relation traversal. Defaults to ``None``.

        Returns:
            Self: A fully populated subclass instance.

        Raises:
            NotImplementedError: If invoked on :class:`_ModelBase` directly rather than an implementing subclass.
        """
        raise NotImplementedError

    @classmethod
    def _from_response(
        cls,
        response: dict[str, Any],
        client: _ClientModel | None = None
    ) -> Self:
        """Build a single instance from a full FRED API response payload.

        Extracts the object list per the subclass-declared
        ``_response_keys`` / ``_response_shape``, validates it is non-empty,
        and dispatches the first entry through :meth:`_from_dict`.

        Args:
            response (dict[str, Any]): The raw FRED API response payload.
            client (_ClientModel, optional): The FRED client to attach to the resulting instance. Defaults to ``None``.

        Returns:
            Self: A single subclass instance built from the first payload entry.

        Raises:
            ModelError: If the resolved list is empty.
            ParsingError: If the response lacks the expected key or shape.
        """
        raw = _extract_objects(response, cls._response_keys, cls._response_shape)

        if not raw:
            raise ModelError(f"No {cls._response_keys[0]} found in the response")  # TODO: ModelError

        return cls._from_dict(raw[0], client=client)

    # Protected Methods
    def _require_client(self) -> _ClientModel:
        """Return the attached client, raising if none is present.

        Used by subclass property accessors that need to issue follow-up
        API calls (e.g., ``Category.children``) so that the missing-client
        error is raised at the point of attempted use rather than at
        construction.

        Returns:
            _ClientModel: The attached FRED client instance.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        if self.client is None:
            raise ModelError("Client not set for this instance.")  # TODO: ModelError

        return self.client


class _DateBase(date):
    """Base for FRED date elements that *are* :class:`datetime.date` subclasses.

    Subclasses pass ``isinstance(date)``, drop cleanly into any API that
    expects a date (comparisons, ``strftime``, pandas indexes, fedfred's
    own date parameters), and render their ISO string in Jupyter rather
    than the verbose ``datetime.date(YYYY, M, D)`` repr. Two flavours of
    subclass are supported:

    - **Pure date elements** (e.g. :class:`fedfred.VintageDate`): no
      metadata, trivial subclass with an overridden :meth:`_parse_value`.
    - **Metadata-bearing elements** (e.g. :class:`fedfred.ReleaseDate`):
      attach kw-only metadata via slot attributes, use a ``create``
      factory routed through ``date.__new__``, and override
      :meth:`_with_date` to preserve metadata through arithmetic and
      :meth:`replace`.

    Arithmetic operators (:meth:`__add__`, :meth:`__sub__`,
    :meth:`__radd__`) route through :meth:`_with_date` so subclasses can
    preserve metadata on the returned instance. This avoids two CPython
    footguns: silent metadata stripping under positional ``date(year,
    month, day)`` reconstruction, and ``TypeError`` from kw-only
    ``__new__`` signatures when CPython's date arithmetic tries
    ``type(self)(year, month, day)`` directly. Subtraction of two dates
    still returns a plain :class:`datetime.timedelta` per the
    :class:`datetime.date` contract.

    Attributes:
        _response_key (ClassVar[str]): Subclass-declared key under which FRED returns the list of objects of this type.

    See Also:
        - :class:`_DateSequence`: The plural-container counterpart.
        - :class:`fedfred.VintageDate`: A pure-date concrete subclass.
        - :class:`fedfred.ReleaseDate`: A metadata-bearing concrete subclass.
    """

    __slots__ = ()

    _response_keys: ClassVar[tuple[str, ...]] = ()
    """Payload key(s) under which FRED returns the list of objects of this type; tried in order."""

    _response_shape: ClassVar[_ResponseShape] = "list"
    """Response container shape: ``"list"`` for a plain list, ``"dict_or_list"`` for id-keyed-dict element payloads."""

    # Class Methods
    @classmethod
    def _parse_value(
        cls,
        raw: JSON
    ) -> Self:
        """Build one element from its raw payload.

        Subclass hook. Implementations decide whether ``raw`` is a string
        (ISO date) or a dict (date plus metadata) and validate accordingly.

        Args:
            raw (Any): The raw element payload from the FRED API.

        Returns:
            Self: A fully populated subclass instance.

        Raises:
            NotImplementedError: If invoked on :class:`_DateBase` directly
                rather than an implementing subclass.
        """
        raise NotImplementedError

    @classmethod
    def _from_response(
        cls,
        response: dict[str, Any]
    ) -> Self:
        """Build a single instance from a full FRED API response payload.

        Extracts the object list per ``_response_keys`` / ``_response_shape``,
        validates it is non-empty, and dispatches the first entry through
        :meth:`_parse_value`.

        Args:
            response (dict[str, Any]): The raw FRED API response payload.

        Returns:
            Self: A single subclass instance built from the first payload entry.

        Raises:
            ModelError: If the resolved list is empty.
            ParsingError: If the response lacks the expected key or shape.
        """
        raw = _extract_objects(response, cls._response_keys, cls._response_shape)

        if not raw:
            raise ModelError(f"No {cls._response_keys[0]!r} found in the response")

        return cls._parse_value(raw[0])

    # Dunder Methods
    def __add__(
        self,
        other: timedelta
    ) -> Self:
        """Add a :class:`timedelta` and return a new instance via :meth:`_with_date`.

        Routes through :meth:`_with_date` so subclass-specific metadata is
        preserved on the resulting instance.

        Args:
            other (timedelta): The duration to add.

        Returns:
            Self: A new instance offset by ``other``.
        """
        d = date(self.year, self.month, self.day) + other

        return self._with_date(d.year, d.month, d.day)

    @overload
    def __sub__(
        self,
        other: datetime
    ) -> Never: ...
    @overload
    def __sub__(
        self,
        other: Self
    ) -> timedelta: ...
    @overload
    def __sub__(
        self,
        other: timedelta
    ) -> Self: ...
    def __sub__(
        self,
        other: datetime | Self | timedelta
    ) -> Self | timedelta:
        """Subtract a :class:`timedelta` or another date.

        - ``other`` is :class:`timedelta` → return a new instance offset
          backward via :meth:`_with_date`, preserving subclass metadata.
        - ``other`` is :class:`date` (including this subclass) → return a
          plain :class:`timedelta` per the standard :class:`datetime.date`
          contract.

        Subtracting a :class:`datetime.datetime` is not supported and is
        statically marked :data:`Never`.

        Args:
            other (timedelta | date | datetime): The value to subtract.

        Returns:
            Self | timedelta: A new instance if ``other`` is a
            :class:`timedelta`; a :class:`timedelta` if ``other`` is a date.
        """
        if isinstance(other, timedelta):
            d = date(self.year, self.month, self.day) - other

            return self._with_date(d.year, d.month, d.day)

        return date(self.year, self.month, self.day) - other

    def __radd__(self, other: timedelta) -> Self:
        """Right-hand :class:`timedelta` addition (``timedelta + date``).

        Args:
            other (timedelta): The duration on the left of the ``+``.

        Returns:
            Self: A new instance offset by ``other``.
        """
        return self.__add__(other)

    # Protected Methods
    def _with_date(
        self,
        year: int,
        month: int,
        day: int
    ) -> Self:
        """Rebuild this instance at a new ``(year, month, day)`` preserving subclass state.

        Default implementation suits subclasses whose ``__new__`` accepts
        only ``(cls, year, month, day)`` (the pure-date case). Metadata-
        bearing subclasses override this method to thread their metadata
        through a ``create`` factory.

        Args:
            year (int): The new year.
            month (int): The new month, 1-12.
            day (int): The new day of the month, 1-31.

        Returns:
            Self: A new instance at the given date.
        """
        return type(self)(year, month, day)

    # Public Methods
    def replace(
        self,
        year: SupportsIndex | None = None,
        month: SupportsIndex | None = None,
        day: SupportsIndex | None = None,
    ) -> Self:
        """Return a new instance with selected date components replaced.

        Override of :meth:`datetime.date.replace` that routes through
        :meth:`_with_date` so subclass metadata is preserved.

        Args:
            year (SupportsIndex, optional): The new year, or ``None`` to keep the current value.
            month (SupportsIndex, optional): The new month, or ``None`` to keep the current value.
            day (SupportsIndex, optional): The new day, or ``None`` to keep the current value.

        Returns:
            Self: A new instance with the requested components replaced.
        """
        return self._with_date(
            self.year if year is None else int(year),
            self.month if month is None else int(month),
            self.day if day is None else int(day),
        )


# Type Variables
T = TypeVar("T")
"""Unbounded element type variable for the generic :class:`_Sequence` base."""

MT = TypeVar("MT", bound="_ModelBase")
"""Element type variable for :class:`_ModelSequence`, constrained to :class:`_ModelBase` subclasses."""

DT = TypeVar("DT", bound="_DateBase")
"""Element type variable for :class:`_DateSequence`, constrained to :class:`_DateBase` subclasses."""


class _Sequence(Sequence[T]):
    """Generic immutable sequence base for FRED response collections.

    Provides shared mechanics common to every response container in
    fedfred: positional indexing (``int``/``slice``), string-key lookup
    (``str`` keys dispatched through :meth:`_lookup_by_key`), iteration,
    length, containment, reversal, value equality against same-typed
    siblings, a developer ``repr``, the Jupyter rich-display sunder
    :meth:`_repr_html_`, and the IPython tab-completion sunder
    :meth:`_ipython_key_completions_`. Payload parsing, ``_from_response``
    construction, and sidecar state (``client`` on :class:`_ModelSequence`,
    future ``series_id`` on tabular siblings) live in the specialized
    subclasses.

    Slicing delegates through :meth:`_clone` so subclasses can forward
    sidecar state to the resulting sequence without reimplementing
    :meth:`__getitem__`. String-key lookup is enabled either by setting
    ``_lookup_key`` to an attribute name on items or by overriding
    :meth:`_lookup_value` for a computed key — :meth:`_supports_lookup`
    detects both pathways.

    Attributes:
        _items (Tuple[T, ...]): The underlying immutable tuple of elements.
        _response_key (ClassVar[str]): Auto-wired from the generic parameter on subclass definition; matches the FRED payload key for the element type.
        _element_cls (ClassVar[type]): Auto-wired element class, used by subclass ``_parse_*`` methods to delegate construction.
        _lookup_key (ClassVar[Optional[str]]): Attribute name on items used by the default :meth:`_lookup_value` implementation. Subclasses with computed keys (such as ISO-date strings) override :meth:`_lookup_value` instead.

    Notes:
        This class is private internals. Concrete sequences subclass either
        :class:`_ModelSequence` or :class:`_DateSequence` rather than
        :class:`_Sequence` directly. ``_lookup_key`` and
        :meth:`_lookup_value` together implement the lookup contract; see
        :meth:`_supports_lookup` for how the framework decides whether
        string indexing is enabled on a given subclass.

    See Also:
        - :class:`_ModelSequence`: Subclass for :class:`_ModelBase` elements.
        - :class:`_DateSequence`: Subclass for :class:`_DateBase` elements.
    """

    __slots__ = ("_items",)

    _response_keys: ClassVar[tuple[str, ...]] = ()
    """Auto-wired from the element class on subclass definition. Payload key(s) under which the element list is returned."""

    _response_shape: ClassVar[_ResponseShape] = "list"
    """Auto-wired from the element class. Response container shape for the element type."""

    _element_cls: ClassVar[type] = object
    """Auto-wired element class used by subclass ``_parse_*`` methods to delegate construction."""

    _lookup_key: ClassVar[str | None] = None
    """Attribute on items used by the default :meth:`_lookup_value` implementation. Subclasses with computed keys should override :meth:`_lookup_value` instead."""

    # Class Methods
    @classmethod
    def _supports_lookup(cls) -> bool:
        """Return whether string-key lookup is enabled on this subclass.

        Lookup is enabled if either ``_lookup_key`` is set to an attribute
        name or :meth:`_lookup_value` is overridden relative to the base
        implementation. The override check uses identity comparison on the
        unbound function objects, which works because Python resolves
        method descriptors lazily: a subclass that does not override gets
        the exact same function object from :class:`_Sequence`.

        Returns:
            bool: ``True`` if string indexing and IPython completion are enabled on this subclass.
        """
        return (
            cls._lookup_key is not None
            or cls._lookup_value is not _Sequence._lookup_value
        )

    @classmethod
    def _extract(cls, response: dict[str, Any]) -> list[Any]:
        """Extract the raw object list per this class's ``_response_keys`` / ``_response_shape``.

        Protected accessor so subclasses with custom constructors (e.g.
        :class:`fedfred.VintageDates`, which threads a ``series_id``) can reuse
        the declared extraction without importing the ``_core`` parsers
        directly.

        Args:
            response (dict[str, Any]): The raw FRED API response payload.

        Returns:
            list[Any]: The extracted object list.

        Raises:
            ParsingError: If the response lacks the expected key or shape.
        """
        return _extract_objects(response, cls._response_keys, cls._response_shape)

    # Dunder Methods
    def __init_subclass__(
        cls,
        **kwargs:object
    ) -> None:
        """Auto-wire ``_response_key`` and ``_element_cls`` from the generic parameter.

        Walks ``cls.__orig_bases__`` for any base whose ``__origin__`` is a
        :class:`_Sequence` subclass, extracts the type argument, and — when
        that argument is a concrete class rather than an unbound
        :class:`TypeVar` — populates ``_response_key`` and ``_element_cls``
        on ``cls`` unless they are already defined in ``cls.__dict__``.

        The :class:`isinstance(element_cls, type) <type>` guard is what
        prevents the intermediate :class:`_ModelSequence` and
        :class:`_DateSequence` definitions (parameterized by the TypeVars
        ``MT`` and ``DT``) from spuriously rewriting their own class vars.
        Concrete leaf classes like ``Categories(_ModelSequence[Category])``
        carry a concrete ``Category`` type argument, so the auto-wire fires.

        Args:
            **kwargs (Any): Forwarded to :meth:`type.__init_subclass__` for cooperative subclassing.
        """
        super().__init_subclass__(**kwargs)

        for base in getattr(cls, "__orig_bases__", ()):
            origin = getattr(base, "__origin__", None)

            if isinstance(origin, type) and issubclass(origin, _Sequence):
                args = getattr(base, "__args__", ())

                if args:
                    element_cls = args[0]

                    if isinstance(element_cls, type):

                        if "_response_keys" not in cls.__dict__:
                            keys = getattr(element_cls, "_response_keys", None)

                            if isinstance(keys, tuple):
                                cls._response_keys = keys

                        if "_response_shape" not in cls.__dict__:
                            shape = getattr(element_cls, "_response_shape", None)

                            if shape is not None:
                                cls._response_shape = shape

                        if "_element_cls" not in cls.__dict__:
                            cls._element_cls = element_cls
                break

    def __init__(
        self,
        items: Iterable[T]
    ) -> None:
        """Materialize ``items`` into the immutable backing tuple.

        Args:
            items (Iterable[T]): The elements to store. Consumed eagerly and frozen into a ``tuple`` so the sequence is immutable and hashable when the elements themselves are hashable.
        """
        self._items: tuple[T, ...] = tuple(items)

    @overload
    def __getitem__(
        self,
        index: int
    ) -> T: ...
    @overload
    def __getitem__(
        self,
        index: str
    ) -> T: ...
    @overload
    def __getitem__(
        self,
        index: slice
    ) -> Self: ...
    def __getitem__(
        self,
        index: int | str | slice
    ) -> T | Self:
        """Dispatch indexing on the runtime type of ``index``.

        - :class:`slice` → return a new sequence of the same concrete type
          via :meth:`_clone`, preserving sidecar state.
        - :class:`str` → delegate to :meth:`_lookup_by_key` for attribute-
          or computed-key lookup. Raises :class:`ModelError` if string
          lookup is not enabled on this subclass.
        - :class:`int` → standard positional indexing on the underlying
          tuple.

        Args:
            index (int | str | slice): The index. Integer for positional access, string for key-based lookup (when enabled), or slice for sub-sequence extraction.

        Returns:
            T | Self: A single element for integer or string indexing; a new sequence for slice indexing.

        Raises:
            IndexError: If ``index`` is an out-of-range integer.
            ModelError: If ``index`` is a string and the subclass does not enable string lookup, or if the key is not found.
        """
        if isinstance(index, slice):
            return self._clone(self._items[index])

        if isinstance(index, str):
            return self._lookup_by_key(index)

        return self._items[index]

    def __len__(self) -> int:
        """Return the number of elements in the sequence.

        Returns:
            int: The element count.
        """
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the elements in order.

        Returns:
            Iterator[T]: A standard tuple iterator.
        """
        return iter(self._items)

    def __contains__(
        self,
        value: object
    ) -> bool:
        """Return whether ``value`` equals any element by value.

        Membership is checked against item equality, not against the
        lookup-key value used by :meth:`__getitem__` with a string index.

        Args:
            value (object): The value to test for membership.

        Returns:
            bool: ``True`` if any element equals ``value``.
        """
        return value in self._items

    def __reversed__(self) -> Iterator[T]:
        """Return a reverse iterator over the elements.

        Returns:
            Iterator[T]: An iterator yielding elements in reverse order.
        """
        return reversed(self._items)

    def __eq__(
        self,
        other: object
    ) -> bool:
        """Compare for value equality against another instance of the same concrete type.

        Returns :data:`NotImplemented` rather than ``False`` for cross-type
        comparisons so Python can attempt the reflected operation on the
        other operand.

        Args:
            other (object): The value to compare against.

        Returns:
            bool: ``True`` if ``other`` is the same concrete type and holds equal items; ``False`` if the items differ; :data:`NotImplemented` if ``other`` is a different type.
        """
        if isinstance(other, type(self)):
            return self._items == other._items

        return NotImplemented

    def __repr__(self) -> str:
        """Return a compact developer representation.

        Returns:
            str: A string of the form ``"<ClassName>(n=<count>)"``. Subclasses with richer element semantics (such as :class:`_DateSequence`) override for additional context.
        """
        return f"{type(self).__name__}(n={len(self._items)})"

    # Sunder Methods
    def _repr_html_(self) -> str:
        """Render a one-line summary for Jupyter rich display.

        Default implementation produces a bold class name and item count;
        concrete sequences override this sunder to produce HTML tables of
        their elements.

        Returns:
            str: An HTML fragment safe to render inside a Jupyter notebook output cell.
        """
        return f"<b>{type(self).__name__}</b> — {len(self._items)} items"

    def _ipython_key_completions_(self) -> list[str]:
        """Return the deduplicated list of valid string keys for tab completion.

        IPython sunder that powers ``obj["<TAB>"]`` completion in
        Jupyter and the IPython REPL. Returns an empty list when the
        subclass does not enable string lookup; otherwise iterates the
        elements, collecting :meth:`_lookup_value` results in insertion
        order while skipping ``None`` and duplicates.

        Returns:
            list[str]: The valid string keys in first-seen order.
        """
        if not type(self)._supports_lookup():
            return []
        seen: dict[str, None] = {}
        for item in self._items:
            v = self._lookup_value(item)
            if v is not None and v not in seen:
                seen[v] = None
        return list(seen)

    # Protected Methods
    def _clone(
        self,
        items: Iterable[T]
    ) -> Self:
        """Construct a new instance of ``type(self)`` holding ``items``.

        Used by :meth:`__getitem__` to produce sliced copies. The default
        implementation suits subclasses whose ``__init__`` accepts only
        ``items``. Subclasses carrying sidecar state (the ``client`` on
        :class:`_ModelSequence`, ``series_id`` on
        :class:`fedfred.VintageDates`, etc.) override this method to
        forward that state to the new instance.

        Args:
            items (Iterable[T]): The elements for the new sequence.

        Returns:
            Self: A new sequence of the same concrete type.
        """
        return type(self)(items)

    def _lookup_value(
        self,
        item: T
    ) -> str | None:
        """Extract the string lookup key for an item, or ``None`` to exclude it.

        Override hook backing :meth:`_lookup_by_key` and
        :meth:`_ipython_key_completions_`. The default implementation reads
        the attribute named by ``_lookup_key`` and stringifies the result;
        subclasses with computed keys override this method to return a
        method-derived value (e.g., ``return item.isoformat()`` on
        :class:`_DateSequence` subclasses).

        Returning ``None`` excludes the item from both string-key lookup
        and from the IPython completion list — useful when the underlying
        attribute is itself optional and may be missing on some items.

        Args:
            item (T): The element to compute a key for.

        Returns:
            str | None: The string lookup key, or ``None`` to skip the item.
        """
        key = self._lookup_key

        if key is None:
            return None

        value = getattr(item, key, None)

        return None if value is None else str(value)

    def _lookup_by_key(
        self,
        key: str
    ) -> T:
        """Look up an item by its string key via :meth:`_lookup_value`.

        Linear scan over the elements, returning the first whose
        :meth:`_lookup_value` equals ``key``. Used by :meth:`__getitem__`
        when the index is a :class:`str`.

        Args:
            key (str): The lookup key to match.

        Returns:
            T: The first element whose :meth:`_lookup_value` equals ``key``.

        Raises:
            ModelError: If the subclass does not enable string lookup (per :meth:`_supports_lookup`), or if no item matches the given key.
        """
        if not type(self)._supports_lookup():
            raise ModelError(
                f"{type(self).__name__} does not support string indexing; "
                f"use positional indexing or iterate"
            )

        for item in self._items:
            if self._lookup_value(item) == key:
                return item

        raise ModelError(key)


class _ModelSequence(_Sequence[MT]):
    """Sequence specialization for :class:`_ModelBase` elements.

    Adds an optional ``client`` reference that is forwarded to elements at
    construction (so that each element can lazily resolve its own related
    resources) and propagated through slicing via the :meth:`_clone`
    override. Specializes :meth:`_from_response` tothread the client through
    payload parsing.

    Attributes:
        client (_ClientModel, optional): The FRED client instance attached
            to this sequence and forwarded to elements during construction.

    Notes:
        The ``client`` slot is independent of any client field on the
        contained elements — both are populated from the same source at
        :meth:`_from_response` time. Concrete sequences (``Categories``,
        ``Seriess``, etc.) subclass this via the parameterized form
        ``_ModelSequence[ConcreteModel]``, which triggers the
        :meth:`_Sequence.__init_subclass__` auto-wire of ``_response_key``
        and ``_element_cls``.

    See Also:
        - :class:`_Sequence`: The generic base.
        - :class:`_ModelBase`: The element base for this specialization.
    """

    __slots__ = ("client",)

    # Class Methods
    @classmethod
    def _parse_item(
        cls,
        data: dict[str, Any],
        client: _ClientModel | None = None
    ) -> MT:
        """Build a single element by delegating to its ``_from_dict`` classmethod.

        Resolves the element class through the auto-wired ``_element_cls``
        rather than referencing the concrete model directly, which keeps
        the parsing logic decoupled from the element module and avoids
        import cycles.

        Args:
            data (dict[str, Any]): The raw element payload from the FRED API.
            client (_ClientModel, optional): The FRED client to attach to the resulting element. Defaults to ``None``.

        Returns:
            MT: A single element instance built by the element class's ``_from_dict``.
        """
        return cast("type[MT]", cls._element_cls)._from_dict(data, client)

    @classmethod
    def _from_response(
        cls,
        response: dict[str, Any],
        client: _ClientModel | None = None
    ) -> Self:
        """Build a sequence from a FRED API response payload.

        Extracts the element list per the auto-wired ``_response_keys`` /
        ``_response_shape``, parses each entry through :meth:`_parse_item`, and
        threads the ``client`` through both the elements and the sequence.

        Args:
            response (dict[str, Any]): The raw FRED API response payload.
            client (_ClientModel, optional): The FRED client to propagate to elements and to the resulting sequence. Defaults to ``None``.

        Returns:
            Self: A sequence of elements.

        Raises:
            ParsingError: If the response lacks the expected key or shape.
        """
        raw = _extract_objects(response, cls._response_keys, cls._response_shape)

        return cls(
            (cls._parse_item(item, client=client) for item in raw),
            client=client,
        )

    # Dunder Methods
    def __init__(
        self,
        items: Iterable[MT],
        client: _ClientModel | None = None
    ) -> None:
        """Materialize ``items`` and attach an optional client.

        Args:
            items (Iterable[MT]): The elements to store.
            client (_ClientModel, optional): The FRED client to attach to this sequence. Forwarded to sliced copies by :meth:`_clone`. Defaults to ``None``.
        """
        super().__init__(items)
        self.client: _ClientModel | None = client

    # Protected Methods
    def _clone(
        self,
        items: Iterable[MT]
    ) -> Self:
        """Construct a new sequence of ``type(self)`` forwarding the client.

        Override of :meth:`_Sequence._clone` that preserves the
        ``client`` reference through slicing so sliced copies retain
        the ability to lazily resolve related resources.

        Args:
            items (Iterable[MT]): The elements for the new sequence.

        Returns:
            Self: A new sequence of the same concrete type holding
            ``items`` and the current ``client``.
        """
        return type(self)(items, client=self.client)


class _DateSequence(_Sequence[DT]):
    """Sequence specialization for :class:`_DateBase` elements.

    Hashable (since :class:`datetime.date` instances are hashable),
    parameterized by a :class:`_DateBase` subclass, and rendered with
    date-range context in both :meth:`__repr__` and the Jupyter rich-
    display sunder :meth:`_repr_html_`. Delegates payload parsing to the
    element class's ``_parse_value`` classmethod via :meth:`_parse_value`.

    The auto-wire on :class:`_Sequence.__init_subclass__` skips the
    intermediate :class:`_DateSequence` definition (parameterized by the
    ``DT`` TypeVar) and fires only on concrete leaf subclasses like
    ``ReleaseDates(_DateSequence[ReleaseDate])``.

    Notes:
        Unlike :class:`_ModelSequence`, :class:`_DateSequence` does not
        carry a ``client`` field — date elements are self-contained and
        do not require lazy relation resolution. Subclasses that need
        sidecar state (such as :class:`fedfred.VintageDates` carrying a
        ``series_id``) override ``__init__`` and :meth:`_Sequence._clone`
        to thread that state through.

    See Also:
        - :class:`_Sequence`: The generic base.
        - :class:`_DateBase`: The element base for this specialization.
    """

    __slots__ = ()

    # Class Methods
    @classmethod
    def _parse_value(cls, raw: dict[str, Any]) -> DT:
        """Build a single element by delegating to the element class's ``_parse_value``.

        Resolves the element class through the auto-wired ``_element_cls``
        rather than referencing the concrete model directly, which keeps
        the parsing logic decoupled from the element module.

        Args:
            raw (Any): The raw element payload from the FRED API.

        Returns:
            DT: A single element instance built by the element class's ``_parse_value``.
        """
        return cast("type[DT]", cls._element_cls)._parse_value(raw)

    @classmethod
    def _from_response(cls, response: dict[str, Any]) -> Self:
        """Build a sequence from a FRED API response payload.

        Extracts the element list per ``_response_keys`` / ``_response_shape``
        and parses each entry through :meth:`_parse_value`.

        Args:
            response (dict[str, Any]): The raw FRED API response payload.

        Returns:
            Self: A sequence of elements.

        Raises:
            ParsingError: If the response lacks the expected key or shape.
        """
        raw = _extract_objects(response, cls._response_keys, cls._response_shape)

        return cls(cls._parse_value(item) for item in raw)

    # Dunder Methods
    def __hash__(self) -> int:
        """Return a hash incorporating the concrete type name and elements.

        Including ``type(self).__name__`` ensures that two sequences with
        identical elements but different concrete types (a hypothetical
        ``ReleaseDates`` and ``VintageDates`` both wrapping the same dates)
        do not collide.

        Returns:
            int: A stable hash for the sequence.
        """
        return hash((type(self).__name__, self._items))

    def __repr__(self) -> str:
        """Return a date-range developer representation.

        Override of :meth:`_Sequence.__repr__` that includes the ISO range
        of the first and last elements when the sequence is non-empty.

        Returns:
            str: A string of the form ``"<ClassName>(n=<count>, <first>
            … <last>)"`` when non-empty, or ``"<ClassName>(n=0)"`` when
            empty.
        """
        if not self._items:
            return f"{type(self).__name__}(n=0)"

        return (
            f"{type(self).__name__}(n={len(self._items)}, "
            f"{self._items[0].isoformat()} … {self._items[-1].isoformat()})"
        )

    def _repr_html_(self) -> str:
        """Render a date-range one-liner for Jupyter rich display.

        Override of :meth:`_Sequence._repr_html_` that includes the ISO
        range of the first and last elements when the sequence is non-
        empty.

        Returns:
            str: An HTML fragment summarizing the date range and item count.
        """
        if not self._items:
            return f"<b>{type(self).__name__}</b> — empty"

        return (
            f"<b>{type(self).__name__}</b> — {len(self._items)} items, "
            f"{self._items[0].isoformat()} → {self._items[-1].isoformat()}"
        )
