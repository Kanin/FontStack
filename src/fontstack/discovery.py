"""Font directory scanning and auto-discovery."""

from __future__ import annotations

from pathlib import Path

from fontTools.ttLib.ttCollection import TTCollection

from fontstack.types import FontConfig

__all__ = ["scan_font_dir"]

_FONT_EXTENSIONS: frozenset[str] = frozenset({".ttf", ".otf", ".ttc", ".otc"})


def scan_font_dir(
    font_dir: str | Path,
    *,
    recursive: bool = False,
) -> list[FontConfig]:
    """
    Scan a directory for font files and return a list of :class:`FontConfig`
    entries suitable for use as a ``default_stack``.

    Recognised extensions: ``.ttf``, ``.otf``, ``.ttc``, ``.otc``.
    TrueType/OpenType Collection files (``.ttc``, ``.otc``) produce one
    :class:`FontConfig` per member font, each with the appropriate
    ``ttc_index``.  Results are sorted by filename for deterministic
    fallback order.

    Parameters
    ----------
    font_dir:
        Path to the directory containing font files.
    recursive:
        When ``True``, search subdirectories recursively.  Defaults to
        ``False``.

    Returns
    -------
    list[FontConfig]
        One or more :class:`FontConfig` entries found in *font_dir*.

    Raises
    ------
    FileNotFoundError
        If *font_dir* does not exist or is not a directory.
    ValueError
        If no font files are found in *font_dir*.
    """
    directory = Path(font_dir)
    if not directory.is_dir():
        raise FileNotFoundError(
            f"Font directory does not exist or is not a directory: {font_dir}"
        )

    configs: list[FontConfig] = []
    files = sorted(
        (
            p
            for p in (directory.rglob("*") if recursive else directory.iterdir())
            if p.is_file() and p.suffix.lower() in _FONT_EXTENSIONS
        ),
        key=lambda p: p.name.lower(),
    )

    for path in files:
        path_str = str(path)
        if path.suffix.lower() in {".ttc", ".otc"}:
            with TTCollection(path_str) as collection:
                for idx in range(len(collection)):
                    configs.append(FontConfig(path=path_str, ttc_index=idx))
        else:
            configs.append(FontConfig(path=path_str))

    if not configs:
        raise ValueError(f"No font files (.ttf, .otf, .ttc, .otc) found in: {font_dir}")

    return configs
