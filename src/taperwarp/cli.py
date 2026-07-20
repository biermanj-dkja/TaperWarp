"""Command-line interface for TaperWarp.

A thin frontend over the public API (:class:`~taperwarp.geometry.Frustum`,
:class:`~taperwarp.geometry.ArtworkRegion`, :func:`~taperwarp.imagewarp.warp_image`).
No geometry or image-processing logic lives here.

Example
-------
Warp artwork for a 20 oz tapered tumbler (all dimensions in mm)::

    taperwarp warp art.png out.png \\
        --top-diameter 84 --bottom-diameter 70 --height 210 \\
        --offset 30 --art-width 180 --art-height 100 --dpi 300

Use ``--units in`` to enter every dimension in inches instead.

Exit codes: 0 on success; 2 on any expected operational failure (invalid
geometry, unreadable input, unwritable output), reported as ``error: …`` on
stderr. The output file is silently overwritten if it exists (conventional
Unix CLI behavior; documented and tested).
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from . import __version__
from .geometry import ArtworkRegion, Frustum, GeometryError
from .imagewarp import warp_image
from .io import FileFormatError, OutputError, inches_to_mm, load_raster, save_png


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="taperwarp",
        description=(
            "Mathematically warp artwork for tapered cylindrical vessels "
            "(right circular frustums)."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"taperwarp {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    warp = sub.add_parser("warp", help="Warp a PNG/JPEG for a tapered vessel.")
    warp.add_argument("input", help="Input artwork (PNG or JPEG).")
    warp.add_argument("output", help="Output path (PNG); overwritten if present.")
    warp.add_argument(
        "--units",
        choices=("mm", "in"),
        default="mm",
        help="Unit for all dimension arguments (default: mm).",
    )
    dims = warp.add_argument_group("vessel dimensions")
    dims.add_argument("--top-diameter", type=float, required=True)
    dims.add_argument("--bottom-diameter", type=float, required=True)
    dims.add_argument("--height", type=float, required=True, help="Vertical height.")
    art = warp.add_argument_group("artwork placement (surface distances)")
    art.add_argument(
        "--offset", type=float, required=True, help="Rim to artwork top edge."
    )
    art.add_argument("--art-width", type=float, required=True)
    art.add_argument("--art-height", type=float, required=True)
    art.add_argument(
        "--width-reference",
        choices=("top", "center", "bottom"),
        default="center",
        help="Edge where artwork width is preserved exactly (default: center).",
    )
    warp.add_argument("--dpi", type=float, default=300.0, help="Output DPI.")
    warp.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging."
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    args = _build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    to_mm = inches_to_mm if args.units == "in" else (lambda x: x)
    try:
        frustum = Frustum(
            top_diameter_mm=to_mm(args.top_diameter),
            bottom_diameter_mm=to_mm(args.bottom_diameter),
            height_mm=to_mm(args.height),
        )
        region = ArtworkRegion(
            top_offset_mm=to_mm(args.offset),
            width_mm=to_mm(args.art_width),
            height_mm=to_mm(args.art_height),
            width_reference=args.width_reference,
        )
        source = load_raster(args.input)
        result = warp_image(source, frustum, region, dpi=args.dpi)
        save_png(result.image, args.output, dpi=result.dpi)
    except (GeometryError, FileFormatError, OutputError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except MemoryError:
        print(
            "error: Ran out of memory while processing; "
            "reduce the DPI or the artwork size.",
            file=sys.stderr,
        )
        return 2
    print(
        f"Wrote {args.output}: {result.image.width}x{result.image.height} px "
        f"at {result.dpi:g} DPI."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
