# TaperWarp Project Guidelines & Development Instructions

**Version:** 1.0
**Status:** Initial Engineering Specification

These are binding instructions for anyone (or any AI assistant) contributing to TaperWarp. Follow them exactly. Where a decision is not covered here, prefer the simplest, most mathematically defensible option and document the reasoning.

---

## 1. Project Goal

Build TaperWarp: an open-source application that mathematically transforms raster and vector artwork so it appears undistorted when engraved, etched, printed, or cut onto tapered cylindrical objects (right circular frustums) — tumblers, mugs, pint glasses, wine glasses, and similar vessels.

Target equipment includes xTool lasers, LightBurn-compatible lasers, Cricut cutters, Glowforge systems, CNC rotary attachments, and similar fabrication tools.

**TaperWarp is not an artistic image warp tool.** Every transformation must be derived from the geometry of a right circular frustum — never from heuristic or manually-tuned image distortion.

---

## 2. Design Philosophy

Prioritize, in no particular ranking but all non-negotiable:

- Mathematical correctness
- Simplicity
- Readability
- Maintainability
- Cross-platform compatibility
- Security
- Deterministic behavior
- Minimal external dependencies
- Open-source friendliness

Write code an intermediate Python developer can understand without additional context.

---

## 3. Guiding Principles

- The geometry engine is the heart of the project. Build it first, and make it correct before anything else.
- Implement, test, document, and validate the mathematics independently of any user interface.
- No GUI code may influence mathematical calculations.
- The application must remain fully functional with no Internet access.

---

## 4. Version 1 — Primary Requirements

Version 1 must:

- Load PNG
- Load JPEG
- Load SVG
- Preserve transparency
- Warp artwork using mathematically correct frustum projection
- Export PNG
- Export SVG where practical
- Support arbitrary image sizes
- Support millimeter input
- Support inch input
- Allow configurable DPI
- Produce deterministic output

### Scope

Version 1 supports **only perfect right circular frustums**.

The user shall specify:

- Top diameter
- Bottom diameter
- Height
- Artwork top offset
- Artwork width
- Artwork height

Version 1 explicitly **excludes**:

- Freeform warp tools
- Perspective editing
- Interactive control points
- Arbitrary mesh editing
- Curved vessel profiles
- Calibration tools

---

## 5. Mathematical Requirements

- Preserve the physical location of every point on the frustum surface.
- Implement an analytical mapping between flat artwork coordinates and frustum surface coordinates, based strictly on right-circular-frustum geometry.
- The mapping must be continuous, deterministic, numerically stable, and invertible over its valid domain.
- Never use heuristic image warping.

### Coordinate Systems

**Image Space**
- Origin: upper-left corner
- +X: right
- +Y: down

**Physical Space**
- Internal units: millimeters
- Origin: top edge of the artwork region
- Vertical coordinate: `z`
- Angular coordinate: `θ`
- Radius: `r(z)`
- Circumference: `C(z)`

All internal calculations use millimeters. Convert between inches and millimeters only at input and output boundaries.

---

## 6. Geometry Engine

The geometry engine must be completely independent of any GUI. It shall:

- Accept physical dimensions
- Compute radius at any vertical position
- Compute circumference at any vertical position
- Generate an exact mapping from a flat rectangle onto a frustum
- Avoid numerical approximation where practical
- Be implemented using pure functions where practical
- Be documented with mathematical derivations and references

### Mathematical Documentation

Include `docs/math.md`, containing:

- Mathematical derivation of the projection
- Coordinate definitions
- Assumptions
- Formula derivations
- References
- Numerical considerations
- Known approximations (if any)

Keep the mathematical specification independent from the implementation — it should read as a standalone reference.

---

## 7. Architecture

Use a layered architecture:

```
GUI
↓
Application Logic
↓
Geometry Engine
↓
Image Processing
↓
File I/O
```

- The geometry engine has no GUI dependencies.
- The image processing layer knows nothing about GUI implementation.

### Public API

Expose a stable, frontend-independent API from the geometry engine, e.g.:

```
Frustum(...)
ArtworkRegion(...)
warp_image(...)
warp_svg(...)
```

The GUI, CLI, and future plugins must all use this same public API.

---

## 8. Language & Dependencies

**Language:** Python 3.12+

**Preferred runtime dependencies:**
- Pillow
- NumPy

