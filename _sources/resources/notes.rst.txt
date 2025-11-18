.. _api-notes:

Special Notes: Added Helpers and Return Object Properties (FedFred 3.0+)
========================================================================

Starting from **version 3.0**, the :mod:`fedfred` library introduces **new helper methods** and **additional properties** in return objects.
These enhancements make it easier to interact with the **FRED® API** while ensuring full compatibility and clean code design.

This page details these important features.

---

New Helper Methods in FedFred
--------------------------------
The :mod:`fedfred.helpers` module now includes additional helper methods to facilitate data handling and conversion.

Added Helper Methods
^^^^^^^^^^^^^^^^^^^^

- :meth:`fedfred.helpers.FredHelpers.pd_frequency_conversion`: Converts fedfred native frequency strings to pandas compatible ones.
- :meth:`fedfred.helpers.FredHelpers.to_pd_series`: Converts a :class:`pd.DataFrame` into a :class:`pd.Series`.

Examples of New Helper Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Using** :meth:`fedfred.helpers.FredHelpers.pd_frequency_conversion` **to convert frequency strings**:

  .. code-block:: python

      from fedfred.helpers import FredHelpers

      freq_str = "BW" # FedFred frequency string for "Biweekly"
      pd_freq = FredHelpers.pd_frequency_conversion(freq_str)
      print(pd_freq)  # Output: '2W'

- **Using** :meth:`fedfred.helpers.FredHelpers.to_pd_series` **to convert DataFrame to Series**:

    .. code-block:: python

        from fedfred.helpers import FredHelpers
        import pandas as pd

        # Sample DataFrame
        df = pd.DataFrame({
            'date': ['2020-01-01', '2020-02-01', '2020-03-01'],
            'value': [100, 200, 300]
        }).set_index('date')

        series = FredHelpers.to_pd_series(df, "value")
        print(series)
        # Output:
        # date
        # 2020-01-01    100
        # 2020-02-01    200
        # 2020-03-01    300
        # Name: value, dtype: int64

---

Additional Properties in Return Objects
---------------------------------------

Several return objects in the :mod:`fedfred.objects` module have been enhanced with additional properties to provide more context and information.

Enhanced Return Object Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**New Properties**:

- :class:`fedfred.objects.Category`:
  - :attr:`fedfred.objects.Category.children` - List of child categories.
  - :attr:`fedfred.objects.Category.related` - List of related categories.
  - :attr:`fedfred.objects.Category.series` - List of series in the category.
  - :attr:`fedfred.objects.Category.tags` - List of tags associated with the category.
  - :attr:`fedfred.objects.Category.related_tags` - List of related tags.

- :class:`fedfred.objects.Series`:
  - :attr:`fedfred.objects.Series.categories` - List of categories for the series.
  - :attr:`fedfred.objects.Series.observations` - DataFrame of observations for the series.
  - :attr:`fedfred.objects.Series.release` - List of releases for the series.
  - :attr:`fedfred.objects.Series.tags` - List of tags for the series.
  - :attr:`fedfred.objects.Series.vintagedates` - List of vintage dates for the series.

- :class:`fedfred.objects.Tag`:
  - :attr:`fedfred.objects.Tag.related_tags` - List of related tags.
  - :attr:`fedfred.objects.Tag.series` - List of series associated with the tag.

- :class:`fedfred.objects.Release`:
  - :attr:`fedfred.objects.Release.dates` - List of release dates for the release.
  - :attr:`fedfred.objects.Release.series` - List of series associated with the release.
  - :attr:`fedfred.objects.Release.sources` - List of sources associated with the release.
  - :attr:`fedfred.objects.Release.tags` - List of tags associated with the release.
  - :attr:`fedfred.objects.Release.related_tags` - List of related tags for the release.
  - :attr:`fedfred.objects.Release.tables` - List of elements for the release.

- :class:`fedfred.objects.Source`:
  - :attr:`fedfred.objects.Source.releases` - List of releases for the source.

- :class:`fedfred.objects.Element`:
  - :attr:`fedfred.objects.Element.release` - List of releases for the element.
  - :attr:`fedfred.objects.Element.series` - List of series for the element.

---

Global API Key Configuration
----------------------------

To simplify API key management, FedFred now supports setting a **global API key** that will be used across all instances of :class:`fedfred.clients.FredAPI`.

Setting a Global API Key
^^^^^^^^^^^^^^^^^^^^^^^^

You can set a global API key using the :function:`fedfred.config.set_api_key(api_key)` function:

.. code-block:: python

    import fedfred as fd
    fd.set_api_key("your_global_api_key")

Overriding the Global API Key
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can still override the global API key by providing an `api_key` parameter when instantiating :class:`fedfred.clients.FredAPI`:

.. code-block:: python

    from fedfred.clients import FredAPI

    # This instance uses the global API key
    fred_global = FredAPI()

    # This instance uses a specific API key
    fred_specific = FredAPI(api_key="your_specific_api_key")

