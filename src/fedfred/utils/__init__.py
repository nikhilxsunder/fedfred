# filepath: /src/fedfred/utils/__init__.py
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
"""fedfred.utils.__init__

This module initializes the utils subpackage of fedfred.

Imports:
    set_api_key: Function to set the global FRED API key.
    get_api_key: Function to get the current global FRED API key.
    Helpers: A class that provides helper methods for the Fred API.
    AsyncHelpers: An asynchronous class that provides helper methods for the Fred API.
"""

from .config import set_api_key, get_api_key, clear_api_key
from .helpers import AsyncHelpers, Helpers

__all__ = [
    "set_api_key",
    "get_api_key",
    "Helpers",
    "AsyncHelpers",
]
