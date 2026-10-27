#!/usr/bin/env python3
"""Inventory locally placed data without claiming organizer authentication.

A present sample supplies a tentative grid signature, but file existence is not
proof of source, lane readiness or a valid holdout. The hash-pinned owner mirror
is restored separately by ``bootstrap_shared_data.py``. This script writes an
inventory to data/ and never grants training or submission approval.
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
            "dtype": str(ds.dtypes[0]),
            "transform": list(ds.transform),
            "res": ds.res,
            "origin": (ds.transform.c, ds.transform.f),
            "nodata": (None if ds.nodata is None else
                       (float(ds.nodata) if np.isfinite(ds.nodata) else str(ds.nodata))),
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
            "source": "local sample_submission.tif (organizer provenance not established)",
            "crs": template["crs"],
            "width": template["width"],
            "height": template["height"],
            "transform": template["transform"],
            "count": template["count"],
            "dtype": template["dtype"],
            "origin_verified": False,
        }
        print("[prepare_data] Local template found; organizer origin is not independently authenticated.")
    else:
        audit["template_signature"] = {
            "source": "documented competition spec (FALLBACK)",
            **FALLBACK,
            "origin_verified": False,
        }
        print("[prepare_data] WARNING: sample_submission.tif not present (DrivenData login-gated).")
        print("[prepare_data] Using documented fallback spec; GEOTRANSFORM ORIGIN IS UNVERIFIED.")
        print("[prepare_data] Copy sample_submission.tif into data/ and re-run to verify.")

    audit["input_files_present"] = all(
        audit["files"][k]["present"] for k in ("training_features", "labels", "sample_submission")
    )
    # File existence alone cannot establish an assigned lane, verified origin,
    # complete registry, leakage controls or holdout readiness.
    audit["ready_for_training"] = False
    audit["ready_for_validation"] = bool(template.get("present"))
    audit["note"] = "A local template permits comparison only; it does not authenticate provenance or authorize a submission."

    out = DATA / "prepare_data.json"
    with open(out, "w") as fh:
        json.dump(audit, fh, indent=2)
    print(f"[prepare_data] Wrote {out}")
    print(f"[prepare_data] ready_for_training={audit['ready_for_training']}")
    return 0 if audit["ready_for_training"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
