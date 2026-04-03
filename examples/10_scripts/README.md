# Example 10 - Devanagari, Hebrew, Bengali, and Thai

Demonstrates FontStack's handling of four complex writing systems beyond
Latin/CJK, each requiring a dedicated Noto script font for correct glyph
coverage.

![Output](output.png)

## What it does

Renders four rows - Hindi in Devanagari, Hebrew, Bengali, and Thai.  Each row
is a `"Language:  native text"` pair where the Latin label is handled by
NotoSans and the native text is automatically routed to the matching script
font.

## Why it's here

These scripts illustrate that complex-script support is purely a matter of font
selection, not special-case code in FontStack.  Each character is looked up in
each font's `cmap` and dispatched accordingly.  FontStack provides no per-script
logic - the routing mechanism is universal.

| Script     | Notable complexity                                   |
|------------|------------------------------------------------------|
| Devanagari | Conjunct consonants, vowel matras, combining marks    |
| Hebrew     | Right-to-left, contextual finals, niqud vowel points |
| Bengali    | Ligature letters, complex conjunct clusters          |
| Thai       | No word spaces, stacked vowel signs                  |

## Stack used

| Priority | Font                  | Coverage                      |
|----------|-----------------------|-------------------------------|
| 1        | NotoSans              | Latin                         |
| 2        | NotoSansDevanagari    | Hindi, Sanskrit, Marathi      |
| 3        | NotoSansHebrew        | Hebrew, Yiddish               |
| 4        | NotoSansBengali       | Bengali, Assamese             |
| 5        | NotoSansThai          | Thai                          |

## Key concepts

- **Script-specific Noto fonts** - every Noto script font is designed to match
  the visual weight and metrics of NotoSans, so mixed Latin + script text looks
  consistent in the same row.

- **Hebrew BiDi** - Hebrew is right-to-left like Arabic.  `python-bidi` handles
  the visual reordering automatically; no Hebrew-specific code is needed.

- **Stack length** - a five-font stack adds negligible overhead.  `cmap` lookups
  are cached, and font objects are shared across all render calls via the LRU
  cache.
