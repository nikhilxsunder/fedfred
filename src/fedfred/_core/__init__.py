# filepath: /src/fedfred/_core/__init__.py
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
""""""

from ._accessors import _first_date_index
from ._comparators import _columns_equal, _row_match_mask
from ._converters import (
    _columns_to_arrow,
    _columns_to_cudf,
    _columns_to_dask,
    _columns_to_pandas,
    _columns_to_polars,
    _dict_type_converter,
    _hashable_type_converter,
)
from ._defaults import _CONCURRENCY_DIVISOR, _WINDOW_SECONDS
from ._mappings import RATE_LIMIT_BUCKET, RATE_LIMIT_RPM
from ._parsers import (
    _extract_objects,
    _observation_columns,
)
from ._resolvers import _resolve_endpoint, _resolve_preparation_function
from ._sentinels import MISSING, _Sentinel
from ._specs import EndpointSpec
from ._types import (
    JSON,
    CacheKey,
    CacheParameters,
    RateLimitBucket,
    T,
    _ResponseShape,
)
from ._validators import _validate_observation_columns

__all__ = [
    "JSON",
    "MISSING",
    "RATE_LIMIT_BUCKET",
    "RATE_LIMIT_RPM",
    "_CONCURRENCY_DIVISOR",
    "_WINDOW_SECONDS",
    "CacheKey",
    "CacheParameters",
    "EndpointSpec",
    "RateLimitBucket",
    "T",
    "_ResponseShape",
    "_Sentinel",
    "_columns_equal",
    "_columns_to_arrow",
    "_columns_to_cudf",
    "_columns_to_dask",
    "_columns_to_pandas",
    "_columns_to_polars",
    "_dict_type_converter",
    "_extract_objects",
    "_first_date_index",
    "_hashable_type_converter",
    "_observation_columns",
    "_resolve_endpoint",
    "_resolve_preparation_function",
    "_row_match_mask",
    "_validate_observation_columns",
]
