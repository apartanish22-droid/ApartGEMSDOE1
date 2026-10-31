#!/usr/bin/env python3
"""Fold-honest hide-and-recover run on the shared gems57 harness.

This is the experiment driver for one feature set. It reuses the shared
components without forking them:

* ``gems57.holdout.build_holdout``    -- whole-segment withholding, buffer, 4 quadrant folds
* ``gems57.anatomy.fold_geometry``    -- every catalogue feature from VISIBLE faults only
* ``gems57.fitting.canary``           -- single-feature AUC leakage canary (>0.90 flags)
* ``gems57.fitting.fit_model``        -- GBM + moment calibration
* ``gems57.fitting.run_cell`` / ``pooled`` -- dot allocation and the shared DTI evaluator

Protocol (fold honest): for each test quadrant the model is fitted only on cells
from the OTHER quadrants, then predicts the withheld cells of the test quadrant.
Each cell's features come from its own visible catalogue, so no withheld trace can
reach a training or test feature.

Every number this script writes is labelled HOLDOUT-DTI with the evaluator version,
the withheld-positive count, and the 95% CIs. A final emitted raster is labelled
as a PROJECTION: it is not a score.

Usage::

    python scripts/run_fold_honest_holdout.py --features base --out evidence/exp/base.json
    python scripts/run_fold_honest_holdout.py --features geo+paired --out ... --emit-tif OUT.tif
"""
from __future__ import annotations

import argparse
import json
import hashlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from gems57 import load_grid
from gems57.anatomy import fold_geometry
from gems57.emit import greedy_allocate
from gems57.fitting import canary, fit_model, pooled, predict_surface, run_cell
from gems57.holdout import FOLD_NAMES, build_holdout
from gems57 import geo as GEO
from gems57 import evaluate_holdout as EH

FEATURE_SETS = ("base", "geo", "geo+paired", "geo-static", "geo+paired-static")
FLOOR = 0.015
MAX_DOTS = 120_000


def _full(ctx, cell) -> np.ndarray:
    m = np.zeros(ctx.grid.shape, bool)
    m[cell.bbox] = cell.active
    return m


def build_planes(grid, feature_set: str) -> dict:
    planes: dict = {}
    if feature_set.startswith("geo"):
        planes.update(GEO.load_planes(grid.footprint))
    if feature_set.startswith("geo+paired"):
        planes.update(GEO.paired_planes(grid.footprint))
    return planes


def is_static(feature_set: str) -> bool:
    """Static sets read no catalogue-derived column (leakage-free control)."""
    return feature_set.endswith("-static")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_holdout(feature_set: str) -> tuple[dict, dict]:
    grid = load_grid()
    ctx = build_holdout(grid)
    planes = build_planes(grid, feature_set) or None
    geoms = {}
    t0 = time.time()
    for cell in ctx.cells:
        geoms[cell.key] = fold_geometry(
            grid, ctx.visible(cell.key), ctx.hidden_by_cell[cell.key],
            _full(ctx, cell), cell.key, geo=planes, static_only=is_static(feature_set))
    geom_s = time.time() - t0

    canary_out = canary(list(geoms.values()))
    leakage = sorted(k for k, v in canary_out.items() if v["leakage_flag"])

    results = {"all": [], "detached": []}
    fold_models = {}
    for fold_idx, fold_name in enumerate(FOLD_NAMES):
        train = [geoms[c.key] for c in ctx.cells if c.fold != fold_idx]
        clf, scale, base = fit_model(train, seed=0)
        fold_models[fold_name] = dict(base_rate=base, scale=scale, n_train_cells=len(train))
        for cell in ctx.cells:
            if cell.fold != fold_idx:
                continue
            r = run_cell(ctx, cell, clf, scale, g=geoms[cell.key], floor=FLOOR, max_dots=MAX_DOTS)
            r["fold_name"] = fold_name
            results[cell.mode].append(r)

    summary = {}
    for arm in ("all", "detached"):
        summary[arm] = pooled(results[arm])
        summary[arm]["withheld_positive_pixels"] = int(sum(r["n_truth"] for r in results[arm]))
        summary[arm]["cells"] = [{k: r[k] for k in ("key", "n_truth", "n_dots", "dti", "coverage",
                                                    "tp", "fp", "fn", "evaluator_version")}
                                 for r in results[arm]]
    out = dict(
        feature_set=feature_set,
        features=list(next(iter(geoms.values())).feature_names),
        evidence_class="HOLDOUT-DTI",
        evaluator_version=results["all"][0]["evaluator_version"],
        primary_arm="all",
        scores={arm: {k: summary[arm][k] for k in (
            "pooled_dti", "coverage", "coverage_ci95", "dti_ci95_coverage_only",
            "dti_ci95_quadrant_jackknife", "jackknife_drop_quadrant", "n_truth",
            "withheld_positive_pixels", "n_dots", "tp", "fp", "fn")}
            for arm in ("all", "detached")},
        cells=summary,
        leakage_canary={"threshold": 0.90, "flagged_features": leakage, "per_feature": canary_out},
        fold_models=fold_models,
        geometry_seconds=round(geom_s, 1),
        ci_note=("Primary CI = quadrant jackknife (respects spatial blocking). "
                 "coverage-only CI ignores spatial heterogeneity."),
    )
    return out, dict(grid=grid, ctx=ctx, geoms=geoms, planes=planes)


