# Example 04 - Scale mode: auto-shrink to fill a fixed width

Demonstrates `mode="scale"`, which reduces the font size in 2-point steps until
a single-line text fits within `max_width`.

![Output](output.png)

## What it does

Three texts of increasing length are rendered into identical 540 × 100 px
strips.  Short text stays at the full 60 pt starting size; the longest string
is progressively shrunk so it still fills the same slot.  All strips share the
same canvas width, making the size difference immediately visible.

## Why it's here

"Scale to fit" is a common UI pattern - badge labels, button captions, dynamic
titles, and image overlays where the text length varies but the target rect is
fixed.  `mode="scale"` handles the entire size negotiation internally.  The
caller only specifies the starting size, the width constraint, and the minimum
size floor; FontStack does the rest.

## Parameters shown

| Parameter   | Value                     | Purpose                                     |
|-------------|---------------------------|---------------------------------------------|
| `mode`      | `"scale"`                 | Enables single-line scale-to-fit            |
| `max_width` | `CANVAS_W - PAD_X * 2`   | Maximum pixel width the text may occupy     |
| `min_size`  | `12`                      | Floor size; never shrinks below this        |
| `size`      | `60`                      | Starting size; shrinks in 2-point steps     |

## Key concepts

- **2-point steps** - sizes are tried at 60, 58, 56 … pt until the measured
  width is ≤ `max_width`.  Integer 2-point decrements avoid sub-pixel
  measurement ambiguity and keep final sizes on even values that the
  font's hinting was designed for.

- **`min_size` floor** - if the text is still wider than `max_width` at
  `min_size`, it renders at `min_size` and overflows.  This prevents text
  becoming illegible rather than silently clipping it.

- **No wrapping** - `mode="scale"` never introduces line breaks.  It is
  designed for single-line elements where wrapping would change the layout.
  Use `mode="fit"` if you want the text to both wrap and shrink.