**Optional (only when justified):**
- svgwrite
- svgpathtools
- SciPy

Do not use OpenCV unless it provides a clearly documented advantage.

Every dependency must:
- Be actively maintained
- Use a permissive license
- Have a clear technical justification
- Be documented in the README

Prefer the standard library whenever practical.

---

## 9. GUI

Use **PySide6** for Version 1 (cross-platform, native appearance, actively maintained, permissively licensed).

- Keep the GUI thin.
- Business logic must not live in the GUI.

---

## 10. Plugin Architecture

The geometry engine must eventually support:

- Standalone GUI
- Command-line interface
- GIMP plugin
- Future Inkscape extension

The geometry engine must never know which frontend is calling it.

---

## 11. Image Processing

- Default raster interpolation: bilinear.
- Future versions may add nearest-neighbor and bicubic.
- Interpolation behavior must be deterministic.

---

## 12. SVG Support

Preserve whenever practical:
- Paths
- Lines
- Polygons
- Circles
- Rectangles

Unsupported SVG objects may be converted to paths. Embedded raster images may be processed as raster artwork.

---

## 13. File Formats

**Inputs:** PNG (RGBA), JPEG (RGB), SVG 1.1
**Outputs:** PNG, SVG (where practical)

---

## 14. Code Quality

Follow:
- PEP 8
- Type hints
- Dataclasses
- Meaningful names
- Small functions
- Pure functions where practical
- Comprehensive docstrings

Avoid:
- Global mutable state
- Hidden side effects
- Unnecessary abstraction

---

## 15. Security

The project must:
- Operate completely offline
- Perform no network communication
- Include no telemetry, analytics, or tracking
- Include no API keys, credentials, or secrets
- Include no auto-update functionality

The project must not:
- Execute arbitrary user code
- Execute external binaries
- Spawn shell commands except during documented testing

Never write files outside user-selected locations.

---

## 16. Dependency Policy

Every dependency must satisfy:
- Active maintenance
- Broad adoption
- Permissive licensing
- Acceptable security history
- Clear technical need

Avoid dependencies for trivial functionality. Document the purpose of every dependency.

---

## 17. Reproducibility

- Pin development dependencies.
- Use compatible version ranges for runtime dependencies.
- Builds must not download additional code during testing.
- CI must test against supported dependency versions.

---

## 18. Testing

Automated testing is mandatory. Required coverage:
- Geometry tests
- Image transform tests
- SVG tests
- Regression tests
- Edge-case tests

Sanity tests must include: cylinder, very small taper, large taper, tiny images, large images, transparent PNG, non-square images, high-DPI exports, invalid dimensions, negative dimensions, zero height, zero diameter, impossible geometry.

Produce meaningful error messages for all failure cases.

### Property-Based Testing

Generate randomized valid frustums and verify:
- Radius monotonicity
- Circumference monotonicity
- Mapping continuity
- No NaN values
- No infinite values
- Coordinates remain within valid bounds

### Regression Fixtures

Include reference fixtures: checkerboard, square grid, cylinder, mild taper, strong taper. Compare both numerical and visual output against these.

---

## 19. Numerical Accuracy

- Avoid cumulative floating-point drift.
- Document every approximation.
- Geometry calculations must agree with analytical solutions within relative error 1×10⁻⁹ **or** absolute error 0.001 mm, whichever is larger.

---

## 20. Performance

The application must:
- Handle 6000×6000 images
- Avoid unnecessary memory copies
- Process efficiently
- Stream processing where practical

Include benchmark scripts for 1000×1000, 3000×3000, and 6000×6000 images.

---

## 21. Documentation

Maintain: README, ChangeLog, Installation Guide, Developer Guide, Architecture Guide, Mathematical Specification, Example Images, Screenshots, Roadmap, FAQ, Known Limitations.

---

## 22. Repository Layout

```
taperwarp/
│
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
│
├── docs/
│   ├── architecture.md
│   ├── math.md
│   └── developer_guide.md
│
├── examples/
├── tests/
│
├── src/
│   └── taperwarp/
│       ├── geometry.py
│       ├── imagewarp.py
│       ├── svgwarp.py
│       ├── io.py
│       ├── cli.py
│       ├── gui/
│       └── plugins/
│
├── pyproject.toml
├── .editorconfig
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE
├── README.md
├── ChangeLog.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
└── PROJECT_GUIDELINES.md
```

