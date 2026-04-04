"""09_cjk - Chinese, Japanese, and Korean via per-character font fallback.  See README.md."""

from pathlib import Path

from PIL import Image

from fontstack import FontConfig, FontManager, draw_text

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"

STACK = [
    FontConfig(path=str(FONTS / "NotoSans[wdth,wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansSC[wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansJP[wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansKR[wght].ttf")),
]

manager = FontManager(default_stack=STACK)

ROWS = [
    ("Chinese", "中文：你好，世界！"),
    ("Japanese", "日本語：こんにちは世界！"),
    ("Korean", "한국어：안녕하세요 세계!"),
]

BG = (250, 250, 250)
rows = []
for label, text in ROWS:
    img = draw_text(
        f"{label}  {text}",
        font_stack=[],
        manager=manager,
        size=42,
        fill=(25, 25, 25),
        background=BG,
        padding=20,
    )
    rows.append(img)

W = max(r.width for r in rows)
GAP = 4
H = sum(r.height for r in rows) + GAP * (len(rows) - 1)
canvas = Image.new("RGBA", (W, H), (*BG, 255))
y = 0
for row in rows:
    canvas.paste(row, (0, y), row)
    y += row.height + GAP
canvas.convert("RGB").save(Path(__file__).parent / "output.png")
print(f"Saved {W}x{H} px")
