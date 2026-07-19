"""Tests for the raster warping layer (taperwarp.imagewarp)."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from taperwarp.geometry import ArtworkRegion, Frustum, GeometryError
from taperwarp.imagewarp import warp_image


def checkerboard(w: int = 64, h: int = 64, cell: int = 8) -> Image.Image:
    yy, xx = np.mgrid[0:h, 0:w]
    board = (((xx // cell) + (yy // cell)) % 2 * 255).astype(np.uint8)
    rgba = np.stack([board, board, board, np.full_like(board, 255)], axis=-1)
    return Image.fromarray(rgba, "RGBA")


CYL = Frustum(80.0, 80.0, 150.0)
TAPER = Frustum(70.0, 90.0, 150.0)
REGION = ArtworkRegion(top_offset_mm=10.0, width_mm=120.0, height_mm=60.0)


class TestCylinder:
    def test_cylinder_output_is_undistorted(self) -> None:
        """On a cylinder the developed artwork is the artwork itself."""
        src = checkerboard()
        result = warp_image(src, CYL, REGION, dpi=25.4)  # 1 px per mm
        out = np.asarray(result.image)
        assert out.shape[:2] == (60, 120)
        # Compare against a plain resize of the source to the same grid.
        ref = np.asarray(src.resize((120, 60), Image.Resampling.BILINEAR).convert("RGBA"))
        # Interiors should match closely (edge pixels differ by sampling).
        diff = np.abs(out[2:-2, 2:-2, :3].astype(int) - ref[2:-2, 2:-2, :3].astype(int))
        assert diff.mean() < 8.0

    def test_cylinder_fully_opaque(self) -> None:
        result = warp_image(checkerboard(), CYL, REGION, dpi=25.4)
        alpha = np.asarray(result.image)[..., 3]
        assert alpha[5:-5, 5:-5].min() == 255


class TestTaper:
    def test_output_larger_than_rectangle_and_has_transparent_corners(self) -> None:
        result = warp_image(checkerboard(), TAPER, REGION, dpi=25.4)
        arr = np.asarray(result.image)
        # Developed arcs bow, so the bounding box is taller than the artwork.
        assert arr.shape[0] > 60
        # Corners lie outside the annular sector -> transparent.
        assert arr[0, 0, 3] == 0
        assert arr[0, -1, 3] == 0

    def test_transparency_preserved(self) -> None:
        """A source with transparent regions keeps them transparent."""
        src = checkerboard()
        a = np.asarray(src).copy()
        a[:, :32, 3] = 0  # left half transparent
        src = Image.fromarray(a, "RGBA")
        result = warp_image(src, TAPER, REGION, dpi=25.4)
        out = np.asarray(result.image)
        # Some interior pixels must be transparent, some opaque.
        interior = out[10:-10, 10:-10, 3]
        assert interior.min() == 0 and interior.max() == 255

    def test_deterministic(self) -> None:
        src = checkerboard()
        r1 = warp_image(src, TAPER, REGION, dpi=96.0)
        r2 = warp_image(src, TAPER, REGION, dpi=96.0)
        assert np.array_equal(np.asarray(r1.image), np.asarray(r2.image))

    def test_wider_at_top_taper(self) -> None:
        f = Frustum(90.0, 70.0, 150.0)
        result = warp_image(checkerboard(), f, REGION, dpi=25.4)
        assert np.asarray(result.image).shape[0] > 60

    def test_non_square_source(self) -> None:
        src = checkerboard(200, 40)
        result = warp_image(src, TAPER, REGION, dpi=50.0)
        assert result.image.width > 0 and result.image.height > 0

    def test_tiny_image(self) -> None:
        src = checkerboard(2, 2, 1)
        result = warp_image(src, TAPER, REGION, dpi=25.4)
        assert result.image.width > 0

    def test_high_dpi_export(self) -> None:
        result = warp_image(checkerboard(), TAPER, REGION, dpi=600.0)
        assert result.dpi == 600.0
        assert result.image.width > 2500  # ~120 mm * 600/25.4


class TestErrors:
    @pytest.mark.parametrize("dpi", [0.0, -300.0, float("nan"), float("inf")])
    def test_invalid_dpi(self, dpi: float) -> None:
        with pytest.raises(GeometryError):
            warp_image(checkerboard(), TAPER, REGION, dpi=dpi)

    def test_absurd_output_size_rejected(self) -> None:
        with pytest.raises(GeometryError, match="reduce the DPI"):
            warp_image(checkerboard(), TAPER, REGION, dpi=1_000_000.0)
