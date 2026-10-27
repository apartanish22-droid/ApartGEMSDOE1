#!/usr/bin/env python3
"""Fail-closed format check against an authoritative sample GeoTIFF.

This validates serialized file format only. It does not test science, holdout
performance, leakage, novelty, or competition eligibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import rasterio


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(candidate: Path, template: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "candidate": str(candidate),
        "template": str(template),
        "sha256": None,
        "format_pass": False,
        "errors": [],
    }
    try:
        report["sha256"] = sha256_file(candidate)
        with rasterio.open(candidate) as src, rasterio.open(template) as ref:
            report["candidate_grid"] = {
                "crs": str(src.crs) if src.crs is not None else None,
                "shape": [int(src.height), int(src.width)],
                "transform": list(src.transform),
                "count": int(src.count),
                "dtype": list(src.dtypes),
            }
            report["template_grid"] = {
                "crs": str(ref.crs) if ref.crs is not None else None,
                "shape": [int(ref.height), int(ref.width)],
                "transform": list(ref.transform),
                "count": int(ref.count),
            }

            errors: list[str] = report["errors"]
            if ref.count != 1:
                errors.append(f"template must have one band (found {ref.count})")
            if src.count != 1:
                errors.append(f"candidate must have one band (found {src.count})")
            elif src.dtypes[0] != "float32":
                errors.append(f"candidate must be float32 (found {src.dtypes[0]})")
            if src.crs is None or ref.crs is None or src.crs != ref.crs:
                errors.append(f"CRS mismatch or missing CRS: candidate={src.crs}, template={ref.crs}")
            if (src.height, src.width) != (ref.height, ref.width):
                errors.append(
                    f"shape mismatch: candidate={(src.height, src.width)}, "
                    f"template={(ref.height, ref.width)}"
                )
            if src.transform != ref.transform:
                errors.append(f"affine transform mismatch: candidate={src.transform}, template={ref.transform}")

            if not errors:
                values = src.read(1, masked=False)
                candidate_valid = src.read_masks(1) > 0
                template_values = ref.read(1, masked=False)
                footprint = (ref.read_masks(1) > 0) & np.isfinite(template_values)
                if footprint.shape != values.shape or not footprint.any():
                    errors.append("template has no usable footprint matching candidate shape")
                else:
                    inside = values[footprint]
                    inside_valid = candidate_valid[footprint]
                    if not inside_valid.all():
                        errors.append("candidate masks or nodata inside the template footprint")
                    if not np.isfinite(inside).all():
                        errors.append("candidate contains NaN or Inf inside the template footprint")
                    elif not ((inside >= 0.0).all() and (inside <= 1.0).all()):
                        errors.append("candidate values outside [0,1] inside the template footprint")

                    outside = ~footprint
                    if outside.any():
                        outside_is_null = (~candidate_valid | np.isnan(values))
                        if not outside_is_null[outside].all():
                            errors.append("candidate outside the template footprint must be nodata/masked or NaN")
                    finite_inside = inside[np.isfinite(inside)]
                    report["footprint"] = {
                        "valid_cells": int(footprint.sum()),
                        "outside_cells": int(outside.sum()),
                        "nan_inside": int(np.isnan(inside).sum()),
                        "inf_inside": int(np.isinf(inside).sum()),
                        "min_inside": float(finite_inside.min()) if finite_inside.size else None,
                        "max_inside": float(finite_inside.max()) if finite_inside.size else None,
                    }
    except Exception as exc:  # report malformed/unreadable input as a failed gate
        report["errors"].append(f"unable to inspect raster: {type(exc).__name__}: {exc}")

    report["format_pass"] = not report["errors"]
    report["status"] = "PASS_FORMAT_ONLY" if report["format_pass"] else "FAIL_FORMAT"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--template", required=True, type=Path,
                        help="authoritative official sample_submission.tif")
    args = parser.parse_args(argv)
    if not args.candidate.is_file() or not args.template.is_file():
        missing = [str(path) for path in (args.candidate, args.template) if not path.is_file()]
        print(json.dumps({"status": "BLOCKED_MISSING_FILE", "missing": missing}, indent=2))
        return 2
    report = validate(args.candidate, args.template)
    print(json.dumps(report, indent=2))
    return 0 if report["format_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
