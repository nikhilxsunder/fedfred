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
    def get_category(self, category_id=None, file_type='json'):
        url_endpoint = '/category'
        data = {
            'file_type': file_type
        }
        if category_id:
            data['category_id'] = category_id
        result = self.__fred_get_request(url_endpoint, data)
        return result
    def get_category_children(self, category_id=None, realtime_start=None, realtime_end=None, file_type='json'):
        pass
    def get_category_related(self, category_id=None, realtime_start=None, realtime_end=None, file_type='json'):
        pass
    def get_category_series(self, category_id=None, realtime_start=None, realtime_end=None, limit=None, offset=None, 
                            order_by=None, sort_order=None, filter_variable=None, filter_value=None, 
                            tag_names=None, exclude_tag_names=None, file_type='json'):
        pass
    #def get_category_tags(self, file_type='json'):
    #def get_category_related_tags(self, file_type='json'):
    ## Releases
    #def get_releases(self, file_type='json'):
    #def get_releases_dates(self, file_type='json'): 
    #def get_release(self, file_type='json'):
    #def get_release_dates(self, file_type='json'):
    #def get_release_series(self, file_type='json'):
    #def get_release_sources(self, file_type='json'):
    #def get_release_tags(self, file_type='json'):
    #def get_release_related_tags(self, file_type='json'): 
    #def get_release_tables(self, file_type='json'): 
    ## Series
    #def get_series(self, file_type='json'):
    #def get_series_categories(self, file_type='json'):
    #def get_series_observation(self, file_type='json'):
    #def get_series_release(self, file_type='json'):
    #def get_series_search(self, file_type='json'):
    #def get_series_search_tags(self, file_type='json'):
    #def get_series_search_related_tags(self, file_type='json'): 
    #def get_series_tags(self, file_type='json'): 
    #def get_series_updates(self, file_type='json'): 
    #def get_series_vintagedates(self, file_type='json'): 
    ## Sources
    #def get_sources(self, file_type='json'): 
    #def get_source(self, file_type='json'): 
    #def get_source_releases(self, file_type='json'): 
    ## Tags
    #def get_tags(self, file_type='json'): 
    #def get_related_tags(self, file_type='json'): 
    #def get_tags_series(self, file_type='json'): 
