# filepath: /test/helpers_test.py
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
Comprehensive tests for the helpers module.
"""

import datetime
import builtins
import pandas as pd
import polars as pl
import dask.dataframe as dd
import geopandas as gpd
import dask_geopandas as dd_gpd
import pytest
from fedfred.helpers import FredHelpers
from fedfred.__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__

class TestConditionalImports:
    """
    Test class for conditional imports in the helpers module.
    """

    def test_to_pl_df_importerror(self, monkeypatch):
        """
        Test that to_pl_df raises ImportError when polars is not installed.
        """

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "polars":
                raise ImportError("No module named 'polars'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(ImportError, match="Polars is not installed"):
            FredHelpers.to_pl_df({"observations": []})

    @pytest.mark.asyncio
    async def test_to_pl_df_importerror_async(self, monkeypatch):
        """
        Test that to_pl_df_async raises ImportError when polars is not installed.
        """

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "polars":
                raise ImportError("No module named 'polars'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(ImportError, match="Polars is not installed"):
            await FredHelpers.to_pl_df_async({"observations": []})

    def test_to_dd_df_importerror(self, monkeypatch):
        """
        Test that to_dd_df raises ImportError when dask.dataframe is not installed.
        """

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "dask.dataframe":
                raise ImportError("No module named 'dask.dataframe'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(ImportError, match="Dask is not installed"):
            FredHelpers.to_dd_df({"observations": []})

    @pytest.mark.asyncio
    async def test_to_dd_df_importerror_async(self, monkeypatch):
        """
        Test that to_dd_df_async raises ImportError when dask.dataframe is not installed.
        """

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "dask.dataframe":
                raise ImportError("No module named 'dask.dataframe'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(ImportError, match="Dask is not installed"):
            await FredHelpers.to_dd_df_async({"observations": []})

    def test_to_dd_gpd_gdf_importerror(self, monkeypatch):
        """
        Test that to_dd_gpd raises ImportError when dask_geopandas is not installed.
        """

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "dask_geopandas":
                raise ImportError("No module named 'dask_geopandas'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(ImportError, match="Dask GeoPandas is not installed"):
            FredHelpers.to_dd_gpd_gdf({"observations": []}, {})

    @pytest.mark.asyncio
    async def test_to_dd_gpd_gdf_importerror_async(self, monkeypatch):
        """
        Test that to_dd_gpd_async raises ImportError when dask_geopandas is not installed.
        """

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "dask_geopandas":
                raise ImportError("No module named 'dask_geopandas'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(ImportError, match="Dask GeoPandas is not installed"):
            await FredHelpers.to_dd_gpd_gdf_async({"observations": []}, {})

    def test_to_pl_st_gdf_importerror(self, monkeypatch):
        """
        Test that to_pl_st_gdf raises ImportError when polars_st is not installed.
        """

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "polars_st":
                raise ImportError("No module named 'polars_st'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(ImportError, match="Polars with geospatial support is not installed"):
            FredHelpers.to_pl_st_gdf({"observations": []}, {})

    @pytest.mark.asyncio
    async def test_to_pl_st_gdf_importerror_async(self, monkeypatch):
        """
        Test that to_pl_st_gdf_async raises ImportError when polars_st is not installed.
        """

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "polars_st":
                raise ImportError("No module named 'polars_st'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(ImportError, match="Polars with geospatial support is not installed"):
            await FredHelpers.to_pl_st_gdf_async({"observations": []}, {})

class TestDataFrameHelpers:
    """
    Test class for DataFrame helper functions.
    """

    response_dict = {
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
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1933-01-01",
                "value": "783.3"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1934-01-01",
                "value": "866.7"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1935-01-01",
                "value": "944.3"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1936-01-01",
                "value": "1065.0"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1937-01-01",
                "value": "1120.6"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1938-01-01",
                "value": "1083.9"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1939-01-01",
                "value": "1170.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1940-01-01",
                "value": "1271.7"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1941-01-01",
                "value": "1497.6"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1942-01-01",
                "value": "1779.4"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1943-01-01",
                "value": "2081.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1944-01-01",
                "value": "2247.3"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1945-01-01",
                "value": "2224.7"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1946-01-01",
                "value": "1969.3"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1947-01-01",
                "value": "1950.6"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1948-01-01",
                "value": "2033.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1949-01-01",
                "value": "2021.1"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1950-01-01",
                "value": "2197.5"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1951-01-01",
                "value": "2376.4"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1952-01-01",
                "value": "2473.1"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1953-01-01",
                "value": "2587.7"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1954-01-01",
                "value": "2574.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1955-01-01",
                "value": "2758.4"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1956-01-01",
                "value": "2818.6"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1957-01-01",
                "value": "2878.5"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1958-01-01",
                "value": "2854.6"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1959-01-01",
                "value": "3050.8"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1960-01-01",
                "value": "3130.4"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1961-01-01",
                "value": "3211.9"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1962-01-01",
                "value": "3409.8"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1963-01-01",
                "value": "3559.0"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1964-01-01",
                "value": "3764.8"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1965-01-01",
                "value": "4008.8"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1966-01-01",
                "value": "4269.4"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1967-01-01",
                "value": "4386.7"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1968-01-01",
                "value": "4602.8"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1969-01-01",
                "value": "4745.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1970-01-01",
                "value": "4754.6"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1971-01-01",
                "value": "4913.6"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1972-01-01",
                "value": "5172.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1973-01-01",
                "value": "5475.1"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1974-01-01",
                "value": "5454.1"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1975-01-01",
                "value": "5430.4"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1976-01-01",
                "value": "5729.1"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1977-01-01",
                "value": "5997.3"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1978-01-01",
                "value": "6326.9"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1979-01-01",
                "value": "6547.0"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1980-01-01",
                "value": "6530.3"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1981-01-01",
                "value": "6688.0"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1982-01-01",
                "value": "6564.6"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1983-01-01",
                "value": "6863.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1984-01-01",
                "value": "7352.5"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1985-01-01",
                "value": "7640.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1986-01-01",
                "value": "7890.9"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1987-01-01",
                "value": "8161.0"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1988-01-01",
                "value": "8509.9"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1989-01-01",
                "value": "8822.6"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1990-01-01",
                "value": "9003.0"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1991-01-01",
                "value": "8988.6"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1992-01-01",
                "value": "9305.0"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1993-01-01",
                "value": "9559.8"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1994-01-01",
                "value": "9932.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1995-01-01",
                "value": "10206.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1996-01-01",
                "value": "10595.1"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1997-01-01",
                "value": "11058.1"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1998-01-01",
                "value": "11540.7"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "1999-01-01",
                "value": "12108.9"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2000-01-01",
                "value": "12614.3"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2001-01-01",
                "value": "12750.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2002-01-01",
                "value": "12970.8"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2003-01-01",
                "value": "13352.2"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2004-01-01",
                "value": "13879.0"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2005-01-01",
                "value": "14340.8"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2006-01-01",
                "value": "14690.9"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2007-01-01",
                "value": "15009.7"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2008-01-01",
                "value": "15009.0"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2009-01-01",
                "value": "14565.1"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2010-01-01",
                "value": "14966.5"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2011-01-01",
                "value": "15286.7"
            },
            {
                "realtime_start": "2013-08-14",
                "realtime_end": "2013-08-14",
                "date": "2012-01-01",
                "value": "15693.1"
            }
        ]
    }
    invalid_response_dict = {
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
    }

    def test_to_pd_df(self):
        """
        Test the to_pd_df function.
        """

        df = FredHelpers.to_pd_df(self.response_dict)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) == len(self.response_dict["observations"])
        assert "realtime_start" in df.columns
        assert "realtime_end" in df.columns
        assert "value" in df.columns
        assert "date" in df.index.names
        assert df.index.name == "date"
        assert df["value"].dtype == "float64"
        assert df.index.dtype == "datetime64[ns]"

        with pytest.raises(ValueError):
            FredHelpers.to_pd_df(self.invalid_response_dict)

    def test_to_pl_df(self):
        """
        Test the to_pl_df function.
        """

        df = FredHelpers.to_pl_df(self.response_dict)

        assert isinstance(df, pl.DataFrame)
        assert not df.is_empty()
        assert df.height == len(self.response_dict["observations"])
        assert "realtime_start" in df.columns
        assert "realtime_end" in df.columns
        assert "value" in df.columns
        assert "date" in df.columns
        assert df["value"].dtype == pl.Float64
        assert df["date"].dtype == pl.String

        with pytest.raises(ValueError):
            FredHelpers.to_pl_df(self.invalid_response_dict)

    def test_to_dd_df(self):
        """
        Test the to_dd_df function.
        """

        df = FredHelpers.to_dd_df(self.response_dict)

        assert isinstance(df, dd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) > 0
        assert len(df) == len(self.response_dict["observations"])
        assert "realtime_start" in df.columns
        assert "realtime_end" in df.columns
        assert "value" in df.columns
        assert df.index.name == "date"
        assert df["value"].dtype == "float64"
        assert df.index.dtype == "datetime64[ns]"

        with pytest.raises(ValueError):
            FredHelpers.to_dd_df(self.invalid_response_dict)

    def test_to_pd_series(self):
        """
        Full-branch coverage tests for FredHelpers.to_pd_series.
        """
        # 1) Series input path
        idx = pd.to_datetime(["2020-01-01", "2020-01-02"])
        s = pd.Series([1, 2], index=idx, name="old_name")
        # Make index non-datetime so conversion is exercised
        s.index = s.index.strftime("%Y-%m-%d")

        result = FredHelpers.to_pd_series(s, name="new_name")
        assert isinstance(result, pd.Series)
        assert result.name == "new_name"
        assert list(result.index) == list(idx)
        assert result.dtype == float
        assert result.tolist() == [1.0, 2.0]

        # 2) Non-Series / Non-DataFrame raises TypeError
        with pytest.raises(TypeError, match="Input must be a pd.Series or pd.DataFrame"):
            FredHelpers.to_pd_series([1, 2, 3], name="x")  # type: ignore[arg-type]

        # 3) DataFrame: index named 'date' → use index
        idx2 = pd.to_datetime(["2021-01-01", "2021-01-02"])
        df_index_date = pd.DataFrame({"value": [10, 20]}, index=idx2)
        df_index_date.index.name = "date"

        result = FredHelpers.to_pd_series(df_index_date, name="s1")
        assert list(result.index) == list(idx2)
        assert result.tolist() == [10.0, 20.0]

        # 4) DataFrame: 'date' column present
        df_date_col = pd.DataFrame(
            {
                "date": ["2022-01-01", "2022-01-02"],
                "value": ["1", "2"],
            }
        )
        # ensure index.name is a str so the assertion passes
        df_date_col.index.name = "idx"

        result = FredHelpers.to_pd_series(df_date_col, name="s2")
        expected_idx = pd.to_datetime(["2022-01-01", "2022-01-02"])
        assert list(result.index) == list(expected_idx)
        assert result.tolist() == [1.0, 2.0]

        # 5) DataFrame: other date-like column (name contains 'date')
        df_other_date_col = pd.DataFrame(
            {
                "observation_date": ["2023-01-01", "2023-01-02"],
                "value": [100, 200],
            }
        )
        df_other_date_col.index.name = "idx"

        result = FredHelpers.to_pd_series(df_other_date_col, name="s3")
        expected_idx = pd.to_datetime(["2023-01-01", "2023-01-02"])
        assert list(result.index) == list(expected_idx)
        assert result.tolist() == [100.0, 200.0]

        # 6) DataFrame: no date-like columns → fallback to index
        idx3 = pd.to_datetime(["2024-01-01", "2024-01-02"])
        df_index_fallback = pd.DataFrame({"value": [3, 4]}, index=idx3)
        df_index_fallback.index.name = "not_date"  # still a str

        result = FredHelpers.to_pd_series(df_index_fallback, name="s4")
        assert list(result.index) == list(idx3)
        assert result.tolist() == [3.0, 4.0]

        # 7) DataFrame: no 'value' column but numeric columns present → first numeric
        df_first_numeric = pd.DataFrame(
            {
                "date": ["2025-01-01", "2025-01-02"],
                "x": [5, 6],        # numeric
                "y": ["a", "b"],    # non-numeric
            }
        )
        df_first_numeric.index.name = "idx"

        result = FredHelpers.to_pd_series(df_first_numeric, name="s5")
        expected_idx = pd.to_datetime(["2025-01-01", "2025-01-02"])
        assert list(result.index) == list(expected_idx)
        assert result.tolist() == [5.0, 6.0]

        # 8) DataFrame: no 'value' and no numeric dtypes → use last column, coerce
        df_last_col = pd.DataFrame(
            {
                "date": ["2026-01-01", "2026-01-02"],
                "a": ["1", "2"],
                "b": ["3", "4"],  # last column, will be coerced
            }
        )
        df_last_col.index.name = "idx"

        result = FredHelpers.to_pd_series(df_last_col, name="s6")
        expected_idx = pd.to_datetime(["2026-01-01", "2026-01-02"])
        assert list(result.index) == list(expected_idx)
        assert result.tolist() == [3.0, 4.0]

        # 9) DataFrame: duplicates in date → keep last, sort
        df_dupes = pd.DataFrame(
            {
                "date": ["2020-01-02", "2020-01-01", "2020-01-01"],
                "value": [1, 2, 3],
            }
        )
        df_dupes.index.name = "idx"

        result = FredHelpers.to_pd_series(df_dupes, name="s7")
        expected_idx = pd.to_datetime(["2020-01-01", "2020-01-02"])
        # For 2020-01-01, last value is 3; for 2020-01-02 it's 1
        assert list(result.index) == list(expected_idx)
        assert result.tolist() == [3.0, 1.0]

    @pytest.mark.asyncio
    async def test_to_pd_df_async(self):
        """
        Test the to_pd_df_async function.
        """

        df = await FredHelpers.to_pd_df_async(self.response_dict)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) == len(self.response_dict["observations"])
        assert "realtime_start" in df.columns
        assert "realtime_end" in df.columns
        assert "value" in df.columns
        assert "date" in df.index.names
        assert df.index.name == "date"
        assert df["value"].dtype == "float64"
        assert df.index.dtype == "datetime64[ns]"

        with pytest.raises(ValueError):
            await FredHelpers.to_pd_df_async(self.invalid_response_dict)

    @pytest.mark.asyncio
    async def test_to_pl_df_async(self):
        """
        Test the to_pl_df_async function.
        """

        df = await FredHelpers.to_pl_df_async(self.response_dict)

        assert isinstance(df, pl.DataFrame)
        assert not df.is_empty()
        assert df.height == len(self.response_dict["observations"])
        assert "realtime_start" in df.columns
        assert "realtime_end" in df.columns
        assert "value" in df.columns
        assert "date" in df.columns
        assert df["value"].dtype == pl.Float64
        assert df["date"].dtype == pl.String

        with pytest.raises(ValueError):
            await FredHelpers.to_pl_df_async(self.invalid_response_dict)

    @pytest.mark.asyncio
    async def test_to_dd_df_async(self):
        """
        Test the to_dd_df_async function.
        """

        df = await FredHelpers.to_dd_df_async(self.response_dict)

        assert isinstance(df, dd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) > 0
        assert len(df) == len(self.response_dict["observations"])
        assert "realtime_start" in df.columns
        assert "realtime_end" in df.columns
        assert "value" in df.columns
        assert df.index.name == "date"
        assert df["value"].dtype == "float64"
        assert df.index.dtype == "datetime64[ns]"

        with pytest.raises(ValueError):
            await FredHelpers.to_dd_df_async(self.invalid_response_dict)

    @pytest.mark.asyncio
    async def test_to_pd_series_async(self, monkeypatch):
        """
        Full coverage for FredHelpers.to_pd_series_async:
        - delegates to FredHelpers.to_pd_series via asyncio.to_thread
        - returns the resulting Series
        - propagates TypeError from the sync helper
        """
        # Prepare a simple Series input
        idx = pd.to_datetime(["2020-01-01", "2020-01-02"])
        s = pd.Series([1, 2], index=idx, name="old_name")

        # 1) Happy path: ensure delegation and return value
        called = {}

        async def fake_to_thread(fn, *args, **kwargs):
            # Capture what function and args were used
            called["fn"] = fn
            called["args"] = args
            called["kwargs"] = kwargs
            # Call the real sync helper to keep behavior realistic
            return fn(*args, **kwargs)

        monkeypatch.setattr("fedfred.helpers.asyncio.to_thread", fake_to_thread)

        result = await FredHelpers.to_pd_series_async(s, "new_name")

        assert isinstance(result, pd.Series)
        assert result.name == "new_name"
        assert called["fn"] is FredHelpers.to_pd_series
        assert called["args"] == (s, "new_name")

        # 2) Error path: TypeError from sync helper is propagated
        with pytest.raises(TypeError, match="Input must be a pd.Series or pd.DataFrame"):
            await FredHelpers.to_pd_series_async([1, 2, 3], "bad")  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_pd_frequency_conversion_async(self, monkeypatch):
        """
        Full coverage for FredHelpers.pd_frequency_conversion_async:
        - delegates to FredHelpers.pd_frequency_conversion via asyncio.to_thread
        - returns the converted string
        """
        called = {}

        async def fake_to_thread(fn, *args, **kwargs):
            called["fn"] = fn
            called["args"] = args
            called["kwargs"] = kwargs
            # Call the real sync helper so behavior stays realistic
            return fn(*args, **kwargs)

        # Patch asyncio.to_thread used inside fedfred.helpers
        monkeypatch.setattr("fedfred.helpers.asyncio.to_thread", fake_to_thread)

        # Use a frequency that exercises a non-trivial branch of the sync helper
        result = await FredHelpers.pd_frequency_conversion_async("wef")

        assert result == "W-FRI"
        assert called["fn"] is FredHelpers.pd_frequency_conversion
        assert called["args"] == ("wef",)
        assert called["kwargs"] == {}

class TestGeoDataFrameHelpers:
    """
    Test class for GeoDataFrame helper functions.
    """
    response_dict = {
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
    meta_data = response_dict.get("meta", {})
    shapefile_dict = {
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
    invalid_response_dict = {
        "meta": {
            "title": "2012 Per Capita Personal Income by State (Dollars)",
            "region": "state",
            "seasonality": "Not Seasonally Adjusted",
            "units": "Dollars",
            "frequency": "Annual",
            "date": "2012-01-01",
            }
        }
    invalid_meta_data = invalid_response_dict.get("meta", {})

    def test_extract_region_type(self):
        """
        Test the extract_region_type function.
        """

        region_type = FredHelpers.extract_region_type(self.response_dict)

        assert isinstance(region_type, str)
        assert region_type == "state"

        with pytest.raises(ValueError):
            no_meta_data = {}
            FredHelpers.extract_region_type(no_meta_data)

        with pytest.raises(ValueError):
            no_region_type = {
                "meta": {
                    "title": "2012 Per Capita Personal Income by State (Dollars)"
                },
            }
            FredHelpers.extract_region_type(no_region_type)

    def test_to_gpd_gdf(self):
        """
        Test the to_gpd_df function.
        """

        shapefile=gpd.GeoDataFrame.from_features(self.shapefile_dict['features'])
        gdf = FredHelpers.to_gpd_gdf(shapefile, self.meta_data)

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert not gdf.empty
        assert len(gdf) == len(shapefile)
        assert "value" in gdf.columns
        assert "region" in gdf.columns

        with pytest.raises(ValueError):
            shapefile=gpd.GeoDataFrame.from_features(self.shapefile_dict['features'])
            FredHelpers.to_gpd_gdf(shapefile, self.invalid_meta_data)

    def test_to_pl_st_gdf(self):
        """
        Test the to_pl_gpd_df function.
        """

        shapefile=gpd.GeoDataFrame.from_features(self.shapefile_dict['features'])
        gdf = FredHelpers.to_pl_st_gdf(shapefile, self.meta_data)

        assert isinstance(gdf, pl.DataFrame)
        assert not gdf.is_empty()
        assert gdf.height == len(shapefile)
        assert "value" in gdf.columns
        assert "region" in gdf.columns

    def test_to_dd_gpd_gdf(self):
        """
        Test the to_dd_gpd_df function.
        """

        shapefile=gpd.GeoDataFrame.from_features(self.shapefile_dict['features'])
        gdf = FredHelpers.to_dd_gpd_gdf(shapefile, self.meta_data)

        assert isinstance(gdf, dd_gpd.GeoDataFrame)
        assert gdf.npartitions == 1
        assert len(gdf) == len(shapefile)
        assert "value" in gdf.columns
        assert "region" in gdf.columns

    @pytest.mark.asyncio
    async def test_extract_region_type_async(self):
        """
        Test the extract_region_type_async function.
        """

        region_type = await FredHelpers.extract_region_type_async(self.response_dict)

        assert isinstance(region_type, str)
        assert region_type == "state"

    @pytest.mark.asyncio
    async def test_to_gpd_gdf_async(self):
        """
        Test the to_gpd_df_async function.
        """

        shapefile=gpd.GeoDataFrame.from_features(self.shapefile_dict['features'])
        gdf = await FredHelpers.to_gpd_gdf_async(shapefile, self.meta_data)

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert not gdf.empty
        assert len(gdf) == len(shapefile)
        assert "value" in gdf.columns
        assert "region" in gdf.columns

    @pytest.mark.asyncio
    async def test_to_pl_st_gdf_async(self):
        """
        Test the to_pl_gpd_df_async function.
        """

        shapefile=gpd.GeoDataFrame.from_features(self.shapefile_dict['features'])
        gdf = await FredHelpers.to_pl_st_gdf_async(shapefile, self.meta_data)

        assert isinstance(gdf, pl.DataFrame)
        assert not gdf.is_empty()
        assert gdf.height == len(shapefile)
        assert "value" in gdf.columns
        assert "region" in gdf.columns

    @pytest.mark.asyncio
    async def test_to_dd_gpd_gdf_async(self):
        """
        Test the to_dd_gpd_df_async function.
        """

        shapefile=gpd.GeoDataFrame.from_features(self.shapefile_dict['features'])
        gdf = await FredHelpers.to_dd_gpd_gdf_async(shapefile, self.meta_data)

        assert isinstance(gdf, dd_gpd.GeoDataFrame)
        assert gdf.npartitions == 1
        assert len(gdf) == len(shapefile)
        assert "value" in gdf.columns
        assert "region" in gdf.columns

class TestConversionHelpers:
    """
    Test class for conversion helper functions.
    """
    def test_liststring_conversion(self):
        """
        Test the liststring_conversion function.
        """

        input_list = ["a", "b", "c"]
        invalid_type = 123
        invalid_list = ["a", 1, "c"]

        result = FredHelpers.liststring_conversion(input_list)

        with pytest.raises(ValueError):
            FredHelpers.liststring_conversion(invalid_list)

        with pytest.raises(ValueError):
            FredHelpers.liststring_conversion(invalid_type)

        assert isinstance(result, str)
        assert result == "a;b;c"

    def test_vintage_dates_type_conversion(self):
        """
        Test the vintage_dates_type_conversion function.
        """

        input_list = ["2023-01-01", "2023-02-01", "2023-03-01"]
        input_string = "2023-01-01"
        input_datetime = datetime.datetime(2023, 1, 1)
        invalid_type = 123
        invalid_list = ["2023-01-01", 123, "2023-03-01"]

        list_result = FredHelpers.vintage_dates_type_conversion(input_list)
        string_result = FredHelpers.vintage_dates_type_conversion(input_string)
        datetime_result = FredHelpers.vintage_dates_type_conversion(input_datetime)

        assert isinstance(list_result, str)
        assert isinstance(string_result, str)
        assert isinstance(datetime_result, str)

        with pytest.raises(ValueError):
            FredHelpers.vintage_dates_type_conversion(invalid_list)

        with pytest.raises(ValueError):
            FredHelpers.vintage_dates_type_conversion(invalid_type)

    def test_datetime_conversion(self):
        """
        Test the datetime_conversion function.
        """

        input_date = datetime.datetime(2023, 1, 1)
        invalid_type = "2023-01-01"

        result = FredHelpers.datetime_conversion(input_date)

        assert isinstance(result, str)
        assert result == "2023-01-01"

        with pytest.raises(ValueError):
            FredHelpers.datetime_conversion(invalid_type)

    def test_datetime_hh_mm_conversion(self):
        """
        Test the datetime_hh_mm_conversion function.
        """

        input_date = datetime.datetime(2023, 1, 1, 12, 30)
        invalid_type = "12:30"

        result = FredHelpers.datetime_hh_mm_conversion(input_date)

        assert isinstance(result, str)
        assert result == "12:30"

        with pytest.raises(ValueError):
            FredHelpers.datetime_hh_mm_conversion(invalid_type)

    @pytest.mark.parametrize(
        "input_freq, expected",
        [
            # Passthrough compatible frequencies (case-insensitive)
            ("d", "D"),
            ("m", "M"),
            ("q", "Q"),
            ("w", "W"),
            ("D", "D"),
            ("M", "M"),
            ("Q", "Q"),
            ("W", "W"),
            # Annual -> yearly
            ("a", "Y"),
            ("A", "Y"),
            # Weekly end variants
            ("wef", "W-FRI"),
            ("WEF", "W-FRI"),
            ("weth", "W-THU"),
            ("WETH", "W-THU"),
            ("wew", "W-WED"),
            ("WEW", "W-WED"),
            ("wetu", "W-TUE"),
            ("WETU", "W-TUE"),
            ("wem", "W-MON"),
            ("WEM", "W-MON"),
            ("wesu", "W-SUN"),
            ("WESU", "W-SUN"),
            ("wesa", "W-SAT"),
            ("WESA", "W-SAT"),
            # Biweekly -> 2 x weekly
            ("bw", "2W"),
            ("BW", "2W"),
            # Biweekly end variants
            ("bwew", "2W-WED"),
            ("BWEW", "2W-WED"),
            ("bwem", "2W-MON"),
            ("BWEM", "2W-MON"),
            # Semiannual -> 2 x quarterly
            ("sa", "2Q"),
            ("SA", "2Q"),
            # Fallback / default branch
            ("unknown", "UNKNOWN"),
            ("", ""),
        ],
    )
    def test_pd_frequency_conversion(self, input_freq, expected):
        """
        Test the pd_frequency_conversion function.
        """
        assert FredHelpers.pd_frequency_conversion(input_freq) == expected

    @pytest.mark.asyncio
    async def test_liststring_conversion_async(self):
        """
        Test the liststring_conversion_async function.
        """

        input_list = ["a", "b", "c"]
        invalid_type = 123
        invalid_list = ["a", 1, "c"]

        result = await FredHelpers.liststring_conversion_async(input_list)

        assert isinstance(result, str)
        assert result == "a;b;c"

        with pytest.raises(ValueError):
            await FredHelpers.liststring_conversion_async(invalid_list)

        with pytest.raises(ValueError):
            await FredHelpers.liststring_conversion_async(invalid_type)

    @pytest.mark.asyncio
    async def test_vintage_dates_type_conversion_async(self):
        """
        Test the vintage_dates_type_conversion_async function.
        """

        input_list = ["2023-01-01", "2023-02-01", "2023-03-01"]
        input_string = "2023-01-01"
        input_datetime = datetime.datetime(2023, 1, 1)
        invalid_type = 123
        invalid_list = ["2023-01-01", 123, "2023-03-01"]

        list_result = await FredHelpers.vintage_dates_type_conversion_async(input_list)
        string_result = await FredHelpers.vintage_dates_type_conversion_async(input_string)
        datetime_result = await FredHelpers.vintage_dates_type_conversion_async(input_datetime)

        assert isinstance(list_result, str)
        assert isinstance(string_result, str)
        assert isinstance(datetime_result, str)

        with pytest.raises(ValueError):
            await FredHelpers.vintage_dates_type_conversion_async(invalid_list)

        with pytest.raises(ValueError):
            await FredHelpers.vintage_dates_type_conversion_async(invalid_type)

    @pytest.mark.asyncio
    async def test_datetime_conversion_async(self):
        """
        Test the datetime_conversion_async function.
        """

        input_date = datetime.datetime(2023, 1, 1)
        invalid_type = "2023-01-01"

        result = await FredHelpers.datetime_conversion_async(input_date)

        assert isinstance(result, str)
        assert result == "2023-01-01"

        with pytest.raises(ValueError):
            await FredHelpers.datetime_conversion_async(invalid_type)

    @pytest.mark.asyncio
    async def test_datetime_hh_mm_conversion_async(self):
        """
        Test the datetime_hh_mm_conversion_async function.
        """

        input_date = datetime.datetime(2023, 1, 1, 12, 30)
        invalid_type = "12:30"

        result = await FredHelpers.datetime_hh_mm_conversion_async(input_date)

        assert isinstance(result, str)
        assert result == "12:30"

        with pytest.raises(ValueError):
            await FredHelpers.datetime_hh_mm_conversion_async(invalid_type)

class TestValidationHelpers:
    """
    Test class for validation helper functions.
    """

    def test_datestring_validation(self):
        """
        Test the datestring_validation function.
        """

        valid_date = "2023-01-01"
        invalid_date = "2023-13-01"

        result = FredHelpers.datestring_validation(valid_date)
        assert result is None

        with pytest.raises(ValueError):
            result = FredHelpers.datestring_validation(invalid_date)

    def test_liststring_validation(self):
        """
        Test the liststrings_validation function.
        """

        valid_liststring = "a;b;c"
        invalid_type = 123
        invalid_liststring_terms = "a;b;%"
        invalid_liststring_seperator = "a,b,c"
        invalid_liststring_empty = "a;;b;c"
        invalid_liststring_whitespace = " a ; b ; c "


        result = FredHelpers.liststring_validation(valid_liststring)
        assert result is None

        with pytest.raises(ValueError):
            result = FredHelpers.liststring_validation(invalid_type)

        with pytest.raises(ValueError):
            result = FredHelpers.liststring_validation(invalid_liststring_terms)

        with pytest.raises(ValueError):
            result = FredHelpers.liststring_validation(invalid_liststring_seperator)

        with pytest.raises(ValueError):
            result = FredHelpers.liststring_validation(invalid_liststring_empty)

        with pytest.raises(ValueError):
            result = FredHelpers.liststring_validation(invalid_liststring_whitespace)

    def test_vintage_dates_validation(self):
        """
        Test the vintage_dates_validation function.
        """

        valid_vintage_list = "2023-01-01,2023-02-01,2023-03-01"
        invalid_vintage_list_seperator = "2023-01-01;2023-02-01;2023-03-01"
        invalid_vintage_list_empty = ""
        invalid_type = 123

        result = FredHelpers.vintage_dates_validation(valid_vintage_list)
        assert result is None

        with pytest.raises(ValueError):
            result = FredHelpers.vintage_dates_validation(invalid_type)

        with pytest.raises(ValueError):
            result = FredHelpers.vintage_dates_validation(invalid_vintage_list_seperator)

        with pytest.raises(ValueError):
            result = FredHelpers.vintage_dates_validation(invalid_vintage_list_empty)

    def test_hh_mm_datestring_validation(self):
        """
        Test the hh_mm_datestring_validation function.
        """

        valid_hh_mm = "12:30"
        invalid_hh_mm = "25:00"
        invalid_type = 123

        result = FredHelpers.hh_mm_datestring_validation(valid_hh_mm)
        assert result is None

        with pytest.raises(ValueError):
            result = FredHelpers.hh_mm_datestring_validation(invalid_hh_mm)

        with pytest.raises(ValueError):
            result = FredHelpers.hh_mm_datestring_validation(invalid_type)

    def test_parameter_validation(self):
        """
        Test the parameter_validation function.
        """

        #category_id
        category_id = {"category_id": 1}
        invalid_category_id_type = {"category_id": "one"}
        invalid_category_id_value = {"category_id": -1}

        category_id_result = FredHelpers.parameter_validation(category_id)
        assert category_id_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_category_id_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_category_id_value)

        #realtime_start
        realtime_start = {"realtime_start": "2023-01-01"}
        invalid_realtime_start = {"realtime_start": "2023-13-01"}
        invalid_realtime_start_type = {"realtime_start": 123}

        realtime_start_result = FredHelpers.parameter_validation(realtime_start)
        assert realtime_start_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_realtime_start)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_realtime_start_type)

        #realtime_end
        realtime_end = {"realtime_end": "2023-01-31"}
        invalid_realtime_end = {"realtime_end": "2023-13-01"}
        invalid_realtime_end_type = {"realtime_end": 123}

        realtime_end_result = FredHelpers.parameter_validation(realtime_end)
        assert realtime_end_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_realtime_end)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_realtime_end_type)

        #limit
        limit = {"limit": 100}
        invalid_limit_type = {"limit": "one"}
        invalid_limit_value = {"limit": -1}

        limit_result = FredHelpers.parameter_validation(limit)
        assert limit_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_limit_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_limit_value)

        #offset
        offset = {"offset": 1}
        invalid_offset_type = {"offset": "one"}
        invalid_offset_value = {"offset": -1}

        offset_result = FredHelpers.parameter_validation(offset)
        assert offset_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_offset_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_offset_value)

        #sort_order
        sort_order = [{"sort_order": "asc"}, {"sort_order": "desc"}]
        invalid_sort_order_type = {"sort_order": 1}
        invalid_sort_order_value = {"sort_order": "ascending"}

        for s in sort_order:
            sort_order_result = FredHelpers.parameter_validation(s)
            assert sort_order_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_sort_order_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_sort_order_value)

        #order_by
        order_by = [
            {"order_by": "series_id"},
            {"order_by": "title"},
            {"order_by": "units"},
            {"order_by": "frequency"},
            {"order_by": "seasonal_adjustment"},
            {"order_by": "realtime_start"},
            {"order_by": "realtime_end"},
            {"order_by": "last_updated"},
            {"order_by": "observation_start"},
            {"order_by": "observation_end"},
            {"order_by": "popularity"},
            {"order_by": "group_popularity"},
            {"order_by": "series_count"},
            {"order_by": "created"},
            {"order_by": "name"},
            {"order_by": "release_id"},
            {"order_by": "press_release"},
            {"order_by": "group_id"},
            {"order_by": "search_rank"},
            {"order_by": "title"},
            ]
        invalid_order_by_type = {"order_by": 1}
        invalid_order_by_value = {"order_by": "invalid_column"}

        for o in order_by:
            order_by_result = FredHelpers.parameter_validation(o)
            assert order_by_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_order_by_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_order_by_value)

        #filter_variable
        filter_variable = [
            {"filter_variable": "frequency"},
            {"filter_variable": "units"},
            {"filter_variable": "seasonal_adjustment"},
        ]
        invalid_filter_variable_type = {"filter_variable": 1}
        invalid_filter_variable_value = {"filter_variable": "invalid_variable"}

        for f in filter_variable:
            filter_variable_result = FredHelpers.parameter_validation(f)
            assert filter_variable_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_filter_variable_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_filter_variable_value)

        #filter_value
        filter_value = {"filter_value": "value1"}
        invalid_filter_value_type = {"filter_value": 1}

        filter_value_result = FredHelpers.parameter_validation(filter_value)
        assert filter_value_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_filter_value_type)

        #tag_names
        tag_names = {"tag_names": "tag1;tag2;tag3"}
        invalid_tag_names_type = {"tag_names": 1}
        invalid_tag_names_value = {"tag_names": "tag1,tag2,tag3"}

        tag_names_result = FredHelpers.parameter_validation(tag_names)
        assert tag_names_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_tag_names_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_tag_names_value)

        #exclude_tag_names
        exclude_tag_names = {"exclude_tag_names": "tag1;tag2;tag3"}
        invalid_exclude_tag_names_type = {"exclude_tag_names": 1}
        invalid_exclude_tag_names_value = {"exclude_tag_names": "tag1,tag2,tag3"}

        exclude_tag_names_result = FredHelpers.parameter_validation(exclude_tag_names)
        assert exclude_tag_names_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_exclude_tag_names_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_exclude_tag_names_value)

        #tag_group_id
        tag_group_id = [
            {"tag_group_id": 1},
            {"tag_group_id": "one"},
        ]
        invalid_tag_group_id_type = {"tag_group_id": [1, 2, 3]}
        invalid_tag_group_id_value = {"tag_group_id": -1}

        for t in tag_group_id:
            tag_group_id_result = FredHelpers.parameter_validation(t)
            assert tag_group_id_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_tag_group_id_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_tag_group_id_value)

        #search_text
        search_text = {"search_text": "test"}
        invalid_search_text_type = {"search_text": 123}

        result = FredHelpers.parameter_validation(search_text)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_search_text_type)

        #file_type
        file_type = {"file_type": "json"}
        invalid_file_type_type = {"file_type": 123}
        invalid_file_type_value = {"file_type": "xml"}

        result = FredHelpers.parameter_validation(file_type)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_file_type_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_file_type_value)

        #api_key
        api_key = {"api_key": "test_key"}
        invalid_api_key_type = {"api_key": 123}

        result = FredHelpers.parameter_validation(api_key)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_api_key_type)

        #include_releases_dates_with_no_data
        include_releases_dates_with_no_data = [
            {"include_releases_dates_with_no_data": True},
            {"include_releases_dates_with_no_data": False}
        ]
        invalid_include_releases_dates_with_no_data_type = {"include_releases_dates_with_no_data": 1}
        invalid_include_releases_dates_with_no_data_value = {"include_releases_dates_with_no_data": "yes"}

        for i in include_releases_dates_with_no_data:
            include_releases_dates_with_no_data_result = FredHelpers.parameter_validation(i)
            assert include_releases_dates_with_no_data_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_include_releases_dates_with_no_data_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_include_releases_dates_with_no_data_value)

        #release_id
        release_id = {"release_id": 1}
        invalid_release_id_type = {"release_id": "one"}
        invalid_release_id_value = {"release_id": -1}

        result = FredHelpers.parameter_validation(release_id)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_release_id_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_release_id_value)

        #series_id
        series_id = {"series_id": "test"}
        invalid_series_id_type = {"series_id": 123}
        invalid_series_id_value = {"series_id": "invalid_series"}
        invalid_series_id_empty = {"series_id": ""}
        invalid_series_id_whitespace = {"series_id": "t est"}

        result = FredHelpers.parameter_validation(series_id)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_series_id_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_series_id_value)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_series_id_empty)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_series_id_whitespace)

        #frequency
        frequency = [
            {"frequency": "d"},
            {"frequency": "w"},
            {"frequency": "bw"},
            {"frequency": "m"},
            {"frequency": "q"},
            {"frequency": "sa"},
            {"frequency": "a"},
            {"frequency": "wef"},
            {"frequency": "weth"},
            {"frequency": "wew"},
            {"frequency": "wetu"},
            {"frequency": "wem"},
            {"frequency": "wesu"},
            {"frequency": "wesa"},
            {"frequency": "bwew"},
            {"frequency": "bwem"},
        ]
        invalid_frequency_type = {"frequency": 1}
        invalid_frequency_value = {"frequency": "invalid_frequency"}

        for f in frequency:
            frequency_result = FredHelpers.parameter_validation(f)
            assert frequency_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_frequency_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_frequency_value)

        #units
        units = [
            {"units": "lin"},
            {"units": "chg"},
            {"units": "ch1"},
            {"units": "pch"},
            {"units": "pc1"},
            {"units": "pca"},
            {"units": "cch"},
            {"units": "cca"},
            {"units": "log"},
        ]
        invalid_units_type = {"units": 1}
        invalid_units_value = {"units": "invalid_units"}

        for u in units:
            units_result = FredHelpers.parameter_validation(u)
            assert units_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_units_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_units_value)

        #aggregation_method
        aggregation_method = [
            {"aggregation_method": "avg"},
            {"aggregation_method": "sum"},
            {"aggregation_method": "eop"},
        ]
        invalid_aggregation_method_type = {"aggregation_method": 1}
        invalid_aggregation_method_value = {"aggregation_method": "invalid_method"}

        for a in aggregation_method:
            aggregation_method_result = FredHelpers.parameter_validation(a)
            assert aggregation_method_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_aggregation_method_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_aggregation_method_value)

        #output_type
        output_type = [
            {"output_type": 1},
            {"output_type": 2},
            {"output_type": 3},
            {"output_type": 4},
        ]
        invalid_output_type = {"output_type": "one"}
        invalid_output_type_value = {"output_type": -1}

        for o in output_type:
            output_type_result = FredHelpers.parameter_validation(o)
            assert output_type_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_output_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_output_type_value)

        #vintage_dates
        vintage_dates = {"vintage_dates": "2023-01-01,2023-02-01,2023-03-01"}
        invalid_vintage_dates_type = {"vintage_dates": 123}
        invalid_vintage_dates_seperator = {"vintage_dates": "2023-01-01;2023-02-01;2023-03-01"}

        vintage_dates_result = FredHelpers.parameter_validation(vintage_dates)
        assert vintage_dates_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_vintage_dates_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_vintage_dates_seperator)

        #search_type
        search_type = [
            {"search_type": "full_text"},
            {"search_type": "series_id"},
        ]
        invalid_search_type = {"search_type": 1}
        invalid_search_type_value = {"search_type": "invalid_search"}

        for s in search_type:
            search_type_result = FredHelpers.parameter_validation(s)
            assert search_type_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_search_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_search_type_value)

        #tag_search_text
        tag_search_text = {"tag_search_text": "test"}
        invalid_tag_search_text_type = {"tag_search_text": 123}

        result = FredHelpers.parameter_validation(tag_search_text)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_tag_search_text_type)

        #start_time
        start_time = {"start_time": "12:30"}
        invalid_start_time = {"start_time": "25:00"}
        invalid_start_time_type = {"start_time": 123}

        start_time_result = FredHelpers.parameter_validation(start_time)
        assert start_time_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_start_time)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_start_time_type)

        #end_time
        end_time = {"end_time": "14:30"}
        invalid_end_time = {"end_time": "25:00"}
        invalid_end_time_type = {"end_time": 123}

        end_time_result = FredHelpers.parameter_validation(end_time)
        assert end_time_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_end_time)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_end_time_type)

        #season
        season = [
            {"season": "seasonally_adjusted"},
            {"season": "not_seasonally_adjusted"}
        ]
        invalid_season_type = {"season": 1}
        invalid_season_value = {"season": "invalid_season"}

        for s in season:
            season_result = FredHelpers.parameter_validation(s)
            assert season_result is None

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_season_type)

        with pytest.raises(ValueError):
            FredHelpers.parameter_validation(invalid_season_value)

    def test_geo_parameter_validation(self):
        """
        Test the geo_parameter_validation function.
        """

        #api_key
        api_key = {"api_key": "test_key"}
        invalid_api_key_type = {"api_key": 123}

        result = FredHelpers.geo_parameter_validation(api_key)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_api_key_type)

        #file_type
        file_type = {"file_type": "json"}
        invalid_file_type_type = {"file_type": 123}
        invalid_file_type_value = {"file_type": "xml"}

        result = FredHelpers.geo_parameter_validation(file_type)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_file_type_type)

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_file_type_value)

        #shape
        shape = [
            {"shape": "bea"},
            {"shape": "msa"},
            {"shape": "frb"},
            {"shape": "necta"},
            {"shape": "state"},
            {"shape": "country"},
            {"shape": "county"},
            {"shape": "censusregion"},
            {"shape": "censusdivision"}
        ]
        invalid_shape_type = {"shape": 123}
        invalid_shape_value = {"shape": "invalid_shape"}

        for s in shape:
            shape_result = FredHelpers.geo_parameter_validation(s)
            assert shape_result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_shape_type)

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_shape_value)

        #series_id
        series_id = {"series_id": "testseries"}
        invalid_series_id_type = {"series_id": 123}
        invalid_series_id_value = {"series_id": "invalid_series"}
        invalid_series_id_whitespace = {"series_id": "s eries"}
        invalid_series_id_empty = {"series_id": ""}

        result = FredHelpers.geo_parameter_validation(series_id)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_series_id_type)

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_series_id_value)

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_series_id_whitespace)

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_series_id_empty)

        #date
        date = {"date": "2023-01-01"}
        invalid_date = {"date": "2023-13-01"}
        invalid_date_type = {"date": 123}

        date_result = FredHelpers.geo_parameter_validation(date)
        assert date_result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_date)

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_date_type)

        #start_date
        start_date = {"start_date": "2023-01-01"}
        invalid_start_date = {"start_date": "2023-13-01"}
        invalid_start_date_type = {"start_date": 123}

        start_date_result = FredHelpers.geo_parameter_validation(start_date)
        assert start_date_result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_start_date)

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_start_date_type)

        #series_group
        series_group = {"series_group": "test_group"}
        invalid_series_group_type = {"series_group": 123}

        result = FredHelpers.geo_parameter_validation(series_group)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_series_group_type)

        #region_type
        region_type = {"region_type": "state"}
        invalid_region_type_type = {"region_type": 123}
        invalid_region_type_value = {"region_type": "invalid_region"}

        result = FredHelpers.geo_parameter_validation(region_type)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_region_type_type)

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_region_type_value)

        #aggregation_method
        aggregation_method = [
            {"aggregation_method": "sum"},
            {"aggregation_method": "avg"},
            {"aggregation_method": "eop"},
        ]
        invalid_aggregation_method_type = {"aggregation_method": 123}
        invalid_aggregation_method_value = {"aggregation_method": "invalid_method"}

        for a in aggregation_method:
            aggregation_method_result = FredHelpers.geo_parameter_validation(a)
            assert aggregation_method_result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_aggregation_method_type)

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_aggregation_method_value)

        #units
        units = {"units": "lin"}
        invalid_units_type = {"units": 123}

        result = FredHelpers.geo_parameter_validation(units)
        assert result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_units_type)

        #season
        season = [
            {"season": "NSA"},
            {"season": "SA"},
            {"season": "SSA"},
            {"season": "SAAR"},
            {"season": "NSAAR"}
        ]
        invalid_season_type = {"season": 123}
        invalid_season_value = {"season": "invalid_season"}

        for s in season:
            season_result = FredHelpers.geo_parameter_validation(s)
            assert season_result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_season_type)

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_season_value)

        #transformation
        transformation = [
            {"transformation": "lin"},
            {"transformation": "chg"},
            {"transformation": "ch1"},
            {"transformation": "pch"},
            {"transformation": "pc1"},
            {"transformation": "pca"},
            {"transformation": "cch"},
            {"transformation": "cca"},
            {"transformation": "log"},
        ]
        invalid_transformation_type = {"transformation": 123}
        invalid_transformation_value = {"transformation": "invalid_transformation"}

        for t in transformation:
            transformation_result = FredHelpers.geo_parameter_validation(t)
            assert transformation_result is None

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_transformation_type)

        with pytest.raises(ValueError):
            FredHelpers.geo_parameter_validation(invalid_transformation_value)

    @pytest.mark.asyncio
    async def test_datestring_validation_async(self):
        """
        Test the datestring_validation_async function.
        """

        valid_date = "2023-01-01"
        invalid_date = "2023-13-01"

        result = await FredHelpers.datestring_validation_async(valid_date)
        assert result is None

        with pytest.raises(ValueError):
            result = await FredHelpers.datestring_validation_async(invalid_date)

    @pytest.mark.asyncio
    async def test_liststring_validation_async(self):
        """
        Test the liststrings_validation_async function.
        """

        valid_liststring = "a;b;c"
        invalid_type = 123
        invalid_liststring_terms = "a;b;%"
        invalid_liststring_seperator = "a,b,c"
        invalid_liststring_empty = "a;;b;c"
        invalid_liststring_whitespace = " a ; b ; c "

        result = await FredHelpers.liststring_validation_async(valid_liststring)
        assert result is None

        with pytest.raises(ValueError):
            result = await FredHelpers.liststring_validation_async(invalid_type)

        with pytest.raises(ValueError):
            result = await FredHelpers.liststring_validation_async(invalid_liststring_terms)

        with pytest.raises(ValueError):
            result = await FredHelpers.liststring_validation_async(invalid_liststring_seperator)

        with pytest.raises(ValueError):
            result = await FredHelpers.liststring_validation_async(invalid_liststring_empty)

        with pytest.raises(ValueError):
            result = await FredHelpers.liststring_validation_async(invalid_liststring_whitespace)

    @pytest.mark.asyncio
    async def test_vintage_dates_validation_async(self):
        """
        Test the vintage_dates_validation_async function.
        """

        valid_vintage_list = "2023-01-01,2023-02-01,2023-03-01"
        invalid_vintage_list_seperator = "2023-01-01;2023-02-01;2023-03-01"
        invalid_vintage_list_empty = ""
        invalid_type = 123

        result = await FredHelpers.vintage_dates_validation_async(valid_vintage_list)
        assert result is None

        with pytest.raises(ValueError):
            result = await FredHelpers.vintage_dates_validation_async(invalid_type)

        with pytest.raises(ValueError):
            result = await FredHelpers.vintage_dates_validation_async(invalid_vintage_list_seperator)

        with pytest.raises(ValueError):
            result = await FredHelpers.vintage_dates_validation_async(invalid_vintage_list_empty)

    @pytest.mark.asyncio
    async def test_hh_mm_datestring_validation_async(self):
        """
        Test the hh_mm_datestring_validation_async function.
        """

        valid_hh_mm = "12:30"
        invalid_hh_mm = "25:00"
        invalid_type = 123

        result = await FredHelpers.hh_mm_datestring_validation_async(valid_hh_mm)
        assert result is None

        with pytest.raises(ValueError):
            result = await FredHelpers.hh_mm_datestring_validation_async(invalid_hh_mm)

        with pytest.raises(ValueError):
            result = await FredHelpers.hh_mm_datestring_validation_async(invalid_type)

    @pytest.mark.asyncio
    async def test_parameter_validation_async(self):
        """
        Test the parameter_validation_async function.
        """

        #category_id
        category_id = {"category_id": 1}
        invalid_category_id_type = {"category_id": "one"}
        invalid_category_id_value = {"category_id": -1}

        category_id_result = await FredHelpers.parameter_validation_async(category_id)
        assert category_id_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_category_id_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_category_id_value)

        #realtime_start
        realtime_start = {"realtime_start": "2023-01-01"}
        invalid_realtime_start = {"realtime_start": "2023-13-01"}
        invalid_realtime_start_type = {"realtime_start": 123}

        realtime_start_result = await FredHelpers.parameter_validation_async(realtime_start)
        assert realtime_start_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_realtime_start)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_realtime_start_type)

        #realtime_end
        realtime_end = {"realtime_end": "2023-01-31"}
        invalid_realtime_end = {"realtime_end": "2023-13-01"}
        invalid_realtime_end_type = {"realtime_end": 123}

        realtime_end_result = await FredHelpers.parameter_validation_async(realtime_end)
        assert realtime_end_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_realtime_end)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_realtime_end_type)

        #limit
        limit = {"limit": 100}
        invalid_limit_type = {"limit": "one"}
        invalid_limit_value = {"limit": -1}

        limit_result = await FredHelpers.parameter_validation_async(limit)
        assert limit_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_limit_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_limit_value)

        #offset
        offset = {"offset": 1}
        invalid_offset_type = {"offset": "one"}
        invalid_offset_value = {"offset": -1}

        offset_result = await FredHelpers.parameter_validation_async(offset)
        assert offset_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_offset_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_offset_value)

        #sort_order
        sort_order = [{"sort_order": "asc"}, {"sort_order": "desc"}]
        invalid_sort_order_type = {"sort_order": 1}
        invalid_sort_order_value = {"sort_order": "ascending"}

        for s in sort_order:
            sort_order_result = await FredHelpers.parameter_validation_async(s)
            assert sort_order_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_sort_order_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_sort_order_value)

        #order_by
        order_by = [
            {"order_by": "series_id"},
            {"order_by": "title"},
            {"order_by": "units"},
            {"order_by": "frequency"},
            {"order_by": "seasonal_adjustment"},
            {"order_by": "realtime_start"},
            {"order_by": "realtime_end"},
            {"order_by": "last_updated"},
            {"order_by": "observation_start"},
            {"order_by": "observation_end"},
            {"order_by": "popularity"},
            {"order_by": "group_popularity"},
            {"order_by": "series_count"},
            {"order_by": "created"},
            {"order_by": "name"},
            {"order_by": "release_id"},
            {"order_by": "press_release"},
            {"order_by": "group_id"},
            {"order_by": "search_rank"},
            {"order_by": "title"},
            ]
        invalid_order_by_type = {"order_by": 1}
        invalid_order_by_value = {"order_by": "invalid_column"}

        for o in order_by:
            order_by_result = await FredHelpers.parameter_validation_async(o)
            assert order_by_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_order_by_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_order_by_value)

        #filter_variable
        filter_variable = [
            {"filter_variable": "frequency"},
            {"filter_variable": "units"},
            {"filter_variable": "seasonal_adjustment"},
        ]
        invalid_filter_variable_type = {"filter_variable": 1}
        invalid_filter_variable_value = {"filter_variable": "invalid_variable"}

        for f in filter_variable:
            filter_variable_result = await FredHelpers.parameter_validation_async(f)
            assert filter_variable_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_filter_variable_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_filter_variable_value)

        #filter_value
        filter_value = {"filter_value": "value1"}
        invalid_filter_value_type = {"filter_value": 1}

        filter_value_result = await FredHelpers.parameter_validation_async(filter_value)
        assert filter_value_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_filter_value_type)

        #tag_names
        tag_names = {"tag_names": "tag1;tag2;tag3"}
        invalid_tag_names_type = {"tag_names": 1}
        invalid_tag_names_value = {"tag_names": "tag1,tag2,tag3"}

        tag_names_result = await FredHelpers.parameter_validation_async(tag_names)
        assert tag_names_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_tag_names_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_tag_names_value)

        #exclude_tag_names
        exclude_tag_names = {"exclude_tag_names": "tag1;tag2;tag3"}
        invalid_exclude_tag_names_type = {"exclude_tag_names": 1}
        invalid_exclude_tag_names_value = {"exclude_tag_names": "tag1,tag2,tag3"}

        exclude_tag_names_result = await FredHelpers.parameter_validation_async(exclude_tag_names)
        assert exclude_tag_names_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_exclude_tag_names_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_exclude_tag_names_value)

        #tag_group_id
        tag_group_id = [
            {"tag_group_id": 1},
            {"tag_group_id": "one"},
        ]
        invalid_tag_group_id_type = {"tag_group_id": [1, 2, 3]}
        invalid_tag_group_id_value = {"tag_group_id": -1}

        for t in tag_group_id:
            tag_group_id_result = await FredHelpers.parameter_validation_async(t)
            assert tag_group_id_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_tag_group_id_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_tag_group_id_value)

        #search_text
        search_text = {"search_text": "test"}
        invalid_search_text_type = {"search_text": 123}

        result = await FredHelpers.parameter_validation_async(search_text)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_search_text_type)

        #file_type
        file_type = {"file_type": "json"}
        invalid_file_type_type = {"file_type": 123}
        invalid_file_type_value = {"file_type": "xml"}

        result = await FredHelpers.parameter_validation_async(file_type)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_file_type_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_file_type_value)

        #api_key
        api_key = {"api_key": "test_key"}
        invalid_api_key_type = {"api_key": 123}

        result = await FredHelpers.parameter_validation_async(api_key)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_api_key_type)

        #include_releases_dates_with_no_data
        include_releases_dates_with_no_data = [
            {"include_releases_dates_with_no_data": True},
            {"include_releases_dates_with_no_data": False}
        ]
        invalid_include_releases_dates_with_no_data_type = {"include_releases_dates_with_no_data": 1}
        invalid_include_releases_dates_with_no_data_value = {"include_releases_dates_with_no_data": "yes"}

        for i in include_releases_dates_with_no_data:
            include_releases_dates_with_no_data_result = await FredHelpers.parameter_validation_async(i)
            assert include_releases_dates_with_no_data_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_include_releases_dates_with_no_data_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_include_releases_dates_with_no_data_value)

        #release_id
        release_id = {"release_id": 1}
        invalid_release_id_type = {"release_id": "one"}
        invalid_release_id_value = {"release_id": -1}

        result = await FredHelpers.parameter_validation_async(release_id)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_release_id_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_release_id_value)

        #series_id
        series_id = {"series_id": "test"}
        invalid_series_id_type = {"series_id": 123}
        invalid_series_id_value = {"series_id": "invalid_series"}
        invalid_series_id_empty = {"series_id": ""}
        invalid_series_id_whitespace = {"series_id": "t est"}

        result = await FredHelpers.parameter_validation_async(series_id)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_series_id_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_series_id_value)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_series_id_empty)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_series_id_whitespace)

        #frequency
        frequency = [
            {"frequency": "d"},
            {"frequency": "w"},
            {"frequency": "bw"},
            {"frequency": "m"},
            {"frequency": "q"},
            {"frequency": "sa"},
            {"frequency": "a"},
            {"frequency": "wef"},
            {"frequency": "weth"},
            {"frequency": "wew"},
            {"frequency": "wetu"},
            {"frequency": "wem"},
            {"frequency": "wesu"},
            {"frequency": "wesa"},
            {"frequency": "bwew"},
            {"frequency": "bwem"},
        ]
        invalid_frequency_type = {"frequency": 1}
        invalid_frequency_value = {"frequency": "invalid_frequency"}

        for f in frequency:
            frequency_result = await FredHelpers.parameter_validation_async(f)
            assert frequency_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_frequency_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_frequency_value)

        #units
        units = [
            {"units": "lin"},
            {"units": "chg"},
            {"units": "ch1"},
            {"units": "pch"},
            {"units": "pc1"},
            {"units": "pca"},
            {"units": "cch"},
            {"units": "cca"},
            {"units": "log"},
        ]
        invalid_units_type = {"units": 1}
        invalid_units_value = {"units": "invalid_units"}

        for u in units:
            units_result = await FredHelpers.parameter_validation_async(u)
            assert units_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_units_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_units_value)

        #aggregation_method
        aggregation_method = [
            {"aggregation_method": "avg"},
            {"aggregation_method": "sum"},
            {"aggregation_method": "eop"},
        ]
        invalid_aggregation_method_type = {"aggregation_method": 1}
        invalid_aggregation_method_value = {"aggregation_method": "invalid_method"}

        for a in aggregation_method:
            aggregation_method_result = await FredHelpers.parameter_validation_async(a)
            assert aggregation_method_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_aggregation_method_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_aggregation_method_value)

        #output_type
        output_type = [
            {"output_type": 1},
            {"output_type": 2},
            {"output_type": 3},
            {"output_type": 4},
        ]
        invalid_output_type = {"output_type": "one"}
        invalid_output_type_value = {"output_type": -1}

        for o in output_type:
            output_type_result = await FredHelpers.parameter_validation_async(o)
            assert output_type_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_output_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_output_type_value)

        #vintage_dates
        vintage_dates = {"vintage_dates": "2023-01-01,2023-02-01,2023-03-01"}
        invalid_vintage_dates_type = {"vintage_dates": 123}
        invalid_vintage_dates_seperator = {"vintage_dates": "2023-01-01;2023-02-01;2023-03-01"}

        vintage_dates_result = await FredHelpers.parameter_validation_async(vintage_dates)
        assert vintage_dates_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_vintage_dates_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_vintage_dates_seperator)

        #search_type
        search_type = [
            {"search_type": "full_text"},
            {"search_type": "series_id"},
        ]
        invalid_search_type = {"search_type": 1}
        invalid_search_type_value = {"search_type": "invalid_search"}

        for s in search_type:
            search_type_result = await FredHelpers.parameter_validation_async(s)
            assert search_type_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_search_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_search_type_value)

        #tag_search_text
        tag_search_text = {"tag_search_text": "test"}
        invalid_tag_search_text_type = {"tag_search_text": 123}

        result = await FredHelpers.parameter_validation_async(tag_search_text)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_tag_search_text_type)

        #start_time
        start_time = {"start_time": "12:30"}
        invalid_start_time = {"start_time": "25:00"}
        invalid_start_time_type = {"start_time": 123}

        start_time_result = await FredHelpers.parameter_validation_async(start_time)
        assert start_time_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_start_time)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_start_time_type)

        #end_time
        end_time = {"end_time": "14:30"}
        invalid_end_time = {"end_time": "25:00"}
        invalid_end_time_type = {"end_time": 123}

        end_time_result = await FredHelpers.parameter_validation_async(end_time)
        assert end_time_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_end_time)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_end_time_type)

        #season
        season = [
            {"season": "seasonally_adjusted"},
            {"season": "not_seasonally_adjusted"}
        ]
        invalid_season_type = {"season": 1}
        invalid_season_value = {"season": "invalid_season"}

        for s in season:
            season_result = await FredHelpers.parameter_validation_async(s)
            assert season_result is None

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_season_type)

        with pytest.raises(ValueError):
            await FredHelpers.parameter_validation_async(invalid_season_value)

    @pytest.mark.asyncio
    async def test_geo_parameter_validation_async(self):
        """
        Test the geo_parameter_validation_async function.
        """

        #api_key
        api_key = {"api_key": "test_key"}
        invalid_api_key_type = {"api_key": 123}

        result = await FredHelpers.geo_parameter_validation_async(api_key)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_api_key_type)

        #file_type
        file_type = {"file_type": "json"}
        invalid_file_type_type = {"file_type": 123}
        invalid_file_type_value = {"file_type": "xml"}

        result = await FredHelpers.geo_parameter_validation_async(file_type)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_file_type_type)

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_file_type_value)

        #shape
        shape = [
            {"shape": "bea"},
            {"shape": "msa"},
            {"shape": "frb"},
            {"shape": "necta"},
            {"shape": "state"},
            {"shape": "country"},
            {"shape": "county"},
            {"shape": "censusregion"},
            {"shape": "censusdivision"}
        ]
        invalid_shape_type = {"shape": 123}
        invalid_shape_value = {"shape": "invalid_shape"}

        for s in shape:
            shape_result = await FredHelpers.geo_parameter_validation_async(s)
            assert shape_result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_shape_type)

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_shape_value)

        #series_id
        series_id = {"series_id": "testseries"}
        invalid_series_id_type = {"series_id": 123}
        invalid_series_id_value = {"series_id": "invalid_series"}
        invalid_series_id_whitespace = {"series_id": "s eries"}
        invalid_series_id_empty = {"series_id": ""}

        result = await FredHelpers.geo_parameter_validation_async(series_id)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_series_id_type)

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_series_id_value)

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_series_id_whitespace)

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_series_id_empty)

        #date
        date = {"date": "2023-01-01"}
        invalid_date = {"date": "2023-13-01"}
        invalid_date_type = {"date": 123}

        date_result = await FredHelpers.geo_parameter_validation_async(date)
        assert date_result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_date)

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_date_type)

        #start_date
        start_date = {"start_date": "2023-01-01"}
        invalid_start_date = {"start_date": "2023-13-01"}
        invalid_start_date_type = {"start_date": 123}

        start_date_result = await FredHelpers.geo_parameter_validation_async(start_date)
        assert start_date_result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_start_date)

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_start_date_type)

        #series_group
        series_group = {"series_group": "test_group"}
        invalid_series_group_type = {"series_group": 123}

        result = await FredHelpers.geo_parameter_validation_async(series_group)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_series_group_type)

        #region_type
        region_type = {"region_type": "state"}
        invalid_region_type_type = {"region_type": 123}
        invalid_region_type_value = {"region_type": "invalid_region"}

        result = await FredHelpers.geo_parameter_validation_async(region_type)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_region_type_type)

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_region_type_value)

        #aggregation_method
        aggregation_method = [
            {"aggregation_method": "sum"},
            {"aggregation_method": "avg"},
            {"aggregation_method": "eop"},
        ]
        invalid_aggregation_method_type = {"aggregation_method": 123}
        invalid_aggregation_method_value = {"aggregation_method": "invalid_method"}

        for a in aggregation_method:
            aggregation_method_result = await FredHelpers.geo_parameter_validation_async(a)
            assert aggregation_method_result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_aggregation_method_type)

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_aggregation_method_value)

        #units
        units = {"units": "lin"}
        invalid_units_type = {"units": 123}

        result = await FredHelpers.geo_parameter_validation_async(units)
        assert result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_units_type)

        #season
        season = [
            {"season": "NSA"},
            {"season": "SA"},
            {"season": "SSA"},
            {"season": "SAAR"},
            {"season": "NSAAR"}
        ]
        invalid_season_type = {"season": 123}
        invalid_season_value = {"season": "invalid_season"}

        for s in season:
            season_result = await FredHelpers.geo_parameter_validation_async(s)
            assert season_result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_season_type)

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_season_value)

        #transformation
        transformation = [
            {"transformation": "lin"},
            {"transformation": "chg"},
            {"transformation": "ch1"},
            {"transformation": "pch"},
            {"transformation": "pc1"},
            {"transformation": "pca"},
            {"transformation": "cch"},
            {"transformation": "cca"},
            {"transformation": "log"},
        ]
        invalid_transformation_type = {"transformation": 123}
        invalid_transformation_value = {"transformation": "invalid_transformation"}

        for t in transformation:
            transformation_result = await FredHelpers.geo_parameter_validation_async(t)
            assert transformation_result is None

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_transformation_type)

        with pytest.raises(ValueError):
            await FredHelpers.geo_parameter_validation_async(invalid_transformation_value)
