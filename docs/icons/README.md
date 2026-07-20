# TaperWarp icons

Application icon assets. All artwork here is original to the TaperWarp
project and MIT-licensed with it.

| File | Purpose |
|---|---|
| `taperwarp.svg` | Master vector icon (placeholder pending final branding). |

## Conventions

- The SVG is the single source of truth; raster sizes are exported from it.
- When final branding lands, add exported PNGs at 16, 32, 48, 64, 128, 256,
  and 512 px, plus platform bundles (`taperwarp.ico` for Windows,
  `taperwarp.icns` for macOS) generated from the same SVG.
- Keep exports deterministic and reproducible (record the export command
  here when raster assets are added).
- These assets are used by the future PySide6 GUI window/installer only —
  nothing in the engine or CLI depends on them.
