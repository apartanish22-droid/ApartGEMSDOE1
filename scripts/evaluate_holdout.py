#!/usr/bin/env python3
"""CLI wrapper delegating directly to the unmodified shared `gems57.evaluate_holdout` module.

Note: Passing a live-submission GeoTIFF that has already zeroed out `<=200 m` around the full
`existing_faults.tif` catalogue measures static post-mask replay (erasing predictions on the 20%
withheld catalogue segments). Full out-of-fold LOQO hide-and-recover evaluation (masking only
`fold['visible']` per fold per Rule 2) is executed by `scripts/run_apartgems_pipeline.py` and
recorded in `evidence/experiments_holdout.json`.
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
        pred = src.read(1).astype(np.float64)
    pred = np.where(np.isfinite(pred) & grid.footprint, pred, 0.0)

    terms = sum(EH.evaluate(pred, f, grid.footprint)[1] for f in folds)
    zero_terms = sum(EH.evaluate(np.zeros_like(pred), f, grid.footprint)[1] for f in folds)
    summary = EH.pooled_summary({"candidate": terms, "zero_control": zero_terms}, candidate="candidate")
    out_txt = json.dumps(summary, indent=2, allow_nan=False)
    if args.out:
        args.out.write_text(out_txt + "\n")
    print(out_txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
