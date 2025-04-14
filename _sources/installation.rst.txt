Installation
============

Using pip
---------

You can install fedfred using pip:

.. code-block:: bash

   pip install fedfred

Using conda
-----------

FedFred is available on Conda-Forge. You can install it with conda:

.. code-block:: bash

   conda install -c conda-forge fedfred

We recommend creating a dedicated environment for your project:

.. code-block:: bash

   conda create -n myenv
   conda activate myenv
   conda install conda-forge::fedfred

Optional Type Stubs
-------------------

If you need type stubs for development (e.g., for `pandas`, `cachetools`, or `geopandas`), you can install the optional dependencies:

Using pip:

.. code-block:: bash

   pip install fedfred[types]

Optional DataFrame Dependencies
-------------------------------

FedFred uses `pandas` and `geopandas` natively but also supports `polars` and `dask` for DataFrames as well as `polars-st` and `dask-geopandas` for GeoDataFrames. You can install the optional dependencies for either library:

Using pip:

.. code-block:: bash

   pip install fedfred[pandas]
   pip install fedfred[polars]
   pip install fedfred[dask]

Development Installation
------------------------

For development purposes, you can install the package with all development dependencies:

Using Poetry (recommended):

.. code-block:: bash

    git clone https://github.com/nikhilxsunder/fedfred.git
    cd fedfred
    poetry install

Using conda:

.. code-block:: bash

    git clone https://github.com/nikhilxsunder/fedfred.git
    cd fedfred

    # Create a conda environment
    conda create -n fedfred-dev python=3.9
    conda activate fedfred-dev

    # Install in development mode with dev dependencies
    pip install -e ".[dev,types]"

    # Install pre-commit hooks
    pre-commit install
