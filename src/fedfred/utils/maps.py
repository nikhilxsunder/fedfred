from.__validators import __Validators, __AsyncValidators


FRED_PARAMETERS_MAP = {
    'category_id': 
    {
        'type_condition': lambda x: isinstance(x, int),
        'value_condition': lambda x: x >= 0,
        'error_message': "category_id must be a non-negative integer"
    },
    'realtime_start': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': __Validators.__datestring_validation,
        'async_value_condition': __AsyncValidators.__datestring_validation,
        'error_message': "realtime_start must be a valid date string in 'YYYY-MM-DD' format"
    },
    'realtime_end':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': __Validators.__datestring_validation,
        'async_value_condition': __AsyncValidators.__datestring_validation,
        'error_message': "realtime_end must be a valid date string in 'YYYY-MM-DD' format"
    },
    'limit': 
    {
        'type_condition': lambda x: isinstance(x, int), 
        'value_condition': lambda x: x >= 0,
        'error_message': "limit must be a non-negative integer"
    },
    'page': 
    {
        'type_condition': lambda x: isinstance(x, int), 
        'value_condition': lambda x: x >= 0,
        'error_message': "page must be a non-negative integer"
    },
    'format':
    {
        'type_condition': lambda x: isinstance(x, str), 
        'value_condition': lambda x: x == 'json', 
        'error_message': "format must be 'json'"
    },
    'offset': 
    {
        'type_condition': lambda x: isinstance(x, int), 
        'value_condition': lambda x: x >= 0,
        'error_message': "offset must be a non-negative integer"
    },
    'sort_order': 
    {
        'type_condition': lambda x: isinstance(x, str), 
        'value_condition': lambda x: x in {'asc', 'desc'},
        'error_message': "sort_order must be 'asc' or 'desc'"
    },
    'order_by': 
    {
        'type_condition': lambda x: isinstance(x, str), 
        'value_condition': lambda x: x in {'series_id', 'title', 'units', 'frequency', 'seasonal_adjustment',
                                            'realtime_start', 'realtime_end', 'last_updated', 'observation_start',
                                            'observation_end', 'popularity', 'group_popularity', 'series_count',
                                            'created', 'name', 'release_id', 'press_release', 'group_id',
                                            'search_rank', 'title'},
        'error_message': "order_by must be one of the valid options"
    },
    'filter_variable':
    {
        'type_condition': lambda x: isinstance(x, str), 
        'value_condition': lambda x: x in {'frequency', 'units', 'seasonal_adjustment'},
        'error_message': "filter_variable must be one of the valid options: 'frequency', 'units', 'seasonal_adjustment'"
    },
    'filter_value': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: len(x) > 0,
        'error_message': "filter_value must be a non-empty string"
    },
    'tag_names': 
    {
        'type_condition': lambda x: isinstance(x, str), 
        'value_condition': __Validators.__liststring_validation,
        'async_value_condition': __AsyncValidators.__liststring_validation,
        'error_message': "tag_names must be a valid semicolon-separated string"
    },
    'exclude_tag_names': 
    {
        'type_condition': lambda x: isinstance(x, str), 
        'value_condition':__Validators.__liststring_validation,
        'async_value_condition': __AsyncValidators.__liststring_validation,
        'error_message': "exclude_tag_names must be a valid semicolon-separated string"
    },
    'tag_group_id': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'complex_condition': lambda x: isinstance(x, int) and x >= 0,
        'error_message': "tag_group_id must be a non-negative integer or a valid string"
    },
    'search_text': 
    {
        'type_condition': lambda x: isinstance(x, str),
    },
    'file_type': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x == 'json',
        'error_message': "file_type must be 'json'"
    },
    'api_key': 
    {
        'type_condition': lambda x: isinstance(x, str)
    },
    'include_releases_dates_with_no_data': 
    {
        'type_condition': lambda x: isinstance(x, bool)
    },
    'release_id': 
    {
        'type_condition': lambda x: isinstance(x, int),
        'value_condition': lambda x: x >= 0,
        'error_message': "release_id must be a non-negative integer"
    },
    'series_id': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: len(x) > 0 and ' ' not in x and x.isalnum(),
        'error_message': "series_id must be a non-empty alphanumeric string without spaces"
    },
    'frequency': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'d', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'},
        'error_message': "frequency must be one of the valid options: 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'"
    },
    'units': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'},
        'error_message': "units must be one of the valid options: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'"
    },
    'aggregation_method': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'sum', 'avg', 'eop'},
        'error_message': "aggregation_method must be one of the valid options: 'avg', 'sum', 'end_of_period', 'max', 'min'"
    },
    'output_type': 
    {
        'type_condition': lambda x: isinstance(x, int),
        'value_condition': lambda x: x in {1,2,3,4},
        'error_message': "output_type must be one of the valid options: 1, 2, 3, 4"
    },
    'vintage_dates': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': __Validators.__vintage_dates_validation,
        'async_value_condition': __AsyncValidators.__vintage_dates_validation,
        'error_message': "vintage_dates must be a valid semicolon-separated string"
    },
    'search_type': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'full_text', 'series_id'},
        'error_message': "search_type must be one of the valid options: 'full_text', 'series_id'"
    },
    'tag_search_text':
    {
        'type_condition': lambda x: isinstance(x, str),
        'error_message': "tag_search_text must be a string"
    },
    'start_time':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': __Validators.__hh_mm_datestring_validation,
        'async_value_condition': __AsyncValidators.__hh_mm_datestring_validation,
        'error_message': "start_time must be a valid time string in 'HH:MM' format"
    },
    'end_time':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': __Validators.__hh_mm_datestring_validation,
        'async_value_condition': __AsyncValidators.__hh_mm_datestring_validation,
        'error_message': "end_time must be a valid time string in 'HH:MM' format"
    },
    'season':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'seasonally_adjusted', 'not_seasonally_adjusted'},
        'error_message': "season must be one of the valid options: 'seasonally_adjusted', 'not_seasonally_adjusted'"
    }
}

