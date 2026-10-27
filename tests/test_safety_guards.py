"""Ensure retired local scripts cannot score or produce a fake submission."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class SafetyGuardTests(unittest.TestCase):
    def test_noncanonical_scoring_and_writers_fail_closed(self):
        for script in ("evaluate_holdout.py", "generate_submission.py"):
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, str(REPO / "scripts" / script)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("BLOCKED", result.stderr)

    def test_canonical_shared_writer_requires_real_input(self):
        result = subprocess.run([sys.executable, str(REPO / "scripts/submission_writer.py")],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("required", result.stderr)
        # The writer is not a retired origin-fabricating stub anymore. Its exact
        # shared-template hash is enforced by test_shared_template_bytes_unchanged.


if __name__ == "__main__":
    unittest.main()
