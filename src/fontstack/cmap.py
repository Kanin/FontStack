"""Character map (cmap) loading via fonttools."""

from __future__ import annotations

from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection

__all__ = ["_load_cmap"]


def _load_cmap(path: str, ttc_index: int = 0) -> frozenset[int]:
    """
    Return every Unicode codepoint supported by a font file as an immutable
    frozen set, using fonttools for accurate, format-agnostic parsing.

    Supports TTF, OTF, and TrueType/OpenType Collections (.ttc/.otc).
    For collections the ``ttc_index`` selects which member font to read.

    fonttools' ``getBestCmap`` selects the widest-coverage subtable
    automatically, preferring the Windows full-repertoire subtable (platform 3,
    encoding 10) over the BMP-only subtable (platform 3, encoding 1) - the
    same priority order used internally by HarfBuzz. This handles all cmap
    formats (0, 2, 4, 6, 8, 10, 12, 13, 14) rather than the Format 4/12 subset
    that a manual binary parser would cover.

    Parameters
    ----------
    path:
        Path to the font file on disk.
    ttc_index:
        Index of the desired font within a collection. Ignored for non-TTC
        files. Defaults to ``0``.

    Returns
    -------
    frozenset[int]
        All codepoints present in the chosen cmap subtable. Returns an empty
        frozenset if the font has no Unicode cmap at all.
    """
    is_collection = path.lower().endswith((".ttc", ".otc"))

    if is_collection:
        # TTCollection exposes each member font as a TTFont instance.
        with TTCollection(path) as collection:
            tt = collection[ttc_index]
            cmap = tt.getBestCmap() or {}
    else:
        # lazy=True defers parsing all tables until accessed; we only need
        # the cmap table so this keeps the load fast.
        with TTFont(path, lazy=True) as tt:
            cmap = tt.getBestCmap() or {}

    # getBestCmap returns {codepoint: glyph_name}; we only need the keys.
    return frozenset(cmap.keys())
