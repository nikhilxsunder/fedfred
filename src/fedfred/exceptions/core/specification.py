# filepath: /src/fedfred/exceptions/core/specification.py
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
"""Specification-validation exceptions for the fedfred core package.

The error hierarchy raised by :meth:`EndpointSpec.__post_init__` in
:mod:`fedfred._core._specs` when a spec is constructed with invalid fields. These
fire at import time (specs are built into the registry on module load) and are
wrapped by :class:`~fedfred.exceptions.core.building.EndpointSpecBuildError` with the
offending endpoint name.

Classes:
    EndpointSpecError: Base for any EndpointSpec validation failure.
    EndpointServiceError: ``service`` is not a recognized service.
    EndpointURLError: ``url`` is empty, non-string, or not ``https://``.
    EndpointAuthError: ``auth`` is not a recognized auth style.
    EndpointFieldTypeError: ``params`` / ``payload`` / ``headers`` is set but not a dict.

See Also:
    - :mod:`fedfred._core._specs`: Raises these.
    - :class:`fedfred.exceptions.core.building.EndpointSpecBuildError`: Wraps these.
    - :class:`fedfred.exceptions.core.base.CoreError`: The core-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import CoreError


@dataclass(frozen=True, slots=True)
class EndpointSpecError(CoreError):
    """Base class for EndpointSpec construction-time validation failures.

    The module catch-all: catch this to handle any malformed-spec failure. The
    builder's ``except`` narrows to this when wrapping spec failures with endpoint
    context. Messages are self-contained; the structured fields are for
    programmatic inspection.

    Attributes:
        field (str): The spec field that failed validation (``"service"``,
            ``"url"``, ``"auth"``, ``"params"``, ``"payload"``, ``"headers"``).
        message (str): Human-readable message (inherited from :class:`CoreError`).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error, if any
            (inherited).
    """

    field: str = ""
    """The spec field that failed validation."""


@dataclass(frozen=True, slots=True)
class EndpointServiceError(EndpointSpecError):
    """Raised when ``EndpointSpec.service`` is not a recognized service.

    Attributes:
        received (str): The invalid service value supplied.
        valid (tuple[str, ...]): The accepted service identities.
        field (str): The failing field, ``"service"`` (inherited).
    """

    received: str = ""
    """The invalid service value supplied."""

    valid: tuple[str, ...] = ()
    """The accepted service identities."""


@dataclass(frozen=True, slots=True)
class EndpointURLError(EndpointSpecError):
    """Raised when ``EndpointSpec.url`` is empty, non-string, or not ``https://``."""


@dataclass(frozen=True, slots=True)
class EndpointAuthError(EndpointSpecError):
    """Raised when ``EndpointSpec.auth`` is not a recognized auth style.

    Attributes:
        received (str): The invalid auth value supplied.
        valid (tuple[str, ...]): The accepted auth styles.
        field (str): The failing field, ``"auth"`` (inherited).
    """

    received: str = ""
    """The invalid auth value supplied."""

    valid: tuple[str, ...] = ()
    """The accepted auth styles."""


@dataclass(frozen=True, slots=True)
class EndpointFieldTypeError(EndpointSpecError):
    """Raised when ``params`` / ``payload`` / ``headers`` is set but is not a dict.

    The same shape check across all three dict-or-None fields; :attr:`field`
    distinguishes which one failed.

    Attributes:
        received (str): The type name actually supplied.
        field (str): The failing field — ``"params"``, ``"payload"``, or
            ``"headers"`` (inherited).
    """

    received: str = ""
    """The type name actually supplied for the field."""
