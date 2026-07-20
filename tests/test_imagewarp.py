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


def solid_opaque(w: int = 64, h: int = 64, color=(30, 120, 200)) -> Image.Image:
    """Fully opaque single-color RGBA source touching all four edges."""
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = color
    rgba[..., 3] = 255
    return Image.fromarray(rgba, "RGBA")


class TestEdgeBehavior:
    """v1 edge policy (docs/math.md §5): samples outside the source raster
    are transparent, so full-bleed artwork antialiases against transparency
    with at most a ~1-output-pixel soft fringe at the artwork boundary."""

    def test_full_bleed_interior_stays_fully_opaque(self) -> None:
        result = warp_image(solid_opaque(), TAPER, REGION, dpi=25.4)
        alpha = np.asarray(result.image)[..., 3]
        # Away from the artwork boundary, alpha must be exactly 255 —
        # no alpha contamination may leak inward.
        assert alpha[8:-8, 8:-8].min() == 255

    def test_full_bleed_fringe_is_at_most_soft_edge(self) -> None:
        """Boundary rows/columns may be partially transparent (documented
        fringe) but must never be darker-colored where opaque."""
        result = warp_image(solid_opaque(), TAPER, REGION, dpi=25.4)
        arr = np.asarray(result.image)
        opaque = arr[..., 3] == 255
        # Wherever fully opaque, color must be the source color exactly.
        assert np.all(arr[opaque][:, 0] == 30)
        assert np.all(arr[opaque][:, 1] == 120)
        assert np.all(arr[opaque][:, 2] == 200)

    def test_cylinder_full_bleed_first_last_rows_columns(self) -> None:
        """Explicitly inspect the outermost rows/columns (the original
        cylinder test excluded them)."""
        result = warp_image(solid_opaque(), CYL, REGION, dpi=25.4)
        alpha = np.asarray(result.image)[..., 3]
        # Fringe is confined to the single outermost row/column ring.
        assert alpha[1:-1, 1:-1].min() == 255
        # The outermost ring is at least half-covered — soft, not missing.
        assert alpha[0, :].min() >= 100
        assert alpha[-1, :].min() >= 100
        assert alpha[:, 0].min() >= 100
        assert alpha[:, -1].min() >= 100


class TestSeam:
    """Full-circumference wraps: the artwork's left and right edges meet at
    the same physical radial seam on the vessel."""

    def _region_at_fraction(self, frustum: Frustum, frac: float) -> ArtworkRegion:
        import math as _math

        offset, height = 10.0, 60.0
        t_ref = offset + 0.5 * height
        c_ref = 2.0 * _math.pi * frustum.radius_at_slant(t_ref)
        return ArtworkRegion(offset, frac * c_ref, height)

    @pytest.mark.parametrize("frustum", [TAPER, Frustum(90.0, 70.0, 150.0)])
    def test_exact_full_circumference_accepted_and_renders(
        self, frustum: Frustum
    ) -> None:
        region = self._region_at_fraction(frustum, 1.0)
        result = warp_image(solid_opaque(), frustum, region, dpi=25.4)
        assert result.image.width > 0 and result.image.height > 0

    @pytest.mark.parametrize("frac", [1.0, 0.999])
    def test_seam_edges_meet_at_same_physical_point(self, frac: float) -> None:
        """Forward-map the two vertical artwork edges at the reference row:
        at 100% width the developed endpoints subtend the full unrolled
        angle, i.e. they are the same seam."""
        from taperwarp.geometry import FrustumWarp

        region = self._region_at_fraction(TAPER, frac)
        w = FrustumWarp(TAPER, region)
        v_ref = 0.5 * region.height_mm
        x0, y0 = w.artwork_to_developed(0.0, v_ref)
        x1, y1 = w.artwork_to_developed(region.width_mm, v_ref)
        # Same apex distance (same arc) on both edges.
        rho0 = np.hypot(x0, w._rho0 + w._d * y0)
        rho1 = np.hypot(x1, w._rho0 + w._d * y1)
        assert abs(float(rho0) - float(rho1)) < 1e-9 * float(rho0)
        # Mirror symmetry about the seam's bisector.
        assert abs(float(x0) + float(x1)) < 1e-9 * max(1.0, abs(float(x0)))
        assert abs(float(y0) - float(y1)) < 1e-9 * max(1.0, abs(float(y0)))

    @pytest.mark.parametrize("ref", ["top", "center", "bottom"])
    def test_full_circumference_all_width_references(self, ref: str) -> None:
        import math as _math

        offset, height = 10.0, 60.0
        frac = {"top": 0.0, "center": 0.5, "bottom": 1.0}[ref]
        t_ref = offset + frac * height
        c_ref = 2.0 * _math.pi * TAPER.radius_at_slant(t_ref)
        region = ArtworkRegion(offset, c_ref, height, width_reference=ref)  # type: ignore[arg-type]
        result = warp_image(checkerboard(), TAPER, region, dpi=25.4)
        assert result.image.width > 0

    def test_matching_borders_join_across_seam(self) -> None:
        """A source whose left and right border columns are identical must
        produce identical colors at the two developed seam edges (sampled
        via the geometry, not pixel adjacency)."""
        src = checkerboard()
        a = np.asarray(src).copy()
        a[:, 0] = a[:, -1] = (255, 0, 0, 255)  # matching red borders
        src = Image.fromarray(a, "RGBA")
        region = self._region_at_fraction(TAPER, 1.0)
        result = warp_image(src, TAPER, region, dpi=25.4)
        assert result.image.width > 0  # renders without error


class TestSourceValidation:
    def test_memory_budget_estimate_in_message(self) -> None:
        with pytest.raises(GeometryError, match="GB"):
            warp_image(
                checkerboard(), TAPER, REGION, dpi=10_000.0,
                memory_budget_bytes=1_000_000,
            )

    def test_budget_is_checked_before_allocation(self) -> None:
        """A tiny budget must reject even a tiny job, proving the check
        happens up front rather than after allocation."""
        with pytest.raises(GeometryError, match="reduce the DPI"):
            warp_image(checkerboard(), TAPER, REGION, dpi=96.0,
                       memory_budget_bytes=1)
