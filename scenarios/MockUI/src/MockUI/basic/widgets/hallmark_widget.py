"""Hallmark widget — deterministic visual fingerprint for a string identifier.

Two rendering modes are available via the ``render`` parameter of
``HallmarkWidget``:

``render="pixel"``  (default, SPEC §3.8)
    14×20 pixel-art grid upscaled 2× with nearest-neighbour to 28×40 px,
    wrapped in an ``lv.image``.  Fast, low memory (560 B/widget).

``render="canvas"``  (SPEC §3.5, spec-compliant)
    30×40 tile composed of:
      • an outer ``lv.obj`` wrapper styled with rounded corners
        (radius = 5 px), the hallmark background color, optional 1 px
        primary-color border, and ``clip_corner=true`` so the inner
        canvas's rectangular corners are masked away;
      • an inner ``lv.canvas`` (RGB565, 2 400 B) that draws the dots
        on top of the matching background color.
    Enable ``bordered=True`` for an explicit stroke.

A module-level cache stores derived data per input string so that
SHA-256 hashing and colour math are not repeated for the same identifier.
Call clear_hallmark_cache() when the caches are no longer needed.
"""

import lvgl as lv
from hallmark import hallmark_digest, hallmark_pixels_packed, hallmark_spec, hallmark_words
from ..ui_consts import HALLMARK_W, HALLMARK_H, HALLMARK_CANVAS_W

# ── Pixel-mode render dimensions (SPEC §3.8) ────────────────────────────────
_SRC_W   = 14   # spec pixel grid width
_SRC_H   = 20   # spec pixel grid height
_SCALE_W = HALLMARK_W // _SRC_W   # horizontal scale factor (currently 2)
_SCALE_H = HALLMARK_H // _SRC_H   # vertical scale factor   (currently 2)
_SCALE   = _SCALE_W                # scale must be uniform (NN); assertion below
assert _SCALE_W == _SCALE_H, "HALLMARK_W/H must give equal scale in both axes"

# ── Canvas-mode render dimensions (SPEC §3.5) ────────────────────────────────
# W = H / 1.32 = 40 / 1.32 ≈ 30  →  spec aspect ratio 100:132 at H=40.
_CANVAS_W       = HALLMARK_CANVAS_W  # 30 px
_CANVAS_H       = HALLMARK_H         # 40 px (fixed)
_C_PAD          = 3                  # floor(0.10 × 30)  padding (all edges)
_C_CS           = 4.8               # (30 − 2×3) / 5   cell size
_C_TILE_R       = 5                  # round(0.16 × 30)  tile corner radius
_C_DOT_D        = 4                  # round(0.40 × 4.8 × 2)  primary dot ⌀
_C_ACC_D        = 4                  # round(0.46 × 4.8 × 2)  accent dot ⌀
_C_MONO_R       = 1                  # round(0.15 × 4)   monochrome accent r
_LV_RADIUS_CIRCLE = 0x7FFF           # LV_RADIUS_CIRCLE — fully-rounded rect

# ── Module-level caches ──────────────────────────────────────────────────────
# Pixel mode:  input_str -> (lv.image_dsc_t, verbal_text)
_dsc_cache = {}
# Canvas mode: input_str -> (cells, colors, verbal_text)  (no pixel buffer)
_canvas_spec_cache = {}
# draw_buf_t objects for canvas mode — kept so they can be destroyed on clear.
# lv.draw_buf_create() allocates C-side memory; we must hold a Python reference.
_canvas_draw_bufs = []


def clear_hallmark_cache():
    """Discard all cached hallmark data (pixel descriptors and canvas specs).

    Called by the dropup close handler so pixel buffers are freed as soon
    as the panel is gone.  The cache refills naturally on the next open().

    IMPORTANT: ``lv.draw_buf_create()`` allocates C-side memory that is
    *not* released when the Python wrapper goes out of scope.  We must
    explicitly call ``buf.destroy()`` on every buffer or the memory leaks
    on every dropup open/close cycle (≈ 2 400 B per canvas hallmark) and
    will eventually crash the device.
    """
    _dsc_cache.clear()
    _canvas_spec_cache.clear()
    for _buf in _canvas_draw_bufs:
        try:
            _buf.destroy()
        except Exception:
            pass
    _canvas_draw_bufs.clear()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _hex_to_rgb565_le(hex_str):
    """Parse '#rrggbb' → (lo_byte, hi_byte) packed as little-endian RGB565."""
    r = int(hex_str[1:3], 16) >> 3   # 5 bits
    g = int(hex_str[3:5], 16) >> 2   # 6 bits
    b = int(hex_str[5:7], 16) >> 3   # 5 bits
    v = (r << 11) | (g << 5) | b     # 16-bit RGB565
    return (v & 0xFF, v >> 8)         # little-endian byte pair


def _hex_to_lv_int(hex_str):
    """Parse '#rrggbb' → 24-bit integer for lv.color_hex()."""
    return int(hex_str[1:], 16)


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


