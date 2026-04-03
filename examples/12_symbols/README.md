# Example 12 - Unicode symbols, math, and special characters

Demonstrates that FontStack's fallback mechanism extends to specialized symbol
fonts covering Unicode planes beyond the Basic Multilingual Plane.

![Output](output.png)

## What it does

Renders seven sections of Unicode symbols, each with a grey label row above and
a larger content row below:

| Section                   | Sample characters          |
|---------------------------|----------------------------|
| Arrows                    | ← → ↑ ↓ ↔ ↕ ↖ ↗ ↘ ↙       |
| Geometric shapes          | ■ □ ▲ △ ▶ ▷ ● ○ ◆ ◇ ★ ☆   |
| Chess & card suits        | ♔ ♕ ♖ ♗ ♘ ♙ ♚ ♛ ♜ ♝ ♞ ♟ ♠ ♣ ♥ ♦ |
| Musical notation          | ♩ ♪ ♫ ♬ ♭ ♮ ♯              |
| Math bold                 | 𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙 |
| Math fraktur              | 𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ |
| Enclosed alphanumerics    | ① ② ③ … ⑩ Ⓐ Ⓑ Ⓒ Ⓓ Ⓔ Ⓕ    |

## Why it's here

Special characters and symbols require fonts specifically designed for each
Unicode block; standard Latin fonts do not cover them.  This example shows that
the same cmap-routing mechanism that handles CJK scripts also transparently
handles specialized symbol coverage across multiple fonts and Unicode planes.

## Stack used

| Priority | Font              | Coverage                                                |
|----------|-------------------|---------------------------------------------------------|
| 1        | NotoSans          | Latin, common punctuation                               |
| 2        | NotoSansMath      | Mathematical alphanumerics - bold, italic, fraktur, script (U+1D400–U+1D7FF) |
| 3        | NotoSansSymbols   | Enclosed alphanumerics, musical notation, Roman numerals, arrows (U+2160+, U+2460+, U+2669+) |
| 4        | NotoSansSymbols2  | Geometric shapes, chess and card suits, Braille, dingbats (U+25A0+, U+2654+, U+2800+) |

## Key concepts

- **Supplementary Multilingual Plane** - math bold (`𝐀`, U+1D400) and fraktur
  (`𝔄`, U+1D504) glyphs live outside the Basic Multilingual Plane.  Standard
  fonts don't cover them; NotoSansMath does.  FontStack handles multi-codepoint
  characters (surrogate pairs) correctly.

- **Split coverage** - arrows appear in both NotoSansSymbols and
  NotoSansSymbols2.  Because NotoSansSymbols is earlier in the stack, it wins
  for any arrows it covers, and NotoSansSymbols2 picks up the rest.  Stack order
  controls which variant is used when coverage overlaps.

- **Label vs content sizes** - this example renders each section as two separate
  `render_text()` images (label at 18 pt, content at 36 pt) and assembles them
  manually.  This pattern is useful when you need different sizes within the same
  visual section.
