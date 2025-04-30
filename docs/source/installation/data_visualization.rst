.. _data-visualization:

Data Visualization Examples
============================

This page shows how to **visualize economic data retrieved with FedFred** using popular Python libraries like **Matplotlib**, **Seaborn**, and **GeoPandas**.  
FedFred integrates seamlessly with visualization tools, enabling clear insights from FRED® data.

---

.. grid::
    :gutter: 2

    .. grid-item-card:: Line Plot with Matplotlib

        Plot a basic time series using :mod:`matplotlib.pyplot`.

        .. code-block:: python

            import matplotlib.pyplot as plt
            import fedfred as fd

            fred = fd.FredAPI(api_key="your_api_key_here")
            data = fred.get_series_observations("GDP")

            plt.figure(figsize=(10, 6))
            plt.plot(data.index, data.values, 'b-', linewidth=2)
            plt.title("GDP Time Series")
            plt.xlabel("Date")
            plt.ylabel("Value")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.xticks(rotation=45)
            plt.show()

    .. grid-item-card:: Bar Plot by Category

        Compare the popularity of series within a category.

        .. code-block:: python

            import matplotlib.pyplot as plt
            import fedfred as fd

            fred = fd.FredAPI(api_key="your_api_key_here")
            series = fred.get_category_series(category_id=125)

            names = [s.title for s in series]
            values = [s.popularity for s in series]

            plt.figure(figsize=(12, 6))
            plt.bar(names, values, color='skyblue')
            plt.title("Category Series Popularity")
            plt.xlabel("Series")
            plt.ylabel("Popularity")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show()

---

Advanced Visualizations
------------------------

.. grid::
    :gutter: 2

    .. grid-item-card:: Correlation Heatmap (Seaborn)

        Visualize correlations between key indicators like GDP, Unemployment, and Inflation.

        .. code-block:: python

            import seaborn as sns
            import matplotlib.pyplot as plt
            import pandas as pd
            import fedfred as fd

            fred = fd.FredAPI(api_key="your_api_key_here")
            ids = ["GDP", "UNRATE", "CPIAUCSL"]
            dfs = [fred.get_series_observations(sid) for sid in ids]

            df = pd.concat(dfs, axis=1)
            df.columns = ids

            corr = df.corr()

            plt.figure(figsize=(8, 6))
            sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
            plt.title("Correlation Heatmap of Economic Indicators")
            plt.show()

    .. grid-item-card:: Geographic Visualization (GeoPandas)

        Map unemployment rates by U.S. state using :mod:`geopandas`.

        .. code-block:: python

            import geopandas as gpd
            import fedfred as fd
            import matplotlib.pyplot as plt

            fred_maps = fd.FredAPI(api_key="your_api_key_here").Maps

            gdf = fred_maps.get_regional_data(
                series_group="unemployment",
                region_type="state",
                date="2023-01-01",
                season="nsa",
                units="percent"
            )

            gdf.plot(
                column="value",
                cmap="OrRd",
                legend=True,
                figsize=(12, 8),
                edgecolor="black"
            )

            plt.title("Unemployment Rates by State (January 2023)")
            plt.show()

---

Related Resources
-----------------

.. grid::
    :gutter: 2
    :margin: 2 0 2 0

    .. grid-item-card:: Basic Usage Guide
        :link: basic-usage
        :link-type: ref
        :link-alt: Getting started with FedFred

        Learn how to initialize the client, fetch series, metadata, categories, and tags.

    .. grid-item-card:: Advanced Usage
        :link: advanced-usage
        :link-type: ref
        :link-alt: Advanced features like caching, async, and error handling

        Dive deeper into async clients, local caching, error management, and custom parameters.

    .. grid-item-card:: Full API Reference
        :link: api-index
        :link-type: ref
        :link-alt: Full API reference documentation

        Browse all available clients, methods, data models, and async equivalents.

    .. grid-item-card:: Example Use Cases
        :link: use-cases
        :link-type: ref
        :link-alt: Real-world usage examples

        See practical examples including economic dashboards, forecasting, and visualizations.