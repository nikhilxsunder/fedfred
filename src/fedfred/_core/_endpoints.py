# filepath: /src/fedfred/_core/_endpoints.py
#
# Copyright (c) 2025-2026 Nikhil Sunder
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
"""fedfred._core._endpoints

This module provides internal endpoint resolution for the fedfred core package.
"""

from dataclasses import dataclass
import asyncio
from typing import Dict, Optional, Any
from ..settings import _resolve_api_key
from ..exceptions import (
    EndpointUnsupportedError,
    EndpointPayloadError,
    EndpointParametersError,
    EndpointHeadersError,
    EndpointServiceError,
    EndpointURLError
)

__all__ = ["_resolve_endpoint", "_resolve_endpoint_async"]

_FRED_BASE_URL: str = "https://api.stlouisfed.org/fred"
"""Base URL for the FRED API."""

_GEOFRED_BASE_URL: str = "https://api.stlouisfed.org/geofred"
"""Base URL for the GeoFRED API."""

_FRASER_BASE_URL: str = "https://api.stlouisfed.org/fraser"
"""Base URL for the FRASER API."""

_FRED_ENDPOINT_MAP: Dict[str, str] = {
    # Category endpoints
    "get_categories": "/category",
    "get_category_children": "/category/children",
    "get_category_related": "/category/related",
    "get_category_series": "/category/series",
    "get_category_tags": "/category/tags",
    "get_category_related_tags": "/category/related_tags",
    # Release Endpoints
    "get_releases": "/releases",
    "get_releases_dates": "/releases/dates",
    "get_release": "/release",
    "get_release_dates": "/release/dates",
    "get_release_series": "/release/series",
    "get_release_sources": "/release/sources",
    "get_release_tags": "/release/tags",
    "get_release_related_tags": "/release/related_tags",
    "get_release_tables": "/release/tables",
    "get_release_observations": "/v2/release/observations",
    # Series Endpoints
    "get_series": "/series",
    "get_series_categories": "/series/categories",
    "get_series_observations": "/series/observations",
    "get_series_release": "/series/release",
    "get_series_search": "/series/search",
    "get_series_search_tags": "/series/search/tags",
    "get_series_search_related_tags": "/series/search/related_tags",
    "get_series_tags": "/series/tags",
    "get_series_updates": "/series/updates",
    "get_series_vintagedates": "/series/vintagedates",
    # Source Endpoints
    "get_sources": "/sources",
    "get_source": "/source",
    "get_source_releases": "/source/releases",
    # Tag Endpoints
    "get_tags": "/tags",
    "get_related_tags": "/related_tags",
    "get_tags_series": "/tags/series",
}
"""Mapping of FRED endpoint names to their corresponding paths."""

_GEOFRED_ENDPOINT_MAP: Dict[str, str] = {
    "get_shape_files": "/shapes/file",
    "get_series_group": "/series/group",
    "get_series_data": "/series/data",
    "get_regional_data": "/regional/data"
}
"""Mapping of GeoFRED endpoint names to their corresponding paths."""

_FRASER_ENDPOINT_MAP: Dict[str, str] = {
    # API key endpoints
    "post_key_request": "/api-key",
    # Titles endpoints
    "get_single_title": "/title/{title_id}",
    "get_all_title_items": "/title/{title_id}/items",
    "get_single_title_table_of_contents": "/title/{title_id}/toc",
    # Items endpoints
    "get_single_item": "/item/{item_id}",
    "get_single_item_table_of_contents": "/item/{item_id}/toc",
    # Table of contents endpoints
    "get_table_of_contents": "/toc/{toc_id}",
    # Author endpoints
    "get_all_authors": "/author",
    "get_single_author": "/author/{author_id}",
    "get_all_author_records": "/author/{author_id}/records",
    # Subjects endpoints
    "get_single_subject": "/subject/{subject_id}",
    "get_all_subjects": "/subject",
    "get_all_subject_records": "/subject/{subject_id}/records",
    # Themes endpoints
    "get_all_themes": "/theme",
    "get_single_theme": "/theme/{theme_id}",
    "get_all_theme_records": "/theme/{theme_id}/records",
    # Timeline endpoints
    "get_single_timeline": "/timeline/{timeline_id}",
    "get_all_timelines": "/timeline",
    "get_all_timeline_events": "/timeline/{timeline_id}/events",
}
"""Mapping of FRASER endpoint names to their corresponding paths."""

