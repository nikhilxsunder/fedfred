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
"""This module defines data classes for the FRED API responses.

Classes:
    Category: Represents a FRED Category.
    Series: Represents a FRED Series.
    Tag: Represents a FRED Tag.
    Release: Represents a FRED Release.
    ReleaseDate: Represents a FRED Release Date.
    Source: Represents a FRED Source.
    VintageDate: Represents a FRED Vintage Date.
    Element: Represents a FRED Element.
    SeriesGroup: Represents a FRED Series Observation.

Examples:
    >>> import fedfred as fd
    >>> fred_client = fd.Fred('your_api_key')
    >>> categories = fred_client.get_category(125)
    >>> for category in categories:
    >>>     print(category.name)
    'International Transactions'

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
    - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
"""

from __future__ import annotations
from datetime import date
from typing import Optional, List, Dict, ClassVar, Any, SupportsIndex, Self, Callable, TYPE_CHECKING
import html
from dataclasses import dataclass
import pandas as pd
from .._internals import _ClientModel, _ModelBase, _ModelSequence, _DateBase, _DateSequence
from .._core import _require_first_list, _objects_iter_dict_or_list, _coerce_lower
from .alfred import VintageDates

if TYPE_CHECKING:
    import polars as pl
    import dask.dataframe as dd

# TODO: Fix all docstrings post error design.

__all__ = [
    "Category", "Categories",
    "Series", "Seriess",
    "Tag", "Tags",
    "Release", "Releases",
    "ReleaseDate", "ReleaseDates",
    "Source", "Sources",
    "Element", "Elements",
    "BulkRelease",
]

@dataclass(slots=True)
class Category(_ModelBase):
    """A class used to represent a FRED Category.

    Represents a single category in the Federal Reserve Economic Data (FRED) hierarchy. Categories are organizational 
    units used by the FRED API to group related time-series (e.g., "Prices", "National Accounts", "Monetary Aggregates").
    Each category has a unique identifier, a human-readable name, and an optional parent category.

    Attributes:
        id (int): The unique identifier for the category.
        name (str): The name of the category.
        parent_id (int, optional): The unique identifier for the parent category.
        client (Fred, optional): The Fred client instance associated with this Category.
        children (List[Category]): The child categories of this category.
        related (List[Category]): The related categories of this category.
        series (List[Series]): The series in this category.
        tags (List[Tag]): The tags associated with this category.
        related_tags (List[Tag]): The related tags associated with this category.

    Notes:
        This class is designed to work with the FRED API and may require a client instance for certain operations.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> categories = fred_client.get_category(125)
        >>> for category in categories:
        >>>     print(category.name)
        'International Transactions'

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Category.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/categories/

    See Also:
        - :class:`fedfred.Tag`: For the object representation of a FRED tag.
    """

    id: int
    """The unique identifier for the category. corresponds to 'category_id' in the FRED API."""

    name: str
    """The name of the category."""

    parent_id: int | None
    """The unique identifier for the parent category, if any. can be used as a 'category_id' in the FRED API."""

    _response_key: ClassVar[str] = "categories"


    # Class Methods
    @classmethod
    def _from_dict(cls, data: dict[str, Any], client: _ClientModel | None = None) -> "Category":
        """Parses FRED API response and returns a list of Category objects.

        Args:
            data (dict[str, Any]): The FRED API response.
            client (_ClientModel | None, optional): The Fred client instance to associate with the Category objects.

        Returns:
            list[Category]: A list of Category objects.

        Raises: 
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "categories": [
            >>>         {"id": 125, "name": "International Transactions", "parent_id": 13},
            >>>         {"id": 126, "name": "Balance of Payments", "parent_id": 125}
            >>>     ]
            >>> }
            >>> categories = fd.Category.to_object(response)
            >>> for category in categories:
            >>>     print(category.id, category.name, category.parent_id)
            125 'International Transactions' 13
            126 'Balance of Payments' 125

        Notes:
            This method assumes that the input response dictionary contains a 'categories' key with a list of category data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Category.to_object.html
        """
        if not isinstance(data, dict):
            raise ModelError("Invalid category payload: expected a mapping") # TODO: Define ModelError

        if "id" not in data or "name" not in data:
            raise ModelError("Invalid category payload: missing 'id' or 'name'") # TODO: Define ModelError

        return cls(id=data["id"], name=data["name"], parent_id=data.get("parent_id"), client=client)

    # Properties
    @property
    def children(self) -> "Categories":
        """The child categories of this category. corresponds to 'get_category_children' in the FRED API."""
        return self._require_client().get_category_children(self.id)

    @property
    def related(self) -> "Categories":
        """The related categories of this category. corresponds to 'get_category_related' in the FRED API."""
        return self._require_client().get_category_related(self.id)

    @property
    def series(self) -> "Seriess":
        """The series in this category. corresponds to 'get_category_series' in the FRED API."""
        return self._require_client().get_category_series(self.id)

    @property
    def tags(self) -> "Tags":
        """The tags associated with this category. corresponds to 'get_category_tags' in the FRED API."""
        return self._require_client().get_category_tags(self.id)

    @property
    def related_tags(self) -> "Tags":
        """The related tags associated with this category. corresponds to 'get_category_related_tags' in the FRED API."""
        return self._require_client().get_category_related_tags(self.id)

