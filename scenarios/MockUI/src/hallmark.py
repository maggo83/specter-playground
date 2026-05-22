# Hallmarks v1.0 — MicroPython reference implementation.
# SPDX-License-Identifier: MIT
#
# Spec:    SPEC.md  (CC0 1.0)  — https://hallmarks.info
# Licence: MIT      — see LICENSE at the repo root
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
# Style parameters — OKLCH [L, C] per role  (SPEC §4)
# =============================================================================

_STYLES = {
    "standard":      {"bg": (0.96, 0.025), "fg": (0.52, 0.16),  "ac": (0.66, 0.18)},
    "high-contrast": {"bg": (0.98, 0.04),  "fg": (0.28, 0.32),  "ac": (0.15, 0.40)},
    "monochrome":    {"bg": (0.96, 0.0),   "fg": (0.30, 0.0),   "ac": (0.30, 0.0)},
}

# =============================================================================
# Mulberry32 PRNG  (SPEC §3.6)
# All arithmetic is mod 2^32; intermediate products are explicitly masked.
# =============================================================================

def _m32_seed(b, off):
    """Return a 1-element list [state] seeded from 4 bytes of *b* at *off*."""
    return [((b[off] << 24) | (b[off + 1] << 16) | (b[off + 2] << 8) | b[off + 3]) & 0xFFFFFFFF]


def _m32_next(st):
    """Advance state in-place and return a float in [0, 1] (divisor 2^32-1)."""
    st[0] = (st[0] + 0x6D2B79F5) & 0xFFFFFFFF
    t = st[0]
    # Step 1
    t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
    # Step 2  — t0 is the value of t *before* this assignment (per spec)
    t0 = t
    mul = ((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF
    t = ((t + mul) & 0xFFFFFFFF) ^ t0
    # Result
    result = (t ^ (t >> 14)) & 0xFFFFFFFF
    return result / 0xFFFFFFFF          # divide by 2^32-1, matching spec §3.6

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
# Color derivation  (SPEC §3.2)
# Returns (bg_hex, primary_hex, accent_hex) for the given style.
# =============================================================================

def _derive_colors(hb, style):
    h1 = ((hb[0] << 8) | hb[1]) / 65536.0 * 360.0
    offset_raw = ((hb[2] << 8) | hb[3]) / 65536.0
    h2 = (h1 + 100.0 + offset_raw * 160.0) % 360.0

    p = _STYLES[style]
    hue_a = 0.0 if style == "monochrome" else h1
    hue_b = 0.0 if style == "monochrome" else h2

    return (
        _oklch_to_hex(p["bg"][0], p["bg"][1], hue_a),
        _oklch_to_hex(p["fg"][0], p["fg"][1], hue_a),
        _oklch_to_hex(p["ac"][0], p["ac"][1], hue_b),
    )

# =============================================================================
# Pattern generation  (SPEC §3.3)
# Produces a list[7][5] of ints (0=background, 1=primary, 2=accent).
# =============================================================================

def _gen_pattern(hb):
    for attempt in range(8):
        off = (4 + attempt * 4) % 28
        st = _m32_seed(hb, off)
        cells = []
        filled = 0
        for _ in range(7):                  # rows
            half = []
            for _ in range(3):              # half-columns (before mirror)
                v = _m32_next(st)
                if v < 0.50:
                    c = 0
                elif v < 0.85:
                    c = 1
                    filled += 1
                else:
                    c = 2
                    filled += 1
                half.append(c)
            # Mirror [a, b, c] → [a, b, c, b, a]
            cells.append([half[0], half[1], half[2], half[1], half[0]])
        if 0.45 <= filled / 21 <= 0.75:
            return cells

    # Fallback: use attempt 0 unconditionally  (SPEC §3.3, last paragraph)
    st = _m32_seed(hb, 4)
    cells = []
    for _ in range(7):
        half = []
        for _ in range(3):
            v = _m32_next(st)
            half.append(0 if v < 0.50 else (1 if v < 0.85 else 2))
        cells.append([half[0], half[1], half[2], half[1], half[0]])
    return cells

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

    Returns bytearray(70).  No intermediate 280-byte allocation is made.
    """
    px = bytearray(70)
    for y in range(7):
        for x in range(5):
            v = cells[y][x]
            if v == 0:
                continue
            bx = x * 3
            by = y * 3
            if v == 1:              # primary: solid 2×2 block
                for ry, cx in ((by, bx), (by, bx + 1), (by + 1, bx), (by + 1, bx + 1)):
                    fi = ry * 14 + cx
                    px[fi >> 2] |= 1 << ((3 - (fi & 3)) * 2)
            else:                   # accent: top-left + bottom-right diagonal
                for ry, cx in ((by, bx), (by + 1, bx + 1)):
                    fi = ry * 14 + cx
                    px[fi >> 2] |= 2 << ((3 - (fi & 3)) * 2)
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
    cells  = _gen_pattern(hb)
    words  = _derive_words(hb)
    packed = _gen_pixels_packed(cells)
    bg, fg, ac = _derive_colors(hb, style)
    return {
        "cells":      cells,
        "words":      words,
        "words_text": " ".join(words),
        "colors":     {"background": bg, "primary": fg, "accent": ac},
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
    cells  = _gen_pattern(hb)
    pixels = _gen_pixels_packed(cells)
    bg, fg, ac = _derive_colors(hb, style)
    return pixels, {"background": bg, "primary": fg, "accent": ac}
