# filepath: /src/fedfred/settings.py
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
"""fedfred.settings

This module defines configuration management for the fedfred package, including setting, getting, and resolving the FRED API key.

The configuration system supports:
    - Setting a global API key via `set_api_key(...)`.
    - Retrieving the current API key via `get_api_key()`.
    - Resolving an API key from an explicit argument, the global setting, or the environment variable via `resolve_api_key(...)`.

Examples:
    >>> import fedfred as fd
    >>> fd.set_api_key("your_api_key_here")
    >>> api_key = fd.get_api_key()

Notes:
    API keys can be set globally using `fedfred.set_api_key`, or can be provided explicitly
    when instantiating the `FredAPI` class. If neither is provided, the class will attempt to
    resolve the API key from the environment variable `FRED_API_KEY`.

Warnings:
    Make sure to handle your API key securely and avoid hardcoding it in your source code.

See Also:
    - :class:`fedfred.FredAPI`: The main class for interacting with the FRED API, which utilizes the API key resolved by this configuration module.

References:
    fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations
from typing import Optional, Literal, Dict
import os
from .__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__

Service = Literal["fred", "fraser"]
"""Type alias for supported services in fedfred package."""

ENV_VARS: Dict[Service, str] = {
    "fred": "FRED_API_KEY",
    "fraser": "FRASER_API_KEY",
}
"""Mapping of services to their respective environment variable names for API keys."""

_GLOBAL_KEYS: Dict[Service, Optional[str]] = {
    "fred": None,
    "fraser": None,
}
"""Global storage for API keys for each service."""

def set_api_key(api_key: str, service: Service = "fred") -> None:
    """Set the global API key for the fedfred package.

    Args:
        api_key (str): API key string.
        service (Service): The service for which to set the API key. Defaults to "fred".

    Raises:
        ValueError: If api_key is not a non-empty string or if an unknown service is specified.
    """

    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("api_key must be a non-empty string.")
    if service not in _GLOBAL_KEYS:
        raise ValueError(f"Unknown service: {service!r}. Expected 'fred' or 'fraser'.")
    _GLOBAL_KEYS[service] = api_key.strip()

def get_api_key(service: Service = "fred") -> Optional[str]:
    """Get the currently configured global API key for a given service, if any.

    Args:
        service (Service): The service for which to get the API key. Defaults to "fred".

    Returns:
        Optional[str]: The resolved API key, or None if not configured.

    Raises:
        ValueError: If an unknown service is specified.
    """

    if service not in _GLOBAL_KEYS:
        raise ValueError(f"Unknown service: {service!r}. Expected 'fred' or 'fraser'.")
    return _GLOBAL_KEYS[service]

def clear_api_key(service: Service = "fred") -> None:
    """Clear the global API key for a service.
    
    Args:
        service (Service): The service for which to clear the API key. Defaults to "fred".

    Raises:
        ValueError: If an unknown service is specified.
    """
    if service not in _GLOBAL_KEYS:
        raise ValueError(f"Unknown service: {service!r}. Expected 'fred' or 'fraser'.")
    _GLOBAL_KEYS[service] = None

def _resolve_api_key(*, service: Service = "fred", env_var: Optional[str] = None,) -> str:
    """Resolve an API key from an explicit argument, the global setting, or the environment variable. Raises if nothing is available.

    Args:
        api_key (Optional[str]): API key explicitly passed by the user.
        service (Service): The service for which to resolve the API key. Defaults to "fred".
        env_var (Optional[str]): Optional environment variable name to override the default for the service.

    Returns:
        str: The resolved API key.

    Raises:
        RuntimeError: If no API key can be resolved.
        ValueError: If an unknown service is specified.
    """

    if service not in _GLOBAL_KEYS:
        raise ValueError(f"Unknown service: {service!r}. Expected 'fred' or 'fraser'.")

    # 2) global
    global_key = _GLOBAL_KEYS.get(service)
    if isinstance(global_key, str) and global_key.strip():
        return global_key.strip()

    # 3) environment
    env_name = env_var or ENV_VARS[service]
    env_value = os.getenv(env_name)
    if isinstance(env_value, str) and env_value.strip():
        return env_value.strip()

    raise RuntimeError(
        f"No API key could be resolved for service={service!r}. "
        f"Provide api_key=..., call set_api_key(..., service={service!r}), "
        f"or set the environment variable {env_name}."
    )
