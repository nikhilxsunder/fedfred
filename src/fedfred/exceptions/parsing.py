

from dataclasses import dataclass

from fedfred.exceptions.base import FedfredError


@dataclass(frozen=True, slots=True)
class ParsingError(FedfredError):
    """Raised when parsing of a value from an API response fails."""

    