class Categories(_ModelSequence[Category]):


    __slots__ = ()

    _lookup_key: ClassVar[str | None] = "name"

    def _repr_html_(self) -> str:


        head = self._items[:10]

        rows = "".join(
            f"<tr><td>{c.id}</td><td>{html.escape(c.name)}</td>"
            f"<td>{'' if c.parent_id is None else c.parent_id}</td></tr>"
            for c in head
        )

        caption = "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"

        return ("<table>" + caption +
                "<thead><tr><th>id</th><th>name</th><th>parent_id</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>")

@dataclass(slots=True)
class Series(_ModelBase):
    """A class used to represent a FRED Series.

    Represents a single series in the Federal Reserve Economic Data (FRED) database. A series is a time-ordered set of data points,
    such as economic indicators, financial metrics, or other statistical measures. Each series has a unique identifier, a title,
    observation dates, frequency, units, and other metadata.

    Attributes:
        id (str): The unique identifier for the series.
        title (str): The title of the series.
        frequency (str): The frequency of the series (e.g., "Monthly", "Quarterly").
        units (str): The units of measurement for the series (e.g., "Percent", "Dollars").
        seasonal_adjustment (str): The seasonal adjustment type for the series (e.g., "Seasonally Adjusted").
        last_updated (str): The date when the series was last updated.
        observation_start (str, optional): The start date of observations for the series.
        observation_end (str, optional): The end date of observations for the series.
        copyright_id (str, optional): The copyright identifier for the series.
        frequency_short (str, optional): The short form of the frequency (e.g., "m", "q").
        units_short (str, optional): The short form of the units (e.g., "pc", "usd").
        seasonal_adjustment_short (str, optional): The short form of the seasonal adjustment type (e.g., "sa").
        popularity (int, optional): A measure of the popularity of the series.
        realtime_start (str, optional): The start date for real-time data, if applicable.
        realtime_end (str, optional): The end date for real-time data, if applicable.
        group_popularity (int, optional): A measure of the popularity within a group, if applicable.
        notes (str, optional): Additional notes about the series.
        categories (List[Category]): The categories associated with this series.
        observations (pd.DataFrame): The DataFrame of observations associated with this series.
        release (List[Release]): The release associated with this series.
        tags (List[Tag]): The tags associated with this series.
        vintagedates (List[VintageDate]): The vintage dates associated with this series.
        client (Fred, optional): The Fred client instance associated with this Series.

    Notes:
        This class is designed to work with the FRED API and may require a client instance for certain operations.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> seriess = fred_client.get_series("GNPCA")
        >>> for series in seriess:
        >>>     print(series.title)
        'Gross National Product'

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Series.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/tags/series

    See Also:
        - :class:`fedfred.Category`: For the object representation of a FRED category.
    """

    id: str
    """The unique identifier for the series. corresponds to 'series_id' in the FRED API."""

    title: str
    """The title of the series."""

    frequency: str
    """The frequency of the series (e.g., "Monthly", "Quarterly")."""

    units: str
    """The units of measurement for the series (e.g., "Percent", "Dollars")."""

    seasonal_adjustment: str
    """The seasonal adjustment type for the series (e.g., "Seasonally Adjusted")."""

    last_updated: str
    """The date when the series was last updated."""

    observation_start: str | None = None
    """The start date of observations for the series. Corresponds to 'observation_start' in the FRED API. YYYY-MM-DD format."""

    observation_end: str | None = None
    """The end date of observations for the series. Corresponds to 'observation_end' in the FRED API. YYYY-MM-DD format."""

    copyright_id: str | None = None

    frequency_short: str | None = None
    """The short form of the frequency (e.g., "m", "q"). Corresponds to 'frequency' in the FRED API."""

    units_short: str | None = None
    """The short form of the units (e.g., "pc", "usd"). Corresponds to 'units' in the FRED API."""

    seasonal_adjustment_short: str | None = None
    """The short form of the seasonal adjustment type (e.g., "sa")."""

    popularity: int | None = None
    """A measure of the popularity of the series."""

    realtime_start: str | None = None
    """The start date for real-time data, if applicable. YYYY-MM-DD format. Corresponds to 'realtime_start' in the FRED API."""

    realtime_end: str | None = None
    """The end date for real-time data, if applicable. YYYY-MM-DD format. Corresponds to 'realtime_end' in the FRED API."""

    group_popularity: int | None = None
    """A measure of the popularity within a group, if applicable."""

    notes: str | None = None
    """Additional notes about the series."""

    _observations: pd.DataFrame | pl.DataFrame | dd.DataFrame | None = None
    """The DataFrame of observations associated with this series."""

    _response_key: ClassVar[str] = "seriess"


    # Class Methods
    @classmethod
    def _from_dict(cls, data: dict[str, Any], client: _ClientModel | None = None) -> "Series":

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
    def categories(self) -> "Categories":
        """The categories associated with this series. corresponds to 'get_series_categories' in the FRED API."""
        return self._require_client().get_series_categories(self.id)

    @property
    def observations(self) -> pd.DataFrame | pl.DataFrame | dd.DataFrame:
        """The DataFrame of observations associated with this series. corresponds to 'get_series_observations' in the FRED API."""
        return self._require_client().get_series_observations(self.id)

    @property
    def release(self) -> "Releases":
        """The release associated with this series. corresponds to 'get_series_release' in the FRED API."""
        return self._require_client().get_series_release(self.id)

    @property
    def tags(self) -> "Tags":
        """The tags associated with this series. corresponds to 'get_series_tags' in the FRED API."""
        return self._require_client().get_series_tags(self.id)

    @property
    def vintagedates(self) -> "VintageDates":
        """The vintage dates associated with this series. corresponds to 'get_series_vintagedates' in the FRED API."""
        return self._require_client().get_series_vintagedates(self.id)

