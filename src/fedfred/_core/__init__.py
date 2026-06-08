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
"""Internal core subpackage of fedfred.

Aggregates the request- and response-processing helpers used across the package
and re-exports them under one namespace for internal use: cache-key conversion
from :mod:`._converters`, endpoint resolution from :mod:`._endpoints`,
per-service parameter preparation from :mod:`._parameters`, and response-shape
parsing from :mod:`._parsers`.

These names are private implementation details, exported only so that sibling
internal modules can import them from a single place; downstream users should
depend on the public ``fedfred`` surface rather than on anything here.

See Also:
    - :mod:`fedfred._core._converters`: Value, DataFrame, and cache-key converters.
    - :mod:`fedfred._core._endpoints`: Endpoint specification resolution.
    - :mod:`fedfred._core._parameters`: Per-service parameter preparation.
    - :mod:`fedfred._core._parsers`: Response-shape parsers.
    - :mod:`fedfred._core._validators`: Parameter validators (used internally; not re-exported here).
"""

from ._converters import (
    _dict_type_converter,
    _hashable_type_converter,
    _coerce_lower,
)
from ._endpoints import _resolve_endpoint
from ._parameters import _resolve_preparation_function
from ._parsers import (
    _ResponseShape,
    _extract_objects,
    _region_type_parser,
)


__all__ = [
    "_ResponseShape",
    "_dict_type_converter",
    "_extract_objects",
    "_coerce_lower",
    "_hashable_type_converter",
    "_region_type_parser",
    "_resolve_endpoint",
    "_resolve_preparation_function",
]
