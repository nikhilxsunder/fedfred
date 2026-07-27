# filepath: /src/fedfred/_core/_specs.py
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
"""Spec value types for the fedfred core package.

The immutable specification dataclasses that describe the API surface — the typed vocabulary the
builders construct, the registries hold, and the resolvers hand back. :class:`EndpointSpec`
captures everything needed to issue one endpoint's request (service, URL, auth style, default
params/payload/headers); :class:`ParameterSpec` captures how one request parameter is prepared
(converter, validator, required). The two are consumed by different layers: endpoint specs by
the endpoint registry and resolver, parameter specs by the parameter preparers.

Both are ``frozen=True, slots=True`` — built once at import time, validated at construction,
shared across all requests and threads, and read on every request. They hold no secrets and
perform no I/O; they are pure descriptions consumed by the layers above them. Note that
``frozen=True`` freezes the fields, not the dicts an :class:`EndpointSpec` points to, which are
shared and must never be mutated in place (see :class:`EndpointSpec` Notes).

Classes:
    EndpointSpec: Immutable request specification for one API endpoint.
    ParameterSpec: Converter/validator/required spec for one request parameter.

See Also:
    - :mod:`fedfred._core._builders`: Constructs :class:`EndpointSpec` instances.
    - :mod:`fedfred._core._registries`: Holds the built endpoint and parameter specs.
    - :mod:`fedfred._core._resolvers`: Hands back :class:`EndpointSpec` at request time.
    - :mod:`fedfred._core._preparers`: Consumes :class:`ParameterSpec` to prepare parameters.
    - :mod:`fedfred._core._types`: Provides ``AuthStyle``, ``Service``, ``ParameterConverter``,
      and ``ParameterValidator``.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..exceptions import (
    EndpointAuthError,
    EndpointFieldTypeError,
    EndpointServiceError,
    EndpointURLError,
)
from ._choices import _VALID_AUTH_STYLES, _VALID_SERVICES
from ._types import (
    AuthStyle,
    ParameterConverter,
    ParameterValidator,
    Service,
)


@dataclass(frozen=True, slots=True)
class EndpointSpec:
    """Immutable request specification for a single FRED-family API endpoint.

    Instances are pre-built into :data:`_ENDPOINT_REGISTRY` at import time and shared across all
    requests and threads for the life of the process. ``frozen=True`` makes accidental field
    reassignment raise :class:`dataclasses.FrozenInstanceError`; ``slots=True`` cuts per-instance
    memory and gives a small attribute-access speedup, worthwhile because the spec is read on
    every request. Validation runs once in :meth:`__post_init__` at construction, so a malformed
    spec fails at import rather than on first request.

    Attributes:
        service (Service): The owning service (``"fred"``, ``"alfred"``, ``"geofred"``, or
            ``"fraser"``).
        url (str): The absolute ``https://`` URL for the endpoint. FRASER endpoints with path
            parameters contain positional ``{}`` placeholders filled at request time via
            :meth:`str.format`.
        auth (AuthStyle): How the transport layer injects the API key at request time. The secret
            itself is never stored on the spec.
        params (dict[str, str] | None): Default query parameters copy-merged (never mutated) into
            each request, or ``None`` when the endpoint takes no defaults.
        payload (dict[str, Any] | None): Default POST body, or ``None`` for GET endpoints.
        headers (dict[str, str] | None): Default headers, or ``None`` when none are needed.

    Examples:
        >>> from fedfred._core._resolvers import _resolve_endpoint
        >>> spec = _resolve_endpoint("fred", "get_series_observations")
        >>> spec.service
        'fred'
        >>> spec.url
        'https://api.stlouisfed.org/fred/series/observations'
        >>> spec.params
        {'file_type': 'json'}
        >>> spec.auth
        'api_key_param'

    Notes:
        ``frozen=True`` freezes the *fields*, not the dicts they point to. The
        ``params`` / ``payload`` / ``headers`` dicts are **shared** between every spec built from
        the same base-parameter constant (e.g. :data:`_FRED_BASE_PARAMETERS`), so consumers must
        copy-merge (``{**spec.params, ...}``) and never write through the spec — one in-place
        mutation in the transport layer would corrupt every endpoint sharing that default dict.
    """

    service: Service
    """The owning service identifier (``"fred"``, ``"alfred"``, ``"geofred"``, or ``"fraser"``)."""

    url: str
    """The absolute ``https://`` URL for the endpoint. May contain positional ``{}`` placeholders
    for FRASER path parameters, filled at request time via :meth:`str.format`."""

    auth: AuthStyle = "api_key_param"
    """API-key injection style applied by the transport layer at request time. Defaults to
    ``"api_key_param"`` (the FRED v1 / GeoFRED query-parameter convention)."""

    params: dict[str, str] | None = None
    """Default query parameters copy-merged into each request to this endpoint, or ``None`` for
    endpoints with no defaults. Shared object — never mutate in place (see class Notes)."""

    payload: dict[str, Any] | None = None
    """Default POST payload for endpoints that take a body, or ``None`` for GET endpoints. Shared
    object — never mutate in place."""

    headers: dict[str, str] | None = None
    """Default headers for requests to this endpoint, or ``None`` for endpoints that take no
    custom headers. Shared object — never mutate in place."""

    def __post_init__(self) -> None:
        """Validate the endpoint specification at construction time.

        Runs once per spec, at import time, because every instance is built into
        :data:`_ENDPOINT_REGISTRY` during module load. A malformed spec fails at ``import
        fedfred`` rather than on first request, keeping call-site code free of defensive shape
        checks.

        Raises:
            EndpointServiceError: If :attr:`service` is not a known :data:`Service` value.
            EndpointURLError: If :attr:`url` is empty, non-string, or does not start with
                ``https://``.
            EndpointAuthError: If :attr:`auth` is not a known :data:`AuthStyle` value.
            EndpointFieldTypeError: If :attr:`params`, :attr:`payload`, or :attr:`headers` is set
                but is not a :class:`dict`. The offending field name is carried in the error's
                ``field``.

        Examples:
            >>> from fedfred._core._specs import EndpointSpec
            >>> try:
            ...     EndpointSpec(service="frd", url="https://api.stlouisfed.org/fred")
            ... except Exception as exc:
            ...     print(type(exc).__name__)
            EndpointServiceError
        """
        if self.service not in _VALID_SERVICES:
            raise EndpointServiceError(
                message=f"EndpointSpec.service must be one of {sorted(_VALID_SERVICES)}, "
                f"got {self.service!r}.",
                field="service",
                received=str(self.service),
                valid=tuple(sorted(_VALID_SERVICES)),
            )

        if not isinstance(self.url, str) or not self.url.strip():
            raise EndpointURLError(
                message="EndpointSpec.url must be a non-empty string.",
                field="url",
            )

        if not self.url.startswith("https://"):
            raise EndpointURLError(
                message="EndpointSpec.url must start with 'https://'.",
                field="url",
            )

        if self.auth not in _VALID_AUTH_STYLES:
            raise EndpointAuthError(
                message=f"EndpointSpec.auth must be one of {sorted(_VALID_AUTH_STYLES)}, "
                f"got {self.auth!r}.",
                field="auth",
                received=str(self.auth),
                valid=tuple(sorted(_VALID_AUTH_STYLES)),
            )

        for field_name, value in (
            ("params", self.params),
            ("payload", self.payload),
            ("headers", self.headers),
        ):
            if value is not None and not isinstance(value, dict):
                raise EndpointFieldTypeError(
                    message=f"EndpointSpec.{field_name} must be a dictionary or None.",
                    field=field_name,
                    received=type(value).__name__,
                )


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    """Specification for preparing a single API request parameter.

    Pairs an optional converter (run first, to normalize a Python value into its wire form) with
    an optional validator (run on the converted value) and a required flag. Consumed by
    :func:`_prepare_parameters`, which applies converter then validator per parameter and, after
    processing, enforces every ``required`` spec.

    Attributes:
        converter (ParameterConverter | None): Optional ``(name, value) -> value`` callable that
            normalizes a raw value into its API form. Run before validation. ``None`` means the
            value is used as-is.
        validator (ParameterValidator | None): Optional ``(name, value) -> None`` callable that
            raises on an invalid value and returns nothing. Run after conversion. ``None`` means
            no validation.
        required (bool): Whether the parameter must be present and non-``None`` after preparation.
            A ``None`` value is treated as absent, so ``required=True`` with a supplied ``None``
            still fails the required-check.

    Examples:
        >>> from fedfred._core._specs import ParameterSpec
        >>> from fedfred._core._validators import _validate_nonnegative_int
        >>> spec = ParameterSpec(validator=_validate_nonnegative_int, required=True)
        >>> spec.required
        True
    """

    converter: ParameterConverter | None = None
    """Optional ``(name, value) -> value`` converter, run before validation to normalize raw
    values into their API form. ``None`` leaves the value unchanged."""

    validator: ParameterValidator | None = None
    """Optional ``(name, value) -> None`` validator, run after conversion; raises on an invalid
    value and returns nothing. ``None`` skips validation."""

    required: bool = False
    """Whether the parameter must be present and non-``None`` after preparation. When ``True``, an
    absent or ``None``-valued parameter raises
    :class:`~fedfred.exceptions.MissingParameterError` from :func:`_prepare_parameters` (not a
    validation error — the value never reaches the validator)."""
