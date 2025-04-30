.. _api-overview:

FedFred API Overview
=====================

FedFred provides a **modular, structured client interface** for interacting with the **FRED® API**, supporting both **synchronous** and **asynchronous** access.

This page summarizes the main client classes, their features, and how they relate to FRED data categories.

---

Client Architecture
-------------------

.. dropdown:: Expand Client Class Hierarchy
    :color: secondary

    - :class:`fedfred.clients.FredAPI`: Synchronous core client

      - :class:`fedfred.clients.FredAPI.AsyncAPI`: Asynchronous core client
        - :class:`fedfred.clients.FredAPI.AsyncAPI.AsyncMapsAPI`: Asynchronous GeoFRED client

      - :class:`fedfred.clients.FredAPI.MapsAPI`: Synchronous GeoFRED client

    Each class is accessed as an attribute:
    
    - ``FredAPI.Async`` → async core
    - ``FredAPI.Maps`` → sync Maps API
    - ``FredAPI.Async.Maps`` → async Maps API

---

Client Capabilities
-------------------

.. grid::
    :gutter: 2

    .. grid-item-card:: Category Access
        Retrieve parent/child metadata trees for all FRED categories.
        Useful for hierarchy navigation and dataset discovery.

    .. grid-item-card:: Series Metadata + Observations
        Fetch time series data and associated metadata (titles, units, frequency, vintages).

    .. grid-item-card:: Releases
        Access scheduled FRED economic data releases including descriptions, dates, and series.

    .. grid-item-card:: Tags + Search
        Use keyword/tag search to discover new indicators programmatically.

    .. grid-item-card:: Vintage Series Support
        Retrieve historical vintages to build forecasting models or study revisions.

    .. grid-item-card:: Regional Data (GeoFRED)
        Use :class:`MapsAPI` and :class:`AsyncMapsAPI` to access state/county-level economic indicators.

---

Enhanced API Features
---------------------

.. grid::
    :gutter: 2

    .. grid-item-card:: Local Caching
        FIFO cache stores recent results in memory.
        Configurable via ``cache_mode`` and ``cache_size``.

    .. grid-item-card:: Retry Logic
        Failed requests automatically retried with exponential backoff (powered by `tenacity`).

    .. grid-item-card:: Rate Limiting
        Enforces FRED's 120 requests/minute rule with a timestamp deque.

    .. grid-item-card:: DataFrame Outputs
        Returns data as:

        - :mod:`pandas` (default)
        - :mod:`polars`
        - :mod:`dask`
        - :mod:`geopandas`
        - :mod:`polars_st` / :mod:`dask_geopandas`

        Fully typed and datetime-aware.

    .. grid-item-card:: Structured Models
        API results parsed into rich typed objects like:

        - :class:`fedfred.objects.Series`
        - :class:`fedfred.objects.Release`
        - :class:`fedfred.objects.Category`
        - :class:`fedfred.objects.Tag`

---

Related Topics
--------------

.. grid::
    :gutter: 2

    .. grid-item-card:: Full API Reference
        :link: api-index
        :link-type: ref
        :link-alt: API Index

        Comprehensive reference for all classes and methods.

    .. grid-item-card:: Quick Start Guide
        :link: quickstart
        :link-type: ref
        :link-alt: Quickstart Tutorial

        Start fetching data with only a few lines of code.

    .. grid-item-card:: Async & Caching Examples
        :link: advanced-usage
        :link-type: ref
        :link-alt: Async and Advanced Features

        Learn about concurrent requests, caching, retries, and customization.

    .. grid-item-card:: Data Visualization Examples
        :link: data-visualization
        :link-type: ref
        :link-alt: Visualization

        Build charts and maps from FRED and GeoFRED datasets.