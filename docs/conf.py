import importlib.metadata
import inspect
import typing

from sphinx.util.inspect import stringify_signature

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

# Sphinx renders every @overload signature separately, which produces 12
# near-identical blocks for draw_text.  Monkey-patch FunctionDocumenter so
# overloaded functions show only the implementation signature.

from sphinx.ext.autodoc import FunctionDocumenter  # noqa: E402

_orig_format_sig = FunctionDocumenter.format_signature


def _format_signature_no_overloads(self, **kwargs):
    """Show only the implementation signature for @overload-ed functions."""
    try:
        overloads = typing.get_overloads(self.object)
    except (TypeError, AttributeError):
        overloads = []
    if not overloads:
        return _orig_format_sig(self, **kwargs)
    # Skip the overloads and format only the implementation's own signature.
    if self.config.autodoc_typehints in ("none", "description"):
        kwargs.setdefault("show_annotation", False)
    sig = inspect.signature(self.object, follow_wrapped=True)
    return stringify_signature(sig, **kwargs)


FunctionDocumenter.format_signature = _format_signature_no_overloads

# endregion
