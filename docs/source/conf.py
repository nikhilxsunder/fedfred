# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

# -- Project information -----------------------------------------------------
project = 'fedfred'
copyright = '2025, Nikhil Sunder'
author = 'Nikhil Sunder'
release = '2.1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
    'myst_parser',
    'sphinxcontrib.googleanalytics',
    'sphinx_sitemap',
    'sphinxext.opengraph',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.graphviz',
    'sphinx.ext.extlinks',
    'sphinx.ext.doctest',
    "sphinx_design",
]

# myst
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 4

# path
sys.path.insert(0, os.path.abspath('../../src'))

# sitemap
sitemap_filename = "sitemap.xml"
sitemap_url_scheme = "{link}"

# google analytics
googleanalytics_id = 'G-Q7LK34R0CV'
googleanalytics_enabled = True

# html
html_baseurl = 'https://nikhilxsunder.github.io/fedfred/'
html_extra_path = ['robots.txt', 'BingSiteAuth.xml', '1bf488999066430fb8b8b741dc2a3486.txt']
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "logo": {
        "image_light": "_static/fedfred-logo.png",
        "image_dark": "_static/fedfred-logo.png",
    },
    "header_links_before_dropdown": 5,
    "navbar_start": ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": [ "navbar-icon-links"],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/nikhilxsunder/fedfred",
            "icon": "fab fa-github",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/fedfred/",
            "icon": "fab fa-python",
        },
        {
            "name": "Conda-Forge",
            "url": "https://anaconda.org/conda-forge/fedfred",
            "icon": "fas fa-database",
        },
        {
            "name": "Codecov",
            "url": "https://app.codecov.io/gh/nikhilxsunder/fedfred",
            "icon": "fas fa-umbrella",
        },
        {
            "name": "Socket",
            "url": "https://socket.dev/pypi/package/fedfred/overview/2.0.9/tar-gz",
            "icon": "fas fa-shield",
        },
        {
            "name": "OpenSSF",
            "url": "https://www.bestpractices.dev/en/projects/10158?criteria_level=2",
            "icon": "fas fa-trophy",
        },
    ],
    "navbar_align": "right",
    "primary_sidebar_end": ["sidebar-ethical-ads"],
    "footer_start": ["copyright"],
    "footer_end": ["sphinx-version", "theme-version"],
    "use_edit_page_button": True,
    "show_toc_level": 1,
    "show_prev_next": True,
    "announcement": """
        <div class="sidebar-message">
            Version 2 is now available!
            Please check the
            <a href="resources/notes.html" target="_self">
                special notes page
            </a>
            for more information.
        </div>
    """,
}
html_static_path = ['_static']
html_title = "fedfred"
html_favicon = "_static/fedfred_favicon.ico"
html_logo = "_static/fedfred-logo.png"
html_context = {
    "github_user": "nikhilxsunder",
    "github_repo": "fedfred",
    "github_version": "main",
    "doc_path": "docs/source",
}
html_meta ={
    "description": "A feature-rich python package for interacting with the Federal Reserve Bank of St. Louis Economic Database: FRED",
    "keywords": "fred, federal reserve, api, economics, finance, economic data, financial data, fred pandas, fred polars, fred dask, fred geopandas, async, pandas, polars, dask, geopandas, cache, financial analysis, economic analysis, data analysis, data science, data visualization, data mining, data wrangling, data cleaning"
}
html_js_files = [
    'json_ld.js',
]

templates_path = ['_templates']

# autodocs
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}
autodoc_typehints = "description"
autodoc_typehints_format = "short"

# md/rst
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# opengraph
ogp_site_url = "https://nikhilxsunder.github.io/fedfred/"
ogp_image = "https://nikhilxsunder.github.io/fedfred/_static/fedfred-logo.png"
ogp_description_length = 300
ogp_type = "website"
ogp_custom_meta_tags = [
    '<meta property="og:locale" content="en_US" />',
    '<meta property="og:site_name" content="FedFred Documentation" />',
    '<meta property="og:url" content="https://nikhilxsunder.github.io/fedfred/" />',
    '<meta property="og:image:alt" content="FedFred Logo" />',
]
ogp_enable_meta_description = True

# intersphinx
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
    'geopandas': ('https://geopandas.org/en/stable/', None),
    'polars': ('https://pola-rs.github.io/polars/py-polars/html/', None),
    'dask': ('https://docs.dask.org/en/stable/', None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "seaborn": ("https://seaborn.pydata.org/", None),
    "tenacity": ("https://tenacity.readthedocs.io/en/latest/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}

# autosummary
autosummary_generate = True

# extlinks
extlinks = {
    'python-doc': ('https://docs.python.org/3/library/%s', 'Python Docs: %s'),
    'pandas-doc': ('https://pandas.pydata.org/pandas-docs/stable/reference/%s', 'Pandas Docs: %s'),
    'geopandas-doc': ('https://geopandas.org/en/stable/docs/reference/%s', 'GeoPandas Docs: %s'),
    'fred-api': ('https://fred.stlouisfed.org/docs/api/fred/%s', 'FRED API Docs: %s'),
    'github': ('https://github.com/nikhilxsunder/fedfred/%s', 'GitHub: %s'),
}
