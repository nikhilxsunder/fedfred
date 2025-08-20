.. _advanced-usage:

Advanced Usage Examples
=======================

FedFred enables **high-performance**, **resilient** FRED® data pipelines.
This page covers **caching**, **rate limiting**, **async concurrent requests**, **geo-data access**, **custom queries**, and **error handling**.

---

Advanced Client Features
-------------------------

.. grid::
    :gutter: 2

    .. grid-item-card:: Caching and Rate Limiting
        :columns: 4
        :link: #caching-and-rate-limiting
        :link-alt: Caching and rate limiting documentation

        Automatically cache responses and throttle API requests to optimize performance.

    .. grid-item-card:: Async Concurrent Requests
        :columns: 4
        :link: #concurrent-requests-with-asyncapi
        :link-alt: Asynchronous requests using AsyncAPI

        Fetch multiple series in parallel with **AsyncAPI** to greatly improve speed.

    .. grid-item-card:: Geographic Data Access
        :columns: 4
        :link: #working-with-geographic-data
        :link-alt: Geographic data handling

        Retrieve regional economic data as **GeoDataFrames** using **MapsAPI**.

    .. grid-item-card:: Custom API Queries
        :columns: 4
        :link: #customizing-api-requests
        :link-alt: Customizing API queries

        Control frequency, date range, aggregation, and sorting easily.

    .. grid-item-card:: Browsing Categories and Tags
        :columns: 4
        :link: #exploring-categories-and-tags
        :link-alt: FRED hierarchy exploration

        Navigate the FRED database using categories and metadata tags.

    .. grid-item-card:: Error Handling
        :columns: 4
        :link: #error-handling-and-validation
        :link-alt: Handling errors and validation failures

        Handle API errors gracefully with automatic validation.

---

Caching and Rate Limiting
-------------------------

.. dropdown:: See Example
    :color: primary
    :open:

    .. code-block:: python

        import fedfred as fd

        fred = fd.FredAPI(api_key="your_api_key_here", cache_mode=True)

        data = fred.get_series_observations("GDPC1")
        print(data.head())

        for series_id in ["UNRATE", "CPIAUCSL", "DGS10"]:
            data = fred.get_series_observations(series_id)
            print(f"Fetched data for {series_id}")

FedFred **automatically** enforces FRED's 120 calls/minute API limit.

---

Concurrent Requests with AsyncAPI
---------------------------------

.. dropdown:: See Example
    :color: primary

    .. code-block:: python

        import asyncio
        import fedfred as fd

        async def fetch_multiple_series():
            fred = fd.FredAPI(api_key="your_api_key_here").Async

            tasks = [
                fred.get_series_observations("UNRATE"),
                fred.get_series_observations("CPIAUCSL"),
                fred.get_series_observations("DGS10")
            ]
            results = await asyncio.gather(*tasks)

            for series, series_id in zip(results, ["UNRATE", "CPIAUCSL", "DGS10"]):
                print(f"Data for {series_id}:")
                print(series.head())

        asyncio.run(fetch_multiple_series())

**AsyncAPI** dramatically improves throughput for bulk data retrieval.

---

Working with Geographic Data
-----------------------------

FedFred supports **GeoPandas**, **Polars-ST**, and **Dask-GeoPandas** for geographic outputs.

.. dropdown:: See Examples
    :color: secondary
    :open:

    .. tab-set::

       .. tab-item:: GeoPandas (Default)

          .. code-block:: python

             import fedfred as fd

             fred_maps = fd.FredAPI(api_key="your_api_key_here").Maps

             unemployment_by_state = fred_maps.get_regional_data(
                 series_group="882",
                 region_type="state",
                 date="2013-01-01",
                 season="NSA",
                 units="Dollars",
                 frequency="a",
                 geodataframe_method="geopandas"  # Default
             )

             print(unemployment_by_state)

       .. tab-item:: Polars-ST (Faster)

          .. code-block:: python

             import fedfred as fd

             fred_maps = fd.FredAPI(api_key="your_api_key_here").Maps

             unemployment_by_state = fred_maps.get_regional_data(
                 series_group="882",
                 region_type="state",
                 date="2013-01-01",
                 season="NSA",
                 units="Dollars",
                 frequency="a",
                 geodataframe_method="polars"  # Use Polars-ST
             )

             print(unemployment_by_state)

       .. tab-item:: Dask-GeoPandas (Parallel)

          .. code-block:: python

             import fedfred as fd

             fred_maps = fd.FredAPI(api_key="your_api_key_here").Maps

             unemployment_by_state = fred_maps.get_regional_data(
                 series_group="882",
                 region_type="state",
                 date="2013-01-01",
                 season="NSA",
                 units="Dollars",
                 frequency="a",
                 geodataframe_method="dask"  # Use Dask-GeoPandas
             )

             print(unemployment_by_state)

Regional economic data is always returned as a **GeoDataFrame-compatible** object, ready for mapping, GIS, or dashboard visualization.

---

Customizing API Requests
-------------------------

.. dropdown:: See Example
    :color: secondary

    .. code-block:: python

        import fedfred as fd

        fred = fd.FredAPI(api_key="your_api_key_here")

        data = fred.get_series_observations(
            series_id="GDPC1",
            observation_start="2000-01-01",
            observation_end="2020-01-01",
            units="chg",
            frequency="q",
            sort_order="asc"
        )
        print(data.head())

Easily control **time ranges**, **frequencies**, and **unit transformations**.

---

Exploring Categories and Tags
------------------------------

.. dropdown:: See Example
    :color: info

    .. code-block:: python

        import fedfred as fd

        fred = fd.FredAPI(api_key="your_api_key_here")

        categories = fred.get_category_children(category_id=0)
        for category in categories:
            print(f"Category: {category.name} (ID: {category.id})")

        tags = fred.get_category_tags(category_id=125)
        for tag in tags:
            print(f"Tag: {tag.name}")

Explore the **hierarchical FRED structure** and discover datasets by topic.

---

Error Handling and Validation
------------------------------

.. dropdown:: See Example
    :color: danger

    .. code-block:: python

        import fedfred as fd
        from tenacity import RetryError

        fred = fd.FredAPI(api_key="your_api_key_here")

        try:
            data = fred.get_series_observations("INVALID_SERIES_ID")
        except RetryError as e:
            print(f"Error: {e}")

        try:
            data = fred.get_series_observations(series_id="GDPC1", observation_start="invalid_date")
        except RetryError as e:
            print(f"Error: {e}")

FedFred **validates parameters** and **raises descriptive errors** to help debug mistakes quickly.

---

Related Resources
-----------------

.. grid::
    :gutter: 2
    :margin: 2 0 2 0

    .. grid-item-card:: API Notes
        :link: api-notes
        :link-type: ref
        :link-alt: API behavior notes

        Learn how FedFred automatically handles parameter conversions and validation rules.

    .. grid-item-card:: API Reference
        :link: api-index
        :link-type: ref
        :link-alt: Full FedFred API documentation

        See detailed docs for every method, client, object model, and async variation.

    .. grid-item-card:: Use Cases
        :link: use-cases
        :link-type: ref
        :link-alt: Practical examples of FedFred in action

        Real-world examples: dashboards, financial modeling, risk analysis, and more.
