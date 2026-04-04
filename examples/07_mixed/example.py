"""07_mixed - mixed Latin and Arabic in one string via per-character font routing.  See README.md."""

from pathlib import Path

from fontstack import FontConfig, draw_text

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"

img = draw_text(
    "Hello, مرحبا! Welcome to FontStack.",
    font_stack=[
        FontConfig(path=str(FONTS / "NotoSans[wdth,wght].ttf")),
        FontConfig(path=str(FONTS / "NotoSansArabic[wdth,wght].ttf")),
    ],
    size=52,
    fill=(30, 30, 30),
    background="white",
    padding=36,
)
img.save(Path(__file__).parent / "output.png")
print(f"Saved {img.width}x{img.height} px")
