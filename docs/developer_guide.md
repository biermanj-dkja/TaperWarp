# Developer Guide

## Setup

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pre-commit install   # optional but recommended
```

## Workflow

1. **Read `docs/math.md` before touching any formula.** It is the source of
   truth; change the derivation there first, then the code.
2. Write or extend tests alongside every change. Geometry changes need
   analytic checks (1e-9 relative / 0.001 mm absolute tolerance),
   property-based coverage, and edge cases.
3. Run locally before pushing:

   ```bash
   ruff check src tests && black --check src tests && mypy && pytest
   ```

   Offline environments without pytest can use `python tests/_minirunner.py`.
4. Use Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:` …).
5. Follow the release checklist in `PROJECT_GUIDELINES.md` §26.4 for any
   version bump; README, ChangeLog, pyproject, and `__version__` move
   together.

## Ground rules (short form)

- Math before features; never heuristic warping.
- Strict layering: GUI → app logic → geometry → image processing → I/O.
- Millimeters internally; inches only at I/O boundaries.
- Offline only: no network, telemetry, or credentials, ever.
- Dependencies: Pillow/NumPy core; svgwrite/svgpathtools/SciPy only with
  written justification; OpenCV disallowed without a documented advantage.
- `logging` (default WARNING), never `print()` outside CLI output.

See `PROJECT_GUIDELINES.md` for the full binding guidelines.
