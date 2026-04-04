"""Integration tests for draw and draw_text (requires real fonts)."""

from __future__ import annotations

import pytest
from PIL import Image

from fontstack import FontConfig, FontManager, draw_text
from fontstack._core import _prepare_bidi

# region draw


class TestDraw:
    def _canvas(self, size: tuple[int, int] = (800, 200)) -> Image.Image:
        return Image.new("RGBA", size, (255, 255, 255, 255))

    def test_returns_nonzero_dimensions(self, font_manager: FontManager) -> None:
        img = self._canvas()
        w, h = font_manager.draw(img, "Hello", position=(10, 10), size=32)
        assert w > 0
        assert h > 0

    def test_empty_string_returns_zero(self, font_manager: FontManager) -> None:
        img = self._canvas()
        result = font_manager.draw(img, "", position=(10, 10), size=32)
        assert result == (0, 0)

    def test_modifies_image_in_place(self, font_manager: FontManager) -> None:
        img = self._canvas()
        original_id = id(img)
        font_manager.draw(img, "Hello", position=(10, 10), size=32)
        assert id(img) == original_id

    def test_wrap_mode_multiline_taller_than_singleline(
        self, font_manager: FontManager
    ) -> None:
        img = self._canvas((800, 400))
        # Force wrapping with a narrow max_width.
        _, h_wrapped = font_manager.draw(
            img,
            "Hello world this is a long string",
            position=(0, 0),
            size=32,
            mode="wrap",
            max_width=120,
        )
        img2 = self._canvas((800, 400))
        _, h_single = font_manager.draw(
            img2,
            "Hello",
            position=(0, 0),
            size=32,
            mode="wrap",
        )
        assert h_wrapped > h_single

    def test_scale_mode_respects_max_width(self, font_manager: FontManager) -> None:
        img = self._canvas((800, 200))
        max_w = 200
        w, _ = font_manager.draw(
            img,
            "Hello world",
            position=(0, 0),
            size=48,
            mode="scale",
            max_width=max_w,
        )
        assert w <= max_w

    def test_invalid_mode_raises(self, font_manager: FontManager) -> None:
        img = self._canvas()
        with pytest.raises(ValueError, match="mode must be"):
            font_manager.draw(img, "Hello", position=(0, 0), mode="invalid")  # type: ignore[arg-type]

    def test_invalid_align_raises(self, font_manager: FontManager) -> None:
        img = self._canvas()
        with pytest.raises(ValueError, match="align must be"):
            font_manager.draw(img, "Hello", position=(0, 0), align="middle")  # type: ignore[arg-type]

    def test_arabic_text_renders(self, font_manager: FontManager) -> None:
        img = self._canvas()
        w, h = font_manager.draw(img, "مرحبا", position=(10, 10), size=32)
        assert w > 0
        assert h > 0

    def test_mixed_script_renders(self, font_manager: FontManager) -> None:
        img = self._canvas((1000, 200))
        w, h = font_manager.draw(img, "Hello مرحبا", position=(10, 10), size=32)
        assert w > 0
        assert h > 0

    def test_center_and_right_differ_from_left(self, font_manager: FontManager) -> None:
        text = "Hello world"
        size = 32
        max_w = 600

        def render_aligned(align: str) -> Image.Image:
            img = Image.new("RGBA", (800, 100), (255, 255, 255, 255))
            font_manager.draw(
                img,
                text,
                position=(0, 0),
                size=size,
                mode="wrap",
                max_width=max_w,
                align=align,  # type: ignore[arg-type]
            )
            return img

        left_img = render_aligned("left")
        center_img = render_aligned("center")
        right_img = render_aligned("right")

        # The three images should differ (different pixel distributions).
        assert left_img.tobytes() != center_img.tobytes()
        assert left_img.tobytes() != right_img.tobytes()

    def test_variable_font_weight(self, font_manager: FontManager) -> None:
        # Verify that integer weight values are accepted without error and produce
        # non-zero output. Whether the font visually changes depends on whether it
        # supports the wght axis; the renderer silently ignores axes for static fonts.
        img_thin = self._canvas()
        img_bold = self._canvas()
        w_thin, h_thin = font_manager.draw(
            img_thin, "Hello", position=(0, 0), size=40, weight=100
        )
        w_bold, h_bold = font_manager.draw(
            img_bold, "Hello", position=(0, 0), size=40, weight=900
        )
        assert w_thin > 0 and h_thin > 0
        assert w_bold > 0 and h_bold > 0


