"""Synthetic raster regression tests for the GeoTIFF format/range gate."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_submission.py"


class ValidateSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.template_path = self.root / "template.tif"
        self.profile = {
            "driver": "GTiff",
            "height": 3,
            "width": 4,
            "count": 1,
            "dtype": "float32",
            "crs": "EPSG:32611",
            "transform": from_origin(500000, 4500000, 30, 30),
            "nodata": -9999.0,
        }
        template_data = np.array(
            [[0, 0, 0, -9999], [0, 0, 0, -9999], [0, 0, 0, -9999]],
            dtype=np.float32,
        )
        with rasterio.open(self.template_path, "w", **self.profile) as dataset:
            dataset.write(template_data, 1)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_candidate(
        self,
        name: str = "candidate.tif",
        data: np.ndarray | None = None,
        **profile_overrides: object,
    ) -> Path:
        path = self.root / name
        profile = {**self.profile, **profile_overrides}
        if data is None:
            data = np.array(
                [[0.0, 0.25, 1.0, -9999.0], [0.2, 0.4, 0.6, -9999.0], [0.3, 0.5, 0.8, -9999.0]],
                dtype=np.float32,
            )
        with rasterio.open(path, "w", **profile) as dataset:
            dataset.write(data, 1 if profile["count"] == 1 else None)
        return path

    def run_validator(self, candidate: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(candidate), "--template", str(self.template_path)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_accepts_matching_single_band_grid_and_unit_values(self) -> None:
        result = self.run_validator(self.write_candidate())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("values in [0,1]", result.stdout)

    def test_rejects_nan_inside_template_footprint(self) -> None:
        data = np.full((3, 4), 0.5, dtype=np.float32)
        data[:, 3] = -9999.0
        data[1, 1] = np.nan
        result = self.run_validator(self.write_candidate(data=data))
        self.assertEqual(result.returncode, 1)
        self.assertIn("NaN or infinity", result.stderr)

    def test_rejects_prediction_outside_unit_interval(self) -> None:
        for invalid in (-0.001, 1.001):
            with self.subTest(value=invalid):
                data = np.full((3, 4), 0.5, dtype=np.float32)
                data[:, 3] = -9999.0
                data[1, 1] = invalid
                result = self.run_validator(self.write_candidate(f"range-{invalid}.tif", data=data))
                self.assertEqual(result.returncode, 1)
                self.assertIn("outside [0,1]", result.stderr)

    def test_rejects_crs_mismatch(self) -> None:
        result = self.run_validator(self.write_candidate(crs="EPSG:4326"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("CRS mismatch", result.stderr)

    def test_rejects_shape_mismatch(self) -> None:
        data = np.full((2, 4), 0.5, dtype=np.float32)
        result = self.run_validator(self.write_candidate(data=data, height=2))
        self.assertEqual(result.returncode, 1)
        self.assertIn("shape mismatch", result.stderr)

    def test_rejects_transform_mismatch(self) -> None:
        result = self.run_validator(
            self.write_candidate(transform=from_origin(500030, 4500000, 30, 30))
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("transform mismatch", result.stderr)

    def test_rejects_non_float32_candidate(self) -> None:
        result = self.run_validator(self.write_candidate(dtype="float64"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("must be float32", result.stderr)

    def test_rejects_finite_values_outside_template_footprint(self) -> None:
        data = np.full((3, 4), 0.5, dtype=np.float32)
        data[:, 3] = 0.0
        result = self.run_validator(self.write_candidate(data=data))
        self.assertEqual(result.returncode, 1)
        self.assertIn("outside template footprint", result.stderr)

    def test_rejects_multiband_candidate(self) -> None:
        path = self.root / "multiband.tif"
        profile = {**self.profile, "count": 2}
        with rasterio.open(path, "w", **profile) as dataset:
            dataset.write(np.full((2, 3, 4), 0.5, dtype=np.float32))
        result = self.run_validator(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("exactly one band", result.stderr)

    def test_allows_nodata_outside_template_footprint(self) -> None:
        data = np.full((3, 4), 0.5, dtype=np.float32)
        data[:, 3] = np.nan
        result = self.run_validator(self.write_candidate(data=data))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_template_nan_defines_outside_footprint_without_nodata_metadata(self) -> None:
        template_profile = {**self.profile, "nodata": None}
        template_data = np.full((3, 4), 1.0, dtype=np.float32)
        template_data[:, 3] = np.nan
        with rasterio.open(self.template_path, "w", **template_profile) as dataset:
            dataset.write(template_data, 1)
        result = self.run_validator(self.write_candidate())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_multiband_template(self) -> None:
        path = self.root / "multiband-template.tif"
        profile = {**self.profile, "count": 2}
        with rasterio.open(path, "w", **profile) as dataset:
            dataset.write(np.full((2, 3, 4), 0.5, dtype=np.float32))
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.write_candidate()), "--template", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("template must have exactly one band", result.stderr)


if __name__ == "__main__":
    unittest.main()
