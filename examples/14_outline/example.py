"""14_outline -- text outlines (strokes) on Latin, Arabic, and mixed scripts.

Renders four outline variants onto a single composite image.
See README.md for details.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from fontstack import FontConfig, draw_text

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"
OUT = Path(__file__).parent / "output.png"

NOTO = str(FONTS / "NotoSans[wdth,wght].ttf")
NOTO_AR = str(FONTS / "NotoSansArabic[wdth,wght].ttf")
STACK = [FontConfig(path=NOTO), FontConfig(path=NOTO_AR)]

BG = (25, 25, 30)
PANEL_PAD = 40
LABEL_H = 36
SPACING = 16

# Each variant: (label, text, extra kwargs)
# Each panel gets its own background that contrasts with the outline color.
variants: list[tuple[str, str, dict]] = [
    (
        "White text, black outline on grey",
        "Outlined Text",
        {
            "size": 72,
            "fill": "white",
            "stroke_width": 3,
            "stroke_fill": "black",
            "background": (120, 120, 130),
        },
    ),
    (
        "Blue outline on warm background",
        "Colourful Outlines",
        {
            "size": 64,
            "fill": (255, 200, 80),
            "stroke_width": 3,
            "stroke_fill": (0, 80, 200),
            "background": (240, 235, 220),
        },
    ),
    (
        "Thick bright outline on Arabic",
        "\u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645",
        {
            "size": 64,
            "fill": (255, 255, 255),
            "stroke_width": 4,
            "stroke_fill": (200, 60, 20),
            "background": (30, 30, 60),
        },
    ),
    (
        "Crimson outline on light background",
        "Hello \u0645\u0631\u062d\u0628\u0627 World",
        {
            "size": 56,
            "fill": (30, 30, 60),
            "stroke_width": 3,
            "stroke_fill": "crimson",
            "background": (230, 230, 235),
        },
    ),
]

# Render each variant individually.
panels: list[Image.Image] = []
for _, text, kwargs in variants:
    img = draw_text(text, font_stack=STACK, padding=PANEL_PAD, **kwargs)
    panels.append(img)

# Build a composite with labels above each panel.
label_font = ImageFont.truetype(NOTO, 20)
total_w = max(p.width for p in panels)
total_h = sum(p.height + LABEL_H + SPACING for p in panels) - SPACING + SPACING * 2
canvas = Image.new("RGB", (total_w + SPACING * 2, total_h), BG)
draw = ImageDraw.Draw(canvas)

y = SPACING
for (label, _, _), panel in zip(variants, panels, strict=True):
    draw.text((SPACING, y), label, fill=(160, 160, 170), font=label_font)
    y += LABEL_H
    canvas.paste(panel, (SPACING, y))
    y += panel.height + SPACING

canvas.save(OUT)
print(f"Saved {OUT.name}: {canvas.width}x{canvas.height} px")
