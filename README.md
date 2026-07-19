# TaperWarp

**Version: 0.1.0-alpha**

TaperWarp mathematically transforms raster (and, in future, vector) artwork so
it appears undistorted when engraved, etched, printed, or cut onto tapered
cylindrical objects — right circular frustums such as tumblers, mugs, pint
glasses, and wine glasses. It targets makers using xTool lasers,
LightBurn-compatible lasers, Cricut cutters, Glowforge systems, CNC rotary
attachments, and similar tools.

TaperWarp is **not** an artistic warp tool. Every transformation is derived
analytically from the geometry of a right circular frustum — the exact
"unrolled cone" (developed surface) construction. The full derivation lives in
[`docs/math.md`](docs/math.md), which is the source of truth for the engine.

The application is fully offline: no network access, telemetry, analytics, or
auto-updates of any kind.

## Quick start (CLI)

```bash
pip install .
taperwarp warp art.png out.png \
    --top-diameter 84 --bottom-diameter 70 --height 210 \
    --offset 30 --art-width 180 --art-height 100 --dpi 300
```

All dimensions default to millimeters; pass `--units in` to use inches.
`--offset`, `--art-width`, and `--art-height` are distances measured **along
the surface** (what you measure with a flexible tape on the vessel).

Example: a 50 mm-grid source and its developed output for a vessel that
widens toward the base:

| Source | Developed (warped) |
|---|---|
| `examples/grid_source.png` | `examples/grid_taper_dev.png` |

## Python API

```python
from taperwarp import Frustum, ArtworkRegion, warp_image
from taperwarp.io import load_raster, save_png

frustum = Frustum(top_diameter_mm=84, bottom_diameter_mm=70, height_mm=210)
region = ArtworkRegion(top_offset_mm=30, width_mm=180, height_mm=100)
result = warp_image(load_raster("art.png"), frustum, region, dpi=300)
save_png(result.image, "out.png", dpi=result.dpi)
```

The public API — `Frustum`, `ArtworkRegion`, `warp_image` (and `warp_svg`,
planned) — is the same one used by the CLI and by the future GUI and plugins.

## Dependencies

| Dependency | Purpose | Why |
|---|---|---|
| NumPy | vectorized inverse mapping and bilinear resampling | approved core dependency |
| Pillow | PNG/JPEG decode/encode, image container | approved core dependency |
| PySide6 *(optional, `gui` extra)* | Version 1 desktop GUI | cross-platform, native look, maintained, permissive |

## Testing

```bash
pip install -e .[dev]
pytest
```

In fully offline environments without pytest, a fallback runner covering the
same suite is included: `python tests/_minirunner.py`.

## Documentation

* [`docs/math.md`](docs/math.md) — mathematical specification (source of truth)
* [`docs/architecture.md`](docs/architecture.md) — layering and module map
* [`docs/developer_guide.md`](docs/developer_guide.md) — contributing workflow
* [`PROJECT_GUIDELINES.md`](PROJECT_GUIDELINES.md) — binding engineering guidelines

## Known limitations (Version 1 scope)

Only perfect right circular frustums are supported: no curved vessel
profiles, freeform warping, perspective editing, interactive control points,
or calibration tools. See the roadmap in `PROJECT_GUIDELINES.md` §29.

---

## Release notes — 0.1.0-alpha (current version)

Initial engineering drop. The geometry engine is implemented, documented, and
tested ahead of all feature work, per project policy.

* **Geometry engine** (`taperwarp.geometry`): exact analytic frustum↔development
  mapping (`Frustum`, `ArtworkRegion`, `FrustumWarp`), forward and inverse,
  numerically stable down to tapers of 10⁻⁶ mm, exact developed bounding box,
  full input validation with meaningful errors.
* **Mathematical specification** (`docs/math.md`): complete derivation,
  coordinate definitions, stability analysis, and the single documented
  approximation (cylinder threshold).
* **Raster warping** (`taperwarp.imagewarp`): deterministic inverse-mapped
  bilinear resampling with premultiplied alpha, transparent background,
  configurable DPI, chunked processing for large outputs.
* **File I/O** (`taperwarp.io`): PNG/JPEG loading as RGBA, PNG export with DPI
  metadata, exact inch↔mm conversion confined to the I/O boundary.
* **CLI** (`taperwarp warp …`): thin frontend over the public API, mm or inch
  units.
* **Tests**: 61 tests — analytic geometry checks, seeded property-based tests
  (monotonicity, round-trip invertibility, continuity, no NaN/Inf, bounds),
  numerical-stability tests at extreme tapers, raster/IO/CLI tests, and all
  required edge cases (zero/negative/impossible dimensions).

Not yet implemented: SVG warping (`warp_svg`), GUI, regression image
fixtures, benchmarks, packaging polish. See `ChangeLog.md` for history.
