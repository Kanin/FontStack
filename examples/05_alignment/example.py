"""05_alignment - left, center, and right alignment in mode="wrap".  See README.md."""

from pathlib import Path

from PIL import Image

from fontstack import FontConfig, FontManager, HorizontalAlign

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"

manager = FontManager(
    default_stack=[FontConfig(path=str(FONTS / "NotoSans[wdth,wght].ttf"))]
)

TEXT = "The quick brown fox jumps over the lazy dog"

BOX_W = 560
BOX_H = 130
PAD = 24
BG_COLORS = [(252, 246, 246), (246, 252, 246), (246, 246, 252)]  # rose, sage, blue

strips = []
ALIGNMENTS: list[HorizontalAlign] = ["left", "center", "right"]
for align, bg in zip(ALIGNMENTS, BG_COLORS, strict=True):
    strip = Image.new("RGBA", (BOX_W, BOX_H), (*bg, 255))
    manager.draw_text_smart(
        image=strip,
        text=TEXT,
        position=(PAD, PAD),
        size=30,
        mode="wrap",
        max_width=BOX_W - PAD * 2,
        align=align,
        fill=(30, 30, 30),
    )
    strips.append(strip)

GAP = 6
H = BOX_H * len(strips) + GAP * (len(strips) - 1)
result = Image.new("RGBA", (BOX_W, H), (200, 200, 200, 255))
y = 0
for strip in strips:
    result.paste(strip, (0, y))
    y += BOX_H + GAP
result.convert("RGB").save(Path(__file__).parent / "output.png")
print(f"Saved {BOX_W}x{H} px")
