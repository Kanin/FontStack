"""Unit tests for FontManager (no rendering - font/cmap operations only)."""

from __future__ import annotations

import pytest
from PIL import ImageFont

from fontstack import FontConfig, FontManager


class TestFontManagerInit:
    def test_empty_stack_raises(self) -> None:
        with pytest.raises(ValueError, match="default_stack must contain at least one"):
            FontManager(default_stack=[])

    def test_single_font_ok(self, noto_sans: str) -> None:
        mgr = FontManager(default_stack=[FontConfig(path=noto_sans)])
        assert len(mgr.default_stack) == 1

    def test_default_stack_property_returns_copy(self, noto_sans: str) -> None:
        mgr = FontManager(default_stack=[FontConfig(path=noto_sans)])
        stack = mgr.default_stack
        stack.clear()
        # Clearing the returned copy must not affect the internal stack.
        assert len(mgr.default_stack) == 1


class TestGetFontChain:
    def test_returns_one_font_per_stack_entry(
        self, font_manager: FontManager, default_stack: list[FontConfig]
    ) -> None:
        chain = font_manager.get_font_chain(size=24)
        assert len(chain) == len(default_stack)

    def test_returns_freetype_fonts(self, font_manager: FontManager) -> None:
        chain = font_manager.get_font_chain(size=32)
        for font in chain:
            assert isinstance(font, ImageFont.FreeTypeFont)

    def test_cache_hit_returns_same_objects(self, font_manager: FontManager) -> None:
        chain1 = font_manager.get_font_chain(size=24, weight=400)
        chain2 = font_manager.get_font_chain(size=24, weight=400)
        # Exact same list object returned from cache.
        assert chain1 is chain2

    def test_different_sizes_give_different_fonts(
        self, font_manager: FontManager
    ) -> None:
        chain_small = font_manager.get_font_chain(size=12)
        chain_large = font_manager.get_font_chain(size=48)
        # Different size → different font objects.
        assert chain_small[0] is not chain_large[0]

    def test_custom_stack_overrides_default(
        self, font_manager: FontManager, noto_sans: str
    ) -> None:
        custom = [FontConfig(path=noto_sans)]
        chain = font_manager.get_font_chain(size=24, custom_stack=custom)
        assert len(chain) == 1


class TestFontHasGlyph:
    def test_latin_in_noto_sans(
        self, font_manager: FontManager, default_stack: list[FontConfig]
    ) -> None:
        primary = default_stack[0]
        assert font_manager._font_has_glyph(primary, "A") is True

    def test_digit_in_noto_sans(
        self, font_manager: FontManager, default_stack: list[FontConfig]
    ) -> None:
        primary = default_stack[0]
        assert font_manager._font_has_glyph(primary, "5") is True

    def test_arabic_in_arabic_font(
        self, font_manager: FontManager, default_stack: list[FontConfig]
    ) -> None:
        arabic_config = default_stack[1]
        # Arabic Alef (U+0627)
        assert font_manager._font_has_glyph(arabic_config, "\u0627") is True


class TestSegmentText:
    def test_empty_text_returns_empty_list(self, font_manager: FontManager) -> None:
        ctx = font_manager._resolve_context(24, 400, None)
        segments = font_manager._segment_text("", ctx)
        assert segments == []

    def test_pure_latin_is_single_segment(self, font_manager: FontManager) -> None:
        ctx = font_manager._resolve_context(24, 400, None)
        segments = font_manager._segment_text("Hello", ctx)
        assert len(segments) == 1
        assert segments[0].text == "Hello"

    def test_mixed_latin_arabic_produces_multiple_segments(
        self, font_manager: FontManager
    ) -> None:
        # 'A' maps to primary (Noto Sans), Arabic text maps to Noto Sans Arabic.
        ctx = font_manager._resolve_context(24, 400, None)
        segments = font_manager._segment_text("A\u0627", ctx)
        # Two different fonts → must be at least 2 segments.
        assert len(segments) >= 2

    def test_segment_text_concatenation_equals_input(
        self, font_manager: FontManager
    ) -> None:
        text = "Hello \u0627\u0644\u0639\u0631\u0628\u064a"
        ctx = font_manager._resolve_context(24, 400, None)
        segments = font_manager._segment_text(text, ctx)
        assert "".join(s.text for s in segments) == text


class TestMeasureText:
    def test_nonempty_text_positive_width(self, font_manager: FontManager) -> None:
        ctx = font_manager._resolve_context(24, 400, None)
        width = font_manager._measure_text("Hello", ctx)
        assert width > 0

    def test_empty_text_zero_width(self, font_manager: FontManager) -> None:
        ctx = font_manager._resolve_context(24, 400, None)
        width = font_manager._measure_text("", ctx)
        assert width == 0.0

    def test_wider_text_larger_width(self, font_manager: FontManager) -> None:
        ctx = font_manager._resolve_context(24, 400, None)
        w_short = font_manager._measure_text("Hi", ctx)
        w_long = font_manager._measure_text("Hello, world!", ctx)
        assert w_long > w_short


class TestResolveContext:
    def test_returns_correct_size(self, font_manager: FontManager) -> None:
        ctx = font_manager._resolve_context(36, 400, None)
        assert ctx.size == 36

    def test_chain_length_matches_stack(
        self, font_manager: FontManager, default_stack: list[FontConfig]
    ) -> None:
        ctx = font_manager._resolve_context(24, 400, None)
        assert len(ctx.chain) == len(default_stack)

    def test_custom_stack_overrides_default(
        self, font_manager: FontManager, noto_sans: str
    ) -> None:
        custom = [FontConfig(path=noto_sans)]
        ctx = font_manager._resolve_context(24, 400, custom)
        assert len(ctx.chain) == 1
        assert len(ctx.stack) == 1

    def test_chain_matches_get_font_chain(self, font_manager: FontManager) -> None:
        """_resolve_context must reuse the LRU-cached chain from get_font_chain."""
        ctx = font_manager._resolve_context(24, 400, None)
        chain = font_manager.get_font_chain(size=24, weight=400)
        assert ctx.chain is chain


class TestWrapLines:
    def test_single_line_when_text_fits(self, font_manager: FontManager) -> None:
        ctx = font_manager._resolve_context(24, 400, None)
        lines = font_manager._wrap_lines("Hello", ctx, 500)
        assert lines == ["Hello"]

    def test_splits_long_text(self, font_manager: FontManager) -> None:
        ctx = font_manager._resolve_context(32, 400, None)
        lines = font_manager._wrap_lines(
            "The quick brown fox jumps over the lazy dog", ctx, 100
        )
        assert len(lines) > 1

    def test_single_word_exceeding_width_stays_on_own_line(
        self, font_manager: FontManager
    ) -> None:
        # Width of 1px cannot fit any word - each word must land on its own
        # line rather than being dropped.
        ctx = font_manager._resolve_context(48, 400, None)
        lines = font_manager._wrap_lines("alpha beta gamma", ctx, 1)
        assert len(lines) == 3
        assert lines == ["alpha", "beta", "gamma"]

    def test_concatenation_preserves_words(self, font_manager: FontManager) -> None:
        text = "one two three four five"
        ctx = font_manager._resolve_context(32, 400, None)
        lines = font_manager._wrap_lines(text, ctx, 200)
        assert " ".join(lines).split() == text.split()
