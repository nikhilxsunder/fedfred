

from dataclasses import dataclass

from fedfred.exceptions.base import FedFredError


@dataclass(frozen=True, slots=True)
class ParsingError(FedFredError):
    """Raised when parsing of a value from an API response fails."""

    
