#!/usr/bin/env python3
<<<<<<< HEAD
"""APARTGEMSDOE1 lane — unique submission generator, Hypothesis H1.

Hypothesis H1 (ranked #1): geothermal-vent conduit propensity.
  Layers: geodetic dilatation rate + shear rate (strain), seismicity (distance to
  earthquake + earthquake intensity/density), magnetic tilt/total curvature,
  depth-to-basement, and a weak catalogue-proximity decay; optionally reinforced
  by GDR #1391 2 m temperature probes and paleo-geothermal (sinter/tufa) vents.
  Target: blind faults that host hydrothermal conduits and are therefore MISSING
  from the USGS/INGENIOUS catalogue (the private test labels are expert-labeled
  NEW faults, so catalogue-proximity alone cannot recover them).
  Differs from everything in the GEMSDOE sites: those submissions are
  catalogue-dotted / DEM-scarp / Euler-lineament / ridge-scatter fields keyed to
  mapped faults; H1 keys strain + seismicity + thermal proxy + basement depth and
  only weakens toward the catalogue.

Output: a soft-probability single-band float32 GeoTIFF on the exact competition
grid (EPSG:32611, 3730x3292, 100 m, origin 243350/4508550), values in [0,1],
0.0 outside the footprint and 0.0 on catalogue faults (masked pixel-exactly),
paired -zeros/-nan variants, zip, and an audit sidecar. No NaN inside the
footprint, so DrivenData's "Predicted values must be in range [0, 1]" cannot fire.

Run after `bash scripts/download_competition_data.sh` (restores hash-pinned data).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gems32.paths import data_dir, docs_dir, downloads_dir  # noqa: E402
from gems32.metric import kernel, ALPHA, BETA, RADIUS_PX, _OFF  # noqa: E402
from gems32.grid import read_footprint, read_labels, sha256  # noqa: E402
from gems32.submission import audit_geotiff  # noqa: E402

RNG = np.random.default_rng(20261027)

# --------------------------------------------------------------------------- #
# H1 layer weights (tunable; experiment 1). Sums to 1.0 over the normalised layers.
# --------------------------------------------------------------------------- #
W = {
    "dilatation": 0.30,   # geodetic dilatation rate - volumetric strain (conduit opening)
    "shear": 0.20,        # geodetic shear rate (fault-zone deformation)
    "seismicity": 0.20,   # earthquake proximity + density (active fracture)
    "curvature": 0.15,    # magnetic tilt/total curvature (blind-structure edge)
    "basement": 0.10,     # depth-to-basement gradient (basement-involved faulting)
    "catalogue": 0.05,    # weak proximity to mapped faults (TP capture, not discovery)
}

EMIT_TARGET_PX = 44_090          # mass-matched to the proven dotted scale (GEMSDOE25/30/32 family)
MIN_SEP_PX = 3.0                 # emission minimum separation (~300 m = kernel radius)
CATALOGUE_BUFFER_PX = 1          # pixels on/next to catalogue forced to zero
GAUSS_SIGMA_PX = 1.2             # light smoothing of the propensity surface before peak picking
PROXIUM_DECAY_PX = 6.0           # catalogue proximity decay scale (~600 m)


def robust_norm(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Robust min-max normalisation to [0, 1] using 2nd/98th percentiles over the footprint."""
    vals = arr[foot & np.isfinite(arr)]
    if vals.size == 0:
        return np.zeros_like(arr)
    lo, hi = np.percentile(vals, 2), np.percentile(vals, 98)
    if hi <= lo:
        return np.zeros_like(arr)
    out = np.clip((arr - lo) / (hi - lo), 0.0, 1.0)
    out[~foot | ~np.isfinite(arr)] = 0.0
    return out


