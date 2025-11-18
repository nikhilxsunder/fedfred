# filepath: /src/fedfred/objects.py
#
# Copyright (c) 2025 Nikhil Sunder
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
"""
This module defines data classes for the FRED API responses.
"""

from __future__ import annotations
from typing import Optional, List, Dict, TYPE_CHECKING
from dataclasses import dataclass, field
import asyncio
import pandas as pd
from .__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__
if TYPE_CHECKING:
    from .clients import FredAPI # pragma: no cover

@dataclass
class Category:
    """
    A class used to represent a Category.
    """
    id: int
    name: str
    parent_id: Optional[int] = None
    client: Optional["FredAPI"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    # Class Methods
    @classmethod
    def to_object(cls, response: Dict) -> List["Category"]:
        """
        Parses FRED API response and returns a list of Category objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Category]: A list of Category objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        if "categories" not in response:
            raise ValueError("Invalid API response: Missing 'categories' field")
        categories = [
            cls(
                id=category["id"],
                name=category["name"],
                parent_id=category.get("parent_id")
            )
            for category in response["categories"]
        ]
        if not categories:
            raise ValueError("No categories found in the response")
        return categories

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["Category"]:
        """
        Asynchronously parses FRED API response and returns a list of Category objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Category]: A list of Category objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        return await asyncio.to_thread(cls.to_object, response)

    # Properties
    @property
    def children(self) -> List["Category"]:
        """
        Get the child categories of this category.

        Returns:
            List[Category]: A list of child Category objects.

        Raises:
            RuntimeError: If the client is not set for this Category.

        Example:
            >>> categories = fred_client.get_category(13)
            >>> for category in categories:
            >>>     children = category.children
            >>>     for child in children:
            >>>         print(child.name)
            'Exports'
            'Imports'
            'Income Payments & Receipts'
            'U.S. International Finance'

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client not set for this Category instance.")
        return self.client.get_category_children(self.id)

    @property
    def related(self) -> List["Category"]:
        """
        Get the related categories of this category.

        Returns:
            List[Category]: A list of related Category objects.

        Raises:
            RuntimeError: If the client is not set for this Category.

        Example:
            >>> categories = fred_client.get_category(32073)
            >>> for category in categories:
            >>>     for related in category.related:
            >>>         print(related.name)
            'Arkansas'
            'Illinois'
            'Indiana'
            'Kentucky'
            'Mississippi'
            'Missouri'
            'Tennessee'

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client not set for this Category instance.")
        return self.client.get_category_related(self.id)

    @property
    def series(self) -> List["Series"]:
        """
        Get the series in this category.

        Returns:
            List[Series]: A list of Series objects in this category.

        Raises:
            RuntimeError: If the client is not set for this Category.

        Example:
            >>> categories = fred_client.get_category(125)
            >>> for category in categories:
            >>>     for series in category.series:
            >>>         print(series.frequency)
            'Quarterly'
            'Annual'
            'Quarterly'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client not set for this Category instance.")
        return self.client.get_category_series(self.id)

    @property
    def tags(self) -> List["Tag"]:
        """
        Get the tags associated with this category.

        Returns:
            List[Tag]: A list of Tag objects associated with this category.

        Raises:
            RuntimeError: If the client is not set for this Category.

        Example:
            >>> categories = fred_client.get_category(125)
            >>> for category in categories:
            >>>     for tag in category.tags:
            >>>         print(tag.notes)
            'U.S. Department of Commerce: Bureau of Economic Analysis'
            'Country Level'
            'United States of America'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client not set for this Category instance.")
        return self.client.get_category_tags(self.id)

    @property
    def related_tags(self) -> List["Tag"]:
        """
        Get the related tags associated with this category.

        Returns:
            List[Tag]: A list of related Tag objects associated with this category.

        Raises:
            RuntimeError: If the client is not set for this Category.

        Example:
            >>> categories = fred_client.get_category(125)
            >>> for category in categories:
            >>>     for tag in category.related_tags:
            >>>         print(tag.name)
            'balance'
            'bea'
            'nation'
            'usa'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client not set for this Category instance.")
        return self.client.get_category_related_tags(self.id)

@dataclass
class Series:
    """
    A class used to represent a Series.
    """
    id: str
    title: str
    observation_start: str
    observation_end: str
    frequency: str
    frequency_short: str
    units: str
    units_short: str
    seasonal_adjustment: str
    seasonal_adjustment_short: str
    last_updated: str
    popularity: int
    realtime_start: Optional[str] = None
    realtime_end: Optional[str] = None
    group_popularity: Optional[int] = None
    notes: Optional[str] = None
    client: Optional["FredAPI"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    # Class Methods
    @classmethod
    def to_object(cls, response: Dict) -> List["Series"]:
        """
        Parses the FRED API response and returns a list of Series objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Series]: A list of Series objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        if "seriess" not in response:
            raise ValueError("Invalid API response: Missing 'seriess' field")
        series_list = [
            cls(
                id=series["id"],
                title=series["title"],
                observation_start=series["observation_start"],
                observation_end=series["observation_end"],
                frequency=series["frequency"],
                frequency_short=series["frequency_short"],
                units=series["units"],
                units_short=series["units_short"],
                seasonal_adjustment=series["seasonal_adjustment"],
                seasonal_adjustment_short=series["seasonal_adjustment_short"],
                last_updated=series["last_updated"],
                popularity=series["popularity"],
                group_popularity=series.get("group_popularity"),
                realtime_start=series.get("realtime_start"),
                realtime_end=series.get("realtime_end"),
                notes=series.get("notes")
            )
            for series in response["seriess"]
        ]
        if not series_list:
            raise ValueError("No series found in the response")
        return series_list

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["Series"]:
        """
        Asynchronously parses the FRED API response and returns a list of Series objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Series]: A list of Series objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        return await asyncio.to_thread(cls.to_object, response)

    # Properties
    @property
    def categories(self) -> List["Category"]:
        """
        Get the categories associated with this series.

        Returns:
            List[Category]: A list of Category objects associated with this series.

        Raises:
            RuntimeError: If the client is not set for this Series.

        Example:
            >>> seriess = fred_client.get_series("EXJPUS")
            >>> for series in seriess:
            >>>     for category in series.categories:
            >>>         print(category.id)
            '95'
            '275'

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Series")
        return self.client.get_series_categories(self.id)

    @property
    def observations(self) -> pd.DataFrame:
        """
        Get the observations associated with this series.

        Returns:
            pd.DataFrame: A DataFrame containing the observations for this series.

        Raises:
            RuntimeError: If the client is not set for this Series.

        Example:
            >>> seriess = fred_client.get_series("GNPCA")
            >>> for series in seriess:
            >>>     observations = series.observations
            >>>     print(observations.head())
            date       realtime_start realtime_end     value
            1929-01-01     2025-02-13   2025-02-13  1202.659
            1930-01-01     2025-02-13   2025-02-13  1100.670
            1931-01-01     2025-02-13   2025-02-13  1029.038
            1932-01-01     2025-02-13   2025-02-13   895.802
            1933-01-01     2025-02-13   2025-02-13   883.847

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Series")
        frame = self.client.get_series_observations(self.id)
        assert isinstance(frame, pd.DataFrame)
        return frame

    @property
    def release(self) -> List["Release"]:
        """
        Get the release associated with this series.

        Returns:
            List[Release]: A list of Release objects associated with this series.

        Raises:
            RuntimeError: If the client is not set for this Series.

        Example:
            >>> seriess = fred_client.get_series("GNPCA")
            >>> for series in seriess:
            >>>     for release in series.release:
            >>>         print(release.name)
            'Gross National Product'

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Series")
        return self.client.get_series_release(self.id)

    @property
    def tags(self) -> List["Tag"]:
        """
        Get the tags associated with this series.

        Returns:
            List[Tag]: A list of Tag objects associated with this series.

        Raises:
            RuntimeError: If the client is not set for this Series.

        Example:
            >>> seriess = fred_client.get_series("GNPCA")
            >>> for series in seriess:
            >>>     for tag in series.tags:
            >>>         print(tag.name)
            'nation'
            'nsa'
            'usa'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Series")
        return self.client.get_series_tags(self.id)

    @property
    def vintagedates(self) -> List['VintageDate']:
        """
        Get the vintage dates associated with this series.

        Returns:
            List[str]: A list of vintage date strings associated with this series.

        Raises:
            RuntimeError: If the client is not set for this Series.

        Example:
            >>> seriess = fred_client.get_series("GNPCA")
            >>> for series in seriess:
            >>>     for date in series.vintagedates:
            >>>         print(date.vintage_date)
            '2025-02-13'
            '2025-01-15'
            '2024-12-13'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Series")
        return self.client.get_series_vintagedates(self.id)

