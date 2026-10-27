import tempfile
import unittest
from pathlib import Path
from scripts.readiness import inspect, REQUIRED


class ReadinessTest(unittest.TestCase):
    def test_empty_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            r = inspect(Path(d))
            self.assertEqual(r['missing'], list(REQUIRED))
            self.assertFalse(r['ready_for_experiment'])
            self.assertFalse(r['submission_authorized'])

    def test_lane_required_even_with_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in REQUIRED:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.touch()
            self.assertFalse(inspect(root)['ready_for_experiment'])
            (root / 'registry/lane.txt').write_text('')
            self.assertFalse(inspect(root)['ready_for_experiment'])
            (root / 'registry/lane.txt').write_text('assigned method')
            self.assertTrue(inspect(root)['ready_for_experiment'])
            self.assertFalse(inspect(root)['submission_authorized'])
