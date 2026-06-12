# filepath: /src/fedfred/exceptions/core/__init__.py
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
"""Public exception surface for the fedfred core layer.

Re-exports every exception raised by the ``fedfred._core`` modules, all rooted at
:class:`CoreError` (which is independent of, not a subclass of,
:class:`~fedfred.exceptions.base.FedFredError`). Import error types from here rather
than the individual ``fedfred.exceptions.core.*`` modules.

Three catch breadths:

- ``except CoreError`` — any core-layer failure.
- ``except <ModuleError>`` (:class:`ConversionError`, :class:`ParsingError`,
  :class:`ValidationError`, …) — any failure from one module's hierarchy.
- ``except <SpecificError>`` — one precise failure.

Hierarchy::

    CoreError
    ├── BuildError                     # building
    │   └── EndpointSpecBuildError
    ├── ConversionError                # conversion
    │   ├── ParameterConversionError
    │   │   ├── TypeConversionError
    │   │   └── DateConversionError
    │   └── DataFrameConversionError
    │       └── GeoDataFrameConversionError
    ├── DependencyLoadingError         # loading
    ├── ParsingError                   # parsing
    │   ├── MissingFieldError
    │   └── ResponseShapeError
    ├── PreparationError               # preparation
    │   ├── UnknownParameterError
    │   └── MissingParameterError
    ├── ResolutionError                # resolution
    │   ├── UnknownServiceError
    │   └── UnsupportedEndpointError
    ├── EndpointSpecError              # specification
    │   ├── EndpointServiceError
    │   ├── EndpointURLError
    │   ├── EndpointAuthError
    │   └── EndpointFieldTypeError
    └── ValidationError                # validation
        └── ParameterValidationError
            ├── TypeValidationError
            └── ValueValidationError

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from .base import CoreError
from .building import BuildError, EndpointSpecBuildError
from .conversion import (
    ConversionError,
    DataFrameConversionError,
    DateConversionError,
    GeoDataFrameConversionError,
    ParameterConversionError,
    TypeConversionError,
)
from .loading import DependencyLoadingError
from .parsing import MissingFieldError, ParsingError, ResponseShapeError
from .preparation import MissingParameterError, PreparationError, UnknownParameterError
from .resolution import ResolutionError, UnknownServiceError, UnsupportedEndpointError
from .specification import (
    EndpointAuthError,
    EndpointFieldTypeError,
    EndpointServiceError,
    EndpointSpecError,
    EndpointURLError,
)
from .validation import (
    ParameterValidationError,
    TypeValidationError,
    ValidationError,
    ValueValidationError,
)

__all__ = [
    "BuildError",
    "ConversionError",
    "CoreError",
    "DataFrameConversionError",
    "DateConversionError",
    "DependencyLoadingError",
    "EndpointAuthError",
    "EndpointFieldTypeError",
    "EndpointServiceError",
    "EndpointSpecBuildError",
    "EndpointSpecError",
    "EndpointURLError",
    "GeoDataFrameConversionError",
    "MissingFieldError",
    "MissingParameterError",
    "ParameterConversionError",
    "ParameterValidationError",
    "ParsingError",
    "PreparationError",
    "ResolutionError",
    "ResponseShapeError",
    "TypeConversionError",
    "TypeValidationError",
    "UnknownParameterError",
    "UnknownServiceError",
    "UnknownServiceError",
    "UnsupportedEndpointError",
    "ValidationError",
    "ValueValidationError",
]