_FRED_BASE_PARAMETERS: Dict[str, str] = {
    'api_key': _resolve_api_key(service="fred"),
    'file_type': 'json'
}
"""Base parameters for all FRED API requests."""

_FRED_VERSION_TWO_BASE_PARAMETERS: Dict[str, str] = {
    'format': 'json'
}
"""Base parameters for FRED API version 2 requests."""

_GEOFRED_BASE_PARAMETERS: Dict[str, str] = _FRED_BASE_PARAMETERS
"""Base parameters for all GeoFRED API requests."""

_FRASER_BASE_PARAMETERS: Dict[str, str] = _FRED_VERSION_TWO_BASE_PARAMETERS
"""Base parameters for all FRASER API requests."""

_FRED_VERSION_TWO_HEADERS: Dict[str, str] = {
    'Authorization': f'Bearer {_resolve_api_key(service="fred")}',
    'format': 'json'
}
"""Headers for FRED API version 2 requests."""

_FRASER_HEADERS: Dict[str, str] = {
    "X-API-Key": _resolve_api_key(service="fraser")
}
"""Headers for FRASER API requests."""

@dataclass(frozen=True, slots=True)
class EndpointSpec:
    """Resolved request specification for an API endpoint.
    
    Attributes:
        service (str): The API service name (e.g., "fred", "geofred", "fraser").
        url (str): The absolute URL for the endpoint.
        params (Dict[str, str]): The default query parameters to include in requests to this endpoint.
        headers (Optional[Dict[str, str]]): The default headers to include in requests to this endpoint, if any.

    Examples:
        >>> # Internal use
        >>> from ._core import _resolve_endpoint
        >>> endpoint_spec = _resolve_endpoint("get_series_observations")
        >>> # Test functionality
        >>> print(endpoint_spec.service)
        >>> print(endpoint_spec.url)
        >>> print(endpoint_spec.params)
        >>> print(endpoint_spec.headers)
        fred
        https://api.stlouisfed.org/fred/series/observations
        {'api_key': 'your_fred_api_key', 'file_type': 'json'}
        None

    Notes:
        This dataclass is used internally to represent the resolved specifications for an API endpoint, including the absolute URL, default parameters, and headers. It is not intended for public use and may be subject to change without warning in future releases.
    """

    service: str
    """The API service name (e.g., "fred", "geofred", "fraser")."""

    url: str
    """The absolute URL for the endpoint."""

    params: Optional[Dict[str, str]] = None
    """The default query parameters to include in requests to this endpoint."""

    payload: Optional[Dict[str, Any]] = None
    """The default payload to include in POST requests to this endpoint, if any."""

    headers: Optional[Dict[str, str]] = None
    """The default headers to include in requests to this endpoint, if any."""

    def __post_init__(self) -> None:
        """Validate the resolved endpoint specification.

        Raises:
            EndpointServiceError: If the service name is invalid.
            EndpointURLError: If the URL is invalid.
            EndpointParametersError: If params are invalid.
            EndpointHeadersError: If headers are invalid.
            EndpointPayloadError: If payload is invalid.

        Examples:
            >>> # Internal use
            >>> from ._core import EndpointSpec
            >>> # Test validation
            >>> try:
            ...     invalid_spec = EndpointSpec(service="", url="invalid_url", params="not_a_dict", headers="not_a_dict", payload="not_a_dict")
            ... except Exception as exc:
            ...     print(type(exc).__name__, exc)
            EndpointServiceError EndpointSpec.service must be a non-empty string.
        """

        if not isinstance(self.service, str) or not self.service.strip():
            raise EndpointServiceError("EndpointSpec.service must be a non-empty string.")

        if not isinstance(self.url, str) or not self.url.strip():
            raise EndpointURLError("EndpointSpec.url must be a non-empty string.")

        if not self.url.startswith("https://"):
            raise EndpointURLError("EndpointSpec.url must start with 'https://'.")

        if not isinstance(self.params, dict) and self.params is not None:
            raise EndpointParametersError("EndpointSpec.params must be a dictionary or None.")

        if not isinstance(self.payload, dict) and self.payload is not None:
            raise EndpointPayloadError("EndpointSpec.payload must be a dictionary or None.")

        if self.headers is not None and not isinstance(self.headers, dict):
            raise EndpointHeadersError("EndpointSpec.headers must be a dictionary or None.")

