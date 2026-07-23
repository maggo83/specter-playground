"""Bit32Vis widget — deterministic visual fingerprint for a string identifier.

Replaces the former Sha256Vis/hallmark widget.  Input is accepted as any
string; hex fingerprints (optional "0x"/"0X" prefix) are parsed directly as
integers, all other strings are reduced to 32 bits via the first 4 bytes of
SHA-256.

Two rendering modes via the ``render`` parameter:

``render="canvas"`` (default)
    32×44 tile composed of:
      • an outer ``lv.obj`` with rounded corners (radius = 5 px), the
        Bit32Vis background color, optional 1 px border, and
        ``clip_corner=true``;
      • an inner ``lv.canvas`` (RGB565, 2 816 B) that renders the
        16×22 connection-graph raster upscaled 2×.

``render="pixel"``
    32×44 ``lv.image`` — plain pixel buffer, no rounded corners.

Call clear_hallmark_cache() to free C-side draw-buffer memory when the
widgets are no longer needed (e.g. on dropup close).
"""

import hashlib
import lvgl as lv
import bit32vis
from ..ui_consts import HALLMARK_W, HALLMARK_H, HALLMARK_CANVAS_W

# ── Render dimensions ─────────────────────────────────────────────────────────
_PX_W  = bit32vis.PIXEL_WIDTH   # 16 — native raster width
_PX_H  = bit32vis.PIXEL_HEIGHT  # 22 — native raster height
_SCALE = 2                       # nearest-neighbour upscale factor
_IMG_W = _PX_W * _SCALE          # 32 == HALLMARK_W
_IMG_H = _PX_H * _SCALE          # 44 == HALLMARK_H

_CANVAS_W   = HALLMARK_CANVAS_W  # 32 px
_CANVAS_H   = HALLMARK_H         # 44 px
_C_TILE_R   = 5                  # rounded corner radius for canvas tile
_LV_RADIUS_CIRCLE = 0x7FFF       # LV_RADIUS_CIRCLE — fully rounded rect

# ── Module-level caches ───────────────────────────────────────────────────────
# Pixel mode:  (input_str, style) -> lv.image_dsc_t
_dsc_cache = {}
# Canvas mode: (input_str, style) -> (background_int, foreground_int, pixels)
_canvas_cache = {}
# C-side draw buffers — must be explicitly destroyed to avoid memory leaks.
_canvas_draw_bufs = []


def clear_hallmark_cache():
    """Discard all cached Bit32Vis widget data and free C-side draw buffers.

    Call this when the containing panel is closed so the 2 816 B per canvas
    widget is released.  The cache refills naturally on the next open().
    """
    _dsc_cache.clear()
    _canvas_cache.clear()
    for _buf in _canvas_draw_bufs:
        try:
            _buf.destroy()
        except Exception:
            pass
    _canvas_draw_bufs.clear()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _str_to_bits(input_str):
    """Convert an input string to an unsigned 32-bit integer.

    Hex strings (with optional "0x"/"0X" prefix) are parsed directly and
    masked to 32 bits.  All other strings are hashed with SHA-256 and the
    first four bytes are returned as a big-endian integer.
    """
    s = input_str.strip()
    if s.startswith(("0x", "0X")):
        s = s[2:]
    try:
        return int(s, 16) & 0xFFFFFFFF
    except ValueError:
        pass
    hb = hashlib.sha256(input_str.encode()).digest()
    return (hb[0] << 24) | (hb[1] << 16) | (hb[2] << 8) | hb[3]


def _map_style(style):
    """Map legacy hyphenated style names to bit32vis underscore names."""
    if style == "high-contrast":
        return bit32vis.HIGH_CONTRAST
    return style


def _hex_to_rgb565_le(hex_str):
    """Parse '#rrggbb' → (lo_byte, hi_byte) little-endian RGB565."""
    r = int(hex_str[1:3], 16) >> 3
    g = int(hex_str[3:5], 16) >> 2
    b = int(hex_str[5:7], 16) >> 3
    v = (r << 11) | (g << 5) | b
    return (v & 0xFF, v >> 8)


def _hex_to_lv_int(hex_str):
    """Parse '#rrggbb' → 24-bit integer for lv.color_hex()."""
    return int(hex_str[1:], 16)


def _get_visual(input_str, style):
    """Return (bg_int, fg_int, pixels) for *input_str*, using cache."""
    cache_key = (input_str, style)
    if cache_key not in _canvas_cache:
        bits = _str_to_bits(input_str)
        vis  = bit32vis.pixels(bits, style)
        _canvas_cache[cache_key] = (
            _hex_to_lv_int(vis["background"]["hex"]),
            _hex_to_lv_int(vis["foreground"]["hex"]),
            vis["pixels"],
        )
    return _canvas_cache[cache_key]


