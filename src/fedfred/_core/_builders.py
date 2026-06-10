


def _build_fred_style_specs(service: Service) -> dict[str, EndpointSpec]:
    """Build the per-endpoint :class:`EndpointSpec` registry for a FRED-style service.

    FRED and ALFRED share host, paths, and auth style; they differ only in
    vintage-parameter handling, which lives in the parameter-preparation
    layer rather than at the endpoint level. This helper produces the same
    set of specs for both, stamped with the appropriate ``service`` value
    so resolution returns the calling client's service identity.

    Endpoints whose path begins with ``/v2/`` use bearer-header auth and
    :data:`_FRED_VERSION_TWO_BASE_PARAMETERS`; all other endpoints use
    query-parameter auth and :data:`_FRED_BASE_PARAMETERS`.

    Args:
        service (Service): The service identity to stamp onto each spec — either ``"fred"`` or ``"alfred"``.

    Returns:
        dict[str, EndpointSpec]: Mapping of endpoint names to fully
        constructed, validated :class:`EndpointSpec` instances ready for
        registration into :data:`_ENDPOINT_REGISTRY`.

    Notes:
        Called once per FRED-style service at module import time. Not
        intended to be invoked at request time.
    """
    specs: dict[str, EndpointSpec] = {}

    for name, path in _FRED_ENDPOINT_MAP.items():
        if path.startswith("/v2/"):
            specs[name] = EndpointSpec(
                service=service,
                url=f"{_ST_LOUIS_FED_BASE_URL}{_FRED_PATH}{path}",
                auth="bearer_header",
                params=_FRED_VERSION_TWO_BASE_PARAMETERS,
            )
        else:
            specs[name] = EndpointSpec(
                service=service,
                url=f"{_ST_LOUIS_FED_BASE_URL}{_FRED_PATH}{path}",
                auth="api_key_param",
                params=_FRED_BASE_PARAMETERS,
            )

    return specs