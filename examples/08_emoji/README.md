# Example 08 - Inline emoji via Pilmoji / Twemoji

Demonstrates that emoji render inline with text at the correct baseline, using
Twemoji raster images sourced and composited by Pilmoji.

![Output](output.png)

## What it does

Renders `"Coding 👩‍💻  Coffee ☕  Deploy 🚀  Party 🎉"` at 52 pt.  Each emoji
codepoint is replaced by a scaled Twemoji PNG and pasted onto the canvas so it
sits on the same visual baseline as the surrounding text.

## Why it's here

PIL's built-in text rasterizer does not support color emoji - it will either
skip them or render a monochrome box.  FontStack delegates emoji to
[Pilmoji](https://github.com/jay3332/pilmoji), which intercepts emoji codepoints
before PIL processes the string, fetches the corresponding
[Twemoji](https://twemoji.twitter.com/) image, scales it to match the current
font size, and composites it in the correct position.

The key challenge is vertical alignment: the emoji image must be placed so its
optical center sits on the same baseline as the adjacent glyphs.  FontStack
computes this offset from the primary font's ascent metrics and passes it to
Pilmoji, so emoji always land on the correct line regardless of font or size.

## Key concepts

- **Pilmoji interception** - Pilmoji splits the string at emoji boundaries using
  a Unicode regex.  Text runs between emoji are drawn by the normal PIL
  rasterizer; emoji are drawn as RGBA PNG images and alpha-composited.

- **Twemoji source** - the default emoji source is Twemoji (open-source,
  consistent cross-platform appearance).  No local emoji font is required; the
  images are fetched on demand and cached in memory.

- **ZWJ sequences** - compound emoji such as `👩‍💻` (woman + zero-width joiner +
  laptop) are matched as a single token by Pilmoji's regex and replaced with
  their single Twemoji image.

- **Scale matching** - Pilmoji scales the emoji image to `font.size` pixels
  square, so emoji size tracks the text size automatically.
