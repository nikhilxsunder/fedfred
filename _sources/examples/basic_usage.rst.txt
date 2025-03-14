Basic Usage Examples
====================

This section provides basic examples of how to use the `fedfred` library to interact with the FRED API.

Initializing the API Client
---------------------------

To use the `fedfred` library, you first need to initialize the API client with your FRED API key.

.. code-block:: python

    import fedfred as fd

    # Initialize the API client
    fred = fd.FredAPI(api_key="your_api_key_here")

Fetching a Time Series
----------------------

You can fetch time series data for a specific economic indicator using the `get_series_observations` method.

.. code-block:: python

    # Fetch data for a specific economic indicator
    series_id = "GDP"  # Example series ID
    data = fred.get_series_observations(series_id)

    # Display the first few rows of the data
    print(data.head())

Fetching Metadata for a Series
------------------------------

You can fetch metadata for a specific series using the `get_series` method.

.. code-block:: python

    # Fetch metadata for a specific series
    series_id = "GDP"
    metadata = fred.get_series(series_id)

    # Display the metadata
    print(f"Title: {metadata.title}")
    print(f"Frequency: {metadata.frequency}")
    print(f"Units: {metadata.units}")

Exploring Categories
--------------------

You can explore categories to discover related data series.

.. code-block:: python

    # Get top-level categories
    categories = fred.get_category_children(category_id=0)

    # Display the categories
    for category in categories:
        print(f"Category: {category.name} (ID: {category.id})")

Fetching Tags for a Series
--------------------------

You can fetch tags associated with a specific series to better understand its context.

.. code-block:: python

    # Fetch tags for a specific series
    series_id = "GDP"
    tags = fred.get_series_tags(series_id)

    # Display the tags
    for tag in tags:
        print(f"Tag: {tag.name}")

Fetching Related Series
-----------------------

You can fetch related series for a specific series using the `get_series_search_related_tags` method.

.. code-block:: python

    # Fetch related series for a specific series
    series_id = "GDP"
    related_series = fred.get_series_search_related_tags(series_id)

    # Display the related series
    for series in related_series:
        print(f"Related Series: {series.title}")
