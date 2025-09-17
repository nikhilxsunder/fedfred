# filepath: /src/fedfred/__init__.py
#
# Copyright (c) 2025 Nikhil Sunder
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
"""
This module initializes the fedfred package.

Imports:
    FredAPI: A class that provides methods to interact with the Fred API.
    FredHelpers: A class that provides helper methods for the Fred API.
    Category: A class representing a category in the Fred database.
    Series: A class representing a series in the Fred database.
    Tag: A class representing a tag in the Fred database.
    Release: A class representing a release in the Fred database.
    ReleaseDate: A class representing a release date in the Fred database.
    Source: A class representing a source in the Fred database.
    Element: A class representing an element in the Fred database.
    VintageDate: A class representing a vintage date in the Fred database.
    SeriesGroup: A class representing a series group in the Fred database.
"""
from fedfred.__about__ import __title__, __version__, __author__, __license__, __copyright__, __description__, __url__

from . import clients
from . import helpers
from . import objects

from .clients import FredAPI
from .helpers import FredHelpers
from .objects import (
    Category,
    Series,
    Tag,
    Release,
    ReleaseDate,
    Source,
    Element,
    VintageDate,
    SeriesGroup
)

AsyncAPI = FredAPI.AsyncAPI
AsyncMapsAPI = FredAPI.AsyncAPI.AsyncMapsAPI
MapsAPI = FredAPI.MapsAPI

__all__ = [
    "__title__",
    "__description__",
    "__version__",
    "__copyright__",
    "__author__",
    "__license__",
    "__url__",
    "clients",
    "helpers",
    "objects",
    "FredAPI",
    "AsyncAPI",
    "AsyncMapsAPI",
    "MapsAPI",
    "FredHelpers",
    "Category",
    "Series",
    "Tag",
    "Release",
    "ReleaseDate",
    "Source",
    "Element",
    "VintageDate",
    "SeriesGroup"
]
