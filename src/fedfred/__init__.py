# filepath: /src/fedfred/__init__.py
#
# Copyright (c) 2025 Nikhil Sunder
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
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
