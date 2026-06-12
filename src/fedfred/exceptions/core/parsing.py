# filepath: /src/fedfred/exceptions/core/parsing.py
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
"""Parsing-layer exceptions for the fedfred core package.

The error hierarchy for :mod:`fedfred._core._parsers`. Every parse failure is one
of two kinds: a required key is absent (:class:`MissingFieldError`) or a value has
the wrong type/shape (:class:`ResponseShapeError`). Both subclass
:class:`ParsingError`, so a caller can ``except ParsingError`` for any malformed
response.

Classes:
    ParsingError: Base for any response-parsing failure.
    MissingFieldError: A required key/field is absent from the response.
    ResponseShapeError: A response value has the wrong type or shape.

See Also:
    - :mod:`fedfred._core._parsers`: Raises these.
    - :class:`fedfred.exceptions.core.base.CoreError`: The core-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import CoreError

__all__ = ["MissingFieldError", "ParsingError", "ResponseShapeError"]


@dataclass(frozen=True, slots=True)
class ParsingError(CoreError):
    """Base class for response-parsing failures in the core layer.

    The module catch-all for :mod:`fedfred._core._parsers`: catch this to handle any
    malformed-response failure regardless of whether a key was missing or a value
    had the wrong shape. Adds no fields; inherits the structured payload
    (:attr:`message`, :attr:`context`, :attr:`original_exception`) from
    :class:`CoreError`.
    """


@dataclass(frozen=True, slots=True)
class MissingFieldError(ParsingError):
    """Raised when a required key/field is absent from a response.

    Covers a missing container key, a missing nested section, and a missing
    per-row field. When several keys were acceptable (FRED's singular/plural
    container shapes), :attr:`candidates` records what was tried.

    Attributes:
        field (str): The single key/field that was expected and absent; empty
            string when a candidate set applies instead.
        candidates (tuple[str, ...]): The acceptable keys that were tried, when more
            than one would have satisfied the lookup.
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error, e.g. the
            ``KeyError`` from a row lookup (inherited).
    """

    field: str = ""
    """The single expected-but-absent key/field; empty when ``candidates`` applies."""

    candidates: tuple[str, ...] = ()
    """The acceptable keys that were tried, when more than one would satisfy the lookup."""

    def __str__(self) -> str:
        """Return the message, suffixed with the missing field or candidate set.

        Returns:
            str: :attr:`message` with ``(expected one of …)`` when
            :attr:`candidates` is set, or ``(field=…)`` when :attr:`field` is set;
            the bare :attr:`message` otherwise.
        """
        if self.candidates:
            return f"{self.message} (expected one of {list(self.candidates)!r})"
        if self.field:
            return f"{self.message} (field={self.field!r})"
        return self.message


@dataclass(frozen=True, slots=True)
class ResponseShapeError(ParsingError):
    """Raised when a response value has the wrong type or shape.

    The response was not a mapping, or a value under a key was not the expected
    container (a ``list``, or a ``dict``-or-``list``).

    Attributes:
        field (str): The key whose value had the wrong shape; empty string for the
            response root.
        expected (str): A description of the required shape, e.g. ``"list"`` or
            ``"dict or list"``.
        received (str): The type name actually received.
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error (inherited).
    """

    field: str = ""
    """The key whose value had the wrong shape; empty for the response root."""

    expected: str = ""
    """A description of the required shape, e.g. ``"list"`` or ``"dict or list"``."""

    received: str = ""
    """The type name actually received."""

    def __str__(self) -> str:
        """Return the message, suffixed with field/expected/received when known.

        Returns:
            str: :attr:`message` with ``(field=…, expected=…, received=…)`` appended
            when :attr:`expected` is set; the bare :attr:`message` otherwise.
        """
        if self.expected:
            return (
                f"{self.message} (field={self.field!r}, "
                f"expected={self.expected!r}, received={self.received!r})"
            )
        return self.message