class Seriess(_ModelSequence[Series]):


    __slots__ = ()


    _lookup_key: ClassVar[str | None] = "id"


    @classmethod
    def to_object(cls, response: dict[str, Any], client: _ClientModel | None = None) -> "Seriess":
        # Same dual-key shape as Series (FRED returns 'seriess' or 'series')

        raw = _require_first_list(response, ("seriess", "series"))

        return cls((cls._parse_item(item, client=client) for item in raw), client=client)

    def _repr_html_(self) -> str:


        head = self._items[:10]

        rows = "".join(
            f"<tr><td><code>{html.escape(s.id)}</code></td>"
            f"<td>{html.escape(s.title)}</td>"
            f"<td>{html.escape(s.frequency)}</td>"
            f"<td>{html.escape(s.units_short or s.units)}</td></tr>"
            for s in head
        )

        caption = "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"

        return ("<table>" + caption +
                "<thead><tr><th>id</th><th>title</th><th>frequency</th><th>units</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>")

@dataclass(slots=True)
class Tag(_ModelBase):
    """A class used to represent a FRED Tag.

    Represents a single tag in the Federal Reserve Economic Data (FRED) database. Tags are keywords or labels that can be
    associated with series to facilitate searching and categorization. Each tag has a name, group ID, creation date,
    popularity, and series count.

    Attributes:
        name (str): The name of the tag.
        group_id (str): The group ID of the tag.
        created (str): The creation date of the tag.
        popularity (int): The popularity of the tag.
        series_count (int): The number of series associated with the tag.
        notes (str, optional): Additional notes about the tag.
        client (Fred, optional): The Fred client instance associated with this Tag.

    Notes:
        This class is designed to work with the FRED API and may require a client instance for certain operations.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> tags = fred_client.get_tags()
        >>> for tag in tags:
        >>>     print(tag.name)
        'nation'
        'usa'
        'frb'...

    References:
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/tags/
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Tag.html

    See Also:
        - :class:`fedfred.Series`: For the object representation of a FRED series.
    """

    name: str
    """The name of the tag. corresponds to 'tag_name' in the FRED API."""

    group_id: str
    """The group ID of the tag."""

    created: str
    """The creation date of the tag."""

    popularity: int
    """The popularity of the tag."""

    series_count: int
    """The number of series associated with the tag."""

    notes: str | None = None
    """Additional notes about the tag."""

    _response_key: ClassVar[str] = "tags"


    # Class Methods
    @classmethod
    def _from_dict(cls, data: dict[str, Any], client: _ClientModel | None = None) -> "Tag":

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
    def related_tags(self) -> "Tags":
        """The related tags associated with this tag."""
        return self._require_client().get_related_tags(self.name)

    @property
    def series(self) -> "Series":
        """The series associated with this tag."""
        return self._require_client().get_tags_series(self.name)

