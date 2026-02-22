# filepath: /src/fedfred/_deprecated.py
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

import warnings
from typing import Dict, Optional, Union
from datetime import datetime
import pandas as pd
from sphinx import TYPE_CHECKING
from ..clients import Fred, GeoFred, AsyncFred, AsyncGeoFred

if TYPE_CHECKING:
    import geopandas as gpd
    import dask.dataframe as dd
    import dask_geopandas as dd_gpd
    import polars as pl
    import polars_st as st

# Deprecated
# OLD FREDHELPERS ARCHITECTURE COMPATIBILITY
class FredHelpers():
    """
    Deprecated alias for Helpers.

    This class exists for backward compatibility and will be removed
    in a future major release.
    """

    def __init__(self):
        warnings.warn(
            "FredHelpers is deprecated and will be removed in a future release. "
            "Use Helpers instead.",
            DeprecationWarning,
            stacklevel=2,
        )



# OLD FREDAPI ARCHITECTURE COMPATIBILITY
class FredAPI(Fred):
    """
    Deprecated alias for Fred.

    This class exists for backward compatibility and will be removed
    in a future major release.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "FredAPI is deprecated and will be removed in a future release. "
            "Use Fred instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    def get_release_observations(self, release_id: int, limit: Optional[int]=None):
        return NotImplementedError("get_release_observations is part of the the Version 2 Fred API and is not supported in the deprecated FredAPI class. For access to Version 2 functionality, please use the new Fred client classes.")

    class MapsAPI(GeoFred):
        """
        Deprecated alias for GeoFred.

        This class exists for backward compatibility and will be removed
        in a future major release.
        """

        def __init__(self, *args, **kwargs):
            warnings.warn(
                "FredAPI.MapsAPI is deprecated and will be removed in a future release. "
                "Use GeoFred instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            super().__init__(*args, **kwargs)

    class AsyncAPI(AsyncFred):
        """
        Deprecated alias for AsyncFred.

        This class exists for backward compatibility and will be removed
        in a future major release.
        """

        def __init__(self, *args, **kwargs):
            warnings.warn(
                "FredAPI.AsyncAPI is deprecated and will be removed in a future release. "
                "Use AsyncFred instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            super().__init__(*args, **kwargs)

        async def get_release_observations(self, release_id: int, limit: Optional[int]=None):
            return NotImplementedError("get_release_observations is part of the the Version 2 Fred API and is not supported in the deprecated AsyncFredAPI class. For access to Version 2 functionality, please use the new AsyncFred client classes.")

        class AsyncMapsAPI(AsyncGeoFred):
            """
            Deprecated alias for AsyncGeoFred.

            This class exists for backward compatibility and will be removed
            in a future major release.
            """

            def __init__(self, *args, **kwargs):
                warnings.warn(
                    "FredAPI.AsyncAPI.AsyncMapsAPI is deprecated and will be removed in a future release. "
                    "Use AsyncGeoFred instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                super().__init__(*args, **kwargs)

        #----------Deprecated Attributes (Properties)----------#
        @property
        def Maps(self):
            """AsyncGeoFred instance for FRED Maps endpoints."""

            warnings.warn(
                "The 'Maps' property is deprecated and will be removed in future versions. "
                "Please use the 'AsyncGeoFred' property instead.",
                DeprecationWarning,
                stacklevel=2
            )
            return self.AsyncMapsAPI(self)
        #------------------------------------------------------#

    #----------Deprecated Attributes (Properties)----------#
    @property
    def Maps(self) -> 'FredAPI.MapsAPI':
        """GeoFred instance for FRED Maps endpoints."""

        warnings.warn(
            "The 'Maps' property is deprecated and will be removed in future versions. "
            "Please use the 'GeoFred' property instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.MapsAPI(self)

    @property
    def Async(self) -> 'FredAPI.AsyncAPI':
        """AsyncFred instance for asynchronous FRED API endpoints."""

        warnings.warn(
            "The 'Async' property is deprecated and will be removed in future versions. "
            "Please use the 'AsyncFred' property instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.AsyncAPI(self)
    #------------------------------------------------------# 