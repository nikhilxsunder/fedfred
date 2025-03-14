"""
Comprehensive unit tests for the fedfred module.
"""
from unittest.mock import patch
import asyncio
import pytest
import pandas as pd
from fedfred import FredAPI
from fedfred.fred_data import Category, Series, Tag, Release, ReleaseDate, Source, Element, VintageDate, SeriesGroup

# FredAPI tests
@pytest.fixture
def fred_api():
    return FredAPI(api_key="test_api_key")

# Category tests
def test_get_category(fred_api):
    # Mock the API response
    mock_response = {
        "categories": [
            {
                "id": 125,
                "name": "Trade Balance",
                "parent_id": None
            }
        ]
    }

    # Test valid category ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        category = fred_api.get_category(125)
        assert isinstance(category, Category)
        assert category.id == 125
        assert category.name == "Trade Balance"
        assert category.parent_id is None

    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category(125)

def test_get_category_children(fred_api):
    # Mock the API response
    mock_response = {
        "categories": [
            {
                "id": 126,
                "name": "Exports",
                "parent_id": 125
            },
            {
                "id": 127,
                "name": "Imports",
                "parent_id": 125
            }
        ]
    }

    # Test valid category ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        children = fred_api.get_category_children(125)
        assert isinstance(children, list)
        assert len(children) == 2
        assert all(isinstance(child, Category) for child in children)
        assert children[0].id == 126
        assert children[0].name == "Exports"
        assert children[0].parent_id == 125

    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category_children(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category_children(125)

def test_get_category_related(fred_api):
    # Mock the API response
    mock_response = {
        "categories": [
            {
                "id": 128,
                "name": "Related Category 1",
                "parent_id": None
            },
            {
                "id": 129,
                "name": "Related Category 2",
                "parent_id": None
            }
        ]
    }

    # Test valid category ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        related = fred_api.get_category_related(125)
        assert isinstance(related, list)
        assert len(related) == 2
        assert all(isinstance(category, Category) for category in related)
        assert related[0].id == 128
        assert related[0].name == "Related Category 1"
        assert related[0].parent_id is None

    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category_related(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category_related(125)

def test_get_category_series(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80,
                "group_popularity": 1,
                "notes": None
            }
        ]
    }

    # Test valid category ID with a single series
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_category_series(125)
        if isinstance(series, list):
            assert len(series) == 1
            assert all(isinstance(s, Series) for s in series)
            assert series[0].id == "GNPCA"
            assert series[0].title == "Real Gross National Product"
        else:
            assert isinstance(series, Series)
            assert series.id == "GNPCA"
            assert series.title == "Real Gross National Product"

    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category_series(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category_series(125)

def test_get_category_tags(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid category ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tags = fred_api.get_category_tags(125)
        if isinstance(tags, list):
            assert isinstance(tags, list)
            assert len(tags) == 2
            assert all(isinstance(tag, Tag) for tag in tags)
            assert tags[0].name == "tag1"
            assert tags[0].group_id == "group1"
            assert tags[0].created == "2021-01-01"
            assert tags[0].popularity == 10
            assert tags[0].series_count == 5
            assert tags[0].notes == "Some notes"
        else:
            assert isinstance(tags, Tag)
            assert tags.name == "tag1"
            assert tags.group_id == "group1"
            assert tags.created == "2021-01-01"
            assert tags.popularity == 10
            assert tags.series_count == 5
            assert tags.notes == "Some notes"
    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category_tags(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category_tags(125)

def test_get_category_related_tags(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "related_tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "related_tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid category ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        related_tags = fred_api.get_category_related_tags(125)
        assert isinstance(related_tags, list)
        assert len(related_tags) == 2
        assert all(isinstance(tag, Tag) for tag in related_tags)
        assert related_tags[0].name == "related_tag1"
        assert related_tags[0].group_id == "group1"
        assert related_tags[0].created == "2021-01-01"
        assert related_tags[0].popularity == 10
        assert related_tags[0].series_count == 5
        assert related_tags[0].notes == "Some notes"

    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category_related_tags(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category_related_tags(125)

# Releases tests
def test_get_releases(fred_api):
    # Mock the API response
    mock_response = {
        "releases": [
            {
                "id": 1,
                "name": "Release 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 1",
                "link": "http://example.com/release1",
                "notes": "Some notes"
            },
            {
                "id": 2,
                "name": "Release 2",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 2",
                "link": "http://example.com/release2",
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        releases = fred_api.get_releases()
        if isinstance(releases, list):
            assert len(releases) == 2
            assert all(isinstance(release, Release) for release in releases)
            assert releases[0].id == 1
            assert releases[0].realtime_start == "2013-08-13"
            assert releases[0].realtime_end == "2013-08-13"
            assert releases[0].name == "Release 1"
            assert releases[0].press_release == "Press Release 1"
            assert releases[0].link == "http://example.com/release1"
            assert releases[0].notes == "Some notes"
        else:
            assert isinstance(releases, Release)
            assert releases.id == 1
            assert releases.name == "Release 1"
            assert releases.realtime_start == "2013-08-13"
            assert releases.realtime_end == "2013-08-13"
            assert releases.press_release == "Press Release 1"
            assert releases.link == "http://example.com/release1"
            assert releases.notes == "Some notes"
    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_releases()

def test_get_releases_dates(fred_api):
    # Mock the API response
    mock_response = {
        "release_dates": [
            {
                "release_id": 1,
                "release_name": "Release 1",
                "date": "2013-08-13",
            },
            {
                "release_id": 2,
                "release_name": "Release 2",
                "date": "2013-08-13",
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        release_dates = fred_api.get_releases_dates()
        if isinstance(release_dates, list):
            assert len(release_dates) == 2
            assert all(isinstance(release_date, ReleaseDate) for release_date in release_dates)
            assert release_dates[0].release_id == 1
            assert release_dates[0].release_name == "Release 1"
            assert release_dates[0].date == "2013-08-13"
        else:
            assert isinstance(release_dates, ReleaseDate)
            assert release_dates.release_id == 1
            assert release_dates.release_name == "Release 1"
            assert release_dates.date == "2013-08-13"
    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_releases_dates()

def test_get_release(fred_api):
    # Mock the API response
    mock_response = {
        "releases": [
            {
                "id": 1,
                "name": "Release 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 1",
                "link": "http://example.com/release1",
                "notes": "Some notes"
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        release = fred_api.get_release(1)
        assert isinstance(release, Release)
        assert release.id == 1
        assert release.realtime_start == "2013-08-13"
        assert release.realtime_end == "2013-08-13"
        assert release.name == "Release 1"
        assert release.press_release == "Press Release 1"
        assert release.link == "http://example.com/release1"
        assert release.notes == "Some notes"

    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release(1)

def test_get_release_dates(fred_api):
    # Mock the API response
    mock_response = {
        "release_dates": [
            {
                "release_id": 1,
                "release_name": "Release 1",
                "date": "2013-08-13",
            },
            {
                "release_id": 2,
                "release_name": "Release 2",
                "date": "2013-08-13",
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        release_dates = fred_api.get_release_dates(1)
        assert isinstance(release_dates, list)
        assert len(release_dates) == 2
        assert all(isinstance(release_date, ReleaseDate) for release_date in release_dates)
        assert release_dates[0].release_id == 1
        assert release_dates[0].release_name == "Release 1"
        assert release_dates[0].date == "2013-08-13"

    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_dates(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_dates(1)

def test_get_release_series(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80,
                "group_popularity": 1,
                "notes": None
            }
        ]
    }

    # Test valid release ID with a single series
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_release_series(1)
        if isinstance(series, list):
            assert len(series) == 1
            assert all(isinstance(s, Series) for s in series)
            assert series[0].id == "GNPCA"
            assert series[0].title == "Real Gross National Product"
        else:
            assert isinstance(series, Series)
            assert series.id == "GNPCA"
            assert series.title == "Real Gross National Product"

    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_series(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_series(1)

def test_get_release_sources(fred_api):
    # Mock the API response
    mock_response = {
        "sources": [
            {
                "id": 1,
                "name": "Source 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "link": "http://example.com/source1",
                "notes": "Some notes"
            },
            {
                "id": 2,
                "name": "Source 2",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "link": "http://example.com/source2",
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        sources = fred_api.get_release_sources(1)
        if isinstance(sources, list):
            assert len(sources) == 2
            assert all(isinstance(source, Source) for source in sources)
            assert sources[0].id == 1
            assert sources[0].realtime_start == "2013-08-13"
            assert sources[0].realtime_end == "2013-08-13"
            assert sources[0].name == "Source 1"
            assert sources[0].link == "http://example.com/source1"
            assert sources[0].notes == "Some notes"
        else:
            assert isinstance(sources, Source)
            assert sources.id == 1
            assert sources.realtime_start == "2013-08-13"
            assert sources.realtime_end == "2013-08-13"
            assert sources.name == "Source 1"
            assert sources.link == "http://example.com/source1"
            assert sources.notes == "Some notes"
    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_sources(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_sources(1)

def test_get_release_tags(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tags = fred_api.get_release_tags(1)
        if isinstance(tags, list):
            assert len(tags) == 2
            assert all(isinstance(tag, Tag) for tag in tags)
            assert tags[0].name == "tag1"
            assert tags[0].group_id == "group1"
            assert tags[0].created == "2021-01-01"
            assert tags[0].popularity == 10
            assert tags[0].series_count == 5
            assert tags[0].notes == "Some notes"
        else:
            assert isinstance(tags, Tag)
            assert tags.name == "tag1"
            assert tags.group_id == "group1"
            assert tags.created == "2021-01-01"
            assert tags.popularity == 10
            assert tags.series_count == 5
            assert tags.notes == "Some notes"
    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_tags(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_tags(1)

def test_get_release_related_tags(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "related_tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "related_tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        related_tags = fred_api.get_release_related_tags(1)
        if isinstance(related_tags, list):
            assert len(related_tags) == 2
            assert all(isinstance(tag, Tag) for tag in related_tags)
            assert related_tags[0].name == "related_tag1"
            assert related_tags[0].group_id == "group1"
            assert related_tags[0].created == "2021-01-01"
            assert related_tags[0].popularity == 10
            assert related_tags[0].series_count == 5
            assert related_tags[0].notes == "Some notes"
        else:
            assert isinstance(related_tags, Tag)
            assert related_tags.name == "related_tag1"
            assert related_tags.group_id == "group1"
            assert related_tags.created == "2021-01-01"
            assert related_tags.popularity == 10
            assert related_tags.series_count == 5
            assert related_tags.notes == "Some notes"
    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_related_tags(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_related_tags(1)

def test_get_release_tables(fred_api):
    # Mock the API response
    mock_response = {
        "elements": {
            "12887": {
            "element_id": 12887,
            "release_id": 53,
            "series_id": "DGDSRL1A225NBEA",
            "parent_id": 12886,
            "line": "3",
            "type": "series",
            "name": "Goods",
            "level": "1",
            "children": [
                {
                "element_id": 12888,
                "release_id": 53,
                "series_id": "DDURRL1A225NBEA",
                "parent_id": 12887,
                "line": "4",
                "type": "series",
                "name": "Durable goods",
                "level": "2",
                "children": [

                ]
                },
                {
                "element_id": 12889,
                "release_id": 53,
                "series_id": "DNDGRL1A225NBEA",
                "parent_id": 12887,
                "line": "5",
                "type": "series",
                "name": "Nondurable goods",
                "level": "2",
                "children": [

                ]
                }
            ]
            },
            "12888": {
            "element_id": 12888,
            "release_id": 53,
            "series_id": "DDURRL1A225NBEA",
            "parent_id": 12887,
            "line": "4",
            "type": "series",
            "name": "Durable goods",
            "level": "2",
            "children": [

            ]
            }
        }
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        elements = fred_api.get_release_tables(1)
        if isinstance(elements, list):
            assert len(elements) == 2
            assert all(isinstance(element, Element) for element in elements)
            assert elements[0].element_id == 12887
            assert elements[0].release_id == 53
            assert elements[0].series_id == "DGDSRL1A225NBEA"
            assert elements[0].parent_id == 12886
            assert elements[0].line == "3"
            assert elements[0].type == "series"
            assert elements[0].name == "Goods"
            assert elements[0].level == "1"
            assert len(elements[0].children) == 2
            assert elements[0].children[0].element_id == 12888
            assert elements[0].children[0].release_id == 53
            assert elements[0].children[0].series_id == "DDURRL1A225NBEA"
            assert elements[0].children[0].parent_id == 12887
            assert elements[0].children[0].line == "4"
            assert elements[0].children[0].type == "series"
            assert elements[0].children[0].name == "Durable goods"
            assert elements[0].children[0].level == "2"
        else:
            assert isinstance(elements, Element)
            assert elements.element_id == 12887
            assert elements.release_id == 53
            assert elements.series_id == "DGDSRL1A225NBEA"
            assert elements.parent_id == 12886
            assert elements.line == "3"
            assert elements.type == "series"
            assert elements.name == "Goods"
            assert elements.level == "1"
            assert len(elements.children) == 2
            assert elements.children[0].element_id == 12888
            assert elements.children[0].release_id == 53
            assert elements.children[0].series_id == "DDURRL1A225NBEA"
            assert elements.children[0].parent_id == 12887
            assert elements.children[0].line == "4"
            assert elements.children[0].type == "series"
            assert elements.children[0].name == "Durable goods"
            assert elements.children[0].level == "2"
    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_tables(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_tables(1)

# Series tests
def test_get_series(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80,
                "group_popularity": 1,
                "notes": None
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_series("GNPCA")
        assert isinstance(series, Series)
        assert series.id == "GNPCA"
        assert series.realtime_start == "2013-08-14"
        assert series.realtime_end == "2013-08-14"
        assert series.title == "Real Gross National Product"
        assert series.observation_start == "1947-01-01"
        assert series.observation_end == "2021-01-01"
        assert series.frequency == "Annual"
        assert series.frequency_short == "A"
        assert series.units == "Billions of Chained 2012 Dollars"
        assert series.units_short == "Bil. of Chn. 2012 $"
        assert series.seasonal_adjustment == "Not Seasonally Adjusted"
        assert series.seasonal_adjustment_short == "NSA"
        assert series.last_updated == "2021-03-25 07:51:36-05"
        assert series.popularity == 80
        assert series.group_popularity == 1
        assert series.notes is None

    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series("GNPCA")

def test_get_series_categories(fred_api):
    # Mock the API response
    mock_response = {
        "categories": [
            {
                "id": 125,
                "name": "Trade Balance",
                "parent_id": None
            },
            {
                "id": 126,
                "name": "Exports",
                "parent_id": 125
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        categories = fred_api.get_series_categories("GNPCA")
        assert isinstance(categories, list)
        assert len(categories) == 2
        assert all(isinstance(category, Category) for category in categories)
        assert categories[0].id == 125
        assert categories[0].name == "Trade Balance"
        assert categories[0].parent_id is None

    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series_categories("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_categories("GNPCA")

# Pandas
def test_get_series_observations_pandas(fred_api):
    # Mock the API response
    mock_response = {
        "observations": [
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2021-01-01",
                "value": 100.0
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2021-01-02",
                "value": 200.0
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        observations = fred_api.get_series_observations("GNPCA")
        assert isinstance(observations, pd.DataFrame)
        assert len(observations) == 2
        assert observations.index[0] == pd.Timestamp("2021-01-01")
        assert observations.index[1] == pd.Timestamp("2021-01-02")
        assert observations.iloc[0]["value"] == 100.0
        assert observations.iloc[1]["value"] == 200.0
    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series_observations("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_observations("GNPCA")

#### Add polars method in next revision

def test_get_series_release(fred_api):
    # Mock the API response
    mock_response = {
        "releases": [
            {
                "id": 1,
                "name": "Release 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 1",
                "link": "http://example.com/release1",
                "notes": "Some notes"
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        release = fred_api.get_series_release("GNPCA")
        assert isinstance(release, Release)
        assert release.id == 1
        assert release.realtime_start == "2013-08-13"
        assert release.realtime_end == "2013-08-13"
        assert release.name == "Release 1"
        assert release.press_release == "Press Release 1"
        assert release.link == "http://example.com/release1"
        assert release.notes == "Some notes"

    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series_release("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_release("GNPCA")

def test_get_series_search(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80,
                "group_popularity": 1,
                "notes": None
            }
        ]
    }

    # Test valid search text
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_series_search("Real Gross National Product")
        assert isinstance(series, Series)
        assert series.id == "GNPCA"
        assert series.realtime_start == "2013-08-14"
        assert series.realtime_end == "2013-08-14"
        assert series.title == "Real Gross National Product"
        assert series.observation_start == "1947-01-01"
        assert series.observation_end == "2021-01-01"
        assert series.frequency == "Annual"
        assert series.frequency_short == "A"
        assert series.units == "Billions of Chained 2012 Dollars"
        assert series.units_short == "Bil. of Chn. 2012 $"
        assert series.seasonal_adjustment == "Not Seasonally Adjusted"
        assert series.seasonal_adjustment_short == "NSA"
        assert series.last_updated == "2021-03-25 07:51:36-05"
        assert series.popularity == 80
        assert series.group_popularity == 1
        assert series.notes is None

    # Test invalid search text
    with pytest.raises(ValueError):
        fred_api.get_series_search("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_search("Real Gross National Product")

def test_get_series_search_tags(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid search text
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tags = fred_api.get_series_search_tags("Real Gross National Product")
        assert isinstance(tags, list)
        assert len(tags) == 2
        assert all(isinstance(tag, Tag) for tag in tags)
        assert tags[0].name == "tag1"
        assert tags[0].group_id == "group1"
        assert tags[0].created == "2021-01-01"
        assert tags[0].popularity == 10
        assert tags[0].series_count == 5
        assert tags[0].notes == "Some notes"

    # Test invalid search text
    with pytest.raises(ValueError):
        fred_api.get_series_search_tags("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_search_tags("Real Gross National Product")

def test_get_series_search_related_tags(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "related_tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "related_tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid search text
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        related_tags = fred_api.get_series_search_related_tags("Real Gross National Product")
        assert isinstance(related_tags, list)
        assert len(related_tags) == 2
        assert all(isinstance(tag, Tag) for tag in related_tags)
        assert related_tags[0].name == "related_tag1"
        assert related_tags[0].group_id == "group1"
        assert related_tags[0].created == "2021-01-01"
        assert related_tags[0].popularity == 10
        assert related_tags[0].series_count == 5
        assert related_tags[0].notes == "Some notes"

    # Test invalid search text
    with pytest.raises(ValueError):
        fred_api.get_series_search_related_tags("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_search_related_tags("Real Gross National Product")

def test_get_series_tags(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tags = fred_api.get_series_tags("GNPCA")
        assert isinstance(tags, list)
        assert len(tags) == 2
        assert all(isinstance(tag, Tag) for tag in tags)
        assert tags[0].name == "tag1"
        assert tags[0].group_id == "group1"
        assert tags[0].created == "2021-01-01"
        assert tags[0].popularity == 10
        assert tags[0].series_count == 5
        assert tags[0].notes == "Some notes"

    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series_tags("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_tags("GNPCA")

def test_get_series_updates(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_series_updates()
        assert isinstance(series, Series)
        assert series.id == "GNPCA"
        assert series.realtime_start == "2013-08-14"
        assert series.realtime_end == "2013-08-14"
        assert series.title == "Real Gross National Product"
        assert series.observation_start == "1947-01-01"
        assert series.observation_end == "2021-01-01"
        assert series.frequency == "Annual"
        assert series.frequency_short == "A"
        assert series.units == "Billions of Chained 2012 Dollars"
        assert series.units_short == "Bil. of Chn. 2012 $"
        assert series.seasonal_adjustment == "Not Seasonally Adjusted"
        assert series.seasonal_adjustment_short == "NSA"
        assert series.last_updated == "2021-03-25 07:51:36-05"
        assert series.popularity == 80

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_updates()

def test_get_series_vintage_dates(fred_api):
    # Mock the API response
    mock_response = {
        "vintage_dates": [
            "1958-12-21",
            "1959-02-19",
            "1959-07-19",
            "1960-02-16",
            "1960-07-22",
            "1961-02-19"
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        vintage_dates = fred_api.get_series_vintagedates("GNPCA")
        if isinstance(vintage_dates, list):
            assert len(vintage_dates) == 6
            assert all(isinstance(vintage_date, VintageDate) for vintage_date in vintage_dates)
            assert vintage_dates[0].vintage_date == "1958-12-21"
        else:
            assert isinstance(vintage_dates, VintageDate)
            assert vintage_dates.vintage_date == "1958-12-21"

    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series_vintagedates("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_vintagedates("GNPCA")

# Sources tests
def test_get_sources(fred_api):
    # Mock the API response
    mock_response = {
        "sources": [
            {
                "id": 1,
                "name": "Source 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "link": "http://example.com/source1",
                "notes": "Some notes"
            },
            {
                "id": 2,
                "name": "Source 2",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "link": "http://example.com/source2",
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid source ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        sources = fred_api.get_sources()
        assert isinstance(sources, list)
        assert len(sources) == 2
        assert all(isinstance(source, Source) for source in sources)
        assert sources[0].id == 1
        assert sources[0].realtime_start == "2013-08-13"
        assert sources[0].realtime_end == "2013-08-13"
        assert sources[0].name == "Source 1"
        assert sources[0].link == "http://example.com/source1"
        assert sources[0].notes == "Some notes"

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_sources()

def test_get_source(fred_api):
    # Mock the API response
    mock_response = {
        "sources": [
            {
                "id": 1,
                "name": "Source 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "link": "http://example.com/source1",
                "notes": "Some notes"
            }
        ]
    }

    # Test valid source ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        source = fred_api.get_source(1)
        assert isinstance(source, Source)
        assert source.id == 1
        assert source.realtime_start == "2013-08-13"
        assert source.realtime_end == "2013-08-13"
        assert source.name == "Source 1"
        assert source.link == "http://example.com/source1"
        assert source.notes == "Some notes"

    # Test invalid source ID
    with pytest.raises(ValueError):
        fred_api.get_source(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_source(1)

def test_get_source_releases(fred_api):
    # Mock the API response
    mock_response = {
        "releases": [
            {
                "id": 1,
                "name": "Release 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 1",
                "link": "http://example.com/release1",
                "notes": "Some notes"
            },
            {
                "id": 2,
                "name": "Release 2",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 2",
                "link": "http://example.com/release2",
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid source ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        releases = fred_api.get_source_releases(1)
        assert isinstance(releases, list)
        assert len(releases) == 2
        assert all(isinstance(release, Release) for release in releases)
        assert releases[0].id == 1
        assert releases[0].realtime_start == "2013-08-13"
        assert releases[0].realtime_end == "2013-08-13"
        assert releases[0].name == "Release 1"
        assert releases[0].press_release == "Press Release 1"
        assert releases[0].link == "http://example.com/release1"
        assert releases[0].notes == "Some notes"

    # Test invalid source ID
    with pytest.raises(ValueError):
        fred_api.get_source_releases(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_source_releases(1)

# Tags tests
def test_get_tags(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid tag ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tags = fred_api.get_tags()
        assert isinstance(tags, list)
        assert len(tags) == 2
        assert all(isinstance(tag, Tag) for tag in tags)
        assert tags[0].name == "tag1"
        assert tags[0].group_id == "group1"
        assert tags[0].created == "2021-01-01"
        assert tags[0].popularity == 10
        assert tags[0].series_count == 5
        assert tags[0].notes == "Some notes"

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_tags()

def test_related_get_tags(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            }
        ]
    }

    # Test valid tag ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tag = fred_api.get_related_tags("tag1")
        assert isinstance(tag, Tag)
        assert tag.name == "tag1"
        assert tag.group_id == "group1"
        assert tag.created == "2021-01-01"
        assert tag.popularity == 10
        assert tag.series_count == 5
        assert tag.notes == "Some notes"

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_related_tags("tag1")

def test_get_tags_series(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80
            }
        ]
    }

    # Test valid tag ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_tags_series("tag1")
        assert isinstance(series, Series)
        assert series.id == "GNPCA"
        assert series.realtime_start == "2013-08-14"
        assert series.realtime_end == "2013-08-14"
        assert series.title == "Real Gross National Product"
        assert series.observation_start == "1947-01-01"
        assert series.observation_end == "2021-01-01"
        assert series.frequency == "Annual"
        assert series.frequency_short == "A"
        assert series.units == "Billions of Chained 2012 Dollars"
        assert series.units_short == "Bil. of Chn. 2012 $"
        assert series.seasonal_adjustment == "Not Seasonally Adjusted"
        assert series.seasonal_adjustment_short == "NSA"
        assert series.last_updated == "2021-03-25 07:51:36-05"
        assert series.popularity == 80

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_tags_series("tag1")

#### add maps tests in next revision

# Async tests fix in next revision
async def test_get_category_async(fred_api):
    # Mock the API response
    mock_response = {
        "categories": [
            {
                "id": 125,
                "name": "Trade Balance",
                "parent_id": None
            }
        ]
    }

    # Test valid category ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        category = fred_api.get_category(125)
        assert isinstance(category, Category)
        assert category.id == 125
        assert category.name == "Trade Balance"
        assert category.parent_id is None

    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category(125)

async def test_get_category_children_async(fred_api):
    # Mock the API response
    mock_response = {
        "categories": [
            {
                "id": 126,
                "name": "Exports",
                "parent_id": 125
            },
            {
                "id": 127,
                "name": "Imports",
                "parent_id": 125
            }
        ]
    }

    # Test valid category ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        children = fred_api.get_category_children(125)
        assert isinstance(children, list)
        assert len(children) == 2
        assert all(isinstance(child, Category) for child in children)
        assert children[0].id == 126
        assert children[0].name == "Exports"
        assert children[0].parent_id == 125

    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category_children(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category_children(125)

async def test_get_category_related_async(fred_api):
    # Mock the API response
    mock_response = {
        "categories": [
            {
                "id": 128,
                "name": "Related Category 1",
                "parent_id": None
            },
            {
                "id": 129,
                "name": "Related Category 2",
                "parent_id": None
            }
        ]
    }

    # Test valid category ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        related = fred_api.get_category_related(125)
        assert isinstance(related, list)
        assert len(related) == 2
        assert all(isinstance(category, Category) for category in related)
        assert related[0].id == 128
        assert related[0].name == "Related Category 1"
        assert related[0].parent_id is None

    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category_related(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category_related(125)

async def test_get_category_series_async(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80,
                "group_popularity": 1,
                "notes": None
            }
        ]
    }

    # Test valid category ID with a single series
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_category_series(125)
        if isinstance(series, list):
            assert len(series) == 1
            assert all(isinstance(s, Series) for s in series)
            assert series[0].id == "GNPCA"
            assert series[0].title == "Real Gross National Product"
        else:
            assert isinstance(series, Series)
            assert series.id == "GNPCA"
            assert series.title == "Real Gross National Product"

    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category_series(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category_series(125)

async def test_get_category_tags_async(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid category ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tags = fred_api.get_category_tags(125)
        if isinstance(tags, list):
            assert isinstance(tags, list)
            assert len(tags) == 2
            assert all(isinstance(tag, Tag) for tag in tags)
            assert tags[0].name == "tag1"
            assert tags[0].group_id == "group1"
            assert tags[0].created == "2021-01-01"
            assert tags[0].popularity == 10
            assert tags[0].series_count == 5
            assert tags[0].notes == "Some notes"
        else:
            assert isinstance(tags, Tag)
            assert tags.name == "tag1"
            assert tags.group_id == "group1"
            assert tags.created == "2021-01-01"
            assert tags.popularity == 10
            assert tags.series_count == 5
            assert tags.notes == "Some notes"
    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category_tags(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category_tags(125)

async def test_get_category_related_tags_async(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "related_tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "related_tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid category ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        related_tags = fred_api.get_category_related_tags(125)
        assert isinstance(related_tags, list)
        assert len(related_tags) == 2
        assert all(isinstance(tag, Tag) for tag in related_tags)
        assert related_tags[0].name == "related_tag1"
        assert related_tags[0].group_id == "group1"
        assert related_tags[0].created == "2021-01-01"
        assert related_tags[0].popularity == 10
        assert related_tags[0].series_count == 5
        assert related_tags[0].notes == "Some notes"

    # Test invalid category ID
    with pytest.raises(ValueError):
        fred_api.get_category_related_tags(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_category_related_tags(125)

# Releases tests
async def test_get_releases_async(fred_api):
    # Mock the API response
    mock_response = {
        "releases": [
            {
                "id": 1,
                "name": "Release 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 1",
                "link": "http://example.com/release1",
                "notes": "Some notes"
            },
            {
                "id": 2,
                "name": "Release 2",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 2",
                "link": "http://example.com/release2",
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        releases = fred_api.get_releases()
        if isinstance(releases, list):
            assert len(releases) == 2
            assert all(isinstance(release, Release) for release in releases)
            assert releases[0].id == 1
            assert releases[0].realtime_start == "2013-08-13"
            assert releases[0].realtime_end == "2013-08-13"
            assert releases[0].name == "Release 1"
            assert releases[0].press_release == "Press Release 1"
            assert releases[0].link == "http://example.com/release1"
            assert releases[0].notes == "Some notes"
        else:
            assert isinstance(releases, Release)
            assert releases.id == 1
            assert releases.name == "Release 1"
            assert releases.realtime_start == "2013-08-13"
            assert releases.realtime_end == "2013-08-13"
            assert releases.press_release == "Press Release 1"
            assert releases.link == "http://example.com/release1"
            assert releases.notes == "Some notes"
    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_releases()

async def test_get_releases_dates_async(fred_api):
    # Mock the API response
    mock_response = {
        "release_dates": [
            {
                "release_id": 1,
                "release_name": "Release 1",
                "date": "2013-08-13",
            },
            {
                "release_id": 2,
                "release_name": "Release 2",
                "date": "2013-08-13",
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        release_dates = fred_api.get_releases_dates()
        if isinstance(release_dates, list):
            assert len(release_dates) == 2
            assert all(isinstance(release_date, ReleaseDate) for release_date in release_dates)
            assert release_dates[0].release_id == 1
            assert release_dates[0].release_name == "Release 1"
            assert release_dates[0].date == "2013-08-13"
        else:
            assert isinstance(release_dates, ReleaseDate)
            assert release_dates.release_id == 1
            assert release_dates.release_name == "Release 1"
            assert release_dates.date == "2013-08-13"
    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_releases_dates()

async def test_get_release_async(fred_api):
    # Mock the API response
    mock_response = {
        "releases": [
            {
                "id": 1,
                "name": "Release 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 1",
                "link": "http://example.com/release1",
                "notes": "Some notes"
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        release = fred_api.get_release(1)
        assert isinstance(release, Release)
        assert release.id == 1
        assert release.realtime_start == "2013-08-13"
        assert release.realtime_end == "2013-08-13"
        assert release.name == "Release 1"
        assert release.press_release == "Press Release 1"
        assert release.link == "http://example.com/release1"
        assert release.notes == "Some notes"

    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release(1)

async def test_get_release_dates_async(fred_api):
    # Mock the API response
    mock_response = {
        "release_dates": [
            {
                "release_id": 1,
                "release_name": "Release 1",
                "date": "2013-08-13",
            },
            {
                "release_id": 2,
                "release_name": "Release 2",
                "date": "2013-08-13",
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        release_dates = fred_api.get_release_dates(1)
        assert isinstance(release_dates, list)
        assert len(release_dates) == 2
        assert all(isinstance(release_date, ReleaseDate) for release_date in release_dates)
        assert release_dates[0].release_id == 1
        assert release_dates[0].release_name == "Release 1"
        assert release_dates[0].date == "2013-08-13"

    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_dates(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_dates(1)

async def test_get_release_series_async(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80,
                "group_popularity": 1,
                "notes": None
            }
        ]
    }

    # Test valid release ID with a single series
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_release_series(1)
        if isinstance(series, list):
            assert len(series) == 1
            assert all(isinstance(s, Series) for s in series)
            assert series[0].id == "GNPCA"
            assert series[0].title == "Real Gross National Product"
        else:
            assert isinstance(series, Series)
            assert series.id == "GNPCA"
            assert series.title == "Real Gross National Product"

    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_series(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_series(1)

async def test_get_release_sources_async(fred_api):
    # Mock the API response
    mock_response = {
        "sources": [
            {
                "id": 1,
                "name": "Source 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "link": "http://example.com/source1",
                "notes": "Some notes"
            },
            {
                "id": 2,
                "name": "Source 2",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "link": "http://example.com/source2",
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        sources = fred_api.get_release_sources(1)
        if isinstance(sources, list):
            assert len(sources) == 2
            assert all(isinstance(source, Source) for source in sources)
            assert sources[0].id == 1
            assert sources[0].realtime_start == "2013-08-13"
            assert sources[0].realtime_end == "2013-08-13"
            assert sources[0].name == "Source 1"
            assert sources[0].link == "http://example.com/source1"
            assert sources[0].notes == "Some notes"
        else:
            assert isinstance(sources, Source)
            assert sources.id == 1
            assert sources.realtime_start == "2013-08-13"
            assert sources.realtime_end == "2013-08-13"
            assert sources.name == "Source 1"
            assert sources.link == "http://example.com/source1"
            assert sources.notes == "Some notes"
    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_sources(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_sources(1)

async def test_get_release_tags_async(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tags = fred_api.get_release_tags(1)
        if isinstance(tags, list):
            assert len(tags) == 2
            assert all(isinstance(tag, Tag) for tag in tags)
            assert tags[0].name == "tag1"
            assert tags[0].group_id == "group1"
            assert tags[0].created == "2021-01-01"
            assert tags[0].popularity == 10
            assert tags[0].series_count == 5
            assert tags[0].notes == "Some notes"
        else:
            assert isinstance(tags, Tag)
            assert tags.name == "tag1"
            assert tags.group_id == "group1"
            assert tags.created == "2021-01-01"
            assert tags.popularity == 10
            assert tags.series_count == 5
            assert tags.notes == "Some notes"
    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_tags(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_tags(1)

async def test_get_release_related_tags_async(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "related_tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "related_tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        related_tags = fred_api.get_release_related_tags(1)
        if isinstance(related_tags, list):
            assert len(related_tags) == 2
            assert all(isinstance(tag, Tag) for tag in related_tags)
            assert related_tags[0].name == "related_tag1"
            assert related_tags[0].group_id == "group1"
            assert related_tags[0].created == "2021-01-01"
            assert related_tags[0].popularity == 10
            assert related_tags[0].series_count == 5
            assert related_tags[0].notes == "Some notes"
        else:
            assert isinstance(related_tags, Tag)
            assert related_tags.name == "related_tag1"
            assert related_tags.group_id == "group1"
            assert related_tags.created == "2021-01-01"
            assert related_tags.popularity == 10
            assert related_tags.series_count == 5
            assert related_tags.notes == "Some notes"
    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_related_tags(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_related_tags(1)

async def test_get_release_tables_async(fred_api):
    # Mock the API response
    mock_response = {
        "elements": {
            "12887": {
            "element_id": 12887,
            "release_id": 53,
            "series_id": "DGDSRL1A225NBEA",
            "parent_id": 12886,
            "line": "3",
            "type": "series",
            "name": "Goods",
            "level": "1",
            "children": [
                {
                "element_id": 12888,
                "release_id": 53,
                "series_id": "DDURRL1A225NBEA",
                "parent_id": 12887,
                "line": "4",
                "type": "series",
                "name": "Durable goods",
                "level": "2",
                "children": [

                ]
                },
                {
                "element_id": 12889,
                "release_id": 53,
                "series_id": "DNDGRL1A225NBEA",
                "parent_id": 12887,
                "line": "5",
                "type": "series",
                "name": "Nondurable goods",
                "level": "2",
                "children": [

                ]
                }
            ]
            },
            "12888": {
            "element_id": 12888,
            "release_id": 53,
            "series_id": "DDURRL1A225NBEA",
            "parent_id": 12887,
            "line": "4",
            "type": "series",
            "name": "Durable goods",
            "level": "2",
            "children": [

            ]
            }
        }
    }

    # Test valid release ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        elements = fred_api.get_release_tables(1)
        if isinstance(elements, list):
            assert len(elements) == 2
            assert all(isinstance(element, Element) for element in elements)
            assert elements[0].element_id == 12887
            assert elements[0].release_id == 53
            assert elements[0].series_id == "DGDSRL1A225NBEA"
            assert elements[0].parent_id == 12886
            assert elements[0].line == "3"
            assert elements[0].type == "series"
            assert elements[0].name == "Goods"
            assert elements[0].level == "1"
            assert len(elements[0].children) == 2
            assert elements[0].children[0].element_id == 12888
            assert elements[0].children[0].release_id == 53
            assert elements[0].children[0].series_id == "DDURRL1A225NBEA"
            assert elements[0].children[0].parent_id == 12887
            assert elements[0].children[0].line == "4"
            assert elements[0].children[0].type == "series"
            assert elements[0].children[0].name == "Durable goods"
            assert elements[0].children[0].level == "2"
        else:
            assert isinstance(elements, Element)
            assert elements.element_id == 12887
            assert elements.release_id == 53
            assert elements.series_id == "DGDSRL1A225NBEA"
            assert elements.parent_id == 12886
            assert elements.line == "3"
            assert elements.type == "series"
            assert elements.name == "Goods"
            assert elements.level == "1"
            assert len(elements.children) == 2
            assert elements.children[0].element_id == 12888
            assert elements.children[0].release_id == 53
            assert elements.children[0].series_id == "DDURRL1A225NBEA"
            assert elements.children[0].parent_id == 12887
            assert elements.children[0].line == "4"
            assert elements.children[0].type == "series"
            assert elements.children[0].name == "Durable goods"
            assert elements.children[0].level == "2"
    # Test invalid release ID
    with pytest.raises(ValueError):
        fred_api.get_release_tables(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_release_tables(1)

# Series tests
async def test_get_series_async(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80,
                "group_popularity": 1,
                "notes": None
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_series("GNPCA")
        assert isinstance(series, Series)
        assert series.id == "GNPCA"
        assert series.realtime_start == "2013-08-14"
        assert series.realtime_end == "2013-08-14"
        assert series.title == "Real Gross National Product"
        assert series.observation_start == "1947-01-01"
        assert series.observation_end == "2021-01-01"
        assert series.frequency == "Annual"
        assert series.frequency_short == "A"
        assert series.units == "Billions of Chained 2012 Dollars"
        assert series.units_short == "Bil. of Chn. 2012 $"
        assert series.seasonal_adjustment == "Not Seasonally Adjusted"
        assert series.seasonal_adjustment_short == "NSA"
        assert series.last_updated == "2021-03-25 07:51:36-05"
        assert series.popularity == 80
        assert series.group_popularity == 1
        assert series.notes is None

    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series("GNPCA")

async def test_get_series_categories_async(fred_api):
    # Mock the API response
    mock_response = {
        "categories": [
            {
                "id": 125,
                "name": "Trade Balance",
                "parent_id": None
            },
            {
                "id": 126,
                "name": "Exports",
                "parent_id": 125
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        categories = fred_api.get_series_categories("GNPCA")
        assert isinstance(categories, list)
        assert len(categories) == 2
        assert all(isinstance(category, Category) for category in categories)
        assert categories[0].id == 125
        assert categories[0].name == "Trade Balance"
        assert categories[0].parent_id is None

    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series_categories("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_categories("GNPCA")

# Pandas
async def test_get_series_observations_pandas_async(fred_api):
    # Mock the API response
    mock_response = {
        "observations": [
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2021-01-01",
                "value": 100.0
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2021-01-02",
                "value": 200.0
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        observations = fred_api.get_series_observations("GNPCA")
        assert isinstance(observations, pd.DataFrame)
        assert len(observations) == 2
        assert observations.index[0] == pd.Timestamp("2021-01-01")
        assert observations.index[1] == pd.Timestamp("2021-01-02")
        assert observations.iloc[0]["value"] == 100.0
        assert observations.iloc[1]["value"] == 200.0
    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series_observations("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_observations("GNPCA")

#### Add Polars method later

async def test_get_series_release_async(fred_api):
    # Mock the API response
    mock_response = {
        "releases": [
            {
                "id": 1,
                "name": "Release 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 1",
                "link": "http://example.com/release1",
                "notes": "Some notes"
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        release = fred_api.get_series_release("GNPCA")
        assert isinstance(release, Release)
        assert release.id == 1
        assert release.realtime_start == "2013-08-13"
        assert release.realtime_end == "2013-08-13"
        assert release.name == "Release 1"
        assert release.press_release == "Press Release 1"
        assert release.link == "http://example.com/release1"
        assert release.notes == "Some notes"

    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series_release("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_release("GNPCA")

async def test_get_series_search_async(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80,
                "group_popularity": 1,
                "notes": None
            }
        ]
    }

    # Test valid search text
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_series_search("Real Gross National Product")
        assert isinstance(series, Series)
        assert series.id == "GNPCA"
        assert series.realtime_start == "2013-08-14"
        assert series.realtime_end == "2013-08-14"
        assert series.title == "Real Gross National Product"
        assert series.observation_start == "1947-01-01"
        assert series.observation_end == "2021-01-01"
        assert series.frequency == "Annual"
        assert series.frequency_short == "A"
        assert series.units == "Billions of Chained 2012 Dollars"
        assert series.units_short == "Bil. of Chn. 2012 $"
        assert series.seasonal_adjustment == "Not Seasonally Adjusted"
        assert series.seasonal_adjustment_short == "NSA"
        assert series.last_updated == "2021-03-25 07:51:36-05"
        assert series.popularity == 80
        assert series.group_popularity == 1
        assert series.notes is None

    # Test invalid search text
    with pytest.raises(ValueError):
        fred_api.get_series_search("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_search("Real Gross National Product")

async def test_get_series_search_tags_async(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid search text
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tags = fred_api.get_series_search_tags("Real Gross National Product")
        assert isinstance(tags, list)
        assert len(tags) == 2
        assert all(isinstance(tag, Tag) for tag in tags)
        assert tags[0].name == "tag1"
        assert tags[0].group_id == "group1"
        assert tags[0].created == "2021-01-01"
        assert tags[0].popularity == 10
        assert tags[0].series_count == 5
        assert tags[0].notes == "Some notes"

    # Test invalid search text
    with pytest.raises(ValueError):
        fred_api.get_series_search_tags("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_search_tags("Real Gross National Product")

async def test_get_series_search_related_tags_async(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "related_tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "related_tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid search text
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        related_tags = fred_api.get_series_search_related_tags("Real Gross National Product")
        assert isinstance(related_tags, list)
        assert len(related_tags) == 2
        assert all(isinstance(tag, Tag) for tag in related_tags)
        assert related_tags[0].name == "related_tag1"
        assert related_tags[0].group_id == "group1"
        assert related_tags[0].created == "2021-01-01"
        assert related_tags[0].popularity == 10
        assert related_tags[0].series_count == 5
        assert related_tags[0].notes == "Some notes"

    # Test invalid search text
    with pytest.raises(ValueError):
        fred_api.get_series_search_related_tags("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_search_related_tags("Real Gross National Product")

async def test_get_series_tags_async(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tags = fred_api.get_series_tags("GNPCA")
        assert isinstance(tags, list)
        assert len(tags) == 2
        assert all(isinstance(tag, Tag) for tag in tags)
        assert tags[0].name == "tag1"
        assert tags[0].group_id == "group1"
        assert tags[0].created == "2021-01-01"
        assert tags[0].popularity == 10
        assert tags[0].series_count == 5
        assert tags[0].notes == "Some notes"

    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series_tags("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_tags("GNPCA")

async def test_get_series_updates_async(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80
            }
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_series_updates()
        assert isinstance(series, Series)
        assert series.id == "GNPCA"
        assert series.realtime_start == "2013-08-14"
        assert series.realtime_end == "2013-08-14"
        assert series.title == "Real Gross National Product"
        assert series.observation_start == "1947-01-01"
        assert series.observation_end == "2021-01-01"
        assert series.frequency == "Annual"
        assert series.frequency_short == "A"
        assert series.units == "Billions of Chained 2012 Dollars"
        assert series.units_short == "Bil. of Chn. 2012 $"
        assert series.seasonal_adjustment == "Not Seasonally Adjusted"
        assert series.seasonal_adjustment_short == "NSA"
        assert series.last_updated == "2021-03-25 07:51:36-05"
        assert series.popularity == 80

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_updates()

async def test_get_series_vintage_dates_async(fred_api):
    # Mock the API response
    mock_response = {
        "vintage_dates": [
            "1958-12-21",
            "1959-02-19",
            "1959-07-19",
            "1960-02-16",
            "1960-07-22",
            "1961-02-19"
        ]
    }

    # Test valid series ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        vintage_dates = fred_api.get_series_vintagedates("GNPCA")
        if isinstance(vintage_dates, list):
            assert len(vintage_dates) == 6
            assert all(isinstance(vintage_date, VintageDate) for vintage_date in vintage_dates)
            assert vintage_dates[0].vintage_date == "1958-12-21"
        else:
            assert isinstance(vintage_dates, VintageDate)
            assert vintage_dates.vintage_date == "1958-12-21"

    # Test invalid series ID
    with pytest.raises(ValueError):
        fred_api.get_series_vintagedates("")

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_series_vintagedates("GNPCA")

# Sources tests
async def test_get_sources_async(fred_api):
    # Mock the API response
    mock_response = {
        "sources": [
            {
                "id": 1,
                "name": "Source 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "link": "http://example.com/source1",
                "notes": "Some notes"
            },
            {
                "id": 2,
                "name": "Source 2",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "link": "http://example.com/source2",
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid source ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        sources = fred_api.get_sources()
        assert isinstance(sources, list)
        assert len(sources) == 2
        assert all(isinstance(source, Source) for source in sources)
        assert sources[0].id == 1
        assert sources[0].realtime_start == "2013-08-13"
        assert sources[0].realtime_end == "2013-08-13"
        assert sources[0].name == "Source 1"
        assert sources[0].link == "http://example.com/source1"
        assert sources[0].notes == "Some notes"

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_sources()

async def test_get_source_async(fred_api):
    # Mock the API response
    mock_response = {
        "sources": [
            {
                "id": 1,
                "name": "Source 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "link": "http://example.com/source1",
                "notes": "Some notes"
            }
        ]
    }

    # Test valid source ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        source = fred_api.get_source(1)
        assert isinstance(source, Source)
        assert source.id == 1
        assert source.realtime_start == "2013-08-13"
        assert source.realtime_end == "2013-08-13"
        assert source.name == "Source 1"
        assert source.link == "http://example.com/source1"
        assert source.notes == "Some notes"

    # Test invalid source ID
    with pytest.raises(ValueError):
        fred_api.get_source(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_source(1)

async def test_get_source_releases_async(fred_api):
    # Mock the API response
    mock_response = {
        "releases": [
            {
                "id": 1,
                "name": "Release 1",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 1",
                "link": "http://example.com/release1",
                "notes": "Some notes"
            },
            {
                "id": 2,
                "name": "Release 2",
                "realtime_start": "2013-08-13",
                "realtime_end": "2013-08-13",
                "press_release": "Press Release 2",
                "link": "http://example.com/release2",
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid source ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        releases = fred_api.get_source_releases(1)
        assert isinstance(releases, list)
        assert len(releases) == 2
        assert all(isinstance(release, Release) for release in releases)
        assert releases[0].id == 1
        assert releases[0].realtime_start == "2013-08-13"
        assert releases[0].realtime_end == "2013-08-13"
        assert releases[0].name == "Release 1"
        assert releases[0].press_release == "Press Release 1"
        assert releases[0].link == "http://example.com/release1"
        assert releases[0].notes == "Some notes"

    # Test invalid source ID
    with pytest.raises(ValueError):
        fred_api.get_source_releases(-1)

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_source_releases(1)

# Tags tests
async def test_get_tags_async(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            },
            {
                "name": "tag2",
                "group_id": "group2",
                "created": "2021-01-02",
                "popularity": 20,
                "series_count": 10,
                "notes": "Some other notes"
            }
        ]
    }

    # Test valid tag ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tags = fred_api.get_tags()
        assert isinstance(tags, list)
        assert len(tags) == 2
        assert all(isinstance(tag, Tag) for tag in tags)
        assert tags[0].name == "tag1"
        assert tags[0].group_id == "group1"
        assert tags[0].created == "2021-01-01"
        assert tags[0].popularity == 10
        assert tags[0].series_count == 5
        assert tags[0].notes == "Some notes"

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_tags()

async def test_related_get_tags_async(fred_api):
    # Mock the API response
    mock_response = {
        "tags": [
            {
                "name": "tag1",
                "group_id": "group1",
                "created": "2021-01-01",
                "popularity": 10,
                "series_count": 5,
                "notes": "Some notes"
            }
        ]
    }

    # Test valid tag ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        tag = fred_api.get_related_tags("tag1")
        assert isinstance(tag, Tag)
        assert tag.name == "tag1"
        assert tag.group_id == "group1"
        assert tag.created == "2021-01-01"
        assert tag.popularity == 10
        assert tag.series_count == 5
        assert tag.notes == "Some notes"

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_related_tags("tag1")

async def test_get_tags_series_async(fred_api):
    # Mock the API response
    mock_response = {
        "seriess": [
            {
                "id": "GNPCA",
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "title": "Real Gross National Product",
                "observation_start": "1947-01-01",
                "observation_end": "2021-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Billions of Chained 2012 Dollars",
                "units_short": "Bil. of Chn. 2012 $",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2021-03-25 07:51:36-05",
                "popularity": 80
            }
        ]
    }

    # Test valid tag ID
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_response):
        series = fred_api.get_tags_series("tag1")
        assert isinstance(series, Series)
        assert series.id == "GNPCA"
        assert series.realtime_start == "2013-08-14"
        assert series.realtime_end == "2013-08-14"
        assert series.title == "Real Gross National Product"
        assert series.observation_start == "1947-01-01"
        assert series.observation_end == "2021-01-01"
        assert series.frequency == "Annual"
        assert series.frequency_short == "A"
        assert series.units == "Billions of Chained 2012 Dollars"
        assert series.units_short == "Bil. of Chn. 2012 $"
        assert series.seasonal_adjustment == "Not Seasonally Adjusted"
        assert series.seasonal_adjustment_short == "NSA"
        assert series.last_updated == "2021-03-25 07:51:36-05"
        assert series.popularity == 80

    # Test invalid API response
    mock_invalid_response = {}
    with patch.object(fred_api, '_FredAPI__fred_get_request', return_value=mock_invalid_response):
        with pytest.raises(ValueError):
            fred_api.get_tags_series("tag1")

# add async maps test in next revision
