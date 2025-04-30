.. _api-index:

API Reference
=============

This section provides detailed, automatically generated documentation for FedFred's **modules**, **classes**, and **functions**.  
It covers both synchronous and asynchronous clients, helper utilities, and typed object models.

All API documentation is generated from the live source code using Sphinx :mod:`autodoc` and :mod:`autosummary`.

---

API Clients
-----------

.. autosummary::
   :toctree: _autosummary
   :template: autosummary/class.rst

   fedfred.FredAPI
   fedfred.AsyncAPI
   fedfred.MapsAPI
   fedfred.AsyncMapsAPI

Utility Helpers
---------------

.. autosummary::
   :toctree: _autosummary
   :template: autosummary/class.rst

   fedfred.helpers.FredHelpers

Data Objects
------------

.. autosummary::
   :toctree: _autosummary
   :template: autosummary/class.rst

   fedfred.objects.Category
   fedfred.objects.Series
   fedfred.objects.Tag
   fedfred.objects.Release
   fedfred.objects.ReleaseDate
   fedfred.objects.Source
   fedfred.objects.Element
   fedfred.objects.VintageDate
   fedfred.objects.SeriesGroup

---

Related Resources
^^^^^^^^^^^^^^^^^

.. grid::
   :gutter: 2

   .. grid-item-card:: Quick Start Tutorial
       :link: quickstart
       :link-type: ref
       :link-alt: Quick Start Tutorial

       Get started with FedFred in minutes.

   .. grid-item-card:: Usage Examples
       :link: basic-usage
       :link-type: ref
       :link-alt: Basic and Advanced Usage Examples

       Explore basic and advanced usage scenarios.

   .. grid-item-card:: Data Visualization
       :link: data-visualization
       :link-type: ref
       :link-alt: Data Visualization Examples

       Build charts, plots, and heatmaps from FRED data.

   .. grid-item-card:: Real-World Use Cases
       :link: use-cases
       :link-type: ref
       :link-alt: Real-World Use Cases

       Discover practical applications of FedFred.

   .. grid-item-card:: Internal Class Structure
       :link: architecture
       :link-type: ref
       :link-alt: Internal Class Structure Overview

       Understand the internal architecture of FedFred.

   .. grid-item-card:: Parameter Handling Notes
       :link: api-notes
       :link-type: ref
       :link-alt: Parameter Conversion and Validation Notes

       Learn how FedFred transforms and validates your parameters.