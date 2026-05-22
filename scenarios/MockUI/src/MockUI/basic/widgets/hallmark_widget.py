"""Hallmark widget — deterministic visual fingerprint for a string identifier.

Uses the hallmark library (https://hallmarks.info/) to generate a 
14x20 pixel-art grid, upscales it 2x with nearest-neighbour to 28x40,
and wraps the result in an lv.image widget.

A module-level cache stores the lv.image_dsc_t per input string so that
rebuilds do not re-hash or re-render the same identifier twice.

Call clear_hallmark_cache() when the descriptors are no longer needed to 
free memory.
"""

import lvgl as lv
from hallmark import hallmark_digest, hallmark_pixels_packed, hallmark_words
from ..ui_consts import HALLMARK_W, HALLMARK_H

# ── Render dimensions ─────────────────────────────────────────────────────────
_SRC_W = 14   # spec pixel grid width  (SPEC §3.8)
_SRC_H = 20   # spec pixel grid height
_SCALE_W = HALLMARK_W // _SRC_W   # horizontal scale factor (currently 2)
_SCALE_H = HALLMARK_H // _SRC_H   # vertical scale factor   (currently 2)
_SCALE = _SCALE_W                  # scale must be uniform (NN); assertion below
assert _SCALE_W == _SCALE_H, "HALLMARK_W/H must give equal scale in both axes"

# ── Module-level cache ────────────────────────────────────────────────────────
# Maps input_str -> (lv.image_dsc_t, verbal_text)
_dsc_cache = {}


def clear_hallmark_cache():
    """Discard all cached hallmark image descriptors.

    Called by the dropup close handler so pixel buffers are freed as soon
    as the panel is gone.  The cache refills naturally on the next open().
    """
    _dsc_cache.clear()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _hex_to_rgb565_le(hex_str):
    """Parse '#rrggbb' → (lo_byte, hi_byte) packed as little-endian RGB565."""
    r = int(hex_str[1:3], 16) >> 3   # 5 bits
    g = int(hex_str[3:5], 16) >> 2   # 6 bits
    b = int(hex_str[5:7], 16) >> 3   # 5 bits
    v = (r << 11) | (g << 5) | b     # 16-bit RGB565
    return (v & 0xFF, v >> 8)         # little-endian byte pair


def _make_dsc(input_str, style):
    """Hash *input_str* once, then derive pixels, colors, and words.

    The SHA-256 digest is computed via hallmark_digest() and reused for both
    hallmark_pixels_packed() and hallmark_words() — no double hashing.

    Returns:
        (lv.image_dsc_t, verbal_text)  where verbal_text is the three words
        joined by spaces, e.g. ``"violin orbit tangerine"``.
    """
    hb = hallmark_digest(input_str)
    packed, colors = hallmark_pixels_packed(hb=hb)
    words = hallmark_words(hb=hb)

    # Unpack 2-bit-per-pixel 14×20 grid → flat array of values 0/1/2.
    # packed is bytearray(70); 4 pixels per byte, MSB-first (SPEC §3.8).
    flat = bytearray(280)
    for i in range(280):
        flat[i] = (packed[i >> 2] >> ((3 - (i & 3)) * 2)) & 3

    # Build RGB565 palette: index 0=background, 1=primary, 2=accent
    palette = [
        _hex_to_rgb565_le(colors["background"]),
        _hex_to_rgb565_le(colors["primary"]),
        _hex_to_rgb565_le(colors["accent"]),
    ]

    # 2× nearest-neighbour upscale: 14×20 → 28×40, RGB565 little-endian.
    data = bytearray(HALLMARK_W * HALLMARK_H * 2)
    for sy in range(_SRC_H):
        for sx in range(_SRC_W):
            lo, hi = palette[flat[sy * _SRC_W + sx]]
            for dy in range(_SCALE_H):
                ty = sy * _SCALE_H + dy
                for dx in range(_SCALE_W):
                    tx = sx * _SCALE_W + dx
                    idx = (ty * HALLMARK_W + tx) * 2
                    data[idx]     = lo
                    data[idx + 1] = hi

    dsc = lv.image_dsc_t({
        "header": {
            "w": HALLMARK_W,
            "h": HALLMARK_H,
            "cf": lv.COLOR_FORMAT.RGB565,
        },
        "data_size": len(data),
        "data": bytes(data),
    })

    return dsc, " ".join(words)


# ── Public API ────────────────────────────────────────────────────────────────

class HallmarkWidget:
    """Deterministic visual fingerprint widget.

    Creates an ``lv.image`` child of *parent* showing the hallmark for
    *input_str*, with cached rendering so repeated opens of the same dropup
    never re-hash or re-render.

    Usage::

        hw = HallmarkWidget(row, seed.get_fingerprint())
        # hw.img   — the lv.image (already parented to *row*)
        # hw.verbal_text  — "word1 word2 word3"

    Attributes:
        img:          The ``lv.image`` LVGL widget (child of *parent*).
        verbal_text:  Space-joined BIP-39 words, e.g. ``"violin orbit tangerine"``.
    """

    def __init__(self, parent, input_str, style="standard"):
        if input_str not in _dsc_cache:
            _dsc_cache[input_str] = _make_dsc(input_str, style)
        dsc, verbal = _dsc_cache[input_str]

        img = lv.image(parent)
        img.set_src(dsc)
        img.set_width(HALLMARK_W)
        img.set_height(HALLMARK_H)

        self.img = img
        self.verbal_text = verbal
