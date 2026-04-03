"""06_arabic - Arabic text with automatic reshaping and BiDi reordering.  See README.md."""

from pathlib import Path

from fontstack import FontConfig, render_text

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"

img = render_text(
    "مرحبا بالعالم",  # "Hello, World" in Arabic
    font_stack=[FontConfig(path=str(FONTS / "NotoSansArabic[wdth,wght].ttf"))],
    size=72,
    fill=(30, 30, 30),
    background="white",
    padding=40,
)
img.save(Path(__file__).parent / "output.png")
print(f"Saved {img.width}x{img.height} px")
