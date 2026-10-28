#!/usr/bin/env python3
"""CLI wrapper delegating directly to the unmodified shared `gems57.evaluate_holdout` module.

This static-file replay is diagnostic only, NOT a fold-local evaluation of a
model that used catalogue inputs. In particular a full-catalogue mask may erase
withheld truths. It cannot establish eligibility for promotion. The legacy
H-APART-1 runner is retired; historical fold-local results are retained in
`evidence/experiments_holdout.json` but have not been independently replayed.
"""
from __future__ import annotations

import argparse
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tif", type=Path, help="Candidate GeoTIFF to evaluate on buffered whole-component holdout")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    grid = load_grid()
    folds, _ = buffered_component_draw(grid, seed=args.seed, hide_frac=0.20, buffer_px=3)
    with rasterio.open(args.tif) as src:
        if src.count != 1 or (src.shape, src.crs, src.transform) != (grid.shape, grid.crs, grid.transform):
            raise ValueError("candidate does not match the bridge grid and single-band format")
        pred = src.read(1).astype(np.float64)
    # Research TIFFs may have NaNs outside the bridge footprint; never repair
    # invalid interior predictions or values outside [0,1].
    values = pred[grid.footprint]
    if not np.isfinite(values).all() or (values < 0).any() or (values > 1).any():
        raise ValueError("candidate contains invalid values inside the footprint")
    pred = np.where(grid.footprint, pred, 0.0)

    terms = sum(EH.evaluate(pred, f, grid.footprint)[1] for f in folds)
    zero_terms = sum(EH.evaluate(np.zeros_like(pred), f, grid.footprint)[1] for f in folds)
    summary = EH.pooled_summary({"candidate": terms, "zero_control": zero_terms}, candidate="candidate")
    summary["evaluation_kind"] = "static-file diagnostic; not a fold-local model replay"
    summary["promotion_eligible"] = False
    out_txt = json.dumps(summary, indent=2, allow_nan=False)
    if args.out:
        args.out.write_text(out_txt + "\n")
    print(out_txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
