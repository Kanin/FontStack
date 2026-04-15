"""17_combined -- all features together: gradient fills, gradient outlines,
gradient shadows, outline, shadow, and multi-script.

Renders eight combined-effect variants onto a single composite image.
See README.md for details.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from fontstack import FontConfig, FontManager, draw_text

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"
OUT = Path(__file__).parent / "output.png"

NOTO = str(FONTS / "NotoSans[wdth,wght].ttf")
NOTO_AR = str(FONTS / "NotoSansArabic[wdth,wght].ttf")
STACK = [FontConfig(path=NOTO), FontConfig(path=NOTO_AR)]

mgr = FontManager(default_stack=STACK)

LABEL_H = 36
SPACING = 16

# (label, text, background, extra kwargs)
variants: list[tuple[str, str, tuple | str, dict]] = [
    (
        "Rainbow + outline + shadow (Latin)",
        "Full Featured!",
        (240, 240, 240),
        {
            "size": 72,
            "fill": "rainbow",
            "stroke_width": 3,
            "stroke_fill": "black",
            "shadow_color": (0, 0, 0, 160),
            "shadow_offset": (4, 4),
        },
    ),
    (
        "Warm gradient + outline + shadow (Arabic)",
        "\u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645",
        (240, 230, 220),
        {
            "size": 64,
            "fill": "gold-darkorange-crimson",
            "stroke_width": 2,
            "stroke_fill": (40, 20, 0),
            "shadow_color": (0, 0, 0, 140),
            "shadow_offset": (3, 3),
        },
    ),
    (
        "Wrapped rainbow with shadow",
        "The quick brown fox jumps over the lazy dog",
        (240, 240, 240),
        {
            "size": 48,
            "fill": "rainbow",
            "stroke_width": 2,
            "stroke_fill": "black",
            "shadow_color": "gray",
            "shadow_offset": (3, 3),
            "mode": "wrap",
            "max_width": 500,
        },
    ),
    (
        "Scale-to-fit with gradient + outline",
        "This long sentence will shrink to fit within the box",
        (220, 220, 225),
        {
            "size": 60,
            "fill": "cyan-magenta-yellow",
            "stroke_width": 2,
            "stroke_fill": (30, 30, 30),
            "shadow_color": (0, 0, 0, 120),
            "shadow_offset": (2, 2),
            "mode": "scale",
            "max_width": 600,
            "min_size": 16,
        },
    ),
    (
        "Mixed-script showcase",
        "Hello \u0645\u0631\u062d\u0628\u0627 Bonjour Hola",
        (230, 230, 235),
        {
            "size": 52,
            "fill": "red-orange-yellow-green-blue",
            "stroke_width": 2,
            "stroke_fill": (30, 30, 50),
            "shadow_color": (0, 0, 0, 160),
            "shadow_offset": (3, 3),
        },
    ),
    (
        "Heavy bold weight with all effects",
        "BOLD FIRE",
        (240, 235, 230),
        {
            "size": 80,
            "weight": 900,
            "fill": "red-orange-yellow",
            "stroke_width": 4,
            "stroke_fill": (40, 0, 0),
            "shadow_color": (0, 0, 0, 140),
            "shadow_offset": (5, 5),
        },
    ),
    (
        "Gradient outline + gradient shadow",
        "All Gradients!",
        (15, 15, 25),
        {
            "size": 72,
            "fill": "cyan-magenta",
            "stroke_width": 4,
            "stroke_fill": "gold-darkorange-crimson",
            "shadow_color": "blue-purple-magenta",
            "shadow_offset": (5, 5),
        },
    ),
    (
        "Rainbow outline on white text with gradient shadow",
        "Neon Glow",
        (10, 10, 20),
        {
            "size": 80,
            "fill": "white",
            "stroke_width": 5,
            "stroke_fill": "rainbow",
            "shadow_color": "cyan-blue-purple",
            "shadow_offset": (4, 4),
        },
    ),
]

# Render each variant.
panels: list[Image.Image] = []
for _, text, bg, kwargs in variants:
    img = draw_text(text, manager=mgr, background=bg, padding=40, **kwargs)
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
