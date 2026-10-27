"""CLI integration tests for the shared GeoTIFF format validator."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
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
        count = 1 if array.ndim == 2 else array.shape[0]
        height, width = array.shape[-2:]
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=count,
            dtype=array.dtype,
            crs=crs,
            transform=transform or self.transform,
            nodata=nodata,
        ) as dst:
            if array.ndim == 2:
                dst.write(array, 1)
            else:
                dst.write(array)

    def _run(self, array: np.ndarray, **kwargs) -> subprocess.CompletedProcess[str]:
        candidate = self.root / "candidate.tif"
        self._write(candidate, array.astype("float32"), **kwargs)
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(candidate), "--template", str(self.reference)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_accepts_matching_grid_and_unit_interval(self) -> None:
        result = self._run(
            np.array([[0, 0.2, 1], [0.4, 0.5, 0.6], [0.7, 0.8, self.nodata]]),
            nodata=self.nodata,
        )
        # The CLI correctly rejects this miniature synthetic grid as non-competition.
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('shape differs from documented competition grid', result.stderr)
        self.assertRegex(result.stdout, r'"sha256": "[0-9a-f]{64}"')
        # Test positive validation arithmetic on a deliberately patched *test* grid.
        from scripts.validate_submission import validate
        with patch('scripts.validate_submission.EXPECTED_SHAPE', (3, 3)), \
             patch('scripts.validate_submission.EXPECTED_PIXEL_M', 30.0):
            report = validate(self.root / 'candidate.tif', self.reference)
        self.assertTrue(report['format_pass'])
        self.assertEqual(report['checks']['value_min_inside'], 0.0)
        self.assertEqual(report['checks']['value_max_inside'], 1.0)
        self.assertFalse(report['slot_approved'])

    def test_rejects_out_of_range_values(self) -> None:
        result = self._run(
            np.array([[0, 0.2, 1], [0.4, 1.2, 0.6], [0.7, 0.8, self.nodata]]),
            nodata=self.nodata,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside [0,1]", result.stderr)

    def test_rejects_nan_inside_footprint(self) -> None:
        result = self._run(
            np.array([[0, 0.2, 1], [0.4, np.nan, 0.6], [0.7, 0.8, self.nodata]]),
            nodata=self.nodata,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NaN or infinity", result.stderr)

    def test_rejects_masked_pixel_inside_footprint(self) -> None:
        result = self._run(
            np.array([[0, 0.2, 1], [0.4, 0.5, 0.6], [0.7, 0.8, self.nodata]]),
            nodata=0.5,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("masked/invalid cells", result.stderr)

    def test_rejects_crs_shape_and_transform_mismatch(self) -> None:
        values = np.zeros((3, 3), dtype="float32")
        with self.subTest("crs"):
            result = self._run(values, crs="EPSG:4326")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CRS mismatch", result.stderr)
        with self.subTest("shape"):
            result = self._run(np.zeros((2, 3), dtype="float32"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shape mismatch", result.stderr)
        with self.subTest("transform"):
            result = self._run(values, transform=from_origin(500010, 4500000, 30, 30))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("transform mismatch", result.stderr)

    def test_rejects_multiband_candidate(self) -> None:
        result = self._run(np.zeros((2, 3, 3), dtype="float32"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one band", result.stderr)

    def test_rejects_non_float32_and_multiband_template(self) -> None:
        candidate = self.root / 'candidate.tif'
        self._write(candidate, np.zeros((3, 3), dtype='float64'))
        result = subprocess.run([sys.executable, str(VALIDATOR), str(candidate), '--template', str(self.reference)],
                                capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('float32', result.stderr)
        template = self.root / 'multi-reference.tif'
        self._write(template, np.zeros((2, 3, 3), dtype='float32'))
        self._write(candidate, np.zeros((3, 3), dtype='float32'))
        result = subprocess.run([sys.executable, str(VALIDATOR), str(candidate), '--template', str(template)],
                                capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('template must have exactly one band', result.stderr)

    def test_template_is_required_even_if_some_checks_are_available(self) -> None:
        candidate = self.root / 'candidate.tif'
        self._write(candidate, np.zeros((3, 3), dtype='float32'))
        result = subprocess.run([sys.executable, str(VALIDATOR), str(candidate)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('template required', result.stderr)


if __name__ == "__main__":
    unittest.main()
