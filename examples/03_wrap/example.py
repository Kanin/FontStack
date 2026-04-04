"""03_wrap - word-wrap at a fixed max_width with mode="wrap".  See README.md."""

from pathlib import Path

from fontstack import FontConfig, draw_text

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"

img = draw_text(
    (
        "Pack my box with five dozen liquor jugs. "
        "The five boxing wizards jump quickly. "
        "How vexingly quick daft zebras jump. "
        "The quick brown fox jumps over the lazy dog."
    ),
    font_stack=[FontConfig(path=str(FONTS / "NotoSans[wdth,wght].ttf"))],
    size=36,
    mode="wrap",
    max_width=560,
    line_spacing=1.5,
    fill=(30, 30, 30),
    background="white",
    padding=32,
)
img.save(Path(__file__).parent / "output.png")
print(f"Saved {img.width}x{img.height} px")
