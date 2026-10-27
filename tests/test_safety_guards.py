"""Ensure retired local scripts cannot score or produce a fake submission."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class SafetyGuardTests(unittest.TestCase):
    def test_noncanonical_scoring_and_writers_fail_closed(self):
        for script in ("evaluate_holdout.py", "submission_writer.py", "generate_submission.py"):
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, str(REPO / "scripts" / script)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("BLOCKED", result.stderr)


if __name__ == "__main__":
    unittest.main()
