"""
Comprehensive unit tests for the fred_data module.
"""
from fedfred.fred_data import Category, Series, Tag, Release, ReleaseDate, Source, Element, VintageDate, SeriesGroup

def test_category_from_api_response():
    response = {
        "categories": [
            {"id": 1, "name": "Category 1", "parent_id": None},
            {"id": 2, "name": "Category 2", "parent_id": 1}
        ]
    }
    categories = Category.from_api_response(response)
    assert isinstance(categories, list)
    assert len(categories) == 2
    assert categories[0].id == 1
    assert categories[1].parent_id == 1

def test_series_from_api_response():
    response = {
        "seriess": [
            {
                "id": "S1", "title": "Series 1", "observation_start": "2020-01-01", "observation_end": "2020-12-31",
                "frequency": "Monthly", "frequency_short": "M", "units": "Units", "units_short": "U",
                "seasonal_adjustment": "None", "seasonal_adjustment_short": "NSA", "last_updated": "2021-01-01",
                "popularity": 100
            }
        ]
    }
    series = Series.from_api_response(response)
    assert isinstance(series, Series)
    assert series.id == "S1"
    assert series.frequency == "Monthly"

def test_tag_from_api_response():
    response = {
        "tags": [
            {"name": "Tag1", "group_id": "G1", "created": "2020-01-01", "popularity": 10, "series_count": 5}
        ]
    }
    tag = Tag.from_api_response(response)
    assert isinstance(tag, Tag)
    assert tag.name == "Tag1"
    assert tag.group_id == "G1"

def test_release_from_api_response():
    response = {
        "releases": [
            {"id": 1, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "name": "Release 1", "press_release": True}
        ]
    }
    release = Release.from_api_response(response)
    assert isinstance(release, Release)
    assert release.id == 1
    assert release.name == "Release 1"

def test_release_date_from_api_response():
    response = {
        "release_dates": [
            {"release_id": 1, "date": "2020-01-01"}
        ]
    }
    release_date = ReleaseDate.from_api_response(response)
    assert isinstance(release_date, ReleaseDate)
    assert release_date.release_id == 1
    assert release_date.date == "2020-01-01"

def test_source_from_api_response():
    response = {
        "sources": [
            {"id": 1, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "name": "Source 1"}
        ]
    }
    source = Source.from_api_response(response)
    assert isinstance(source, Source)
    assert source.id == 1
    assert source.name == "Source 1"

def test_element_from_api_response():
    response = {
        "elements": {
            "1": {
                "element_id": 1, "release_id": 1, "series_id": "S1", "parent_id": 0, "line": "Line 1", "type": "Type 1",
                "name": "Element 1", "level": "Level 1", "children": []
            }
        }
    }
    element = Element.from_api_response(response)
    assert isinstance(element, Element)
    assert element.element_id == 1
    assert element.name == "Element 1"

def test_vintage_date_from_api_response():
    response = {
        "vintage_dates": ["2020-01-01"]
    }
    vintage_date = VintageDate.from_api_response(response)
    assert isinstance(vintage_date, VintageDate)
    assert vintage_date.vintage_date == "2020-01-01"

def test_series_group_from_api_response():
    response = {
        "series_group": {
            "title": "Group 1", "region_type": "Region 1", "series_group": "Group 1", "season": "Season 1",
            "units": "Units", "frequency": "Monthly", "min_date": "2020-01-01", "max_date": "2020-12-31"
        }
    }
    series_group = SeriesGroup.from_api_response(response)
    assert isinstance(series_group, SeriesGroup)
    assert series_group.title == "Group 1"
    assert series_group.region_type == "Region 1"