# endregion


# region draw_text


class TestDrawText:
    def test_returns_image(self, default_stack: list[FontConfig]) -> None:
        img = draw_text("Hello", font_stack=default_stack, size=32)
        assert isinstance(img, Image.Image)

    def test_returns_rgba(self, default_stack: list[FontConfig]) -> None:
        img = draw_text("Hello", font_stack=default_stack, size=32)
        assert img.mode == "RGBA"

    def test_nonempty_result(self, default_stack: list[FontConfig]) -> None:
        img = draw_text("Hello", font_stack=default_stack, size=32)
        assert img.width > 0
        assert img.height > 0

    def test_padding_increases_dimensions(
        self, default_stack: list[FontConfig]
    ) -> None:
        no_pad = draw_text("Hello", font_stack=default_stack, size=32, padding=0)
        padded = draw_text("Hello", font_stack=default_stack, size=32, padding=20)
        assert padded.width == no_pad.width + 40
        assert padded.height == no_pad.height + 40

    def test_no_stack_no_manager_raises(self) -> None:
        with pytest.raises(ValueError, match="Provide at least one FontConfig"):
            draw_text("Hello", font_stack=[])

    def test_reuse_manager_produces_same_output(
        self, font_manager: FontManager, default_stack: list[FontConfig]
    ) -> None:
        img_direct = draw_text("Hello", font_stack=default_stack, size=32)
        img_mgr = draw_text("Hello", font_stack=[], manager=font_manager, size=32)
        # Both should be non-empty and the same width/height.
        assert img_direct.size == img_mgr.size

    def test_background_color_applied(self, default_stack: list[FontConfig]) -> None:
        img = draw_text(
            "Hello", font_stack=default_stack, size=32, background="white", padding=10
        )
        # Edge pixels (in the padding zone) should be white.
        corner = img.getpixel((0, 0))
        assert isinstance(corner, tuple) and corner[:3] == (255, 255, 255)

    def test_empty_text_returns_minimal_image(
        self, default_stack: list[FontConfig]
    ) -> None:
        img = draw_text("", font_stack=default_stack, size=32)
        # Empty text returns the 1×1 fallback.
        assert img.width >= 1
        assert img.height >= 1

    def test_arabic_text_renders(self, default_stack: list[FontConfig]) -> None:
        img = draw_text("مرحبا", font_stack=default_stack, size=32)
        assert img.width > 0
        assert img.height > 0

    def test_scale_mode(self, default_stack: list[FontConfig]) -> None:
        max_w = 150
        img = draw_text(
            "This is quite a long piece of text",
            font_stack=default_stack,
            size=40,
            mode="scale",
            max_width=max_w,
        )
        assert img.width <= max_w + 5  # small tolerance for sub-pixel rounding

    def test_draw_text_no_max_width_reasonable_canvas(
        self, default_stack: list[FontConfig]
    ) -> None:
        """Unconstrained draw_text must not balloon the canvas."""
        text = "Hello world"
        size = 40
        img = draw_text(text, font_stack=default_stack, size=size)
        # The heuristic caps canvas_w to len(text) * size + 150 (+ 50 margin);
        # verify the result is nowhere near the old 100,049 px wide canvas.
        assert img.width < len(text) * size * 2
        assert img.width > 0


# endregion


# region BiDi and Arabic reshaping


