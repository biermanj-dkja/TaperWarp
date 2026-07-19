# ChangeLog

Permanent, append-only history of every TaperWarp release (newest first).
The current release's notes are duplicated in `README.md`; all older
releases live only here.

## 0.1.0-alpha — 2026-07-19

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
fixtures, benchmarks, packaging polish.
