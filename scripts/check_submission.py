"""Validate a submission GeoTIFF against the competition template (APARTGEMSDOE1 lane).

Reuses the canonical `gems32.submission.audit_geotiff` (zero private fork).
Prints the 12-point audit receipt for a `-zeros.tif` or `-nan.tif` variant.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gems32.paths import data_dir  # noqa: E402
from gems32.submission import audit_geotiff  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geotiff", type=Path, help="Submission GeoTIFF to validate")
    parser.add_argument("--template", type=Path, default=None, help="Reference template (default: data/sample_submission.tif)")
    parser.add_argument("--mode", default="zeros", choices=["zeros", "nan"])
    args = parser.parse_args()

    ddir = data_dir()
    template = args.template or (ddir / "sample_submission.tif")
    foot_template = None
    labels = None
    # Reconstruct footprint/labels from the template grid for the audit's shape checks.
    import numpy as np
    import rasterio

    with rasterio.open(template) as tpl:
        foot_template = np.isfinite(tpl.read(1))
    with rasterio.open(ddir / "labels.tif") as lab:
        labels = (lab.read(1) > 0) & foot_template

    if not args.geotiff.is_file():
        print(f"Error: {args.geotiff} does not exist", file=sys.stderr)
        return 1
    if not template.is_file():
        print(f"Error: {template} does not exist", file=sys.stderr)
        return 1

    report = audit_geotiff(args.geotiff, foot_template, labels, mode=args.mode, template_tif=template)
    print(json.dumps(report, indent=2))
    return 0 if report["all_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
