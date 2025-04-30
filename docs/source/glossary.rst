.. _glossary:

Glossary
========

.. glossary::

    DataFrame
        A two-dimensional, size-mutable, and heterogeneous tabular data structure commonly used in data analysis and machine learning workflows. 
        Provided by libraries like :mod:`pandas`, :mod:`polars`, and :mod:`dask`. 
        See also: :term:`GeoDataFrame`.

    GeoDataFrame
        An extension of a :term:`DataFrame` for managing geospatial data with spatial operations.
        Available through libraries like :mod:`geopandas` and :mod:`dask_geopandas`. 
        Often used alongside :mod:`shapely` and :mod:`pyproj` for geospatial analysis.

    async
        Short for asynchronous programming in Python, enabling non-blocking execution of code using the ``asyncio`` event loop. 
        Critical for high-performance applications such as concurrent API data retrieval.

    caching
        Temporarily storing API responses locally to improve performance and reduce redundant network requests. 
        FedFred supports :term:`cache mode` to enhance API efficiency.

    vintage
        A snapshot of a time series dataset as published on a specific date, useful for real-time macroeconomic analysis and backtesting. 
        Related to vintage economic data revision studies.

    rate limiting
        A method of controlling the number of API requests over time to prevent exceeding service quotas. 
        Essential when interacting with the FRED® API to avoid request throttling.

    retry strategy
        Automatic re-attempting of failed API requests, typically due to transient network errors, using exponential backoff or fixed intervals. 
        Often implemented together with :term:`rate limiting` and :term:`caching`.

    ETL
        Extract, Transform, Load — a common workflow for data ingestion and preprocessing, especially in data pipelines and analytics projects. 
        Often involves working with :term:`DataFrame` and geospatial extensions like :term:`GeoDataFrame`.

    API key
        A unique credential provided by the St. Louis Fed to authenticate and authorize access to the FRED® API. 
        Required for making requests to endpoints covered in :mod:`fedfred.clients.FredAPI`.

    GeoFRED
        The geospatial visualization and mapping extension of the FRED database, offering regional economic data through choropleth maps.
        Related functionality is supported in :mod:`fedfred.clients.MapsAPI`.

    cache mode
        A configuration option in FedFred that enables local caching of API responses, improving retrieval speed and reducing reliance on repeated network calls.
        See also: :term:`caching`.