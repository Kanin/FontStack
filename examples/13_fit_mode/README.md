# Example 13 - Fit mode: wrap, shrink, then truncate

Demonstrates `mode="fit"`, FontStack's most powerful layout mode.  It fills a
fixed bounding box by applying three successive strategies in order until the
text fits.

![Output](output.png)

## What it does

Four text strips are rendered into identical 540 × 110 px boxes, illustrating
each stage of the fit algorithm:

| Strip | Text length | Final size | What happens |
|-------|-------------|------------|--------------|
| 1 - lavender | Short ("Fit mode.") | 52 pt | Single line, fits at full size |
| 2 - mint | Medium (fox pangram) | 42 pt | Wraps to 2 lines; font shrinks to fit height |
| 3 - amber | Long (typography sentence) | 20 pt | Wraps to 3 lines; more shrinking needed |
| 4 - rose | Dense (multi-pangram paragraph) | 12 pt (min) | Hits minimum size; last line is truncated with `...` |

## Why it's here

This is the real-world bounded-box use case: any time you place text inside a
UI card, image thumbnail, badge, or notification where the box is fixed but the
content length is variable, `mode="fit"` ensures the text always stays inside
the box, looks as large as possible, and fails gracefully when it truly can't fit.

## The three strategies

| Step          | Action                                                        | When |
|---------------|---------------------------------------------------------------|------|
| 1 - **Wrap**  | Break text into lines at `max_width`                         | Always |
| 2 - **Shrink**| Reduce font by 2 pt, re-wrap, repeat                         | While wrapped block height > `max_height` and size > `min_size` |
| 3 - **Truncate** | Drop lines outside the box; append `...` to the last kept line | Only when still overflowing at `min_size` |

## Parameters shown

| Parameter    | Value                    | Purpose                                        |
|--------------|--------------------------|------------------------------------------------|
| `mode`       | `"fit"`                  | Enables the three-strategy fit algorithm       |
| `max_width`  | `BOX_W - PAD_X * 2`      | Maximum line width for wrapping                |
| `max_height` | `BOX_H - PAD_Y * 2`      | Maximum block height the wrapped text must fit |
| `size`       | `52`                     | Starting font size; shrinks from here          |
| `min_size`   | `12`                     | Minimum size floor; triggers truncation        |

## Key concepts

- **2-point shrink steps** - the size decreases by 2 pt per iteration.  Smaller
  steps would be imperceptible; larger steps risk a jarring size jump.  Even
  values also keep sizes on typographically natural numbers.

- **Truncation with `...`** - when `min_size` is reached and the block still
  overflows, lines that fall below the box boundary are dropped.  The last kept
  line is shortened progressively (word by word, then character by character)
  until the `...` suffix fits within `max_width`.

- **Caching across shrink steps** - `get_font_chain()` is LRU-cached on
  `(stack_hash, size, weight)`.  The shrink loop calls `_resolve_context()` once
  per size step, but each unique size is only loaded once.  On repeated calls
  to `draw()` with the same settings, the entire loop is essentially
  free after the first run.

- **`min_size=12` is deliberate** - strip 4 demonstrates truncation, which only
  triggers when the block cannot fit at `min_size`.  Setting a floor above the
  natural fit size would skip the truncation step and make strip 4 look
  identical to strip 3.
