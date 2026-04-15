"""FontStack - Unicode text rendering with automatic per-character font fallback."""

__version__ = "0.3.0"

from fontstack.discovery import scan_font_dir
from fontstack.draw import draw_text
from fontstack.manager import FontManager
from fontstack.types import (
    FillType,
    FontConfig,
    HorizontalAlign,
    RenderMode,
    VariationAxes,
)

__all__ = [
    "FontConfig",
    "FontManager",
    "FillType",
    "HorizontalAlign",
    "RenderMode",
    "VariationAxes",
    "draw_text",
    "scan_font_dir",
]
