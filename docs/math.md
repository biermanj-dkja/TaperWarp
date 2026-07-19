# TaperWarp Mathematical Specification

**Status:** Version 1 reference. This document is the source of truth for the
geometry engine. If the code and this document disagree, the code is wrong.

This specification is self-contained and independent of the implementation.

---

## 1. Problem statement

A flat rectangular piece of artwork of physical width `W` and height `h`
(millimeters) is to be applied to the lateral surface of a **right circular
frustum** (a cone with its tip cut off parallel to its base) — a tumbler, mug,
or similar vessel. The artwork's top edge must follow a circle of constant
height on the vessel (parallel to the rim), and vertical lines in the artwork
must remain "vertical" on the vessel (i.e., lie along lines of steepest
descent on the surface).

Because the lateral surface of a cone is *developable* (it can be unrolled
onto a plane without stretching), there exists an exact, analytical mapping
between the flat artwork rectangle and the region it occupies on the unrolled
(developed) surface. TaperWarp computes artwork in that developed shape so
that, once the printed/engraved result is wrapped onto the vessel, the artwork
appears as designed.

No heuristic warping is involved anywhere; every formula below follows from
frustum geometry.

---

## 2. Definitions and coordinate systems

### 2.1 Frustum parameters (user input)

| Symbol | Meaning | Constraint |
|---|---|---|
| `D_t` | top diameter (rim) | `D_t ≥ 0` |
| `D_b` | bottom diameter (base) | `D_b ≥ 0` |
| `H`   | vertical height of the vessel (along the axis) | `H > 0` |

Radii: `r_t = D_t / 2`, `r_b = D_b / 2`. At least one radius must be
positive, and any point covered by artwork must have strictly positive radius
(Section 7).

All lengths are millimeters. Inch↔mm conversion happens only at I/O
boundaries (1 in = 25.4 mm, exactly).

### 2.2 Derived frustum quantities

**Slant height** (length of the lateral surface measured along the surface
from rim to base):

```
L = sqrt( H² + (r_b − r_t)² )
```

**Taper rate along the slant** (dimensionless):

```
c = (r_b − r_t) / L          (may be negative; |c| = sin α,
                              where α is the half-angle of the cone)
```

`c > 0`: vessel is wider at the bottom. `c < 0`: wider at the top
(e.g., a pint glass). `c = 0`: a cylinder.

**Radius as a function of position.** Two equivalent parameterizations are
used:

*Vertical parameterization* — `z` measured downward from the rim along the
axis, `z ∈ [0, H]`:

```
r(z) = r_t + (r_b − r_t) · z / H
C(z) = 2π · r(z)
```

Both `r(z)` and `C(z)` are linear (hence monotonic) in `z`.

*Slant parameterization* — `t` measured from the rim along the lateral
surface, `t ∈ [0, L]`:

```
r_s(t) = r_t + c · t
```

The two are related by `t = z · L / H` (and `z = t · H / L`).

### 2.3 Artwork region (user input)

The artwork region is specified **on the surface**, i.e. all of the following
are distances measured along the lateral surface (slant distances), because
that is what a maker measures with a flexible tape on the physical vessel:

| Symbol | Meaning | Constraint |
|---|---|---|
| `t₀` | offset from the rim to the artwork's top edge | `t₀ ≥ 0` |
| `W`  | artwork width (arc length at the reference height, §3.3) | `0 < W ≤ C_ref` |
| `h`  | artwork height along the surface | `h > 0`, `t₀ + h ≤ L` |

### 2.4 Image space

Source artwork pixels use the standard raster convention: origin at the
upper-left corner, +X right, +Y down. The source image of `w_px × h_px`
pixels is linearly identified with the physical rectangle
`(u, v) ∈ [0, W] × [0, h]`:

```
u = (x_px + ½) · W / w_px        v = (y_px + ½) · h / h_px
```

(pixel centers at half-integer coordinates).

### 2.5 Developed (unrolled) surface

Cut the cone along one line of steepest descent and unroll it. Every point of
the lateral surface at slant distance `s` from the **apex** of the (extended)
cone lands at distance `ρ = s` from the apex in the plane. A full
circumference at radius `r` (arc length `2πr`) unrolls to an arc of length
`2πr` at radius `ρ = r / |c|`, subtending the angle

```
φ_full = 2πr / ρ = 2π|c|
```

Hence a physical azimuth `θ` (radians around the vessel axis) unrolls to the
development angle

```
φ = θ · |c|                                            (angle compression)
```

The apex distance of the circle at slant position `t` is

```
ρ(t) = r_s(t) / |c|
```

Note `ρ(t) = ρ(0) + d·t` with `d = sign(c) = ±1`: moving down the surface by
1 mm moves exactly 1 mm along a radial line of the development (the
development is an isometry of the surface).

---

## 3. The artwork → development mapping

### 3.1 Requirements encoded

1. Rows of constant `v` (horizontal lines of the artwork) map to arcs of
   constant `ρ` — circles of constant height on the vessel. ✔ rim-parallel.
2. Columns of constant `u` (vertical lines) map to radial lines of the
   development — lines of steepest descent on the vessel. ✔ "vertical".
3. Distances along `v` are preserved exactly (radial lines are unrolled
   without stretch).
4. Distances along `u` are preserved exactly at one chosen **reference
   height** (§3.3) and scale as `ρ/ρ_ref` elsewhere. This residual scaling is
   *not* an approximation or a heuristic — it is a geometric necessity: a
   rectangle cannot cover an annular sector with both families of lines
   preserved, because concentric arcs of different radii subtending the same
   angle have different lengths. The mapping below is the unique analytic
   mapping satisfying (1)–(3) with a linear angular coordinate.

### 3.2 Local development frame

