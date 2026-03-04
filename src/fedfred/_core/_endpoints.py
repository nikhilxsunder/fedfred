



from dataclasses import dataclass
import asyncio
from typing import Mapping, Optional, Dict, Union, Any

from ..settings import _resolve_api_key

_BASE_URL: str = "https://api.stlouisfed.org/fred"

_CATEGORIES_ENDPOINT: str = "/category"
_CATEGORY_CHILDREN_ENDPOINT: str = "/category/children"
_CATEGORY_RELATED_ENDPOINT: str = "/category/related"
_CATEGORY_SERIES_ENDPOINT: str = "/category/series"
_CATEGORY_TAGS_ENDPOINT: str = "/category/tags"
_CATEGORY_RELATED_TAGS_ENDPOINT: str = "/category/related_tags"

_RELEASES_ENDPOINT: str = "/releases"
_RELEASES_DATES_ENDPOINT: str = "/releases/dates"


_BASE_PARAMETERS: Dict[str, str] = {
    'api_key': _resolve_api_key(service="fred"),
    'file_type': 'json'
}
_VERSION_TWO_HEADERS: Dict[str, str] = {
    'Authorization': f'Bearer {_resolve_api_key(service="fred")}',
    'format': 'json'
}
_VERSION_TWO_BASE_PARAMETERS: Dict[str, str] = {
    'format': 'json'
}

@dataclass(frozen=True, slots=True)
class _EndpointSpec:
    """Defines how to call an endpoint family."""
    base_url: str
    default_params: Mapping[str, str]
    default_headers: Mapping[str, str] | None = None

# Example specs (names illustrative)
_FRED_V1 = _EndpointSpec(
    base_url=_BASE_URL,
    default_params=_BASE_PARAMETERS,
    default_headers=None,
)

_FRED_V2 = _EndpointSpec(
    base_url=_BASE_URL,  # or a different base if it truly differs
    default_params=_VERSION_TWO_BASE_PARAMETERS,
    default_headers=_VERSION_TWO_HEADERS,
)

def _resolve_endpoint(url_endpoint: str) -> _EndpointSpec:
    # Centralize the “what counts as v2” rule here (not in transport).
    return _FRED_V2 if url_endpoint.startswith("/v2/") else _FRED_V1

async def _resolve_endpoint_async(url_endpoint: str) -> _EndpointSpec:

    return await asyncio.to_thread(_resolve_endpoint, url_endpoint)