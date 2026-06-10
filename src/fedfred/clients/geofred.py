# filepath: /src/fedfred/clients/geofred.py
#
# Copyright (c) 2026 Nikhil Sunder
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
"""fedfred.clients.geofred

This module defines the GeoFred client for interacting with the Federal Reserve FRED Maps API.


It provides synchronous and asynchronous methods to access various endpoints of the FRED Maps API, including
series groups. The client includes features such as automatic parameter conversion, unified response objects,
rate limiting, retries, and typed results.

Classes:
    GeoFred: Client for the Federal Reserve FRED Maps API.
    AsyncGeoFred: Asychronous client for Federal Reserve FRED Maps API.

Examples:
    >>> import fedfred as fd
    >>> geofred = fd.GeoFred('your_api_key')
    >>> series_group = geofred.get_series_group('SMU56000000500000001')
    >>> print(series_group[0].title)
    'State Personal Income'
"""

from __future__ import annotations

import asyncio
from collections.abc import KeysView
from datetime import date, datetime
from types import TracebackType
from typing import TYPE_CHECKING, Any

import geopandas as gpd

from ..._core import (
    _CACHE,
    # Rate Limit
    _FRED_MAX_REQUESTS_PER_MINUTE,
    _GEOFRED_PATH,
    # Endpoints
    _ST_LOUIS_FED_BASE_URL,
    ASYNC_GEODATAFRAME_CONVERTER_MAP,
    GEODATAFRAME_CONVERTER_MAP,
    _cached_get_request_async,
    # Transport
    _get_request_async,
    # Converters
    _hashable_type_converter_async,
    # Parsers
    _region_type_parser,
    _region_type_parser_async,
    get_cache_maxsize,
    # Caching
    set_cache_maxsize,
)
from ...models import SeriesGroup
from ...settings import _resolve_api_key, set_api_key
from .._internals import _AsyncBaseClient, _BaseClient

if TYPE_CHECKING:
    import dask_geopandas as dd_gpd  # pragma: no cover
    import polars_st as st  # pragma: no cover

# TODO: Fix all docstrings post error design.

__all__ = ["AsyncGeoFred", "GeoFred"]


