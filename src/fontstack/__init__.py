"""FontStack - Unicode text rendering with automatic per-character font fallback."""

__version__ = "0.2.0"

from fontstack._core import (
    FillType,
    FontConfig,
    FontManager,
    HorizontalAlign,
    RenderMode,
    VariationAxes,
    draw_text,
)

__all__ = [
    "FontConfig",
    "FontManager",
    "FillType",
    "HorizontalAlign",
    "RenderMode",
    "VariationAxes",
    "draw_text",
]
