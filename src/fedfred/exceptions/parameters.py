
from dataclasses import dataclass
from typing import Any, Dict, Optional
from fedfred.exceptions.base import FedFredError

@dataclass(frozen=True, slots=True)
class ParameterServiceError(FedFredError):
    """Rasied when an error occurs within the service resolution for parameter preparation."""
    service: str = ""
    reason: str = ""
    details: Optional[Dict[str, Any]] = None
