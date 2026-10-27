#!/usr/bin/env python3
"""Read-only forensic intake of the already-generated parallel H2 artifact.

No generation, tuning, holdout evaluation or slot selection. A single pinned
registry witness is sufficient to reject a promotion under the literal rule.
A calibration control is NOT exempted. This is not a claim of copied physics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.footprint import load_footprint, write_template  # noqa: E402
from gems.novelty import dot_overlap, is_duplicate  # noqa: E402
from restore_data import restore_blob  # noqa: E402
from validate_submission import validate  # noqa: E402

ORIGINAL_COMMIT = "570be4bab6634ffece60104e9abcbf406f98a863"
ORIGINAL_CARD = ROOT / "archive/2026-10-27-parallel-review-and-h2/run-card.json"
WITNESS_ID = "GEMSDOE24:inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inspect(*, allow_download: bool = True) -> dict:
    card = json.loads(ORIGINAL_CARD.read_text())
    candidate = ROOT / card["submission"]["file"]
    candidate.resolve().relative_to((ROOT / "docs/downloads").resolve())
    expected = card["raster_sha256"]["zeros_tif"]
    if sha256(candidate) != expected:
        raise ValueError("Parallel H2 bytes differ from the original card; no audit or promotion")
    registry = json.loads((ROOT / "evidence/registry.json").read_text())
    witness = next(e for e in registry["entries"] if e["id"] == WITNESS_ID)
    witness_path = ROOT / witness["cache_path"]
    if not witness_path.exists():
        if not allow_download:
            raise FileNotFoundError("Pinned witness is not cached; allow its integrity-checked restoration")
        restore_blob(witness["repo"], {"sha": witness["blob_sha"], "size": witness["bytes"]}, witness_path)
    if sha256(witness_path) != witness["sha256"]:
        raise ValueError("Registry witness SHA-256 mismatch")
    fp = load_footprint()
    with rasterio.open(candidate) as src, rasterio.open(witness_path) as ref:
        if (src.count != 1 or ref.count != 1 or src.shape != fp.shape
                or src.shape != ref.shape or src.crs != ref.crs or src.transform != ref.transform):
            raise ValueError("Intake rasters are not single-band, aligned to the pinned footprint")
        values, reference = src.read(1), ref.read(1)
        if not np.isfinite(values[fp]).all() or not np.isfinite(reference[fp]).all():
            raise ValueError("Nonfinite values inside the mirrored footprint")
        points = (values > 0) & fp
        reference_points = (reference > 0) & fp
    overlap = dot_overlap(points, reference_points, radius_px=3.0)
    duplicate = is_duplicate(None, overlap["candidate_within_3px_of_reference"])
    if not duplicate:
        raise ValueError("Recorded rejection no longer reproduced; fail closed, never auto-promote")
    # A technical format check does not evaluate a hypothesis or re-run holdout.
    with tempfile.TemporaryDirectory() as directory:
        template = Path(directory) / "template.tif"
        write_template(template)
        formatting = validate(candidate, template)
    count = int(points.sum())
    fleet = json.loads((ROOT / "evidence/fleet_audit.json").read_text())
    if fleet["lattice"]["sha256"] != witness["sha256"]:
        raise ValueError("Independent geometric bound has a different witness")
    uncovered = fleet["lattice"]["uncovered_footprint_pixels"]
    return {
        "schema_version": 1,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "checker_sha256": sha256(Path(__file__)),
        "evidence_class": "MEASURED GEOMETRY AND FORMAT; NOT A PERFORMANCE SCORE",
        "scope": "Already-generated parallel H2 intake only; not an AP1 experiment, retune or holdout evaluation",
        "original_commit": ORIGINAL_COMMIT,
        "original_card_path": str(ORIGINAL_CARD.relative_to(ROOT)),
        "original_card_sha256": sha256(ORIGINAL_CARD),
        "original_card_url": f"https://github.com/apartanish22-droid/ApartGEMSDOE1/blob/{ORIGINAL_COMMIT}/run-card.json",
        "original_promotion": card["submission"]["verdict"],
        "original_declared_max_overlap": card["registry"]["max_our_dots_within_3px_of_registry_dots"],
        "original_separately_listed_control": card["registry"]["degenerate_reference_logged"],
        "candidate": str(candidate.relative_to(ROOT)),
        "raster_sha256": expected,
        "requested_filename_budget": 44090,
        "actual_positive_pixels": count,
        "original_validator_positive_pixels": card["validator"]["emitted_positive_pixels"],
        "original_validator_count_matches": count == card["validator"]["emitted_positive_pixels"],
        "witness": {k: witness[k] for k in ("id", "ref", "sha256", "source_url", "positive_pixels")},
        "directional_overlap": overlap,
        "independent_geometry_lower_bound": max(0, count - uncovered) / count,
        "duplicate_stop": duplicate,
        "controls_exempted": False,
        "stopped_after_first_witness": True,
        "rank_correlation": None,
        "rank_correlation_reason": "Not recomputed: the first final-dot witness independently mandates STOP",
        "holdout_recomputed": False,
        "new_experiments": 0,
        "slots_selected_or_uploaded": 0,
        "format": formatting,
        "organizer_acceptance_tested": False,
        "verdict": "negative",
        "submission_authorized": False,
        "interpretation": "Reject original promotion under the user's no-exemption overlap rule. High lattice overlap is not proof of copied geology or physics. Original H2 holdout claims are preserved, not independently validated or compared with AP1. The original validator count is checked against the actual bytes; its 40,308 declaration differs from this file's 44,090 positive pixels.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=ROOT / "evidence/parallel-intake.json")
    parser.add_argument("--offline", action="store_true", help="Never restore a missing registry witness")
    args = parser.parse_args()
    report = inspect(allow_download=not args.offline)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"H2 intake: NEGATIVE; {report['actual_positive_pixels']} positive pixels; "
          f"overlap {report['directional_overlap']['candidate_within_3px_of_reference']:.6f}; "
          f"local format pass {report['format']['format_pass']}; no slot authorized")


if __name__ == "__main__":
    main()
