# Example 05 - Horizontal alignment within a fixed-width block

Demonstrates left, center, and right alignment in `mode="wrap"` using the
`align` parameter.

![Output](output.png)

## What it does

The same pangram is drawn three times - left, center, right - into equally
sized 560 × 130 px strips with tinted backgrounds.  The colored backdrop makes
the alignment anchor visually obvious even on shorter lines.

## Why it's here

Alignment only matters when individual lines are narrower than the available
column width.  In `mode="wrap"`, every line may have a different pixel width;
`align` governs how each shorter line is positioned within the `max_width`
column.  This example shows all three options side by side so the difference is
unambiguous.

## Parameters shown

| Parameter   | Value                           | Purpose                                  |
|-------------|----------------------------------|------------------------------------------|
| `mode`      | `"wrap"`                        | Multi-line rendering                     |
| `align`     | `"left"` / `"center"` / `"right"` | Horizontal anchor for each line        |
| `max_width` | `BOX_W - PAD * 2`               | Column width all lines are aligned within |

## Key concepts

- **Alignment is per-line** - each line's pixel width is measured independently
  before it is drawn.  `align="center"` adds `(max_width - line_width) // 2`
  pixels to the x origin; `align="right"` adds the full difference.

- **`draw()` vs `draw_text()`** - this example uses
  `draw()` directly, painting onto a pre-created `Image`.  This is
  the correct approach when building composite layouts where individual strips
  are assembled into a larger canvas, because it gives explicit control over
  position and canvas color.

- **`HorizontalAlign` type** - FontStack exports `HorizontalAlign` as a
  `Literal["left", "center", "right"]` type alias, which IDEs use for
  autocomplete and type-checkers use for validation.
