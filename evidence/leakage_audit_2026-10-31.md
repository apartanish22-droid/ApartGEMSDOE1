# Leakage audit · 2026-10-31

Sources: `evidence/experiments/exp1_base_v3.json`, `exp2_geo_static_v3.json`, `exp3_geo_paired_static_v3.json` (evaluator `gems57-pooled-hide-v3`, arm `all`). Every number below is copied from those files; no new experiments were run. Budget: 3 experiments, all spent.

## Per-experiment result

| Run | Features | HOLDOUT-DTI (arm all) | 95% CI (quadrant jackknife) | Withheld positives | Canary (AUC > 0.90) | Status |
|---|---|---|---|---|---|---|
| E1 | base (includes catalogue-proximity features) | 0.3323 | [0.2966, 0.3681] | 22,641 | **flagged: `d`, `d_perp`** | INVALID: proximity leakage |
| E2 | geo-static (no catalogue column) | 0.0635 | [0.0514, 0.0757] | 22,641 | none (max AUC 0.609, `g_slope`) | leak-free baseline |
| E3 | geo + paired-static | 0.0704 | [0.0595, 0.0813] | 22,641 | none (max AUC 0.620, `p_corr_elev_grav`) | leak-free; see caveat 1 |

Detached arm (conservative reading): E2 0.0668 [0.0486, 0.0849]; E3 0.0713 [0.0541, 0.0885].

## Findings

1. **E1 is leakage.** Features `d` and `d_perp` (distance to a visible catalogue trace and its perpendicular component) separate withheld from visible cells on a single feature. Raw per-fold AUCs are inverted (`d` 0.091–0.141; `d_perp` 0.063–0.108). Read discriminatively, `d` reaches a per-fold maximum of 0.909 (mean 0.883) and `d_perp` a maximum of 0.937 (mean 0.916). The canary flags both because the maximum exceeds the 0.90 threshold. The model can use the same signal, because the holdout cells sit next to catalogue faults that remain visible. The 0.3323 score is therefore proximity-inflated and is not a valid estimate. It is about five times the leak-free value.
2. **E2 and E3 pass the canary.** No feature exceeds AUC 0.90. The highest single-feature AUCs are about 0.61–0.62.
3. **E3 minus E2 (paired, per cell, 8 cells).** Arm all mean +0.0106, bootstrap 95% [0.0043, 0.0180], 7/8 cells positive. Pooled gap +0.0069. Eight cells is a small sample; treat the gain as weak evidence.

## Caveat 1 · the emitted file was not the evaluated surface (critical)

The holdout score and the emitted GeoTIFF use different dot-allocation procedures:

* **Holdout** (`scripts/run_fold_honest_holdout.py` → `run_cell` → `greedy_allocate` per withheld cell, `max_dots=120,000` per cell): produced **281,318** dots in total across 16 cells.
* **Emission** (`emit_projection`): a single `greedy_allocate` on the full footprint with `k_truth = Σp` over allowed cells (**11,983.4**), `max_dots=120,000`: produced **30,562** dots.

The two allocations differ in dot count (about nine times fewer in the file), in the per-cell versus global `k_truth`, and in the surface used. **Therefore the 0.0704 holdout score does not measure the emitted file.** Its score is unmeasured. Measuring it would be a fourth experiment, which the budget does not allow. This is the main reason the file is not cleared for submission.

## Caveat 2 · proxy only

The official test labels are new faults "not included in the existing USGS fault database" (official problem page). The holdout uses the existing catalogue, so it is a proxy in both directions.

## Decision

* E2 is the clean baseline. E3 is marginally higher with weak support.
* No arm may be labelled as a leaderboard estimate. The emitted file carries no HOLDOUT-DTI label, because its own score has not been measured.