Define a Cartesian frame in the development plane with origin at the image of
the artwork's **top-center** point, +x in the direction of increasing `u`,
+y in the direction of increasing `v` (down the vessel surface). Let

```
ρ₀     = ρ(t₀)          apex distance of the artwork's top edge
d      = sign(c)        +1 wider-at-bottom, −1 wider-at-top
ρ_ref  = ρ(t₀ + f·h)    f ∈ [0,1]: width reference fraction (§3.3)
```

### 3.3 Width reference

`f = 0` preserves widths exactly along the artwork's top edge, `f = 1` along
the bottom edge, `f = ½` (the default) at mid-height, which minimizes the
maximum width error over the artwork. `C_ref = 2π ρ_ref |c|` is the vessel
circumference at the reference height; the constraint `W ≤ C_ref` prevents
overlap.

### 3.4 Forward mapping

For artwork coordinates `(u, v) ∈ [0, W] × [0, h]`:

```
φ   = (u − W/2) / ρ_ref                    development angle, φ ∈ [−φ_m, φ_m]
ρ   = ρ₀ + d·v                             apex distance
x   = ρ · sin φ
y   = d · (ρ · cos φ − ρ₀)
```

with half-angle `φ_m = W / (2 ρ_ref)`.

The factor `d` in `y` orients the output so that the artwork's top edge is at
the top (+y down), regardless of taper direction. For `d = +1` the arcs bow
upward (frown ∩-shape as commonly seen on tumbler wraps); for `d = −1` they
bow downward (∪).

### 3.5 Inverse mapping

Given development coordinates `(x, y)` in the local frame:

```
Y   = ρ₀ + d·y                     ( = ρ cos φ )
ρ   = sqrt(x² + Y²)
φ   = atan2(x, Y)
v   = d · (ρ − ρ₀)
u   = φ · ρ_ref + W/2
```

The point lies inside the artwork iff `0 ≤ v ≤ h` and `0 ≤ u ≤ W`.

**Numerically stable form.** For very small tapers, `ρ₀` is enormous
(`ρ₀ → ∞` as `c → 0`) while `ρ − ρ₀` is small; computing it by subtraction
cancels catastrophically. Instead use the algebraically identical

```
ρ − ρ₀ = (x² + 2 ρ₀ d y + y²) / (ρ + ρ₀)
```

which involves no cancellation of large terms (each term in the numerator is
of the order of the artwork size times `ρ₀` at most, and the division
restores full relative precision).

### 3.6 Invertibility and continuity

On the valid domain (`ρ > 0`, `|φ| < π`) the forward map is a composition of
smooth bijections (linear maps and polar coordinates), hence continuous,
smooth, and invertible. `W ≤ C_ref ⇒ φ_m = π|c|·(W/C_ref) ≤ π|c| < π`, so
the artwork never self-overlaps in the development.

---

## 4. Cylinder special case

When `r_t = r_b` the surface is a cylinder; its development is an exact
rectangle and the mapping degenerates to the identity:

```
x = u − W/2        y = v
```

The general formulas approach this as `c → 0` (the arcs flatten), but they
are ill-conditioned there, so the implementation switches to the exact
cylinder mapping when `|r_b − r_t| < ε_cyl`. With `ε_cyl = 10⁻⁶ mm`, the
maximum geometric discrepancy introduced by the switch is the sagitta of the
widest possible arc: `≈ ρ₀ φ_m² / 2 ≤ W²·|c| / (8 r) `, which for
`|Δr| = 10⁻⁶ mm` is far below the 0.001 mm accuracy budget for any physically
meaningful vessel. **This threshold is the only approximation in the
engine**, and it is documented here per the accuracy policy.

---

## 5. Raster resampling

The developed output raster is produced by **inverse mapping**: for every
output pixel center, compute `(u, v)` via §3.5, then sample the source image
bilinearly. Pixels mapping outside `[0, W] × [0, h]` are fully transparent.

To avoid dark fringes at transparent edges, sampling is performed on
**alpha-premultiplied** RGBA values and un-premultiplied afterward. Bilinear
interpolation on a fixed pixel grid with float64 arithmetic is deterministic.

The output bounding box is computed **exactly** from the geometry: the
extrema of `x` and `y` over the region boundary occur only at the four
corners, at the arc midpoints (`φ = 0`), and — when `φ_m ≥ π/2` — at
`φ = ±π/2` on each bounding arc. Evaluating the forward map at this finite
candidate set gives the exact bounds.

---

## 6. Units, DPI

Internal computation: millimeters and radians, float64. DPI (`p` pixels per
inch) converts to pixel pitch `25.4 / p` mm at the raster boundary only.

---

## 7. Validity conditions (rejected with errors)

* `H > 0`; `D_t ≥ 0`; `D_b ≥ 0`; all finite.
* `h > 0`, `W > 0`, `t₀ ≥ 0`, `t₀ + h ≤ L`.
* Radius strictly positive over the whole artwork band:
  `min(r_s(t₀), r_s(t₀+h)) > 0` (artwork may not wrap over a cone apex).
* `W ≤ C_ref` (artwork may not overlap itself around the vessel).

---

## 8. Accuracy statement

All formulas above are closed-form. Agreement with analytical values is
required within relative error `1×10⁻⁹` or absolute error `0.001 mm`,
whichever is larger; the only intentional deviation is the cylinder threshold
of §4, which is bounded well inside that budget.

---

## 9. References

* Standard development (unrolling) of a right circular cone: any analytic
  geometry text, e.g. G. A. Korn & T. M. Korn, *Mathematical Handbook for
  Scientists and Engineers*, §3 (surfaces of revolution, developable
  surfaces).
* Sheet-metal cone layout ("flat pattern of a truncated cone") — the same
  construction used industrially for rolled-cone fabrication.
