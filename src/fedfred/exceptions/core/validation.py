# filepath: /src/fedfred/exceptions/core/validation.py
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
"""Validation-layer exceptions for the fedfred core package.

The error hierarchy for :mod:`fedfred._core._validators`. A validator either returns
``None`` or raises one of these. :class:`TypeValidationError` covers a wrong type;
:class:`ValueValidationError` covers a right-typed value that is otherwise invalid;
both subclass :class:`ParameterValidationError`, which carries the parameter and a
short reason.

Classes:
    ValidationError: Base for any validation failure.
    ParameterValidationError: A per-parameter validation failure (parameter + reason).
    TypeValidationError: A value has the wrong type.
    ValueValidationError: A right-typed value is otherwise invalid.

See Also:
    - :mod:`fedfred._core._validators`: Raises these.
    - :class:`fedfred.exceptions.core.base.CoreError`: The core-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import CoreError


@dataclass(frozen=True, slots=True)
class ValidationError(CoreError):
    """Base class for validation failures in the core layer.

    The module catch-all for :mod:`fedfred._core._validators`. Adds no fields;
    inherits the structured payload from :class:`CoreError`. Used directly (with a
    positional message) for non-parameter validation such as observation-column
    checks.
    """


@dataclass(frozen=True, slots=True)
class ParameterValidationError(ValidationError):
    """Base class for per-parameter validation failures.

    Carries the offending parameter name and a short, specific reason, shared by the
    type and value subclasses. Structured detail (the offending value, the allowed
    choices, etc.) goes in the inherited :attr:`context` mapping.

    Attributes:
        parameter (str): The parameter that failed validation.
        reason (str): A short, specific reason for the failure.
        message (str): Human-readable message (inherited from :class:`CoreError`).
        context (Mapping[str, Any]): Structured detail about the failure (inherited).
        original_exception (BaseException | None): The underlying error, if any
            (inherited).
    """

    parameter: str = ""
    """The parameter that failed validation."""

    reason: str = ""
    """A short, specific reason for the failure."""

    def __str__(self) -> str:
        """Return the message, suffixed with parameter and reason when known.

        Returns:
            str: :attr:`message` with ``(parameter=…, reason=…)`` appended when
            :attr:`parameter` is set; the bare :attr:`message` otherwise.
        """
        if not self.parameter:
            return self.message
        extra = f"parameter={self.parameter!r}"
        if self.reason:
            extra += f", reason={self.reason!r}"
        return f"{self.message} ({extra})"


@dataclass(frozen=True, slots=True)
class TypeValidationError(ParameterValidationError):
    """Raised when a parameter value is not of the expected type.

    Attributes:
        expected (str): A description of the expected type(s).
        received (str): The type name actually received.
        parameter (str): The parameter (inherited).
        reason (str): A short reason (inherited).
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Structured detail (inherited).
        original_exception (BaseException | None): The underlying error (inherited).
    """

    expected: str = ""
    """A description of the expected type(s)."""

    received: str = ""
    """The type name actually received."""

    def __str__(self) -> str:
        """Return the message, suffixed with parameter/expected/received when known.

        Returns:
            str: :attr:`message` with ``(parameter=…, expected=…, received=…)``
            appended when :attr:`parameter` is set; the bare :attr:`message`
            otherwise.
        """
        if not self.parameter:
            return self.message
        return (
            f"{self.message} (parameter={self.parameter!r}, "
            f"expected={self.expected!r}, received={self.received!r})"
        )


@dataclass(frozen=True, slots=True)
class ValueValidationError(ParameterValidationError):
    """Raised when a parameter value is the right type but otherwise invalid.

    Covers out-of-range numbers, empty strings, bad date/time formats, disallowed
    choices, and malformed delimited lists. The offending value and any supporting
    detail (allowed choices, invalid terms, expected format) go in the inherited
    :attr:`context` mapping; ``reason`` carries the one-line cause. Adds no fields of
    its own.
    """
