.. _installation:

Installing FedFred
==================

FedFred is available on both **PyPI** and **Conda-Forge**.  
This page covers multiple ways to install FedFred for production or development use.

---

Installation Methods
--------------------

.. tab-set::

   .. tab-item:: pip (PyPI)

      Install the latest stable release from PyPI:

      .. code-block:: bash

         pip install fedfred

      Installs core dependencies needed for Pandas-based :term:`DataFrame` outputs.

   .. tab-item:: conda (Conda-Forge)

      Install via Conda-Forge:

      .. code-block:: bash

         conda install -c conda-forge fedfred

      We recommend creating a new environment:

      .. code-block:: bash

         conda create -n myenv
         conda activate myenv
         conda install -c conda-forge fedfred

   .. tab-item:: Development Install (GitHub)

      Clone and install for local development:

      .. code-block:: bash

         git clone https://github.com/nikhilxsunder/fedfred.git
         cd fedfred
         poetry install

      See :ref:`contributing` for developer guidelines.

---

Optional Enhancements
----------------------

.. dropdown:: Install Type Stubs for Static Typing
   :color: secondary
   :open:

   Boost development experience with type hints (e.g., :mod:`mypy`, :mod:`pyright`):

   .. code-block:: bash

      pip install fedfred[types]

   Includes stubs for `pandas`, `geopandas`, `cachetools`, and others.

.. dropdown:: Install Additional DataFrame Backends
   :color: secondary
   :open:

   FedFred supports optional high-performance DataFrame libraries:

   .. code-block:: bash

      pip install fedfred[polars]
      pip install fedfred[dask]

   - **Polars**: Lightning-fast DataFrames for large datasets.
   - **Dask**: Parallel, out-of-core DataFrame computation.

   See :ref:`api-overview` for details.

---

Developer Quick Setup
----------------------

.. grid::
   :gutter: 2

   .. grid-item-card:: Development Setup (Poetry)
      :link: https://github.com/nikhilxsunder/fedfred
      :link-alt: View Source on GitHub

      Clone the repository and install with all development dependencies:

      .. code-block:: bash

         git clone https://github.com/nikhilxsunder/fedfred.git
         cd fedfred
         poetry install

   .. grid-item-card:: Alternative Setup (conda + pip)
      :link: https://github.com/nikhilxsunder/fedfred
      :link-alt: View Source on GitHub

      Create a dedicated environment manually:

      .. code-block:: bash

         git clone https://github.com/nikhilxsunder/fedfred.git
         cd fedfred

         conda create -n fedfred-dev python=3.9
         conda activate fedfred-dev

         pip install -e ".[dev,types]"

         pre-commit install

---

Related Resources
-----------------

.. grid::
   :gutter: 2

   .. grid-item-card:: Installation & Usage Guide
      :link: installation-usage
      :link-type: ref
      :link-alt: Installation and Usage Documentation

      Full beginner tutorial for setting up FedFred and fetching data.

   .. grid-item-card:: Basic and Advanced Examples
      :link: basic-usage
      :link-type: ref
      :link-alt: Basic and Advanced Usage Examples

      Examples on time series retrieval, DataFrame conversion, and visualization.

   .. grid-item-card:: Parameter Handling Notes
      :link: api-notes
      :link-type: ref
      :link-alt: API Parameter Handling Notes

      Learn how FedFred automatically validates and transforms parameters.

---