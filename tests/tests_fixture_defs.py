"""Shared source/vessel definitions for golden-image fixtures.

Imported by both ``generate_fixtures.py`` and ``test_golden.py`` so the
generator and the test can never drift apart.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from taperwarp import ArtworkRegion, Frustum

REGION = ArtworkRegion(top_offset_mm=10.0, width_mm=120.0, height_mm=60.0)
DPI = 25.4  # 1 px/mm keeps fixtures small and exact

VESSELS: dict[str, Frustum] = {
    "cylinder": Frustum(80.0, 80.0, 150.0),
    "mild_taper": Frustum(70.0, 90.0, 150.0),
    "strong_taper": Frustum(120.0, 40.0, 100.0),
    "pint": Frustum(90.0, 70.0, 150.0),
}


def checkerboard(w: int = 64, h: int = 64, cell: int = 8) -> Image.Image:
    yy, xx = np.mgrid[0:h, 0:w]
    board = (((xx // cell) + (yy // cell)) % 2 * 255).astype(np.uint8)
    rgba = np.stack([board, board, board, np.full_like(board, 255)], axis=-1)
    return Image.fromarray(rgba, "RGBA")


def square_grid(w: int = 64, h: int = 64, cell: int = 8) -> Image.Image:
    """White field with black grid lines every ``cell`` pixels."""
    rgba = np.full((h, w, 4), 255, dtype=np.uint8)
    rgba[::cell, :, :3] = 0
    rgba[:, ::cell, :3] = 0
    rgba[-1, :, :3] = 0
    rgba[:, -1, :3] = 0
    return Image.fromarray(rgba, "RGBA")


SOURCES = {"checker": checkerboard, "grid": square_grid}
