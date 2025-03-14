Data Visualization Examples
===========================

This section provides examples of how to visualize economic data fetched using the `fedfred` library. These examples demonstrate how to use popular Python libraries like Matplotlib, Seaborn, and GeoPandas for creating insightful visualizations.

Line Plot of Time Series Data
-----------------------------

This example demonstrates how to create a simple line plot of time series data using Matplotlib.

.. code-block:: python

    import matplotlib.pyplot as plt
    import fedfred as fd

    # Fetch data for a specific economic indicator
    fred = fd.FredAPI(api_key="your_api_key_here")
    series_id = "GDP"  # Example series ID
    data = fred.get_series_observations(series_id)

    # Create a visualization
    plt.figure(figsize=(10, 6))
    plt.plot(data.index, data.values, 'b-', linewidth=2)

    # Add labels and title
    plt.title(f"{series_id} Time Series Data", fontsize=14)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Value", fontsize=12)
    plt.grid(True, alpha=0.3)

    # Format the plot
    plt.tight_layout()
    plt.xticks(rotation=45)

    # Show the plot
    plt.show()

Bar Plot of Category Data
-------------------------

This example demonstrates how to create a bar plot to visualize data for multiple categories.

.. code-block:: python

    import matplotlib.pyplot as plt
    import fedfred as fd

    # Fetch data for a specific category
    fred = fd.FredAPI(api_key="your_api_key_here")
    category_id = 125  # Example category ID
    series = fred.get_category_series(category_id)

    # Extract series names and values
    series_names = [s.title for s in series]
    series_values = [s.popularity for s in series]

    # Create a bar plot
    plt.figure(figsize=(12, 6))
    plt.bar(series_names, series_values, color='skyblue')

    # Add labels and title
    plt.title("Category Series Popularity", fontsize=14)
    plt.xlabel("Series", fontsize=12)
    plt.ylabel("Popularity", fontsize=12)
    plt.xticks(rotation=45, ha='right')

    # Format the plot
    plt.tight_layout()

    # Show the plot
    plt.show()

Heatmap of Correlations
-----------------------

This example demonstrates how to create a heatmap of correlations between multiple time series using Seaborn.

.. code-block:: python

    import seaborn as sns
    import pandas as pd
    import fedfred as fd

    # Fetch data for multiple series
    fred = fd.FredAPI(api_key="your_api_key_here")
    series_ids = ["GDP", "UNRATE", "CPIAUCSL"]  # Example series IDs
    data_frames = [fred.get_series_observations(series_id) for series_id in series_ids]

    # Combine data into a single DataFrame
    combined_data = pd.concat(data_frames, axis=1)
    combined_data.columns = series_ids

    # Compute correlations
    correlations = combined_data.corr()

    # Create a heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(correlations, annot=True, cmap="coolwarm", fmt=".2f")

    # Add title
    plt.title("Correlation Heatmap of Economic Indicators", fontsize=14)

    # Show the plot
    plt.show()

Geographic Visualization with GeoPandas
---------------------------------------

This example demonstrates how to visualize geographic data using GeoPandas.

.. code-block:: python

    import geopandas as gpd
    import fedfred as fd

    # Fetch geographic data for unemployment rates by state
    fred_maps = fd.FredMapsAPI(api_key="your_api_key_here")
    unemployment_by_state = fred_maps.get_regional_data(
        series_group="unemployment",
        region_type="state",
        date="2023-01-01",
        season="nsa",  # Not seasonally adjusted
        units="percent"
    )

    # Plot the data
    unemployment_by_state.plot(
        column="value",
        cmap="OrRd",
        legend=True,
        figsize=(12, 8),
        edgecolor="black"
    )

    # Add title
    plt.title("Unemployment Rates by State (January 2023)", fontsize=14)

    # Show the plot
    plt.show()
