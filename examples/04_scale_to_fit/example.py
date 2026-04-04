"""04_scale_to_fit - mode="scale" auto-shrinks the font to fill max_width.  See README.md."""

from pathlib import Path

from PIL import Image

from fontstack import FontConfig, FontManager

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"

manager = FontManager(
    default_stack=[FontConfig(path=str(FONTS / "NotoSans[wdth,wght].ttf"))]
)

texts = [
    "Short",
    "A medium-length phrase fits here",
    "The quick brown fox jumps over the lazy dog",
]

CANVAS_W = 540
STRIP_H = 100
PAD_X = 20
GAP = 6

strips = []
for text in texts:
    strip = Image.new("RGBA", (CANVAS_W, STRIP_H), (248, 248, 255, 255))
    manager.draw(
        image=strip,
        text=text,
        position=(PAD_X, 20),
        size=60,
        mode="scale",
        max_width=CANVAS_W - PAD_X * 2,
        min_size=12,
        fill=(30, 30, 30),
    )
    strips.append(strip)

H = STRIP_H * len(strips) + GAP * (len(strips) - 1)
canvas = Image.new("RGBA", (CANVAS_W, H), (210, 210, 215, 255))
y = 0
for strip in strips:
    canvas.paste(strip, (0, y))
    y += STRIP_H + GAP
canvas.convert("RGB").save(Path(__file__).parent / "output.png")
print(f"Saved {CANVAS_W}x{H} px")