@dataclass
class Tag:
    """
    A class used to represent a Tag.
    """
    name: str
    group_id: str
    created: str
    popularity: int
    series_count: int
    notes: Optional[str] = None
    client: Optional["FredAPI"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    # Class Methods
    @classmethod
    def to_object(cls, response: Dict) -> List["Tag"]:
        """
        Parses the FRED API response and returns a  list of Tag objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Tag]: A list of Tag objects.

        Raises:
            ValueError: If the response does not contain the expected data.
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
                series_count=tag["series_count"]
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
        """
        return await asyncio.to_thread(cls.to_object, response)

    # Properties
    @property
    def related_tags(self) -> List["Tag"]:
        """
        Get the related tags associated with this tag.

        Returns:
            List[Tag]: A list of related Tag objects associated with this tag.

        Raises:
            RuntimeError: If the client is not set for this Tag.

        Example:
            >>> tags = fred_client.get_tags()
            >>> for tag in tags:
            >>>     for related_tag in tag.related_tags:
            >>>         print(related_tag.name)
            'nation'
            'usa'
            'frb'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Tag")
        return self.client.get_related_tags(self.name)

    @property
    def series(self) -> List["Series"]:
        """
        Get the series associated with this tag.

        Returns:
            List[Series]: A list of Series objects associated with this tag.

        Raises:
            RuntimeError: If the client is not set for this Tag.

        Example:
            >>> tags = fred_client.get_tags()
            >>> for tag in tags:
            >>>     for series in tag.series:
            >>>         print(series.id)
            'CPGDFD02SIA657N'
            'CPGDFD02SIA659N'
            'CPGDFD02SIM657N'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Tag")
        return self.client.get_tags_series(self.name)

@dataclass
class Release:
    """
    A class used to represent a Release.
    """
    id: int
    realtime_start: str
    realtime_end: str
    name: str
    press_release: bool
    link: Optional[str] = None
    notes: Optional[str] = None
    client: Optional["FredAPI"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    # Class Methods
    @classmethod
    def to_object(cls, response: Dict) -> List["Release"]:
        """
        Parses the FRED API response and returns a list of Release objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Release]: A list of Release objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        if "releases" not in response:
            raise ValueError("Invalid API response: Missing 'releases' field")
        releases = [
            cls(
                id=release["id"],
                realtime_start=release["realtime_start"],
                realtime_end=release["realtime_end"],
                name=release["name"],
                press_release=release["press_release"],
                link=release.get("link"),
                notes=release.get("notes")
            )
            for release in response["releases"]
        ]
        if not releases:
            raise ValueError("No releases found in the response")
        return releases

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["Release"]:
        """
        Asynchronously parses the FRED API response and returns a list of Release objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Release]: A list of Release objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        return await asyncio.to_thread(cls.to_object, response)

    # Properties
    @property
    def dates(self) -> List["ReleaseDate"]:
        """
        Get the release dates associated with this release.

        Returns:
            List[ReleaseDate]: A list of ReleaseDate objects associated with this release.

        Raises:
            RuntimeError: If the client is not set for this Release.

        Example:
            >>> releases = fred_client.get_release(82)
            >>> for release in releases:
            >>>     for date in release.dates:
            >>>         print(date.date)
            '1997-02-10'
            '1998-02-10'
            '1999-02-04'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        return self.client.get_release_dates(self.id)

    @property
    def series(self) -> List["Series"]:
        """
        Get the series associated with this release.

        Returns:
            List[Series]: A list of Series objects associated with this release.

        Raises:
            RuntimeError: If the client is not set for this Release.

        Example:
            >>> releases = fred_client.get_release(51)
            >>> for release in releases:
            >>>     for series in release.series:
            >>>         print(series.id)
            'BOMTVLM133S'
            'BOMVGMM133S'
            'BOMVJMM133S'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        return self.client.get_release_series(self.id)

    @property
    def sources(self) -> List["Source"]:
        """
        Get the sources associated with this release.

        Returns:
            List[Source]: A list of Source objects associated with this release.

        Raises:
            RuntimeError: If the client is not set for this Release.

        Example:
            >>> releases = fred_client.get_release(51)
            >>> for release in releases:
            >>>     for source in release.sources:
            >>>         print(source.name)
            'U.S. Department of Commerce: Bureau of Economic Analysis'
            'U.S. Department of Commerce: Census Bureau'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        return self.client.get_release_sources(self.id)

    @property
    def tags(self) -> List["Tag"]:
        """
        Get the tags associated with this release.

        Returns:
            List[Tag]: A list of Tag objects associated with this release.

        Raises:
            RuntimeError: If the client is not set for this Release.

        Example:
            >>> releases = fred_client.get_release(86)
            >>> for release in releases:
            >>>     for tag in release.tags:
            >>>         print(tag.name)
            'commercial paper'
            'frb'
            'nation'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        return self.client.get_release_tags(self.id)

    @property
    def related_tags(self) -> List["Tag"]:
        """
        Get the related tags associated with this release.

        Returns:
            List[Tag]: A list of related Tag objects associated with this release.

        Raises:
            RuntimeError: If the client is not set for this Release.

        Example:
            >>> releases = fred_client.get_release(86)
            >>> for release in releases:
            >>>     for tag in release.related_tags:
            >>>         print(tag.name)
            'commercial paper'
            'frb'
            'nation'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        return self.client.get_release_related_tags(self.id)

    @property
    def tables(self) -> List["Element"]:
        """
        Get the tables associated with this release.

        Returns:
            List[Element]: A list of Element objects associated with this release.

        Raises:
            RuntimeError: If the client is not set for this Release.

        Example:
            >>> releases = fred_client.get_release(53)
            >>> for release in releases:
            >>>     for element in release.tables:
            >>>         print(element.series_id)
            'DGDSRL1A225NBEA'
            'DDURRL1A225NBEA'
            'DNDGRL1A225NBEA'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Release")
        return self.client.get_release_tables(self.id)

@dataclass
class ReleaseDate:
    """
    A class used to represent a ReleaseDate.
    """
    release_id: int
    date: str
    release_name: Optional[str] = None
    # Class Methods
    @classmethod
    def to_object(cls, response: Dict) -> List["ReleaseDate"]:
        """
        Parses the FRED API response and returns a list of ReleaseDate objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[ReleaseDate]: A list of ReleaseDate objects.

        Raises:
            ValueError: If the response does not contain the expected data.
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
        """
        Asynchronously parses the FRED API response and returns a list of ReleaseDate objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[ReleaseDate]: A list of ReleaseDate objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        return await asyncio.to_thread(cls.to_object, response)

@dataclass
class Source:
    """
    A class used to represent a Source.
    """
    id: int
    realtime_start: str
    realtime_end: str
    name: str
    link: Optional[str] = None
    notes: Optional[str] = None
    client: Optional["FredAPI"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    # Class Methods
    @classmethod
    def to_object(cls, response: Dict) -> List["Source"]:
        """
        Parses the FRED API response and returns a list of Source objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Source]: A list of Source objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        if "sources" not in response:
            raise ValueError("Invalid API response: Missing 'sources' field")
        sources = [
            cls(
                id=source["id"],
                realtime_start=source["realtime_start"],
                realtime_end=source["realtime_end"],
                name=source["name"],
                link=source.get("link"),
                notes=source.get("notes")
            )
            for source in response["sources"]
        ]
        if not sources:
            raise ValueError("No sources found in the response")
        return sources

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["Source"]:
        """
        Asynchronously parses the FRED API response and returns a list of Source objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Source]: A list of Source objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        return await asyncio.to_thread(cls.to_object, response)

    # Properties
    @property
    def releases(self) -> List["Release"]:
        """
        Get the releases associated with this source.

        Returns:
            List[Release]: A list of Release objects associated with this source.

        Raises:
            RuntimeError: If the client is not set for this Source.

        Example:
            >>> sources = fred_client.get_source(1)
            >>> for source in sources:
            >>>     for release in source.releases:
            >>>         print(release.name)
            'G.17 Industrial Production and Capacity Utilization'
            'G.19 Consumer Credit'
            'G.5 Foreign Exchange Rates'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Source")
        return self.client.get_source_releases(self.id)

@dataclass
class Element:
    """
    A class used to represent an Element.
    """
    element_id: int
    release_id: int
    series_id: str
    parent_id: int
    line: str
    type: str
    name: str
    level: str
    children: Optional[List["Element"]] = None
    client: Optional["FredAPI"] = field(
        default=None,
        repr=False,
        compare=False,
    )
    # Class Methods
    @classmethod
    def to_object(cls, response: Dict, client: Optional["FredAPI"] = None) -> List["Element"]:
        """
        Parses the FRED API response and returns a list of Elements objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Element]: A list of Element objects.

        Raises:
            ValueError: If the response does not contain the expected data.
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
        """
        Asynchronously parses the FRED API response and returns a list of Element objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[Element]: A list of Element objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        return await asyncio.to_thread(cls.to_object, response)

    # Properties
    @property
    def release(self) -> List["Release"]:
        """
        Get the release associated with this element.

        Returns:
            List[Release]: A list of Release objects associated with this element.

        Raises:
            RuntimeError: If the client is not set for this Element.

        Example:
            >>> elements = fred_client.get_release_tables(53)
            >>> for element in elements:
            >>>     for release in element.release:
            >>>         print(release.name)
            'Real Gross Domestic Product'
            'Gross Domestic Product'
            'Personal Income and Outlays'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Element")
        return self.client.get_release(self.release_id)

    @property
    def series(self) -> List["Series"]:
        """
        Get the series associated with this element.

        Returns:
            List[Series]: A list of Series objects associated with this element.

        Raises:
            RuntimeError: If the client is not set for this Element.

        Example:
            >>> elements = fred_client.get_release_tables(53)
            >>> for element in elements:
            >>>     for series in element.series:
            >>>         print(series.id)
            'DGDSRL1A225NBEA'
            'DDURRL1A225NBEA'
            'DNDGRL1A225NBEA'...

        Note: This property is meant for simple relational requests, for more complex queries use the client methods directly.
        """
        if self.client is None:
            raise RuntimeError("Client is not set for this Element")
        return self.client.get_series(self.series_id)

