.. _architecture:

Internal Architecture
=====================

FedFred is designed to be **modular**, **extensible**, and **high-performance**, supporting both **synchronous** and **asynchronous** interaction with the **FRED® API**.

This page outlines the internal **class hierarchy**, **core mechanisms**, and **design principles** behind FedFred.

---

Class Hierarchy Overview
------------------------

.. dropdown:: Expand Class Hierarchy
    :color: secondary

    - :class:`fedfred.clients.FredAPI` (synchronous core client)
    
      - :class:`fedfred.clients.FredAPI.AsyncAPI` (asynchronous core client)
        - :class:`fedfred.clients.FredAPI.AsyncAPI.AsyncMapsAPI` (async Maps API client)
    
      - :class:`fedfred.clients.FredAPI.MapsAPI` (synchronous Maps API client)

    ➤ Nested clients are accessible via attributes like ``fred.Async``, ``fred.Maps``, and ``fred.Async.Maps``.

    See :ref:`api-overview` for a full breakdown.

---

Key Internal Mechanisms
------------------------

.. grid::
    :gutter: 2

    .. grid-item-card:: Rate Limiting
        :link-alt: FRED API Rate Limits

        Enforces the FRED 120 requests/min limit using a **timestamp deque**.  
        Automatically evicts old calls and blocks excess requests.

    .. grid-item-card:: Retry Strategy
        :link-alt: Retry on Failure

        Failed API calls (timeouts/network errors) retry using `tenacity`.  
        Uses exponential backoff with jitter to avoid hammering FRED.

    .. grid-item-card:: Local Caching
        :link-alt: Local FIFO Cache

        In-memory FIFO cache stores **256 entries** by default.  
        Works in sync and async clients. Toggle via ``cache_mode``.

    .. grid-item-card:: Asynchronous Engine
        :link-alt: Async Architecture

        Async clients use `httpx.AsyncClient` and `asyncio.Lock` for concurrency-safe access and rate compliance.  
        Suitable for high-throughput pipelines.

    .. grid-item-card:: Structured Objects
        :link-alt: Typed Response Models

        API responses are parsed into Python classes like:

        - :class:`fedfred.objects.Series`
        - :class:`fedfred.objects.Release`
        - :class:`fedfred.objects.Category`
        - :class:`fedfred.objects.Tag`

        Enables static type checking, autocompletion, and safer usage.

    .. grid-item-card:: DataFrame Output
        :link-alt: Multi-Backend Support

        Supports flexible backend switching via ``dataframe_method``:

        - Pandas (:term:`DataFrame`)
        - Polars (faster)
        - Dask (parallel)
        - GeoPandas (:term:`GeoDataFrame`)

        Ideal for data science, GIS, and big data use cases.

---

Design Philosophy
-----------------

.. dropdown:: Principles Behind the Package
    :color: primary

    - **Ease of Use**: Minimal boilerplate, clear method names, simple init.
    - **Performance**: Async support, FIFO caching, adaptive retries.
    - **Flexibility**: Sync + Async, backend switching, local rate enforcement.
    - **Reliability**: Typed models, parameter validation, safe defaults.

---

Related Topics
--------------

.. grid::
    :gutter: 2

    .. grid-item-card:: Full API Reference
        :link: api-index
        :link-type: ref
        :link-alt: API Index

        All classes, methods, parameters, and return types.

    .. grid-item-card:: Quick Start Guide
        :link: quickstart
        :link-type: ref
        :link-alt: Quickstart

        How to install, fetch data, and use async/sync clients.

    .. grid-item-card:: Advanced Usage
        :link: advanced-usage
        :link-type: ref
        :link-alt: Async, caching, query control

        Includes caching, rate limiting, retries, and async pipelines.

    .. grid-item-card:: API Client Hierarchy
        :link: api-overview
        :link-type: ref
        :link-alt: API Architecture

        Understand how FredAPI, MapsAPI, and AsyncAPI interconnect.