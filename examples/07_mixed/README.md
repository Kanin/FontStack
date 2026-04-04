# Example 07 - Mixed Latin and Arabic in one string

Demonstrates FontStack's per-character font routing: Latin and Arabic characters
in the same string are automatically dispatched to the correct font, with no
manual segmentation or language detection required.

![Output](output.png)

## What it does

Renders `"Hello, مرحبا! Welcome to fontstack."` - a sentence that mixes English
and Arabic - using a two-font stack.  Latin characters are drawn by NotoSans;
the Arabic greeting is drawn by NotoSansArabic.

## Why it's here

This is the core value proposition of a font stack.  A single `draw_text()`
call handles a string whose characters span multiple scripts and Unicode blocks.
FontStack walks the stack for each character, picks the first font whose `cmap`
contains that codepoint, groups consecutive same-font characters into runs, and
renders each run in one PIL draw call.  The result is seamless mixed-script text
that would otherwise require significant manual scaffolding.

## Stack used

| Priority | Font           | Covers                    |
|----------|----------------|---------------------------|
| 1        | NotoSans       | Latin, punctuation, digits |
| 2        | NotoSansArabic | Arabic script (U+0600–)   |

## Key concepts

- **`cmap` routing** - the font's character map is a lookup table of codepoints
  the font covers.  FontStack caches each font's `cmap` at load time so
  per-character routing is a single `in` check - O(1) per character.

- **Stack order matters** - the first font in the list wins for any shared
  glyph.  `!` and `,` are in both NotoSans and NotoSansArabic; because NotoSans
  is first, the Latin punctuation variants are used.

- **BiDi is still applied** - the Arabic substring is reshaped and reordered
  even within a mixed-script string.  The surrounding Latin text is unaffected.

- **Segment grouping** - consecutive characters that map to the same font are
  batched into a single `draw.text()` call, preserving the font's kern pairs and
  ligature rules within each run.
