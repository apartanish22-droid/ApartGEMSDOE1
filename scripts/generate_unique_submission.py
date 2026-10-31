#!/usr/bin/env python3
"""Generate ONE unique submission candidate: dilatational step-over / relay-ramp dots.

Hypothesis H1 (ranked first in this session's hypothesis review; see the
executive summary): in the transtensional Walker Lane / western Great Basin
setting, releasing step-overs and relay ramps between en-echelon mapped fault
segments concentrate concealed geothermal upflow and can host fault traces
missing from the USGS / INGENIOUS catalogue. The competition scores exactly
those catalogue-missing faults (official problem page: the scored faults are
not in the existing USGS database).

Method (geometry-only: no feature cache, no organizer data, no leakage):
  1. Load the pinned competition grid (EPSG:32611, 100 m, 3730 x 3292) and the
     mapped-fault catalogue from data/bridge/.
  2. Skeletonize the catalogue; estimate local strike at every skeleton pixel
     from the gradient of the distance transform (strike is normal to the
     across-trace gradient).
  3. For each skeleton pixel, probe both normal directions at gap distances of
     4-14 px for a counterpart skeleton pixel whose strike is within 30 deg and
     whose along-strike offset is <= 3 px, across a mostly-empty gap. Each
     accepted pair yields one dot at the gap midpoint (the relay/step-over
     center, i.e. an off-catalogue upflow zone).
  4. Non-maximum suppress at 6 px; cap at 12 000 dots - well under the 21 713
     dot budget that is even necessary to be measurable against the pinned
     lattice witness (0.30 x N dots must fall outside its 3-px halo).
  5. Snap dots off mapped catalogue pixels; keep footprint cells only. Emit
     float32 values of 1.0 at dots, 0.0 elsewhere: all finite, in [0,1], zero
     outside the footprint, zero on the mapped catalogue.

Verification (fail-closed; no upload occurs):
  - local format preflight via gems57.validate
  - literal uniqueness vs the pinned 13GEMSDOE lattice witness:
      < 70% of dots within 3 px AND Spearman rho < 0.90 (full footprint)
  - holdout: this fixed binary mask replayed on the label-blind v3 buffered
    component folds -> HOLDOUT-DTI + 95% CI (catalogue proxy truth; not the
    hidden organizer truth, not a leaderboard estimate)
  - submission_writer receipt: .tif + .zip + .json, approved_for_weekly_slot=False

Outputs:
  docs/downloads/apartgems1-stepover-relay-dots-20261031.{tif,zip,json}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from skimage.morphology import skeletonize
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import load_grid
from gems57.holdout import buffered_component_draw
from gems57 import evaluate_holdout as EH
from gems57.validate import validate
from gems57.submission_writer import write_submission

SEED = 2026
TARGET_DOTS = 12_000
NMS_RADIUS_PX = 6
GAP_MIN_PX, GAP_MAX_PX = 4, 14
ORIENT_TOL_DEG = 30.0
ALONG_TOL_PX = 3.0
# 0.30 x N dots must fall outside the witness halo to be measurable at all;
# measured uncovered cells for the pinned witness: 6 514 -> max necessary N ~21 713.
CAP_NECESSARY_DOTS = 21_713

NAME = "apartgems1-stepover-relay-dots-20261031"
NOTE = ("Step-over/relay-ramp dots between en-echelon mapped segments; unique off-catalogue geometry; not selector-approved - do not submit")
HYPOTHESIS = ("H1: dilatational step-over / relay-ramp zones between en-echelon mapped fault "
              "segments host concealed geothermal upflow traces missing from the USGS / "
              "INGENIOUS catalogue")
MECHANISM = ("Releasing (dilatational) step-overs and relay ramps between offset, "
             "sub-parallel normal fault segments dilate the crust and focus geothermal "
             "upflow; the through-going trace in the gap center is often unmapped, so "
             "dots placed at gap midpoints target catalogue-missing faults, which is "
             "what the competition scores.")
NAMED_NON_FAULT_MIMIC = ("Alluvial-fan distributary channels and erosional scarps cutting "
                         "between fault traces can produce linear gaps in topography that look "
                         "like structural step-overs; lithologic contacts can produce parallel "
                         "geophysical lineaments with no fault.")
assert len(NAME) <= 140, len(NAME)
assert len(NOTE) <= 140, len(NOTE)

OUT_TIF = ROOT / "docs" / "downloads" / f"{NAME}.tif"
OUT_JSON = ROOT / "evidence" / f"{NAME}-run-card.json"
WITNESS_AUDIT_OUT = ROOT / "evidence" / f"{NAME}-lattice-witness-audit.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_strike(catalogue: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Unit strike vectors (row, col components) at catalogue pixels.

    Strike is perpendicular to the gradient of the distance transform: at a
    trace pixel the across-trace gradient points away from the trace, so the
    trace direction is the gradient rotated +90 deg in image coordinates
    (row increases southwards, col eastwards).
    """
    dist = ndi.distance_transform_edt(~catalogue)
    g_row = ndi.sobel(dist, axis=0)
    g_col = ndi.sobel(dist, axis=1)
    s_row = -g_col  # rotate gradient by +90 deg in (row, col) image coords
    s_col = g_row
    mag = np.hypot(s_row, s_col)
    s_row = np.where(mag > 0.0, s_row / np.maximum(mag, 1e-12), 0.0)
    s_col = np.where(mag > 0.0, s_col / np.maximum(mag, 1e-12), 0.0)
    return s_row, s_col


