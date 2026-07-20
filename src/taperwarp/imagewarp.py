"""Raster warping for TaperWarp.

Renders artwork into its developed (unrolled) shape by inverse mapping every
output pixel through the geometry engine and sampling the source bilinearly
(``docs/math.md`` §5). Depends only on NumPy and Pillow; knows nothing about
any GUI.

Determinism: fixed pixel grid, float64 geometry coordinates, float32 pixel
arithmetic, chunked in a fixed row order; identical inputs on the same
platform always produce identical output bytes.

Memory model (v0.1.1a1): the destination raster is allocated once as
``uint8`` (4 bytes/pixel). Each row chunk is inverse-mapped, sampled,
un-premultiplied, and quantized to ``uint8`` before the next chunk starts,
so peak working memory is the small chunk plus the source — never a
full-size floating-point copy of the output. The estimated peak is computed
*before* any allocation and the job is rejected with an actionable message
if it exceeds the memory budget.

Edge behavior (v1 policy, tested): source samples outside the source raster
are treated as fully transparent. Opaque artwork that touches the source
edge therefore antialiases against transparency and may show a soft
(partially transparent) fringe up to one output pixel wide at the artwork
boundary. This suits floating logos/decals; a clamp-to-edge mode for
full-bleed artwork is on the roadmap.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .geometry import ArtworkRegion, Frustum, FrustumWarp, GeometryError

__all__ = ["DEFAULT_MEMORY_BUDGET_BYTES", "MM_PER_INCH", "WarpResult", "warp_image"]

logger = logging.getLogger(__name__)

MM_PER_INCH: float = 25.4

#: Default budget for estimated peak working memory of a single warp job.
#: Chosen so the largest accepted job stays comfortable on an ordinary
#: 8 GB machine. Callers may pass a different ``memory_budget_bytes``.
DEFAULT_MEMORY_BUDGET_BYTES: int = 2 * 1024**3  # 2 GiB

#: Rows per processing chunk are sized so each chunk's working arrays stay
#: near this many float64 elements (coordinate grids dominate).
_CHUNK_TARGET_ELEMENTS: int = 4_000_000


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


def _estimate_peak_bytes(
    out_w: int, out_h: int, src_w: int, src_h: int, chunk_rows: int
) -> int:
    """Estimate peak working memory for a warp job, in bytes.

    Counted (deliberately slightly conservative):

    * destination uint8 RGBA:                ``4 * out_w * out_h``
    * source float32 RGBA + premultiplied:   ``2 * 16 * src_w * src_h``
    * per-chunk arrays: two float64 coordinate grids in and two out of the
      inverse mapping, the inside mask, two float64 source-pixel-coordinate
      grids, and the float32 RGBA chunk accumulator.
    """
    dest = 4 * out_w * out_h
    source = 2 * 16 * src_w * src_h
    chunk_px = chunk_rows * out_w
    chunk = chunk_px * (6 * 8 + 1 + 4 * 4)  # 6 f64 grids + bool mask + f32 RGBA
    return dest + source + chunk


def _bilinear_sample_rgba(
    premultiplied: NDArray[np.float32],
    u_px: NDArray[np.float64],
    v_px: NDArray[np.float64],
    inside: NDArray[np.bool_],
) -> NDArray[np.float32]:
    """Deterministic bilinear sampling of a premultiplied-alpha RGBA array.

    ``u_px``/``v_px`` are continuous source pixel coordinates (pixel centers
    at half-integers). Samples outside the source raster are treated as
    fully transparent (see module docstring for the v1 edge policy).
    Coordinates and weights are computed in float64; pixel accumulation is
    float32, which carries far more precision than the 8-bit output needs.
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

    out = np.zeros(u_px.shape + (4,), dtype=np.float32)
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
            out += ((weight * valid).astype(np.float32))[..., None] * sample
    return out


