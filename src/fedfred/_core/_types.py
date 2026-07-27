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

The lowest layer of the core: the package's type aliases, all defined as PEP 695 ``type``
statements and grouped by what they name. Pure vocabulary — no logic, no runtime state — imported
upward by nearly every other core module.

Service and routing identities
    :data:`Service` (the four FRED-family services) and :data:`RateLimitBucket` (the two
    rate-limit buckets each service maps to). :data:`Service` is canonical here; the runtime set
    :data:`fedfred._core._choices._VALID_SERVICES` is derived from it via
    ``get_args(Service.__value__)``, so the two cannot drift.

Backend selectors
    :data:`DataFrameBackend` and :data:`GeoDataFrameBackend` — the closed sets of return-frame
    backends the conversion layer supports.

Endpoint auth
    :data:`AuthStyle` — how the transport injects the API key; carried by
    :attr:`EndpointSpec.auth` and mirrored (derived) by
    :data:`fedfred._core._choices._VALID_AUTH_STYLES`.

Parameter-preparation callables
    :data:`ParameterConverter` (``(name, value) -> value``) and :data:`ParameterValidator`
    (``(name, value) -> None``) — the two callable halves of a :class:`ParameterSpec`.

Response and cache shapes
    :data:`_ResponseShape` (the payload container shape the parsers dispatch on) and the cache-key
    chain :data:`CacheValue` -> :data:`CacheParameters` -> :data:`CacheKey`.

JSON
    :data:`JSON` — a recursive alias for any JSON-serializable value.

Only ``Service`` and ``AuthStyle`` back derived ``_VALID_*`` sets (in :mod:`._choices`); the
backend aliases do **not** — their validity tuples are hand-authored in :mod:`._choices` and
must be kept in sync with these types by hand (see module notes on backend drift).

Aliases:
    Service: The four supported FRED-family services.
    RateLimitBucket: The rate-limit bucket a service maps to.
    DataFrameBackend: Supported DataFrame return backends.
    GeoDataFrameBackend: Supported GeoDataFrame return backends.
    AuthStyle: How the API key is injected for an endpoint.
    ParameterConverter: ``(name, value) -> value`` scalar parameter converter.
    ParameterValidator: ``(name, value) -> None`` parameter validator (raises on invalid).
    _ResponseShape: Container shape of a FRED response payload.
    CacheValue: A single cache-keyable prepared parameter value (str, int, or None).
    CacheParameters: A prepared request-parameter mapping (name -> value) to be cache-keyed.
    CacheKey: The hashable, key-sorted form of CacheParameters, used as a cache key.
    JSON: Any JSON-serializable value (recursive).

See Also:
    - :mod:`fedfred._core._choices`: Derives ``_VALID_SERVICES`` / ``_VALID_AUTH_STYLES`` from
      these aliases, and holds the hand-authored backend validity tuples.
    - :mod:`fedfred._core._specs`: Uses these aliases as field types.
    - :mod:`fedfred._core._parsers`: Dispatches on :data:`_ResponseShape`.
    - :mod:`fedfred._core._converters`: Uses the cache-key chain and backend selectors.
    - :mod:`fedfred._core._mappings`: Uses :data:`RateLimitBucket` for the rate-limit maps.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Literal

type Service = Literal["fred", "fraser", "geofred", "alfred"]
"""The FRED-family services fedfred supports.

The canonical definition; :data:`_VALID_SERVICES` is derived from it via
``get_args(Service.__value__)``, so the runtime check and the static type cannot drift. FRED,
GeoFRED, and ALFRED are one backend (shared key, endpoints, and rate-limit bucket); FRASER is
separate."""

type DataFrameBackend = Literal["pandas", "polars", "dask", "cudf", "fedfred"]
"""The DataFrame return backends fedfred supports.

One of these selects the frame type observation conversions return (see the ``_columns_to_*``
converters). ``"pandas"`` is the only non-optional backend; the rest require their package."""

type GeoDataFrameBackend = Literal[
    "geopandas", "polars-st", "dask-geopandas", "cuspatial", "fedfred"
]
"""The GeoDataFrame return backends fedfred supports for GeoFRED shape data.

``"geopandas"`` is the default; the rest require their package."""

type AuthStyle = Literal["api_key_param", "bearer_header", "api_key_header", "none"]
"""How the transport layer injects the API key for an endpoint.

``"api_key_param"`` (query string, FRED v1 / GeoFRED), ``"bearer_header"`` (FRED v2),
``"api_key_header"`` (FRASER), or ``"none"``. Carried by :attr:`EndpointSpec.auth`;
:data:`_VALID_AUTH_STYLES` is derived from this alias so the two cannot drift."""

type ParameterConverter = Callable[[str, object], object]
"""A scalar parameter converter: ``(name, value) -> value``.

Takes a parameter name and a raw Python value, returns the API-ready (usually wire-string) value.
The converter half of a :class:`ParameterSpec`; see the ``_*_converter`` functions."""

type _ResponseShape = Literal[
    "list",
    "dict_or_list",
]
"""Shape of the object container in a FRED-family response payload.

``"list"`` for a plain list under the payload key, ``"dict_or_list"`` for FRED's id-keyed-dict
element payloads. Selects the extractor branch in :func:`_extract_objects`."""

type ParameterValidator = Callable[[str, object], None]
"""A parameter validator: ``(name, value) -> None``.

Takes a parameter name and a value, returns ``None``, and raises (a ``ParsingError``- or
validation-family error) on invalid input. The validator half of a :class:`ParameterSpec`; see
the ``_validate_*`` functions."""

type CacheValue = str | int | None
"""A single cache-keyable prepared-parameter value: a string, an int, or ``None``.

Constrained to hashable scalars so a :data:`CacheParameters` mapping can be canonicalized into a
hashable :data:`CacheKey`."""

type CacheParameters = dict[str, CacheValue]
"""A prepared request-parameter mapping (parameter name -> value) to be cache-keyed.

The dict form; :func:`_hashable_type_converter` turns it into a :data:`CacheKey`."""

type CacheKey = tuple[tuple[str, CacheValue], ...]
"""The hashable, key-sorted form of :data:`CacheParameters`, used as a cache key.

Produced by :func:`_hashable_type_converter` (sorted by key so insertion order is irrelevant)
and reversed by :func:`_dict_type_converter`."""

type RateLimitBucket = Literal["fred", "fraser"]
"""The rate-limit bucket a service maps to, selecting the applicable limiter.

Keys :data:`RATE_LIMIT_RPM`; :data:`RATE_LIMIT_BUCKET` maps each :data:`Service` to one of these
(FRED/GeoFRED/ALFRED share ``"fred"``, FRASER uses ``"fraser"``)."""

type JSON = str | int | float | bool | None | Mapping[str, "JSON"] | Sequence["JSON"]
"""A JSON-serializable value: string, number, boolean, null, object, or array.

A recursive PEP 695 ``type`` alias — the forward-referenced ``"JSON"`` in the ``Mapping`` and
``Sequence`` arms make it self-referential, so it describes arbitrarily nested JSON."""
