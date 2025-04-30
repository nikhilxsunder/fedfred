.. _faq:

Frequently Asked Questions (FAQ)
================================

Here are answers to common questions about **FedFred**, the modern Python client for the **FRED® API**.

---

What is FedFred?
----------------

.. dropdown:: See Answer
    :color: secondary

    FedFred is a **feature-rich Python client** for the **St. Louis Federal Reserve Economic Database (FRED®)**.

    Highlights:

    - **Synchronous** and **asynchronous** access to FRED datasets,
    - Native support for :term:`DataFrame` formats: Pandas, Polars, and Dask,
    - Built-in caching, retry handling, and structured typed object models.

    ➔ See the :ref:`quickstart` for a simple example.

---

How is FedFred different from ``fredapi`` and other FRED clients?
-----------------------------------------------------------------

.. dropdown:: See Answer
    :color: secondary

    FedFred improves upon traditional FRED libraries like ``fredapi`` by offering:

    - **Asynchronous Support**: Concurrently fetch thousands of series via :class:`fedfred.clients.FredAPI.AsyncAPI`.
    - **Built-in Rate Limiting**: Automatic compliance with FRED’s 120 requests/minute rule.
    - **Configurable Local Caching**: Rapid repeated queries via FIFO cache.
    - **Structured Objects**: Typed Python models like :class:`fedfred.objects.Series` and :class:`fedfred.objects.Release`.
    - **Flexible Backends**: Support for Polars and Dask :term:`DataFrame` outputs.

    ➔ See the full library comparison in :ref:`comparison`.

---

Does FedFred support GeoFRED (Maps API) data?
---------------------------------------------

.. dropdown:: See Answer
    :color: secondary

    Yes! FedFred includes robust support for geographic datasets via:

    - :class:`fedfred.clients.FredAPI.MapsAPI` for synchronous access,
    - :class:`fedfred.clients.FredAPI.AsyncAPI.AsyncMapsAPI` for asynchronous access.

    You can retrieve:

    - Regional economic indicators,
    - Shapefiles for states, counties, metro areas,
    - Output ready for GIS tools as :term:`GeoDataFrame`.

    ➔ Explore regional analysis examples in :ref:`use-cases`.

---

Is caching supported in FedFred?
--------------------------------

.. dropdown:: See Answer
    :color: secondary

    Yes! FedFred supports **local FIFO caching** natively.

    - Stores recent API responses (default 256 items),
    - Fully async-aware: works seamlessly across sync and async clients.

    Example usage:

    .. code-block:: python

        import fedfred as fd

        fred = fd.FredAPI(api_key="your_api_key_here", cache_mode=True, cache_size=1000)

    ➔ Learn more in the :ref:`advanced-usage` section.

---

Related Topics
--------------

.. grid::
    :gutter: 2

    .. grid-item-card:: Quick Start Guide
        :link: quickstart
        :link-type: ref
        :link-alt: FedFred Quickstart Guide

        Set up and fetch your first time series with FedFred.

    .. grid-item-card:: Full API Documentation
        :link: api-index
        :link-type: ref
        :link-alt: FedFred Full API Reference

        Explore all available methods, objects, and modules.

    .. grid-item-card:: Example Projects
        :link: use-cases
        :link-type: ref
        :link-alt: FedFred Example Applications

        See real-world dashboard, GIS, and async pipeline use cases.

    .. grid-item-card:: Architecture Overview
        :link: architecture
        :link-type: ref
        :link-alt: FedFred Architecture

        Understand the internal structure powering FedFred's API client.