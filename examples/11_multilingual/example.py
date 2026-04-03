"""11_multilingual - "Hello, World!" in nine scripts, one FontManager.  See README.md."""

from pathlib import Path

from PIL import Image

from fontstack import FontConfig, FontManager, render_text

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"

# Full recommended stack - order matters: early entries win for shared codepoints.
STACK = [
    FontConfig(path=str(FONTS / "NotoSans[wdth,wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansArabic[wdth,wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansSC[wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansJP[wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansKR[wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansDevanagari[wdth,wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansHebrew[wdth,wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansBengali[wdth,wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansThai[wdth,wght].ttf")),
]

manager = FontManager(default_stack=STACK)

GREETINGS = [
    ("English", "Hello, World!"),
    ("Arabic", "مرحبا بالعالم"),
    ("Chinese", "你好，世界！"),
    ("Japanese", "こんにちは世界！"),
    ("Korean", "안녕하세요 세계!"),
    ("Hindi", "नमस्ते दुनिया"),
    ("Hebrew", "שלום עולם"),
    ("Bengali", "হ্যালো পৃথিবী"),
    ("Thai", "สวัสดีชาวโลก"),
]

BG = (250, 250, 250)
SIZE = 44
PAD = 16

rows = []
for _lang, greeting in GREETINGS:
    img = render_text(
        greeting,
        font_stack=[],
        manager=manager,
        size=SIZE,
        fill=(25, 25, 25),
        background=BG,
        padding=PAD,
    )
    rows.append(img)

W = max(r.width for r in rows)
GAP = 2
H = sum(r.height for r in rows) + GAP * (len(rows) - 1)
canvas = Image.new("RGBA", (W, H), (*BG, 255))
y = 0
for row in rows:
    canvas.paste(row, (0, y), row)
    y += row.height + GAP
canvas.convert("RGB").save(Path(__file__).parent / "output.png")
print(f"Saved {W}x{H} px")