class Tags(_ModelSequence[Tag]):


    __slots__ = ()


    _lookup_key: ClassVar[str | None] = "name"


    def _repr_html_(self) -> str:


        head = self._items[:10]

        rows = "".join(
            f"<tr><td>{html.escape(t.name)}</td>"
            f"<td>{html.escape(t.group_id)}</td>"
            f"<td>{t.popularity}</td>"
            f"<td>{t.series_count}</td></tr>"
            for t in head
        )

        caption = "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"

        return ("<table>" + caption +
                "<thead><tr><th>name</th><th>group_id</th><th>popularity</th><th>series_count</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>")

@dataclass(slots=True)
class Release(_ModelBase):
    """A class used to represent a Release.

    Represents a single release in the Federal Reserve Economic Data (FRED) database. A release is a scheduled publication of economic data,
    such as employment reports, GDP figures, or inflation statistics. Each release has a unique identifier, a name, real-time start and end dates,
    and other metadata.

    Attributes:
        name (str): The name of the release.
        id (int): The unique identifier for the release.
        realtime_start (str, optional): The start date for real-time data.
        realtime_end (str, optional): The end date for real-time data.
        press_release (bool, optional): Indicates if the release is a press release.
        link (str, optional): A link to more information about the release.
        notes (str, optional): Additional notes about the release.
        client (Fred, optional): The Fred client instance associated with this Release.
        dates (List[ReleaseDate]): The release dates associated with this release.
        series (List[Series]): The series associated with this release.
        sources (List[Source]): The sources associated with this release.
        tags (List[Tag]): The tags associated with this release.
        related_tags (List[Tag]): The related tags associated with this release.
        tables (List[Element]): The tables associated with this release.

    Notes:
        This class is designed to work with the FRED API and may require a client instance for certain operations.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> releases = fred_client.get_release(82)
        >>> for release in releases:
        >>>     print(release.name)
        'Employment Situation'

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Release.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/releases/

    See Also:
        - :class:`fedfred.Source`: For the object representation of a FRED source.
    """

    id: int
    """The unique identifier for the release. corresponds to 'release_id' in the FRED API."""

    name: str
    """The name of the release."""

    realtime_start: str | None = None
    """The start date for real-time data. YYYY-MM-DD format. corresponds to 'realtime_start' in the FRED API."""

    realtime_end: str | None = None
    """The end date for real-time data. YYYY-MM-DD format. corresponds to 'realtime_end' in the FRED API."""

    press_release: bool | None = None
    """Indicates if the release is a press release."""

    link: str | None = None
    """A link to more information about the release."""

    notes: str | None = None
    """Additional notes about the release."""

    _sources: "Sources" | None = None

    _response_key: ClassVar[str] = "releases"


    # Class Methods
    @classmethod
    def _from_dict(cls, data: dict[str, Any], client: _ClientModel | None = None) -> "Release":


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

    @classmethod
    def to_object(cls, response: dict[str, Any], client: _ClientModel | None = None) -> "Release":

        raw = _require_first_list(response, ("releases", "release"))

        if not raw:
            raise ModelError("No release found in the response")

        return cls._from_dict(raw[0], client=client)

    # Properties
    @property
    def dates(self) -> "ReleaseDates":
        """The release dates associated with this release."""
        return self._require_client().get_release_dates(self.id)

    @property
    def series(self) -> "Series":
        """The series associated with this release."""
        return self._require_client().get_release_series(self.id)

    @property
    def sources(self) -> "Sources":
        """The sources associated with this release."""
        return self._require_client().get_release_sources(self.id)

    @property
    def tags(self) -> "Tags":
        """The tags associated with this release."""
        return self._require_client().get_release_tags(self.id)

    @property
    def related_tags(self) -> "Tags":
        """The related tags associated with this release."""
        return self._require_client().get_release_related_tags(self.id)

    @property
    def tables(self) -> "Elements":
        """The tables associated with this release."""
        return self._require_client().get_release_tables(self.id)

