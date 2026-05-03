"""Shared type aliases, constants, and data classes used across the package."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, NamedTuple, TypedDict

from PIL import ImageFont

__all__ = [
    "Anchor",
    "FillType",
    "FontConfig",
    "HorizontalAlign",
    "RenderMode",
    "VariationAxes",
    "_RenderContext",
    "_Segment",
    "_UNBOUNDED_WIDTH",
]

# region Type aliases

# Pillow-compatible fill type: color name, L/RGB/RGBA tuple, or palette integer.
# Dash-separated color strings (e.g. ``"red-blue"``, ``"#FF0000-#00FF00-#0000FF"``)
# are interpreted as linear gradients (slightly diagonal by default).  The preset
# ``"rainbow"`` expands to ``"red-orange-yellow-green-blue-indigo-violet"``.
# Gradient strings are accepted by *fill*, *stroke_fill*, and *shadow_color*.
FillType = str | int | tuple[int, int, int] | tuple[int, int, int, int]

# Rendering mode: word-wrap or shrink-to-fit.
RenderMode = Literal["wrap", "scale", "fit"]

# Horizontal alignment within the text block.
HorizontalAlign = Literal["left", "center", "right"]

# Anchor point for positioning a text block at a given coordinate.
# Two-character PIL-style code: horizontal (l/m/r) + vertical (t/m/b).
# ``"lt"`` (top-left, the default) is backward-compatible with the
# ``position`` argument having always referred to the top-left corner.
Anchor = Literal["lt", "mt", "rt", "lm", "mm", "rm", "lb", "mb", "rb"]

# Sentinel used as an unconstrained width budget.  Using a finite number avoids
# None-checks throughout the layout and measurement code while keeping all
# comparisons valid.  The value (99,999 px) comfortably exceeds any real display
# dimension; it is never used to allocate memory directly.
_UNBOUNDED_WIDTH: int = 99_999

# endregion


# region Data classes


class VariationAxes(TypedDict, total=False):
    """OpenType variable-font axis overrides.

    Each key is a registered axis tag and the value is the desired
    position on that axis.  Only the axes listed here are set; all
    others keep their font-defined defaults.

    Commonly used axes:

    ``wght``
        Weight axis (100 = Thin … 400 = Regular … 700 = Bold … 900 = Black).
    ``wdth``
        Width axis (percentage of normal width, e.g. 75 = Condensed, 100 = Normal).
    ``ital``
        Italic axis (0 = Upright, 1 = Italic).
    ``slnt``
        Slant axis (degrees of counter-clockwise slant, e.g. -12).
    ``opsz``
        Optical-size axis (intended point size for optical compensation).
    """

    wght: float
    wdth: float
    ital: float
    slnt: float
    opsz: float


@dataclass
class FontConfig:
    """
    Configuration for a single font entry in a fallback stack.

    Parameters
    ----------
    path : str
        Absolute or relative path to a TTF, OTF, TTC, or OTC font file.
    axes : VariationAxes or None, optional
        Default variable-font axis values applied when loading this font.
        The ``weight`` argument passed to rendering methods always overrides
        the ``wght`` axis specifically. See :class:`VariationAxes` for the
        full list of standard axes. Defaults to ``None``.
    ttc_index : int, optional
        Zero-based index of the desired font within a TrueType Collection
        (``.ttc`` / ``.otc``) file. Ignored for non-collection files.
        Defaults to ``0``.

    Examples
    --------
    Basic font entry::

        FontConfig(path="fonts/NotoSans[wdth,wght].ttf")

    Variable font with custom default axes::

        FontConfig(
            path="fonts/NotoSans[wdth,wght].ttf",
            axes=VariationAxes(wght=300.0, wdth=75.0),
        )

    Font from a TrueType Collection::

        FontConfig(path="fonts/NotoSansCJK.ttc", ttc_index=2)
    """

    path: str
    axes: VariationAxes | None = None
    ttc_index: int = 0


# endregion


# region Internal named tuples


class _Segment(NamedTuple):
    """A run of text and the resolved Pillow font to draw it with."""

    text: str
    font: ImageFont.FreeTypeFont


class _RenderContext(NamedTuple):
    """
    Immutable bundle of resolved rendering inputs shared across one draw call.

    Created once per :meth:`FontManager.draw` invocation (and once
    per size step in ``"scale"``/``"fit"`` modes) by
    :meth:`FontManager._resolve_context`, then threaded through every internal
    helper so that ``get_font_chain`` and its expensive ``_stack_hash`` are
    each called exactly once per size rather than once per character.

    Attributes
    ----------
    stack:
        The resolved :class:`FontConfig` list for this call (either the
        caller-supplied ``font_stack`` override or the manager's
        ``default_stack``).
    chain:
        Loaded :class:`~PIL.ImageFont.FreeTypeFont` objects corresponding
        one-to-one with ``stack``, already sized and weight-configured.
    size:
        The font size (points) at which ``chain`` was loaded. Stored so that
        the fallback heuristic in :meth:`_measure_text` can scale correctly
        when ``getlength`` raises.
    """

    stack: list[FontConfig]
    chain: list[ImageFont.FreeTypeFont]
    size: int


# endregion
