"""15_shadow -- drop shadows on various scripts and emoji.

Renders five shadow variants onto a single composite image.
Emoji shadows appear as solid-color silhouettes, not duplicate emoji.
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

LABEL_H = 36
SPACING = 16

# (label, text, background, extra kwargs)
variants: list[tuple[str, str, tuple, dict]] = [
    (
        "Simple dark shadow",
        "Shadow Demo",
        (70, 130, 180),
        {
            "size": 72,
            "fill": "white",
            "shadow_color": (0, 0, 0, 180),
            "shadow_offset": (4, 4),
        },
    ),
    (
        "Shadow with emoji (silhouette)",
        "Rocket \U0001f680 Launch \U0001f6f8 Stars \u2728",
        (200, 210, 230),
        {
            "size": 52,
            "fill": (30, 30, 60),
            "shadow_color": (0, 0, 0, 140),
            "shadow_offset": (3, 3),
        },
    ),
    (
        "Shadow on Arabic text",
        "\u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645",
        (220, 200, 230),
        {
            "size": 64,
            "fill": (60, 20, 80),
            "shadow_color": (0, 0, 0, 160),
            "shadow_offset": (3, 3),
        },
    ),
    (
        "Large offset shadow on mixed text",
        "Hello \u0645\u0631\u062d\u0628\u0627 World",
        (230, 230, 230),
        {
            "size": 56,
            "fill": (30, 30, 30),
            "shadow_color": (120, 120, 120),
            "shadow_offset": (6, 6),
        },
    ),
    (
        "Shadow combined with outline",
        "Outlined + Shadow",
        (240, 240, 240),
        {
            "size": 60,
            "fill": (30, 30, 80),
            "stroke_width": 2,
            "stroke_fill": "navy",
            "shadow_color": (0, 0, 0, 160),
            "shadow_offset": (4, 4),
        },
    ),
]

# Render each variant.
panels: list[Image.Image] = []
for _, text, bg, kwargs in variants:
    img = draw_text(text, font_stack=STACK, background=bg, padding=40, **kwargs)
    panels.append(img)

# Build composite.
label_font = ImageFont.truetype(NOTO, 20)
total_w = max(p.width for p in panels)
total_h = sum(p.height + LABEL_H + SPACING for p in panels) - SPACING + SPACING * 2
canvas = Image.new("RGB", (total_w + SPACING * 2, total_h), (25, 25, 30))
draw = ImageDraw.Draw(canvas)

y = SPACING
for (label, _, _, _), panel in zip(variants, panels, strict=True):
    draw.text((SPACING, y), label, fill=(160, 160, 170), font=label_font)
    y += LABEL_H
    canvas.paste(panel, (SPACING, y))
    y += panel.height + SPACING

canvas.save(OUT)
print(f"Saved {OUT.name}: {canvas.width}x{canvas.height} px")
