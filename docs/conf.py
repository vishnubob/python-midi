# Sphinx configuration for python-midi

project = "python-midi"
copyright = "2024, Giles Hall"
author = "Giles Hall"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.inheritance_diagram",
    "sphinx_autodoc_typehints",
]

# -- autodoc settings --------------------------------------------------------
autodoc_typehints = "description"
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}

# -- Napoleon settings -------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- intersphinx settings ----------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- HTML output -------------------------------------------------------------
html_theme = "sphinx_rtd_theme"

# -- General settings --------------------------------------------------------
exclude_patterns = ["_build"]
