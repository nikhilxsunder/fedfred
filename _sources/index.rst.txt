.. _home:

FedFred: A Modern Python Client for FRED® API
=============================================

FedFred is a **feature-rich Python package** for interacting with the **Federal Reserve Bank of St. Louis Economic Database (FRED®)**.  
It supports **synchronous** and **asynchronous** access to FRED data, along with **DataFrame transformations**, **rate-limiting**, **local caching**, and **typed object models** — making it the most modern FRED client available for Python developers.

Install FedFred
---------------

.. tab-set::

   .. tab-item:: pip

      .. code-block:: bash

         pip install fedfred

   .. tab-item:: conda

      .. code-block:: bash

         conda install -c conda-forge fedfred

See :ref:`installation` for more options, including conda and optional dependencies.

---

Badges
------

.. grid::
    :gutter: 2

    .. grid-item-card:: Build Status
        :columns: 4
        :link: https://github.com/nikhilxsunder/fedfred/actions/workflows/main.yml
        :link-alt: GitHub Build Status

        GitHub Actions build status.

        .. image:: https://github.com/nikhilxsunder/fedfred/actions/workflows/main.yml/badge.svg
           :alt: Build Status
           :align: center

    .. grid-item-card:: Static Analysis
        :columns: 4
        :link: https://github.com/nikhilxsunder/fedfred/actions/workflows/analyze.yml
        :link-alt: GitHub Static Analysis Status

        Code linting and static analysis checks.

        .. image:: https://github.com/nikhilxsunder/fedfred/actions/workflows/analyze.yml/badge.svg
           :alt: Static Analysis Status
           :align: center

    .. grid-item-card:: Unit Test Status
        :columns: 4
        :link: https://github.com/nikhilxsunder/fedfred/actions/workflows/test.yml
        :link-alt: GitHub Unit Tests

        Unit test coverage for critical components.

        .. image:: https://github.com/nikhilxsunder/fedfred/actions/workflows/test.yml/badge.svg
           :alt: Unit Test Status
           :align: center

    .. grid-item-card:: Security Analysis
        :columns: 4
        :link: https://github.com/nikhilxsunder/fedfred/actions/workflows/codeql.yml
        :link-alt: GitHub Security CodeQL Scan

        GitHub CodeQL security scanning.

        .. image:: https://github.com/nikhilxsunder/fedfred/actions/workflows/codeql.yml/badge.svg
           :alt: Security Analysis Status
           :align: center

    .. grid-item-card:: OpenSSF Best Practices
        :columns: 4
        :link: https://www.bestpractices.dev/projects/10158
        :link-alt: OpenSSF Best Practices Certification

        Open Source Security Foundation (OpenSSF) Gold Badge.

        .. image:: https://www.bestpractices.dev/projects/10158/badge
           :alt: OpenSSF Best Practices Certified
           :align: center

    .. grid-item-card:: Code Coverage
        :columns: 4
        :link: https://codecov.io/gh/nikhilxsunder/fedfred
        :link-alt: Code Coverage with Codecov

        Codecov test coverage report.

        .. image:: https://codecov.io/gh/nikhilxsunder/fedfred/graph/badge.svg
           :alt: Code Coverage
           :align: center

    .. grid-item-card:: Socket Security Score
        :columns: 4
        :link: https://socket.dev/pypi/package/fedfred/overview/2.1.1/tar-gz
        :link-alt: Socket Security Analysis

        Security risk analysis via Socket.dev.

        .. image:: https://socket.dev/api/badge/pypi/package/fedfred/2.1.1?artifact_id=tar-gz
           :alt: Socket Security Score
           :align: center

    .. grid-item-card:: Packaging Status
        :columns: 4
        :link: https://repology.org/project/python%3Afedfred/versions
        :link-alt: Packaging Status Repology

        Repology packaging status across Linux distributions.

        .. image:: https://repology.org/badge/tiny-repos/python%3Afedfred.svg
           :alt: Packaging Status
           :align: center

    .. grid-item-card:: PyPI Version
        :columns: 4
        :link: https://pypi.org/project/fedfred/
        :link-alt: View FedFred on PyPI

        Latest version released on PyPI.

        .. image:: https://img.shields.io/pypi/v/fedfred.svg
           :alt: PyPI Version
           :align: center

    .. grid-item-card:: PyPI Downloads
        :columns: 4
        :link: https://pepy.tech/projects/fedfred
        :link-alt: PyPI Download Statistics

        Download stats via Pepy.tech.

        .. image:: https://static.pepy.tech/badge/fedfred
           :alt: PyPI Downloads
           :align: center

    .. grid-item-card:: Conda-Forge Version
        :columns: 4
        :link: https://anaconda.org/conda-forge/fedfred
        :link-alt: View FedFred on Conda-Forge

        Conda-forge published version.

        .. image:: https://anaconda.org/conda-forge/fedfred/badges/version.svg
           :alt: Conda-Forge Version
           :align: center

    .. grid-item-card:: Conda-Forge Downloads
        :columns: 4
        :link: https://anaconda.org/conda-forge/fedfred
        :link-alt: Conda-Forge Download Statistics

        Number of downloads from Conda-Forge.

        .. image:: https://anaconda.org/conda-forge/fedfred/badges/downloads.svg
           :alt: Conda-Forge Downloads
           :align: center

Key Features
------------

.. dropdown:: Flexible DataFrames
   :color: primary
   :icon: table

   Output data as Pandas, Polars, or Dask DataFrames for seamless data manipulation.

.. dropdown:: GeoSpatial Support
   :color: secondary
   :icon: location

   Native output to GeoDataFrames using GeoPandas, Polars-ST, and Dask-GeoPandas.

.. dropdown:: Async Compatibility
   :color: primary
   :icon: rocket

   Full async client (:class:`fedfred.clients.FredAPI.AsyncAPI`) for non-blocking data pipelines.

.. dropdown:: Local Caching
   :color: secondary
   :icon: archive

   FIFO local cache accelerates repeated queries dramatically.

.. dropdown:: Rate Limiting
   :color: primary
   :icon: clock

   Automatic throttling to comply with FRED’s API request limits.

.. dropdown:: Structured Models
   :color: secondary
   :icon: database

   Rich typed objects (:class:`fedfred.objects.Series`, :class:`fedfred.objects.Release`) representing FRED entities.

Resources
---------

Explore the documentation:

.. toctree::
   :maxdepth: 2
   :caption: Get Started

   installation/index

.. toctree::
   :maxdepth: 2
   :caption: Developer Reference

   api/index
   resources/index
   glossary

.. toctree::
   :maxdepth: 1
   :caption: Project

   contributing
   changelog
   code_of_conduct
   security
   license
