"""Bidirectional text preparation (Arabic reshaping + BiDi reordering)."""

from __future__ import annotations

import arabic_reshaper
from bidi.algorithm import get_display

__all__ = ["_prepare_bidi"]


def _prepare_bidi(text: str) -> str:
    """
    Apply Arabic reshaping (contextual letter forms) and the Unicode
    Bidirectional Algorithm to *text*, making it safe to pass to a
    left-to-right renderer such as Pillow/Pilmoji.

    Arabic characters in their base (isolated) Unicode codepoints are first
    converted to the correct initial/medial/final/isolated presentation forms
    by ``arabic-reshaper``. The result is then visually reordered for
    left-to-right rendering by ``python-bidi``.

    For purely LTR text this is a no-op.

    Parameters
    ----------
    text:
        Raw input string, potentially containing Arabic/Hebrew/mixed-direction
        content.

    Returns
    -------
    str
        Display-ready string with correct visual character order.
    """
    text = arabic_reshaper.reshape(text)
    # get_display returns StrOrBytes; the rendered result is always a str here.
    return str(get_display(text))
