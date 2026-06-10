

# Endpoint Resolution
def _resolve_endpoint(service: Service, endpoint_name: str) -> EndpointSpec:
    """Resolve a ``(service, endpoint_name)`` pair to its pre-built specification.

    Two dict lookups, no allocation. The endpoint name is normalized by
    ``.strip().lower()`` before the second lookup so callers can pass
    whitespace-padded or differently cased names without each call site
    needing to defend the registry shape.

    Args:
        service (Service): The calling client's service identity (``"fred"``, ``"alfred"``, ``"geofred"``, or ``"fraser"``).
        endpoint_name (str): The endpoint name to resolve, e.g., ``"get_series_observations"``. Whitespace is trimmed and the name is lowercased before lookup.

    Returns:
        EndpointSpec: The immutable, import-time-validated specification.

    Raises:
        EndpointServiceError: If ``service`` is not a key in :data:`_ENDPOINT_REGISTRY`.
        EndpointUnsupportedError: If ``endpoint_name`` is not recognized within the resolved service's registry.

    Examples:
        >>> from ._endpoints import _resolve_endpoint
        >>> spec = _resolve_endpoint("fred", "get_series_observations")
        >>> spec.url
        'https://api.stlouisfed.org/fred/series/observations'
        >>> # FRED and ALFRED return separate specs that share most fields
        >>> # but carry different `service` identities.
        >>> spec is _resolve_endpoint("alfred", "get_series_observations")
        False

    Notes:
        Endpoint names are unique per service, not globally; the same name
        may resolve under multiple services by design (FRED and ALFRED
        share endpoint names, differing only in vintage-parameter handling
        at the parameter-preparation layer).
    """
    try:
        service_registry = _ENDPOINT_REGISTRY[service]
    except KeyError as exc:
        raise EndpointServiceError(
            f"Unknown service: {service!r}. Expected one of {sorted(_ENDPOINT_REGISTRY)}."
        ) from exc

    try:
        return service_registry[endpoint_name.strip().lower()]
    except KeyError as exc:
        raise EndpointUnsupportedError(
            f"Unsupported endpoint {endpoint_name!r} for service {service!r}."
        ) from exc
    
def _resolve_preparation_function(
    parameters: Mapping[str, Any] | None,
    service: str
) -> dict[str, Any]:
    """Prepare parameters using the preparer for ``service``.

    Args:
        parameters (Mapping[str, Any] | None): The raw parameters to prepare.
        service (str): The service name (case-insensitive): ``"fred"``, ``"geofred"``, or ``"fraser"``.

    Returns:
        dict[str, Any]: The prepared parameters from the resolved service preparer.

    Raises:
        ParameterServiceError: If ``service`` is not a recognized service.
        TypeConversionError: If a converter fails to normalize a value.
        TypeValidationError: If a validator rejects a value's type.
        ValueValidationError: If a value is invalid or a required parameter is missing.

    Examples:
        >>> from fedfred._core._parameters import _resolve_preparation_function
        >>> _resolve_preparation_function({"limit": 100}, service="fred")
        {'limit': 100}
    """
    service = service.lower()

    try:
        return FRED_PREPARATION_FUNCTIONS[service](parameters)

    except KeyError as exc:
        raise ParameterServiceError(
            message=f"Unknown service {service!r} for parameter preparation.",
            service=service,
            reason="Unrecognized service name.",
            details={"service": service, "expected_services": tuple(FRED_PREPARATION_FUNCTIONS)},
        ) from exc