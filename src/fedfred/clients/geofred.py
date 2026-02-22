

from __future__ import annotations
import asyncio
from datetime import datetime
import time
from typing import TYPE_CHECKING, Optional, Dict, Union, List, Tuple, Any
import httpx
import geopandas as gpd
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type
from cachetools import FIFOCache, cached
from asyncache import cached as async_cached
from ..__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__
from .fred import Fred, AsyncFred
from .._core import (
    # Converters
    _dict_type_converter, _dict_type_converter_async,
    _hashable_type_converter, _hashable_type_converter_async,
    _datetime_converter, _datetime_converter_async,
    _geopandas_geodataframe_converter, _geopandas_geodataframe_converter_async,
    _dask_geopandas_geodataframe_converter, _dask_geopandas_geodataframe_converter_async,
    _polars_geodataframe_converter, _polars_geodataframe_converter_async,
    # Validators
    _geofred_parameter_validator, _geofred_parameter_validator_async,
    # Helpers
    _region_type_extractor, _region_type_extractor_async
)
from ..models import SeriesGroup

if TYPE_CHECKING:
    import dask_geopandas as dd_gpd # pragma: no cover
    import polars_st as st # pragma: no cover

class GeoFred:
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

    # Dunder Methods
    def __init__(self, parent: 'Fred') -> None:
        """Initialize the GeoFred with a reference to the parent Fred instance.

        Args:
            parent (Fred): The parent Fred instance that this MapsAPI instance is associated with

        Raises:
            ValueError: If the parent instance is not an instance of Fred.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred

            or directly with a Fred instance

            >>> fred_maps = fd.GeoFred(fred)

        Notes:
            API keys can be set globally using `fedfred.set_api_key(...)`, or can be provided explicitly
            when instantiating the `Fred` class. If neither is provided, the class will attempt to
            resolve the API key from the environment variable `FRED_API_KEY`.

        See Also:
            - :func:`fedfred.set_api_key`: Function to set the global FRED API key.
            - :class:`fedfred.Helpers`: Helper functions for parameter validation and conversion.
        """

        if not isinstance(parent, Fred):
            raise ValueError("parent must be an instance of Fred")

        self._parent: Fred = parent
        self.cache_mode: bool = parent.cache_mode
        self.cache: FIFOCache = parent.cache
        self.base_url: str = 'https://api.stlouisfed.org/geofred'

    def __repr__(self) -> str:
        """String representation of the GeoFred Class.

        Returns:
            str: A string representation of the GeoFred instance.

        Notes:
            The string representation includes the parent Fred instance's string representation and the GeoFred 
            instance's string representation.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred
            >>> print(fred_maps)
            'Fred(api_key='your_api_key', cache_mode=True, cache_size=256).GeoFred(base_url=https://api.stlouisfed.org/geofred)'
        """

        return f"{self._parent.__repr__()}.GeoFred(base_url={self.base_url})"

    def __str__(self) -> str:
        """String representation of the GeoFred instance.

        Returns:
            str: A user-friendly string representation of the GeoFred instance.

        Notes:
            The string representation includes the parent Fred instance's string representation and the GeoFred instance's string representation.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred
            >>> print(fred_maps)
            'Fred Instance:'
            '  Base URL: https://api.stlouisfed.org/fred'
            '  API Key: ****your_api_key'
            '  Cache Mode: Enabled'
            '  Cache Size: 256 items'
            '  Max Requests per Minute: 120'
            '  GeoFred Instance:'
            '      Base URL: https://api.stlouisfed.org/geofred'
        """

        return (
            f"{self._parent.__str__()}"
            f"  GeoFred Instance:\n"
            f"    Base URL: {self.base_url}\n"
        )

    def __eq__(self, other: object) -> bool:
        """Equality comparison for the GeoFred class.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.

        Notes:
            This method compares two GeoFred instances based on their attributes. If the other object is not a GeoFred 
            instance, it returns NotImplemented.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred
            >>> fred_maps2 = fd.GeoFred(fred)
            >>> fred_maps == fred_maps2
            True
        """

        if not isinstance(other, GeoFred):
            return NotImplemented
        return self._parent == other._parent

    def __hash__(self) -> int:
        """Hash function for the GeoFred class.

        Returns:
            int: A hash value for the GeoFred instance.

        Notes:
            This method generates a hash based on the GeoFred instance's attributes, including the parent Fred 
            instance's attributes.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred
            >>> hash(fred_maps)
            1234567890 # Example hash value
        """

        return hash((self._parent, self.base_url))

    def __del__(self) -> None:
        """Destructor for the GeoFred instance. Clears the cache when the instance is deleted.

        Notes:
            This method ensures that the cache is cleared when the GeoFred instance is deleted.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred
            >>> del fred_maps
            >>> # Cache is cleared when fred_maps is deleted
        """

        if hasattr(self, "cache"):
            self.cache.clear()

    def __len__(self) -> int:
        """Get the number of cached items in the GeoFred instance.

        Returns:
            int: The number of cached items in the GeoFred instance.

        Notes:
            This method returns the size of the cache if the cache is enabled.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred
            >>> print(len(fred_maps))
            256 # Example length of cache
        """

        return len(self.cache)

    def __contains__(self, key: str) -> bool:
        """Check if a specific item exists in the cache.

        Args:
            key (str): The name of the attribute to check.

        Returns:
            bool: True if the key exists, False otherwise.

        Notes:
            This method checks if a specific item exists in the cache.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred
            >>> print('some_key' in fred_maps)
            True
        """

        return key in self.cache.keys()

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
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred
            >>> value = fred_maps['some_key']
            >>> print(value)
            'some_value'
        """

        if key in self.cache.keys():
            return self.cache[key]
        else:
            raise AttributeError(f"'{key}' not found in cache.")

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a specific item in the cache.

        Args:
            key (str): The name of the attribute to set.
            value (Any): The value to set.

        Notes:
            This method allows setting cached items using the indexing syntax.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred
            >>> fred_maps['some_key'] = 'some_value'
            >>> print(fred_maps['some_key'])
            'some_value'
        """

        self.cache[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete a specific item from the cache.

        Args:
            key (str): The name of the attribute to delete.

        Raises:
            AttributeError: If the key does not exist.

        Notes:
            This method allows deletion of cached items using the indexing syntax.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred
            >>> del fred_maps['some_key']
            >>> print('some_key' in fred_maps)
            False
        """

        if key in self.cache.keys():
            del self.cache[key]
        else:
            raise AttributeError(f"'{key}' not found in cache.")

    def __call__(self) -> str:
        """Call the GeoFred instance to get a summary of its configuration.

        Returns:
            str: A string representation of the GeoFred instance's configuration.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> fred_maps = fred.GeoFred
            >>> print(fred_maps())
            'Fred Instance:'
            '  GeoFred Instance:'
            '    Base URL: https://api.stlouisfed.org/geofred'
            '    Cache Mode: Enabled'
            '    Cache Size: 256 items'
            '    API Key: ****your_api_key'
        """

        return (
            f"Fred Instance:\n"
            f"  GeoFred Instance:\n"
            f"    Base URL: {self.base_url}\n"
            f"    Cache Mode: {'Enabled' if self.cache_mode else 'Disabled'}\n"
            f"    Cache Size: {len(self.cache)} items\n"
            f"    API Key: {'****' + self._parent.api_key[-4:] if self._parent.api_key else 'Not Set'}\n"
        )

    # Properties
    @property
    def keys(self) -> List[str]:
        """List of keys in the cache."""

        return list(self.cache.keys() if self._parent.cache_mode else [])

    # Private Methods
    def __rate_limited(self) -> None:
        """Ensures synchronous requests comply with rate limits.

        Notes:
            This method tracks the timestamps of requests and enforces rate limiting by sleeping when the maximum 
            number of requests per minute is reached.

        Warnings:
            This method uses time.sleep(), which blocks the current thread. Avoid using it in asynchronous contexts.
        """

        now = time.time()
        self._parent.request_times.append(now)
        while self._parent.request_times and self._parent.request_times[0] < now - 60:
            self._parent.request_times.popleft()
        if len(self._parent.request_times) >= self._parent.max_requests_per_minute:
            time.sleep(60 - (now - self._parent.request_times[0]))

    def __fred_get_request(self, url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
        """Helper method to perform a synchronous GET request to the FRED Maps API.

        Args:
            url_endpoint (str): The FRED Maps API endpoint to query.
            data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

        Returns:
            Dict[str, Any]: The JSON response from the FRED Maps API.

        Raises:
            httpx.HTTPError: If the HTTP request fails.

        Notes:
            This method handles rate limiting and caching for synchronous GET requests to the FRED Maps API.

        Warnings:
            Caching is only applied if `cache_mode` is enabled. Ensure that the `data` parameter is hashable for 
            caching to work correctly.
        """

        @retry(wait=wait_fixed(1),
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type(httpx.HTTPError),
            reraise=True,)
        def __get_request(url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
            """Perform a GET request without caching.

            Args:
                url_endpoint (str): The FRED API endpoint to query.
                data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

            Returns:
                Dict[str, Any]: The JSON response from the FRED Maps API.

            Raises:
                httpx.HTTPError: If the HTTP request fails.

            Notes:
                This method handles rate limiting and caching for synchronous GET requests to the FRED Maps API.
            """

            self.__rate_limited()
            params = {
                **(data or {}),
                'api_key': self._parent.api_key
            }
            with httpx.Client() as client:
                try:
                    response = client.get(self.base_url + url_endpoint, params=params, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError as e:
                    raise ValueError(f"HTTP Error Ocurred {e}") from e

        @cached(cache=self.cache)
        def __cached_get_request(url_endpoint: str, hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]=None) -> Dict[str, Any]:
            """Perform a GET request with caching.

            Args:
                url_endpoint (str): The FRED Maps API endpoint to query.
                hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]], optional): The hashable representation of the data. Defaults to None.

            Returns:
                Dict[str, Any]: The JSON response from the FRED Maps API.

            Raises:
                httpx.HTTPError: If the HTTP request fails.
            """

            return __get_request(url_endpoint, _dict_type_converter(hashable_data))

        if data:
            _geofred_parameter_validator(data)
        if self.cache_mode:
            return __cached_get_request(url_endpoint, _hashable_type_converter(data))
        else:
            return __get_request(url_endpoint, data)

    # Public Methods
    def get_shape_files(self, shape: str, geodataframe_method: str='geopandas') -> Union[gpd.GeoDataFrame, 'dd_gpd.GeoDataFrame', 'st.GeoDataFrame']:
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

        url_endpoint = '/shapes/file'
        data: Dict[str, Optional[Union[str, int]]] = {
            'shape': shape
        }
        response = self.__fred_get_request(url_endpoint, data)
        if geodataframe_method == 'geopandas':
            return gpd.GeoDataFrame.from_features(response['features'])
        elif geodataframe_method == 'dask':
            gdf = gpd.GeoDataFrame.from_features(response['features'])
            try:
                import dask_geopandas as dd_gpd
                return dd_gpd.from_geopandas(gdf, npartitions=1)
            except ImportError as e:
                raise ImportError(
                    f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method."
                ) from e
        elif geodataframe_method == 'polars':
            gdf = gpd.GeoDataFrame.from_features(response['features'])
            try:
                import polars_st as st
                return st.from_geopandas(gdf)
            except ImportError as e:
                raise ImportError(
                    f"{e}: Polars is not installed. Install it with `pip install polars` to use this method."
                ) from e
        else:
            raise ValueError("geodataframe_method must be 'geopandas', 'dask', or 'polars'")

    def get_series_group(self, series_id: str) -> List[SeriesGroup]:
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

        url_endpoint = '/series/group'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id,
            'file_type': 'json'
        }
        response = self.__fred_get_request(url_endpoint, data)
        return SeriesGroup.to_object(response)

    def get_series_data(self, series_id: str, geodataframe_method: str='geopandas', date: Optional[Union[str, datetime]]=None,
                        start_date: Optional[Union[str, datetime]]=None) -> Union[gpd.GeoDataFrame, 'dd_gpd.GeoDataFrame', 'st.GeoDataFrame']:
        """Get GeoFRED series data

        This request returns a cross section of regional data for a specified release date. If no date is specified, the most recent data available are returned.

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

        url_endpoint = '/series/data'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id,
            'file_type': 'json'
        }
        if date:
            if isinstance(date, datetime):
                date = _datetime_converter(date)
            data['date'] = date
        if start_date:
            if isinstance(start_date, datetime):
                start_date = _datetime_converter(start_date)
            data['start_date'] = start_date
        response = self.__fred_get_request(url_endpoint, data)
        meta_data = response.get('meta', {})
        region_type = _region_type_extractor(response)
        shapefile = self.get_shape_files(region_type)
        if isinstance(shapefile, gpd.GeoDataFrame):
            if geodataframe_method == 'geopandas':
                return _geopandas_geodataframe_converter(shapefile, meta_data)
            elif geodataframe_method == 'dask':
                return _dask_geopandas_geodataframe_converter(shapefile, meta_data)
            elif geodataframe_method == 'polars':
                return _polars_geodataframe_converter(shapefile, meta_data)
            else:
                raise ValueError("geodataframe_method must be 'geopandas', 'polars', or 'dask'")
        else:
            raise ValueError("shapefile type error")

    def get_regional_data(self, series_group: str, region_type: str, date: Union[str, datetime], season: str,
                          units: str, frequency: str, geodataframe_method: str='geopandas',
                          start_date: Optional[Union[str, datetime]]=None, transformation: Optional[str]=None,
                          aggregation_method: Optional[str]=None) -> Union[gpd.GeoDataFrame, 'dd_gpd.GeoDataFrame', 'st.GeoDataFrame']:
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

        if isinstance(date, datetime):
            date = _datetime_converter(date)
        url_endpoint = '/regional/data'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_group': series_group,
            'region_type': region_type,
            'date': date,
            'season': season,
            'units': units,
            'frequency': frequency,
            'file_type': 'json'
        }
        if start_date:
            if isinstance(start_date, datetime):
                start_date = _datetime_converter(start_date)
            data['start_date'] = start_date
        if transformation:
            data['transformation'] = transformation
        if aggregation_method:
            data['aggregation_method'] = aggregation_method
        response = self.__fred_get_request(url_endpoint, data)
        meta_data = response.get('meta', {})
        region_type = _region_type_extractor(response)
        shapefile = self.get_shape_files(region_type)
        if isinstance(shapefile, gpd.GeoDataFrame):
            if geodataframe_method == 'geopandas':
                return _geopandas_geodataframe_converter(shapefile, meta_data)
            elif geodataframe_method == 'dask':
                return _dask_geopandas_geodataframe_converter(shapefile, meta_data)
            elif geodataframe_method == 'polars':
                return _polars_geodataframe_converter(shapefile, meta_data)
            else:
                raise ValueError("geodataframe_method must be 'geopandas', 'polars', or 'dask'")
        else:
            raise ValueError("shapefile type error")

