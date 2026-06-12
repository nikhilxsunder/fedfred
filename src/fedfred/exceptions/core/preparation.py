# filepath: /src/fedfred/exceptions/core/preparation.py
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
"""Preparation-layer exceptions for the fedfred core package.

The error hierarchy for :mod:`fedfred._core._preparers`. These cover the *set-level*
failures the preparer raises itself — an unrecognized parameter, or a missing
required one — as opposed to the per-value :class:`ConversionError` /
:class:`ValidationError` that the converters and validators it composes raise.

Classes:
    PreparationError: Base for any parameter-preparation failure.
    UnknownParameterError: A parameter has no spec and ``allow_unknown`` is False.
    MissingParameterError: A required parameter is absent after preparation.

See Also:
    - :mod:`fedfred._core._preparers`: Raises these.
    - :class:`fedfred.exceptions.core.base.CoreError`: The core-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import CoreError

__all__ = [
    "MissingParameterError",
    "PreparationError",
    "UnknownParameterError",
]


@dataclass(frozen=True, slots=True)
class PreparationError(CoreError):
    """Base class for parameter-preparation failures in the core layer.

    The module catch-all for :mod:`fedfred._core._preparers`. Carries the offending
    parameter and the service it was being prepared for, shared by every subclass.

    Attributes:
        parameter (str): The parameter that triggered the failure.
        service (str): The service the parameters were being prepared for.
        message (str): Human-readable message (inherited from :class:`CoreError`).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error, if any
            (inherited).
    """

    parameter: str = ""
    """The parameter that triggered the failure."""

    service: str = ""
    """The service the parameters were being prepared for."""

    def __str__(self) -> str:
        """Return the message, suffixed with parameter/service context when known.

        Returns:
            str: :attr:`message` with ``(parameter=…, service=…)`` appended when
            :attr:`parameter` is set; the bare :attr:`message` otherwise.
        """
        if self.parameter:
            return f"{self.message} (parameter={self.parameter!r}, service={self.service!r})"
        return self.message


@dataclass(frozen=True, slots=True)
class UnknownParameterError(PreparationError):
    """Raised when a parameter has no spec and ``allow_unknown`` is False.

    The strict-mode failure: the caller passed a parameter the service's spec map
    doesn't recognize. :attr:`known_parameters` lists the accepted names to make the
    likely typo obvious.

    Attributes:
        known_parameters (tuple[str, ...]): The parameter names the service accepts.
        parameter (str): The unrecognized parameter (inherited).
        service (str): The service (inherited).
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error (inherited).
    """

    known_parameters: tuple[str, ...] = ()
    """The parameter names the service accepts."""

    def __str__(self) -> str:
        """Return the message, suffixed with parameter, service, and known names.

        Returns:
            str: :attr:`message` with ``(parameter=…, service=…, known=…)`` appended
            when :attr:`parameter` is set; the bare :attr:`message` otherwise.
        """
        if self.parameter:
            return (
                f"{self.message} (parameter={self.parameter!r}, service={self.service!r}, "
                f"known={list(self.known_parameters)!r})"
            )
        return self.message


@dataclass(frozen=True, slots=True)
class MissingParameterError(PreparationError):
    """Raised when a required parameter is absent after preparation.

    A parameter whose spec is marked ``required=True`` was not present (or was
    ``None``) in the prepared set. Inherits :class:`PreparationError`'s
    ``parameter``/``service`` ``__str__``; adds no fields.
    """
