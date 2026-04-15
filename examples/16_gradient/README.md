# Example 16 - Gradient Text Fills, Outlines, and Shadows

Demonstrates the gradient fill syntax: dash-separated color stops and the
built-in `"rainbow"` preset. Also shows gradient values for `stroke_fill`
and `shadow_color`.

## What it does

Renders eight variants that exercise gradient fills, outlines, and shadows:

1. **Rainbow preset** - `fill="rainbow"` expands to
   `red-orange-yellow-green-blue-indigo-violet` across the text width.
2. **Two-stop gradient** - `fill="red-blue"` for a simple left-to-right ramp.
3. **Hex gradient** - three stops using `#RRGGBB` notation.
4. **Arabic gradient** - right-to-left text with a warm gold-to-crimson ramp.
5. **Gradient + solid outline** - pairs a cyan-to-magenta gradient fill with
   a solid white 3 px stroke.
6. **Rainbow + shadow** - rainbow gradient fill with a semi-transparent
   dark shadow.
7. **Gradient outline** - solid white text with a rainbow gradient stroke
   (`stroke_fill="rainbow"`) on a dark background.
8. **Gradient shadow** - solid dark text with a rainbow gradient shadow
   (`shadow_color="red-orange-yellow-green-blue"`) on a light background.

## Gradient syntax

| Value                            | Result                              |
|----------------------------------|-------------------------------------|
| `"rainbow"`                      | Seven spectral colour stops         |
| `"red-blue"`                     | Two stops, left to right            |
| `"#FF6600-#FFFF00-#00CC66"`      | Three hex stops, evenly spaced      |
| `"gold-darkorange-crimson"`      | Named Pillow colors work too        |

Stops are distributed evenly across the rendered text width with linear
interpolation between adjacent pairs.

## Key takeaways

- Any Pillow-recognized color name or `#RRGGBB` hex code can be a stop.
- By default the gradient runs at a slight diagonal (`gradient_angle=15.0`)
  so multi-line text gets natural color variation per line. Set
  `gradient_angle=0.0` for a pure left-to-right gradient.
- Gradients compose with outlines and shadows. `fill`, `stroke_fill`, and
  `shadow_color` all accept gradient strings.
