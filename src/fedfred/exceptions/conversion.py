from dataclasses import dataclass

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
class DateConversionError(ParameterConversionError):
    """
    Raised for datetime/date conversion issues specifically.
    """

    # Optionally include the expected pattern
    pattern: str = "YYYY-MM-DD"