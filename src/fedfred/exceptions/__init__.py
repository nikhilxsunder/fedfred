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

from .validation import (
    ValueValidationError,
    TypeValidationError,
    ParameterValidationError,
    ValidationError
)

from .conversion import (
    ConversionError,
    ParameterConversionError,
    TypeConversionError,
    DateConversionError,
    DataFrameConversionError,
    GeoDataFrameConversionError
)

from .dependencies import OptionalDependencyError

from .parsing import ParsingError

from .base import FedFredError

from .transport import (
    TransportError,
    RequestPreparationError,
    TransportRequestError,
    TransportConnectionError,
    TransportTimeoutError,
    ConnectTimeoutError,
    ReadTimeoutError,
    WriteTimeoutError,
    PoolTimeoutError,
    TransportReadError,
    TransportWriteError,
    TransportProtocolError,
    ProxyTransportError,
    UnsupportedProtocolError,
    TooManyRedirectsError,
    ResponseDecodingError,
    TransportRetryError,
    HTTPResponseError,
    HTTPClientError,
    BadRequestError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    MethodNotAllowedError,
    ConflictError,
    GoneError,
    UnprocessableEntityError,
    RateLimitError,
    HTTPServerError,
    InternalServerError,
    BadGatewayError,
    ServiceUnavailableError,
    GatewayTimeoutError,
    UnexpectedHTTPStatusError
)

from .endpoints import (
    EndpointError,
    EndpointConfigurationError,
    EndpointResolutionError,
    EndpointSpecError,
    EndpointContextError,
    EndpointNameTypeError,
    EndpointNameValueError,
    EndpointUnsupportedError,
    EndpointMapError,
    EndpointBaseURLError,
    EndpointPayloadError,
    EndpointParametersError,
    EndpointHeadersError,
    EndpointServiceError,
    EndpointURLError
)

from .rate_limit import(
    LimiterLimitError,
    LimiterWakeError,
    LimiterLoopError,
    LimiterReleaseError,
    LimiterServiceError,
    RateLimiterConfigurationError,
    RateLimiterStateError,
)

from .caching import (
    CachingError,
    CacheConfigurationError,
    CacheInitializationError,
    CacheResizeError,
    CacheOperationError,
    CacheSetError,
    CacheDeleteError,
    CacheClearError,
    CachePopError,
    CacheAccessError,
    CacheKeyError,
    CacheBackendError,
)
