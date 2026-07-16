# filepath: /src/fedfred/clients/fraser.py
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
"""fedfred.clients.fraser

This module defines the Fraser client for interacting with the Federal Reserve Fraser API.
"""

from .._internals import _AsyncBaseClient, _BaseClient


class Fraser(_BaseClient):
    """Client for the Federal Reserve FRASER API.

    The Fraser class contains methods for interacting with the Federal Reserve FRASER API,
    and provides synchronous endpoints with automatic parameter conversion, unified response
    objects, rate limiting, retries, and typed results.

    Attributes:
        api_key (Optional[str]): The API key for accessing the Fraser API.
        base_url (str): The base URL for the Fraser API.
        cache_mode (bool): Whether to enable caching for GET requests.
        cache_size (int): The maximum size of the cache for GET requests.
        cache (FIFOCache): The cache object for storing GET request responses.
        max_requests_per_minute (int): The maximum number of requests allowed per minute.
        request_times (deque): A deque to track the timestamps of recent requests for rate limiting.

    Args:
        api_key (Optional[str]): The API key for accessing the Fraser API. If None, it will be resolved from configuration.
        cache_mode (bool): Whether to enable caching for GET requests. Default is True.
        cache_size (int): The maximum size of the cache for GET requests. Default is 256.

    Raises:
        RuntimeError: If the API key is not provided for GET requests.

    Notes:
        API keys can be set globally using the :class:`set_api_key` function or provided per-client during initialization.
        The FRASER API uses a different API key then the FRED API.

    Examples:
        >>> import fedfred as fd
        >>> fraser_client = fd.Fraser(api_key="your_fraser_api_key")

    See Also:
        - :func:`fedfred.set_api_key`
        - :func:`fedfred.get_api_key`
    """

    # Public Methods
    ## API-Key
    def post_key_request(self, email: str, description: str) -> None:
        """ """
        url_endpoint = "/api-key"
        data = {
            "email": email,
            "description": description,
        }
        self._client_post_request(url_endpoint, data)
        return None

    ## Titles
    def get_single_title(self, title_id: int, limit: int | None = None, page: int | None = None):

        url_endpoint = f"/title/{title_id}"
        data = {}
        if limit:
            data["limit"] = limit
        if page:
            data["page"] = page
        response = self.__fraser_get_request(url_endpoint, data)

    def get_all_title_items(self, title_id: int, limit: int | None = None, page: int | None = None):

        url_endpoint = f"/title/{title_id}/items"
        data = {}
        if limit:
            data["limit"] = limit
        if page:
            data["page"] = page
        response = self.__fraser_get_request(url_endpoint, data)

    def get_single_title_table_of_contents(self, title_id: int):

        url_endpoint = f"/title/{title_id}/toc"
        response = self.__fraser_get_request(url_endpoint)

    ## Items
    def get_single_item(self, item_id: int):

        url_endpoint = f"/item/{item_id}"
        response = self.__fraser_get_request(url_endpoint)

    def get_single_item_table_of_contents(
        self, item_id: int, limit: int | None = None, page: int | None = None
    ):

        url_endpoint = f"/item/{item_id}/toc"
        data = {}
        if limit:
            data["limit"] = limit
        if page:
            data["page"] = page
        response = self.__fraser_get_request(url_endpoint, data)

    ## Table of Contents
    def get_table_of_contents(self, toc_id: int, limit: int | None = None, page: int | None = None):

        url_endpoint = f"/toc/{toc_id}"
        data = {}
        if limit:
            data["limit"] = limit
        if page:
            data["page"] = page
        response = self.__fraser_get_request(url_endpoint, data)

    ## Authors
    def get_all_authors(self, limit: int | None = None, page: int | None = None):

        url_endpoint = "/author"
        data = {}
        if limit:
            data["limit"] = limit
        if page:
            data["page"] = page
        response = self.__fraser_get_request(url_endpoint, data)

    def get_single_author(self, author_id: int):

        url_endpoint = f"/author/{author_id}"
        response = self.__fraser_get_request(url_endpoint)

    def get_all_author_records(self, author_id: int, role: str | None = None):

        url_endpoint = f"/author/{author_id}/records"
        data = {}
        if role:
            data["role"] = role
        response = self.__fraser_get_request(url_endpoint, data)

    ## Subjects
    def get_single_subject(self, subject_id: int):

        url_endpoint = f"/subject/{subject_id}"
        response = self.__fraser_get_request(url_endpoint)

    def get_all_subjects(self, limit: int | None = None, page: int | None = None):

        url_endpoint = "/subject"
        data = {}
        if limit:
            data["limit"] = limit
        if page:
            data["page"] = page
        response = self.__fraser_get_request(url_endpoint, data)

    def get_all_subject_records(
        self, subject_id: int, limit: int | None = None, page: int | None = None
    ):

        url_endpoint = f"/subject/{subject_id}/records"
        data = {}
        if limit:
            data["limit"] = limit
        if page:
            data["page"] = page
        response = self.__fraser_get_request(url_endpoint, data)

    ## Themes
    def get_all_themes(self, limit: int | None = None, page: int | None = None):

        url_endpoint = "/theme"
        data = {}
        if limit:
            data["limit"] = limit
        if page:
            data["page"] = page
        response = self.__fraser_get_request(url_endpoint, data)

    def get_single_theme(self, theme_id: int):

        url_endpoint = f"/theme/{theme_id}"
        response = self.__fraser_get_request(url_endpoint)

    def get_all_theme_records(self, theme_id: int):
        url_endpoint = f"/theme/{theme_id}/records"
        response = self.__fraser_get_request(url_endpoint)

    ## Timelines
    def get_single_timeline(self, timeline_id: int):

        url_endpoint = f"/timeline/{timeline_id}"
        response = self.__fraser_get_request(url_endpoint)

    def get_all_timelines(self, limit: int | None = None, page: int | None = None):

        url_endpoint = "/timeline"
        data = {}
        if limit:
            data["limit"] = limit
        if page:
            data["page"] = page
        response = self.__fraser_get_request(url_endpoint, data)

    def get_all_timeline_events(
        self, timeline_id: int, limit: int | None = None, page: int | None = None
    ):

        url_endpoint = f"/timeline/{timeline_id}/events"
        data = {}
        if limit:
            data["limit"] = limit
        if page:
            data["page"] = page
        response = self.__fraser_get_request(url_endpoint, data)


class AsyncFraser(_AsyncBaseClient):
    pass
