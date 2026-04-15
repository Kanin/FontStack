# Example 15 - Drop Shadows

Demonstrates the `shadow_color` and `shadow_offset` parameters across Latin,
Arabic, CJK, emoji, and combinations with outlines.

## What it does

Renders five variants that exercise drop shadows:

1. **Basic shadow** - white text with a semi-transparent black shadow offset
   4 px right and down on a steel-blue background.
2. **Emoji shadow** - space-themed emoji mixed with text, showing the shadow
   layer behind both glyph and emoji content.
3. **Arabic shadow** - right-to-left text with a dark shadow on a purple
   background.
4. **Large offset** - a bigger (6, 6) offset on a mixed Latin and Arabic
   string to illustrate how the shadow shifts independently.
5. **Outline + shadow** - combines `stroke_width`/`stroke_fill` with the
   shadow for a layered depth effect.

## Parameters shown

| Parameter       | Purpose                                           |
|-----------------|---------------------------------------------------|
| `shadow_color`  | Shadow color (name, RGB, or RGBA with opacity)    |
| `shadow_offset` | `(x, y)` pixel shift; positive = right and down   |
| `stroke_width`  | Outline thickness (used in the combo variant)     |
| `stroke_fill`   | Outline color (used in the combo variant)         |

## Key takeaways

- The shadow is rendered on a separate overlay beneath the main text, so
  semi-transparent shadow colors (RGBA) blend cleanly without affecting the
  foreground.
- `shadow_color=None` (the default) disables the shadow entirely with no
  performance cost.
- Shadows pair naturally with outlines for a "raised lettering" look.