---

## 23. Continuous Integration

GitHub Actions must:
- Run tests on Linux, Windows, and macOS
- Run Ruff, Black, and mypy
- Require all checks to pass before merge

Configuration for Ruff, Black, and mypy resides in `pyproject.toml`.

---

## 24. Logging

Use Python's standard `logging` module. Do not use `print()` except for CLI output. Default logging level: `WARNING`.

---

## 25. Git Practices

Use:
- Conventional Commits
- Semantic Versioning (see Section 26)
- Pull Request template
- Bug Report template
- Feature Request template
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `CONTRIBUTING.md`

---

## 26. Versioning Rules

### 26.1 Naming Scheme

TaperWarp uses **Semantic Versioning 2.0.0**: `MAJOR.MINOR.PATCH` (e.g. `1.2.3`).

- **MAJOR** — increment for breaking changes to the public API (`geometry.py` interfaces, CLI flags, file formats) or for changes that alter output for existing valid inputs.
- **MINOR** — increment for backward-compatible new functionality (e.g. a new supported SVG element, a new interpolation mode).
- **PATCH** — increment for backward-compatible bug fixes, performance improvements, or documentation-only changes that don't alter behavior.

Pre-1.0 and pre-release builds may append a suffix, e.g. `0.1.0-alpha`, `1.0.0-rc.1`. Suffixes follow SemVer pre-release rules (lower precedence than the equivalent release version).

Tag releases in git as `vMAJOR.MINOR.PATCH` (e.g. `v1.2.3`).

### 26.2 Where the Version Lives

- **The canonical version number of the project is recorded in `README.md`.** This is the single source of truth for "what version is this." Every release updates the version string at the top of the README.
- `pyproject.toml` and any `__version__` string in code must match the README's declared version — never let them drift.

### 26.3 Release Notes: README vs. ChangeLog

- **`ChangeLog.md` is the permanent, append-only history of every release**, oldest to newest (or newest-first, whichever convention the project settles on — just be consistent). Every version that has ever shipped keeps its entry here, indefinitely.
- **`README.md` shows release notes for the current version only.** When a new version ships:
  1. Write the new version's release notes into `ChangeLog.md` (this is the permanent record).
  2. Write the *same* release notes for that current version into `README.md`, replacing whatever the previous version's notes were.
  3. The previous version's notes are removed from the README — they now live only in `ChangeLog.md`.
- In short: **the current version's notes are duplicated in both files; every older version's notes exist only in `ChangeLog.md`.** The README never accumulates historical entries — it always reflects just the current release.

### 26.4 Release Checklist

When cutting a release:
1. Confirm all tests pass and CI is green on Linux, Windows, and macOS.
2. Decide MAJOR/MINOR/PATCH per Section 26.1.
3. Update the version string in `README.md`, `pyproject.toml`, and code.
4. Add the new version's entry to `ChangeLog.md`.
5. Replace the "Current Version" notes section of `README.md` with this same entry.
6. Tag the release `vMAJOR.MINOR.PATCH`.

---

## 27. What Not To Do

Do **not**:
- Embed AI-generated code without understanding it.
- Add unnecessary frameworks.
- Download code at runtime.
- Execute arbitrary user scripts.
- Require cloud services.
- Require proprietary software.
- Implement unrelated features before the geometry engine is mathematically correct.

---

## 28. Known Assumptions (Version 1)

- Perfect right circular frustums
- Constant wall thickness is irrelevant
- No vessel curvature
- No manufacturing tolerances

Decorative or curved vessels are out of scope for Version 1.

---

## 29. Future Roadmap (Out of Scope for V1)

- GIMP plugin
- Inkscape extension
- Live 3D preview
- Vessel profile library
- Calibration wizard
- Multiple diameter measurements
- Batch processing
- Text layout tools
- Native installers
- GPU acceleration (only if profiling demonstrates need)

---

## 30. Definition of Done (Version 1)

Version 1 is complete when:
- All analytical geometry tests pass.
- Cylinder mode produces mathematically correct output.
- Regression fixtures match expected results within documented tolerances.
- CI passes on Linux, Windows, and macOS.
- Ruff, Black, and mypy complete without errors.
- Documentation is complete.
- The application operates fully offline.
- No known high-severity defects remain open.
