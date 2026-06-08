# filepath: /src/fedfred/exceptions/__init__.py
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
"""fedfred.exceptions.__init__"""

from .base import FedFredError
from .caching import (
    CacheAccessError,
    CacheBackendError,
    CacheClearError,
    CacheConfigurationError,
    CacheDeleteError,
    CacheInitializationError,
    CacheKeyError,
    CacheOperationError,
    CachePopError,
    CacheResizeError,
    CacheSetError,
    CachingError,
)
from .conversion import ConversionError, DataFrameConversionError, DateConversionError, GeoDataFrameConversionError, ParameterConversionError, TypeConversionError
from .dependencies import OptionalDependencyError
from .endpoints import (
    EndpointBaseURLError,
    EndpointConfigurationError,
    EndpointContextError,
    EndpointError,
    EndpointHeadersError,
    EndpointMapError,
    EndpointNameTypeError,
    EndpointNameValueError,
    EndpointParametersError,
    EndpointPayloadError,
    EndpointResolutionError,
    EndpointServiceError,
    EndpointSpecError,
    EndpointUnsupportedError,
    EndpointURLError,
)
from .parameters import (
    ParameterServiceError,
)
from .parsing import ParsingError
from .rate_limit import (
    LimiterLimitError,
    LimiterLoopError,
    LimiterReleaseError,
    LimiterServiceError,
    LimiterWakeError,
    RateLimiterConfigurationError,
    RateLimiterStateError,
)
from .transport import (
    AuthenticationError,
    AuthorizationError,
    BadGatewayError,
    BadRequestError,
    ConflictError,
    ConnectTimeoutError,
    GatewayTimeoutError,
    GoneError,
    HTTPClientError,
    HTTPResponseError,
    HTTPServerError,
    InternalServerError,
    MethodNotAllowedError,
    NotFoundError,
    PoolTimeoutError,
    ProxyTransportError,
    RateLimitError,
    ReadTimeoutError,
    RequestPreparationError,
    ResponseDecodingError,
    ServiceUnavailableError,
    TooManyRedirectsError,
    TransportConnectionError,
    TransportError,
    TransportProtocolError,
    TransportReadError,
    TransportRequestError,
    TransportRetryError,
    TransportTimeoutError,
    TransportWriteError,
    UnexpectedHTTPStatusError,
    UnprocessableEntityError,
    UnsupportedProtocolError,
    WriteTimeoutError,
)
from .validation import ParameterValidationError, TypeValidationError, ValidationError, ValueValidationError
