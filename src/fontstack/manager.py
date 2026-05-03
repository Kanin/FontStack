"""FontManager class - the core engine for per-character font fallback rendering."""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from dataclasses import asdict
from pathlib import Path
from typing import Literal, overload

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFont
from pilmoji import EMOJI_REGEX, Pilmoji
from pilmoji.source import BaseSource, Twemoji

from fontstack.bidi import _prepare_bidi
from fontstack.cmap import _load_cmap
from fontstack.discovery import scan_font_dir
from fontstack.gradient import (
    _GRADIENT_ANGLE,
    _apply_gradient_mask,
    _is_gradient,
    _make_gradient,
    _parse_gradient,
)
from fontstack.types import (
    _UNBOUNDED_WIDTH,
    Anchor,
    FillType,
    FontConfig,
    HorizontalAlign,
    RenderMode,
    _RenderContext,
    _Segment,
)


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
        lacks a glyph for a given character.  Mutually exclusive with
        *font_dir*; at least one of the two must be provided.
    font_dir:
        Path to a directory of font files (``.ttf``, ``.otf``, ``.ttc``,
        ``.otc``).  When given, the directory is scanned via
        :func:`scan_font_dir` and the resulting :class:`FontConfig` list
        becomes the ``default_stack``.  Mutually exclusive with
        *default_stack*.
    max_cache:
        Maximum number of ``(stack, size, weight)`` entries to keep in the
        font-object LRU cache. Older entries are evicted when the cache is
        full. Defaults to ``30``.

    Example
    -------
    ::

        # Explicit font stack
        manager = FontManager(
            default_stack=[
                FontConfig(path="fonts/NotoSans.ttf"),
                FontConfig(path="fonts/NotoSansCJK.ttc", ttc_index=0),
                FontConfig(path="fonts/NotoSansArabic.ttf"),
            ]
        )

        # Or scan from a directory
        manager = FontManager(font_dir="fonts/")

        img = Image.new("RGBA", (800, 100), "white")
        manager.draw(img, "Hello مرحبا 世界", position=(10, 20), size=40)
    """

    def __init__(
        self,
        default_stack: list[FontConfig] | None = None,
        max_cache: int = 30,
        *,
        font_dir: str | Path | None = None,
    ) -> None:
        if default_stack is not None and font_dir is not None:
            raise ValueError("Specify either default_stack or font_dir, not both.")

        self._font_dir: str | Path | None = font_dir
        if font_dir is not None:
            default_stack = scan_font_dir(font_dir)

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

    @property
    def font_dir(self) -> str | Path | None:
        """The font directory passed at construction time, or ``None``."""
        return self._font_dir

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

        # Split at emoji boundaries first so that each emoji sequence lands in
        # its own segment.  This guarantees that Pilmoji's internal text_line
        # for emoji segments is spaces-only, making getmask2's offset[1]
        # predictable (= ascent) regardless of what surrounds the emoji.  When
        # emoji share a segment with real glyphs getmask2 returns offset[1] ≈
        # vto instead, so a single emoji_position_offset cannot serve both
        # cases correctly.
        raw: list[_Segment] = []
        prev = 0
        for m in EMOJI_REGEX.finditer(text):
            span_start, span_end = m.start(), m.end()
            if span_start > prev:
                # Non-emoji span - segment by font as usual.
                span = text[prev:span_start]
                cur_font = self._get_font_for_char(span[0], ctx)
                cur_run = span[0]
                for char in span[1:]:
                    f = self._get_font_for_char(char, ctx)
                    if f is cur_font:
                        cur_run += char
                    else:
                        raw.append(_Segment(cur_run, cur_font))
                        cur_run = char
                        cur_font = f
                raw.append(_Segment(cur_run, cur_font))
            # Emoji sequence - always primary font, isolated segment.
            raw.append(_Segment(m.group(), ctx.chain[0]))
            prev = span_end
        if prev < len(text):
            # Trailing non-emoji span.
            span = text[prev:]
            cur_font = self._get_font_for_char(span[0], ctx)
            cur_run = span[0]
            for char in span[1:]:
                f = self._get_font_for_char(char, ctx)
                if f is cur_font:
                    cur_run += char
                else:
                    raw.append(_Segment(cur_run, cur_font))
                    cur_run = char
                    cur_font = f
            raw.append(_Segment(cur_run, cur_font))

        if not raw:
            return []

        # Merge adjacent non-emoji segments that use the same font.
        segments: list[_Segment] = [raw[0]]
        for seg in raw[1:]:
            prev_seg = segments[-1]
            if (
                seg.font is prev_seg.font
                and not EMOJI_REGEX.search(prev_seg.text)
                and not EMOJI_REGEX.search(seg.text)
            ):
                segments[-1] = _Segment(prev_seg.text + seg.text, prev_seg.font)
            else:
                segments.append(seg)
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
        1-3 for mixed-script text - while still producing accurate per-font
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

    def _measure_block(
        self,
        text: str,
        ctx: _RenderContext,
        mode: RenderMode,
        effective_width: int,
        max_height: int | None,
        min_size: int,
        line_spacing: float,
        weight: int | str,
        font_stack: list[FontConfig] | None,
    ) -> tuple[int, int, int, int]:
        """
        Return the pixel-accurate visual bounding box ``(left, top, right,
        bottom)`` of the text block, as offsets relative to the draw origin
        ``(x_start, y_pos)`` that :meth:`draw` would use.

        Mirrors the layout logic of :meth:`draw` for all three modes to
        determine which lines are rendered and at what font size, then renders
        those lines onto a small temporary grayscale canvas and calls
        :meth:`~PIL.Image.Image.getbbox` on the result to find the actual
        pixel extent.  This approach captures FreeType hinting effects that
        cause ``FreeTypeFont.getbbox`` to diverge from the true rendered
        positions by a few pixels.

        The same ``visual_top_offset`` (``getbbox("A")[1]``) Y-correction that
        :meth:`draw` applies is used so that vertical bounds are relative to
        the caller-supplied ``y_pos`` (not the internal FreeType draw origin).

        *text* must already be BiDi-reordered before calling.
        Used by :meth:`draw` to compute anchor offsets before positioning.
        """
        size = ctx.size

        # Phase 1 – replicate layout logic to determine which lines/text
        # are actually rendered and at what size (identical to draw()).
        if mode == "scale":
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
            if not display_text:
                return (0, 0, 0, 0)
            render_lines = [display_text]
            line_step = int(ctx.size * line_spacing)

        elif mode == "wrap":
            render_lines = self._wrap_lines(text, ctx, effective_width)
            line_step = int(size * line_spacing)

        else:  # "fit"
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
                ctx = self._resolve_context(current_size, weight, font_stack)
                lines = self._wrap_lines(text, ctx, effective_width)

            line_step = int(current_size * line_spacing)
            kept: list[str] = []
            for i, line in enumerate(lines):
                if (i * line_step + current_size) <= effective_height:
                    kept.append(line)
                else:
                    if kept:
                        last = kept[-1]
                        while last:
                            candidate = last + "..."
                            if self._measure_text(candidate, ctx) <= effective_width:
                                kept[-1] = candidate
                                break
                            last = last[:-1]
                        else:
                            kept[-1] = "..."
                    break

            if not kept:
                return (0, 0, 0, 0)
            render_lines = kept

        # Phase 2 – render to a tiny temp canvas and read actual pixel bounds.
        #
        # FreeType hinting can shift glyphs by a few pixels relative to the
        # theoretical advance origin that FreeTypeFont.getbbox() reports.
        # Rendering to a throw-away image and calling Image.getbbox() gives
        # the true pixel positions and eliminates that discrepancy.
        #
        # We apply the same Y correction as _render_segments:
        #   font_y = y_pos - vto   (vto = getbbox("A")[1])
        # We use MARGIN >= vto so that font_y is always non-negative.
        primary = ctx.chain[0]
        vto = int(primary.getbbox("A")[1])
        primary_asc = primary.getmetrics()[0]
        MARGIN = max(vto + 2, 8)

        n = len(render_lines)
        est_w = (
            int(max(self._measure_text(ln, ctx) for ln in render_lines) * 1.1)
            + MARGIN * 2
            + 20
        )
        est_h = (n - 1) * line_step + ctx.size + MARGIN * 2 + 20

        temp = Image.new("L", (max(est_w, 20), max(est_h, 20)), 0)
        temp_draw = ImageDraw.Draw(temp)
        for i, line in enumerate(render_lines):
            y_pos = MARGIN + i * line_step
            # Use the same per-segment, per-font rendering as _render_segments
            # so that fallback-font glyphs (Arabic, CJK, …) are measured with
            # their actual font rather than the primary font's .notdef glyphs.
            # Primary-font-only rendering produced incorrect vis_l values for
            # Arabic text (tofu boxes have a positive left inset that doesn't
            # exist in the real glyphs), causing x_off to push text off-canvas.
            baseline = y_pos - vto + primary_asc
            x_seg = MARGIN
            for segment in self._segment_text(line, ctx):
                if EMOJI_REGEX.search(segment.text):
                    # Pilmoji renders each emoji sequence as a square image of
                    # side ctx.size starting exactly at x_seg (no left bearing).
                    # The emoji image top lands at y_pos (matching _render_segments
                    # with oy = vto - asc).  Paint a sentinel pixel there so that
                    # getbbox() captures the true left and top bounds of the line.
                    # Using baseline - seg_asc (= y_pos - vto) was wrong: it placed
                    # the sentinel at the ascender line, inflating |vis_t| by ~vto
                    # and causing the vis_t correction in emoji_oy to over-shift.
                    temp_draw.point((int(x_seg), int(y_pos)), fill=255)
                    x_seg += ctx.size
                    continue
                seg_asc = segment.font.getmetrics()[0]
                seg_y = baseline - seg_asc
                temp_draw.text(
                    (int(x_seg), seg_y), segment.text, font=segment.font, fill=255
                )
                try:
                    x_seg += segment.font.getlength(segment.text)
                except Exception:
                    x_seg += ctx.size * 0.6 * len(segment.text)

        bb = temp.getbbox()
        if bb is None:
            return (0, 0, 0, 0)
        return (bb[0] - MARGIN, bb[1] - MARGIN, bb[2] - MARGIN, bb[3] - MARGIN)

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
        stroke_width: int = ...,
        stroke_fill: FillType | None = ...,
        shadow_color: FillType | None = ...,
        shadow_offset: tuple[int, int] = ...,
        gradient_angle: float = ...,
        anchor: Anchor = ...,
        font_stack: list[FontConfig] | None = ...,
        emoji_source: BaseSource | type[BaseSource] = ...,
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
        stroke_width: int = ...,
        stroke_fill: FillType | None = ...,
        shadow_color: FillType | None = ...,
        shadow_offset: tuple[int, int] = ...,
        gradient_angle: float = ...,
        anchor: Anchor = ...,
        font_stack: list[FontConfig] | None = ...,
        emoji_source: BaseSource | type[BaseSource] = ...,
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
        stroke_width: int = ...,
        stroke_fill: FillType | None = ...,
        shadow_color: FillType | None = ...,
        shadow_offset: tuple[int, int] = ...,
        gradient_angle: float = ...,
        anchor: Anchor = ...,
        font_stack: list[FontConfig] | None = ...,
        emoji_source: BaseSource | type[BaseSource] = ...,
    ) -> tuple[int, int]: ...

    # Overload 4/4 - generic ``RenderMode`` fallback
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Catches calls where ``mode`` is a runtime ``RenderMode`` union value
    # (e.g. a variable forwarded from an outer scope). Both ``min_size`` and
    # all other parameters are present so the type checker can resolve the call
    # without ambiguity. This overload is never chosen when the caller passes a
    # string literal; overloads 1-3 take priority.
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
        stroke_width: int = ...,
        stroke_fill: FillType | None = ...,
        shadow_color: FillType | None = ...,
        shadow_offset: tuple[int, int] = ...,
        gradient_angle: float = ...,
        anchor: Anchor = ...,
        font_stack: list[FontConfig] | None = ...,
        emoji_source: BaseSource | type[BaseSource] = ...,
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
        stroke_width: int = 0,
        stroke_fill: FillType | None = None,
        shadow_color: FillType | None = None,
        shadow_offset: tuple[int, int] = (2, 2),
        gradient_angle: float = _GRADIENT_ANGLE,
        anchor: Anchor = "lt",
        font_stack: list[FontConfig] | None = None,
        emoji_source: BaseSource | type[BaseSource] = Twemoji,
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
            50% opacity), or an integer for palette/grayscale images.
            A dash-separated string of colors (``"red-blue"``,
            ``"#FF0000-#00FF00-#0000FF"``) produces a linear gradient
            across the text (slightly diagonal so multi-line text gets
            natural color variation per line). The preset ``"rainbow"``
            expands to ``"red-orange-yellow-green-blue-indigo-violet"``.
            Defaults to ``"black"``.
        stroke_width:
            Outline thickness in pixels drawn around each glyph. ``0`` means
            no outline. Defaults to ``0``.
        stroke_fill:
            Outline color. Accepts the same value types as *fill*, including
            gradient strings (e.g. ``"rainbow"``, ``"red-blue"``). When
            ``None`` and *stroke_width* > 0, Pillow uses *fill* as the stroke
            color. Defaults to ``None``.
        shadow_color:
            Drop-shadow color. Accepts the same value types as *fill*,
            including gradient strings. The shadow shape includes the
            outline when *stroke_width* > 0. ``None`` disables the shadow.
            Defaults to ``None``.
        shadow_offset:
            ``(x, y)`` pixel offset for the drop shadow relative to the main
            text position. Positive values shift right and down. Only used
            when *shadow_color* is not ``None``. Defaults to ``(2, 2)``.
        gradient_angle:
            Gradient direction in degrees, clockwise from horizontal. ``0``
            produces a pure left-to-right gradient; the default ``15.0``
            adds a slight diagonal so multi-line text gets natural color
            variation per line. Only used when *fill*, *stroke_fill*, or
            *shadow_color* is a gradient string. Defaults to ``15.0``.
        font_stack:
            Override the instance's :attr:`default_stack` for this call only.
        anchor:
            Two-character PIL-style anchor code specifying which point of the
            text block is placed at *position*. The first character selects
            the horizontal reference (``l`` = left edge, ``m`` = horizontal
            center, ``r`` = right edge) and the second selects the vertical
            reference (``t`` = top edge, ``m`` = vertical center,
            ``b`` = bottom edge). Valid values are ``"lt"``, ``"mt"``,
            ``"rt"``, ``"lm"``, ``"mm"``, ``"rm"``, ``"lb"``, ``"mb"``,
            ``"rb"``. Defaults to ``"lt"`` (top-left), which preserves the
            historical behavior where *position* was the top-left corner.
        emoji_source:
            Pilmoji emoji source - either a :class:`~pilmoji.source.BaseSource`
            subclass (e.g. ``Twemoji``) or an already-constructed instance.
            Defaults to :class:`~pilmoji.source.Twemoji`.

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
        ValueError
            If *anchor* is not one of the nine valid two-character codes.
        """
        if mode not in {"wrap", "scale", "fit"}:
            raise ValueError(f"mode must be 'wrap', 'scale', or 'fit', got {mode!r}.")
        if align not in {"left", "center", "right"}:
            raise ValueError(
                f"align must be 'left', 'center', or 'right', got {align!r}."
            )
        _valid_anchors = {"lt", "mt", "rt", "lm", "mm", "rm", "lb", "mb", "rb"}
        if anchor not in _valid_anchors:
            raise ValueError(
                f"anchor must be one of {sorted(_valid_anchors)!r}, got {anchor!r}."
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

        # Adjust position for the requested anchor point.
        # _measure_block replicates the full layout logic without drawing;
        # we call it only when the anchor is not the default top-left ("lt")
        # so there is no overhead for the common case.
        vis_l, vis_t, vis_r, vis_b = self._measure_block(
            text,
            ctx,
            mode,
            effective_width,
            max_height,
            min_size,
            line_spacing,
            weight,
            font_stack,
        )
        h_char, v_char = anchor[0], anchor[1]
        if h_char == "l":
            x_off = -vis_l
        elif h_char == "m":
            x_off = -(vis_l + vis_r) // 2
        else:  # "r"
            x_off = -vis_r
        if v_char == "t":
            y_off = -vis_t
        elif v_char == "m":
            y_off = -(vis_t + vis_b) // 2
        else:  # "b"
            y_off = -vis_b
        position = (position[0] + x_off, position[1] + y_off)

        # Determine whether fill is a gradient specification.
        gradient_stops: list[tuple[int, int, int]] | None = None
        if isinstance(fill, str) and _is_gradient(fill):
            use_gradient = True
            gradient_stops = _parse_gradient(fill)
        else:
            use_gradient = False
        # When rendering with a gradient, draw text in opaque white first, then
        # mask it with the gradient image after all lines are drawn.
        render_fill: FillType = (255, 255, 255) if use_gradient else fill

        # Detect gradient stroke_fill / shadow_color.
        gradient_stroke_stops: list[tuple[int, int, int]] | None = None
        if isinstance(stroke_fill, str) and _is_gradient(stroke_fill):
            use_gradient_stroke = True
            gradient_stroke_stops = _parse_gradient(stroke_fill)
        else:
            use_gradient_stroke = False
        render_stroke_fill: FillType | None = (
            (255, 255, 255) if use_gradient_stroke else stroke_fill
        )

        gradient_shadow_stops: list[tuple[int, int, int]] | None = None
        if isinstance(shadow_color, str) and _is_gradient(shadow_color):
            use_gradient_shadow = True
            gradient_shadow_stops = _parse_gradient(shadow_color)
        else:
            use_gradient_shadow = False

        # When gradient fill or gradient stroke is combined with a visible
        # stroke, a fill mask is needed to apply gradients independently to
        # the fill and stroke regions of the same overlay (avoiding seams
        # caused by compositing two separate overlays with antialiased edges).
        need_fill_mask = stroke_width > 0 and (
            use_gradient_stroke or (use_gradient and stroke_fill is not None)
        )

        # Shadow and main text are drawn onto separate overlays so that the
        # shadow never bleeds through semi-transparent gradient text.
        shadow_overlay: Image.Image | None = None
        _shadow_rgb: tuple[int, int, int] = (0, 0, 0)
        _shadow_alpha: int = 255
        if shadow_color is not None:
            shadow_overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
            if use_gradient_shadow:
                # Gradient shadow: render in white, apply gradient later.
                _shadow_rgb = (255, 255, 255)
            else:
                # Resolve shadow_color to separate RGB and alpha components.
                # The shadow pass renders at full opacity; alpha is applied
                # during post-processing so emoji silhouettes match text.
                if isinstance(shadow_color, str):
                    _sc = ImageColor.getrgb(shadow_color)
                elif isinstance(shadow_color, int):
                    _sc = (shadow_color, shadow_color, shadow_color)
                else:
                    _sc = shadow_color
                _shadow_rgb = (_sc[0], _sc[1], _sc[2])
                _shadow_alpha = _sc[3] if len(_sc) == 4 else 255
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        fill_mask_overlay: Image.Image | None = None
        if need_fill_mask:
            fill_mask_overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))

        def _render_segments(
            target: Image.Image,
            line: str,
            x: int,
            y_pos: int,
            draw_ctx: _RenderContext,
            seg_fill: FillType,
            seg_stroke_width: int = 0,
            seg_stroke_fill: FillType | None = None,
        ) -> None:
            """
            Draw all segments of *line* onto *target* at ``(x, y_pos)``.

            Shared by both the shadow pass and the main text pass to avoid
            duplicating the per-segment baseline-correction logic.
            """
            with Pilmoji(target, source=emoji_source) as pil:
                primary = draw_ctx.chain[0]
                primary_ascent = primary.getmetrics()[0]
                visual_top_offset = primary.getbbox("A")[1]
                corrected_y = y_pos - visual_top_offset
                baseline = corrected_y + primary_ascent

                for segment in self._segment_text(line, draw_ctx):
                    font_ascent = segment.font.getmetrics()[0]
                    font_y = baseline - font_ascent

                    # Emoji segments are isolated (no real glyphs), so Pilmoji
                    # passes a spaces-only text_line to getmask2.  With the
                    # default "la" anchor getmask2 then returns offset[1] =
                    # primary_ascent, shifting line_y to y_pos + (asc - vto)
                    # (the baseline).  Correct with oy = vto - asc so the
                    # emoji image lands at y_pos (the visual glyph top).
                    #
                    # Text segments contain real glyphs alongside spaces, so
                    # getmask2 returns offset[1] ≈ vto, giving line_y ≈ y_pos
                    # already.  No correction needed (oy = 0).
                    has_emoji = bool(EMOJI_REGEX.search(segment.text))
                    if has_emoji:
                        # Pilmoji renders emoji as a square of side `font.size`.
                        # getmask2 on a spaces-only run returns offset[1] = asc,
                        # so line_y = font_y + asc = y_pos + (asc - vto) = baseline.
                        # We want the emoji vertically centered on the cap height
                        # (y_pos … baseline), so:
                        #   emoji_top = y_pos + (cap_h - emoji_size) / 2
                        #             = y_pos - (emoji_size - cap_h) / 2
                        # where cap_h = asc - vto.
                        # emoji_oy = emoji_top - line_y
                        #          = -(cap_h + emoji_size) / 2
                        cap_h = primary_ascent - visual_top_offset
                        emoji_size = draw_ctx.size
                        emoji_oy = -int((cap_h + emoji_size) / 2)
                    else:
                        emoji_oy = 0

                    text_kwargs: dict = {
                        "fill": seg_fill,
                        "stroke_width": seg_stroke_width,
                        "emoji_position_offset": (0, emoji_oy),
                    }
                    if seg_stroke_fill is not None:
                        text_kwargs["stroke_fill"] = seg_stroke_fill
                    pil.text(
                        (int(x), int(font_y)),
                        segment.text,
                        font=segment.font,
                        **text_kwargs,
                    )
                    x += pil.getsize(segment.text, font=segment.font)[0]

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

            When *shadow_color* is set, a shadow copy of the line is drawn
            first onto a separate overlay at ``(x + shadow_offset[0],
            y + shadow_offset[1])``.  The main text (with optional stroke)
            is then drawn on the primary overlay.
            """
            # Compute x offset for alignment within the text block width.
            if align == "center":
                x = int(x_start + (effective_width - line_width) // 2)
            elif align == "right":
                x = int(x_start + effective_width - int(line_width))
            else:
                x = x_start

            # Shadow pass - includes stroke shape so the shadow matches the
            # full outline rather than hiding behind it.  Render at
            # full-opacity RGB; the shadow alpha is applied in post-processing.
            if shadow_overlay is not None and shadow_color is not None:
                sx = x + shadow_offset[0]
                sy = y_pos + shadow_offset[1]
                _render_segments(
                    shadow_overlay,
                    line,
                    sx,
                    sy,
                    draw_ctx,
                    _shadow_rgb,
                    stroke_width,
                    _shadow_rgb,
                )

            # Main text pass (with optional stroke).
            if fill_mask_overlay is not None:
                # Render the full glyph (fill + stroke) onto the main
                # overlay.  The fill mask rendered separately lets us apply
                # different gradients to fill vs stroke pixels later.
                #
                # IMPORTANT: use a uniform base color so that antialiased
                # boundary pixels between fill and stroke don't produce a
                # visible fringe.  The gradient composite replaces RGB in
                # the fill/stroke regions; using the *other* region's color
                # as the base means boundary blending is between gradient
                # and that region's final color, not gradient and white.
                if use_gradient and use_gradient_stroke:
                    # Both regions get gradient-masked; base color is
                    # irrelevant since all RGB will be replaced.
                    _render_segments(
                        overlay,
                        line,
                        x,
                        y_pos,
                        draw_ctx,
                        (128, 128, 128),
                        stroke_width,
                        (128, 128, 128),
                    )
                elif use_gradient:
                    # Gradient fill, solid stroke: paint everything in the
                    # stroke color so boundary pixels blend gradient<->stroke.
                    _eff_stroke: FillType = (
                        render_stroke_fill
                        if render_stroke_fill is not None
                        else render_fill
                    )
                    _render_segments(
                        overlay,
                        line,
                        x,
                        y_pos,
                        draw_ctx,
                        _eff_stroke,
                        stroke_width,
                        _eff_stroke,
                    )
                else:
                    # Solid fill, gradient stroke: paint everything in the
                    # fill color so boundary pixels blend gradient<->fill.
                    _render_segments(
                        overlay,
                        line,
                        x,
                        y_pos,
                        draw_ctx,
                        render_fill,
                        stroke_width,
                        render_fill,
                    )
                # Fill-only pass for the mask (no stroke).
                _render_segments(
                    fill_mask_overlay,
                    line,
                    x,
                    y_pos,
                    draw_ctx,
                    (255, 255, 255),
                )
            else:
                _render_segments(
                    overlay,
                    line,
                    x,
                    y_pos,
                    draw_ctx,
                    render_fill,
                    stroke_width,
                    render_stroke_fill,
                )

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
            # fit and truncate the last kept line with "...".
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
                            if self._measure_text(candidate, ctx) <= effective_width:
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

        # Post-process the shadow overlay so that emoji bitmaps (pasted as
        # full-color PNGs by Pilmoji) become solid-color silhouettes that
        # look like proper shadows instead of duplicate emoji.
        if shadow_overlay is not None:
            if use_gradient_shadow and gradient_shadow_stops is not None:
                # Flatten all pixels to white (unify emoji + text), then
                # apply gradient masking.
                _, _, _, a_chan = shadow_overlay.split()
                shadow_overlay = Image.merge(
                    "RGBA",
                    (
                        Image.new("L", shadow_overlay.size, 255),
                        Image.new("L", shadow_overlay.size, 255),
                        Image.new("L", shadow_overlay.size, 255),
                        a_chan,
                    ),
                )
                _apply_gradient_mask(
                    shadow_overlay, gradient_shadow_stops, gradient_angle
                )
            else:
                _, _, _, a_chan = shadow_overlay.split()
                if _shadow_alpha < 255:
                    mod = Image.new("L", shadow_overlay.size, _shadow_alpha)
                    a_chan = ImageChops.multiply(a_chan, mod)
                shadow_overlay = Image.merge(
                    "RGBA",
                    (
                        Image.new("L", shadow_overlay.size, _shadow_rgb[0]),
                        Image.new("L", shadow_overlay.size, _shadow_rgb[1]),
                        Image.new("L", shadow_overlay.size, _shadow_rgb[2]),
                        a_chan,
                    ),
                )

        # Apply gradient masking.  When a fill mask is available, use it to
        # apply separate gradients to fill and stroke pixels within the same
        # overlay (no compositing seam).  Otherwise fall back to the simple
        # whole-overlay mask.
        if fill_mask_overlay is not None:
            fill_mask = fill_mask_overlay.split()[3]  # alpha = fill area
            text_bbox = overlay.getbbox()
            if text_bbox is not None:
                left_g, top_g, right_g, bottom_g = text_bbox
                grad_w = right_g - left_g
                grad_h = bottom_g - top_g
                region = overlay.crop(text_bbox)
                r_o, g_o, b_o, a_o = region.split()
                fm = fill_mask.crop(text_bbox)

                # Build fill gradient channels (or reuse original if solid).
                if use_gradient and gradient_stops is not None:
                    fg = _make_gradient(gradient_stops, grad_w, grad_h, gradient_angle)
                    r_fg, g_fg, b_fg, _ = fg.split()
                else:
                    r_fg, g_fg, b_fg = r_o, g_o, b_o

                # Build stroke gradient channels (or reuse original if solid).
                if use_gradient_stroke and gradient_stroke_stops is not None:
                    sg = _make_gradient(
                        gradient_stroke_stops, grad_w, grad_h, gradient_angle
                    )
                    r_sg, g_sg, b_sg, _ = sg.split()
                else:
                    r_sg, g_sg, b_sg = r_o, g_o, b_o

                # Composite: fill_mask=255 --> fill gradient, 0 --> stroke.
                r_new = Image.composite(r_fg, r_sg, fm)
                g_new = Image.composite(g_fg, g_sg, fm)
                b_new = Image.composite(b_fg, b_sg, fm)
                overlay.paste(
                    Image.merge("RGBA", (r_new, g_new, b_new, a_o)),
                    (left_g, top_g),
                )
        elif use_gradient and gradient_stops is not None:
            _apply_gradient_mask(overlay, gradient_stops, gradient_angle)

        # Composite: shadow (bottom) -> main overlay (top).
        if shadow_overlay is not None:
            image.paste(shadow_overlay, (0, 0), shadow_overlay)

        bbox = overlay.getbbox()
        image.paste(overlay, (0, 0), overlay)

        if bbox:
            # Expand the bounding box to include any shadow pixels.
            if shadow_overlay is not None:
                shadow_bbox = shadow_overlay.getbbox()
                if shadow_bbox is not None:
                    sl, st, sr, sb = shadow_bbox
                    bl, bt, br, bb = bbox
                    bbox = (min(bl, sl), min(bt, st), max(br, sr), max(bb, sb))

            left, top, right, bottom = bbox
            return (right - left, bottom - top)

        return (0, 0)

    # endregion
