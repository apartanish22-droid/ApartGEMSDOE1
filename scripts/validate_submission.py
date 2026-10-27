#!/usr/bin/env python3
"""Check a candidate against a supplied template; this does not authorize upload.

This compatibility CLI delegates to the same saved-byte inspector as
``validate_raster.py``. It accepts an arbitrary template for local diagnostics,
but does not authenticate it or assert organizer acceptance. For a pinned
owner-mirror check, use ``scripts/validate_raster.py`` instead.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems_audit.rasters import inspect_candidate, template_info  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--template", type=Path, required=True,
                    help="comparison grid; provenance must be established separately")
    args = ap.parse_args()
    try:
        report = inspect_candidate(args.candidate, template_info(args.template))
    except (OSError, ValueError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    messages = {
        "geotiff": "candidate is not a GeoTIFF",
        "single_band": "expected exactly one band",
        "float32": "candidate is not float32",
        "crs_match": "CRS mismatch",
        "shape_match": "shape mismatch",
        "transform_match": "transform mismatch",
        "inside_all_finite": "NaN or infinity inside footprint",
        "inside_in_range_0_1": "values outside [0,1] inside footprint",
        "inside_not_nodata": "masked/invalid cells inside footprint",
        "no_unmasked_positive_outside_footprint": "positive cells outside footprint (index comparison if grids differ)",
    }
    failures = [messages[name] for name, passed in report["checks"].items() if not passed]
    if failures:
        print("FAIL: " + "; ".join(failures), file=sys.stderr)
        print(f"sha256={report['sha256']}; upload NOT authorized")
        return 1
    print(f"PASS: basic saved-byte checks; min={report['inside_min']:.8g} "
          f"max={report['inside_max']:.8g}; sha256={report['sha256']}")
    print("Template provenance, outside encoding, uniqueness, holdout and organizer acceptance are not established; upload NOT authorized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
