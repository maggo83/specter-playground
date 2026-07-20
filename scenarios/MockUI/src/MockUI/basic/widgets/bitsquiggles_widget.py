"""Small MockUI adapter for the shared BitSquiggles LVGL renderers."""

import bitsquiggle32
import bitsquiggles_renderer_lvgl as lvgl_renderer


class BitsquigglesRasterWidget:
    """Attach an exact or smooth BitSquiggles visual to an LVGL parent.

    ``render="pixel"`` preserves the exact raster. ``render="smooth"`` uses
    the rounded shared canvas renderer. The historical ``"canvas"`` spelling
    remains an alias for ``"smooth"`` during the playground transition.
    """

    WIDTH = bitsquiggle32.PIXEL_WIDTH * 2
    HEIGHT = bitsquiggle32.PIXEL_HEIGHT * 2
    H_PAD = 6

    def __init__(self, parent, fingerprint, style="standard", render="pixel",
                 bordered=False):
        bits = _fingerprint_to_bits(fingerprint)
        if render == "pixel":
            widget = lvgl_renderer.render_raster(
                parent, bitsquiggle32.pixels(bits, style), scale=2)
        elif render in ("smooth", "canvas"):
            widget = lvgl_renderer.render_smooth(
                parent, bitsquiggle32.spec(bits, style), scale=2, bordered=bordered)
        else:
            raise ValueError("render must be 'pixel' or 'smooth'")
        widget.set_style_margin_left(self.H_PAD, 0)
        widget.set_style_margin_right(self.H_PAD, 0)
        self.img = widget
        self.verbal_text = None


def _fingerprint_to_bits(fingerprint):
    if isinstance(fingerprint, int):
        if 0 <= fingerprint <= 0xFFFFFFFF:
            return fingerprint
        raise ValueError("fingerprint must be an unsigned 32-bit integer")
    if not isinstance(fingerprint, str):
        raise ValueError("fingerprint must be an unsigned 32-bit integer or hexadecimal string")
    value = fingerprint.strip()
    if value.startswith(("0x", "0X")):
        value = value[2:]
    if not value or len(value) > 8:
        raise ValueError("fingerprint must contain one to eight hexadecimal digits")
    try:
        return int(value, 16)
    except ValueError:
        raise ValueError("fingerprint must contain hexadecimal digits")


def text_prefix_to_bits(value):
    """Return the big-endian value of the first four UTF-8 bytes of a label."""
    if not isinstance(value, str):
        raise ValueError("text value must be a string")
    encoded = value.encode()[:4]
    result = 0
    for byte in encoded:
        result = (result << 8) | byte
    return result << (8 * (4 - len(encoded)))


def clear_bitsquiggles_cache():
    """Release shared LVGL renderer caches after deleting parent widgets."""
    lvgl_renderer.clear_cache()
