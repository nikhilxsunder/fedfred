.. _basic-usage:

Basic Usage Examples
=====================

This page shows how to quickly start using the :mod:`fedfred` package to interact with the **FRED® API**.
You'll learn how to **initialize a client**, **fetch time series**, **retrieve metadata**, and **explore categories and tags**.

If you're new to FedFred, start here!

---

Getting Started
---------------

.. grid::
   :gutter: 2

   .. grid-item-card:: Initialize the Client

      .. code-block:: python

         import fedfred as fd

         fred = fd.FredAPI(api_key="your_api_key_here")

      Initialize with your **FRED API key**.
      See :ref:`advanced-usage` for async and caching options.

   .. grid-item-card:: Fetch Time Series Observations

      .. tab-set::

        .. tab-item:: Pandas

            .. code-block:: python

                import fedfred as fd
                fred = fd.FredAPI(api_key="your_api_key")
                data = fred.get_series_observations("GDP")

                # Pandas DataFrame
                print(data.head())

        .. tab-item:: Polars

            .. code-block:: python

                import fedfred as fd
                fred = fd.FredAPI(api_key="your_api_key", dataframe_method="polars")
                data = fred.get_series_observations("GDP")

                # Polars DataFrame
                print(data)

        .. tab-item:: Dask

            .. code-block:: python

                import fedfred as fd
                fred = fd.FredAPI(api_key="your_api_key", dataframe_method="dask")
                data = fred.get_series_observations("GDP")

                # Dask DataFrame
                print(data.head())

      Fetch historical observations for a series.
      Output is a :term:`DataFrame` (or Polars/Dask — see :ref:`api-overview`).

   .. grid-item-card:: Retrieve Series Metadata

      .. code-block:: python

         metadata = fred.get_series("GDP")
         print(metadata[0].title)
         print(metadata[0].frequency)
         print(metadata[0].units)

      Get structured metadata using :class:`fedfred.objects.Series`.

---

Exploring FRED® Data
--------------------

.. dropdown:: Explore Categories
   :color: secondary
   :open:

   FRED organizes economic data into a hierarchy of **categories**.

   .. code-block:: python

      categories = fred.get_category_children(category_id=0)
      for category in categories:
          print(f"Category: {category.name} (ID: {category.id})")

   Useful for browsing thematic economic data collections.

.. dropdown:: Retrieve Tags for a Series
   :color: secondary
   :open:

   Tags describe **concepts** (e.g., "inflation", "gdp", "employment").

   .. code-block:: python

      tags = fred.get_series_tags("GDP")
      for tag in tags:
          print(f"Tag: {tag.name}")

   Useful for semantic searching and exploration.

.. dropdown:: Find Related Series
   :color: secondary
   :open:

   Discover related tags using text-based series search.

   .. code-block:: python

      related_tags = fred.get_series_search_related_tags("mortgage rate", tag_names="frb")
      for tag in related_tags:
         print(f"Related Tag: {tag.name}")

   Great for exploratory **economic research** and **model-building**.

---

Related Resources
-----------------

.. grid::
   :gutter: 2

   .. grid-item-card:: Advanced Usage
      :link: advanced-usage
      :link-type: ref
      :link-alt: Advanced Usage Documentation

      Learn about async clients, caching, and error handling.

   .. grid-item-card:: Full API Reference
      :link: api-index
      :link-type: ref
      :link-alt: Complete FedFred API Reference

      Detailed API docs for all classes and methods.

   .. grid-item-card:: Parameter Handling Notes
      :link: api-notes
      :link-type: ref
      :link-alt: Automatic Parameter Conversion

      Understand how parameters are validated and transformed internally.

---
