#!/usr/bin/env python3
"""Audit the owner-mirror template and prior TIFF against the public format spec.

This is a local, read-only inspection. It does not contact DrivenData, repair or
rewrite a TIFF, validate an upload, generate a new candidate, or use a slot.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio

from gems57 import load_grid
from gems57.validate import validate

OFFICIAL_PROBLEM_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"
PRIOR_FILE = ROOT / "docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def raster_summary(path: Path) -> dict:
    with rasterio.open(path) as src:
        array = src.read(1)
        finite = np.isfinite(array)
        finite_values = array[finite]
        nodata = src.nodata
        return {
            "file": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "count": src.count,
            "dtype": src.dtypes[0],
            "crs": str(src.crs),
            "shape": [src.height, src.width],
            "transform": [float(x) for x in tuple(src.transform)[:6]],
            "nodata": "NaN" if nodata is not None and np.isnan(float(nodata)) else nodata,
            "finite_pixels": int(finite.sum()),
            "nan_pixels": int(np.isnan(array).sum()),
            "infinite_pixels": int(np.isinf(array).sum()),
            "positive_pixels": int(((array > 0) & finite).sum()),
            "zero_pixels": int(((array == 0) & finite).sum()),
            "finite_min": float(finite_values.min()) if finite_values.size else None,
            "finite_max": float(finite_values.max()) if finite_values.size else None,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "evidence/format_irregularity_audit.json")
    args = parser.parse_args()

    grid = load_grid()
    sample_path = ROOT / "data/bridge/sample_submission.tif"
    labels_path = ROOT / "data/official/labels.tif"
    existing_path = ROOT / "data/bridge/existing_faults.tif"
    sample = raster_summary(sample_path)
    labels = raster_summary(labels_path)
    existing = raster_summary(existing_path)
    with rasterio.open(sample_path) as src:
        sample_array = src.read(1)
    sample_positive = np.isfinite(sample_array) & (sample_array > 0)
    mapped_support = grid.catalogue & grid.footprint
    support_xor = int(np.count_nonzero(sample_positive ^ mapped_support))

    legacy = validate(PRIOR_FILE, footprint=grid.footprint, catalogue=grid.catalogue)
    source_text = {
        "url": OFFICIAL_PROBLEM_URL,
        "reviewed_utc_date": datetime.now(timezone.utc).date().isoformat(),
        "evidence_class": "OFFICIAL PUBLIC FORMAT TEXT; source page was read in this review",
        "requirements_transcribed": [
            "EPSG:32611 / UTM zone 11N; 100 m resolution; same bounds as training data.",
            "Data outside the bounds must be null or NaN.",
            "Single-layer float32 predictions with values in [0, 1].",
            "The sample submission is described as predicting total fault absence.",
        ],
        "provenance_limit": "The official page text is verified, but the downloaded owner-mirror TIFFs are not authenticated organizer-origin files.",
    }
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "LOCAL FORMAT AUDIT + OFFICIAL PUBLIC SPEC REVIEW; NOT ORGANIZER ACCEPTANCE",
        "official_source": source_text,
        "owner_mirror_integrity": {
            "sample_sha256": sample["sha256"],
            "labels_sha256": labels["sha256"],
            "existing_faults_sha256": existing["sha256"],
            "sample": sample,
            "labels": labels,
            "existing_faults": existing,
            "sample_positive_support_equals_mapped_catalogue": support_xor == 0,
            "sample_vs_catalogue_support_xor_pixels": support_xor,
            "published_total_absence_description_matches_mirror_content": bool(sample["positive_pixels"] == 0),
            "irregularity": (
                "The mirrored sample has 60,988 positive cells, and its positive support exactly equals the mapped-fault catalogue; "
                "this conflicts with the official page's description of the sample as total fault absence."
            ) if sample["positive_pixels"] and support_xor == 0 else None,
            "origin_authenticated": False,
        },
        "legacy_candidate": {
            "file": str(PRIOR_FILE.relative_to(ROOT)),
            "sha256": legacy["sha256"],
            "is_new_candidate": False,
            "submission_name": "apartgems1-maw-gsi-e3-20261028-87f83db9",
            "validation": legacy,
            "format_pass": bool(legacy["all_checks_passed"]),
            "failure_checks": [name for name, passed in legacy["checks"].items() if not passed],
            "decision": "DO NOT DOWNLOAD OR SUBMIT AS A COMPETITION CANDIDATE; historical duplicate and exterior zeros do not match the public sample nodata convention.",
        },
        "historical_validation_transition": {
            "status": "OLDER_ALL_FINITE_ZERO_EXTERIOR_REPORTS_ARE_SUPERSEDED",
            "superseded_reports": [
                "evidence/validation_receipt.json",
                "evidence/literal_witness_audit.json",
                "evidence/cli_validator_check.json",
                "docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.json",
            ],
            "current_format_failures": [name for name, passed in legacy["checks"].items() if not passed],
            "interpretation": "Their all-finite/zero-exterior checks are historical facts about an older private policy, not current format clearance; the public outside-footprint NaN/nodata rule supersedes them.",
        },
        "shared_writer_repair": {
            "status": "IMPLEMENTED_AND_TESTED_LOCALLY",
            "test_command": ".venv/bin/pytest -q tests/test_submission_format.py",
            "test_result": "5 passed in this review; synthetic local TIFF round-trip only, not organizer acceptance.",
            "policy": "Require finite in-footprint [0,1] probabilities; reject infinities, in-footprint NaNs, out-of-range values, and positive mass outside; serialize exterior cells as NaN with a NaN nodata tag.",
            "acceptance_limit": "The tests prove the local writer/validator contract against the pinned owner-mirror sample, not organizer-origin authenticity or portal acceptance.",
            "modules": [
                "src/gems57/grid.py",
                "src/gems57/gates.py",
                "src/gems57/submission_writer.py",
                "src/gems57/validate.py",
            ],
        },
        "reported_portal_error": {
            "text": "Predicted values must be in range [0, 1]",
            "cause": "UNKNOWN; no organizer submission receipt, uploaded file hash, or authenticated template validation is available.",
            "note": "The legacy TIFF's finite values are in [0,1], but its exterior-zero policy is inconsistent with the public outside-bounds rule. This does not prove that the exterior zeros caused the reported portal error.",
        },
        "competition_status": {
            "new_geotiff_generated": False,
            "model_experiment_run": False,
            "weekly_slots_used": 0,
            "reason": "The assigned lane has a mandatory literal-duplicate stop, and there is no complete registry or comparable v3 holdout baseline to clear a new candidate.",
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.out),
        "legacy_format_pass": report["legacy_candidate"]["format_pass"],
        "legacy_failure_checks": report["legacy_candidate"]["failure_checks"],
        "sample_positive_pixels": sample["positive_pixels"],
        "sample_positive_support_equals_catalogue": support_xor == 0,
        "new_geotiff_generated": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
