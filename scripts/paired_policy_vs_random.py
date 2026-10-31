#!/usr/bin/env python3
"""Paired CI: H-SC1 submitted policy vs density-matched random placement (HOLDOUT-DTI).

Reporting step, not a new experiment. Uses the same folds, evaluator and pooled
physical-block bootstrap as scripts/build_scarp_crest_candidate.py. The candidate arm
is the exact submitted policy (crest dots minus ALL mapped-catalogue cells, minus each
fold's visible catalogue). The random arm places the same number of dots uniformly on
lidar-valid footprint cells that are not on the mapped catalogue, one draw per seed.

Output: evidence/paired_policy_vs_random.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import evaluate_holdout as EH  # noqa: E402
from gems57 import load_grid  # noqa: E402
from gems57.holdout import buffered_component_draw  # noqa: E402

spec = importlib.util.spec_from_file_location("hsc1", ROOT / "scripts" / "build_scarp_crest_candidate.py")
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--quantiles", type=float, nargs="*", default=[0.90, 0.95, 0.97])
    ap.add_argument("--random-draws", type=int, default=5)
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "paired_policy_vs_random.json")
    args = ap.parse_args()

    grid = load_grid()
    fp = grid.footprint
    dec = H.decode_lidar(["step_max", "lapneg_max", "coh100"])
    valid = np.isfinite(dec["coh100"]) & fp
    score = H.crest_score(dec, valid)
    folds, _ = buffered_component_draw(grid, seed=args.seed, hide_frac=0.20, buffer_px=3)
    folds = list(folds)
    zero_terms = sum(EH.evaluate(np.zeros(fp.shape), f, fp)[1] for f in folds)
    pool = np.flatnonzero((valid & fp & ~grid.catalogue).ravel())

    out = {}
    for q in args.quantiles:
        thr = H.threshold_for_quantile(score, valid, q)
        raw = H.crest_dots(score, thr, fp)
        policy = raw & ~grid.catalogue
        n = int(policy.sum())
        cand_terms = 0
        for f in folds:
            pred = (policy & ~f["visible"]).astype(np.float64)
            cand_terms = cand_terms + EH.evaluate(pred, f, fp)[1]
        draws = []
        for d in range(args.random_draws):
            rng = np.random.default_rng(args.seed + 1000 * d + int(round(q * 1000)))
            flat = rng.choice(pool, size=n, replace=False)
            rd = np.zeros(fp.size, bool)
            rd[flat] = True
            rd = rd.reshape(fp.shape)
            rterms = 0
            for f in folds:
                pred = (rd & ~f["visible"]).astype(np.float64)
                rterms = rterms + EH.evaluate(pred, f, fp)[1]
            s = EH.pooled_summary({"candidate": cand_terms, "random": rterms,
                                   "zero_control": zero_terms}, candidate="candidate")
            draws.append(dict(draw=d, random_dti=s["scores"]["random"]["dti"],
                              random_ci95=s["scores"]["random"]["ci95"],
                              paired_candidate_minus_random=s["paired_differences"]["random"]))
        cand_s = EH.pooled_summary({"candidate": cand_terms, "random": cand_terms,
                                    "zero_control": zero_terms}, candidate="candidate")["scores"]["candidate"]
        out[f"q{q}"] = dict(
            quantile=q, threshold_score=thr, dots_submitted_policy=n,
            candidate_dti=cand_s["dti"], candidate_ci95=cand_s["ci95"],
            random_draws=draws,
            random_dti_mean=float(np.mean([d["random_dti"] for d in draws])),
            random_dti_min=float(np.min([d["random_dti"] for d in draws])),
            random_dti_max=float(np.max([d["random_dti"] for d in draws])),
        )
        print(q, n, round(cand_s["dti"], 4), round(out[f"q{q}"]["random_dti_mean"], 4))

    doc = dict(
        evidence_class="HOLDOUT-DTI", evaluator_version=EH.VERSION,
        holdout_draw=dict(seed=args.seed, hide_frac=0.20, buffer_px=3, folds=len(folds)),
        arms="candidate = submitted policy; random = matched count on non-catalogue valid cells; zero_control",
        random_draws_per_quantile=args.random_draws,
        results=out,
        read_me=("A paired CI with a point difference below zero means the random arm beats the candidate. "
                 "Each candidate/random pair uses the same physical blocks."),
    )
    args.out.write_text(json.dumps(doc, indent=1, allow_nan=False, default=float) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
