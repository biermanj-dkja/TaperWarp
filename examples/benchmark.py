"""Benchmark TaperWarp raster warping at the required sizes.

Runs the standard 1000x1000, 3000x3000, and 6000x6000 benchmarks from the
project guidelines. Deterministic input (seeded checkerboard), timing only.

Usage::

    python examples/benchmark.py [--dpi 300]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from taperwarp import ArtworkRegion, Frustum, warp_image  # noqa: E402

SIZES = (1000, 3000, 6000)


def make_source(n: int) -> Image.Image:
    yy, xx = np.mgrid[0:n, 0:n]
    board = (((xx // 64) + (yy // 64)) % 2 * 255).astype(np.uint8)
    rgba = np.stack([board, board, board, np.full_like(board, 255)], axis=-1)
    return Image.fromarray(rgba, "RGBA")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dpi", type=float, default=300.0)
    args = parser.parse_args()

    frustum = Frustum(top_diameter_mm=70.0, bottom_diameter_mm=95.0, height_mm=180.0)
    region = ArtworkRegion(top_offset_mm=10.0, width_mm=180.0, height_mm=110.0)

    print(f"{'size':>10} {'seconds':>10} {'out px':>16}")
    for n in SIZES:
        src = make_source(n)
        t0 = time.perf_counter()
        result = warp_image(src, frustum, region, dpi=args.dpi)
        dt = time.perf_counter() - t0
        print(f"{n}x{n:>5} {dt:>10.2f} {result.image.width}x{result.image.height:>7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
