#!/usr/bin/env python3
"""Generate per-icon .py files and a btc_icons.py aggregator from SVG or PNG sources.

Each icon gets its own file at <symbol_lib_dir>/icons/<lower_snake>.py so that
mpy-cross compiles each file independently (solves the OOM on large bitmaps).

Design benefits
---------------
- 42×42 icons fit: each file is ~6 KB of source, not 1.4 MB
- Custom icons (e.g. smartcard.py) live in icons/ and are never overwritten
- Build-time tree-shaking becomes possible: grep for BTC_ICONS.FOO usage,
  only copy used icons/ modules into the firmware image
- SVG input: auto-detected, rendered via Inkscape to a fresh sibling dir

Input auto-detection
--------------------
    SVG dir  → renders all SVGs at --size pixels into a fresh sibling dir
               (e.g. .../svg/filled at size 42 → .../png-42/filled)
               then processes those PNGs.
    PNG dir  → processes PNGs directly (no rendering step).

Usage
-----
    # From SVGs (Inkscape required)
    python3 generate_btc_icons.py <svg_or_png_dir> <symbol_lib_dir> [--size N]

    # Only regenerate the aggregator (btc_icons.py) from existing icons/
    python3 generate_btc_icons.py --aggregate-only <symbol_lib_dir>

Arguments
---------
    source_dir       Directory containing source SVG or PNG files
    symbol_lib_dir   Directory that contains icon.py; icons/ will be created here
    --size N         Target icon size in pixels (default: 42)
    --aggregate-only Skip icon conversion; only rebuild btc_icons.py

Example
-------
    python3 tools/symbol_lib/generate_btc_icons.py \\
        data/Bitcoin-Icons-0.1.10/svg/filled \\
        scenarios/MockUI/src/MockUI/basic/symbol_lib \\
        --size 42
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def render_svgs(svg_dir: Path, size: int) -> Path:
    """Render all SVGs in svg_dir to a fresh sibling PNG directory.

    Output dir: <svg_dir.parent.parent>/png-{size}/<svg_dir.name>
    e.g. .../svg/filled  →  .../png-42/filled

    The directory is always wiped clean before rendering so there are never
    stale PNGs from a previous run at a different size.
    Requires Inkscape on PATH.
    """
    png_dir = svg_dir.parent.parent / f"png-{size}" / svg_dir.name

    if png_dir.exists():
        shutil.rmtree(png_dir)
    png_dir.mkdir(parents=True)

    inkscape = shutil.which("inkscape")
    if inkscape is None:
        print("ERROR: inkscape not found on PATH. Install inkscape to render SVGs.",
              file=sys.stderr)
        sys.exit(1)

    svgs = sorted(svg_dir.glob("*.svg"))
    if not svgs:
        print(f"ERROR: No .svg files found in {svg_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Rendering {len(svgs)} SVGs at {size}\u00d7{size}px  ({inkscape})")
    print(f"  from: {svg_dir}")
    print(f"  into: {png_dir}")
    for i, svg in enumerate(svgs, 1):
        out = png_dir / (svg.stem + ".png")
        subprocess.run(
            [
                inkscape,
                "--export-type=png",
                f"--export-width={size}",
                f"--export-height={size}",
                f"--export-filename={out}",
                str(svg),
            ],
            check=True,
            capture_output=True,  # suppress inkscape's verbose stderr
        )
        print(f"\r  [{i}/{len(svgs)}] {svg.stem}", end="", flush=True)
    print()  # newline after progress line

    return png_dir


def stem_to_name(stem: str) -> str:
    """Convert a file stem to a BTC_ICONS attribute name.

    Examples:
        qr-code      -> QR_CODE
        address_book -> ADDRESS_BOOK  (underscores already OK)
        bitcoin      -> BITCOIN
    """
    return stem.upper().replace("-", "_")


def png_to_alpha_bytes(png_path: Path, size: int) -> bytes:
    """Open a PNG, resize to size×size with LANCZOS, return raw A8 alpha bytes."""
    img = Image.open(png_path).convert("RGBA")
    if img.size != (size, size):
        img = img.resize((size, size), Image.LANCZOS)
    _, _, _, a = img.split()
    return bytes(a.tobytes())


def format_icon_file(name: str, size: int, data: bytes) -> str:
    """Return the full content of an individual icon .py file.

    Uses adjacent bytes LITERALS (b'\\x00...') rather than a bytes([...])
    constructor call.  In MicroPython frozen bytecode, bytes literals are stored
    as constants in flash (ROM), so pattern data costs zero heap at runtime.
    bytes([...]) would allocate size*size bytes on the heap per icon at import
    time — 126 icons × 1764 bytes = 217 KB for 42×42, causing an OOM crash.

    Adjacent string literal concatenation (b'...' b'...') is resolved by the
    compiler, not at runtime, so each row stays within mpy-cross limits.
    """
    rows = []
    for row_start in range(0, len(data), size):
        row = data[row_start:row_start + size]
        rows.append("        b\"" + "".join(f"\\x{v:02x}" for v in row) + "\"")
    body = "\n".join(rows)
    return (
        f'"""AUTO-GENERATED — do not edit. '
        f"Regenerate with tools/symbol_lib/generate_btc_icons.py\"\"\"\n"
        f"from ..icon import Icon\n"
        f"\n"
        f"# bytes literals — stored in flash (ROM) in frozen bytecode, zero heap\n"
        f"{name} = Icon(\n"
        f"    pattern=(\n"
        f"{body}\n"
        f"    ),\n"
        f"    width={size},\n"
        f"    height={size},\n"
        f")\n"
    )


