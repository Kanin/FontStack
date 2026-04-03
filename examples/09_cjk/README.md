# Example 09 - Chinese, Japanese, and Korean via font fallback

Demonstrates per-character fallback across the three main CJK scripts.  A
four-font stack routes each character to the correct ideographic font without
any manual language detection.

![Output](output.png)

## What it does

Renders three rows - one for Chinese, one for Japanese, one for Korean.  Each
row is a `"Language  native text"` pair.  The Latin label is drawn by NotoSans;
the CJK greeting is automatically routed to whichever CJK font covers those
codepoints.

## Why it's here

CJK scripts use tens of thousands of distinct codepoints spread across multiple
Unicode blocks.  No single font covers all of them.  FontStack's `cmap`-based
routing means you compose a stack from the fonts you have; each character is
silently handed off to the first font that covers it.  No language tags, no
special API - just the right fonts in the right order.

## Stack used

| Priority | Font       | Coverage                              |
|----------|------------|---------------------------------------|
| 1        | NotoSans   | Latin, digits, common punctuation     |
| 2        | NotoSansSC | Chinese Simplified (CJK Unified Ideographs) |
| 3        | NotoSansJP | Japanese hiragana, katakana, and kanji |
| 4        | NotoSansKR | Korean hangul syllables               |

## Key concepts

- **Stack order for CJK** - CJK fonts share many codepoints, especially unified
  Han characters used across Chinese, Japanese, and Korean.  The font placed
  first wins.  For a Chinese-primary product, NotoSansSC before NotoSansJP is
  correct; for Japanese-primary, reverse them.

- **LRU font cache** - each `(stack_hash, size, weight)` triple is cached.
  Rendering all three rows with the same `FontManager` instance means all four
  fonts are loaded once, not three times.

- **Segment grouping** - consecutive CJK characters that map to the same font
  are grouped into a single `draw.text()` call, so inter-character spacing is
  controlled by the font's own advance widths rather than by FontStack.
