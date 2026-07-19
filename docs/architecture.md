# TaperWarp Architecture

## Layering

Strict, one-directional layering. Each layer may import only from layers
below it; nothing imports upward.

```
GUI (src/taperwarp/gui/, PySide6)          — not yet implemented
        ↓
Application Logic / frontends (cli.py, future plugins/)
        ↓
Geometry Engine (geometry.py)              — pure math, NumPy only
        ↓
Image Processing (imagewarp.py, future svgwarp.py)
        ↓
File I/O (io.py)
```

Notes on the arrows: frontends *orchestrate* — they call I/O to load, the
warp functions to transform, and I/O to save. The geometry engine imports
nothing from any other project module. `imagewarp.py` consumes the geometry
engine's public mapping; it never re-implements math. `io.py` knows only
Pillow and paths.

Rules enforced by review and tests:

* `geometry.py` and `imagewarp.py` contain **zero** GUI imports or
  GUI-shaped assumptions.
* All frontends (CLI, GUI, plugins) consume exactly the same public API:
  `Frustum`, `ArtworkRegion`, `warp_image`, and (planned) `warp_svg`.
  Behavior is never forked per-frontend.
* Inch↔mm conversion happens only in `io.py` helpers and CLI argument
  handling; every internal number is millimeters.

## Module map

| Module | Responsibility |
|---|---|
| `taperwarp/geometry.py` | Analytic frustum↔development mapping. Pure, deterministic, documented in `docs/math.md`. |
| `taperwarp/imagewarp.py` | Inverse-mapped bilinear raster resampling with premultiplied alpha; exact output bounds; DPI handling. |
| `taperwarp/io.py` | Raster load/save (PNG, JPEG), unit conversion. |
| `taperwarp/cli.py` | Thin argparse frontend. No math, no format decisions beyond dispatch. |
| `taperwarp/svgwarp.py` | Planned: vector warping via the same geometry API. |
| `taperwarp/gui/` | Planned: thin PySide6 frontend. |
| `taperwarp/plugins/` | Planned: GIMP / Inkscape adapters over the public API. |

## Determinism & offline guarantees

* Float64 arithmetic on fixed grids; no randomness in production paths; the
  same inputs always produce byte-identical output.
* No module performs network access, telemetry, or file writes outside
  caller-provided paths.

## Error handling

Invalid geometry raises `taperwarp.geometry.GeometryError`; unreadable or
unsupported files raise `taperwarp.io.FileFormatError`. Both derive from
`ValueError` and carry human-actionable messages. The CLI maps them to exit
code 2 with `error: …` on stderr.