def build_aggregator(icons_dir: Path, symbol_lib_dir: Path, size: int, count: int) -> str:
    """Scan icons/ and return the content of btc_icons.py."""
    icon_files = sorted(
        p for p in icons_dir.glob("*.py") if p.name != "__init__.py"
    )
    if not icon_files:
        print("WARNING: no .py files found in icons/ — btc_icons.py will be empty",
              file=sys.stderr)

    imports = []
    attrs = []
    for f in icon_files:
        name = stem_to_name(f.stem)
        imports.append(f"from .icons.{f.stem} import {name}")
        attrs.append(f"    {name} = {name}")

    imports_block = "\n".join(imports)
    attrs_block = "\n".join(attrs)
    n_icons = len(icon_files)

    return (
        f'"""Bitcoin icon library aggregator — {n_icons} icons at {size}×{size} px.\n'
        f"\n"
        f"AUTO-GENERATED — do not edit directly.\n"
        f"Regenerate with:\n"
        f"    python3 tools/symbol_lib/generate_btc_icons.py \\\\\n"
        f"        <png_dir> \\\\\n"
        f"        scenarios/MockUI/src/MockUI/basic/symbol_lib \\\\\n"
        f"        --size {size}\n"
        f"\n"
        f"Custom icons in icons/ (files without a matching PNG) are preserved\n"
        f"between runs; add them to icons/ and rerun --aggregate-only.\n"
        f'"""\n'
        f"\n"
        f"{imports_block}\n"
        f"\n"
        f"\n"
        f"class BTC_ICONS:\n"
        f"    \"\"\"\n"
        f"    Library of Bitcoin-themed icons ({n_icons} total, {size}×{size} px).\n"
        f"\n"
        f"    Icons default to white; pass a color to tint them:\n"
        f"        BTC_ICONS.WALLET(lv.color_hex(0xFF0000))  # red\n"
        f"        BTC_ICONS.QR_CODE(GREEN_HEX)\n"
        f"        BTC_ICONS.BITCOIN                         # white (default)\n"
        f"    \"\"\"\n"
        f"{attrs_block}\n"
    )


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def generate_icons(png_dir: Path, symbol_lib_dir: Path, size: int) -> int:
    """Write one .py file per PNG into <symbol_lib_dir>/icons/. Returns count."""
    png_files = sorted(png_dir.glob("*.png"))
    if not png_files:
        print(f"ERROR: No PNG files found in {png_dir}", file=sys.stderr)
        sys.exit(1)

    icons_dir = symbol_lib_dir / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    init_file = icons_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# icons package — individual icon modules\n")

    count = 0
    for png_path in png_files:
        name = stem_to_name(png_path.stem)
        stem_lower = png_path.stem.replace("-", "_").lower()
        out_path = icons_dir / f"{stem_lower}.py"
        data = png_to_alpha_bytes(png_path, size)
        out_path.write_text(format_icon_file(name, size, data))
        count += 1

    print(f"Wrote {count} icon files ({size}×{size} px) → {icons_dir}/")
    return count


def generate_aggregator(symbol_lib_dir: Path, size: int, count: int) -> None:
    """Regenerate btc_icons.py from all files currently in icons/."""
    icons_dir = symbol_lib_dir / "icons"
    aggregator_path = symbol_lib_dir / "btc_icons.py"
    content = build_aggregator(icons_dir, symbol_lib_dir, size, count)
    aggregator_path.write_text(content)
    n = len([p for p in icons_dir.glob("*.py") if p.name != "__init__.py"])
    print(f"Wrote aggregator ({n} icons) → {aggregator_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate per-icon .py files and btc_icons.py aggregator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "source_dir",
        type=Path,
        nargs="?",
        help="Directory containing source SVG or PNG files (omit with --aggregate-only)",
    )
    parser.add_argument(
        "symbol_lib_dir",
        type=Path,
        help="symbol_lib directory (contains icon.py; icons/ created here)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=42,
        metavar="N",
        help="Target icon size in pixels (default: 42)",
    )
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Skip PNG conversion; only rebuild btc_icons.py from existing icons/",
    )
    args = parser.parse_args()

    if not args.symbol_lib_dir.is_dir():
        print(f"ERROR: symbol_lib_dir not found: {args.symbol_lib_dir}", file=sys.stderr)
        sys.exit(1)

    if args.aggregate_only:
        generate_aggregator(args.symbol_lib_dir, args.size, 0)
    else:
        if args.source_dir is None:
            parser.error("source_dir is required unless --aggregate-only is set")
        if not args.source_dir.is_dir():
            print(f"ERROR: source_dir not found: {args.source_dir}", file=sys.stderr)
            sys.exit(1)

        # Auto-detect SVG vs PNG input
        svgs = list(args.source_dir.glob("*.svg"))
        pngs = list(args.source_dir.glob("*.png"))
        if svgs and not pngs:
            png_dir = render_svgs(args.source_dir, args.size)
        elif pngs:
            if svgs:
                print(
                    f"WARNING: {args.source_dir} contains both SVGs and PNGs "
                    "— using PNGs directly",
                    file=sys.stderr,
                )
            png_dir = args.source_dir
        else:
            print(
                f"ERROR: No SVG or PNG files found in {args.source_dir}",
                file=sys.stderr,
            )
            sys.exit(1)

        count = generate_icons(png_dir, args.symbol_lib_dir, args.size)
        generate_aggregator(args.symbol_lib_dir, args.size, count)


if __name__ == "__main__":
    main()
