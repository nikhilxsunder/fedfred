# filepath: /src/fedfred/fred/__init__.py
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
"""fedfred.fred.__init__

This module initializes the fred subpackage of fedfred.

Imports:
    FredAPI: A class that provides methods to interact with the Fred API.
    AsyncFredAPI: An asynchronous class for interacting with the Fred API.
    FredMapsAPI: A class that provides methods to interact with the Fred Maps API.
    AsyncFredMapsAPI: An asynchronous class for interacting with the Fred Maps API.
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

from .clients import Fred, AsyncFred, GeoFred, AsyncGeoFred
from .objects import (
    Category,
    Series,
    Tag,
    Release,
    ReleaseDate,
    Source,
    Element,
    VintageDate,
    SeriesGroup,
    BulkRelease
)

__all__ = [
    "Fred",
    "AsyncFred",
    "GeoFred",
    "AsyncGeoFred",
    "Category",
    "Series",
    "Tag",
    "Release",
    "ReleaseDate",
    "Source",
    "Element",
    "BulkRelease",
    "VintageDate",
    "SeriesGroup",
]