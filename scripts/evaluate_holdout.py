#!/usr/bin/env python3
"""Static-raster replay against the shared hide-and-recover folds.

Important: a single saved submission TIFF is *not* a fold-honest hide-and-recover
model evaluation. If the raster was built from the full fault catalogue, applying
fold masks afterward can erase predictions around withheld faults. This CLI is
therefore labelled STATIC-REPLAY-DTI and must not be reported as a model holdout
or leaderboard estimate. Fold-honest experiments must rebuild catalogue-derived
features from each fold's visible catalogue and use the shared evaluator directly.

The loader rejects bad grids, non-float32 data, NaN/Inf inside the footprint,
out-of-range values, and positive predictions outside it. It never repairs
invalid in-footprint predictions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio
from gems57 import evaluate_holdout as EH
from gems57 import load_grid
from gems57.holdout import buffered_component_draw


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_static_prediction(path: Path, grid) -> np.ndarray:
    """Read a format-checked static TIFF and apply only the study-area mask.

    NaN is allowed outside the footprint because the public format instructions
    allow null/NaN out of bounds. Inside the scored footprint values must be
    finite and in [0,1]. Outside values must be either NaN or zero; positive
    outside mass is rejected rather than silently discarded.
    """
    path = Path(path)
    with rasterio.open(path) as src:
        if src.count != 1:
            raise ValueError(f"prediction TIFF must have one band, found {src.count}")
        if src.dtypes[0] != "float32":
            raise ValueError(f"prediction TIFF must be float32, found {src.dtypes[0]}")
        if src.shape != grid.shape:
            raise ValueError(f"prediction shape {src.shape} does not match grid {grid.shape}")
        if src.crs != grid.crs:
            raise ValueError(f"prediction CRS {src.crs} does not match grid {grid.crs}")
        if src.transform != grid.transform:
            raise ValueError("prediction transform does not match the competition grid")
        values = src.read(1).astype(np.float64, copy=False)

    footprint = np.asarray(grid.footprint, dtype=bool)
    if footprint.shape != grid.shape:
        raise ValueError("grid footprint shape does not match grid metadata")
    if np.isinf(values).any():
        raise ValueError("prediction TIFF contains infinite values")
    inside = values[footprint]
    if not np.isfinite(inside).all():
        raise ValueError("prediction TIFF has NaN or non-finite values inside the footprint")
    if (inside < 0.0).any() or (inside > 1.0).any():
        raise ValueError("prediction values inside the footprint must be in [0,1]")

    outside = values[~footprint]
    outside_finite = outside[np.isfinite(outside)]
    if (outside_finite < 0.0).any() or (outside_finite > 1.0).any():
        raise ValueError("finite prediction values outside the footprint must be in [0,1]")
    if np.any(outside_finite > 0.0):
        raise ValueError("positive prediction mass outside the footprint is not allowed")

    # The metric is defined on the valid study area. Only already-validated
    # outside NaNs are represented as zero in this temporary scoring array.
    prediction = np.zeros(grid.shape, dtype=np.float64)
    prediction[footprint] = inside
    return prediction


def mark_static_replay(summary: dict, *, candidate_sha256: str) -> dict:
    """Prevent output from being mistaken for fold-honest HOLDOUT-DTI."""
    summary["evidence_class"] = "STATIC-REPLAY-DTI"
    summary["score_scope"] = (
        "Static saved-raster replay against hide-and-recover folds; not a fold-honest model holdout."
    )
    summary["holdout_contract_fulfilled"] = False
    summary["fold_honest"] = False
    summary["model_retrained_per_fold"] = False
    summary["confidence_interval_scope"] = (
        "Conditional spatial-block bootstrap of a fixed raster; not a fold-honest model CI or leaderboard interval."
    )
    summary["candidate_sha256"] = candidate_sha256
    summary["leaderboard_estimate"] = None
    for score in summary.get("scores", {}).values():
        score["evidence_class"] = "STATIC-REPLAY-DTI"
        score["score_scope"] = summary["score_scope"]
        score["confidence_interval_scope"] = summary["confidence_interval_scope"]
        score["leaderboard_estimate"] = None
    for difference in summary.get("paired_differences", {}).values():
        difference["evidence_class"] = "STATIC-REPLAY-DTI"
        difference["score_scope"] = summary["score_scope"]
        difference["confidence_interval_scope"] = summary["confidence_interval_scope"]
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tif", type=Path, help="Static GeoTIFF to replay; this is not a model holdout")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    grid = load_grid()
    pred = load_static_prediction(args.tif, grid)
    folds, _ = buffered_component_draw(grid, seed=args.seed, hide_frac=0.20, buffer_px=3)

    terms = sum(EH.evaluate(pred, fold, grid.footprint)[1] for fold in folds)
    zero_terms = sum(
        EH.evaluate(np.zeros_like(pred), fold, grid.footprint)[1]
        for fold in folds
    )
    summary = EH.pooled_summary(
        {"candidate": terms, "zero_control": zero_terms}, candidate="candidate"
    )
    result = mark_static_replay(summary, candidate_sha256=sha256(args.tif))
    result["input_file"] = str(args.tif)
    result["withheld_positive_pixels"] = result["scores"]["candidate"]["withheld_positive_pixels"]
    text = json.dumps(result, indent=2, allow_nan=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
