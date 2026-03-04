


from typing import  Optional, Dict, Union, Tuple, Any
import httpx
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type
from cachetools import FIFOCache, cached
from asyncache import cached as async_cached

from ._converters import _dict_type_converter, _dict_type_converter_async
from ._rate_limit import _rate_limiter, _rate_limiter_async
from ._endpoints import _resolve_endpoint, _resolve_endpoint_async

_CACHE: FIFOCache = FIFOCache(maxsize=256) # fix cache size resolution, refactor resolution logic to settings module.


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), retry=retry_if_exception_type(httpx.HTTPError),reraise=True,)
def _get_request(url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
    """Perform a GET request without caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        httpx.HTTPError: If the HTTP request fails.

    Notes:
        This method handles rate limiting and caching for synchronous GET requests to the FRED API.
    """

    _rate_limiter()

    spec = _resolve_endpoint(url_endpoint)

    params: Dict[str, Any] = {
        **spec.default_params,
        **(data or {}),
    }

    headers = dict(spec.default_headers or {})

    with httpx.Client() as client:
        try:
            response = client.get(spec.base_url + url_endpoint, params=params, headers=headers or None, timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise ValueError(f"HTTP Error occurred: {exc}") from exc

@cached(cache=_CACHE)
def _cached_get_request(url_endpoint: str, hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]=None) -> Dict[str, Any]:
    """Perform a GET request with caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]], optional): The hashable representation of the data. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        httpx.HTTPError: If the HTTP request fails.
    """

    return _get_request(url_endpoint, _dict_type_converter(hashable_data))

@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), retry=retry_if_exception_type(httpx.HTTPError), reraise=True)
async def _get_request_async(url_endpoint: str, data: Optional[Dict[str, Optional[Union[str, int]]]]=None) -> Dict[str, Any]:
    """Perform a GET request without caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        data (Dict[str, Optional[str | int]], optional): The query parameters for the request. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        httpx.HTTPError: If the HTTP request fails.

    Notes:
        This method handles rate limiting and caching for synchronous GET requests to the FRED API.
    """

    await _rate_limiter_async()
    
    spec = await _resolve_endpoint_async(url_endpoint)

    params: Dict[str, Any] = {
        **spec.default_params,
        **(data or {}),
    }

    headers = dict(spec.default_headers or {})

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(spec.base_url + url_endpoint, params=params, headers=headers or None, timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise ValueError(f"HTTP Error occurred: {exc}") from exc

@async_cached(cache=_CACHE)
async def _cached_get_request_async(url_endpoint: str, hashable_data: Optional[Tuple[Tuple[str, Optional[Union[str, int]]], ...]]=None) -> Dict[str, Any]:
    """Perform a GET request with caching.

    Args:
        url_endpoint (str): The FRED API endpoint to query.
        hashable_data (Optional[Tuple[Tuple[str, Optional[str | int]], ...]], optional): The hashable representation of the data. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the FRED API.

    Raises:
        httpx.HTTPError: If the HTTP request fails.
    """

    return await _get_request_async(url_endpoint, await _dict_type_converter_async(hashable_data))