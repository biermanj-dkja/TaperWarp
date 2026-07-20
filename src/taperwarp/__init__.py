"""TaperWarp: mathematically correct artwork warping for tapered vessels.

Public API (stable across frontends — GUI, CLI, and plugins all use exactly
these entry points):

* :class:`taperwarp.geometry.Frustum`
* :class:`taperwarp.geometry.ArtworkRegion`
* :func:`taperwarp.imagewarp.warp_image`
* ``warp_svg`` (planned; not yet implemented)
"""

from .geometry import ArtworkRegion, Frustum, FrustumWarp, GeometryError
from .imagewarp import WarpResult, warp_image

# Canonical version (PEP 440). Must match README.md and pyproject.toml —
# the release checklist (PROJECT_GUIDELINES.md §26.4) moves all three together.
__version__ = "0.1.1a1"

__all__ = [
    "ArtworkRegion",
    "Frustum",
    "FrustumWarp",
    "GeometryError",
    "WarpResult",
    "__version__",
    "warp_image",
]
