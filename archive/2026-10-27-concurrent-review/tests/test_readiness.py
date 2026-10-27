import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from scripts.prepare_data import inspect_data
from scripts.readiness import REQUIRED, inspect


class ReadinessTest(unittest.TestCase):
    def test_empty_repository_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            report = inspect(Path(directory))
            self.assertEqual(report["missing"], list(REQUIRED))
            self.assertFalse(report["all_required_paths_present"])
            self.assertFalse(report["ready_for_experiment"])
            self.assertFalse(report["submission_authorized"])

    def test_path_presence_never_means_verified_or_authorized(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in REQUIRED:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("placeholder")
            report = inspect(root)
            self.assertTrue(report["all_required_paths_present"])
            self.assertTrue(report["lane_present"])
            self.assertFalse(report["ready_for_experiment"])
            self.assertFalse(report["submission_authorized"])
            self.assertIn("provenance", report["reason"])

    def test_prepare_data_does_not_claim_validation_without_template_and_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = inspect_data(root)
            self.assertFalse(report["ready_for_template_validation"])
            self.assertFalse(report["ready_for_training_inputs"])
            self.assertFalse(report["template_signature"]["origin_verified"])
            self.assertFalse(report["submission_authorized"])

    def test_prepare_data_template_validation_requires_both_saved_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = {
                "driver": "GTiff", "height": 2, "width": 2, "count": 1,
                "dtype": "float32", "crs": "EPSG:32611",
                "transform": from_origin(500000, 4500000, 100, 100),
            }
            with rasterio.open(root / "sample_submission.tif", "w", **profile) as dst:
                dst.write(np.zeros((2, 2), dtype=np.float32), 1)
            report = inspect_data(root)
            self.assertFalse(report["ready_for_template_validation"])
            with rasterio.open(root / "candidate.tif", "w", **profile) as dst:
                dst.write(np.full((2, 2), 0.5, dtype=np.float32), 1)
            report = inspect_data(root)
            self.assertTrue(report["ready_for_template_validation"])
            self.assertFalse(report["submission_authorized"])
            self.assertFalse(report["template_signature"]["origin_verified"])
            self.assertIn("authenticity must be verified", report["template_signature"]["source"])


if __name__ == "__main__":
    unittest.main()
