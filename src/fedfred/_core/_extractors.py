# filepath: /src/fedfred/_core/_extractors.py
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
"""fedfred._core._extractors

This module provides internal helper methods for the fedfred package, specifically for extracting data from certain FRED API responses.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
    - Federal Reserve Bank of St. Louis, FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
"""

import asyncio
from typing import Dict

from fedfred.exceptions.extraction import ExtractionError

def _region_type_extractor(response: Dict) -> str:
    """Helper method to extract the region type from a GeoFred response dict.

    Args:
        response (Dict): FRED GeoFred response dictionary.

    Returns:
        str: Extracted region type.

    Raises:
        ValueError: If no meta data or region type is found in the response.
    
    Examples:
        >>> import fedfred as fd
        >>> response = {
        >>>     "meta": {
        >>>         "region_type": "state"
        >>>     },
        >>>     "data": {
        >>>         "observations": []
        >>>     }
        >>> }
        >>> region_type = fd.Helpers.extract_region_type(response)
        >>> print(region_type)
        state

    Notes:
        This method looks for the 'region' key in the 'meta' section of the response dictionary.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.extract_region_type.html

    See Also:
        - :meth:`Helpers.to_gpd_gdf`: Convert a FRED observation dictionary to a GeoPandas GeoDataFrame.
        - :meth:`Helpers.to_dd_gpd_gdf`: Convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame.
        - :meth:`Helpers.to_pl_st_gdf`: Convert a FRED observation dictionary to a Polars GeoDataFrame.
    """

    meta_data = response.get('meta', {})
    if not meta_data:
        raise ExtractionError(
            message="No meta data found in the response"
            )

    region_type = meta_data.get('region')
    if not region_type:
        raise ExtractionError(
            message="No region type found in the response meta data"
            )

    return region_type

async def _region_type_extractor_async(response: Dict) -> str:
    """Helper method to extract the region type from a GeoFred response dictionary asynchronously.

    Args:
        response (Dict): FRED GeoFred response dictionary.

    Returns:
        str: Extracted region type.

    Raises:
        ValueError: If no meta data or region type is found in the response.

    Examples:
        >>> import asyncio
        >>> import fedfred as fd
        >>> response = {
        >>>     "meta": {
        >>>         "region_type": "state"
        >>>     },
        >>>     "data": {
        >>>         "observations": []
        >>>     }
        >>> }
        >>> async def main():
        >>>     region_type = await fd.AsyncHelpers.extract_region_type(response)
        >>>     print(region_type)
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        state

    Notes:
        This method looks for the 'region_type' key in the 'meta' section of the response.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.extract_region_type.html

    See Also:
        - :meth:`AsyncHelpers.to_gpd_gdf`: Asynchronously convert a FRED observation dictionary to a GeoPandas GeoDataFrame.
        - :meth:`AsyncHelpers.to_dd_gpd_gdf`: Asynchronously convert a FRED observation dictionary to a Dask GeoPandas GeoDataFrame.
        - :meth:`AsyncHelpers.to_pl_st_gdf`: Asynchronously convert a FRED observation dictionary to a Polars GeoDataFrame.
    """

    return await asyncio.to_thread(_region_type_extractor, response)
