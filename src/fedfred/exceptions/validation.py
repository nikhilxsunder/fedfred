from dataclasses import dataclass, field
from typing import Any, Mapping

from .base import FedfredError


@dataclass(frozen=True, slots=True)
class ValidationError(FedfredError):
    """
    Base class for validation failures (user input / parameter validation).
    """

@dataclass(frozen=True, slots=True)
class ParameterValidationError(ValidationError):
    """
    Raised when a named parameter fails validation.
    """

    parameter: str = ""
    reason: str = ""

    def __str__(self) -> str:
        if self.parameter:
            return f"{self.message} (parameter={self.parameter!r}, reason={self.reason!r})"
        return self.message


@dataclass(frozen=True, slots=True)
class TypeValidationError(ParameterValidationError):
    """
    Raised when a parameter has an invalid type.
    """

    expected: str = ""
    received: str = ""


@dataclass(frozen=True, slots=True)
class ValueValidationError(ParameterValidationError):
    """
    Raised when a parameter has an invalid value/range/format.
    """

    # Example: min/max, allowed set, regex, etc.
    details: Mapping[str, Any] = field(default_factory=dict)