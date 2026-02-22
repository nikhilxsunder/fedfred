# filepath: /src/fedfred/__init__.py
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
"""fedfred.__init__

This module initializes the fedfred package.

Imports:
    Fred: A class that provides methods to interact with the Fred API.
    AsyncFred: An asynchronous class for interacting with the Fred API.
    GeoFred: A class that provides methods to interact with the Fred Maps API.
    AsyncGeoFred: An asynchronous class for interacting with the Fred Maps API.
    Fraser: A class that provides methods to interact with the Fraser API.
    Helpers: A class that provides helper methods for the Fred API.
    AsyncHelpers: An asynchronous class that provides helper methods for the Fred API.
    set_api_key: Function to set the global FRED API key.
    get_api_key: Function to get the current global FRED API key.
    Category: A class representing a category in the Fred database.
    Series: A class representing a series in the Fred database.
    Tag: A class representing a tag in the Fred database.
    Release: A class representing a release in the Fred database.
    ReleaseDate: A class representing a release date in the Fred database.
    Source: A class representing a source in the Fred database.
    Element: A class representing an element in the Fred database.
    VintageDate: A class representing a vintage date in the Fred database.
    SeriesGroup: A class representing a series group in the Fred database.
    BulkRelease: A class representing a bulk release in the Fred database.
"""

# About
from .__about__ import (
    __title__,
    __version__,
    __author__,
    __email__,
    __license__,
    __copyright__,
    __description__,
    __docs__,
    __repository__,
)

# Settings
from .settings import set_api_key, get_api_key, clear_api_key

# Models
from .models import (
    Category,
    Series,
    Tag,
    Release,
    ReleaseDate,
    Source,
    Element,
    VintageDate,
    SeriesGroup,
    BulkRelease,
)

# Clients
from .clients import (
    Fred,
    AsyncFred,
    GeoFred,
    AsyncGeoFred,
    Fraser,
    Alfred
)

# Exceptions
from .exceptions import (
    FedFredError,
    RequestContext,
    FedFredTransportError,
    FedFredParsingError,
    FedFredAPIError,
    FedFredRateLimitError,
    FedFredValidationError,
    FedFredHTTPError,
    FedFredAuthError,
    FedFredNotFoundError,
    FedFredServerError
)

# Deprecated
from ._core import (
    FredHelpers,
    FredAPI
)
AsyncAPI = FredAPI.AsyncAPI
AsyncMapsAPI = FredAPI.AsyncAPI.AsyncMapsAPI
MapsAPI = FredAPI.MapsAPI

# All
__all__ = [
    # About
    "__title__",
    "__description__",
    "__version__",
    "__copyright__",
    "__author__",
    "__email__",
    "__license__",
    "__repository__",
    "__docs__",
    # Settings
    "set_api_key",
    "get_api_key",
    "clear_api_key",
    # Clients
    "Fred",
    "AsyncFred",
    "AsyncGeoFred",
    "GeoFred",
    "AsyncGeoFred",
    "Fraser",
    "Alfred",
    # Models
    "Category",
    "Series",
    "Tag",
    "Release",
    "ReleaseDate",
    "Source",
    "Element",
    "VintageDate",
    "SeriesGroup",
    "BulkRelease",
    # Exceptions
    "FedFredError",
    "RequestContext",
    "FedFredTransportError",
    "FedFredParsingError",
    "FedFredAPIError",
    "FedFredRateLimitError",
    "FedFredValidationError",
    "FedFredHTTPError",
    "FedFredAuthError",
    "FedFredNotFoundError",
    "FedFredServerError",
    # Deprecated
    "FredHelpers",
    "FredAPI",
    "AsyncAPI",
    "AsyncMapsAPI",
    "MapsAPI",
]
