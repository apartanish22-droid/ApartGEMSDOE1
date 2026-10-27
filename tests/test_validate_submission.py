"""Synthetic CLI tests for the saved-GeoTIFF format gate."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "scripts" / "validate_submission.py"


class ValidateSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.transform = from_origin(500000, 4500000, 30, 30)
        self.template = self.root / "official-sample.tif"
        self.candidate = self.root / "candidate.tif"
        self._write(
            self.template,
            np.array([[0, 0, 0], [0, 0, 0], [0, 0, -9999]], dtype=np.float32),
            nodata=-9999.0,
        )

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
        dtype: str | None = None,
    ) -> None:
        count = 1 if array.ndim == 2 else array.shape[0]
        height, width = array.shape[-2:]
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=count,
            dtype=dtype or str(array.dtype),
            crs=crs,
            transform=transform or self.transform,
            nodata=nodata,
        ) as dataset:
            dataset.write(array, 1 if array.ndim == 2 else None)

    def _run(self, data: np.ndarray, **kwargs) -> subprocess.CompletedProcess[str]:
        self._write(self.candidate, data, **kwargs)
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(self.candidate), "--template", str(self.template)],
            capture_output=True,
            text=True,
            check=False,
        )

    def _json(self, result: subprocess.CompletedProcess[str]) -> dict:
        return json.loads(result.stdout)

    def test_accepts_matching_float32_grid_and_nodata_outside(self) -> None:
        data = np.array([[0, 0.2, 1], [0.4, 0.5, 0.6], [0.7, 0.8, np.nan]], dtype=np.float32)
        result = self._run(data, nodata=np.nan)
        report = self._json(result)
        self.assertEqual(result.returncode, 0, report)
        self.assertEqual(report["status"], "PASS_FORMAT_ONLY")
        self.assertRegex(report["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(report["sha256"], hashlib.sha256(self.candidate.read_bytes()).hexdigest())

    def test_rejects_nan_inside_template_footprint(self) -> None:
        data = np.full((3, 3), 0.5, dtype=np.float32)
        data[1, 1] = np.nan
        data[2, 2] = np.nan
        result = self._run(data, nodata=np.nan)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any("NaN or Inf inside" in error for error in self._json(result)["errors"]))

    def test_rejects_infinity_and_out_of_range_inside(self) -> None:
        for invalid in (np.inf, -0.01, 1.01):
            with self.subTest(value=invalid):
                data = np.full((3, 3), 0.5, dtype=np.float32)
                data[0, 0] = invalid
                data[2, 2] = np.nan
                result = self._run(data, nodata=np.nan)
                self.assertEqual(result.returncode, 1)
                self.assertFalse(self._json(result)["format_pass"])

    def test_rejects_non_null_value_outside_template_footprint(self) -> None:
        data = np.full((3, 3), 0.5, dtype=np.float32)
        data[2, 2] = 0.0
        result = self._run(data)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any("outside the template footprint" in e for e in self._json(result)["errors"]))

    def test_accepts_finite_nodata_outside_when_masked(self) -> None:
        data = np.full((3, 3), 0.5, dtype=np.float32)
        data[2, 2] = -9999.0
        result = self._run(data, nodata=-9999.0)
        self.assertEqual(result.returncode, 0, self._json(result))

    def test_rejects_crs_shape_and_transform_mismatch(self) -> None:
        valid = np.full((3, 3), 0.5, dtype=np.float32)
        for label, kwargs, data in (
            ("crs", {"crs": "EPSG:4326"}, valid),
            ("transform", {"transform": from_origin(500030, 4500000, 30, 30)}, valid),
            ("shape", {}, np.full((2, 3), 0.5, dtype=np.float32)),
        ):
            with self.subTest(kind=label):
                result = self._run(data, **kwargs)
                self.assertEqual(result.returncode, 1)
                report = self._json(result)
                self.assertTrue(report["errors"])

    def test_rejects_non_float32_and_multiband(self) -> None:
        data64 = np.full((3, 3), 0.5, dtype=np.float64)
        result = self._run(data64)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any("float32" in e for e in self._json(result)["errors"]))

        multiband = self.root / "multiband.tif"
        self._write(multiband, np.zeros((2, 3, 3), dtype=np.float32))
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(multiband), "--template", str(self.template)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any("one band" in e for e in self._json(result)["errors"]))

    def test_rejects_multiband_template(self) -> None:
        template = self.root / "multiband-template.tif"
        self._write(template, np.zeros((2, 3, 3), dtype=np.float32))
        data = np.full((3, 3), 0.5, dtype=np.float32)
        self._write(self.candidate, data)
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(self.candidate), "--template", str(template)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any("template must have one band" in e for e in self._json(result)["errors"]))

    def test_requires_template(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(self.candidate)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
