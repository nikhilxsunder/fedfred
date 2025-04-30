.. _resources-index:

Resources
=========

Explore advanced topics, comparisons, architecture insights, and usage guides for **FedFred**, a modern Python client for the **FRED® API**.

This section contains **essential resources** to help you **use FedFred effectively**, **compare it to alternatives**, and **understand its internal design**.

---

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Resources

   faq
   comparison
   use_cases
   api_overview
   architecture

---

Additional API Notes
--------------------

Some important notes about FedFred's internal behavior:

.. toctree::
   :maxdepth: 1

   notes

Topics include:
- Parameter auto-conversion (e.g., :class:`datetime.datetime`, :class:`list` handling),
- Nested class structure (:class:`fedfred.clients.FredAPI.AsyncAPI`, :class:`fedfred.clients.FredAPI.MapsAPI`, :class:`fedfred.clients.FredAPI.AsyncAPI.AsyncMapsAPI`),
- :term:`DataFrame` backend configuration options (Pandas, Polars, Dask).

For a high-level overview of how FedFred is structured internally, see :ref:`architecture`.

---

Related Topics
--------------

.. grid::
    :gutter: 2

    .. grid-item-card:: Full API Reference
        :link: api-index
        :link-type: ref
        :link-alt: API Method Documentation

        Explore detailed documentation for all FedFred methods, clients, and object models.

    .. grid-item-card:: Quick Start Guide
        :link: quickstart
        :link-type: ref
        :link-alt: Quick Start Guide

        Get started instantly with FedFred — install, configure, and fetch your first series.

    .. grid-item-card:: Installation and Setup
        :link: installation-usage
        :link-type: ref
        :link-alt: Installation and Configuration Guide

        Learn how to properly install FedFred using pip or conda, and configure it for your project.