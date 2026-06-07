.. _quickstart:

Quick Start Guide
=================

Get started with **FedFred**, a modern Python client for the **FRED® API**.
This guide shows you how to install, initialize, fetch time series data, handle async operations, and work with :term:`DataFrame` and geographic data.

---

Getting Started
---------------

First, obtain a free **FRED API key** from the official website:
`FRED API Key Request <https://fred.stlouisfed.org/docs/api/api_key.html>`_

Install FedFred using pip or conda (see :ref:`installation` for more options).

---

.. tab-set::

   .. tab-item:: Synchronous Usage

      .. code-block:: python

         import fedfred as fd

         fred = fd.FredAPI(api_key="your_api_key_here")

         # Fetch a time series
         data = fred.get_series_observations("GDPC1")
         print(data.head())

      Default output is a :term:`DataFrame` (Pandas).

   .. tab-item:: Asynchronous Usage

      .. code-block:: python

         import asyncio
         import fedfred as fd

         async def main():
             fred = fd.FredAPI(api_key="your_api_key_here").Async

             data = await fred.get_series_observations("GDPC1")
             print(data.head())

             # Concurrent fetch
             tasks = [
                 fred.get_series_observations("UNRATE"),
                 fred.get_series_observations("CPIAUCSL"),
                 fred.get_series_observations("DGS10"),
             ]
             results = await asyncio.gather(*tasks)

             for series in results:
                 print(series.head())

         asyncio.run(main())

      See :ref:`advanced-usage` for bulk concurrent requests.

---

Working with DataFrames
------------------------

FedFred supports multiple backends.

.. tab-set::

   .. tab-item:: Pandas (Default)

      .. code-block:: python

         data = fred.get_series_observations("GDPC1")

   .. tab-item:: Polars (High Performance)

      .. code-block:: python

         data = fred.get_series_observations("GDPC1", dataframe_method="polars")

   .. tab-item:: Dask (Parallelized)

      .. code-block:: python

         data = fred.get_series_observations("GDPC1", dataframe_method="dask")

You can also customize the request:

.. dropdown:: Customizing Queries
   :color: secondary

   .. code-block:: python

      inflation = fred.get_series_observations(
          series_id="CPIAUCSL",
          observation_start="2020-01-01",
          observation_end="2022-12-31",
          units="pc1",
          frequency="q",
          sort_order="asc"
      )

Learn more about optional backends in :ref:`installation`.

---

Exploring Metadata
------------------

Browse FRED's structured categories and tags.

.. grid::
    :gutter: 2

    .. grid-item-card:: Categories
        :link: api-index
        :link-type: ref
        :link-alt: API Reference

        .. code-block:: python

           categories = fred.get_category_children(category_id=0)

    .. grid-item-card:: Tags
        :link: api-index
        :link-type: ref
        :link-alt: API Reference

        .. code-block:: python

           gdp_tags = fred.get_series_tags("GDPC1")

---

Searching for Series
--------------------

FedFred simplifies search operations:

.. code-block:: python

    # Keyword Search
    results = fred.get_series_search("unemployment rate", limit=5)

    # Category Search
    results = fred.get_category_series(category_id=3)

    # Tag Search
    results = fred.get_tags_series(tag_names="inflation")

---

Caching and Rate Limiting
-------------------------

FedFred automatically respects **rate limits** (~120 calls/minute).
You can enable **local caching** to boost performance:

.. code-block:: python

    fred = fd.FredAPI(
        api_key="your_api_key_here",
        cache_mode=True,
        cache_size=1000
    )

See details in :ref:`advanced-usage`.

---

Geographic Data (MapsAPI)
-------------------------

Access **regional economic indicators** easily.

.. code-block:: python

    fred_maps = fd.FredAPI(api_key="your_api_key_here").Maps

    unemployment_by_state = fred_maps.get_regional_data(
        series_group="882",
        region_type="state",
        date="2013-01-01",
        season="NSA",
        units="Dollars",
        frequency="a"
    )

Result is a :term:`GeoDataFrame` ready for plotting.
See :ref:`data-visualization` for mapping examples.

---

Fetching Common Economic Indicators
------------------------------------

Quick examples:

.. code-block:: python

    gdp = fred.get_series_observations("GDPC1")
    unemployment = fred.get_series_observations("UNRATE")
    inflation = fred.get_series_observations("CPIAUCSL")
    fed_funds = fred.get_series_observations("DFF")
    treasury_10y = fred.get_series_observations("DGS10")

Perfect for dashboards and models.

---

What's Next?
^^^^^^^^^^^^

.. grid::
    :gutter: 2

    .. grid-item-card:: Full API Reference
        :link: api-index
        :link-type: ref
        :link-alt: API Index

        Explore every available method and object.

    .. grid-item-card:: Advanced Usage
        :link: advanced-usage
        :link-type: ref
        :link-alt: Advanced Usage Examples

        Learn about async, caching, custom queries, error handling.

    .. grid-item-card:: Data Visualization
        :link: data-visualization
        :link-type: ref
        :link-alt: Data Visualization Examples

        Build charts, plots, and heatmaps from FRED data.

    .. grid-item-card:: Parameter Handling Notes
        :link: api-notes
        :link-type: ref
        :link-alt: Parameter Conversion and Validation Notes

        Understand how FedFred transforms and validates your parameters.
