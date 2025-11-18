# filepath: /src/fedfred/config.py
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
This module defines configuration for the fedfred package
"""

from __future__ import annotations
from threading import RLock
from typing import Optional
import os
from .__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__

_API_KEY: Optional[str] = None
_LOCK = RLock()
_ENV_VAR_NAME = "FRED_API_KEY"


def set_api_key(api_key: str) -> None:
    """
    Set the global FRED API key for the fedfred package.

    Args:
        api_key (str): FRED API key string.

    Returns:
        None

    Raises:
        ValueError: If api_key is not a non-empty string.
    """
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("api_key must be a non-empty string.")
    with _LOCK:
        global _API_KEY
        _API_KEY = api_key.strip()

def get_api_key() -> Optional[str]:
    """
    Get the currently configured global FRED API key, if any.

    Args:
        None

    Returns:
        Optional[str]: The resolved API key, or None if not configured.

    Raises:
        None

    Note:
        Resolution order:
        1. Key set via set_api_key(...)
        2. Environment variable FRED_API_KEY
    """
    with _LOCK:
        if _API_KEY is not None:
            return _API_KEY

    env_key = os.getenv(_ENV_VAR_NAME)
    return env_key.strip() if env_key else None

def resolve_api_key(explicit: Optional[str] = None) -> str:
    """
    Resolve an API key from an explicit argument, the global setting, or the environment variable. Raises if nothing is available.

    Args:
        explicit (Optional[str]): API key explicitly passed by the user.

    Returns:
        str: The resolved API key.

    Raises:
        RuntimeError: If no API key can be resolved.
    """
    if explicit is not None:
        if not explicit.strip():
            raise ValueError("explicit API key must be a non-empty string.")
        return explicit.strip()

    key = get_api_key()
    if key is None:
        raise RuntimeError(
            "No FRED API key configured. "
            "Pass api_key=..., call fedfred.set_api_key(...), "
            "or set the FRED_API_KEY environment variable."
        )
    return key
