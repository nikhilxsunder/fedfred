Quick Start Guide
=================

Getting Started
---------------

First, obtain a FRED API key from `https://fred.stlouisfed.org/docs/api/api_key.html <https://fred.stlouisfed.org/docs/api/api_key.html>`_.

Basic Usage
-----------

.. code-block:: python

    import fedfred as fd

    # Initialize the API client
    fred = fd.FredAPI(api_key="your_api_key_here")

    # Fetch a time series
    data = fred.get_series_observations("GDPC1")

    # Convert to pandas DataFrame
    data.head()

Working with Data
-----------------

FedFred supports both pandas and polars DataFrames:

.. code-block:: python

    # Pandas DataFrame (default)
    gdp_pandas = fred.get_series_observations("GDPC1")

    # Polars DataFrame
    gdp_polars = fred.get_series_observations("GDPC1", dataframe_method="polars")

    # Customize your query
    inflation = fred.get_series_observations(
        "CPIAUCSL",
        observation_start="2020-01-01",
        observation_end="2022-12-31",
        units="pc1",  # Percent change from a year ago
        frequency="q"  # Quarterly frequency
    )

Other methods return objects structured by the internal data classes:

.. code-block:: python

    # Get category tags
    tags = fred.get_category_tags(category_id=125)

    # tags is a List[Tag] object
    for tag in tags:
        print(tag.name)

Searching for Series
--------------------

Find series by searching with keywords:

.. code-block:: python

    # Search for unemployment series
    unemployment_series = fred.get_series_search("unemployment rate", limit=5)

    # Get series by category
    category_series = fred.get_category_series(category_id=32991)  # GDP category

    # Find series by tag
    inflation_series = fred.get_tags_series(tag_names="inflation")

Categories and Tags
-------------------

Browse and explore the FRED data hierarchy:

.. code-block:: python

    # Get top-level categories
    categories = fred.get_category_children(category_id=0)

    # Get child categories for a specific category
    gdp_categories = fred.get_category_children(category_id=32991)  # GDP category

    # Get tags for a series
    gdp_tags = fred.get_series_tags("GDPC1")

Caching and Rate Limits
-----------------------

Enable caching to improve performance and manage API rate limits:

.. code-block:: python

    # Initialize client with caching enabled
    fred = fd.FredAPI(
        api_key="your_api_key_here",
        cache_mode=True
    )

    # The library automatically handles rate limiting, but caching helps
    # reduce the number of API calls for repeated queries

Geographic Data with FredMapsAPI
--------------------------------

Access geographic economic data using the FredMapsAPI:

.. code-block:: python

    # Initialize the maps API client
    fred_maps = fd.FredMapsAPI(api_key="your_api_key_here")

    # Get regional data
    unemployment_by_state = fred_maps.get_regional_data(
        series_group="unemployment",
        region_type="state",
        date="2023-01-01",
        season="nsa",  # Not seasonally adjusted
        units="percent"
    )

    # Response is already structured as a GeoDataFrame
    print(unemployment_by_state)

Common Economic Indicators
--------------------------

Quick access to key economic indicators:

.. code-block:: python

    # Real GDP (quarterly, seasonally adjusted)
    gdp = fred.get_series_observations("GDPC1")

    # Unemployment Rate (monthly, seasonally adjusted)
    unemployment = fred.get_series_observations("UNRATE")

    # Consumer Price Index (monthly, seasonally adjusted)
    cpi = fred.get_series_observations("CPIAUCSL")

    # Federal Funds Effective Rate (daily)
    fed_funds = fred.get_series_observations("DFF")

    # 10-Year Treasury Constant Maturity Rate (daily)
    treasury_10y = fred.get_series_observations("DGS10")
