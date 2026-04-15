"""16_gradient -- gradient text fills, gradient outlines, and gradient shadows.

Renders eight gradient variants onto a single composite image.
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
variants: list[tuple[str, str, tuple | str, dict]] = [
    (
        "Rainbow preset",
        "Rainbow Text!",
        "black",
        {"size": 72, "fill": "rainbow"},
    ),
    (
        "Two-stop gradient (red to blue)",
        "Red to Blue",
        (240, 240, 240),
        {"size": 64, "fill": "red-blue"},
    ),
    (
        "Three-stop hex gradient",
        "Hex Gradient",
        (30, 30, 30),
        {"size": 56, "fill": "#FF6600-#FFFF00-#00CC66"},
    ),
    (
        "Warm gradient on Arabic",
        "\u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645",
        (240, 240, 240),
        {"size": 64, "fill": "gold-darkorange-crimson"},
    ),
    (
        "Gradient with white outline",
        "Gradient + Outline",
        (20, 20, 20),
        {"size": 64, "fill": "cyan-magenta", "stroke_width": 3, "stroke_fill": "white"},
    ),
    (
        "Rainbow with shadow on light background",
        "Rainbow Shadow",
        (230, 230, 235),
        {
            "size": 64,
            "fill": "rainbow",
            "shadow_color": (0, 0, 0, 140),
            "shadow_offset": (3, 3),
        },
    ),
    (
        "Gradient outline on white text",
        "Gradient Outline",
        (20, 20, 25),
        {"size": 72, "fill": "white", "stroke_width": 4, "stroke_fill": "rainbow"},
    ),
    (
        "Gradient shadow behind solid text",
        "Gradient Shadow",
        (245, 245, 250),
        {
            "size": 72,
            "fill": (30, 30, 50),
            "shadow_color": "red-orange-yellow-green-blue",
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
