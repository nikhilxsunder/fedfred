# filepath: /test/objects_test.py
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
Comprehensive unit tests for the objects module.
"""

from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
from fedfred.objects import Category, Series, Tag, Release, ReleaseDate, Source, Element, VintageDate, SeriesGroup
from fedfred.__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__

class TestCategory:
    def test_category_to_object(self):
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
        assert categories[0].name == "Category 1"
        assert categories[1].parent_id == 1

    @pytest.mark.asyncio
    async def test_category_to_object_async(self):
        response = {
            "categories": [
                {"id": 1, "name": "Category 1", "parent_id": None},
                {"id": 2, "name": "Category 2", "parent_id": 1}
            ]
        }
        categories = await Category.to_object_async(response)
        assert isinstance(categories, list)
        assert isinstance(categories[0], Category)
        assert len(categories) == 2
        assert categories[0].id == 1
        assert categories[0].name == "Category 1"
        assert categories[1].parent_id == 1

    def test_invalid_response(self):
        response = {
            "invalid_key": [
                {"id": 1, "name": "Category 1", "parent_id": None}
            ]
        }
        with pytest.raises(ValueError):
            Category.to_object(response)

    def test_empty_response(self):
        response = {
            "categories": []
        }
        with pytest.raises(ValueError):
            Category.to_object(response)

    def test_children_property(self):
        """
        Full coverage for children property:
        """
        # 1) client is None -> RuntimeError
        cat_no_client = Category(id=13, name="Test", parent_id=None, client=None)
        with pytest.raises(RuntimeError, match="Client not set for this Category instance."):
            _ = cat_no_client.children

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        mock_child = Category(id=14, name="Child", parent_id=13, client=None)
        mock_client.get_category_children.return_value = [mock_child]

        cat_with_client = Category(id=13, name="Test", parent_id=None, client=mock_client)
        children = cat_with_client.children

        mock_client.get_category_children.assert_called_once_with(13)
        assert children == [mock_child]
        assert children[0].name == "Child"

    def test_related_property(self):
        """
        Full coverage for related property.
        """
        # 1) client is None -> RuntimeError
        cat_no_client = Category(id=32073, name="Test", parent_id=None, client=None)
        with pytest.raises(RuntimeError, match="Client not set for this Category instance."):
            _ = cat_no_client.related

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        related_cat = Category(id=1, name="Arkansas", parent_id=32073, client=None)
        mock_client.get_category_related.return_value = [related_cat]

        cat_with_client = Category(id=32073, name="Test", parent_id=None, client=mock_client)
        related = cat_with_client.related

        mock_client.get_category_related.assert_called_once_with(32073)
        assert related == [related_cat]
        assert related[0].name == "Arkansas"

    def test_series_property(self):
        """
        Full coverage for Category.series property:
        - raises when client is None
        - delegates to client.get_category_series when client is set
        """
        # 1) client is None -> RuntimeError
        cat_no_client = Category(id=125, name="Test", parent_id=None, client=None)
        with pytest.raises(RuntimeError, match="Client not set for this Category instance."):
            _ = cat_no_client.series

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        mock_series = Series(
            id="S1",
            title="Test Series",
            observation_start="2000-01-01",
            observation_end="2001-01-01",
            frequency="Quarterly",
            frequency_short="Q",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-01-01",
            popularity=1,
        )
        mock_client.get_category_series.return_value = [mock_series]

        cat_with_client = Category(id=125, name="Test", parent_id=None, client=mock_client)
        series_list = cat_with_client.series

        mock_client.get_category_series.assert_called_once_with(125)
        assert series_list == [mock_series]
        assert series_list[0].id == "S1"
        assert series_list[0].frequency == "Quarterly"

    def test_tags_property(self):
        """
        Full coverage for Category.tags property:
        - raises when client is None
        - delegates to client.get_category_tags when client is set
        """
        # 1) client is None -> RuntimeError
        cat_no_client = Category(id=125, name="Test", parent_id=None, client=None)
        with pytest.raises(RuntimeError, match="Client not set for this Category instance."):
            _ = cat_no_client.tags

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        mock_tag = Tag(
            name="Tag1",
            group_id="G1",
            created="2020-01-01",
            popularity=10,
            series_count=5,
            notes="Some notes",
        )
        mock_client.get_category_tags.return_value = [mock_tag]

        cat_with_client = Category(id=125, name="Test", parent_id=None, client=mock_client)
        tags = cat_with_client.tags

        mock_client.get_category_tags.assert_called_once_with(125)
        assert tags == [mock_tag]
        assert tags[0].name == "Tag1"
        assert tags[0].notes == "Some notes"

    def test_related_tags_property(self):
        """
        Full coverage for Category.related_tags property:
        - raises when client is None
        - delegates to client.get_category_related_tags when client is set
        """
        # 1) client is None -> RuntimeError
        cat_no_client = Category(id=125, name="Test", parent_id=None, client=None)
        with pytest.raises(RuntimeError, match="Client not set for this Category instance."):
            _ = cat_no_client.related_tags

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        mock_tag = Tag(
            name="balance",
            group_id="grp",
            created="2020-01-01",
            popularity=10,
            series_count=5,
            notes="Some notes",
        )
        mock_client.get_category_related_tags.return_value = [mock_tag]

        cat_with_client = Category(id=125, name="Test", parent_id=None, client=mock_client)
        related_tags = cat_with_client.related_tags

        mock_client.get_category_related_tags.assert_called_once_with(125)
        assert related_tags == [mock_tag]
        assert related_tags[0].name == "balance"
        assert related_tags[0].notes == "Some notes"

class TestSeries:
    def test_series_to_object(self):
        response = {
            "seriess": [
                {
                    "id": "S1", "title": "Series 1", "observation_start": "2020-01-01", "observation_end": "2020-12-31",
                    "frequency": "Monthly", "frequency_short": "M", "units": "Units", "units_short": "U",
                    "seasonal_adjustment": "None", "seasonal_adjustment_short": "NSA", "last_updated": "2021-01-01",
                    "popularity": 100, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "group_popularity": 50,
                    "notes": "Notes"
                }
            ]
        }
        series = Series.to_object(response)
        assert isinstance(series, list)
        assert isinstance(series[0], Series)
        assert series[0].id == "S1"
        assert series[0].title == "Series 1"
        assert series[0].observation_start == "2020-01-01"
        assert series[0].observation_end == "2020-12-31"
        assert series[0].frequency == "Monthly"
        assert series[0].frequency_short == "M"
        assert series[0].units == "Units"
        assert series[0].units_short == "U"
        assert series[0].seasonal_adjustment == "None"
        assert series[0].seasonal_adjustment_short == "NSA"
        assert series[0].last_updated == "2021-01-01"
        assert series[0].popularity == 100
        assert series[0].realtime_start == "2020-01-01"
        assert series[0].realtime_end == "2020-12-31"
        assert series[0].group_popularity == 50
        assert series[0].notes == "Notes"

    @pytest.mark.asyncio
    async def test_series_to_object_async(self):
        response = {
            "seriess": [
                {
                    "id": "S1", "title": "Series 1", "observation_start": "2020-01-01", "observation_end": "2020-12-31",
                    "frequency": "Monthly", "frequency_short": "M", "units": "Units", "units_short": "U",
                    "seasonal_adjustment": "None", "seasonal_adjustment_short": "NSA", "last_updated": "2021-01-01",
                    "popularity": 100, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "group_popularity": 50,
                    "notes": "Notes"
                }
            ]
        }
        series = await Series.to_object_async(response)
        assert isinstance(series, list)
        assert isinstance(series[0], Series)
        assert series[0].id == "S1"
        assert series[0].title == "Series 1"
        assert series[0].observation_start == "2020-01-01"
        assert series[0].observation_end == "2020-12-31"
        assert series[0].frequency == "Monthly"
        assert series[0].frequency_short == "M"
        assert series[0].units == "Units"
        assert series[0].units_short == "U"
        assert series[0].seasonal_adjustment == "None"
        assert series[0].seasonal_adjustment_short == "NSA"
        assert series[0].last_updated == "2021-01-01"
        assert series[0].popularity == 100
        assert series[0].realtime_start == "2020-01-01"
        assert series[0].realtime_end == "2020-12-31"
        assert series[0].group_popularity == 50
        assert series[0].notes == "Notes"

    def test_invalid_response(self):
        response = {
            "invalid_key": [
                {
                    "id": "S1", "title": "Series 1", "observation_start": "2020-01-01", "observation_end": "2020-12-31",
                    "frequency": "Monthly", "frequency_short": "M", "units": "Units", "units_short": "U",
                    "seasonal_adjustment": "None", "seasonal_adjustment_short": "NSA", "last_updated": "2021-01-01",
                    "popularity": 100, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31",
                    "group_popularity": 50, "notes": None
                }
            ]
        }
        with pytest.raises(ValueError):
            Series.to_object(response)

    def test_empty_response(self):
        response = {
            "seriess": []
        }
        with pytest.raises(ValueError):
            Series.to_object(response)

    def test_categories_property(self):
        """
        Full coverage for Series.categories property:
        - raises when client is None
        - delegates to client.get_series_categories when client is set
        """
        # 1) client is None -> RuntimeError
        series_no_client = Series(
            id="S1",
            title="Test Series",
            observation_start="2000-01-01",
            observation_end="2001-01-01",
            frequency="Monthly",
            frequency_short="M",
            units="Units",
            units_short="U",
            seasonal_adjustment="None",
            seasonal_adjustment_short="NSA",
            last_updated="2025-01-01",
            popularity=1,
            realtime_start="2000-01-01",
            realtime_end="2001-01-01",
            group_popularity=1,
            notes="Notes",
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Series"):
            _ = series_no_client.categories

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        cat1 = Category(id=95, name="Cat 95", parent_id=None, client=None)
        cat2 = Category(id=275, name="Cat 275", parent_id=None, client=None)
        mock_client.get_series_categories.return_value = [cat1, cat2]

        series_with_client = Series(
            id="S1",
            title="Test Series",
            observation_start="2000-01-01",
            observation_end="2001-01-01",
            frequency="Monthly",
            frequency_short="M",
            units="Units",
            units_short="U",
            seasonal_adjustment="None",
            seasonal_adjustment_short="NSA",
            last_updated="2025-01-01",
            popularity=1,
            realtime_start="2000-01-01",
            realtime_end="2001-01-01",
            group_popularity=1,
            notes="Notes",
            client=mock_client,
        )

        categories = series_with_client.categories

        mock_client.get_series_categories.assert_called_once_with("S1")
        assert categories == [cat1, cat2]
        assert [c.id for c in categories] == [95, 275]

    def test_observations_property(self):
        """
        Full coverage for Series.observations property:
        - raises when client is None
        - delegates to client.get_series_observations and returns a DataFrame
        """
        # 1) client is None -> RuntimeError
        series_no_client = Series(
            id="GNPCA",
            title="Test Series",
            observation_start="2000-01-01",
            observation_end="2001-01-01",
            frequency="Annual",
            frequency_short="A",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-01-01",
            popularity=1,
            realtime_start="2000-01-01",
            realtime_end="2001-01-01",
            group_popularity=1,
            notes="Notes",
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Series"):
            _ = series_no_client.observations

        # 2) client present -> delegate and return DataFrame
        mock_client = MagicMock()
        df = pd.DataFrame(
            {
                "date": ["1929-01-01", "1930-01-01"],
                "realtime_start": ["2025-02-13", "2025-02-13"],
                "realtime_end": ["2025-02-13", "2025-02-13"],
                "value": [1202.659, 1100.670],
            }
        )
        mock_client.get_series_observations.return_value = df

        series_with_client = Series(
            id="GNPCA",
            title="Test Series",
            observation_start="1929-01-01",
            observation_end="1930-01-01",
            frequency="Annual",
            frequency_short="A",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-02-13",
            popularity=1,
            realtime_start="1929-01-01",
            realtime_end="1930-01-01",
            group_popularity=1,
            notes="Notes",
            client=mock_client,
        )

        observations = series_with_client.observations

        mock_client.get_series_observations.assert_called_once_with("GNPCA")
        assert isinstance(observations, pd.DataFrame)
        pd.testing.assert_frame_equal(observations, df)

    def test_release_property(self):
        """
        Full coverage for Series.release property:
        - raises when client is None
        - delegates to client.get_series_release when client is set
        """
        # 1) client is None -> RuntimeError
        series_no_client = Series(
            id="GNPCA",
            title="Test Series",
            observation_start="1929-01-01",
            observation_end="1930-01-01",
            frequency="Annual",
            frequency_short="A",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-02-13",
            popularity=1,
            realtime_start="1929-01-01",
            realtime_end="1930-01-01",
            group_popularity=1,
            notes="Notes",
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Series"):
            _ = series_no_client.release

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        mock_release = Release(
            id=1,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Gross National Product",
            press_release=True,
            link="http://example.com",
            notes="Some notes",
        )
        mock_client.get_series_release.return_value = [mock_release]

        series_with_client = Series(
            id="GNPCA",
            title="Test Series",
            observation_start="1929-01-01",
            observation_end="1930-01-01",
            frequency="Annual",
            frequency_short="A",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-02-13",
            popularity=1,
            realtime_start="1929-01-01",
            realtime_end="1930-01-01",
            group_popularity=1,
            notes="Notes",
            client=mock_client,
        )

        rel_list = series_with_client.release

        mock_client.get_series_release.assert_called_once_with("GNPCA")
        assert rel_list == [mock_release]
        assert rel_list[0].name == "Gross National Product"

    def test_tags_property(self):
        """
        Full coverage for Series.tags property:
        - raises when client is None
        - delegates to client.get_series_tags when client is set
        """
        # 1) client is None -> RuntimeError
        series_no_client = Series(
            id="GNPCA",
            title="Test Series",
            observation_start="1929-01-01",
            observation_end="1930-01-01",
            frequency="Annual",
            frequency_short="A",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-02-13",
            popularity=1,
            realtime_start="1929-01-01",
            realtime_end="1930-01-01",
            group_popularity=1,
            notes="Notes",
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Series"):
            _ = series_no_client.tags

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        tag1 = Tag(
            name="nation",
            group_id="geo",
            created="2020-01-01",
            popularity=10,
            series_count=5,
            notes="Nation tag",
        )
        tag2 = Tag(
            name="usa",
            group_id="geo",
            created="2020-01-01",
            popularity=9,
            series_count=4,
            notes="USA tag",
        )
        mock_client.get_series_tags.return_value = [tag1, tag2]

        series_with_client = Series(
            id="GNPCA",
            title="Test Series",
            observation_start="1929-01-01",
            observation_end="1930-01-01",
            frequency="Annual",
            frequency_short="A",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-02-13",
            popularity=1,
            realtime_start="1929-01-01",
            realtime_end="1930-01-01",
            group_popularity=1,
            notes="Notes",
            client=mock_client,
        )

        tags = series_with_client.tags

        mock_client.get_series_tags.assert_called_once_with("GNPCA")
        assert tags == [tag1, tag2]
        assert [t.name for t in tags] == ["nation", "usa"]

    def test_vintagedates_property(self):
        """
        Full coverage for Series.vintagedates property:
        - raises when client is None
        - delegates to client.get_series_vintagedates when client is set
        """
        # 1) client is None -> RuntimeError
        series_no_client = Series(
            id="GNPCA",
            title="Test Series",
            observation_start="1929-01-01",
            observation_end="1930-01-01",
            frequency="Annual",
            frequency_short="A",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-02-13",
            popularity=1,
            realtime_start="1929-01-01",
            realtime_end="1930-01-01",
            group_popularity=1,
            notes="Notes",
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Series"):
            _ = series_no_client.vintagedates

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        vd1 = VintageDate(vintage_date="2025-02-13")
        vd2 = VintageDate(vintage_date="2025-01-15")
        vd3 = VintageDate(vintage_date="2024-12-13")
        mock_client.get_series_vintagedates.return_value = [vd1, vd2, vd3]

        series_with_client = Series(
            id="GNPCA",
            title="Test Series",
            observation_start="1929-01-01",
            observation_end="1930-01-01",
            frequency="Annual",
            frequency_short="A",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-02-13",
            popularity=1,
            realtime_start="1929-01-01",
            realtime_end="1930-01-01",
            group_popularity=1,
            notes="Notes",
            client=mock_client,
        )

        vintages = series_with_client.vintagedates

        mock_client.get_series_vintagedates.assert_called_once_with("GNPCA")
        assert vintages == [vd1, vd2, vd3]
        assert [v.vintage_date for v in vintages] == [
            "2025-02-13",
            "2025-01-15",
            "2024-12-13",
        ]

class TestTag:
    def test_tag_to_object(self):
        response = {
            "tags": [
                {"name": "Tag1", "group_id": "G1", "created": "2020-01-01", "popularity": 10, "series_count": 5, "notes": "Notes"}
            ]
        }
        tag = Tag.to_object(response)
        assert isinstance(tag, list)
        assert isinstance(tag[0], Tag)
        assert tag[0].name == "Tag1"
        assert tag[0].group_id == "G1"
        assert tag[0].created == "2020-01-01"
        assert tag[0].popularity == 10
        assert tag[0].series_count == 5
        assert tag[0].notes == "Notes"

    @pytest.mark.asyncio
    async def test_tag_to_object_async(self):
        response = {
            "tags": [
                {"name": "Tag1", "group_id": "G1", "created": "2020-01-01", "popularity": 10, "series_count": 5, "notes": "Notes"}
            ]
        }
        tag = await Tag.to_object_async(response)
        assert isinstance(tag, list)
        assert isinstance(tag[0], Tag)
        assert tag[0].name == "Tag1"
        assert tag[0].group_id == "G1"
        assert tag[0].created == "2020-01-01"
        assert tag[0].popularity == 10
        assert tag[0].series_count == 5
        assert tag[0].notes == "Notes"

    def test_invalid_response(self):
        response = {
            "invalid_key": [
                {"name": "Tag1", "group_id": "G1", "created": "2020-01-01", "popularity": 10, "series_count": 5, "notes": None}
            ]
        }
        with pytest.raises(ValueError):
            Tag.to_object(response)

    def test_empty_response(self):
        response = {
            "tags": []
        }
        with pytest.raises(ValueError):
            Tag.to_object(response)

    def test_related_tags_property(self):
        """
        Full coverage for Tag.related_tags property:
        - raises when client is None
        - delegates to client.get_related_tags when client is set
        """
        # 1) client is None -> RuntimeError
        tag_no_client = Tag(
            name="nation",
            group_id="geo",
            created="2020-01-01",
            popularity=10,
            series_count=5,
            notes="Nation tag",
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Tag"):
            _ = tag_no_client.related_tags

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        related1 = Tag(
            name="usa",
            group_id="geo",
            created="2020-01-02",
            popularity=9,
            series_count=4,
            notes="USA tag",
        )
        related2 = Tag(
            name="frb",
            group_id="org",
            created="2020-01-03",
            popularity=8,
            series_count=3,
            notes="FRB tag",
        )
        mock_client.get_related_tags.return_value = [related1, related2]

        tag_with_client = Tag(
            name="nation",
            group_id="geo",
            created="2020-01-01",
            popularity=10,
            series_count=5,
            notes="Nation tag",
            client=mock_client,
        )

        related_tags = tag_with_client.related_tags

        mock_client.get_related_tags.assert_called_once_with("nation")
        assert related_tags == [related1, related2]
        assert [t.name for t in related_tags] == ["usa", "frb"]

    def test_series_property(self):
        """
        Full coverage for Tag.series property:
        - raises when client is None
        - delegates to client.get_tags_series when client is set
        """
        # 1) client is None -> RuntimeError
        tag_no_client = Tag(
            name="cpi",
            group_id="gen",
            created="2020-01-01",
            popularity=10,
            series_count=3,
            notes="CPI tag",
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Tag"):
            _ = tag_no_client.series

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        s1 = Series(
            id="CPGDFD02SIA657N",
            title="Series 1",
            observation_start="2000-01-01",
            observation_end="2001-01-01",
            frequency="Monthly",
            frequency_short="M",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-01-01",
            popularity=1,
        )
        s2 = Series(
            id="CPGDFD02SIA659N",
            title="Series 2",
            observation_start="2000-01-01",
            observation_end="2001-01-01",
            frequency="Monthly",
            frequency_short="M",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-01-01",
            popularity=2,
        )
        mock_client.get_tags_series.return_value = [s1, s2]

        tag_with_client = Tag(
            name="cpi",
            group_id="gen",
            created="2020-01-01",
            popularity=10,
            series_count=3,
            notes="CPI tag",
            client=mock_client,
        )

        series_list = tag_with_client.series

        mock_client.get_tags_series.assert_called_once_with("cpi")
        assert series_list == [s1, s2]
        assert [s.id for s in series_list] == ["CPGDFD02SIA657N", "CPGDFD02SIA659N"]

class TestRelease:
    def test_release_to_object(self):
        response = {
            "releases": [
                {"id": 1, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "name": "Release 1", "press_release": True, "link": "http://example.com", "notes": "Notes"}
            ]
        }
        release = Release.to_object(response)
        assert isinstance(release, list)
        assert isinstance(release[0], Release)
        assert release[0].id == 1
        assert release[0].name == "Release 1"
        assert release[0].realtime_start == "2020-01-01"
        assert release[0].realtime_end == "2020-12-31"
        assert release[0].press_release is True
        assert release[0].link == "http://example.com"
        assert release[0].notes == "Notes"

    @pytest.mark.asyncio
    async def test_release_to_object_async(self):
        response = {
            "releases": [
                {"id": 1, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "name": "Release 1", "press_release": True, "link": "http://example.com", "notes": "Notes"}
            ]
        }
        release = await Release.to_object_async(response)
        assert isinstance(release, list)
        assert isinstance(release[0], Release)
        assert release[0].id == 1
        assert release[0].name == "Release 1"
        assert release[0].realtime_start == "2020-01-01"
        assert release[0].realtime_end == "2020-12-31"
        assert release[0].press_release is True
        assert release[0].link == "http://example.com"
        assert release[0].notes == "Notes"

    def test_invalid_response(self):
        response = {
            "invalid_key": [
                {"id": 1, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "name": "Release 1", "press_release": True, "link": None, "notes": None}
            ]
        }
        with pytest.raises(ValueError):
            Release.to_object(response)

    def test_empty_response(self):
        response = {
            "releases": []
        }
        with pytest.raises(ValueError):
            Release.to_object(response)

    def test_dates_property(self):
        """
        Full coverage for Release.dates property:
        - raises when client is None
        - delegates to client.get_release_dates when client is set
        """
        # 1) client is None -> RuntimeError
        release_no_client = Release(
            id=82,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Release"):
            _ = release_no_client.dates

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        d1 = ReleaseDate(release_id=82, date="1997-02-10", release_name="Test Release")
        d2 = ReleaseDate(release_id=82, date="1998-02-10", release_name="Test Release")
        d3 = ReleaseDate(release_id=82, date="1999-02-04", release_name="Test Release")
        mock_client.get_release_dates.return_value = [d1, d2, d3]

        release_with_client = Release(
            id=82,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=mock_client,
        )

        dates = release_with_client.dates

        mock_client.get_release_dates.assert_called_once_with(82)

    def test_series_property(self):
        """
        Full coverage for Release.series property:
        - raises when client is None
        - delegates to client.get_release_series when client is set
        """
        # 1) client is None -> RuntimeError
        release_no_client = Release(
            id=51,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Release"):
            _ = release_no_client.series

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        s1 = Series(
            id="BOMTVLM133S",
            title="Series 1",
            observation_start="2000-01-01",
            observation_end="2001-01-01",
            frequency="Monthly",
            frequency_short="M",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-01-01",
            popularity=1,
        )
        s2 = Series(
            id="BOMVGMM133S",
            title="Series 2",
            observation_start="2000-01-01",
            observation_end="2001-01-01",
            frequency="Monthly",
            frequency_short="M",
            units="Index",
            units_short="Idx",
            seasonal_adjustment="Not Seasonally Adjusted",
            seasonal_adjustment_short="NSA",
            last_updated="2025-01-01",
            popularity=2,
        )
        mock_client.get_release_series.return_value = [s1, s2]

        release_with_client = Release(
            id=51,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=mock_client,
        )

        series_list = release_with_client.series

        mock_client.get_release_series.assert_called_once_with(51)
        assert series_list == [s1, s2]
        assert [s.id for s in series_list] == ["BOMTVLM133S", "BOMVGMM133S"]

    def test_sources_property(self):
        """
        Full coverage for Release.sources property:
        - raises when client is None
        - delegates to client.get_release_sources when client is set
        """
        # 1) client is None -> RuntimeError
        release_no_client = Release(
            id=51,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Release"):
            _ = release_no_client.sources

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        src1 = Source(
            id=1,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="U.S. Department of Commerce: Bureau of Economic Analysis",
            link=None,
            notes=None,
        )
        src2 = Source(
            id=2,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="U.S. Department of Commerce: Census Bureau",
            link=None,
            notes=None,
        )
        mock_client.get_release_sources.return_value = [src1, src2]

        release_with_client = Release(
            id=51,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=mock_client,
        )

        sources = release_with_client.sources

        mock_client.get_release_sources.assert_called_once_with(51)
        assert sources == [src1, src2]
        assert [s.name for s in sources] == [
            "U.S. Department of Commerce: Bureau of Economic Analysis",
            "U.S. Department of Commerce: Census Bureau",
        ]

    def test_tags_property(self):
        """
        Full coverage for Release.tags property:
        - raises when client is None
        - delegates to client.get_release_tags when client is set
        """
        # 1) client is None -> RuntimeError
        release_no_client = Release(
            id=51,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Release"):
            _ = release_no_client.tags

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        tag1 = Tag(
            name="gdp",
            group_id="gen",
            created="2020-01-01",
            popularity=10,
            series_count=5,
            notes="GDP tag",
        )
        mock_client.get_release_tags.return_value = [tag1]

        release_with_client = Release(
            id=51,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=mock_client,
        )

        tags = release_with_client.tags

        mock_client.get_release_tags.assert_called_once_with(51)
        assert tags == [tag1]
        assert [t.name for t in tags] == ["gdp"]

    def test_related_tags_property(self):
        """
        Full coverage for Release.related_tags property:
        - raises when client is None
        - delegates to client.get_release_related_tags when client is set
        """
        # 1) client is None -> RuntimeError
        release_no_client = Release(
            id=51,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Release"):
            _ = release_no_client.related_tags

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        tag1 = Tag(
            name="economy",
            group_id="gen",
            created="2020-01-01",
            popularity=8,
            series_count=3,
            notes="Economy tag",
        )
        mock_client.get_release_related_tags.return_value = [tag1]

        release_with_client = Release(
            id=51,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=mock_client,
        )

        related_tags = release_with_client.related_tags

        mock_client.get_release_related_tags.assert_called_once_with(51)
        assert related_tags == [tag1]
        assert [t.name for t in related_tags] == ["economy"]

    def test_tables_property(self):
        """
        Full coverage for Release.tables property:
        - raises when client is None
        - delegates to client.get_release_tables when client is set
        """
        # 1) client is None -> RuntimeError
        release_no_client = Release(
            id=51,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Release"):
            _ = release_no_client.tables

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        table1 = Element(
            element_id=1,
            release_id=51,
            series_id="DGDSRL1A225NBEA",
            parent_id=0,
            line="Line 1",
            type="Type 1",
            name="Element 1",
            level="Level 1",
            children=None,
        )
        mock_client.get_release_tables.return_value = [table1]

        release_with_client = Release(
            id=51,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Release",
            press_release=True,
            link=None,
            notes=None,
            client=mock_client,
        )

        tables = release_with_client.tables

        mock_client.get_release_tables.assert_called_once_with(51)
        assert tables == [table1]
        assert [t.series_id for t in tables] == ["DGDSRL1A225NBEA"]

class TestReleaseDate:
    def test_release_date_to_object(self):
        response = {
            "release_dates": [
                {"release_id": 1, "date": "2020-01-01", "release_name": "Release 1"}
            ]
        }
        release_date = ReleaseDate.to_object(response)
        assert isinstance(release_date, list)
        assert isinstance(release_date[0], ReleaseDate)
        assert release_date[0].release_id == 1
        assert release_date[0].date == "2020-01-01"
        assert release_date[0].release_name == "Release 1"

    @pytest.mark.asyncio
    async def test_release_date_to_object_async(self):
        response = {
            "release_dates": [
                {"release_id": 1, "date": "2020-01-01", "release_name": "Release 1"}
            ]
        }
        release_date = await ReleaseDate.to_object_async(response)
        assert isinstance(release_date, list)
        assert isinstance(release_date[0], ReleaseDate)
        assert release_date[0].release_id == 1
        assert release_date[0].date == "2020-01-01"
        assert release_date[0].release_name == "Release 1"

    def test_invalid_response(self):
        response = {
            "invalid_key": [
                {"release_id": 1, "date": "2020-01-01", "release_name": None}
            ]
        }
        with pytest.raises(ValueError):
            ReleaseDate.to_object(response)

    def test_empty_response(self):
        response = {
            "release_dates": []
        }
        with pytest.raises(ValueError):
            ReleaseDate.to_object(response)

class TestSource:
    def test_source_to_object(self):
        response = {
            "sources": [
                {"id": 1, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "name": "Source 1", "link": "http://example.com", "notes": "Notes"}
            ]
        }
        source = Source.to_object(response)
        assert isinstance(source, list)
        assert isinstance(source[0], Source)
        assert source[0].id == 1
        assert source[0].name == "Source 1"
        assert source[0].realtime_start == "2020-01-01"
        assert source[0].realtime_end == "2020-12-31"
        assert source[0].link == "http://example.com"
        assert source[0].notes == "Notes"

    @pytest.mark.asyncio
    async def test_source_to_object_async(self):
        response = {
            "sources": [
                {"id": 1, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "name": "Source 1", "link": "http://example.com", "notes": "Notes"}
            ]
        }
        source = await Source.to_object_async(response)
        assert isinstance(source, list)
        assert isinstance(source[0], Source)
        assert source[0].id == 1
        assert source[0].name == "Source 1"
        assert source[0].realtime_start == "2020-01-01"
        assert source[0].realtime_end == "2020-12-31"
        assert source[0].link == "http://example.com"
        assert source[0].notes == "Notes"

    def test_invalid_response(self):
        response = {
            "invalid_key": [
                {"id": 1, "realtime_start": "2020-01-01", "realtime_end": "2020-12-31", "name": None, "link": None, "notes": None}
            ]
        }
        with pytest.raises(ValueError):
            Source.to_object(response)

    def test_empty_response(self):
        response = {
            "sources": []
        }
        with pytest.raises(ValueError):
            Source.to_object(response)

    def test_releases_property(self):
        """
        Full coverage for Source.releases property:
        - raises when client is None
        - delegates to client.get_source_releases when client is set
        """
        # 1) client is None -> RuntimeError
        source_no_client = Source(
            id=1,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Source",
            link=None,
            notes=None,
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Source"):
            _ = source_no_client.releases

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        rel1 = Release(
            id=1,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Release 1",
            press_release=True,
            link="http://example.com",
            notes="Some notes",
        )
        mock_client.get_source_releases.return_value = [rel1]

        source_with_client = Source(
            id=1,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Test Source",
            link=None,
            notes=None,
            client=mock_client,
        )

        releases = source_with_client.releases

        mock_client.get_source_releases.assert_called_once_with(1)
        assert releases == [rel1]
        assert releases[0].name == "Release 1"

class TestElement:
    def test_element_to_object(self):
        response = {
            "elements": {
                "1": {
                    "element_id": 1,
                    "release_id": 1,
                    "series_id": "S1",
                    "parent_id": 0,
                    "line": "Line 1",
                    "type": "Type 1",
                    "name": "Element 1",
                    "level": "Level 1",
                    "children": [
                        {
                            "element_id": 2,
                            "release_id": 1,
                            "series_id": "S1",
                            "parent_id": 1,
                            "line": "Line 2",
                            "type": "Type 2",
                            "name": "Element 2",
                            "level": "Level 2",
                            "children": []
                        }
                    ]
                }
            }
        }
        element = Element.to_object(response)
        assert isinstance(element, list)
        assert isinstance(element[0], Element)
        assert element[0].element_id == 1
        assert element[0].release_id == 1
        assert element[0].series_id == "S1"
        assert element[0].parent_id == 0
        assert element[0].line == "Line 1"
        assert element[0].type == "Type 1"
        assert element[0].name == "Element 1"
        assert element[0].level == "Level 1"
        assert isinstance(element[0].children, list)
        assert isinstance(element[0].children[0], Element)
        assert element[0].children[0].element_id == 2
        assert element[0].children[0].release_id == 1
        assert element[0].children[0].series_id == "S1"
        assert element[0].children[0].parent_id == 1
        assert element[0].children[0].line == "Line 2"
        assert element[0].children[0].type == "Type 2"
        assert element[0].children[0].name == "Element 2"
        assert element[0].children[0].level == "Level 2"

        # No-children branch
        no_children_response = {
            "elements": {
                "1": {
                    "element_id": 1,
                    "release_id": 1,
                    "series_id": "S1",
                    "parent_id": 0,
                    "line": "Line 1",
                    "type": "Type 1",
                    "name": "Element 1",
                    "level": "Level 1",
                    "children": []
                }
            }
        }
        no_children_element = Element.to_object(no_children_response)
        assert isinstance(no_children_element, list)
        assert isinstance(no_children_element[0], Element)
        assert no_children_element[0].element_id == 1
        assert no_children_element[0].release_id == 1
        assert no_children_element[0].series_id == "S1"
        assert no_children_element[0].parent_id == 0
        assert no_children_element[0].line == "Line 1"
        assert no_children_element[0].type == "Type 1"
        assert no_children_element[0].name == "Element 1"
        assert no_children_element[0].level == "Level 1"
        # children is now None when the input children list is empty
        assert no_children_element[0].children is None

    @pytest.mark.asyncio
    async def test_element_to_object_async(self):
        response = {
            "elements": {
                "1": {
                    "element_id": 1,
                    "release_id": 1,
                    "series_id": "S1",
                    "parent_id": 0,
                    "line": "Line 1",
                    "type": "Type 1",
                    "name": "Element 1",
                    "level": "Level 1",
                    "children": [
                        {
                            "element_id": 2,
                            "release_id": 1,
                            "series_id": "S1",
                            "parent_id": 1,
                            "line": "Line 2",
                            "type": "Type 2",
                            "name": "Element 2",
                            "level": "Level 2",
                            "children": []
                        }
                    ]
                }
            }
        }
        element = await Element.to_object_async(response)
        assert isinstance(element, list)
        assert isinstance(element[0], Element)
        assert element[0].element_id == 1
        assert element[0].release_id == 1
        assert element[0].series_id == "S1"
        assert element[0].parent_id == 0
        assert element[0].line == "Line 1"
        assert element[0].type == "Type 1"
        assert element[0].name == "Element 1"
        assert element[0].level == "Level 1"
        assert isinstance(element[0].children, list)
        assert isinstance(element[0].children[0], Element)
        assert element[0].children[0].element_id == 2
        assert element[0].children[0].release_id == 1
        assert element[0].children[0].series_id == "S1"
        assert element[0].children[0].parent_id == 1
        assert element[0].children[0].line == "Line 2"
        assert element[0].children[0].type == "Type 2"
        assert element[0].children[0].name == "Element 2"
        assert element[0].children[0].level == "Level 2"

    def test_invalid_response(self):
        response = {
            "invalid_key": {
                "1": {
                    "element_id": 1,
                    "release_id": 1,
                    "series_id": "S1",
                    "parent_id": 0,
                    "line": "Line 1",
                    "type": None,
                    "name": None,
                    "level": None,
                    "children": []
                }
            }
        }
        with pytest.raises(ValueError):
            Element.to_object(response)

    def test_empty_response(self):
        response = {
            "elements": {}
        }
        with pytest.raises(ValueError):
            Element.to_object(response)

    def test_release_property(self):
        """
        Full coverage for Element.release property:
        - raises when client is None
        - delegates to client.get_release when client is set
        """
        # 1) client is None -> RuntimeError
        element_no_client = Element(
            element_id=1,
            release_id=53,
            series_id="DGDSRL1A225NBEA",
            parent_id=0,
            line="Line 1",
            type="Type 1",
            name="Element 1",
            level="Level 1",
            children=None,
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Element"):
            _ = element_no_client.release

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        mock_release = Release(
            id=53,
            realtime_start="2020-01-01",
            realtime_end="2020-12-31",
            name="Real Gross Domestic Product",
            press_release=True,
            link=None,
            notes=None,
        )
        mock_client.get_release.return_value = [mock_release]

        element_with_client = Element(
            element_id=1,
            release_id=53,
            series_id="DGDSRL1A225NBEA",
            parent_id=0,
            line="Line 1",
            type="Type 1",
            name="Element 1",
            level="Level 1",
            children=None,
            client=mock_client,
        )

        releases = element_with_client.release

        mock_client.get_release.assert_called_once_with(53)
        assert releases == [mock_release]
        assert releases[0].name == "Real Gross Domestic Product"

    def test_series_property(self):
        """
        Full coverage for Element.series property:
        - raises when client is None
        - delegates to client.get_series when client is set
        """
        # 1) client is None -> RuntimeError
        element_no_client = Element(
            element_id=1,
            release_id=53,
            series_id="DGDSRL1A225NBEA",
            parent_id=0,
            line="Line 1",
            type="Type 1",
            name="Element 1",
            level="Level 1",
            children=None,
            client=None,
        )
        with pytest.raises(RuntimeError, match="Client is not set for this Element"):
            _ = element_no_client.series

        # 2) client present -> delegate and return value
        mock_client = MagicMock()
        mock_series = Series(
            id="DGDSRL1A225NBEA",
            title="Real Gross Domestic Product",
            observation_start="1947-01-01",
            observation_end="2023-01-01",
            frequency="Quarterly",
            frequency_short="Q",
            units="Billions of Chained 2012 Dollars",
            units_short="Bil. of Chn. 2012 $",
            seasonal_adjustment="Seasonally Adjusted Annual Rate",
            seasonal_adjustment_short="SAAR",
            last_updated="2024-01-01",
            popularity=100,
        )
        mock_client.get_series.return_value = [mock_series]

        element_with_client = Element(
            element_id=1,
            release_id=53,
            series_id="DGDSRL1A225NBEA",
            parent_id=0,
            line="Line 1",
            type="Type 1",
            name="Element 1",
            level="Level 1",
            children=None,
            client=mock_client,
        )

        series = element_with_client.series

        mock_client.get_series.assert_called_once_with("DGDSRL1A225NBEA")
        assert series == [mock_series]
        assert series[0].title == "Real Gross Domestic Product"

class TestVintageDate:
    def test_vintage_date_to_object(self):
        response = {
            "vintage_dates": ["2020-01-01"]
        }
        vintage_date = VintageDate.to_object(response)
        assert isinstance(vintage_date, list)
        assert isinstance(vintage_date[0], VintageDate)
        assert vintage_date[0].vintage_date == "2020-01-01"

    @pytest.mark.asyncio
    async def test_vintage_date_to_object_async(self):
        response = {
            "vintage_dates": ["2020-01-01"]
        }
        vintage_date = await VintageDate.to_object_async(response)
        assert isinstance(vintage_date, list)
        assert isinstance(vintage_date[0], VintageDate)
        assert vintage_date[0].vintage_date == "2020-01-01"

    def test_invalid_response(self):
        response = {
            "invalid_key": ["2020-01-01"]
        }
        with pytest.raises(ValueError):
            VintageDate.to_object(response)

    def test_empty_response(self):
        response = {
            "vintage_dates": []
        }
        with pytest.raises(ValueError):
            VintageDate.to_object(response)

class TestSeriesGroup:
    def test_series_group_to_object(self):
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
        assert series_group[0].series_group == "Group 1"
        assert series_group[0].season == "Season 1"
        assert series_group[0].units == "Units"
        assert series_group[0].frequency == "Monthly"
        assert series_group[0].min_date == "2020-01-01"
        assert series_group[0].max_date == "2020-12-31"

    @pytest.mark.asyncio
    async def test_series_group_to_object_async(self):
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
        series_group = await SeriesGroup.to_object_async(response)
        assert isinstance(series_group, list)
        assert isinstance(series_group[0], SeriesGroup)
        assert series_group[0].title == "Group 1"
        assert series_group[0].region_type == "Region 1"
        assert series_group[0].series_group == "Group 1"
        assert series_group[0].season == "Season 1"
        assert series_group[0].units == "Units"
        assert series_group[0].frequency == "Monthly"
        assert series_group[0].min_date == "2020-01-01"
        assert series_group[0].max_date == "2020-12-31"

    def test_invalid_response(self):
        response = {
            "invalid_key": {
                "title": "Group 1",
                "region_type": "Region 1",
                "series_group": None,
                "season": None,
                "units": None,
                "frequency": None,
                "min_date": None,
                "max_date": None
            }
        }
        with pytest.raises(ValueError):
            SeriesGroup.to_object(response)

    def test_empty_response(self):
        response = {}
        with pytest.raises(ValueError):
            SeriesGroup.to_object(response)

    def test_empty_series_group(self):
        response = {
            "series_group": []
        }
        with pytest.raises(ValueError):
            SeriesGroup.to_object(response)
