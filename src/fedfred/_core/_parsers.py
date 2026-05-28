# filepath: /src/fedfred/_core/_parsers.py
#
# Copyright (c) 2025–2026 Nikhil Sunder
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
"""fedfred._core._parsers

This module provides internal helper methods for the fedfred package, specifically for extracting data from certain FRED API responses.
"""

from __future__ import annotations
import asyncio
from typing import Dict, Any, Tuple, List
from ..exceptions.parsing import ParsingError

__all__ = [
    "_region_type_parser", "_region_type_parser_async", "_require_list", "_require_first_list"
]

def _region_type_parser(response: Dict) -> str:
    """Internal parser function to extract the region type from a GeoFred response dictionary.

    Args:
        response (Dict): FRED GeoFred response dictionary.

    Returns:
        str: Extracted region type.

    Raises:
        ParsingError: If no meta data or region type is found in the response.
    
    Examples:
        >>> # Internal use
        >>> from ._core import _region_type_parser
        >>> response = {
        >>>     "meta": {
        >>>         "region_type": "state"
        >>>     },
        >>>     "data": {
        >>>         "observations": []
        >>>     }
        >>> }
        >>> region_type = _region_type_parser(response)
        >>> print(region_type)
        state

    Notes:
        This method looks for the 'region' key in the 'meta' section of the response dictionary.
    """

    meta_data = response.get('meta', {})
    if not meta_data:
        raise ParsingError(
            message="No meta data found in the response"
            )

    region_type = meta_data.get('region')
    if not region_type:
        raise ParsingError(
            message="No region type found in the response meta data"
            )

    return region_type

async def _region_type_parser_async(response: Dict) -> str:
    """Internal asynchronous parser function to extract the region type from a GeoFred response dictionary.

    Args:
        response (Dict): FRED GeoFred response dictionary.

    Returns:
        str: Extracted region type.

    Raises:
        ParsingError: If no meta data or region type is found in the response.

    Examples:
        >>> # Internal use
        >>> from ._core import _region_type_parser_async
        >>> response = {
        >>>     "meta": {
        >>>         "region_type": "state"
        >>>     },
        >>>     "data": {
        >>>         "observations": []
        >>>     }
        >>> }
        >>> async def main():
        >>>     region_type = await _region_type_parser_async(response)
        >>>     print(region_type)
        >>> # Event loops should not be created in the library codebase, so this method should only be used within an existing async context. 
        >>> # For documentation purposes, the following pattern can be used to check the output data:
        >>> import asyncio
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        state

    Notes:
        This method looks for the 'region_type' key in the 'meta' section of the response.
    """

    return await asyncio.to_thread(_region_type_parser, response)

def _require_list(response: Dict[str, Any], key: str) -> List[Any]:
    """Validate a response has ``key`` pointing to a list. Raise otherwise.
    
    Args:
        response (Dict[str, Any]): The API response to validate.
        key (str): The key that should point to a list.

    Returns:
        List[Any]: The list found under ``key``.

    Raises:
        ParsingError: If the response is not a dict, if ``key`` is missing, or if the value under ``key`` is not a list.

    Examples:
        >>> # Internal use
        >>> from ._core import _require_list
        >>> response = {
        >>>     "data": {
        >>>         "observations": []
        >>>     }
        >>> }
        >>> data = _require_list(response["data"], "observations")
        >>> print(data)
        []
    """

    if not isinstance(response, dict) or key not in response:
        raise ParsingError(f"Invalid API response: missing {key!r} field")

    raw = response[key]

    if not isinstance(raw, list):
        raise ParsingError(f"Invalid API response: {key!r} must be a list")

    return raw

def _require_first_list(response: Dict[str, Any], keys: Tuple[str, ...]) -> List[Any]:
    """Return the list under the first matching key in ``keys``, or raise.

    Args:
        response (Dict[str, Any]): The API response to validate.
        keys (Tuple[str, ...]): The keys to check for a list value.

    Returns:
        List[Any]: The list found under the first matching key.

    Raises:
        ParsingError: If the response is not a dict, if none of the keys are present, or if the value under the first matching key is not a list.

    Note: 
        FRED's ``series`` and ``release`` endpoints sometimes return data under the plural key (``seriess``/``releases``) and sometimes 
        the singular (``series``/``release``); this lets a single parser handle both shapes.
    """

    if not isinstance(response, dict):
        raise ParsingError(
            f"Invalid API response: expected a mapping, got {type(response).__name__}"
        )

    for key in keys:
        if key in response:
            raw = response[key]
            if not isinstance(raw, list):
                raise ParsingError(f"Invalid API response: {key!r} must be a list")

            return raw

    pretty = " or ".join(repr(k) for k in keys)

    raise ParsingError(f"Invalid API response: missing {pretty} field")