class Releases(_ModelSequence[Release]):

    __slots__ = ()


    _lookup_key: ClassVar[str | None] = "name"


    @classmethod
    def to_object(cls, response: Dict[str, Any], client: _ClientModel | None = None) -> "Releases":

        raw = _require_first_list(response, ("releases", "release"))

        return cls((cls._parse_item(item, client=client) for item in raw), client=client)

    def _repr_html_(self) -> str:

        head = self._items[:10]

        rows = "".join(
            f"<tr><td>{r.id}</td><td>{html.escape(r.name)}</td>"
            f"<td>{'yes' if r.press_release else ''}</td></tr>"
            for r in head
        )

        caption = "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"

        return ("<table>" + caption +
                "<thead><tr><th>id</th><th>name</th><th>press_release</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>")

class ReleaseDate(_DateBase):

    __slots__ = ("release_id", "release_name")

    release_id: int
    """The ID of the release. Corresponds to 'release_id' in the FRED API."""

    release_name: str | None
    """The name of the release. Corresponds to 'release_name' in the FRED API."""

    _response_key: ClassVar[str] = "release_dates"

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
        """Pickle/copy rebuild factory routed through create() for validation parity."""
        return cls.create(
            year, month, day,
            release_id=release_id,
            release_name=release_name,
        )

    def __repr__(self) -> str:

        return (
            f"ReleaseDate({self.isoformat()}, "
            f"release_id={self.release_id}, release_name={self.release_name!r})"
        )

    def __reduce__(self) -> tuple[Callable[..., "ReleaseDate"], tuple[Any, ...]]:

        return (
            type(self)._rebuild,
            (self.year, self.month, self.day, self.release_id, self.release_name),
        )

    def _with_date(self, year: int, month: int, day: int) -> Self:

        return type(self).create(
            year, month, day,
            release_id=self.release_id,
            release_name=self.release_name,
        )

    @classmethod
    def _parse_value(cls, raw: Any) -> "ReleaseDate":

        if not isinstance(raw, dict):
            raise ModelError("Invalid release_date payload: expected a mapping")
        if "release_id" not in raw or "date" not in raw:
            raise ModelError("Invalid release_date payload: missing 'release_id' or 'date'")
        d_raw = raw["date"]
        d = date.fromisoformat(d_raw) if isinstance(d_raw, str) else d_raw
        return cls.create(
            d.year, d.month, d.day,
            release_id=raw["release_id"],
            release_name=raw.get("release_name"),
        )

class ReleaseDates(_DateSequence[ReleaseDate]):
    """Auto-wired sequence; no container-level metadata."""
    __slots__ = ()

    def _lookup_value(self, item: ReleaseDate) -> str:
        return item.isoformat()

@dataclass(slots=True)
class Source(_ModelBase):
    """A class used to represent a Source.

    Represents a single source in the Federal Reserve Economic Data (FRED) database. A source is an organization or entity that provides
    economic data, such as government agencies, research institutions, or private companies. Each source has a unique identifier, a name,
    real-time start and end dates, and other metadata.

    Attributes:
        name (str): The name of the source.
        id (int, optional): The unique identifier for the source.
        realtime_start (str, optional): The start date for real-time data.
        realtime_end (str, optional): The end date for real-time data.
        link (str, optional): A link to more information about the source.
        notes (str, optional): Additional notes about the source.
        client (Fred, optional): The Fred client instance associated with this Source.
        releases (List[Release]): The releases associated with this source.

    Notes:
        This class is designed to work with the FRED API and may require a client instance for certain operations.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> sources = fred_client.get_source(1)
        >>> for source in sources:
        >>>     print(source.name)
        'Federal Reserve Board'
        'Bureau of Economic Analysis'...

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Source.html
        - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/sources/

    See Also:
        - :class:`fedfred.Release`: For the object representation of a FRED release.
    """

    name: str
    """The name of the source."""

    id: int | None
    """The unique identifier for the source. corresponds to 'source_id' in the FRED API."""

    realtime_start: str | None
    """The start date for real-time data. YYYY-MM-DD format. corresponds to 'realtime_start' in the FRED API."""

    realtime_end: str | None
    """The end date for real-time data. YYYY-MM-DD format. corresponds to 'realtime_end' in the FRED API."""

    link: str | None = None
    """A link to more information about the source."""

    notes: str | None = None
    """Additional notes about the source."""

    _response_key: ClassVar[str] = "sources"

    # Class Methods
    @classmethod
    def _from_dict(cls, data: Dict[str, Any], client: _ClientModel | None = None) -> "Source":

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
    def releases(self) -> "Releases":
        """The releases associated with this source."""
        return self._require_client().get_source_releases(self.id)

