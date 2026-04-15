"""Tests for the cmap loading helper (_load_cmap)."""

from __future__ import annotations

from pathlib import Path

import pytest

from fontstack.cmap import _load_cmap

FONTS_DIR = Path(__file__).parent / "fonts"
NOTO_SANS = FONTS_DIR / "NotoSans[wdth,wght].ttf"


def test_load_cmap_returns_frozenset(noto_sans: str) -> None:
    cmap = _load_cmap(noto_sans)
    assert isinstance(cmap, frozenset)


def test_load_cmap_contains_basic_latin(noto_sans: str) -> None:
    cmap = _load_cmap(noto_sans)
    # Basic Latin block: A–Z, a–z, 0–9 must all be present in Noto Sans.
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789":
        assert ord(char) in cmap, f"Expected {char!r} (U+{ord(char):04X}) in cmap"


def test_load_cmap_contains_cyrillic(noto_sans: str) -> None:
    cmap = _load_cmap(noto_sans)
    # Cyrillic А (U+0410) should be present in Noto Sans.
    assert 0x0410 in cmap


def test_load_cmap_contains_greek(noto_sans: str) -> None:
    cmap = _load_cmap(noto_sans)
    # Greek α (U+03B1) should be present in Noto Sans.
    assert 0x03B1 in cmap


def test_load_cmap_arabic_font_contains_arabic(noto_sans_arabic: str) -> None:
    cmap = _load_cmap(noto_sans_arabic)
    # Arabic letter Alef (U+0627) must be in Noto Sans Arabic.
    assert 0x0627 in cmap


def test_load_cmap_nonexistent_file_raises() -> None:
    with pytest.raises((FileNotFoundError, OSError)):
        _load_cmap("/nonexistent/path/font.ttf")


def test_load_cmap_nonempty(noto_sans: str) -> None:
    cmap = _load_cmap(noto_sans)
    assert len(cmap) > 100
