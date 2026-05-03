"""Integration tests for draw and draw_text (requires real fonts)."""

from __future__ import annotations

import pytest
from PIL import Image

from fontstack import FontConfig, FontManager, draw_text
from fontstack.bidi import _prepare_bidi

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
        with pytest.raises(
            ValueError, match="Provide font_stack, font_dir, or a pre-built manager"
        ):
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


# region Gradient helpers


class TestGradientHelpers:
    def test_is_gradient_plain_color_string(self) -> None:
        from fontstack.gradient import _is_gradient

        assert _is_gradient("red") is False
        assert _is_gradient("black") is False
        assert _is_gradient("skyblue") is False

    def test_is_gradient_non_string(self) -> None:
        from fontstack.gradient import _is_gradient

        assert _is_gradient((255, 0, 0)) is False
        assert _is_gradient(0) is False

    def test_is_gradient_dash_separated(self) -> None:
        from fontstack.gradient import _is_gradient

        assert _is_gradient("red-blue") is True
        assert _is_gradient("#FF0000-#00FF00-#0000FF") is True

    def test_is_gradient_rainbow_preset(self) -> None:
        from fontstack.gradient import _is_gradient

        assert _is_gradient("rainbow") is True

    def test_parse_gradient_rainbow(self) -> None:
        from fontstack.gradient import _parse_gradient

        stops = _parse_gradient("rainbow")
        assert len(stops) == 7
        # First stop should be red-ish.
        assert stops[0] == (255, 0, 0)

    def test_parse_gradient_two_stops(self) -> None:
        from fontstack.gradient import _parse_gradient

        stops = _parse_gradient("red-blue")
        assert len(stops) == 2
        assert stops[0] == (255, 0, 0)
        assert stops[1] == (0, 0, 255)

    def test_parse_gradient_hex_colors(self) -> None:
        from fontstack.gradient import _parse_gradient

        stops = _parse_gradient("#FF0000-#00FF00-#0000FF")
        assert len(stops) == 3
        assert stops[0] == (255, 0, 0)
        assert stops[1] == (0, 255, 0)
        assert stops[2] == (0, 0, 255)

    def test_parse_gradient_single_color_raises(self) -> None:
        from fontstack.gradient import _parse_gradient

        with pytest.raises(ValueError, match="at least two"):
            _parse_gradient("red")

    def test_make_gradient_dimensions(self) -> None:
        from fontstack.gradient import _make_gradient

        img = _make_gradient([(255, 0, 0), (0, 0, 255)], 100, 50)
        assert img.size == (100, 50)
        assert img.mode == "RGBA"

    def test_make_gradient_left_right_colors(self) -> None:
        from fontstack.gradient import _make_gradient

        img = _make_gradient([(255, 0, 0), (0, 0, 255)], 100, 10)
        # Left edge should be red, right edge should be blue.
        left_pixel = img.getpixel((0, 0))
        right_pixel = img.getpixel((99, 0))
        assert isinstance(left_pixel, tuple) and left_pixel[:3] == (255, 0, 0)
        assert isinstance(right_pixel, tuple) and right_pixel[:3] == (0, 0, 255)


# endregion


# region Stroke (outline) rendering


class TestStrokeRendering:
    def _canvas(self, size: tuple[int, int] = (800, 200)) -> Image.Image:
        return Image.new("RGBA", size, (255, 255, 255, 255))

    def test_stroke_produces_wider_bbox(self, font_manager: FontManager) -> None:
        """Text with a stroke outline should occupy more pixels than without."""
        img_plain = self._canvas()
        w_plain, h_plain = font_manager.draw(
            img_plain,
            "Hello",
            position=(10, 10),
            size=40,
            stroke_width=0,
        )
        img_stroke = self._canvas()
        w_stroke, h_stroke = font_manager.draw(
            img_stroke,
            "Hello",
            position=(10, 10),
            size=40,
            stroke_width=4,
            stroke_fill="red",
        )
        assert w_stroke > w_plain or h_stroke > h_plain

    def test_stroke_via_draw_text(self, default_stack: list[FontConfig]) -> None:
        img = draw_text(
            "Outlined",
            font_stack=default_stack,
            size=48,
            stroke_width=3,
            stroke_fill="blue",
        )
        assert isinstance(img, Image.Image)
        assert img.width > 0

    def test_stroke_no_fill_uses_text_color(self, font_manager: FontManager) -> None:
        """When stroke_fill is None, Pillow uses fill as the outline color."""
        img = self._canvas()
        w, h = font_manager.draw(
            img,
            "Test",
            position=(10, 10),
            size=40,
            stroke_width=2,
            stroke_fill=None,
            fill="red",
        )
        assert w > 0 and h > 0


