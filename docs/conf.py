import importlib.metadata
import typing

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


# region Overload collapsing

# Sphinx discovers @overload signatures via typing.get_overloads() and creates
# a separate documentation entry for each one.  For draw_text (12 overloads)
# and FontManager.draw (4 overloads) this produces massive duplication.
# Patching typing.get_overloads to return [] for our functions makes Sphinx
# document only the single implementation signature while keeping the overloads
# fully available to type-checkers at development time.

_orig_get_overloads = typing.get_overloads


def _get_overloads_suppressed(func):
    """Return [] for fontstack functions so Sphinx shows one signature."""
    module = getattr(func, "__module__", "") or ""
    if module.startswith("fontstack"):
        return []
    return _orig_get_overloads(func)


typing.get_overloads = _get_overloads_suppressed

# endregion
