# TaperWarp

**Version: 0.1.1a1**

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
the surface** (what you measure with a flexible tape on the vessel). The
output path is overwritten if it already exists.

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
`warp_image` estimates its peak working memory before allocating anything
large and rejects over-budget jobs with an actionable error; the default
2 GiB budget can be adjusted per call via `memory_budget_bytes`.

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

Golden-image regression fixtures live in `tests/fixtures/`; regenerate them
deliberately (never automatically) with `python tests/generate_fixtures.py`
and justify any visual change in the PR.

## Documentation

* [`docs/math.md`](docs/math.md) — mathematical specification (source of truth)
* [`docs/architecture.md`](docs/architecture.md) — dependency structure and module map
* [`docs/developer_guide.md`](docs/developer_guide.md) — contributing workflow
* [`docs/icons/`](docs/icons/) — application icon assets (master SVG plus export conventions)
* [`PROJECT_GUIDELINES.md`](PROJECT_GUIDELINES.md) — binding engineering guidelines

## Known limitations (Version 1 scope)

Only perfect right circular frustums are supported: no curved vessel
profiles, freeform warping, perspective editing, interactive control points,
or calibration tools. Full-bleed artwork antialiases against transparency at
its boundary (documented edge policy, `docs/math.md` §5); a clamp-to-edge
mode is on the roadmap. See the roadmap in `PROJECT_GUIDELINES.md` §29.

---

## Release notes — 0.1.1a1 (current version)

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
validation, packaging polish. See `ChangeLog.md` for history.
