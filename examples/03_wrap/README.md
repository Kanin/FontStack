# Example 03 - Word-wrap at a fixed maximum width

Demonstrates `mode="wrap"`, which breaks long text into multiple lines so that
each line fits within a `max_width` pixel constraint.

![Output](output.png)

## What it does

Renders four pangrams joined into one long string.  FontStack word-wraps the
text at 560 px with `line_spacing=1.5`, producing a readable multi-line block,
and saves it to `output.png`.

## Why it's here

Without `mode="wrap"`, `draw_text()` draws everything on a single line.
Setting `mode="wrap"` and `max_width` tells FontStack to split the text
greedily at word boundaries - equivalent to CSS `word-wrap: break-word` - so
any paragraph-length content stays within its container.

## Parameters shown

| Parameter      | Value   | Purpose                                               |
|----------------|---------|-------------------------------------------------------|
| `mode`         | `"wrap"` | Enables automatic word-wrapping                      |
| `max_width`    | `560`   | Maximum pixel width per line                          |
| `line_spacing` | `1.5`   | Line-height multiplier (1.0 = tight, 1.5 = airy)     |

## Key concepts

- **Greedy wrapping** - words are appended to the current line one at a time.
  When adding the next word would push the measured width past `max_width`, the
  word starts a new line.  A single word that is wider than `max_width` is
  placed alone on its own line and allowed to overflow without truncation.

- **`line_spacing`** - the vertical distance between line tops is
  `int(size × line_spacing)`.  The default is `1.2`; `1.5` adds more breathing
  room, which is recommended for body text at smaller sizes.

- **Measurement accuracy** - line widths are measured with
  `ImageFont.getlength()` (float precision), which accurately accounts for
  kerning pairs in the font's advance-width table.
