from typing import Optional, List, Dict, Union, Any
from dataclasses import dataclass

@dataclass
class Category:
    id: int
    name: str
    parent_id: Optional[int]
    def __init__(self,
                 id: int,
                 name: str,
                 parent_id: Optional[int] = None) -> None: ...
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> Union["Category", List["Category"], None]: ...

@dataclass
class Series:
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
    group_popularity: Optional[int]
    notes: Optional[str]
    def __init__(self,
                id: str,
                title: str,
                observation_start: str,
                observation_end: str,
                frequency: str,
                frequency_short: str,
                units: str,
                units_short: str,
                seasonal_adjustment: str,
                seasonal_adjustment_short: str,
                last_updated: str,
                popularity: int,
                group_popularity: Optional[int]=None,
                notes: Optional[str]=None) -> None: ...
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> Union["Series", List["Series"], None]: ...

@dataclass
class Tag:
    name: str
    group_id: str
    created: str
    popularity: int
    series_count: int
    notes: Optional[str]
    def __init__(self,
                name: str,
                group_id: str,
                created: str,
                popularity: int,
                series_count: int,
                notes: Optional[str]=None) -> None: ...
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> Union["Tag", List["Tag"], None]: ...

@dataclass
class Release:
    id: int
    realtime_start: str
    realtime_end: str
    name: str
    press_release: bool
    link: Optional[str]
    notes: Optional[str]
    def __init__(self,
                id: int,
                realtime_start: str,
                realtime_end: str,
                name: str,
                press_release: bool,
                link: Optional[str]=None,
                notes: Optional[str]=None) -> None: ...
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> Union["Release", List["Release"], None]: ...

@dataclass
class ReleaseDate:
    release_id: int
    date: str
    release_name: Optional[str]
    def __init__(self,
                release_id: int,
                date: str,
                release_name: Optional[str]=None) -> None: ...
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> Union["ReleaseDate", List["ReleaseDate"], None]: ...

@dataclass
class Source:
    id: int
    realtime_start: str
    realtime_end: str
    name: str
    link: Optional[str]
    notes: Optional[str]
    def __init__(self,
                id: int,
                realtime_start: str,
                realtime_end: str,
                name: str,
                link: Optional[str]=None,
                notes: Optional[str]=None) -> None: ...
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> Union["Source", List["Source"], None]: ...

@dataclass
class Element:
    element_id: int
    release_id: int
    series_id: str
    parent_id: int
    line: str
    type: str
    name: str
    level: str
    children: Optional[List["Element"]]
    def __init__(self,
                element_id: int,
                release_id: int,
                series_id: str,
                parent_id: int,
                line: str,
                type: str,
                name: str,
                level: str,
                children: Optional[List["Element"]]=None) -> None: ...
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> Union["Element", List["Element"], None]: ...

@dataclass
class VintageDate:
    vintage_date: str
    def __init__(self, vintage_date: str) -> None: ...
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> Union["VintageDate", List["VintageDate"], None]: ...

@dataclass
class SeriesGroup:
    title: str
    region_type: str
    series_group: str
    season: str
    units: str
    frequency: str
    min_date: str
    max_date: str
    def __init__(self,
                title: str,
                region_type: str,
                series_group: str,
                season: str,
                units: str,
                frequency: str,
                min_date: str,
                max_date: str) -> None: ...
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> Union["SeriesGroup", List["SeriesGroup"], None]: ...
