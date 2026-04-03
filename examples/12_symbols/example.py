"""12_symbols - Unicode symbols, math, and special characters via font fallback.  See README.md."""

from pathlib import Path

from PIL import Image

from fontstack import FontConfig, FontManager, render_text

FONTS = Path(__file__).parent.parent.parent / "tests" / "fonts"

STACK = [
    FontConfig(path=str(FONTS / "NotoSans[wdth,wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansMath-Regular.ttf")),
    FontConfig(path=str(FONTS / "NotoSansSymbols[wght].ttf")),
    FontConfig(path=str(FONTS / "NotoSansSymbols2-Regular.ttf")),
]

manager = FontManager(default_stack=STACK)

SECTIONS = [
    ("Arrows", "← → ↑ ↓ ↔ ↕ ↖ ↗ ↘ ↙"),
    ("Geometric shapes", "■ □ ▲ △ ▶ ▷ ● ○ ◆ ◇ ★ ☆"),
    ("Chess & card suits", "♔ ♕ ♖ ♗ ♘ ♙ ♚ ♛ ♜ ♝ ♞ ♟ ♠ ♣ ♥ ♦"),
    ("Musical notation", "♩ ♪ ♫ ♬ ♭ ♮ ♯"),
    ("Math bold  𝐀𝐁𝐂", "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙"),
    ("Math fraktur  𝔄𝔅𝔉", "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ"),
    ("Enclosed alphanumerics", "① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩ Ⓐ Ⓑ Ⓒ Ⓓ Ⓔ Ⓕ"),
]

BG = (250, 250, 250)
LABEL_SIZE = 18
CONTENT_SIZE = 36
LABEL_COLOR = (140, 140, 140)
CONTENT_COLOR = (25, 25, 25)
MARGIN_X = 16
MARGIN_Y = 12
SECTION_GAP = 12

rendered = []
for label, content in SECTIONS:
    label_img = render_text(
        label,
        font_stack=[],
        manager=manager,
        size=LABEL_SIZE,
        fill=LABEL_COLOR,
        background=BG,
        padding=0,
    )
    content_img = render_text(
        content,
        font_stack=[],
        manager=manager,
        size=CONTENT_SIZE,
        fill=CONTENT_COLOR,
        background=BG,
        padding=0,
    )
    rendered.append((label_img, content_img))

W = max(max(li.width, ci.width) for li, ci in rendered) + MARGIN_X * 2
total_h = MARGIN_Y
for li, ci in rendered:
    total_h += li.height + 4 + ci.height + SECTION_GAP
total_h -= SECTION_GAP  # no gap after last section
total_h += MARGIN_Y

canvas = Image.new("RGB", (W, total_h), BG)
y = MARGIN_Y
for li, ci in rendered:
    canvas.paste(li, (MARGIN_X, y))
    y += li.height + 4
    canvas.paste(ci, (MARGIN_X, y))
    y += ci.height + SECTION_GAP

out = Path(__file__).parent / "output.png"
canvas.save(out)
print(f"Saved {canvas.width}×{canvas.height} → {out}")
