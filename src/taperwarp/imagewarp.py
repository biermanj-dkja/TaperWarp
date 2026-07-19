"""Raster warping for TaperWarp.

Renders artwork into its developed (unrolled) shape by inverse mapping every
output pixel through the geometry engine and sampling the source bilinearly
(``docs/math.md`` §5). Depends only on NumPy and Pillow; knows nothing about
any GUI.

Determinism: pure float64 arithmetic on a fixed pixel grid; identical inputs
always produce identical output bytes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .geometry import ArtworkRegion, Frustum, FrustumWarp, GeometryError

__all__ = ["MM_PER_INCH", "WarpResult", "warp_image"]

logger = logging.getLogger(__name__)

MM_PER_INCH: float = 25.4

#: Refuse pathological output sizes instead of exhausting memory.
_MAX_OUTPUT_PIXELS: int = 250_000_000


@dataclass(frozen=True)
class WarpResult:
    """A warped raster plus the physical placement of its bounding box.

    ``origin_x_mm`` / ``origin_y_mm`` give the position of the output
    image's upper-left corner in the developed local frame of
    :meth:`taperwarp.geometry.FrustumWarp.developed_bounds` (origin at the
    artwork's top-center point, +x right, +y down).
    """

    image: Image.Image
    dpi: float
    origin_x_mm: float
    origin_y_mm: float


def _bilinear_sample_rgba(
    premultiplied: NDArray[np.float64],
    u_px: NDArray[np.float64],
    v_px: NDArray[np.float64],
    inside: NDArray[np.bool_],
) -> NDArray[np.float64]:
    """Deterministic bilinear sampling of a premultiplied-alpha RGBA array.

    ``u_px``/``v_px`` are continuous source pixel coordinates (pixel centers
    at half-integers). Samples outside the source are treated as fully
    transparent, so edges fade correctly instead of smearing.
    """
    src_h, src_w, _ = premultiplied.shape
    # Continuous coordinate -> index space where integer k is the center of
    # pixel k: subtract the half-pixel offset.
    fx = u_px - 0.5
    fy = v_px - 0.5
    x0 = np.floor(fx).astype(np.int64)
    y0 = np.floor(fy).astype(np.int64)
    wx = fx - x0
    wy = fy - y0

    out = np.zeros(u_px.shape + (4,), dtype=np.float64)
    for dy in (0, 1):
        for dx in (0, 1):
            xi = x0 + dx
            yi = y0 + dy
            valid = inside & (xi >= 0) & (xi < src_w) & (yi >= 0) & (yi < src_h)
            weight = np.where(dx == 1, wx, 1.0 - wx) * np.where(
                dy == 1, wy, 1.0 - wy
            )
            xi_c = np.clip(xi, 0, src_w - 1)
            yi_c = np.clip(yi, 0, src_h - 1)
            sample = premultiplied[yi_c, xi_c, :]
            out += (weight * valid)[..., None] * sample
    return out


def warp_image(
    source: Image.Image,
    frustum: Frustum,
    region: ArtworkRegion,
    dpi: float = 300.0,
) -> WarpResult:
    """Warp ``source`` into the developed shape for ``frustum``/``region``.

    Parameters
    ----------
    source:
        Input artwork. Converted to RGBA; the image is linearly identified
        with the physical rectangle ``region.width_mm x region.height_mm``.
    frustum, region:
        Vessel geometry and artwork placement (see :mod:`taperwarp.geometry`).
    dpi:
        Output resolution in pixels per inch. Must be positive and finite.

    Returns
    -------
    WarpResult
        RGBA image of the developed artwork on a transparent background,
        plus the physical position of its upper-left corner.
    """
    if not (np.isfinite(dpi) and dpi > 0):
        raise GeometryError(f"dpi must be a positive finite number, got {dpi!r}.")

    warp = FrustumWarp(frustum=frustum, region=region)
    bounds = warp.developed_bounds()

    px_per_mm = dpi / MM_PER_INCH
    out_w = max(1, int(np.ceil(bounds.width * px_per_mm)))
    out_h = max(1, int(np.ceil(bounds.height * px_per_mm)))
    if out_w * out_h > _MAX_OUTPUT_PIXELS:
        raise GeometryError(
            f"Output raster would be {out_w}x{out_h} pixels at {dpi} DPI; "
            "reduce the DPI or the artwork size."
        )
    logger.debug("Developed output raster: %dx%d px at %.1f DPI", out_w, out_h, dpi)

    rgba = np.asarray(source.convert("RGBA"), dtype=np.float64) / 255.0
    premult = rgba.copy()
    premult[..., :3] *= premult[..., 3:4]

    src_h, src_w = rgba.shape[0], rgba.shape[1]

    # Output pixel centers in developed-frame millimeters (row-chunked to
    # bound peak memory on very large outputs).
    xs = bounds.x_min + (np.arange(out_w, dtype=np.float64) + 0.5) / px_per_mm
    result = np.zeros((out_h, out_w, 4), dtype=np.float64)
    chunk_rows = max(1, int(8_000_000 // max(out_w, 1)))
    for row0 in range(0, out_h, chunk_rows):
        row1 = min(row0 + chunk_rows, out_h)
        ys = bounds.y_min + (np.arange(row0, row1, dtype=np.float64) + 0.5) / px_per_mm
        gx, gy = np.meshgrid(xs, ys)
        u_mm, v_mm = warp.developed_to_artwork(gx, gy)
        inside = (
            (u_mm >= 0.0)
            & (u_mm <= region.width_mm)
            & (v_mm >= 0.0)
            & (v_mm <= region.height_mm)
        )
        u_px = u_mm * (src_w / region.width_mm)
        v_px = v_mm * (src_h / region.height_mm)
        result[row0:row1] = _bilinear_sample_rgba(premult, u_px, v_px, inside)

    # Un-premultiply.
    alpha = result[..., 3:4]
    with np.errstate(divide="ignore", invalid="ignore"):
        rgb = np.where(alpha > 0.0, result[..., :3] / alpha, 0.0)
    out = np.concatenate([rgb, alpha], axis=-1)
    out_u8 = np.clip(np.rint(out * 255.0), 0, 255).astype(np.uint8)

    image = Image.fromarray(out_u8, mode="RGBA")
    return WarpResult(
        image=image,
        dpi=dpi,
        origin_x_mm=bounds.x_min,
        origin_y_mm=bounds.y_min,
    )
