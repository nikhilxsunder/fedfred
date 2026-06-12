# filepath: /src/fedfred/exceptions/core/building.py
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
"""Build-layer exceptions for the fedfred core package.

The error hierarchy for :mod:`fedfred._core._builders`, which assembles
:class:`~fedfred._core._specs.EndpointSpec` registries at import time. A
construction failure surfaces here, scoped under :class:`BuildError` so a caller
can catch any build failure, or :class:`EndpointSpecBuildError` for the specific
case of one endpoint's spec failing to construct.

Classes:
    BuildError: Base for any build-layer failure.
    EndpointSpecBuildError: A single endpoint's EndpointSpec failed to construct.

See Also:
    - :mod:`fedfred._core._builders`: Raises these while building the registry.
    - :class:`fedfred.exceptions.core.base.CoreError`: The core-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import CoreError

__all__ = ["BuildError", "EndpointSpecBuildError"]


@dataclass(frozen=True, slots=True)
class BuildError(CoreError):
    """Base class for failures while building specifications at import time.

    The module catch-all for :mod:`fedfred._core._builders`: catch this to handle
    any build-layer failure regardless of which spec or endpoint was being
    constructed. Adds no fields; inherits the structured payload (:attr:`message`,
    :attr:`context`, :attr:`original_exception`) from :class:`CoreError`.
    """


@dataclass(frozen=True, slots=True)
class EndpointSpecBuildError(BuildError):
    """Raised when an :class:`EndpointSpec` cannot be constructed for an endpoint.

    The builder constructs every endpoint's spec in a loop at import time; when one
    fails its construction-time validation, that error is wrapped here with the
    service and endpoint name, so the import-time failure identifies which registry
    entry is malformed rather than surfacing a bare validation message with no
    endpoint context. The underlying error is chained via ``raise … from`` and also
    carried on :attr:`CoreError.original_exception`.

    Attributes:
        service (str): The service whose registry was being built (``"fred"``,
            ``"alfred"``, ``"geofred"``, or ``"fraser"``); empty string if unset.
        endpoint_name (str): The endpoint whose spec failed to construct (e.g.
            ``"get_series_observations"``); empty string if unset.
        message (str): Human-readable message (inherited from :class:`CoreError`).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The wrapped spec-validation
            error (inherited).

    Examples:
        >>> from fedfred.exceptions.core.building import BuildError, EndpointSpecBuildError
        >>> exc = EndpointSpecBuildError(
        ...     message="Failed to build EndpointSpec.",
        ...     service="fred",
        ...     endpoint_name="get_series_observations",
        ... )
        >>> str(exc)
        "Failed to build EndpointSpec. (service='fred', endpoint='get_series_observations')"
        >>> isinstance(exc, BuildError)
        True
    """

    service: str = ""
    """The service whose endpoint registry was being built when construction failed."""

    endpoint_name: str = ""
    """The endpoint name whose :class:`EndpointSpec` failed to construct."""

    def __str__(self) -> str:
        """Return the message, suffixed with service/endpoint context when known.

        Returns:
            str: :attr:`message` with ``(service=…, endpoint=…)`` appended when
            :attr:`endpoint_name` is set; the bare :attr:`message` otherwise.
        """
        if self.endpoint_name:
            return f"{self.message} (service={self.service!r}, endpoint={self.endpoint_name!r})"

        return self.message