# endregion


# region Shadow rendering


class TestShadowRendering:
    def _canvas(self, size: tuple[int, int] = (800, 200)) -> Image.Image:
        return Image.new("RGBA", size, (255, 255, 255, 255))

    def test_shadow_extends_bbox(self, font_manager: FontManager) -> None:
        """Shadow should make the bounding box larger due to the offset copy."""
        img_plain = self._canvas()
        w_plain, h_plain = font_manager.draw(
            img_plain,
            "Hello",
            position=(10, 10),
            size=40,
        )
        img_shadow = self._canvas()
        w_shadow, h_shadow = font_manager.draw(
            img_shadow,
            "Hello",
            position=(10, 10),
            size=40,
            shadow_color="gray",
            shadow_offset=(5, 5),
        )
        assert w_shadow >= w_plain
        assert h_shadow >= h_plain

    def test_shadow_via_draw_text(self, default_stack: list[FontConfig]) -> None:
        img = draw_text(
            "Shadow",
            font_stack=default_stack,
            size=48,
            shadow_color=(0, 0, 0, 128),
            shadow_offset=(3, 3),
        )
        assert isinstance(img, Image.Image)
        assert img.width > 0

    def test_no_shadow_when_color_is_none(self, font_manager: FontManager) -> None:
        """When shadow_color is None, the output should be identical to no-shadow."""
        img_a = self._canvas()
        w_a, h_a = font_manager.draw(
            img_a,
            "Test",
            position=(10, 10),
            size=40,
            shadow_color=None,
        )
        img_b = self._canvas()
        w_b, h_b = font_manager.draw(
            img_b,
            "Test",
            position=(10, 10),
            size=40,
        )
        assert (w_a, h_a) == (w_b, h_b)


# endregion


# region Gradient rendering


class TestGradientRendering:
    def test_gradient_fill_produces_colored_output(
        self,
        default_stack: list[FontConfig],
    ) -> None:
        """Gradient fill should produce non-uniform colored pixels."""
        img = draw_text(
            "Gradient",
            font_stack=default_stack,
            size=60,
            fill="red-blue",
            padding=2,
        )
        assert img.width > 0
        assert img.height > 0
        # Sample left and right thirds of the image row at the vertical center.
        mid_y = img.height // 2
        left_pixel = img.getpixel((2, mid_y))
        right_pixel = img.getpixel((img.width - 3, mid_y))
        # They should differ in color (gradient moves from red to blue).
        assert isinstance(left_pixel, tuple) and isinstance(right_pixel, tuple)
        assert left_pixel[:3] != right_pixel[:3]

    def test_rainbow_preset(self, default_stack: list[FontConfig]) -> None:
        img = draw_text(
            "Rainbow",
            font_stack=default_stack,
            size=60,
            fill="rainbow",
            padding=2,
        )
        assert img.width > 0
        assert img.height > 0

    def test_gradient_with_stroke(self, default_stack: list[FontConfig]) -> None:
        """Gradient fill combined with a solid stroke outline."""
        img = draw_text(
            "GradStroke",
            font_stack=default_stack,
            size=48,
            fill="red-green-blue",
            stroke_width=2,
            stroke_fill="black",
            padding=4,
        )
        assert img.width > 0

    def test_gradient_with_shadow(self, default_stack: list[FontConfig]) -> None:
        """Gradient fill combined with a drop shadow."""
        img = draw_text(
            "GradShadow",
            font_stack=default_stack,
            size=48,
            fill="rainbow",
            shadow_color="gray",
            shadow_offset=(3, 3),
            padding=4,
        )
        assert img.width > 0

    def test_gradient_with_stroke_and_shadow(
        self,
        default_stack: list[FontConfig],
    ) -> None:
        """All three features combined: gradient + stroke + shadow."""
        img = draw_text(
            "AllFeatures",
            font_stack=default_stack,
            size=48,
            fill="red-blue",
            stroke_width=2,
            stroke_fill="white",
            shadow_color="black",
            shadow_offset=(2, 2),
            background="white",
            padding=8,
        )
        assert isinstance(img, Image.Image)
        assert img.width > 0
        assert img.height > 0

    def test_plain_color_still_works(self, default_stack: list[FontConfig]) -> None:
        """Non-gradient string fills must keep working as before."""
        img = draw_text(
            "Plain",
            font_stack=default_stack,
            size=32,
            fill="red",
            padding=2,
        )
        assert img.width > 0