Special Notes: Parameter Conversion and Nested Classes (FedFred 2.0+)
=====================================================================

Starting from **version 2.0**, the :mod:`fedfred` library introduces **automatic parameter conversion** and **nested class access**.
These enhancements make it easier to interact with the **FRED® API** while ensuring full compatibility and clean code design.

This page details these important features.

---

Parameter Conversion in FedFred
-------------------------------

FedFred **automatically converts** method parameters into formats accepted by the FRED API, simplifying the user experience.

Supported Conversions
^^^^^^^^^^^^^^^^^^^^^

- :class:`datetime.datetime` **objects**:

  Automatically converted to `YYYY-MM-DD` formatted strings.

  Example:

  .. code-block:: python

      from datetime import datetime
      fred.get_series_observations(
          series_id="GNPCA",
          observation_start=datetime(2020, 1, 1)
      )
      # Converts to: "2020-01-01"

- :class:`list` **of** :class:`str` **or** :class:`str`:

  Lists are converted into semicolon-delimited strings.

  Example:

  .. code-block:: python

      fred.get_tags(tag_names=["nation", "usa", "economy"])
      # Converts to: "nation;usa;economy"

- :class:`Optional[Union[str, list[str]]]`:

  Accepts either a string or a list of strings seamlessly.

  Example:

  .. code-block:: python

      fred.get_related_tags(tag_names="nation")
      fred.get_related_tags(tag_names=["nation", "usa"])

- :class:`Optional[Union[str, datetime.datetime]]`:

  Accepts either a string date or a datetime object.

  Example:

  .. code-block:: python

      fred.get_series_observations(
          series_id="GNPCA",
          observation_start="2020-01-01",
          observation_end=datetime(2021, 1, 1)
      )

Helper Methods for Conversion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Parameter conversion is handled internally by helper methods in the :class:`fedfred.helpers.FredHelpers` class:

- :meth:`fedfred.helpers.FredHelpers.datetime_conversion`: Converts :class:`datetime.datetime` objects into `YYYY-MM-DD` strings.
- :meth:`fedfred.helpers.FredHelpers.liststring_conversion`: Converts lists of strings into a semicolon-delimited string.
- :meth:`fedfred.helpers.FredHelpers.parameter_validation`: Validates parameters before API requests are made.

See :ref:`resources-index` for more about helper utilities.

---

Examples of Parameter Conversion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Using** :class:`datetime.datetime` **parameters**:

  .. code-block:: python

      from datetime import datetime
      fred.get_series_observations(
          series_id="GNPCA",
          observation_start=datetime(2020, 1, 1),
          observation_end=datetime(2021, 1, 1)
      )

- **Using** :class:`list` **parameters**:

  .. code-block:: python

      fred.get_tags(tag_names=["sticky", "price", "nation"])

- **Mixing** :class:`str` **and** :class:`list` **parameters**:

  .. code-block:: python

      fred.get_related_tags(tag_names="nation")
      fred.get_related_tags(tag_names=["nation", "usa"])

---

Accessing Nested Classes in :class:`fedfred.clients.FredAPI`
------------------------------------------------------------

FedFred's :class:`fedfred.clients.FredAPI` contains nested classes that expand functionality for asynchronous (:term:`async`) and geospatial (:term:`GeoDataFrame`) data retrieval.

Available Nested Classes
^^^^^^^^^^^^^^^^^^^^^^^^

- :class:`fedfred.clients.FredAPI.AsyncAPI` **(accessed via** `fred.Async` **):**

  .. code-block:: python

      import asyncio
      from fedfred.clients import FredAPI

      fred = FredAPI(api_key="your_api_key")
      async_api = fred.Async

      async def main():
          categories = await async_api.get_category_children(category_id=0)
          for category in categories:
              print(category.name)

      asyncio.run(main())

- :class:`fedfred.clients.FredAPI.MapsAPI` **(accessed via** `fred.Maps` **):**

  .. code-block:: python

      from fedfred.clients import FredAPI

      fred = FredAPI(api_key="your_api_key")
      maps_api = fred.Maps

      regional_data = maps_api.get_series_data(
          series_id="SMU53000000500000001",
          date="2023-01-01"
      )
      print(regional_data)

- :class:`fedfred.clients.FredAPI.AsyncAPI.AsyncMapsAPI` **(accessed via** `fred.Async.Maps` **):**

  .. code-block:: python

      import asyncio
      from fedfred.clients import FredAPI

      fred = FredAPI(api_key="your_api_key")
      async_maps_api = fred.Async.Maps

      async def main():
          regional_data = await async_maps_api.get_series_data(
              series_id="SMU53000000500000001",
              date="2023-01-01"
          )
          print(regional_data)

      asyncio.run(main())

---

Related Topics
^^^^^^^^^^^^^^

- See the full API documentation: :ref:`api-index`
- Learn about real-world applications: :ref:`use-cases`
- Understand helper utilities: :ref:`resources-index`
