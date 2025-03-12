Data Visualization Examples
===========================

Example 1
---------

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
