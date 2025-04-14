Advanced Usage Examples
=======================

This section provides advanced usage examples for the `fedfred` library, including caching, rate limiting, concurrent requests, and working with geographic data.

Caching and Rate Limiting
-------------------------

The `fedfred` library includes built-in support for caching and rate limiting to optimize API usage.

.. code-block:: python

    import fedfred as fd

    # Initialize the API client with caching enabled
    fred = fd.FredAPI(api_key="your_api_key_here", cache_mode=True)

    # Fetch a time series (cached locally for faster subsequent access)
    data = fred.get_series_observations("GDPC1")
    print(data.head())

    # The built-in rate limiter ensures you don't exceed 120 API calls per minute
    for series_id in ["UNRATE", "CPIAUCSL", "DGS10"]:
        data = fred.get_series_observations(series_id)
        print(f"Fetched data for {series_id}")

Concurrent Requests with AsyncAPI
---------------------------------

You can use the `AsyncAPI` to make concurrent requests for improved performance.

.. code-block:: python

    import asyncio
    import fedfred as fd

    async def fetch_multiple_series():
        fred = fd.FredAPI(api_key="your_api_key_here").Async

        # Fetch multiple series concurrently
        tasks = [
            fred.get_series_observations("UNRATE"),
            fred.get_series_observations("CPIAUCSL"),
            fred.get_series_observations("DGS10")
        ]
        results = await asyncio.gather(*tasks)

        # Process the results
        for series, series_id in zip(results, ["UNRATE", "CPIAUCSL", "DGS10"]):
            print(f"Data for {series_id}:")
            print(series.head())

    asyncio.run(fetch_multiple_series())

Working with Geographic Data
----------------------------

The `FredMapsAPI` allows you to fetch and analyze geographic data, such as unemployment rates by state.

.. code-block:: python

    import fedfred as fd

    # Initialize the FredMapsAPI client
    fred_maps = fd.MapsAPI(api_key="your_api_key_here")

    # Fetch regional data for unemployment rates by state
    unemployment_by_state = fred_maps.get_regional_data(
        series_group="unemployment",
        region_type="state",
        date="2023-01-01",
        season="nsa",  # Not seasonally adjusted
        units="percent"
    )

    # The result is a GeoPandas GeoDataFrame
    print(unemployment_by_state)

Customizing API Requests
------------------------

You can customize API requests by passing additional parameters to methods.

.. code-block:: python

    import fedfred as fd

    # Initialize the API client
    fred = fd.FredAPI(api_key="your_api_key_here")

    # Fetch data with custom parameters
    data = fred.get_series_observations(
        series_id="GDPC1",
        observation_start="2000-01-01",
        observation_end="2020-01-01",
        units="chg",  # Change from the previous value
        frequency="q",  # Quarterly data
        sort_order="asc"
    )
    print(data.head())

Exploring Categories and Tags
-----------------------------

You can explore categories and tags to discover related data series.

.. code-block:: python

    import fedfred as fd

    # Initialize the API client
    fred = fd.FredAPI(api_key="your_api_key_here")

    # Get top-level categories
    categories = fred.get_category_children(category_id=0)
    for category in categories:
        print(f"Category: {category.name} (ID: {category.id})")

    # Get tags for a specific category
    tags = fred.get_category_tags(category_id=125)
    for tag in tags:
        print(f"Tag: {tag.name}")

Error Handling and Validation
-----------------------------

The `fedfred` library raises exceptions for invalid API requests or responses. You can handle these exceptions to improve the robustness of your application.

.. code-block:: python

    import fedfred as fd

    # Initialize the API client
    fred = fd.FredAPI(api_key="your_api_key_here")

    try:
        # Attempt to fetch data for an invalid series ID
        data = fred.get_series_observations("INVALID_SERIES_ID")
    except ValueError as e:
        print(f"Error: {e}")

    try:
        # Attempt to fetch data with invalid parameters
        data = fred.get_series_observations(series_id="GDPC1", observation_start="invalid_date")
    except ValueError as e:
        print(f"Error: {e}")