def build_training_state(feature_set: str) -> dict:
    """Grid, holdout cells, planes and per-cell geometry (no CV). Used by emit-only runs."""
    grid = load_grid()
    ctx = build_holdout(grid)
    planes = build_planes(grid, feature_set) or None
    geoms = {cell.key: fold_geometry(grid, ctx.visible(cell.key), ctx.hidden_by_cell[cell.key],
                                     _full(ctx, cell), cell.key, geo=planes,
                                     static_only=is_static(feature_set))
             for cell in ctx.cells}
    return dict(grid=grid, ctx=ctx, geoms=geoms, planes=planes)


def emit_projection(state: dict, feature_set: str) -> dict:
    """Train on all 16 cells, predict the full footprint, allocate dots, return the array.

    The per-cell training geometry is released before the full-footprint pass to
    stay inside a 3 GB machine (the first emit attempt was killed by the OS).
    """
    import gc
    grid, planes = state["grid"], state["planes"]
    clf, scale, base = fit_model(list(state["geoms"].values()), seed=0)
    state["geoms"] = None
    gc.collect()
    full_visible = grid.catalogue.copy()
    allowed = grid.footprint & ~grid.catalogue
    g_final = fold_geometry(grid, full_visible, np.zeros(grid.shape, bool),
                            allowed, "final", geo=planes or None,
                            static_only=is_static(feature_set))
    p = predict_surface(clf, scale, g_final, grid.shape)
    n_feat_nan = int(np.isnan(g_final.X).sum())
    del g_final
    gc.collect()
    p[~allowed] = 0.0
    diag = dict(p_nan=int(np.isnan(p).sum()), p_inf=int(np.isinf(p).sum()),
                p_min=float(np.nanmin(p)), p_max=float(np.nanmax(p)), feature_nan=n_feat_nan,
                allowed_cells=int(allowed.sum()))
    print("[emit diagnostics]", json.dumps(diag), flush=True)
    if not np.isfinite(p).all():
        raise ValueError(f"projection contains non-finite values: {diag}")
    k_truth = float(p[allowed].sum())
    alloc = greedy_allocate(p, allowed, k_truth=k_truth, floor=FLOOR, max_dots=MAX_DOTS)
    emitted = alloc.emitted.astype(np.float32)
    return dict(values=emitted, p=p, allowed=allowed, n_dots=int(alloc.n_dots),
                k_truth_expected=k_truth, base_rate=base, scale=scale)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--features", choices=FEATURE_SETS, required=True)
    ap.add_argument("--out", type=Path, required=True, help="JSON evidence file to write")
    ap.add_argument("--emit-tif", type=Path, default=None,
                    help="Also write a template-format raster (NaN outside, dots inside) to this path")
    ap.add_argument("--emit-only", action="store_true",
                    help="Skip the holdout CV (already recorded in --out) and only emit the raster")
    args = ap.parse_args()

    if not args.emit_only:
        out, state = run_holdout(args.features)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        a = out["scores"]["all"]
        print(f"[{args.features}] HOLDOUT-DTI(all)={a['pooled_dti']:.4f} "
              f"jackknife95={a['dti_ci95_quadrant_jackknife']} withheld_pos={a['withheld_positive_pixels']} "
              f"evaluator={out['evaluator_version']} leakage_flags={out['leakage_canary']['flagged_features']}",
              flush=True)
        print(f"[{args.features}] HOLDOUT-DTI(detached)={out['scores']['detached']['pooled_dti']:.4f}", flush=True)
        del state
    if args.emit_tif:
        from gems57.submission_writer import write_template_submission
        state = build_training_state(args.features)
        proj = emit_projection(state, args.features)
        receipt = write_template_submission(
            args.emit_tif, proj["values"], state["grid"].footprint, state["grid"].catalogue,
            name=args.emit_tif.stem[:140], note=f"{args.features} dots n={proj['n_dots']}",
            metadata=dict(feature_set=args.features, n_dots=proj["n_dots"],
                          k_truth_expected=proj["k_truth_expected"], scale=proj["scale"],
                          base_rate=proj["base_rate"], evidence_class="PROJECTION-NOT-A-SCORE"))
        print(json.dumps({"emitted_tif": receipt["file"], "sha256": receipt["sha256"],
                          "n_dots": proj["n_dots"], "k_truth_expected": proj["k_truth_expected"]}, indent=2),
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
