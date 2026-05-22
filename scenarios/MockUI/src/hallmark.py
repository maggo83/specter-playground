# Sha256Vis — MicroPython port of the Sha256Vis visual identity algorithm.
# SPDX-License-Identifier: MIT
#
# Algorithm: https://github.com/specter-diy/hallmarks  (Sha256Vis variant)
#
# Pipeline:
#   1. sha256(input) → 32 bytes hb[0..31]
#   2. For i in 0..3:  c[i] = CRC-8/SMBUS(hb[i], hb[i+4], …, hb[i+28])
#   3. c[0] → hue (top 4 bits) + chroma offset (bottom 4 bits)
#      c[1]+c[2]+top 5 bits of c[3] → 21 cell bits (7 rows × 3 cols, mirrored to 7×5)
#      bit 2 of c[3] → flip bit; bits 1..0 of c[3] → luminance index
#   4. Mirror 7×3 grid → 7×5 cells (on/off only, no accent).
#
# ── BIP-39 wordlist dependency ────────────────────────────────────────────────
# This module tries to import the BIP-39 English wordlist from embit
# (https://github.com/diybitcoinhardware/embit), a widely used Bitcoin library
# for embedded Python.  When embit is present its wordlist is compiled as a
# frozen module, so reusing it costs zero extra RAM or flash.
#
# If embit is not installed, the bundled bip39_english.py in this directory is
# loaded instead.  That file is a standalone copy of the same public-domain word
# list; freeze it via your board manifest to keep it in flash rather than RAM.
# ─────────────────────────────────────────────────────────────────────────────

import hashlib
import math

try:
    from embit.wordlists.bip39 import WORDLIST as _BIP39
except ImportError:
    from bip39_english import WORDLIST as _BIP39

# =============================================================================
# Tunable constants (matching Sha256Vis Java reference implementation)
# =============================================================================

_BASE_L_MIN      = 0.50
_BASE_L_MAX      = 0.70
_CHROMA_MIN      = 0.05
_CHROMA_MAX      = 0.25
_HC_L_ADD        = 0.30
_BG_L_SPREAD     = 0.50
_BG_L_EXTRA_HC   = 0.30
_CHROMA_STD_ADD  = 0.00
_CHROMA_HC_ADD   = 0.10

# =============================================================================
# CRC-8/SMBUS (poly=0x07, init=0x00, no reflect, no xorout)
# =============================================================================

def _crc8(data):
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def _c_bytes(hb):
    """Compute the four c-bytes from a 32-byte hash via CRC-8/SMBUS."""
    c = [0, 0, 0, 0]
    buf = bytearray(8)
    for i in range(4):
        for k in range(8):
            buf[k] = hb[i + k * 4]
        c[i] = _crc8(buf)
    return c


def _sha_parity(hb):
    """XOR-parity of all 32 SHA-256 bytes: True when total set-bit count is odd."""
    p = 0
    for b in hb:
        v = b
        v = v - ((v >> 1) & 0x55)
        v = (v & 0x33) + ((v >> 2) & 0x33)
        p ^= (v + (v >> 4)) & 0x0F
    return (p & 1) == 1

# =============================================================================
# OKLCH → sRGB  (SPEC §3.7)
# =============================================================================

def _srgb_encode(v):
    v = max(0.0, min(1.0, v))
    if v <= 0.0031308:
        return 12.92 * v
    return 1.055 * (v ** (1.0 / 2.4)) - 0.055


def _oklch_to_hex(L, C, h):
    """Convert OKLCH triple to a lowercase '#rrggbb' hex string."""
    hr = h * math.pi / 180.0
    a = C * math.cos(hr)
    b = C * math.sin(hr)

    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l3 = l_ * l_ * l_
    m3 = m_ * m_ * m_
    s3 = s_ * s_ * s_

    r  = _srgb_encode( 4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3)
    g  = _srgb_encode(-1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3)
    b_ = _srgb_encode(-0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3)

    ri = max(0, min(255, round(r  * 255)))
    gi = max(0, min(255, round(g  * 255)))
    bi = max(0, min(255, round(b_ * 255)))
    return "#{:02x}{:02x}{:02x}".format(ri, gi, bi)

# =============================================================================
# Color derivation — dynamic OKLCH colors derived from c[0] and c[3].
# Returns (bg_hex, fg_hex) for the given style.
# =============================================================================

