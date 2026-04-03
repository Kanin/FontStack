"""02_weights - variable font weight spectrum, wght 100–900.  See README.md."""

from pathlib import Path

from PIL import Image

from fontstack import FontConfig, FontManager, render_text

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"

manager = FontManager(
    default_stack=[FontConfig(path=str(FONTS / "NotoSans[wdth,wght].ttf"))]
)

rows = []
for weight in [100, 200, 300, 400, 500, 600, 700, 800, 900]:
    row = render_text(
        f"wght {weight}  The quick brown fox jumps over the lazy dog",
        font_stack=[],
        manager=manager,
        size=34,
        weight=weight,
        fill=(25, 25, 25),
        background=(250, 250, 250),
        padding=12,
    )
    rows.append(row)

W = max(r.width for r in rows)
H = sum(r.height for r in rows) + (len(rows) - 1) * 4
canvas = Image.new("RGBA", (W, H), (250, 250, 250, 255))
y = 0
for row in rows:
    canvas.paste(row, (0, y), row)
    y += row.height + 4
canvas.convert("RGB").save(Path(__file__).parent / "output.png")
print(f"Saved {W}x{H} px")
