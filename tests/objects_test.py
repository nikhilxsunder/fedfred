# filepath: /test/fred_data_test.py
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
Comprehensive unit tests for the fred_data module.
"""

from fedfred.objects import Category, Series, Tag, Release, ReleaseDate, Source, Element, VintageDate, SeriesGroup

def test_category_to_object():
    response = {
        "categories": [
            {"id": 1, "name": "Category 1", "parent_id": None},
            {"id": 2, "name": "Category 2", "parent_id": 1}
        ]
    }
    categories = Category.to_object(response)
    assert isinstance(categories, list)
    assert isinstance(categories[0], Category)
    assert len(categories) == 2
    assert categories[0].id == 1
    assert categories[1].parent_id == 1

def test_series_to_object():
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
    series = Series.to_object(response)
    assert isinstance(series, list)
    assert isinstance(series[0], Series)
    assert series[0].id == "S1"
    assert series[0].frequency == "Monthly"

def test_tag_to_object():
    response = {
        "tags": [
            {"name": "Tag1", "group_id": "G1", "created": "2020-01-01", "popularity": 10, "series_count": 5}
        ]
    }
    tag = Tag.to_object(response)
    assert isinstance(tag, list)
    assert isinstance(tag[0], Tag)
    assert tag[0].name == "Tag1"
    assert tag[0].group_id == "G1"

def test_release_to_object():
    response = {
        "releases": [
            {"id": 1, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "name": "Release 1", "press_release": True}
        ]
    }
    release = Release.to_object(response)
    assert isinstance(release, list)
    assert isinstance(release[0], Release)
    assert release[0].id == 1
    assert release[0].name == "Release 1"

def test_release_date_to_object():
    response = {
        "release_dates": [
            {"release_id": 1, "date": "2020-01-01"}
        ]
    }
    release_date = ReleaseDate.to_object(response)
    assert isinstance(release_date, list)
    assert isinstance(release_date[0], ReleaseDate)
    assert release_date[0].release_id == 1
    assert release_date[0].date == "2020-01-01"

def test_source_to_object():
    response = {
        "sources": [
            {"id": 1, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "name": "Source 1"}
        ]
    }
    source = Source.to_object(response)
    assert isinstance(source, list)
    assert isinstance(source[0], Source)
    assert source[0].id == 1
    assert source[0].name == "Source 1"

def test_element_to_object():
    response = {
        "elements": {
            "1": {
                "element_id": 1, "release_id": 1, "series_id": "S1", "parent_id": 0, "line": "Line 1", "type": "Type 1",
                "name": "Element 1", "level": "Level 1", "children": []
            }
        }
    }
    element = Element.to_object(response)
    assert isinstance(element, list)
    assert isinstance(element[0], Element)
    assert element[0].element_id == 1
    assert element[0].name == "Element 1"

def test_vintage_date_to_object():
    response = {
        "vintage_dates": ["2020-01-01"]
    }
    vintage_date = VintageDate.to_object(response)
    assert isinstance(vintage_date, list)
    assert isinstance(vintage_date[0], VintageDate)
    assert vintage_date[0].vintage_date == "2020-01-01"

def test_series_group_to_object():
    response = {
        "series_group": {
            "title": "Group 1",
            "region_type": "Region 1",
            "series_group": "Group 1",
            "season": "Season 1",
            "units": "Units",
            "frequency": "Monthly",
            "min_date": "2020-01-01",
            "max_date": "2020-12-31"
        }
    }
    series_group = SeriesGroup.to_object(response)
    assert isinstance(series_group, list)
    assert isinstance(series_group[0], SeriesGroup)
    assert series_group[0].title == "Group 1"
    assert series_group[0].region_type == "Region 1"
