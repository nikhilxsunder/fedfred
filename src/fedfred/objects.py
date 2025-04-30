# filepath: /src/fedfred/object.py
#
# Copyright (c) 2025 Nikhil Sunder
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
This module defines data classes for the FRED API responses.
"""

from typing import Optional, List, Dict
from dataclasses import dataclass
import asyncio
from fedfred.__about__ import __title__, __version__, __author__, __license__, __copyright__, __description__, __url__

@dataclass
class Category:
    """
    A class used to represent a Category.
    """
    id: int
    name: str
    parent_id: Optional[int] = None

    @classmethod
    def to_object(cls, response: Dict) -> List["Category"]:
        """
        Parses FRED API response and returns a list of Category objects.
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
        Asynchronously parses FRED API response and returns a list of Category Objects.
        """
        return await asyncio.to_thread(cls.to_object, response)
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

    @classmethod
    def to_object(cls, response: Dict) -> List["Series"]:
        """
        Parses the FRED API response and returns a list of Series objects.
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
        """
        return await asyncio.to_thread(cls.to_object, response)

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

    @classmethod
    def to_object(cls, response: Dict) -> List["Tag"]:
        """
        Parses the FRED API response and returns a  list of Tag objects.
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
        """
        return await asyncio.to_thread(cls.to_object, response)

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

    @classmethod
    def to_object(cls, response: Dict) -> List["Release"]:
        """
        Parses the FRED API response and returns a list of Release objects.
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
        """
        return await asyncio.to_thread(cls.to_object, response)

@dataclass
class ReleaseDate:
    """
    A class used to represent a ReleaseDate.
    """
    release_id: int
    date: str
    release_name: Optional[str] = None

    @classmethod
    def to_object(cls, response: Dict) -> List["ReleaseDate"]:
        """
        Parses the FRED API response and returns a list of ReleaseDate objects.
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

    @classmethod
    def to_object(cls, response: Dict) -> List["Source"]:
        """
        Parses the FRED API response and returns a list of Source objects.
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
        """
        return await asyncio.to_thread(cls.to_object, response)

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

    @classmethod
    def to_object(cls, response: Dict) -> List["Element"]:
        """
        Parses the FRED API response and returns a list of Elements objects.
        """
        if "elements" not in response:
            raise ValueError("Invalid API response: Missing 'elements' field")
        elements = []
        def process_element(element_data: Dict) -> "Element":
            children_list = []
            for child_data in element_data.get("children", []):
                child_resp = {"elements": {str(child_data["element_id"]): child_data}}
                child_result = cls.to_object(child_resp)
                if isinstance(child_result, list):
                    children_list.extend(child_result)
                elif child_result is not None:
                    children_list.append(child_result)
            return cls(
                element_id=element_data["element_id"],
                release_id=element_data["release_id"],
                series_id=element_data["series_id"],
                parent_id=element_data["parent_id"],
                line=element_data["line"],
                type=element_data["type"],
                name=element_data["name"],
                level=element_data["level"],
                children=children_list if children_list else None
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
        """
        return await asyncio.to_thread(cls.to_object, response)

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
        """
        return await asyncio.to_thread(cls.to_object, response)