class TestPrepareBidi:
    def test_arabic_reshaping_changes_string(self) -> None:
        """arabic_reshaper must replace isolated codepoints with presentation forms."""
        original = "مرحبا"
        result = _prepare_bidi(original)
        # Reshaping changes the codepoints to presentation forms, so the
        # display string must differ from the raw input.
        assert result != original

    def test_latin_text_is_unchanged(self) -> None:
        """Pure LTR Latin text should pass through _prepare_bidi unmodified."""
        text = "Hello, world!"
        assert _prepare_bidi(text) == text

    def test_rtl_text_is_reordered(self) -> None:
        """A right-to-left string must be visually reversed after BiDi reordering."""
        # hebrew letters Aleph, Bet, Gimel - a simple RTL string
        rtl = "\u05d0\u05d1\u05d2"
        result = _prepare_bidi(rtl)
        # The BiDi algorithm reverses visual order for RTL runs.
        assert result == rtl[::-1]

    def test_mixed_arabic_latin_renders_without_error(
        self, font_manager: FontManager
    ) -> None:
        """Mixed Arabic+Latin passes through _prepare_bidi and renders successfully."""
        img = Image.new("RGBA", (800, 200), (255, 255, 255, 255))
        w, h = font_manager.draw(img, "Hello مرحبا world", position=(10, 10), size=32)
        assert w > 0 and h > 0


# endregion


# region fit mode


class TestFitMode:
    def _canvas(self, size: tuple[int, int] = (800, 300)) -> Image.Image:
        return Image.new("RGBA", size, (255, 255, 255, 255))

    def test_fit_mode_respects_max_height(self, font_manager: FontManager) -> None:
        img = self._canvas((800, 400))
        max_h = 80
        _, h = font_manager.draw(
            img,
            "One two three four five six seven eight nine ten",
            position=(0, 0),
            size=32,
            mode="fit",
            max_width=400,
            max_height=max_h,
        )
        assert h <= max_h

    def test_fit_mode_no_max_height_behaves_like_wrap(
        self, font_manager: FontManager
    ) -> None:
        text = "Hello world this is a long string"

        img_wrap = self._canvas()
        _, h_wrap = font_manager.draw(
            img_wrap, text, position=(0, 0), size=32, mode="wrap", max_width=250
        )
        img_fit = self._canvas()
        _, h_fit = font_manager.draw(
            img_fit, text, position=(0, 0), size=32, mode="fit", max_width=250
        )
        assert h_fit == h_wrap

    def test_fit_mode_renders_text(self, font_manager: FontManager) -> None:
        """fit mode must always produce non-zero output for non-empty text."""
        img = self._canvas()
        w, h = font_manager.draw(
            img,
            "Hello world",
            position=(0, 0),
            size=32,
            mode="fit",
            max_width=300,
            max_height=200,
        )
        assert w > 0
        assert h > 0

    def test_fit_mode_via_draw_text(self, default_stack: list[FontConfig]) -> None:
        img = draw_text(
            "One two three four five six",
            font_stack=default_stack,
            size=36,
            mode="fit",
            max_width=300,
            max_height=100,
        )
        assert isinstance(img, Image.Image)
        assert img.width > 0
        assert img.height > 0

    def test_fit_mode_shrinks_font_for_tall_content(
        self, font_manager: FontManager
    ) -> None:
        """A tighter max_height forces a smaller font, producing a shorter block."""
        text = "The quick brown fox jumps over the lazy dog"
        img_large = self._canvas((800, 400))
        _, h_large = font_manager.draw(
            img_large,
            text,
            position=(0, 0),
            size=40,
            mode="fit",
            max_width=400,
            max_height=200,
        )
        img_small = self._canvas((800, 400))
        _, h_small = font_manager.draw(
            img_small,
            text,
            position=(0, 0),
            size=40,
            mode="fit",
            max_width=400,
            max_height=60,
        )
        # Tighter box → smaller font → shorter rendered block.
        assert h_small < h_large
        assert h_small <= 60

    def test_fit_mode_truncates_when_min_size_reached(
        self, font_manager: FontManager
    ) -> None:
        """When content overflows even at min_size, the last line is truncated."""
        # 80 words cannot possibly fit in a 1-line box even at the largest
        # font that satisfies min_size=30.
        long_text = " ".join(["word"] * 80)
        img = self._canvas((800, 400))
        max_h = 40
        w, h = font_manager.draw(
            img,
            long_text,
            position=(0, 0),
            size=40,
            mode="fit",
            max_width=400,
            max_height=max_h,
            min_size=30,
        )
        # Output must stay within bounds and must be non-empty (truncated, not dropped).
        assert h <= max_h
        assert w > 0


# endregion
