#!/usr/bin/env python3
"""Leakage canary + single-feature holdout baseline on the v3 shared evaluator.

Protocol gate 4 (README): test each feature ALONE on the holdout before trusting
any result. For every cached band this script

1. draws the shared hide-and-recover folds (``gems57.holdout.buffered_component_draw``,
   the v3 visible-only mask) for the given seeds;
2. computes a symmetric AUC on the scored domain (valid & region & ~visible),
   truth = withheld fault pixels;
3. emits the top-K pixels of that band alone (K = 37,654, the prior dot budget),
   excluding the full USGS/INGENIOUS catalogue, and scores it with the shared
   ``evaluate_holdout.evaluate`` + ``pooled_summary`` (HOLDOUT-DTI with a
   physical-block 95% CI).

It writes evidence only. It never writes a GeoTIFF and never uses a submission slot.
Any AUC > 0.90 is reported as LEAKAGE-SUSPECT until explained.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import load_grid  # noqa: E402
from gems57 import evaluate_holdout as EH  # noqa: E402
from gems57.holdout import buffered_component_draw, visible_score_mask  # noqa: E402

CACHE = ROOT / ".cache" / "features"
EVIDENCE = ROOT / "evidence" / "feature_canary_v3_2026-10-31.json"
SEEDS = (20, 21)
K_BUDGET = 37654
AUC_LEAK = 0.90
AUC_SAMPLE = 400_000


def band_names():
    prov = json.loads((CACHE / "cache_provenance.json").read_text())
    return sorted(prov["band_sha256"], key=int)


def rank_unit(values: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Label-blind percentile in [0,1] over the footprint; NaN -> 0 (lowest)."""
    out = np.zeros(values.shape, np.float64)
    v = values[footprint]
    finite = np.isfinite(v)
    idx = np.flatnonzero(finite)
    order = np.argsort(v[idx], kind="mergesort")
    ranks = np.empty(order.size, np.float64)
    ranks[order] = (np.arange(order.size) + 1) / order.size
    flat = np.zeros(v.shape, np.float64)
    flat[idx] = ranks
    out[footprint] = flat
    return out


def topk_mask(score: np.ndarray, footprint: np.ndarray, catalogue: np.ndarray, k: int) -> np.ndarray:
    pool = footprint & ~catalogue
    s = np.where(pool, score, -np.inf)
    flat = s.ravel()
    sel = np.argpartition(-flat, k)[:k]
    mask = np.zeros(flat.shape, bool)
    mask[sel] = True
    return mask.reshape(score.shape) & pool


def main() -> int:
    grid = load_grid()
    names = band_names()
    results = {}
    rng = np.random.default_rng(1)
    for seed in SEEDS:
        folds, quad = buffered_component_draw(grid, seed=seed)
        for name in names:
            band = np.load(CACHE / f"band-{int(name):02d}.npy", mmap_mode="r")
            if band.shape != grid.footprint.shape:
                raise ValueError(f"band {name} shape {band.shape} != grid")
            band = np.asarray(band, dtype=np.float32)
            score = rank_unit(band, grid.footprint)
            emit = topk_mask(score, grid.footprint, grid.catalogue, K_BUDGET)
            ent = results.setdefault(name, {"auc_by_fold": {}, "terms": None, "sym_auc": None})
            per_fold_auc = {}
            terms_all = None
            for f in folds:
                active = grid.footprint & f["region"] & ~visible_score_mask(f)
                pos = active & f["truth"]
                neg = active & ~f["truth"]
                if pos.sum() == 0:
                    continue
                pi = np.flatnonzero(pos.ravel())
                ni = np.flatnonzero(neg.ravel())
                ni = rng.choice(ni, size=min(ni.size, AUC_SAMPLE), replace=False)
                y = np.r_[np.ones(pi.size), np.zeros(ni.size)]
                s = np.r_[score.ravel()[pi], score.ravel()[ni]]
                auc = roc_auc_score(y, s)
                per_fold_auc[f"seed{seed}_{f['name']}"] = float(auc)
                prediction = np.where(emit, 1.0, 0.0)
                _res, terms = EH.evaluate(prediction, f, grid.footprint)
                terms_all = terms if terms_all is None else terms_all + terms
            ent["auc_by_fold"].update(per_fold_auc)
            if terms_all is not None:
                ent.setdefault("_terms", []).append(terms_all)
    # pooled per-band results
    out_bands = {}
    for name in names:
        ent = results[name]
        aucs = list(ent["auc_by_fold"].values())
        mean_auc = float(np.mean(aucs))
        sym = float(max(mean_auc, 1 - mean_auc))
        terms = sum(ent["_terms"]) if ent.get("_terms") else None
        if terms is not None:
            summ = EH.pooled_summary({name: terms}, candidate=name)["scores"][name]
        else:
            summ = None
        out_bands[name] = {
            "description_index": int(name),
            "mean_auc_over_folds": mean_auc,
            "symmetric_auc": sym,
            "auc_by_fold": ent["auc_by_fold"],
            "leakage_flag": "LEAKAGE-SUSPECT (AUC>0.90)" if sym > AUC_LEAK else "not flagged",
            "single_feature_top_k_holdout": summ,
        }
    # Note: pooled_summary above pools seeds x folds of one band into one block list;
    # with two seeds the same physical block can appear twice, so CIs are a
    # conservative upper bound on independence only if blocks are merged. Recorded in caveat.
    doc = {
        "record": "Leakage canary and single-feature top-K baseline (v3 shared evaluator)",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "HOLDOUT-DTI (single-feature diagnostic; not a submission)",
        "evaluator_version": EH.VERSION,
        "seeds": list(SEEDS),
        "budget_topk": K_BUDGET,
        "alpha": 0.2, "beta": 0.8, "kernel_radius_m": 300,
        "auc_threshold": AUC_LEAK,
        "caveat": ("Single-feature top-K binary emission; the 95% CI resamples physical 20 km "
                   "blocks but seeds 20 and 21 may share blocks, so intervals are indicative. "
                   "No organizer receipt; not a leaderboard estimate."),
        "bands": out_bands,
        "implementation_sha256": EH.implementation_hashes(),
    }
    EVIDENCE.write_text(json.dumps(doc, indent=2, allow_nan=False) + "\n")
    for name in names:
        b = out_bands[name]
        s = b["single_feature_top_k_holdout"]
        dti = f"{s['dti']:.4f} CI[{s['ci95'][0]:.4f},{s['ci95'][1]:.4f}] n_pos={s['withheld_positive_pixels']}" if s else "n/a"
        print(f"band {name:>2}  symAUC={b['symmetric_auc']:.3f}  {b['leakage_flag']:<12}  topK-DTI {dti}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
