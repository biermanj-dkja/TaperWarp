# TaperWarp Project Specification & Development Guidelines

**Version:** 1.0
**Status:** Initial Engineering Specification

---

# Project Goal

TaperWarp is an open-source application that mathematically transforms raster and vector artwork so that it appears undistorted when engraved, etched, printed, or cut onto tapered cylindrical objects (right circular frustums), including tumblers, mugs, pint glasses, wine glasses, and similar vessels.

The software is intended for makers using equipment such as xTool lasers, LightBurn-compatible lasers, Cricut cutters, Glowforge systems, CNC rotary attachments, and similar fabrication tools.

TaperWarp is **not** an artistic image warp tool.

All transformations shall be based on the geometry of a right circular frustum rather than heuristic or manually adjusted image distortion.

---

# Design Philosophy

The project shall prioritize:

* Mathematical correctness
* Simplicity
* Readability
* Maintainability
* Cross-platform compatibility
* Security
* Deterministic behavior
* Minimal external dependencies
* Open-source friendliness

The codebase should be understandable by intermediate Python developers.

---

# Guiding Principles

The geometry engine is the heart of the project.

The mathematics shall be implemented, tested, documented, and validated independently of any user interface.

No GUI code shall influence mathematical calculations.

The project shall remain fully functional without Internet access.

---

# Primary Requirements

Version 1 shall:

* Load PNG
* Load JPEG
* Load SVG
* Preserve transparency
* Warp artwork using mathematically correct frustum projection
* Export PNG
* Export SVG where practical
* Support arbitrary image sizes
* Support millimeter input
* Support inch input
* Allow configurable DPI
* Produce deterministic output

---

# Version 1 Scope

Version 1 supports only **perfect right circular frustums**.

The user shall specify:

* Top diameter
* Bottom diameter
* Height
* Artwork top offset
* Artwork width
* Artwork height

Version 1 explicitly excludes:

* Freeform warp tools
* Perspective editing
* Interactive control points
* Arbitrary mesh editing
* Curved vessel profiles
* Calibration tools

---

# Mathematical Requirements

The transformation shall preserve the physical location of every point on the frustum surface.

The geometry engine shall implement an analytical mapping between:

* Flat artwork coordinates
* Frustum surface coordinates

The implementation shall be based on the geometry of a right circular frustum.

The mapping shall be:

* Continuous
* Deterministic
* Numerically stable
* Invertible over the valid domain

No heuristic image warping shall be used.

---

# Coordinate Systems

## Image Space

Origin:

Upper-left corner

Positive X:

Right

Positive Y:

Down

---

## Physical Space

Internal units:

Millimeters

Origin:

Top edge of the artwork region

Vertical coordinate:

z

Angular coordinate:

θ

Radius:

r(z)

Circumference:

C(z)

All internal calculations shall use millimeters.

Conversions between inches and millimeters shall occur only during input and output.

---

# Geometry Engine

The geometry engine shall be completely independent of any GUI.

It shall:

* Accept physical dimensions
* Compute radius at any vertical position
* Compute circumference at any vertical position
* Generate an exact mapping from a flat rectangle onto a frustum
* Avoid numerical approximation where practical
* Be implemented using pure functions where practical
* Be documented with mathematical derivations and references

---

# Mathematical Documentation

The repository shall include:

```
docs/math.md
```

This document shall contain:

* Mathematical derivation of the projection
* Coordinate definitions
* Assumptions
* Formula derivations
* References
* Numerical considerations
* Known approximations (if any)

The mathematical specification shall remain independent from the implementation.

---

# Architecture

Use a layered architecture.

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

The geometry engine shall have no GUI dependencies.

The image processing layer shall know nothing about GUI implementation.

---

# Public API

The geometry engine shall expose a stable API independent of any frontend.

Typical interfaces should resemble:

```
Frustum(...)

ArtworkRegion(...)

warp_image(...)

warp_svg(...)
```

The GUI, CLI, and future plugins shall use the same public API.

---

# Language

Python 3.12+

---

# Preferred Dependencies

Runtime dependencies shall remain intentionally small.

Preferred:

* Pillow
* NumPy

Optional (only when justified):

* svgwrite
* svgpathtools
* SciPy

OpenCV shall not be used unless it provides a clearly documented advantage.

Every dependency shall:

* Be actively maintained
* Use a permissive license
* Have a clear technical justification
* Be documented in the README

Prefer Python standard-library modules whenever practical.

---

# GUI

Version 1 shall use:

PySide6

Reasons:

* Cross-platform
* Native appearance
* Active maintenance
* Permissive licensing

The GUI shall remain thin.

Business logic shall not reside in the GUI.

---

# Plugin Architecture

The geometry engine shall eventually support:

* Standalone GUI
* Command-line interface
* GIMP plugin
* Future Inkscape extension

The geometry engine shall not know which frontend is calling it.

---

# Image Processing

Raster interpolation shall default to:

* Bilinear interpolation

Future versions may support:

* Nearest-neighbor
* Bicubic

Interpolation behavior shall be deterministic.

---

# SVG Support

Version 1 should preserve whenever practical:

