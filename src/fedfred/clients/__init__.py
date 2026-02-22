# filepath: /src/fedfred/clients/__init__.py
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
"""fedfred.clients.__init__

This module initializes the clients subpackage of fedfred.

Imports:
    Fred: A class that provides methods to interact with the FRED API.
    AsyncFred: An asynchronous class that provides methods to interact with the FRED API.
    GeoFred: A class that provides methods to interact with the GeoFRED API.
    AsyncGeoFred: An asynchronous class that provides methods to interact with the GeoFRED API.
    Alfred: A class that provides methods to interact with the ALFRED API.
    Fraser: A class that provides methods to interact with the Fraser API.
"""

from .fred import Fred, AsyncFred
from .geofred import GeoFred, AsyncGeoFred
from.alfred import Alfred
from .fraser import Fraser

__all__ = [
    "Fred",
    "AsyncFred",
    "GeoFred",
    "AsyncGeoFred",
    "Alfred",
    "Fraser",
]
