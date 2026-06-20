# filepath: /src/fedfred/models/fred.py
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
"""This module defines the response object hierarchy for the FRED API.

The module exposes two flavors of model: singleton objects representing a single
FRED resource (``Category``, ``Series``, ``Tag``, ``Release``, ``ReleaseDate``,
``Source``, ``Element``) and immutable, notebook-friendly sequence containers
(``Categories``, ``Seriess``, ``Tags``, ``Releases``, ``ReleaseDates``,
``Sources``, ``Elements``) that wrap multiple results from a single API call.

Singletons are :class:`dataclasses.dataclass` subclasses of
:class:`fedfred._internals._models._ModelBase` (or, in the date-bearing case,
:class:`fedfred._internals._models._DateBase`) and carry an optional ``client``
reference enabling lazy traversal of related resources via property accessors.

Sequences are immutable :class:`collections.abc.Sequence` subclasses providing
positional indexing, slicing (which preserves the concrete subclass type),
string-key lookup against ``_lookup_key``, IPython tab completion, and a
Jupyter-friendly ``_repr_html_`` rendering. The ``client`` is propagated to
items at construction so that traversal continues to work on individual entries.

Classes:
    Category: A FRED Category resource.
    Categories: An immutable sequence of :class:`Category` objects.
    Series: A FRED Series resource.
    Seriess: An immutable sequence of :class:`Series` objects.
    Tag: A FRED Tag resource.
    Tags: An immutable sequence of :class:`Tag` objects.
    Release: A FRED Release resource.
    Releases: An immutable sequence of :class:`Release` objects.
    ReleaseDate: A FRED Release Date (date subclass carrying release metadata).
    ReleaseDates: An immutable sequence of :class:`ReleaseDate` objects.
    Source: A FRED Source resource.
    Sources: An immutable sequence of :class:`Source` objects.
    Element: A FRED Release Table Element.
    Elements: An immutable sequence of :class:`Element` objects.
    BulkRelease: A bulk-release observation aggregation (slated for rewrite in v4).

Examples:
    >>> import fedfred as fd
    >>> fred_client = fd.Fred('your_api_key')
    >>> category = fred_client.get_category(125)
    >>> print(category.name)
    'Trade Balance'

Notes:
    Every model object accepts an optional ``client`` keyword. When present,
    property accessors traverse related resources through that client (for
    example ``category.series`` invokes ``client.get_category_series(category.id)``).
    Constructing a model directly without a client is supported, but related-resource
    properties will raise on access.

See Also:
    - :class:`fedfred.Fred`: The synchronous FRED client.
    - :class:`fedfred.AsyncFred`: The asynchronous FRED client.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

import html
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Self,
    SupportsIndex,
    cast,
)

import numpy as np
import pandas as pd

from .._internals import (
    _cell_date,  # TODO: this is a re-export from _core._accessors, needs a refactor fix.
    _cell_value,  # TODO: this is a re-export from _core._accessors, needs a refactor fix.
    _ClientModel,
    _coerce_lower,  # TODO: this is a re-export from _core._converters needs a refactor fix.
    _DateBase,
    _DateSequence,
    _ModelBase,
    _ModelSequence,
    _ObservationBase,
    _ObservationSequence,
    _ResponseShape,
)
from .alfred import VintageDates, VintageSeries

if TYPE_CHECKING:
    import dask.dataframe as dd
    import polars as pl
    import torch

    from ..clients import Fred

# TODO: Fix all docstrings post error design.


@dataclass(slots=True)
class Category(_ModelBase):
    """A FRED Category.

    Represents a single category in the Federal Reserve Economic Data (FRED)
    hierarchy. Categories are organizational units used by the FRED API to
    group related time-series (e.g., "Prices", "National Accounts",
    "Monetary Aggregates"). Each category has a unique identifier, a
    human-readable name, and an optional parent category that defines its
    position within the tree.

    When a ``client`` is attached, the related-resource properties
    (:attr:`children`, :attr:`related`, :attr:`series`, :attr:`tags`,
    :attr:`related_tags`) lazily fetch their contents from the FRED API on
    access.

    Attributes:
        id (int): The unique identifier for the category.
        name (str): The human-readable name of the category.
        parent_id (int, optional): The unique identifier for the parent category, or ``None`` if the category is a root.
        client (Fred, optional): The Fred client instance associated with this Category. Required for related-resource access.
        children (Categories): Lazily fetched child categories.
        related (Categories): Lazily fetched related categories.
        series (Seriess): Lazily fetched series belonging to this category.
        tags (Tags): Lazily fetched tags associated with this category.
        related_tags (Tags): Lazily fetched related tags.

    Notes:
        This class is designed to work with the FRED API. Direct construction
        is supported (useful for tests), but related-resource properties
        require a ``client`` to be attached.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> category = fred_client.get_category(125)
        >>> print(category.name)
        'Trade Balance'
        >>> for child in category.children:
        >>>     print(child.name)
        'Exports'
        'Imports'

    See Also:
        - :class:`fedfred.Categories`: The plural sequence container.
        - :class:`fedfred.Tag`: For the object representation of a FRED tag.
        - :class:`fedfred.Series`: For the object representation of a FRED series.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Category.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/categories/
    """

    id: int
    """The unique identifier for the category. Corresponds to ``category_id`` in the FRED API."""

    name: str
    """The human-readable name of the category."""

    parent_id: int | None
    """The unique identifier for the parent category, if any. Can itself be used as a ``category_id`` in the FRED API to traverse the tree upward."""

    _response_keys: ClassVar[tuple[str, ...]] = ("categories",)
    """The key in the FRED API response payload that contains the category list."""

    # Class Methods
    @classmethod
    def _from_dict(cls, data: dict[str, Any], client: _ClientModel | None = None) -> Category:
        """Build a single :class:`Category` from one raw FRED payload mapping.

        Internal parser used by :meth:`_from_response` and by sequence containers
        when wiring up child items. Validates the presence of the required
        ``id`` and ``name`` fields and tolerates a missing ``parent_id``
        (root categories).

        Args:
            data (dict[str, Any]): The raw category payload from the FRED API.
            client (_ClientModel, optional): The FRED client to attach to the
                resulting object for lazy relation traversal. Defaults to ``None``.

        Returns:
            Category: A fully populated :class:`Category` instance.

        Raises:
            ModelError: If ``data`` is not a mapping or is missing the
                ``id`` or ``name`` fields.

        Examples:
            >>> import fedfred as fd
            >>> data = {"id": 125, "name": "Trade Balance", "parent_id": 13}
            >>> category = fd.Category._from_dict(data)
            >>> print(category.id, category.name, category.parent_id)
            125 'Trade Balance' 13

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Category.html
        """
        if not isinstance(data, dict):
            raise ModelError(
                "Invalid category payload: expected a mapping"
            )  # TODO: Define ModelError

        if "id" not in data or "name" not in data:
            raise ModelError(
                "Invalid category payload: missing 'id' or 'name'"
            )  # TODO: Define ModelError

        return cls(id=data["id"], name=data["name"], parent_id=data.get("parent_id"), client=client)

    # Properties
    @property
    def children(self) -> Categories:
        """The child categories of this category.

        Lazily resolves to ``client.get_category_children(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Categories: A sequence of child :class:`Category` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_category_children(self.id)

    @property
    def related(self) -> Categories:
        """The related categories of this category.

        Lazily resolves to ``client.get_category_related(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Categories: A sequence of related :class:`Category` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_category_related(self.id)

    @property
    def series(self) -> Seriess:
        """The series belonging to this category.

        Lazily resolves to ``client.get_category_series(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Seriess: A sequence of :class:`Series` objects in this category.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_category_series(self.id)

    @property
    def tags(self) -> Tags:
        """The tags associated with this category.

        Lazily resolves to ``client.get_category_tags(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Tags: A sequence of :class:`Tag` objects associated with this category.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_category_tags(self.id)

    @property
    def related_tags(self) -> Tags:
        """The related tags associated with this category.

        Lazily resolves to ``client.get_category_related_tags(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Tags: A sequence of related :class:`Tag` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_category_related_tags(self.id)


class Categories(_ModelSequence[Category]):
    """An immutable, notebook-friendly sequence of :class:`Category` objects.

    Behaves like a tuple of :class:`Category` (indexing, slicing, iteration,
    ``len``, ``==``, ``in``) but is also string-keyed by ``name`` for ergonomic
    lookup in notebooks (``categories["Trade Balance"]``) and supports
    IPython tab completion against the same key. Slicing returns a new
    :class:`Categories` carrying the same client.

    Renders a compact HTML table preview in Jupyter via :meth:`_repr_html_`,
    showing the first ten entries with id, name, and parent id.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> categories = fred_client.get_category_children(13)
        >>> categories[0].name
        'Exports'
        >>> categories["Imports"].id
        13
        >>> len(categories)
        4

    See Also:
        - :class:`fedfred.Category`: The element type.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Categories.html
    """

    __slots__ = ()

    _lookup_key: ClassVar[str | None] = "name"
    """Attribute used for string-key lookup and tab completion (``categories["<name>"]``)."""

    # Sunder Methods
    def _repr_html_(self) -> str:
        """Render a compact HTML table preview of the first ten categories.

        Returns:
            str: An HTML ``<table>`` with id, name, and parent_id columns and
            a truncation caption when the sequence exceeds ten entries.
        """
        head = self._items[:10]

        rows = "".join(
            f"<tr><td>{c.id}</td><td>{html.escape(c.name)}</td>"
            f"<td>{'' if c.parent_id is None else c.parent_id}</td></tr>"
            for c in head
        )

        caption = (
            "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"
        )

        return (
            "<table>"
            + caption
            + "<thead><tr><th>id</th><th>name</th><th>parent_id</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )


@dataclass(slots=True)
class Series(_ModelBase):
    """A FRED Series.

    Represents a single time series in the Federal Reserve Economic Data (FRED)
    database. A series is a time-ordered set of observations (an economic
    indicator, financial metric, or statistical measure) identified by a stable
    string ``id`` such as ``"UNRATE"`` or ``"GNPCA"``. Metadata accompanying
    the series describes its title, frequency, units, seasonal adjustment,
    observation range, and the date it was last updated by FRED.

    When a ``client`` is attached, the related-resource properties traverse the
    FRED API lazily: :attr:`categories`, :attr:`observations`, :attr:`release`,
    :attr:`tags`, and :attr:`vintagedates` each issue a single GET on access.

    Attributes:
        id (str): The unique identifier for the series.
        title (str): The human-readable title of the series.
        frequency (str): The long-form frequency description (e.g., ``"Monthly"``).
        units (str): The long-form units description (e.g., ``"Percent"``).
        seasonal_adjustment (str): The long-form seasonal-adjustment description (e.g., ``"Seasonally Adjusted"``).
        last_updated (str): The date when the series was last updated by FRED.
        observation_start (str, optional): The start date of available observations in ``YYYY-MM-DD`` format.
        observation_end (str, optional): The end date of available observations in ``YYYY-MM-DD`` format.
        copyright_id (str, optional): The copyright identifier for the series, if any.
        frequency_short (str, optional): The short-form frequency code (e.g., ``"m"``).
        units_short (str, optional): The short-form units code (e.g., ``"pc"``).
        seasonal_adjustment_short (str, optional): The short-form seasonal-adjustment code (e.g., ``"sa"``).
        popularity (int, optional): A FRED-assigned popularity score.
        realtime_start (str, optional): The start of the real-time period in ``YYYY-MM-DD`` format.
        realtime_end (str, optional): The end of the real-time period in ``YYYY-MM-DD`` format.
        group_popularity (int, optional): Popularity within a release group, if applicable.
        notes (str, optional): Free-form notes accompanying the series metadata.
        client (Fred, optional): The Fred client instance associated with this Series.
        categories (Categories): Lazily fetched categories the series belongs to.
        observations (pd.DataFrame | pl.DataFrame | dd.DataFrame): Lazily fetched observations DataFrame.
        release (Releases): Lazily fetched release(s) associated with this series.
        tags (Tags): Lazily fetched tags associated with this series.
        vintagedates (VintageDates): Lazily fetched ALFRED vintage dates for this series.

    Notes:
        Short-form codes (``frequency_short``, ``units_short``, ``seasonal_adjustment_short``) are coerced to lowercase at parse time by :meth:`_from_dict` to normalize FRED's inconsistent casing.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> series = fred_client.get_series("GNPCA")
        >>> print(series.title)
        'Real Gross National Product'
        >>> series.frequency, series.units_short
        ('Annual', 'bil. of chn. 2017 $')

    See Also:
        - :class:`fedfred.Seriess`: The plural sequence container.
        - :class:`fedfred.Category`: For the object representation of a FRED category.
        - :class:`fedfred.Release`: For the release this series belongs to.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Series.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/tags/series
    """

    id: str
    """The unique identifier for the series. Corresponds to ``series_id`` in the FRED API."""

    title: str
    """The human-readable title of the series."""

    frequency: str
    """The long-form frequency of the series (e.g., ``"Monthly"``, ``"Quarterly"``)."""

    units: str
    """The long-form units of measurement (e.g., ``"Percent"``, ``"Dollars"``)."""

    seasonal_adjustment: str
    """The long-form seasonal-adjustment type (e.g., ``"Seasonally Adjusted"``)."""

    last_updated: str
    """The date when the series was last updated by FRED."""

    observation_start: str | None = None
    """The start date of available observations in ``YYYY-MM-DD`` format. Corresponds to ``observation_start`` in the FRED API."""

    observation_end: str | None = None
    """The end date of available observations in ``YYYY-MM-DD`` format. Corresponds to ``observation_end`` in the FRED API."""

    copyright_id: str | None = None
    """The copyright identifier for the series, if any. ``None`` for non-copyrighted series."""

    frequency_short: str | None = None
    """The short-form frequency code (e.g., ``"m"``, ``"q"``), coerced to lowercase. Corresponds to ``frequency`` in the FRED API."""

    units_short: str | None = None
    """The short-form units code (e.g., ``"pc"``, ``"usd"``), coerced to lowercase. Corresponds to ``units`` in the FRED API."""

    seasonal_adjustment_short: str | None = None
    """The short-form seasonal-adjustment code (e.g., ``"sa"``), coerced to lowercase."""

    popularity: int | None = None
    """A FRED-assigned popularity score for the series."""

    realtime_start: str | None = None
    """The start of the real-time period in ``YYYY-MM-DD`` format. Corresponds to ``realtime_start`` in the FRED API."""

    realtime_end: str | None = None
    """The end of the real-time period in ``YYYY-MM-DD`` format. Corresponds to ``realtime_end`` in the FRED API."""

    group_popularity: int | None = None
    """A popularity score within a release group, if applicable."""

    notes: str | None = None
    """Free-form notes accompanying the series metadata."""

    _observations: pd.DataFrame | pl.DataFrame | dd.DataFrame | None = None
    """Reserved slot for the cached observations DataFrame (BulkRelease pipeline). Not part of the public surface."""

    _response_keys: ClassVar[tuple[str, ...]] = ("seriess", "series")
    """Payload key(s) under which FRED returns the series list. Both singular and plural keys are accepted to accommodate different endpoint shapes."""

    # Class Methods
    @classmethod
    def _from_dict(cls, data: dict[str, Any], client: _ClientModel | None = None) -> Series:
        """Build a single :class:`Series` from one raw FRED payload mapping.

        Internal parser used by :meth:`_from_response` and by sequence containers
        when wiring up child items. Accepts both ``id`` and ``series_id`` as
        the identifier key (FRED is inconsistent across endpoints), validates
        the presence of the long-form metadata fields, and routes the
        short-form codes through :func:`fedfred._core._coerce_lower` for
        case normalization.

        Args:
            data (dict[str, Any]): The raw series payload from the FRED API.
            client (_ClientModel, optional): The FRED client to attach to the resulting object for lazy relation traversal. Defaults to ``None``.

        Returns:
            Series: A fully populated :class:`Series` instance.

        Raises:
            ModelError: If ``data`` is not a mapping, lacks an identifier (``id`` or ``series_id``), or is missing any of the required long-form fields (``title``, ``frequency``, ``units``, ``seasonal_adjustment``, ``last_updated``).

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Series.html
        """
        if not isinstance(data, dict):
            raise ModelError("Invalid series payload: expected a mapping")

        sid = data.get("id") or data.get("series_id")

        if not sid:
            raise ModelError("Invalid series payload: missing 'id'/'series_id'")

        for required in ("title", "frequency", "units", "seasonal_adjustment", "last_updated"):
            if required not in data:
                raise ModelError(f"Invalid series payload: missing {required!r}")

        return cls(
            id=sid,
            title=data["title"],
            frequency=data["frequency"],
            units=data["units"],
            seasonal_adjustment=data["seasonal_adjustment"],
            last_updated=data["last_updated"],
            observation_start=data.get("observation_start"),
            observation_end=data.get("observation_end"),
            copyright_id=data.get("copyright_id"),
            frequency_short=_coerce_lower(data.get("frequency_short")),
            units_short=_coerce_lower(data.get("units_short")),
            seasonal_adjustment_short=_coerce_lower(data.get("seasonal_adjustment_short")),
            popularity=data.get("popularity"),
            realtime_start=data.get("realtime_start"),
            realtime_end=data.get("realtime_end"),
            group_popularity=data.get("group_popularity"),
            notes=data.get("notes"),
            client=client,
        )

    # Properties
    @property
    def categories(self) -> Categories:
        """The categories this series belongs to.

        Lazily resolves to ``client.get_series_categories(self.id)`` on access. Requires a ``client`` to be attached to this instance.

        Returns:
            Categories: A sequence of :class:`Category` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_series_categories(self.id)

    @property
    def observations(self) -> pd.DataFrame | pl.DataFrame | dd.DataFrame:
        """The DataFrame of observations for this series.

        Lazily resolves to ``client.get_series_observations(self.id)`` on access.
        The return type follows the client's configured dataframe backend
        (pandas, polars, or dask). Requires a ``client`` to be attached.

        Returns:
            pd.DataFrame | pl.DataFrame | dd.DataFrame: A DataFrame of
            observations indexed by date.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_series_observations(self.id)

    @property
    def release(self) -> Release:
        """The release this series belongs to.

        Lazily resolves to ``client.get_series_release(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Release: The :class:`Release` object.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_series_release(self.id)

    @property
    def tags(self) -> Tags:
        """The tags associated with this series.

        Lazily resolves to ``client.get_series_tags(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Tags: A sequence of :class:`Tag` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_series_tags(self.id)

    @property
    def vintagedates(self) -> VintageDates:
        """The ALFRED vintage dates for this series.

        Lazily resolves to ``client.get_series_vintagedates(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            VintageDates: A sequence of :class:`fedfred.VintageDate` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_series_vintagedates(self.id)


class Seriess(_ModelSequence[Series]):
    """An immutable, notebook-friendly sequence of :class:`Series` objects.

    Behaves like a tuple of :class:`Series` (indexing, slicing, iteration,
    ``len``, ``==``, ``in``) and is string-keyed by ``id`` for ergonomic
    lookup in notebooks (``seriess["UNRATE"]``) with IPython tab completion
    against the same key. Slicing returns a new :class:`Seriess` carrying
    the same client.

    The container name reflects FRED's own (idiosyncratic) plural; the API
    returns the sequence under either ``"seriess"`` or ``"series"`` depending
    on the endpoint, both of which are handled by :meth:`_from_response`.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> seriess = fred_client.get_category_series(125)
        >>> seriess[0].id
        'BOPBCA'
        >>> seriess["BOPBCA"].title
        'Balance on Current Account'

    See Also:
        - :class:`fedfred.Series`: The element type.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Seriess.html
    """

    __slots__ = ()

    _lookup_key: ClassVar[str | None] = "id"
    """Attribute used for string-key lookup and tab completion (``seriess["<series_id>"]``)."""

    # Sunder Methods
    def _repr_html_(self) -> str:
        """Render a compact HTML table preview of the first ten series.

        Returns:
            str: An HTML ``<table>`` with id, title, frequency, and units columns and a truncation caption when the sequence exceeds ten entries.
        """
        head = self._items[:10]

        rows = "".join(
            f"<tr><td><code>{html.escape(s.id)}</code></td>"
            f"<td>{html.escape(s.title)}</td>"
            f"<td>{html.escape(s.frequency)}</td>"
            f"<td>{html.escape(s.units_short or s.units)}</td></tr>"
            for s in head
        )

        caption = (
            "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"
        )

        return (
            "<table>"
            + caption
            + "<thead><tr><th>id</th><th>title</th><th>frequency</th><th>units</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )


@dataclass(slots=True)
class Tag(_ModelBase):
    """A FRED Tag.

    Represents a single tag in the Federal Reserve Economic Data (FRED)
    database. Tags are keywords or labels (e.g., ``"nation"``, ``"usa"``,
    ``"frb"``) that can be associated with series to facilitate search,
    discovery, and categorization. Each tag carries a name, a group ID
    classifying its type (geography, source, frequency, etc.), a creation
    date, a FRED-assigned popularity score, and a count of how many series
    reference it.

    When a ``client`` is attached, the related-resource properties
    (:attr:`related_tags`, :attr:`series`) lazily fetch contents on access.

    Attributes:
        name (str): The tag name (used as the FRED API identifier).
        group_id (str): The group classification for the tag.
        created (str): The creation timestamp of the tag.
        popularity (int): The FRED-assigned popularity score.
        series_count (int): The number of series associated with this tag.
        notes (str, optional): Free-form notes accompanying the tag.
        client (Fred, optional): The Fred client instance associated with this Tag.
        related_tags (Tags): Lazily fetched related tags.
        series (Seriess): Lazily fetched series carrying this tag.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> tags = fred_client.get_tags()
        >>> for tag in tags[:3]:
        >>>     print(tag.name)
        'nation'
        'usa'
        'frb'

    See Also:
        - :class:`fedfred.Tags`: The plural sequence container.
        - :class:`fedfred.Series`: For the object representation of a FRED series.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Tag.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/tags/
    """

    name: str
    """The tag name. Corresponds to ``tag_name`` in the FRED API and serves as the lookup identifier."""

    group_id: str
    """The group classification for the tag (e.g., ``"geo"``, ``"src"``, ``"freq"``)."""

    created: str
    """The creation timestamp of the tag."""

    popularity: int
    """A FRED-assigned popularity score for the tag."""

    series_count: int
    """The number of series that reference this tag."""

    notes: str | None = None
    """Free-form notes accompanying the tag, if any."""

    _response_keys: ClassVar[tuple[str, ...]] = ("tags",)
    """The key in the FRED API response payload that contains the tag list."""

    # Class Methods
    @classmethod
    def _from_dict(cls, data: dict[str, Any], client: _ClientModel | None = None) -> Tag:
        """Build a single :class:`Tag` from one raw FRED payload mapping.

        Internal parser used by :meth:`_from_response` and by sequence containers.
        Validates the presence of every required field; tolerates a missing
        ``notes`` field.

        Args:
            data (dict[str, Any]): The raw tag payload from the FRED API.
            client (_ClientModel, optional): The FRED client to attach to the
                resulting object for lazy relation traversal. Defaults to ``None``.

        Returns:
            Tag: A fully populated :class:`Tag` instance.

        Raises:
            ModelError: If ``data`` is not a mapping or is missing any of the
                required fields (``name``, ``group_id``, ``created``,
                ``popularity``, ``series_count``).

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Tag.html
        """
        if not isinstance(data, dict):
            raise ModelError("Invalid tag payload: expected a mapping")

        for required in ("name", "group_id", "created", "popularity", "series_count"):
            if required not in data:
                raise ModelError(f"Invalid tag payload: missing {required!r}")

        return cls(
            name=data["name"],
            group_id=data["group_id"],
            created=data["created"],
            popularity=data["popularity"],
            series_count=data["series_count"],
            notes=data.get("notes"),
            client=client,
        )

    # Properties
    @property
    def related_tags(self) -> Tags:
        """The tags related to this tag.

        Lazily resolves to ``client.get_related_tags(self.name)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Tags: A sequence of related :class:`Tag` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_related_tags(self.name)

    @property
    def series(self) -> Seriess:
        """The series that carry this tag.

        Lazily resolves to ``client.get_tags_series(self.name)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Seriess: A sequence of :class:`Series` objects tagged with this tag.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_tags_series(self.name)


class Tags(_ModelSequence[Tag]):
    """An immutable, notebook-friendly sequence of :class:`Tag` objects.

    Behaves like a tuple of :class:`Tag` (indexing, slicing, iteration,
    ``len``, ``==``, ``in``) and is string-keyed by ``name`` for ergonomic
    lookup (``tags["nation"]``) with IPython tab completion. Slicing returns
    a new :class:`Tags` carrying the same client.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> tags = fred_client.get_tags()
        >>> tags["nation"].series_count
        128719

    See Also:
        - :class:`fedfred.Tag`: The element type.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Tags.html
    """

    __slots__ = ()

    _lookup_key: ClassVar[str | None] = "name"
    """Attribute used for string-key lookup and tab completion (``tags["<tag_name>"]``)."""

    # Sunder Methods
    def _repr_html_(self) -> str:
        """Render a compact HTML table preview of the first ten tags.

        Returns:
            str: An HTML ``<table>`` with name, group_id, popularity, and
            series_count columns and a truncation caption when the sequence
            exceeds ten entries.
        """
        head = self._items[:10]

        rows = "".join(
            f"<tr><td>{html.escape(t.name)}</td>"
            f"<td>{html.escape(t.group_id)}</td>"
            f"<td>{t.popularity}</td>"
            f"<td>{t.series_count}</td></tr>"
            for t in head
        )

        caption = (
            "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"
        )

        return (
            "<table>"
            + caption
            + "<thead><tr><th>name</th><th>group_id</th><th>popularity</th><th>series_count</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )


@dataclass(slots=True)
class Release(_ModelBase):
    """A FRED Release.

    Represents a single release in the Federal Reserve Economic Data (FRED)
    database. A release is a scheduled publication of economic data — for
    example, the Employment Situation, the Consumer Price Index, or quarterly
    GDP — that bundles together a set of related series and an associated
    publication calendar. Each release has a stable integer identifier, a
    human-readable name, an optional press-release flag, an optional
    documentation link, and an optional realtime period.

    When a ``client`` is attached, the related-resource properties traverse
    the FRED API lazily on access: :attr:`dates`, :attr:`series`,
    :attr:`sources`, :attr:`tags`, :attr:`related_tags`, and :attr:`tables`.

    Attributes:
        id (int): The unique identifier for the release.
        name (str): The human-readable name of the release.
        realtime_start (str, optional): The start of the real-time period in ``YYYY-MM-DD`` format.
        realtime_end (str, optional): The end of the real-time period in ``YYYY-MM-DD`` format.
        press_release (bool, optional): Whether the release is a press release.
        link (str, optional): A documentation URL for the release.
        notes (str, optional): Free-form notes accompanying the release.
        client (Fred, optional): The Fred client instance associated with this Release.
        dates (ReleaseDates): Lazily fetched calendar of publication dates.
        series (Seriess): Lazily fetched series in this release.
        sources (Sources): Lazily fetched data sources for this release.
        tags (Tags): Lazily fetched tags associated with this release.
        related_tags (Tags): Lazily fetched related tags.
        tables (Elements): Lazily fetched release-table elements.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> release = fred_client.get_release(82)
        >>> print(release.name)
        'Employment Situation'

    See Also:
        - :class:`fedfred.Releases`: The plural sequence container.
        - :class:`fedfred.ReleaseDate`: The calendar-entry type for a release.
        - :class:`fedfred.Source`: For the object representation of a FRED source.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Release.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/releases/
    """

    id: int
    """The unique identifier for the release. Corresponds to ``release_id`` in the FRED API."""

    name: str
    """The human-readable name of the release."""

    realtime_start: str | None = None
    """The start of the real-time period in ``YYYY-MM-DD`` format. Corresponds to ``realtime_start`` in the FRED API."""

    realtime_end: str | None = None
    """The end of the real-time period in ``YYYY-MM-DD`` format. Corresponds to ``realtime_end`` in the FRED API."""

    press_release: bool | None = None
    """Whether the release is a press release."""

    link: str | None = None
    """A documentation URL for the release. Tolerates ``"link"`` or ``"url"`` keys from the FRED payload."""

    notes: str | None = None
    """Free-form notes accompanying the release, if any."""

    _sources: Sources | None = None
    """Reserved slot for the cached sources (BulkRelease pipeline). Not part of the public surface."""

    _response_keys: ClassVar[tuple[str, ...]] = ("releases", "release")
    """Payload key(s) under which FRED returns the release list. Both singular and plural keys are accepted to accommodate different endpoint shapes."""

    # Class Methods
    @classmethod
    def _from_dict(cls, data: dict[str, Any], client: _ClientModel | None = None) -> Release:
        """Build a single :class:`Release` from one raw FRED payload mapping.

        Internal parser used by :meth:`_from_response` and by sequence containers.
        Accepts both ``id`` and ``release_id`` as the identifier key and both
        ``link`` and ``url`` as the documentation link, normalizing FRED's
        inconsistent payload shapes across endpoints.

        Args:
            data (dict[str, Any]): The raw release payload from the FRED API.
            client (_ClientModel, optional): The FRED client to attach to the resulting object for lazy relation traversal. Defaults to ``None``.

        Returns:
            Release: A fully populated :class:`Release` instance.

        Raises:
            ModelError: If ``data`` is not a mapping, lacks an identifier (``id`` or ``release_id``), or is missing the ``name`` field.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Release.html
        """
        if not isinstance(data, dict):
            raise ModelError("Invalid release payload: expected a mapping")

        rid = data.get("id") or data.get("release_id")

        if rid is None:
            raise ModelError("Invalid release payload: missing 'id'/'release_id'")

        if "name" not in data:
            raise ModelError("Invalid release payload: missing 'name'")

        return cls(
            id=rid,
            name=data["name"],
            realtime_start=data.get("realtime_start"),
            realtime_end=data.get("realtime_end"),
            press_release=data.get("press_release"),
            link=data.get("link") or data.get("url"),
            notes=data.get("notes"),
            client=client,
        )

    # Properties
    @property
    def dates(self) -> ReleaseDates:
        """The publication-date calendar for this release.

        Lazily resolves to ``client.get_release_dates(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            ReleaseDates: A sequence of :class:`ReleaseDate` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_release_dates(self.id)

    @property
    def series(self) -> Seriess:
        """The series published under this release.

        Lazily resolves to ``client.get_release_series(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Seriess: A sequence of :class:`Series` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_release_series(self.id)

    @property
    def sources(self) -> Sources:
        """The data sources for this release.

        Lazily resolves to ``client.get_release_sources(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Sources: A sequence of :class:`Source` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_release_sources(self.id)

    @property
    def tags(self) -> Tags:
        """The tags associated with this release.

        Lazily resolves to ``client.get_release_tags(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Tags: A sequence of :class:`Tag` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_release_tags(self.id)

    @property
    def related_tags(self) -> Tags:
        """The tags related to those on this release.

        Lazily resolves to ``client.get_release_related_tags(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Tags: A sequence of related :class:`Tag` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_release_related_tags(self.id)

    @property
    def tables(self) -> Elements:
        """The release-table elements for this release.

        Lazily resolves to ``client.get_release_tables(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Elements: A sequence of :class:`Element` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_release_tables(self.id)


class Releases(_ModelSequence[Release]):
    """An immutable, notebook-friendly sequence of :class:`Release` objects.

    Behaves like a tuple of :class:`Release` (indexing, slicing, iteration,
    ``len``, ``==``, ``in``) and is string-keyed by ``name`` for ergonomic
    lookup (``releases["Employment Situation"]``) with IPython tab completion.
    Slicing returns a new :class:`Releases` carrying the same client.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> releases = fred_client.get_releases()
        >>> releases["Consumer Price Index"].id
        10

    See Also:
        - :class:`fedfred.Release`: The element type.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Releases.html
    """

    __slots__ = ()

    _lookup_key: ClassVar[str | None] = "name"
    """Attribute used for string-key lookup and tab completion (``releases["<release_name>"]``)."""

    # Sunder Methods
    def _repr_html_(self) -> str:
        """Render a compact HTML table preview of the first ten releases.

        Returns:
            str: An HTML ``<table>`` with id, name, and press_release columns
            and a truncation caption when the sequence exceeds ten entries.
        """
        head = self._items[:10]

        rows = "".join(
            f"<tr><td>{r.id}</td><td>{html.escape(r.name)}</td>"
            f"<td>{'yes' if r.press_release else ''}</td></tr>"
            for r in head
        )

        caption = (
            "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"
        )

        return (
            "<table>"
            + caption
            + "<thead><tr><th>id</th><th>name</th><th>press_release</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )


class ReleaseDate(_DateBase):
    """A FRED Release Date.

    Represents a single publication date for a FRED release. ``ReleaseDate``
    *is a* :class:`datetime.date` (subclass), so it drops cleanly into any API
    expecting a date (comparisons, ``strftime``, pandas indexes, fedfred's own
    date parameters) while carrying additional release metadata as slot
    attributes.

    Construction goes through the :meth:`create` factory, which uses
    ``date.__new__`` to satisfy CPython's immutable date initialization
    and then attaches the release metadata via ``setattr``. Direct calls to
    ``ReleaseDate(year, month, day)`` will succeed as a plain date but
    will not populate the release metadata; prefer :meth:`create`.

    Pickling is supported via :meth:`__reduce__`, which routes through
    :meth:`_rebuild` so that round-tripped instances preserve their
    release metadata.

    Attributes:
        release_id (int): The unique identifier for the release this date belongs to.
        release_name (str, optional): The human-readable name of the release.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> release_dates = fred_client.get_release_dates(82)
        >>> release_dates[-1]
        ReleaseDate(2024-12-06, release_id=82, release_name='Employment Situation')
        >>> release_dates[-1].isoformat()
        '2024-12-06'

    See Also:
        - :class:`fedfred.ReleaseDates`: The plural sequence container.
        - :class:`fedfred.Release`: The release this date belongs to.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.ReleaseDate.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/release_dates.html
    """

    __slots__ = ("release_id", "release_name")

    release_id: int
    """The unique identifier for the release this date belongs to. Corresponds to ``release_id`` in the FRED API."""

    release_name: str | None
    """The human-readable name of the release. Corresponds to ``release_name`` in the FRED API."""

    _response_keys: ClassVar[tuple[str, ...]] = ("release_dates",)
    """The key in the FRED API response payload that contains the release date list."""

    # Class Methods
    @classmethod
    def create(
        cls,
        year: SupportsIndex,
        month: SupportsIndex,
        day: SupportsIndex,
        *,
        release_id: int,
        release_name: str | None = None,
    ) -> Self:
        """Construct a :class:`ReleaseDate` with attached release metadata.

        This is the canonical construction path for :class:`ReleaseDate`.
        Uses ``date.__new__`` to bypass the immutable date initialization
        contract and then attaches the release metadata via ``setattr`` to
        populate the slot attributes.

        Args:
            year (SupportsIndex): The four-digit year.
            month (SupportsIndex): The month, 1-12.
            day (SupportsIndex): The day of the month, 1-31.
            release_id (int): The release identifier this date belongs to.
            release_name (str, optional): The human-readable name of the release.

        Returns:
            ReleaseDate: A fully populated :class:`ReleaseDate` instance.

        Examples:
            >>> rd = ReleaseDate.create(2024, 12, 6, release_id=82,
            ...                         release_name="Employment Situation")
            >>> rd.isoformat()
            '2024-12-06'
            >>> rd.release_id
            82
        """
        self: Self = date.__new__(cls, year, month, day)

        self.release_id = release_id

        self.release_name = release_name

        return self

    @classmethod
    def _rebuild(
        cls,
        year: SupportsIndex,
        month: SupportsIndex,
        day: SupportsIndex,
        release_id: int,
        release_name: str | None,
    ) -> Self:
        """Pickle/copy rebuild factory routed through :meth:`create`.

        Used by :meth:`__reduce__` so that unpickling and ``copy.deepcopy``
        re-enter the validated construction path and preserve the release
        metadata. Exposed as a classmethod (rather than a module-level
        helper) so that pickle can resolve it by qualified name without
        polluting the module namespace.

        Args:
            year (SupportsIndex): The four-digit year.
            month (SupportsIndex): The month, 1-12.
            day (SupportsIndex): The day of the month, 1-31.
            release_id (int): The release identifier.
            release_name (str | None): The release name, or ``None``.

        Returns:
            ReleaseDate: A reconstructed :class:`ReleaseDate` instance.
        """
        return cls.create(
            year,
            month,
            day,
            release_id=release_id,
            release_name=release_name,
        )

    @classmethod
    def _parse_value(cls, raw: object) -> ReleaseDate:
        """Build a single :class:`ReleaseDate` from one raw FRED payload mapping.

        Internal parser used by :class:`ReleaseDates`. Accepts an ISO date
        string or a :class:`datetime.date` instance under the ``date`` key.

        Args:
            raw (object): The raw release-date payload from the FRED API. Expected to be a mapping with ``release_id``, ``date``, and optional ``release_name`` keys.

        Returns:
            ReleaseDate: A fully populated :class:`ReleaseDate` instance.

        Raises:
            ModelError: If ``raw`` is not a mapping or is missing the ``release_id`` or ``date`` fields.
        """
        if not isinstance(raw, dict):
            raise ModelError("Invalid release_date payload: expected a mapping")

        if "release_id" not in raw or "date" not in raw:
            raise ModelError("Invalid release_date payload: missing 'release_id' or 'date'")

        d_raw = raw["date"]

        d = date.fromisoformat(d_raw) if isinstance(d_raw, str) else d_raw

        return cls.create(
            d.year,
            d.month,
            d.day,
            release_id=raw["release_id"],
            release_name=raw.get("release_name"),
        )

    # Dunder Methods
    def __repr__(self) -> str:
        """Return a developer-readable representation including release metadata.

        Returns:
            str: A string of the form ``ReleaseDate(<iso_date>, release_id=<id>, release_name=<name>)``.
        """
        return (
            f"ReleaseDate({self.isoformat()}, "
            f"release_id={self.release_id}, release_name={self.release_name!r})"
        )

    def __reduce__(self) -> tuple[Callable[..., ReleaseDate], tuple[Any, ...]]:
        """Support pickling and ``copy.deepcopy`` via :meth:`_rebuild`.

        Returns:
            tuple: A two-tuple of the rebuild callable and the positional arguments needed to reconstruct the instance. Using ``type(self)._rebuild`` (rather than a hard-coded ``ReleaseDate._rebuild``) preserves subclass identity on round-trip.
        """
        return (
            type(self)._rebuild,
            (self.year, self.month, self.day, self.release_id, self.release_name),
        )

    # Protected Methods
    def _with_date(self, year: int, month: int, day: int) -> Self:
        """Rebuild this instance at a new (year, month, day), preserving metadata.

        Override of :meth:`fedfred._internals._models._DateBase._with_date`
        that routes through :meth:`create` to preserve the ``release_id``
        and ``release_name`` slots when arithmetic on the underlying date
        is performed by the base class.

        Args:
            year (int): The new year.
            month (int): The new month.
            day (int): The new day.

        Returns:
            ReleaseDate: A new :class:`ReleaseDate` at the given date with
            the same release metadata.
        """
        return type(self).create(
            year,
            month,
            day,
            release_id=self.release_id,
            release_name=self.release_name,
        )


class ReleaseDates(_DateSequence[ReleaseDate]):
    """An immutable, notebook-friendly sequence of :class:`ReleaseDate` objects.

    Behaves like a tuple of :class:`ReleaseDate` (indexing, slicing, iteration,
    ``len``, ``==``, ``in``, hashable) and is string-keyed by ISO date for
    ergonomic lookup (``release_dates["2024-12-06"]``) with IPython tab
    completion against the same key. Slicing returns a new :class:`ReleaseDates`.

    The lookup key is computed via :meth:`_lookup_value` rather than read from
    an attribute, since :class:`ReleaseDate` is itself the date and we want to
    key on its ISO-formatted string.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> release_dates = fred_client.get_release_dates(82)
        >>> release_dates[-1].release_name
        'Employment Situation'
        >>> release_dates["2024-12-06"].release_id
        82

    See Also:
        - :class:`fedfred.ReleaseDate`: The element type.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.ReleaseDates.html
    """

    __slots__ = ()

    # Protected Methods
    def _lookup_value(self, item: ReleaseDate) -> str:
        """Compute the lookup key for an item as its ISO date string.

        Override of :meth:`fedfred._internals._models._DateSequence._lookup_value`
        that enables string-key indexing and tab completion against ISO dates
        (e.g., ``release_dates["2024-12-06"]``).

        Args:
            item (ReleaseDate): The element to compute a lookup key for.

        Returns:
            str: The ISO 8601 representation of the date.
        """
        return item.isoformat()


@dataclass(slots=True)
class Source(_ModelBase):
    """A FRED Source.

    Represents a single data source in the Federal Reserve Economic Data
    (FRED) database. A source is an organization or entity that provides
    economic data — for example, the Bureau of Economic Analysis, the
    Bureau of Labor Statistics, or the Federal Reserve Board itself.
    Each source has an optional integer identifier, a name, an optional
    realtime period, an optional homepage link, and optional notes.

    When a ``client`` is attached, :attr:`releases` lazily fetches the
    releases published by this source.

    Attributes:
        name (str): The human-readable name of the source.
        id (int, optional): The unique identifier for the source.
        realtime_start (str, optional): The start of the real-time period in
            ``YYYY-MM-DD`` format.
        realtime_end (str, optional): The end of the real-time period in
            ``YYYY-MM-DD`` format.
        link (str, optional): A homepage URL for the source.
        notes (str, optional): Free-form notes accompanying the source.
        client (Fred, optional): The Fred client instance associated with this Source.
        releases (Releases): Lazily fetched releases published by this source.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> source = fred_client.get_source(1)
        >>> print(source.name)
        'Board of Governors of the Federal Reserve System (US)'

    See Also:
        - :class:`fedfred.Sources`: The plural sequence container.
        - :class:`fedfred.Release`: For the object representation of a FRED release.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Source.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/sources/
    """

    name: str
    """The human-readable name of the source."""

    id: int
    """The unique identifier for the source. Corresponds to ``source_id`` in the FRED API. ``None`` when the FRED payload omits it."""

    realtime_start: str | None
    """The start of the real-time period in ``YYYY-MM-DD`` format. Corresponds to ``realtime_start`` in the FRED API."""

    realtime_end: str | None
    """The end of the real-time period in ``YYYY-MM-DD`` format. Corresponds to ``realtime_end`` in the FRED API."""

    link: str | None = None
    """A homepage URL for the source. Tolerates ``"link"`` or ``"url"`` keys from the FRED payload."""

    notes: str | None = None
    """Free-form notes accompanying the source, if any."""

    _response_keys: ClassVar[tuple[str, ...]] = ("sources",)
    """The key in the FRED API response payload that contains the source list."""

    # Class Methods
    @classmethod
    def _from_dict(cls, data: dict[str, Any], client: _ClientModel | None = None) -> Source:
        """Build a single :class:`Source` from one raw FRED payload mapping.

        Internal parser used by :meth:`_from_response` and by sequence containers.
        Accepts both ``link`` and ``url`` as the homepage key.

        Args:
            data (dict[str, Any]): The raw source payload from the FRED API.
            client (_ClientModel, optional): The FRED client to attach to the
                resulting object for lazy relation traversal. Defaults to ``None``.

        Returns:
            Source: A fully populated :class:`Source` instance.

        Raises:
            ModelError: If ``data`` is not a mapping or is missing the
                ``name`` field.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Source.html
        """
        if not isinstance(data, dict):
            raise ModelError("Invalid source payload: expected a mapping")

        if "name" not in data:
            raise ModelError("Invalid source payload: missing 'name'")

        return cls(
            name=data["name"],
            id=data.get("id"),
            realtime_start=data.get("realtime_start"),
            realtime_end=data.get("realtime_end"),
            link=data.get("link") or data.get("url"),
            notes=data.get("notes"),
            client=client,
        )

    # Properties
    @property
    def releases(self) -> Releases:
        """The releases published by this source.

        Lazily resolves to ``client.get_source_releases(self.id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Releases: A sequence of :class:`Release` objects.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_source_releases(self.id)


class Sources(_ModelSequence[Source]):
    """An immutable, notebook-friendly sequence of :class:`Source` objects.

    Behaves like a tuple of :class:`Source` (indexing, slicing, iteration,
    ``len``, ``==``, ``in``) and is string-keyed by ``name`` for ergonomic
    lookup (``sources["Bureau of Economic Analysis"]``) with IPython tab
    completion. Slicing returns a new :class:`Sources` carrying the same client.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> sources = fred_client.get_sources()
        >>> sources["Board of Governors of the Federal Reserve System (US)"].id
        1

    See Also:
        - :class:`fedfred.Source`: The element type.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Sources.html
    """

    __slots__ = ()

    _lookup_key: ClassVar[str | None] = "name"
    """Attribute used for string-key lookup and tab completion (``sources["<source_name>"]``)."""

    # Sunder Methods
    def _repr_html_(self) -> str:
        """Render a compact HTML table preview of the first ten sources.

        Returns:
            str: An HTML ``<table>`` with id, name, and link columns and a
            truncation caption when the sequence exceeds ten entries.
        """
        head = self._items[:10]

        rows = "".join(
            f"<tr><td>{'' if s.id is None else s.id}</td>"
            f"<td>{html.escape(s.name)}</td>"
            f"<td>{html.escape(s.link or '')}</td></tr>"
            for s in head
        )

        caption = (
            "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"
        )

        return (
            "<table>" + caption + "<thead><tr><th>id</th><th>name</th><th>link</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )


@dataclass(slots=True)
class Element(_ModelBase):
    """A FRED Release Table Element.

    Represents a single element (row, section heading, or aggregate line)
    within a FRED release table — the structured table-of-contents view that
    accompanies major releases like the National Income and Product Accounts.
    Each element references a series, sits at a particular hierarchical
    level, and may contain child elements forming a tree.

    When a ``client`` is attached, :attr:`release` and :attr:`series` lazily
    resolve the related-resource references.

    Attributes:
        element_id (int): The unique identifier for the element.
        release_id (int): The release this element belongs to.
        series_id (str): The series this element references.
        parent_id (int): The parent element in the table hierarchy.
        line (str): The line label for the element.
        type (str): The element type classifier.
        name (str): The human-readable element name.
        level (str): The hierarchical level within the table.
        children (Elements, optional): Child elements in the table hierarchy.
        client (Fred, optional): The Fred client instance associated with this Element.
        release (Release): Lazily fetched release this element belongs to.
        series (Series): Lazily fetched series this element references.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> elements = fred_client.get_release_tables(53)
        >>> elements[0].name
        'Real Gross Domestic Product'

    See Also:
        - :class:`fedfred.Elements`: The plural sequence container.
        - :class:`fedfred.Release`: For the release this element belongs to.
        - :class:`fedfred.Series`: For the series this element references.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Element.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/release_tables.html
    """

    element_id: int
    """The unique identifier for the element."""

    release_id: int
    """The release this element belongs to. Corresponds to ``release_id`` in the FRED API."""

    series_id: str
    """The series this element references. Corresponds to ``series_id`` in the FRED API."""

    parent_id: int
    """The parent element in the table hierarchy. ``0`` for top-level entries."""

    line: str
    """The line label for the element (typically a row number or section anchor)."""

    type: str
    """The element type classifier (e.g., ``"header"``, ``"line"``)."""

    name: str
    """The human-readable element name."""

    level: str
    """The hierarchical level within the table (typically a numeric string)."""

    children: Elements | None = None
    """Child elements in the table hierarchy, or ``None`` if this is a leaf."""

    _response_keys: ClassVar[tuple[str, ...]] = ("elements",)
    """The key in the FRED API response payload that contains the element list. FRED returns this as a dict keyed by element id rather than a list; :func:`fedfred._core._objects_iter_dict_or_list` normalizes both shapes."""

    _response_shape: ClassVar[_ResponseShape] = "dict_or_list"
    """The shape of the FRED API response payload for this model, used by :func:`fedfred._core._objects_iter_dict_or_list` to normalize inconsistent shapes across endpoints. FRED returns ``"elements"`` as a dict keyed by element id rather than a list."""

    # Class Methods
    @classmethod
    def _from_dict(cls, data: dict[str, Any], client: _ClientModel | None = None) -> Element:
        """Build a single :class:`Element` from one raw FRED payload mapping.

        Internal parser used by :meth:`_from_response` and by sequence containers.
        Recursively constructs an :class:`Elements` for the ``children``
        field when present.

        Args:
            data (dict[str, Any]): The raw element payload from the FRED API.
            client (_ClientModel, optional): The FRED client to attach to the resulting object (and to recursively constructed children) for lazy relation traversal. Defaults to ``None``.

        Returns:
            Element: A fully populated :class:`Element` instance.

        Raises:
            ModelError: If ``data`` is not a mapping or is missing any of the required fields (``element_id``, ``release_id``, ``series_id``, ``parent_id``, ``line``, ``type``, ``name``, ``level``).

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Element.html
        """
        if not isinstance(data, dict):
            raise ModelError("Invalid element payload: expected a mapping")

        for required in (
            "element_id",
            "release_id",
            "series_id",
            "parent_id",
            "line",
            "type",
            "name",
            "level",
        ):
            if required not in data:
                raise ModelError(f"Invalid element payload: missing {required!r}")

        raw_children = data.get("children") or []

        children = (
            Elements(
                (cls._from_dict(c, client=client) for c in raw_children),
                client=client,
            )
            if raw_children
            else None
        )

        return cls(
            element_id=data["element_id"],
            release_id=data["release_id"],
            series_id=data["series_id"],
            parent_id=data["parent_id"],
            line=data["line"],
            type=data["type"],
            name=data["name"],
            level=data["level"],
            children=children,
            client=client,
        )

    # Properties
    @property
    def release(self) -> Release:
        """The release this element belongs to.

        Lazily resolves to ``client.get_release(self.release_id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Release: The :class:`Release` this element belongs to.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_release(self.release_id)

    @property
    def series(self) -> Series:
        """The series this element references.

        Lazily resolves to ``client.get_series(self.series_id)`` on access.
        Requires a ``client`` to be attached to this instance.

        Returns:
            Series: The :class:`Series` this element references.

        Raises:
            ModelError: If no client is attached to this instance.
        """
        client = cast("Fred", self._require_client())
        return client.get_series(self.series_id)


class Elements(_ModelSequence[Element]):
    """An immutable, notebook-friendly sequence of :class:`Element` objects.

    Behaves like a tuple of :class:`Element` (indexing, slicing, iteration,
    ``len``, ``==``, ``in``) and is string-keyed by ``name`` for ergonomic
    lookup (``elements["Real Gross Domestic Product"]``) with IPython tab
    completion. Slicing returns a new :class:`Elements` carrying the same
    client.

    FRED's release-tables endpoint returns the element collection as a dict
    keyed by element id rather than a list; the :meth:`_from_response` constructor
    normalizes both shapes.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> elements = fred_client.get_release_tables(53)
        >>> elements["Real Gross Domestic Product"].series_id
        'GDPC1'

    See Also:
        - :class:`fedfred.Element`: The element type.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.Elements.html
    """

    __slots__ = ()

    _lookup_key: ClassVar[str | None] = "name"
    """Attribute used for string-key lookup and tab completion (``elements["<element_name>"]``)."""

    # Sunder Methods
    def _repr_html_(self) -> str:
        """Render a compact HTML table preview of the first ten elements.

        Returns:
            str: An HTML ``<table>`` with element_id, name, type, and level
            columns and a truncation caption when the sequence exceeds ten
            entries.
        """
        head = self._items[:10]

        rows = "".join(
            f"<tr><td>{e.element_id}</td><td>{html.escape(e.name)}</td>"
            f"<td>{html.escape(e.type)}</td><td>{html.escape(e.level)}</td></tr>"
            for e in head
        )

        caption = (
            "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"
        )

        return (
            "<table>"
            + caption
            + "<thead><tr><th>element_id</th><th>name</th><th>type</th><th>level</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )


@dataclass(frozen=True, slots=True)
class PointObservation(_ObservationBase):
    """A FRED observation: a unique observation date mapped to a value.

    Within an :class:`ObservationSeries` the ``date`` is unique — one value per
    date — so a collection of these is ``DatetimeIndex``-able. A standard FRED
    response carries a single realtime window for the whole series; that window
    is series-level metadata on the owning sequence, never duplicated onto each
    row. To participate in vintage-aware operations, promote with
    :meth:`VintageObservation.from_base` (element) or ``ObservationSeries.as_vintage``
    (sequence), which broadcast that constant window back onto the rows.

    Inherits ``date``, ``value``, and ``is_missing`` from
    :class:`_ObservationBase` and adds no fields; it is a distinct type so the
    date-unique invariant is carried in the type system and ``isinstance`` checks
    cleanly separate point from vintage data.

    Examples:
        >>> import fedfred as fd
        >>> from datetime import date
        >>> p = fd.PointObservation(date(1929, 1, 1), 1202.659)
        >>> (p.date, p.value)
        (datetime.date(1929, 1, 1), 1202.659)
        >>> p == fd.PointObservation(date(1929, 1, 1), 1202.659)
        True
        >>> isinstance(p, fd.VintageObservation)
        False
    """


class PointSeries(_ObservationSequence[PointObservation]):
    """ """

    # TODO: Empty Docstring

    __slots__ = ("realtime_end", "realtime_start")

    _element_type = PointObservation

    # Class Methods
    @classmethod
    def _assemble(
        cls,
        response: dict,
        dates: np.ndarray,
        values: np.ndarray,
        series_id: str,
        units: str | None,
        frequency: str | None,
    ) -> PointSeries:
        """ """
        # TODO: Empty Docstring
        return cls(
            dates,
            values,
            series_id=series_id,
            units=units,
            frequency=frequency,
            realtime_start=date.fromisoformat(response["realtime_start"]),
            realtime_end=date.fromisoformat(response["realtime_end"]),
        )

    # Dunder Methods
    def __init__(
        self,
        dates: np.ndarray,
        values: np.ndarray,
        series_id: str,
        realtime_start: date,
        realtime_end: date,
        units: str | None = None,
        frequency: str | None = None,
    ) -> None:
        """ """
        # TODO: Empty docstring
        super().__init__(dates, values, series_id=series_id, units=units, frequency=frequency)
        self.realtime_start = realtime_start
        self.realtime_end = realtime_end

    # Protected Methods
    def _make(self, i: int) -> PointObservation:
        """ """
        # TODO: Empty docstring
        return PointObservation(_cell_date(self._dates, i), _cell_value(self._values, i))

    def _metadata(self) -> dict[str, Any]:
        """ """
        # TODO: Empty docstring
        return {
            **super()._metadata(),
            "realtime_start": self.realtime_start,
            "realtime_end": self.realtime_end,
        }

    def _rebuild(self, columns: dict[str, np.ndarray], metadata: dict[str, Any]) -> PointSeries:
        """ """
        # TODO: Empty Docstring
        return PointSeries(columns["date"], columns["value"], **metadata)

    # Public Methods
    def as_vintage(self) -> VintageSeries:
        """ """
        # TODO: Empty docstring
        n = len(self)
        return VintageSeries(
            self._dates,
            self._values,
            realtime_start=np.full(n, np.datetime64(self.realtime_start, "D")),
            realtime_end=np.full(n, np.datetime64(self.realtime_end, "D")),
            series_id=self.series_id,
            units=self.units,
            frequency=self.frequency,
        )

    def to_series(self) -> pd.Series:
        """The observations as one freq-aware pandas Series, named by series id."""
        return _columns_to_series(self._values, self._dates, self.frequency, self.series_id)

    def to_torch(self, dtype: torch.dtype | None = None, device: str = "cpu") -> torch.Tensor:
        """The values as a 1-D float tensor, shape ``(T,)``.

        Dates are intentionally excluded — a tensor is numeric, and the date axis is
        not tensor-natural; use ``to_series().index`` if you need it. Missing
        observations are ``NaN`` (derive a finite mask with ``~torch.isnan(t)``).

        Args:
            dtype: Torch dtype; defaults to ``torch.float32`` (ML/GPU convention).
                Pass ``torch.float64`` for state-space/Kalman work where the
                covariance recursions are precision-sensitive.
            device: Target device (``"cpu"``, ``"cuda"``, …).
        """
        torch = self._require("torch", "to_torch")
        return torch.tensor(self._values, dtype=dtype or torch.float32, device=device)


@dataclass(slots=True)
class ObservablesRelease:  # TODO: This thing is honest to god completely fucked just rewrite this with the v2 method.
    """Placeholder for the bulk-release observation aggregation (v4 rewrite pending).

    The v3 implementation of bulk-release retrieval is being replaced by a
    cursor-based streaming aggregation in v4. This class is retained as a
    type marker so that :meth:`fedfred.Fred.get_release_observations` keeps
    a stable signature during the transition; the implementation will be
    filled in once the v4 endpoint and observation-model designs are settled.

    Warning:
        This class is intentionally not yet implemented. Do not depend on
        any attribute or method here. The full design will land alongside
        the v4 observation model.

    See Also:
        - :class:`fedfred.Release`: For the underlying release object.
        - :class:`fedfred.Series`: For the underlying series objects bundled in a bulk release.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.BulkRelease.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/release_observations.html
    """

    release: Release

    seriess: Seriess

