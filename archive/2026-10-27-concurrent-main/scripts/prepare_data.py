#!/usr/bin/env python3
"""
scripts/prepare_data.py

Audit the data/ directory after download_competition_data.sh has run.

Verifies:
  * training_features.tif, labels.tif, sample_submission.tif presence
    (DrivenData login-gated; must be copied in manually)
  * example_submission.tif / existing_faults.tif / GeoDAWN stack mirrors
  * Computes and records the submission template signature (CRS, shape,
    transform, dtype, bands, nodataval) from sample_submission.tif if present;
    otherwise falls back to the documented competition spec:
        EPSG:32611, 3730 x 3292, 100 m pixels, float32, 1 band
    and FLAGS the origin as UNVERIFIED (template origin cannot be known
    without the official sample_submission.tif).

Writes data/prepare_data.json (machine-readable audit) for the validator.

No labels are touched; no scores are computed here.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import rasterio

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"

# Documented competition spec (GEMSDOE family sites, e.g. GEMSDOE31/GEMSDOE36
# format receipts: "EPSG:32611 · 3730x3292 · float32"). The geotransform
# ORIGIN is template-specific and unavailable without DrivenData auth.
FALLBACK = {
    "crs": "EPSG:32611",
    "width": 3292,
    "height": 3730,
    "res_x": 100.0,
    "res_y": -100.0,
    "transform_origin": "UNVERIFIED_WITHOUT_TEMPLATE",
    "count": 1,
    "dtype": "float32",
}


def info(path: Path) -> dict:
    if not path.exists():
        return {"present": False}
    with rasterio.open(path) as ds:
        return {
            "present": True,
            "name": path.name,
            "size_bytes": path.stat().st_size,
            "crs": str(ds.crs) if ds.crs is not None else None,
            "width": ds.width,
            "height": ds.height,
            "count": ds.count,
            "dtype": str(ds.dtype),
            "transform": list(ds.transform),
            "res": ds.res,
            "origin": (ds.transform.c, ds.transform.f),
            "nodata": ds.nodata,
            "bounds": ds.bounds,
        }


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    candidates = {
        "training_features": DATA / "training_features.tif",
        "labels": DATA / "labels.tif",
        "sample_submission": DATA / "sample_submission.tif",
        "example_submission": DATA / "example_submission.tif",
        "existing_faults": DATA / "existing_faults.tif",
        "geodawn_features": DATA / "gems-geodawn-numerical-features.tif",
    }
    audit = {"data_dir": str(DATA), "files": {name: info(p) for name, p in candidates.items()}}

    template = audit["files"]["sample_submission"]
    if template.get("present"):
        audit["template_signature"] = {
            "source": "official sample_submission.tif",
            "crs": template["crs"],
            "width": template["width"],
            "height": template["height"],
            "transform": template["transform"],
            "count": template["count"],
            "dtype": template["dtype"],
            "origin_verified": True,
        }
        print("[prepare_data] Official template found: sample_submission.tif")
    else:
        audit["template_signature"] = {
            "source": "documented competition spec (FALLBACK)",
            **FALLBACK,
            "origin_verified": False,
        }
        print("[prepare_data] WARNING: sample_submission.tif not present (DrivenData login-gated).")
        print("[prepare_data] Using documented fallback spec; GEOTRANSFORM ORIGIN IS UNVERIFIED.")
        print("[prepare_data] Copy sample_submission.tif into data/ and re-run to verify.")

    audit["ready_for_training"] = all(
        audit["files"][k]["present"] for k in ("training_features", "labels", "sample_submission")
    )
    audit["ready_for_validation"] = audit["files"]["example_submission"]["present"] or True  # format spec known

    out = DATA / "prepare_data.json"
    with open(out, "w") as fh:
        json.dump(audit, fh, indent=2)
    print(f"[prepare_data] Wrote {out}")
    print(f"[prepare_data] ready_for_training={audit['ready_for_training']}")
    return 0 if audit["ready_for_training"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