@dataclass
class VintageDate:
    """
    A class used to represent a VintageDate.
    """
    vintage_date: str

    @classmethod
    def to_object(cls, response: Dict) -> List["VintageDate"]:
        """
        Parses the FRED API response and returns a list of VintageDate objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[VintageDate]: A list of VintageDate objects.

        Raises:
            ValueError: If the response does not contain the expected data.
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
        """
        Asynchronously parses the FRED API response and returns a list of VintageDate objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[VintageDate]: A list of VintageDate objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        return await asyncio.to_thread(cls.to_object, response)

@dataclass
class SeriesGroup:
    """
    A class used to represent a SeriesGroup.
    """
    title: str
    region_type: str
    series_group: str
    season: str
    units: str
    frequency: str
    min_date: str
    max_date: str

    @classmethod
    def to_object(cls, response: Dict) -> List["SeriesGroup"]:
        """
        Parses the FRED API response and returns a list of SeriesGroup objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[SeriesGroup]: A list of SeriesGroup objects.

        Raises:
            ValueError: If the response does not contain the expected data.
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
        """
        Asynchronously parses the FRED API response and returns a list of SeriesGroup objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[SeriesGroup]: A list of SeriesGroup objects.

        Raises:
            ValueError: If the response does not contain the expected data.
        """
        return await asyncio.to_thread(cls.to_object, response)
