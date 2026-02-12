# filepath: /src/fedfred/fred/objects.py
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
"""fedfred.fred.objects

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

from __future__ import annotations
from typing import Optional, List, Dict, TYPE_CHECKING
from dataclasses import dataclass, field
import asyncio
import pandas as pd
from ..utils.helpers import Helpers, AsyncHelpers
from ..__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__

if TYPE_CHECKING:
    from .clients import Fred # pragma: no cover

@dataclass
class Category:
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

    parent_id: Optional[int] = None
    """The unique identifier for the parent category, if any. can be used as a 'category_id' in the FRED API."""

    client: Optional["Fred"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    """The Fred client instance associated with this Category. Used for making further API calls related to this Category."""

    # Class Methods
    @classmethod
    def to_object(cls, response: Dict, client: Optional["Fred"] = None) -> List["Category"]:
        """Parses FRED API response and returns a list of Category objects.

        Args:
            response (Dict): The FRED API response.
            client (Fred, optional): The Fred client instance to associate with the Category objects.

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

        if "categories" not in response:
            raise ValueError("Invalid API response: Missing 'categories' field")
        categories = [
            cls(
                id=category["id"],
                name=category["name"],
                parent_id=category.get("parent_id"),
                client=client if client is not None else None
            )
            for category in response["categories"]
        ]
        if not categories:
            raise ValueError("No categories found in the response")
        return categories

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["Category"]:
        """Asynchronously parses FRED API response and returns a list of Category objects.

        Args:
            response (Dict): The FRED API response.

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
            >>> async def main():
            >>>     categories = await fd.Category.to_object_async(response)
            >>>     for category in categories:
            >>>         print(category.id, category.name, category.parent_id)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            125 'International Transactions' 13
            126 'Balance of Payments' 125

        Notes: 
            This method assumes that the input response dictionary contains a 'categories' key with a list of category data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Category.to_object_async.html
        """

        return await asyncio.to_thread(cls.to_object, response)

    # Properties
    @property
    def children(self) -> List["Category"]:
        """The child categories of this category. corresponds to 'get_category_children' in the FRED API."""

        if self.client is None:
            raise RuntimeError("Client not set for this Category instance.")
        return self.client.get_category_children(self.id)

    @property
    def related(self) -> List["Category"]:
        """The related categories of this category. corresponds to 'get_category_related' in the FRED API."""

        if self.client is None:
            raise RuntimeError("Client not set for this Category instance.")
        return self.client.get_category_related(self.id)

    @property
    def series(self) -> List["Series"]:
        """The series in this category. corresponds to 'get_category_series' in the FRED API."""

        if self.client is None:
            raise RuntimeError("Client not set for this Category instance.")
        return self.client.get_category_series(self.id)

    @property
    def tags(self) -> List["Tag"]:
        """The tags associated with this category. corresponds to 'get_category_tags' in the FRED API."""

        if self.client is None:
            raise RuntimeError("Client not set for this Category instance.")
        return self.client.get_category_tags(self.id)

    @property
    def related_tags(self) -> List["Tag"]:
        """The related tags associated with this category. corresponds to 'get_category_related_tags' in the FRED API."""

        if self.client is None:
            raise RuntimeError("Client not set for this Category instance.")
        return self.client.get_category_related_tags(self.id)

