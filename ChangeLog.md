# ChangeLog

Permanent, append-only history of every TaperWarp release (newest first).
The current release's notes are duplicated in `README.md`; all older
releases live only here.

## 0.1.1a1 — 2026-07-20

Hardening pass driven by external code review. No changes to any geometry
formula; the engine's mathematics are untouched.

* **Raster memory pipeline reworked** (`taperwarp.imagewarp`): the
  destination is now allocated once as uint8 and each row chunk is
  inverse-mapped, sampled, un-premultiplied, and quantized before the next
  begins — no full-size floating-point copy of the output ever exists.
  Pixel buffers moved to float32 (geometry coordinates remain float64).
  `warp_image` now estimates peak working memory **before** allocating and
  rejects over-budget jobs (default budget 2 GiB, caller-configurable via
  `memory_budget_bytes`) with the estimate stated in the error message.
  Source images are validated for positive dimensions.
* **Version metadata fixed**: the previous release advertised
  `0.1.0-alpha` in the README while packaging said `0.1.0` (a plain
  release, and not valid PEP 440 as written). The canonical version is now
  the PEP 440 pre-release `0.1.1a1`, identical in `README.md`,
  `pyproject.toml`, and `taperwarp.__version__`.
* **Edge policy defined and tested** (`docs/math.md` §5): source samples
  outside the source raster are transparent; full-bleed artwork gets at
  most a ~1-px soft fringe at the artwork boundary, with no color shift in
  opaque regions and no inward alpha contamination. New tests inspect the
  outermost rows/columns explicitly. A clamp-to-edge mode remains on the
  roadmap.
* **Seam coverage**: new tests at exactly 100% and just-under-100% of the
  reference circumference, across both taper directions and all three
  width references, verifying the two artwork edges land on the same
  physical radial seam.
* **Golden-image regression fixtures** (`tests/fixtures/`): checkerboard
  and square-grid sources across cylinder, mild-taper, strong-taper, and
  pint (reverse-taper) vessels; exact byte comparison with a small
  documented cross-platform tolerance path. Regenerate deliberately with
  `python tests/generate_fixtures.py`.
* **CLI operational errors**: unwritable outputs (missing directory,
  permission denied, path is a directory, disk full) now raise the new
  `taperwarp.io.OutputError` and exit cleanly with code 2 instead of a
  traceback; `MemoryError` is also caught at the CLI boundary. Silent
  overwrite of an existing output is now documented and tested.
* **Architecture docs corrected**: the layering diagram in
  `docs/architecture.md` and `PROJECT_GUIDELINES.md` §7 previously showed
  geometry above image processing; in dependency terms the renderers
  consume the geometry engine, and I/O is a sibling called by frontends.
  The diagrams now match the actual (and intended) structure; the binding
  rules themselves are unchanged. Determinism is now stated as byte-exact
  per-platform.
* **Test-suite cleanup**: `approx_geometry` now plainly encodes the
  rel 1e-9 / abs 0.001 mm policy (a vestigial `ABS_TOL_MM * 0` term was
  removed). Suite grew from 61 to 86 tests.
* **Icons**: added `docs/icons/` with the master SVG placeholder icon and
  conventions for future raster/platform exports.

Still not implemented: SVG warping (`warp_svg`), GUI, physical wrap
validation, packaging polish.

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
