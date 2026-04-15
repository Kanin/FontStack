"""Tests for font directory scanning and font_dir constructor arg."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from fontstack import FontConfig, FontManager, draw_text, scan_font_dir

FONTS_DIR = Path(__file__).parent / "fonts"


class TestScanFontDir:
    def test_finds_all_fonts(self) -> None:
        configs = scan_font_dir(FONTS_DIR)
        # tests/fonts/ contains 12 .ttf files (no .ttc), so 12 configs expected.
        assert len(configs) == 12

    def test_returns_font_configs(self) -> None:
        configs = scan_font_dir(FONTS_DIR)
        assert all(isinstance(c, FontConfig) for c in configs)

    def test_nonexistent_dir_raises(self) -> None:
        with pytest.raises(FileNotFoundError, match="does not exist"):
            scan_font_dir("/nonexistent/path/to/fonts")

    def test_empty_dir_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="No font files"):
            scan_font_dir(tmp_path)

    def test_deterministic_order(self) -> None:
        configs_a = scan_font_dir(FONTS_DIR)
        configs_b = scan_font_dir(FONTS_DIR)
        assert configs_a == configs_b
        # Verify sorted by filename (case-insensitive).
        names = [Path(c.path).name.lower() for c in configs_a]
        assert names == sorted(names)

    def test_accepts_string_path(self) -> None:
        configs = scan_font_dir(str(FONTS_DIR))
        assert len(configs) >= 1

    def test_recursive_flag(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        # Copy a font into the subdirectory.
        src = next(FONTS_DIR.glob("*.ttf"))
        (sub / src.name).write_bytes(src.read_bytes())
        # Non-recursive should find nothing in the top-level tmp_path.
        with pytest.raises(ValueError, match="No font files"):
            scan_font_dir(tmp_path, recursive=False)
        # Recursive should find the font in the subdirectory.
        configs = scan_font_dir(tmp_path, recursive=True)
        assert len(configs) == 1


class TestFontManagerFontDir:
    def test_constructor_with_font_dir(self) -> None:
        mgr = FontManager(font_dir=FONTS_DIR)
        assert len(mgr.default_stack) == 12

    def test_font_dir_property(self) -> None:
        mgr = FontManager(font_dir=FONTS_DIR)
        assert mgr.font_dir == FONTS_DIR

    def test_font_dir_none_when_stack_used(self) -> None:
        mgr = FontManager(
            default_stack=[FontConfig(path=str(next(FONTS_DIR.glob("*.ttf"))))]
        )
        assert mgr.font_dir is None

    def test_both_raises(self) -> None:
        stack = [FontConfig(path=str(next(FONTS_DIR.glob("*.ttf"))))]
        with pytest.raises(ValueError, match="not both"):
            FontManager(default_stack=stack, font_dir=FONTS_DIR)

    def test_neither_raises(self) -> None:
        with pytest.raises(ValueError):
            FontManager()

    def test_draw_with_font_dir(self) -> None:
        mgr = FontManager(font_dir=FONTS_DIR)
        img = Image.new("RGBA", (800, 100), "white")
        w, h = mgr.draw(img, "Hello World", position=(10, 10), size=32)
        assert w > 0 and h > 0


class TestDrawTextFontDir:
    def test_draw_text_with_font_dir(self) -> None:
        result = draw_text("Hello World", font_dir=FONTS_DIR, size=32)
        assert result.width > 0 and result.height > 0

    def test_draw_text_font_dir_ignored_when_manager(self) -> None:
        mgr = FontManager(font_dir=FONTS_DIR)
        result = draw_text("Hello", manager=mgr, size=32)
        assert result.width > 0
