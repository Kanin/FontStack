"""10_scripts - Devanagari, Hebrew, Bengali, and Thai via font fallback.  See README.md."""

from pathlib import Path

from PIL import Image

from fontstack import FontConfig, FontManager, draw_text

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"

STACK = [
    FontConfig(path=str(FONTS / "NotoSans[wdth,wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansDevanagari[wdth,wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansHebrew[wdth,wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansBengali[wdth,wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansThai[wdth,wght].ttf")),
]

manager = FontManager(default_stack=STACK)

ROWS = [
    ("Hindi", "हिंदी: नमस्ते दुनिया"),
    ("Hebrew", "עברית: שלום עולם"),
    ("Bengali", "বাংলা: হ্যালো পৃথিবী"),
    ("Thai", "ภาษาไทย: สวัสดีชาวโลก"),
]

BG_COLORS = [
    (252, 248, 244),  # warm
    (244, 248, 252),  # cool blue
    (244, 252, 248),  # sage
    (252, 244, 252),  # lavender
]
BOX_W = 620
PAD = 20

strips = []
for (label, text), bg in zip(ROWS, BG_COLORS, strict=True):
    row = draw_text(
        f"{label}:  {text}",
        font_stack=[],
        manager=manager,
        size=40,
        fill=(25, 25, 25),
        background=bg,
        padding=PAD,
    )
    # Pad each row to uniform width
    if row.width < BOX_W:
        padded = Image.new("RGBA", (BOX_W, row.height), (*bg, 255))
        padded.paste(row, (0, 0), row)
        row = padded
    strips.append(row)

GAP = 5
H = sum(s.height for s in strips) + GAP * (len(strips) - 1)
canvas = Image.new("RGBA", (BOX_W, H), (200, 200, 200, 255))
y = 0
for strip in strips:
    canvas.paste(strip, (0, y), strip)
    y += strip.height + GAP
canvas.convert("RGB").save(Path(__file__).parent / "output.png")
print(f"Saved {BOX_W}x{H} px")
