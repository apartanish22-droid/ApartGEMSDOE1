#!/usr/bin/env python3
"""
scripts/submission_writer.py

Write a GEMS Prize Challenge submission GeoTIFF that matches the submission
format: single-band GeoTIFF, float32, values in [0,1], no NaN, CRS/shape
and geotransform matching the template (sample_submission.tif).

Usage:
    python scripts/submission_writer.py \
        --scores data/submission_scores.tif \
        --out submissions/gemsdoe1-blind-conduit-<id>-zeros.tif \
        --template data/sample_submission.tif   # optional; documented fallback if absent

The writer NEVER invents a geotransform origin: if the template is absent it
falls back to the documented spec (EPSG:32611, 3730 x 3292, 100 m pixels) and
flags the origin UNVERIFIED. Such a file passes every checkable gate but MUST
be re-placed on the official template before a DrivenData upload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"

FALLBACK = {
    "crs": "EPSG:32611",
    "width": 3292,
    "height": 3730,
    "res": 100.0,
}


def _template_signature(template: Path | None):
    if template is not None and template.exists():
        with rasterio.open(template) as ds:
            return {
                "source": "official template",
                "crs": str(ds.crs) if ds.crs is not None else None,
                "width": ds.width,
                "height": ds.height,
                "transform": list(ds.transform),
                "count": ds.count,
                "dtype": str(ds.dtype),
                "origin_verified": True,
            }
    return {
        "source": "documented competition spec (FALLBACK - origin UNVERIFIED)",
        **FALLBACK,
        "transform": [FALLBACK["res"], 0.0, 0.0, 0.0, -FALLBACK["res"], 0.0],
        "origin_verified": False,
    }


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_submission(scores: np.ndarray, out_path: Path, template: Path | None = None) -> dict:
    """Write scores as a validated submission GeoTIFF.

    scores: 2D float array in [0, 1], shape must match template.
    out_path: destination .tif
    template: optional sample_submission.tif for CRS/transform.
    """
    scores = np.asarray(scores, dtype=np.float32)
    if not np.all(np.isfinite(scores)):
        raise ValueError("scores contain NaN/inf; submission must be all-finite")
    if scores.min() < 0.0 or scores.max() > 1.0:
        raise ValueError("scores outside [0, 1]; clip before writing")

    sig = _template_signature(template)
    h, w = scores.shape
    if sig["origin_verified"]:
        # Re-derive transform from template; require shape match.
        with rasterio.open(template) as ds:
            transform = ds.transform
            crs = ds.crs
        if h != sig["height"] or w != sig["width"]:
            raise ValueError(
                f"scores shape {(h, w)} != template {(sig['height'], sig['width'])}"
            )
    else:
        transform = rasterio.Affine(
            sig["transform"][0], sig["transform"][1], sig["transform"][2],
            sig["transform"][3], sig["transform"][4], sig["transform"][5],
        )
        from rasterio.crs import CRS
        crs = CRS.from_user_input(sig["crs"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "height": h,
        "width": w,
        "crs": crs,
        "transform": transform,
        "tiled": False,
        "compress": "deflate",
        "nodata": None,
    }
    with rasterio.open(out_path, "w", **profile) as ds:
        ds.write(scores, 1)
        ds.set_band_description(1, "geothermal-fault-propensity [0,1]")

    sha = _sha256(out_path)
    # Re-open and self-verify
    report = validate_geotiff(out_path, template)
    report.update({
        "path": str(out_path),
        "sha256": sha,
        "size_bytes": out_path.stat().st_size,
        "n_dots_int32": int(np.count_nonzero(scores > 0.5)),
        "value_min": float(scores.min()),
        "value_max": float(scores.max()),
        "template_signature": sig,
        "written_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    sidecar = out_path.with_suffix(".json")
    with open(sidecar, "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"[submission_writer] Wrote {out_path}  sha256={sha}")
    print(f"[submission_writer] dots(>0.5)={report['n_dots_int32']}  "
          f"range=[{report['value_min']:.6f}, {report['value_max']:.6f}]  "
          f"format_pass={report['format_pass']}")
    return report


def validate_geotiff(path: Path, template: Path | None) -> dict:
    checks = {}
    with rasterio.open(path) as ds:
        arr = ds.read(1).astype(np.float64)
        checks["crs"] = str(ds.crs) if ds.crs is not None else None
        checks["shape"] = [ds.height, ds.width]
        checks["count"] = ds.count
        checks["dtype"] = str(ds.dtype)
        checks["transform"] = list(ds.transform)
        checks["bounds"] = ds.bounds
        checks["nodata"] = ds.nodata

    finite_mask = np.isfinite(arr)
    checks["all_finite"] = bool(finite_mask.all())
    checks["n_nan"] = int(np.isnan(arr).sum())
    checks["n_inf"] = int(np.isinf(arr).sum())
    checks["value_min"] = float(arr.min())
    checks["value_max"] = float(arr.max())
    checks["in_range_0_1"] = bool((arr >= 0.0).all() and (arr <= 1.0).all())

    if template is not None and template.exists():
        with rasterio.open(template) as td:
            checks["template_shape_match"] = (ds.height == td.height and ds.width == td.width)
            checks["template_crs_match"] = str(ds.crs) == str(td.crs)
            checks["template_transform_match"] = list(ds.transform) == list(td.transform)
    else:
        checks["template_shape_match"] = None
        checks["template_crs_match"] = None
        checks["template_transform_match"] = None

    checks["format_pass"] = bool(
        checks["all_finite"]
        and checks["in_range_0_1"]
        and checks["count"] == 1
        and checks["dtype"] == "float32"
        and (checks["template_crs_match"] is not False)
        and (checks["template_shape_match"] is not False)
    )
    return checks


def main() -> int:
    ap = argparse.ArgumentParser(description="Write a GEMS submission GeoTIFF")
    ap.add_argument("--scores", required=True, help="input scores .tif (single band float [0,1])")
    ap.add_argument("--out", required=True, help="output submission .tif path")
    ap.add_argument("--template", default=None, help="optional sample_submission.tif template")
    args = ap.parse_args()

    with rasterio.open(args.scores) as ds:
        scores = ds.read(1).astype(np.float32)
    report = write_submission(scores, Path(args.out),
                              Path(args.template) if args.template else None)
    return 0 if report["format_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