def step_over_dot_centers(
    catalogue: np.ndarray,
    footprint: np.ndarray,
    *,
    seed: int = SEED,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Return dot row/col arrays plus a diagnostics dict."""
    diag: dict = {}
    skel = skeletonize(catalogue)
    sy_, sx_ = local_strike(catalogue)
    ys, xs = np.nonzero(skel & footprint)
    n_skel = int(ys.size)
    diag["catalogue_pixels"] = int(catalogue.sum())
    diag["skeleton_pixels"] = n_skel
    if n_skel == 0:
        return np.array([], dtype=int), np.array([], dtype=int), diag

    # Geological strike azimuth, clockwise from north, modulo 180 deg.
    # strike vector (s_row, s_col); azimuth = atan2(east, north) = atan2(s_col, -s_row).
    orient = (np.degrees(np.arctan2(sx_[ys, xs], -sy_[ys, xs])) % 180.0).astype(np.float32)
    tree = cKDTree(np.column_stack([ys, xs]).astype(np.float64))

    rng = np.random.default_rng(seed)
    mids_y: list[float] = []
    mids_x: list[float] = []
    quality: list[float] = []

    # Probe both normal directions at every gap distance.
    offsets = []
    for g in range(GAP_MIN_PX, GAP_MAX_PX + 1):
        offsets.append((g, 1))
        offsets.append((g, -1))

    for i in range(n_skel):
        py, px = int(ys[i]), int(xs[i])
        sr, sc = float(sy_[py, px]), float(sx_[py, px])
        o_i = float(orient[i])
        # normals (row, col components): rotate strike by +/- 90 deg.
        for g, side in offsets:
            nr, nc = -side * sc, side * sr  # unit normal
            qy = py + int(round(g * nr))
            qx = px + int(round(g * nc))
            if not (0 <= qy < catalogue.shape[0] and 0 <= qx < catalogue.shape[1]):
                continue
            for q_idx in tree.query_ball_point([qy, qx], r=2.0):
                if q_idx == i:
                    continue
                qy2, qx2 = int(ys[q_idx]), int(xs[q_idx])
                # similar strike (mod 180 deg)
                d_orient = abs(o_i - float(orient[q_idx]))
                d_orient = min(d_orient, 180.0 - d_orient)
                if d_orient > ORIENT_TOL_DEG:
                    continue
                # small along-strike offset between the two trace points
                along = abs((qy2 - py) * sr + (qx2 - px) * sc)
                if along > ALONG_TOL_PX:
                    continue
                # the gap between the points must be mostly empty of catalogue
                n_sample = 9
                ty = np.linspace(py, qy2, n_sample)
                tx = np.linspace(px, qx2, n_sample)
                ty_i = np.clip(np.rint(ty).astype(int), 0, catalogue.shape[0] - 1)
                tx_i = np.clip(np.rint(tx).astype(int), 0, catalogue.shape[1] - 1)
                gap_frac = float(catalogue[ty_i, tx_i].mean())
                if gap_frac > 0.5:
                    continue
                mids_y.append(0.5 * (py + qy2))
                mids_x.append(0.5 * (px + qx2))
                quality.append(1.0 / float(g))  # narrower gaps first

    diag["raw_step_over_candidates"] = len(mids_y)
    if not mids_y:
        return np.array([], dtype=int), np.array([], dtype=int), diag

    mids = np.column_stack([mids_y, mids_x])
    qual = np.array(quality)
    order = np.argsort(-qual, kind="stable")
    chosen: list[int] = []
    kept = np.zeros(len(mids), dtype=bool)
    for idx in order:
        if kept[idx]:
            continue
        chosen.append(int(idx))
        dy = mids[:, 0] - mids[idx, 0]
        dx = mids[:, 1] - mids[idx, 1]
        kept |= (dy * dy + dx * dx) <= float(NMS_RADIUS_PX * NMS_RADIUS_PX)

    chosen = np.array(chosen, dtype=int)
    dots = np.rint(mids[chosen]).astype(int)
    dots_y = np.clip(dots[:, 0], 0, catalogue.shape[0] - 1)
    dots_x = np.clip(dots[:, 1], 0, catalogue.shape[1] - 1)

    # Cap the dot budget (uniqueness against the lattice witness requires N dots
    # with at least 30% outside its halo; measured uncovered cells = 6 514).
    if dots_y.size > TARGET_DOTS:
        keep_order = np.argsort(-qual[chosen], kind="stable")[:TARGET_DOTS]
        dots_y = dots_y[keep_order]
        dots_x = dots_x[keep_order]

    # Snap dots off the mapped catalogue: nearest non-catalogue footprint pixel
    # within 3 px; otherwise drop the dot.
    keep = np.ones(dots_y.size, dtype=bool)
    not_cat_fp = footprint & ~catalogue
    dist_to_ok, nearest = ndi.distance_transform_edt(~not_cat_fp, return_indices=True)
    for k in range(dots_y.size):
        y, x = int(dots_y[k]), int(dots_x[k])
        if catalogue[y, x]:
            ny, nx = int(nearest[0, y, x]), int(nearest[1, y, x])
            if dist_to_ok[y, x] <= 3.0 and footprint[ny, nx] and not catalogue[ny, nx]:
                dots_y[k], dots_x[k] = ny, nx
            else:
                keep[k] = False
    dots_y, dots_x = dots_y[keep], dots_x[keep]

    diag["dots_after_snap"] = int(dots_y.size)
    diag["dots_on_catalogue"] = int((catalogue[dots_y, dots_x]).sum()) if dots_y.size else 0
    diag["dots_outside_footprint"] = int((~footprint[dots_y, dots_x]).sum()) if dots_y.size else 0
    return dots_y, dots_x, diag


def holdout_replay(prediction: np.ndarray, grid) -> dict:
    """Static replay of a fixed mask on the label-blind v3 folded holdout.

    This is fold-honest for scoring (the draw is label-blind), but a real
    experiment must rebuild catalogue-derived features per fold from visible
    faults only; this fixed-mask replay cannot do that. Reported as
    HOLDOUT-DTI-style output with an explicit scope caveat, not as a model
    holdout or leaderboard estimate.
    """
    folds, _quad = buffered_component_draw(grid, seed=SEED)
    terms_by_arm: dict[str, np.ndarray] = {}
    per_fold_detail: dict[str, dict] = {}
    for arm_name, pred in (("candidate", prediction), ("zero_control", np.zeros_like(prediction))):
        block_terms = None
        fold_scores = {}
        for fold in folds:
            result, terms = EH.evaluate(pred, fold, grid.footprint)
            block_terms = terms.copy() if block_terms is None else block_terms + terms
            fold_scores[fold["name"]] = float(result["dti"])
        terms_by_arm[arm_name] = block_terms
        per_fold_detail[arm_name] = fold_scores
    summary = EH.pooled_summary(
        terms_by_arm, draws=1000, seed=520810, candidate="candidate"
    )
    summary["per_fold_dti"] = per_fold_detail
    summary["scope"] = (
        "Fixed binary mask replayed on label-blind buffered-component folds; "
        "catalogue-proxy truth, not organizer-held labels; features not rebuilt "
        "per fold; not a leaderboard estimate."
    )
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-upload-check", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()

    grid = load_grid()
    footprint = grid.footprint
    catalogue = grid.catalogue

    dots_y, dots_x, diag = step_over_dot_centers(catalogue, footprint, seed=SEED)
    n_dots = int(dots_y.size)

    prediction = np.zeros(grid.shape, dtype=np.float32)
    if n_dots:
        prediction[dots_y, dots_x] = np.float32(1.0)
    prediction[~footprint] = 0.0

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "hypothesis": HYPOTHESIS,
        "mechanism": MECHANISM,
        "named_non_fault_mimic_process": NAMED_NON_FAULT_MIMIC,
        "evidence_class": "UNIQUE-CANDIDATE-GENERATION",
        "grid": {
            "crs": str(grid.crs),
            "shape": list(grid.shape),
            "transform": [float(v) for v in tuple(grid.transform)[:6]],
        },
        "generation_diagnostics": diag,
        "emitted_dots": n_dots,
        "dot_value": 1.0,
        "name": NAME,
        "note": NOTE,
        "note_chars": len(NOTE),
    }

    # --- 1. Local format preflight ---------------------------------------
    OUT_TIF.parent.mkdir(parents=True, exist_ok=True)
    sample_path = ROOT / "data" / "bridge" / "sample_submission.tif"
    receipt = write_submission(
        OUT_TIF,
        prediction,
        sample_path,
        footprint,
        name=NAME,
        note=NOTE,
        catalogue=catalogue,
        metadata=dict(hypothesis="H1 step-over relay dots"),
    )
    report["writer_receipt"] = receipt
    report["output_file"] = str(OUT_TIF.relative_to(ROOT))
    report["output_sha256"] = sha256_file(OUT_TIF)

    local_validation = validate(OUT_TIF, footprint=footprint, catalogue=catalogue)
    report["format_validation"] = local_validation
    if not local_validation["all_checks_passed"]:
        failed = [k for k, v in local_validation["checks"].items() if not v]
        raise RuntimeError(f"format preflight failed: {failed}")

    # --- 2. Uniqueness vs the pinned lattice witness ---------------------
    witness_proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_literal_witness.py"),
            "--candidate",
            str(OUT_TIF),
            "--out",
            str(WITNESS_AUDIT_OUT),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    witness_text = witness_proc.stdout + witness_proc.stderr
    witness_audit = None
    if WITNESS_AUDIT_OUT.is_file():
        witness_audit = json.loads(WITNESS_AUDIT_OUT.read_text())
    report["witness_audit"] = witness_audit
    report["witness_audit_stdout"] = witness_text[-2000:]

    unique = bool(
        witness_audit is not None
        and not witness_audit["final_dot_gate"]["duplicate"]
        and witness_audit["format_validation"]["all_checks_passed"]
    )
    report["unique_vs_pinned_witness"] = unique
    report["overlap_3px"] = (
        witness_audit["final_dot_gate"]["forward_overlap_3px"] if witness_audit else None
    )
    report["rho_vs_witness"] = (
        witness_audit["final_dot_gate"]["spearman_full_footprint"] if witness_audit else None
    )

    # --- 3. Holdout replay (HOLDOUT-DTI-style, catalogue proxy) ---------
    holdout = holdout_replay(prediction > 0.0, grid)
    report["holdout"] = holdout
    report["holdout_dti"] = holdout["scores"]["candidate"]["dti"]
    report["holdout_ci95"] = holdout["scores"]["candidate"]["ci95"]
    report["holdout_withheld_positives"] = holdout["scores"]["candidate"][
        "withheld_positive_pixels"
    ]

    # --- 4. Fail-closed promotion decision --------------------------------
    format_ok = bool(local_validation["all_checks_passed"])
    uniqueness_ok = bool(unique)
    holdout_runs = holdout is not None
    gates = {
        "format_and_range_local": format_ok,
        "uniqueness_vs_pinned_witness": uniqueness_ok,
        "holdout_evaluated": holdout_runs,
        "complete_registry_checked": False,
        "organizer_receipt": False,
        "selector_approval": False,
    }
    report["gates"] = gates
    report["verdict"] = (
        "promote-to-selector-only"
        if all([format_ok, uniqueness_ok]) and holdout_runs
        else "negative"
    )
    report["verdict_reason"] = (
        "All local gates pass; complete registry, organizer receipt and selector "
        "approval remain outstanding, so no weekly slot is claimed."
        if report["verdict"] == "promote-to-selector-only"
        else "Not all gates pass (see gates); file is a research artifact and is "
        "NOT cleared for upload."
    )

    OUT_JSON.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report["verdict"] == "promote-to-selector-only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
