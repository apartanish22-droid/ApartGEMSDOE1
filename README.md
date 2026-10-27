# ApartGEMSDOE1 — DOE GEMS Prize Challenge submission factory

**Branch:** `arena/86539e2e-apartgemsdoe1` (fixed; all work, commits, pushes and PRs happen on this branch only).
**Status:** active.

This file is the standing project charter. Read it at the start of every work session. It consolidates the full operating prompt (deduplicated): goal, competition facts, the nine GEMSDOE focus sites, the Parallel-Run Protocol, submission-format rules, required outputs, and known irregularities/blockers.

---

## 1. Goal

Produce a **unique**, downloadable single-band GeoTIFF submission for the DOE Geologic Enhanced Mapping System (GEMS) Prize Challenge that (a) passes automated format/range validation, (b) is demonstrably not a duplicate of any prior GEMSDOE-site submission, and (c) is engineered to beat the best GEMSDOE-site submission (GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, team-published 0.2778) and move toward the organizer-confirmed public leaderboard high score.

**Organizer-confirmed public leaderboard (fetched 2026-10-27):** #1 `xiaofanhu` **0.4544** DW-Tversky (public test set). The user-cited numbers 0.4413 and 0.3195 are stale: 0.3195 is rank #25 (kpomazi) and 0.4413 does not appear in the top 29 rows. See `registry/irregularities.json` IR-01.

Source: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

---

## 2. The competition (official, verified)

- Home: https://www.drivendata.org/competitions/306/competition-doe-gems/
- Problem description / metric / submission format: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- About page: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- Data tab (login required): https://www.drivendata.org/competitions/306/competition-doe-gems/data/  (BLOCKER: no DrivenData auth in this sandbox; see IR-02)
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Rules: https://www.drivendata.org/competitions/306/competition-doe-gems/rules/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution (U-Net, John Lipor, PSU)
- Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- Forum: https://community.drivendata.org/c/gems-prize-challenge/111 · gemsprize@nlr.gov
- Sponsor: DOE Office of Geothermal; National Lab of the Rockies. End date: 2026-12-03 23:59 UTC. Prize pool $300,000.

**Metric (verbatim from page 967):** distance-weighted Tversky index, alpha=0.2 (FP penalty), beta=0.8 (FN penalty), triangular kernel k(d)=max(1-d/R,0) with R=300 m = 3 px at 100 m:

DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w + eps), over fault pixels g:
- TP_w = Σ_g max_{x: d(x,g)≤R} p(x)·k(d(x,g))
- FP_w = Σ_{x:p(x)>0} p(x)·[1 − max_g k(d(x,g))]
- FN_w = Σ_g [1 − max_{x: d(x,g)≤R} p(x)·k(d(x,g))]

**Submission format (page 967):** single-band GeoTIFF, float32, values in [0,1] (higher = fault probability), EPSG:32611 (UTM 11N), 100 m resolution, same bounds as training data, NaN/null outside bounds. The DrivenData portal rejects values outside [0,1] ("Predicted values must be in range [0, 1]").

**Verified grid geometry (from the hash-pinned owner mirror, NOT organizer-authenticated):** EPSG:32611, width 3292 × height 3730, 100 m, transform from_origin(243350, 4508550, 100, 100), footprint 5,167,373 px, catalogue positives 60,988 px. SHA-256 pins in `registry/data_manifest.json`.

**Grid provenance (read before use):** training_features.tif / labels.tif / sample_submission.tif are restored from owner-supplied GitHub mirrors (buffedlizard55-lab/GEMSDOE, /GEMSDOE24). They are integrity-pinned (sha256) but NOT organizer-authenticated. The official login-walled files must be re-verified before a weekly submission slot is spent.

---

## 3. Nine GEMSDOE focus sites — executive summary inputs

