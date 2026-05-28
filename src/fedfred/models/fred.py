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
"""fedfred.models.fred

This module defines data classes for the FRED API responses.

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

from typing import Optional, List, Dict, ClassVar, Any
import html
from dataclasses import dataclass, field
import asyncio
import pandas as pd
from ..__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__
from .._internals import _ClientModel, _ModelBase, _ModelSequence # pragma: no cover
from .._core import _require_first_list

# TODO: Fix all docstrings post error design.

__all__ = [
    "Category", "Categories",
    "Series", "Seriess",
    "Tag", "Tags",
    "Release", "Releases",
    "ReleaseDate", "ReleaseDates",
    "Source", "Sources",
    "Element", "Elements",
    "VintageDate", "VintageDates",
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

    parent_id: Optional[int]
    """The unique identifier for the parent category, if any. can be used as a 'category_id' in the FRED API."""

    _response_key: ClassVar[str] = "categories"

    # Class Methods
    @classmethod
    def _from_dict(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> "Category":
        """Parses FRED API response and returns a list of Category objects.

        Args:
            data (Dict[str, Any]): The FRED API response.
            client (Optional[_ClientModel], optional): The Fred client instance to associate with the Category objects.

        Returns:
            List[Category]: A list of Category objects.

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
    def children(self) -> List["Category"]:
        """The child categories of this category. corresponds to 'get_category_children' in the FRED API."""

        return self._require_client().get_category_children(self.id)

    @property
    def related(self) -> List["Category"]:
        """The related categories of this category. corresponds to 'get_category_related' in the FRED API."""

        return self._require_client().get_category_related(self.id)

    @property
    def series(self) -> List["Series"]:
        """The series in this category. corresponds to 'get_category_series' in the FRED API."""

        return self._require_client().get_category_series(self.id)

    @property
    def tags(self) -> List["Tag"]:
        """The tags associated with this category. corresponds to 'get_category_tags' in the FRED API."""

        return self._require_client().get_category_tags(self.id)

    @property
    def related_tags(self) -> List["Tag"]:
        """The related tags associated with this category. corresponds to 'get_category_related_tags' in the FRED API."""

        return self._require_client().get_category_related_tags(self.id)

