#!/usr/bin/env python3
"""Non-authorizing saved-byte check against a supplied template.

Delegates to the same raster inspector as validate_raster.py. The supplied
comparison file is not automatically authenticated as the organizer's grid.
The default policy conservatively requires masked/nodata or NaN outside the
irregular footprint; portal acceptance of this policy remains unverified.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems_audit.rasters import inspect_candidate, sha256_file, template_info  # noqa: E402


def validate(candidate: Path, template: Path) -> dict:
    result = {"candidate": str(candidate), "template": str(template),
              "sha256": None, "format_pass": False, "errors": [],
              "approved_to_submit": False, "organizer_accepted": False,
              "template_authenticity": "not established by this comparison"}
    try:
        result["sha256"] = sha256_file(candidate)
        with rasterio.open(template) as ref:
            if ref.count != 1:
                result["errors"].append(f"template must have one band (found {ref.count})")
        if not result["errors"]:
            report = inspect_candidate(candidate, template_info(template))
            result["inspection"] = report
            messages = {
                "geotiff": "candidate must be a GeoTIFF",
                "single_band": "candidate must have one band",
                "float32": "candidate must be float32",
                "crs_match": "CRS mismatch or missing CRS",
                "shape_match": "shape mismatch",
                "transform_match": "affine transform mismatch",
                "inside_all_finite": "candidate contains NaN or Inf inside the template footprint",
                "inside_in_range_0_1": "candidate values outside [0,1] inside the template footprint",
                "inside_not_nodata": "candidate masks or nodata inside the template footprint",
                "no_unmasked_positive_outside_footprint": "candidate has positive pixels outside the template footprint (array-index diagnostic if grids differ)",
            }
            result["errors"].extend(messages[name] for name, passed in report["checks"].items() if not passed)
            if report.get("strict_irregular_footprint_null") is False:
                result["errors"].append("candidate outside the template footprint must be nodata/masked or NaN")
    except (OSError, ValueError, KeyError, rasterio.errors.RasterioError) as exc:
        result["errors"].append(f"unable to inspect raster: {type(exc).__name__}: {exc}")
    result["format_pass"] = not result["errors"]
    result["status"] = "PASS_FORMAT_ONLY" if result["format_pass"] else "FAIL_FORMAT"
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--template", type=Path, required=True,
                    help="comparison grid; its origin/authenticity must be established separately")
    args = ap.parse_args()
    if not args.candidate.is_file() or not args.template.is_file():
        missing = [str(path) for path in (args.candidate, args.template) if not path.is_file()]
        print(json.dumps({"status": "BLOCKED_MISSING_FILE", "missing": missing}, indent=2))
        return 2
    report = validate(args.candidate, args.template)
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report["format_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
