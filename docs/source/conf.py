# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# -- Project information -----------------------------------------------------
project = 'fedfred'
copyright = '2025, Nikhil Sunder'
author = 'Nikhil Sunder'
release = '2.0.9'

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
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

# sitemap
sitemap_filename = "sitemap.xml"
sitemap_url_scheme = "{link}"

# google analytics
googleanalytics_id = 'G-Q7LK34R0CV'
googleanalytics_enabled = True

# html
html_baseurl = 'https://nikhilxsunder.github.io/fedfred/'
html_extra_path = ['robots.txt', 'BingSiteAuth.xml']
html_theme = 'furo'
html_theme_options = {
    "sidebar_hide_name": False,
    "light_css_variables": {
        "color-brand-primary": "#4B6EAF",
        "color-brand-content": "#4B6EAF",
    },
    "dark_css_variables": {
        "color-brand-primary": "#7A97D0",
        "color-brand-content": "#7A97D0",
    },
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/nikhilxsunder/fedfred",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/fedfred/",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zM4.5 7.5a.5.5 0 0 0 0 1h5.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 0-.708.708L10.293 7.5H4.5z"/>
                </svg>
            """,
        },
    ],
}
html_static_path = ['_static']
html_title = "fedfred"
html_favicon = "_static/fedfred_favicon.ico"
html_logo = "_static/fedfred-logo.png"
html_meta ={
    "description": "A feature-rich python package for interacting with the Federal Reserve Bank of St. Louis Economic Database: FRED",
    "keywords": "fred, federal reserve, api, economics, finance, economic data, financial data, fred pandas, fred polars, fred dask, fred geopandas, async, pandas, polars, dask, geopandas, cache, financial analysis, economic analysis, data analysis, data science, data visualization, data mining, data wrangling, data cleaning"
}
html_context = {
    "json_ld": """
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "FedFred",
        "url": "https://nikhilxsunder.github.io/fedfred/",
        "description": "A feature-rich Python package for interacting with the Federal Reserve Bank of St. Louis Economic Database (FRED).",
        "applicationCategory": "FinanceApplication",
        "operatingSystem": "Linux, MacOS, Windows",
        "softwareVersion": "1.3.0",
        "author": {
            "@type": "Person",
            "name": "Nikhil Sunder"
        },
        "license": "https://www.gnu.org/licenses/agpl-3.0.html",
        "programmingLanguage": "Python",
        "downloadUrl": "https://pypi.org/project/fedfred/",
        "sourceCode": "https://github.com/nikhilxsunder/fedfred",
        "documentation": "https://nikhilxsunder.github.io/fedfred/"
    }
    </script>
    """
}
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
ogp_image = "_static/fedfred-logo.png"
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
    'httpx': ('https://www.python-httpx.org/en/stable/', None),
    'polars': ('https://pola-rs.github.io/polars/py-polars/html/', None),
    'dask': ('https://docs.dask.org/en/stable/', None),
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
