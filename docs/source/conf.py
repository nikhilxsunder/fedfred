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
release = '1.2.9'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
    'myst_parser',
    'sphinxcontrib.googleanalytics',
    'sphinx_sitemap',
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

# autodocs
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

# md/rst
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
html_static_path = ['_static']
