# filepath: /src/fedfred/exceptions/core/conversion.py
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
"""Conversion-layer exceptions for the fedfred core package.

The error hierarchy for :mod:`fedfred._core._converters`. The live raisers are the
scalar parameter converters (:class:`TypeConversionError` family); DataFrame build
failures get :class:`DataFrameConversionError`, and missing optional backends raise
:class:`~fedfred.exceptions.core.loading.OptionalDependencyError` from the loader
rather than a conversion error.

Classes:
    ConversionError: Base for any conversion failure.
    ParameterConversionError: A request-parameter value could not be converted.
    TypeConversionError: A value was not one of the accepted input types.
    DateConversionError: A date/datetime value could not be converted.
    DataFrameConversionError: Building a backend frame failed.
    GeoDataFrameConversionError: Building a backend geo-frame failed.

See Also:
    - :mod:`fedfred._core._converters`: Raises these.
    - :class:`fedfred.exceptions.core.base.CoreError`: The core-layer base.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import CoreError

__all__ = [
    "ConversionError",
    "DataFrameConversionError",
    "DateConversionError",
    "GeoDataFrameConversionError",
    "ParameterConversionError",
    "TypeConversionError",
]


@dataclass(frozen=True, slots=True)
class ConversionError(CoreError):
    """Base class for conversion failures in the core layer.

    The module catch-all for :mod:`fedfred._core._converters`: catch this to handle
    any conversion failure, whether a request parameter, a date, or a backend frame
    was being converted. Adds no fields; inherits the structured payload
    (:attr:`message`, :attr:`context`, :attr:`original_exception`) from
    :class:`CoreError`.
    """


@dataclass(frozen=True, slots=True)
class ParameterConversionError(ConversionError):
    """Raised when a scalar request-parameter value cannot be converted to its wire form.

    Base of the parameter-conversion family, raised (via its subclasses) by the
    scalar converters in :mod:`fedfred._core._converters` when a caller-supplied
    value cannot be normalized into the string form FRED expects on the wire.

    Attributes:
        parameter (str): The name of the parameter that failed to convert; empty
            string if unset.
        value_repr (str): A repr of the offending value, when captured.
        target_format (str): The wire format the value was being converted to,
            when relevant.
        message (str): Human-readable message (inherited from :class:`CoreError`).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error, if any
            (inherited).
    """

    parameter: str = ""
    """The name of the parameter that failed to convert; empty string if unset."""

    value_repr: str = ""
    """A repr of the offending value, when captured."""

    target_format: str = ""
    """The wire format the value was being converted to, when relevant."""

    def __str__(self) -> str:
        """Return the message, suffixed with parameter context when known.

        Returns:
            str: :attr:`message` with ``(parameter=…, value=…, target_format=…)``
            appended when :attr:`parameter` is set; the bare :attr:`message`
            otherwise.
        """
        if self.parameter:
            return (
                f"{self.message} (parameter={self.parameter!r}, "
                f"value={self.value_repr!r}, target_format={self.target_format!r})"
            )
        return self.message


@dataclass(frozen=True, slots=True)
class TypeConversionError(ParameterConversionError):
    """Raised when a parameter value is not one of the accepted input types.

    The most common parameter-conversion failure: the converter received a value
    whose type it cannot handle (e.g. an ``int`` where ``str | date | datetime``
    was expected). Overrides ``__str__`` to surface the accepted-vs-received types
    rather than the unused ``value_repr`` / ``target_format`` of its base.

    Attributes:
        expected (str): A description of the accepted input type(s), e.g.
            ``"str | date | datetime"``.
        received (str): The type name of the value actually received.
        parameter (str): The parameter name (inherited).
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error (inherited).
    """

    expected: str = ""
    """A description of the accepted input type(s), e.g. ``"str | date | datetime"``."""

    received: str = ""
    """The type name of the value actually received."""

    def __str__(self) -> str:
        """Return the message, suffixed with expected/received types when a parameter is known.

        Returns:
            str: :attr:`message` with ``(parameter=…, expected=…, received=…)``
            appended when :attr:`parameter` is set; the bare :attr:`message`
            otherwise.
        """
        if self.parameter:
            return (
                f"{self.message} (parameter={self.parameter!r}, "
                f"expected={self.expected!r}, received={self.received!r})"
            )
        return self.message


@dataclass(frozen=True, slots=True)
class DateConversionError(ParameterConversionError):
    """Raised for date/datetime conversion failures specifically.

    A specialization of :class:`ParameterConversionError` for date-valued
    parameters, carrying the expected date pattern so a caller can distinguish a
    date-format failure from a generic type failure.

    Attributes:
        pattern (str): The expected date format. Defaults to ``"YYYY-MM-DD"``.
        parameter (str): The parameter name (inherited).
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error (inherited).
    """

    pattern: str = "YYYY-MM-DD"
    """The expected date format the value should have matched."""


@dataclass(frozen=True, slots=True)
class DataFrameConversionError(ConversionError):
    """Raised when building a backend DataFrame from observation columns fails.

    Concerns the output side rather than parameters: when assembling a
    pandas/polars/dask (or geopandas) frame from the columnar data fails for a
    reason *other* than a missing optional backend — a missing backend raises
    :class:`~fedfred.exceptions.core.loading.OptionalDependencyError` from the
    loader instead.

    Attributes:
        backend (str): The frame backend being built. Defaults to ``"pandas"``.
        details (str): Additional detail about the failure, when available.
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error (inherited).
    """

    backend: str = "pandas"
    """The frame backend being built when the conversion failed."""

    details: str = ""
    """Additional detail about the failure, when available."""

    def __str__(self) -> str:
        """Return the message, suffixed with backend/details context.

        Returns:
            str: :attr:`message` with ``(backend=…, details=…)`` appended when
            :attr:`backend` is set; the bare :attr:`message` otherwise.
        """
        if self.backend:
            return f"{self.message} (backend={self.backend!r}, details={self.details!r})"
        return self.message


@dataclass(frozen=True, slots=True)
class GeoDataFrameConversionError(DataFrameConversionError):
    """Raised when building a backend GeoDataFrame fails.

    A specialization of :class:`DataFrameConversionError` for the GeoFRED spatial
    frames (geopandas / dask-geopandas / polars-st), adding the geometry column and
    CRS context relevant to a spatial build.

    Attributes:
        backend (str): The geo-frame backend. Defaults to ``"geopandas"``.
        geometry_column (str): The geometry column name. Defaults to ``"geometry"``.
        crs (str): The coordinate reference system, when known.
        details (str): Additional failure detail (inherited from
            :class:`DataFrameConversionError`).
        message (str): Human-readable message (inherited).
        context (Mapping[str, Any]): Optional structured context (inherited).
        original_exception (BaseException | None): The underlying error (inherited).
    """

    backend: str = "geopandas"
    """The geo-frame backend being built when the conversion failed."""

    geometry_column: str = "geometry"
    """The geometry column name."""

    crs: str = ""
    """The coordinate reference system, when known."""
