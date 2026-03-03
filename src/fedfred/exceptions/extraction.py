

from dataclasses import dataclass

from fedfred.exceptions.base import FedfredError


@dataclass(frozen=True, slots=True)
class ExtractionError(FedfredError):
    """Raised when extraction of a value from an API response fails."""

    
