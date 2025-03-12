Basic Usage Examples
====================

Fetching a Single Series Observations
-------------------------------------

.. code-block:: python

    from fedfred.fedfred import FredAPI

    fred = FredAPI(api_key="your_api_key_here")

    # Get GDP data
    gdp = fred.get_series_observations("GDP")

    # Observations are already in a Pandas DataFrame
    print(gdp.head())

Working with Categories
-----------------------

.. code-block:: python

    # Get top-level categories
    categories = fred.get_category()

    # Get child categories for category ID 32991 (U.S. Economy)
    child_categories = fred.get_category(category_id=32991)

    for category in child_categories:
        print(f"{category.id}: {category.name}")
