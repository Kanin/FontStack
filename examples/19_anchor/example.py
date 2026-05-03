"""19_anchor -- anchor points for FontManager.draw().

Renders the same short text nine times in a 3×3 grid.  Every cell uses a
different ``anchor`` value; all nine draws aim at the exact centre of their
cell.  A crosshair marks that reference point so you can see exactly how the
text block is positioned relative to it.  See README.md for details.
"""

from pathlib import Path

from PIL import Image, ImageDraw

from fontstack import Anchor, FontConfig, FontManager

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"
OUT = Path(__file__).parent / "output.png"

manager = FontManager(
    default_stack=[FontConfig(path=str(FONTS / "NotoSans[wdth,wght].ttf"))]
)

TEXT = "FontStack"
FONT_SIZE = 28
WEIGHT = 700

# Grid layout
COLS, ROWS = 3, 3
CELL_W, CELL_H = 280, 110
PAD = 12  # inner padding so text never clips at the edge
CROSS_R = 4  # crosshair circle radius
CROSS_COLOR = (220, 60, 60, 255)

ANCHORS: list[Anchor] = [
    "lt",
    "mt",
    "rt",
    "lm",
    "mm",
    "rm",
    "lb",
    "mb",
    "rb",
]

LABELS = {
    "lt": "lt  (top-left)",
    "mt": "mt  (top-center)",
    "rt": "rt  (top-right)",
    "lm": "lm  (mid-left)",
    "mm": "mm  (center)",
    "rm": "rm  (mid-right)",
    "lb": "lb  (bottom-left)",
    "mb": "mb  (bottom-center)",
    "rb": "rb  (bottom-right)",
}

# Tint each cell so the 3×3 grid is easy to scan
TINTS = [
    (248, 244, 255),
    (244, 248, 255),
    (244, 255, 248),
    (255, 248, 244),
    (255, 255, 244),
    (244, 255, 255),
    (255, 244, 248),
    (248, 255, 244),
    (255, 244, 255),
]

GAP = 2
CANVAS_W = CELL_W * COLS + GAP * (COLS - 1)
CANVAS_H = CELL_H * ROWS + GAP * (ROWS - 1)
canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (180, 180, 180, 255))

label_font_size = 13

for idx, (anchor, tint) in enumerate(zip(ANCHORS, TINTS, strict=True)):
    col = idx % COLS
    row = idx // COLS
    ox = col * (CELL_W + GAP)
    oy = row * (CELL_H + GAP)

    cell = Image.new("RGBA", (CELL_W, CELL_H), (*tint, 255))
    draw = ImageDraw.Draw(cell)

    # Reference point: centre of each cell
    rx, ry = CELL_W // 2, CELL_H // 2

    # Draw thin crosshair lines
    draw.line([(rx - 12, ry), (rx + 12, ry)], fill=CROSS_COLOR, width=1)
    draw.line([(rx, ry - 12), (rx, ry + 12)], fill=CROSS_COLOR, width=1)
    draw.ellipse(
        [rx - CROSS_R, ry - CROSS_R, rx + CROSS_R, ry + CROSS_R],
        fill=CROSS_COLOR,
    )

    # Draw the main text using the anchor
    manager.draw(
        cell,
        TEXT,
        position=(rx, ry),
        size=FONT_SIZE,
        weight=WEIGHT,
        fill=(30, 30, 50),
        anchor=anchor,
    )

    # Small anchor label in the corner
    manager.draw(
        cell,
        LABELS[anchor],
        position=(PAD, CELL_H - PAD),
        size=label_font_size,
        weight=400,
        fill=(100, 100, 120),
        anchor="lb",
    )

    canvas.paste(cell, (ox, oy))

canvas.convert("RGB").save(OUT)
print(f"Saved {CANVAS_W}×{CANVAS_H} px → {OUT}")
