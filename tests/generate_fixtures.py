"""Regenerate the golden-image regression fixtures in tests/fixtures/.

Run deliberately (never automatically) when an intentional visual change
lands, and explain the change in the PR:

    python tests/generate_fixtures.py

The fixture set covers the reference cases required by
PROJECT_GUIDELINES.md §18: checkerboard and square-grid sources across
cylinder, mild-taper, strong-taper, and reverse (pint) taper vessels.
Definitions are shared with ``test_golden.py`` via ``tests_fixture_defs.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from taperwarp import warp_image  # noqa: E402
from tests_fixture_defs import DPI, REGION, SOURCES, VESSELS  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def main() -> int:
    FIXTURES.mkdir(exist_ok=True)
    for vessel_name, frustum in VESSELS.items():
        for src_name, make in SOURCES.items():
            out = FIXTURES / f"{src_name}_{vessel_name}.png"
            result = warp_image(make(), frustum, REGION, dpi=DPI)
            result.image.save(out, format="PNG")
            print(f"wrote {out.name}: {result.image.width}x{result.image.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