@dataclass
class Series:
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

    client: Optional["Fred"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    """The Fred client instance associated with this Series. Used for making further API calls related to this Series."""

    # Class Methods
    @classmethod
    def to_object(cls, response: Dict, client: Optional["Fred"] = None) -> List["Series"]:
        """Parses the FRED API response and returns a list of Series objects.

        Args:
            response (Dict): The FRED API response.
            client (Fred, optional): The Fred client instance to associate with the Series objects.

        Returns:
            List[Series]: A list of Series objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "seriess": [
            >>>         {
            >>>             "id": "GNPCA",
            >>>             "title": "Gross National Product",
            >>>             "observation_start": "1947-01-01",
            >>>             "observation_end": "2021-12-01",
            >>>             "frequency": "Monthly",
            >>>             "frequency_short": "M",
            >>>             "units": "Billions of Dollars",
            >>>             "units_short": "USD",
            >>>             "seasonal_adjustment": "Seasonally Adjusted",
            >>>             "seasonal_adjustment_short": "SA",
            >>>             "last_updated": "2022-01-01",
            >>>             "popularity": 1500
            >>>         }
            >>>     ]
            >>> }
            >>> seriess = fd.Series.to_object(response)
            >>> for series in seriess:
            >>>     print(series.id, series.title)
            GNPCA 'Gross National Product'

        Notes:
            This method assumes that the input response dictionary contains a 'seriess' key with a list of series data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Series.to_object.html
        """

        dict_key = None
        if "seriess" in response:
            dict_key = "seriess"
        elif "series" in response:
            dict_key = "series"
        else:
            raise ValueError("Invalid API response: Missing 'seriess' field")
        series_list = [
            cls(
                id=series["id"] or series["series_id"],
                title=series["title"],
                observation_start=series.get("observation_start"),
                observation_end=series.get("observation_end"),
                frequency=series["frequency"],
                frequency_short=series.get("frequency_short").lower(),
                units=series["units"],
                units_short=series.get("units_short").lower(),
                seasonal_adjustment=series["seasonal_adjustment"],
                seasonal_adjustment_short=series.get("seasonal_adjustment_short").lower(),
                last_updated=series["last_updated"],
                popularity=series.get("popularity"),
                group_popularity=series.get("group_popularity"),
                realtime_start=series.get("realtime_start"),
                realtime_end=series.get("realtime_end"),
                notes=series.get("notes"),
                copyright_id=series.get("copyright_id"),
                _observations=Helpers.to_pd_df(series["observations"]) if "observations" in series else None,
                client=client if client is not None else None
            )
            for series in response[dict_key]
        ]
        if not series_list:
            raise ValueError("No series found in the response")
        return series_list

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["Series"]:
        """Asynchronously parses the FRED API response and returns a list of Series objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Series]: A list of Series objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "seriess": [
            >>>         {
            >>>             "id": "GNPCA",
            >>>             "title": "Gross National Product",
            >>>             "observation_start": "1947-01-01",
            >>>             "observation_end": "2021-12-01",
            >>>             "frequency": "Monthly",
            >>>             "frequency_short": "M",
            >>>             "units": "Billions of Dollars",
            >>>             "units_short": "USD",
            >>>             "seasonal_adjustment": "Seasonally Adjusted",
            >>>             "seasonal_adjustment_short": "SA",
            >>>             "last_updated": "2022-01-01",
            >>>             "popularity": 1500
            >>>         }
            >>>     ]
            >>> }
            >>> async def main():
            >>>     seriess = await fd.Series.to_object_async(response)
            >>>     for series in seriess:
            >>>         print(series.id, series.title)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            GNPCA 'Gross National Product'

        Notes:
            This method assumes that the input response dictionary contains a 'seriess' key with a list of series data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Series.to_object_async.html
        """

        dict_key = None
        if "seriess" in response:
            dict_key = "seriess"
        elif "series" in response:
            dict_key = "series"
        else:
            raise ValueError("Invalid API response: Missing 'seriess' field")
        series_list = [
            cls(
                id=series["id"] or series["series_id"],
                title=series["title"],
                observation_start=series.get("observation_start"),
                observation_end=series.get("observation_end"),
                frequency=series["frequency"],
                frequency_short=series.get("frequency_short").lower(),
                units=series["units"],
                units_short=series.get("units_short").lower(),
                seasonal_adjustment=series["seasonal_adjustment"],
                seasonal_adjustment_short=series.get("seasonal_adjustment_short").lower(),
                last_updated=series["last_updated"],
                popularity=series.get("popularity"),
                group_popularity=series.get("group_popularity"),
                realtime_start=series.get("realtime_start"),
                realtime_end=series.get("realtime_end"),
                notes=series.get("notes"),
                copyright_id=series.get("copyright_id"),
                _observations=await AsyncHelpers.to_pd_df(series["observations"]) if "observations" in series else None
            )
            for series in response[dict_key]
        ]
        if not series_list:
            raise ValueError("No series found in the response")
        return series_list

    # Properties
    @property
    def categories(self) -> List["Category"]:
        """The categories associated with this series. corresponds to 'get_series_categories' in the FRED API."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Series")
        return self.client.get_series_categories(self.id)

    @property
    def observations(self) -> pd.DataFrame:
        """The DataFrame of observations associated with this series. corresponds to 'get_series_observations' in the FRED API."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Series")
        if self._observations is None:
            frame = self.client.get_series_observations(self.id)
            assert isinstance(frame, pd.DataFrame)
            return frame
        else:
            return self._observations

    @property
    def release(self) -> List["Release"]:
        """The release associated with this series. corresponds to 'get_series_release' in the FRED API."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Series")
        return self.client.get_series_release(self.id)

    @property
    def tags(self) -> List["Tag"]:
        """The tags associated with this series. corresponds to 'get_series_tags' in the FRED API."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Series")
        return self.client.get_series_tags(self.id)

    @property
    def vintagedates(self) -> List['VintageDate']:
        """The vintage dates associated with this series. corresponds to 'get_series_vintagedates' in the FRED API."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Series")
        return self.client.get_series_vintagedates(self.id)

@dataclass
class Tag:
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

    client: Optional["Fred"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    """The Fred client instance associated with this Tag. Used for making further API calls related to this Tag."""

    # Class Methods
    @classmethod
    def to_object(cls, response: Dict, client: Optional["Fred"] = None) -> List["Tag"]:
        """Parses the FRED API response and returns a list of Tag objects.

        Args:
            response (Dict): The FRED API response.
            client (Fred, optional): The Fred client instance to associate with the Tag objects.

        Returns:
            List[Tag]: A list of Tag objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "tags": [
            >>>         {
            >>>             "name": "nation",
            >>>             "group_id": "geographic",
            >>>             "created": "2004-01-01",
            >>>             "popularity": 5000,
            >>>             "series_count": 150
            >>>         }
            >>>     ]
            >>> }
            >>> tags = fd.Tag.to_object(response)
            >>> for tag in tags:
            >>>     print(tag.name, tag.group_id)
            nation geographic

        Notes: 
            This method assumes that the input response dictionary contains a 'tags' key with a list of tag data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Tag.to_object.html
        """

        if "tags" not in response:
            raise ValueError("Invalid API response: Missing 'tags' field")
        tags = [
            cls(
                name=tag["name"],
                group_id=tag["group_id"],
                notes=tag.get("notes"),
                created=tag["created"],
                popularity=tag["popularity"],
                series_count=tag["series_count"],
                client=client if client is not None else None
            )
            for tag in response["tags"]
        ]
        if not tags:
            raise ValueError("No tags found in the response")
        return tags

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["Tag"]:
        """
        Asynchronously parses the FRED API response and returns a list of Tags objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Tag]: A list of Tag objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "tags": [
            >>>         {
            >>>             "name": "nation",
            >>>             "group_id": "geographic",
            >>>             "created": "2004-01-01",
            >>>             "popularity": 5000,
            >>>             "series_count": 150
            >>>         }
            >>>     ]
            >>> }
            >>> async def main():
            >>>     tags = await fd.Tag.to_object_async(response)
            >>>     for tag in tags:
            >>>         print(tag.name, tag.group_id)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            nation geographic
        
        Notes: 
            This method assumes that the input response dictionary contains a 'tags' key with a list of tag data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Tag.to_object_async.html
        """

        return await asyncio.to_thread(cls.to_object, response)

    # Properties
    @property
    def related_tags(self) -> List["Tag"]:
        """The related tags associated with this tag."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Tag")
        return self.client.get_related_tags(self.name)

    @property
    def series(self) -> List["Series"]:
        """The series associated with this tag."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Tag")
        return self.client.get_tags_series(self.name)

@dataclass
class Release:
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

    client: Optional["Fred"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    """The Fred client instance associated with this Release. Used for making further API calls related to this Release."""

    # Class Methods
    @classmethod
    def to_object(cls, response: Dict, client: Optional["Fred"] = None) -> List["Release"]:
        """Parses the FRED API response and returns a list of Release objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Release]: A list of Release objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "releases": [
            >>>         {
            >>>             "id": 82,
            >>>             "realtime_start": "2000-01-01",
            >>>             "realtime_end": "2025-12-31",
            >>>             "name": "Employment Situation",
            >>>             "press_release": true
            >>>         }
            >>>     ]
            >>> }
            >>> releases = fd.Release.to_object(response)
            >>> for release in releases:
            >>>     print(release.id, release.name)
            82 'Employment Situation'

        Notes:
            This method assumes that the input response dictionary contains a 'releases' key with a list of release data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Release.to_object.html
        """

        dict_key = None

        if "releases" in response:
            dict_key = "releases"
        elif "release" in response:
            dict_key = "release"
        else:
            raise ValueError("Invalid API response: Missing 'releases' field")
        releases = [
            cls(
                id=release["id"] or release["release_id"],
                realtime_start=release.get("realtime_start"),
                realtime_end=release.get("realtime_end"),
                name=release["name"],
                press_release=release.get("press_release"),
                link=release.get("link") or release.get("url"),
                notes=release.get("notes"),
                _sources= Source.to_object(release) if release.get("sources") else None,
                client=client if client is not None else None
            )
            for release in response[dict_key]
        ]
        if not releases:
            raise ValueError("No releases found in the response")
        return releases

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["Release"]:
        """Asynchronously parses the FRED API response and returns a list of Release objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Release]: A list of Release objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "releases": [
            >>>         {
            >>>             "id": 82,
            >>>             "realtime_start": "2000-01-01",
            >>>             "realtime_end": "2025-12-31",
            >>>             "name": "Employment Situation",
            >>>             "press_release": true
            >>>         }
            >>>     ]
            >>> }
            >>> async def main():
            >>>     releases = await fd.Release.to_object_async(response)
            >>>     for release in releases:
            >>>         print(release.id, release.name)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            82 'Employment Situation'
        
        Notes:
            This method assumes that the input response dictionary contains a 'releases' key with a list of release data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.Release.to_object_async.html
        """

        return await asyncio.to_thread(cls.to_object, response)

    # Properties
    @property
    def dates(self) -> List["ReleaseDate"]:
        """The release dates associated with this release."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        return self.client.get_release_dates(self.id)

    @property
    def series(self) -> List["Series"]:
        """The series associated with this release."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        return self.client.get_release_series(self.id)

    @property
    def sources(self) -> List["Source"]:
        """The sources associated with this release."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        if self._sources is None:
            return self.client.get_release_sources(self.id)
        else:
            return self._sources

    @property
    def tags(self) -> List["Tag"]:
        """The tags associated with this release."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        return self.client.get_release_tags(self.id)

    @property
    def related_tags(self) -> List["Tag"]:
        """The related tags associated with this release."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        return self.client.get_release_related_tags(self.id)

    @property
    def tables(self) -> List["Element"]:
        """The tables associated with this release."""

        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        return self.client.get_release_tables(self.id)