class Categories(_ModelSequence[Category]):


    __slots__ = ()


    _response_key: ClassVar[str] = Category._response_key


    @classmethod
    def _parse_item(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> Category:
        
        
        return Category._from_dict(data, client=client)

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

    observation_start: Optional[str] = None
    """The start date of observations for the series. Corresponds to 'observation_start' in the FRED API. YYYY-MM-DD format."""

    observation_end: Optional[str] = None
    """The end date of observations for the series. Corresponds to 'observation_end' in the FRED API. YYYY-MM-DD format."""

    copyright_id: Optional[str] = None

    frequency_short: Optional[str] = None
    """The short form of the frequency (e.g., "m", "q"). Corresponds to 'frequency' in the FRED API."""

    units_short: Optional[str] = None
    """The short form of the units (e.g., "pc", "usd"). Corresponds to 'units' in the FRED API."""

    seasonal_adjustment_short: Optional[str] = None
    """The short form of the seasonal adjustment type (e.g., "sa")."""

    popularity: Optional[int] = None
    """A measure of the popularity of the series."""

    realtime_start: Optional[str] = None
    """The start date for real-time data, if applicable. YYYY-MM-DD format. Corresponds to 'realtime_start' in the FRED API."""

    realtime_end: Optional[str] = None
    """The end date for real-time data, if applicable. YYYY-MM-DD format. Corresponds to 'realtime_end' in the FRED API."""

    group_popularity: Optional[int] = None
    """A measure of the popularity within a group, if applicable."""

    notes: Optional[str] = None
    """Additional notes about the series."""

    _observations: Optional[pd.DataFrame] = None
    """The DataFrame of observations associated with this series."""

    # Class Methods
    @classmethod
    def _from_dict(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> "Series":

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
    def categories(self) -> List["Category"]:
        """The categories associated with this series. corresponds to 'get_series_categories' in the FRED API."""

        return self._require_client().get_series_categories(self.id)

    @property
    def observations(self) -> pd.DataFrame:
        """The DataFrame of observations associated with this series. corresponds to 'get_series_observations' in the FRED API."""

        return self._require_client().get_series_observations(self.id)

    @property
    def release(self) -> List["Release"]:
        """The release associated with this series. corresponds to 'get_series_release' in the FRED API."""

        return self._require_client().get_series_release(self.id)

    @property
    def tags(self) -> List["Tag"]:
        """The tags associated with this series. corresponds to 'get_series_tags' in the FRED API."""

        return self._require_client().get_series_tags(self.id)

    @property
    def vintagedates(self) -> List['VintageDate']:
        """The vintage dates associated with this series. corresponds to 'get_series_vintagedates' in the FRED API."""

        return self._require_client().get_series_vintagedates(self.id)

class Seriess(_ModelSequence[Series]):


    __slots__ = ()


    _response_key: ClassVar[str] = Series._response_key


    @classmethod
    def _parse_item(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> Series:

        return Series._from_dict(data, client=client)

    @classmethod
    def to_object(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None) -> "Seriess":
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

    notes: Optional[str] = None
    """Additional notes about the tag."""

    # Class Methods
    @classmethod
    def _from_dict(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> "Tag":

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
    def related_tags(self) -> List["Tag"]:
        """The related tags associated with this tag."""

        return self._require_client().get_related_tags(self.name)

    @property
    def series(self) -> List["Series"]:
        """The series associated with this tag."""

        return self._require_client().get_tags_series(self.name)

class Tags(_ModelSequence[Tag]):


    __slots__ = ()

    _response_key: ClassVar[str] = Tag._response_key

    @classmethod
    def _parse_item(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> Tag:

        return Tag._from_dict(data, client=client)

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

    realtime_start: Optional[str] = None
    """The start date for real-time data. YYYY-MM-DD format. corresponds to 'realtime_start' in the FRED API."""

    realtime_end: Optional[str] = None
    """The end date for real-time data. YYYY-MM-DD format. corresponds to 'realtime_end' in the FRED API."""

    press_release: Optional[bool] = None
    """Indicates if the release is a press release."""

    link: Optional[str] = None
    """A link to more information about the release."""

    notes: Optional[str] = None
    """Additional notes about the release."""

    _sources: Optional[List["Source"]] = None


    # Class Methods
    @classmethod
    def _from_dict(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> "Release":


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
    def to_object(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None) -> "Release":

        raw = _require_first_list(response, ("releases", "release"))

        if not raw:
            raise ModelError("No release found in the response")
        
        return cls._from_dict(raw[0], client=client)

    # Properties
    @property
    def dates(self) -> List["ReleaseDate"]:
        """The release dates associated with this release."""

        return self._require_client().get_release_dates(self.id)

    @property
    def series(self) -> List["Series"]:
        """The series associated with this release."""

        return self._require_client().get_release_series(self.id)

    @property
    def sources(self) -> List["Source"]:
        """The sources associated with this release."""

        return self._require_client().get_release_sources(self.id)

    @property
    def tags(self) -> List["Tag"]:
        """The tags associated with this release."""

        return self._require_client().get_release_tags(self.id)

    @property
    def related_tags(self) -> List["Tag"]:
        """The related tags associated with this release."""

        return self._require_client().get_release_related_tags(self.id)

    @property
    def tables(self) -> List["Element"]:
        """The tables associated with this release."""

        return self._require_client().get_release_tables(self.id)

class Releases(_ModelSequence[Release]):

    __slots__ = ()

    _response_key: ClassVar[str] = Release._response_key

    @classmethod
    def _parse_item(cls, data: Dict[str, Any], client: Optional[_ClientModel] = None) -> Release:

        return Release._from_dict(data, client=client)

    @classmethod
    def to_object(cls, response: Dict[str, Any], client: Optional[_ClientModel] = None) -> "Releases":

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
@dataclass(slots=True)
class ReleaseDate:
    """A class used to represent a ReleaseDate.

    Represents a single release date in the Federal Reserve Economic Data (FRED) database. A release date indicates when a specific
    economic data release is scheduled to occur. Each release date is associated with a release and includes the date of the release.
    
    Attributes:
        release_id (int): The ID of the release.
        date (str): The date of the release.
        release_name (Optional[str]): The name of the release.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> release_dates = fred_client.get_release_dates(82)
        >>> for release_date in release_dates:
        >>>     print(release_date.date)
        '2024-07-05'
        '2024-08-02'...

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.ReleaseDate.html

    See Also:
        - :class:`fedfred.Release`: For the object representation of a FRED release.
    """

    release_id: int
    """The ID of the release. corresponds to 'release_id' in the FRED API."""

    date: str
    """The date of the release. corresponds to 'date' in the FRED API."""

    release_name: Optional[str] = None
    """The name of the release. corresponds to 'release_name' in the FRED API."""


    # Class Methods
    @classmethod
    def to_object(cls, response: Dict) -> List["ReleaseDate"]:
        """Parses the FRED API response and returns a list of ReleaseDate objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[ReleaseDate]: A list of ReleaseDate objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "release_dates": [
            >>>         {
            >>>             "release_id": 82,
            >>>             "date": "2024-07-05",
            >>>             "release_name": "Employment Situation"
            >>>         }
            >>>     ]
            >>> }
            >>> release_dates = fd.ReleaseDate.to_object(response)
            >>> for release_date in release_dates:
            >>>     print(release_date.release_id, release_date.date)
            82 '2024-07-05'

        Notes:
            This method assumes that the input response dictionary contains a 'release_dates' key with a list of release date data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.ReleaseDate.to_object.html
        """

        if "release_dates" not in response:
            raise ValueError("Invalid API response: Missing 'release_dates' field")
        release_dates = [
            cls(
                release_id=release_date["release_id"],
                date=release_date["date"],
                release_name=release_date.get("release_name")
            )
            for release_date in response["release_dates"]
        ]
        if not release_dates:
            raise ValueError("No release dates found in the response")
        return release_dates

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["ReleaseDate"]:
        """Asynchronously parses the FRED API response and returns a list of ReleaseDate objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[ReleaseDate]: A list of ReleaseDate objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "release_dates": [
            >>>         {
            >>>             "release_id": 82,
            >>>             "date": "2024-07-05",
            >>>             "release_name": "Employment Situation"
            >>>         }
            >>>     ]
            >>> }
            >>> async def main():
            >>>     release_dates = await fd.ReleaseDate.to_object_async(response)
            >>>     for release_date in release_dates:
            >>>         print(release_date.release_id, release_date.date)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            82 '2024-07-05'

        Notes:
            This method assumes that the input response dictionary contains a 'release_dates' key with a list of release date data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.ReleaseDate.to_object_async.html
        """

        return await asyncio.to_thread(cls.to_object, response)

@dataclass(slots=True)
class Source:
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

    id: Optional[int]
    """The unique identifier for the source. corresponds to 'source_id' in the FRED API."""

    realtime_start: Optional[str]
    """The start date for real-time data. YYYY-MM-DD format. corresponds to 'realtime_start' in the FRED API."""

    realtime_end: Optional[str]
    """The end date for real-time data. YYYY-MM-DD format. corresponds to 'realtime_end' in the FRED API."""

    link: Optional[str] = None
    """A link to more information about the source."""

    notes: Optional[str] = None
    """Additional notes about the source."""

    client: Optional["Fred"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    """The Fred client instance associated with this Source. Used for making further API calls related to this Source."""

    # Class Methods
    @classmethod
    def to_object(cls, response: Dict, client: Optional["Fred"] = None) -> List["Source"]:
        """Parses the FRED API response and returns a list of Source objects.

        Args:
            response (Dict): The FRED API response.
            client (Fred, optional): The Fred client instance to associate with the Source objects.

        Returns:
            List[Source]: A list of Source objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "sources": [
            >>>         {
            >>>             "id": 1,
            >>>             "realtime_start": "2000-01-01",
            >>>             "realtime_end": "2025-12-31",
            >>>             "name": "Federal Reserve Board"
            >>>         }
            >>>     ]
            >>> }
            >>> sources = fd.Source.to_object(response)
            >>> for source in sources:
            >>>     print(source.id, source.name)
            1 'Federal Reserve Board'

        Notes:
            This method assumes that the input response dictionary contains a 'sources' key with a list of source data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Source.to_object.html
            - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/sources/
        """

        if "sources" not in response:
            raise ValueError("Invalid API response: Missing 'sources' field")
        sources = [
            cls(
                id=source.get("id"),
                realtime_start=source.get("realtime_start"),
                realtime_end=source.get("realtime_end"),
                name=source["name"],
                link=source.get("link") or source.get("url"),
                notes=source.get("notes"),
                client=client if client is not None else None
            )
            for source in response["sources"]
        ]
        if not sources:
            raise ValueError("No sources found in the response")
        return sources

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["Source"]:
        """Asynchronously parses the FRED API response and returns a list of Source objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Source]: A list of Source objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "sources": [
            >>>         {
            >>>             "id": 1,
            >>>             "realtime_start": "2000-01-01",
            >>>             "realtime_end": "2025-12-31",
            >>>             "name": "Federal Reserve Board"
            >>>         }
            >>>     ]
            >>> }
            >>> async def main():
            >>>     sources = await fd.Source.to_object_async(response)
            >>>     for source in sources:
            >>>         print(source.id, source.name)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            1 'Federal Reserve Board'

        Notes:
            This method assumes that the input response dictionary contains a 'sources' key with a list of source data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Source.to_object_async.html
        """

        return await asyncio.to_thread(cls.to_object, response)

    # Properties
    @property
    def releases(self) -> List["Release"]:
        """The releases associated with this source."""
        if self.client is None:
            raise RuntimeError("Client is not set for this Source")
        if self.id:
            return self.client.get_source_releases(self.id)
        else:
            raise RuntimeError("Source ID is not set for this Source")

@dataclass(slots=True)
class Element:
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

    client: Optional["Fred"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    """The Fred client instance associated with this Element. Used for making further API calls related to this Element."""

    # Class Methods
    @classmethod
    def to_object(cls, response: Dict, client: Optional["Fred"] = None) -> List["Element"]:
        """Parses the FRED API response and returns a list of Elements objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Element]: A list of Element objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "elements": {
            >>>         "1": {
            >>>             "element_id": 1,
            >>>             "release_id": 53,
            >>>             "series_id": "DGDSRL1A225NBEA",
            >>>             "parent_id": 0,
            >>>             "line": "1. Real Gross Domestic Product",
            >>>             "type": "table",
            >>>             "name": "Real Gross Domestic Product",
            >>>             "level": "0",
            >>>             "children": []
            >>>         }
            >>>     }
            >>> }
            >>> elements = fd.Element.to_object(response)
            >>> for element in elements:
            >>>     print(element.element_id, element.name)
            1 'Real Gross Domestic Product'
        
        Notes:
            This method assumes that the input response dictionary contains an 'elements' key with a dictionary of element data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Element.to_object.html
        """

        if "elements" not in response:
            raise ValueError("Invalid API response: Missing 'elements' field")
        elements: List[Element] = []
        def process_element(element_data: Dict) -> "Element":
            children_list: List[Element] = []
            for child_data in element_data.get("children", []):
                child_element = process_element(child_data)
                children_list.append(child_element)
            return cls(
                element_id=element_data["element_id"],
                release_id=element_data["release_id"],
                series_id=element_data["series_id"],
                parent_id=element_data["parent_id"],
                line=element_data["line"],
                type=element_data["type"],
                name=element_data["name"],
                level=element_data["level"],
                children=children_list or None,
                client=client,
            )
        for element_data in response["elements"].values():
            elements.append(process_element(element_data))
        if not elements:
            raise ValueError("No elements found in the response")
        return elements

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["Element"]:
        """Asynchronously parses the FRED API response and returns a list of Element objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Element]: A list of Element objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "elements": {
            >>>         "1": {
            >>>             "element_id": 1,
            >>>             "release_id": 53,
            >>>             "series_id": "DGDSRL1A225NBEA",
            >>>             "parent_id": 0,
            >>>             "line": "1. Real Gross Domestic Product",
            >>>             "type": "table",
            >>>             "name": "Real Gross Domestic Product",
            >>>             "level": "0",
            >>>             "children": []
            >>>         }
            >>>     }
            >>> }
            >>> async def main():
            >>>     elements = await fd.Element.to_object_async(response)
            >>>     for element in elements:
            >>>         print(element.element_id, element.name)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            1 'Real Gross Domestic Product'
        
        Notes:
            This method assumes that the input response dictionary contains an 'elements' key with a dictionary of element data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Element.to_object_async.html
        """

        return await asyncio.to_thread(cls.to_object, response)

    # Properties
    @property
    def release(self) -> List["Release"]:
        """The release associated with this element."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Element")
        return self.client.get_release(self.release_id)

    @property
    def series(self) -> List["Series"]:
        """The series associated with this element."""
        if self.client is None:
            raise RuntimeError("Client is not set for this Element")
        return self.client.get_series(self.series_id)

@dataclass(slots=True)
class VintageDate:
    """A class used to represent a VintageDate.

    Represents a single vintage date in the Federal Reserve Economic Data (FRED) database. A vintage date indicates the date
    when a specific version of economic data was released or updated. Each vintage date is associated with a series and includes the date of the vintage.
    
    Attributes:
        vintage_date (str): The date of the vintage.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> vintage_dates = fred_client.get_series_vintage_dates('GDP')
        >>> for vintage_date in vintage_dates:
        >>>     print(vintage_date.vintage_date)
        '2024-07-01'
        '2024-06-01'...

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.VintageDate.html

    See Also:
        - :class:`fedfred.Series`: For the object representation of a FRED series.
    """

    vintage_date: str
    """The date of the vintage. corresponds to 'vintage_date' in the FRED API."""

    @classmethod
    def to_object(cls, response: Dict) -> List["VintageDate"]:
        """Parses the FRED API response and returns a list of VintageDate objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[VintageDate]: A list of VintageDate objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "vintage_dates": [
            >>>         "2024-07-01",
            >>>         "2024-06-01"
            >>>     ]
            >>> }
            >>> vintage_dates = fd.VintageDate.to_object(response)
            >>> for vintage_date in vintage_dates:
            >>>     print(vintage_date.vintage_date)
            '2024-07-01'
            '2024-06-01'

        Notes:
            This method assumes that the input response dictionary contains a 'vintage_dates' key with a list of vintage date data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.VintageDate.to_object.html
        """

        if "vintage_dates" not in response:
            raise ValueError("Invalid API response: Missing 'vintage_dates' field")
        vintage_dates = [
            cls(vintage_date=date)
            for date in response["vintage_dates"]
        ]
        if not vintage_dates:
            raise ValueError("No vintage dates found in the response")
        return vintage_dates

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["VintageDate"]:
        """Asynchronously parses the FRED API response and returns a list of VintageDate objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[VintageDate]: A list of VintageDate objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "vintage_dates": [
            >>>         "2024-07-01",
            >>>         "2024-06-01"
            >>>     ]
            >>> }
            >>> async def main():
            >>>     vintage_dates = await fd.VintageDate.to_object_async(response)
            >>>     for vintage_date in vintage_dates:
            >>>         print(vintage_date.vintage_date)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            '2024-07-01'
            '2024-06-01'
        
        Notes:
            This method assumes that the input response dictionary contains a 'vintage_dates' key with a list of vintage date data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.VintageDate.to_object_async.html
        """

        return await asyncio.to_thread(cls.to_object, response)

@dataclass(slots=True)
class BulkRelease:
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
