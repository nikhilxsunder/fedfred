from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import geopandas as gpd

from ..settings import _resolve_geodataframe_backend

if TYPE_CHECKING:
    import dask_geopandas as dd_gpd  # pragma: no cover
    import polars_st as st  # pragma: no cover


# -------------------This-Section--Will-Be-Refactored-By-GeoFred-Objects-Design-Implementation-------------------#
def _geopandas_geodataframe_converter(
    shapefile: gpd.GeoDataFrame, meta_data: dict
) -> gpd.GeoDataFrame:
    """Attach GeoFRED observation values to a shapefile GeoDataFrame.

    Args:
        shapefile (geopandas.GeoDataFrame): The region geometries, with a ``name`` column.
        meta_data (dict): The GeoFRED response metadata containing a ``data`` section.

    Returns:
        geopandas.GeoDataFrame: ``shapefile`` indexed by ``name`` with ``value`` and ``series_id``
            columns populated from the metadata.

    Raises:
        GeoDataFrameConversionError: If ``meta_data`` has no ``data`` section.

    Examples:
        >>> from fedfred._core._converters import _geopandas_geodataframe_converter  # doctest: +SKIP
        >>> _geopandas_geodataframe_converter(shapefile, meta_data)  # doctest: +SKIP

    Notes:
        Matches observation rows to geometries by region name; geometries with no
        matching observation keep ``None`` for ``value`` and ``series_id``.
    """
    shapefile.set_index("name", inplace=True)

    shapefile["value"] = None

    shapefile["series_id"] = None

    data_section = meta_data.get("data", {})

    if not data_section:
        raise GeoDataFrameConversionError(
            message="GeoDataFrame conversion failed: No data section found in metadata",
            backend="geopandas",
            missing_fields=("data",),
            details="Metadata must contain 'data' section with observations",
        )

    data_key = next(iter(data_section))

    items = data_section[data_key]

    for item in items:
        if item["region"] in shapefile.index:
            shapefile.loc[item["region"], "value"] = item["value"]

            shapefile.loc[item["region"], "series_id"] = item["series_id"]

    return shapefile


def _dask_geopandas_geodataframe_converter(
    shapefile: gpd.GeoDataFrame, meta_data: dict
) -> dd_gpd.GeoDataFrame:
    """Attach GeoFRED observation values to a shapefile as a Dask GeoPandas GeoDataFrame.

    Args:
        shapefile (geopandas.GeoDataFrame): The region geometries, with a ``name`` column.
        meta_data (dict): The GeoFRED response metadata containing a ``data`` section.

    Returns:
        dask_geopandas.GeoDataFrame: The populated GeoDataFrame as a single-partition Dask GeoPandas frame.

    Raises:
        OptionalDependencyError: If dask-geopandas is not installed.
        GeoDataFrameConversionError: If ``meta_data`` has no ``data`` section.

    Examples:
        >>> from fedfred._core._converters import _dask_geopandas_geodataframe_converter  # doctest: +SKIP
        >>> _dask_geopandas_geodataframe_converter(shapefile, meta_data)  # doctest: +SKIP

    Notes:
        Built by populating a geopandas GeoDataFrame first
        (:func:`_geopandas_geodataframe_converter`), then wrapping it in a
        single-partition Dask GeoPandas frame.
    """
    try:
        import dask_geopandas as dd_gpd

    except ImportError as e:
        raise OptionalDependencyError(
            message=f"{e}: Dask GeoPandas is not installed. Install it with `pip install dask-geopandas` to use this method.",
            package="dask-geopandas",
            feature="Helpers.to_dd_gpd_gdf",
            install_hint="pip install dask-geopandas",
        ) from e

    gdf = _geopandas_geodataframe_converter(shapefile, meta_data)

    return dd_gpd.from_geopandas(gdf, npartitions=1)


def _polars_geodataframe_converter(shapefile: gpd.GeoDataFrame, meta_data: dict) -> st.GeoDataFrame:
    """Attach GeoFRED observation values to a shapefile as a Polars-ST GeoDataFrame.

    Args:
        shapefile (geopandas.GeoDataFrame): The region geometries, with a ``name`` column.
        meta_data (dict): The GeoFRED response metadata containing a ``data`` section.

    Returns:
        polars_st.GeoDataFrame: The populated GeoDataFrame converted to Polars-ST.

    Raises:
        OptionalDependencyError: If polars-st is not installed.
        GeoDataFrameConversionError: If ``meta_data`` has no ``data`` section.

    Examples:
        >>> from fedfred._core._converters import _polars_geodataframe_converter  # doctest: +SKIP
        >>> _polars_geodataframe_converter(shapefile, meta_data)  # doctest: +SKIP

    Notes:
        Built by populating a geopandas GeoDataFrame first
        (:func:`_geopandas_geodataframe_converter`), then converting it to
        Polars-ST.
    """
    try:
        import polars_st as st

    except ImportError as e:
        raise OptionalDependencyError(
            message=f"{e}: Polars with geospatial support is not installed. Install it with `pip install polars-st` to use this method.",
            package="polars-st",
            feature="Helpers.to_pl_st_gdf",
            install_hint="pip install polars-st",
        ) from e

    gdf = _geopandas_geodataframe_converter(shapefile, meta_data)

    return st.from_geopandas(gdf)


GEODATAFRAME_CONVERTER_MAP: dict[str, Callable] = {
    "geopandas": _geopandas_geodataframe_converter,
    "dask": _dask_geopandas_geodataframe_converter,
    "polars": _polars_geodataframe_converter,
}
"""Mapping of geodataframe backend name to its observation converter."""


def _resolve_geodataframe_converter(backend: str | None = None) -> Callable:
    """Return the geodataframe converter for a backend.

    Args:
        backend (str | None): The backend name (``"geopandas"``, ``"dask"``, or ``"polars"``). If ``None``, the configured default backend is used.

    Returns:
        Callable: The observation converter for the resolved backend.

    Examples:
        >>> from fedfred._core._converters import _resolve_geodataframe_converter
        >>> _resolve_geodataframe_converter("geopandas").__name__
        '_geopandas_geodataframe_converter'
    """
    if backend is None:
        backend = _resolve_geodataframe_backend()

    return GEODATAFRAME_CONVERTER_MAP[backend]


# ---------------------------------------------------------------------------------------------------------------#
