"""
This module defines data classes for the FRED API responses.
"""
from typing import Optional, List, Dict, Union
from dataclasses import dataclass

@dataclass
class Category:
    """
    A class used to represent a Category.
    """
    id: int
    name: str
    parent_id: Optional[int] = None

    @classmethod
    def from_api_response(cls, response: Dict) -> Union["Category", List["Category"], None]:
        """
        Parses FRED API response and returns either a single Category or a list of Categories.
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
            return None
        elif len(categories) == 1:
            return categories[0]
        else:
            return categories
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
    def from_api_response(cls, response: Dict) -> Union["Series", List["Series"], None]:
        """
        Parses the FRED API response and returns a single Series or a list of Series.
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
            return None
        if len(series_list) == 1:
            return series_list[0]
        return series_list

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
    def from_api_response(cls, response: Dict) -> Union["Tag", List["Tag"], None]:
        """
        Parses the FRED API response and returns a single Tag or a list of Tags.
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
            return None
        if len(tags) == 1:
            return tags[0]
        return tags

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
    def from_api_response(cls, response: Dict) -> Union["Release", List["Release"], None]:
        """
        Parses the FRED API response and returns a single Release or a list of Releases.
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
            return None
        if len(releases) == 1:
            return releases[0]
        return releases

@dataclass
class ReleaseDate:
    """
    A class used to represent a ReleaseDate.
    """
    release_id: int
    date: str
    release_name: Optional[str] = None

    @classmethod
    def from_api_response(cls, response: Dict) -> Union["ReleaseDate", List["ReleaseDate"], None]:
        """
        Parses the FRED API response and returns a single ReleaseDate or a list of ReleaseDates.
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
            return None
        if len(release_dates) == 1:
            return release_dates[0]
        return release_dates

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
    def from_api_response(cls, response: Dict) -> Union["Source", List["Source"], None]:
        """
        Parses the FRED API response and returns a single Source or a list of Sources.
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
            return None
        if len(sources) == 1:
            return sources[0]
        return sources

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
    def from_api_response(cls, response: Dict) -> Union["Element", List["Element"], None]:
        """
        Parses the FRED API response and returns a single Element or a list of Elements.
        """
        if "elements" not in response:
            raise ValueError("Invalid API response: Missing 'elements' field")
        elements = []
        def process_element(element_data: Dict) -> "Element":
            children_list = []
            for child_data in element_data.get("children", []):
                child_resp = {"elements": {str(child_data["element_id"]): child_data}}
                child_result = cls.from_api_response(child_resp)
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
            return None
        if len(elements) == 1:
            return elements[0]
        return elements

@dataclass
class VintageDate:
    """
    A class used to represent a VintageDate.
    """
    vintage_date: str

    @classmethod
    def from_api_response(cls, response: Dict) -> Union["VintageDate", List["VintageDate"], None]:
        """
        Parses the FRED API response and returns a single VintageDate or a list of VintageDates.
        """
        if "vintage_dates" not in response:
            raise ValueError("Invalid API response: Missing 'vintage_dates' field")
        vintage_dates = [
            cls(vintage_date=date)
            for date in response["vintage_dates"]
        ]
        if not vintage_dates:
            return None
        if len(vintage_dates) == 1:
            return vintage_dates[0]
        return vintage_dates

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
    def from_api_response(cls, response: Dict) -> Union["SeriesGroup", List["SeriesGroup"], None]:
        """
        Parses the FRED API response and returns a single SeriesGroup or a list of SeriesGroups.
        """
        if "series_group" not in response:
            raise ValueError("Invalid API response: Missing 'series_group' field")
        if isinstance(response["series_group"], dict):
            series_group_data = response["series_group"]
            return cls(
                title=series_group_data["title"],
                region_type=series_group_data["region_type"],
                series_group=series_group_data["series_group"],
                season=series_group_data["season"],
                units=series_group_data["units"],
                frequency=series_group_data["frequency"],
                min_date=series_group_data["min_date"],
                max_date=series_group_data["max_date"]
            )
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
            for series_group in response["series_group"]
        ]
        if not series_groups:
            return None
        if len(series_groups) == 1:
            return series_groups[0]
        return series_groups
