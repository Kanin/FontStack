# Example 02 - Variable font weight spectrum

Demonstrates that `weight` is a first-class parameter for variable fonts,
producing nine distinct typographic weights from a single font file.

![Output](output.png)

## What it does

Renders the pangram `"The quick brown fox jumps over the lazy dog"` nine times
- once per weight in `[100, 200, 300, 400, 500, 600, 700, 800, 900]` - and
stacks all rows into a single comparison image.

## Why it's here

OpenType variable fonts store every weight in one file via the `wght` design
axis.  FontStack exposes this through the `weight` argument on every render
call.  Passing an integer maps directly to the axis value; FontStack calls
`set_variation_by_axes()` internally and caches the loaded font so repeated
renders at the same weight cost nothing.

## Parameters shown

| Parameter | Value     | Purpose                                               |
|-----------|-----------|-------------------------------------------------------|
| `weight`  | `100`–`900` | Sets the `wght` variation axis                      |
| `manager` | shared    | One `FontManager` instance reused across all nine rows |
| `size`    | `34`      | Comfortable body-text size that shows weight differences clearly |

## Key concepts

- **Weight as an axis value** - `weight=700` calls
  `font.set_variation_by_axes([700.0])` under the hood.  Named weights such as
  `weight="Bold"` are also accepted for static fonts that use named instances.

- **Shared `FontManager`** - instantiating the manager once and passing it to
  every `render_text()` call means each `(stack_hash, size, weight)` triple is
  loaded once and reused.  The internal LRU cache has a configurable cap
  (default 30 entries).

- **Static fonts** - if the font does not have a `wght` axis, the `weight`
  parameter is silently ignored and FontStack falls back to the unmodified font.
  No error is raised.
