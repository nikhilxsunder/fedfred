.. _api-notes:

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

      fred.get_tags(tag_names=["nation", "usa", "economy"])

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