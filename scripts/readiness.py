#!/usr/bin/env python3
"""Existence preflight only; it never declares experiment or slot readiness."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED = (
    "data/sample_submission.tif",
    "data/labels.tif",
    ".cache/gems_work/feature_stack.npy",
    "registry/rasters.json",
    "registry/lane.txt",
    # These locations are for the canonical runtime, not root demo scripts.
    "src/gems32/evaluate_holdout.py",
    "src/gems32/submission_writer.py",
)


def inspect(root: Path) -> dict[str, Any]:
    missing = [path for path in REQUIRED if not (root / path).is_file()]
    lane = root / "registry/lane.txt"
    lane_present = lane.is_file() and bool(lane.read_text().strip())
    all_paths_present = not missing and lane_present
    return {
        "schema_version": 3,
        "missing": missing,
        "lane_present": lane_present,
        "all_required_paths_present": all_paths_present,
        "canonical_runtime_verified": False,
        "ready_for_experiment": False,
        "ready_for_template_validation": (root / "data/sample_submission.tif").is_file(),
        "submission_authorized": False,
        "reason": (
            "File presence is not provenance or protocol validation. Verify the "
            "lane, official data/template, canonical runtime, registry, and experiment design; a "
            "separate selector must authorize any submission slot."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    report = inspect(args.root)
    print(json.dumps(report, indent=2))
    return 0 if report["ready_for_experiment"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
