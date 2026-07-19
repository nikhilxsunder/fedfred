# filepath: /src/fedfred/exceptions/internals/clients.py
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
"""Client-layer exceptions for the fedfred internals package.

The error hierarchy for :mod:`fedfred._internals._clients`, the abstract client
bases. Two kinds of failure originate in the client layer itself, both under the
module base :class:`ClientError`: construction failures
(:class:`ClientConfigurationError` — an API key that could not be registered or an
invalid cache size) carrying the offending parameter and value, and cache-surface
failures (:class:`ClientCacheDisabledError` — the dict-like cache-inspection surface
was touched while caching is disabled) carrying the offending key.

The client also *resolves* API keys, but a missing/unresolvable key surfaces as
:class:`~fedfred.exceptions.settings.APIKeyResolutionError` from the settings layer
(the client only catches it); it is not defined here, because ``fedfred.settings``
sits below the internals layer and cannot depend on it.

Classes:
    ClientError: Base for any client-layer failure.
    ClientConfigurationError: A client was constructed with invalid configuration.
    ClientCacheDisabledError: The cache-inspection surface was used while caching is disabled.

See Also:
    - :mod:`fedfred._internals._clients`: Raises these.
    - :class:`fedfred.exceptions.internals.base.InternalsError`: The internals-layer base.
    - :class:`fedfred.exceptions.settings.APIKeyResolutionError`: The settings-layer
      key-resolution error the client catches.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import InternalsError

__all__ = [
    "ClientCacheDisabledError",
    "ClientConfigurationError",
    "ClientError",
]


@dataclass(frozen=True, slots=True)
class ClientError(InternalsError):
    """Base class for client-layer failures.

    The module catch-all for :mod:`fedfred._internals._clients`. Adds no fields;
    inherits the structured payload from :class:`InternalsError`.
    """


@dataclass(frozen=True, slots=True)
class ClientConfigurationError(ClientError):
    """Raised when a client is constructed with invalid configuration.

    Covers an API key that could not be registered and an invalid cache size;
    carries the offending parameter and value.

    Attributes:
        parameter (str): The configuration parameter that was invalid
            (``"api_key"`` or ``"cache_size"``).
        value (object): The invalid value supplied.
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error, e.g. the
            ``ValueError`` from :func:`fedfred.settings.set_api_key` (inherited).
    """

    parameter: str = ""
    """The configuration parameter that was invalid."""

    value: object = None
    """The invalid value supplied."""

    def __str__(self) -> str:
        """Return the message, suffixed with parameter/value when known.

        Returns:
            str: :attr:`message` with ``(parameter=…, value=…)`` appended when
            :attr:`parameter` is set; the bare :attr:`message` otherwise.
        """
        if self.parameter:
            return f"{self.message} (parameter={self.parameter!r}, value={self.value!r})"

        return self.message


@dataclass(frozen=True, slots=True)
class ClientCacheDisabledError(ClientError):
    """Raised when the cache-inspection surface is used while caching is disabled.

    The client exposes a dict-like read surface over the module-global cache
    (:meth:`~fedfred._internals._clients._ClientModel.__getitem__`); indexing it on
    a client constructed with ``caching_enabled=False`` raises this rather than a
    bare :class:`KeyError`, so a configuration mistake is distinguishable from a
    genuine cache miss. Deliberately does *not* subclass :class:`KeyError`, matching
    :class:`~fedfred.exceptions.internals.caching.CacheKeyError`.

    Attributes:
        key (object): The cache key whose lookup was attempted.
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error, if any (inherited).
    """

    key: object = None
    """The cache key whose lookup was attempted while caching was disabled."""

    def __str__(self) -> str:
        """Return the message, suffixed with the key when known.

        Returns:
            str: :attr:`message` with ``(key=…)`` appended when :attr:`key` is not
            ``None``; the bare :attr:`message` otherwise.
        """
        if self.key is not None:
            return f"{self.message} (key={self.key!r})"

        return self.message
