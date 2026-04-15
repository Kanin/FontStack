"""Linear gradient construction and masking helpers."""

from __future__ import annotations

import math

from PIL import Image, ImageColor

__all__ = [
    "_GRADIENT_ANGLE",
    "_GRADIENT_PRESETS",
    "_apply_gradient_mask",
    "_is_gradient",
    "_make_gradient",
    "_parse_gradient",
]

# Default angle (degrees, clockwise from horizontal) for gradient rendering.
# A slight diagonal avoids identical color bands on every line of multi-line
# text.  0 = pure left-to-right.
_GRADIENT_ANGLE: float = 15.0

# Built-in gradient preset mapping.
_GRADIENT_PRESETS: dict[str, str] = {
    "rainbow": "red-orange-yellow-green-blue-indigo-violet",
}


def _is_gradient(fill: str | int | tuple[int, ...]) -> bool:
    """
    Return ``True`` if *fill* is a gradient specification.

    A gradient is a string that either matches a preset name (e.g. ``"rainbow"``)
    or contains at least one ``-`` delimiter separating two or more color stops
    (e.g. ``"red-blue"``).  Plain color names (``"red"``, ``"skyblue"``) and
    non-string fill values always return ``False``.
    """
    if not isinstance(fill, str):
        return False
    if fill in _GRADIENT_PRESETS:
        return True
    return "-" in fill and len(fill.split("-")) >= 2


def _parse_gradient(fill: str) -> list[tuple[int, int, int]]:
    """
    Parse a gradient string into a list of RGB color stops.

    Accepts a preset name (``"rainbow"``) or a dash-separated series of Pillow
    color specifiers (``"red-#00FF00-blue"``).  Each stop is resolved through
    :func:`PIL.ImageColor.getrgb`.

    Parameters
    ----------
    fill:
        The gradient specification string.

    Returns
    -------
    list[tuple[int, int, int]]
        Two or more ``(R, G, B)`` tuples.

    Raises
    ------
    ValueError
        If the string cannot be parsed into at least two color stops, or if
        any individual stop is not a recognized color specifier.
    """
    resolved = _GRADIENT_PRESETS.get(fill, fill)
    stops = resolved.split("-")
    if len(stops) < 2:
        raise ValueError(
            f"Gradient string must contain at least two dash-separated colors, "
            f"got {fill!r}."
        )
    colors: list[tuple[int, int, int]] = []
    for stop in stops:
        rgb = ImageColor.getrgb(stop.strip())
        # getrgb may return (R, G, B) or (R, G, B, A); keep only RGB.
        colors.append((rgb[0], rgb[1], rgb[2]))
    return colors


def _make_gradient(
    stops: list[tuple[int, int, int]],
    width: int,
    height: int,
    angle: float = 0.0,
) -> Image.Image:
    """
    Build a linear-gradient RGBA image from *stops*.

    Color stops are distributed evenly along the gradient axis.  Intermediate
    pixels are linearly interpolated between adjacent stops.

    Parameters
    ----------
    stops:
        Two or more ``(R, G, B)`` tuples defining the gradient color ramp.
    width:
        Image width in pixels. Must be >= 1.
    height:
        Image height in pixels. Must be >= 1.
    angle:
        Gradient direction in degrees, clockwise from horizontal.  ``0``
        produces a purely left-to-right gradient; positive values tilt the
        ramp diagonally so that successive text lines receive slightly
        different colors.

    Returns
    -------
    Image.Image
        An ``"RGBA"`` image filled with the gradient and fully opaque alpha.
    """
    width = max(width, 1)
    height = max(height, 1)
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    pixels = gradient.load()
    n_stops = len(stops)

    if angle == 0.0:
        # Fast path: purely horizontal (column-uniform).
        for x in range(width):
            t = x / max(width - 1, 1) * (n_stops - 1)
            idx = min(int(t), n_stops - 2)
            frac = t - idx
            c0 = stops[idx]
            c1 = stops[idx + 1]
            r = int(c0[0] + (c1[0] - c0[0]) * frac)
            g = int(c0[1] + (c1[1] - c0[1]) * frac)
            b = int(c0[2] + (c1[2] - c0[2]) * frac)
            for y in range(height):
                pixels[x, y] = (r, g, b, 255)  # type: ignore[index]
    else:
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        # Projection range across all four corners.
        projs = [
            cx * cos_a + cy * sin_a for cx in (0, width - 1) for cy in (0, height - 1)
        ]
        p_min = min(projs)
        p_range = max(max(projs) - p_min, 1)
        scale = (n_stops - 1) / p_range
        for y in range(height):
            base = y * sin_a - p_min
            for x in range(width):
                t = (x * cos_a + base) * scale
                idx = min(int(t), n_stops - 2)
                frac = t - idx
                c0 = stops[idx]
                c1 = stops[idx + 1]
                r = int(c0[0] + (c1[0] - c0[0]) * frac)
                g = int(c0[1] + (c1[1] - c0[1]) * frac)
                b = int(c0[2] + (c1[2] - c0[2]) * frac)
                pixels[x, y] = (r, g, b, 255)  # type: ignore[index]

    return gradient


def _apply_gradient_mask(
    target: Image.Image,
    stops: list[tuple[int, int, int]],
    angle: float = 0.0,
) -> None:
    """Replace RGB channels of *target* with a gradient, preserving alpha.

    The gradient is built from *stops* and sized to the bounding box of
    non-transparent pixels in *target*.  Modifies *target* in-place.
    """
    bbox = target.getbbox()
    if bbox is None:
        return
    left, top, right, bottom = bbox
    gradient_img = _make_gradient(stops, right - left, bottom - top, angle)
    region = target.crop(bbox)
    _, _, _, a = region.split()
    r_g, g_g, b_g, _ = gradient_img.split()
    target.paste(
        Image.merge("RGBA", (r_g, g_g, b_g, a)),
        (left, top),
    )