class GeoFred(_BaseClient):
    """Client for interacting with the Federal Reserve Economic Data (FRED) Maps API.

    The GeoFred class provides methods to interact with the FRED Maps API, which offers geospatial
    data and maps related to economic indicators. This class extends the functionality of the Fred
    class by adding specific methods for handling geospatial data and maps.

    Attributes:
        cache_mode (bool): Whether to enable caching of API responses.
        cache (FIFOCache): The cache used to store API responses.
        base_url (str): The base URL for the FRED Maps API.

    Args:
        parent (Fred): The parent Fred instance that this MapsAPI instance is associated with.

    Raises:
        ValueError: If the parent instance is not an instance of Fred.

    Notes:
        The GeoFred class is designed to work in conjunction with the Fred class, providing a more specialized interface for
        accessing geospatial data and maps from the FRED API. It leverages the caching and rate-limiting mechanisms of the
        parent Fred instance to ensure efficient and reliable access to geospatial data and maps.

    Examples:
        >>> import fedfred as fd
        >>> fred = fd.Fred('your_api_key')
        >>> # Use GeoFred property to access geospatial data and maps from the FRED API
        >>> fred_maps = fred.GeoFred
        >>> # Also acceptable to initialize directly with a Fred instance
        >>> fred_maps = fd.GeoFred(fred)

    Warnings:
        Ensure that the parent Fred instance is properly configured with the necessary API key and other parameters.

    See Also:
        - :class:`fedfred.Fred`: The parent class for interacting with the FRED API.
        - :class:`fedfred.Helpers`: Helper methods for the FRED API.
    """

    # Public Methods
    def get_shape_files(
        self, shape: str, geodataframe_method: str = "geopandas"
    ) -> gpd.GeoDataFrame | dd_gpd.GeoDataFrame | st.GeoDataFrame:
        """Get GeoFRED shape files

        This request returns shape files from FRED Maps in GeoJSON format.

        Args:
            shape (str, required): The type of shape you want to pull GeoJSON data for. Available Shape Types: 'bea' (Bureau of Economic Anaylis Region), 'msa' (Metropolitan Statistical Area), 'frb' (Federal Reserve Bank Districts), 'necta' (New England City and Town Area), 'state', 'country', 'county' (USA Counties), 'censusregion' (US Census Regions), 'censusdivision' (US Census Divisons).
            geodataframe_method (str, optional): The method to use for creating the GeoDataFrame. Options are 'geopandas', 'dask' or 'polars'. Default is 'geopandas'.

        Returns:
            geopandas.GeoDataFrame | dask_geopandas.GeoDataFrame | polars_st.GeoDataFrame: Depending on the geodataframe_method selected. Default is geopandas.GeoDataFrame.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').GeoFred
            >>> shapefile = fred.get_shape_files('state')
            >>> print(shapefile.head())
                                                        geometry  ...   type
            0  MULTIPOLYGON (((9727 7650, 10595 7650, 10595 7...  ...  State
            1  MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...  ...  State
            2  POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...  ...  State
            3  POLYGON ((-50 7955, -833 8186, -851 8223, -847...  ...  State
            4  MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...  ...  State
            [5 rows x 20 columns]

        See Also:
            - :class:`fedfred.Helpers`: Helper methods for parameter validation and conversion.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/geofred/shapes.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.GeoFred.get_shape_files.html
        """
        endpoint_name = "get_shapes_file"

        data: dict[str, Any] = {"shape": shape}

        response = self.__geofred_get_request(endpoint_name, data)

        # ----------------------------Needs-Abstraction-----------------------------------------------------------------
        if geodataframe_method == "geopandas":
            return gpd.GeoDataFrame.from_features(response["features"])
        elif geodataframe_method == "dask":
            gdf = gpd.GeoDataFrame.from_features(response["features"])
            try:  # TODO: Optional Import logic needs to be relegated to a helper
                import dask_geopandas as dd_gpd

                return dd_gpd.from_geopandas(gdf, npartitions=1)
            except ImportError as e:  # TODO: Needs exception hierarchy defined Error Class
                raise ImportError(
                    f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method."
                ) from e
        elif geodataframe_method == "polars":
            gdf = gpd.GeoDataFrame.from_features(response["features"])
            try:
                import polars_st as st

                return st.from_geopandas(gdf)
            except ImportError as e:
                raise ImportError(
                    f"{e}: Polars is not installed. Install it with `pip install polars` to use this method."
                ) from e
        else:
            raise ValueError(
                "geodataframe_method must be 'geopandas', 'dask', or 'polars'"
            )  # TODO: Custom Error class
        # ------------------------------------------------------------------------------------------------------------

    def get_series_group(self, series_id: str) -> list[SeriesGroup]:
        """Get a GeoFRED series group

        This request returns the meta information needed to make requests for FRED data. Minimum
        and maximum date are also supplied for the data range available.

        Args:
            series_id (str, required): The FRED series id you want to request maps meta information for. Not all series that are in FRED have geographical data.

        Returns:
            List[SeriesGroup]: If multiple series groups are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').GeoFred
            >>> series_group = fred.get_series_group('SMU56000000500000001')
            >>> print(series_group[0].title)
            'State Personal Income'

        See Also:
            - :class:`fedfred.SeriesGroup`: The SeriesGroup object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/geofred/series_group.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.GeoFred.get_series_group.html
        """
        endpoint_name = "get_series_group"

        data: dict[str, Any] = {"series_id": series_id, "file_type": "json"}

        response = self.__geofred_get_request(endpoint_name, data)

        return SeriesGroup.to_object(response)

    def get_series_data(
        self,
        series_id: str,
        geodataframe_method: str = "geopandas",
        date: str | datetime | date | None = None,
        start_date: str | datetime | date | None = None,
    ) -> gpd.GeoDataFrame | dd_gpd.GeoDataFrame | st.GeoDataFrame:
        """Get GeoFRED series data

        This request returns a cross section of regional data for a specified release date. If no date is specified, the most recent data available are returned.

        Args:
            series_id (string, required): The FRED series_id you want to request maps data for. Not all series that are in FRED have geographical data.
            geodataframe_method (str, optional): The method to use for creating the GeoDataFrame. Options are 'geopandas' 'polars', or 'dask'. Default is 'geopandas'.
            date (string | datetime, optional): The date you want to request series group data from. String format: YYYY-MM-DD
            start_date (string | datetime, optional): The start date you want to request series group data from. This allows you to pull a range of data. String format: YYYY-MM-DD

        Returns:
            - geopandas.GeoDataFrame
            - dask_geopandas.GeoDataFrame
            - polars_st.GeoDataFrame: Depending on the geodataframe_method selected. Default is geopandas.GeoDataFrame.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').GeoFred
            >>> series_data = fred.get_series_data('SMU56000000500000001')
            >>> print(series_data.head())
            name                                                    geometry  ...             series_id
            Washington     MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...  ...  SMU53000000500000001
            California     POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...  ...  SMU06000000500000001
            Oregon         POLYGON ((-50 7955, -833 8186, -851 8223, -847...  ...  SMU41000000500000001
            Wisconsin      MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...  ...  SMU55000000500000001

        See Also:
            - :class:`fedfred.Helpers`: Helper methods for parameter validation and conversion.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/geofred/series_data.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.GeoFred.get_series_data.html
        """
        endpoint_name = "get_series_data"

        data: dict[str, Any] = {
            "series_id": series_id,
            "file_type": "json",
            "date": date,
            "start_date": start_date,
        }

        # ----------------------------Needs-Abstraction-----------------------------------------------------------------
        response = self.__geofred_get_request(endpoint_name, data)
        meta_data = response.get("meta", {})
        region_type = _region_type_parser(response)
        shapefile = self.get_shape_files(region_type)
        # --------------------------------------------------------------------------------------------------------------

        if isinstance(
            shapefile, gpd.GeoDataFrame
        ):  # TODO: Slight logic fix (No front end validation)
            try:
                return GEODATAFRAME_CONVERTER_MAP[geodataframe_method](shapefile, meta_data)
            except Exception as exc:
                raise ValueError(
                    "geodataframe_method must be 'geopandas', 'polars', or 'dask'"
                ) from exc  # TODO: Needs custom Error handling exception hierarchy.
        else:
            raise ValueError(
                "shapefile type error"
            )  # TODO: Needs custom Error handling exception hierarchy.

    def get_regional_data(
        self,
        series_group: str,
        region_type: str,
        date: str | datetime | date,
        season: str,
        units: str,
        frequency: str,
        geodataframe_method: str = "geopandas",
        start_date: str | datetime | date | None = None,
        transformation: str | None = None,
        aggregation_method: str | None = None,
    ) -> gpd.GeoDataFrame | dd_gpd.GeoDataFrame | st.GeoDataFrame:
        """Get GeoFRED regional data

        Retrieve regional data for a specified series group and date from the FRED Maps API.

        Args:
            series_group (str): The series group for which you want to request regional data.
            region_type (str): The type of region for which you want to request data. Options are 'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', or 'censusdivision'.
            date (str | datetime): The date for which you want to request regional data. String format: YYYY-MM-DD.
            season (str): The seasonality of the data. Options include 'seasonally_adjusted' or 'not_seasonally_adjusted'.
            units (str): The units of the data. Options are 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca' and 'log'.
            frequency (str): The frequency of the data. Options are 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew'and 'bwem'.
            geodataframe_method (str, optional): The method to use for creating the GeoDataFrame. Options are 'geopandas', 'dask' or 'polars'. Default is 'geopandas'.
            start_date (str, optional): The start date for the range of data you want to request. Format: YYYY-MM-DD.
            transformation (str, optional): The data transformation to apply. Options are 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', and 'log'.
            aggregation_method (str, optional): The aggregation method to use. Options are 'avg', 'sum', and 'eop'.

        Returns:
            - geopandas.GeoDataFrame
            - dask_geopandas.GeoDataFrame
            - polars_st.GeoDataFrame: Depending on the geodataframe_method selected. Default is geopandas.GeoDataFrame.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').GeoFred
            >>> regional_data = fred.get_regional_data(series_group='882', date='2013-01-01', region_type='state', units='Dollars', frequency='a', season='NSA')
            >>> print(regional_data.head())
            name                                                    geometry hc-group  ...  value  series_id
            Massachusetts  MULTIPOLYGON (((9727 7650, 10595 7650, 10595 7...   admin1  ...  56119     MAPCPI
            Washington     MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...   admin1  ...  47448     WAPCPI
            California     POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...   admin1  ...  48074     CAPCPI
            Oregon         POLYGON ((-50 7955, -833 8186, -851 8223, -847...   admin1  ...  39462     ORPCPI
            Wisconsin      MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...   admin1  ...  42685     WIPCPI
            [5 rows x 21 columns]

        See Also:
            - :class:`fedfred.Helpers`: Helper methods for parameter validation and conversion.

        References:
            Fred API Documentation: https://fred.stlouisfed.org/docs/api/geofred/regional_data.html
            fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.GeoFred.get_regional_data.html
        """
        endpoint_name = "get_regional_data"

        data: dict[str, Any] = {
            "series_group": series_group,
            "region_type": region_type,
            "date": date,
            "season": season,
            "units": units,
            "frequency": frequency,
            "file_type": "json",
            "start_date": start_date,
            "transformation": transformation,
            "aggregation_method": aggregation_method,
        }

        # ----------------------------Needs-Abstraction-----------------------------------------------------------------
        response = self.__geofred_get_request(endpoint_name, data)
        meta_data = response.get("meta", {})
        region_type = _region_type_parser(response)
        shapefile = self.get_shape_files(region_type)
        # --------------------------------------------------------------------------------------------------------------

        if isinstance(
            shapefile, gpd.GeoDataFrame
        ):  # TODO: Slight logic fix (No front end validation)
            try:
                return GEODATAFRAME_CONVERTER_MAP[geodataframe_method](shapefile, meta_data)
            except Exception as exc:
                raise ValueError(
                    "geodataframe_method must be 'geopandas', 'polars', or 'dask'"
                ) from exc  # TODO: Needs custom Error handling exception hierarchy.
        else:
            raise ValueError(
                "shapefile type error"
            )  # TODO: Needs custom Error handling exception hierarchy.