Best submission per site (team-published claims from the sites' own pages; UNVERIFIED against the organizer; never restated as organizer-confirmed):

| Site | Best submission (team-published) | Score | Unique vs other focus sites? |
|---|---|---:|---|
| GEMSDOE24 | h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan | 0.2477 | claim only; raster not independently compared here |
| GEMSDOE25 | dotted-h19-5-d2-8-20261002-e56ea318af89-nan | 0.2600 | claim only |
| GEMSDOE27 | topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan | 0.2449 | claim only |
| GEMSDOE28 | h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan | 0.2710 (of 0.2708/0.2649/0.2710/0.2707) | claim only |
| GEMSDOE30 | d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca | 0.2600 | claim only |
| GEMSDOE31 | h27-4-solo-d28-20261004-8acb75e1-nan | 0.2708 | claim only |
| GEMSDOE32 | h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros | **0.2778 ← best of the nine** | claim only |
| GEMSDOE33 | h33d-analog-tip-stepover-r30-20261004-cb490425926e | 0.2632 | claim only |
| GEMSDOE36 | anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros | 0.2750 | claim only |

Site URLs follow the pattern https://buffedlizard55-lab.github.io/GEMSDOE<N>/ (or /docs/index.html). Full link list and per-site submissions are reproduced in the raw prompt (archived in this README's source prompt); uniqueness claims on those sites are not raster-verified in this repo.

The submission to beat from these sites: **GEMSDOE32 0.2778**. PhD-level read of why it scored: the DTI (alpha 0.2, beta 0.8, R=300 m) rewards high-confidence coverage of fault pixels at low false-positive mass; a sparse "dotted" emission (~44k px of a 5.17M-px footprint) with dots on/near faults captures nearly all TP_w while FP_w stays tiny because isolated dots outside the 300 m kernel radius contribute only their own small mass and "-zeros" keeps everything outside the footprint at exactly 0. Limit: it recovers mapped faults; the private test labels are expert-labeled NEW faults, so catalogue-keyed dotting plateaus (~0.099 pooled holdout DTI on the canonical holdout evaluator for the 0.2778 incumbent, per the lane's run cards).

Can we beat 0.2778? In principle yes: widen recall on off-catalogue faults without adding FP mass, using non-catalogue geophysical/geothermal evidence (geodetic dilatation/shear, seismicity, magnetic curvature, basement depth, GDR thermal/sinter proxies). That is H1 below. Any estimate of our score is a PROJECTION, never written as a score (Protocol Rule 3).

---

## 4. Parallel-Run Protocol (binding on this lane)

1. **LANE.** Stay in the single method paragraph: holdout = hide-and-recover (withhold whole fault segments with a buffer; derive every catalogue-based feature only from visible faults; mask visible faults pixel-exactly; score pooled DTI alpha 0.2 / beta 0.8 / 300 m triangular kernel). If our raster's rank-correlation with any registry raster exceeds 0.90, or >70% of our dots fall within 3 px of one registry raster's dots → duplicate: log it, stop. Check before placement AND on final dots.
2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack, `scripts/evaluate_holdout.py` and `scripts/submission_writer.py`. If a shared tool is wrong, fix it once and report it in `registry/irregularities.json`; never keep a private fork.
3. **LABEL EVERY NUMBER:** HOLDOUT-DTI (evaluator version, # withheld positives, 95% CI) or ORGANIZER-CONFIRMED (submission-page receipt). A projection is never written as a score.
4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting it. AUC above 0.90 ⇒ leakage until proven otherwise.
5. **RUN CARD.** End with one JSON card: hypothesis; mechanism; named non-fault mimic process; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside footprint, values in [0,1], CRS/shape/transform match); submission name + note ≤ 140 chars; verdict promote / negative. Negative results are deliverables.
6. **BUDGET.** Stop after 3 experiments or 2 hours. Do not pick submissions: promotion to a real slot is a separate selector step (weekly cap on the submission page).

---

## 5. Required outputs

1. A **unique TIF** in `docs/downloads/` (downloadable from the GitHub Pages site) with an explicit "OK to download and submit?" status (see index.html).
2. `docs/executive-summary.html` — table: file to download, estimate score (labeled projection vs ORGANIZER-CONFIRMED vs team-published), uniqueness.
3. `docs/hypotheses.html` — 3–5 candidate hypotheses, layers, signature, why it catches catalogue-missing faults, differentiation, ranked by expected DTI improvement vs implementation cost; top candidate validated on the spatially-blocked holdout before any slot is used.
4. `docs/run-card.json` — one JSON run card per Protocol Rule 5 (also copied to the repo root).
5. Validation sidecars (`*-audit.json`, `*-validate.json`) for the generated TIF.
6. This README kept current.

---

## 6. How to run (this sandbox has no DrivenData auth; run data restore on any machine with GitHub access)

```bash
# 1. Restore hash-pinned competition data (training_features.tif 419 MB, labels.tif,
#    sample_submission.tif, external layers, scored registry rasters) from GitHub mirrors.
bash scripts/download_competition_data.sh

# 2. Prepare + audit the rasters.
python scripts/prepare_data.py

# 3. Generate the unique H1 submission (writes docs/downloads/*.tif, .zip, sidecars).
python scripts/generate_submission.py

# 4. Validate + lane checks against registry rasters.
python scripts/validate_submission.py docs/downloads/<your>-zeros.tif

# 5. Holdout evaluation (HOLDOUT-DTI + 95% CI; requires labels).
python scripts/evaluate_holdout.py docs/downloads/<your>-zeros.tif --out evidence/holdout_receipt.json
```

Data restore uses `gh` + codeload.github.com (allowed hosts). Mirrors are content-addressed by sha256; see `registry/data_manifest.json`.

---

## 7. Core values (Arena AI team)

- **Maximize P(Win):** every decision weighs tradeoffs and risk to maximize the probability of winning.
- **Own the Outcome:** end-to-end ownership; treat failure and success as signals.

---

## 8. Known irregularities & blockers (`registry/irregularities.json`)

IR-01: user-cited leaderboard high scores (0.4413 / 0.3195) conflict with the official public leaderboard (#1 0.4544 xiaofanhu, fetched 2026-10-27).
IR-02: DrivenData data tab requires login; no credentials in this sandbox; true holdout DTI/organizer scoring impossible here.
IR-03: GEMSDOE site scores are team-published and unverified.
IR-04: Dropbox competition-data links unreachable from this sandbox.
IR-05: no auto-submission to DrivenData; user must upload manually.

---

## 9. Official sources used

- Competition problem/format/metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Public leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- GeoDAWN survey (USGS): https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (USGS ScienceBase item 657e1d85d34e23d3533209f7)
- INGENIOUS (GBCGE): https://gbcge.org/current-projects/ingenious/ · GDR submission 1391 (DOI 10.15121/1881483, CC BY 4.0): https://gdr.openei.org/submissions/1391
- EPSG:32611: https://epsg.io/32611
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- TIGER roads / BLM claims / USGS 3DEP / USGS SGMC: external layers used by the template (see registry/data_manifest.json provenance).
