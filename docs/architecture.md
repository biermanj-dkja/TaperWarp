# TaperWarp Architecture

## Structure

TaperWarp is organized as a small dependency tree. Frontends orchestrate;
the geometry engine sits at the bottom and imports nothing from any other
project module.

```
                GUI / CLI / Plugins  (frontends — orchestrate a workflow)
                   /       |       \
                  /        |        \
           File I/O    Raster      Vector renderer
           (io.py)   renderer      (svgwarp.py, planned)
                    (imagewarp.py)      |
                          \             /
                           \           /
                        Geometry Engine
                         (geometry.py)
```

> **Note (v0.1.1a1):** earlier documentation showed geometry *above* image
> processing in a linear stack. In dependency terms that was backwards:
> `imagewarp.py` imports and consumes `geometry.py`, and image processing
> does not depend on `io.py` at all — the frontend calls each independently.
> The diagram above reflects the actual (and intended) dependency
> direction. The binding rules are unchanged: the geometry engine and the
> renderers have zero GUI imports, and the geometry engine imports nothing
> from any other project module.

Notes on the arrows: frontends *orchestrate* — they call I/O to load, the
warp functions to transform, and I/O to save. `imagewarp.py` consumes the
geometry engine's public mapping; it never re-implements math. `io.py`
knows only Pillow and paths.

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
| `taperwarp/imagewarp.py` | Inverse-mapped bilinear raster resampling with premultiplied alpha; exact output bounds; DPI handling; chunked uint8 output pipeline with an upfront memory estimate. |
| `taperwarp/io.py` | Raster load/save (PNG, JPEG), unit conversion. |
| `taperwarp/cli.py` | Thin argparse frontend. No math, no format decisions beyond dispatch. |
| `taperwarp/svgwarp.py` | Planned: vector warping via the same geometry API. |
| `taperwarp/gui/` | Planned: thin PySide6 frontend. |
| `taperwarp/plugins/` | Planned: GIMP / Inkscape adapters over the public API. |

## Determinism & offline guarantees

* Fixed pixel grids, float64 geometry coordinates, float32 pixel
  accumulation, fixed chunk order, no randomness in production paths: the
  same inputs always produce byte-identical output **on the same platform**.
  (Cross-platform bit-identity is not guaranteed — transcendental functions
  in system math libraries may differ in the last ulp; golden-image
  fixtures therefore also carry a small documented tolerance path.)
* No module performs network access, telemetry, or file writes outside
  caller-provided paths.

## Memory model of the raster renderer

`warp_image` estimates its peak working memory **before** allocating
anything large (destination uint8 raster + float32 source copies + one row
chunk of working arrays) and rejects the job with an actionable
`GeometryError` if the estimate exceeds the memory budget
(default 2 GiB, caller-configurable). The destination is allocated once as
uint8; each row chunk is inverse-mapped, sampled, un-premultiplied, and
quantized before the next chunk starts, so no full-size floating-point copy
of the output ever exists.

## Error handling

Invalid geometry raises `taperwarp.geometry.GeometryError`; unreadable or
unsupported input files raise `taperwarp.io.FileFormatError`; unwritable
outputs (permissions, missing directory, disk full) raise
`taperwarp.io.OutputError`. All derive from `ValueError` and carry
human-actionable messages. The CLI maps them (and `MemoryError`) to exit
code 2 with `error: …` on stderr.
