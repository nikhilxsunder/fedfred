# filepath: /src/fedfred/exceptions/core/resolution.py
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
"""Resolution-layer exceptions for the fedfred core package.

The error hierarchy for :mod:`fedfred._core._resolvers`. Request-time resolution can
fail two ways: the service identity is not recognized (:class:`UnknownServiceError`,
raised by both endpoint resolution and preparation dispatch) or the endpoint name is
not in the resolved service's registry (:class:`UnsupportedEndpointError`). Both
subclass :class:`ResolutionError`.

Classes:
    ResolutionError: Base for any request-resolution failure.
    UnknownServiceError: The service identity is not recognized.
    UnsupportedEndpointError: The endpoint name is not in the service's registry.

See Also:
    - :mod:`fedfred._core._resolvers`: Raises these.
    - :class:`fedfred.exceptions.core.base.CoreError`: The core-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import CoreError

__all__ = ["ResolutionError", "UnknownServiceError", "UnsupportedEndpointError"]


@dataclass(frozen=True, slots=True)
class ResolutionError(CoreError):
    """Base class for request-time resolution failures in the core layer.

    The module catch-all for :mod:`fedfred._core._resolvers`. Carries the service
    identity being resolved, shared by every subclass.

    Attributes:
        service (str): The service identity that was being resolved.
        message (str): Human-readable message (inherited from :class:`CoreError`).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying ``KeyError`` from
            the failed lookup, if any (inherited).
    """

    service: str = ""
    """The service identity that was being resolved."""

    def __str__(self) -> str:
        """Return the message, suffixed with the service when known.

        Returns:
            str: :attr:`message` with ``(service=…)`` appended when :attr:`service`
            is set; the bare :attr:`message` otherwise.
        """
        if self.service:
            return f"{self.message} (service={self.service!r})"
        return self.message


@dataclass(frozen=True, slots=True)
class UnknownServiceError(ResolutionError):
    """Raised when a service identity is not recognized.

    Raised by both endpoint resolution and preparation dispatch. The valid set
    differs by call site (the endpoint registry includes ``"alfred"``; the
    preparation dispatch does not, since ALFRED reuses the FRED preparer), so
    :attr:`known_services` records what was actually acceptable.

    Attributes:
        known_services (tuple[str, ...]): The service identities that were accepted.
        service (str): The unrecognized service (inherited).
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error (inherited).
    """

    known_services: tuple[str, ...] = ()
    """The service identities that were accepted at the failing call site."""

    def __str__(self) -> str:
        """Return the message, suffixed with the service and the accepted set.

        Returns:
            str: :attr:`message` with ``(service=…, known=…)`` appended when
            :attr:`service` is set; the bare :attr:`message` otherwise.
        """
        if self.service:
            return f"{self.message} (service={self.service!r}, known={list(self.known_services)!r})"
        return self.message


@dataclass(frozen=True, slots=True)
class UnsupportedEndpointError(ResolutionError):
    """Raised when an endpoint name is not in the resolved service's registry.

    The service was recognized, but it has no spec for the requested endpoint.

    Attributes:
        endpoint_name (str): The unrecognized endpoint name.
        service (str): The service whose registry was searched (inherited).
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error (inherited).
    """

    endpoint_name: str = ""
    """The unrecognized endpoint name."""

    def __str__(self) -> str:
        """Return the message, suffixed with the endpoint and service.

        Returns:
            str: :attr:`message` with ``(endpoint=…, service=…)`` appended when
            :attr:`endpoint_name` is set; the bare :attr:`message` otherwise.
        """
        if self.endpoint_name:
            return f"{self.message} (endpoint={self.endpoint_name!r}, service={self.service!r})"
        return self.message