def catalogue_proximity(labels: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Soft proximity to mapped faults: exp(-distance / PROXIUM_DECAY_PX), 0 on faults."""
    d = ndimage.distance_transform_edt(~labels)
    prox = np.exp(-d / PROXIUM_DECAY_PX)
    prox[labels] = 0.0          # never emit on the mapped trace itself
    prox[~foot] = 0.0
    return prox


def point_influence(csv_path: Path, foot: np.ndarray, transform, decay_px: float = 12.0) -> np.ndarray:
    """Rasterise GDR point observations as exponential-decay influence grids.

    The restored GDR CSVs carry UTM (EPSG:32611) `utm_x`/`utm_y`, so no reprojection is needed.
    Influence accumulates per-point over a small bounding window (cheap, no full-grid mgrid per point).
    """
    out = np.zeros(foot.shape, dtype=np.float64)
    try:
        import csv
    except ImportError:
        return out
    pts = []  # (row, col) pixel coordinates
    try:
        with csv_path.open() as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                try:
                    if r.get("row") is not None and r.get("col") is not None:
                        pts.append((float(r["row"]), float(r["col"])))
                        continue
                    x = float(r.get("utm_x") or r.get("UTM_X") or r.get("x"))
                    y = float(r.get("utm_y") or r.get("UTM_Y") or r.get("y"))
                except (TypeError, ValueError):
                    continue
                if not (np.isfinite(x) and np.isfinite(y)):
                    continue
                pts.append(((y - transform.f) / transform.e, (x - transform.c) / transform.a))  # -> (row, col)
    except FileNotFoundError:
        return out
    if not pts:
        return out
    H, W_ = foot.shape
    rows = np.array([p[0] for p in pts]).astype(int)
    cols = np.array([p[1] for p in pts]).astype(int)
    k = int(np.ceil(3.0 * decay_px))
    yy = np.arange(H, dtype=np.float64)
    xx = np.arange(W_, dtype=np.float64)
    for r0, c0 in zip(rows, cols):
        r_lo, r_hi = max(0, r0 - k), min(H, r0 + k + 1)
        c_lo, c_hi = max(0, c0 - k), min(W_, c0 + k + 1)
        if r_lo >= r_hi or c_lo >= c_hi:
            continue
        d = np.hypot(yy[r_lo:r_hi, None] - r0, xx[None, c_lo:c_hi] - c0)
        infl = np.exp(-d / decay_px)
        out[r_lo:r_hi, c_lo:c_hi] = np.maximum(out[r_lo:r_hi, c_lo:c_hi], infl)
    out[~foot] = 0.0
    return out


def build_field(ddir: Path) -> dict:
    """Build the H1 propensity field on the competition grid."""
    with rasterio.open(ddir / "sample_submission.tif") as tpl:
        template_foot = np.isfinite(tpl.read(1))
        template_transform = tpl.transform
    # The submission grid is defined by sample_submission.tif; band values outside that
    # footprint are treated as absent (the feature raster's footprint can differ slightly).
    foot = template_foot.copy()
    labels = read_labels(ddir / "labels.tif") & foot
    # Band index -> name (from registry/data_manifest.json, verified against the raster tags):
    # 1 mag_anom 2 rtp 3 tmi_hg 4 geod_2ndinv 5 iso_grav_anom_slope 6 tc
    # 7 geod_shearrate 8 geod_dilaterate 9 tmi_vg 10 deq_n100a15
    # 11 iso_grav_anom_vg 12 det_elev 13 iso_grav_anom 14 tmi 15 depth_to_base_surf
    # 16 ieq_n100a15 17 cond_surf 18 iso_grav_anom_hg 19 det_elev_slope
    BAND_INDEX = {"geod_dilaterate": 8, "geod_shearrate": 7, "deq_n100a15": 10,
                  "ieq_n100a15": 16, "tc": 6, "depth_to_base_surf": 15}
    transform = template_transform

    # Read and normalise one band at a time (float32) to keep peak memory low on the
    # 419 MB multi-band feature raster.
    def _band(name: str) -> np.ndarray:
        return robust_norm(src.read(BAND_INDEX[name]).astype(np.float32), foot)

    layers: dict[str, np.ndarray] = {}
    with rasterio.open(ddir / "training_features.tif") as src:
        layers["dilatation"] = _band("geod_dilaterate")
        layers["shear"] = _band("geod_shearrate")
        # Seismicity layer: earthquake intensity/density, down-weighted far from earthquakes.
        layers["seismicity"] = robust_norm(
            0.6 * _band("ieq_n100a15") + 0.4 * (1.0 - _band("deq_n100a15")), foot)
        layers["curvature"] = _band("tc")
        layers["basement"] = _band("depth_to_base_surf")
    # Weak catalogue proximity (TP capture, not discovery): distance decay off mapped faults.
    layers["catalogue"] = catalogue_proximity(labels, foot)

    field = np.zeros(foot.shape, dtype=np.float64)
    for name in ("dilatation", "shear", "seismicity", "curvature", "basement"):
        field += W[name] * layers[name]
    field += W["catalogue"] * layers["catalogue"]
    field = np.clip(field, 0.0, 1.0)

    # External thermal/hydrothermal proxies (GDR #1391, CC-BY 4.0): 2 m temperature probes,
    # paleo-geothermal (sinter/tufa) vents. Added only when the restored files exist.
    if (ddir / "external" / "gdr_wellspring_in_footprint.csv").exists() or \
       (ddir / "external" / "gdr_volcanic_vents_in_footprint.csv").exists():
        for name, csv_name, decay in (("temp_probe", "gdr_wellspring_in_footprint.csv", 12.0),
                                      ("paleo_vent", "gdr_volcanic_vents_in_footprint.csv", 12.0)):
            csv_path = ddir / "external" / csv_name
            if csv_path.exists():
                layers[name] = point_influence(csv_path, foot, transform, decay_px=decay)
                W[name] = 0.08
                for k in W:
                    if k not in ("temp_probe", "paleo_vent"):
                        W[k] *= 0.92
        for name in ("temp_probe", "paleo_vent"):
            if name in layers:
                field += W[name] * layers[name]
        field = np.clip(field, 0.0, 1.0)

    field = ndimage.gaussian_filter(field, GAUSS_SIGMA_PX, mode="constant")
    field = np.clip(field, 0.0, 1.0)
    field_pre_mask = field.copy()
    field[~foot] = 0.0
    field[labels] = 0.0  # pixel-exact catalogue mask (also enforced by the writer)
    return {"field": field, "field_pre_mask": field_pre_mask, "foot": foot, "labels": labels,
            "layers": layers, "weights": W, "transform": transform}


def emit_dots(field: np.ndarray, foot: np.ndarray, labels: np.ndarray, target_px: int,
              min_sep_px: float) -> np.ndarray:
    """Pick `target_px` emission pixels as separated maxima of the field.

    Deterministic greedy non-maximum suppression: rank pixels by field value, accept a
    pixel if not already blocked, then block its +/- ceil(min_sep_px) Chebyshev
    neighbourhood. O(candidates) with O(1) per candidate.
    """
    H, W_ = field.shape
    cand = np.argwhere(foot & (field > 0) & ~labels)
    order = np.argsort(-field[cand[:, 0], cand[:, 1]], kind="stable")
    blocked = np.zeros((H, W_), dtype=bool)
    accepted = np.zeros((H, W_), dtype=bool)
    nblk = int(np.ceil(min_sep_px))
    n_emitted = 0
    scanned = 0
    for idx in order:
        r, c = int(cand[idx, 0]), int(cand[idx, 1])
        scanned += 1
        if blocked[r, c]:
            continue
        accepted[r, c] = True
        n_emitted += 1
        r0, r1 = max(0, r - nblk), min(H, r + nblk + 1)
        c0, c1 = max(0, c - nblk), min(W_, c + nblk + 1)
        blocked[r0:r1, c0:c1] = True
        if n_emitted >= target_px:
            break
    print(f"[H1] candidates={cand.shape[0]} scanned={scanned} emitted={n_emitted}")
    return accepted


def write_geotiff(arr: np.ndarray, template: Path, out_path: Path, nodata) -> None:
    """Write single-band float32 GeoTIFF on the exact template grid."""
    with rasterio.open(template) as tpl:
        profile = tpl.profile.copy()
    profile.update(driver="GTiff", dtype="float32", count=1, nodata=nodata,
                   compress="deflate", predictor=3, zlevel=9, tiled=True,
                   blockxsize=256, blockysize=256)
    out = np.asarray(arr, dtype=np.float32)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(out, 1)


def main() -> int:
    t0 = time.time()
    ddir = data_dir()
    print(f"[H1] STEP data_dir {ddir}", flush=True)

    import argparse as _ap
    _ap2 = _ap.ArgumentParser(add_help=False)
    _ap2.add_argument("--weights", default=None, help="JSON weight override for W, e.g. '{\"catalogue\":0.35}'")
    _ap2.add_argument("--variant", default="h1", help="Variant tag appended to the slug")
    _known, _ = _ap2.parse_known_args()
    if _known.weights:
        W.update(json.loads(_known.weights))
        print(f"[H1] weights override applied: {W}", flush=True)
    VARIANT_TAG = _known.variant
    for f in ("training_features.tif", "labels.tif", "sample_submission.tif"):
        if not (ddir / f).exists():
            raise SystemExit(f"Missing {ddir / f}. Run `bash scripts/download_competition_data.sh` first.")
    print("[H1] STEP files-present", flush=True)

    with rasterio.open(ddir / "sample_submission.tif") as tpl:
        template_foot = np.isfinite(tpl.read(1))
    print("[H1] STEP template-foot", flush=True)

    built = build_field(ddir)
    print("[H1] STEP build_field", flush=True)
    field, foot, labels = built["field"], built["foot"], built["labels"]
    assert np.array_equal(foot, template_foot), "footprint must match the sample submission"

    # Leakage canary (Protocol Rule 4): AUC of the field against VISIBLE catalogue faults.
    # AUC > 0.90 => the field is just reproducing the catalogue => lane drift / leakage.
    y_true = labels[foot].astype(np.float64)
    y_score = built["field_pre_mask"][foot]
    order = np.argsort(y_score)
    ranks = np.empty(order.size, dtype=np.float64)
    ranks[order] = np.arange(1, order.size + 1)
    # tie-corrected average ranks
    pos = y_true == 1
    n_pos = int(pos.sum()); n_neg = int((~pos).sum())
    auc = (ranks[pos].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg) if n_pos and n_neg else float("nan")
    print(f"[H1] leakage canary AUC(field vs visible catalogue faults) = {auc:.4f}")

    emit = emit_dots(field, foot, labels, EMIT_TARGET_PX, MIN_SEP_PX)
    soft = np.zeros(foot.shape, dtype=np.float32)
    soft[emit] = np.clip(field[emit], 0.0, 1.0).astype(np.float32)
    soft[~foot] = 0.0
    soft[labels] = 0.0

    # ---- sidecar metadata ----
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(soft.tobytes()).hexdigest()[:8]
    slug = f"apartgemsdoe1-{VARIANT_TAG}-geothermal-vent-conduit-{EMIT_TARGET_PX}"
    name = f"{slug}-{ts}-{digest8}"
    out_dir = downloads_dir()
    zeros_path = out_dir / f"{name}-zeros.tif"
    nan_path = out_dir / f"{name}-nan.tif"
    zip_path = out_dir / f"{name}.zip"

    write_geotiff(soft, ddir / "sample_submission.tif", zeros_path, nodata=None)
    write_geotiff(np.where(foot, soft, np.nan).astype(np.float32), ddir / "sample_submission.tif",
                  nan_path, nodata=np.nan)

    import zipfile
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(zeros_path, arcname=zeros_path.name)

    foot_arr, labels_arr = foot, labels
    audit = audit_geotiff(zeros_path, foot_arr, labels_arr, mode="zeros",
                          template_tif=ddir / "sample_submission.tif")

    # Self-diagnostics (truth-free): emitted mass, field stats, weight summary.
    emitted = int((soft > 0).sum())
    diag = {
        "schema_version": "apartgemsdoe1-h1-v1",
        "generated_utc": ts,
        "lane": "APARTGEMSDOE1-H1",
        "hypothesis": "H1 geothermal-vent conduit propensity (strain + seismicity + curvature + basement + weak catalogue + thermal proxies)",
        "emitted_px": emitted,
        "emitted_soft_mass": float(soft.sum()),
        "field_mean": float(field[foot].mean()),
        "field_max": float(field.max()),
        "auc_field_vs_visible_catalogue": auc,
        "weights": built["weights"],
        "target_px": EMIT_TARGET_PX,
        "min_sep_px": MIN_SEP_PX,
        "files": {
            "zeros_tif": {"path": str(zeros_path), "sha256": sha256(zeros_path), "bytes": zeros_path.stat().st_size},
            "nan_tif": {"path": str(nan_path), "sha256": sha256(nan_path), "bytes": nan_path.stat().st_size},
            "zip": {"path": str(zip_path), "sha256": sha256(zip_path), "bytes": zip_path.stat().st_size},
        },
        "audit": audit,
        "seconds": round(time.time() - t0, 1),
    }
    sidecar = out_dir / f"{name}-audit.json"
    sidecar.write_text(json.dumps(diag, indent=2) + "\n")
    print(json.dumps(diag, indent=2))
    print(f"[H1] WROTE {zeros_path}  sha256={sha256(zeros_path)}")
    print(f"[H1] WROTE {nan_path}")
    print(f"[H1] WROTE {zip_path}")
    print(f"[H1] WROTE {sidecar}")
    print("[H1] STATUS: format-validated. OK to download; NOT cleared for competition slot until "
          "holdout DTI is computed (scripts/evaluate_holdout.py) and lane checks pass "
          "(scripts/validate_submission.py).")
    return 0
=======
"""Fail-closed guard for the retired synthetic TIF generator.

The earlier demo generator used artificial Gaussian blobs and synthetic fault
traces. It was not a GEMS geophysical model and must not be run as a submission
pipeline. Its already-generated, labeled research artifact is retained under
docs/assets/ for inspection only; this entry point creates nothing.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "BLOCKED: STOP: no competition prediction generated. The previous generator "
        "was synthetic-only and has been disabled; no authorized feature stack, "
        "canonical writer, official template, or holdout is available.",
        file=sys.stderr,
    )
    return 2
>>>>>>> origin/main


if __name__ == "__main__":
    raise SystemExit(main())
