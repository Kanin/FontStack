# Example 14 - Text Outlines (Strokes)

Demonstrates the `stroke_width` and `stroke_fill` parameters across multiple
scripts and emoji.

## What it does

Renders four variants that exercise text outlines:

1. **Basic outline** - white text with a black 3 px stroke on a grey background.
2. **Colourful outline** - warm yellow text with a blue stroke on a warm
   background.
3. **Arabic outline** - right-to-left Arabic text with a thick 4 px red-orange
   stroke on a dark background.
4. **Mixed-script outline** - Latin and Arabic in a single line with a crimson
   stroke on a light background.

## Parameters shown

| Parameter      | Purpose                                           |
|----------------|---------------------------------------------------|
| `stroke_width` | Outline thickness in pixels (0 = no outline)      |
| `stroke_fill`  | Outline color (name, RGB tuple, or RGBA tuple)    |
| `fill`         | Interior text color                               |
| `background`   | Canvas background color                           |

## Key takeaways

- Outlines are rendered by Pillow's FreeType stroke engine via Pilmoji, so
  they work on any glyph the loaded font can rasterise.
- Emoji (handled by Pilmoji) are unaffected by `stroke_width`; the outline
  applies only to vector glyphs.
- Setting `stroke_fill=None` with `stroke_width > 0` uses the text `fill`
  color for the stroke, producing a thicker version of the same color.