class AsyncGeoFred(_AsyncBaseClient):
    """Asynchronous client for interacting with the Federal Reserve Economic Data (FRED) Maps API.

    The AsyncGeoFred class provides methods to access various endpoints of the FRED Maps API asynchronously.
    It is designed to be used as part of the AsyncFred client.

    Attributes:
        cache_mode (bool): Indicates whether caching is enabled.
        cache (FIFOCache): The cache instance for storing API responses.
        base_url (str): The base URL for the FRED Maps API.

    Args:
        parent (AsyncFred): The parent AsyncFred instance.

    Raises:
        ValueError: If the parent is not a valid AsyncFred instance.

    Notes:
        The AsyncGeoFred class is intended to be used as a sub-client of the AsyncFred class. It should
        not be instantiated directly. Instead, access it via the AsyncGeoFred property of the AsyncFred
        instance.

    Examples:
        >>> import fedfred as fd
        >>> import asyncio
        >>> async def main():
        >>>     fred = fd.Fred('your_api_key').AsyncFred
        >>>     # Use AsyncGeoFred property to access geospatial data and maps asynchronously from the FRED API
        >>>     maps_api = fred.AsyncGeoFred
        >>>     # Also acceptable to initialize directly with a Fred instance
        >>>     maps_api = fd.AsyncGeoFred(fred)

    Warnings:
        Ensure that the parent AsyncFred instance is properly initialized before accessing the AsyncGeoFred.

    See Also:
        - :class:`fedfred.AsyncFred`: The parent asynchronous FRED API client.
        - :class:`fedfred.Fred`: The synchronous FRED API client
    """

    # Dunder Methods
    def __init__(
        self, api_key: str | None = None, caching_enabled: bool = True, cache_size: int = 256
    ) -> None:
        """Initialize with a reference to the parent AsyncFred instance and the grandparent Fred instance.

        Args:
            parent (AsyncFred): The parent AsyncFred instance.

        Raises:
            ValueError: If the parent is not a valid AsyncFred instance.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred
            >>>     maps_api = fred.AsyncGeoFred
            >>>     # Also acceptable to initialize directly with a Fred instance
            >>>     maps_api = fd.AsyncGeoFred(fred)
            >>> asyncio.run(main())

        Notes:
            The AsyncGeoFred class is intended to be used as a sub-client of the AsyncFred class. It should
            not be instantiated directly. Instead, access it via the AsyncGeoFred property of the AsyncFred
            instance.

        See Also:
            - :class:`fedfred.AsyncFred`: The parent asynchronous FRED API client.
            - :class:`fedfred.Fred`: The synchronous FRED API client
            - :func:`fedfred.set_api_key`: Function to set the API key for FRED API access.
        """
        if api_key:
            set_api_key(api_key, service="fred")

        if caching_enabled:
            set_cache_maxsize(cache_size)

        self.caching_enabled: bool = caching_enabled
        self.cache_size: int = get_cache_maxsize() if caching_enabled else cache_size

    def __repr__(self) -> str:
        """String representation of the AsyncGeoFred class.

        Returns:
            str: String representation of the AsyncGeoFred instance.

        Notes:
            The string representation includes the parent AsyncFred instance's string representation, the grandparent
            Fred instance's string representation, and the AsyncGeoFred instance's string representation.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key', cache_mode=True, cache_size=256).AsyncFred
            >>> maps_api = fred.AsyncGeoFred
            >>> print(repr(maps_api))
            'Fred(api_key='your_api_key', cache_mode=True, cache_size=256).AsyncFred(base_url=https://api.stlouisfed.org/fred/).AsyncGeoFred(base_url=https://api.stlouisfed.org/fred/maps/)'
        """
        try:
            has_key = bool(_resolve_api_key(service="geofred"))
        except (
            RuntimeError
        ):  # TODO: Add custom exception for missing API key and catch that instead.
            has_key = False

        auth = "<set>" if has_key else "None"

        # TODO: include size of instance object in the repr string for debugging purposes (can use sys.getsizeof() for that).

        return (
            f"{type(self).__name__}("
            f"api_key={auth}, "
            f"caching_enabled={self.caching_enabled}, "
            f"cache_size={self.cache_size}"
            f")"
        )

    def __str__(self) -> str:
        """String representation of the AsyncGeoFred class.

        Returns:
            str: String representation of the AsyncGeoFred instance.

        Notes:
            The string representation includes the parent AsyncFred instance's string representation, the grandparent
            Fred instance's string representation, and the AsyncGeoFred instance's string representation.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').AsyncFred
            >>> maps_api = fred.AsyncGeoFred
            >>> print(str(maps_api))
            'Fred Instance:'
            '  Base URL: https://api.stlouisfed.org/fred'
            '  API Key: ****your_api_key'
            '  Cache Mode: Enabled'
            '  Cache Size: 256 items'
            '  Max Requests per Minute: 120'
            '  AsyncFred Instance:'
            '    Base URL: https://api.stlouisfed.org/fred'
            '    AsyncGeoFred Instance:'
            '      Base URL: https://api.stlouisfed.org/fred/maps/'
        """
        try:
            has_key = bool(_resolve_api_key(service="geofred"))
        except (
            RuntimeError
        ):  # TODO: Add custom exception for missing API key and catch that instead.
            has_key = False

        auth_line = "configured" if has_key else "not configured"

        cache_line = (
            f"enabled (FIFO, maxsize={self.cache_size})" if self.caching_enabled else "disabled"
        )

        return (
            f"{type(self).__name__} Instance:\n"
            f"  Service: GeoFRED ({_ST_LOUIS_FED_BASE_URL}{_GEOFRED_PATH})\n"
            f"  API Key: {auth_line}\n"
            f"  Cache: {cache_line}\n"
            f"  Rate Limit: {_FRED_MAX_REQUESTS_PER_MINUTE} req/min\n"
        )

    def __eq__(self, other: object) -> bool:
        """Equality comparison for the AsyncGeoFred class.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.

        Notes:
            This method compares two AsyncGeoFred instances based on their attributes. If the other object is not a GeoFred
            instance, it returns NotImplemented.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').AsyncFred
            >>> maps_api1 = fred.AsyncGeoFred
            >>> maps_api2 = fred.AsyncGeoFred
            >>> print(maps_api1 == maps_api2)
            True
        """
        try:
            assert isinstance(other, type(self))
        except AssertionError:
            return NotImplemented

        return self.caching_enabled == other.caching_enabled and self.cache_size == other.cache_size

    def __hash__(self) -> int:
        """Hash function for AsyncGeoFred instances.

        Returns:
            int: The hash value of the AsyncGeoFred instance.

        Notes:
            The hash value is computed based on the API key of the grandparent Fred instance, the cache mode of the parent
            AsyncFred instance, and the cache size of the grandparent Fred instance.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').AsyncFred
            >>> maps_api = fred.AsyncGeoFred
            >>> print(hash(maps_api))
        """
        return hash((type(self).__name__, self.caching_enabled, self.cache_size))

    def __len__(self) -> int:
        """Get the number of cached items in the AsyncGeoFred instance.

        Returns:
            int: The number of items in the cache.

        Notes:
            This method returns the number of items currently stored in the cache.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').AsyncFred
            >>> maps_api = fred.AsyncGeoFred
            >>> print(len(maps_api))
        """
        return len(_CACHE) if self.caching_enabled else 0

    def __contains__(self, key: str) -> bool:
        """Check if a specific item exists in the cache.

        Args:
            key (str): The name of the attribute to check.

        Returns:
            bool: True if the key exists, False otherwise.

        Notes:
            This method checks if a specific key is present in the cache.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').AsyncFred
            >>> maps_api = fred.AsyncGeoFred
            >>> print('some_key' in maps_api)
            True
        """
        return self.caching_enabled and key in _CACHE

    def __getitem__(self, key: str) -> Any:
        """Get a specific item from the cache.

        Args:
            key (str): The name of the attribute to get.

        Returns:
            Any: The value of the attribute.

        Raises:
            AttributeError: If the key does not exist.

        Notes:
            This method allows access to cached items using the indexing syntax.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').AsyncFred
            >>> maps_api = fred.AsyncGeoFred
            >>> value = maps_api['some_key']
            >>> print(value)
            'some_value'
        """
        if not self.caching_enabled:
            raise KeyError(
                key
            )  # TODO: Add custom exception for cache disabled and catch that instead.

        return _CACHE.cache[key]

    async def __aenter__(self) -> AsyncGeoFred:
        """Enter the asynchronous runtime context.

        Returns:
            AsyncFred: The AsyncFred instance itself.

        Notes:
            AsyncFred does not currently own per-instance resources requiring explicit cleanup — transport opens and closes httpx.AsyncClient per
            request, and the cache and rate-limit buckets are module-global. The context manager exists for ergonomic parity with httpx and as a
            forward-compatible seam for future per-instance connection pooling.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            ...     async with fd.AsyncFred("your_api_key") as fred:
            ...         categories = await fred.get_category(125)
            >>> asyncio.run(main())
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit the asynchronous runtime context. No-op.

        Args:
            exc_type: Exception type if one was raised in the async-with-block.
            exc: Exception instance, if any.
            tb: Traceback, if any.

        Notes:
            Does not clear the cache or rate-limit buckets — those are shared
            across all live Fred and AsyncFred instances.
        """
        return None

    @property
    def keys(self) -> KeysView[tuple[Any, ...]] | None:
        """List of keys in the cache."""
        return _CACHE.keys() if self.caching_enabled else None

    # Private Methods
    async def __geofred_get_request(
        self, url_endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Helper method to perform an asynchronous GET request to the FRED Maps API.

        Args:
            url_endpoint (str): The endpoint URL to send the GET request to.
            data (Dict[str, Optional[Union[str, int]]], optional): The query parameters for the GET request.

        Returns:
            Dict[str, Any]: The JSON response from the FRED Maps API.

        Raises:
            ValueError: If the response from the FRED Maps API indicates an error.

        Notes:
            This method handles rate limiting and caching for asynchronous GET requests to the FRED Maps API.

        Warnings:
            Caching is only applied if `cache_mode` is enabled in the parent Fred instance. Ensure that the `data` parameter is hashable for
            caching to work correctly.
        """
        if self.caching_enabled:
            return await _cached_get_request_async(
                url_endpoint, await _hashable_type_converter_async(data)
            )

        else:
            return await _get_request_async(url_endpoint, data)

    # Public Methods
    async def get_shape_files(
        self, shape: str, geodataframe_method: str = "geopandas"
    ) -> gpd.GeoDataFrame | dd_gpd.GeoDataFrame | st.GeoDataFrame:
        """Get GeoFRED shape files

        This request returns shape files from FRED in GeoJSON format.

        Args:
            shape (str, required): The type of shape you want to pull GeoJSON data for. Available Shape Types: 'bea' (Bureau of Economic Anaylis Region), 'msa' (Metropolitan Statistical Area), 'frb' (Federal Reserve Bank Districts), 'necta' (New England City and Town Area), 'state', 'country', 'county' (USA Counties), 'censusregion' (US Census Regions), 'censusdivision' (US Census Divisons).
            geodataframe_method (str, optional): The method to use for creating the GeoDataFrame. Options are 'geopandas', 'dask' or 'polars'. Default is 'geopandas'.

        Returns:
            geopandas.GeoDataFrame | dask_geopandas.GeoDataFrame | polars_st.GeoDataFrame: Depending on the geodataframe_method selected. Default is geopandas.GeoDataFrame.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred.AsyncGeoFred
            >>>     shapefile = fred.get_shape_files('state')
            >>>     print(shapefile.head())
            >>> asyncio.run(main())
                                                        geometry  ...   type
            0  MULTIPOLYGON (((9727 7650, 10595 7650, 10595 7...  ...  State
            1  MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...  ...  State
            2  POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...  ...  State
            3  POLYGON ((-50 7955, -833 8186, -851 8223, -847...  ...  State
            4  MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...  ...  State
            [5 rows x 20 columns]

        See Also:
            - :class:`fedfred.AsyncHelpers`: Async helper methods for parameter validation and conversion.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/geofred/shapes.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncGeoFred.get_shape_files.html
        """
        endpoint_name = "get_shapes_file"

        data: dict[str, Any] = {"shape": shape}

        response = await self.__geofred_get_request(endpoint_name, data)

        # ----------------------------Needs-Abstraction-----------------------------------------------------------------
        if geodataframe_method == "geopandas":
            return await asyncio.to_thread(gpd.GeoDataFrame.from_features, response["features"])
        elif geodataframe_method == "dask":
            gdf = await asyncio.to_thread(gpd.GeoDataFrame.from_features, response["features"])
            try:
                import dask_geopandas as dd_gpd

                return dd_gpd.from_geopandas(gdf, npartitions=1)
            except ImportError as e:
                raise ImportError(
                    f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method."
                ) from e
        elif geodataframe_method == "polars":
            gdf = await asyncio.to_thread(gpd.GeoDataFrame.from_features, response["features"])
            try:
                import polars_st as st

                return st.from_geopandas(gdf)
            except ImportError as e:
                raise ImportError(
                    f"{e}: Polars is not installed. Install it with `pip install polars` to use this method."
                ) from e
        else:
            raise ValueError(
                "geodataframe_method must be 'geopandas', 'dask', or 'polars'"
            )  # TODO: Custom error class
        # ---------------------------------------------------------------------------------------------------------------

    async def get_series_group(self, series_id: str) -> list[SeriesGroup]:
        """Get a GeoFRED series group

        This request returns the meta information needed to make requests for FRED data. Minimum
        and maximum date are also supplied for the data range available.

        Args:
            series_id (str, required): The FRED series id you want to request maps meta information for. Not all series that are in FRED have geographical data.

        Returns:
            List[SeriesGroup]: If multiple series groups are returned.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred.AsyncGeoFred
            >>>     series_group = await fred.get_series_group('SMU56000000500000001')
            >>>     print(series_group)
            >>> asyncio.run(main())
            'State Personal Income'

        See Also:
            - :class:`fedfred.SeriesGroup`: The SeriesGroup object representation.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/geofred/series_group.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncGeoFred.get_series_group.html
        """
        endpoint_name = "get_series_group"

        data: dict[str, Any] = {"series_id": series_id, "file_type": "json"}

        response = await self.__geofred_get_request(endpoint_name, data)

        return await SeriesGroup.to_object_async(response)

    async def get_series_data(
        self,
        series_id: str,
        geodataframe_method: str = "geopandas",
        date: str | datetime | date | None = None,
        start_date: str | datetime | date | None = None,
    ) -> gpd.GeoDataFrame | dd_gpd.GeoDataFrame | st.GeoDataFrame:
        """Get GeoFRED series data

        This request returns a cross section of regional data for a specified release date. If no
        date is specified, the most recent data available are returned.

        Args:
            series_id (string, required): The FRED series_id you want to request maps data for. Not all series that are in FRED have geographical data.
            geodataframe_method (str, optional): The method to use for creating the GeoDataFrame. Options are 'geopandas' 'polars', or 'dask'. Default is 'geopandas'.
            date (string | datetime, optional): The date you want to request series group data from. String format: YYYY-MM-DD
            start_date (string | datetime, optional): The start date you want to request series group data from. This allows you to pull a range of data. String format: YYYY-MM-DD

        Returns:
            geopandas.GeoDataFrame | dask_geopandas.GeoDataFrame | polars_st.GeoDataFrame: Depending on the geodataframe_method selected. Default is geopandas.GeoDataFrame.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred.AsyncGeoFred
            >>>     series_data = fred.get_series_data('SMU56000000500000001')
            >>>     print(series_data.head())
            >>> asyncio.run(main())
            name                                                    geometry  ...             series_id
            Washington     MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...  ...  SMU53000000500000001
            California     POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...  ...  SMU06000000500000001
            Oregon         POLYGON ((-50 7955, -833 8186, -851 8223, -847...  ...  SMU41000000500000001
            Wisconsin      MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...  ...  SMU55000000500000001

        See Also:
            - :class:`fedfred.AsyncHelpers`: Async helper methods for parameter validation and conversion.

        References:
            -Fred API Documentation: https://fred.stlouisfed.org/docs/api/geofred/series_data.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncGeoFred.get_series_data.html
        """
        endpoint_name = "get_series_data"

        data: dict[str, Any] = {
            "series_id": series_id,
            "file_type": "json",
            "date": date,
            "start_date": start_date,
        }

        # ----------------------------Needs-Abstraction-----------------------------------------------------------------
        response = await self.__geofred_get_request(endpoint_name, data)
        meta_data = response.get("meta", {})
        region_type = await _region_type_parser_async(response)
        shapefile = await self.get_shape_files(region_type)
        # --------------------------------------------------------------------------------------------------------------

        if isinstance(
            shapefile, gpd.GeoDataFrame
        ):  # TODO: Slight logic fix (No front end validation)
            try:
                return await ASYNC_GEODATAFRAME_CONVERTER_MAP[geodataframe_method](
                    shapefile, meta_data
                )
            except Exception as exc:
                raise ValueError(
                    "geodataframe_method must be 'geopandas', 'polars', or 'dask'"
                ) from exc  # TODO: Needs custom Error handling exception hierarchy.
        else:
            raise ValueError(
                "shapefile type error"
            )  # TODO: Needs custom Error handling exception hierarchy.

    async def get_regional_data(
        self,
        series_group: str,
        region_type: str,
        date: str | datetime,
        season: str,
        units: str,
        frequency: str,
        geodataframe_method: str = "geopandas",
        start_date: str | datetime | None = None,
        transformation: str | None = None,
        aggregation_method: str | None = None,
    ) -> gpd.GeoDataFrame | dd_gpd.GeoDataFrame | st.GeoDataFrame:
        """Get GeoFRED regional data

        Retrieve regional data for a specified series group and date from the FRED Maps API.

        Args:
            series_group (str): The series group for which you want to request regional data.
            region_type (str): The type of region for which you want to request data. Options are 'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', or 'censusdivision'.
            date (str | datetime): The date for which you want to request regional data. String format: YYYY-MM-DD.
            season (str): The seasonality of the data. Options include 'seasonally_adjusted' or 'not_seasonally_adjusted'.
            units (str): The units of the data. Options are 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca' and 'log'.
            frequency (str): The frequency of the data. Options are 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew'and 'bwem'.
            geodataframe_method (str, optional): The method to use for creating the GeoDataFrame. Options are 'geopandas', 'dask' or 'polars'. Default is 'geopandas'.
            start_date (str, optional): The start date for the range of data you want to request. Format: YYYY-MM-DD.
            transformation (str, optional): The data transformation to apply. Options are 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', and 'log'.
            aggregation_method (str, optional): The aggregation method to use. Options are 'avg', 'sum', and 'eop'.

        Returns:
            geopandas.GeoDataFrame | dask_geopandas.GeoDataFrame | polars_st.GeoDataFrame: Depending on the geodataframe_method selected. Default is geopandas.GeoDataFrame.

        Raises:
            ValueError: If the API request fails or returns an error.

        Examples:
            >>> import fedfred as fd
            >>> import asyncio
            >>> async def main():
            >>>     fred = fd.Fred('your_api_key').AsyncFred.AsyncGeoFred
            >>>     regional_data = fred.get_regional_data(series_group='882', date='2013-01-01', region_type='state', units='Dollars', frequency='a', season='NSA')
            >>>     print(regional_data.head())
            >>> asyncio.run(main())
            name                                                    geometry hc-group  ...  value  series_id
            Massachusetts  MULTIPOLYGON (((9727 7650, 10595 7650, 10595 7...   admin1  ...  56119     MAPCPI
            Washington     MULTIPOLYGON (((-77 9797, -56 9768, -91 9757, ...   admin1  ...  47448     WAPCPI
            California     POLYGON ((-833 8186, -50 7955, -253 7203, 32 6...   admin1  ...  48074     CAPCPI
            Oregon         POLYGON ((-50 7955, -833 8186, -851 8223, -847...   admin1  ...  39462     ORPCPI
            Wisconsin      MULTIPOLYGON (((6206 8297, 6197 8237, 6159 815...   admin1  ...  42685     WIPCPI
            [5 rows x 21 columns]

        See Also:
            - :class:`fedfred.AsyncFred`: Async helper methods for parameter validation and conversion.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/geofred/regional_data.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncGeoFred.get_regional_data.html
        """
        url_endpoint = "get_regional_data"

        data: dict[str, Any] = {
            "series_group": series_group,
            "region_type": region_type,
            "date": date,
            "season": season,
            "units": units,
            "frequency": frequency,
            "file_type": "json",
            "start_date": start_date,
            "transformation": transformation,
            "aggregation_method": aggregation_method,
        }

        # ----------------------------Needs-Abstraction-----------------------------------------------------------------
        response = await self.__geofred_get_request(url_endpoint, data)
        meta_data = response.get("meta", {})
        region_type = await _region_type_parser_async(response)
        shapefile = await self.get_shape_files(region_type)
        # --------------------------------------------------------------------------------------------------------------

        if isinstance(
            shapefile, gpd.GeoDataFrame
        ):  # TODO: Slight logic fix (No front end validation)
            try:
                return ASYNC_GEODATAFRAME_CONVERTER_MAP[geodataframe_method](shapefile, meta_data)
            except Exception as exc:
                raise ValueError(
                    "geodataframe_method must be 'geopandas', 'polars', or 'dask'"
                ) from exc  # TODO: Needs custom Error handling exception hierarchy.
        else:
            raise ValueError(
                "shapefile type error"
            )  # TODO: Needs custom Error handling exception hierarchy.
