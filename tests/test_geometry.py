"""Tests for the geometry engine (taperwarp.geometry).

Accuracy policy (docs/math.md §8): computed values must agree with analytic
values within relative error 1e-9 or absolute error 0.001 mm, whichever is
larger. ``approx_geometry`` encodes exactly that.

Property-based tests use randomized valid frustums with a fixed seed, so
they remain fully deterministic.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from taperwarp.geometry import (
    ArtworkRegion,
    Frustum,
    FrustumWarp,
    GeometryError,
)

REL_TOL = 1e-9
ABS_TOL_MM = 1e-3


def approx_geometry(actual: float, expected: float) -> bool:
    """Accuracy criterion from docs/math.md §8: agreement within relative
    error 1e-9 or absolute error 0.001 mm, whichever is larger."""
    return abs(actual - expected) <= max(REL_TOL * abs(expected), ABS_TOL_MM)


# ---------------------------------------------------------------------------
# Frustum basics against hand-computed analytic values
# ---------------------------------------------------------------------------


class TestFrustum:
    def test_radius_is_linear_and_matches_endpoints(self) -> None:
        f = Frustum(top_diameter_mm=60.0, bottom_diameter_mm=80.0, height_mm=100.0)
        assert approx_geometry(f.radius_at(0.0), 30.0)
        assert approx_geometry(f.radius_at(100.0), 40.0)
        assert approx_geometry(f.radius_at(50.0), 35.0)
        assert approx_geometry(f.radius_at(25.0), 32.5)

    def test_circumference(self) -> None:
        f = Frustum(top_diameter_mm=60.0, bottom_diameter_mm=80.0, height_mm=100.0)
        assert approx_geometry(f.circumference_at(50.0), 2 * math.pi * 35.0)

    def test_slant_height_pythagoras(self) -> None:
        # dr = 5 mm, H = 12 mm -> L = 13 mm exactly (3-4-5 family).
        f = Frustum(top_diameter_mm=20.0, bottom_diameter_mm=30.0, height_mm=12.0)
        assert approx_geometry(f.slant_height_mm, 13.0)

    def test_cylinder_slant_equals_height(self) -> None:
        f = Frustum(top_diameter_mm=80.0, bottom_diameter_mm=80.0, height_mm=120.0)
        assert f.is_cylinder
        assert approx_geometry(f.slant_height_mm, 120.0)

    def test_taper_sign(self) -> None:
        wider_bottom = Frustum(70.0, 90.0, 100.0)
        wider_top = Frustum(90.0, 70.0, 100.0)
        assert wider_bottom.taper_rate > 0
        assert wider_top.taper_rate < 0

    def test_vertical_slant_roundtrip(self) -> None:
        f = Frustum(60.0, 90.0, 110.0)
        z = 43.21
        assert approx_geometry(f.vertical_from_slant(f.slant_from_vertical(z)), z)


# ---------------------------------------------------------------------------
# Invalid inputs must fail with meaningful GeometryError
# ---------------------------------------------------------------------------


class TestValidation:
    @pytest.mark.parametrize(
        "kwargs",
        [
            dict(top_diameter_mm=80.0, bottom_diameter_mm=70.0, height_mm=0.0),
            dict(top_diameter_mm=80.0, bottom_diameter_mm=70.0, height_mm=-5.0),
            dict(top_diameter_mm=-1.0, bottom_diameter_mm=70.0, height_mm=100.0),
            dict(top_diameter_mm=80.0, bottom_diameter_mm=-70.0, height_mm=100.0),
            dict(top_diameter_mm=0.0, bottom_diameter_mm=0.0, height_mm=100.0),
            dict(top_diameter_mm=math.nan, bottom_diameter_mm=70.0, height_mm=100.0),
            dict(top_diameter_mm=math.inf, bottom_diameter_mm=70.0, height_mm=100.0),
        ],
    )
    def test_invalid_frustum(self, kwargs: dict) -> None:
        with pytest.raises(GeometryError):
            Frustum(**kwargs)

    @pytest.mark.parametrize(
        "kwargs",
        [
            dict(top_offset_mm=0.0, width_mm=0.0, height_mm=50.0),
            dict(top_offset_mm=0.0, width_mm=-10.0, height_mm=50.0),
            dict(top_offset_mm=0.0, width_mm=100.0, height_mm=0.0),
            dict(top_offset_mm=-1.0, width_mm=100.0, height_mm=50.0),
            dict(top_offset_mm=0.0, width_mm=math.nan, height_mm=50.0),
        ],
    )
    def test_invalid_region(self, kwargs: dict) -> None:
        with pytest.raises(GeometryError):
            ArtworkRegion(**kwargs)

    def test_artwork_past_bottom(self) -> None:
        f = Frustum(80.0, 70.0, 100.0)
        r = ArtworkRegion(top_offset_mm=60.0, width_mm=100.0, height_mm=60.0)
        with pytest.raises(GeometryError):
            FrustumWarp(f, r)

    def test_artwork_wider_than_circumference(self) -> None:
        f = Frustum(80.0, 70.0, 100.0)  # circumference ~ 236 mm
        r = ArtworkRegion(top_offset_mm=0.0, width_mm=400.0, height_mm=50.0)
        with pytest.raises(GeometryError):
            FrustumWarp(f, r)

    def test_artwork_over_apex(self) -> None:
        # Full cone: top diameter 0. Artwork touching the tip is impossible.
        f = Frustum(top_diameter_mm=0.0, bottom_diameter_mm=80.0, height_mm=100.0)
        r = ArtworkRegion(top_offset_mm=0.0, width_mm=10.0, height_mm=10.0)
        with pytest.raises(GeometryError):
            FrustumWarp(f, r)

    def test_error_messages_are_meaningful(self) -> None:
        with pytest.raises(GeometryError, match="height_mm must be positive"):
            Frustum(80.0, 70.0, 0.0)
        f = Frustum(80.0, 70.0, 100.0)
        with pytest.raises(GeometryError, match="overlap"):
            FrustumWarp(f, ArtworkRegion(0.0, 500.0, 50.0))


# ---------------------------------------------------------------------------
# Mapping correctness against analytic values
# ---------------------------------------------------------------------------


def make_warp(
    dt: float = 70.0,
    db: float = 90.0,
    h: float = 120.0,
    offset: float = 10.0,
    aw: float = 150.0,
    ah: float = 80.0,
    ref: str = "center",
) -> FrustumWarp:
    return FrustumWarp(
        Frustum(dt, db, h),
        ArtworkRegion(offset, aw, ah, width_reference=ref),  # type: ignore[arg-type]
    )


class TestMapping:
    def test_top_center_maps_to_origin(self) -> None:
        w = make_warp()
        x, y = w.artwork_to_developed(w.region.width_mm / 2.0, 0.0)
        assert abs(float(x)) < 1e-12
        assert abs(float(y)) < 1e-12

    def test_center_column_is_vertical_and_length_preserving(self) -> None:
        w = make_warp()
        for v in (0.0, 13.7, 80.0):
            x, y = w.artwork_to_developed(w.region.width_mm / 2.0, v)
            assert abs(float(x)) < 1e-9
            assert approx_geometry(float(y), v)  # radial lines unroll isometrically

    def test_rows_map_to_constant_apex_distance(self) -> None:
        """Horizontal artwork lines must land on arcs (constant rho)."""
        w = make_warp()
        us = np.linspace(0.0, w.region.width_mm, 17)
        for v in (0.0, 40.0, 80.0):
            x, y = w.artwork_to_developed(us, np.full_like(us, v))
            rho = np.hypot(x, w._rho0 + w._d * y)
            assert np.max(np.abs(rho - rho[0])) < 1e-9 * rho[0]

    def test_arc_length_preserved_at_reference_height(self) -> None:
        """At the reference row, distance along the arc equals delta-u."""
        for ref, frac in (("top", 0.0), ("center", 0.5), ("bottom", 1.0)):
            w = make_warp(ref=ref)
            v = frac * w.region.height_mm
            u0, u1 = 20.0, 130.0
            x0, y0 = w.artwork_to_developed(u0, v)
            rho_ref = w._rho_ref
            # Arc length = rho_ref * delta-phi = rho_ref * (u1-u0)/rho_ref.
            phi0 = (u0 - w.region.width_mm / 2) / rho_ref
            phi1 = (u1 - w.region.width_mm / 2) / rho_ref
            arc = rho_ref * (phi1 - phi0)
            assert approx_geometry(arc, u1 - u0)
            del x0, y0

    def test_cylinder_mapping_is_identity(self) -> None:
        f = Frustum(80.0, 80.0, 150.0)
        r = ArtworkRegion(10.0, 200.0, 100.0)
        w = FrustumWarp(f, r)
        assert w.is_cylinder
        u = np.array([0.0, 37.5, 200.0])
        v = np.array([0.0, 42.0, 100.0])
        x, y = w.artwork_to_developed(u, v)
        assert np.allclose(x, u - 100.0, rtol=0, atol=1e-12)
        assert np.allclose(y, v, rtol=0, atol=1e-12)

    def test_wider_at_top_orientation(self) -> None:
        """Pint-glass taper: mapping still puts artwork top at y=0, v grows +y."""
        w = make_warp(dt=90.0, db=70.0)
        _, y_top = w.artwork_to_developed(w.region.width_mm / 2, 0.0)
        _, y_bot = w.artwork_to_developed(w.region.width_mm / 2, 80.0)
        assert abs(float(y_top)) < 1e-12
        assert approx_geometry(float(y_bot), 80.0)

    def test_handedness_preserved(self) -> None:
        """Increasing u must map to increasing x for both taper directions."""
        for dt, db in ((70.0, 90.0), (90.0, 70.0)):
            w = make_warp(dt=dt, db=db)
            x0, _ = w.artwork_to_developed(10.0, 40.0)
            x1, _ = w.artwork_to_developed(140.0, 40.0)
            assert float(x1) > float(x0)


# ---------------------------------------------------------------------------
# Property-based tests over randomized valid frustums (fixed seed)
# ---------------------------------------------------------------------------


def random_valid_cases(n: int = 200, seed: int = 20260719):
    rng = np.random.default_rng(seed)
    cases = []
    while len(cases) < n:
        dt = float(rng.uniform(0.0, 200.0))
        db = float(rng.uniform(0.5, 200.0))
        h = float(rng.uniform(1.0, 400.0))
        try:
            f = Frustum(dt, db, h)
        except GeometryError:
            continue
        length = f.slant_height_mm
        offset = float(rng.uniform(0.0, 0.5 * length))
        ah = float(rng.uniform(0.05 * length, length - offset))
        # keep radius positive across artwork
        r_lo = min(f.radius_at_slant(offset), f.radius_at_slant(offset + ah))
        if r_lo <= 0.01:
            continue
        c_ref = 2 * math.pi * f.radius_at_slant(offset + 0.5 * ah)
        aw = float(rng.uniform(0.05 * c_ref, c_ref))
        try:
            w = FrustumWarp(f, ArtworkRegion(offset, aw, ah))
        except GeometryError:
            continue
        cases.append(w)
    return cases


CASES = random_valid_cases()


class TestProperties:
    def test_radius_and_circumference_monotonic(self) -> None:
        for w in CASES:
            f = w.frustum
            z = np.linspace(0.0, f.height_mm, 64)
            r = np.asarray(f.radius_at(z))
            diffs = np.diff(r)
            sign = np.sign(f.bottom_radius_mm - f.top_radius_mm)
            assert np.all(sign * diffs >= -1e-12)
            assert np.all(np.diff(np.asarray(f.circumference_at(z))) * sign >= -1e-12)

    def test_roundtrip_inverse(self) -> None:
        rng = np.random.default_rng(7)
        for w in CASES:
            u = rng.uniform(0.0, w.region.width_mm, size=64)
            v = rng.uniform(0.0, w.region.height_mm, size=64)
            x, y = w.artwork_to_developed(u, v)
            u2, v2 = w.developed_to_artwork(x, y)
            scale = max(w.region.width_mm, w.region.height_mm)
            assert np.max(np.abs(u2 - u)) <= max(REL_TOL * scale, 1e-9)
            assert np.max(np.abs(v2 - v)) <= max(REL_TOL * scale, 1e-9)

    def test_no_nan_or_inf(self) -> None:
        for w in CASES:
            u = np.linspace(0.0, w.region.width_mm, 33)
            v = np.linspace(0.0, w.region.height_mm, 33)
            gu, gv = np.meshgrid(u, v)
            x, y = w.artwork_to_developed(gu, gv)
            assert np.all(np.isfinite(x)) and np.all(np.isfinite(y))
            u2, v2 = w.developed_to_artwork(x, y)
            assert np.all(np.isfinite(u2)) and np.all(np.isfinite(v2))

    def test_mapping_continuity(self) -> None:
        """Nearby artwork points map to nearby developed points.

        The map is 1-Lipschitz in v and (rho/rho_ref)-Lipschitz in u; a
        loose factor-4 bound over a fine grid catches any discontinuity.
        """
        for w in CASES[:50]:
            u = np.linspace(0.0, w.region.width_mm, 200)
            v = np.full_like(u, 0.3 * w.region.height_mm)
            x, y = w.artwork_to_developed(u, v)
            step = u[1] - u[0]
            d = np.hypot(np.diff(x), np.diff(y))
            assert np.all(d <= 4.0 * step + 1e-9)

    def test_coordinates_within_bounds(self) -> None:
        for w in CASES[:50]:
            b = w.developed_bounds()
            u = np.linspace(0.0, w.region.width_mm, 41)
            v = np.linspace(0.0, w.region.height_mm, 41)
            gu, gv = np.meshgrid(u, v)
            x, y = w.artwork_to_developed(gu, gv)
            eps = 1e-9 * max(1.0, b.width, b.height)
            assert np.min(x) >= b.x_min - eps and np.max(x) <= b.x_max + eps
            assert np.min(y) >= b.y_min - eps and np.max(y) <= b.y_max + eps


# ---------------------------------------------------------------------------
# Numerical stability at extreme tapers
# ---------------------------------------------------------------------------


class TestNumericalStability:
    def test_tiny_taper_roundtrip(self) -> None:
        """Taper just above the cylinder threshold must still be stable."""
        f = Frustum(80.0, 80.0 + 4e-6, 150.0)  # dr = 2e-6 mm > epsilon
        assert not f.is_cylinder
        w = FrustumWarp(f, ArtworkRegion(5.0, 200.0, 100.0))
        u = np.array([0.0, 50.0, 100.0, 199.0])
        v = np.array([0.0, 25.0, 75.0, 100.0])
        x, y = w.artwork_to_developed(u, v)
        u2, v2 = w.developed_to_artwork(x, y)
        assert np.max(np.abs(u2 - u)) < 1e-6
        assert np.max(np.abs(v2 - v)) < 1e-6

    def test_tiny_taper_close_to_cylinder_result(self) -> None:
        f_taper = Frustum(80.0, 80.0 + 4e-6, 150.0)
        f_cyl = Frustum(80.0, 80.0, 150.0)
        region = ArtworkRegion(5.0, 200.0, 100.0)
        wt = FrustumWarp(f_taper, region)
        wc = FrustumWarp(f_cyl, region)
        u, v = 37.0, 61.0
        xt, yt = wt.artwork_to_developed(u, v)
        xc, yc = wc.artwork_to_developed(u, v)
        assert abs(float(xt) - float(xc)) < ABS_TOL_MM
        assert abs(float(yt) - float(yc)) < ABS_TOL_MM

    def test_strong_taper(self) -> None:
        """Near-conical martini-glass style taper."""
        f = Frustum(120.0, 10.0, 80.0)
        w = FrustumWarp(f, ArtworkRegion(2.0, 60.0, 50.0))
        u = np.linspace(0, 60.0, 25)
        v = np.linspace(0, 50.0, 25)
        gu, gv = np.meshgrid(u, v)
        x, y = w.artwork_to_developed(gu, gv)
        u2, v2 = w.developed_to_artwork(x, y)
        assert np.max(np.abs(u2 - gu)) < 1e-8
        assert np.max(np.abs(v2 - gv)) < 1e-8