def _resolve_endpoint(endpoint_name: str) -> EndpointSpec:
    """Resolve a fedfred endpoint name to its absolute URL and specifications.
    
    Args:
        endpoint_name (str): The name of the endpoint to resolve (e.g., "get_series_observations").

    Returns:
        EndpointSpec: A dataclass containing the resolved endpoint specifications, including the absolute URL, default parameters, and headers.

    Raises:
        EndpointServiceError: If the service name is invalid.
        EndpointURLError: If the URL is invalid.
        EndpointParametersError: If params are invalid.
        EndpointHeadersError: If headers are invalid.
        UnsupportedEndpointError: If the endpoint name is not recognized in any service registry.
    
    Examples:
        >>> # Internal use
        >>> from ._core import _resolve_endpoint
        >>> endpoint_spec = _resolve_endpoint("get_series_observations")
        >>> print(endpoint_spec.service)
        >>> print(endpoint_spec.url)
        >>> print(endpoint_spec.params)
        >>> print(endpoint_spec.headers)
        fred
        https://api.stlouisfed.org/fred/series/observations
        {'api_key': 'your_fred_api_key', 'file_type': 'json'}
        None
    """

    normalized_endpoint_name: str = endpoint_name.strip().lower()

    if normalized_endpoint_name in _FRED_ENDPOINT_MAP:
        path: str = _FRED_ENDPOINT_MAP[normalized_endpoint_name]

        if path.startswith("/v2/"):
            return EndpointSpec(
                service="fred",
                url=f"{_FRED_BASE_URL}{path}",
                headers=_FRED_VERSION_TWO_HEADERS,
                params=_FRED_VERSION_TWO_BASE_PARAMETERS,
            )

        return EndpointSpec(
            service="fred",
            url=f"{_FRED_BASE_URL}{path}",
            headers=None,
            params=_FRED_BASE_PARAMETERS,
        )

    if normalized_endpoint_name in _GEOFRED_ENDPOINT_MAP:
        return EndpointSpec(
            service="geofred",
            url=f"{_GEOFRED_BASE_URL}{_GEOFRED_ENDPOINT_MAP[normalized_endpoint_name]}",
            headers=None,
            params=_GEOFRED_BASE_PARAMETERS,
        )

    if normalized_endpoint_name in _FRASER_ENDPOINT_MAP:

        if normalized_endpoint_name.startswith("post_"):
            return EndpointSpec(
                service="fraser",
                url=f"{_FRASER_BASE_URL}{_FRASER_ENDPOINT_MAP[normalized_endpoint_name]}",
                headers=_FRASER_HEADERS,
                params=None,
                payload=_FRASER_BASE_PARAMETERS
            )

        return EndpointSpec(
            service="fraser",
            url=f"{_FRASER_BASE_URL}{_FRASER_ENDPOINT_MAP[normalized_endpoint_name]}",
            headers=_FRASER_HEADERS,
            params=_FRASER_BASE_PARAMETERS,
        )

    raise EndpointUnsupportedError(
        f"Unsupported endpoint name: {endpoint_name!r}."
    )

async def _resolve_endpoint_async(endpoint_name: str) -> EndpointSpec:
    """Asynchronously resolve a fedfred endpoint name to its absolute URL and specifications.

    Args:
        endpoint_name (str): The name of the endpoint to resolve (e.g., "get_series_observations").

    Returns:
        EndpointSpec: A dataclass containing the resolved endpoint specifications, including the absolute URL, default parameters, and headers.

    Raises:
        EndpointServiceError: If the service name is invalid.
        EndpointURLError: If the URL is invalid.
        EndpointParametersError: If params are invalid.
        EndpointHeadersError: If headers are invalid.
        UnsupportedEndpointError: If the endpoint name is not recognized in any service registry.

    Examples:
        >>> # Internal use
        >>> from ._core import _resolve_endpoint_async
        >>> import asyncio
        >>> async def main():
        ...     endpoint_spec = await _resolve_endpoint_async("get_series_observations")
        ...     print(endpoint_spec.service)
        ...     print(endpoint_spec.url)
        ...     print(endpoint_spec.params)
        ...     print(endpoint_spec.headers)
        >>> # Do not run this example in production code; it is for internal testing purposes only.
        >>> if __name__ == "__main__":
        ...     asyncio.run(main())
        fred
        https://api.stlouisfed.org/fred/series/observations
        {'api_key': 'your_fred_api_key', 'file_type': 'json'}
        None

    """

    return await asyncio.to_thread(_resolve_endpoint, endpoint_name)
