from dataclasses import dataclass
from typing import Tuple
from .base import FedfredError

@dataclass(frozen=True, slots=True)
class ConversionError(FedfredError):
    """
    Base class for conversion failures (e.g., converting datetimes, lists, enums
    into API-compatible strings).
    """

@dataclass(frozen=True, slots=True)
class ParameterConversionError(ConversionError):
    """
    Raised when conversion of a specific parameter fails.
    """

    parameter: str = ""
    value_repr: str = ""
    target_format: str = ""

    def __str__(self) -> str:
        if self.parameter:
            return (
                f"{self.message} (parameter={self.parameter!r}, "
                f"value={self.value_repr!r}, target_format={self.target_format!r})"
            )
        return self.message

@dataclass(frozen=True, slots=True)
class TypeConversionError(ParameterConversionError):
    """
    Raised when a parameter value cannot be converted to the expected type/format.
    """

    expected: str = ""
    received: str = ""

@dataclass(frozen=True, slots=True)
class DataFrameConversionError(ConversionError):
    """Raised when conversion to a DataFrame fails."""

    backend: str = "pandas"
    missing_fields: Tuple[str, ...] = ()
    details: str = ""

    def __str__(self) -> str:
        parts: list[str] = [self.message]
        if self.backend:
            parts.append(f"backend={self.backend!r}")
        if self.missing_fields:
            parts.append(f"missing_fields={self.missing_fields!r}")
        if self.details:
            parts.append(f"details={self.details!r}")
        return " (" .join([parts[0], ", ".join(parts[1:])]) + ")" if len(parts) > 1 else parts[0]

@dataclass(frozen=True, slots=True)
class GeoDataFrameConversionError(DataFrameConversionError):
    """Raised when conversion to a GeoDataFrame fails."""

    backend: str = "geopandas"
    geometry_column: str = "geometry"
    crs: str = ""

@dataclass(frozen=True, slots=True)
class DateConversionError(ParameterConversionError):
    """
    Raised for datetime/date conversion issues specifically.
    """

    # Optionally include the expected pattern
    pattern: str = "YYYY-MM-DD"
