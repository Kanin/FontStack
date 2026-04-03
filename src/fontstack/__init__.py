"""FontStack - Unicode text rendering with automatic per-character font fallback."""

__version__ = "0.1.1"

from fontstack._core import (
    FillType,
    FontConfig,
    FontManager,
    HorizontalAlign,
    RenderMode,
    VariationAxes,
    render_text,
)

__all__ = [
    "FontConfig",
    "FontManager",
    "FillType",
    "HorizontalAlign",
    "RenderMode",
    "VariationAxes",
    "render_text",
]