@dataclass
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

@dataclass
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

@dataclass
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

@dataclass
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

@dataclass
class SeriesGroup:
    """A class used to represent a SeriesGroup.

    Represents a single series group in the Federal Reserve Economic Data (FRED) database. A series group is a collection of related
    economic data series that share common characteristics, such as region type, seasonality, units, and frequency. Each series group has a title, region type, series group identifier,
    seasonality, units, frequency, and date range.

    Attributes:
        title (str): The title of the series group.
        region_type (str): The region type of the series group.
        series_group (str): The identifier of the series group.
        season (str): The seasonality of the series group.
        units (str): The units of the series group.
        frequency (str): The frequency of the series group.
        min_date (str): The minimum date of the series group.
        max_date (str): The maximum date of the series group.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> series_groups = fred_client.get_series_group('GDP')
        >>> for series_group in series_groups:
        >>>     print(series_group.title)
        'Gross Domestic Product'
        'Real Gross Domestic Product'...

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.SeriesGroup.html

    See Also:
        - :class:`fedfred.Series`: For the object representation of a FRED series.
        - :meth:`fedfred.Fred.get_series_group`: For retrieving series group information from the FRED API.
    """
    title: str
    """The title of the series group."""

    region_type: str
    """The region type of the series group."""

    series_group: str
    """The identifier of the series group."""

    season: str
    """The seasonality of the series group."""

    units: str
    """The units of the series group."""

    frequency: str
    """The frequency of the series group."""

    min_date: str
    """The minimum date of the series group."""

    max_date: str
    """The maximum date of the series group."""

    @classmethod
    def to_object(cls, response: Dict) -> List["SeriesGroup"]:
        """Parses the FRED API response and returns a list of SeriesGroup objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[SeriesGroup]: A list of SeriesGroup objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "series_group": [
            >>>         {
            >>>             "title": "Gross Domestic Product",
            >>>             "region_type": "NATIONAL",
            >>>             "series_group": "GDP",
            >>>             "season": "SA",
            >>>             "units": "Billions of Dollars",
            >>>             "frequency": "Quarterly",
            >>>             "min_date": "1947-01-01",
            >>>             "max_date": "2024-06-01"
            >>>         }
            >>>     ]
            >>> }
            >>> series_groups = fd.SeriesGroup.to_object(response)
            >>> for series_group in series_groups:
            >>>     print(series_group.title)
            'Gross Domestic Product'

        Notes:
            This method assumes that the input response dictionary contains a 'series_group' key with a list of series group data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.SeriesGroup.to_object.html
        """

        if "series_group" not in response:
            raise ValueError("Invalid API response: Missing 'series_group' field")
        series_group_data = response["series_group"]
        if isinstance(series_group_data, dict):
            series_group_data = [series_group_data]
        series_groups = [
            cls(
                title=series_group["title"],
                region_type=series_group["region_type"],
                series_group=series_group["series_group"],
                season=series_group["season"],
                units=series_group["units"],
                frequency=series_group["frequency"],
                min_date=series_group["min_date"],
                max_date=series_group["max_date"]
            )
            for series_group in series_group_data
        ]
        if not series_groups:
            raise ValueError("No series groups found in the response")
        return series_groups

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["SeriesGroup"]:
        """Asynchronously parses the FRED API response and returns a list of SeriesGroup objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[SeriesGroup]: A list of SeriesGroup objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "series_group": [
            >>>         {
            >>>             "title": "Gross Domestic Product",
            >>>             "region_type": "NATIONAL",
            >>>             "series_group": "GDP",
            >>>             "season": "SA",
            >>>             "units": "Billions of Dollars",
            >>>             "frequency": "Quarterly",
            >>>             "min_date": "1947-01-01",
            >>>             "max_date": "2024-06-01"
            >>>         }
            >>>     ]
            >>> }
            >>> async def main():
            >>>     series_groups = await fd.SeriesGroup.to_object_async(response)
            >>>     for series_group in series_groups:
            >>>         print(series_group.title)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            'Gross Domestic Product'

        Notes:
            This method assumes that the input response dictionary contains a 'series_group' key with a list of series group data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.SeriesGroup.to_object_async.html
        """

        return await asyncio.to_thread(cls.to_object, response)

@dataclass
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
