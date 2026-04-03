import importlib.metadata

project = "fontstack"
author = "Kanin"
release = importlib.metadata.version("fontstack")

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "notfound.extension",
]

html_theme = "sphinx_rtd_theme"
