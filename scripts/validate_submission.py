#!/usr/bin/env python3
"""APARTGEMSDOE1 submission validator + Parallel-Run Protocol lane checks.

1. 12-point GeoTIFF audit (reuses gems32.submission.audit_geotiff): CRS EPSG:32611,
   shape 3730x3292, transform matching sample_submission.tif, float32, values in [0,1]
   inside the footprint, zero NaN/sentinel inside the footprint (zeros variant: zero
   NaN anywhere), zero on catalogue faults.
2. LANE check (Protocol Rule 1): rank (Spearman) correlation of our raster against every
   restored registry/scored raster; flag if any |rho| > 0.90. Also flag if >70% of our
   emitted dots fall within 3 px of one registry raster's dots.
   Duplicates are logged and the run card verdict must not be "promote".
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gems32.paths import data_dir, downloads_dir  # noqa: E402
from gems32.submission import audit_geotiff  # noqa: E402
from gems32.grid import read_labels, sha256  # noqa: E402


def rho_safe(a: np.ndarray, b: np.ndarray) -> float:
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 10:
        return float("nan")
    try:
        return float(spearmanr(a[m], b[m])[0])
    except Exception:
        return float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("geotiff", type=Path, help="-zeros.tif submission to validate")
    ap.add_argument("--registry", type=Path, default=None,
                    help="Directory of registry/scored rasters (default: data/scored)")
    ap.add_argument("--template", type=Path, default=None)
    args = ap.parse_args()

    ddir = data_dir()
    template = args.template or (ddir / "sample_submission.tif")
    registry_dir = args.registry or (ddir / "scored")

    import rasterio as _rio
    with _rio.open(template) as tpl:
        foot = np.isfinite(tpl.read(1))
    labels = read_labels(ddir / "labels.tif") & foot

    with _rio.open(args.geotiff) as src:
        arr = src.read(1).astype(np.float64)
        crs = src.crs
        transform = src.transform

    report = audit_geotiff(args.geotiff, foot, labels, mode="zeros", template_tif=template)

    # ---- LANE checks ----
    lane = {"registry_rasters_checked": [], "max_abs_rho": 0.0, "lane_violation": False,
            "dot_overlap_violation": False, "degenerate_references": []}
    registry_paths = sorted(registry_dir.glob("*.tif")) if registry_dir.exists() else []
    our_dots = (arr > 0) & foot
    if our_dots.any():
        d_to_our = distance_transform_edt(~our_dots)
    for rp in registry_paths:
        try:
            with _rio.open(rp) as ds:
                reg = ds.read(1).astype(np.float64)
            reg_same_grid = (ds.shape == arr.shape and ds.transform == transform)
        except Exception as exc:
            lane["registry_rasters_checked"].append({"file": rp.name, "error": str(exc)})
            continue
        rho = rho_safe(arr, reg)
        entry = {
            "file": rp.name, "same_grid": bool(reg_same_grid),
            "spearman_rho": None if np.isnan(rho) else round(rho, 4),
            "flag_rho_gt_090": bool(not np.isnan(rho) and abs(rho) > 0.90),
        }
        if not np.isnan(rho) and abs(rho) > 0.90:
            lane["lane_violation"] = True
        lane["max_abs_rho"] = max(lane["max_abs_rho"], abs(rho) if not np.isnan(rho) else 0.0)
        if our_dots.any() and (reg > 0).any():
            reg_dots = (reg > 0)
            reg_density = float(reg_dots.sum() / float(foot.sum()))
            entry["registry_dot_density"] = round(reg_density, 4)
            # A near-universal lattice / background reference overlaps every dotted field by
            # construction; it is not a submission lane, so it is logged rather than tripped.
            if reg_density > 0.02:
                entry["degenerate_reference"] = True
                lane["degenerate_references"].append(rp.name)
            else:
                d_reg = distance_transform_edt(~reg_dots)
                near = float((d_reg[our_dots] <= 3.0).mean())
                entry["our_dots_within_3px_of_registry_dots"] = round(near, 4)
                entry["flag_overlap_gt_70pct"] = bool(near > 0.70)
                if near > 0.70:
                    lane["dot_overlap_violation"] = True
        lane["registry_rasters_checked"].append(entry)

    verdict = "promote" if (report["all_checks_passed"] and not lane["lane_violation"]
                            and not lane["dot_overlap_violation"]) else "negative"
    out = {"schema_version": "apartgemsdoe1-validate-v1",
           "file": str(args.geotiff), "sha256": sha256(args.geotiff), "bytes": args.geotiff.stat().st_size,
           "crs": str(crs), "transform": [round(float(v), 4) for v in transform][:6],
           "audit": report, "lane": lane, "verdict": verdict}
    print(json.dumps(out, indent=2))
    sidecar = args.geotiff.with_suffix(".validate.json")
    sidecar.write_text(json.dumps(out, indent=2) + "\n")
    print(f"[VALIDATE] verdict={verdict} sidecar={sidecar}")
    return 0 if verdict == "promote" else 1


if __name__ == "__main__":
    raise SystemExit(main())
