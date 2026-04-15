"""Convenience ``draw_text`` function for one-shot text rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, overload

from PIL import Image
from pilmoji.source import BaseSource, Twemoji

from fontstack.gradient import _GRADIENT_ANGLE
from fontstack.manager import FontManager
from fontstack.types import (
    _UNBOUNDED_WIDTH,
    FillType,
    FontConfig,
    HorizontalAlign,
    RenderMode,
)

# draw_text overloads
# --------------------
# Three orthogonal dimensions produce 12 signatures:
#
#   source dimension
#   ----------------
#   A (overloads  1- 4): font_stack: list[FontConfig]  required  - no manager/font_dir needed
#   B (overloads  5- 8): manager: FontManager           required  - font_stack optional
#   C (overloads  9-12): font_dir: str | Path            required  - font_stack/manager optional
#
#   mode dimension (all groups)
#   ----------------------------
#   x/1  mode="wrap"       - min_size absent (no effect in wrap mode)
#   x/2  mode="scale"      - min_size present
#   x/3  mode="fit"        - min_size + max_height present
#   x/4  mode=RenderMode   - generic runtime-value fallback


# --- Group A: font_stack required, manager optional ---


# Overload 1/8 - font_stack required, mode="wrap"
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig],
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: Literal["wrap"] = ...,
    max_width: int | None = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path | None = ...,
    manager: FontManager | None = ...,
) -> Image.Image: ...


# Overload 2/8 - font_stack required, mode="scale"
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig],
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: Literal["scale"] = ...,
    max_width: int | None = ...,
    min_size: int = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path | None = ...,
    manager: FontManager | None = ...,
) -> Image.Image: ...


# Overload 3/8 - font_stack required, mode="fit"
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig],
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: Literal["fit"] = ...,
    max_width: int | None = ...,
    max_height: int | None = ...,
    min_size: int = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path | None = ...,
    manager: FontManager | None = ...,
) -> Image.Image: ...


# Overload 4/8 - font_stack required, generic RenderMode fallback
# Catches calls where ``mode`` is a runtime ``RenderMode`` union value.
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig],
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: RenderMode = ...,
    max_width: int | None = ...,
    max_height: int | None = ...,
    min_size: int = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path | None = ...,
    manager: FontManager | None = ...,
) -> Image.Image: ...


# --- Group B: manager required, font_stack optional ---


# Overload 5/8 - manager required, mode="wrap"
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig] | None = ...,
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: Literal["wrap"] = ...,
    max_width: int | None = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path | None = ...,
    manager: FontManager,
) -> Image.Image: ...


# Overload 6/8 - manager required, mode="scale"
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig] | None = ...,
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: Literal["scale"] = ...,
    max_width: int | None = ...,
    min_size: int = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path | None = ...,
    manager: FontManager,
) -> Image.Image: ...


# Overload 7/8 - manager required, mode="fit"
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig] | None = ...,
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: Literal["fit"] = ...,
    max_width: int | None = ...,
    max_height: int | None = ...,
    min_size: int = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path | None = ...,
    manager: FontManager,
) -> Image.Image: ...


# Overload 8/8 - manager required, generic RenderMode fallback
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig] | None = ...,
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: RenderMode = ...,
    max_width: int | None = ...,
    max_height: int | None = ...,
    min_size: int = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path | None = ...,
    manager: FontManager,
) -> Image.Image: ...


# --- Group C: font_dir required, font_stack/manager optional ---


# Overload 9/12 - font_dir required, mode="wrap"
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig] | None = ...,
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: Literal["wrap"] = ...,
    max_width: int | None = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path,
    manager: FontManager | None = ...,
) -> Image.Image: ...


# Overload 10/12 - font_dir required, mode="scale"
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig] | None = ...,
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: Literal["scale"] = ...,
    max_width: int | None = ...,
    min_size: int = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path,
    manager: FontManager | None = ...,
) -> Image.Image: ...


# Overload 11/12 - font_dir required, mode="fit"
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig] | None = ...,
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: Literal["fit"] = ...,
    max_width: int | None = ...,
    max_height: int | None = ...,
    min_size: int = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path,
    manager: FontManager | None = ...,
) -> Image.Image: ...


# Overload 12/12 - font_dir required, generic RenderMode fallback
@overload
def draw_text(
    text: str,
    font_stack: list[FontConfig] | None = ...,
    *,
    size: int = ...,
    weight: int | str = ...,
    mode: RenderMode = ...,
    max_width: int | None = ...,
    max_height: int | None = ...,
    min_size: int = ...,
    align: HorizontalAlign = ...,
    line_spacing: float = ...,
    fill: FillType = ...,
    stroke_width: int = ...,
    stroke_fill: FillType | None = ...,
    shadow_color: FillType | None = ...,
    shadow_offset: tuple[int, int] = ...,
    gradient_angle: float = ...,
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    font_dir: str | Path,
    manager: FontManager | None = ...,
) -> Image.Image: ...


def draw_text(
    text: str,
    font_stack: list[FontConfig] | None = None,
    *,
    size: int = 40,
    weight: int | str = 400,
    mode: RenderMode = "wrap",
    max_width: int | None = None,
    max_height: int | None = None,
    min_size: int = 12,
    align: HorizontalAlign = "left",
    line_spacing: float = 1.2,
    fill: FillType = "black",
    stroke_width: int = 0,
    stroke_fill: FillType | None = None,
    shadow_color: FillType | None = None,
    shadow_offset: tuple[int, int] = (2, 2),
    gradient_angle: float = _GRADIENT_ANGLE,
    background: FillType = (0, 0, 0, 0),
    padding: int = 0,
    emoji_source: type[BaseSource] = Twemoji,
    font_dir: str | Path | None = None,
    manager: FontManager | None = None,
) -> Image.Image:
    """
    Render *text* and return a new PIL image sized to fit the result.

    Creates a :class:`FontManager` from *font_stack* (or reuses *manager* if
    provided), renders the text onto an oversized transparent canvas, crops the
    result to the exact pixel bounding box, adds *padding* on all sides, and
    composites onto *background*. When *manager* is passed, *font_stack* is
    ignored and the manager's caches are reused across calls, which makes this
    efficient for batch rendering::

        mgr = FontManager(default_stack=[FontConfig(path="fonts/NotoSans.ttf")])
        images = [draw_text(label, manager=mgr) for label in labels]

    Parameters
    ----------
    text:
        The string to render. BiDi reordering and Arabic reshaping are applied
        automatically. May contain emoji.
    font_stack:
        Ordered list of :class:`FontConfig` entries defining the fallback font
        stack. Ignored when *manager* is provided. May be omitted (``None``)
        when *font_dir* or *manager* is supplied.
    font_dir:
        Path to a directory of font files. When given, a :class:`FontManager`
        is constructed from the scanned directory via :func:`scan_font_dir`.
        Ignored when *manager* is provided.
    size:
        Initial font size in points. Defaults to ``40``.
    weight:
        Font weight - integer (e.g. ``700``) or named style string
        (e.g. ``"Bold"``). Defaults to ``400``.
    mode:
        ``"wrap"`` (word-wrap at *max_width*), ``"scale"`` (shrink to fit
        *max_width*), or ``"fit"`` (wrap then shrink to fit *max_height*).
        When *max_width* is ``None``, all modes render at full
        size with no constraint. Defaults to ``"wrap"``.
    max_width:
        Maximum pixel width for the text area. ``None`` means no constraint.
        Defaults to ``None``.
    max_height:
        Maximum pixel height for the text block. Only used in ``"fit"`` mode.
        ``None`` means no height constraint. Defaults to ``None``.
    min_size:
        Minimum font size floor for ``"scale"`` and ``"fit"`` modes.
        Defaults to ``12``.
    align:
        Horizontal alignment: ``"left"``, ``"center"``, or ``"right"``.
        Defaults to ``"left"``.
    line_spacing:
        Line height multiplier relative to *size*. Defaults to ``1.2``.
    fill:
        Text color. Accepts a Pillow color name, RGB tuple, RGBA tuple
        (e.g. ``(0, 0, 0, 128)`` for 50% opacity), or a dash-separated
        gradient string (e.g. ``"red-blue"``, ``"#FF0000-#00FF00"``).
        Gradients are slightly diagonal so multi-line text gets natural
        color variation. The preset ``"rainbow"`` expands to the seven
        spectral colors. Defaults to ``"black"``.
    stroke_width:
        Outline thickness in pixels around each glyph. ``0`` disables the
        outline. Defaults to ``0``.
    stroke_fill:
        Outline color. Accepts the same value types as *fill*, including
        gradient strings (e.g. ``"rainbow"``). ``None`` uses *fill* as
        the stroke color when *stroke_width* > 0. Defaults to ``None``.
    shadow_color:
        Drop-shadow color. Accepts the same value types as *fill*,
        including gradient strings. The shadow shape includes the outline
        when *stroke_width* > 0. ``None`` disables the shadow.
        Defaults to ``None``.
    shadow_offset:
        ``(x, y)`` pixel offset for the drop shadow. Defaults to ``(2, 2)``.
    gradient_angle:
        Gradient direction in degrees, clockwise from horizontal. ``0``
        produces a pure left-to-right gradient; the default ``15.0`` adds a
        slight diagonal so multi-line text gets natural color variation per
        line. Only used when *fill*, *stroke_fill*, or *shadow_color* is a
        gradient string. Defaults to ``15.0``.
    background:
        Background color of the returned image. Defaults to fully transparent
        ``(0, 0, 0, 0)``. Pass ``"white"`` or an RGB/RGBA tuple for an opaque
        background.
    padding:
        Uniform padding in pixels added to all four edges of the cropped
        result. Prevents glyphs from touching the image border. Defaults to
        ``0``.
    emoji_source:
        Pilmoji emoji source class. Defaults to
        :class:`~pilmoji.source.Twemoji`.
    manager:
        An existing :class:`FontManager` instance to reuse. When provided,
        *font_stack* is ignored and no new manager is constructed. Useful for
        batch rendering where cmap caches should be shared across calls.

    Returns
    -------
    Image.Image
        A new ``"RGBA"`` image cropped tightly to the rendered text with
        *padding* added on all sides and *background* filled behind the text.

    Raises
    ------
    ValueError
        If none of *font_stack*, *font_dir*, or *manager* provides a usable
        font configuration.

    Example
    -------
    ::

        img = draw_text(
            "Hello مرحبا 世界 🌍",
            font_stack=[
                FontConfig(path="fonts/NotoSans.ttf"),
                FontConfig(path="fonts/NotoSansCJK.ttc", ttc_index=0),
                FontConfig(path="fonts/NotoSansArabic.ttf"),
            ],
            size=48,
            weight=700,
            fill=(20, 20, 20),
            background="white",
            padding=16,
        )
        img.save("hello.png")
    """
    if manager is None:
        if font_dir is not None:
            manager = FontManager(font_dir=font_dir)
        elif font_stack:
            manager = FontManager(default_stack=font_stack)
        else:
            raise ValueError("Provide font_stack, font_dir, or a pre-built manager.")

    effective_width = max_width if max_width is not None else _UNBOUNDED_WIDTH

    # Canvas sizing strategy
    # ----------------------
    # The canvas is cropped to the actual bounding box after rendering, so its
    # exact dimensions only need to be *large enough* - they are not visible in
    # the output.  The two axes are handled differently:
    #
    # Width: when max_width is given, use it directly.  When unconstrained, use
    # a per-character heuristic: len(text) * size pixels is always >= the real
    # rendered width for any reasonable font (most glyphs are narrower than
    # their em-square), so we avoid allocating a 100 000-pixel-wide canvas for
    # short unconstrained strings.
    #
    # Height: size * 40 accommodates well over 30 lines at the default 1.2×
    # line spacing before the crop discards the blank space.
    #
    # stroke_width adds extra margin on every side; shadow_offset may push
    # pixels further right/down.  Both are accounted for in the canvas size
    # and the starting position so that no glyph edge is clipped.
    sw = stroke_width
    sx_off = max(shadow_offset[0], 0) if shadow_color is not None else 0
    sy_off = max(shadow_offset[1], 0) if shadow_color is not None else 0
    margin = sw + max(sx_off, sy_off)

    canvas_w = (
        (effective_width if max_width is not None else len(text) * size + 100)
        + 50
        + margin * 2
    )

    # Start rendering at (margin, size + margin) so that stroke expansion
    # and shadow offset never push pixels past the canvas edge.  The blank
    # rows around the text are removed by the getbbox() crop below.
    # In "fit" mode, cap canvas height to max_height (+ margin) when provided,
    # since content beyond that will be truncated anyway.
    canvas_h = (
        max_height + size + margin * 2
        if max_height is not None and mode == "fit"
        else size * 40
    )
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    manager.draw(
        image=canvas,
        text=text,
        position=(margin, size + margin),
        size=size,
        weight=weight,
        mode=mode,
        max_width=max_width,
        max_height=max_height,
        min_size=min_size,
        align=align,
        line_spacing=line_spacing,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
        shadow_color=shadow_color,
        shadow_offset=shadow_offset,
        gradient_angle=gradient_angle,
        emoji_source=emoji_source,
    )

    bbox = canvas.getbbox()
    if bbox is None:
        return Image.new("RGBA", (1, 1), background)

    left, top, right, bottom = bbox
    cropped = canvas.crop((left, top, right, bottom))

    pad_w = cropped.width + padding * 2
    pad_h = cropped.height + padding * 2
    result = Image.new("RGBA", (pad_w, pad_h), background)
    result.paste(cropped, (padding, padding), cropped)
    return result
