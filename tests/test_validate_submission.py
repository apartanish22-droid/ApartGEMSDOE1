"""Integration tests for the GeoTIFF submission gate (requires rasterio/numpy)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

import numpy as np
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_submission import validate  # noqa: E402


class ValidateSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.transform = from_origin(500000, 4500000, 30, 30)
        self.crs = "EPSG:32611"
        self.nodata = -9999.0
        self.reference = self.root / "reference.tif"
        reference = np.array(
            [[1, 1, 1], [1, 0, 1], [1, 1, self.nodata]], dtype="float32"
        )
        self._write(self.reference, reference, nodata=self.nodata)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write(
        self,
        path: Path,
        array: np.ndarray,
        *,
        crs: str = "EPSG:32611",
        transform=None,
        nodata: float | None = None,
    ) -> None:
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=array.shape[0],
            width=array.shape[1],
            count=1,
            dtype=array.dtype,
            crs=crs,
            transform=transform or self.transform,
            nodata=nodata,
        ) as dst:
            dst.write(array, 1)

    def _candidate(self, values: np.ndarray, **kwargs) -> Path:
        path = self.root / "candidate.tif"
        self._write(path, values.astype("float32"), **kwargs)
        return path

    def test_accepts_matching_grid_and_unit_interval_in_footprint(self) -> None:
        candidate = self._candidate(
            np.array([[0, 0.2, 1], [0.4, 0.5, 0.6], [0.7, 0.8, self.nodata]]),
            nodata=self.nodata,
        )
        result = validate(candidate, self.reference)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["footprint_pixels_checked"], 8)
        self.assertEqual(result["value_range_inside_footprint"], [0.0, 1.0])
        self.assertEqual(len(result["sha256"]), 64)

    def test_rejects_out_of_range_values(self) -> None:
        candidate = self._candidate(np.array([[0, 0.2, 1], [0.4, 1.2, 0.6], [0.7, 0.8, self.nodata]]), nodata=self.nodata)
        with self.assertRaisesRegex(ValueError, r"range \[0, 1\]"):
            validate(candidate, self.reference)

    def test_rejects_nan_inside_footprint(self) -> None:
        candidate = self._candidate(np.array([[0, 0.2, 1], [0.4, np.nan, 0.6], [0.7, 0.8, self.nodata]]), nodata=self.nodata)
        with self.assertRaisesRegex(ValueError, "non-finite"):
            validate(candidate, self.reference)

    def test_rejects_masked_pixel_inside_footprint(self) -> None:
        candidate = self._candidate(np.array([[0, 0.2, 1], [0.4, 0.5, 0.6], [0.7, 0.8, self.nodata]]), nodata=0.5)
        with self.assertRaisesRegex(ValueError, "masked/nodata"):
            validate(candidate, self.reference)

    def test_rejects_crs_shape_and_transform_mismatch(self) -> None:
        values = np.zeros((3, 3), dtype="float32")
        with self.subTest("crs"):
            candidate = self._candidate(values, crs="EPSG:4326")
            with self.assertRaisesRegex(ValueError, "CRS mismatch"):
                validate(candidate, self.reference)
        with self.subTest("shape"):
            candidate = self._candidate(np.zeros((2, 3), dtype="float32"))
            with self.assertRaisesRegex(ValueError, "Shape mismatch"):
                validate(candidate, self.reference)
        with self.subTest("transform"):
            candidate = self._candidate(values, transform=from_origin(500010, 4500000, 30, 30))
            with self.assertRaisesRegex(ValueError, "Transform mismatch"):
                validate(candidate, self.reference)

    def test_rejects_multiband_candidate(self) -> None:
        path = self.root / "multiband.tif"
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=3,
            width=3,
            count=2,
            dtype="float32",
            crs=self.crs,
            transform=self.transform,
        ) as dst:
            dst.write(np.zeros((2, 3, 3), dtype="float32"))
        with self.assertRaisesRegex(ValueError, "single-band"):
            validate(path, self.reference)


if __name__ == "__main__":
    unittest.main()
