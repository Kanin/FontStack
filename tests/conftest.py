"""Shared pytest fixtures for fontstack tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from fontstack import FontConfig, FontManager

FONTS_DIR = Path(__file__).parent / "fonts"

NOTO_SANS = FONTS_DIR / "NotoSans[wdth,wght].ttf"
NOTO_SANS_ARABIC = FONTS_DIR / "NotoSansArabic[wdth,wght].ttf"


def _require_font(path: Path) -> str:
    """Return the font path as a str, skipping the test if the file is missing."""
    if not path.exists():
        pytest.skip(f"Test font not found: {path.name} - run font download step.")
    return str(path)


@pytest.fixture()
def noto_sans() -> str:
    return _require_font(NOTO_SANS)


@pytest.fixture()
def noto_sans_arabic() -> str:
    return _require_font(NOTO_SANS_ARABIC)


@pytest.fixture()
def default_stack(noto_sans: str, noto_sans_arabic: str) -> list[FontConfig]:
    """A two-font stack: Noto Sans (primary) + Noto Sans Arabic (fallback)."""
    return [
        FontConfig(path=noto_sans),
        FontConfig(path=noto_sans_arabic),
    ]


@pytest.fixture()
def font_manager(default_stack: list[FontConfig]) -> FontManager:
    """A pre-built FontManager using the two-font test stack."""
    return FontManager(default_stack=default_stack)
