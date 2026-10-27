#!/usr/bin/env python3
"""
scripts/validate_submission.py

Pre-submission validation gate for a GEMS Prize Challenge GeoTIFF.
Runs without human intervention and emits a machine-readable JSON report.

Modes:
  * With --template (official sample_submission.tif): exact CRS / shape /
    affine-transform match against the template, finite [0,1] values inside
    the template footprint (fail-closed, same semantics as main's validator).
  * Without --template: documented competition fallback spec
    (EPSG:32611, 3730 x 3292, 100 m pixels, float32, single band, [0,1],
    all-finite); the geotransform ORIGIN is flagged UNVERIFIED because the
    official template is DrivenData login-gated.

Checks (all automated):
  F1. Single band, float32 dtype
  F2. All values finite (no NaN / inf)
  F3. All values in [0, 1]          <- fixes the portal error
        "Predicted values must be in range [0, 1]"
  F4. CRS == EPSG:32611 (or template match when template given)
  F5. Shape == 3730 x 3292 (or template match when template given)
  F6. Geotransform: pixel size 100 m; origin verified only vs template
  F7. No masked/invalid cells inside the template footprint (template mode)

Exit codes:
  0  all checks PASS, template-origin verified (upload-eligible on format)
  1  format-fatal failure (do not upload)
  2  PASS on every checkable gate but template origin UNVERIFIED
     -> download OK for research; DO NOT upload until origin verified and
        evaluate_holdout.py reports a passing holdout-DTI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

HEIGHT, WIDTH = 3730, 3292
EXPECTED_CRS = "EPSG:32611"
RES_M = 100.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(candidate: Path, template: Path | None = None) -> dict:
    r = {
        "file": str(candidate),
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": {},
        "format_pass": False,
        "template_origin_verified": False,
        "verdict": None,
    }
    try:
        ds = rasterio.open(candidate)
    except Exception as exc:  # noqa: BLE001 - report unreadable files as fatal
        r["checks"]["open"] = False
        r["checks"]["error"] = str(exc)
        r["verdict"] = "FATAL_CANNOT_OPEN"
        return r

    with ds:
        arr = ds.read(1, masked=False).astype(np.float64)
        mask = ds.read_masks(1) > 0
        r["checks"]["open"] = True
        r["checks"]["crs"] = str(ds.crs) if ds.crs is not None else None
        r["checks"]["shape"] = [int(ds.height), int(ds.width)]
        r["checks"]["count"] = int(ds.count)
        r["checks"]["dtype"] = str(ds.dtypes[0])
        r["checks"]["transform"] = list(ds.transform)
        r["checks"]["res"] = [float(ds.transform.a), abs(float(ds.transform.e))]
        r["checks"]["origin"] = [float(ds.transform.c), float(ds.transform.f)]
        r["checks"]["bounds"] = ds.bounds
        r["checks"]["nodata"] = ds.nodata

    # F1
    r["checks"]["single_band"] = bool(r["checks"]["count"] == 1)
    r["checks"]["float32"] = bool(r["checks"]["dtype"] == "float32")
    # F2
    finite = np.isfinite(arr)
    r["checks"]["all_finite"] = bool(finite.all())
    r["checks"]["n_nan"] = int(np.isnan(arr).sum())
    r["checks"]["n_inf"] = int(np.isinf(arr).sum())
    # F3
    in_range = bool((arr >= 0.0).all() and (arr <= 1.0).all())
    r["checks"]["in_range_0_1"] = in_range
    r["checks"]["value_min"] = float(arr.min())
    r["checks"]["value_max"] = float(arr.max())

    if template is not None and template.exists():
        with rasterio.open(template) as td:
            t_arr = td.read(1, masked=False)
            t_mask = td.read_masks(1) > 0
            r["checks"]["template_crs_match"] = bool(
                ds.crs is not None and td.crs is not None and ds.crs == td.crs)
            r["checks"]["template_shape_match"] = bool(
                ds.height == td.height and ds.width == td.width)
            r["checks"]["template_transform_match"] = bool(
                list(ds.transform) == list(td.transform))
            r["template_origin_verified"] = bool(
                r["checks"]["template_crs_match"]
                and r["checks"]["template_shape_match"]
                and r["checks"]["template_transform_match"])
            # F7: masked/invalid cells inside template footprint
            footprint = t_mask
            if footprint.shape != arr.shape or not footprint.any():
                r["checks"]["template_footprint_ok"] = False
            else:
                r["checks"]["template_footprint_ok"] = True
                inside = arr[footprint]
                r["checks"]["finite_in_footprint"] = bool(np.isfinite(inside).all())
                r["checks"]["in_range_in_footprint"] = bool(
                    (inside >= 0.0).all() and (inside <= 1.0).all())
                r["checks"]["masked_cells_in_footprint"] = int(
                    (~mask[footprint]).sum())
            r["checks"]["crs"] = str(td.crs) if td.crs is not None else None
            r["checks"]["shape"] = [int(td.height), int(td.width)]
            r["checks"]["transform"] = list(td.transform)
            r["checks"]["res"] = [float(td.transform.a), abs(float(td.transform.e))]
            r["checks"]["origin"] = [float(td.transform.c), float(td.transform.f)]
    else:
        r["checks"]["template_crs_match"] = None
        r["checks"]["template_shape_match"] = None
        r["checks"]["template_transform_match"] = None
        r["checks"]["template_footprint_ok"] = None
        r["template_origin_verified"] = False
        r["checks"]["template_note"] = (
            "sample_submission.tif absent (DrivenData login-gated): geotransform origin "
            "UNVERIFIED. Obtain the official template before upload.")
        r["checks"]["crs_match"] = bool(str(ds.crs) == EXPECTED_CRS if ds.crs is not None else False)
        r["checks"]["shape_match"] = bool(ds.height == HEIGHT and ds.width == WIDTH)
        r["checks"]["resolution_100m"] = bool(
            abs(float(ds.transform.a)) == RES_M and abs(float(ds.transform.e)) == RES_M)

    # Fallback-mode CRS/shape/res when no template
    if template is None or not template.exists():
        r["checks"]["crs_match"] = bool(str(ds.crs) == EXPECTED_CRS if ds.crs is not None else False)
        r["checks"]["shape_match"] = bool(ds.height == HEIGHT and ds.width == WIDTH)
        r["checks"]["resolution_100m"] = bool(
            abs(float(ds.transform.a)) == RES_M and abs(float(ds.transform.e)) == RES_M)

    n_positive = int(np.count_nonzero(arr > 0))
    r["checks"]["n_positive_cells"] = n_positive
    r["checks"]["fraction_positive"] = float(n_positive / arr.size)

    checks = r["checks"]
    fatal = not (
        checks["single_band"] and checks["float32"] and checks["all_finite"]
        and checks["in_range_0_1"]
        and (checks.get("crs_match", True) is not False)
        and (checks.get("shape_match", True) is not False)
        and (checks.get("resolution_100m", True) is not False)
        and (checks.get("template_footprint_ok", True) is not False)
        and (checks.get("finite_in_footprint", True) is not False)
        and (checks.get("in_range_in_footprint", True) is not False)
    )
    if template is not None and template.exists():
        fatal = fatal or not (
            checks["template_crs_match"] and checks["template_shape_match"]
            and checks["template_transform_match"])
    checks["format_pass"] = not fatal
    r["format_pass"] = not fatal

    if fatal:
        r["verdict"] = "DO_NOT_SUBMIT_FORMAT_FAILURE"
    elif not r["template_origin_verified"]:
        r["verdict"] = "RESEARCH_ONLY_ORIGIN_UNVERIFIED"
    else:
        r["verdict"] = "OK_TO_SUBMIT_FORMAT_VERIFIED"

    print(json.dumps(r, indent=2))
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path, help="candidate prediction GeoTIFF")
    ap.add_argument("--template", type=Path, default=None,
                    help="official template GeoTIFF (sample_submission.tif)")
    args = ap.parse_args()

    if not args.candidate.is_file():
        print(f"FAIL: candidate file does not exist: {args.candidate}", file=sys.stderr)
        return 2
    if args.template is not None and not args.template.is_file():
        print(f"FAIL: template file does not exist: {args.template}", file=sys.stderr)
        return 2

    try:
        import numpy as np  # noqa: F401
        import rasterio  # noqa: F401
    except ImportError as exc:
        print(f"FAIL: required package unavailable: {exc}", file=sys.stderr)
        return 2

    r = validate(args.candidate, args.template)
    if r["verdict"] == "OK_TO_SUBMIT_FORMAT_VERIFIED":
        return 0
    if r["verdict"] == "RESEARCH_ONLY_ORIGIN_UNVERIFIED":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
