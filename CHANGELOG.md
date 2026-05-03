# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.5] - 2026-05-03

### Fixed

- Emoji rendered too high when the text block used a non-`"lt"` anchor. The measurement sentinel pixel placed in `_measure_block` for emoji segments was positioned at `baseline - seg_asc` (the font ascender line, `y_pos - vto`) instead of `y_pos` where Pilmoji actually renders the emoji image. This caused `vis_t` to be inflated by roughly `vto` pixels, and the `vis_t` correction applied to `emoji_oy` in `_render_segments` then shifted emoji up by the same amount. Sentinel is now placed at `y_pos`, matching the true emoji render top.

## [0.3.4] - 2026-05-03

### Fixed

- Glyphs with negative left side bearings (certain Arabic contextual forms extend 1 px left of the advance origin) were clipped at the canvas edge in `draw_text()`. A 4 px overhang buffer is now added to `margin` so the leftmost pixel always falls within the canvas before the `getbbox()` crop removes the surplus space.
- `_measure_block` computed the visual bounding box by rendering all characters with the primary (Latin) font. For Arabic/CJK fallback text, this produced `.notdef` tofu boxes whose left inset did not match the real glyphs, yielding an incorrect `vis_l` and a negative `x_off` that clipped text against the left edge. `_measure_block` now iterates `_segment_text` and draws each segment with its actual fallback font, matching the per-font logic of `_render_segments`.
- Text blocks starting with an emoji were shifted left by `vis_l` pixels when using anchor `"lt"`. The measurement canvas previously skipped emoji segments but advanced `x_seg` by `font.getlength()`, which returns the `.notdef` advance (~38 px at size 64) rather than the actual pilmoji render width (~64 px). This inflated `vis_l`, causing `x_off = -vis_l` to push the whole block off-canvas. The fix paints a sentinel pixel at each emoji's top-left corner in the measurement canvas so `getbbox()` sees the true left boundary of the line, and advances `x_seg` by `ctx.size` (the actual pilmoji square size).
- `emoji_position_offset` is now adjusted by `vis_t` (the vertical offset returned by `_measure_block`) so emoji tops align with the true visual top of the text rather than the nominal `y_pos`, eliminating a ~1 px low-drift when the anchor shifts the draw position upward.

## [0.3.3] - 2026-05-03

### Fixed

- Emoji vertical alignment is now correct in all cases. The root cause was that Pilmoji's internal `getmask2` returns `offset[1] ≈ vto` for mixed text/emoji strings but `offset[1] = ascent` for spaces-only strings (emoji placeholders), making a single `emoji_position_offset` unable to work for both. `_segment_text` now splits at emoji boundaries via `EMOJI_REGEX.finditer` so each emoji sequence is isolated in its own segment. With a spaces-only `text_line`, `getmask2` returns a predictable `offset[1] = ascent`, which is corrected with `oy = vto − ascent` to place the emoji image at the visual glyph top. Text-only segments use `oy = 0` since their `getmask2` offset already lands text at `y_pos`.
- Fallback-font glyphs (e.g. Arabic) no longer render too high when mixed with Latin. A previous fix attempt used `anchor="lt"` on `pil.text()`, which bypassed each font's own `getmask2` vertical offset and caused non-primary fonts to be drawn from their em-square top instead of their ascender line. Reverted to Pilmoji's default `"la"` anchor: each font's `getmask2` offset is font-specific and naturally aligns all scripts to the shared baseline.

## [0.3.2] - 2026-05-03

### Fixed

- `emoji_source` parameter type corrected from `type[BaseSource]` to `BaseSource | type[BaseSource]` on `FontManager.draw()` and `draw_text()`. Pilmoji accepts either a source class or a pre-constructed instance; the previous annotation unnecessarily rejected instances.

## [0.3.1] - 2026-05-03

### Added

- `anchor` parameter on `FontManager.draw()`. Accepts PIL-style two-character codes (`"lt"`, `"mm"`, `"rb"`, etc.) to specify which point of the rendered text block is placed at `position`. Default `"lt"` (top-left) is fully backward-compatible.
- `Anchor` type alias (`Literal["lt", "mt", "rt", "lm", "mm", "rm", "lb", "mb", "rb"]`) exported from the top-level `fontstack` package.

## [0.3.0] - 2026-04-14

### Added

