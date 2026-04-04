"""
fontstack._core
===============
Utilities for rendering Unicode text onto PIL images with automatic per-character
font fallback, bidirectional (BiDi) text support, Arabic reshaping, TrueType
Collection (.ttc/.otc) support, and Twemoji/Pilmoji emoji rendering.

Typical usage
-------------
::

    from fontstack import FontManager, FontConfig, draw_text
    from PIL import Image

    # --- Using FontManager directly (full control) ---
    manager = FontManager(
        default_stack=[
            FontConfig(path="fonts/NotoSans.ttf"),
            FontConfig(path="fonts/NotoSansCJK.ttc", ttc_index=0),
            FontConfig(path="fonts/NotoSansArabic.ttf"),
        ]
    )

    img = Image.new("RGBA", (800, 200), "white")
    w, h = manager.draw(
        image=img,
        text="Hello 世界 مرحبا 🌍",
        position=(50, 80),
        size=48,
        weight=700,
        mode="wrap",
        max_width=700,
        fill=(30, 30, 30),
    )

    # --- Using draw_text (zero-setup convenience) ---
    img2 = draw_text(
        text="Hello 世界 مرحبا 🌍",
        font_stack=[
            FontConfig(path="fonts/NotoSans.ttf"),
            FontConfig(path="fonts/NotoSansCJK.ttc", ttc_index=0),
        ],
        size=48,
        padding=20,
        fill=(30, 30, 30),
        background="white",
    )
    img2.save("output.png")

    # --- Reusing a manager across many draw_text calls (avoids re-parsing cmaps) ---
    manager = FontManager(default_stack=[FontConfig(path="fonts/NotoSans.ttf")])
    for label in labels:
        img = draw_text(label, manager=manager, size=32)
"""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from dataclasses import asdict, dataclass
from typing import Literal, NamedTuple, TypedDict, overload

import arabic_reshaper
from bidi.algorithm import get_display
from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection
from PIL import Image, ImageFont
from pilmoji import EMOJI_REGEX, Pilmoji
from pilmoji.source import BaseSource, Twemoji

# Pillow-compatible fill type: color name, L/RGB/RGBA tuple, or palette integer.
FillType = str | int | tuple[int, int, int] | tuple[int, int, int, int]

# Rendering mode: word-wrap or shrink-to-fit.
RenderMode = Literal["wrap", "scale", "fit"]

# Horizontal alignment within the text block.
HorizontalAlign = Literal["left", "center", "right"]

# Sentinel used as an unconstrained width budget.  Using a finite number avoids
# None-checks throughout the layout and measurement code while keeping all
# comparisons valid.  The value (99,999 px) comfortably exceeds any real display
# dimension; it is never used to allocate memory directly.
_UNBOUNDED_WIDTH: int = 99_999


# region Data types