def _derive_colors(c, style, swap_luminance):
    """Derive bg/fg hex colors from c-bytes.
    swap_luminance (bool): when True, swap fg and bg luminance (driven by SHA parity).
    """
    hi4 = (c[0] >> 4) & 0xF
    lo4 = c[0] & 0xF
    hue        = hi4 * (360.0 / 16.0)
    chroma_off = _CHROMA_MIN + lo4 * ((_CHROMA_MAX - _CHROMA_MIN) / 15.0)

    lum_idx = (c[3] >> 2) & 0x3   # c[3] bits 3..2
    base_l  = _BASE_L_MIN + lum_idx * ((_BASE_L_MAX - _BASE_L_MIN) / 3.0)

    if style == "standard":
        fg_l = base_l
        bg_l = fg_l - _BG_L_SPREAD
        fg_c = chroma_off + _CHROMA_STD_ADD
        bg_c = chroma_off + _CHROMA_STD_ADD
    elif style == "high-contrast":
        fg_l = base_l + _HC_L_ADD
        bg_l = fg_l - _BG_L_SPREAD - _BG_L_EXTRA_HC
        fg_c = chroma_off + _CHROMA_HC_ADD
        bg_c = chroma_off + _CHROMA_HC_ADD
    else:  # monochrome
        fg_l = base_l + _HC_L_ADD
        bg_l = fg_l - _BG_L_SPREAD - _BG_L_EXTRA_HC
        fg_c = 0.0
        bg_c = 0.0

    fg_l = max(0.0, min(1.0, fg_l))
    bg_l = max(0.0, min(1.0, bg_l))

    if swap_luminance:
        fg_l, bg_l = bg_l, fg_l

    fg_h = hue
    bg_h = (hue + 180.0) % 360.0

    return _oklch_to_hex(bg_l, bg_c, bg_h), _oklch_to_hex(fg_l, fg_c, fg_h)

# =============================================================================
# Cell generation — 20-bit stream from c[1]/c[2]/c[3] into a 7×5 grid.
# Produces a list[7][5] of ints (0=background, 1=foreground).
#
# Mirror mode selected by parity_odd:
#   Even: vertical mirror  — rows 4,5,6 mirror rows 2,1,0; center cell = 0
#   Odd:  horizontal mirror — cols 3,4 mirror cols 1,0;   center cell = 1
#
# Point-mirror override: if swap=True and raw set-bit count < 10, use POINT_MAP.
# =============================================================================

# 180°-rotationally-symmetric layout for the point-mirror override.
# Cells sharing the same index are symmetric around [3][2].
_POINT_MAP = (
     0,  1,  2,  3,  4,
     5,  6,  7,  8,  9,
    10, 11, 12, 13, 17,
    14, 15, 16, 15, 14,
    17, 18, 12, 11, 10,
    19,  8,  7,  6,  5,
     4,  3,  2,  1,  0,
)


def _invert_cells(grid):
    for r in range(7):
        for col in range(5):
            grid[r][col] ^= 1


def _build_axis_grid(stream, parity_odd):
    grid = [[0] * 5 for _ in range(7)]
    if not parity_odd:
        # Even parity: vertical mirror (top↔bottom), center cell forced off.
        bit = 0
        for r in range(4):
            for col in range(5):
                grid[r][col] = (stream >> (19 - bit)) & 1
                bit += 1
        grid[3][2] = 0
        for col in range(5):
            grid[4][col] = grid[2][col]
            grid[5][col] = grid[1][col]
            grid[6][col] = grid[0][col]
    else:
        # Odd parity: horizontal mirror (left↔right), center cell forced on.
        bit = 0
        for col in range(3):
            for r in range(7):
                if r == 3 and col == 2:
                    continue
                grid[r][col] = (stream >> (19 - bit)) & 1
                bit += 1
        grid[3][2] = 1
        for r in range(7):
            grid[r][3] = grid[r][1]
            grid[r][4] = grid[r][0]
    return grid


