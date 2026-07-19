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

# Must match the version declared in README.md and pyproject.toml.
__version__ = "0.1.0"

__all__ = [
    "ArtworkRegion",
    "Frustum",
    "FrustumWarp",
    "GeometryError",
    "WarpResult",
    "__version__",
    "warp_image",
]
