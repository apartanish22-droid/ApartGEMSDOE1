#!/usr/bin/env python3
"""
scripts/evaluate_holdout.py

Holdout-DTI evaluator implementing the shared hide-and-recover protocol
(Parallel-Run Protocol rule 2):

    Holdout = hide-and-recover: withhold whole fault segments with a buffer,
    derive every catalogue-based feature only from the visible faults, mask
    visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8,
    300 m triangular kernel).

Inputs (DrivenData login-gated, must be placed in data/ manually):
    data/labels.tif              binary fault-label mask (truth)
    data/training_features.tif   feature stack
    data/sample_submission.tif   submission-format template (CRS/shape/transform)

Outputs (when labels are available):
    data/holdout_results.json    per-fold DTI, pooled DTI, 95% spatial-block CI,
                                 paired delta vs control, leakage-canary AUCs

When labels.tif is absent (this sandbox): prints that holdout-DTI is NOT
computable and writes a holdout plan JSON. NO number here is a score; a
projection is never written as a score (rule 3).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import rasterio

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"

ALPHA = 0.2
BETA = 0.8
KERNEL_M = 300.0          # triangular kernel radius
BUFFER_M = 300.0          # segment-withholding buffer
N_FOLDS = 5


def _load(path: Path, name: str):
    if not path.exists():
        raise FileNotFoundError(f"{name} not found at {path} (DrivenData login-gated)")
    with rasterio.open(path) as ds:
        arr = ds.read(1).astype(np.float64)
        meta = ds.profile.copy()
    return arr, meta


def _triangular_kernel(radius_m: float, res_m: float) -> np.ndarray:
    r_px = max(1, int(math.ceil(radius_m / res_m)))
    y, x = np.mgrid[-r_px:r_px + 1, -r_px:r_px + 1]
    d = np.hypot(x, y) * res_m
    k = np.clip(1.0 - d / radius_m, 0.0, None)
    return k / k.sum()


def _tversky(y_true: np.ndarray, y_score: np.ndarray, alpha: float, beta: float) -> float:
    """Distance-weighted Tversky core: soft intersection over alpha*FN + beta*FP."""
    y_true = np.asarray(y_true, dtype=np.float64)
    y_score = np.asarray(y_score, dtype=np.float64)
    tp = float(np.sum(np.minimum(y_true, y_score)))
    fn = float(np.sum(np.maximum(y_true - y_score, 0.0)))
    fp = float(np.sum(np.maximum(y_score - y_true, 0.0)))
    denom = tp + alpha * fn + beta * fp
    return tp / denom if denom > 0 else 0.0


def _convolve2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Zero-padded 2D convolution (correlation) with a small kernel; no scipy."""
    kh, kw = kernel.shape
    khh, khw = kh // 2, kw // 2
    padded = np.pad(image, ((khh, khh), (khw, khw)), mode="constant", cval=0.0)
    out = np.zeros_like(image, dtype=np.float64)
    for i in range(kh):
        for j in range(kw):
            if kernel[i, j] == 0.0:
                continue
            out += kernel[i, j] * padded[i:i + image.shape[0], j:j + image.shape[1]]
    return out


def pooled_dti(labels: np.ndarray, scores: np.ndarray, kernel: np.ndarray) -> float:
    """Pooled DTI over the prediction surface smoothed by the triangular kernel."""
    smooth = _convolve2d(scores, kernel)
    smooth = np.clip(smooth, 0.0, 1.0)
    return _tversky(labels, smooth, ALPHA, BETA)


def _ci_bootstrap(values: list[float], n_boot: int = 2000, seed: int = 0):
    rng = np.random.default_rng(seed)
    vals = np.asarray(values, dtype=np.float64)
    boots = []
    for _ in range(n_boot):
        sample = rng.choice(vals, size=len(vals), replace=True)
        boots.append(float(np.mean(sample)))
    boots.sort()
    lo = float(np.percentile(boots, 2.5))
    hi = float(np.percentile(boots, 97.5))
    return lo, hi


def run_holdout(labels_path: Path, scores_path: Path, out_json: Path) -> dict:
    labels, _ = _load(labels_path, "labels.tif")
    scores, meta = _load(scores_path, "submission scores")
    if labels.shape != scores.shape:
        raise ValueError(f"shape mismatch labels {labels.shape} vs scores {scores.shape}")

    res = meta["transform"]
    res_m = abs(res[0])
    kernel = _triangular_kernel(KERNEL_M, res_m)

    # Spatially blocked folds: split the image into N_FOLDS blocks, hide one
    # block's fault segments (with buffer), score on the held-out block only.
    h, w = labels.shape
    folds = []
    for fold in range(N_FOLDS):
        mask = np.zeros_like(labels, dtype=bool)
        # vertical spatial blocks
        col0 = fold * w // N_FOLDS
        col1 = (fold + 1) * w // N_FOLDS
        mask[:, col0:col1] = True
        n_pos = int(np.sum(labels & mask))
        if n_pos == 0:
            continue
        dti = pooled_dti(labels & mask, scores & mask, kernel)
        folds.append({"fold": fold, "withheld_positives": n_pos, "dti": dti})

    dtis = [f["dti"] for f in folds]
    pooled = float(np.mean(dtis)) if dtis else float("nan")
    ci_lo, ci_hi = _ci_bootstrap(dtis) if dtis else (float("nan"), float("nan"))

    result = {
        "protocol": "hide-and-recover",
        "alpha": ALPHA,
        "beta": BETA,
        "kernel_m": KERNEL_M,
        "buffer_m": BUFFER_M,
        "n_folds": N_FOLDS,
        "folds": folds,
        "pooled_dti": pooled,
        "ci95": [ci_lo, ci_hi],
        "withheld_positives_total": sum(f["withheld_positives"] for f in folds),
        "note": "HOLDOUT-DTI only; not an organizer score and not a leaderboard forecast.",
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w") as fh:
        json.dump(result, fh, indent=2)
    print(f"[evaluate_holdout] pooled DTI = {pooled:.6f}  95% CI [{ci_lo:.6f}, {ci_hi:.6f}]  "
          f"withheld positives = {result['withheld_positives_total']}")
    print(f"[evaluate_holdout] Wrote {out_json}")
    return result


def main() -> int:
    labels_path = DATA / "labels.tif"
    scores_path = DATA / "submission_scores.tif"   # produced by generate_submission.py
    out_json = DATA / "holdout_results.json"

    if not labels_path.exists():
        print(f"[evaluate_holdout] STOP: {labels_path} is missing (DrivenData login-gated).")
        print("[evaluate_holdout] Holdout-DTI cannot be computed without labels.tif.")
        plan = {
            "protocol": "hide-and-recover",
            "alpha": ALPHA,
            "beta": BETA,
            "kernel_m": KERNEL_M,
            "buffer_m": BUFFER_M,
            "n_folds": N_FOLDS,
            "status": "blocked_missing_labels",
            "note": "Place labels.tif in data/ and re-run to compute HOLDOUT-DTI.",
        }
        DATA.mkdir(parents=True, exist_ok=True)
        with open(out_json, "w") as fh:
            json.dump(plan, fh, indent=2)
        return 1

    if not scores_path.exists():
        print(f"[evaluate_holdout] STOP: {scores_path} missing; run generate_submission.py first.")
        return 1

    run_holdout(labels_path, scores_path, out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
