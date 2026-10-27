#!/usr/bin/env python3
"""Format inspection only: this command NEVER authorizes a competition upload.

The normative competition check is the byte-pinned shared gems.submission
checker. Relative-template checks are also exposed for small unit fixtures;
passing an arbitrary reference is explicitly NOT verified competition format.
Missing templates are errors, never a fabricated origin or synthetic grid.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.submission import check_variants  # noqa: E402 — shared authority, not a metric/writer fork


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def json_safe(value):
    """Failed rasters may have Inf mass; reports must still be strict JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_safe(item) for item in value]
    return value


def validate(candidate: Path, template: Path | None = None) -> dict:
    candidate = Path(candidate)
    report = {"file": str(candidate), "format_pass": False,
              "competition_format_verified": False, "relative_template_pass": False, "submission_authorized": False, "organizer_acceptance_tested": False,
              "verdict": "DO_NOT_SUBMIT", "errors": [], "checks": {},
              "slot_approved": False, "organizer_acceptance_established": False, "template_organizer_authenticated": None}
    if template is None:
        report["errors"].append("template required; no implicit or guessed-grid fallback")
        return report
    template = Path(template)
    if not candidate.is_file() or not template.is_file():
        report["errors"].append("Candidate and an existing template are required; run scripts/restore_data.py for pinned public mirrors.")
        return report
    try:
        with rasterio.open(template) as ref, rasterio.open(candidate) as ds:
            values = ds.read(1)
            valid = ds.read_masks(1) > 0
            footprint = (ref.read_masks(1) > 0) & np.isfinite(ref.read(1))
            checks = report["checks"]
            checks["template_single_band"] = ref.count == 1
            checks["single_band"] = ds.count == 1
            checks["float32"] = ds.dtypes == ("float32",)
            checks["crs_match"] = ds.crs is not None and ds.crs == ref.crs
            checks["shape_match"] = ds.shape == ref.shape
            checks["transform_match"] = ds.transform == ref.transform
            checks["nonempty_footprint"] = bool(footprint.any())
            if ds.shape == ref.shape and footprint.any():
                inside = values[footprint]
                checks["finite_inside"] = bool(np.isfinite(inside).all())
                checks["range_inside"] = bool(np.all((inside >= 0) & (inside <= 1)))
                checks["all_inside_valid"] = bool(valid[footprint].all())
                checks["exterior_null"] = bool(((~valid[~footprint]) | np.isnan(values[~footprint])).all())
                finite = inside[np.isfinite(inside)]
                report["min"] = float(finite.min()) if finite.size else None
                report["max"] = float(finite.max()) if finite.size else None
            messages = {
                "template_single_band": "template must have exactly one band",
                "single_band": "candidate must have exactly one band",
                "float32": "candidate must be float32",
                "crs_match": "CRS mismatch", "shape_match": "shape mismatch",
                "transform_match": "transform mismatch", "nonempty_footprint": "empty template footprint",
                "finite_inside": "NaN or infinity inside footprint",
                "range_inside": "predicted values outside [0,1] inside footprint",
                "all_inside_valid": "masked/invalid cells inside footprint",
                "exterior_null": "nonnull cells outside the template footprint",
            }
            report["errors"] = [messages[key] for key, passed in checks.items() if not passed]
            report["format_pass"] = bool(checks and all(checks.values()))
            checks["outside_null"] = checks.get("exterior_null", False)
            checks["inside_pixels"] = int(footprint.sum())
        # The shared check additionally rejects a self-consistent but guessed grid.
        shared = check_variants(candidate, template)
        report["shared_validator"] = shared
        report["relative_template_pass"] = report["format_pass"]
        report["competition_format_verified"] = bool(report["relative_template_pass"] and shared["format_valid"])
        report["format_pass"] = report["competition_format_verified"]
        if report["relative_template_pass"] and not report["format_pass"]:
            report["errors"].append("not the pinned competition grid/footprint; arbitrary-template self-consistency is insufficient")
        report["sha256"] = sha256_file(candidate)
        if report["format_pass"]:
            report["verdict"] = "FORMAT_ONLY_NOT_SUBMISSION_AUTHORIZATION"
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        report["format_pass"] = False
        report["competition_format_verified"] = False
        report["errors"].append(str(exc))
    return json_safe(report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--json", action="store_true", help="Only a machine-readable report")
    args = parser.parse_args()
    if args.template is None:
        print("FAIL: template required; no implicit or guessed-grid fallback", file=sys.stderr)
        return 2
    report = validate(args.candidate, args.template)
    print(json.dumps(report, indent=2, allow_nan=False))
    if not report["format_pass"]:
        print("FAIL: " + "; ".join(report["errors"]), file=sys.stderr)
        return 1
    if not args.json:
        print(f"PASS (local pinned-grid format only, NO upload approval): min={report['min']:g}, max={report['max']:g}, sha256={report['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
