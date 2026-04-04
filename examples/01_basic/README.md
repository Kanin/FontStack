# Example 01 - Basic single-line rendering

The simplest possible FontStack usage: render one line of text to a PNG with
`draw_text()`.

![Output](output.png)

## What it does

Renders `"Hello, world!"` in NotoSans at 72 pt onto a white canvas with 40 px
of padding and saves the result to `output.png`.

## Why it's here

`draw_text()` is FontStack's zero-configuration entry point.  It wraps
`FontManager.draw()` in a single call that handles canvas creation,
padding, and image assembly - you supply text and a font, and you get a
ready-to-save `PIL.Image` back.  This is the right starting point before
exploring wrap, fit, or fallback features.

## Parameters shown

| Parameter    | Value                        | Purpose                                        |
|--------------|------------------------------|------------------------------------------------|
| `font_stack` | `[FontConfig(path=…)]`       | Ordered list of fonts to try per character     |
| `size`       | `72`                         | Font size in points                            |
| `fill`       | `(30, 30, 30)`               | Near-black text color                          |
| `background` | `"white"`                    | Canvas background (PIL color string or tuple)  |
| `padding`    | `40`                         | Uniform pixel padding on all four sides        |

## Key concepts

- **`FontConfig`** - the data class that describes one font in the stack.  At
  minimum it needs a `path`.  Variable fonts pick up axis defaults
  automatically; weights and custom axes can be set via `axes=VariationAxes(…)`.

- **`draw_text()` vs `draw()`** - `draw_text()` creates a new
  `Image` each call, which is convenient for one-shot renders.  When building
  composite layouts, use `FontManager.draw()` directly to paint onto
  an existing image at a specific position.