* Paths
* Lines
* Polygons
* Circles
* Rectangles

Unsupported SVG objects may be converted to paths.

Embedded raster images may be processed as raster artwork.

---

# File Formats

Supported inputs:

* PNG (RGBA)
* JPEG (RGB)
* SVG 1.1

Supported outputs:

* PNG
* SVG where practical

---

# Code Quality

Follow:

* PEP 8
* Type hints
* Dataclasses
* Meaningful names
* Small functions
* Pure functions where practical
* Comprehensive docstrings

Avoid:

* Global mutable state
* Hidden side effects
* Unnecessary abstraction

---

# Security

The project shall:

* Operate completely offline
* Perform no network communication
* Include no telemetry
* Include no analytics
* Include no tracking
* Include no API keys
* Include no credentials
* Include no secrets
* Include no auto-update functionality

The project shall not:

* Execute arbitrary user code
* Execute external binaries
* Spawn shell commands except during documented testing

The application shall never write files outside user-selected locations.

---

# Dependency Policy

Minimize third-party dependencies.

Every dependency shall satisfy:

* Active maintenance
* Broad adoption
* Permissive licensing
* Acceptable security history
* Clear technical need

Avoid dependencies for trivial functionality.

Document the purpose of every dependency.

---

# Reproducibility

Development dependencies shall be pinned.

Runtime dependencies should use compatible version ranges.

Builds shall not download additional code during testing.

CI shall test against supported dependency versions.

---

# Testing

Automated testing is mandatory.

Required:

* Geometry tests
* Image transform tests
* SVG tests
* Regression tests
* Edge-case tests

Sanity tests shall include:

* Cylinder
* Very small taper
* Large taper
* Tiny images
* Large images
* Transparent PNG
* Non-square images
* High DPI exports
* Invalid dimensions
* Negative dimensions
* Zero height
* Zero diameter
* Impossible geometry

The application shall produce meaningful error messages.

---

# Property-Based Testing

Generate randomized valid frustums.

Verify:

* Radius monotonicity
* Circumference monotonicity
* Mapping continuity
* No NaN values
* No infinite values
* Coordinates remain within valid bounds

---

# Regression Fixtures

Include reference fixtures including:

* Checkerboard
* Square grid
* Cylinder
* Mild taper
* Strong taper

Regression tests shall compare numerical output and visual output.

---

# Numerical Accuracy

Avoid cumulative floating-point drift.

Document every approximation.

Geometry calculations should agree with analytical solutions within:

* Relative error: 1×10⁻⁹

or

* Absolute error: 0.001 mm

whichever is larger.

---

# Performance

The application shall:

* Handle 6000×6000 images
* Avoid unnecessary memory copies
* Process efficiently
* Stream processing where practical

Include benchmark scripts for:

* 1000×1000
* 3000×3000
* 6000×6000

---

# Documentation

The repository shall include:

* README
* ChangeLog
* Installation Guide
* Developer Guide
* Architecture Guide
* Mathematical Specification
* Example Images
* Screenshots
* Roadmap
* FAQ
* Known Limitations
* Icons

---

# Repository Layout

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
│   ├── developer_guide.md
│   └──icons/
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

# Continuous Integration

GitHub Actions shall:

* Run tests on Linux
* Run tests on Windows
* Run tests on macOS
* Run Ruff
* Run Black
* Run mypy
* Require all checks to pass before merge

---

# Formatting and Static Analysis

Use:

* Ruff
* Black
* mypy

Configuration shall reside in:

```
pyproject.toml
```

---

# Logging

Use Python's standard logging module.

Do not use `print()` except for CLI output.

Default logging level shall be:

WARNING

---

# Git Practices

Use:

* Conventional Commits
* Semantic Versioning
* Pull Request template
* Bug Report template
* Feature Request template
* CODE_OF_CONDUCT.md
* SECURITY.md
* CONTRIBUTING.md

---

# What Not To Do

Do **not**:

* Embed AI-generated code without understanding it.
* Add unnecessary frameworks.
* Download code at runtime.
* Execute arbitrary user scripts.
* Require cloud services.
* Require proprietary software.
* Implement unrelated features before the geometry engine is mathematically correct.

---

# Known Assumptions

Version 1 assumes:

* Perfect right circular frustums
* Constant wall thickness is irrelevant
* No vessel curvature
* No manufacturing tolerances

Decorative or curved vessels are outside the scope of Version 1.

---

# Future Roadmap (Out of Scope)

Potential future work includes:

* GIMP plugin
* Inkscape extension
* Live 3D preview
* Vessel profile library
* Calibration wizard
* Multiple diameter measurements
* Batch processing
* Text layout tools
* Native installers
* GPU acceleration (only if profiling demonstrates need)

---

# Definition of Done (Version 1)

Version 1 is considered complete when:

* All analytical geometry tests pass.
* Cylinder mode produces mathematically correct output.
* Regression fixtures match expected results within documented tolerances.
* CI passes on Linux, Windows, and macOS.
* Ruff, Black, and mypy complete without errors.
* Documentation is complete.
* The application operates fully offline.
* No known high-severity defects remain open.
