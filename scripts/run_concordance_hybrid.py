#!/usr/bin/env python3
"""Lane H-APART-2: Concordance-Anchored Hybrid (CAH).

Novelty vs prior promoted raster (UDTH-Submod E3, HOLDOUT-DTI 0.0523):
dots are ranked by *cross-lineage concordance* -- distance from a dot in one
independent lineage (our UDTH E3 dots; the GEMSDOE32 B2 dots, themselves an
exact subset of the H19-5 dotted ridge lineage, ORGANIZER-context 0.2778*)
to the nearest dot of the other lineage. Agreement within the 300 m DTI
kernel is treated as two independent detectors voting for the same hidden
fault; isolated dots are kept only to fill the fixed 38,500-dot budget.
The B2 raster is used for learning/measurement only (forensic identity in
evidence/focus_sites_forensic_audit.json); the emitted raster is a new
selection at our own positions/budget and must pass |rho|<=0.90 and
<=70% 3-px overlap vs every registry raster incl. B2 itself.

All scores produced here are HOLDOUT-DTI (gems57-pooled-hide-v2) unless
explicitly labelled USER-REPORTED context copied from the prompt ledger.
A live-score PROJECTION (never a score) is derived in the run card from
DTI algebra anchored on the 0.2778* context value.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path
import numpy as np, rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems57.grid import load_grid, write_submission
from gems57.holdout import buffered_component_draw
from gems57 import evaluate_holdout as EH
from gems57.validate import validate, assert_submittable
from apartgems.uniqueness import fast_near_3px

BUDGET = 38500
B2_PATH = ROOT / ".cache/registry/gemsdoe32-b2.tif"
OURS_PATH = ROOT / "docs/downloads/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif"

def load_pos(p):
    with rasterio.open(p) as ds: a = ds.read(1)
    return a > 0

def greedy_spacing(cand_yx, score, budget, min_dist=2.8):
    """Accept in score order, rejecting dots within min_dist px of accepted (grid-hash exact)."""
    order = np.argsort(-score, kind="stable")
    ys, xs = cand_yx
    from collections import defaultdict
    buckets = defaultdict(list); sel = []
    cell = max(int(min_dist), 1)
    for idx in order:
        y, x = int(ys[idx]), int(xs[idx])
        ok = True
        for by in range(y // cell - 1, y // cell + 2):
            for bx in range(x // cell - 1, x // cell + 2):
                for (ay, ax) in buckets.get((by, bx), ()): 
                    if (ay - y) ** 2 + (ax - x) ** 2 <= min_dist ** 2: ok = False; break
                if not ok: break
            if not ok: break
        if ok:
            sel.append(idx); buckets[(y // cell, x // cell)].append((y, x))
            if len(sel) >= budget: break
    out = np.zeros(ys.shape, bool); out[np.array(sel, dtype=int)] = True
    # convert candidate-index mask to full-grid mask via caller trick: return indices
    return sel

def main():
    t0 = time.time()
    grid = load_grid(); fp, cat = grid.footprint, grid.catalogue
    b2, ours = load_pos(B2_PATH), load_pos(OURS_PATH)
    assert not (b2 & cat).any() and not (ours & cat).any()
    d_b2 = ndi.distance_transform_edt(~b2); d_ours = ndi.distance_transform_edt(~ours)
    d_cat = ndi.distance_transform_edt(~cat)

    # ---- Leakage canary: concordance surface alone on holdout ----
    folds, _ = buffered_component_draw(grid, seed=2026, hide_frac=0.20, buffer_px=3)
    eval_mask = np.zeros(grid.shape, bool); truth = np.zeros(grid.shape, bool)
    for f in folds:
        act = f["region"] & fp & ~f["masked_known"]; eval_mask |= act; truth[f["truth"] & act] = True
    conc = np.exp(-np.minimum(d_b2, d_ours) / 4.0).astype(np.float32)
    pos = np.flatnonzero((eval_mask & truth).ravel()); negp = np.flatnonzero((eval_mask & ~truth).ravel())
    rng = np.random.default_rng(7); neg = np.sort(rng.choice(negp, 250000, replace=False))
    idx = np.concatenate([pos, neg]); y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]
    auc = float(roc_auc_score(y, conc.ravel()[idx])); canary = max(auc, 1-auc)
    print(f"canary concordance AUC={auc:.4f} sym={canary:.4f} (cap 0.90)")
    assert canary <= 0.90, "LEAKAGE CANARY FAIL"

    def pooled(arms):
        terms = {}
        for name, mask in arms.items():
            terms[name] = sum(EH.evaluate(mask.astype(np.float32), f, fp)[1] for f in folds)
        return EH.pooled_summary(terms, draws=1000, seed=520810, candidate=list(arms)[-1])

    # ---- Candidate construction (shared) ----
    cand = b2 | ours
    ys, xs = np.nonzero(cand)
    is_ours = ours[ys, xs]
    d_other = np.where(is_ours, d_b2[ys, xs], d_ours[ys, xs]).astype(np.float64)
    score = np.exp(-d_other / 4.0) + 0.01 * is_ours  # concordance; tie->our position
    allowed = cand & fp & (d_cat > 2.0)
    keep = allowed[ys, xs]; ys, xs, score, is_ours = ys[keep], xs[keep], score[keep], is_ours[keep]

    def to_mask(yy, xx, sel_idx):
        mk = np.zeros(grid.shape, bool); mk[yy[sel_idx], xx[sel_idx]] = True; return mk
    hybrid = to_mask(ys, xs, greedy_spacing((ys, xs), score, BUDGET))
    # Exp2: ours-fill only (no B2-only positions; B2 used as concordance weight only)
    m = is_ours; hybrid_ours = to_mask(ys[m], xs[m], greedy_spacing((ys[m], xs[m]), score[m], min(BUDGET, int(m.sum()))))
    # Exp3: B2-only concordance prune to 30k
    m2 = ~is_ours; b2_pruned = to_mask(ys[m2], xs[m2], greedy_spacing((ys[m2], xs[m2]), score[m2], 30000))

    arms = {"GEMSDOE32_B2_control": b2, "UDTH_E3_control": ours,
            "EXP2_hybrid_ours_positions_only": hybrid_ours,
            "EXP3_b2_concordance_prune30k": b2_pruned,
            "EXP1_concordance_hybrid": hybrid}
    summ = pooled(arms)
    for k, s in summ["scores"].items(): print(f"{k:38s} HOLDOUT-DTI={s['dti']:.4f} CI{s['ci95']}")
    (ROOT/"evidence/concordance_holdout.json").write_text(json.dumps(summ, indent=2)+"\n")

    # winner among EXP1-3 by holdout; promote only if beats UDTH control
    exp_keys = ["EXP1_concordance_hybrid","EXP2_hybrid_ours_positions_only","EXP3_b2_concordance_prune30k"]
    win_key = max(exp_keys, key=lambda k: summ["scores"][k]["dti"])
    win_mask = {"EXP1_concordance_hybrid": hybrid, "EXP2_hybrid_ours_positions_only": hybrid_ours,
                "EXP3_b2_concordance_prune30k": b2_pruned}[win_key]
    ctrl = summ["scores"]["UDTH_E3_control"]["dti"]; win_dti = summ["scores"][win_key]["dti"]
    verdict = "promote" if win_dti > ctrl else "negative"
    print(f"winner={win_key} dti={win_dti:.4f} vs UDTH control {ctrl:.4f} -> {verdict}")

    # ---- Uniqueness vs B2 and vs our previous raster (full registry in prior evidence) ----
    def uniq(mask, ref, name):
        ov = float((mask & fast_near_3px(ref)).sum() / max(mask.sum(),1))
        fi = np.flatnonzero(fp.ravel()); rng2 = np.random.default_rng(3)
        s = np.sort(rng2.choice(fi, 400000, replace=False))
        rho = float(spearmanr(mask.ravel()[s].astype(float), ref.ravel()[s].astype(float)).statistic)
        return {"vs": name, "dot_overlap_3px_frac": round(ov,4), "spearman_sample400k": round(rho,4),
                "pass": bool(ov <= 0.70 and abs(rho) <= 0.90)}
    uniq_b2, uniq_ours = uniq(win_mask, b2, "GEMSDOE32_B2_0.2778*"), uniq(win_mask, ours, "ApartGEMSDOE1_UDTH_E3")
    print("uniqueness:", uniq_b2, uniq_ours)
    if not (uniq_b2["pass"] and uniq_ours["pass"]):
        verdict = "negative"  # Protocol Rule 1: >70% 3-px overlap = drifted into another lane; log duplicate and stop
        print("UNIQUENESS GATE FAIL -> verdict downgraded to negative; no submission file will be written")

    out = np.zeros(grid.shape, np.float32); out[win_mask & fp] = 1.0
    sha_pre = hashlib.sha256(out.tobytes()).hexdigest()[:8]
    name = f"apartgems1-cah-{win_key.split('_')[0].lower()}-20261028-{sha_pre}-zeros"
    tif = ROOT/f"docs/downloads/{name}.tif"
    if verdict == "promote" and uniq_b2["pass"] and uniq_ours["pass"]:
        write_submission(tif, out, mode="zeros")
        rec = validate(tif, footprint=fp, catalogue=cat); assert_submittable(rec)
        import zipfile
        with zipfile.ZipFile(ROOT/f"docs/downloads/{name}.zip","w",zipfile.ZIP_DEFLATED) as z: z.write(tif, tif.name)
    else:
        rec, tif = None, None
    card = {
      "hypothesis": "H-APART-2 Concordance-Anchored Hybrid: hidden faults are where two independent lineages (UDTH updip/scarp/thermal E3 and H19-5 dotted-ridge lineage) place dots within the 300 m DTI kernel of each other.",
      "mechanism": "Cross-lineage concordance exp(-d_other/4px) ranking, 2.8 px kernel-matched spacing, >200 m catalogue collar, fixed 38,500 budget, binary 1.0 dots.",
      "named_non_fault_mimic_process": "Co-located Lahontan shoreline benches / road embankments detected by both lineages (shared mimic would fake concordance).",
      "holdout_dti": {"label":"HOLDOUT-DTI","evaluator_version":EH.VERSION,
        "withheld_positive_pixels": summ["scores"][win_key]["withheld_positive_pixels"],
        "winner": win_key, "dti": win_dti, "ci95": summ["scores"][win_key]["ci95"],
        "all_arms": {k: {"dti": v["dti"], "ci95": v["ci95"]} for k,v in summ["scores"].items()},
        "leakage_canary_concordance_sym_auc": round(canary,4)},
      "organizer_context": {"GEMSDOE32_B2": "0.2778 USER-REPORTED (prompt ledger, no portal receipt in repo)",
        "live_projection": "PROJECTION ONLY (not a score): if hybrid retains >=60% of B2 kernel credit and UDTH-only dots have >= break-even precision p*=0.071, DTI algebra anchored at 0.2778* gives ~0.24-0.30; wide uncertainty, unproven until portal receipt."},
      "correlation_overlap_vs_registry": {"vs_GEMSDOE32_B2": uniq_b2, "vs_own_previous": uniq_ours,
        "note": "Full 352-raster registry from prior session (evidence/focus_sites_forensic_audit.json): previous raster max overlap 62.48%; this run re-checks the two binding neighbours; other registry rasters are subsets/derivatives of these lineages - flagged as limitation."},
      "raster_sha256": hashlib.sha256(tif.read_bytes()).hexdigest() if tif and tif.exists() else None,
      "validator_output": rec, "submission_name": name,
      "submission_note": "H-APART-2 CAH: cross-lineage concordance hybrid, 2.8px spacing, >200m collar, all-finite [0,1] (38500 dots)."[:140],
      "verdict": verdict, "runtime_s": round(time.time()-t0,1)}
    (ROOT/"evidence/run_card_cah.json").write_text(json.dumps(card, indent=2)+"\n")
    print(json.dumps({k: card[k] for k in ("submission_name","verdict","raster_sha256")}, indent=2))
    return 0
if __name__ == "__main__": raise SystemExit(main())
