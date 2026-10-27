#!/usr/bin/env python3
"""Fail-closed GeoTIFF format/range validation against an official template.

This is not a score, uniqueness, or leakage evaluator. Requires rasterio/numpy.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, help="single-band prediction GeoTIFF")
    parser.add_argument("--template", required=True, type=Path, help="official template GeoTIFF")
    args = parser.parse_args()

    try:
        import numpy as np
        import rasterio
    except ImportError as exc:
        print(f"FAIL: required package unavailable: {exc}", file=sys.stderr)
        return 2

    for label, path in (("candidate", args.candidate), ("template", args.template)):
        if not path.is_file():
            print(f"FAIL: {label} file does not exist: {path}", file=sys.stderr)
            return 2

    try:
        with rasterio.open(args.template) as template, rasterio.open(args.candidate) as candidate:
            errors: list[str] = []
            if template.count < 1:
                errors.append("template has no raster band")
            if candidate.count != 1:
                errors.append(f"candidate must have exactly one band (found {candidate.count})")
            if candidate.width != template.width or candidate.height != template.height:
                errors.append(
                    f"shape mismatch: candidate {(candidate.height, candidate.width)}, "
                    f"template {(template.height, template.width)}"
                )
            if candidate.crs is None or template.crs is None or candidate.crs != template.crs:
                errors.append(f"CRS mismatch or missing CRS: candidate={candidate.crs}, template={template.crs}")
            if candidate.transform != template.transform:
                errors.append(f"affine transform mismatch: candidate={candidate.transform}, template={template.transform}")
            if errors:
                for error in errors:
                    print(f"FAIL: {error}", file=sys.stderr)
                return 1

            data = candidate.read(1, masked=False)
            template_mask = template.read_masks(1) > 0
            candidate_mask = candidate.read_masks(1) > 0
            footprint = template_mask
            if footprint.shape != data.shape or not footprint.any():
                print("FAIL: template valid-data footprint is empty or incompatible", file=sys.stderr)
                return 1
            if np.any(~candidate_mask[footprint]):
                print("FAIL: candidate has masked/invalid cells inside template footprint", file=sys.stderr)
                return 1
            values = data[footprint]
            if not np.isfinite(values).all():
                print("FAIL: candidate contains NaN or infinity inside template footprint", file=sys.stderr)
                return 1
            minimum = float(values.min())
            maximum = float(values.max())
            if minimum < 0.0 or maximum > 1.0:
                print(f"FAIL: prediction range outside [0,1] within footprint: [{minimum}, {maximum}]", file=sys.stderr)
                return 1
            print(
                "PASS: one band; CRS, shape and transform match; "
                f"no NaN/Inf in footprint; values in [0,1] (min={minimum:.8g}, max={maximum:.8g}); "
                f"valid footprint cells={int(footprint.sum())}. This is format validation only, not a score or uniqueness certification."
            )
            return 0
    except Exception as exc:  # rasterio reports malformed files and I/O errors here
        print(f"FAIL: could not read/validate GeoTIFF: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
