# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

# ---------------------------------------------------------------------------
# Project information
# ---------------------------------------------------------------------------
project = "fedfred"
author = "Nikhil Sunder"
copyright = "2026, Nikhil Sunder"
release = "4.0.0"

# ---------------------------------------------------------------------------
# General configuration
# ---------------------------------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "myst_parser",
    "sphinx_sitemap",
    "sphinxext.opengraph",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.graphviz",
    "sphinx.ext.extlinks",
    "sphinx.ext.doctest",
    "sphinx_design",
]

templates_path = ["_templates"]
language = "en"

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Fail the build on dangling cross-references; ignore externals without an objects.inv.
nitpicky = True
nitpick_ignore = [
    ("py:class", "httpx.HTTPError"),
    ("py:class", "httpx.Response"),
    # add others as the first nitpicky build surfaces them
]

# ---------------------------------------------------------------------------
# Extension configuration
# ---------------------------------------------------------------------------

# -- autodoc + typehints ----------------------------------------------------
# Docstrings are the single source of truth for types; the typehints extension
# is suppressed from injecting its own :type:/:rtype: directives.
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_member_order = "bysource"  # render base -> leaves in source order, not alphabetical
autodoc_typehints = "none"

typehints_use_signature = False
typehints_use_signature_return = False
typehints_document_rtype = False  # your Returns: block owns the return type
always_document_param_types = False

# -- napoleon ---------------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False  # Google-style only; stop the NumPy parser
napoleon_include_init_with_doc = False  # __init__ is dataclass-generated; document on the class
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True  # picks up __str__ docstrings
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = True  # renders Notes: as a styled admonition
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True  # Attributes: -> :ivar: (correct for dataclass fields)
napoleon_use_param = True
napoleon_use_keyword = True
napoleon_use_rtype = True
napoleon_preprocess_types = True  # normalize "str | None" etc. in docstring type strings
napoleon_attr_annotations = True  # let field annotations supply Attributes types
napoleon_custom_sections = None

# -- autosummary ------------------------------------------------------------
autosummary_generate = True

