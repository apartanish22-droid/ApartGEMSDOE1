#!/usr/bin/env python3
"""
scripts/validate_submission.py

Pre-submission validation gate for a GEMS Prize Challenge GeoTIFF.
Runs without human intervention and emits a machine-readable JSON report.

Checks (all automated):
  F1. Single band, float32 dtype
  F2. All values finite (no NaN / inf) inside and outside the footprint
  F3. All values in [0, 1]          <- fixes the portal error
        "Predicted values must be in range [0, 1]"
  F4. CRS == EPSG:32611
  F5. Shape == 3730 x 3292
  F6. Geotransform: pixel size 100 m; ORIGIN match vs official template
      (UNVERIFIED if sample_submission.tif is absent - DrivenData login-gated)
  F7. Dot/count sanity and footprint coverage (informational)

Exit codes:
  0  all checks PASS (template-verified)
  1  format-fatal failure (do not upload)
  2  PASS on all checkable gates but template origin UNVERIFIED
     -> download OK for research; DO NOT upload until origin verified
       and evaluate_holdout.py reports a passing holdout-DTI.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS

HEIGHT, WIDTH = 3730, 3292
EXPECTED_CRS = "EPSG:32611"
RES_M = 100.0


def validate(path: Path, template: Path | None = None) -> dict:
    r = {
        "file": str(path),
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": {},
        "format_pass": False,
        "template_origin_verified": False,
        "verdict": None,
    }
    try:
        ds = rasterio.open(path)
    except Exception as exc:  # noqa: BLE001
        r["checks"]["open"] = False
        r["checks"]["error"] = str(exc)
        r["verdict"] = "FATAL_CANNOT_OPEN"
        return r

    with ds:
        arr = ds.read(1).astype(np.float64)
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
    # F4
    r["checks"]["crs_match"] = bool(str(ds.crs) == EXPECTED_CRS if ds.crs is not None else False)
    # F5
    r["checks"]["shape_match"] = bool(ds.height == HEIGHT and ds.width == WIDTH)
    # F6
    res_ok = bool(abs(float(ds.transform.a)) == RES_M and abs(float(ds.transform.e)) == RES_M)
    r["checks"]["resolution_100m"] = res_ok
    if template is not None and template.exists():
        with rasterio.open(template) as td:
            r["checks"]["template_crs_match"] = bool(str(ds.crs) == str(td.crs))
            r["checks"]["template_shape_match"] = bool(
                ds.height == td.height and ds.width == td.width)
            r["checks"]["template_transform_match"] = bool(
                list(ds.transform) == list(td.transform))
            r["template_origin_verified"] = bool(
                r["checks"]["template_crs_match"]
                and r["checks"]["template_shape_match"]
                and r["checks"]["template_transform_match"])
    else:
        r["checks"]["template_crs_match"] = None
        r["checks"]["template_shape_match"] = None
        r["checks"]["template_transform_match"] = None
        r["template_origin_verified"] = False
        r["checks"]["template_note"] = (
            "sample_submission.tif absent (DrivenData login-gated): geotransform origin "
            "UNVERIFIED. Obtain the official template before upload.")

    # F7 informational
    n_nonzero = int((arr > 0).any(axis=0).sum()) if arr.ndim == 2 else int((arr > 0).sum())
    r["checks"]["n_positive_cells"] = int(np.count_nonzero(arr > 0))
    r["checks"]["fraction_positive"] = float(np.count_nonzero(arr > 0) / arr.size)

    checks = r["checks"]
    fatal = not (
        checks["single_band"] and checks["float32"] and checks["all_finite"]
        and checks["in_range_0_1"] and checks["crs_match"] and checks["shape_match"]
        and res_ok
    )
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
    if len(sys.argv) < 2:
        print("usage: python scripts/validate_submission.py <file.tif> [template.tif]", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    template = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    r = validate(path, template)
    if r["verdict"] == "OK_TO_SUBMIT_FORMAT_VERIFIED":
        return 0
    if r["verdict"] == "RESEARCH_ONLY_ORIGIN_UNVERIFIED":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
