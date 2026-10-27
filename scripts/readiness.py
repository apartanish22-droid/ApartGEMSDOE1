"""Fail-closed preflight. This is not a substitute for the shared evaluator."""
import argparse
import json
from pathlib import Path

REQUIRED = ('data/sample_submission.tif', 'data/labels.tif',
            '.cache/gems_work/feature_stack.npy', 'scripts/evaluate_holdout.py',
            'scripts/submission_writer.py', 'registry/rasters.json')


def inspect(root):
    missing = [p for p in REQUIRED if not (root / p).is_file()]
    lane = root / 'registry/lane.txt'
    lane_present = lane.is_file() and bool(lane.read_text().strip())
    # Presence alone cannot authenticate the canonical runtime, compare the full
    # registry, repair the shared writer, or establish a frozen holdout.
    return {'schema_version': 1, 'missing': missing, 'lane_present': lane_present,
            'canonical_runtime_verified': False, 'ready_for_experiment': False,
            'submission_authorized': False,
            'reason': 'Canonical runtime and scientific gates are unverified. Preflight cannot authorize a slot.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    report = inspect(args.root)
    print(json.dumps(report, indent=2))
    return 0 if report['ready_for_experiment'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
