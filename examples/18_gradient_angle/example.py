"""18_gradient_angle -- gradient angle on multi-line text.

Renders the same wrapped text at five different gradient angles so the
effect of the angle parameter is easy to compare side by side.
See README.md for details.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from fontstack import FontConfig, draw_text

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"
OUT = Path(__file__).parent / "output.png"

NOTO = str(FONTS / "NotoSans[wdth,wght].ttf")
STACK = [FontConfig(path=NOTO)]

LABEL_H = 36
SPACING = 16

TEXT = "The quick brown fox jumps over the lazy dog near the riverbank"

# (label, gradient_angle)
variants: list[tuple[str, float]] = [
    ("gradient_angle=0 (left to right)", 0.0),
    ("gradient_angle=15 (default)", 15.0),
    ("gradient_angle=30", 30.0),
    ("gradient_angle=45", 45.0),
    ("gradient_angle=90 (top to bottom)", 90.0),
]

# Render each variant.
panels: list[Image.Image] = []
for _, angle in variants:
    img = draw_text(
        TEXT,
        font_stack=STACK,
        size=48,
        fill="red-orange-yellow-green-cyan-blue-violet",
        mode="wrap",
        max_width=500,
        gradient_angle=angle,
        background=(20, 20, 25),
        padding=40,
    )
    panels.append(img)

# Build composite.
label_font = ImageFont.truetype(NOTO, 20)
total_w = max(p.width for p in panels)
total_h = sum(p.height + LABEL_H + SPACING for p in panels) - SPACING + SPACING * 2
canvas = Image.new("RGB", (total_w + SPACING * 2, total_h), (25, 25, 30))
draw = ImageDraw.Draw(canvas)

y = SPACING
for (label, _), panel in zip(variants, panels, strict=True):
    draw.text((SPACING, y), label, fill=(160, 160, 170), font=label_font)
    y += LABEL_H
    canvas.paste(panel, (SPACING, y))
    y += panel.height + SPACING

canvas.save(OUT)
print(f"Saved {OUT.name}: {canvas.width}x{canvas.height} px")