# -- intersphinx ------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
    "geopandas": ("https://geopandas.org/en/stable/", None),
    "polars": ("https://pola-rs.github.io/polars/py-polars/html/", None),
    "dask": ("https://docs.dask.org/en/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "seaborn": ("https://seaborn.pydata.org/", None),
    "tenacity": ("https://tenacity.readthedocs.io/en/latest/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
    "cachetools": ("https://cachetools.readthedocs.io/en/stable/", None),
    "dask_geopandas": ("https://dask-geopandas.readthedocs.io/en/latest/", None),
    "polars_st": ("https://oreilles.github.io/polars-st/", None),
    "mypy": ("https://mypy.readthedocs.io/en/stable/", None),
}

# -- extlinks ---------------------------------------------------------------
extlinks = {
    "python-doc": ("https://docs.python.org/3/library/%s", "Python Docs: %s"),
    "pandas-doc": ("https://pandas.pydata.org/pandas-docs/stable/reference/%s", "Pandas Docs: %s"),
    "geopandas-doc": ("https://geopandas.org/en/stable/docs/reference/%s", "GeoPandas Docs: %s"),
    "fred-api": ("https://fred.stlouisfed.org/docs/api/fred/%s", "FRED API Docs: %s"),
    "github": ("https://github.com/nikhilxsunder/fedfred/%s", "GitHub: %s"),
}

# -- myst -------------------------------------------------------------------
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

# -- opengraph --------------------------------------------------------------
ogp_site_url = "https://nikhilxsunder.github.io/fedfred/"
ogp_image = "https://nikhilxsunder.github.io/fedfred/_static/fedfred_social_preview_transparent.png"
ogp_description_length = 300
ogp_type = "website"
ogp_enable_meta_description = True
ogp_custom_meta_tags = [
    '<meta property="og:locale" content="en_US" />',
    '<meta property="og:site_name" content="FedFred Documentation" />',
    '<meta property="og:url" content="https://nikhilxsunder.github.io/fedfred/" />',
    '<meta property="og:image:alt" content="FedFred Logo" />',
]

# -- sitemap ----------------------------------------------------------------
sitemap_filename = "sitemap.xml"
sitemap_url_scheme = "{link}"

# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------
html_theme = "pydata_sphinx_theme"
html_title = "fedfred"
html_baseurl = "https://nikhilxsunder.github.io/fedfred/"
html_logo = "_static/fedfred_banner.png"
html_favicon = "_static/fedfred_favicon.ico"
html_static_path = ["_static"]
html_extra_path = ["robots.txt", "BingSiteAuth.xml", "29979ea943cf4526830870100b86564a.txt"]

html_context = {
    "github_user": "nikhilxsunder",
    "github_repo": "fedfred",
    "github_version": "v4-dev",  # TODO: flip to "main" at the v4 cutover (with the switcher json_url)
    "doc_path": "docs/source",
}

html_meta = {
    "description": "A feature-rich python package for interacting with the Federal Reserve Bank of St. Louis Economic Database: FRED",
    "keywords": "fred, federal reserve, api, economics, finance, economic data, financial data, fred pandas, fred polars, fred dask, fred geopandas, async, pandas, polars, dask, geopandas, cache, financial analysis, economic analysis, data analysis, data science, data visualization, data mining, data wrangling, data cleaning",
}

html_theme_options = {
    "analytics": {
        "google_analytics_id": "G-Q7LK34R0CV",
    },
    "logo": {
        "image_light": "_static/fedfred_banner_transparent.png",
        "image_dark": "_static/fedfred_banner_transparent.png",
    },
    "show_version_warning_banner": True,
    "header_links_before_dropdown": 5,
    "switcher": {
        "json_url": "https://raw.githubusercontent.com/nikhilxsunder/fedfred/v4-dev/docs/source/_static/switcher.json",  # TODO: point at the stable switcher.json once v4 is released
        "version_match": release,  # matches the "version" field in the JSON
    },
    "check_switcher": True,
    "navbar_start": ["navbar-logo", "version-switcher"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": [
        "navbar-icon-links",
        "theme-switcher",
    ],
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
            "icon": "fas fa-flask",
        },
        {
            "name": "Codecov",
            "url": "https://app.codecov.io/gh/nikhilxsunder/fedfred",
            "icon": "fas fa-umbrella",
        },
        {
            "name": "Socket",
            "url": "https://socket.dev/pypi/package/fedfred/overview/2.1.1/tar-gz",
            "icon": "fas fa-shield",
        },
        {
            "name": "OpenSSF",
            "url": "https://www.bestpractices.dev/en/projects/10158?criteria_level=2",
            "icon": "fas fa-trophy",
        },
    ],
    "navbar_align": "left",
    "primary_sidebar_end": ["sidebar-ethical-ads"],
    "footer_start": ["copyright"],
    "footer_end": ["sphinx-version", "theme-version"],
    "use_edit_page_button": True,
    "show_toc_level": 1,
    "show_prev_next": True,
    "announcement": """
        <div class="sidebar-message">
            Version 4 is now available!
            Please check the
            <a href="https://nikhilxsunder.github.io/fedfred/resources/notes.html" target="_self">
                special notes page
            </a>
            for more information.
        </div>
    """,
}

html_css_files = [
    "custom.css",
    "https://cdn.jsdelivr.net/gh/orestbida/cookieconsent@3.1.0/dist/cookieconsent.css",
]
html_js_files = [
    "consent-default.js",  # FIRST: deny-by-default before gtag
    "json_ld.js",
    (
        "https://cdn.jsdelivr.net/gh/orestbida/cookieconsent@3.1.0/dist/cookieconsent.umd.js",
        {"defer": "defer"},
    ),
    ("cookie-consent.js", {"defer": "defer"}),
]