class VariationAxes(TypedDict, total=False):
    """
    Standard OpenType variation axes for variable fonts.

    All fields are optional (``total=False``). Non-standard axes such as
    ``"YTLC"`` cannot be expressed in this TypedDict but will still pass
    through to Pillow at runtime.

    Attributes
    ----------
    wght : float
        Weight axis. Typical range 100–900. ``400`` is Regular, ``700`` is Bold.
    wdth : float
        Width axis. Typical range 50–200. ``100`` is normal width.
    ital : float
        Italic axis. ``0`` is upright, ``1`` is italic.
    slnt : float
        Slant axis in degrees. Negative values lean right (e.g. ``-12``).
    opsz : float
        Optical size axis. Should match the intended display size in points
        (e.g. ``12``, ``24``, ``72``).
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


class _Segment(NamedTuple):
    """A contiguous run of text characters that all map to the same PIL font."""

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


# region cmap helpers (fonttools-backed)


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


# endregion


# region BiDi helpers


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


# endregion


# region FontManager


class FontManager:
    """
    Manages a prioritized fallback stack of fonts and renders Unicode text
    onto PIL images, including emoji, Arabic/RTL script, and CJK.

    How fallback works
    ------------------
    Each character in a string is assigned to the first font in the stack
    whose cmap contains that codepoint. Emoji are always pinned to the
    *primary* (index-0) font because Pilmoji intercepts and rasterises them
    independently; routing them to a fallback font would corrupt the baseline
    correction applied during rendering.

    TTC support
    -----------
    Font collection files (`.ttc`, `.otc`) are supported via the
    ``ttc_index`` key in :class:`FontConfig`. Each TTC entry is treated as a
    normal font; the manager reads the cmap of the specified member and loads
    it through Pillow using the same index.

    BiDi / RTL support
    ------------------
    All text is automatically processed before rendering. Arabic is reshaped
    with ``arabic-reshaper`` to produce the correct contextual letter forms
    (initial, medial, final, isolated), then passed through ``python-bidi``
    for Unicode BiDi reordering. This makes Arabic render correctly under
    Pillow's BASIC layout engine.

    Caching
    -------
    Font objects and cmap data are LRU-cached internally. Repeated calls
    with the same ``(stack, size, weight)`` triple are essentially free.

    Parameters
    ----------
    default_stack:
        Ordered list of :class:`FontConfig` entries. The first item is the
        primary font; subsequent entries are tried in order when the primary
        lacks a glyph for a given character.
    max_cache:
        Maximum number of ``(stack, size, weight)`` entries to keep in the
        font-object LRU cache. Older entries are evicted when the cache is
        full. Defaults to ``30``.

    Example
    -------
    ::

        manager = FontManager(
            default_stack=[
                FontConfig(path="fonts/NotoSans.ttf"),
                FontConfig(path="fonts/NotoSansCJK.ttc", ttc_index=0),
                FontConfig(path="fonts/NotoSansArabic.ttf"),
            ]
        )
        img = Image.new("RGBA", (800, 100), "white")
        manager.draw(img, "Hello مرحبا 世界", position=(10, 20), size=40)
    """

    def __init__(
        self,
        default_stack: list[FontConfig],
        max_cache: int = 30,
    ) -> None:
        if not default_stack:
            raise ValueError("default_stack must contain at least one FontConfig.")

        self._default_stack = default_stack
        self._max_cache = max_cache
        # LRU cache keyed by (stack_hash, size, weight).
        self._font_cache: OrderedDict[tuple, list[ImageFont.FreeTypeFont]] = (
            OrderedDict()
        )
        # cmap cache keyed by (path, ttc_index), populated lazily on first use.
        self._cmap_cache: dict[tuple[str, int], frozenset[int]] = {}

    # region Public properties

    @property
    def default_stack(self) -> list[FontConfig]:
        """The fallback font stack supplied at construction time (read-only copy)."""
        return list(self._default_stack)

    # endregion

    # region Internal helpers - cmap & font loading

    def _get_cmap(self, config: FontConfig) -> frozenset[int]:
        """Return the cached (or freshly parsed) cmap for the font in *config*."""
        key = (config.path, config.ttc_index)
        if key not in self._cmap_cache:
            self._cmap_cache[key] = _load_cmap(config.path, config.ttc_index)
        return self._cmap_cache[key]

    def _font_has_glyph(self, config: FontConfig, char: str) -> bool:
        """Return ``True`` if the font described by *config* contains *char*."""
        return ord(char) in self._get_cmap(config)

    @staticmethod
    def _stack_hash(stack: list[FontConfig]) -> str:
        """Produce a stable MD5 hex-digest for a font stack (used as cache key)."""
        return hashlib.md5(
            json.dumps([asdict(c) for c in stack], sort_keys=True).encode(),
            usedforsecurity=False,
        ).hexdigest()

    def get_font_chain(
        self,
        size: int,
        weight: int | str = 400,
        custom_stack: list[FontConfig] | None = None,
    ) -> list[ImageFont.FreeTypeFont]:
        """
        Return a list of loaded :class:`~PIL.ImageFont.FreeTypeFont` objects for each
        entry in the active stack at the given size and weight.
        The result is LRU-cached so subsequent calls with the same arguments
        are essentially free.

        Parameters
        ----------
        size:
            Point size passed to :func:`PIL.ImageFont.truetype`.
        weight:
            Font weight. Can be an integer (e.g. ``400``, ``700``) which sets
            the ``wght`` variation axis, or a named style string (e.g.
            ``"Bold"``) passed to
            :meth:`~PIL.ImageFont.FreeTypeFont.set_variation_by_name`. For
            static (non-variable) fonts the weight parameter is silently
            ignored.
        custom_stack:
            Override the instance's ``default_stack`` for this call only.
            Useful when rendering a single text element with a bespoke font
            combination without affecting the manager's default behaviour.

        Returns
        -------
        list[ImageFont.FreeTypeFont]
            One loaded font object per stack entry, in the same order as the
            stack.
        """
        stack = custom_stack or self._default_stack
        cache_key = (self._stack_hash(stack), size, weight)

        if cache_key in self._font_cache:
            self._font_cache.move_to_end(cache_key)
            return self._font_cache[cache_key]

        chain: list[ImageFont.FreeTypeFont] = []
        for config in stack:
            font = ImageFont.truetype(
                config.path,
                size,
                index=config.ttc_index,
                layout_engine=ImageFont.Layout.BASIC,
            )

            if isinstance(weight, int):
                axes: dict[str, float] = dict(config.axes or {})  # type: ignore[assignment]
                axes["wght"] = float(weight)
                try:
                    font.set_variation_by_axes(list(axes.values()))
                except (OSError, AttributeError, TypeError):
                    # Axis order may differ; rebuild from the font's own axis metadata.
                    # Pillow's Axis TypedDict exposes minimum/default/maximum/name but
                    # not "tag" (present at runtime, absent from the stub), so we read
                    # each axis via a plain-dict cast to avoid false type errors.
                    try:
                        available = font.get_variation_axes()
                        coords: list[float] = []
                        for a in available:
                            raw: dict[str, object] = a  # type: ignore[assignment]
                            tag = str(raw.get("tag", ""))
                            _d = raw.get("default")
                            default = float(_d) if isinstance(_d, (int, float)) else 0.0
                            coords.append(axes.get(tag, default))
                        font.set_variation_by_axes(coords)
                    except Exception:
                        # Static font or unsupported variable font - skip silently.
                        pass
            elif isinstance(weight, str):
                try:
                    font.set_variation_by_name(weight)
                except (OSError, AttributeError):
                    pass

            chain.append(font)

        if len(self._font_cache) >= self._max_cache:
            self._font_cache.popitem(last=False)
        self._font_cache[cache_key] = chain
        return chain

    def _resolve_context(
        self,
        size: int,
        weight: int | str,
        font_stack: list[FontConfig] | None,
    ) -> _RenderContext:
        """
        Build a :class:`_RenderContext` for one render pass at a given size.

        Resolves the active stack (``font_stack`` override or ``default_stack``)
        and calls :meth:`get_font_chain` exactly once, returning a bundle that
        internal helpers can share without repeating the stack hash or font
        lookup.

        This is the single place where the expensive per-call work happens:
        ``get_font_chain`` serialises the stack to JSON, computes an MD5 key,
        and either returns a cached chain or loads and configures every font.
        Callers in the hot path (segmentation, measurement) receive the
        resolved chain directly and never pay that cost again.

        Parameters
        ----------
        size:
            Font size in points. Passed through to :meth:`get_font_chain`.
        weight:
            Font weight (integer axis value or named style string). Passed
            through to :meth:`get_font_chain`.
        font_stack:
            Optional per-call stack override. ``None`` falls back to
            ``self._default_stack``.

        Returns
        -------
        _RenderContext
            Resolved stack, loaded chain, and size bundled for the call.
        """
        stack = font_stack or self._default_stack
        chain = self.get_font_chain(size, weight, font_stack)
        return _RenderContext(stack=stack, chain=chain, size=size)

    # endregion

    # region Internal helpers - per-character font selection & segmentation

    def _get_font_for_char(
        self,
        char: str,
        ctx: _RenderContext,
    ) -> ImageFont.FreeTypeFont:
        """
        Return the best loaded font for a single character.

        Emoji (as detected by Pilmoji's ``EMOJI_REGEX``) are always pinned to
        the primary font regardless of which font actually contains the glyph,
        because Pilmoji renders them independently and tying them to a fallback
        font would corrupt the baseline offset calculation in
        :meth:`draw`.

        For all other characters the stack is walked in order and the first
        font whose cmap contains the codepoint is returned. The primary font
        is used as a final fallback if no font covers the character (renders
        as a .notdef box, which is the best we can do).

        Parameters
        ----------
        char:
            The single character to look up.
        ctx:
            Resolved render context from :meth:`_resolve_context`. Both
            ``ctx.stack`` and ``ctx.chain`` are used directly - no further
            ``get_font_chain`` call is made.
        """
        if EMOJI_REGEX.match(char):
            return ctx.chain[0]

        for config, font in zip(ctx.stack, ctx.chain, strict=True):
            if self._font_has_glyph(config, char):
                return font

        return ctx.chain[0]

    def _segment_text(
        self,
        text: str,
        ctx: _RenderContext,
    ) -> list[_Segment]:
        """
        Split *text* into a list of :class:`_Segment` named tuples, where each
        segment is a contiguous run of characters that all map to the same font.

        Grouping characters into runs (rather than calling Pilmoji character by
        character) preserves Pilmoji's internal emoji-tracking state and
        produces correct kerning within each font-fallback run.

        Parameters
        ----------
        text:
            The string to segment. Should already be BiDi-reordered.
        ctx:
            Resolved render context. Passed through to
            :meth:`_get_font_for_char`, which reads ``ctx.stack`` and
            ``ctx.chain`` directly without any further font loading.

        Returns
        -------
        list[_Segment]
            Empty list if *text* is empty.
        """
        if not text:
            return []

        segments: list[_Segment] = []
        current_font = self._get_font_for_char(text[0], ctx)
        current_run = text[0]

        for char in text[1:]:
            font = self._get_font_for_char(char, ctx)
            if font is current_font:
                current_run += char
            else:
                segments.append(_Segment(current_run, current_font))
                current_run = char
                current_font = font

        segments.append(_Segment(current_run, current_font))
        return segments

    def _measure_text(
        self,
        text: str,
        ctx: _RenderContext,
    ) -> float:
        """
        Return the total pixel width of *text* using per-segment font
        measurement, without drawing anything.

        Calls :meth:`_segment_text` to group characters into font-homogeneous
        runs, then measures each run as a whole with
        :meth:`~PIL.ImageFont.FreeTypeFont.getlength`. This reduces the number
        of ``getlength`` calls from O(characters) to O(segments) - typically
        1–3 for mixed-script text - while still producing accurate per-font
        widths.

        Falls back to ``ctx.size * 0.6 * len(segment.text)`` for any segment
        whose font raises from ``getlength`` (e.g. certain bitmap or corrupted
        fonts).

        Parameters
        ----------
        text:
            The string to measure. Should already be BiDi-reordered.
        ctx:
            Resolved render context from :meth:`_resolve_context`.
        """
        total = 0.0
        for segment in self._segment_text(text, ctx):
            try:
                total += segment.font.getlength(segment.text)
            except Exception:
                total += ctx.size * 0.6 * len(segment.text)
        return total

    def _wrap_lines(
        self,
        text: str,
        ctx: _RenderContext,
        effective_width: int,
    ) -> list[str]:
        """
        Split *text* into a list of word-wrapped lines that each fit within
        *effective_width* pixels at the size and weight encoded in *ctx*.

        Words are split on ASCII spaces. A single word that is wider than
        *effective_width* is placed on its own line and will overflow without
        truncation (consistent with ``"wrap"`` mode's documented behaviour).

        Parameters
        ----------
        text:
            The BiDi-reordered string to wrap.
        ctx:
            Resolved render context for the current font size/weight. Passed
            through to :meth:`_measure_text`.
        effective_width:
            Maximum pixel width per line. Use :data:`_UNBOUNDED_WIDTH` when
            there is no constraint.

        Returns
        -------
        list[str]
            Ordered list of line strings. Never empty (at least one element
            when *text* is non-empty).
        """
        words = text.split(" ")
        current_line: list[str] = []
        lines: list[str] = []

        for word in words:
            test_line = " ".join(current_line + [word])
            if self._measure_text(test_line, ctx) <= effective_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    # endregion

    # region Public rendering API

    # Overload 1/3 - ``mode="wrap"`` (default)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ``min_size`` is intentionally absent. In wrap mode the rendered font size
    # never changes; text is simply broken across lines at whitespace.
    # Exposing ``min_size`` here would be misleading, as it has no effect.
    @overload
    def draw(
        self,
        image: Image.Image,
        text: str,
        position: tuple[int, int],
        *,
        size: int = ...,
        weight: int | str = ...,
        mode: Literal["wrap"] = ...,
        max_width: int | None = ...,
        align: HorizontalAlign = ...,
        line_spacing: float = ...,
        fill: FillType = ...,
        font_stack: list[FontConfig] | None = ...,
        emoji_source: type[BaseSource] = ...,
    ) -> tuple[int, int]: ...

    # Overload 2/3 - ``mode="scale"``
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ``min_size`` is present: scale mode shrinks the font in 2-point steps
    # down to ``min_size`` before truncating with an ellipsis. Type checkers
    # and IDEs surface ``min_size`` in autocomplete only when the caller
    # explicitly writes ``mode="scale"``.
    @overload
    def draw(
        self,
        image: Image.Image,
        text: str,
        position: tuple[int, int],
        *,
        size: int = ...,
        weight: int | str = ...,
        mode: Literal["scale"] = ...,
        max_width: int | None = ...,
        min_size: int = ...,
        align: HorizontalAlign = ...,
        line_spacing: float = ...,
        fill: FillType = ...,
        font_stack: list[FontConfig] | None = ...,
        emoji_source: type[BaseSource] = ...,
    ) -> tuple[int, int]: ...

    # Overload 3/4 - ``mode="fit"``
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ``min_size`` and ``max_height`` are both present: fit mode wraps text at
    # *max_width*, then shrinks the font until the wrapped block fits within
    # *max_height*, and finally truncates the last line with ``…`` if even
    # *min_size* is not enough.  Both parameters are surfaced by type checkers
    # only when the caller explicitly writes ``mode="fit"``.
    @overload
    def draw(
        self,
        image: Image.Image,
        text: str,
        position: tuple[int, int],
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
        font_stack: list[FontConfig] | None = ...,
        emoji_source: type[BaseSource] = ...,
    ) -> tuple[int, int]: ...

    # Overload 4/4 - generic ``RenderMode`` fallback
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Catches calls where ``mode`` is a runtime ``RenderMode`` union value
    # (e.g. a variable forwarded from an outer scope). Both ``min_size`` and
    # all other parameters are present so the type checker can resolve the call
    # without ambiguity. This overload is never chosen when the caller passes a
    # string literal; overloads 1–3 take priority.
    @overload
    def draw(
        self,
        image: Image.Image,
        text: str,
        position: tuple[int, int],
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
        font_stack: list[FontConfig] | None = ...,
        emoji_source: type[BaseSource] = ...,
    ) -> tuple[int, int]: ...

    def draw(
        self,
        image: Image.Image,
        text: str,
        position: tuple[int, int],
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
        font_stack: list[FontConfig] | None = None,
        emoji_source: type[BaseSource] = Twemoji,
    ) -> tuple[int, int]:
        """
        Draw *text* onto *image* with automatic per-character font fallback,
        BiDi/Arabic support, and emoji rendering, then return the pixel dimensions
        of the rendered bounding box.

        Before any measuring or drawing, *text* is reshaped and BiDi-reordered
        by :func:`_prepare_bidi`, making mixed-direction strings render correctly
        in Pillow's left-to-right model. Text is rendered into a transparent RGBA
        overlay first, then composited onto *image*, which prevents anti-aliasing
        artifacts on non-white backgrounds.

        Parameters
        ----------
        image:
            The target :class:`~PIL.Image.Image`. Modified **in place**.
            ``"RGBA"`` mode is recommended; other modes composite correctly
            but may lose transparency.
        text:
            The string to render. May contain any Unicode codepoints, emoji
            sequences, or Arabic/Hebrew/mixed-direction content. BiDi
            reordering and reshaping are applied automatically.
        position:
            ``(x, y)`` pixel coordinate of the **visual top-left corner** of
            the text block. Corrects for the font's internal bounding-box
            offset so this maps to visible pixels, not FreeType's internal
            origin.
        size:
            Initial font size in points. In ``"scale"`` mode this may be
            reduced; in ``"wrap"`` mode it is used as-is for all lines.
            Defaults to ``40``.
        weight:
            Font weight. Integer (e.g. ``700``) sets the ``wght`` variable
            axis; a string (e.g. ``"Bold"``) calls
            :meth:`~PIL.ImageFont.FreeTypeFont.set_variation_by_name`. Static
            fonts ignore this silently. Defaults to ``400``.
        mode:
            Rendering mode. One of:

            ``"wrap"``
                Word-wrap the text at *max_width*. Lines are spaced at
                ``size * line_spacing`` pixels. A single word wider than
                *max_width* will overflow without truncation. When
                *max_width* is ``None``, the text renders as a single line
                with no wrapping.

            ``"scale"``
                Shrink the font in 2pt steps down to *min_size* until the
                text fits within *max_width*. If it still overflows, characters
                are truncated with an ellipsis. When *max_width* is ``None``,
                the text renders at full *size* with no scaling.

            ``"fit"``
                Word-wrap at *max_width* first (like ``"wrap"``), then shrink
                the font in 2pt steps until the wrapped text block fits within
                *max_height*. If the block still overflows at *min_size*, lines
                that do not fit are dropped and the last kept line is truncated
                with an ellipsis. When *max_height* is ``None``, this mode
                behaves identically to ``"wrap"``.

            Defaults to ``"wrap"``.
        max_width:
            Maximum pixel width for the text area. ``None`` means no
            constraint. Defaults to ``None``.
        max_height:
            Maximum pixel height for the text block. Only used in ``"fit"``
            mode. ``None`` means no height constraint. Defaults to ``None``.
        min_size:
            Minimum font size (points) used as the floor in ``"scale"`` and
            ``"fit"`` modes. Ignored in ``"wrap"`` mode. Defaults to ``12``.
        align:
            Horizontal alignment of lines within the text block. One of
            ``"left"``, ``"center"``, or ``"right"``. Only affects multi-line
            ``"wrap"`` output; single-line text always starts at *position*.
            Defaults to ``"left"``.
        line_spacing:
            Line height multiplier relative to *size*. ``1.2`` means each
            line's top is ``size * 1.2`` pixels below the previous line's top.
            Increase for scripts with tall diacritics (e.g. Arabic tashkeel).
            Defaults to ``1.2``.
        fill:
            Text color. Accepts a Pillow color name (``"red"``), an RGB
            tuple (``(255, 0, 0)``), an RGBA tuple (``(255, 0, 0, 128)`` for
            50% opacity), or an integer for palette/grayscale images. Defaults
            to ``"black"``.
        font_stack:
            Override the instance's :attr:`default_stack` for this call only.
        emoji_source:
            Pilmoji emoji image source **class** (not instance). Defaults to
            :class:`~pilmoji.source.Twemoji`.

        Returns
        -------
        tuple[int, int]
            ``(width, height)`` of the tightest bounding box around the
            actually-drawn pixels, ignoring all font internal padding. Returns
            ``(0, 0)`` if nothing was drawn (e.g. empty string).

        Raises
        ------
        ValueError
            If *mode* is not ``"wrap"``, ``"scale"``, or ``"fit"``.
        ValueError
            If *align* is not ``"left"``, ``"center"``, or ``"right"``.
        """
        if mode not in {"wrap", "scale", "fit"}:
            raise ValueError(f"mode must be 'wrap', 'scale', or 'fit', got {mode!r}.")
        if align not in {"left", "center", "right"}:
            raise ValueError(
                f"align must be 'left', 'center', or 'right', got {align!r}."
            )

        if not text:
            return (0, 0)

        # Apply Arabic reshaping and BiDi reordering before any measurement or
        # rendering.
        text = _prepare_bidi(text)

        # Treat None max_width as unconstrained - a very large number avoids
        # special-casing it throughout the measurement and layout code.
        effective_width = max_width if max_width is not None else _UNBOUNDED_WIDTH

        # Resolve the font chain once for the initial size.  Internal helpers
        # (_measure_text, _segment_text) accept this context directly so that
        # _stack_hash / get_font_chain are never called more than once per size.
        ctx = self._resolve_context(size, weight, font_stack)

        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))

        with Pilmoji(overlay, source=emoji_source) as pilmoji:
            x_start, y = position

            def draw_line(
                line: str,
                y_pos: int,
                draw_ctx: _RenderContext,
                line_width: float,
            ) -> None:
                """
                Draw a single pre-BiDi-reordered line at the given vertical
                position, honouring the *align* setting.

                *line_width* is the pre-measured pixel width of *line*,
                passed in to avoid measuring it twice.

                *draw_ctx* is the :class:`_RenderContext` for the current font
                size; it supplies the primary font (``draw_ctx.chain[0]``) for
                baseline metrics and is forwarded to :meth:`_segment_text`.

                Applies a bounding-box correction so that *y_pos* is the
                **visual** top of the glyphs rather than the FreeType origin
                (which includes internal ascender padding). Each font-fallback
                segment is vertically aligned to the shared baseline of the
                primary font.
                """
                # Compute x offset for alignment within the text block width.
                if align == "center":
                    x = x_start + (effective_width - line_width) // 2
                elif align == "right":
                    x = x_start + effective_width - int(line_width)
                else:
                    x = x_start

                primary = draw_ctx.chain[0]
                primary_ascent = primary.getmetrics()[0]

                # bbox[1] is the internal top-padding above the visual cap-height.
                # Subtracting it makes y_pos the true visual top of the text.
                visual_top_offset = primary.getbbox("A")[1]
                corrected_y = y_pos - visual_top_offset
                baseline = corrected_y + primary_ascent

                for segment in self._segment_text(line, draw_ctx):
                    font_ascent = segment.font.getmetrics()[0]
                    font_y = baseline - font_ascent

                    # Pilmoji positions emoji relative to the text origin it
                    # receives; compensate for our vertical shift so emoji land
                    # on the visual baseline.
                    emoji_y_correction = font_y - corrected_y

                    pilmoji.text(
                        (int(x), int(font_y)),
                        segment.text,
                        font=segment.font,
                        fill=fill,
                        emoji_position_offset=(0, int(-emoji_y_correction)),
                    )
                    x += pilmoji.getsize(segment.text, font=segment.font)[0]

            if mode == "scale":
                # Shrink font in 2pt steps until text fits or we hit min_size.
                # _resolve_context is called once per step; get_font_chain returns
                # the cached chain for any size we've seen before.
                current_size = size
                while current_size > min_size:
                    if self._measure_text(text, ctx) <= effective_width:
                        break
                    current_size -= 2
                    ctx = self._resolve_context(current_size, weight, font_stack)

                display_text = text
                if self._measure_text(display_text, ctx) > effective_width:
                    while display_text:
                        display_text = display_text[:-1]
                        candidate = display_text + "..."
                        if self._measure_text(candidate, ctx) <= effective_width:
                            display_text = candidate
                            break
                    else:
                        display_text = (
                            "..."
                            if self._measure_text("...", ctx) <= effective_width
                            else ""
                        )

                if display_text:
                    w = self._measure_text(display_text, ctx)
                    draw_line(display_text, y, ctx, w)

            elif mode == "wrap":
                lines = self._wrap_lines(text, ctx, effective_width)

                for i, line in enumerate(lines):
                    w = self._measure_text(line, ctx)
                    draw_line(line, y, ctx, w)
                    if i < len(lines) - 1:
                        y += int(size * line_spacing)

            elif mode == "fit":
                # Phase 1: shrink the font in 2pt steps until the wrapped block
                # fits within max_height (or we reach min_size).
                # _resolve_context is O(1) after the first call for each size
                # because get_font_chain is LRU-cached.
                current_size = size
                effective_height = (
                    max_height if max_height is not None else _UNBOUNDED_WIDTH
                )

                while current_size > min_size:
                    ctx = self._resolve_context(current_size, weight, font_stack)
                    lines = self._wrap_lines(text, ctx, effective_width)
                    total_h = (len(lines) - 1) * int(
                        current_size * line_spacing
                    ) + current_size
                    if total_h <= effective_height:
                        break
                    current_size -= 2
                else:
                    # Reached min_size - compute the final wrap one last time.
                    ctx = self._resolve_context(current_size, weight, font_stack)
                    lines = self._wrap_lines(text, ctx, effective_width)

                # Phase 2: if the block still overflows, drop lines that don't
                # fit and truncate the last kept line with "…".
                line_step = int(current_size * line_spacing)
                kept: list[str] = []
                for i, line in enumerate(lines):
                    top_of_line = i * line_step
                    bottom_of_line = top_of_line + current_size
                    if bottom_of_line <= effective_height:
                        kept.append(line)
                    else:
                        # This line falls outside the box - truncate the previous
                        # line with an ellipsis and stop.
                        if kept:
                            last = kept[-1]
                            while last:
                                candidate = last + "..."
                                if (
                                    self._measure_text(candidate, ctx)
                                    <= effective_width
                                ):
                                    kept[-1] = candidate
                                    break
                                last = last[:-1]
                            else:
                                kept[-1] = "..."
                        break

                for i, line in enumerate(kept):
                    w = self._measure_text(line, ctx)
                    draw_line(line, y, ctx, w)
                    if i < len(kept) - 1:
                        y += line_step

        bbox = overlay.getbbox()
        image.paste(overlay, (0, 0), overlay)

        if bbox:
            left, top, right, bottom = bbox
            return (right - left, bottom - top)

        return (0, 0)

    # endregion


# endregion


# region Convenience function

# ---------------------------------------------------------------------------


# draw_text overloads
# --------------------
# Two orthogonal dimensions produce 8 signatures:
#
#   font_stack dimension
#   --------------------
#   A (overloads 1–4): font_stack: list[FontConfig]  required  — no manager supplied
#   B (overloads 5–8): font_stack: list[FontConfig] | None = ... — manager: FontManager supplied
#
#   mode dimension (both groups)
#   ----------------------------
#   x/1  mode="wrap"       – min_size absent (no effect in wrap mode)
#   x/2  mode="scale"      – min_size present
#   x/3  mode="fit"        – min_size + max_height present
#   x/4  mode=RenderMode   – generic runtime-value fallback


# --- Group A: font_stack required, manager optional ---


# Overload 1/8 – font_stack required, mode="wrap"
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
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    manager: FontManager | None = ...,
) -> Image.Image: ...


# Overload 2/8 – font_stack required, mode="scale"
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
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    manager: FontManager | None = ...,
) -> Image.Image: ...


# Overload 3/8 – font_stack required, mode="fit"
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
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    manager: FontManager | None = ...,
) -> Image.Image: ...


# Overload 4/8 – font_stack required, generic RenderMode fallback
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
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    manager: FontManager | None = ...,
) -> Image.Image: ...


# --- Group B: manager required, font_stack optional ---


# Overload 5/8 – manager required, mode="wrap"
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
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    manager: FontManager,
) -> Image.Image: ...


# Overload 6/8 – manager required, mode="scale"
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
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    manager: FontManager,
) -> Image.Image: ...


# Overload 7/8 – manager required, mode="fit"
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
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    manager: FontManager,
) -> Image.Image: ...


# Overload 8/8 – manager required, generic RenderMode fallback
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
    background: FillType = ...,
    padding: int = ...,
    emoji_source: type[BaseSource] = ...,
    manager: FontManager,
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
    background: FillType = (0, 0, 0, 0),
    padding: int = 0,
    emoji_source: type[BaseSource] = Twemoji,
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
        when a *manager* is supplied directly.
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
        Text color. Accepts a Pillow color name, RGB tuple, or RGBA tuple
        (e.g. ``(0, 0, 0, 128)`` for 50% opacity). Defaults to ``"black"``.
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
        If neither *font_stack* nor *manager* is provided with usable font
        configuration.

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
        if not font_stack:
            raise ValueError(
                "Provide at least one FontConfig in font_stack, "
                "or pass a pre-built manager."
            )
        manager = FontManager(default_stack=font_stack)

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
    canvas_w = (
        effective_width if max_width is not None else len(text) * size + 100
    ) + 50

    # Start rendering at (0, size) so that draw_line's visual_top_offset
    # correction never produces a negative y coordinate that would clip tall
    # ascenders (e.g. "f", "t") against the canvas top edge.  The blank rows
    # above the text are removed by the getbbox() crop below.
    # In "fit" mode, cap canvas height to max_height (+ margin) when provided,
    # since content beyond that will be truncated anyway.
    canvas_h = (
        max_height + size if max_height is not None and mode == "fit" else size * 40
    )
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    manager.draw(
        image=canvas,
        text=text,
        position=(0, size),
        size=size,
        weight=weight,
        mode=mode,
        max_width=max_width,
        max_height=max_height,
        min_size=min_size,
        align=align,
        line_spacing=line_spacing,
        fill=fill,
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


# endregion
