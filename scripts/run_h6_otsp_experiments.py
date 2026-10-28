#!/usr/bin/env python3
"""Run the three pre-registered H-APART-6 OTSP holdout experiments.

This script deliberately stops at selector evidence.  It does not consume a weekly
submission slot and does not write a submission GeoTIFF.  A separate promotion
step is permitted only when the winner beats the recorded H-APART-2 holdout best.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pickle
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

from apartgems.features import ensure_blind_feature_cache
from apartgems.model import (
    _rank01_on_mask,
    _score_emitted_and_detached,
    allocate_maw_gsi_dual_submodular,
)
from apartgems.otsp import compute_otsp_surfaces, ensure_otsp_static_cache
from gems57 import evaluate_holdout as EH
from gems57 import load_grid
from gems57.holdout import buffered_component_draw

BASELINE_DTI = 0.117438
BASELINE_CI95 = [0.099365, 0.136129]
BASELINE_WITHHELD = 11_360

EXPERIMENTS = (
    {
        "id": "E1",
        "name": "OTSP topographic tangent transport",
        "feature": "otsp_topographic",
        "blend_weight": 0.25,
        "specialist_fraction": 0.20,
    },
    {
        "id": "E2",
        "name": "OTSP topography + gravity tangent transport",
        "feature": "otsp_cross_physics",
        "blend_weight": 0.35,
        "specialist_fraction": 0.30,
    },
    {
        "id": "E3",
        "name": "OTSP multi-scale topography/gravity persistence",
        "feature": "otsp_persistent",
        "blend_weight": 0.50,
        "specialist_fraction": 0.40,
    },
)


def _load_h2_oof_raw(feature_dir: Path, visible: np.ndarray) -> dict:
    vis_sig = hashlib.sha256(np.packbits(visible[load_grid().footprint]).tobytes()).hexdigest()[:12]
    checkpoint = feature_dir / f"loqo_models_{vis_sig}_full.pkl"
    if not checkpoint.exists():
        raise FileNotFoundError(
            f"Missing {checkpoint}; run scripts/run_apartgems_pipeline.py once to fit the shared H-APART-2 cache"
        )
    payload = pickle.loads(checkpoint.read_bytes())
    return payload


def _base_oof_surfaces(payload: dict, folds: list[dict], fp: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p2 = np.asarray(payload["E3"]["oof_p2_raw_fp"], dtype=np.float32)
    vent = np.asarray(payload["E3"]["oof_vent_fp"], dtype=np.float32)
    unified = np.zeros(p2.shape, dtype=np.float32)
    eval_union = np.zeros(fp.shape, dtype=bool)
    for fold in folds:
        active_2d = fold["region"] & fp & ~fold["masked_known"]
        active_fp = active_2d[fp]
        r_p2 = _rank01_on_mask(p2, active_fp)
        r_vent = _rank01_on_mask(vent, active_fp)
        unified[active_fp] = 0.52 * r_p2[active_fp] + 0.48 * r_vent[active_fp]
        eval_union |= active_2d
    base = np.zeros(fp.shape, dtype=np.float32)
    vent_2d = np.zeros(fp.shape, dtype=np.float32)
    base[fp] = unified
    vent_2d[fp] = vent
    base[~eval_union] = 0.0
    vent_2d[~eval_union] = 0.0
    return base, vent_2d, eval_union


def _rank_blend_by_fold(
    base: np.ndarray,
    specialist: np.ndarray,
    folds: list[dict],
    fp: np.ndarray,
    weight: float,
) -> np.ndarray:
    out = np.zeros(fp.shape, dtype=np.float32)
    base_fp = base[fp]
    spec_fp = specialist[fp]
    for fold in folds:
        active = (fold["region"] & fp & ~fold["masked_known"])[fp]
        rb = _rank01_on_mask(base_fp, active)
        rs = _rank01_on_mask(spec_fp, active)
        out_fp = (1.0 - weight) * rb[active] + weight * rs[active]
        tmp = out[fp]
        tmp[active] = out_fp
        out[fp] = tmp
    return out


def _leakage_canaries(surfaces: dict[str, np.ndarray], folds: list[dict], fp: np.ndarray) -> dict:
    eval_2d = np.zeros(fp.shape, dtype=bool)
    truth_2d = np.zeros(fp.shape, dtype=bool)
    for fold in folds:
        active = fold["region"] & fp & ~fold["masked_known"]
        eval_2d |= active
        truth_2d |= fold["truth"] & active
    eval_fp = eval_2d[fp]
    truth_fp = truth_2d[fp]
    pos = np.flatnonzero(eval_fp & truth_fp)
    neg_pool = np.flatnonzero(eval_fp & ~truth_fp)
    rng = np.random.default_rng(20261028)
    neg = np.sort(rng.choice(neg_pool, size=min(250_000, len(neg_pool)), replace=False))
    idx = np.concatenate([pos, neg])
    y = np.concatenate([np.ones(len(pos), np.int8), np.zeros(len(neg), np.int8)])
    rows = []
    for name in ("otsp_topographic", "otsp_cross_physics", "otsp_persistent"):
        vals = surfaces[name][fp][idx].astype(np.float64)
        auc = float(roc_auc_score(y, vals))
        symmetric = max(auc, 1.0 - auc)
        rows.append({
            "feature": name,
            "roc_auc": round(auc, 6),
            "symmetric_auc": round(symmetric, 6),
            "cap": 0.90,
            "passed": bool(symmetric <= 0.90),
        })
    return {
        "evidence_class": "LEAKAGE-CANARY-HOLDOUT",
        "evaluator_version": EH.VERSION,
        "withheld_positive_pixels": int(len(pos)),
        "negative_sample_pixels": int(len(neg)),
        "features": rows,
        "max_symmetric_auc": max(r["symmetric_auc"] for r in rows),
        "all_passed": all(r["passed"] for r in rows),
    }


def main() -> int:
    started = time.time()
    grid = load_grid()
    fp = grid.footprint
    folds, _ = buffered_component_draw(grid, seed=2026, hide_frac=0.20, buffer_px=3)
    visible = folds[0]["visible"]

    print("[1/4] Loading shared H-APART-2 caches and fold-honest OOF surfaces...", flush=True)
    feat_paths = ensure_blind_feature_cache(grid, force=False)
    payload = _load_h2_oof_raw(next(iter(feat_paths.values())).parent, visible)
    base, _vent, eval_union = _base_oof_surfaces(payload, folds, fp)

    print("[2/4] Building catalogue-independent OTSP static fields and fold-visible transport...", flush=True)
    static_paths = ensure_otsp_static_cache(grid, force=False)
    otsp = compute_otsp_surfaces(visible, grid, static_paths)
    for name in ("otsp_topographic", "otsp_cross_physics", "otsp_persistent"):
        otsp[name][~eval_union] = 0.0
    canary = _leakage_canaries(otsp, folds, fp)
    print(f"      max symmetric AUC={canary['max_symmetric_auc']:.6f}; passed={canary['all_passed']}", flush=True)
    if not canary["all_passed"]:
        raise RuntimeError("OTSP leakage canary failed; stop without placement")

    d_vis = ndi.distance_transform_edt(~visible).astype(np.float32)
    d_cat = ndi.distance_transform_edt(~grid.catalogue).astype(np.float32)
    n_eval = int((eval_union & (d_vis > 2.05)).sum())
    n_live = int((fp & (d_cat > 2.05)).sum())
    holdout_target = int(round(37_654 * n_eval / max(n_live, 1)))

    print(f"[3/4] Running exactly {len(EXPERIMENTS)} pre-registered placements (target={holdout_target})...", flush=True)
    terms_by_arm = {}
    results = []
    emitted_by_id = {}
    for spec in EXPERIMENTS:
        blended = _rank_blend_by_fold(
            base, otsp[spec["feature"]], folds, fp, float(spec["blend_weight"])
        )
        emitted = allocate_maw_gsi_dual_submodular(
            blended,
            otsp[spec["feature"]],
            visible,
            eval_union,
            target_dots=holdout_target,
            vent_specialist_frac=float(spec["specialist_fraction"]),
            collar_px=2.05,
        )
        terms, detached, per_fold = _score_emitted_and_detached(emitted, folds, visible, fp)
        terms_by_arm[spec["id"]] = terms
        emitted_by_id[spec["id"]] = emitted
        score = float(EH.from_terms(terms.sum(axis=0)))
        rec = {
            **spec,
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": score,
            "detached_gt_800m_dti": float(detached),
            "withheld_positive_pixels": int(terms[:, 3].sum()),
            "emitted_oof_dots": int(emitted.sum()),
            "per_fold": per_fold,
        }
        results.append(rec)
        print(
            f"      {spec['id']} {spec['name']}: HOLDOUT-DTI={score:.6f}; "
            f"detached={detached:.6f}; dots={int(emitted.sum())}",
            flush=True,
        )

    zero_terms = sum(EH.evaluate(np.zeros(grid.shape, np.float32), fold, fp)[1] for fold in folds)
    terms_by_arm["zero_control"] = zero_terms
    winner = max(results, key=lambda row: row["dti"])
    summary = EH.pooled_summary(
        terms_by_arm,
        draws=1000,
        seed=520810,
        candidate=winner["id"],
    )
    for row in results:
        pooled = summary["scores"][row["id"]]
        row["ci95"] = pooled["ci95"]
        row["tpw"] = pooled["tpw"]
        row["fpw"] = pooled["fpw"]
        row["fnw"] = pooled["fnw"]

    beats_baseline = bool(winner["dti"] > BASELINE_DTI)
    selector_verdict = "eligible_for_separate_uniqueness_and_format_selector" if beats_baseline else "negative_stop"
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis_lane": "H-APART-6 OTSP",
        "experiment_budget_used": 3,
        "experiment_budget_cap": 3,
        "baseline": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": BASELINE_DTI,
            "ci95": BASELINE_CI95,
            "withheld_positive_pixels": BASELINE_WITHHELD,
        },
        "leakage_canary": canary,
        "experiments": results,
        "selected_holdout_winner": winner["id"],
        "winner_holdout_dti": winner["dti"],
        "beats_current_holdout_best": beats_baseline,
        "selector_verdict": selector_verdict,
        "weekly_submission_slots_used": 0,
        "elapsed_seconds": round(time.time() - started, 3),
        "bootstrap": summary["bootstrap"],
    }
    out = ROOT / "evidence/experiments_h6_otsp.json"
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (ROOT / "docs/data/experiments_h6_otsp.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"[4/4] {selector_verdict}; winner={winner['id']} ({winner['dti']:.6f}); wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