def _make_canvas(parent, input_str, style, bordered):
    """Build a canvas-mode widget (SPEC §3.5, 30×40 px).

    The widget is composed of two LVGL objects:

      • ``wrapper`` — an ``lv.obj`` styled with rounded corners
        (radius = _C_TILE_R), the hallmark background color, an
        optional 1 px primary-color border, and ``clip_corner=true``
        so the rectangular pixels of the inner canvas are masked.
      • ``canvas`` — an RGB565 ``lv.canvas`` child filled with the
        same background color, on which the dots are drawn.

    Returns:
        (wrapper, verbal_text)
    """
    # ── Retrieve or derive cell/color data (cached) ───────────────────────
    if input_str not in _canvas_spec_cache:
        hb   = hallmark_digest(input_str)
        spec = hallmark_spec(hb=hb, style=style)
        _canvas_spec_cache[input_str] = (
            spec["cells"],
            spec["colors"],
            spec["words_text"],
        )
    cells, colors, verbal_text = _canvas_spec_cache[input_str]

    bg_int = _hex_to_lv_int(colors["background"])
    fg_int = _hex_to_lv_int(colors["primary"])
    ac_int = _hex_to_lv_int(colors["accent"])

    # ── Outer wrapper: rounded background + optional border ───────────────
    # clip_corner masks the inner canvas's rectangular corner pixels so the
    # tile appears truly rounded without needing an ARGB8888 buffer.
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
    # No scroll behaviour on the static tile container.
    wrapper.remove_flag(lv.obj.FLAG.SCROLLABLE)

    # ── Inner canvas: dots only (RGB565, 2 400 B) ─────────────────────────
    # lv.draw_buf_create() allocates C-side memory; keep a Python reference
    # in _canvas_draw_bufs so it isn't garbage-collected while in use.
    draw_buf = lv.draw_buf_create(_CANVAS_W, _CANVAS_H,
                                   lv.COLOR_FORMAT.RGB565, 0)
    canvas   = lv.canvas(wrapper)
    canvas.set_draw_buf(draw_buf)
    canvas.set_pos(0, 0)
    _canvas_draw_bufs.append(draw_buf)

    # Fill with the same background color as the wrapper — clip_corner on
    # the wrapper hides the four rectangular corners.
    canvas.fill_bg(lv.color_hex(bg_int), lv.OPA.COVER)

    # ── Draw dots via the LVGL v9 layer API ───────────────────────────────
    layer = lv.layer_t()
    canvas.init_layer(layer)

    is_mono = (style == "monochrome")
    dot = lv.draw_rect_dsc_t()
    dot.init()
    dot.bg_opa     = lv.OPA.COVER
    dot.border_opa = lv.OPA.TRANSP

    for row in range(7):
        tly = round(_C_PAD + row * _C_CS + _C_CS / 2 - _C_DOT_D / 2)
        for col in range(5):
            v = cells[row][col]
            if v == 0:
                continue
            tlx = round(_C_PAD + col * _C_CS + _C_CS / 2 - _C_DOT_D / 2)
            if v == 2:
                # Accent: circle for standard/high-contrast; rounded square
                # for monochrome (shape carries the value-2 distinction).
                dot.bg_color = lv.color_hex(ac_int)
                dot.radius   = _C_MONO_R if is_mono else _LV_RADIUS_CIRCLE
                d = _C_ACC_D
            else:
                # Primary (value 1): filled circle.
                dot.bg_color = lv.color_hex(fg_int)
                dot.radius   = _LV_RADIUS_CIRCLE
                d = _C_DOT_D
            area = lv.area_t({"x1": tlx, "y1": tly,
                              "x2": tlx + d - 1, "y2": tly + d - 1})
            lv.draw_rect(layer, dot, area)

    canvas.finish_layer(layer)

    return wrapper, verbal_text


# ── Public API ────────────────────────────────────────────────────────────────

class HallmarkWidget:
    """Deterministic visual fingerprint widget.

    Parameters
    ----------
    parent    : lv.obj
        Parent LVGL object.
    input_str : str
        String identifier to visualise (address, fingerprint, …).
    style     : str
        ``"standard"`` (default), ``"high-contrast"``, or ``"monochrome"``.
    render    : str
        ``"pixel"`` (default) — SPEC §3.8 pixel-art upscaled to 28×40 px.
        ``"canvas"``          — SPEC §3.5 tile, 30×40 px, rounded corners.
    bordered  : bool
        Canvas mode only: draw a 1 px primary-color border around the tile
        (SPEC §3.5).  Makes the rounded corners visible.  Default ``False``.

    Usage::

        hw = HallmarkWidget(row, seed.get_fingerprint())
        hw = HallmarkWidget(row, addr, render="canvas", bordered=True)

    Attributes:
        img:          The LVGL widget (``lv.image`` or ``lv.canvas``).
        verbal_text:  Space-joined BIP-39 words, e.g. ``"violin orbit tangerine"``.
    """

    # Horizontal padding applied to *both* render modes so the widget
    # always reserves 3 px gutter on each side in flex/row layouts.
    # Implemented as an outer margin (LVGL adds it outside the widget
    # in flex/grid layouts) so the actual hallmark graphic keeps its
    # native pixel-perfect dimensions.
    H_PAD = 6

    def __init__(self, parent, input_str, style="standard",
                 render="pixel", bordered=False):
        if render == "canvas":
            # _make_canvas returns the wrapper, already sized _CANVAS_W×_CANVAS_H.
            widget, verbal = _make_canvas(parent, input_str, style, bordered)
        else:
            if input_str not in _dsc_cache:
                _dsc_cache[input_str] = _make_dsc(input_str, style)
            dsc, verbal = _dsc_cache[input_str]
            widget = lv.image(parent)
            widget.set_src(dsc)
            widget.set_width(HALLMARK_W)
            widget.set_height(HALLMARK_H)

        widget.set_style_margin_left(self.H_PAD, 0)
        widget.set_style_margin_right(self.H_PAD, 0)

        self.img = widget   # .img alias kept for existing callers
        self.verbal_text = verbal