def _finalize_chunk(chunk: NDArray[np.float32]) -> NDArray[np.uint8]:
    """Un-premultiply one float32 RGBA chunk and quantize it to uint8."""
    alpha = chunk[..., 3:4]
    with np.errstate(divide="ignore", invalid="ignore"):
        rgb = np.where(alpha > 0.0, chunk[..., :3] / alpha, np.float32(0.0))
    out = np.concatenate([rgb, alpha], axis=-1)
    return np.clip(np.rint(out * 255.0), 0, 255).astype(np.uint8)


def warp_image(
    source: Image.Image,
    frustum: Frustum,
    region: ArtworkRegion,
    dpi: float = 300.0,
    memory_budget_bytes: int = DEFAULT_MEMORY_BUDGET_BYTES,
) -> WarpResult:
    """Warp ``source`` into the developed shape for ``frustum``/``region``.

    Parameters
    ----------
    source:
        Input artwork. Converted to RGBA; the image is linearly identified
        with the physical rectangle ``region.width_mm x region.height_mm``.
        Must have positive width and height.
    frustum, region:
        Vessel geometry and artwork placement (see :mod:`taperwarp.geometry`).
    dpi:
        Output resolution in pixels per inch. Must be positive and finite.
    memory_budget_bytes:
        Maximum estimated peak working memory for this job. Jobs whose
        estimate exceeds the budget are rejected with a
        :class:`~taperwarp.geometry.GeometryError` *before* any large
        allocation, with the estimate stated in the message.

    Returns
    -------
    WarpResult
        RGBA image of the developed artwork on a transparent background,
        plus the physical position of its upper-left corner.
    """
    if not (np.isfinite(dpi) and dpi > 0):
        raise GeometryError(f"dpi must be a positive finite number, got {dpi!r}.")
    if source.width <= 0 or source.height <= 0:
        raise GeometryError(
            f"Source image must have positive dimensions, got "
            f"{source.width}x{source.height}."
        )

    warp = FrustumWarp(frustum=frustum, region=region)
    bounds = warp.developed_bounds()

    px_per_mm = dpi / MM_PER_INCH
    out_w = max(1, int(np.ceil(bounds.width * px_per_mm)))
    out_h = max(1, int(np.ceil(bounds.height * px_per_mm)))
    src_w, src_h = source.width, source.height

    chunk_rows = max(1, min(out_h, _CHUNK_TARGET_ELEMENTS // max(out_w, 1)))
    estimated = _estimate_peak_bytes(out_w, out_h, src_w, src_h, chunk_rows)
    if estimated > memory_budget_bytes:
        raise GeometryError(
            f"Output raster would be {out_w}x{out_h} pixels at {dpi:g} DPI, "
            f"with an estimated peak working memory of "
            f"{estimated / 1024**3:.1f} GB (budget "
            f"{memory_budget_bytes / 1024**3:.1f} GB); "
            "reduce the DPI or the artwork size."
        )
    logger.debug(
        "Developed output raster: %dx%d px at %.1f DPI (est. %.2f GB peak)",
        out_w, out_h, dpi, estimated / 1024**3,
    )

    rgba = np.asarray(source.convert("RGBA"), dtype=np.float32) / np.float32(255.0)
    premult = rgba.copy()
    premult[..., :3] *= premult[..., 3:4]

    # Destination allocated once, as uint8 (4 bytes/px). Each chunk is
    # finalized (un-premultiplied + quantized) before the next one starts.
    out_u8 = np.zeros((out_h, out_w, 4), dtype=np.uint8)
    xs = bounds.x_min + (np.arange(out_w, dtype=np.float64) + 0.5) / px_per_mm
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
        chunk = _bilinear_sample_rgba(premult, u_px, v_px, inside)
        out_u8[row0:row1] = _finalize_chunk(chunk)

    image = Image.fromarray(out_u8, mode="RGBA")
    return WarpResult(
        image=image,
        dpi=dpi,
        origin_x_mm=bounds.x_min,
        origin_y_mm=bounds.y_min,
    )
