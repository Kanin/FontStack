import importlib.metadata

project = "fontstack"
author = "Kanin"
release = importlib.metadata.version("fontstack")

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "notfound.extension",
]

html_theme = "furo"

html_theme_options = {
    "top_of_page_buttons": ["view", "edit"],
}

# Move type annotations from signatures into parameter descriptions.
autodoc_typehints = "description"

# Keep members in source-code order rather than alphabetical.
autodoc_member_order = "bysource"

# Wrap long signatures.
maximum_signature_line_length = 88

# Map type aliases so Sphinx renders "FillType" instead of the full union.
autodoc_type_aliases = {
    "FillType": "FillType",
    "RenderMode": "RenderMode",
    "HorizontalAlign": "HorizontalAlign",
}

# Link to Pillow / Python docs for cross-references.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "PIL": ("https://pillow.readthedocs.io/en/stable/", None),
}
