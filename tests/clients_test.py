# filepath: /test/clients_test.py
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
Comprehensive unit tests for the clients module.
"""

import time
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from collections import deque
from datetime import datetime
import pytest
import httpx
import tenacity
import geopandas as gpd
from fedfred.clients import FredAPI
from fedfred.__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__

class TestFredAPI:
    # Dunder methods
    def test_init(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=42)
        assert api.base_url == 'https://api.stlouisfed.org/fred'
        assert api.api_key == "testkey"
        assert api.cache_mode is True
        assert api.cache_size == 42
        assert hasattr(api, "cache")
        assert api.max_requests_per_minute == 120
        assert isinstance(api.request_times, type(deque()))
        assert hasattr(api, "lock")
        assert hasattr(api, "semaphore")
        assert isinstance(api.Maps, FredAPI.MapsAPI)
        assert isinstance(api.Async, FredAPI.AsyncAPI)

    def test_repr(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        assert isinstance(repr(api), str)
        assert "FredAPI" in repr(api)

    def test_str(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        assert isinstance(str(api), str)
        assert "FredAPI" in str(api)

    def test_hash(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        assert isinstance(hash(api), int)

    def test_eq(self):
        api1 = FredAPI("testkey", cache_mode=True, cache_size=10)
        api2 = FredAPI("testkey", cache_mode=True, cache_size=10)
        api3 = FredAPI("testkey", cache_mode=False, cache_size=5)
        assert api1 == api2
        assert api1 != api3

        a = FredAPI("key", cache_mode=True, cache_size=10)
        assert (a == 42) is False
        assert (a == "not a FredAPI") is False

    def test_del(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        api.cache["GDP"] = "Gross Domestic Product"
        api.__delitem__("GDP")
        assert "GDP" not in api.cache

        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        with pytest.raises(AttributeError, match="'NON_EXISTENT_KEY' not found in cache."):
            api.__delitem__("NON_EXISTENT_KEY")

    def test_getitem(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        api.cache["GDP"] = "Gross Domestic Product"
        assert api["GDP"] == "Gross Domestic Product"

        with pytest.raises(AttributeError):
            _ = api["NON_EXISTENT_KEY"]

    def test_len(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        api.cache["GDP"] = "Gross Domestic Product"
        assert len(api) == 1

    def test_contains(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        api.cache["GDP"] = "Gross Domestic Product"
        assert "GDP" in api
        assert "NON_EXISTENT_KEY" not in api

    def test_setitem(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        api["GDP"] = "Gross Domestic Product"
        assert api["GDP"] == "Gross Domestic Product"

    def test_delitem(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        api.cache["GDP"] = "Gross Domestic Product"
        del api.cache["GDP"]
        with pytest.raises(KeyError):
            _ = api.cache["GDP"]

    def test_call(self):
        api = FredAPI("testkey1234", cache_mode=True, cache_size=5)
        summary = api()
        assert isinstance(summary, str)
        assert "FredAPI Instance" in summary
        assert "Base URL" in summary
        assert "Cache Mode: Enabled" in summary
        assert "Cache Size: 0 items" in summary
        assert "API Key: ****1234" in summary

    # Private methods
    @pytest.mark.parametrize(
        "request_offsets,should_sleep",
        [
            ([-70], False),         # Only one old request, after cleanup and append: 1 (should NOT sleep)
            ([-10], False),         # Only one recent request, after append: 2 (should NOT sleep)
            ([-10, -5], True),      # Two recent requests, after append: 3 (should sleep)
            ([-10, -5, -1], True),  # Three recent requests, after append: 4 (should sleep)
        ]
    )
    def test_rate_limited(self, request_offsets, should_sleep):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        api.max_requests_per_minute = 3

        now = time.time()
        api.request_times.clear()
        api.request_times.extend([now + offset for offset in request_offsets])

        with patch("time.sleep") as mock_sleep:
            api._FredAPI__rate_limited()
            if should_sleep:
                assert mock_sleep.called
                sleep_args = mock_sleep.call_args[0][0]
                assert sleep_args > 0
            else:
                mock_sleep.assert_not_called()

    @pytest.mark.parametrize(
        "cache_mode,data,should_validate",
        [
            (False, {"baz": 1}, True),   # cache off, with data
            (True, {"baz": 1}, True),    # cache on, with data
            (False, None, False),        # cache off, no data
            (True, None, False),         # cache on, no data
        ]
    )
    def test_fred_get_request(self, cache_mode, data, should_validate):
        api = FredAPI("testkey", cache_mode=cache_mode, cache_size=10)
        fake_json = {"foo": "bar"}

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = fake_json

        with patch("httpx.Client.get", return_value=mock_response) as mock_get:
            with patch("fedfred.helpers.FredHelpers.parameter_validation") as mock_validate:
                result = api._FredAPI__fred_get_request("/test", data=data)
                assert result == fake_json
                mock_get.assert_called_once()
                if should_validate:
                    mock_validate.assert_called_once()
                else:
                    mock_validate.assert_not_called()

    # Public methods
    ## Categories
    def test_get_category(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "categories": [
                {
                    "id": 125,
                    "name": "Trade Balance",
                    "parent_id": 13
                }
            ]
        }
        fake_category = [MagicMock()]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Category.to_object", return_value=fake_category) as mock_to_object:
                result = api.get_category(125)
                mock_get.assert_called_once_with("/category", {"category_id": 125})
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_category

    def test_get_category_children(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "categories": [
                {
                    "id": 16,
                    "name": "Exports",
                    "parent_id": 13
                },
                {
                    "id": 17,
                    "name": "Imports",
                    "parent_id": 13
                }
            ]
        }
        fake_category = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.Category.to_object", return_value=fake_category) as mock_to_object:
                    result = api.get_category_children(13, realtime_start=dt_start, realtime_end=dt_end)
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/category/children",
                        {"category_id": 13, "realtime_start": "converted", "realtime_end": "converted"}
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_category

    def test_get_category_related(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "categories": [
                {
                    "id": 149,
                    "name": "Arkansas",
                    "parent_id": 27281
                },
                {
                    "id": 150,
                    "name": "Illinois",
                    "parent_id": 27281
                }
            ]
        }
        fake_category = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.Category.to_object", return_value=fake_category) as mock_to_object:
                    result = api.get_category_related(27281, realtime_start=dt_start, realtime_end=dt_end)
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/category/related",
                        {"category_id": 27281, "realtime_start": "converted", "realtime_end": "converted"}
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_category

    def test_get_category_series(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2017-08-01",
            "realtime_end": "2017-08-01",
            "order_by": "series_id",
            "sort_order": "asc",
            "count": 45,
            "offset": 0,
            "limit": 1000,
            "seriess": [
                {
                    "id": "BOPBCA",
                    "realtime_start": "2017-08-01",
                    "realtime_end": "2017-08-01",
                    "title": "Balance on Current Account (DISCONTINUED)",
                    "observation_start": "1960-01-01",
                    "observation_end": "2014-01-01",
                    "frequency": "Quarterly",
                    "frequency_short": "Q",
                    "units": "Billions of Dollars",
                    "units_short": "Bil. of $",
                    "seasonal_adjustment": "Seasonally Adjusted",
                    "seasonal_adjustment_short": "SA",
                    "last_updated": "2014-06-18 08:41:28-05",
                    "popularity": 32,
                    "group_popularity": 34,
                    "notes": "This series has been discontinued as a result of the comprehensive restructuring of the international economic accounts (http:\/\/www.bea.gov\/international\/modern.htm). For a crosswalk of the old and new series in FRED see: http:\/\/research.stlouisfed.org\/CompRevisionReleaseID49.xlsx."
                },
                {
                    "id": "BOPBCAA",
                    "realtime_start": "2017-08-01",
                    "realtime_end": "2017-08-01",
                    "title": "Balance on Current Account (DISCONTINUED)",
                    "observation_start": "1960-01-01",
                    "observation_end": "2013-01-01",
                    "frequency": "Annual",
                    "frequency_short": "A",
                    "units": "Billions of Dollars",
                    "units_short": "Bil. of $",
                    "seasonal_adjustment": "Not Seasonally Adjusted",
                    "seasonal_adjustment_short": "NSA",
                    "last_updated": "2014-06-18 08:41:28-05",
                    "popularity": 14,
                    "group_popularity": 34,
                    "notes": "This series has been discontinued as a result of the comprehensive restructuring of the international economic accounts (http:\/\/www.bea.gov\/international\/modern.htm). For a crosswalk of the old and new series in FRED see: http:\/\/research.stlouisfed.org\/CompRevisionReleaseID49.xlsx."
                },
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_dt_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=lambda x: "joined") as mock_list_conv:
                    with patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
                        result = api.get_category_series(
                            125,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            limit=50,
                            offset=10,
                            order_by="title",
                            sort_order="desc",
                            filter_variable="frequency",
                            filter_value="Annual",
                            tag_names=tag_list,
                            exclude_tag_names=exclude_tag_list,
                        )
                        assert mock_dt_conv.call_count == 2
                        assert mock_list_conv.call_count == 2
                        mock_get.assert_called_once_with(
                            "/category/series",
                            {
                                "category_id": 125,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "limit": 50,
                                "offset": 10,
                                "order_by": "title",
                                "sort_order": "desc",
                                "filter_variable": "frequency",
                                "filter_value": "Annual",
                                "tag_names": "joined",
                                "exclude_tag_names": "joined",
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_series

        with pytest.raises(ValueError):
            api.get_category_series(-1)
        with pytest.raises(ValueError):
            api.get_category_series("not_an_int")

    def test_get_category_tags(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-13",
            "realtime_end": "2013-08-13",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 21,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "bea",
                    "group_id": "src",
                    "notes": "U.S. Department of Commerce: Bureau of Economic Analysis",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 87,
                    "series_count": 24
                },
                {
                    "name": "nation",
                    "group_id": "geot",
                    "notes": "Country Level",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 100,
                    "series_count": 24
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=lambda x: "macro,gdp") as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
                        result = api.get_category_tags(
                            125,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names=tag_list
                        )
                        assert mock_conv.call_count == 2
                        mock_list_conv.assert_called_once_with(tag_list)
                        mock_get.assert_called_once_with(
                            "/category/tags",
                            {
                                "category_id": 125,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro,gdp"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion") as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
                        result = api.get_category_tags(
                            125,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names="macro"
                        )
                        assert mock_conv.call_count == 2
                        mock_list_conv.assert_not_called()
                        mock_get.assert_called_once_with(
                            "/category/tags",
                            {
                                "category_id": 125,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted"):
                with patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=lambda x: "macro,gdp"):
                    with patch("fedfred.clients.Tag.to_object", return_value=fake_tags):
                        result = api.get_category_tags(
                            125,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names=tag_list,
                            tag_group_id=42,
                            search_text="foo",
                            limit=5,
                            offset=2,
                            order_by="series_count",
                            sort_order="desc"
                        )
                        mock_get.assert_called_once_with(
                            "/category/tags",
                            {
                                "category_id": 125,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro,gdp",
                                "tag_group_id": 42,
                                "search_text": "foo",
                                "limit": 5,
                                "offset": 2,
                                "order_by": "series_count",
                                "sort_order": "desc"
                            }
                        )
                        assert result == fake_tags

    def test_get_category_related_tags(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-13",
            "realtime_end": "2013-08-13",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 7,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "balance",
                    "group_id": "gen",
                    "notes": "",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 65,
                    "series_count": 4
                },
                {
                    "name": "bea",
                    "group_id": "src",
                    "notes": "U.S. Department of Commerce: Bureau of Economic Analysis",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 87,
                    "series_count": 4
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=",".join) as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
                        result = api.get_category_related_tags(
                            125,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names=tag_list,
                            exclude_tag_names=exclude_tag_list,
                            tag_group_id="grp",
                            search_text="foo",
                            limit=5,
                            offset=2,
                            order_by="series_count",
                            sort_order="desc"
                        )
                        assert mock_conv.call_count == 2
                        assert mock_list_conv.call_count == 2
                        mock_get.assert_called_once_with(
                            "/category/related_tags",
                            {
                                "category_id": 125,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro,gdp",
                                "exclude_tag_names": "foo,bar",
                                "tag_group_id": "grp",
                                "search_text": "foo",
                                "limit": 5,
                                "offset": 2,
                                "order_by": "series_count",
                                "sort_order": "desc"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion") as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
                        result = api.get_category_related_tags(
                            125,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names="macro",
                            exclude_tag_names="foo"
                        )
                        assert mock_conv.call_count == 2
                        mock_list_conv.assert_not_called()
                        mock_get.assert_called_once_with(
                            "/category/related_tags",
                            {
                                "category_id": 125,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro",
                                "exclude_tag_names": "foo"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
                result = api.get_category_related_tags(125)
                mock_get.assert_called_once_with(
                    "/category/related_tags",
                    {"category_id": 125}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_tags

    ## Releases
    def test_get_releases(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-13",
            "realtime_end": "2013-08-13",
            "order_by": "release_id",
            "sort_order": "asc",
            "count": 158,
            "offset": 0,
            "limit": 1000,
            "releases": [
                {
                    "id": 9,
                    "realtime_start": "2013-08-13",
                    "realtime_end": "2013-08-13",
                    "name": "Advance Monthly Sales for Retail and Food Services",
                    "press_release": True,
                    "link": "http://www.census.gov/retail/"
                },
                {
                    "id": 10,
                    "realtime_start": "2013-08-13",
                    "realtime_end": "2013-08-13",
                    "name": "Consumer Price Index",
                    "press_release": True,
                    "link": "http://www.bls.gov/cpi/"
                }
            ]
        }
        fake_releases = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
                    result = api.get_releases(
                        realtime_start=dt_start,
                        realtime_end=dt_end,
                        limit=50,
                        offset=10,
                        order_by="name",
                        sort_order="desc"
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/releases",
                        {
                            "realtime_start": "converted",
                            "realtime_end": "converted",
                            "limit": 50,
                            "offset": 10,
                            "order_by": "name",
                            "sort_order": "desc"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_releases

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
                result = api.get_releases(
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31",
                    limit=10,
                    offset=2,
                    order_by="release_id",
                    sort_order="asc"
                )
                mock_get.assert_called_once_with(
                    "/releases",
                    {
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31",
                        "limit": 10,
                        "offset": 2,
                        "order_by": "release_id",
                        "sort_order": "asc"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
                result = api.get_releases()
                mock_get.assert_called_once_with("/releases", {})
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

    def test_get_releases_dates(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-01-01",
            "realtime_end": "9999-12-31",
            "order_by": "release_date",
            "sort_order": "desc",
            "count": 1129,
            "offset": 0,
            "limit": 1000,
            "release_dates": [
                {
                    "release_id": 9,
                    "release_name": "Advance Monthly Sales for Retail and Food Services",
                    "date": "2013-08-13"
                },
                {
                    "release_id": 262,
                    "release_name": "Failures and Assistance Transactions",
                    "date": "2013-08-13"
                }
            ]
        }
        fake_dates = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.ReleaseDate.to_object", return_value=fake_dates) as mock_to_object:
                    result = api.get_releases_dates(
                        realtime_start=dt_start,
                        realtime_end=dt_end,
                        limit=50,
                        offset=10,
                        order_by="release_date",
                        sort_order="desc",
                        include_releases_dates_with_no_data=True
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/releases/dates",
                        {
                            "realtime_start": "converted",
                            "realtime_end": "converted",
                            "limit": 50,
                            "offset": 10,
                            "order_by": "release_date",
                            "sort_order": "desc",
                            "include_releases_dates_with_no_data": True
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_dates

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.ReleaseDate.to_object", return_value=fake_dates) as mock_to_object:
                result = api.get_releases_dates(
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31",
                    limit=10,
                    offset=2,
                    order_by="release_id",
                    sort_order="asc",
                    include_releases_dates_with_no_data=False
                )
                mock_get.assert_called_once_with(
                    "/releases/dates",
                    {
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31",
                        "limit": 10,
                        "offset": 2,
                        "order_by": "release_id",
                        "sort_order": "asc"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_dates

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.ReleaseDate.to_object", return_value=fake_dates) as mock_to_object:
                result = api.get_releases_dates()
                mock_get.assert_called_once_with("/releases/dates", {})
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_dates

    def test_get_release(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "releases": [
                {
                    "id": 53,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "Gross Domestic Product",
                    "press_release": True,
                    "link": "http://www.bea.gov/national/index.htm"
                }
            ]
        }
        fake_releases = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
                    result = api.get_release(
                        53,
                        realtime_start=dt_start,
                        realtime_end=dt_end
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/release/",
                        {
                            "release_id": 53,
                            "realtime_start": "converted",
                            "realtime_end": "converted"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_releases

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
                result = api.get_release(
                    53,
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/release/",
                    {
                        "release_id": 53,
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
                result = api.get_release(53)
                mock_get.assert_called_once_with(
                    "/release/",
                    {"release_id": 53}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

    def test_get_release_dates(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "1776-07-04",
            "realtime_end": "9999-12-31",
            "order_by": "release_date",
            "sort_order": "asc",
            "count": 17,
            "offset": 0,
            "limit": 10000,
            "release_dates": [
                {
                    "release_id": 82,
                    "date": "1997-02-10"
                },
                {
                    "release_id": 82,
                    "date": "1998-02-10"
                }
            ]
        }
        fake_dates = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.ReleaseDate.to_object", return_value=fake_dates) as mock_to_object:
                    result = api.get_release_dates(
                        82,
                        realtime_start=dt_start,
                        realtime_end=dt_end,
                        limit=100,
                        offset=5,
                        sort_order="desc",
                        include_releases_dates_with_no_data=True
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/release/dates",
                        {
                            "release_id": 82,
                            "realtime_start": "converted",
                            "realtime_end": "converted",
                            "limit": 100,
                            "offset": 5,
                            "sort_order": "desc",
                            "include_releases_dates_with_no_data": True
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_dates

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.ReleaseDate.to_object", return_value=fake_dates) as mock_to_object:
                result = api.get_release_dates(
                    82,
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31",
                    limit=10,
                    offset=2,
                    sort_order="asc",
                    include_releases_dates_with_no_data=False
                )
                mock_get.assert_called_once_with(
                    "/release/dates",
                    {
                        "release_id": 82,
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31",
                        "limit": 10,
                        "offset": 2,
                        "sort_order": "asc"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_dates

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.ReleaseDate.to_object", return_value=fake_dates) as mock_to_object:
                result = api.get_release_dates(82)
                mock_get.assert_called_once_with(
                    "/release/dates",
                    {"release_id": 82}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_dates

    def test_get_release_series(self):
        api= FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2017-08-01",
            "realtime_end": "2017-08-01",
            "order_by": "series_id",
            "sort_order": "asc",
            "count": 57,
            "offset": 0,
            "limit": 1000,
            "seriess": [
                {
                "id": "BOMTVLM133S",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "U.S. Imports of Services - Travel",
                "observation_start": "1992-01-01",
                "observation_end": "2017-05-01",
                "frequency": "Monthly",
                "frequency_short": "M",
                "units": "Million of Dollars",
                "units_short": "Mil. of $",
                "seasonal_adjustment": "Seasonally Adjusted",
                "seasonal_adjustment_short": "SA",
                "last_updated": "2017-07-06 09:34:00-05",
                "popularity": 0,
                "group_popularity": 0
                },
                {
                "id": "BOMVGMM133S",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "U.S. Imports of Services: U.S. Government Miscellaneous Services (DISCONTINUED)",
                "observation_start": "1992-01-01",
                "observation_end": "2013-12-01",
                "frequency": "Monthly",
                "frequency_short": "M",
                "units": "Millions of Dollars",
                "units_short": "Mil. of $",
                "seasonal_adjustment": "Seasonally Adjusted",
                "seasonal_adjustment_short": "SA",
                "last_updated": "2014-10-20 09:27:37-05",
                "popularity": 0,
                "group_popularity": 0,
                "notes": "BEA has introduced new table presentations, including a new presentation of services, as part of a comprehensive restructuring of BEA\u2019s international economic accounts.For more information see http:\/\/www.bea.gov\/international\/revision-2014.htm."
                }
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        exclude_tag_list = ["foo", "bar"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=lambda x: "foo,bar") as mock_list_conv:
                    with patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
                        result = api.get_release_series(
                            51,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            limit=100,
                            offset=5,
                            sort_order="desc",
                            filter_variable="units",
                            filter_value="Millions of Dollars",
                            exclude_tag_names=exclude_tag_list
                        )
                        assert mock_conv.call_count == 2
                        mock_list_conv.assert_called_once_with(exclude_tag_list)
                        mock_get.assert_called_once_with(
                            "/release/series",
                            {
                                "release_id": 51,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "limit": 100,
                                "offset": 5,
                                "sort_order": "desc",
                                "filter_variable": "units",
                                "filter_value": "Millions of Dollars",
                                "exclude_tag_names": "foo,bar"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
                result = api.get_release_series(
                    51,
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31",
                    limit=10,
                    offset=2,
                    sort_order="asc",
                    filter_variable="frequency",
                    filter_value="Monthly",
                    exclude_tag_names="foo"
                )
                mock_get.assert_called_once_with(
                    "/release/series",
                    {
                        "release_id": 51,
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31",
                        "limit": 10,
                        "offset": 2,
                        "sort_order": "asc",
                        "filter_variable": "frequency",
                        "filter_value": "Monthly",
                        "exclude_tag_names": "foo"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
                result = api.get_release_series(51)
                mock_get.assert_called_once_with(
                    "/release/series",
                    {"release_id": 51}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_series

        with pytest.raises(ValueError):
            api.get_release_series(-1)
        with pytest.raises(ValueError):
            api.get_release_series("not_an_int")

    def test_get_release_sources(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "sources": [
                {
                    "id": 18,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "U.S. Department of Commerce: Bureau of Economic Analysis",
                    "link": "http://www.bea.gov/"
                },
                {
                    "id": 19,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "U.S. Department of Commerce: Census Bureau",
                    "link": "http://www.census.gov/"
                }
            ]
        }
        fake_sources = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.Source.to_object", return_value=fake_sources) as mock_to_object:
                    result = api.get_release_sources(
                        51,
                        realtime_start=dt_start,
                        realtime_end=dt_end
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/release/sources",
                        {
                            "release_id": 51,
                            "realtime_start": "converted",
                            "realtime_end": "converted"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_sources

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Source.to_object", return_value=fake_sources) as mock_to_object:
                result = api.get_release_sources(
                    51,
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/release/sources",
                    {
                        "release_id": 51,
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_sources

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Source.to_object", return_value=fake_sources) as mock_to_object:
                result = api.get_release_sources(51)
                mock_get.assert_called_once_with(
                    "/release/sources",
                    {"release_id": 51}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_sources

    def test_get_release_tags(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 13,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "commercial paper",
                    "group_id": "gen",
                    "notes": "",
                    "created": "2012-03-19 10:40:59-05",
                    "popularity": 55,
                    "series_count": 18
                },
                {
                    "name": "frb",
                    "group_id": "src",
                    "notes": "Board of Governors of the Federal Reserve System",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 90,
                    "series_count": 18
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=lambda x: "macro;gdp") as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
                        result = api.get_release_tags(
                            86,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names=tag_list
                        )
                        assert mock_conv.call_count == 2
                        mock_list_conv.assert_called_once_with(tag_list)
                        mock_get.assert_called_once_with(
                            "/release/tags",
                            {
                                "release_id": 86,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro;gdp"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion") as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
                        result = api.get_release_tags(
                            86,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names="macro"
                        )
                        assert mock_conv.call_count == 2
                        mock_list_conv.assert_not_called()
                        mock_get.assert_called_once_with(
                            "/release/tags",
                            {
                                "release_id": 86,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted"):
                with patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=lambda x: "macro;gdp"):
                    with patch("fedfred.clients.Tag.to_object", return_value=fake_tags):
                        result = api.get_release_tags(
                            86,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names=tag_list,
                            tag_group_id=42,
                            search_text="foo",
                            limit=5,
                            offset=2,
                            order_by="series_count"
                        )
                        mock_get.assert_called_once_with(
                            "/release/tags",
                            {
                                "release_id": 86,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro;gdp",
                                "tag_group_id": 42,
                                "search_text": "foo",
                                "limit": 5,
                                "offset": 2,
                                "order_by": "series_count"
                            }
                        )
                        assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
                result = api.get_release_tags(86)
                mock_get.assert_called_once_with(
                    "/release/tags",
                    {"release_id": 86}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_tags

    def test_get_release_related_tags(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 7,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "commercial paper",
                    "group_id": "gen",
                    "notes": "",
                    "created": "2012-03-19 10:40:59-05",
                    "popularity": 55,
                    "series_count": 2
                },
                {
                    "name": "frb",
                    "group_id": "src",
                    "notes": "Board of Governors of the Federal Reserve System",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 90,
                    "series_count": 2
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=";".join) as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
                        result = api.get_release_related_tags(
                            86,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names=tag_list,
                            exclude_tag_names=exclude_tag_list,
                            tag_group_id="grp",
                            search_text="foo",
                            limit=5,
                            offset=2,
                            order_by="series_count",
                            sort_order="desc"
                        )
                        assert mock_conv.call_count == 2
                        assert mock_list_conv.call_count == 2
                        mock_get.assert_called_once_with(
                            "/release/related_tags",
                            {
                                "release_id": 86,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro;gdp",
                                "exclude_tag_names": "foo;bar",
                                "tag_group_id": "grp",
                                "search_text": "foo",
                                "limit": 5,
                                "offset": 2,
                                "order_by": "series_count",
                                "sort_order": "desc"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion") as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
                        result = api.get_release_related_tags(
                            86,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names="macro",
                            exclude_tag_names="foo"
                        )
                        assert mock_conv.call_count == 2
                        mock_list_conv.assert_not_called()
                        mock_get.assert_called_once_with(
                            "/release/related_tags",
                            {
                                "release_id": 86,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro",
                                "exclude_tag_names": "foo"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
                result = api.get_release_related_tags(86)
                mock_get.assert_called_once_with(
                    "/release/related_tags",
                    {"release_id": 86}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_tags

    def test_get_release_tables(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "name": "Personal consumption expenditures",
            "element_id": 12886,
            "release_id": "53",
            "elements":
            {
                "12887":
                {
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
                            "children": []
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
                            "children": []
                        }
                    ]
                },
                "12888":
                {
                    "element_id": 12888,
                    "release_id": 53,
                    "series_id": "DDURRL1A225NBEA",
                    "parent_id": 12887,
                    "line": "4",
                    "type": "series",
                    "name": "Durable goods",
                    "level": "2",
                    "children": []
                },
                "12889":
                {
                    "element_id": 12889,
                    "release_id": 53,
                    "series_id": "DNDGRL1A225NBEA",
                    "parent_id": 12887,
                    "line": "5",
                    "type": "series",
                    "name": "Nondurable goods",
                    "level": "2",
                    "children": []
                },
                "12890":
                {
                    "element_id": 12890,
                    "release_id": 53,
                    "series_id": "DSERRL1A225NBEA",
                    "parent_id": 12886,
                    "line": "6",
                    "type": "series",
                    "name": "Services",
                    "level": "1",
                    "children": []
                }
            }
        }
        fake_elements = [MagicMock()]
        dt_obs = datetime(2020, 1, 1)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "2020-01-01") as mock_dt_conv:
                with patch("fedfred.clients.Element.to_object", return_value=fake_elements) as mock_to_object:
                    result = api.get_release_tables(
                        53,
                        element_id=12887,
                        include_observation_values=True,
                        observation_date=dt_obs
                    )
                    mock_dt_conv.assert_called_once_with(dt_obs)
                    mock_get.assert_called_once_with(
                        "/release/tables",
                        {
                            "release_id": 53,
                            "element_id": 12887,
                            "include_observation_values": True,
                            "observation_date": "2020-01-01"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response, client=api)
                    assert result == fake_elements

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Element.to_object", return_value=fake_elements) as mock_to_object:
                result = api.get_release_tables(
                    53,
                    observation_date="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/release/tables",
                    {
                        "release_id": 53,
                        "observation_date": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response, client=api)
                assert result == fake_elements

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Element.to_object", return_value=fake_elements) as mock_to_object:
                result = api.get_release_tables(53)
                mock_get.assert_called_once_with(
                    "/release/tables",
                    {"release_id": 53}
                )
                mock_to_object.assert_called_once_with(fake_response, client=api)
                assert result == fake_elements

    ## Series
    def test_get_series(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "seriess": [
                {
                    "id": "GNPCA",
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "title": "Real Gross National Product",
                    "observation_start": "1929-01-01",
                    "observation_end": "2012-01-01",
                    "frequency": "Annual",
                    "frequency_short": "A",
                    "units": "Billions of Chained 2009 Dollars",
                    "units_short": "Bil. of Chn. 2009 $",
                    "seasonal_adjustment": "Not Seasonally Adjusted",
                    "seasonal_adjustment_short": "NSA",
                    "last_updated": "2013-07-31 09:26:16-05",
                    "popularity": 39,
                    "notes": "BEA Account Code: A001RX1"
                }
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
                    result = api.get_series(
                        "GNPCA",
                        realtime_start=dt_start,
                        realtime_end=dt_end
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/series",
                        {
                            "series_id": "GNPCA",
                            "realtime_start": "converted",
                            "realtime_end": "converted"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
                result = api.get_series(
                    "GNPCA",
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/series",
                    {
                        "series_id": "GNPCA",
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
                result = api.get_series("GNPCA")
                mock_get.assert_called_once_with(
                    "/series",
                    {"series_id": "GNPCA"}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_series

    def test_get_series_categories(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "categories": [
                {
                    "id": 95,
                    "name": "Monthly Rates",
                    "parent_id": 15
                },
                {
                    "id": 275,
                    "name": "Japan",
                    "parent_id": 158
                }
            ]
        }
        fake_categories = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.Category.to_object", return_value=fake_categories) as mock_to_object:
                    result = api.get_series_categories(
                        "EXJPUS",
                        realtime_start=dt_start,
                        realtime_end=dt_end
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/series/categories",
                        {
                            "series_id": "EXJPUS",
                            "realtime_start": "converted",
                            "realtime_end": "converted"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_categories

        # With string for start/end
        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Category.to_object", return_value=fake_categories) as mock_to_object:
                result = api.get_series_categories(
                    "EXJPUS",
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/series/categories",
                    {
                        "series_id": "EXJPUS",
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_categories

        # Only required argument
        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Category.to_object", return_value=fake_categories) as mock_to_object:
                result = api.get_series_categories("EXJPUS")
                mock_get.assert_called_once_with(
                    "/series/categories",
                    {"series_id": "EXJPUS"}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_categories

    def test_get_series_observations(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "observation_start": "1776-07-04",
            "observation_end": "9999-12-31",
            "units": "lin",
            "output_type": 1,
            "file_type": "json",
            "order_by": "observation_date",
            "sort_order": "asc",
            "count": 84,
            "offset": 0,
            "limit": 100000,
            "observations": [
                {
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "date": "1929-01-01",
                    "value": "1065.9"
                },
                {
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "date": "1930-01-01",
                    "value": "975.5"
                },
                {
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "date": "1931-01-01",
                    "value": "912.1"
                },
                {
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "date": "1932-01-01",
                    "value": "794.1"
                }
            ]
        }
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        ob_start = datetime(1776, 7, 4)
        ob_end = datetime(9999, 12, 31)
        vintage_dates_list = [datetime(2020, 1, 1), datetime(2020, 2, 1)]

        # Test pandas
        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_dt_conv, \
            patch("fedfred.clients.FredHelpers.vintage_dates_type_conversion", return_value="2020-01-01,2020-02-01") as mock_vintage_conv, \
            patch("fedfred.clients.FredHelpers.to_pd_df", return_value="pd_df") as mock_pd:
            result = api.get_series_observations(
                "GNPCA",
                dataframe_method="pandas",
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=10,
                offset=2,
                sort_order="desc",
                observation_start=ob_start,
                observation_end=ob_end,
                units="chg",
                frequency="m",
                aggregation_method="sum",
                output_type=2,
                vintage_dates=vintage_dates_list
            )
            assert mock_dt_conv.call_count == 4
            mock_vintage_conv.assert_called_once_with(vintage_dates_list)
            mock_get.assert_called_once_with(
                "/series/observations",
                {
                    "series_id": "GNPCA",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 10,
                    "offset": 2,
                    "sort_order": "desc",
                    "observation_start": "converted",
                    "observation_end": "converted",
                    "units": "chg",
                    "frequency": "m",
                    "aggregation_method": "sum",
                    "output_type": 2,
                    "vintage_dates": "2020-01-01,2020-02-01"
                }
            )
            mock_pd.assert_called_once_with(fake_response)
            assert result == "pd_df"

        # Test polars
        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.to_pl_df", return_value="pl_df") as mock_pl:
            result = api.get_series_observations("GNPCA", dataframe_method="polars")
            mock_get.assert_called_once_with("/series/observations", {"series_id": "GNPCA"})
            mock_pl.assert_called_once_with(fake_response)
            assert result == "pl_df"

        # Test dask
        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.to_dd_df", return_value="dd_df") as mock_dd:
            result = api.get_series_observations("GNPCA", dataframe_method="dask")
            mock_get.assert_called_once_with("/series/observations", {"series_id": "GNPCA"})
            mock_dd.assert_called_once_with(fake_response)
            assert result == "dd_df"

        # Test default (pandas)
        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.to_pd_df", return_value="pd_df") as mock_pd:
            result = api.get_series_observations("GNPCA")
            mock_get.assert_called_once_with("/series/observations", {"series_id": "GNPCA"})
            mock_pd.assert_called_once_with(fake_response)
            assert result == "pd_df"

        # Test invalid dataframe_method
        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response):
            with pytest.raises(ValueError, match="dataframe_method must be a string, options are: 'pandas', 'polars', or 'dask'"):
                api.get_series_observations("GNPCA", dataframe_method="invalid")

    def test_get_series_release(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "releases": [
                {
                    "id": 21,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "H.6 Money Stock Measures",
                    "press_release": True,
                    "link": "http://www.federalreserve.gov/releases/h6/"
                }
            ]
        }
        fake_releases = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv:
                with patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
                    result = api.get_series_release(
                        "GNPCA",
                        realtime_start=dt_start,
                        realtime_end=dt_end
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/series/release",
                        {
                            "series_id": "GNPCA",
                            "realtime_start": "converted",
                            "realtime_end": "converted"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_releases

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
                result = api.get_series_release(
                    "GNPCA",
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/series/release",
                    {
                        "series_id": "GNPCA",
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get:
            with patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
                result = api.get_series_release("GNPCA")
                mock_get.assert_called_once_with(
                    "/series/release",
                    {"series_id": "GNPCA"}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

    def test_get_series_search(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2017-08-01",
            "realtime_end": "2017-08-01",
            "order_by": "search_rank",
            "sort_order": "desc",
            "count": 32,
            "offset": 0,
            "limit": 1000,
            "seriess": [
                {
                "id": "MSIM2",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "Monetary Services Index: M2 (preferred)",
                "observation_start": "1967-01-01",
                "observation_end": "2013-12-01",
                "frequency": "Monthly",
                "frequency_short": "M",
                "units": "Billions of Dollars",
                "units_short": "Bil. of $",
                "seasonal_adjustment": "Seasonally Adjusted",
                "seasonal_adjustment_short": "SA",
                "last_updated": "2014-01-17 07:16:44-06",
                "popularity": 34,
                "group_popularity": 33,
                "notes": "The MSI measure the flow of monetary services received each period by households and firms from their holdings of monetary assets (levels of the indexes are sometimes referred to as Divisia monetary aggregates).\nPreferred benchmark rate equals 100 basis points plus the largest rate in the set of rates.\nAlternative benchmark rate equals the larger of the preferred benchmark rate and the Baa corporate bond yield.\nMore information about the new MSI can be found at\nhttp:\/\/research.stlouisfed.org\/msi\/index.html."
                },
                {
                "id": "MSIM1P",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "Monetary Services Index: M1 (preferred)",
                "observation_start": "1967-01-01",
                "observation_end": "2013-12-01",
                "frequency": "Monthly",
                "frequency_short": "M",
                "units": "Billions of Dollars",
                "units_short": "Bil. of $",
                "seasonal_adjustment": "Seasonally Adjusted",
                "seasonal_adjustment_short": "SA",
                "last_updated": "2014-01-17 07:16:45-06",
                "popularity": 26,
                "group_popularity": 26,
                "notes": "The MSI measure the flow of monetary services received each period by households and firms from their holdings of monetary assets (levels of the indexes are sometimes referred to as Divisia monetary aggregates)."
                }
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=",".join) as mock_list_conv, \
            patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
            result = api.get_series_search(
                "monetary services index",
                search_type="full_text",
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=10,
                offset=2,
                order_by="search_rank",
                sort_order="desc",
                filter_variable="frequency",
                filter_value="Monthly",
                tag_names=tag_list,
                exclude_tag_names=exclude_tag_list
            )
            assert mock_conv.call_count == 2
            assert mock_list_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/series/search",
                {
                    "search_text": "monetary services index",
                    "search_type": "full_text",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 10,
                    "offset": 2,
                    "order_by": "search_rank",
                    "sort_order": "desc",
                    "filter_variable": "frequency",
                    "filter_value": "Monthly",
                    "tag_names": "macro,gdp",
                    "exclude_tag_names": "foo,bar"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
            result = api.get_series_search(
                "monetary services index",
                tag_names="macro",
                exclude_tag_names="foo",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31"
            )
            mock_get.assert_called_once_with(
                "/series/search",
                {
                    "search_text": "monetary services index",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "macro",
                    "exclude_tag_names": "foo"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
            result = api.get_series_search("monetary services index")
            mock_get.assert_called_once_with(
                "/series/search",
                {"search_text": "monetary services index"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

    def test_get_series_search_tags(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 18,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "academic data",
                    "group_id": "gen",
                    "notes": "Time series data created mainly by academia to address growing demand in understanding specific concerns in the economy that are not well modeled by ordinary statistical agencies.",
                    "created": "2012-08-29 10:22:19-05",
                    "popularity": 62,
                    "series_count": 25
                },
                {
                    "name": "anderson & jones",
                    "group_id": "src",
                    "notes": "Richard Anderson and Barry Jones",
                    "created": "2013-06-21 10:22:49-05",
                    "popularity": 46,
                    "series_count": 25
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=lambda x: "macro;gdp") as mock_list_conv, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_series_search_tags(
                "monetary services index",
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=tag_list,
                tag_group_id="grp",
                tag_search_text="foo",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_list_conv.assert_called_once_with(tag_list)
            mock_get.assert_called_once_with(
                "/series/search/tags",
                {
                    "series_search_text": "monetary services index",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "tag_names": "macro;gdp",
                    "tag_group_id": "grp",
                    "tag_search_text": "foo",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_series_search_tags(
                "monetary services index",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                tag_names="macro"
            )
            mock_get.assert_called_once_with(
                "/series/search/tags",
                {
                    "series_search_text": "monetary services index",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "macro"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_series_search_tags("monetary services index")
            mock_get.assert_called_once_with(
                "/series/search/tags",
                {"series_search_text": "monetary services index"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

    def test_get_series_search_related_tags(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 10,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "conventional",
                    "group_id": "gen",
                    "notes": "",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 63,
                    "series_count": 3
                },
                {
                    "name": "h15",
                    "group_id": "rls",
                    "notes": "H.15 Selected Interest Rates",
                    "created": "2012-08-16 15:21:17-05",
                    "popularity": 84,
                    "series_count": 3
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=";".join) as mock_list_conv, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_series_search_related_tags(
                "mortgage rate",
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=tag_list,
                exclude_tag_names=exclude_tag_list,
                tag_group_id="grp",
                tag_search_text="foo",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            assert mock_list_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/series/search/related_tags",
                {
                    "series_search_text": "mortgage rate",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "tag_names": "macro;gdp",
                    "exclude_tag_names": "foo;bar",
                    "tag_group_id": "grp",
                    "tag_search_text": "foo",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_series_search_related_tags(
                "mortgage rate",
                tag_names="macro",
                exclude_tag_names="foo",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31"
            )
            mock_get.assert_called_once_with(
                "/series/search/related_tags",
                {
                    "series_search_text": "mortgage rate",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "macro",
                    "exclude_tag_names": "foo"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_series_search_related_tags("mortgage rate", tag_names="")
            mock_get.assert_called_once_with(
                "/series/search/related_tags",
                {"series_search_text": "mortgage rate", "tag_names": ""}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

    def test_get_series_tags(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 8,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "nation",
                    "group_id": "geot",
                    "notes": "Country Level",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 100,
                    "series_count": 105200
                },
                {
                    "name": "nsa",
                    "group_id": "seas",
                    "notes": "Not seasonally adjusted",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 96,
                    "series_count": 100468
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_series_tags(
                "GNPCA",
                realtime_start=dt_start,
                realtime_end=dt_end,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/series/tags",
                {
                    "series_id": "GNPCA",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_series_tags(
                "GNPCA",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                order_by="name"
            )
            mock_get.assert_called_once_with(
                "/series/tags",
                {
                    "series_id": "GNPCA",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "order_by": "name"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_series_tags(
                "GNPCA",
                sort_order="asc"
            )
            mock_get.assert_called_once_with(
                "/series/tags",
                {
                    "series_id": "GNPCA",
                    "sort_order": "asc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_series_tags("GNPCA")
            mock_get.assert_called_once_with(
                "/series/tags",
                {"series_id": "GNPCA"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

    def test_get_series_updates(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "filter_variable": "geography",
            "filter_value": "all",
            "order_by": "last_updated",
            "sort_order": "desc",
            "count": 143535,
            "offset": 0,
            "limit": 100,
            "seriess": [
                {
                    "id": "PPIITM",
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "title": "Producer Price Index: Intermediate Materials: Supplies & Components",
                    "observation_start": "1947-04-01",
                    "observation_end": "2013-07-01",
                    "frequency": "Monthly",
                    "frequency_short": "M",
                    "units": "Index 1982=100",
                    "units_short": "Index 1982=100",
                    "seasonal_adjustment": "Seasonally Adjusted",
                    "seasonal_adjustment_short": "SA",
                    "last_updated": "2013-08-14 08:36:05-05",
                    "popularity": 52
                },
                {
                    "id": "PPILFE",
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "title": "Producer Price Index: Finished Goods Less Food & Energy",
                    "observation_start": "1974-01-01",
                    "observation_end": "2013-07-01",
                    "frequency": "Monthly",
                    "frequency_short": "M",
                    "units": "Index 1982=100",
                    "units_short": "Index 1982=100",
                    "seasonal_adjustment": "Seasonally Adjusted",
                    "seasonal_adjustment_short": "SA",
                    "last_updated": "2013-08-14 08:36:05-05",
                    "popularity": 51
                }
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        dt_hhmm_start = datetime(2020, 1, 1, 8, 30)
        dt_hhmm_end = datetime(2020, 1, 1, 17, 45)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_dt_conv, \
            patch("fedfred.clients.FredHelpers.datetime_hh_mm_conversion", side_effect=lambda x: "08:30" if x == dt_hhmm_start else "17:45") as mock_hhmm_conv, \
            patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
            result = api.get_series_updates(
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=50,
                offset=10,
                filter_value="foo",
                start_time=dt_hhmm_start,
                end_time=dt_hhmm_end
            )
            assert mock_dt_conv.call_count == 2
            assert mock_hhmm_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/series/updates",
                {
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 50,
                    "offset": 10,
                    "filter_value": "foo",
                    "start_time": "08:30",
                    "end_time": "17:45"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
            result = api.get_series_updates(
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                limit=10,
                offset=2,
                filter_value="bar",
                start_time="09:00",
                end_time="18:00"
            )
            mock_get.assert_called_once_with(
                "/series/updates",
                {
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "limit": 10,
                    "offset": 2,
                    "filter_value": "bar",
                    "start_time": "09:00",
                    "end_time": "18:00"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
            result = api.get_series_updates()
            mock_get.assert_called_once_with("/series/updates", {})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
            result = api.get_series_updates(limit=5, offset=1)
            mock_get.assert_called_once_with(
                "/series/updates",
                {"limit": 5, "offset": 1}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

    def test_get_series_vintage_dates(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "1776-07-04",
            "realtime_end": "9999-12-31",
            "order_by": "vintage_date",
            "sort_order": "asc",
            "count": 162,
            "offset": 0,
            "limit": 10000,
            "vintage_dates": [
                "1958-12-21",
                "1959-02-19",
                "1959-07-19",
                "1960-02-16",
                "1960-07-22",
                "1961-02-19",
            ]
        }
        fake_vintage_dates = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.VintageDate.to_object", return_value=fake_vintage_dates) as mock_to_object:
            result = api.get_series_vintagedates(
                "GNPCA",
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=50,
                offset=10,
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/series/vintagedates",
                {
                    "series_id": "GNPCA",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 50,
                    "offset": 10,
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_vintage_dates

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.VintageDate.to_object", return_value=fake_vintage_dates) as mock_to_object:
            result = api.get_series_vintagedates(
                "GNPCA",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                limit=10,
                offset=2
            )
            mock_get.assert_called_once_with(
                "/series/vintagedates",
                {
                    "series_id": "GNPCA",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "limit": 10,
                    "offset": 2
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_vintage_dates

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.VintageDate.to_object", return_value=fake_vintage_dates) as mock_to_object:
            result = api.get_series_vintagedates("GNPCA")
            mock_get.assert_called_once_with(
                "/series/vintagedates",
                {"series_id": "GNPCA"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_vintage_dates

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.VintageDate.to_object", return_value=fake_vintage_dates) as mock_to_object:
            result = api.get_series_vintagedates("GNPCA", sort_order="asc")
            mock_get.assert_called_once_with(
                "/series/vintagedates",
                {"series_id": "GNPCA", "sort_order": "asc"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_vintage_dates

        with pytest.raises(ValueError):
            api.get_series_vintagedates("")

        with pytest.raises(ValueError):
            api.get_series_vintagedates(123)

    ## Sources
    def test_get_sources(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "source_id",
            "sort_order": "asc",
            "count": 58,
            "offset": 0,
            "limit": 1000,
            "sources": [
                {
                    "id": 1,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "Board of Governors of the Federal Reserve System",
                    "link": "http://www.federalreserve.gov/"
                },
                {
                    "id": 3,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "Federal Reserve Bank of Philadelphia",
                    "link": "http://www.philadelphiafed.org/"
                }
            ]
        }
        fake_sources = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.Source.to_object", return_value=fake_sources) as mock_to_object:
            result = api.get_sources(
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=50,
                offset=10,
                order_by="name",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/sources",
                {
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 50,
                    "offset": 10,
                    "order_by": "name",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_sources

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Source.to_object", return_value=fake_sources) as mock_to_object:
            result = api.get_sources(
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                limit=10,
                offset=2
            )
            mock_get.assert_called_once_with(
                "/sources",
                {
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "limit": 10,
                    "offset": 2
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_sources

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Source.to_object", return_value=fake_sources) as mock_to_object:
            result = api.get_sources()
            mock_get.assert_called_once_with("/sources", {})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_sources

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Source.to_object", return_value=fake_sources) as mock_to_object:
            result = api.get_sources(order_by="source_id", sort_order="asc")
            mock_get.assert_called_once_with(
                "/sources",
                {"order_by": "source_id", "sort_order": "asc"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_sources

    def test_get_source(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "sources": [
                {
                    "id": 1,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "Board of Governors of the Federal Reserve System",
                    "link": "http://www.federalreserve.gov/"
                }
            ]
        }
        fake_source = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.Source.to_object", return_value=fake_source) as mock_to_object:
            result = api.get_source(
                1,
                realtime_start=dt_start,
                realtime_end=dt_end
            )
            assert mock_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/source",
                {
                    "source_id": 1,
                    "realtime_start": "converted",
                    "realtime_end": "converted"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_source

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Source.to_object", return_value=fake_source) as mock_to_object:
            result = api.get_source(
                1,
                realtime_start="2021-01-01",
                realtime_end="2021-12-31"
            )
            mock_get.assert_called_once_with(
                "/source",
                {
                    "source_id": 1,
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_source

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Source.to_object", return_value=fake_source) as mock_to_object:
            result = api.get_source(1)
            mock_get.assert_called_once_with(
                "/source",
                {"source_id": 1}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_source

    def test_get_source_releases(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "release_id",
            "sort_order": "asc",
            "count": 26,
            "offset": 0,
            "limit": 1000,
            "releases": [
                {
                    "id": 13,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "G.17 Industrial Production and Capacity Utilization",
                    "press_release": True,
                    "link": "http://www.federalreserve.gov/releases/g17/"
                },
                {
                    "id": 14,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "G.19 Consumer Credit",
                    "press_release": True,
                    "link": "http://www.federalreserve.gov/releases/g19/"
                }
            ]
        }
        fake_releases = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
            result = api.get_source_releases(
                1,
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=5,
                offset=2,
                order_by="release_id",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/source/releases",
                {
                    "source_id": 1,
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "release_id",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_releases

        # All arguments as string
        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
            result = api.get_source_releases(
                1,
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                limit=10,
                offset=3,
                order_by="name",
                sort_order="asc"
            )
            mock_get.assert_called_once_with(
                "/source/releases",
                {
                    "source_id": 1,
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "limit": 10,
                    "offset": 3,
                    "order_by": "name",
                    "sort_order": "asc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_releases

        # Only required argument
        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
            result = api.get_source_releases(1)
            mock_get.assert_called_once_with(
                "/source/releases",
                {"source_id": 1}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_releases

        # Only some optional arguments
        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Release.to_object", return_value=fake_releases) as mock_to_object:
            result = api.get_source_releases(
                1,
                limit=7,
                offset=4
            )
            mock_get.assert_called_once_with(
                "/source/releases",
                {"source_id": 1, "limit": 7, "offset": 4}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_releases

    ## Tags
    def test_get_tags(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 4794,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "nation",
                    "group_id": "geot",
                    "notes": "Country Level",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 100,
                    "series_count": 105200
                },
                {
                    "name": "nsa",
                    "group_id": "seas",
                    "notes": "Not seasonally adjusted",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 96,
                    "series_count": 100468
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=";".join) as mock_list_conv, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_tags(
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=["foo", "bar"],
                tag_group_id="grp",
                search_text="baz",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_list_conv.assert_called_once_with(["foo", "bar"])
            mock_get.assert_called_once_with(
                "/tags",
                {
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "tag_names": "foo;bar",
                    "tag_group_id": "grp",
                    "search_text": "baz",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=lambda x: "macro;gdp") as mock_list_conv, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_tags(
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=tag_list,
                tag_group_id="grp",
                search_text="baz",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_list_conv.assert_called_once_with(tag_list)
            mock_get.assert_called_once_with(
                "/tags",
                {
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "tag_names": "macro;gdp",
                    "tag_group_id": "grp",
                    "search_text": "baz",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_tags(
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                tag_names="foo",
                tag_group_id="grp",
                search_text="baz",
                limit=10,
                offset=3,
                order_by="popularity",
                sort_order="asc"
            )
            mock_get.assert_called_once_with(
                "/tags",
                {
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "foo",
                    "tag_group_id": "grp",
                    "search_text": "baz",
                    "limit": 10,
                    "offset": 3,
                    "order_by": "popularity",
                    "sort_order": "asc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_tags()
            mock_get.assert_called_once_with("/tags", {})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_tags(
                tag_names="foo",
                limit=7,
                offset=4
            )
            mock_get.assert_called_once_with(
                "/tags",
                {"tag_names": "foo", "limit": 7, "offset": 4}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", side_effect=ValueError("API error")):
            with pytest.raises(ValueError):
                api.get_tags(tag_names="foo")

    def test_get_related_tags(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 13,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "nation",
                    "group_id": "geot",
                    "notes": "Country Level",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 100,
                    "series_count": 12
                },
                {
                    "name": "usa",
                    "group_id": "geo",
                    "notes": "United States of America",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 100,
                    "series_count": 12
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=";".join) as mock_list_conv, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_related_tags(
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=tag_list,
                exclude_tag_names=exclude_tag_list,
                tag_group_id="grp",
                search_text="foo",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            assert mock_list_conv.call_count == 2
            mock_list_conv.assert_any_call(tag_list)
            mock_list_conv.assert_any_call(exclude_tag_list)
            mock_get.assert_called_once_with(
                "/related_tags",
                {
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "tag_names": "macro;gdp",
                    "exclude_tag_names": "foo;bar",
                    "tag_group_id": "grp",
                    "search_text": "foo",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_related_tags(
                tag_names="macro",
                exclude_tag_names="foo",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31"
            )
            mock_get.assert_called_once_with(
                "/related_tags",
                {
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "macro",
                    "exclude_tag_names": "foo"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        # Supply tag_names explicitly (empty) to match new signature
        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_related_tags(tag_names="")
            mock_get.assert_called_once_with("/related_tags", {"tag_names": ""})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Tag.to_object", return_value=fake_tags) as mock_to_object:
            result = api.get_related_tags(
                tag_names="foo",
                limit=7,
                offset=4
            )
            mock_get.assert_called_once_with(
                "/related_tags",
                {"tag_names": "foo", "limit": 7, "offset": 4}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(api, "_FredAPI__fred_get_request", side_effect=ValueError("API error")):
            with pytest.raises(ValueError):
                api.get_related_tags(tag_names="foo")

    def test_get_tags_series(self):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        fake_response = {
            "realtime_start": "2017-08-01",
            "realtime_end": "2017-08-01",
            "order_by": "series_id",
            "sort_order": "asc",
            "count": 18,
            "offset": 0,
            "limit": 1000,
            "seriess": [
                {
                "id": "CPGDFD02SIA657N",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "Consumer Price Index: Total Food Excluding Restaurants for Slovenia\u00a9",
                "observation_start": "1996-01-01",
                "observation_end": "2016-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Growth Rate Previous Period",
                "units_short": "Growth Rate Previous Period",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2017-04-20 00:48:35-05",
                "popularity": 0,
                "group_popularity": 0,
                "notes": "OECD descriptor ID: CPGDFD02\nOECD unit ID: GP\nOECD country ID: SVN\n\nAll OECD data should be cited as follows: OECD, \"Main Economic Indicators - complete database\", Main Economic Indicators (database),http:\/\/dx.doi.org\/10.1787\/data-00052-en (Accessed on date)\nCopyright, 2016, OECD. Reprinted with permission."
                },
                {
                "id": "CPGDFD02SIA659N",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "Consumer Price Index: Total Food Excluding Restaurants for Slovenia\u00a9",
                "observation_start": "1996-01-01",
                "observation_end": "2016-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Growth Rate Same Period Previous Year",
                "units_short": "Growth Rate Same Period Previous Yr.",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2017-04-20 00:48:35-05",
                "popularity": 0,
                "group_popularity": 0,
                "notes": "OECD descriptor ID: CPGDFD02\nOECD unit ID: GY\nOECD country ID: SVN\n\nAll OECD data should be cited as follows: OECD, \"Main Economic Indicators - complete database\", Main Economic Indicators (database),http:\/\/dx.doi.org\/10.1787\/data-00052-en (Accessed on date)\nCopyright, 2016, OECD. Reprinted with permission."
                }
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion", side_effect=lambda x: "converted") as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion", side_effect=";".join) as mock_list_conv, \
            patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
            result = api.get_tags_series(
                tag_names=tag_list,
                exclude_tag_names=exclude_tag_list,
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=5,
                offset=2,
                order_by="series_id",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            assert mock_list_conv.call_count == 2
            mock_list_conv.assert_any_call(tag_list)
            mock_list_conv.assert_any_call(exclude_tag_list)
            mock_get.assert_called_once_with(
                "/tags/series",
                {
                    "tag_names": "macro;gdp",
                    "exclude_tag_names": "foo;bar",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_id",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
            result = api.get_tags_series(
                tag_names="macro",
                exclude_tag_names="foo",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31"
            )
            mock_get.assert_called_once_with(
                "/tags/series",
                {
                    "tag_names": "macro",
                    "exclude_tag_names": "foo",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
            # Supply tag_names explicitly (empty) to satisfy new signature
            result = api.get_tags_series(tag_names="")
            mock_get.assert_called_once_with("/tags/series", {"tag_names": ""})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.Series.to_object", return_value=fake_series) as mock_to_object:
            result = api.get_tags_series(
                tag_names="foo",
                limit=7,
                offset=4
            )
            mock_get.assert_called_once_with(
                "/tags/series",
                {"tag_names": "foo", "limit": 7, "offset": 4}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(api, "_FredAPI__fred_get_request", side_effect=ValueError("API error")):
            with pytest.raises(ValueError):
                api.get_tags_series(tag_names="foo")

class TestMapsAPI:
    # Dunder methods
    def test_init(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        assert maps_api._parent is parent
        assert maps_api.cache_mode == parent.cache_mode
        assert maps_api.cache is parent.cache
        assert maps_api.base_url == 'https://api.stlouisfed.org/geofred'

    def test_repr(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        expected = f"{repr(parent)}.MapsAPI"
        assert repr(maps_api) == expected

    def test_str(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        expected = (
            f"{str(parent)}"
            f"  MapsAPI Instance:\n"
            f"      Base URL: {maps_api.base_url}\n"
        )
        assert str(maps_api) == expected

    def test_eq(self):
        parent1 = FredAPI("testkey1", cache_mode=True, cache_size=10)
        parent2 = FredAPI("testkey2", cache_mode=True, cache_size=10)
        maps_api1 = parent1.Maps
        maps_api2 = parent2.Maps
        assert maps_api1 == maps_api1
        assert maps_api1 != maps_api2
        assert (maps_api1 == 42) is False
        assert (maps_api1 == "not a MapsAPI") is False

    def test_hash(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        expected_hash = hash((parent.api_key, parent.cache_mode, parent.cache_size, maps_api.base_url))
        assert hash(maps_api) == expected_hash

    def test_del(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        maps_api.__del__()
        assert len(maps_api.cache) == 0

    def test_getitem(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        maps_api.cache["foo"] = "bar"
        assert maps_api["foo"] == "bar"
        with pytest.raises(AttributeError, match="'baz' not found in cache."):
            _ = maps_api["baz"]

    def test_len(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        maps_api.cache["foo"] = "bar"
        maps_api.cache["baz"] = "qux"
        assert len(maps_api) == 2

    def test_contains(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        maps_api.cache["foo"] = "bar"
        maps_api.cache["baz"] = "qux"
        assert "foo" in maps_api
        assert "baz" in maps_api
        assert "quux" not in maps_api

    def test_setitem(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        maps_api["foo"] = "bar"
        assert maps_api.cache["foo"] == "bar"
        maps_api["baz"] = "qux"
        assert maps_api.cache["baz"] == "qux"

    def test_delitem(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        maps_api.cache["foo"] = "bar"
        del maps_api["foo"]
        assert "foo" not in maps_api

        with pytest.raises(AttributeError, match="'baz' not found in cache."):
            del maps_api["baz"]

    def test_call(self):
        parent = FredAPI("testkey1234", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        maps_api.cache["foo"] = "bar"
        maps_api.cache["baz"] = "qux"
        summary = maps_api()
        assert isinstance(summary, str)
        assert "FredAPI Instance:" in summary
        assert "MapsAPI Instance:" in summary
        assert f"Base URL: {maps_api.base_url}" in summary
        assert "Cache Mode: Enabled" in summary
        assert "Cache Size: 2 items" in summary
        assert "API Key: ****1234" in summary

    # Private Methods
    @pytest.mark.parametrize(
        "request_offsets,should_sleep",
        [
            ([-70], False),         # Only one old request, after cleanup and append: 1 (should NOT sleep)
            ([-10], False),         # Only one recent request, after append: 2 (should NOT sleep)
            ([-10, -5], True),      # Two recent requests, after append: 3 (should sleep)
            ([-10, -5, -1], True),  # Three recent requests, after append: 4 (should sleep)
        ]
    )
    def test_rate_limited(self, request_offsets, should_sleep):
        api = FredAPI("testkey", cache_mode=True, cache_size=10)
        api.max_requests_per_minute = 3
        maps_api = api.Maps

        now = time.time()
        api.request_times.clear()
        api.request_times.extend([now + offset for offset in request_offsets])

        with patch("time.sleep") as mock_sleep, patch("time.time", return_value=now):
            maps_api._MapsAPI__rate_limited()
            if should_sleep:
                assert mock_sleep.called
                sleep_args = mock_sleep.call_args[0][0]
                assert sleep_args > 0
            else:
                mock_sleep.assert_not_called()

    @pytest.mark.parametrize(
        "cache_mode,data,should_validate",
        [
            (False, {"foo": 1}, True),   # cache off, with data
            (True, {"foo": 1}, True),    # cache on, with data
            (False, None, False),        # cache off, no data
            (True, None, False),         # cache on, no data
        ]
    )
    def test_fred_mapsapi_fred_get_request(self, cache_mode, data, should_validate):
        api = FredAPI("testkey", cache_mode=cache_mode, cache_size=10)
        maps_api = api.Maps
        fake_json = {"bar": "baz"}

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = fake_json

        with patch("fedfred.helpers.FredHelpers.geo_parameter_validation") as mock_validate, \
             patch("httpx.Client.get", return_value=mock_response) as mock_get, \
             patch.object(maps_api, "_MapsAPI__rate_limited") as mock_rate_limited:
            with patch("fedfred.clients.cached", lambda cache: (lambda f: f)):
                result = maps_api._MapsAPI__fred_get_request("/test", data=data)
                assert result == fake_json
                mock_get.assert_called_once()
                mock_rate_limited.assert_called()
                if should_validate:
                    mock_validate.assert_called_once_with(data)
                else:
                    mock_validate.assert_not_called()

    # Public Methods
    def test_get_shape_files(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps

        fake_response = {
            "title":"United States of America, small",
            "version":"1.1.3",
            "type":"FeatureCollection",
            "copyright":"Copyright (c) 2020 Highsoft AS, Based on data from Natural Earth",
            "copyrightShort":"Natural Earth",
            "copyrightUrl":"http:\/\/www.naturalearthdata.com",
            "crs":{
                "type":"name",
                "properties":{
                    "name":"urn:ogc:def:crs:EPSG:102004"
                    }
                },
            "hc-transform":{
                "default":{
                    "crs":"+proj=lcc +lat_1=33 +lat_2=45 +lat_0=39 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs",
                    "scale":0.000151481324748,
                    "jsonres":15.5,
                    "jsonmarginX":-999,
                    "jsonmarginY":9851,
                    "xoffset":-2361356.09818,
                    "yoffset":1398996.77886},
                    "us-all-hawaii":{
                        "xpan":190,
                        "ypan":417,
                        "hitZone":{
                            "type":"Polygon",
                            "coordinates":[[[1747,3920],[3651,2950],[3651,-999],[1747,-999],[1747,3920]]]
                            },
                        "crs":"+proj=aea +lat_1=8 +lat_2=18 +lat_0=13 +lon_0=-157 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs",
                        "scale":0.000123090941806,
                        "jsonres":15.5,
                        "jsonmarginX":-999,
                        "jsonmarginY":9851,
                        "xoffset":-338610.47557,
                        "yoffset":1022754.31736
                        },
                    "us-all-alaska":{
                        "rotation":-0.0174532925199,
                        "xpan":5,
                        "ypan":357,
                        "hitZone":{
                            "type":
                            "Polygon",
                            "coordinates":[[[-999,5188],[-707,5188],[1747,3920],[1747,-999],[-999,-999],[-999,5188]]]
                            },
                        "crs":"+proj=tmerc +lat_0=54 +lon_0=-142 +k=0.9999 +x_0=500000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs",
                        "scale":5.84397059179e-5,
                        "jsonres":15.5,"jsonmarginX":-999,
                        "jsonmarginY":9851,
                        "xoffset":-1566154.00853,
                        "yoffset":1992671.14918
                        }
                    },
            "features":[{
                "type":"Feature",
                "id":"US.MA",
                "properties":{
                    "hc-group":"admin1",
                    "hc-middle-x":0.36,
                    "hc-middle-y":0.47,
                    "hc-key":"us-ma",
                    "hc-a2":"MA",
                    "labelrank":"0",
                    "hasc":"US.MA",
                    "woe-id":"2347580",
                    "state_fips":"25",
                    "fips":"US25",
                    "postal-code":"MA",
                    "name":"Massachusetts",
                    "country":"United States of America",
                    "region":"Northeast",
                    "longitude":"-71.99930000000001",
                    "woe-name":"Massachusetts",
                    "latitude":"42.3739",
                    "woe-label":"Massachusetts, US, United States",
                    "type":"State"
                    },
                "geometry":{
                    "type":"MultiPolygon",
                    "coordinates":[[[[9727,7650],[10595,7650],[10595,7123],[9727,7123],[9727,7650]]],[[[9430,7889],[9476,7878],[9436,7864],[9417,7844],[9430,7889]]],[[[9314,7915],[9312,7927],[9304,7921],[9278,7938],[9254,7990],[9177,7968],[8997,7925],[8860,7896],[8853,7901],[8856,8080],[8922,8096],[9005,8115],[9005,8115],[9222,8166],[9242,8201],[9300,8236],[9318,8197],[9357,8186],[9312,8147],[9299,8081],[9324,8091],[9365,8074],[9428,7985],[9483,7974],[9525,8007],[9501,8067],[9535,8028],[9549,7982],[9504,7965],[9420,7906],[9411,7955],[9371,7921],[9373,7898],[9339,7878],[9327,7915],[9314,7915]]]]
                    }
                },]
            }
        for method in ["geopandas", "dask", "polars"]:
            with patch.object(maps_api, "_MapsAPI__fred_get_request", return_value=fake_response):
                with patch("geopandas.GeoDataFrame.from_features", return_value="gdf") as mock_gdf:
                    if method == "geopandas":
                        result = maps_api.get_shape_files("state", geodataframe_method="geopandas")
                        mock_gdf.assert_called_once_with(fake_response["features"])
                        assert result == "gdf"
                    elif method == "dask":
                        with patch("dask_geopandas.from_geopandas", return_value="dd_gdf") as mock_dd:
                            result = maps_api.get_shape_files("state", geodataframe_method="dask")
                            mock_gdf.assert_called_once_with(fake_response["features"])
                            mock_dd.assert_called_once_with("gdf", npartitions=1)
                            assert result == "dd_gdf"
                    elif method == "polars":
                        with patch("polars_st.from_geopandas", return_value="pl_gdf") as mock_pl:
                            result = maps_api.get_shape_files("state", geodataframe_method="polars")
                            mock_gdf.assert_called_once_with(fake_response["features"])
                            mock_pl.assert_called_once_with("gdf")
                            assert result == "pl_gdf"

        # Test dask ImportError
        with patch.object(maps_api, "_MapsAPI__fred_get_request", return_value=fake_response):
            with patch("geopandas.GeoDataFrame.from_features", return_value="gdf"):
                with patch.dict("sys.modules", {"dask_geopandas": None}):
                    with pytest.raises(ImportError) as excinfo:
                        maps_api.get_shape_files("state", geodataframe_method="dask")
                    assert "Dask GeoPandas is not installed" in str(excinfo.value)

        # Test polars ImportError
        with patch.object(maps_api, "_MapsAPI__fred_get_request", return_value=fake_response):
            with patch("geopandas.GeoDataFrame.from_features", return_value="gdf"):
                with patch.dict("sys.modules", {"polars_st": None}):
                    with pytest.raises(ImportError) as excinfo:
                        maps_api.get_shape_files("state", geodataframe_method="polars")
                    assert "Polars is not installed" in str(excinfo.value)

        # Test invalid method
        with patch.object(maps_api, "_MapsAPI__fred_get_request", return_value=fake_response):
            with patch("geopandas.GeoDataFrame.from_features", return_value="gdf"):
                with pytest.raises(ValueError, match="geodataframe_method must be 'geopandas', 'dask', or 'polars'"):
                    maps_api.get_shape_files("state", geodataframe_method="invalid")

    def test_get_series_group(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps

        fake_response = {
            "series_group": {
                "title" : "All Employees: Total Private",
                "region_type" : "state",
                "series_group" : "1223",
                "season" : "NSA",
                "units" : "Thousands of Persons",
                "frequency" : "Annual",
                "min_date" : "1990-01-01",
                "max_date" : "2021-01-01"
            }
        }
        fake_series_group = [MagicMock()]

        with patch.object(maps_api, "_MapsAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.clients.SeriesGroup.to_object", return_value=fake_series_group) as mock_to_object:
            result = maps_api.get_series_group("SMU56000000500000001")
            mock_get.assert_called_once_with("/series/group", {"series_id": "SMU56000000500000001", "file_type": "json"})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series_group

        with patch.object(maps_api, "_MapsAPI__fred_get_request", side_effect=ValueError("API error")):
            with pytest.raises(ValueError, match="API error"):
                maps_api.get_series_group("SMU56000000500000001")

        with patch.object(maps_api, "_MapsAPI__fred_get_request", return_value=fake_response), \
            patch("fedfred.clients.SeriesGroup.to_object", side_effect=ValueError("Parse error")):
            with pytest.raises(ValueError, match="Parse error"):
                maps_api.get_series_group("SMU56000000500000001")

    def test_get_series_data(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps

        fake_response = {
            "meta": {
                "title": "2012 Per Capita Personal Income by State (Dollars)",
                "region": "state",
                "seasonality": "Not Seasonally Adjusted",
                "units": "Dollars",
                "frequency": "Annual",
                "date": "2012-01-01",
                "data":{"2013-01-01":[{
                    "region": "Massachusetts",
                    "code": "25",
                    "value": "56713",
                    "series_id": "MAPCPI"
                    },]
                }
            }
        }
        meta_data = fake_response["meta"]
        fake_gdf = MagicMock(spec=gpd.GeoDataFrame)

        with patch.object(maps_api, "_MapsAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.helpers.FredHelpers.extract_region_type", return_value="state") as mock_extract, \
            patch.object(maps_api, "get_shape_files", return_value=fake_gdf) as mock_shape:

            # geopandas
            with patch("fedfred.helpers.FredHelpers.to_gpd_gdf", return_value="gdf") as mock_gdf_func:
                result = maps_api.get_series_data("MAPCPI", geodataframe_method="geopandas")
                mock_get.assert_called_once_with("/series/data", {"series_id": "MAPCPI", "file_type": "json"})
                mock_extract.assert_called_once_with(fake_response)
                mock_shape.assert_called_once_with("state")
                mock_gdf_func.assert_called_once_with(fake_gdf, meta_data)
                assert result == "gdf"

            # dask
            mock_get.reset_mock(); mock_extract.reset_mock(); mock_shape.reset_mock()
            with patch("fedfred.helpers.FredHelpers.to_dd_gpd_gdf", return_value="dd_gdf") as mock_dd:
                result = maps_api.get_series_data("MAPCPI", geodataframe_method="dask")
                mock_get.assert_called_once()
                mock_extract.assert_called_once()
                mock_shape.assert_called_once()
                mock_dd.assert_called_once_with(fake_gdf, meta_data)
                assert result == "dd_gdf"

            # polars
            mock_get.reset_mock(); mock_extract.reset_mock(); mock_shape.reset_mock()
            with patch("fedfred.helpers.FredHelpers.to_pl_st_gdf", return_value="pl_gdf") as mock_pl:
                result = maps_api.get_series_data("MAPCPI", geodataframe_method="polars")
                mock_get.assert_called_once()
                mock_extract.assert_called_once()
                mock_shape.assert_called_once()
                mock_pl.assert_called_once_with(fake_gdf, meta_data)
                assert result == "pl_gdf"

            # invalid geodataframe_method
            mock_get.reset_mock(); mock_extract.reset_mock(); mock_shape.reset_mock()
            with pytest.raises(ValueError, match="geodataframe_method must be 'geopandas', 'polars', or 'dask'"):
                maps_api.get_series_data("MAPCPI", geodataframe_method="invalid")

            # shapefile not a GeoDataFrame
            mock_get.reset_mock(); mock_extract.reset_mock(); mock_shape.reset_mock()
            with patch.object(maps_api, "get_shape_files", return_value=123):
                with pytest.raises(ValueError, match="shapefile type error"):
                    maps_api.get_series_data("MAPCPI", geodataframe_method="geopandas")

        # Test with date and start_date as datetime
        dt = datetime(2012, 1, 1)
        with patch.object(maps_api, "_MapsAPI__fred_get_request", return_value=fake_response) as mock_get, \
            patch("fedfred.helpers.FredHelpers.extract_region_type", return_value="state"), \
            patch.object(maps_api, "get_shape_files", return_value=fake_gdf), \
            patch("fedfred.helpers.FredHelpers.to_gpd_gdf", return_value="gdf"), \
            patch("fedfred.helpers.FredHelpers.datetime_conversion", return_value="2012-01-01") as mock_dtconv:
            maps_api.get_series_data("MAPCPI", geodataframe_method="geopandas", date=dt, start_date=dt)
            assert mock_dtconv.call_count == 2

    def test_get_regional_data(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Maps
        fake_response = {
            "2013 Per Capita Personal Income by State (Dollars)": {
                "2013": [{
                    "region": "Alabama",
                    "code": "01",
                    "value": "36481",
                    "series_id": "ALPCPI"
                }, {
                    "region": "Alaska",
                    "code": "02",
                    "value": "50150",
                    "series_id": "AKPCPI"
                }, {
                    "region": "Arizona",
                    "code": "04",
                    "value": "36983",
                    "series_id": "AZPCPI"
                }, {
                    "region": "Arkansas",
                    "code": "05",
                    "value": "36698",
                    "series_id": "ARPCPI"
                }, {
                    "region": "California",
                    "code": "06",
                    "value": "48434",
                    "series_id": "CAPCPI"
                }, {
                    "region": "Colorado",
                    "code": "08",
                    "value": "46897",
                    "series_id": "COPCPI"
                }, {
                    "region": "Connecticut",
                    "code": "09",
                    "value": "60658",
                    "series_id": "CTPCPI"
                }, {
                    "region": "Delaware",
                    "code": "10",
                    "value": "44815",
                    "series_id": "DEPCPI"
                }, {
                    "region": "District of Columbia",
                    "code": "11",
                    "value": "75329",
                    "series_id": "DCPCPI"
                }, {
                    "region": "Florida",
                    "code": "12",
                    "value": "41497",
                    "series_id": "FLPCPI"
                }, {
                    "region": "Georgia",
                    "code": "13",
                    "value": "37845",
                    "series_id": "GAPCPI"
                }, {
                    "region": "Hawaii",
                    "code": "15",
                    "value": "45204",
                    "series_id": "HIPCPI"
                }, {
                    "region": "Idaho",
                    "code": "16",
                    "value": "36146",
                    "series_id": "IDPCPI"
                }, {
                    "region": "Illinois",
                    "code": "17",
                    "value": "46980",
                    "series_id": "ILPCPI"
                }, {
                    "region": "Indiana",
                    "code": "18",
                    "value": "38622",
                    "series_id": "INPCPI"
                }, {
                    "region": "Iowa",
                    "code": "19",
                    "value": "44763",
                    "series_id": "IAPCPI"
                }, {
                    "region": "Kansas",
                    "code": "20",
                    "value": "44417",
                    "series_id": "KSPCPI"
                }, {
                    "region": "Kentucky",
                    "code": "21",
                    "value": "36214",
                    "series_id": "KYPCPI"
                }, {
                    "region": "Louisiana",
                    "code": "22",
                    "value": "41204",
                    "series_id": "LAPCPI"
                }, {
                    "region": "Maine",
                    "code": "23",
                    "value": "40924",
                    "series_id": "MEPCPI"
                }, {
                    "region": "Maryland",
                    "code": "24",
                    "value": "53826",
                    "series_id": "MDPCPI"
                }, {
                    "region": "Massachusetts",
                    "code": "25",
                    "value": "57248",
                    "series_id": "MAPCPI"
                }, {
                    "region": "Michigan",
                    "code": "26",
                    "value": "39055",
                    "series_id": "MIPCPI"
                }, {
                    "region": "Minnesota",
                    "code": "27",
                    "value": "47500",
                    "series_id": "MNPCPI"
                }, {
                    "region": "Mississippi",
                    "code": "28",
                    "value": "33913",
                    "series_id": "MSPCPI"
                }, {
                    "region": "Missouri",
                    "code": "29",
                    "value": "40663",
                    "series_id": "MOPCPI"
                }, {
                    "region": "Montana",
                    "code": "30",
                    "value": "39366",
                    "series_id": "MTPCPI"
                }, {
                    "region": "Nebraska",
                    "code": "31",
                    "value": "47157",
                    "series_id": "NEPCPI"
                }, {
                    "region": "Nevada",
                    "code": "32",
                    "value": "39235",
                    "series_id": "NVPCPI"
                }, {
                    "region": "New Hampshire",
                    "code": "33",
                    "value": "51013",
                    "series_id": "NHPCPI"
                }, {
                    "region": "New Jersey",
                    "code": "34",
                    "value": "55386",
                    "series_id": "NJPCPI"
                }, {
                    "region": "New Mexico",
                    "code": "35",
                    "value": "35965",
                    "series_id": "NMPCPI"
                }, {
                    "region": "New York",
                    "code": "36",
                    "value": "54462",
                    "series_id": "NYPCPI"
                }, {
                    "region": "North Carolina",
                    "code": "37",
                    "value": "38683",
                    "series_id": "NCPCPI"
                }, {
                    "region": "North Dakota",
                    "code": "38",
                    "value": "53182",
                    "series_id": "NDPCPI"
                }, {
                    "region": "Ohio",
                    "code": "39",
                    "value": "41049",
                    "series_id": "OHPCPI"
                }, {
                    "region": "Oklahoma",
                    "code": "40",
                    "value": "41861",
                    "series_id": "OKPCPI"
                }, {
                    "region": "Oregon",
                    "code": "41",
                    "value": "39848",
                    "series_id": "ORPCPI"
                }, {
                    "region": "Pennsylvania",
                    "code": "42",
                    "value": "46202",
                    "series_id": "PAPCPI"
                }, {
                    "region": "Rhode Island",
                    "code": "44",
                    "value": "46989",
                    "series_id": "RIPCPI"
                }, {
                    "region": "South Carolina",
                    "code": "45",
                    "value": "35831",
                    "series_id": "SCPCPI"
                }, {
                    "region": "South Dakota",
                    "code": "46",
                    "value": "46039",
                    "series_id": "SDPCPI"
                }, {
                    "region": "Tennessee",
                    "code": "47",
                    "value": "39558",
                    "series_id": "TNPCPI"
                }, {
                    "region": "Texas",
                    "code": "48",
                    "value": "43862",
                    "series_id": "TXPCPI"
                }, {
                    "region": "Utah",
                    "code": "49",
                    "value": "36640",
                    "series_id": "UTPCPI"
                }, {
                    "region": "Vermont",
                    "code": "50",
                    "value": "45483",
                    "series_id": "VTPCPI"
                }, {
                    "region": "Virginia",
                    "code": "51",
                    "value": "48838",
                    "series_id": "VAPCPI"
                }, {
                    "region": "Washington",
                    "code": "53",
                    "value": "47717",
                    "series_id": "WAPCPI"
                }, {
                    "region": "West Virginia",
                    "code": "54",
                    "value": "35533",
                    "series_id": "WVPCPI"
                }, {
                    "region": "Wisconsin",
                    "code": "55",
                    "value": "43244",
                    "series_id": "WIPCPI"
                }, {
                    "region": "Wyoming",
                    "code": "56",
                    "value": "52826",
                    "series_id": "WYPCPI"
                }]
            }
        }

        # Simulate the API's actual return structure for this endpoint
        meta_data = {"meta": "meta_info"}
        # Patch the API to return a dict with a 'meta' key for compatibility
        patched_response = {"meta": meta_data}

        fake_gdf = MagicMock(spec=gpd.GeoDataFrame)

        with patch.object(maps_api, "_MapsAPI__fred_get_request", return_value=patched_response) as mock_get, \
            patch("fedfred.helpers.FredHelpers.extract_region_type", return_value="state") as mock_extract, \
            patch.object(maps_api, "get_shape_files", return_value=fake_gdf) as mock_shape:

            # geopandas
            with patch("fedfred.helpers.FredHelpers.to_gpd_gdf", return_value="gdf") as mock_gdf_func:
                result = maps_api.get_regional_data(
                    series_group="882",
                    region_type="state",
                    date="2013-01-01",
                    season="NSA",
                    units="Dollars",
                    frequency="a",
                    geodataframe_method="geopandas"
                )
                mock_get.assert_called_once_with(
                    "/regional/data",
                    {
                        "series_group": "882",
                        "region_type": "state",
                        "date": "2013-01-01",
                        "season": "NSA",
                        "units": "Dollars",
                        "frequency": "a",
                        "file_type": "json"
                    }
                )
                mock_extract.assert_called_once_with(patched_response)
                mock_shape.assert_called_once_with("state")
                mock_gdf_func.assert_called_once_with(fake_gdf, meta_data)
                assert result == "gdf"

            # dask
            mock_get.reset_mock(); mock_extract.reset_mock(); mock_shape.reset_mock()
            with patch("fedfred.helpers.FredHelpers.to_dd_gpd_gdf", return_value="dd_gdf") as mock_dd:
                result = maps_api.get_regional_data(
                    series_group="882",
                    region_type="state",
                    date="2013-01-01",
                    season="NSA",
                    units="Dollars",
                    frequency="a",
                    geodataframe_method="dask"
                )
                mock_get.assert_called_once()
                mock_extract.assert_called_once()
                mock_shape.assert_called_once()
                mock_dd.assert_called_once_with(fake_gdf, meta_data)
                assert result == "dd_gdf"

            # polars
            mock_get.reset_mock(); mock_extract.reset_mock(); mock_shape.reset_mock()
            with patch("fedfred.helpers.FredHelpers.to_pl_st_gdf", return_value="pl_gdf") as mock_pl:
                result = maps_api.get_regional_data(
                    series_group="882",
                    region_type="state",
                    date="2013-01-01",
                    season="NSA",
                    units="Dollars",
                    frequency="a",
                    geodataframe_method="polars"
                )
                mock_get.assert_called_once()
                mock_extract.assert_called_once()
                mock_shape.assert_called_once()
                mock_pl.assert_called_once_with(fake_gdf, meta_data)
                assert result == "pl_gdf"

            # invalid geodataframe_method
            mock_get.reset_mock(); mock_extract.reset_mock(); mock_shape.reset_mock()
            with pytest.raises(ValueError, match="geodataframe_method must be 'geopandas', 'polars', or 'dask'"):
                maps_api.get_regional_data(
                    series_group="882",
                    region_type="state",
                    date="2013-01-01",
                    season="NSA",
                    units="Dollars",
                    frequency="a",
                    geodataframe_method="invalid"
                )

            # shapefile not a GeoDataFrame
            mock_get.reset_mock(); mock_extract.reset_mock(); mock_shape.reset_mock()
            with patch.object(maps_api, "get_shape_files", return_value=123):
                with pytest.raises(ValueError, match="shapefile type error"):
                    maps_api.get_regional_data(
                        series_group="882",
                        region_type="state",
                        date="2013-01-01",
                        season="NSA",
                        units="Dollars",
                        frequency="a",
                        geodataframe_method="geopandas"
                    )

        # Test with date and start_date as datetime, and all optional params
        dt = datetime(2013, 1, 1)
        dt_start = datetime(2012, 1, 1)
        with patch.object(maps_api, "_MapsAPI__fred_get_request", return_value=patched_response) as mock_get, \
            patch("fedfred.helpers.FredHelpers.extract_region_type", return_value="state"), \
            patch.object(maps_api, "get_shape_files", return_value=fake_gdf), \
            patch("fedfred.helpers.FredHelpers.to_gpd_gdf", return_value="gdf"), \
            patch("fedfred.helpers.FredHelpers.datetime_conversion", return_value="2013-01-01") as mock_dtconv:
            maps_api.get_regional_data(
                series_group="882",
                region_type="state",
                date=dt,
                season="NSA",
                units="Dollars",
                geodataframe_method="geopandas",
                start_date=dt_start,
                transformation="lin",
                frequency="a",
                aggregation_method="avg"
            )
            assert mock_dtconv.call_count == 2

class TestAsyncAPI:
    # Dunder methods
    def test_init(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async

        assert async_api._parent is parent
        assert async_api.cache_mode == parent.cache_mode
        assert async_api.cache is parent.cache
        assert async_api.base_url == parent.base_url
        assert hasattr(async_api, "Maps")
        assert isinstance(async_api.Maps, parent.AsyncAPI.AsyncMapsAPI)

    def test_repr(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        expected = f"{repr(parent)}.AsyncAPI"
        assert repr(async_api) == expected

    def test_str(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        expected = (
            f"{str(parent)}"
            f"  AsyncAPI Instance:\n"
            f"      Base URL: {async_api.base_url}\n"
        )
        assert str(async_api) == expected

    def test_eq(self):
        parent1 = FredAPI("testkey1", cache_mode=True, cache_size=10)
        parent2 = FredAPI("testkey2", cache_mode=True, cache_size=10)
        async_api1 = parent1.Async
        async_api2 = parent2.Async
        assert async_api1 == async_api1
        assert async_api1 != async_api2
        assert (async_api1 == 42) is False
        assert (async_api1 == "not an AsyncAPI") is False

    def test_hash(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        expected_hash = hash((parent.api_key, parent.cache_mode, parent.cache_size, parent.base_url))
        assert hash(async_api) == expected_hash

    def test_del(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        async_api.__del__()
        assert len(async_api.cache) == 0

    def test_getitem(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        async_api.cache["foo"] = "bar"
        assert async_api["foo"] == "bar"
        with pytest.raises(AttributeError, match="'baz' not found in cache."):
            _ = async_api["baz"]

    def test_len(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        async_api.cache["foo"] = "bar"
        async_api.cache["baz"] = "qux"
        assert len(async_api) == 2

    def test_contains(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        async_api.cache["foo"] = "bar"
        async_api.cache["baz"] = "qux"
        assert "foo" in async_api
        assert "baz" in async_api
        assert "quux" not in async_api

    def test_setitem(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        async_api["foo"] = "bar"
        assert async_api.cache["foo"] == "bar"
        async_api["baz"] = "qux"
        assert async_api.cache["baz"] == "qux"

    def test_delitem(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        async_api["foo"] = "bar"
        async_api["baz"] = "qux"
        del async_api["foo"]
        assert "foo" not in async_api
        assert "baz" in async_api
        with pytest.raises(AttributeError, match="'notfound' not found in cache."):
            del async_api["notfound"]

    def test_call(self):
        parent = FredAPI("testkey1234", cache_mode=True, cache_size=10)
        async_api = parent.Async
        async_api.cache["foo"] = "bar"
        async_api.cache["baz"] = "qux"
        summary = async_api()
        assert isinstance(summary, str)
        assert "FredAPI Instance:" in summary
        assert "AsyncAPI Instance:" in summary
        assert f"Base URL: {async_api.base_url}" in summary
        assert "Cache Mode: Enabled" in summary
        assert "Cache Size: 2 items" in summary
        assert "API Key: ****1234" in summary

    # Private Methods
    @pytest.mark.asyncio
    async def test_update_semaphore(self, monkeypatch):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async

        # Patch time.time to control "now"
        fake_now = 1_000_000.0
        monkeypatch.setattr("time.time", lambda: fake_now)

        # Case 1: No requests in the last minute
        parent.request_times.clear()
        parent.max_requests_per_minute = 10
        # Should set new_limit to max(1, min(1, 10//2)) = 1
        requests_left, time_left = await async_api._AsyncAPI__update_semaphore()
        assert requests_left == 10
        assert time_left == 60
        assert isinstance(parent.semaphore, asyncio.Semaphore)
        assert parent.semaphore._value == 1

        # Case 2: Some requests older than 60s should be purged
        parent.request_times.clear()
        parent.request_times.extend([fake_now - 70, fake_now - 61, fake_now - 10, fake_now - 5])
        parent.max_requests_per_minute = 10
        # Only -10 and -5 should remain after purge
        requests_left, time_left = await async_api._AsyncAPI__update_semaphore()
        assert list(parent.request_times) == [fake_now - 10, fake_now - 5]
        assert requests_left == 8
        # time_left = max(1, 60 - (now - (oldest))) = max(1, 60 - (0 - (-10))) = 50
        assert time_left == 50
        # new_limit = max(1, min(1, 8//2)) = 1
        assert parent.semaphore._value == 1

        # Case 3: All requests within last minute, requests_left < max_requests_per_minute
        parent.request_times.clear()
        parent.request_times.extend([fake_now - 10, fake_now - 5, fake_now - 1])
        parent.max_requests_per_minute = 5
        requests_left, time_left = await async_api._AsyncAPI__update_semaphore()
        assert requests_left == 2
        assert time_left == 50
        # new_limit = max(1, min(0, 2//2)) = 1
        assert parent.semaphore._value == 1

        # Case 4: All requests used up (requests_left == 0)
        parent.request_times.clear()
        parent.request_times.extend([fake_now - 10, fake_now - 5, fake_now - 1, fake_now - 0.5, fake_now - 0.1])
        parent.max_requests_per_minute = 5
        requests_left, time_left = await async_api._AsyncAPI__update_semaphore()
        assert requests_left == 0
        assert time_left == 50
        assert parent.semaphore._value == 1

        # Case 5: request_times is empty (should not error)
        parent.request_times.clear()
        parent.max_requests_per_minute = 15
        requests_left, time_left = await async_api._AsyncAPI__update_semaphore()
        assert requests_left == 15
        assert time_left == 60
        assert parent.semaphore._value == 1

    @pytest.mark.parametrize(
        "request_offsets,requests_left,time_left,expected_sleep",
        [
            ([-70], 1, 60, 60),        # Only one old request, requests_left > 0, sleep 60/1=60
            ([-10], 2, 50, 25),        # Two recent requests, requests_left > 0, sleep 50/2=25
            ([-10, -5], 0, 40, 60),    # All requests used, requests_left == 0, sleep 60
            ([-10, -5, -1], 0, 30, 60) # All requests used, requests_left == 0, sleep 60
        ]
    )
    @pytest.mark.asyncio
    async def test_async_rate_limited(self, request_offsets, requests_left, time_left, expected_sleep, monkeypatch):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async

        fake_now = 1_000_000.0
        monkeypatch.setattr("time.time", lambda: fake_now)
        parent.request_times.clear()
        for offset in request_offsets:
            parent.request_times.append(fake_now + offset)
        parent.semaphore = asyncio.Semaphore(1)
        parent.lock = asyncio.Lock()

        async def fake_update_semaphore():
            return requests_left, time_left

        monkeypatch.setattr(async_api, "_AsyncAPI__update_semaphore", fake_update_semaphore)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await async_api._AsyncAPI__rate_limited()
            if requests_left > 0:
                mock_sleep.assert_awaited_once_with(expected_sleep)
            else:
                mock_sleep.assert_awaited_once_with(60)
            assert len(parent.request_times) >= 1
            assert parent.request_times[-1] == fake_now

    @pytest.mark.parametrize(
        "cache_mode,data,should_validate",
        [
            (False, {"baz": 1}, True),   # cache off, with data
            (True, {"baz": 1}, True),    # cache on, with data
            (False, None, False),        # cache off, no data
            (True, None, False),         # cache on, no data
        ]
    )
    @pytest.mark.asyncio
    async def test_async_fred_get_request(self, cache_mode, data, should_validate, monkeypatch):
        parent = FredAPI("testkey", cache_mode=cache_mode, cache_size=10)
        async_api = parent.Async
        fake_json = {"foo": "bar"}

        with patch("fedfred.helpers.FredHelpers.parameter_validation_async", new_callable=AsyncMock) as mock_validate:
            monkeypatch.setattr(async_api, "_AsyncAPI__rate_limited", AsyncMock())
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = fake_json

            class DummyAsyncClient:
                async def __aenter__(self):
                    return self
                async def __aexit__(self, exc_type, exc, tb):
                    pass
                async def get(self, url, params=None, timeout=None):
                    return mock_response

            def fake_async_cached(cache):
                def decorator(func):
                    async def wrapper(*args, **kwargs):
                        return await func(*args, **kwargs)
                    return wrapper
                return decorator

            with patch("httpx.AsyncClient", DummyAsyncClient), \
                patch("fedfred.clients.async_cached", fake_async_cached):
                result = await async_api._AsyncAPI__fred_get_request("/test", data=data)
                assert result == fake_json
                if should_validate:
                    mock_validate.assert_awaited_once_with(data)
                else:
                    mock_validate.assert_not_awaited()

        class HTTPStatusErrorAsyncClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
            async def get(self, url, params=None, timeout=None):
                raise httpx.HTTPStatusError("fail", request=MagicMock(), response=MagicMock())

        with patch("fedfred.helpers.FredHelpers.parameter_validation_async", new_callable=AsyncMock), \
            patch("httpx.AsyncClient", HTTPStatusErrorAsyncClient), \
            patch("fedfred.clients.async_cached", fake_async_cached):
            monkeypatch.setattr(async_api, "_AsyncAPI__rate_limited", AsyncMock())
            with pytest.raises(tenacity.RetryError) as excinfo:
                await async_api._AsyncAPI__fred_get_request("/test", data=data)
            assert isinstance(excinfo.value.last_attempt.exception(), ValueError)
            assert "HTTP Error occurred:" in str(excinfo.value.last_attempt.exception())
        class RequestErrorAsyncClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
            async def get(self, url, params=None, timeout=None):
                raise httpx.RequestError("fail", request=MagicMock())

        with patch("fedfred.helpers.FredHelpers.parameter_validation_async", new_callable=AsyncMock), \
            patch("httpx.AsyncClient", RequestErrorAsyncClient), \
            patch("fedfred.clients.async_cached", fake_async_cached):
            monkeypatch.setattr(async_api, "_AsyncAPI__rate_limited", AsyncMock())
            with pytest.raises(tenacity.RetryError) as excinfo:
                await async_api._AsyncAPI__fred_get_request("/test", data=data)
            assert isinstance(excinfo.value.last_attempt.exception(), ValueError)
            assert "Request Error occurred:" in str(excinfo.value.last_attempt.exception())

    # Public methods
    ## Categories
    @pytest.mark.asyncio
    async def test_get_category(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async

        fake_response = {
            "categories": [
                {
                    "id": 125,
                    "name": "Trade Balance",
                    "parent_id": 13
                }
            ]
        }
        fake_result = [MagicMock()]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Category.to_object_async", AsyncMock(return_value=fake_result)) as mock_to_obj:
            result = await async_api.get_category(125)
            mock_get.assert_awaited_once_with("/category", {"category_id": 125})
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_result

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(side_effect=ValueError("HTTP Error"))):
            with pytest.raises(ValueError, match="HTTP Error"):
                await async_api.get_category(125)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
            patch("fedfred.objects.Category.to_object_async", AsyncMock(side_effect=ValueError("Parse Error"))):
            with pytest.raises(ValueError, match="Parse Error"):
                await async_api.get_category(125)

    @pytest.mark.asyncio
    async def test_get_category_children(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async

        fake_response = {
            "categories": [
                {
                    "id": 16,
                    "name": "Exports",
                    "parent_id": 13
                },
                {
                    "id": 17,
                    "name": "Imports",
                    "parent_id": 13
                }
            ]
        }
        fake_result = [MagicMock()]
        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Category.to_object_async", AsyncMock(return_value=fake_result)) as mock_to_obj:
            result = await async_api.get_category_children(13)
            mock_get.assert_awaited_once_with("/category/children", {"category_id": 13})
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_result

        dt = datetime(2020, 1, 1)
        with patch("fedfred.helpers.FredHelpers.datetime_conversion_async", AsyncMock(return_value="2020-01-01")) as mock_dtconv, \
            patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Category.to_object_async", AsyncMock(return_value=fake_result)) as mock_to_obj:
            result = await async_api.get_category_children(13, realtime_start=dt, realtime_end=dt)
            assert mock_dtconv.await_count == 2
            mock_get.assert_awaited_once_with(
                "/category/children",
                {"category_id": 13, "realtime_start": "2020-01-01", "realtime_end": "2020-01-01"}
            )
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_result

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Category.to_object_async", AsyncMock(return_value=fake_result)) as mock_to_obj:
            result = await async_api.get_category_children(13, realtime_start="2021-01-01", realtime_end="2021-12-31")
            mock_get.assert_awaited_once_with(
                "/category/children",
                {"category_id": 13, "realtime_start": "2021-01-01", "realtime_end": "2021-12-31"}
            )
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_result

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(side_effect=ValueError("HTTP Error"))):
            with pytest.raises(ValueError, match="HTTP Error"):
                await async_api.get_category_children(13)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
            patch("fedfred.objects.Category.to_object_async", AsyncMock(side_effect=ValueError("Parse Error"))):
            with pytest.raises(ValueError, match="Parse Error"):
                await async_api.get_category_children(13)

    @pytest.mark.asyncio
    async def test_get_category_related(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async

        fake_response = {
            "categories": [
                {
                    "id": 149,
                    "name": "Arkansas",
                    "parent_id": 27281
                },
                {
                    "id": 150,
                    "name": "Illinois",
                    "parent_id": 27281
                }
            ]
        }
        fake_result = [MagicMock()]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Category.to_object_async", AsyncMock(return_value=fake_result)) as mock_to_obj:
            result = await async_api.get_category_related(27281)
            mock_get.assert_awaited_once_with("/category/related", {"category_id": 27281})
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_result

        dt = datetime(2021, 1, 1)
        with patch("fedfred.helpers.FredHelpers.datetime_conversion_async", AsyncMock(return_value="2021-01-01")) as mock_dtconv, \
            patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Category.to_object_async", AsyncMock(return_value=fake_result)) as mock_to_obj:
            result = await async_api.get_category_related(27281, realtime_start=dt, realtime_end=dt)
            assert mock_dtconv.await_count == 2
            mock_get.assert_awaited_once_with(
                "/category/related",
                {"category_id": 27281, "realtime_start": "2021-01-01", "realtime_end": "2021-01-01"}
            )
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_result

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Category.to_object_async", AsyncMock(return_value=fake_result)) as mock_to_obj:
            result = await async_api.get_category_related(27281, realtime_start="2022-01-01", realtime_end="2022-12-31")
            mock_get.assert_awaited_once_with(
                "/category/related",
                {"category_id": 27281, "realtime_start": "2022-01-01", "realtime_end": "2022-12-31"}
            )
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_result

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(side_effect=ValueError("HTTP Error"))):
            with pytest.raises(ValueError, match="HTTP Error"):
                await async_api.get_category_related(27281)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
            patch("fedfred.objects.Category.to_object_async", AsyncMock(side_effect=ValueError("Parse Error"))):
            with pytest.raises(ValueError, match="Parse Error"):
                await async_api.get_category_related(27281)

    @pytest.mark.asyncio
    async def test_get_category_series(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async

        fake_response = {
            "realtime_start": "2017-08-01",
            "realtime_end": "2017-08-01",
            "order_by": "series_id",
            "sort_order": "asc",
            "count": 45,
            "offset": 0,
            "limit": 1000,
            "seriess": [
                {
                    "id": "BOPBCA",
                    "realtime_start": "2017-08-01",
                    "realtime_end": "2017-08-01",
                    "title": "Balance on Current Account (DISCONTINUED)",
                    "observation_start": "1960-01-01",
                    "observation_end": "2014-01-01",
                    "frequency": "Quarterly",
                    "frequency_short": "Q",
                    "units": "Billions of Dollars",
                    "units_short": "Bil. of $",
                    "seasonal_adjustment": "Seasonally Adjusted",
                    "seasonal_adjustment_short": "SA",
                    "last_updated": "2014-06-18 08:41:28-05",
                    "popularity": 32,
                    "group_popularity": 34,
                    "notes": "This series has been discontinued as a result of the comprehensive restructuring of the international economic accounts (http:\/\/www.bea.gov\/international\/modern.htm). For a crosswalk of the old and new series in FRED see: http:\/\/research.stlouisfed.org\/CompRevisionReleaseID49.xlsx."
                },
                {
                    "id": "BOPBCAA",
                    "realtime_start": "2017-08-01",
                    "realtime_end": "2017-08-01",
                    "title": "Balance on Current Account (DISCONTINUED)",
                    "observation_start": "1960-01-01",
                    "observation_end": "2013-01-01",
                    "frequency": "Annual",
                    "frequency_short": "A",
                    "units": "Billions of Dollars",
                    "units_short": "Bil. of $",
                    "seasonal_adjustment": "Not Seasonally Adjusted",
                    "seasonal_adjustment_short": "NSA",
                    "last_updated": "2014-06-18 08:41:28-05",
                    "popularity": 14,
                    "group_popularity": 34,
                    "notes": "This series has been discontinued as a result of the comprehensive restructuring of the international economic accounts (http:\/\/www.bea.gov\/international\/modern.htm). For a crosswalk of the old and new series in FRED see: http:\/\/research.stlouisfed.org\/CompRevisionReleaseID49.xlsx."
                },
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
             patch("fedfred.objects.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_obj:
            result = await async_api.get_category_series(125)
            mock_get.assert_awaited_once_with("/category/series", {"category_id": 125})
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
             patch("fedfred.objects.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_obj:
            result = await async_api.get_category_series(
                125,
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                limit=10,
                offset=2,
                order_by="series_id",
                sort_order="asc",
                filter_variable="frequency",
                filter_value="Quarterly",
                tag_names="macro",
                exclude_tag_names="foo"
            )
            mock_get.assert_awaited_once_with(
                "/category/series",
                {
                    "category_id": 125,
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "limit": 10,
                    "offset": 2,
                    "order_by": "series_id",
                    "sort_order": "asc",
                    "filter_variable": "frequency",
                    "filter_value": "Quarterly",
                    "tag_names": "macro",
                    "exclude_tag_names": "foo"
                }
            )
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_series

        with patch("fedfred.helpers.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "dt2020")), \
            patch("fedfred.helpers.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=",".join)) as mock_list_conv, \
             patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
             patch("fedfred.objects.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_obj:
            result = await async_api.get_category_series(
                125,
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=tag_list,
                exclude_tag_names=exclude_tag_list
            )
            assert mock_list_conv.await_count == 2
            mock_get.assert_awaited_once_with(
                "/category/series",
                {
                    "category_id": 125,
                    "realtime_start": "dt2020",
                    "realtime_end": "dt2020",
                    "tag_names": "macro,gdp",
                    "exclude_tag_names": "foo,bar"
                }
            )
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(side_effect=ValueError("HTTP Error"))):
            with pytest.raises(ValueError, match="HTTP Error"):
                await async_api.get_category_series(125)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
             patch("fedfred.objects.Series.to_object_async", AsyncMock(side_effect=ValueError("Parse Error"))):
            with pytest.raises(ValueError, match="Parse Error"):
                await async_api.get_category_series(125)

    @pytest.mark.asyncio
    async def test_get_category_tags(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async

        fake_response = {
            "realtime_start": "2013-08-13",
            "realtime_end": "2013-08-13",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 21,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "bea",
                    "group_id": "src",
                    "notes": "U.S. Department of Commerce: Bureau of Economic Analysis",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 87,
                    "series_count": 24
                },
                {
                    "name": "nation",
                    "group_id": "geot",
                    "notes": "Country Level",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 100,
                    "series_count": 24
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_obj:
            result = await async_api.get_category_tags(125)
            mock_get.assert_awaited_once_with("/category/tags", {"category_id": 125})
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_obj:
            result = await async_api.get_category_tags(
                125,
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                tag_names="macro",
                tag_group_id=1,
                search_text="foo",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            mock_get.assert_awaited_once_with(
                "/category/tags",
                {
                    "category_id": 125,
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "macro",
                    "tag_group_id": 1,
                    "search_text": "foo",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_tags

        with patch("fedfred.helpers.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "dt2020")), \
            patch("fedfred.helpers.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=",".join)) as mock_list_conv, \
            patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_obj:
            result = await async_api.get_category_tags(
                125,
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=tag_list
            )
            assert mock_list_conv.await_count == 1
            mock_get.assert_awaited_once_with(
                "/category/tags",
                {
                    "category_id": 125,
                    "realtime_start": "dt2020",
                    "realtime_end": "dt2020",
                    "tag_names": "macro,gdp"
                }
            )
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(side_effect=ValueError("HTTP Error"))):
            with pytest.raises(ValueError, match="HTTP Error"):
                await async_api.get_category_tags(125)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
            patch("fedfred.objects.Tag.to_object_async", AsyncMock(side_effect=ValueError("Parse Error"))):
            with pytest.raises(ValueError, match="Parse Error"):
                await async_api.get_category_tags(125)

    @pytest.mark.asyncio
    async def test_get_category_related_tags(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-13",
            "realtime_end": "2013-08-13",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 7,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "balance",
                    "group_id": "gen",
                    "notes": "",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 65,
                    "series_count": 4
                },
                {
                    "name": "bea",
                    "group_id": "src",
                    "notes": "U.S. Department of Commerce: Bureau of Economic Analysis",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 87,
                    "series_count": 4
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_obj:
            result = await async_api.get_category_related_tags(125)
            mock_get.assert_awaited_once_with("/category/related_tags", {"category_id": 125})
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_obj:
            result = await async_api.get_category_related_tags(
                125,
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                tag_names="macro",
                exclude_tag_names="foo",
                tag_group_id="grp",
                search_text="foo",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            mock_get.assert_awaited_once_with(
                "/category/related_tags",
                {
                    "category_id": 125,
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "macro",
                    "exclude_tag_names": "foo",
                    "tag_group_id": "grp",
                    "search_text": "foo",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_tags

        with patch("fedfred.helpers.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "dt2020")), \
            patch("fedfred.helpers.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=",".join)) as mock_list_conv, \
            patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.objects.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_obj:
            result = await async_api.get_category_related_tags(
                125,
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=tag_list,
                exclude_tag_names=exclude_tag_list
            )
            assert mock_list_conv.await_count == 2
            mock_get.assert_awaited_once_with(
                "/category/related_tags",
                {
                    "category_id": 125,
                    "realtime_start": "dt2020",
                    "realtime_end": "dt2020",
                    "tag_names": "macro,gdp",
                    "exclude_tag_names": "foo,bar"
                }
            )
            mock_to_obj.assert_awaited_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(side_effect=ValueError("HTTP Error"))):
            with pytest.raises(ValueError, match="HTTP Error"):
                await async_api.get_category_related_tags(125)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
            patch("fedfred.objects.Tag.to_object_async", AsyncMock(side_effect=ValueError("Parse Error"))):
            with pytest.raises(ValueError, match="Parse Error"):
                await async_api.get_category_related_tags(125)

    ## Releases
    @pytest.mark.asyncio
    async def test_get_releases(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-13",
            "realtime_end": "2013-08-13",
            "order_by": "release_id",
            "sort_order": "asc",
            "count": 158,
            "offset": 0,
            "limit": 1000,
            "releases": [
                {
                    "id": 9,
                    "realtime_start": "2013-08-13",
                    "realtime_end": "2013-08-13",
                    "name": "Advance Monthly Sales for Retail and Food Services",
                    "press_release": True,
                    "link": "http://www.census.gov/retail/"
                },
                {
                    "id": 10,
                    "realtime_start": "2013-08-13",
                    "realtime_end": "2013-08-13",
                    "name": "Consumer Price Index",
                    "press_release": True,
                    "link": "http://www.bls.gov/cpi/"
                }
            ]
        }
        fake_releases = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
                    result = await async_api.get_releases(
                        realtime_start=dt_start,
                        realtime_end=dt_end,
                        limit=50,
                        offset=10,
                        order_by="name",
                        sort_order="desc"
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/releases",
                        {
                            "realtime_start": "converted",
                            "realtime_end": "converted",
                            "limit": 50,
                            "offset": 10,
                            "order_by": "name",
                            "sort_order": "desc"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_releases

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
                result = await async_api.get_releases(
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31",
                    limit=10,
                    offset=2,
                    order_by="release_id",
                    sort_order="asc"
                )
                mock_get.assert_called_once_with(
                    "/releases",
                    {
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31",
                        "limit": 10,
                        "offset": 2,
                        "order_by": "release_id",
                        "sort_order": "asc"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
                result = await async_api.get_releases()
                mock_get.assert_called_once_with("/releases", {})
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

    @pytest.mark.asyncio
    async def test_get_releases_dates(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-01-01",
            "realtime_end": "9999-12-31",
            "order_by": "release_date",
            "sort_order": "desc",
            "count": 1129,
            "offset": 0,
            "limit": 1000,
            "release_dates": [
                {
                    "release_id": 9,
                    "release_name": "Advance Monthly Sales for Retail and Food Services",
                    "date": "2013-08-13"
                },
                {
                    "release_id": 262,
                    "release_name": "Failures and Assistance Transactions",
                    "date": "2013-08-13"
                }
            ]
        }
        fake_dates = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.ReleaseDate.to_object_async", AsyncMock(return_value=fake_dates)) as mock_to_object:
                    result = await async_api.get_releases_dates(
                        realtime_start=dt_start,
                        realtime_end=dt_end,
                        limit=50,
                        offset=10,
                        order_by="release_date",
                        sort_order="desc",
                        include_releases_dates_with_no_data=True
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/releases/dates",
                        {
                            "realtime_start": "converted",
                            "realtime_end": "converted",
                            "limit": 50,
                            "offset": 10,
                            "order_by": "release_date",
                            "sort_order": "desc",
                            "include_releases_dates_with_no_data": True
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_dates

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.ReleaseDate.to_object_async", AsyncMock(return_value=fake_dates)) as mock_to_object:
                result = await async_api.get_releases_dates(
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31",
                    limit=10,
                    offset=2,
                    order_by="release_id",
                    sort_order="asc",
                    include_releases_dates_with_no_data=False
                )
                mock_get.assert_called_once_with(
                    "/releases/dates",
                    {
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31",
                        "limit": 10,
                        "offset": 2,
                        "order_by": "release_id",
                        "sort_order": "asc"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_dates

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.ReleaseDate.to_object_async", AsyncMock(return_value=fake_dates)) as mock_to_object:
                result = await async_api.get_releases_dates()
                mock_get.assert_called_once_with("/releases/dates", {})
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_dates

    @pytest.mark.asyncio
    async def test_get_release(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "releases": [
                {
                    "id": 53,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "Gross Domestic Product",
                    "press_release": True,
                    "link": "http://www.bea.gov/national/index.htm"
                }
            ]
        }
        fake_releases = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
                    result = await async_api.get_release(
                        53,
                        realtime_start=dt_start,
                        realtime_end=dt_end
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/release/",
                        {
                            "release_id": 53,
                            "realtime_start": "converted",
                            "realtime_end": "converted"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_releases

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
                result = await async_api.get_release(
                    53,
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/release/",
                    {
                        "release_id": 53,
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
                result = await async_api.get_release(53)
                mock_get.assert_called_once_with(
                    "/release/",
                    {"release_id": 53}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

    @pytest.mark.asyncio
    async def test_get_release_dates(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "1776-07-04",
            "realtime_end": "9999-12-31",
            "order_by": "release_date",
            "sort_order": "asc",
            "count": 17,
            "offset": 0,
            "limit": 10000,
            "release_dates": [
                {
                    "release_id": 82,
                    "date": "1997-02-10"
                },
                {
                    "release_id": 82,
                    "date": "1998-02-10"
                }
            ]
        }
        fake_dates = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.ReleaseDate.to_object_async", AsyncMock(return_value=fake_dates)) as mock_to_object:
                    result = await async_api.get_release_dates(
                        82,
                        realtime_start=dt_start,
                        realtime_end=dt_end,
                        limit=100,
                        offset=5,
                        sort_order="desc",
                        include_releases_dates_with_no_data=True
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/release/dates",
                        {
                            "release_id": 82,
                            "realtime_start": "converted",
                            "realtime_end": "converted",
                            "limit": 100,
                            "offset": 5,
                            "sort_order": "desc",
                            "include_releases_dates_with_no_data": True
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_dates

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.ReleaseDate.to_object_async", AsyncMock(return_value=fake_dates)) as mock_to_object:
                result = await async_api.get_release_dates(
                    82,
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31",
                    limit=10,
                    offset=2,
                    sort_order="asc",
                    include_releases_dates_with_no_data=False
                )
                mock_get.assert_called_once_with(
                    "/release/dates",
                    {
                        "release_id": 82,
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31",
                        "limit": 10,
                        "offset": 2,
                        "sort_order": "asc"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_dates

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.ReleaseDate.to_object_async", AsyncMock(return_value=fake_dates)) as mock_to_object:
                result = await async_api.get_release_dates(82)
                mock_get.assert_called_once_with(
                    "/release/dates",
                    {"release_id": 82}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_dates

        with pytest.raises(ValueError, match="category_id must be a non-negative integer"):
            await async_api.get_release_dates(-1)
        with pytest.raises(ValueError, match="category_id must be a non-negative integer"):
            await async_api.get_release_dates("not_an_int")

    @pytest.mark.asyncio
    async def test_get_release_series(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2017-08-01",
            "realtime_end": "2017-08-01",
            "order_by": "series_id",
            "sort_order": "asc",
            "count": 57,
            "offset": 0,
            "limit": 1000,
            "seriess": [
                {
                "id": "BOMTVLM133S",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "U.S. Imports of Services - Travel",
                "observation_start": "1992-01-01",
                "observation_end": "2017-05-01",
                "frequency": "Monthly",
                "frequency_short": "M",
                "units": "Million of Dollars",
                "units_short": "Mil. of $",
                "seasonal_adjustment": "Seasonally Adjusted",
                "seasonal_adjustment_short": "SA",
                "last_updated": "2017-07-06 09:34:00-05",
                "popularity": 0,
                "group_popularity": 0
                },
                {
                "id": "BOMVGMM133S",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "U.S. Imports of Services: U.S. Government Miscellaneous Services (DISCONTINUED)",
                "observation_start": "1992-01-01",
                "observation_end": "2013-12-01",
                "frequency": "Monthly",
                "frequency_short": "M",
                "units": "Millions of Dollars",
                "units_short": "Mil. of $",
                "seasonal_adjustment": "Seasonally Adjusted",
                "seasonal_adjustment_short": "SA",
                "last_updated": "2014-10-20 09:27:37-05",
                "popularity": 0,
                "group_popularity": 0,
                "notes": "BEA has introduced new table presentations, including a new presentation of services, as part of a comprehensive restructuring of BEA\u2019s international economic accounts.For more information see http:\/\/www.bea.gov\/international\/revision-2014.htm."
                }
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        exclude_tag_list = ["foo", "bar"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=lambda x: "foo,bar")) as mock_list_conv:
                    with patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
                        result = await async_api.get_release_series(
                            51,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            limit=100,
                            offset=5,
                            sort_order="desc",
                            filter_variable="units",
                            filter_value="Millions of Dollars",
                            exclude_tag_names=exclude_tag_list
                        )
                        assert mock_conv.call_count == 2
                        mock_list_conv.assert_called_once_with(exclude_tag_list)
                        mock_get.assert_called_once_with(
                            "/release/series",
                            {
                                "release_id": 51,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "limit": 100,
                                "offset": 5,
                                "sort_order": "desc",
                                "filter_variable": "units",
                                "filter_value": "Millions of Dollars",
                                "exclude_tag_names": "foo,bar"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
                result = await async_api.get_release_series(
                    51,
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31",
                    limit=10,
                    offset=2,
                    sort_order="asc",
                    filter_variable="frequency",
                    filter_value="Monthly",
                    exclude_tag_names="foo"
                )
                mock_get.assert_called_once_with(
                    "/release/series",
                    {
                        "release_id": 51,
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31",
                        "limit": 10,
                        "offset": 2,
                        "sort_order": "asc",
                        "filter_variable": "frequency",
                        "filter_value": "Monthly",
                        "exclude_tag_names": "foo"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
                result = await async_api.get_release_series(51)
                mock_get.assert_called_once_with(
                    "/release/series",
                    {"release_id": 51}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_series

        with pytest.raises(tenacity.RetryError) as excinfo:
            await async_api.get_release_series(-1)
        assert isinstance(excinfo.value.last_attempt.exception(), ValueError)
        assert "release_id must be a non-negative integer" in str(excinfo.value.last_attempt.exception())

        with pytest.raises(tenacity.RetryError) as excinfo:
            await async_api.get_release_series("not_an_int")
        assert isinstance(excinfo.value.last_attempt.exception(), ValueError)
        assert "release_id must be a non-negative integer" in str(excinfo.value.last_attempt.exception())

    @pytest.mark.asyncio
    async def test_get_release_sources(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "sources": [
                {
                    "id": 18,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "U.S. Department of Commerce: Bureau of Economic Analysis",
                    "link": "http://www.bea.gov/"
                },
                {
                    "id": 19,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "U.S. Department of Commerce: Census Bureau",
                    "link": "http://www.census.gov/"
                }
            ]
        }
        fake_sources = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.Source.to_object_async", AsyncMock(return_value=fake_sources)) as mock_to_object:
                    result = await async_api.get_release_sources(
                        51,
                        realtime_start=dt_start,
                        realtime_end=dt_end
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/release/sources",
                        {
                            "release_id": 51,
                            "realtime_start": "converted",
                            "realtime_end": "converted"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_sources

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Source.to_object_async", AsyncMock(return_value=fake_sources)) as mock_to_object:
                result = await async_api.get_release_sources(
                    51,
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/release/sources",
                    {
                        "release_id": 51,
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_sources

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Source.to_object_async", AsyncMock(return_value=fake_sources)) as mock_to_object:
                result = await async_api.get_release_sources(51)
                mock_get.assert_called_once_with(
                    "/release/sources",
                    {"release_id": 51}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_sources

    @pytest.mark.asyncio
    async def test_get_release_tags(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 13,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "commercial paper",
                    "group_id": "gen",
                    "notes": "",
                    "created": "2012-03-19 10:40:59-05",
                    "popularity": 55,
                    "series_count": 18
                },
                {
                    "name": "frb",
                    "group_id": "src",
                    "notes": "Board of Governors of the Federal Reserve System",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 90,
                    "series_count": 18
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=lambda x: "macro;gdp")) as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
                        result = await async_api.get_release_tags(
                            86,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names=tag_list
                        )
                        assert mock_conv.call_count == 2
                        mock_list_conv.assert_called_once_with(tag_list)
                        mock_get.assert_called_once_with(
                            "/release/tags",
                            {
                                "release_id": 86,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro;gdp"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=lambda x: "macro;gdp")) as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
                        result = await async_api.get_release_tags(
                            86,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names="macro"
                        )
                        assert mock_conv.call_count == 2
                        mock_list_conv.assert_not_called()
                        mock_get.assert_called_once_with(
                            "/release/tags",
                            {
                                "release_id": 86,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=lambda x: "macro;gdp")) as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
                        result = await async_api.get_release_tags(
                            86,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names=tag_list,
                            tag_group_id=42,
                            search_text="foo",
                            limit=5,
                            offset=2,
                            order_by="series_count"
                        )
                        mock_get.assert_called_once_with(
                            "/release/tags",
                            {
                                "release_id": 86,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro;gdp",
                                "tag_group_id": 42,
                                "search_text": "foo",
                                "limit": 5,
                                "offset": 2,
                                "order_by": "series_count"
                            }
                        )
                        assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
                result = await async_api.get_release_tags(86)
                mock_get.assert_called_once_with(
                    "/release/tags",
                    {"release_id": 86}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_tags

    @pytest.mark.asyncio
    async def test_get_release_related_tags(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 7,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "commercial paper",
                    "group_id": "gen",
                    "notes": "",
                    "created": "2012-03-19 10:40:59-05",
                    "popularity": 55,
                    "series_count": 2
                },
                {
                    "name": "frb",
                    "group_id": "src",
                    "notes": "Board of Governors of the Federal Reserve System",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 90,
                    "series_count": 2
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=";".join)) as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
                        result = await async_api.get_release_related_tags(
                            86,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names=tag_list,
                            exclude_tag_names=exclude_tag_list,
                            tag_group_id="grp",
                            search_text="foo",
                            limit=5,
                            offset=2,
                            order_by="series_count",
                            sort_order="desc"
                        )
                        assert mock_conv.call_count == 2
                        assert mock_list_conv.call_count == 2
                        mock_get.assert_called_once_with(
                            "/release/related_tags",
                            {
                                "release_id": 86,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro;gdp",
                                "exclude_tag_names": "foo;bar",
                                "tag_group_id": "grp",
                                "search_text": "foo",
                                "limit": 5,
                                "offset": 2,
                                "order_by": "series_count",
                                "sort_order": "desc"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=";".join)) as mock_list_conv:
                    with patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
                        result = await async_api.get_release_related_tags(
                            86,
                            realtime_start=dt_start,
                            realtime_end=dt_end,
                            tag_names="macro",
                            exclude_tag_names="foo"
                        )
                        assert mock_conv.call_count == 2
                        mock_list_conv.assert_not_called()
                        mock_get.assert_called_once_with(
                            "/release/related_tags",
                            {
                                "release_id": 86,
                                "realtime_start": "converted",
                                "realtime_end": "converted",
                                "tag_names": "macro",
                                "exclude_tag_names": "foo"
                            }
                        )
                        mock_to_object.assert_called_once_with(fake_response)
                        assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
                result = await async_api.get_release_related_tags(86)
                mock_get.assert_called_once_with(
                    "/release/related_tags",
                    {"release_id": 86}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_tags

    @pytest.mark.asyncio
    async def test_get_release_tables(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "name": "Personal consumption expenditures",
            "element_id": 12886,
            "release_id": "53",
            "elements":
            {
                "12887":
                {
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
                            "children": []
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
                            "children": []
                        }
                    ]
                },
                "12888":
                {
                    "element_id": 12888,
                    "release_id": 53,
                    "series_id": "DDURRL1A225NBEA",
                    "parent_id": 12887,
                    "line": "4",
                    "type": "series",
                    "name": "Durable goods",
                    "level": "2",
                    "children": []
                },
                "12889":
                {
                    "element_id": 12889,
                    "release_id": 53,
                    "series_id": "DNDGRL1A225NBEA",
                    "parent_id": 12887,
                    "line": "5",
                    "type": "series",
                    "name": "Nondurable goods",
                    "level": "2",
                    "children": []
                },
                "12890":
                {
                    "element_id": 12890,
                    "release_id": 53,
                    "series_id": "DSERRL1A225NBEA",
                    "parent_id": 12886,
                    "line": "6",
                    "type": "series",
                    "name": "Services",
                    "level": "1",
                    "children": []
                }
            }
        }
        fake_elements = [MagicMock()]
        dt_obs = datetime(2020, 1, 1)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "2020-01-01")) as mock_dt_conv:
                with patch("fedfred.clients.Element.to_object_async", AsyncMock(return_value=fake_elements)) as mock_to_object:
                    result = await async_api.get_release_tables(
                        53,
                        element_id=12887,
                        include_observation_values=True,
                        observation_date=dt_obs
                    )
                    mock_dt_conv.assert_called_once_with(dt_obs)
                    mock_get.assert_called_once_with(
                        "/release/tables",
                        {
                            "release_id": 53,
                            "element_id": 12887,
                            "include_observation_values": True,
                            "observation_date": "2020-01-01"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_elements

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Element.to_object_async", AsyncMock(return_value=fake_elements)) as mock_to_object:
                result = await async_api.get_release_tables(
                    53,
                    observation_date="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/release/tables",
                    {
                        "release_id": 53,
                        "observation_date": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_elements

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Element.to_object_async", AsyncMock(return_value=fake_elements)) as mock_to_object:
                result = await async_api.get_release_tables(53)
                mock_get.assert_called_once_with(
                    "/release/tables",
                    {"release_id": 53}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_elements

    ## Series
    @pytest.mark.asyncio
    async def test_get_series(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "seriess": [
                {
                    "id": "GNPCA",
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "title": "Real Gross National Product",
                    "observation_start": "1929-01-01",
                    "observation_end": "2012-01-01",
                    "frequency": "Annual",
                    "frequency_short": "A",
                    "units": "Billions of Chained 2009 Dollars",
                    "units_short": "Bil. of Chn. 2009 $",
                    "seasonal_adjustment": "Not Seasonally Adjusted",
                    "seasonal_adjustment_short": "NSA",
                    "last_updated": "2013-07-31 09:26:16-05",
                    "popularity": 39,
                    "notes": "BEA Account Code: A001RX1"
                }
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
                    result = await async_api.get_series(
                        "GNPCA",
                        realtime_start=dt_start,
                        realtime_end=dt_end
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/series",
                        {
                            "series_id": "GNPCA",
                            "realtime_start": "converted",
                            "realtime_end": "converted"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
                result = await async_api.get_series(
                    "GNPCA",
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/series",
                    {
                        "series_id": "GNPCA",
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
                result = await async_api.get_series("GNPCA")
                mock_get.assert_called_once_with(
                    "/series",
                    {"series_id": "GNPCA"}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_series

    @pytest.mark.asyncio
    async def test_get_series_categories(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "categories": [
                {
                    "id": 95,
                    "name": "Monthly Rates",
                    "parent_id": 15
                },
                {
                    "id": 275,
                    "name": "Japan",
                    "parent_id": 158
                }
            ]
        }
        fake_categories = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.Category.to_object_async", AsyncMock(return_value=fake_categories)) as mock_to_object:
                    result = await async_api.get_series_categories(
                        "EXJPUS",
                        realtime_start=dt_start,
                        realtime_end=dt_end
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/series/categories",
                        {
                            "series_id": "EXJPUS",
                            "realtime_start": "converted",
                            "realtime_end": "converted"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_categories

        # With string for start/end
        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Category.to_object_async", AsyncMock(return_value=fake_categories)) as mock_to_object:
                result = await async_api.get_series_categories(
                    "EXJPUS",
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/series/categories",
                    {
                        "series_id": "EXJPUS",
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_categories

        # Only required argument
        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Category.to_object_async", AsyncMock(return_value=fake_categories)) as mock_to_object:
                result = await async_api.get_series_categories("EXJPUS")
                mock_get.assert_called_once_with(
                    "/series/categories",
                    {"series_id": "EXJPUS"}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_categories

    @pytest.mark.asyncio
    async def test_get_series_observations(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "observation_start": "1776-07-04",
            "observation_end": "9999-12-31",
            "units": "lin",
            "output_type": 1,
            "file_type": "json",
            "order_by": "observation_date",
            "sort_order": "asc",
            "count": 84,
            "offset": 0,
            "limit": 100000,
            "observations": [
                {
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "date": "1929-01-01",
                    "value": "1065.9"
                },
                {
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "date": "1930-01-01",
                    "value": "975.5"
                },
                {
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "date": "1931-01-01",
                    "value": "912.1"
                },
                {
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "date": "1932-01-01",
                    "value": "794.1"
                }
            ]
        }
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        ob_start = datetime(1776, 7, 4)
        ob_end = datetime(9999, 12, 31)
        vintage_dates_list = [datetime(2020, 1, 1), datetime(2020, 2, 1)]

        # Test pandas
        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_dt_conv, \
            patch("fedfred.clients.FredHelpers.vintage_dates_type_conversion_async", AsyncMock(return_value="2020-01-01,2020-02-01")) as mock_vintage_conv, \
            patch("fedfred.clients.FredHelpers.to_pd_df_async", AsyncMock(return_value="pd_df")) as mock_pd:
            result = await async_api.get_series_observations(
                "GNPCA",
                dataframe_method="pandas",
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=10,
                offset=2,
                sort_order="desc",
                observation_start=ob_start,
                observation_end=ob_end,
                units="chg",
                frequency="m",
                aggregation_method="sum",
                output_type=2,
                vintage_dates=vintage_dates_list
            )
            assert mock_dt_conv.call_count == 4
            mock_vintage_conv.assert_called_once_with(vintage_dates_list)
            mock_get.assert_called_once_with(
                "/series/observations",
                {
                    "series_id": "GNPCA",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 10,
                    "offset": 2,
                    "sort_order": "desc",
                    "observation_start": "converted",
                    "observation_end": "converted",
                    "units": "chg",
                    "frequency": "m",
                    "aggregation_method": "sum",
                    "output_type": 2,
                    "vintage_dates": "2020-01-01,2020-02-01"
                }
            )
            mock_pd.assert_called_once_with(fake_response)
            assert result == "pd_df"

        # Test polars
        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.to_pl_df_async", AsyncMock(return_value="pl_df")) as mock_pl:
            result = await async_api.get_series_observations("GNPCA", dataframe_method="polars")
            mock_get.assert_called_once_with("/series/observations", {"series_id": "GNPCA"})
            mock_pl.assert_called_once_with(fake_response)
            assert result == "pl_df"

        # Test dask
        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.to_dd_df_async", AsyncMock(return_value="dd_df")) as mock_dd:
            result = await async_api.get_series_observations("GNPCA", dataframe_method="dask")
            mock_get.assert_called_once_with("/series/observations", {"series_id": "GNPCA"})
            mock_dd.assert_called_once_with(fake_response)
            assert result == "dd_df"

        # Test default (pandas)
        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.to_pd_df_async", AsyncMock(return_value="pd_df")) as mock_pd:
            result = await async_api.get_series_observations("GNPCA")
            mock_get.assert_called_once_with("/series/observations", {"series_id": "GNPCA"})
            mock_pd.assert_called_once_with(fake_response)
            assert result == "pd_df"

        # Test invalid dataframe_method
        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)):
            with pytest.raises(ValueError, match="dataframe_method must be a string, options are: 'pandas', 'polars', or 'dask'"):
                await async_api.get_series_observations("GNPCA", dataframe_method="invalid")

    @pytest.mark.asyncio
    async def test_get_series_release(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "releases": [
                {
                    "id": 21,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "H.6 Money Stock Measures",
                    "press_release": True,
                    "link": "http://www.federalreserve.gov/releases/h6/"
                }
            ]
        }
        fake_releases = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv:
                with patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
                    result = await async_api.get_series_release(
                        "GNPCA",
                        realtime_start=dt_start,
                        realtime_end=dt_end
                    )
                    assert mock_conv.call_count == 2
                    mock_get.assert_called_once_with(
                        "/series/release",
                        {
                            "series_id": "GNPCA",
                            "realtime_start": "converted",
                            "realtime_end": "converted"
                        }
                    )
                    mock_to_object.assert_called_once_with(fake_response)
                    assert result == fake_releases

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
                result = await async_api.get_series_release(
                    "GNPCA",
                    realtime_start="2021-01-01",
                    realtime_end="2021-12-31"
                )
                mock_get.assert_called_once_with(
                    "/series/release",
                    {
                        "series_id": "GNPCA",
                        "realtime_start": "2021-01-01",
                        "realtime_end": "2021-12-31"
                    }
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get:
            with patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
                result = await async_api.get_series_release("GNPCA")
                mock_get.assert_called_once_with(
                    "/series/release",
                    {"series_id": "GNPCA"}
                )
                mock_to_object.assert_called_once_with(fake_response)
                assert result == fake_releases

    @pytest.mark.asyncio
    async def test_get_series_search(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2017-08-01",
            "realtime_end": "2017-08-01",
            "order_by": "search_rank",
            "sort_order": "desc",
            "count": 32,
            "offset": 0,
            "limit": 1000,
            "seriess": [
                {
                "id": "MSIM2",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "Monetary Services Index: M2 (preferred)",
                "observation_start": "1967-01-01",
                "observation_end": "2013-12-01",
                "frequency": "Monthly",
                "frequency_short": "M",
                "units": "Billions of Dollars",
                "units_short": "Bil. of $",
                "seasonal_adjustment": "Seasonally Adjusted",
                "seasonal_adjustment_short": "SA",
                "last_updated": "2014-01-17 07:16:44-06",
                "popularity": 34,
                "group_popularity": 33,
                "notes": "The MSI measure the flow of monetary services received each period by households and firms from their holdings of monetary assets (levels of the indexes are sometimes referred to as Divisia monetary aggregates).\nPreferred benchmark rate equals 100 basis points plus the largest rate in the set of rates.\nAlternative benchmark rate equals the larger of the preferred benchmark rate and the Baa corporate bond yield.\nMore information about the new MSI can be found at\nhttp:\/\/research.stlouisfed.org\/msi\/index.html."
                },
                {
                "id": "MSIM1P",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "Monetary Services Index: M1 (preferred)",
                "observation_start": "1967-01-01",
                "observation_end": "2013-12-01",
                "frequency": "Monthly",
                "frequency_short": "M",
                "units": "Billions of Dollars",
                "units_short": "Bil. of $",
                "seasonal_adjustment": "Seasonally Adjusted",
                "seasonal_adjustment_short": "SA",
                "last_updated": "2014-01-17 07:16:45-06",
                "popularity": 26,
                "group_popularity": 26,
                "notes": "The MSI measure the flow of monetary services received each period by households and firms from their holdings of monetary assets (levels of the indexes are sometimes referred to as Divisia monetary aggregates)."
                }
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=",".join)) as mock_list_conv, \
            patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
            result = await async_api.get_series_search(
                "monetary services index",
                search_type="full_text",
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=10,
                offset=2,
                order_by="search_rank",
                sort_order="desc",
                filter_variable="frequency",
                filter_value="Monthly",
                tag_names=tag_list,
                exclude_tag_names=exclude_tag_list
            )
            assert mock_conv.call_count == 2
            assert mock_list_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/series/search",
                {
                    "search_text": "monetary services index",
                    "search_type": "full_text",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 10,
                    "offset": 2,
                    "order_by": "search_rank",
                    "sort_order": "desc",
                    "filter_variable": "frequency",
                    "filter_value": "Monthly",
                    "tag_names": "macro,gdp",
                    "exclude_tag_names": "foo,bar"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
            result = await async_api.get_series_search(
                "monetary services index",
                tag_names="macro",
                exclude_tag_names="foo",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31"
            )
            mock_get.assert_called_once_with(
                "/series/search",
                {
                    "search_text": "monetary services index",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "macro",
                    "exclude_tag_names": "foo"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
            result = await async_api.get_series_search("monetary services index")
            mock_get.assert_called_once_with(
                "/series/search",
                {"search_text": "monetary services index"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

    @pytest.mark.asyncio
    async def test_get_series_search_tags(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 18,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "academic data",
                    "group_id": "gen",
                    "notes": "Time series data created mainly by academia to address growing demand in understanding specific concerns in the economy that are not well modeled by ordinary statistical agencies.",
                    "created": "2012-08-29 10:22:19-05",
                    "popularity": 62,
                    "series_count": 25
                },
                {
                    "name": "anderson & jones",
                    "group_id": "src",
                    "notes": "Richard Anderson and Barry Jones",
                    "created": "2013-06-21 10:22:49-05",
                    "popularity": 46,
                    "series_count": 25
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=lambda x: "macro;gdp")) as mock_list_conv, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_series_search_tags(
                "monetary services index",
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=tag_list,
                tag_group_id="grp",
                tag_search_text="foo",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_list_conv.assert_called_once_with(tag_list)
            mock_get.assert_called_once_with(
                "/series/search/tags",
                {
                    "series_search_text": "monetary services index",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "tag_names": "macro;gdp",
                    "tag_group_id": "grp",
                    "tag_search_text": "foo",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_series_search_tags(
                "monetary services index",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                tag_names="macro"
            )
            mock_get.assert_called_once_with(
                "/series/search/tags",
                {
                    "series_search_text": "monetary services index",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "macro"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_series_search_tags("monetary services index")
            mock_get.assert_called_once_with(
                "/series/search/tags",
                {"series_search_text": "monetary services index"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

    @pytest.mark.asyncio
    async def test_get_series_search_related_tags(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 10,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "conventional",
                    "group_id": "gen",
                    "notes": "",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 63,
                    "series_count": 3
                },
                {
                    "name": "h15",
                    "group_id": "rls",
                    "notes": "H.15 Selected Interest Rates",
                    "created": "2012-08-16 15:21:17-05",
                    "popularity": 84,
                    "series_count": 3
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=";".join)) as mock_list_conv, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_series_search_related_tags(
                "mortgage rate",
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=tag_list,
                exclude_tag_names=exclude_tag_list,
                tag_group_id="grp",
                tag_search_text="foo",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            assert mock_list_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/series/search/related_tags",
                {
                    "series_search_text": "mortgage rate",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "tag_names": "macro;gdp",
                    "exclude_tag_names": "foo;bar",
                    "tag_group_id": "grp",
                    "tag_search_text": "foo",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_series_search_related_tags(
                "mortgage rate",
                tag_names="macro",
                exclude_tag_names="foo",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31"
            )
            mock_get.assert_called_once_with(
                "/series/search/related_tags",
                {
                    "series_search_text": "mortgage rate",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "macro",
                    "exclude_tag_names": "foo"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_series_search_related_tags("mortgage rate", tag_names="")
            mock_get.assert_called_once_with(
                "/series/search/related_tags",
                {"series_search_text": "mortgage rate", "tag_names": ""}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

    @pytest.mark.asyncio
    async def test_get_series_tags(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 8,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "nation",
                    "group_id": "geot",
                    "notes": "Country Level",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 100,
                    "series_count": 105200
                },
                {
                    "name": "nsa",
                    "group_id": "seas",
                    "notes": "Not seasonally adjusted",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 96,
                    "series_count": 100468
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_series_tags(
                "GNPCA",
                realtime_start=dt_start,
                realtime_end=dt_end,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/series/tags",
                {
                    "series_id": "GNPCA",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_series_tags(
                "GNPCA",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                order_by="name"
            )
            mock_get.assert_called_once_with(
                "/series/tags",
                {
                    "series_id": "GNPCA",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "order_by": "name"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_series_tags(
                "GNPCA",
                sort_order="asc"
            )
            mock_get.assert_called_once_with(
                "/series/tags",
                {
                    "series_id": "GNPCA",
                    "sort_order": "asc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_series_tags("GNPCA")
            mock_get.assert_called_once_with(
                "/series/tags",
                {"series_id": "GNPCA"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

    @pytest.mark.asyncio
    async def test_get_series_updates(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "filter_variable": "geography",
            "filter_value": "all",
            "order_by": "last_updated",
            "sort_order": "desc",
            "count": 143535,
            "offset": 0,
            "limit": 100,
            "seriess": [
                {
                    "id": "PPIITM",
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "title": "Producer Price Index: Intermediate Materials: Supplies & Components",
                    "observation_start": "1947-04-01",
                    "observation_end": "2013-07-01",
                    "frequency": "Monthly",
                    "frequency_short": "M",
                    "units": "Index 1982=100",
                    "units_short": "Index 1982=100",
                    "seasonal_adjustment": "Seasonally Adjusted",
                    "seasonal_adjustment_short": "SA",
                    "last_updated": "2013-08-14 08:36:05-05",
                    "popularity": 52
                },
                {
                    "id": "PPILFE",
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "title": "Producer Price Index: Finished Goods Less Food & Energy",
                    "observation_start": "1974-01-01",
                    "observation_end": "2013-07-01",
                    "frequency": "Monthly",
                    "frequency_short": "M",
                    "units": "Index 1982=100",
                    "units_short": "Index 1982=100",
                    "seasonal_adjustment": "Seasonally Adjusted",
                    "seasonal_adjustment_short": "SA",
                    "last_updated": "2013-08-14 08:36:05-05",
                    "popularity": 51
                }
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        dt_hhmm_start = datetime(2020, 1, 1, 8, 30)
        dt_hhmm_end = datetime(2020, 1, 1, 17, 45)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_dt_conv, \
            patch("fedfred.clients.FredHelpers.datetime_hh_mm_conversion_async", AsyncMock(side_effect=lambda x: "08:30" if x == dt_hhmm_start else "17:45")) as mock_hhmm_conv, \
            patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
            result = await async_api.get_series_updates(
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=50,
                offset=10,
                filter_value="foo",
                start_time=dt_hhmm_start,
                end_time=dt_hhmm_end
            )
            assert mock_dt_conv.call_count == 2
            assert mock_hhmm_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/series/updates",
                {
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 50,
                    "offset": 10,
                    "filter_value": "foo",
                    "start_time": "08:30",
                    "end_time": "17:45"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
            result = await async_api.get_series_updates(
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                limit=10,
                offset=2,
                filter_value="bar",
                start_time="09:00",
                end_time="18:00"
            )
            mock_get.assert_called_once_with(
                "/series/updates",
                {
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "limit": 10,
                    "offset": 2,
                    "filter_value": "bar",
                    "start_time": "09:00",
                    "end_time": "18:00"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
            result = await async_api.get_series_updates()
            mock_get.assert_called_once_with("/series/updates", {})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
            result = await async_api.get_series_updates(limit=5, offset=1)
            mock_get.assert_called_once_with(
                "/series/updates",
                {"limit": 5, "offset": 1}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

    @pytest.mark.asyncio
    async def test_get_series_vintage_dates(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "1776-07-04",
            "realtime_end": "9999-12-31",
            "order_by": "vintage_date",
            "sort_order": "asc",
            "count": 162,
            "offset": 0,
            "limit": 10000,
            "vintage_dates": [
                "1958-12-21",
                "1959-02-19",
                "1959-07-19",
                "1960-02-16",
                "1960-07-22",
                "1961-02-19",
            ]
        }
        fake_vintage_dates = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.VintageDate.to_object_async", AsyncMock(return_value=fake_vintage_dates)) as mock_to_object:
            result = await async_api.get_series_vintagedates(
                "GNPCA",
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=50,
                offset=10,
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/series/vintagedates",
                {
                    "series_id": "GNPCA",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 50,
                    "offset": 10,
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_vintage_dates

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.VintageDate.to_object_async", AsyncMock(return_value=fake_vintage_dates)) as mock_to_object:
            result = await async_api.get_series_vintagedates(
                "GNPCA",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                limit=10,
                offset=2
            )
            mock_get.assert_called_once_with(
                "/series/vintagedates",
                {
                    "series_id": "GNPCA",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "limit": 10,
                    "offset": 2
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_vintage_dates

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.VintageDate.to_object_async", AsyncMock(return_value=fake_vintage_dates)) as mock_to_object:
            result = await async_api.get_series_vintagedates("GNPCA")
            mock_get.assert_called_once_with(
                "/series/vintagedates",
                {"series_id": "GNPCA"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_vintage_dates

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.VintageDate.to_object_async", AsyncMock(return_value=fake_vintage_dates)) as mock_to_object:
            result = await async_api.get_series_vintagedates("GNPCA", sort_order="asc")
            mock_get.assert_called_once_with(
                "/series/vintagedates",
                {"series_id": "GNPCA", "sort_order": "asc"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_vintage_dates

        with pytest.raises(ValueError):
            await async_api.get_series_vintagedates("")

        with pytest.raises(ValueError):
            await async_api.get_series_vintagedates(123)

    ## Sources
    @pytest.mark.asyncio
    async def test_get_sources(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "source_id",
            "sort_order": "asc",
            "count": 58,
            "offset": 0,
            "limit": 1000,
            "sources": [
                {
                    "id": 1,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "Board of Governors of the Federal Reserve System",
                    "link": "http://www.federalreserve.gov/"
                },
                {
                    "id": 3,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "Federal Reserve Bank of Philadelphia",
                    "link": "http://www.philadelphiafed.org/"
                }
            ]
        }
        fake_sources = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.Source.to_object_async", AsyncMock(return_value=fake_sources)) as mock_to_object:
            result = await async_api.get_sources(
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=50,
                offset=10,
                order_by="name",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/sources",
                {
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 50,
                    "offset": 10,
                    "order_by": "name",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_sources

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Source.to_object_async", AsyncMock(return_value=fake_sources)) as mock_to_object:
            result = await async_api.get_sources(
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                limit=10,
                offset=2
            )
            mock_get.assert_called_once_with(
                "/sources",
                {
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "limit": 10,
                    "offset": 2
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_sources

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Source.to_object_async", AsyncMock(return_value=fake_sources)) as mock_to_object:
            result = await async_api.get_sources()
            mock_get.assert_called_once_with("/sources", {})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_sources

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Source.to_object_async", AsyncMock(return_value=fake_sources)) as mock_to_object:
            result = await async_api.get_sources(order_by="source_id", sort_order="asc")
            mock_get.assert_called_once_with(
                "/sources",
                {"order_by": "source_id", "sort_order": "asc"}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_sources

    @pytest.mark.asyncio
    async def test_get_source(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "sources": [
                {
                    "id": 1,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "Board of Governors of the Federal Reserve System",
                    "link": "http://www.federalreserve.gov/"
                }
            ]
        }
        fake_source = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.Source.to_object_async", AsyncMock(return_value=fake_source)) as mock_to_object:
            result = await async_api.get_source(
                1,
                realtime_start=dt_start,
                realtime_end=dt_end
            )
            assert mock_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/source",
                {
                    "source_id": 1,
                    "realtime_start": "converted",
                    "realtime_end": "converted"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_source

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Source.to_object_async", AsyncMock(return_value=fake_source)) as mock_to_object:
            result = await async_api.get_source(
                1,
                realtime_start="2021-01-01",
                realtime_end="2021-12-31"
            )
            mock_get.assert_called_once_with(
                "/source",
                {
                    "source_id": 1,
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_source

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Source.to_object_async", AsyncMock(return_value=fake_source)) as mock_to_object:
            result = await async_api.get_source(1)
            mock_get.assert_called_once_with(
                "/source",
                {"source_id": 1}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_source

    @pytest.mark.asyncio
    async def test_get_source_releases(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "release_id",
            "sort_order": "asc",
            "count": 26,
            "offset": 0,
            "limit": 1000,
            "releases": [
                {
                    "id": 13,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "G.17 Industrial Production and Capacity Utilization",
                    "press_release": True,
                    "link": "http://www.federalreserve.gov/releases/g17/"
                },
                {
                    "id": 14,
                    "realtime_start": "2013-08-14",
                    "realtime_end": "2013-08-14",
                    "name": "G.19 Consumer Credit",
                    "press_release": True,
                    "link": "http://www.federalreserve.gov/releases/g19/"
                }
            ]
        }
        fake_releases = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
            result = await async_api.get_source_releases(
                1,
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=5,
                offset=2,
                order_by="release_id",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_get.assert_called_once_with(
                "/source/releases",
                {
                    "source_id": 1,
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "release_id",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_releases

        # All arguments as string
        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
            result = await async_api.get_source_releases(
                1,
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                limit=10,
                offset=3,
                order_by="name",
                sort_order="asc"
            )
            mock_get.assert_called_once_with(
                "/source/releases",
                {
                    "source_id": 1,
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "limit": 10,
                    "offset": 3,
                    "order_by": "name",
                    "sort_order": "asc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_releases

        # Only required argument
        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
            result = await async_api.get_source_releases(1)
            mock_get.assert_called_once_with(
                "/source/releases",
                {"source_id": 1}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_releases

        # Only some optional arguments
        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Release.to_object_async", AsyncMock(return_value=fake_releases)) as mock_to_object:
            result = await async_api.get_source_releases(
                1,
                limit=7,
                offset=4
            )
            mock_get.assert_called_once_with(
                "/source/releases",
                {"source_id": 1, "limit": 7, "offset": 4}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_releases

    ## Tags
    @pytest.mark.asyncio
    async def test_get_tags(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 4794,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "nation",
                    "group_id": "geot",
                    "notes": "Country Level",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 100,
                    "series_count": 105200
                },
                {
                    "name": "nsa",
                    "group_id": "seas",
                    "notes": "Not seasonally adjusted",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 96,
                    "series_count": 100468
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=";".join)) as mock_list_conv, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_tags(
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=["foo", "bar"],
                tag_group_id="grp",
                search_text="baz",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_list_conv.assert_called_once_with(["foo", "bar"])
            mock_get.assert_called_once_with(
                "/tags",
                {
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "tag_names": "foo;bar",
                    "tag_group_id": "grp",
                    "search_text": "baz",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=lambda x: "macro;gdp")) as mock_list_conv, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_tags(
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=tag_list,
                tag_group_id="grp",
                search_text="baz",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            mock_list_conv.assert_called_once_with(tag_list)
            mock_get.assert_called_once_with(
                "/tags",
                {
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "tag_names": "macro;gdp",
                    "tag_group_id": "grp",
                    "search_text": "baz",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_tags(
                realtime_start="2021-01-01",
                realtime_end="2021-12-31",
                tag_names="foo",
                tag_group_id="grp",
                search_text="baz",
                limit=10,
                offset=3,
                order_by="popularity",
                sort_order="asc"
            )
            mock_get.assert_called_once_with(
                "/tags",
                {
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "foo",
                    "tag_group_id": "grp",
                    "search_text": "baz",
                    "limit": 10,
                    "offset": 3,
                    "order_by": "popularity",
                    "sort_order": "asc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_tags()
            mock_get.assert_called_once_with("/tags", {})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_tags(
                tag_names="foo",
                limit=7,
                offset=4
            )
            mock_get.assert_called_once_with(
                "/tags",
                {"tag_names": "foo", "limit": 7, "offset": 4}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", side_effect=ValueError("API error")):
            with pytest.raises(ValueError):
                await async_api.get_tags(tag_names="foo")

    @pytest.mark.asyncio
    async def test_get_related_tags(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "order_by": "series_count",
            "sort_order": "desc",
            "count": 13,
            "offset": 0,
            "limit": 1000,
            "tags": [
                {
                    "name": "nation",
                    "group_id": "geot",
                    "notes": "Country Level",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 100,
                    "series_count": 12
                },
                {
                    "name": "usa",
                    "group_id": "geo",
                    "notes": "United States of America",
                    "created": "2012-02-27 10:18:19-06",
                    "popularity": 100,
                    "series_count": 12
                }
            ]
        }
        fake_tags = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=";".join)) as mock_list_conv, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_related_tags(
                realtime_start=dt_start,
                realtime_end=dt_end,
                tag_names=tag_list,
                exclude_tag_names=exclude_tag_list,
                tag_group_id="grp",
                search_text="foo",
                limit=5,
                offset=2,
                order_by="series_count",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            assert mock_list_conv.call_count == 2
            mock_list_conv.assert_any_call(tag_list)
            mock_list_conv.assert_any_call(exclude_tag_list)
            mock_get.assert_called_once_with(
                "/related_tags",
                {
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "tag_names": "macro;gdp",
                    "exclude_tag_names": "foo;bar",
                    "tag_group_id": "grp",
                    "search_text": "foo",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_count",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_related_tags(
                tag_names="macro",
                exclude_tag_names="foo",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31"
            )
            mock_get.assert_called_once_with(
                "/related_tags",
                {
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31",
                    "tag_names": "macro",
                    "exclude_tag_names": "foo"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_related_tags()
            mock_get.assert_called_once_with("/related_tags", {})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Tag.to_object_async", AsyncMock(return_value=fake_tags)) as mock_to_object:
            result = await async_api.get_related_tags(
                tag_names="foo",
                limit=7,
                offset=4
            )
            mock_get.assert_called_once_with(
                "/related_tags",
                {"tag_names": "foo", "limit": 7, "offset": 4}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_tags

        with patch.object(async_api, "_AsyncAPI__fred_get_request", side_effect=ValueError("API error")):
            with pytest.raises(ValueError):
                await async_api.get_related_tags(tag_names="foo")

    @pytest.mark.asyncio
    async def test_get_tags_series(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = parent.Async
        fake_response = {
            "realtime_start": "2017-08-01",
            "realtime_end": "2017-08-01",
            "order_by": "series_id",
            "sort_order": "asc",
            "count": 18,
            "offset": 0,
            "limit": 1000,
            "seriess": [
                {
                "id": "CPGDFD02SIA657N",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "Consumer Price Index: Total Food Excluding Restaurants for Slovenia\u00a9",
                "observation_start": "1996-01-01",
                "observation_end": "2016-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Growth Rate Previous Period",
                "units_short": "Growth Rate Previous Period",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2017-04-20 00:48:35-05",
                "popularity": 0,
                "group_popularity": 0,
                "notes": "OECD descriptor ID: CPGDFD02\nOECD unit ID: GP\nOECD country ID: SVN\n\nAll OECD data should be cited as follows: OECD, \"Main Economic Indicators - complete database\", Main Economic Indicators (database),http:\/\/dx.doi.org\/10.1787\/data-00052-en (Accessed on date)\nCopyright, 2016, OECD. Reprinted with permission."
                },
                {
                "id": "CPGDFD02SIA659N",
                "realtime_start": "2017-08-01",
                "realtime_end": "2017-08-01",
                "title": "Consumer Price Index: Total Food Excluding Restaurants for Slovenia\u00a9",
                "observation_start": "1996-01-01",
                "observation_end": "2016-01-01",
                "frequency": "Annual",
                "frequency_short": "A",
                "units": "Growth Rate Same Period Previous Year",
                "units_short": "Growth Rate Same Period Previous Yr.",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "seasonal_adjustment_short": "NSA",
                "last_updated": "2017-04-20 00:48:35-05",
                "popularity": 0,
                "group_popularity": 0,
                "notes": "OECD descriptor ID: CPGDFD02\nOECD unit ID: GY\nOECD country ID: SVN\n\nAll OECD data should be cited as follows: OECD, \"Main Economic Indicators - complete database\", Main Economic Indicators (database),http:\/\/dx.doi.org\/10.1787\/data-00052-en (Accessed on date)\nCopyright, 2016, OECD. Reprinted with permission."
                }
            ]
        }
        fake_series = [MagicMock()]
        dt_start = datetime(2020, 1, 1)
        dt_end = datetime(2020, 12, 31)
        tag_list = ["macro", "gdp"]
        exclude_tag_list = ["foo", "bar"]

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.FredHelpers.datetime_conversion_async", AsyncMock(side_effect=lambda x: "converted")) as mock_conv, \
            patch("fedfred.clients.FredHelpers.liststring_conversion_async", AsyncMock(side_effect=";".join)) as mock_list_conv, \
            patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
            result = await async_api.get_tags_series(
                tag_names=tag_list,
                exclude_tag_names=exclude_tag_list,
                realtime_start=dt_start,
                realtime_end=dt_end,
                limit=5,
                offset=2,
                order_by="series_id",
                sort_order="desc"
            )
            assert mock_conv.call_count == 2
            assert mock_list_conv.call_count == 2
            mock_list_conv.assert_any_call(tag_list)
            mock_list_conv.assert_any_call(exclude_tag_list)
            mock_get.assert_called_once_with(
                "/tags/series",
                {
                    "tag_names": "macro;gdp",
                    "exclude_tag_names": "foo;bar",
                    "realtime_start": "converted",
                    "realtime_end": "converted",
                    "limit": 5,
                    "offset": 2,
                    "order_by": "series_id",
                    "sort_order": "desc"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
            result = await async_api.get_tags_series(
                tag_names="macro",
                exclude_tag_names="foo",
                realtime_start="2021-01-01",
                realtime_end="2021-12-31"
            )
            mock_get.assert_called_once_with(
                "/tags/series",
                {
                    "tag_names": "macro",
                    "exclude_tag_names": "foo",
                    "realtime_start": "2021-01-01",
                    "realtime_end": "2021-12-31"
                }
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
            result = await async_api.get_tags_series()
            mock_get.assert_called_once_with("/tags/series", {})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.Series.to_object_async", AsyncMock(return_value=fake_series)) as mock_to_object:
            result = await async_api.get_tags_series(
                tag_names="foo",
                limit=7,
                offset=4
            )
            mock_get.assert_called_once_with(
                "/tags/series",
                {"tag_names": "foo", "limit": 7, "offset": 4}
            )
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series

        with patch.object(async_api, "_AsyncAPI__fred_get_request", side_effect=ValueError("API error")):
            with pytest.raises(ValueError):
                await async_api.get_tags_series(tag_names="foo")

class TestAsyncMapsAPI:
    # Dunder methods
    def test_init(self):
        fred_api = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = fred_api.Async
        async_maps_api = async_api.Maps
        assert async_maps_api._parent == async_api
        assert async_maps_api._grandparent == fred_api
        assert async_maps_api.cache_mode == async_api.cache_mode
        assert async_maps_api.cache == async_api.cache
        assert async_maps_api.base_url == fred_api.Maps.base_url

    def test_repr(self):
        fred_api = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = fred_api.Async
        async_maps_api = async_api.Maps
        expected_repr = f"{repr(async_api)}.AsyncMapsAPI(base_url={async_maps_api.base_url})"
        assert repr(async_maps_api) == expected_repr

    def test_str(self):
        fred_api = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_api = fred_api.Async
        async_maps_api = async_api.Maps

        expected = (
            f"{str(async_api)}"
            f"      AsyncMapsAPI Instance:\n"
            f"          Base URL: {async_maps_api.base_url}\n"
        )
        assert str(async_maps_api) == expected

    def test_eq(self):
        fred_api1 = FredAPI("testkey", cache_mode=True, cache_size=10)
        fred_api2 = FredAPI("testkey", cache_mode=True, cache_size=10)
        fred_api3 = FredAPI("otherkey", cache_mode=True, cache_size=10)
        fred_api4 = FredAPI("testkey", cache_mode=False, cache_size=10)
        fred_api5 = FredAPI("testkey", cache_mode=True, cache_size=5)

        async_maps1 = fred_api1.Async.Maps
        async_maps2 = fred_api2.Async.Maps
        async_maps3 = fred_api3.Async.Maps
        async_maps4 = fred_api4.Async.Maps
        async_maps5 = fred_api5.Async.Maps

        assert async_maps1 == async_maps1
        assert async_maps1 == async_maps2
        assert async_maps1 != async_maps3
        assert async_maps1 != async_maps4
        assert async_maps1 != async_maps5
        assert (async_maps1 == 42) is False
        assert (async_maps1 == "not a MapsAPI") is False

    def test_hash(self):
        fred_api1 = FredAPI("testkey", cache_mode=True, cache_size=10)
        fred_api2 = FredAPI("testkey", cache_mode=True, cache_size=10)
        fred_api3 = FredAPI("otherkey", cache_mode=True, cache_size=10)
        fred_api4 = FredAPI("testkey", cache_mode=False, cache_size=10)
        fred_api5 = FredAPI("testkey", cache_mode=True, cache_size=5)

        async_maps1 = fred_api1.Async.Maps
        async_maps2 = fred_api2.Async.Maps
        async_maps3 = fred_api3.Async.Maps
        async_maps4 = fred_api4.Async.Maps
        async_maps5 = fred_api5.Async.Maps

        expected_hash = hash((fred_api1.api_key, fred_api1.cache_mode, fred_api1.cache_size))

        assert hash(async_maps1) == expected_hash
        assert hash(async_maps1) == hash(async_maps2)
        assert hash(async_maps1) != hash(async_maps3)
        assert hash(async_maps1) != hash(async_maps4)
        assert hash(async_maps1) != hash(async_maps5)
        assert isinstance(hash(async_maps1), int)

    def test_del(self):
        fred_api = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_maps_api = fred_api.Async.Maps
        async_maps_api.cache["foo"] = "bar"
        async_maps_api.cache["baz"] = "qux"
        assert len(async_maps_api.cache) == 2
        async_maps_api.__del__()
        assert len(async_maps_api.cache) == 0
        del async_maps_api.cache
        async_maps_api.__del__()

    def test_getitem(self):
        fred_api = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_maps_api = fred_api.Async.Maps
        async_maps_api["foo"] = "bar"
        async_maps_api["baz"] = "qux"
        assert async_maps_api["foo"] == "bar"
        assert async_maps_api["baz"] == "qux"
        with pytest.raises(AttributeError):
            _ = async_maps_api["quux"]

    def test_len(self):
        fred_api = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_maps_api = fred_api.Async.Maps
        async_maps_api.cache["foo"] = "bar"
        async_maps_api.cache["baz"] = "qux"
        assert len(async_maps_api) == 2
        async_maps_api.cache.clear()
        assert len(async_maps_api) == 0

    def test_contains(self):
        fred_api = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_maps_api = fred_api.Async.Maps
        async_maps_api.cache["foo"] = "bar"
        async_maps_api.cache["baz"] = "qux"
        assert "foo" in async_maps_api
        assert "baz" in async_maps_api
        assert "quux" not in async_maps_api

    def test_setitem(self):
        fred_api = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_maps_api = fred_api.Async.Maps
        async_maps_api["foo"] = "bar"
        assert async_maps_api["foo"] == "bar"
        async_maps_api["baz"] = "qux"
        assert async_maps_api["baz"] == "qux"

    def test_delitem(self):
        fred_api = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_maps_api = fred_api.Async.Maps
        async_maps_api["foo"] = "bar"
        async_maps_api["baz"] = "qux"
        assert "foo" in async_maps_api
        assert "baz" in async_maps_api
        del async_maps_api["foo"]
        assert "foo" not in async_maps_api
        assert "baz" in async_maps_api

        with pytest.raises(AttributeError, match="'notfound' not found in cache."):
            del async_maps_api["notfound"]

    def test_call(self):
        fred = FredAPI("testapikey1234", cache_mode=True, cache_size=5)
        async_maps = fred.Async.Maps
        async_maps.cache["foo"] = "bar"
        async_maps.cache["baz"] = "qux"
        summary = async_maps()

        assert isinstance(summary, str)
        assert "FredAPI Instance" in summary
        assert "MapsAPI Instance" in summary
        assert "AsyncMapsAPI Instance" in summary
        assert f"Base URL: {async_maps.base_url}" in summary
        assert "Cache Mode: Enabled" in summary
        assert "Cache Size: 2 items" in summary
        assert "API Key: ****1234" in summary

        fred2 = FredAPI("testapikey1234", cache_mode=False, cache_size=1)
        fred2.api_key = ""
        async_maps2 = fred2.Async.Maps
        summary2 = async_maps2()

        assert "API Key: Not Set" in summary2
        assert "Cache Mode: Disabled" in summary2

    # Private Methods
    @pytest.mark.asyncio
    async def test_update_semaphore(self, monkeypatch):
        fred_api = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_maps_api = fred_api.Async.Maps

        # Patch time.time to control "now"
        fake_now = 1_000_000.0
        monkeypatch.setattr("time.time", lambda: fake_now)

        # Case 1: No requests in the last minute
        fred_api.request_times.clear()
        fred_api.max_requests_per_minute = 10
        requests_left, time_left = await async_maps_api._AsyncMapsAPI__update_semaphore()
        assert requests_left == 10
        assert time_left == 60
        assert isinstance(fred_api.semaphore, asyncio.Semaphore)
        assert fred_api.semaphore._value == 1

        # Case 2: Some requests older than 60s should be purged
        fred_api.request_times.clear()
        fred_api.request_times.extend([fake_now - 70, fake_now - 61, fake_now - 10, fake_now - 5])
        fred_api.max_requests_per_minute = 10
        requests_left, time_left = await async_maps_api._AsyncMapsAPI__update_semaphore()
        assert list(fred_api.request_times) == [fake_now - 10, fake_now - 5]
        assert requests_left == 8
        assert time_left == 50
        assert fred_api.semaphore._value == 1

        # Case 3: All requests within last minute, requests_left < max_requests_per_minute
        fred_api.request_times.clear()
        fred_api.request_times.extend([fake_now - 10, fake_now - 5, fake_now - 1])
        fred_api.max_requests_per_minute = 5
        requests_left, time_left = await async_maps_api._AsyncMapsAPI__update_semaphore()
        assert requests_left == 2
        assert time_left == 50
        assert fred_api.semaphore._value == 1

        # Case 4: All requests used up (requests_left == 0)
        fred_api.request_times.clear()
        fred_api.request_times.extend([fake_now - 10, fake_now - 5, fake_now - 1, fake_now - 0.5, fake_now - 0.1])
        fred_api.max_requests_per_minute = 5
        requests_left, time_left = await async_maps_api._AsyncMapsAPI__update_semaphore()
        assert requests_left == 0
        assert time_left == 50
        assert fred_api.semaphore._value == 1

        # Case 5: request_times is empty (should not error)
        fred_api.request_times.clear()
        fred_api.max_requests_per_minute = 15
        requests_left, time_left = await async_maps_api._AsyncMapsAPI__update_semaphore()
        assert requests_left == 15
        assert time_left == 60
        assert fred_api.semaphore._value == 1

    @pytest.mark.parametrize(
        "request_offsets,requests_left,time_left,expected_sleep",
        [
            ([-70], 1, 60, 60),        # Only one old request, requests_left > 0, sleep 60/1=60
            ([-10], 2, 50, 25),        # Two recent requests, requests_left > 0, sleep 50/2=25
            ([-10, -5], 0, 40, 60),    # All requests used, requests_left == 0, sleep 60
            ([-10, -5, -1], 0, 30, 60) # All requests used, requests_left == 0, sleep 60
        ]
    )
    @pytest.mark.asyncio
    async def test_rate_limited(self, request_offsets, requests_left, time_left, expected_sleep, monkeypatch):
        fred_api = FredAPI("testkey", cache_mode=True, cache_size=10)
        async_maps_api = fred_api.Async.Maps

        fake_now = 1_000_000.0
        monkeypatch.setattr("time.time", lambda: fake_now)
        fred_api.request_times.clear()
        for offset in request_offsets:
            fred_api.request_times.append(fake_now + offset)
        fred_api.semaphore = asyncio.Semaphore(1)
        fred_api.lock = asyncio.Lock()

        async def fake_update_semaphore():
            return requests_left, time_left

        monkeypatch.setattr(async_maps_api, "_AsyncMapsAPI__update_semaphore", fake_update_semaphore)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await async_maps_api._AsyncMapsAPI__rate_limited()
            if requests_left > 0:
                mock_sleep.assert_awaited_once_with(expected_sleep)
            else:
                mock_sleep.assert_awaited_once_with(60)
            assert len(fred_api.request_times) >= 1
            assert fred_api.request_times[-1] == fake_now

    @pytest.mark.parametrize(
        "cache_mode,data,should_validate",
        [
            (False, {"foo": 1}, True),   # cache off, with data
            (True, {"foo": 1}, True),    # cache on, with data
            (False, None, False),        # cache off, no data
            (True, None, False),         # cache on, no data
        ]
    )
    @pytest.mark.asyncio
    async def test_fred_get_request(self, cache_mode, data, should_validate, monkeypatch):
        parent = FredAPI("testkey", cache_mode=cache_mode, cache_size=10)
        async_maps_api = parent.Async.Maps
        fake_json = {"bar": "baz"}

        # Patch geo_parameter_validation_async
        with patch("fedfred.helpers.FredHelpers.geo_parameter_validation_async", new_callable=AsyncMock) as mock_validate:
            # Patch rate limiting
            monkeypatch.setattr(async_maps_api, "_AsyncMapsAPI__rate_limited", AsyncMock())

            # Patch httpx.AsyncClient to return a dummy response
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = fake_json

            class DummyAsyncClient:
                async def __aenter__(self):
                    return self
                async def __aexit__(self, exc_type, exc, tb):
                    pass
                async def get(self, url, params=None, timeout=None):
                    return mock_response

            # Patch async_cached to just call the function
            def fake_async_cached(cache):
                def decorator(func):
                    async def wrapper(*args, **kwargs):
                        return await func(*args, **kwargs)
                    return wrapper
                return decorator

            with patch("httpx.AsyncClient", DummyAsyncClient), \
                patch("fedfred.clients.async_cached", fake_async_cached):
                result = await async_maps_api._AsyncMapsAPI__fred_get_request("/test", data=data)
                assert result == fake_json
                if should_validate:
                    mock_validate.assert_awaited_once_with(data)
                else:
                    mock_validate.assert_not_awaited()

        # HTTPStatusError branch
        class HTTPStatusErrorAsyncClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
            async def get(self, url, params=None, timeout=None):
                raise httpx.HTTPStatusError("fail", request=MagicMock(), response=MagicMock())

        with patch("fedfred.helpers.FredHelpers.geo_parameter_validation_async", new_callable=AsyncMock), \
            patch("httpx.AsyncClient", HTTPStatusErrorAsyncClient), \
            patch("fedfred.clients.async_cached", fake_async_cached):
            monkeypatch.setattr(async_maps_api, "_AsyncMapsAPI__rate_limited", AsyncMock())
            with pytest.raises(tenacity.RetryError) as excinfo:
                await async_maps_api._AsyncMapsAPI__fred_get_request("/test", data=data)
            # The root cause is a ValueError, check its message:
            assert "HTTP Error occurred:" in str(excinfo.value.last_attempt.exception())

        # RequestError branch
        class RequestErrorAsyncClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
            async def get(self, url, params=None, timeout=None):
                raise httpx.RequestError("fail", request=MagicMock())

        with patch("fedfred.helpers.FredHelpers.geo_parameter_validation_async", new_callable=AsyncMock), \
            patch("httpx.AsyncClient", RequestErrorAsyncClient), \
            patch("fedfred.clients.async_cached", fake_async_cached):
            monkeypatch.setattr(async_maps_api, "_AsyncMapsAPI__rate_limited", AsyncMock())
            with patch("fedfred.helpers.FredHelpers.geo_parameter_validation_async", new_callable=AsyncMock), \
                patch("httpx.AsyncClient", RequestErrorAsyncClient), \
                patch("fedfred.clients.async_cached", fake_async_cached):
                monkeypatch.setattr(async_maps_api, "_AsyncMapsAPI__rate_limited", AsyncMock())
                with pytest.raises(tenacity.RetryError) as excinfo:
                    await async_maps_api._AsyncMapsAPI__fred_get_request("/test", data=data)
                assert "Request Error occurred:" in str(excinfo.value.last_attempt.exception())

    @pytest.mark.asyncio
    async def test_get_shape_files(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Async.Maps

        fake_response = {
            "features": [{"type": "Feature", "properties": {"name": "foo"}, "geometry": {}}],
        }

        # Test: geodataframe_method = 'geopandas'
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)):
            with patch("geopandas.GeoDataFrame.from_features", return_value="gdf") as mock_gdf:
                result = await maps_api.get_shape_files("state", geodataframe_method="geopandas")
                mock_gdf.assert_called_once_with(fake_response["features"])
                assert result == "gdf"

        # Test: geodataframe_method = 'dask'
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)):
            with patch("geopandas.GeoDataFrame.from_features", return_value="gdf") as mock_gdf:
                with patch("dask_geopandas.from_geopandas", return_value="dd_gdf") as mock_dd:
                    result = await maps_api.get_shape_files("state", geodataframe_method="dask")
                    mock_gdf.assert_called_once_with(fake_response["features"])
                    mock_dd.assert_called_once_with("gdf", npartitions=1)
                    assert result == "dd_gdf"

        # Test: geodataframe_method = 'polars'
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)):
            with patch("geopandas.GeoDataFrame.from_features", return_value="gdf") as mock_gdf:
                with patch("polars_st.from_geopandas", return_value="pl_gdf") as mock_pl:
                    result = await maps_api.get_shape_files("state", geodataframe_method="polars")
                    mock_gdf.assert_called_once_with(fake_response["features"])
                    mock_pl.assert_called_once_with("gdf")
                    assert result == "pl_gdf"

        # Test: ImportError for dask
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)):
            with patch("geopandas.GeoDataFrame.from_features", return_value="gdf"):
                import builtins
                orig_import = builtins.__import__
                def fake_import(name, *args, **kwargs):
                    if name == "dask_geopandas":
                        raise ImportError("Dask GeoPandas is not installed")
                    return orig_import(name, *args, **kwargs)
                with patch("builtins.__import__", side_effect=fake_import):
                    with pytest.raises(ImportError, match="Dask GeoPandas is not installed"):
                        await maps_api.get_shape_files("state", geodataframe_method="dask")

        # Test: ImportError for polars
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)):
            with patch("geopandas.GeoDataFrame.from_features", return_value="gdf"):
                import builtins
                orig_import = builtins.__import__
                def fake_import(name, *args, **kwargs):
                    if name == "polars_st":
                        raise ImportError("Polars is not installed")
                    return orig_import(name, *args, **kwargs)
                with patch("builtins.__import__", side_effect=fake_import):
                    with pytest.raises(ImportError, match="Polars is not installed"):
                        await maps_api.get_shape_files("state", geodataframe_method="polars")

        # Test: ValueError for invalid geodataframe_method
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)):
            with patch("geopandas.GeoDataFrame.from_features", return_value="gdf"):
                with pytest.raises(ValueError, match="geodataframe_method must be 'geopandas', 'dask', or 'polars'"):
                    await maps_api.get_shape_files("state", geodataframe_method="invalid")

        # Test: ValueError for invalid shape argument (empty string)
        with pytest.raises(ValueError, match="shape must be a non-empty string"):
            await maps_api.get_shape_files("", geodataframe_method="geopandas")

        # Test: ValueError for invalid shape argument (not a string)
        with pytest.raises(ValueError, match="shape must be a non-empty string"):
            await maps_api.get_shape_files(None, geodataframe_method="geopandas")

    @pytest.mark.asyncio
    async def test_get_series_group(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Async.Maps

        fake_response = {
            "series_group": {
                "title" : "All Employees: Total Private",
                "region_type" : "state",
                "series_group" : "1223",
                "season" : "NSA",
                "units" : "Thousands of Persons",
                "frequency" : "Annual",
                "min_date" : "1990-01-01",
                "max_date" : "2021-01-01"
            }
        }
        fake_series_group = [MagicMock()]

        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.clients.SeriesGroup.to_object_async", AsyncMock(return_value=fake_series_group)) as mock_to_object:
            result = await maps_api.get_series_group("SMU56000000500000001")
            mock_get.assert_called_once_with("/series/group", {"series_id": "SMU56000000500000001", "file_type": "json"})
            mock_to_object.assert_called_once_with(fake_response)
            assert result == fake_series_group

        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(side_effect=ValueError("API error"))):
            with pytest.raises(ValueError, match="API error"):
                await maps_api.get_series_group("SMU56000000500000001")

        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
            patch("fedfred.clients.SeriesGroup.to_object_async", side_effect=ValueError("Parse error")):
            with pytest.raises(ValueError, match="Parse error"):
                await maps_api.get_series_group("SMU56000000500000001")

    @pytest.mark.asyncio
    async def test_get_series_data(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Async.Maps

        fake_response = {
            "meta": {
                "title": "2012 Per Capita Personal Income by State (Dollars)",
                "region": "state",
                "seasonality": "Not Seasonally Adjusted",
                "units": "Dollars",
                "frequency": "Annual",
                "date": "2012-01-01",
                "data":{"2013-01-01":[{
                    "region": "Massachusetts",
                    "code": "25",
                    "value": "56713",
                    "series_id": "MAPCPI"
                    },]
                }
            }
        }
        meta_data = fake_response["meta"]
        region_type = "state"
        fake_gdf = MagicMock(spec=gpd.GeoDataFrame)

        # Patch helpers and get_shape_files for all geodataframe_method branches
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
            patch("fedfred.helpers.FredHelpers.extract_region_type_async", AsyncMock(return_value=region_type)), \
            patch.object(maps_api, "get_shape_files", AsyncMock(return_value=fake_gdf)):

            # geopandas branch
            with patch("fedfred.helpers.FredHelpers.to_gpd_gdf_async", AsyncMock(return_value="gpd_gdf")) as mock_gpd:
                result = await maps_api.get_series_data("SMU56000000500000001", geodataframe_method="geopandas")
                mock_gpd.assert_awaited_once_with(fake_gdf, meta_data)
                assert result == "gpd_gdf"

            # dask branch
            with patch("fedfred.helpers.FredHelpers.to_dd_gpd_gdf_async", AsyncMock(return_value="dd_gdf")) as mock_dd:
                result = await maps_api.get_series_data("SMU56000000500000001", geodataframe_method="dask")
                mock_dd.assert_awaited_once_with(fake_gdf, meta_data)
                assert result == "dd_gdf"

            # polars branch
            with patch("fedfred.helpers.FredHelpers.to_pl_st_gdf_async", AsyncMock(return_value="pl_gdf")) as mock_pl:
                result = await maps_api.get_series_data("SMU56000000500000001", geodataframe_method="polars")
                mock_pl.assert_awaited_once_with(fake_gdf, meta_data)
                assert result == "pl_gdf"

            # invalid geodataframe_method
            with pytest.raises(ValueError, match="geodataframe_method must be 'geopandas', 'polars', or 'dask'"):
                await maps_api.get_series_data("SMU56000000500000001", geodataframe_method="invalid")

        # shapefile not a GeoDataFrame
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
            patch("fedfred.helpers.FredHelpers.extract_region_type_async", AsyncMock(return_value=region_type)), \
            patch.object(maps_api, "get_shape_files", AsyncMock(return_value="not_a_gdf")):
            with pytest.raises(ValueError, match="shapefile type error"):
                await maps_api.get_series_data("SMU56000000500000001")

        # Test with date and start_date as datetime
        dt = datetime(2012, 1, 1)
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)) as mock_get, \
            patch("fedfred.helpers.FredHelpers.extract_region_type_async", AsyncMock(return_value=region_type)), \
            patch.object(maps_api, "get_shape_files", AsyncMock(return_value=fake_gdf)), \
            patch("fedfred.helpers.FredHelpers.to_gpd_gdf_async", AsyncMock(return_value="gpd_gdf")), \
            patch("fedfred.helpers.FredHelpers.datetime_conversion_async", AsyncMock(return_value="2012-01-01")) as mock_dtconv:
            result = await maps_api.get_series_data("SMU56000000500000001", date=dt, start_date=dt)
            assert result == "gpd_gdf"
            # Check that datetime_conversion_async was called for both date and start_date
            assert mock_dtconv.await_count >= 2

    @pytest.mark.asyncio
    async def test_get_regional_data(self):
        parent = FredAPI("testkey", cache_mode=True, cache_size=10)
        maps_api = parent.Async.Maps

        fake_response = {
            "2013 Per Capita Personal Income by State (Dollars)": {
                "2013": [{
                    "region": "Alabama",
                    "code": "01",
                    "value": "36481",
                    "series_id": "ALPCPI"
                }, {
                    "region": "Alaska",
                    "code": "02",
                    "value": "50150",
                    "series_id": "AKPCPI"
                }, {
                    "region": "Arizona",
                    "code": "04",
                    "value": "36983",
                    "series_id": "AZPCPI"
                }, {
                    "region": "Arkansas",
                    "code": "05",
                    "value": "36698",
                    "series_id": "ARPCPI"
                }, {
                    "region": "California",
                    "code": "06",
                    "value": "48434",
                    "series_id": "CAPCPI"
                }, {
                    "region": "Colorado",
                    "code": "08",
                    "value": "46897",
                    "series_id": "COPCPI"
                }, {
                    "region": "Connecticut",
                    "code": "09",
                    "value": "60658",
                    "series_id": "CTPCPI"
                }, {
                    "region": "Delaware",
                    "code": "10",
                    "value": "44815",
                    "series_id": "DEPCPI"
                }, {
                    "region": "District of Columbia",
                    "code": "11",
                    "value": "75329",
                    "series_id": "DCPCPI"
                }, {
                    "region": "Florida",
                    "code": "12",
                    "value": "41497",
                    "series_id": "FLPCPI"
                }, {
                    "region": "Georgia",
                    "code": "13",
                    "value": "37845",
                    "series_id": "GAPCPI"
                }, {
                    "region": "Hawaii",
                    "code": "15",
                    "value": "45204",
                    "series_id": "HIPCPI"
                }, {
                    "region": "Idaho",
                    "code": "16",
                    "value": "36146",
                    "series_id": "IDPCPI"
                }, {
                    "region": "Illinois",
                    "code": "17",
                    "value": "46980",
                    "series_id": "ILPCPI"
                }, {
                    "region": "Indiana",
                    "code": "18",
                    "value": "38622",
                    "series_id": "INPCPI"
                }, {
                    "region": "Iowa",
                    "code": "19",
                    "value": "44763",
                    "series_id": "IAPCPI"
                }, {
                    "region": "Kansas",
                    "code": "20",
                    "value": "44417",
                    "series_id": "KSPCPI"
                }, {
                    "region": "Kentucky",
                    "code": "21",
                    "value": "36214",
                    "series_id": "KYPCPI"
                }, {
                    "region": "Louisiana",
                    "code": "22",
                    "value": "41204",
                    "series_id": "LAPCPI"
                }, {
                    "region": "Maine",
                    "code": "23",
                    "value": "40924",
                    "series_id": "MEPCPI"
                }, {
                    "region": "Maryland",
                    "code": "24",
                    "value": "53826",
                    "series_id": "MDPCPI"
                }, {
                    "region": "Massachusetts",
                    "code": "25",
                    "value": "57248",
                    "series_id": "MAPCPI"
                }, {
                    "region": "Michigan",
                    "code": "26",
                    "value": "39055",
                    "series_id": "MIPCPI"
                }, {
                    "region": "Minnesota",
                    "code": "27",
                    "value": "47500",
                    "series_id": "MNPCPI"
                }, {
                    "region": "Mississippi",
                    "code": "28",
                    "value": "33913",
                    "series_id": "MSPCPI"
                }, {
                    "region": "Missouri",
                    "code": "29",
                    "value": "40663",
                    "series_id": "MOPCPI"
                }, {
                    "region": "Montana",
                    "code": "30",
                    "value": "39366",
                    "series_id": "MTPCPI"
                }, {
                    "region": "Nebraska",
                    "code": "31",
                    "value": "47157",
                    "series_id": "NEPCPI"
                }, {
                    "region": "Nevada",
                    "code": "32",
                    "value": "39235",
                    "series_id": "NVPCPI"
                }, {
                    "region": "New Hampshire",
                    "code": "33",
                    "value": "51013",
                    "series_id": "NHPCPI"
                }, {
                    "region": "New Jersey",
                    "code": "34",
                    "value": "55386",
                    "series_id": "NJPCPI"
                }, {
                    "region": "New Mexico",
                    "code": "35",
                    "value": "35965",
                    "series_id": "NMPCPI"
                }, {
                    "region": "New York",
                    "code": "36",
                    "value": "54462",
                    "series_id": "NYPCPI"
                }, {
                    "region": "North Carolina",
                    "code": "37",
                    "value": "38683",
                    "series_id": "NCPCPI"
                }, {
                    "region": "North Dakota",
                    "code": "38",
                    "value": "53182",
                    "series_id": "NDPCPI"
                }, {
                    "region": "Ohio",
                    "code": "39",
                    "value": "41049",
                    "series_id": "OHPCPI"
                }, {
                    "region": "Oklahoma",
                    "code": "40",
                    "value": "41861",
                    "series_id": "OKPCPI"
                }, {
                    "region": "Oregon",
                    "code": "41",
                    "value": "39848",
                    "series_id": "ORPCPI"
                }, {
                    "region": "Pennsylvania",
                    "code": "42",
                    "value": "46202",
                    "series_id": "PAPCPI"
                }, {
                    "region": "Rhode Island",
                    "code": "44",
                    "value": "46989",
                    "series_id": "RIPCPI"
                }, {
                    "region": "South Carolina",
                    "code": "45",
                    "value": "35831",
                    "series_id": "SCPCPI"
                }, {
                    "region": "South Dakota",
                    "code": "46",
                    "value": "46039",
                    "series_id": "SDPCPI"
                }, {
                    "region": "Tennessee",
                    "code": "47",
                    "value": "39558",
                    "series_id": "TNPCPI"
                }, {
                    "region": "Texas",
                    "code": "48",
                    "value": "43862",
                    "series_id": "TXPCPI"
                }, {
                    "region": "Utah",
                    "code": "49",
                    "value": "36640",
                    "series_id": "UTPCPI"
                }, {
                    "region": "Vermont",
                    "code": "50",
                    "value": "45483",
                    "series_id": "VTPCPI"
                }, {
                    "region": "Virginia",
                    "code": "51",
                    "value": "48838",
                    "series_id": "VAPCPI"
                }, {
                    "region": "Washington",
                    "code": "53",
                    "value": "47717",
                    "series_id": "WAPCPI"
                }, {
                    "region": "West Virginia",
                    "code": "54",
                    "value": "35533",
                    "series_id": "WVPCPI"
                }, {
                    "region": "Wisconsin",
                    "code": "55",
                    "value": "43244",
                    "series_id": "WIPCPI"
                }, {
                    "region": "Wyoming",
                    "code": "56",
                    "value": "52826",
                    "series_id": "WYPCPI"
                }]
            }
        }
        region_type = "state"
        fake_gdf = MagicMock(spec=gpd.GeoDataFrame)
        meta_data = {}

        # Patch helpers and get_shape_files for all geodataframe_method branches
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
            patch("fedfred.helpers.FredHelpers.extract_region_type_async", AsyncMock(return_value=region_type)), \
            patch.object(maps_api, "get_shape_files", AsyncMock(return_value=fake_gdf)):

            # geopandas branch
            with patch("fedfred.helpers.FredHelpers.to_gpd_gdf_async", AsyncMock(return_value="gpd_gdf")) as mock_gpd:
                result = await maps_api.get_regional_data(
                    series_group="882",
                    region_type="state",
                    date="2013-01-01",
                    season="NSA",
                    units="Dollars",
                    frequency="a",
                    geodataframe_method="geopandas"
                )
                mock_gpd.assert_awaited_once_with(fake_gdf, meta_data)
                assert result == "gpd_gdf"

            # dask branch
            with patch("fedfred.helpers.FredHelpers.to_dd_gpd_gdf_async", AsyncMock(return_value="dd_gdf")) as mock_dd:
                result = await maps_api.get_regional_data(
                    series_group="882",
                    region_type="state",
                    date="2013-01-01",
                    season="NSA",
                    units="Dollars",
                    frequency="a",
                    geodataframe_method="dask"
                )
                mock_dd.assert_awaited_once_with(fake_gdf, meta_data)
                assert result == "dd_gdf"

            # polars branch
            with patch("fedfred.helpers.FredHelpers.to_pl_st_gdf_async", AsyncMock(return_value="pl_gdf")) as mock_pl:
                result = await maps_api.get_regional_data(
                    series_group="882",
                    region_type="state",
                    date="2013-01-01",
                    season="NSA",
                    units="Dollars",
                    frequency="a",
                    geodataframe_method="polars"
                )
                mock_pl.assert_awaited_once_with(fake_gdf, meta_data)
                assert result == "pl_gdf"

            # invalid geodataframe_method
            with pytest.raises(ValueError, match="geodataframe_method must be 'geopandas', 'polars', or 'dask'"):
                await maps_api.get_regional_data(
                    series_group="882",
                    region_type="state",
                    date="2013-01-01",
                    season="NSA",
                    units="Dollars",
                    frequency="a",
                    geodataframe_method="invalid"
                )

        # shapefile not a GeoDataFrame
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
            patch("fedfred.helpers.FredHelpers.extract_region_type_async", AsyncMock(return_value=region_type)), \
            patch.object(maps_api, "get_shape_files", AsyncMock(return_value="not_a_gdf")):
            with pytest.raises(ValueError, match="shapefile type error"):
                await maps_api.get_regional_data(
                    series_group="882",
                    region_type="state",
                    date="2013-01-01",
                    season="NSA",
                    units="Dollars",
                    frequency="a"
                )

        # Test with date and start_date as datetime
        dt = datetime(2013, 1, 1)
        dt_start = datetime(2012, 1, 1)
        with patch.object(maps_api, "_AsyncMapsAPI__fred_get_request", AsyncMock(return_value=fake_response)), \
            patch("fedfred.helpers.FredHelpers.extract_region_type_async", AsyncMock(return_value=region_type)), \
            patch.object(maps_api, "get_shape_files", AsyncMock(return_value=fake_gdf)), \
            patch("fedfred.helpers.FredHelpers.to_gpd_gdf_async", AsyncMock(return_value="gpd_gdf")), \
            patch("fedfred.helpers.FredHelpers.datetime_conversion_async", AsyncMock(return_value="2013-01-01")) as mock_dtconv:
            result = await maps_api.get_regional_data(
                series_group="882",
                region_type="state",
                date=dt,
                season="NSA",
                units="Dollars",
                geodataframe_method="geopandas",
                start_date=dt_start,
                transformation="lin",
                frequency="a",
                aggregation_method="avg"
            )
            assert result == "gpd_gdf"
            assert mock_dtconv.await_count == 1  # Only start_date is async, date is sync in your code
