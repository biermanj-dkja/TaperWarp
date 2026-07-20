"""Golden-image regression tests.

Byte-level comparison of warped output against checked-in fixtures. On the
platform that generated the fixtures this is exact; a small documented
tolerance path (max channel delta <= 1, on <= 0.5% of pixels) absorbs
last-ulp libm differences on other platforms without hiding real
regressions such as shifts, flipped curvature, halos, or bound changes.

Regenerate fixtures deliberately with ``python tests/generate_fixtures.py``
and justify the visual change in the PR.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from taperwarp import warp_image
from tests_fixture_defs import DPI, REGION, SOURCES, VESSELS

FIXTURES = Path(__file__).parent / "fixtures"

CASES = [
    (src_name, vessel_name)
    for vessel_name in VESSELS
    for src_name in SOURCES
]


@pytest.mark.parametrize("src_name,vessel_name", CASES)
def test_golden(src_name: str, vessel_name: str) -> None:
    fixture = FIXTURES / f"{src_name}_{vessel_name}.png"
    assert fixture.is_file(), f"missing fixture {fixture.name}"
    expected = np.asarray(Image.open(fixture).convert("RGBA"))

    result = warp_image(SOURCES[src_name](), VESSELS[vessel_name], REGION, dpi=DPI)
    actual = np.asarray(result.image)

    # Dimensions must match exactly — a changed bounding box is a regression.
    assert actual.shape == expected.shape, (
        f"{fixture.name}: shape {actual.shape} != {expected.shape}"
    )

    if np.array_equal(actual, expected):
        return  # exact match (same platform as fixture generation)

    # Documented tolerance path for cross-platform libm ulp differences.
    diff = np.abs(actual.astype(np.int16) - expected.astype(np.int16))
    max_delta = int(diff.max())
    frac_diff = float((diff.max(axis=-1) > 0).mean())
    assert max_delta <= 1 and frac_diff <= 0.005, (
        f"{fixture.name}: max channel delta {max_delta}, "
        f"{frac_diff:.4%} of pixels differ — regenerate fixtures only if "
        "this visual change is intentional (see tests/generate_fixtures.py)."
    )
