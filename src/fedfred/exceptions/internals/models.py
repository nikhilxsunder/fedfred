# filepath: /src/fedfred/exceptions/internals/models.py
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
"""Response-model exceptions for the fedfred internals package.

The error hierarchy for :mod:`fedfred._internals._models`. :class:`ModelError` covers the
two failure kinds the model layer originates itself: using a relation accessor without an
attached client (:class:`ClientNotAttachedError`), and string-key lookup failures on a
sequence (:class:`KeyLookupError` and its leaves). Response-*parsing* failures are not
here — they carry their true identity as core
:class:`~fedfred.exceptions.core.parsing.ParsingError` subclasses, raised by the core
parsers the models delegate to.

Classes:
    ModelError: Base for model-layer failures.
    ClientNotAttachedError: A relation accessor was used without a client.
    KeyLookupError: Base for ``sequence[str]`` lookup failures.
    StringLookupUnsupportedError: The sequence does not enable string indexing.
    KeyNotFoundError: No element matched the requested key.
    InvalidDateKeyError: A lookup key was not a valid ISO date.

See Also:
    - :mod:`fedfred._internals._models`: Raises these.
    - :class:`fedfred.exceptions.internals.base.InternalsError`: The internals-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import InternalsError

__all__ = [
    "ClientNotAttachedError",
    "InvalidDateKeyError",
    "KeyLookupError",
    "KeyNotFoundError",
    "ModelError",
    "StringLookupUnsupportedError",
]


@dataclass(frozen=True, slots=True)
class ModelError(InternalsError):
    """Base class for response-model failures originating in the model layer.

    The catch-all for :mod:`fedfred._internals._models`. Adds no fields; inherits the
    structured payload (:attr:`message`, :attr:`context`, :attr:`original_exception`)
    from :class:`InternalsError`.
    """


@dataclass(frozen=True, slots=True)
class ClientNotAttachedError(ModelError):
    """Raised when a relation accessor is used on an object with no client attached.

    Raised by :meth:`_ModelBase._require_client` when a property that must issue a
    follow-up API call is invoked on an instance constructed without a client.
    """


@dataclass(frozen=True, slots=True)
class KeyLookupError(ModelError):
    """Base for string-key lookup failures on a sequence (``sequence[str]``)."""


@dataclass(frozen=True, slots=True)
class StringLookupUnsupportedError(KeyLookupError):
    """Raised when string indexing is attempted on a sequence that does not enable it."""


@dataclass(frozen=True, slots=True)
class KeyNotFoundError(KeyLookupError):
    """Raised when no element matches the requested string key."""


@dataclass(frozen=True, slots=True)
class InvalidDateKeyError(KeyLookupError):
    """Raised when a sequence lookup key is not a valid ISO date string."""