def _build_point_grid(stream):
    grid = [[0] * 5 for _ in range(7)]
    for i in range(35):
        grid[i // 5][i % 5] = (stream >> (19 - _POINT_MAP[i])) & 1
    return grid


def _build_cells(c, flip, parity_odd, swap):
    """Build the 7×5 cell grid.
    flip       — c[3] bit 1: invert cells (on↔off) after mirroring.
    parity_odd — SHA-256 parity (True=odd): selects mirror axis.
    swap       — c[3] bit 0: enables point-mirror override when set-bit count < 10.
    """
    stream = (c[1] << 12) | (c[2] << 4) | (c[3] >> 4)   # 20-bit

    grid = _build_axis_grid(stream, parity_odd)
    if flip:
        _invert_cells(grid)

    # Raw set-bit count in the 20-bit stream (adjusted for flip inversion)
    raw_bits = stream & 0xFFFFF
    raw_set = (20 - bin(raw_bits).count('1')) if flip else bin(raw_bits).count('1')
    if swap and raw_set < 10:
        grid = _build_point_grid(stream)
        if flip:
            _invert_cells(grid)

    return grid

# =============================================================================
# Verbal companion  (SPEC §3.4)
# Three BIP-39 words derived from the low 33 bits of bytes 27..31.
# =============================================================================

def _derive_words(hb):
    hi = hb[27] & 0x7F                                              # 7 bits
    lo = (hb[28] << 24) | (hb[29] << 16) | (hb[30] << 8) | hb[31] # 32 bits
    i1 = ((hi << 5) | (lo >> 27)) & 0x7FF
    i2 = (lo >> 11) & 0x7FF
    i3 = lo & 0x7FF
    return (_BIP39[i1], _BIP39[i2], _BIP39[i3])

# =============================================================================
# 14×20 low-resolution pixel grid  (SPEC §3.8)
#
# Internally the grid is always generated in 2-bit-packed form (70 bytes),
# where 4 pixels share one byte, MSB-first:
#
#   byte index  = flat_index >> 2
#   bit shift   = (3 - (flat_index & 3)) * 2
#   value mask  = 0b11  (0, 1, or 2)
#
# Pixel 0 occupies bits 7:6 of byte 0, pixel 1 bits 5:4, pixel 2 bits 3:2,
# pixel 3 bits 1:0, pixel 4 bits 7:6 of byte 1, and so on.
# This costs 70 bytes vs 280 for the flat form — useful on devices that keep
# several grids in RAM simultaneously.
# =============================================================================

def _gen_pixels_packed(cells):
    """Generate the 14x20 pixel grid directly in 2-bit-packed form.

    Each on-cell fills a 2×2 block in the top-left corner of its 3×3 slot.
    Only values 0 (background) and 1 (foreground) are produced — no accent.

    Returns bytearray(70).  No intermediate 280-byte allocation is made.
    """
    px = bytearray(70)
    for y in range(7):
        for x in range(5):
            if cells[y][x] == 0:
                continue
            bx = x * 3
            by = y * 3
            for ry, cx in ((by, bx), (by, bx + 1), (by + 1, bx), (by + 1, bx + 1)):
                fi = ry * 14 + cx
                px[fi >> 2] |= 1 << ((3 - (fi & 3)) * 2)
    return px


def pixels_unpack(packed):
    """Expand a 2-bit-packed pixel grid to a flat bytearray.

    Parameters
    ----------
    packed : bytearray(70)
        Output of ``_gen_pixels_packed`` or ``hallmark_pixels_packed``.

    Returns
    -------
    bytearray(280) — row-major 14x20, values 0/1/2.
    """
    out = bytearray(280)
    for i in range(280):
        out[i] = (packed[i >> 2] >> ((3 - (i & 3)) * 2)) & 3
    return out


def pixels_pack(unpacked):
    """Pack a flat pixel grid into 2-bit-per-pixel form.

    Convenience utility for code that already holds a bytearray(280) and
    wants to compress it.  When generating from scratch, prefer
    ``hallmark_pixels_packed`` to avoid ever allocating the flat form.

    Parameters
    ----------
    unpacked : bytearray(280)
        Row-major 14x20 grid, values 0/1/2.

    Returns
    -------
    bytearray(70).
    """
    px = bytearray(70)
    for i in range(280):
        v = unpacked[i]
        if v:
            px[i >> 2] |= v << ((3 - (i & 3)) * 2)
    return px

# =============================================================================
# Public API
#
# Every entry point takes either *input_str* (a UTF-8 string) or *hb* (the
# 32-byte SHA-256 digest of that string).  Pass *hb* when you have already
# computed it — e.g. when requesting both words and pixels for the same input —
# to avoid hashing twice.  Use ``hallmark_digest`` to obtain it.
# =============================================================================

def hallmark_digest(input_str):
    """Return the 32-byte SHA-256 digest of *input_str* (UTF-8 encoded).

    Pass the result as ``hb=`` to any other entry point in this module to
    avoid re-hashing when several outputs are needed for the same input.
    """
    return hashlib.sha256(input_str.encode()).digest()


def hallmark_spec(input_str=None, style="standard", hb=None):
    """Return the full Hallmark specification.

    Parameters
    ----------
    input_str : str, optional
        Any UTF-8 string (address, fingerprint, hash, …).  Required unless
        *hb* is given.
    style : str
        One of ``"standard"`` (default), ``"high-contrast"``, ``"monochrome"``.
    hb : bytes(32), optional
        Pre-computed SHA-256 digest from ``hallmark_digest``.  When supplied,
        *input_str* is ignored and no hashing is performed.

    Returns
    -------
    dict with keys:
        cells      — list[7][5] of int (0=background, 1=primary, 2=accent)
        words      — tuple of 3 BIP-39 strings
        words_text — space-joined verbal companion
        colors     — dict {background, primary, accent} → ``"#rrggbb"`` hex strings
        pixels     — bytearray(280), row-major 14x20 grid, values 0/1/2
        style      — the style string used
    """
    if hb is None:
        hb = hashlib.sha256(input_str.encode()).digest()
    c          = _c_bytes(hb)
    parity_odd = _sha_parity(hb)
    flip       = ((c[3] >> 1) & 1) == 1
    swap       = (c[3] & 1) == 1
    cells  = _build_cells(c, flip, parity_odd, swap)
    words  = _derive_words(hb)
    packed = _gen_pixels_packed(cells)
    bg, fg = _derive_colors(c, style, swap)
    return {
        "cells":      cells,
        "words":      words,
        "words_text": " ".join(words),
        "colors":     {"background": bg, "primary": fg, "accent": fg},
        "pixels":     pixels_unpack(packed),
        "style":      style,
    }


def hallmark_words(input_str=None, hb=None):
    """Return the three BIP-39 verbal companion words.

    This is the cheapest call — only the word-index extraction runs; no
    colour math or pixel generation.

    Parameters
    ----------
    input_str : str, optional
        Any UTF-8 string.  Required unless *hb* is given.
    hb : bytes(32), optional
        Pre-computed SHA-256 digest from ``hallmark_digest``.

    Returns
    -------
    tuple of 3 strings, e.g. ``("violin", "orbit", "tangerine")``
    """
    if hb is None:
        hb = hashlib.sha256(input_str.encode()).digest()
    return _derive_words(hb)


def hallmark_pixels(input_str=None, style="standard", hb=None):
    """Return the 14x20 pixel raster and the resolved paint colors.

    This is the primary output for embedded displays.  The pixel grid is
    style-independent (same positions and values for all styles); only the
    colors change.

    Parameters
    ----------
    input_str : str, optional
        Any UTF-8 string.  Required unless *hb* is given.
    style : str
        One of ``"standard"``, ``"high-contrast"``, ``"monochrome"``.
    hb : bytes(32), optional
        Pre-computed SHA-256 digest from ``hallmark_digest``.

    Returns
    -------
    (pixels, colors) where:
        pixels — bytearray(280), row-major 14x20.  0=background, 1=primary,
                 2=accent.  Upscale with nearest-neighbour (SPEC §3.8).
        colors — dict {background, primary, accent} → ``"#rrggbb"`` hex strings.
                 For monochrome displays collapse values 1 and 2 to "on".
    """
    packed, colors = hallmark_pixels_packed(input_str, style, hb=hb)
    return pixels_unpack(packed), colors


def hallmark_pixels_packed(input_str=None, style="standard", hb=None):
    """Return the 14x20 pixel grid in compact 2-bit-packed form.

    This is the preferred entry point on memory-constrained devices.  The
    grid is generated directly into 70 bytes; a 280-byte intermediate is
    never allocated.  Use ``pixels_unpack`` only if you need the flat form
    for a particular renderer.

    Parameters
    ----------
    input_str : str, optional
        Any UTF-8 string.  Required unless *hb* is given.
    style : str
        One of ``"standard"`` (default), ``"high-contrast"``, ``"monochrome"``.
    hb : bytes(32), optional
        Pre-computed SHA-256 digest from ``hallmark_digest``.

    Returns
    -------
    (pixels_packed, colors) where:
        pixels_packed — bytearray(70), 2 bits per pixel, 4 pixels per byte,
                        MSB-first.  Use ``pixels_unpack`` to expand.
        colors        — dict {background, primary, accent} → ``"#rrggbb"``.
    """
    if hb is None:
        hb = hashlib.sha256(input_str.encode()).digest()
    c          = _c_bytes(hb)
    parity_odd = _sha_parity(hb)
    flip       = ((c[3] >> 1) & 1) == 1
    swap       = (c[3] & 1) == 1
    cells  = _build_cells(c, flip, parity_odd, swap)
    pixels = _gen_pixels_packed(cells)
    bg, fg = _derive_colors(c, style, swap)
    return pixels, {"background": bg, "primary": fg, "accent": fg}
