.. _use-cases:

Example Use Cases
=================

FedFred powers **economic dashboards**, **async data pipelines**, **regional economic analysis**, and **financial research** using the **FRED® API**.

Explore how you can integrate FedFred into your projects:

---

Economic Dashboard Development
-------------------------------

.. dropdown:: See Example
    :color: secondary
    :open:

    Build real-time economic dashboards by combining:

    - **Pandas** or **Polars** for fast data wrangling,
    - **Matplotlib**, **Seaborn**, or **Plotly** for visualizations,
    - **Dash**, **Streamlit**, or **Gradio** for deployment.

    Example applications:

    - Track GDP, CPI, Unemployment rates dynamically,
    - Visualize yield curve spreads,
    - Build sectoral dashboards (housing, labor, inflation).

    See visualization examples in :ref:`data-visualization`.

---

Asynchronous Data Pipelines
----------------------------

.. dropdown:: See Example
    :color: secondary

    Use :class:`fedfred.clients.FredAPI.AsyncAPI` to fetch **hundreds or thousands of series concurrently** with Python's :mod:`asyncio`.

    Ideal for:

    - High-throughput ETL pipelines,
    - Automated economic indicator collectors,
    - Research workflows for bulk data collection.

    Features like **built-in caching** and **resilient retrying** ensure reliability.

    See async examples in :ref:`advanced-usage`.

---

Regional Economic Analysis
---------------------------

.. dropdown:: See Example
    :color: secondary

    Analyze geographic economic data via:

    - :class:`fedfred.clients.FredAPI.MapsAPI` (sync),
    - :class:`fedfred.clients.FredAPI.AsyncAPI.AsyncMapsAPI` (async).

    Applications:

    - Map unemployment rates, housing prices, GDP by state,
    - Monitor regional economic performance,
    - Conduct spatial econometrics with :mod:`geopandas` or :mod:`pysal`.

    Output: native :term:`GeoDataFrame` ready for GIS analysis.

    See mapping examples in :ref:`data-visualization`.

---

Financial Research and Backtesting
-----------------------------------

.. dropdown:: See Example
    :color: secondary

    Use FedFred for **real-time historical data research**:

    - Fetch available **vintage dates**,
    - Retrieve series observations for specific vintages,
    - Analyze preliminary vs final release values.

    Example applications:

    - Build macroeconomic forecasting models using only real-time available data (no lookahead bias),
    - Create economic surprise indices for trading strategies.

---

Related Resources
-----------------

.. grid::
    :gutter: 2

    .. grid-item-card:: Full API Documentation
        :link: api-index
        :link-type: ref
        :link-alt: FedFred Full API Reference

        Browse all FedFred API methods, client classes, and structured data models.

    .. grid-item-card:: Quick Start Guide
        :link: quickstart
        :link-type: ref
        :link-alt: FedFred Quick Start

        Install, initialize, and start fetching FRED data in minutes.

    .. grid-item-card:: Parameter Handling Notes
        :link: api-notes
        :link-type: ref
        :link-alt: FedFred Parameter Handling

        Understand how FedFred automatically handles dates, lists, and type conversions.

    .. grid-item-card:: Visualization Examples
        :link: data-visualization
        :link-type: ref
        :link-alt: FedFred Visualization Guide

        Build charts, dashboards, and geographic maps from FRED datasets.