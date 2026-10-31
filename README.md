# ApartGEMSDOE1 · GEMS geothermal fault prediction

> **No file is cleared for download or submission. NOT CLEARED: DO NOT SUBMIT.** The H-SC1 candidate fails the literal uniqueness gate, and it does not clearly beat random placement.
>
> **Slot: not promoted.** Current lane status — stop for H-SC1 (uniqueness gate fails; no clear edge over random density).
>
> Candidate `hsc1_q090.tif` (SHA-256 `f36bf98e18cd31d8147a65cf1af377092231551dfed8df6286874167e69d3029`) is held in the local cache and is **not published**.
>
> [Executive summary](docs/executive-summary.html) · [Nine-site table](evidence/focus_nine_table.md) · [Candidate selection](evidence/candidate_selection.json) · [Run card](evidence/run_card_h-sc1-hsc1_q090.json) · [Hypotheses](evidence/hypotheses_2026-10-31.md) · [Registry inventory](evidence/registry_inventory.json)

## Future-session start-up: read before every run

1. Read this README and `evidence/candidate_selection.json` (verdict, flags, sources).
2. Read the full competition prompt. **The verbatim prompt is not stored in this repo yet** (listed as remaining work). Add it at `docs/prompt-full.md`.
3. Read `evidence/hypotheses_2026-10-31.md` and pick one lane. Stay in a single method lane per session.
4. Check the lane budget: three experiments or two hours per lane. Single-feature AUC >0.90 is leakage until proven otherwise.
5. Run the uniqueness gate on the complete registry scan before any upload decision. Fail closed.

## Project brief (condensed; full prompt not stored verbatim)

**Goal.** Place at the top of the DOE GEMS leaderboard by predicting concealed geothermal faults that are **not** in the USGS fault database. Submit one single-band float32 GeoTIFF (EPSG:32611, 100 m, values in [0, 1]). Scoring is distance-weighted Tversky, α = 0.2, β = 0.8, 300 m (3 px) kernel.

Sources: [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) · [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution). The rules and leaderboard were read on 2026-10-30 and are not re-verified here (the sandbox cannot reach those hosts).

**Working rules (standing protocol).**
1. A file is submittable only if it is unique: no more than 70% of its dots within 3 px of one registry raster, and rank correlation at most 0.90, on a complete registry scan. Check the surface and the final dots.
2. Reuse the shared template (`gems57` metric, holdout, uniqueness gate, `submission_writer`). Fix shared tools in place; do not fork.
3. Label every number **HOLDOUT-DTI** (our proxy, with evaluator version, withheld-positive count and 95% CI) or **ORGANIZER-CONFIRMED** (from a submission-page receipt). Never present a projection as a score.
4. Leakage canary: a single feature with AUC above 0.90 means leakage until proven otherwise.
5. Every run ends with a run card. Budget: three experiments or two hours per lane. Do not pick submissions; promotion is a separate selector step.

**Core values.** *Maximize P(Win)*: weigh evidence, expected value and risk. *Own the outcome*: report failures and fix shared defects.

## Current status

* **Candidate:** `apartgems1-hsc1-q090` (H-SC1 lidar convex-crest scarp traces, catalogue-free score map, q0.90).
* **Holdout, submitted policy (HOLDOUT-DTI):** 0.0508 [95% CI 0.0407, 0.0613] on 11,360 withheld positives, evaluator `gems57-pooled-hide-v3`. Proxy only.
* **Against matched random placement:** candidate minus random = +0.0072 to +0.0099 across 5 draws. The lower 95% bound is above zero in 2 of 5 draws. The advantage over random density is not established.
* **Uniqueness (literal gate):** FAIL at q0.90, q0.95 and q0.97. First duplicate: 100% overlap with a registry blanket. Sensitivity run with blankets excluded: still FAIL (99.8% overlap with a 206,895-dot lattice). See the flags in `evidence/candidate_selection.json`.
* **Leaderboard:** no organizer receipt exists for any file. The public top value read on 2026-10-30 is 0.4544 (team standing, not a file score). The prompt's 0.4413 and 0.3195 do not appear in that read.

## Prior candidate overlap (diagnostic)

* The earlier MAW-GSI TIF (`apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif`, SHA-256 `09fa04bd481d896a4dcbb808e4ef8136f8e6d0e0d88cebe9afd957db2779d62f`) is **research only, DO NOT SUBMIT**. Its 3-px forward overlap with the lattice witness is 99.68% (limit 70%).
* The H-SC1 gate failure is not caused by the prior file. It comes from registry rasters: a blanket in the literal screen, and genuine dot-set overlaps (up to 99.8%) in the sensitivity run.

## Unique among focus nine? (closest peer)

Nine-by-nine pairwise 3-px overlap (`evidence/focus_pairwise_overlap.json`). No focus file is unique to another.

