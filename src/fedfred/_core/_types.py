# filepath: /src/fedfred/_core/_types.py
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
"""Shared type vocabulary for the fedfred core package.

The package's type aliases and the runtime sets mechanically derived from them. Two
flavours live here: ``Literal`` aliases naming a closed set of string values
(:data:`AuthStyle`, :data:`_ResponseShape`), and ``Callable`` aliases naming a
function signature (:data:`ParameterConverter`, :data:`ParameterValidator`). The
``frozenset`` validation sets (:data:`_VALID_AUTH_STYLES`, :data:`_VALID_SERVICES`)
are obtained via :func:`typing.get_args` from their Literal and kept here beside
those types, so the static type and its runtime form cannot drift.

The lowest layer of the core — pure vocabulary, no logic — imported upward by
:mod:`._specs` (field types), :mod:`._validators` / :mod:`._builders` (the
``_VALID_*`` checks), and :mod:`._parsers` (``_ResponseShape``).

Aliases:
    AuthStyle: How the API key is injected for an endpoint.
    ParameterConverter: ``(name, value) -> value`` scalar parameter converter.
    ParameterValidator: ``(name, value) -> None`` parameter validator (raises on invalid).
    _ResponseShape: Container shape of a FRED response payload.
    CacheValue: A single cache-keyable prepared parameter value (str, int, or None).
    CacheParameters: A prepared request-parameter mapping (name -> value) to be cache-keyed.
    CacheKey: The hashable, key-sorted form of CacheParameters, used as a cache key.
    T: Generic type variable for caller-supplied default values.

Constants:
    _VALID_AUTH_STYLES: Runtime form of :data:`AuthStyle`.
    _VALID_SERVICES: Runtime form of :data:`fedfred.settings.Service`.

See Also:
    - :mod:`fedfred._core._specs`: Uses these aliases as field types.
    - :mod:`fedfred.settings`: Defines :data:`Service`, mirrored by :data:`_VALID_SERVICES`.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Literal, TypeAlias, TypeVar, get_args

from ..settings import Service

AuthStyle = Literal["api_key_param", "bearer_header", "api_key_header", "none"]
"""How the transport layer injects the API key for an endpoint.

One of:

- ``"api_key_param"``: append ``api_key=<key>`` as a query parameter
  (FRED, ALFRED, GeoFRED v1 endpoints).
- ``"bearer_header"``: send ``Authorization: Bearer <key>`` (FRED v2
  endpoints under ``/v2/``).
- ``"api_key_header"``: send the key in a service-specific header (FRASER).
- ``"none"``: no auth (public endpoints).

The literal values double as the :class:`EndpointSpec.auth` field type.
"""

_VALID_AUTH_STYLES: frozenset[str] = frozenset(get_args(AuthStyle))
"""Runtime validation set for :attr:`EndpointSpec.auth`, derived from :data:`AuthStyle` so the two
cannot drift."""

_VALID_SERVICES: frozenset[str] = frozenset(get_args(Service))
"""Runtime validation set for :attr:`EndpointSpec.service`, derived from
:data:`fedfred.settings.Service` so the two cannot drift."""

ParameterConverter = Callable[[str, object], object]
"""Type alias for a scalar parameter converter: takes a parameter name and a raw value, returns the
API-ready value."""

_ResponseShape = Literal[
    "list",
    "dict_or_list",
]
"""Shape of the object container in a FRED-family response payload.

One of:

- ``"list"``: the objects are returned as a plain JSON list under the response key.
- ``"dict_or_list"``: the objects may come as a list *or* as a dict keyed by id
  (FRED's ``related_tags`` / ``elements`` payloads); the parser normalizes both to
  a list.

Declared on each model class as ``_response_shape`` and consumed by
:func:`fedfred._core._parsers._extract_objects` to choose the extraction strategy.
"""

ParameterValidator = Callable[[str, object], None]
"""Type alias for a parameter validator: takes a parameter name and a value, returns ``None``, and
raises on invalid input."""

CacheValue = str | int | None
"""A single cache-keyable prepared parameter value: a string, an int, or ``None``."""

CacheParameters = dict[str, CacheValue]
"""A prepared request-parameter mapping (parameter name -> value) to be cache-keyed."""

CacheKey = tuple[tuple[str, CacheValue], ...]
"""The hashable, key-sorted form of :data:`CacheParameters`, used as a cache key."""

T = TypeVar("T")
"""Generic type variable for caller-supplied default values."""

RateLimitBucket = Literal["fred", "fraser"]
"""The rate-limit bucket an endpoint belongs to, used to select the applicable limiter."""

JSON: TypeAlias = str | int | float | bool | None | Mapping[str, "JSON"] | Sequence["JSON"]
