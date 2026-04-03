# Example 11 - "Hello, World!" in nine scripts

The hallmark example: a single `FontManager` with a nine-font stack renders
any of the world's major writing systems without per-language configuration.

![Output](output.png)

## What it does

Renders "Hello, World!" in nine scripts - English, Arabic, Chinese, Japanese,
Korean, Hindi, Hebrew, Bengali, and Thai.  Each greeting is placed on its own
row; all nine rows are assembled into a single stacked image.  One `FontManager`
instance handles every script.

## Why it's here

This example proves the cmap-routing model scales to a fully multilingual
product.  Every routing decision, BiDi pass, Arabic reshaping, and weight
application happens transparently inside FontStack.  The application code is
identical for every script; there is no branching on language.

## Stack used (in priority order)

| Font                  | Script                        |
|-----------------------|-------------------------------|
| NotoSans              | Latin, digits, punctuation    |
| NotoSansArabic        | Arabic                        |
| NotoSansSC            | Chinese Simplified            |
| NotoSansJP            | Japanese                      |
| NotoSansKR            | Korean                        |
| NotoSansDevanagari    | Hindi (Devanagari)            |
| NotoSansHebrew        | Hebrew                        |
| NotoSansBengali       | Bengali                       |
| NotoSansThai          | Thai                          |

## Key concepts

- **One manager, nine renders** - all nine fonts are loaded once into the LRU
  cache.  Each subsequent call with the same `(stack, size, weight)` returns the
  cached chain instantly.

- **Stack order** - NotoSans is placed first so it wins for Latin characters
  that some CJK fonts also include.  Arabic comes before CJK because Arabic
  fonts don't overlap CJK codepoints, but placing it second keeps the most-used
  scripts near the top of the lookup chain.

- **Consistent visual weight** - the Noto font family was designed so every
  script version has matching x-height and stroke weight, making multi-script
  rows look harmonious rather than mismatched.