class Sources(_ModelSequence[Source]):

    __slots__ = ()


    _lookup_key: ClassVar[str | None] = "name"


    def _repr_html_(self) -> str:


        head = self._items[:10]

        rows = "".join(
            f"<tr><td>{'' if s.id is None else s.id}</td>"
            f"<td>{html.escape(s.name)}</td>"
            f"<td>{html.escape(s.link or '')}</td></tr>"
            for s in head
        )

        caption = "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"

        return ("<table>" + caption +
                "<thead><tr><th>id</th><th>name</th><th>link</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>")

@dataclass(slots=True)
class Element(_ModelBase):
    """A class used to represent an Element.

    Represents a single element in the Federal Reserve Economic Data (FRED) database. An element is a component of a release,
    such as a table or a line item within a table. Each element has a unique identifier, a release ID, a series ID, a parent ID,
    and other metadata.

    Attributes:
        element_id (int): The unique identifier for the element.
        release_id (int): The ID of the release associated with the element.
        series_id (str): The ID of the series associated with the element.
        parent_id (int): The ID of the parent element.
        line (str): The line description of the element.
        type (str): The type of the element.
        name (str): The name of the element.
        level (str): The level of the element.
        children (List[Element], optional): The child elements of this element.
        client (Fred, optional): The Fred client instance associated with this Element.

    Notes:
        This class is designed to work with the FRED API and may require a client instance for certain operations.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> elements = fred_client.get_release_tables(53)
        >>> for element in elements:
        >>>     print(element.name)
        'Real Gross Domestic Product'
        'Gross Domestic Product'
        'Personal Income and Outlays'...

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Element.html

    See Also:
        - :class:`fedfred.Release`: For the object representation of a FRED release.
        - :class:`fedfred.Series`: For the object representation of a FRED series.
    """

    element_id: int
    """The unique identifier for the element"""

    release_id: int
    """The ID of the release associated with the element. corresponds to 'release_id' in the FRED API."""

    series_id: str
    """The ID of the series associated with the element. corresponds to 'series_id' in the FRED API."""

    parent_id: int
    """The ID of the parent element"""

    line: str
    """The line description of the element"""

    type: str
    """The type of the element"""

    name: str
    """The name of the element"""

    level: str
    """The level of the element"""

    children: Optional[List["Element"]] = None
    """The child elements of this element."""

    # Class Methods
    @classmethod
    def _from_dict(cls, data: Dict[str, Any], client: _ClientModel | None = None) -> "Element":


        if not isinstance(data, dict):
            raise ModelError("Invalid element payload: expected a mapping")
        
        for required in ("element_id", "release_id", "series_id", "parent_id", "line", "type", "name", "level"):
            if required not in data:
                raise ModelError(f"Invalid element payload: missing {required!r}")
            
        raw_children = data.get("children") or []

        children = Elements(
            (cls._from_dict(c, client=client) for c in raw_children),
            client=client,
        ) if raw_children else None
        
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

    @classmethod
    def to_object(cls, response: Dict[str, Any], client: _ClientModel | None = None) -> "Element":
        # FRED returns 'elements' as a dict keyed by id, not a list. Take the first.
        items = _objects_iter_dict_or_list(response, cls._response_key)
        if not items:
            raise ModelError("No element found in the response")
        return cls._from_dict(items[0], client=client)

    # Properties
    @property
    def release(self) -> List["Release"]:
        """The release associated with this element."""

        return self._require_client().get_release(self.release_id)

    @property
    def series(self) -> List["Series"]:
        """The series associated with this element."""

        return self._require_client().get_series(self.series_id)

