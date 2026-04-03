# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-04-03

### Fixed

- README gallery images now load correctly on PyPI and GitHub — URLs updated to use the correct branch path.

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

[0.1.2]: https://github.com/Kanin/fontstack/releases/tag/v0.1.2
[0.1.1]: https://github.com/Kanin/fontstack/releases/tag/v0.1.1
[0.1.0]: https://github.com/Kanin/fontstack/releases/tag/v0.1.0