GEOFRED_PARAMETERS_MAP = {
    'api_key': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'error_message': "api_key must be a string"
    },
    'file_type': 
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x == 'json',
        'error_message': "file_type must be one of the valid options: 'geojson', 'shp', 'kml', 'gdb', 'gpkg'"
    },
    'shape':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision'},
        'error_message': "shape must be one of the valid options: 'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision'"
    },
    'series_id':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: len(x) > 0 and ' ' not in x and x.isalnum(),
        'error_message': "series_id must be a non-empty alphanumeric string without spaces"
    },
    'date':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': __Validators.__datestring_validation,
        'async_value_condition': __AsyncValidators.__datestring_validation,
        'error_message': "date must be a valid date string in 'YYYY-MM-DD' format"
    },
    'start_date':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': __Validators.__datestring_validation,
        'async_value_condition': __AsyncValidators.__datestring_validation,
        'error_message': "start_date must be a valid date string in 'YYYY-MM-DD' format"
    },
    'series_group':
    {
        'type_condition': lambda x: isinstance(x, str),
        'error_message': "series_group must be a string"
    },
    'region_type':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision'},
        'error_message': "region_type must be one of the valid options: 'bea', 'msa', 'frb', 'necta', 'state', 'country', 'county', 'censusregion', 'censusdivision'"
    },
    'aggregation_method':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'sum', 'avg', 'eop'},
        'error_message': "aggregation_method must be one of the valid options: 'avg', 'sum', 'end_of_period', 'max', 'min'"
    },
    'units':
    {
        'type_condition': lambda x: isinstance(x, str),
        'error_message': "units must be a valid string"
    },
    'season':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'NSA', 'SA', 'SSA', 'SAAR', 'NSAAR'},
        'error_message': "season must be one of the valid options: 'NSA', 'SA', 'SSA', 'SAAR', 'NSAAR'"
    },
    'transformation':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'},
        'error_message': "transformation must be one of the valid options: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'"
    }
}

FRASER_PARAMETERS_MAP = {
    'limit':
    {
        'type_condition': lambda x: isinstance(x, int),
        'value_condition': lambda x: x >= 0,
        'error_message': "limit must be a non-negative integer"
    },
    'page':
    {
        'type_condition': lambda x: isinstance(x, int),
        'value_condition': lambda x: x >= 0,
        'error_message': "page must be a non-negative integer"
    },
    'format':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x == 'json',
        'error_message': "format must be 'json'"
    },
    'role':
    {
        'type_condition': lambda x: isinstance(x, str),
        'value_condition': lambda x: x in {'creator', 'contributor', 'editor', 'repository', 'uncertain', 'subject'},
        'error_message': "role must be one of the valid options: 'creator', 'contributor', 'editor', 'repository', 'uncertain', 'subject'"
    },
}

FREQUENCIES_MAP = {
    'D': 'D',
    'M': 'M',
    'Q': 'Q',
    'W': 'W',
    'A': 'Y',
    'WEF': 'W-FRI',
    'WETH': 'W-THU',
    'WEW': 'W-WED',
    'WETU': 'W-TUE',
    'WEM': 'W-MON',
    'WESU': 'W-SUN',
    'WESA': 'W-SAT',
    'BW': '2W',
    'BWEW': '2W-WED',
    'BWEM': '2W-MON',
    'SA': '2Q',
}