| Site | Historical file | Claimed score | Estimated score | Unique among nine? (closest peer) | Submit? |
| --- | --- | --- | --- | --- | --- |
| GEMSDOE24 | `docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | 0.2477 (user claim) | not estimable | no: 100.00% to GEMSDOE25 | NO |
| GEMSDOE25 | `docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | 0.2600 (user claim) | not estimable | no: 100.00% to GEMSDOE24 | NO |
| GEMSDOE27 | `docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | 0.2449 (user claim) | not estimable | no: 98.02% to GEMSDOE24 | NO |
| GEMSDOE28 | `docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | 0.2710 (user claim) | not estimable | no: 100.00% to GEMSDOE24 | NO |
| GEMSDOE30 | `docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif` | 0.2600 (user claim) | not estimable | no: 100.00% to GEMSDOE24 | NO |
| GEMSDOE31 | `docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | 0.2708 (user claim) | not estimable | no: 100.00% to GEMSDOE24 | NO |
| GEMSDOE32 | `docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | 0.2778 (user claim) | not estimable | no: 100.00% to GEMSDOE24 | NO |
| GEMSDOE33 | `docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif` | 0.2632 (user claim) | not estimable | no: 99.71% to GEMSDOE27 | NO |
| GEMSDOE36 | `docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | 0.2750 (user claim) | not estimable | no: 97.58% to GEMSDOE27 | NO |

**GEMSDOE32 (claimed 0.2778).** It has the highest claim in the nine-site list, but no linked organizer receipt exists. Its 37,654 dots match the lattice witness count. The 0.3195 "highest" figure in the prompt does not match the leaderboard read.

## Irregularities for review

See `evidence/candidate_selection.json` (`flags`). The main ones:

* **Blanket registry raster.** ApartGEMSDOE2's `…top37654…` files are full-footprint blankets (5,106,385 positive cells, 98.8% of the footprint). Their name says 37,654 dots, but they do not contain 37,654 dots. A 3-px dot overlap against a blanket is degenerate. It is the first duplicate the literal screen hit. The sensitivity run (blankets excluded) still fails on genuine dot sets, for example the 13gems r13 lattice at 99.79%.
* **Zeros outside the footprint.** Official rule text (R1 in `evidence/official_rules_check.json`) says data outside the bounds is "null or nan". The DrivenData reference notebook writes zeros. `sample_submission.tif` uses NaN. The portal's behaviour on either is untested.
* **Unexplained portal error.** "Predicted values must be in range [0, 1]": the file that triggered it is not identified.
* **`labels.tif` is byte-identical to `existing_faults.tif`** (SHA-256 `7ba308cc…`). Consistent with R5.
* **Leaderboard conflict.** The prompt cites 0.4413 and 0.3195; the repo's 2026-10-30 read shows 0.4544 at the top.

## Reproduce

```bash
python -m pip install -r requirements.txt
python scripts/build_registry.py --workers 3                 # GitHub API via gh; rate-limited
python scripts/focus_pairwise.py
python scripts/build_scarp_crest_candidate.py --mode holdout --seed 2026 --quantiles 0.97 0.99 0.995 --json-out evidence/holdout_h_sc1_seed2026.json
python scripts/build_scarp_crest_candidate.py --mode holdout --seed 2026 --quantiles 0.90 0.95 --json-out evidence/holdout_h_sc1_experiment2.json
python scripts/paired_policy_vs_random.py
python scripts/build_scarp_crest_candidate.py --mode final --quantile 0.9 --out .cache/candidates/hsc1_q090.tif --name apartgems1-hsc1-q090 --note "H-SC1 lidar convex-crest dots (q0.90), 3px spacing, catalogue cells removed. Holdout proxy only; not cleared."
python scripts/check_uniqueness.py .cache/candidates/hsc1_q090.tif --json-out evidence/uniqueness_hsc1_q090.json
python scripts/write_run_card.py --help                      # see evidence/run_card_h-sc1-hsc1_q090.json for the arguments used
python scripts/build_submission_hub.py
.venv/bin/python -m pytest -q
```

## Limits and remaining work

* The sandbox cannot reach `drivendata.org`, `docs.nlr.gov`, `usgs.gov`, `nasa.gov` or the `github.io` pages. Competition text and the leaderboard come from the 2026-10-30 reads recorded in the repo.
* The registry is the public GitHub mirror repos listed in the prompt. It excludes private, unlinked and later uploads.
* A holdout DTI is a proxy. It scores recovery of catalogue faults, but the competition scores new faults.
* Decision needed (affects other lanes, not this one): whether blanket rasters should be excluded from the dot-overlap statistic. Excluding them does not clear H-SC1, because the sensitivity run still fails on genuine dot sets.
* Full prompt text to be added to `docs/prompt-full.md`.
* Next lanes: `evidence/hypotheses_2026-10-31.md`.