- Gradient text fills via dash-separated color strings (e.g. `fill="red-blue"`) and the built-in `"rainbow"` preset.
- Gradient outlines (`stroke_fill="rainbow"`) and gradient shadows (`shadow_color="red-orange-yellow"`) using the same syntax.
- Configurable `gradient_angle` parameter on `draw()` and `draw_text()`. Defaults to `15.0` degrees (slightly diagonal so multi-line text gets natural color variation per line). Set to `0.0` for a pure left-to-right gradient.
- Text outlines (strokes) with `stroke_width` and `stroke_fill` parameters. Works on all vector glyphs across Latin, Arabic, and other scripts.
- Drop shadows with `shadow_color` and `shadow_offset`. Shadow shape includes the outline when `stroke_width > 0`. Semi-transparent RGBA colors blend cleanly.
- Font directory scanning via `font_dir=` on `FontManager` or `scan_font_dir()`. Point to a folder of fonts and skip manual `FontConfig` wiring. Fonts load in alphabetical order by filename (case-insensitive), so the first file becomes the primary font.
- `scan_font_dir()` exported as a public API for inspecting discovered fonts before building a manager.

### Changed

- Internal module split: the monolithic `_core.py` is now split into `types.py`, `gradient.py`, `bidi.py`, `cmap.py`, `discovery.py`, `manager.py`, and `draw.py`. Public API is unchanged - all imports from `fontstack` still work.
- `scan_font_dir` added to `__all__` in the top-level package.

## [0.2.0] - 2026-04-03

### Changed

- **Breaking:** `FontManager.draw_text_smart()` renamed to `FontManager.draw()`.
- **Breaking:** `render_text()` renamed to `draw_text()`.

---

## [0.1.3.post1] - 2026-04-03

### Fixed

- README formatting corrected for proper rendering on PyPI.

---

## [0.1.3] - 2026-04-03

### Added

- ReadTheDocs configuration (`.readthedocs.yaml`) with Sphinx and `sphinx-rtd-theme`.
- Sphinx documentation directory (`docs/`) with `conf.py`, `index.rst`, and `requirements.txt`.

---

## [0.1.2] - 2026-04-03

### Fixed

- README gallery images now load correctly on PyPI and GitHub; URLs updated to use the correct branch path.

### Changed

- `render_text`: `font_stack` is now optional (defaults to `None`) when a pre-built `manager` is passed, so callers no longer need to write `font_stack=[]` as a placeholder.
- `render_text` overloads split into two groups (8 total): one where `font_stack: list[FontConfig]` is required, and one where `manager: FontManager` is required. Type checkers now reject calls where neither is supplied.

---

## [0.1.1] - 2026-04-03

### Fixed

- Added missing `arabic-reshaper` dependency to package metadata.

### Changed

- Source distribution now includes only `src/`, test files, and project documentation - test fonts and example images are excluded, reducing the sdist from 25 MB to ~60 KB.

---

## [0.1.0] - 2026-04-02

### Added

- `FontManager` class with a prioritized fallback font stack and LRU caching.
- Per-character font fallback using fonttools cmap parsing (all cmap formats).
- TrueType/OpenType Collection (`.ttc`/`.otc`) support via `ttc_index`.
- Variable font support: integer `weight` sets the `wght` axis; string `weight` calls `set_variation_by_name`.
- `VariationAxes` TypedDict for type-safe variable font axis configuration (`wght`, `wdth`, `ital`, `slnt`, `opsz`).
- `draw_text_smart` method with `"wrap"` (word-wrap), `"scale"` (shrink-to-fit), and `"fit"` (wrap then shrink to height) modes, `"left"`/`"center"`/`"right"` alignment, and configurable line spacing.
- `render_text` convenience function that returns a cropped, padded `PIL.Image.Image` sized to the rendered output.
- Automatic BiDi reordering via `python-bidi`. Arabic is pre-processed with `arabic_reshaper` before reordering so letters connect correctly under Pillow's BASIC layout engine.
- Emoji rendering via `pilmoji` / Twemoji with correct baseline alignment across mixed font-emoji runs.
- `@overload` signatures for `draw_text_smart` and `render_text` exposing `min_size` only when `mode="scale"` or `mode="fit"`, and `max_height` only when `mode="fit"`.
- `Literal` types for `mode` (`"wrap"` | `"scale"` | `"fit"`) and `align` (`"left"` | `"center"` | `"right"`).
- `py.typed` marker for PEP 561 compatibility.

### Changed

- Switched from Pillow's RAQM layout engine to the BASIC layout engine for font loading. BASIC produces consistent glyph advance widths across all platforms and doesn't require the optional `libraqm` system library.

[0.3.0]: https://github.com/Kanin/fontstack/releases/tag/v0.3.0
[0.2.0]: https://github.com/Kanin/fontstack/releases/tag/v0.2.0
[0.1.3.post1]: https://github.com/Kanin/fontstack/releases/tag/v0.1.3.post1
[0.1.3]: https://github.com/Kanin/fontstack/releases/tag/v0.1.3
[0.1.2]: https://github.com/Kanin/fontstack/releases/tag/v0.1.2
[0.1.1]: https://github.com/Kanin/fontstack/releases/tag/v0.1.1
[0.1.0]: https://github.com/Kanin/fontstack/releases/tag/v0.1.0
