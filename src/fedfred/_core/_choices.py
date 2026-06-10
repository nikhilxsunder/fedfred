FRED_FREQUENCIES = {
    "d",
    "w",
    "bw",
    "m",
    "q",
    "sa",
    "a",
    "wef",
    "weth",
    "wew",
    "wetu",
    "wem",
    "wesu",
    "wesa",
    "bwew",
    "bwem",
}
"""Valid ``frequency`` values for FRED API parameters."""

FRED_UNITS = {
    "lin",
    "chg",
    "ch1",
    "pch",
    "pc1",
    "pca",
    "cch",
    "cca",
    "log",
}
"""Valid ``units`` values for FRED API parameters."""

SORT_ORDERS = {"asc", "desc"}
"""Valid ``sort_order`` values for FRED API parameters."""

AGGREGATION_METHODS = {"sum", "avg", "eop"}
"""Valid ``aggregation_method`` values for FRED API parameters."""

OUTPUT_TYPES = {1, 2, 3, 4}
"""Valid ``output_type`` values for FRED API parameters."""

FRED_ORDER_BY = {
    "series_id",
    "title",
    "units",
    "frequency",
    "seasonal_adjustment",
    "realtime_start",
    "realtime_end",
    "last_updated",
    "observation_start",
    "observation_end",
    "popularity",
    "group_popularity",
    "series_count",
    "created",
    "name",
    "release_id",
    "press_release",
    "group_id",
    "search_rank",
}
"""Valid ``order_by`` values for FRED API parameters."""

GEOFRED_REGION_TYPES = {
    "bea",
    "msa",
    "frb",
    "necta",
    "state",
    "country",
    "county",
    "censusregion",
    "censusdivision",
}
"""Valid region-type values for GeoFRED API parameters."""