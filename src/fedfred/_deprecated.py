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
import inspect
from functools import wraps
from .utils.helpers import Helpers, AsyncHelpers
from .fred.clients import Fred, GeoFred, AsyncFred, AsyncGeoFred

__all__ = ["FredHelpers", "FredAPI"]

# Deprecated
def _deprecated_wrapper(func, deprecated_qualname: str, *, is_async: bool):
    msg = (
        f"{deprecated_qualname} is deprecated and will be removed in a future release. "
        "Use Helpers / AsyncHelpers instead."
    )

    if is_async:
        @wraps(func)
        async def _wrapped_async(*args, **kwargs):
            warnings.warn(msg, DeprecationWarning, stacklevel=3)
            return await func(*args, **kwargs)
        return staticmethod(_wrapped_async)

    @wraps(func)
    def _wrapped_sync(*args, **kwargs):
        warnings.warn(msg, DeprecationWarning, stacklevel=3)
        return func(*args, **kwargs)
    return staticmethod(_wrapped_sync)

class FredHelpers(Helpers):
    """
    Deprecated compatibility façade.

    Back-compat behavior:
      - FredHelpers.foo(...) delegates to Helpers.foo(...)
      - FredHelpers.foo_async(...) delegates to AsyncHelpers.foo(...)
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "FredHelpers is deprecated and will be removed in a future release. "
            "Use Helpers / AsyncHelpers instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

# FOR IMPORT COMPATIBILITY ONLY
class AsyncFredHelpers(AsyncHelpers):
    """
    Deprecated alias for AsyncHelpers (kept for callers importing AsyncFredHelpers).
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "AsyncFredHelpers is deprecated and will be removed in a future release. "
            "Use AsyncHelpers instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


def _install_fredhelpers_compat_methods() -> None:
    for name in dir(Helpers):
        if name.startswith("_"):
            continue
        attr = getattr(Helpers, name, None)
        if callable(attr):
            setattr(FredHelpers, name, _deprecated_wrapper(attr, f"FredHelpers.{name}", is_async=False))

    for name in dir(AsyncHelpers):
        if name.startswith("_"):
            continue
        attr = getattr(AsyncHelpers, name, None)
        if callable(attr):
            setattr(
                FredHelpers,
                f"{name}_async",
                _deprecated_wrapper(attr, f"FredHelpers.{name}_async", is_async=True),
            )

    for name in dir(AsyncHelpers):
        if name.startswith("_"):
            continue
        attr = getattr(AsyncHelpers, name, None)
        if callable(attr):
            setattr(AsyncFredHelpers, name, _deprecated_wrapper(attr, f"AsyncFredHelpers.{name}", is_async=inspect.iscoroutinefunction(attr)))

_install_fredhelpers_compat_methods()

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

    def get_release_observations(self, release_id, limit):
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

        async def get_release_observations(self, release_id, limit):
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

