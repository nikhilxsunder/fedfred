"""
fedfred: A simple python wrapper for interacting with the US Federal Reserve database: FRED
"""
import requests

class FredAPI:
    """
    The FredAPI class contains methods for interacting with the Federal Reserve Bank of St. Louis 
    FRED® API.
    """
    # Dunder Methods
    def __init__(self, api_key):
        """
        Initialize the FredAPI class that provides functions which query FRED data.
        """
        self.base_url = 'https://api.stlouisfed.org/fred'
        self.api_key = api_key
    # Private Methods
    def __fred_get_request(self, url_endpoint, data=None):
        params = {
            **data,
            'api_key': self.api_key
        }
        req = requests.get((self.base_url + url_endpoint), params=params, timeout=10)
        req.raise_for_status()
        return req.json()
    # Public Methods
    ## Categories
    def get_category(self, category_id, file_type='json'):
        """
        Retrieve information about a specific category from the FRED API.
        Parameters:
        category_id (int): The ID of the category to retrieve.
        file_type (str, optional): The format of the response. Defaults to 'json'.
        Returns:
        dict or str: The response from the FRED API in the specified format.
        Raises:
        ValueError: If the response from the FRED API indicates an error.
        Example:
        >>> fred_instance.get_category(125)
        {'id': 125, 'name': 'Production & Business Activity', ...}
        Reference:
        https://fred.stlouisfed.org/docs/api/fred/category.html
        """
        url_endpoint = '/category'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_category_children(self, category_id, realtime_start=None, realtime_end=None,
                              file_type='json'):
        """
        Get the child categories for a specified category ID from the FRED API.
        Parameters:
        category_id (int): The ID for the category whose children are to be retrieved.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        file_type (str, optional): The format of the response. Default is 'json'. Other 
        options include 'xml'.
        Returns:
        dict: A dictionary containing the child categories for the specified category ID.
        Raises:
        ValueError: If the API request fails or returns an error.
        FRED API Documentation:
        https://fred.stlouisfed.org/docs/api/fred/category_children.html
        """
        url_endpoint = '/category/children'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_category_related(self, category_id, realtime_start=None, realtime_end=None,
                             file_type='json'):
        """
        Get related categories for a given category ID from the FRED API.
        Parameters:
        category_id (int): The ID for the category.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        file_type (str, optional): The format of the response. Default is 'json'. Options 
        are 'json', 'xml'.
        Returns:
        dict or str: The response from the FRED API. The format depends on the file_type parameter.
        Raises:
        ValueError: If the API request fails or returns an error.
        FRED API Documentation:
        https://fred.stlouisfed.org/docs/api/fred/category_related.html
        """
        url_endpoint = '/category/related'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_category_series(self, category_id, realtime_start=None, realtime_end=None,
                            limit=None, offset=None, order_by=None, sort_order=None,
                            filter_variable=None, filter_value=None, tag_names=None,
                            exclude_tag_names=None, file_type='json'):
        """
        Get the series in a category.
        Parameters:
        category_id (int): The ID for a category.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        limit (int, optional): The maximum number of results to return. Default is 1000.
        offset (int, optional): The offset for the results. Used for pagination.
        order_by (str, optional): Order results by values. Options are 'series_id', 'title', 
        'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 
        'last_updated', 'observation_start', 'observation_end', 'popularity', 'group_popularity'.
        sort_order (str, optional): Sort results in ascending or descending order. Options are 
        'asc' or 'desc'.
        filter_variable (str, optional): The attribute to filter results by. Options are 
        'frequency', 'units', 'seasonal_adjustment'.
        filter_value (str, optional): The value of the filter_variable to filter results by.
        tag_names (str, optional): A semicolon-separated list of tag names to filter results by.
        exclude_tag_names (str, optional): A semicolon-separated list of tag names to exclude 
        results by.
        file_type (str, optional): The type of file to return. Default is 'json'. Options are 
        'json', 'xml'.
        Returns:
        dict: A dictionary containing the series in the specified category.
        Raises:
        ValueError: If the request to the FRED API fails or returns an error.
        """
        url_endpoint = '/category/series'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        if filter_variable:
            data['filter_variable'] = filter_variable
        if filter_value:
            data['filter_value'] = filter_value
        if tag_names:
            data['tag_names'] = tag_names
        if exclude_tag_names:
            data['exclude_tag_names'] = exclude_tag_names
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_category_tags(self, category_id, realtime_start=None, realtime_end=None,
                          tag_names=None, tag_group_id=None, search_text=None,limit=None,
                          offset=None, order_by=None, sort_order=None, file_type='json'):
        """
        Get the tags for a category.
        Parameters:
        category_id (int): The ID for a category.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        tag_names (str, optional): A semicolon delimited list of tag names to filter tags by.
        tag_group_id (int, optional): A tag group ID to filter tags by type.
        search_text (str, optional): The words to find matching tags with.
        limit (int, optional): The maximum number of results to return. Default is 1000.
        offset (int, optional): The offset for the results. Used for pagination.
        order_by (str, optional): Order results by values. Options are 'series_count', 
        'popularity', 'created', 'name'. Default is 'series_count'.
        sort_order (str, optional): Sort results in ascending or descending order. Options are
        'asc', 'desc'. Default is 'desc'.
        file_type (str, optional): A key that indicates the type of file to send. Default is 'json'.
        Returns:
        dict: A dictionary containing the tags for the specified category.
        """
        url_endpoint = '/category/tags'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_category_related_tags(self, category_id, realtime_start=None, realtime_end=None,
                                  tag_names=None, exclude_tag_names=None, tag_group_id=None,
                                  search_text=None, limit=None, offset=None, order_by=None,
                                  sort_order=None, file_type='json'):
        """
        Retrieve related tags for a specified category from the FRED API.
        Parameters:
        category_id (int): The ID for the category.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        tag_names (str, optional): A semicolon-delimited list of tag names to include.
        exclude_tag_names (str, optional): A semicolon-delimited list of tag names to exclude.
        tag_group_id (int, optional): The ID for a tag group.
        search_text (str, optional): The words to find matching tags with.
        limit (int, optional): The maximum number of results to return.
        offset (int, optional): The offset for the results.
        order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
        sort_order (str, optional): Sort order, either 'asc' or 'desc'.
        file_type (str, optional): The type of file to return. Default is 'json'.
        Returns:
        dict: A dictionary containing the related tags for the specified category.
        Raises:
        ValueError: If the request to the FRED API fails or returns an error.
        """
        url_endpoint = '/category/related_tags'
        data = {
            'category_id': category_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if exclude_tag_names:
            data['exclude_tag_names'] = exclude_tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    ## Releases
    def get_releases(self, realtime_start=None, realtime_end=None, limit=None, offset=None,
                     order_by=None, sort_order=None, file_type='json'):
        """
        Get economic data releases from the FRED API.
        Parameters:
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        limit (int, optional): The maximum number of results to return. Default is None.
        offset (int, optional): The offset for the results. Default is None.
        order_by (str, optional): Order results by values such as 'release_id', 'name', 
        'press_release', 'realtime_start', 'realtime_end'. Default is None.
        sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) 
        order. Default is None.
        file_type (str, optional): The format of the response. Default is 'json'.
        Returns:
        dict: A dictionary containing the releases data from the FRED API.
        Raises:
        ValueError: If the API request fails or returns an error.
        """
        url_endpoint = '/releases'
        data = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_releases_dates(self, realtime_start=None, realtime_end=None, limit=None, offset=None,
                           order_by=None, sort_order=None, include_releases_dates_with_no_data=None,
                           file_type='json'):
        """
        Get release dates for economic data releases.
        This method retrieves the release dates for economic data releases from the 
        Federal Reserve Economic Data (FRED) API.
        Parameters:
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        limit (int, optional): The maximum number of results to return. Default is None.
        offset (int, optional): The offset for the results. Default is None.
        order_by (str, optional): Order results by values. Options include 'release_id', 
        'release_name', 'release_date', 'realtime_start', 'realtime_end'. Default is None.
        sort_order (str, optional): Sort order of results. Options include 'asc' (ascending) 
        or 'desc' (descending). Default is None.
        include_releases_dates_with_no_data (bool, optional): Whether to include release dates 
        with no data. Default is None.
        file_type (str, optional): The format of the response. Options include 'json', 'xml'. 
        Default is 'json'.
        Returns:
        dict: A dictionary containing the release dates for economic data releases.
        Raises:
        Exception: If the request to the FRED API fails.
        Example:
        >>> fred = Fred(api_key='your_api_key')
        >>> fred.get_releases_dates(realtime_start='2022-01-01', realtime_end='2022-12-31')
        """
        url_endpoint = '/releases/dates'
        data = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        if include_releases_dates_with_no_data:
            data['include_releases_dates_with_no_data'] = include_releases_dates_with_no_data
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_release(self, release_id, realtime_start=None, realtime_end=None, file_type='json'):
        """
        Get the release for a given release ID from the FRED API.
        Parameters:
        release_id (int): The ID for the release.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        file_type (str, optional): A key indicating the file type of the response. Default 
        is 'json'.
        Returns:
        dict or str: The release data in the specified file type format.
        Raises:
        ValueError: If the request to the FRED API fails or returns an error.
        FRED API Documentation:
        https://fred.stlouisfed.org/docs/api/fred/release.html
        """
        url_endpoint = '/release/'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_release_dates(self, release_id, realtime_start=None, realtime_end=None, limit=None,
                          offset=None, sort_order=None, include_releases_dates_with_no_data=None,
                          file_type='json'):
        """
        Get the release dates for a given release ID from the FRED API.
        Parameters:
        release_id (int): The ID for the release.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        limit (int, optional): The maximum number of results to return.
        offset (int, optional): The offset for the results.
        sort_order (str, optional): The order of the results. Possible values are 'asc' or 'desc'.
        include_releases_dates_with_no_data (bool, optional): Whether to include release dates 
        with no data.
        file_type (str, optional): The type of file to return. Default is 'json'.
        Returns:
        dict: A dictionary containing the release dates and related information.
        Raises:
        ValueError: If the API request fails or returns an error.
        Example:
        >>> fred = Fred(api_key='your_api_key')
        >>> release_dates = fred.get_release_dates(release_id=123)
        >>> print(release_dates)
        """
        url_endpoint = '/release/dates'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        if include_releases_dates_with_no_data:
            data['include_releases_dates_with_no_data'] = include_releases_dates_with_no_data
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_release_series(self, release_id, realtime_start=None, realtime_end=None, limit=None,
                           offset=None, sort_order=None, filter_variable=None, filter_value=None,
                           exclude_tag_names=None, file_type='json'):
        """
        Get the series in a release.
        Parameters:
        release_id (int): The ID for the release.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        limit (int, optional): The maximum number of results to return. Default is 1000.
        offset (int, optional): The offset for the results. Default is 0.
        sort_order (str, optional): Order results by values. Options are 'asc' or 'desc'.
        filter_variable (str, optional): The attribute to filter results by.
        filter_value (str, optional): The value of the filter variable.
        exclude_tag_names (str, optional): A semicolon-separated list of tag names to exclude.
        file_type (str, optional): The type of file to return. Default is 'json'.
        Returns:
        dict: A dictionary containing the response from the FRED API.
        Raises:
        ValueError: If the API request fails or returns an error.
        """
        url_endpoint = '/release/series'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        if filter_variable:
            data['filter_variable'] = filter_variable
        if filter_value:
            data['filter_value'] = filter_value
        if exclude_tag_names:
            data['exclude_tag_names'] = exclude_tag_names
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_release_sources(self, release_id, realtime_start=None, realtime_end=None,
                            file_type='json'):
        """
        Retrieve the sources for a specified release from the FRED API.
        Parameters:
        release_id (int): The ID of the release for which to retrieve sources.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. 
        Defaults to None.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. 
        Defaults to None.
        file_type (str, optional): The format of the response. Options are 'json' or 'xml'. 
        Defaults to 'json'.
        Returns:
        dict or xml.etree.ElementTree.Element: The response from the FRED API in the 
        specified format.
        Raises:
        ValueError: If the API request fails or returns an error.
        Example:
        >>> fred = Fred(api_key='your_api_key')
        >>> sources = fred.get_release_sources(release_id=123)
        >>> print(sources)
        """
        url_endpoint = '/release/sources'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_release_tags(self, release_id, realtime_start=None, realtime_end=None, tag_names=None,
                         tag_group_id=None, search_text=None, limit=None, offset=None,
                         order_by=None, file_type='json'):
        """
        Get the release tags for a given release ID from the FRED API.
        Parameters:
        release_id (int): The ID for the release.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        tag_names (str, optional): A semicolon delimited list of tag names.
        tag_group_id (int, optional): The ID for a tag group.
        search_text (str, optional): The words to find matching tags with.
        limit (int, optional): The maximum number of results to return. Default is 1000.
        offset (int, optional): The offset for the results. Default is 0.
        order_by (str, optional): Order results by values. Options are 'series_count', 
        'popularity', 'created', 'name', 'group_id'. Default is 'series_count'.
        file_type (str, optional): The type of file to return. Default is 'json'.
        Returns:
        dict: A dictionary containing the release tags data from the FRED API.
        Raises:
        ValueError: If the API request fails or returns an error.
        """
        url_endpoint = '/release/tags'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_release_related_tags(self, series_search_text, realtime_start=None, realtime_end=None,
                                 tag_names=None, tag_group_id=None, tag_search_text=None,
                                 limit=None, offset=None, order_by=None, sort_order=None,
                                 file_type='json'):
        """
        Get release related tags for a given series search text.
        This method retrieves tags related to a release for a given series search text from 
        the FRED API.
        Parameters:
        series_search_text (str): The text to match against economic data series.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        tag_names (str, optional): A semicolon delimited list of tag names to match.
        tag_group_id (str, optional): A tag group id to filter tags by type.
        tag_search_text (str, optional): The text to match against tags.
        limit (int, optional): The maximum number of results to return.
        offset (int, optional): The offset for the results.
        order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 
        'created', 'name', 'group_id'.
        sort_order (str, optional): Sort order of results. Options: 'asc', 'desc'.
        file_type (str, optional): The type of file to return. Default is 'json'.
        Returns:
        dict: A dictionary containing the related tags data from the FRED API.
        Raises:
        ValueError: If the API request fails or returns an error.
        """
        url_endpoint = '/release/related_tags'
        data = {
            'series_search_text': series_search_text,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if tag_search_text:
            data['tag_search_text'] = tag_search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_release_tables(self, release_id, element_id=None, include_observation_values=None,
                           observation_date=None, file_type='json'):
        """
        Fetches release tables from the FRED API.
        Parameters:
        release_id (int): The ID for the release.
        element_id (int, optional): The ID for the element. Defaults to None.
        include_observation_values (bool, optional): Whether to include observation values. 
        Defaults to None.
        observation_date (str, optional): The observation date in YYYY-MM-DD format. Defaults 
        to None.
        file_type (str, optional): The format of the returned data. Defaults to 'json'.
        Returns:
        dict: The response from the FRED API containing the release tables.
        Raises:
        ValueError: If the API request fails or returns an error.
        """

        url_endpoint = '/release/tables'
        data = {
            'release_id': release_id,
            'file_type': file_type
        }
        if element_id:
            data['element_id'] = element_id
        if include_observation_values:
            data['include_observation_values'] = include_observation_values
        if observation_date:
            data['observation_date'] = observation_date
        result = self.__fred_get_request(url_endpoint, data)
        return result
    ## Series
    def get_series(self, series_id, realtime_start=None, realtime_end=None, file_type='json'):
        """
        Retrieve economic data series information from the FRED API.
        Parameters:
        series_id (str): The ID for the economic data series.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        file_type (str, optional): The format of the returned data. Default is 'json'. Options 
        are 'json', 'xml', 'txt', etc.
        Returns:
        dict or str: The response from the FRED API in the specified file_type format.
        Raises:
        ValueError: If the series_id is not provided.
        HTTPError: If the request to the FRED API fails.
        Example:
        >>> fred = Fred(api_key='your_api_key')
        >>> series_data = fred.get_series('GNPCA')
        >>> print(series_data)
        """

        url_endpoint = '/series'
        data = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_series_categories(self, series_id, realtime_start=None, realtime_end=None,
                              file_type='json'):
        """
        Get the categories for a specified series.
        Parameters:
        series_id (str): The ID for the series.
        realtime_start (str, optional): The start of the real-time period. Defaults to None.
        realtime_end (str, optional): The end of the real-time period. Defaults to None.
        file_type (str, optional): The type of file to return. Defaults to 'json'.
        Returns:
        dict: A dictionary containing the categories for the specified series.
        Raises:
        ValueError: If the series_id is not provided or invalid.
        HTTPError: If the request to the FRED API fails.
        FRED API Documentation:
        https://fred.stlouisfed.org/docs/api/fred/series_categories.html
        """

        url_endpoint = '/series/categories'
        data = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_series_observation(self, series_id, realtime_start=None, realtime_end=None, limit=None,
                               offset=None, sort_order=None, observation_start=None,
                               observation_end=None, units=None, frequency=None,
                               aggregation_method=None, output_type=None, vintage_dates=None,
                               file_type='json'):
        """
        Get observations for a FRED series.
        Parameters:
        series_id (str): The ID for a series.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        limit (int, optional): The maximum number of results to return. Default is 100000.
        offset (int, optional): The offset for the results. Used for pagination.
        sort_order (str, optional): Sort results by observation date. Options: 'asc', 'desc'.
        observation_start (str, optional): The start of the observation period. Format: YYYY-MM-DD.
        observation_end (str, optional): The end of the observation period. Format: YYYY-MM-DD.
        units (str, optional): A key that indicates a data transformation. Options: 'lin', 'chg', 
        'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'.
        frequency (str, optional): An optional parameter to change the frequency of the 
        observations. Options: 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 
        'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'.
        aggregation_method (str, optional): A key that indicates the aggregation method used 
        for frequency aggregation. Options: 'avg', 'sum', 'eop'.
        output_type (int, optional): An integer indicating the type of output. Options: 1 
        (observations by realtime period), 2 (observations by vintage date), 3 (observations by 
        vintage date and realtime period).
        vintage_dates (str, optional): A comma-separated string of vintage dates. 
        Format: YYYY-MM-DD.
        file_type (str, optional): A key that indicates the file type of the response. 
        Default is 'json'. Options: 'json', 'xml'.
        Returns:
        dict: A dictionary containing the observations for the specified series.
        Raises:
        Exception: If the request to the FRED API fails.
        """
        url_endpoint = '/series/observations'
        data = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        if observation_start:
            data['observation_start'] = observation_start
        if observation_end:
            data['observation_end'] = observation_end
        if units:
            data['units'] = units
        if frequency:
            data['frequency'] = frequency
        if aggregation_method:
            data['aggregation_method'] = aggregation_method
        if output_type:
            data['output_type'] = output_type
        if vintage_dates:
            data['vintage_dates'] = vintage_dates
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_series_release(self, series_id, realtime_start=None, realtime_end=None,
                           file_type='json'):
        """
        Get the release for a specified series from the FRED API.
        Parameters:
        series_id (str): The ID for the series.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. 
        Defaults to None.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. 
        Defaults to None.
        file_type (str, optional): The format of the response. Options are 'json', 'xml'. 
        Defaults to 'json'.
        Returns:
        dict or str: The release information for the specified series. The format depends 
        on the file_type parameter.
        Raises:
        ValueError: If the series_id is not provided or invalid.
        HTTPError: If the request to the FRED API fails.
        FRED API Documentation:
        https://fred.stlouisfed.org/docs/api/fred/series_release.html
        """
        url_endpoint = '/series/release'
        data = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_series_search(self, search_text, search_type=None, realtime_start=None,
                          realtime_end=None, limit=None, offset=None, order_by=None,
                          sort_order=None, filter_variable=None, filter_value=None,
                          tag_names=None, exclude_tag_names=None, file_type='json'):
        """
        Searches for economic data series based on text queries.
        This method interacts with the FRED (Federal Reserve Economic Data) API to search 
        for economic data series that match the provided search text and optional parameters.
        Parameters:
        search_text (str): The text to search for in economic data series.
        search_type (str, optional): The type of search to perform. Options include 'full_text' 
        or 'series_id'. Defaults to None.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. 
        Defaults to None.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. 
        Defaults to None.
        limit (int, optional): The maximum number of results to return. Defaults to None.
        offset (int, optional): The offset for the results. Defaults to None.
        order_by (str, optional): The attribute to order results by. Options include 
        'search_rank', 'series_id', 'title', etc. Defaults to None.
        sort_order (str, optional): The order to sort results. Options include 'asc' or 
        'desc'. Defaults to None.
        filter_variable (str, optional): The variable to filter results by. Defaults to None.
        filter_value (str, optional): The value to filter results by. Defaults to None.
        tag_names (str, optional): A comma-separated list of tag names to include in the search.
        Defaults to None.
        exclude_tag_names (str, optional): A comma-separated list of tag names to exclude from 
        the search. Defaults to None.
        file_type (str, optional): The format of the response. Options include 'json', 'xml'. 
        Defaults to 'json'.
        Returns:
        dict: The response from the FRED API containing the search results.
        Raises:
        Exception: If the API request fails or returns an error.
        """
        url_endpoint = '/series/search'
        data = {
            'search_text': search_text,
            'file_type': file_type
        }
        if search_type:
            data['search_type'] = search_type
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        if filter_variable:
            data['filter_variable'] = filter_variable
        if filter_value:
            data['filter_value'] = filter_value
        if tag_names:
            data['tag_names'] = tag_names
        if exclude_tag_names:
            data['exclude_tag_names'] = exclude_tag_names
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_series_search_tags(self, series_search_text, realtime_start=None, realtime_end=None,
                               tag_names=None, tag_group_id=None, tag_search_text=None, limit=None,
                               offset=None, order_by=None, sort_order=None, file_type='json'):
        """
        Get the tags for a series search.
        This method retrieves the tags for a series search based on the provided search text and 
        optional parameters.
        Parameters:
        series_search_text (str): The words to match against economic data series.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        tag_names (str, optional): A semicolon-delimited list of tag names to match.
        tag_group_id (str, optional): A tag group id to filter tags by type.
        tag_search_text (str, optional): The words to match against tags.
        limit (int, optional): The maximum number of results to return. Default is 1000.
        offset (int, optional): The offset for the results. Default is 0.
        order_by (str, optional): Order results by values of the specified attribute. Options 
        are 'series_count', 'popularity', 'created', 'name', 'group_id'.
        sort_order (str, optional): Sort results in ascending or descending order. Options 
        are 'asc' or 'desc'. Default is 'asc'.
        file_type (str, optional): The type of file to return. Default is 'json'.
        Returns:
        dict: A dictionary containing the tags for the series search.
        See also:
        https://fred.stlouisfed.org/docs/api/fred/series_search_tags.html
        """
        url_endpoint = '/series/search/tags'
        data = {
            'series_search_text': series_search_text,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if tag_search_text:
            data['tag_search_text'] = tag_search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_series_search_related_tags(self, series_search_text, realtime_start=None,
                                       realtime_end=None, tag_names=None, exclude_tag_names=None,
                                       tag_group_id=None, tag_search_text=None, limit=None,
                                       offset=None, order_by=None, sort_order=None,
                                       file_type='json'):
        """
        Get related tags for a series search text.
        This method retrieves related tags for a given series search text from the FRED API.
        Parameters:
        series_search_text (str): The text to search for series.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        tag_names (str, optional): A semicolon-delimited list of tag names to include.
        exclude_tag_names (str, optional): A semicolon-delimited list of tag names to exclude.
        tag_group_id (str, optional): The tag group id to filter tags by type.
        tag_search_text (str, optional): The text to search for tags.
        limit (int, optional): The maximum number of results to return. Default is 1000.
        offset (int, optional): The offset for the results. Used for pagination.
        order_by (str, optional): Order results by values. Options are 'series_count', 
        'popularity', 'created', 'name', 'group_id'.
        sort_order (str, optional): Sort order of results. Options are 'asc' (ascending) 
        or 'desc' (descending).
        file_type (str, optional): The type of file to return. Default is 'json'.
        Returns:
        dict: A dictionary containing the related tags for the series search text.
        Raises:
        ValueError: If the API request fails or returns an error.
        Example:
        >>> fred = Fred(api_key='your_api_key')
        >>> related_tags = fred.get_series_search_related_tags('GDP')
        >>> print(related_tags)
        """
        url_endpoint = '/series/search/related_tags'
        data = {
            'series_search_text': series_search_text,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if exclude_tag_names:
            data['exclude_tag_names'] = exclude_tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if tag_search_text:
            data['tag_search_text'] = tag_search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_series_tags(self, series_id, realtime_start=None, realtime_end=None, order_by=None,
                        sort_order=None, file_type='json'):
        """
        Get the tags for a series.
        Parameters:
        series_id (str): The ID for a series.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        order_by (str, optional): Order results by values such as 'series_id', 'name', 
        'popularity', etc.
        sort_order (str, optional): Sort results in 'asc' (ascending) or 'desc' (descending) order.
        file_type (str, optional): A key that indicates the type of file to download. Default 
        is 'json'.
        Returns:
        dict: A dictionary containing the tags for the series.
        Endpoint:
        https://api.stlouisfed.org/fred/series/tags
        Example:
        >>> get_series_tags('GNPCA')
        """
        url_endpoint = '/series/tags'
        data = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_series_updates(self, realtime_start=None, realtime_end=None, limit=None, offset=None,
                           filter_value=None, start_time=None, end_time=None, file_type='json'):
        """
        Retrieves updates for a series from the FRED API.
        Parameters:
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        limit (int, optional): The maximum number of results to return. Default is 1000.
        offset (int, optional): The offset for the results. Used for pagination.
        filter_value (str, optional): Filter results by this value.
        start_time (str, optional): The start time for the updates. Format: HH:MM.
        end_time (str, optional): The end time for the updates. Format: HH:MM.
        file_type (str, optional): The format of the returned data. Default is 'json'. 
        Options are 'json' or 'xml'.
        Returns:
        dict: A dictionary containing the series updates from the FRED API.
        Raises:
        requests.exceptions.RequestException: If an error occurs during the API request.
        Example:
        >>> fred = Fred(api_key='your_api_key')
        >>> updates = fred.get_series_updates(realtime_start='2020-01-01', 
        realtime_end='2020-01-31')
        >>> print(updates)
        """
        url_endpoint = '/series/updates'
        data = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if filter_value:
            data['filter_value'] = filter_value
        if start_time:
            data['start_time'] = start_time
        if end_time:
            data['end_time'] = end_time
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_series_vintagedates(self, series_id, realtime_start=None, realtime_end=None, limit=None,
                                offset=None, sort_order=None, file_type='json'):
        """
        Get the vintage dates for a given FRED series.
        Parameters:
        series_id (str): The ID for the FRED series.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        limit (int, optional): The maximum number of results to return.
        offset (int, optional): The offset for the results.
        sort_order (str, optional): The order of the results. Possible values: 'asc' or 'desc'.
        file_type (str, optional): The format of the returned data. Default is 'json'.
        Returns:
        dict: A dictionary containing the vintage dates for the specified series.
        Raises:
        ValueError: If the series_id is not provided.
        """
        url_endpoint = '/series/vintagedates'
        data = {
            'series_id': series_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    ## Sources
    def get_sources(self, realtime_start=None, realtime_end=None, limit=None, offset=None,
                    order_by=None, sort_order=None, file_type='json'):
        """
        Retrieve sources of economic data from the FRED API.
        Parameters:
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        limit (int, optional): The maximum number of results to return. Default is 1000,
        maximum is 1000.
        offset (int, optional): The offset for the results. Used for pagination.
        order_by (str, optional): Order results by values. Options are 'source_id', 'name', 
        'realtime_start', 'realtime_end'.
        sort_order (str, optional): Sort order of results. Options are 'asc' (ascending) or 
        'desc' (descending).
        file_type (str, optional): The format of the returned data. Default is 'json'. Options 
        are 'json', 'xml'.
        Returns:
        dict: A dictionary containing the sources of economic data.
        Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP request.
        """
        url_endpoint = '/sources'
        data = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_source(self, source_id, realtime_start=None, realtime_end=None, file_type='json'):
        """
        Retrieves information about a source from the FRED API.
        Parameters:
        source_id (int): The ID for the source.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD. 
        Defaults to None.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD. 
        Defaults to None.
        file_type (str, optional): The format of the file to be returned. Options are 'json', 
        'xml'. Defaults to 'json'.
        Returns:
        dict: A dictionary containing the source information.
        Raises:
        ValueError: If the request to the FRED API fails or returns an error.
        Example:
        >>> fred = Fred(api_key='your_api_key')
        >>> source_info = fred.get_source(source_id=1)
        >>> print(source_info)
        """
        url_endpoint = '/source'
        data = {
            'source_id': source_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_source_releases(self, source_id, realtime_start=None, realtime_end=None, limit=None,
                            offset=None, order_by=None, sort_order=None, file_type='json'):
        """
        Get the releases for a specified source from the FRED API.
        Parameters:
        source_id (int): The ID for the source.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        limit (int, optional): The maximum number of results to return.
        offset (int, optional): The offset for the results.
        order_by (str, optional): Order results by values such as 'release_id', 'name', etc.
        sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for 
        descending.
        file_type (str, optional): The format of the response. Default is 'json'.
        Returns:
        dict: A dictionary containing the releases for the specified source.
        Raises:
        ValueError: If the source_id is not provided or invalid.
        Example:
        >>> fred = Fred(api_key='your_api_key')
        >>> releases = fred.get_source_releases(source_id=1)
        >>> print(releases)
        """
        url_endpoint = '/source/releases'
        data = {
            'source_id': source_id,
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    ## Tags
    def get_tags(self, realtime_start=None, realtime_end=None, tag_names=None, tag_group_id=None,
                search_text=None, limit=None, offset=None, order_by=None, sort_order=None,
                file_type='json'):
        """
        Retrieve FRED tags based on specified parameters.
        Parameters:
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        tag_names (str, optional): A semicolon-delimited list of tag names to filter results.
        tag_group_id (str, optional): A tag group ID to filter results.
        search_text (str, optional): The words to match against tag names and descriptions.
        limit (int, optional): The maximum number of results to return. Default is 1000.
        offset (int, optional): The offset for the results. Used for pagination.
        order_by (str, optional): Order results by values such as 'series_count', 'popularity', etc.
        sort_order (str, optional): Sort order of results. 'asc' for ascending, 'desc' for 
        descending.
        file_type (str, optional): The format of the returned data. Default is 'json'.
        Returns:
        dict: A dictionary containing the FRED tags that match the specified parameters.
        Raises:
        ValueError: If the API request fails or returns an error.
        """
        url_endpoint = '/tags'
        data = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_related_tags(self, realtime_start=None, realtime_end=None, tag_names=None,
                         exclude_tag_names=None, tag_group_id=None, search_text=None, limit=None,
                         offset=None, order_by=None, sort_order=None, file_type='json'):
        """
        Retrieve related tags for a given set of tags from the FRED API.
        Parameters:
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        tag_names (str, optional): A semicolon-delimited list of tag names to include in the search.
        exclude_tag_names (str, optional): A semicolon-delimited list of tag names to exclude from 
        the search.
        tag_group_id (str, optional): A tag group ID to filter tags by group.
        search_text (str, optional): The words to match against tag names and descriptions.
        limit (int, optional): The maximum number of results to return. Default is 1000.
        offset (int, optional): The offset for the results. Used for pagination.
        order_by (str, optional): Order results by values. Options: 'series_count', 'popularity', 
        'created', 'name', 'group_id'.
        sort_order (str, optional): Sort order of results. Options: 'asc' (ascending), 'desc' 
        (descending). Default is 'asc'.
        file_type (str, optional): The type of file to return. Default is 'json'.
        Returns:
        dict: A dictionary containing the related tags data from the FRED API.
        Raises:
        ValueError: If the API request fails or returns an error.
        """
        url_endpoint = '/related_tags'
        data = {
            'file_type': file_type
        }
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if tag_names:
            data['tag_names'] = tag_names
        if exclude_tag_names:
            data['exclude_tag_names'] = exclude_tag_names
        if tag_group_id:
            data['tag_group_id'] = tag_group_id
        if search_text:
            data['search_text'] = search_text
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_tags_series(self, tag_names=None, exclude_tag_names=None, realtime_start=None,
                        realtime_end=None, limit=None, offset=None, order_by=None,
                        sort_order=None, file_type='json'):
        """
        Get the series matching tags.
        Parameters:
        tag_names (str, optional): A semicolon delimited list of tag names to include in the search.
        exclude_tag_names (str, optional): A semicolon delimited list of tag names to exclude in 
        the search.
        realtime_start (str, optional): The start of the real-time period. Format: YYYY-MM-DD.
        realtime_end (str, optional): The end of the real-time period. Format: YYYY-MM-DD.
        limit (int, optional): The maximum number of results to return. Default is 1000.
        offset (int, optional): The offset for the results. Default is 0.
        order_by (str, optional): Order results by values. Options: 'series_id', 'title', 'units', 
        'frequency', 'seasonal_adjustment', 'realtime_start', 'realtime_end', 'last_updated', 
        'observation_start', 'observation_end', 'popularity', 'group_popularity'.
        sort_order (str, optional): Sort results in ascending or descending order. Options: 'asc', 
        'desc'.
        file_type (str, optional): The type of file to return. Default is 'json'. Options: 'json', 
        'xml'.
        Returns:
        dict: A dictionary containing the series matching the tags.
        """
        url_endpoint = '/tags/series'
        data = {
            'file_type': file_type
        }
        if tag_names:
            data['tag_names'] = tag_names
        if exclude_tag_names:
            data['exclude_tag_names'] = exclude_tag_names
        if realtime_start:
            data['realtime_start'] = realtime_start
        if realtime_end:
            data['realtime_end'] = realtime_end
        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if order_by:
            data['order_by'] = order_by
        if sort_order:
            data['sort_order'] = sort_order
        result = self.__fred_get_request(url_endpoint, data)
        return result
