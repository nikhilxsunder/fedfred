from __future__ import annotations

import importlib
from types import ModuleType

from ..exceptions.dependencies import OptionalDependencyError


def _require_module(module: str, feature: str, extra: str | None = None) -> ModuleType:
    """Import an optional dependency or raise a typed OptionalDependencyError."""
    try:
        return importlib.import_module(module)
    except ImportError as e:
        pkg = module.split(".")[0]
        raise OptionalDependencyError(
            message=f"{pkg} is required for {feature}.",
            package=pkg,
            feature=feature,
            install_hint=f"pip install fedfred[{extra or pkg}]",
        ) from e