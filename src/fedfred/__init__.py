"""
This module initializes the fedfred package.

Imports:
    FredAPI: A class that provides methods to interact with the Fred API.
    FredMapsAPI: A class that provides methods to interact with the Fred Maps API.
"""
from .fedfred import FredAPI
# Import data classes
from .fred_data import (
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

__all__ = [
    "FredAPI",
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
