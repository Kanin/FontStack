# Example 06 - Arabic text with automatic reshaping and BiDi reordering

Demonstrates that FontStack handles right-to-left Arabic script transparently -
no application-level reshaping or directionality logic is required.

![Output](output.png)

## What it does

Renders `"مرحبا بالعالم"` (Hello, World in Arabic) in NotoSansArabic at 72 pt.
The letters join correctly into their contextual forms and the word order reads
right-to-left.

## Why it's here

Arabic is a cursive, contextual script: each letter has up to four distinct
presentation forms depending on its neighbors (isolated, initial, medial,
final).  The string also reads right-to-left.  Without preprocessing, a standard
rasterizer would display disconnected isolated glyphs in the wrong order.

FontStack pipes every string through two preprocessing steps automatically:

1. **arabic-reshaper** - substitutes the correct Unicode presentation-form
   codepoints (U+FE70–U+FEFF) so letters connect as they would in handwriting.
2. **python-bidi** - applies the Unicode Bidirectional Algorithm, reversing the
   visual run so right-to-left text displays in the correct reading order.

Both steps happen inside FontStack before the string ever reaches PIL.  You do
not need to call them yourself, and there is no flag to disable them.

## Parameters shown

| Parameter    | Value              | Purpose                              |
|--------------|--------------------|--------------------------------------|
| `font_stack` | NotoSansArabic     | A font whose `cmap` covers Arabic    |
| `size`       | `72`               | Large size to make shaping visible   |
| `fill`       | `(30, 30, 30)`     | Near-black text color                |

## Key concepts

- **No bidi flag needed** - the reshaping and BiDi pass is applied globally.
  Mixed strings (Latin + Arabic) are handled correctly too; see example 07.

- **Font selection still matters** - BiDi and reshaping produce correct
  codepoints, but the font must contain glyphs for the Arabic Unicode block.
  NotoSansArabic covers the full Arabic script range.
