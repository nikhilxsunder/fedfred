.. _comparison:

Comparison with Other FRED Clients
==================================

FedFred offers a **modern, feature-rich alternative** to existing Python clients for the **St. Louis FRED® API**.  
Below is a detailed comparison.

---

Feature Comparison Table
------------------------

+---------------------+-------------------------+---------+-----------+----------------+
| Feature             | fedfred                 | fredapi | pyfredapi | frb/fredbrain  |
+=====================+=========================+=========+===========+================+
| Async Support       | Yes                     | No      | Partial   | No             |
+---------------------+-------------------------+---------+-----------+----------------+
| Caching             | Yes (FIFO Cache)        | No      | No        | No             |
+---------------------+-------------------------+---------+-----------+----------------+
| Rate Limiting       | Yes (120 req/min)       | No      | No        | No             |
+---------------------+-------------------------+---------+-----------+----------------+
| Object Models       | Yes (Typed Classes)     | No      | No        | No             |
+---------------------+-------------------------+---------+-----------+----------------+
| Maps API Support    | Yes                     | No      | No        | No             |
+---------------------+-------------------------+---------+-----------+----------------+
| DataFrame Support   | Pandas, Polars, Dask    | Partial | Partial   | No             |
+---------------------+-------------------------+---------+-----------+----------------+
| License             | AGPL                    | MIT     | MIT       | Varies         |
+---------------------+-------------------------+---------+-----------+----------------+


---

Key Differences Explained
--------------------------

.. dropdown:: Why Async Support Matters
    :color: secondary

    FedFred enables **true concurrency** when downloading large batches of FRED data, dramatically improving speed.  
    Ideal for production pipelines, real-time apps, and bulk research.

.. dropdown:: Caching and Rate Limit Handling
    :color: secondary

    No need to manually throttle API calls or install external caches.  
    FedFred includes **intelligent caching** and **built-in 120 requests/minute throttling**.

.. dropdown:: Structured Objects vs Raw JSON
    :color: secondary

    Rather than returning nested dictionaries, FedFred parses responses into **typed Python classes** like :class:`fedfred.objects.Series`, ensuring autocompletion and static type checking.

.. dropdown:: GeoFRED and Regional Data Access
    :color: secondary

    FedFred uniquely supports regional economic data (state, metro, county) directly into :term:`GeoDataFrame`, perfect for mapping and GIS analysis.

.. dropdown:: Backend Flexibility
    :color: secondary

    You can output to **Pandas**, **Polars**, **Polars-ST**, or **Dask**, depending on your workflow's performance needs.

---

Summary
-------

FedFred is the **most complete** and **future-proof** choice if you are building:

- Economic Dashboards
- High-frequency Research Pipelines
- Geographic Data Applications
- Financial Forecasting Models

It combines modern Python practices (asyncio, typing, DataFrames) with the full breadth of FRED API capabilities.

➔ Check real-world examples in :ref:`use-cases`.  
➔ Explore client internals at :ref:`api-overview`.

---

Related Topics
--------------

.. grid::
    :gutter: 2

    .. grid-item-card:: Full API Documentation
        :link: api-index
        :link-type: ref
        :link-alt: API Index

        Explore every method, object, and client class.

    .. grid-item-card:: Quick Start Tutorial
        :link: quickstart
        :link-type: ref
        :link-alt: Quick Start Guide

        Learn how to fetch your first FRED dataset.

    .. grid-item-card:: Regional Datasets
        :link: data-visualization
        :link-type: ref
        :link-alt: Data Visualization

        Visualize regional economic trends using MapsAPI.