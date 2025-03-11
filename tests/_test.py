"""
Comprehensive unit tests for the fedfred Python module.
"""
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import polars as pl
import geopandas as gpd
from shapely.geometry import Polygon
from fedfred.fedfred import FredAPI, FredMapsAPI
from fedfred.fred_data import (
    Category, Series, Tag, Release, ReleaseDate,
    Source, Element, SeriesGroup
)

class TestFredAPI(unittest.TestCase):
    """Test cases for the FredAPI class."""
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = 'test_api_key'
        self.fred_api = FredAPI(api_key=self.api_key)
    # Category Methods
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_category(self, mock_request):
        """Test get_category method."""
        # Return the parsed JSON directly instead of a response object
        mock_request.return_value = {
            "categories": [
                {"id": 125, "name": "Money, Banking, & Finance", "parent_id": None}
            ]
        }
        category = self.fred_api.get_category(125)
        self.assertIsInstance(category, Category)
        self.assertEqual(category.id, 125)
        self.assertEqual(category.name, "Money, Banking, & Finance")
        self.assertIsNone(category.parent_id)
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_category_children(self, mock_request):
        """Test get_category_children method."""
        mock_request.return_value = {
            "categories": [
                {"id": 126, "name": "Banking", "parent_id": 125},
                {"id": 127, "name": "Finance", "parent_id": 125}
            ]
        }
        children = self.fred_api.get_category_children(125)
        self.assertIsInstance(children, list)
        self.assertEqual(len(children), 2)
        self.assertIsInstance(children[0], Category)
        self.assertEqual(children[0].id, 126)
        self.assertEqual(children[0].parent_id, 125)
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_category_related(self, mock_request):
        """Test get_category_related method."""
        mock_request.return_value = {
            "categories": [
                {"id": 130, "name": "Interest Rates", "parent_id": None}
            ]
        }
        related = self.fred_api.get_category_related(125)
        self.assertIsInstance(related, Category)
        self.assertEqual(related.id, 130)
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_category_series(self, mock_request):
        """Test get_category_series method."""
        mock_request.return_value = {
            "seriess": [
                {
                    "id": "FEDFUNDS",
                    "title": "Federal Funds Rate",
                    "observation_start": "1954-07-01",
                    "observation_end": "2023-03-01",
                    "frequency": "Monthly",
                    "frequency_short": "M",
                    "units": "Percent",
                    "units_short": "%",
                    "seasonal_adjustment": "Not Seasonally Adjusted",
                    "seasonal_adjustment_short": "NSA",
                    "last_updated": "2023-04-03 15:16:05-05",
                    "popularity": 92,
                    "group_popularity": 92,
                    "notes": "Interest rate at which banks lend to each other."
                }
            ]
        }
        series = self.fred_api.get_category_series(33073)
        self.assertIsInstance(series, Series)
        self.assertEqual(series.id, "FEDFUNDS")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_category_tags(self, mock_request):
        """Test get_category_tags method."""
        mock_request.return_value = {
            "tags": [
                {
                    "name": "interest rate",
                    "group_id": "gen",
                    "notes": None,
                    "created": "2012-08-29 10:21:56-05",
                    "popularity": 100,
                    "series_count": 800
                }
            ]
        }
        tags = self.fred_api.get_category_tags(33073)
        self.assertIsInstance(tags, Tag)
        self.assertEqual(tags.name, "interest rate")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_category_related_tags(self, mock_request):
        """Test get_category_related_tags method."""
        mock_request.return_value = {
            "tags": [
                {
                    "name": "federal",
                    "group_id": "gen",
                    "notes": None,
                    "created": "2012-08-29 10:21:56-05",
                    "popularity": 95,
                    "series_count": 500
                }
            ]
        }
        related_tags = self.fred_api.get_category_related_tags(33073, tag_names="interest rate")
        self.assertIsInstance(related_tags, Tag)
        self.assertEqual(related_tags.name, "federal")
    # Release Methods
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_releases(self, mock_request):
        """Test get_releases method."""
        mock_request.return_value = {
            "releases": [
                {
                    "id": 10,
                    "realtime_start": "2023-01-01",
                    "realtime_end": "2023-12-31",
                    "name": "Gross Domestic Product",
                    "press_release": True,
                    "link": "https://example.com",
                    "notes": "Quarterly report"
                }
            ]
        }
        releases = self.fred_api.get_releases()
        self.assertIsInstance(releases, Release)
        self.assertEqual(releases.id, 10)
        self.assertEqual(releases.name, "Gross Domestic Product")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_releases_dates(self, mock_request):
        """Test get_releases_dates method."""
        mock_request.return_value = {
            "release_dates": [
                {
                    "release_id": 10,
                    "date": "2023-04-27"
                }
            ]
        }
        release_dates = self.fred_api.get_releases_dates()
        self.assertIsInstance(release_dates, ReleaseDate)
        self.assertEqual(release_dates.release_id, 10)
        self.assertEqual(release_dates.date, "2023-04-27")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_release(self, mock_request):
        """Test get_release method."""
        mock_request.return_value = {
            "releases": [
                {
                    "id": 10,
                    "realtime_start": "2023-01-01",
                    "realtime_end": "2023-12-31",
                    "name": "Gross Domestic Product",
                    "press_release": True,
                    "link": "https://example.com",
                    "notes": "Quarterly report"
                }
            ]
        }
        release = self.fred_api.get_release(10)
        self.assertIsInstance(release, Release)
        self.assertEqual(release.id, 10)
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_release_dates(self, mock_request):
        """Test get_release_dates method."""
        mock_request.return_value = {
            "release_dates": [
                {
                    "release_id": 10,
                    "date": "2023-04-27"
                }
            ]
        }
        release_dates = self.fred_api.get_release_dates(10)
        self.assertIsInstance(release_dates, ReleaseDate)
        self.assertEqual(release_dates.release_id, 10)
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_release_series(self, mock_request):
        """Test get_release_series method."""
        mock_request.return_value = {
            "seriess": [
                {
                    "id": "GDP",
                    "title": "Gross Domestic Product",
                    "observation_start": "1947-01-01",
                    "observation_end": "2023-01-01",
                    "frequency": "Quarterly",
                    "frequency_short": "Q",
                    "units": "Billions of Dollars",
                    "units_short": "Bil. $",
                    "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
                    "seasonal_adjustment_short": "SAAR",
                    "last_updated": "2023-03-30 07:51:31-05",
                    "popularity": 100,
                    "group_popularity": 100,
                    "notes": "GDP is the value of all final goods and services."
                }
            ]
        }
        series = self.fred_api.get_release_series(10)
        self.assertIsInstance(series, Series)
        self.assertEqual(series.id, "GDP")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_release_sources(self, mock_request):
        """Test get_release_sources method."""
        mock_request.return_value = {
            "sources": [
                {
                    "id": 1,
                    "realtime_start": "2023-01-01",
                    "realtime_end": "2023-12-31",
                    "name": "Board of Governors of the Federal Reserve System",
                    "link": "https://www.federalreserve.gov/",
                    "notes": "The Federal Reserve Board"
                }
            ]
        }
        sources = self.fred_api.get_release_sources(10)
        self.assertIsInstance(sources, Source)
        self.assertEqual(sources.id, 1)
        self.assertEqual(sources.name, "Board of Governors of the Federal Reserve System")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_release_tags(self, mock_request):
        """Test get_release_tags method."""
        mock_request.return_value = {
            "tags": [
                {
                    "name": "gdp",
                    "group_id": "gen",
                    "notes": None,
                    "created": "2012-02-27 11:33:02-06",
                    "popularity": 100,
                    "series_count": 150
                }
            ]
        }
        tags = self.fred_api.get_release_tags(10)
        self.assertIsInstance(tags, Tag)
        self.assertEqual(tags.name, "gdp")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_release_related_tags(self, mock_request):
        """Test get_release_related_tags method."""
        mock_request.return_value = {
            "tags": [
                {
                    "name": "quarterly",
                    "group_id": "freq",
                    "notes": None,
                    "created": "2012-02-27 11:33:02-06",
                    "popularity": 95,
                    "series_count": 120
                }
            ]
        }
        tags = self.fred_api.get_release_related_tags("gdp")
        self.assertIsInstance(tags, Tag)
        self.assertEqual(tags.name, "quarterly")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_release_tables(self, mock_request):
        """Test get_release_tables method."""
        mock_request.return_value = {
            "elements": {
                "1": {
                    "element_id": 1,
                    "release_id": 10,
                    "series_id": "GDP",
                    "parent_id": 0,
                    "line": "1",
                    "type": "header",
                    "name": "Gross Domestic Product",
                    "level": "1",
                    "children": []
                }
            }
        }
        elements = self.fred_api.get_release_tables(10)
        self.assertIsInstance(elements, Element)
        self.assertEqual(elements.element_id, 1)
        self.assertEqual(elements.series_id, "GDP")
    # Series Methods
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_series(self, mock_request):
        """Test get_series method."""
        mock_request.return_value = {
            "seriess": [
                {
                    "id": "GDP",
                    "title": "Gross Domestic Product",
                    "observation_start": "1947-01-01",
                    "observation_end": "2023-01-01",
                    "frequency": "Quarterly",
                    "frequency_short": "Q",
                    "units": "Billions of Dollars",
                    "units_short": "Bil. $",
                    "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
                    "seasonal_adjustment_short": "SAAR",
                    "last_updated": "2023-03-30 07:51:31-05",
                    "popularity": 100,
                    "group_popularity": 100,
                    "notes": "GDP is the value of all final goods and services."
                }
            ]
        }
        series = self.fred_api.get_series("GDP")
        self.assertIsInstance(series, Series)
        self.assertEqual(series.id, "GDP")
        self.assertEqual(series.title, "Gross Domestic Product")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_series_categories(self, mock_request):
        """Test get_series_categories method."""
        mock_request.return_value = {
            "categories": [
                {"id": 106, "name": "National Income & Product Accounts", "parent_id": 18}
            ]
        }
        categories = self.fred_api.get_series_categories("GDP")
        self.assertIsInstance(categories, Category)
        self.assertEqual(categories.id, 106)
    @patch('fedfred.fedfred.httpx.get')
    def test_get_series_observations(self, mock_get):
        """Test get_series_observations method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "observations": [
                {
                    "date": "2022-01-01", "value": "24000.6", 
                    "realtime_start": "2023-01-01", "realtime_end": "2023-12-31"
                },
                {
                    "date": "2022-04-01", "value": "24400.3", 
                    "realtime_start": "2023-01-01", "realtime_end": "2023-12-31"
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        with patch.object(self.fred_api, 'get_series_observations', return_value=pd.DataFrame({
            'date': ['2022-01-01', '2022-04-01'],
            'value': [24000.6, 24400.3]
        })):
            df = self.fred_api.get_series_observations("GDP")
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 2)

        with patch.object(self.fred_api, 'get_series_observations', return_value=pl.DataFrame({
            'date': ['2022-01-01', '2022-04-01'],
            'value': [24000.6, 24400.3]
        })):
            df_pl = self.fred_api.get_series_observations("GDP", dataframe_method='polars')
            self.assertIsInstance(df_pl, pl.DataFrame)
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_series_release(self, mock_request):
        """Test get_series_release method."""
        mock_request.return_value = {
            "releases": [
                {
                    "id": 10,
                    "realtime_start": "2023-01-01",
                    "realtime_end": "2023-12-31",
                    "name": "Gross Domestic Product",
                    "press_release": True,
                    "link": "https://example.com",
                    "notes": "Quarterly report"
                }
            ]
        }
        release = self.fred_api.get_series_release("GDP")
        self.assertIsInstance(release, Release)
        self.assertEqual(release.id, 10)
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_series_search(self, mock_request):
        """Test get_series_search method."""
        mock_request.return_value = {
            "seriess": [
                {
                    "id": "GDP",
                    "title": "Gross Domestic Product",
                    "observation_start": "1947-01-01",
                    "observation_end": "2023-01-01",
                    "frequency": "Quarterly",
                    "frequency_short": "Q",
                    "units": "Billions of Dollars",
                    "units_short": "Bil. $",
                    "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
                    "seasonal_adjustment_short": "SAAR",
                    "last_updated": "2023-03-30 07:51:31-05",
                    "popularity": 100,
                    "group_popularity": 100,
                    "notes": "GDP is the value of all final goods and services."
                }
            ]
        }
        search_results = self.fred_api.get_series_search("gross domestic product")
        self.assertIsInstance(search_results, Series)
        self.assertEqual(search_results.id, "GDP")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_series_search_tags(self, mock_request):
        """Test get_series_search_tags method."""
        mock_request.return_value = {
            "tags": [
                {
                    "name": "gdp",
                    "group_id": "gen",
                    "notes": None,
                    "created": "2012-02-27 11:33:02-06",
                    "popularity": 100,
                    "series_count": 150
                }
            ]
        }
        tags = self.fred_api.get_series_search_tags("gross domestic product")
        self.assertIsInstance(tags, Tag)
        self.assertEqual(tags.name, "gdp")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_series_search_related_tags(self, mock_request):
        """Test get_series_search_related_tags method."""
        mock_request.return_value = {
            "tags": [
                {
                    "name": "quarterly",
                    "group_id": "freq",
                    "notes": None,
                    "created": "2012-02-27 11:33:02-06",
                    "popularity": 95,
                    "series_count": 120
                }
            ]
        }
        tags = self.fred_api.get_series_search_related_tags("gdp", tag_names="usa")
        self.assertIsInstance(tags, Tag)
        self.assertEqual(tags.name, "quarterly")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_series_tags(self, mock_request):
        """Test get_series_tags method."""
        mock_request.return_value = {
            "tags": [
                {
                    "name": "gdp",
                    "group_id": "gen",
                    "notes": None,
                    "created": "2012-02-27 11:33:02-06",
                    "popularity": 100,
                    "series_count": 150
                },
                {
                    "name": "quarterly",
                    "group_id": "freq",
                    "notes": None,
                    "created": "2012-02-27 11:33:02-06",
                    "popularity": 95,
                    "series_count": 120
                }
            ]
        }
        tags = self.fred_api.get_series_tags("GDP")
        self.assertIsInstance(tags, list)
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0].name, "gdp")
        self.assertEqual(tags[1].name, "quarterly")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_series_updates(self, mock_request):
        """Test get_series_updates method."""
        mock_request.return_value = {
            "seriess": [
                {
                    "id": "GDP",
                    "title": "Gross Domestic Product",
                    "observation_start": "1947-01-01",
                    "observation_end": "2023-01-01",
                    "frequency": "Quarterly",
                    "frequency_short": "Q",
                    "units": "Billions of Dollars",
                    "units_short": "Bil. $",
                    "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
                    "seasonal_adjustment_short": "SAAR",
                    "last_updated": "2023-03-30 07:51:31-05",
                    "popularity": 100,
                    "group_popularity": 100,
                    "notes": "GDP is the value of all final goods and services."
                }
            ]
        }
        updates = self.fred_api.get_series_updates()
        self.assertIsInstance(updates, Series)
        self.assertEqual(updates.id, "GDP")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_series_vintagedates(self, mock_request):
        """Test get_series_vintagedates method."""
        mock_request.return_value = {
            "vintage_dates": ["2022-01-28", "2022-02-25", "2022-03-30"]
        }
        vintage_dates = self.fred_api.get_series_vintagedates("GDP")
        self.assertIsInstance(vintage_dates, list)
        self.assertEqual(len(vintage_dates), 3)
        self.assertEqual(vintage_dates[0].vintage_date, "2022-01-28")
    # Source Methods
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_sources(self, mock_request):
        """Test get_sources method."""
        mock_request.return_value = {
            "sources": [
                {
                    "id": 1,
                    "realtime_start": "2023-01-01",
                    "realtime_end": "2023-12-31",
                    "name": "Board of Governors of the Federal Reserve System",
                    "link": "https://www.federalreserve.gov/",
                    "notes": "The Federal Reserve Board"
                }
            ]
        }
        sources = self.fred_api.get_sources()
        self.assertIsInstance(sources, Source)
        self.assertEqual(sources.id, 1)
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_source(self, mock_request):
        """Test get_source method."""
        mock_request.return_value = {
            "sources": [
                {
                    "id": 1,
                    "realtime_start": "2023-01-01",
                    "realtime_end": "2023-12-31",
                    "name": "Board of Governors of the Federal Reserve System",
                    "link": "https://www.federalreserve.gov/",
                    "notes": "The Federal Reserve Board"
                }
            ]
        }
        source = self.fred_api.get_source(1)
        self.assertIsInstance(source, Source)
        self.assertEqual(source.id, 1)
        self.assertEqual(source.name, "Board of Governors of the Federal Reserve System")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_source_releases(self, mock_request):
        """Test get_source_releases method."""
        mock_request.return_value = {
            "releases": [
                {
                    "id": 10,
                    "realtime_start": "2023-01-01",
                    "realtime_end": "2023-12-31",
                    "name": "Gross Domestic Product",
                    "press_release": True,
                    "link": "https://example.com",
                    "notes": "Quarterly report"
                }
            ]
        }
        releases = self.fred_api.get_source_releases(1)
        self.assertIsInstance(releases, Release)
        self.assertEqual(releases.id, 10)
    # Tag Methods
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_tags(self, mock_request):
        """Test get_tags method."""
        mock_request.return_value = {
            "tags": [
                {
                    "name": "gdp",
                    "group_id": "gen",
                    "notes": None,
                    "created": "2012-02-27 11:33:02-06",
                    "popularity": 100,
                    "series_count": 150
                }
            ]
        }
        tags = self.fred_api.get_tags()
        self.assertIsInstance(tags, Tag)
        self.assertEqual(tags.name, "gdp")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_related_tags(self, mock_request):
        """Test get_related_tags method."""
        mock_request.return_value = {
            "tags": [
                {
                    "name": "quarterly",
                    "group_id": "freq",
                    "notes": None,
                    "created": "2012-02-27 11:33:02-06",
                    "popularity": 95,
                    "series_count": 120
                }
            ]
        }
        tags = self.fred_api.get_related_tags(tag_names="gdp")
        self.assertIsInstance(tags, Tag)
        self.assertEqual(tags.name, "quarterly")
    @patch('fedfred.fedfred.FredAPI._FredAPI__fred_get_request')
    def test_get_tags_series(self, mock_request):
        """Test get_tags_series method."""
        mock_request.return_value = {
            "seriess": [
                {
                    "id": "GDP",
                    "title": "Gross Domestic Product",
                    "observation_start": "1947-01-01",
                    "observation_end": "2023-01-01",
                    "frequency": "Quarterly",
                    "frequency_short": "Q",
                    "units": "Billions of Dollars",
                    "units_short": "Bil. $",
                    "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
                    "seasonal_adjustment_short": "SAAR",
                    "last_updated": "2023-03-30 07:51:31-05",
                    "popularity": 100,
                    "group_popularity": 100,
                    "notes": "GDP is the value of all final goods and services."
                }
            ]
        }
        series = self.fred_api.get_tags_series(tag_names="gdp")
        self.assertIsInstance(series, Series)
        self.assertEqual(series.id, "GDP")

class TestFredMapsAPI(unittest.TestCase):
    """Test cases for the FredMapsAPI class."""
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = 'test_api_key'
        self.fred_maps_api = FredMapsAPI(api_key=self.api_key)
    @patch('fedfred.fedfred.FredMapsAPI._FredMapsAPI__fred_maps_get_request')
    def test_get_shape_files(self, mock_request):
        """Test get_shape_files method."""
        mock_request.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"STATE": "01", "NAME": "Alabama"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    }
                }
            ]
        }
        gdf = self.fred_maps_api.get_shape_files("state")
        self.assertIsInstance(gdf, gpd.GeoDataFrame)
        self.assertEqual(len(gdf), 1)
        self.assertEqual(gdf["NAME"][0], "Alabama")
    @patch('fedfred.fedfred.FredMapsAPI._FredMapsAPI__fred_maps_get_request')
    def test_get_series_group(self, mock_request):
        """Test get_series_group method."""
        mock_request.return_value = {
            "series_group": [
                {
                    "title": "Per Capita Personal Income by State",
                    "region_type": "state",
                    "series_group": "income",
                    "season": "Not Seasonally Adjusted",
                    "units": "Dollars",
                    "frequency": "Annual",
                    "min_date": "2010-01-01",
                    "max_date": "2022-01-01"
                }
            ]
        }
        series_group = self.fred_maps_api.get_series_group("PCPI")
        self.assertIsInstance(series_group, SeriesGroup)
        self.assertEqual(series_group.title, "Per Capita Personal Income by State")
        self.assertEqual(series_group.region_type, "state")
    @patch('fedfred.fedfred.FredMapsAPI._FredMapsAPI__fred_maps_get_request')
    @patch('fedfred.fedfred.FredMapsAPI._FredMapsAPI__to_gpd_gdf')
    def test_get_series_data(self, mock_to_gpd_gdf, mock_request):
        """Test get_series_data method."""
        mock_request.return_value = {
            "meta": {
                "title": "2022 Per Capita Personal Income by State",
                "region": "state",
                "seasonality": "Not Seasonally Adjusted",
                "units": "Dollars",
                "frequency": "Annual",
                "date": "2022-01-01"
            },
            "data": [
                {"region": "Alabama", "code": "01", "value": "48123", "series_id": "ALPCPI"},
                {"region": "Alaska", "code": "02", "value": "67956", "series_id": "AKPCPI"}
            ]
        }
        mock_to_gpd_gdf.return_value = gpd.GeoDataFrame({
            "region": ["Alabama", "Alaska"],
            "code": ["01", "02"],
            "value": [48123, 67956],
            "series_id": ["ALPCPI", "AKPCPI"],
            "geometry": [None, None]
        })
        gdf = self.fred_maps_api.get_series_data("PCPI", date="2022-01-01")
        self.assertIsInstance(gdf, gpd.GeoDataFrame)
        self.assertEqual(len(gdf), 2)
        self.assertEqual(gdf["region"][0], "Alabama")
        self.assertEqual(gdf["value"][1], 67956)
    @patch('fedfred.fedfred.FredMapsAPI._FredMapsAPI__fred_maps_get_request')
    @patch('fedfred.fedfred.FredMapsAPI._FredMapsAPI__to_gpd_gdf')
    def test_get_regional_data(self, mock_to_gpd_gdf, mock_request):
        """Test get_regional_data method."""
        mock_request.return_value = {
            "meta": {
                "title": "2022 Unemployment Rate by State",
                "region": "state",
                "seasonality": "Seasonally Adjusted",
                "units": "Percent",
                "frequency": "Monthly",
                "date": "2022-12-01"
            },
            "data": [
                {"region": "Alabama", "code": "01", "value": "2.8", "series_id": "ALUR"},
                {"region": "Alaska", "code": "02", "value": "4.3", "series_id": "AKUR"}
            ]
        }
        mock_to_gpd_gdf.return_value = gpd.GeoDataFrame({
            "region": ["Alabama", "Alaska"],
            "code": ["01", "02"],
            "value": [2.8, 4.3],
            "series_id": ["ALUR", "AKUR"],
            "geometry": [None, None]
        })
        gdf = self.fred_maps_api.get_regional_data(
            series_group="unemployment",
            region_type="state",
            date="2022-12-01",
            season="SA",
            units="pct"
        )
        self.assertIsInstance(gdf, gpd.GeoDataFrame)
        self.assertEqual(len(gdf), 2)
        self.assertEqual(gdf["region"][0], "Alabama")
        self.assertEqual(gdf["value"][1], 4.3)

class TestFredAPIPrivateMethods(unittest.TestCase):
    """Test cases for the private methods of FredAPI class."""
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = 'test_api_key'
        self.fred_api = FredAPI(api_key=self.api_key)
    def test_to_pd_df(self):
        """Test the __to_pd_df method."""
        test_data = {
            'observations': [
                {'date': '2022-01-01', 'value': '100.5', 'realtime_start': '2023-01-01'},
                {'date': '2022-02-01', 'value': '101.2', 'realtime_start': '2023-01-01'},
                {'date': '2022-03-01', 'value': 'NA', 'realtime_start': '2023-01-01'}  # Test NA handling
            ]
        }
        df = self.fred_api._FredAPI__to_pd_df(test_data)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertTrue(df.index.name == 'date')
        self.assertEqual(df['value'][0], 100.5)
        self.assertTrue(pd.isna(df['value'][2]))
    def test_to_pl_df(self):
        """Test the __to_pl_df method."""
        test_data = {
            'observations': [
                {'date': '2022-01-01', 'value': '100.5', 'realtime_start': '2023-01-01'},
                {'date': '2022-02-01', 'value': '101.2', 'realtime_start': '2023-01-01'}
            ]
        }
        df = self.fred_api._FredAPI__to_pl_df(test_data)
        self.assertIsInstance(df, pl.DataFrame)
        self.assertEqual(len(df), 2)
        first_row = df.filter(pl.col('date') == '2022-01-01')
        first_value = first_row.select('value').to_numpy()[0]
        self.assertEqual(first_value, 100.5)
    def test_fred_get_request(self):
        """Test the __fred_get_request method."""
        test_data = {'test': 'data'}
        original_method = self.fred_api._FredAPI__fred_get_request
        try:
            def mock_implementation(url_endpoint, data=None):
                params = {**(data or {}), 'api_key': self.api_key}
                return test_data
            self.fred_api._FredAPI__fred_get_request = mock_implementation
            result = self.fred_api._FredAPI__fred_get_request('test_endpoint', {'param': 'value'})
            self.assertEqual(result, test_data)
        finally:
            self.fred_api._FredAPI__fred_get_request = original_method

class TestFredMapsAPIPrivateMethods(unittest.TestCase):
    """Test cases for the private methods of FredMapsAPI class."""
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = 'test_api_key'
        self.fred_maps_api = FredMapsAPI(api_key=self.api_key)
    def test_to_gpd_gdf(self):
        """Test the __to_gpd_gdf method."""
        test_data = {
            "meta": {
                "title": "State Boundaries",
                "region": "state", 
                "date": "2022-01-01"
            },
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"STATE": "01", "NAME": "Alabama"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    }
                }
            ]
        }
        original_method = self.fred_maps_api._FredMapsAPI__to_gpd_gdf
        try:
            def mock_implementation(data):
                return gpd.GeoDataFrame({
                    "NAME": ["Alabama"],
                    "STATE": ["01"],
                    "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
                })
            self.fred_maps_api._FredMapsAPI__to_gpd_gdf = mock_implementation
            gdf = self.fred_maps_api._FredMapsAPI__to_gpd_gdf(test_data)
            self.assertIsInstance(gdf, gpd.GeoDataFrame)
            self.assertEqual(len(gdf), 1)
            self.assertEqual(gdf["NAME"][0], "Alabama")
            self.assertEqual(gdf["STATE"][0], "01")
        finally:
            self.fred_maps_api._FredMapsAPI__to_gpd_gdf = original_method
    def test_fred_maps_get_request(self):
        """Test the FRED Maps GET request method."""
        test_data = {"type": "FeatureCollection", "features": []}
        original_method = self.fred_maps_api._FredMapsAPI__fred_maps_get_request
        try:
            def mock_implementation(url_endpoint, data=None):
                params = {**(data or {}), 'api_key': self.api_key}
                self.assertEqual(data.get('param'), 'value')
                return test_data
            self.fred_maps_api._FredMapsAPI__fred_maps_get_request = mock_implementation
            result = self.fred_maps_api._FredMapsAPI__fred_maps_get_request('test_endpoint', {'param': 'value'})
            self.assertEqual(result, test_data)
        finally:
            self.fred_maps_api._FredMapsAPI__fred_maps_get_request = original_method

if __name__ == "__main__":
    unittest.main()
