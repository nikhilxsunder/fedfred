"""

"""

from dataclasses import dataclass
from typing import Optional
from .base import FedFredError


@dataclass(frozen=True, slots=True)
class OptionalDependencyError(FedFredError):
    """Raised when an optional third-party dependency is required but not installed.

    This exception is used when a feature depends on an external library
    (e.g., pandas, polars, dask) that is not part of fedfred's required
    installation set.

    Args:
        package (str): Name of the missing package.
        feature (str, optional): Feature requiring the dependency.
        install_hint (str, optional): Suggested installation command.
        version_spec (str, optional): Required version constraint.

    Examples:
        >>> raise OptionalDependencyError(
        ...     package="polars",
        ...     feature="Helpers.to_pl_df",
        ...     install_hint="pip install polars"
        ... )
    """

    package: str = ""
    feature: Optional[str] = None
    install_hint: Optional[str] = None
    version_spec: Optional[str] = None

    def __post_init__(self) -> None:
        base_message = f"Optional dependency '{self.package}' is not installed"

        if self.version_spec:
            base_message += f" (required version: {self.version_spec})"

        if self.feature:
            base_message += f". This dependency is required for '{self.feature}'."

        if self.install_hint:
            base_message += f" Install it with `{self.install_hint}`."

        super().__init__(base_message)