# endregion


# region Anchor


class TestDrawAnchor:
    def _canvas(self, size: tuple[int, int] = (800, 400)) -> Image.Image:
        return Image.new("RGBA", size, (0, 0, 0, 0))

    def test_default_anchor_matches_lt(self, font_manager: FontManager) -> None:
        """anchor="lt" must produce the same result as omitting anchor entirely."""
        img_default = self._canvas()
        img_lt = self._canvas()

        font_manager.draw(img_default, "Hello", position=(50, 50), size=32)
        font_manager.draw(img_lt, "Hello", position=(50, 50), size=32, anchor="lt")

        assert img_default.tobytes() == img_lt.tobytes()

    def test_center_anchor_shifts_position(self, font_manager: FontManager) -> None:
        """anchor="mm" should shift the text so its center lands at position."""
        cx, cy = 400, 200
        img_center = self._canvas()
        font_manager.draw(img_center, "Hello", position=(cx, cy), size=32, anchor="mm")

        bbox = img_center.getbbox()
        assert bbox is not None
        rendered_cx = (bbox[0] + bbox[2]) // 2
        rendered_cy = (bbox[1] + bbox[3]) // 2
        # Allow ±5 px tolerance for sub-pixel rounding in font metrics.
        assert abs(rendered_cx - cx) <= 5
        assert abs(rendered_cy - cy) <= 5

    def test_bottom_right_anchor(self, font_manager: FontManager) -> None:
        """anchor="rb" should place the text so its bottom-right edge is at position."""
        px, py = 600, 300
        img = self._canvas()
        w, h = font_manager.draw(img, "Hi", position=(px, py), size=32, anchor="rb")

        # The rendered block should end at or near (px, py).
        bbox = img.getbbox()
        assert bbox is not None
        assert abs(bbox[2] - px) <= 10  # right edge ≈ px
        assert abs(bbox[3] - py) <= 10  # bottom edge ≈ py

    def test_top_center_anchor(self, font_manager: FontManager) -> None:
        """anchor="mt" centers horizontally but keeps the top at position."""
        px, py = 400, 50
        img = self._canvas()
        font_manager.draw(img, "Hello", position=(px, py), size=32, anchor="mt")

        bbox = img.getbbox()
        assert bbox is not None
        rendered_cx = (bbox[0] + bbox[2]) // 2
        assert abs(rendered_cx - px) <= 5  # centered horizontally
        assert abs(bbox[1] - py) <= 5  # top edge preserved

    def test_invalid_anchor_raises(self, font_manager: FontManager) -> None:
        img = self._canvas()
        with pytest.raises(ValueError, match="anchor must be one of"):
            font_manager.draw(img, "Hello", position=(0, 0), anchor="xx")  # type: ignore[arg-type]

    def test_emoji_leading_text_not_clipped(self, font_manager: FontManager) -> None:
        """Text starting with an emoji must not be shifted off the left edge.

        _measure_block advances x by ctx.size for emoji segments (not by
        font.getlength, which returns a .notdef advance).  A wrong advance
        inflates vis_l and causes x_off = -vis_l to push the block off-canvas.
        """
        px, py = 100, 100
        img = self._canvas()
        font_manager.draw(img, "🏆 Winner", position=(px, py), size=32, anchor="lt")

        bbox = img.getbbox()
        assert bbox is not None
        # The leftmost rendered pixel must be at or to the right of px.
        # A negative x_off bug would place it significantly left of px.
        assert bbox[0] >= px - 2  # allow 2 px for sub-pixel bearing


# endregion