class AsyncGeoFred:
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
    def __init__(self, parent: 'AsyncFred') -> None:
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

        if not isinstance(parent, AsyncFred):
            raise ValueError("parent must be an instance of AsyncFred")

        self._parent: AsyncFred = parent
        self._grandparent: Fred = parent._parent
        self.cache_mode: bool = parent._parent.cache_mode
        self.cache: FIFOCache = parent._parent.cache
        self.base_url: str = 'https://api.stlouisfed.org/geofred'

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

        return f"{self._parent.__repr__()}.AsyncGeoFred(base_url={self.base_url})"

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

        return (
            f"{self._parent.__str__()}"
            f"    AsyncGeoFred Instance:\n"
            f"      Base URL: {self.base_url}\n"
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

        if not isinstance(other, AsyncGeoFred):
            return NotImplemented
        return self._parent == other._parent

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

        return hash((self._grandparent, self._parent, self.base_url))

    def __del__(self) -> None:
        """Destructor for the AsyncGeoFred instance. Clears the cache when the instance is deleted.

        Notes:
            This method ensures that the cache is cleared when the AsyncGeoFred instance is deleted.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').AsyncFred
            >>> maps_api = fred.AsyncGeoFred
            >>> del maps_api
        """

        if hasattr(self, "cache"):
            self.cache.clear()

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

        return len(self.cache)

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

        return key in self.cache.keys()

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

        if key in self.cache.keys():
            return self.cache[key]
        else:
            raise AttributeError(f"'{key}' not found in cache.")

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a specific item in the cache.

        Args:
            key (str): The name of the attribute to set.
            value (Any): The value to set.

        Notes:
            This method allows setting cached items using the indexing syntax.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').AsyncFred
            >>> maps_api = fred.AsyncGeoFred
            >>> maps_api['some_key'] = 'some_value'
            >>> print(maps_api['some_key'])
            'some_value'
        """

        self.cache[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete a specific item from the cache.

        Args:
            key (str): The name of the attribute to delete.

        Raises:
            AttributeError: If the key does not exist.

        Notes:
            This method allows deletion of cached items using the indexing syntax.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').AsyncFred
            >>> maps_api = fred.AsyncGeoFred
            >>> del maps_api['some_key']
            >>> print('some_key' in maps_api)
            False
        """

        if key in self.cache.keys():
            del self.cache[key]
        else:
            raise AttributeError(f"'{key}' not found in cache.")

    def __call__(self) -> str:
        """Call the AsyncGeoFred instance to get a summary of its configuration.

        Returns:
            str: A string representation of the AsyncGeoFred instance's configuration.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key').AsyncFred
            >>> maps_api = fred.AsyncGeoFred
            >>> print(maps_api())
            'Fred Instance:'
            '  AsyncFred Instance:'
            '    AsyncGeoFred Instance:'
            '      Base URL: https://api.stlouisfed.org/fred/maps/'
            '      Cache Mode: Enabled'
            '      Cache Size: 256 items'
            '      API Key: ****your_api_key'
        """

        return (
            f"Fred Instance:\n"
            f"  AsyncFred Instance:\n"
            f"    AsyncGeoFred Instance:\n"
            f"      Base URL: {self.base_url}\n"
            f"      Cache Mode: {'Enabled' if self.cache_mode else 'Disabled'}\n"
            f"      Cache Size: {len(self.cache)} items\n"
            f"      API Key: {'****' + self._grandparent.api_key[-4:] if self._grandparent.api_key else 'Not Set'}\n"
        )

    # Private Methods
    async def __update_semaphore(self) -> Tuple[Any, float]:
        """Dynamically adjusts the semaphore based on requests left in the minute.

        Returns:
            Tuple[int, float]: A tuple containing the number of requests left and the time left in the current minute.

        Notes:
            This method updates the semaphore limit based on the number of requests made in the last minute.

        Warnings:
            This method should be called within an asynchronous context to ensure proper locking and timing.
        """

        async with self._grandparent.lock:
            now = time.time()
            while self._grandparent.request_times and self._grandparent.request_times[0] < now - 60:
                self._grandparent.request_times.popleft()
            requests_made = len(self._grandparent.request_times)
            requests_left = max(0, self._grandparent.max_requests_per_minute - requests_made)
            time_left = max(1, 60 - (now - (self._grandparent.request_times[0] if self._grandparent.request_times else now)))
            new_limit = max(1, min(self._grandparent.max_requests_per_minute // 10, requests_left // 2))
            self._grandparent.semaphore = asyncio.Semaphore(new_limit)
            return requests_left, time_left

    async def __rate_limited(self) -> None:
        """Ensures asynchronous requests comply with rate limits.

        Notes:
            This method ensures that API requests adhere to the rate limit by dynamically adjusting the wait time based on the 
            number of requests left and the time remaining in the current minute.

        Warnings:
            This method should be used within an asynchronous context to ensure proper locking and timing.
        """

        async with self._grandparent.semaphore:
            requests_left, time_left = await self.__update_semaphore()
            if requests_left > 0:
                sleep_time = time_left / max(1, requests_left)
                await asyncio.sleep(sleep_time)
            else:
                await asyncio.sleep(60)
            async with self._grandparent.lock:
                self._grandparent.request_times.append(time.time())

    async def __fred_get_request(self, url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
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

        @retry(wait=wait_fixed(1),
               stop=stop_after_attempt(3),
               retry=retry_if_exception_type(httpx.HTTPError),
               reraise=True,)
        async def __get_request(url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
            """Perform a GET request without caching.

            Args:
                url_endpoint (str): The FRED Maps API endpoint to query.
                data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

            Returns:
                Dict[str, Any]: The JSON response from the FRED Maps API.

            Raises:
                httpx.HTTPError: If the HTTP request fails.

            Notes:
                This method handles rate limiting and caching for synchronous GET requests to the FRED Maps API.
            """

            await self.__rate_limited()
            params = {
                **(data or {}),
                'api_key': self._grandparent.api_key
            }
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(self.base_url + url_endpoint, params=params, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError as e:
                    raise ValueError(f"HTTP Error occurred: {e}") from e

        @async_cached(cache=self.cache)
        async def __cached_get_request(url_endpoint: str, hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]=None) -> Dict[str, Any]:
            """Perform a GET request with caching.

            Args:
                url_endpoint (str): The FRED API endpoint to query.
                hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]], optional): The hashable representation of the data. Defaults to None.

            Returns:
                Dict[str, Any]: The JSON response from the FRED API.

            Raises:
                httpx.HTTPError: If the HTTP request fails.
            """

            return await __get_request(url_endpoint, await _dict_type_converter_async(hashable_data))

        if data:
            await _geofred_parameter_validator_async(data)
        if self.cache_mode:
            return await __cached_get_request(url_endpoint, await _hashable_type_converter_async(data))
        else:
            return await __get_request(url_endpoint, data)

    # Public Methods
    async def get_shape_files(self, shape: str, geodataframe_method: str='geopandas') -> Union[gpd.GeoDataFrame, 'dd_gpd.GeoDataFrame', 'st.GeoDataFrame']:
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

        if not isinstance(shape, str) or shape == '':
            raise ValueError("shape must be a non-empty string")
        url_endpoint = '/shapes/file'
        data: Dict[str, Optional[Union[str, int]]] = {
            'shape': shape
        }
        response = await self.__fred_get_request(url_endpoint, data)
        if geodataframe_method == 'geopandas':
            return await asyncio.to_thread(gpd.GeoDataFrame.from_features, response['features'])
        elif geodataframe_method == 'dask':
            gdf = await asyncio.to_thread(gpd.GeoDataFrame.from_features, response['features'])
            try:
                import dask_geopandas as dd_gpd
                return dd_gpd.from_geopandas(gdf, npartitions=1)
            except ImportError as e:
                raise ImportError(
                    f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method."
                ) from e
        elif geodataframe_method == 'polars':
            gdf = await asyncio.to_thread(gpd.GeoDataFrame.from_features, response['features'])
            try:
                import polars_st as st
                return st.from_geopandas(gdf)
            except ImportError as e:
                raise ImportError(
                    f"{e}: Polars is not installed. Install it with `pip install polars` to use this method."
                ) from e
        else:
            raise ValueError("geodataframe_method must be 'geopandas', 'dask', or 'polars'")

    async def get_series_group(self, series_id: str) -> List[SeriesGroup]:
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

        url_endpoint = '/series/group'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id,
            'file_type': 'json'
        }
        response = await self.__fred_get_request(url_endpoint, data)
        return await SeriesGroup.to_object_async(response)

    async def get_series_data(self, series_id: str, geodataframe_method: str='geopandas', date: Optional[Union[str, datetime]]=None,
                              start_date: Optional[Union[str, datetime]]=None) -> Union[gpd.GeoDataFrame, 'dd_gpd.GeoDataFrame', 'st.GeoDataFrame']:
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

        url_endpoint = '/series/data'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_id': series_id,
            'file_type': 'json'
        }
        if date:
            if isinstance(date, datetime):
                date = await _datetime_converter_async(date)
            data['date'] = date
        if start_date:
            if isinstance(start_date, datetime):
                start_date = await _datetime_converter_async(start_date)
            data['start_date'] = start_date
        response = await self.__fred_get_request(url_endpoint, data)
        meta_data = response.get('meta', {})
        region_type = await _region_type_extractor_async(response)
        shapefile = await self.get_shape_files(region_type)
        if isinstance(shapefile, gpd.GeoDataFrame):
            if geodataframe_method == 'geopandas':
                return await _geopandas_geodataframe_converter_async(shapefile, meta_data)
            elif geodataframe_method == 'dask':
                return await _dask_geopandas_geodataframe_converter_async(shapefile, meta_data)
            elif geodataframe_method == 'polars':
                return await _polars_geodataframe_converter_async(shapefile, meta_data)
            else:
                raise ValueError("geodataframe_method must be 'geopandas', 'polars', or 'dask'")
        else:
            raise ValueError("shapefile type error")

    async def get_regional_data(self, series_group: str, region_type: str, date: Union[str, datetime], season: str,
                                units: str, frequency: str, geodataframe_method: str='geopandas', start_date: Optional[Union[str, datetime]]=None,
                                transformation: Optional[str]=None, aggregation_method: Optional[str]=None) -> Union[gpd.GeoDataFrame, 'dd_gpd.GeoDataFrame', 'st.GeoDataFrame']:
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
            - :class:`fedfred.AsyncHelpers`: Async helper methods for parameter validation and conversion.

        References:
            - Fred API Documentation: https://fred.stlouisfed.org/docs/api/geofred/regional_data.html
            - fedfred package documentation: https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.AsyncGeoFred.get_regional_data.html
        """

        if isinstance(date, datetime):
            date = _datetime_converter(date)
        url_endpoint = '/regional/data'
        data: Dict[str, Optional[Union[str, int]]] = {
            'series_group': series_group,
            'region_type': region_type,
            'date': date,
            'season': season,
            'units': units,
            'frequency': frequency,
            'file_type': 'json'
        }
        if start_date:
            if isinstance(start_date, datetime):
                start_date = await _datetime_converter_async(start_date)
            data['start_date'] = start_date
        if transformation:
            data['transformation'] = transformation
        if aggregation_method:
            data['aggregation_method'] = aggregation_method
        response = await self.__fred_get_request(url_endpoint, data)
        meta_data = response.get('meta', {})
        region_type = await _region_type_extractor_async(response)
        shapefile = await self.get_shape_files(region_type)
        if isinstance(shapefile, gpd.GeoDataFrame):
            if geodataframe_method == 'geopandas':
                return await _geopandas_geodataframe_converter_async(shapefile, meta_data)
            elif geodataframe_method == 'dask':
                return await _dask_geopandas_geodataframe_converter_async(shapefile, meta_data)
            elif geodataframe_method == 'polars':
                return await _polars_geodataframe_converter_async(shapefile, meta_data)
            else:
                raise ValueError("geodataframe_method must be 'geopandas', 'polars', or 'dask'")
        else:
            raise ValueError("shapefile type error")
