"""13_fit_mode - mode="fit": wrap, shrink to min_size, then truncate.  See README.md."""

from pathlib import Path

from PIL import Image

from fontstack import FontConfig, FontManager

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"

manager = FontManager(
    default_stack=[FontConfig(path=str(FONTS / "NotoSans[wdth,wght].ttf"))]
)

# region Layout constants - shared by every strip

BOX_W = 540  # strip canvas width
BOX_H = 110  # strip canvas height
PAD_X = 20  # horizontal padding (left & right)
PAD_Y = 14  # vertical padding (top only; used as position offset)
SIZE = 52  # starting font size in points
MIN_SIZE = 12  # minimum font size; the final strip always truncates at this threshold
GAP = 6  # gap between strips in the final canvas

BG_COLORS = [
    (245, 245, 255, 255),  # lavender - short text, full size
    (240, 252, 245, 255),  # mint     - wraps, font shrinks to fit
    (255, 251, 235, 255),  # amber    - font shrinks more to fit
    (255, 240, 240, 255),  # rose     - hits min_size, last line truncated
]

texts = [
    # 1. Short text - a single line renders at the full starting size.
    "Fit mode.",
    # 2. A common sentence - wraps to a few lines; font must shrink to fit
    # the block within BOX_H - PAD_Y * 2 pixels.
    "The quick brown fox jumps over the lazy dog.",
    # 3. A longer sentence - more words force the font to shrink further.
    "Typography is the art and technique of arranging type to make written language legible, readable, and appealing when displayed.",
    # 4. Dense text - font shrinks to MIN_SIZE and still overflows, so the
    # last visible line is truncated with "...".
    (
        "Pack my box with five dozen liquor jugs. How vexingly quick daft "
        "zebras jump! The five boxing wizards jump quickly. Sphinx of black "
        "quartz, judge my vow. Blowzy red vixens fight for a quick jump. "
        "Two driven jocks help fax my big quiz. Quick zephyrs blow, vexing "
        "daft Jim. The jay, pig, fox, zebra and my wolves quack!"
    ),
]

# endregion

# region Render

strips = []
for text, bg in zip(texts, BG_COLORS, strict=True):
    strip = Image.new("RGBA", (BOX_W, BOX_H), bg)
    manager.draw_text_smart(
        image=strip,
        text=text,
        position=(PAD_X, PAD_Y),
        size=SIZE,
        mode="fit",
        max_width=BOX_W - PAD_X * 2,
        max_height=BOX_H - PAD_Y * 2,
        min_size=MIN_SIZE,
        fill=(30, 30, 30),
    )
    strips.append(strip)

# endregion

# region Assemble and save

H = BOX_H * len(strips) + GAP * (len(strips) - 1)
canvas = Image.new("RGBA", (BOX_W, H), (200, 200, 205, 255))
y = 0
for strip in strips:
    canvas.paste(strip, (0, y))
    y += BOX_H + GAP

out = Path(__file__).parent / "output.png"
canvas.convert("RGB").save(out)
print(f"Saved {BOX_W}×{H} px → {out}")
# endregion
