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
"""fedfred._core.__init__

This module initializes the _core subpackage of fedfred. It imports and exposes the core helper 
methods for data conversion, validation, and extraction used across the fedfred package.
"""

from ._converters import (
    _hashable_type_converter, _hashable_type_converter_async,
    DATAFRAME_CONVERTER_MAP, ASYNC_DATAFRAME_CONVERTER_MAP,
)

from ._transport import (
    _get_request, _get_request_async,
    _cached_get_request, _cached_get_request_async,
)

from._caching import (
    set_cache_maxsize, get_cache_maxsize, _CACHE,
)

from ._endpoints import (
    _ST_LOUIS_FED_BASE_URL, _FRED_PATH
)

from ._rate_limit import(
    _FRED_MAX_REQUESTS_PER_MINUTE,
)
