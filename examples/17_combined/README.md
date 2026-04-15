# Example 17 - Combined Features

Demonstrates gradient fills, gradient outlines, gradient shadows, text
outlines, drop shadows, multiple scripts, variable font weights, and
different rendering modes all working together.

## What it does

Renders eight images that layer every new feature on top of the existing
rendering pipeline:

1. **Latin combo** - rainbow gradient + 3 px black outline + dark shadow on
   light background.
2. **Arabic combo** - warm gradient + brown outline + shadow on a warm canvas.
3. **Wrapped combo** - multiline word-wrap at 500 px with rainbow text,
   outline, and shadow.
4. **Scaled combo** - `mode="scale"` shrinks a long sentence to fit 600 px,
   using a cyan-magenta-yellow gradient plus outline and shadow.
5. **Multilingual combo** - Latin and Arabic with a five-stop gradient,
   outline, and shadow.
6. **Bold combo** - `weight=900` with a fire-themed gradient, thick outline,
   and deep shadow.
7. **Triple gradient** - gradient fill + gradient outline + gradient shadow --
   all three accept gradient strings simultaneously.
8. **Neon glow** - white text with a rainbow gradient outline and a
   cyan-blue-purple gradient shadow on a dark background.

## Parameters exercised

| Parameter       | Values shown                                      |
|-----------------|---------------------------------------------------|
| `fill`          | `"rainbow"`, named gradients, hex gradients        |
| `stroke_width`  | 2, 3, 4, 5                                        |
| `stroke_fill`   | `"black"`, RGB tuples, gradient strings            |
| `shadow_color`  | RGBA tuples, `"gray"`, gradient strings             |
| `shadow_offset` | `(2,2)` through `(5,5)`                           |
| `mode`          | `"wrap"`, `"scale"` (default wrap also used)      |
| `weight`        | `400` (default), `900`                            |
| `manager`       | Shared `FontManager` reused across all eight calls |

## Key takeaways

- All three visual effects (gradient, outline, shadow) compose cleanly. The
  shadow is rendered first on its own layer, then the outlined gradient text
  is composited on top.
- Reusing a `FontManager` across calls avoids re-parsing cmap tables, keeping
  batch rendering fast.
- Variable font weight (`weight=900`) interacts correctly with outlines; the
  heavier glyphs receive the stroke around their bolder contours.
- Gradient fills span the tight bounding box of rendered text, so wrapped
  lines each get the full gradient sweep independently per line.
