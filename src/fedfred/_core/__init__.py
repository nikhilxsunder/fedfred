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
"""fedfred._core.__init__

This module initializes the _core subpackage of fedfred. It imports and exposes the core helper 
methods for data conversion, validation, and extraction used across the fedfred package.
"""

from ._converters import (
    _dict_type_converter, _dict_type_converter_async,
    _hashable_type_converter, _hashable_type_converter_async,
    _datetime_converter, _datetime_converter_async,
    _liststring_converter, _liststring_converter_async,
    _vintage_dates_type_converter, _vintage_dates_type_converter_async,
    _pandas_dataframe_converter, _pandas_dataframe_converter_async,
    _polars_dataframe_converter, _polars_dataframe_converter_async,
    _dask_dataframe_converter, _dask_dataframe_converter_async,
    _datetime_hh_mm_converter, _datetime_hh_mm_converter_async,
    _geopandas_geodataframe_converter, _geopandas_geodataframe_converter_async,
    _dask_geopandas_geodataframe_converter, _dask_geopandas_geodataframe_converter_async,
    _polars_geodataframe_converter, _polars_geodataframe_converter_async
)

from ._validators import (
    _fred_parameter_validator, _fred_parameter_validator_async,
    _geofred_parameter_validator, _geofred_parameter_validator_async
)

from ._parsers import (
    _region_type_parser, _region_type_parser_async
)

from ._transport import (
    _get_request, _get_request_async,
    _cached_get_request, _cached_get_request_async
)

__all__ = [
    # Converters
    '_dict_type_converter', '_dict_type_converter_async',
    '_hashable_type_converter', '_hashable_type_converter_async',
    '_datetime_converter', '_datetime_converter_async',
    '_liststring_converter', '_liststring_converter_async',
    '_vintage_dates_type_converter', '_vintage_dates_type_converter_async',
    '_pandas_dataframe_converter', '_pandas_dataframe_converter_async',
    '_polars_dataframe_converter', '_polars_dataframe_converter_async',
    '_dask_dataframe_converter', '_dask_dataframe_converter_async',
    '_datetime_hh_mm_converter', '_datetime_hh_mm_converter_async',
    '_geopandas_geodataframe_converter', '_geopandas_geodataframe_converter_async',
    '_dask_geopandas_geodataframe_converter', '_dask_geopandas_geodataframe_converter_async',
    '_polars_geodataframe_converter', '_polars_geodataframe_converter_async',
    # Validators
    '_fred_parameter_validator', '_fred_parameter_validator_async',
    '_geofred_parameter_validator', '_geofred_parameter_validator_async',
    # Parsers
    '_region_type_parser', '_region_type_parser_async',
    # Transport
    '_get_request', '_get_request_async',
    '_cached_get_request', '_cached_get_request_async'
]
