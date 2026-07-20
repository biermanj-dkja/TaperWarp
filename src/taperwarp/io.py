"""File I/O for TaperWarp.

Loading and saving of raster artwork plus unit conversion helpers. Inch↔mm
conversion happens **only** here and in the CLI argument layer — internal
code works exclusively in millimeters. Depends only on Pillow and the
standard library; knows nothing about any GUI.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

__all__ = [
    "MM_PER_INCH",
    "FileFormatError",
    "OutputError",
    "inches_to_mm",
    "load_raster",
    "mm_to_inches",
    "save_png",
]

logger = logging.getLogger(__name__)

MM_PER_INCH: float = 25.4

_SUPPORTED_RASTER_SUFFIXES = {".png", ".jpg", ".jpeg"}


class FileFormatError(ValueError):
    """Raised for unsupported or unreadable input files."""


class OutputError(ValueError):
    """Raised when an output file cannot be written (permissions, missing
    directory, disk full, path is a directory, …), with a clean message."""


def inches_to_mm(value_in: float) -> float:
    """Convert inches to millimeters (exact: 1 in = 25.4 mm)."""
    return value_in * MM_PER_INCH


def mm_to_inches(value_mm: float) -> float:
    """Convert millimeters to inches (exact)."""
    return value_mm / MM_PER_INCH


def load_raster(path: str | Path) -> Image.Image:
    """Load a PNG or JPEG image as RGBA, preserving transparency.

    Raises
    ------
    FileFormatError
        If the file does not exist, has an unsupported extension, or cannot
        be decoded.
    """
    p = Path(path)
    if not p.is_file():
        raise FileFormatError(f"Input file not found: {p}")
    if p.suffix.lower() not in _SUPPORTED_RASTER_SUFFIXES:
        raise FileFormatError(
            f"Unsupported raster format {p.suffix!r}; "
            "supported inputs are PNG and JPEG."
        )
    try:
        with Image.open(p) as img:
            img.load()
            return img.convert("RGBA")
    except OSError as exc:  # Pillow raises OSError family for decode failures
        raise FileFormatError(f"Could not decode image {p}: {exc}") from exc


def save_png(image: Image.Image, path: str | Path, dpi: float) -> None:
    """Save an RGBA image as PNG with embedded DPI metadata.

    Only writes to the exact path the caller (i.e., the user) selected.

    Raises
    ------
    FileFormatError
        If the output path does not end in ``.png``.
    OutputError
        If the file cannot be written (permission denied, missing parent
        directory, disk full, path is a directory, …).
    """
    p = Path(path)
    if p.suffix.lower() != ".png":
        raise FileFormatError(
            f"Output path must end in .png, got {p.suffix!r}."
        )
    try:
        image.save(p, format="PNG", dpi=(dpi, dpi))
    except OSError as exc:
        raise OutputError(f"Could not save {p}: {exc}") from exc
    logger.info("Wrote %s (%dx%d px, %.0f DPI)", p, image.width, image.height, dpi)
