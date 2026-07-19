"""Analytic geometry engine for TaperWarp.

Implements the exact mapping between a flat artwork rectangle and the
developed (unrolled) lateral surface of a right circular frustum, as derived
in ``docs/math.md``. That document is the source of truth for every formula
in this module.

This module depends only on the standard library and NumPy. It has no GUI,
image-processing, or file-I/O dependencies, and every public function is
pure and deterministic.

All lengths are millimeters; all angles are radians.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "CYLINDER_EPSILON_MM",
    "ArtworkRegion",
    "DevelopedBounds",
    "Frustum",
    "FrustumWarp",
    "GeometryError",
    "WidthReference",
]

#: Taper thresholds below which the frustum is treated as an exact cylinder.
#: See docs/math.md §4 — this is the engine's only documented approximation;
#: its geometric effect is far below the 0.001 mm accuracy budget.
CYLINDER_EPSILON_MM: float = 1e-6

WidthReference = Literal["top", "center", "bottom"]

_REFERENCE_FRACTION: dict[str, float] = {"top": 0.0, "center": 0.5, "bottom": 1.0}


class GeometryError(ValueError):
    """Raised when frustum or artwork parameters are geometrically invalid."""


def _require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise GeometryError(f"{name} must be a finite number, got {value!r}.")


@dataclass(frozen=True)
class Frustum:
    """A right circular frustum (tapered vessel), defined by user inputs.

    Parameters
    ----------
    top_diameter_mm:
        Diameter at the rim (top), in millimeters. Must be ``>= 0``.
    bottom_diameter_mm:
        Diameter at the base (bottom), in millimeters. Must be ``>= 0``.
    height_mm:
        Vertical height of the vessel along its axis, in millimeters.
        Must be ``> 0``.

    Notes
    -----
    ``z`` denotes vertical distance measured downward from the rim
    (``0 <= z <= height_mm``); ``t`` denotes distance measured from the rim
    along the lateral surface (slant distance, ``0 <= t <= slant_height_mm``).
    """

    top_diameter_mm: float
    bottom_diameter_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        for name in ("top_diameter_mm", "bottom_diameter_mm", "height_mm"):
            _require_finite(name, getattr(self, name))
        if self.height_mm <= 0.0:
            raise GeometryError(
                f"height_mm must be positive, got {self.height_mm} mm. "
                "A vessel with zero or negative height has no surface to map."
            )
        if self.top_diameter_mm < 0.0 or self.bottom_diameter_mm < 0.0:
            raise GeometryError(
                "Diameters must be non-negative "
                f"(got top={self.top_diameter_mm} mm, "
                f"bottom={self.bottom_diameter_mm} mm)."
            )
        if self.top_diameter_mm == 0.0 and self.bottom_diameter_mm == 0.0:
            raise GeometryError(
                "At least one diameter must be positive; both are zero."
            )

    # -- basic derived quantities -------------------------------------------

    @property
    def top_radius_mm(self) -> float:
        """Radius at the rim, in millimeters."""
        return self.top_diameter_mm / 2.0

    @property
    def bottom_radius_mm(self) -> float:
        """Radius at the base, in millimeters."""
        return self.bottom_diameter_mm / 2.0

    @property
    def slant_height_mm(self) -> float:
        """Length of the lateral surface from rim to base (math.md §2.2)."""
        return math.hypot(self.height_mm, self.bottom_radius_mm - self.top_radius_mm)

    @property
    def taper_rate(self) -> float:
        """``c = (r_b - r_t) / L`` — signed taper per unit slant distance.

        Positive when the vessel is wider at the bottom, negative when wider
        at the top, zero for a cylinder. ``|c| = sin(alpha)`` with ``alpha``
        the half-angle of the underlying cone.
        """
        return (self.bottom_radius_mm - self.top_radius_mm) / self.slant_height_mm

    @property
    def is_cylinder(self) -> bool:
        """True when the taper is below :data:`CYLINDER_EPSILON_MM`."""
        return (
            abs(self.bottom_radius_mm - self.top_radius_mm) < CYLINDER_EPSILON_MM
        )

    # -- radius / circumference ---------------------------------------------

    def radius_at(self, z_mm: float | NDArray[np.float64]) -> float | NDArray[np.float64]:
        """Radius (mm) at vertical distance ``z_mm`` below the rim.

        ``r(z) = r_t + (r_b - r_t) * z / H`` (math.md §2.2); linear and
        therefore monotonic in ``z``. Accepts scalars or NumPy arrays.
        """
        rt, rb = self.top_radius_mm, self.bottom_radius_mm
        if isinstance(z_mm, np.ndarray):
            return rt + (rb - rt) * (z_mm.astype(np.float64) / self.height_mm)
        return rt + (rb - rt) * (z_mm / self.height_mm)

    def circumference_at(
        self, z_mm: float | NDArray[np.float64]
    ) -> float | NDArray[np.float64]:
        """Circumference (mm) at vertical distance ``z_mm`` below the rim."""
        return 2.0 * math.pi * self.radius_at(z_mm)

    def radius_at_slant(self, t_mm: float) -> float:
        """Radius (mm) at slant distance ``t_mm`` from the rim (math.md §2.2)."""
        return self.top_radius_mm + self.taper_rate * t_mm

    def slant_from_vertical(self, z_mm: float) -> float:
        """Convert vertical distance below the rim to slant distance."""
        return z_mm * self.slant_height_mm / self.height_mm

    def vertical_from_slant(self, t_mm: float) -> float:
        """Convert slant distance from the rim to vertical distance."""
        return t_mm * self.height_mm / self.slant_height_mm


@dataclass(frozen=True)
class ArtworkRegion:
    """Placement of a flat artwork rectangle on the frustum surface.

    All values are surface (slant) distances in millimeters — what a maker
    measures with a flexible tape on the physical vessel (math.md §2.3).

    Parameters
    ----------
    top_offset_mm:
        Distance along the surface from the rim to the artwork's top edge.
    width_mm:
        Artwork width — the arc length it spans at the reference height.
    height_mm:
        Artwork height along the surface.
    width_reference:
        Where widths are preserved exactly: ``"top"``, ``"center"``
        (default), or ``"bottom"`` edge of the artwork (math.md §3.3).
    """

    top_offset_mm: float
    width_mm: float
    height_mm: float
    width_reference: WidthReference = "center"

    def __post_init__(self) -> None:
        for name in ("top_offset_mm", "width_mm", "height_mm"):
            _require_finite(name, getattr(self, name))
        if self.width_mm <= 0.0:
            raise GeometryError(f"width_mm must be positive, got {self.width_mm} mm.")
        if self.height_mm <= 0.0:
            raise GeometryError(f"height_mm must be positive, got {self.height_mm} mm.")
        if self.top_offset_mm < 0.0:
            raise GeometryError(
                f"top_offset_mm must be >= 0, got {self.top_offset_mm} mm."
            )
        if self.width_reference not in _REFERENCE_FRACTION:
            raise GeometryError(
                f"width_reference must be 'top', 'center', or 'bottom', "
                f"got {self.width_reference!r}."
            )

    @property
    def reference_fraction(self) -> float:
        """Fraction ``f`` of the artwork height where width is exact."""
        return _REFERENCE_FRACTION[self.width_reference]


@dataclass(frozen=True)
class DevelopedBounds:
    """Axis-aligned bounding box of the developed artwork, local frame (mm)."""

    x_min: float
    x_max: float
    y_min: float
    y_max: float

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min


@dataclass(frozen=True)
class FrustumWarp:
    """The exact mapping between artwork coordinates and the developed plane.

    Coordinates follow ``docs/math.md`` §3: artwork space ``(u, v)`` with
    ``u ∈ [0, W]`` rightward and ``v ∈ [0, h]`` downward; development space
    ``(x, y)`` in millimeters with origin at the image of the artwork's
    top-center point, +x right, +y down.

    Instances are immutable; all methods are pure, deterministic, and accept
    either scalars or NumPy arrays (applied elementwise).
    """

    frustum: Frustum
    region: ArtworkRegion

    # Derived, precomputed constants (math.md §3.2). Populated in __post_init__.
    _is_cylinder: bool = field(init=False, repr=False)
    _d: float = field(init=False, repr=False)
    _rho0: float = field(init=False, repr=False)
    _rho_ref: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        fr, rg = self.frustum, self.region
        length = fr.slant_height_mm
        if rg.top_offset_mm + rg.height_mm > length + 1e-12:
            raise GeometryError(
                "Artwork extends past the bottom of the vessel: "
                f"top_offset ({rg.top_offset_mm} mm) + height ({rg.height_mm} mm) "
                f"exceeds the slant height ({length:.6f} mm)."
            )

        r_top_art = fr.radius_at_slant(rg.top_offset_mm)
        r_bot_art = fr.radius_at_slant(rg.top_offset_mm + rg.height_mm)
        if min(r_top_art, r_bot_art) <= 0.0:
            raise GeometryError(
                "The artwork band reaches the apex of the cone "
                "(radius is zero or negative somewhere under the artwork). "
                "Reduce the artwork height or offset."
            )

        object.__setattr__(self, "_is_cylinder", fr.is_cylinder)
        if self._is_cylinder:
            object.__setattr__(self, "_d", 0.0)
            object.__setattr__(self, "_rho0", math.inf)
            object.__setattr__(self, "_rho_ref", math.inf)
            circumference_ref = fr.circumference_at(0.0)
        else:
            c = fr.taper_rate
            d = math.copysign(1.0, c)
            rho0 = r_top_art / abs(c)
            t_ref = rg.top_offset_mm + rg.reference_fraction * rg.height_mm
            rho_ref = fr.radius_at_slant(t_ref) / abs(c)
            object.__setattr__(self, "_d", d)
            object.__setattr__(self, "_rho0", rho0)
            object.__setattr__(self, "_rho_ref", rho_ref)
            circumference_ref = 2.0 * math.pi * fr.radius_at_slant(t_ref)

        if rg.width_mm > circumference_ref * (1.0 + 1e-12):
            raise GeometryError(
                f"Artwork width ({rg.width_mm} mm) exceeds the vessel "
                f"circumference at the reference height "
                f"({circumference_ref:.6f} mm); the artwork would overlap "
                "itself around the vessel."
            )

    # -- mappings -----------------------------------------------------------

    @property
    def is_cylinder(self) -> bool:
        """True when the exact cylinder (identity) mapping is in effect."""
        return self._is_cylinder

    def artwork_to_developed(
        self,
        u: float | NDArray[np.float64],
        v: float | NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Forward mapping (math.md §3.4): artwork ``(u, v)`` → developed ``(x, y)``."""
        u_arr = np.asarray(u, dtype=np.float64)
        v_arr = np.asarray(v, dtype=np.float64)
        w = self.region.width_mm
        if self._is_cylinder:
            return u_arr - w / 2.0, v_arr + np.zeros_like(u_arr)
        phi = (u_arr - w / 2.0) / self._rho_ref
        rho = self._rho0 + self._d * v_arr
        x = rho * np.sin(phi)
        y = self._d * (rho * np.cos(phi) - self._rho0)
        return x, y

    def developed_to_artwork(
        self,
        x: float | NDArray[np.float64],
        y: float | NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Inverse mapping (math.md §3.5): developed ``(x, y)`` → artwork ``(u, v)``.

        Uses the cancellation-free form of ``rho - rho0`` so the mapping stays
        numerically stable for arbitrarily small tapers.
        """
        x_arr = np.asarray(x, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64)
        w = self.region.width_mm
        if self._is_cylinder:
            return x_arr + w / 2.0, y_arr + np.zeros_like(x_arr)
        big_y = self._rho0 + self._d * y_arr
        rho = np.hypot(x_arr, big_y)
        # rho - rho0 without catastrophic cancellation (math.md §3.5):
        rho_minus_rho0 = (
            x_arr * x_arr + 2.0 * self._rho0 * self._d * y_arr + y_arr * y_arr
        ) / (rho + self._rho0)
        v = self._d * rho_minus_rho0
        u = np.arctan2(x_arr, big_y) * self._rho_ref + w / 2.0
        return u, v

    # -- bounds -------------------------------------------------------------

    def developed_bounds(self) -> DevelopedBounds:
        """Exact bounding box of the developed artwork (math.md §5).

        Extrema over the region boundary occur only at the corners, at the
        arc midpoints (``phi = 0``) and, when the half-angle reaches π/2, at
        ``phi = ±π/2`` on each bounding arc — a finite candidate set.
        """
        w, h = self.region.width_mm, self.region.height_mm
        if self._is_cylinder:
            return DevelopedBounds(-w / 2.0, w / 2.0, 0.0, h)

        phi_m = w / (2.0 * self._rho_ref)
        candidate_u = [0.0, w / 2.0, w]
        if phi_m >= math.pi / 2.0:
            # u values where phi = ±π/2
            for phi in (-math.pi / 2.0, math.pi / 2.0):
                candidate_u.append(phi * self._rho_ref + w / 2.0)
        us: list[float] = []
        vs: list[float] = []
        for uu in candidate_u:
            for vv in (0.0, h):
                us.append(uu)
                vs.append(vv)
        x, y = self.artwork_to_developed(np.array(us), np.array(vs))
        return DevelopedBounds(
            float(np.min(x)), float(np.max(x)), float(np.min(y)), float(np.max(y))
        )