class Elements(_ModelSequence[Element]):
    """Immutable, notebook-friendly sequence of FRED release-table elements."""

    __slots__ = ()


    _lookup_key: ClassVar[str | None] = "name"


    @classmethod
    def to_object(cls, response: Dict[str, Any], client: _ClientModel | None = None) -> "Elements":


        items = _objects_iter_dict_or_list(response, cls._response_key)
        return cls((cls._parse_item(item, client=client) for item in items), client=client)

    def _repr_html_(self) -> str:


        head = self._items[:10]

        rows = "".join(
            f"<tr><td>{e.element_id}</td><td>{html.escape(e.name)}</td>"
            f"<td>{html.escape(e.type)}</td><td>{html.escape(e.level)}</td></tr>"
            for e in head
        )

        caption = "" if len(self._items) <= 10 else f"<caption>showing 10 of {len(self._items)}</caption>"

        return ("<table>" + caption +
                "<thead><tr><th>element_id</th><th>name</th><th>type</th><th>level</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>")

@dataclass(slots=True)
class BulkRelease: # TODO: This thing is honest to god competely fucked just rewrite this with the v2 method.
    """A class used to represent a BulkRelease.

    Represents a bulk release in the Federal Reserve Economic Data (FRED) database. A bulk release contains multiple series
    associated with a single release. This class encapsulates the release information along with the list of
    series included in the bulk release.

    Attributes:
        release (List[Release]): The Release object associated with this BulkRelease.
        series (List[Series]): The list of Series objects associated with this BulkRelease.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> bulk_release = fred_client.get_release_observations('GDP')
        >>> print(bulk_release.release.title)
        'Gross Domestic Product'

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.BulkRelease.html

    See Also:
        - :class:`fedfred.Release`: For the object representation of a FRED release.
        - :class:`fedfred.Series`: For the object representation of a FRED series.
    """

    release: List[Release]
    """The Release object associated with this BulkRelease."""

    series: List[Series]
    """The list of Series objects associated with this BulkRelease."""

    @classmethod
    def to_object(cls, response: Dict, client: Optional["Fred"] = None) -> "BulkRelease":
        """Parses the FRED API response and returns a BulkRelease object.

        Args:
            response (Dict): The FRED API response.
            client (Fred, optional): The Fred client instance to associate with the BulkRelease

        Returns:
            BulkRelease: A BulkRelease object.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "release": {
            >>>         "id": 53,
            >>>         "title": "Gross Domestic Product"
            >>>     },
            >>>     "series": [
            >>>         {
            >>>             "id": "GDP",
            >>>             "title": "Gross Domestic Product"
            >>>         }
            >>>     ]
            >>> }
            >>> bulk_release = fd.BulkRelease.to_object(response)
            >>> print(bulk_release.release.title)
            'Gross Domestic Product'

        Notes:
            This method assumes that the input response dictionary contains 'release' and 'series' keys with the relevant data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.BulkRelease.to_object.html
        """

        bulk_release = cls(
                release=Release.to_object(response, client=client),
                series=Series.to_object(response, client=client)
            )
        if not bulk_release:
            raise ValueError("No bulk releases found in the response")
        return bulk_release

    @classmethod
    async def to_object_async(cls, response: Dict) -> "BulkRelease":
        """Asynchronously parses the FRED API response and returns a BulkRelease object.

        Args:
            response (Dict): The FRED API response.
            client (Fred, optional): The Fred client instance to associate with the BulkRelease  

        Returns:
            BulkRelease: A BulkRelease object.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "release": {
            >>>         "id": 53,
            >>>         "title": "Gross Domestic Product"
            >>>     },
            >>>     "series": [
            >>>         {
            >>>             "id": "GDP",
            >>>             "title": "Gross Domestic Product"
            >>>         }
            >>>     ]
            >>> }
            >>> async def main():
            >>>     bulk_release = await fd.BulkRelease.to_object_async(response)
            >>>     print(bulk_release.release.title)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            'Gross Domestic Product'

        Notes:
            This method assumes that the input response dictionary contains 'release' and 'series' keys with the relevant data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.BulkRelease.to_object_async.html
        """

        bulk_release = cls(
                release=await Release.to_object_async(response),
                series=await Series.to_object_async(response)
            )
        if not bulk_release:
            raise ValueError("No bulk releases found in the response")
        return bulk_release