def _make_dsc(input_str, style):
    """Build an RGB565 lv.image_dsc_t (32×44) from the Bit32Vis raster."""
    bits = _str_to_bits(input_str)
    vis  = bit32vis.pixels(bits, style)
    pix  = vis["pixels"]
    bg   = _hex_to_rgb565_le(vis["background"]["hex"])
    fg   = _hex_to_rgb565_le(vis["foreground"]["hex"])

    # 2× nearest-neighbour upscale: 16×22 → 32×44, RGB565 little-endian.
    data = bytearray(_IMG_W * _IMG_H * 2)
    for sy in range(_PX_H):
        for sx in range(_PX_W):
            lo, hi = fg if pix[sy * _PX_W + sx] else bg
            for dy in range(_SCALE):
                ty = sy * _SCALE + dy
                for dx in range(_SCALE):
                    tx = sx * _SCALE + dx
                    idx = (ty * _IMG_W + tx) * 2
                    data[idx]     = lo
                    data[idx + 1] = hi

    return lv.image_dsc_t({
        "header": {
            "w": _IMG_W,
            "h": _IMG_H,
            "cf": lv.COLOR_FORMAT.RGB565,
        },
        "data_size": len(data),
        "data": bytes(data),
    })


def _make_canvas(parent, input_str, style, bordered):
    """Build a canvas-mode Bit32Vis tile (32×44 px) with rounded corners.

    Composed of:
      • ``wrapper`` — lv.obj with rounded corners, background color,
        optional border, and clip_corner=True.
      • ``canvas``  — RGB565 lv.canvas child that holds the 2× upscaled
        connection-graph raster.

    Returns the wrapper widget.
    """
    bg_int, fg_int, pix = _get_visual(input_str, style)

    # ── Outer wrapper ─────────────────────────────────────────────────────
    wrapper = lv.obj(parent)
    wrapper.set_size(_CANVAS_W, _CANVAS_H)
    wrapper.set_style_radius(_C_TILE_R, 0)
    wrapper.set_style_bg_color(lv.color_hex(bg_int), 0)
    wrapper.set_style_bg_opa(lv.OPA.COVER, 0)
    wrapper.set_style_pad_all(0, 0)
    wrapper.set_style_clip_corner(True, 0)
    if bordered:
        wrapper.set_style_border_color(lv.color_hex(fg_int), 0)
        wrapper.set_style_border_width(1, 0)
        wrapper.set_style_border_opa(lv.OPA.COVER, 0)
    else:
        wrapper.set_style_border_width(0, 0)
    wrapper.remove_flag(lv.obj.FLAG.SCROLLABLE)

    # ── Inner canvas ──────────────────────────────────────────────────────
    # lv.draw_buf_create() allocates C-side memory; keep a reference in
    # _canvas_draw_bufs so it survives GC and can be explicitly freed.
    draw_buf = lv.draw_buf_create(_CANVAS_W, _CANVAS_H,
                                  lv.COLOR_FORMAT.RGB565, 0)
    canvas = lv.canvas(wrapper)
    canvas.set_draw_buf(draw_buf)
    canvas.set_pos(0, 0)
    _canvas_draw_bufs.append(draw_buf)

    canvas.fill_bg(lv.color_hex(bg_int), lv.OPA.COVER)

    # ── Draw 2× upscaled connection-graph raster ─────────────────────────
    layer = lv.layer_t()
    canvas.init_layer(layer)

    rect = lv.draw_rect_dsc_t()
    rect.init()
    rect.bg_opa     = lv.OPA.COVER
    rect.border_opa = lv.OPA.TRANSP
    rect.bg_color   = lv.color_hex(fg_int)
    rect.radius     = 0

    for py in range(_PX_H):
        for px in range(_PX_W):
            if pix[py * _PX_W + px]:
                x1 = px * _SCALE
                y1 = py * _SCALE
                area = lv.area_t({
                    "x1": x1, "y1": y1,
                    "x2": x1 + _SCALE - 1, "y2": y1 + _SCALE - 1,
                })
                lv.draw_rect(layer, rect, area)

    canvas.finish_layer(layer)
    return wrapper


# ── Public API ────────────────────────────────────────────────────────────────

class HallmarkWidget:
    """Bit32Vis visual fingerprint widget.

    Parameters
    ----------
    parent    : lv.obj
        Parent LVGL object.
    input_str : str
        Hex fingerprint or arbitrary label string.
    style     : str
        ``"standard"`` (default), ``"high_contrast"`` / ``"high-contrast"``,
        or ``"monochrome"``.
    render    : str
        ``"canvas"`` (default) — 32×44 tile with rounded corners.
        ``"pixel"``            — 32×44 plain lv.image, no rounding.
    bordered  : bool
        Canvas mode only: draw a 1 px border.  Default ``False``.

    Attributes
    ----------
    img         : The LVGL widget (lv.obj wrapper or lv.image).
    verbal_text : Always ``None`` — Bit32Vis has no verbal output.
    """

    H_PAD = 6  # left + right margin in flex/row layouts

    def __init__(self, parent, input_str, style="standard",
                 render="canvas", bordered=False):
        style = _map_style(style)

        if render == "canvas":
            widget = _make_canvas(parent, input_str, style, bordered)
        else:
            cache_key = (input_str, style)
            if cache_key not in _dsc_cache:
                _dsc_cache[cache_key] = _make_dsc(input_str, style)
            dsc = _dsc_cache[cache_key]
            widget = lv.image(parent)
            widget.set_src(dsc)
            widget.set_width(_IMG_W)
            widget.set_height(_IMG_H)

        widget.set_style_margin_left(self.H_PAD, 0)
        widget.set_style_margin_right(self.H_PAD, 0)

        self.img        = widget
        self.verbal_text = None  # Bit32Vis has no verbal/word output
