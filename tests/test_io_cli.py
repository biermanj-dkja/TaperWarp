"""Tests for taperwarp.io and the CLI."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from taperwarp.cli import main
from taperwarp.io import (
    FileFormatError,
    inches_to_mm,
    load_raster,
    mm_to_inches,
    save_png,
)


class TestUnits:
    def test_exact_conversion(self) -> None:
        assert inches_to_mm(1.0) == 25.4
        assert mm_to_inches(25.4) == 1.0
        assert mm_to_inches(inches_to_mm(3.21)) == pytest.approx(3.21, rel=1e-15)


class TestIO:
    def test_load_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileFormatError, match="not found"):
            load_raster(tmp_path / "nope.png")

    def test_load_unsupported_extension(self, tmp_path: Path) -> None:
        p = tmp_path / "art.bmp"
        p.write_bytes(b"junk")
        with pytest.raises(FileFormatError, match="Unsupported"):
            load_raster(p)

    def test_load_corrupt_png(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.png"
        p.write_bytes(b"not a png at all")
        with pytest.raises(FileFormatError, match="decode"):
            load_raster(p)

    def test_png_roundtrip_preserves_alpha(self, tmp_path: Path) -> None:
        rgba = np.zeros((8, 8, 4), dtype=np.uint8)
        rgba[..., 0] = 200
        rgba[:4, :, 3] = 255  # top half opaque, bottom transparent
        p = tmp_path / "a.png"
        save_png(Image.fromarray(rgba, "RGBA"), p, dpi=300.0)
        back = np.asarray(load_raster(p))
        assert np.array_equal(back, rgba)

    def test_save_rejects_non_png_suffix(self, tmp_path: Path) -> None:
        img = Image.new("RGBA", (4, 4))
        with pytest.raises(FileFormatError):
            save_png(img, tmp_path / "out.jpg", dpi=300.0)

    def test_jpeg_loads_as_rgba(self, tmp_path: Path) -> None:
        p = tmp_path / "a.jpg"
        Image.new("RGB", (8, 8), (10, 20, 30)).save(p, "JPEG")
        img = load_raster(p)
        assert img.mode == "RGBA"


class TestCLI:
    def _write_src(self, tmp_path: Path) -> Path:
        p = tmp_path / "src.png"
        Image.new("RGBA", (32, 32), (255, 0, 0, 255)).save(p)
        return p

    def test_warp_happy_path_mm(self, tmp_path: Path) -> None:
        src = self._write_src(tmp_path)
        out = tmp_path / "out.png"
        code = main(
            [
                "warp", str(src), str(out),
                "--top-diameter", "70", "--bottom-diameter", "90",
                "--height", "150", "--offset", "10",
                "--art-width", "120", "--art-height", "60", "--dpi", "96",
            ]
        )
        assert code == 0
        assert out.is_file()
        assert Image.open(out).mode == "RGBA"

    def test_warp_inches(self, tmp_path: Path) -> None:
        src = self._write_src(tmp_path)
        out = tmp_path / "out.png"
        code = main(
            [
                "warp", str(src), str(out), "--units", "in",
                "--top-diameter", "2.75", "--bottom-diameter", "3.5",
                "--height", "6", "--offset", "0.5",
                "--art-width", "4", "--art-height", "2", "--dpi", "96",
            ]
        )
        assert code == 0 and out.is_file()

    def test_geometry_error_exit_code(self, tmp_path: Path) -> None:
        src = self._write_src(tmp_path)
        code = main(
            [
                "warp", str(src), str(tmp_path / "out.png"),
                "--top-diameter", "70", "--bottom-diameter", "90",
                "--height", "0", "--offset", "10",
                "--art-width", "120", "--art-height", "60",
            ]
        )
        assert code == 2
