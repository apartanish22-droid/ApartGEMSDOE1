# ApartGEMSDOE1 · Geothermal fault discovery

> **STOP — NO FILE IS READY TO SUBMIT.** The prior MAW-GSI GeoTIFF passes the local finite/range/grid preflight against owner-mirror files, but its zero-outside policy conflicts with the official null/NaN requirement and 99.68% of its dots overlap a registered lattice within three pixels, exceeding the 70% internal protocol limit. The surface gate is unverified. No new submission-candidate GeoTIFF or competition submission was made; disposable format-test files were not candidates. Archived H-APART-6 v2 experiments predated discovery of the witness.
>
> [Open the dashboard](docs/index.html) · [Executive summary and submission guide](docs/executive-summary.html) · [Current negative run card](evidence/run_card.json) · [Official rule excerpts](evidence/official_rules_check.json) · [Reproducible witness audit](evidence/literal_witness_audit.json) · [Prior three-pass review](evidence/review_passes.md) · [2026-10-30 repo review](evidence/repository_review_2026-10-30.md) · [Overlap and metric verification 2026-10-30](evidence/repo_review_2026-10-30_overlap.md)
>
> [Download the **prior TIFF for research only — do not submit**](docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif) · SHA-256 `09fa04bd481d896a4dcbb808e4ef8136f8e6d0e0d88cebe9afd957db2779d62f`

## Future-session start-up: read before every run

**Objective.** Build an evidence-led, original fault-prediction GeoTIFF for geothermal exploration, and say plainly whether any file is safe to download or submit. The nine focus sites are GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36. Their historical scores are user-reported claims, not submission receipts; the reported GEMSDOE32 value 0.2778 is not explained by geometry alone. Its support matches GEMSDOE25 after a two-pixel catalogue collar is removed, which suggests—but does not prove—a redundancy-pruning mechanism under max-kernel DTI. Do not turn this into a causal claim, score estimate, or promotion without hidden-label evidence.

**Current lane status — stop.** The “single method” paragraph in the supplied request was not unambiguously identified. Repo context records an inherited H-APART-6 OTSP lane, three archived v2 experiments, and a later mandatory duplicate stop. The existing candidate overlaps one pinned lattice witness by 37,533/37,654 dots (99.6787%, over the 70% limit); the pre-placement surface and complete registry are unavailable, and the training-feature cache is absent from this checkout. Do not choose a replacement method, run experiments, generate a new TIFF, or use a slot until a new lane is explicitly assigned and its prerequisites are met. See the [ranked future hypotheses](evidence/next_hypotheses.md) for design candidates, not permission to run them.

### Mandatory gates

1. **One lane, originality before placement.** Before implementation, rank 3–5 untried geological hypotheses by expected DTI improvement and cost. For each, name the layers and physical signature, why it could find a catalogue-missing fault, how it differs from this repository, a named non-fault mimic, and the official source/data-availability check. Stay within the assigned single method. Check registry rank correlation on each surface before placement and 3-pixel dot overlap after placement; stop if any correlation exceeds 0.90 or overlap exceeds 70%. No density exemptions.
2. **Reuse shared tools.** Reuse the template feature stack, shared holdout evaluator, and `submission_writer.py`; fix shared tools instead of making private forks. Hide whole fault segments with a buffer, derive catalogue features only from visible faults, mask visible faults pixel-exactly, and use pooled DTI with α=0.2, β=0.8, and a 300 m triangular kernel.
3. **Leakage and score labels.** Test every feature alone on holdout; AUC >0.90 is leakage until explained. A measured result must be `HOLDOUT-DTI` with evaluator version, withheld-positive count, and 95% CI. Use `ORGANIZER-CONFIRMED` only for a score tied to an actual submission-page receipt. Never call a projection a score or infer leaderboard performance from a holdout.
4. **Run card and budget.** Record hypothesis, mechanism, named non-fault mimic, holdout DTI/CI, registry comparisons, raster SHA-256, format/grid validation, submission name and note ≤140 characters, and promote/negative verdict. Stop after at most three experiments or two hours, and immediately on either duplication threshold. A separate selector—not the experiment runner—chooses a real weekly slot within the current cap.
5. **Review and report.** Verify claims against official sources, preserve limitations and source links, run three implementation/review passes, and publish negative results honestly. No local validation is organizer acceptance; no upload is authorized without all gates and separate selector approval.

**Future-session checklist:** read this section, the latest review in [`evidence/review_passes.md`](evidence/review_passes.md), the run cards, and [`evidence/official_rules_check.json`](evidence/official_rules_check.json); confirm the assigned lane and current stop state; check whether required data/cache is actually present in this checkout; only then proceed. Keep the public feed fail-closed and do not revive retired runners.

**Core values:** *Maximize P(Win)* means weigh evidence, expected value, and risk rather than spending a slot on a weak or duplicated method. *Own the Outcome* means report failure, fix shared defects, and preserve reproducible negative evidence.

## Executive summary · nine requested sites

These are the highest historical files **named in the user prompt**, not a complete census. Prompt values are unverified user reports; no submission-page receipts were found. The future leaderboard estimate is unavailable for every row. The focus-nine column reports each file's maximum directed 3-pixel overlap with its closest peer; all nine exceed the 70% cap. The separate prior-candidate overlap is diagnostic only and does not define focus-nine uniqueness. Do not resubmit these historical files as new.

| Site | Historical file (research only) | Method (owner-described) | Prompt claim | Future estimate | Unique among focus nine? (closest peer) | Prior candidate overlap (diagnostic) | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/9e185929eeaa6244f96c3022cf3462faa8ca4de0/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif?raw=1) | Owner-described 1.5-pixel thinning of H19-5 ridges. | 0.2477 (user claim, unconfirmed) | Unavailable | NO · focus-nine overlap exceeds 70%; 100.00% within 3 px of GEMSDOE25 | Prior-candidate overlap 49.94% (diagnostic only) | Do not resubmit |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/fb1db37274776a29dbc48abe55b2e531f2ba6aad/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif?raw=1) | Owner-described 2.8-pixel thinning of H19-5 ridges. | 0.2600 (user claim, unconfirmed) | Unavailable | NO · focus-nine overlap exceeds 70%; 100.00% within 3 px of GEMSDOE24 | Prior-candidate overlap 48.56% (diagnostic only) | Do not resubmit |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/6704fa2a5133e751df2516feb2e32565ad5fc1df/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif?raw=1) | Owner-described topographic gap closure added to a D1.5 dotted map. | 0.2449 (user claim, unconfirmed) | Unavailable | NO · focus-nine overlap exceeds 70%; 98.02% within 3 px of GEMSDOE24 | Prior-candidate overlap 50.85% (diagnostic only) | Do not resubmit |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/9509b73eaf35f66d0b23fce63b2540ceff2a88e0/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif?raw=1) | Owner-described one-pixel collar prune plus blind step-over rungs on D2.8. | 0.2710 (user claim, unconfirmed) | Unavailable | NO · focus-nine overlap exceeds 70%; 100.00% within 3 px of GEMSDOE24 | Prior-candidate overlap 47.36% (diagnostic only) | Do not resubmit |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | [`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/31696c6541cfc54620ff850a748c51625461f27f/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif?raw=1) | Owner-described D2.8 Poisson-disk baseline; footprint values equal GEMSDOE25. | 0.2600 (user claim, unconfirmed) | Unavailable | NO · focus-nine overlap exceeds 70%; 100.00% within 3 px of GEMSDOE24 | Prior-candidate overlap 48.56% (diagnostic only) | Do not resubmit |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/) | [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/06930b9d03473a9313094a4f2312c4fc6efd4fbb/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif?raw=1) | Owner-described solo / one-pixel catalogue-collar pruning on D2.8. | 0.2708 (user claim, unconfirmed) | Unavailable | NO · focus-nine overlap exceeds 70%; 100.00% within 3 px of GEMSDOE24 | Prior-candidate overlap 47.88% (diagnostic only) | Do not resubmit |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/) | [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/97597a066d1c61d2c226fdba349716f41b30c1c6/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif?raw=1) | D2.8 set minus points at distance ≤2 pixels from mapped catalogue (verified support identity). | 0.2778 (user claim, unconfirmed) | Unavailable | NO · focus-nine overlap exceeds 70%; 100.00% within 3 px of GEMSDOE24 | Prior-candidate overlap 46.71% (diagnostic only) | Do not resubmit |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/3eaf85efb49f364b84f8be04e8b084b12d0303b9/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif?raw=1) | Owner-described analog fault-tip and step-over additions on D2.8. | 0.2632 (user claim, unconfirmed) | Unavailable | NO · focus-nine overlap exceeds 70%; 99.71% within 3 px of GEMSDOE27 | Prior-candidate overlap 48.36% (diagnostic only) | Do not resubmit |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/) | [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/e280188adbbe762e6b7ac6f3b8e105e8e7915026/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif?raw=1) | Owner-described Andersonian geothermal PINN additions to the B2 base. | 0.2750 (user claim, unconfirmed) | Unavailable | NO · focus-nine overlap exceeds 70%; 97.58% within 3 px of GEMSDOE27 | Prior-candidate overlap 47.41% (diagnostic only) | Do not resubmit |

The re-audit confirms GEMSDOE32 B2's support equals GEMSDOE25's support outside a two-pixel catalogue collar; GEMSDOE25 and GEMSDOE30 have identical footprint values. The user-reported GEMSDOE32 value of 0.2778 has no linked organizer receipt. The official max-kernel DTI makes reduced redundancy a plausible explanation, not proof; hidden labels are unavailable. No result here establishes that a new method will exceed it.

## Official rule check (verified 2026-10-30)

Quoted excerpts and sources are in [`evidence/official_rules_check.json`](evidence/official_rules_check.json).

* **Format:** [official problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — "data outside the bounds is null or nan", values between 0 and 1, float32, single layer, EPSG 32611, 100 m.
* **Metric:** same page — distance-weighted Tversky with α=0.2, β=0.8 and R = 300 m (3 px).
* **Test labels:** same page — the scored faults are new faults "not included in the existing USGS fault database". The repository's holdout uses the existing catalogue, so it is only a proxy.
* **Limits and originality:** [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — three submissions per week (§3.2), one final submission (§3.4), originality warranty (A.5 item 1), and a generative-AI disclosure in the narrative (§3.2).
* **Reference solution:** [drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) writes raw float predictions with no NaN step, georeferenced from the labels raster.
* **Leaderboard:** [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) showed a top public DW-Tversky of **0.4544** (direct read on 2026-10-30; the scheduled feed script failed the same day, see `docs/data/public_feed.json`). This is a team-level public standing—not a file receipt, hidden-test score, or future estimate. The prompt's 0.4413 and 0.3195 do not match that page, and the prompt's site claims (0.2449–0.2778) are unconfirmed.
* **Unresolved:** whether the portal accepts NaN outside the footprint, and which file produced the reported "Predicted values must be in range [0, 1]" error. A NaN-outside variant with identical in-footprint values reproduces the sample template's NaN mask exactly (verified locally, not uploaded).

## Current result and limitations

* **HOLDOUT-DTI, historical only:** 0.1174 [0.0994, 0.1361], evaluator `gems57-pooled-hide-v2`, 11,360 withheld positives, 95% CI. This prior run used a scoring mask that included buffer-removed non-visible catalogue pixels; it is not a comparable v3 baseline or a leaderboard prediction. No v3 model run was performed after the duplicate stop.
* **Literal uniqueness:** 37,533/37,654 prior dots overlap the [pinned lattice witness](https://github.com/buffedlizard55-lab/13GEMSDOE/blob/92ee6f074323f161eed837b80ec3ee5b662e26f5/docs/downloads/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif); only one witness is necessary to prove failure, but this is not a complete registry inventory. The word duplicate here means protocol overlap, not byte identity.
* **Feasibility:** the lattice leaves 6,514 allowed cells outside its halo, so a 37,654-dot budget cannot pass. A budget no larger than 21,713 is necessary against this witness, not sufficient for quality or uniqueness.
* **Format:** the prior file has one float32 band, finite [0,1] values, and matches the stored sample grid. Its outside-footprint cells are zeros. The official rule requires null/NaN outside the bounds (verified below), so this file does **not** match the rule. This is local preflight only, not organizer acceptance.
* **Access:** the [competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) redirected to login; no hidden labels, submission-page receipt, quota, or authorized upload session is available. Mirror hash equality does not prove official origin. The official reference solution supports CPU as well as GPU.
* **Official sources:** [problem and DTI](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [DOE GDR INGENIOUS](https://gdr.openei.org/submissions/1391), and the [research source register](evidence/research_sources.md).

## Archived H-APART-6 OTSP experiment

Before discovery of the lattice witness, exactly three v2 orientation-transport arms were measured. The best was **HOLDOUT-DTI 0.110930 [0.094184, 0.128997]**, evaluator `gems57-pooled-hide-v2`, 11,360 withheld positives, 95% CI. It lost to its historical v2 comparator; maximum feature-canary symmetric AUC was 0.672831 (<0.90). This is archived and not comparable to v3, no H6 GeoTIFF was written, and zero slots were used. See the [H6 run card](evidence/run_card_h6_otsp.json) and [three-arm evidence](evidence/experiments_h6_otsp.json).

## Reproduce the negative decision

```bash
python -m pip install -r requirements.txt
python scripts/audit_literal_witness.py             # downloads one pinned witness through gh; never submits
python scripts/audit_historical_focus.py           # nine pinned GitHub mirror files; no model experiment
python scripts/audit_holdout_mask.py               # rebuild masks only; no model score
python scripts/validate_submission.py docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif --format-only
python scripts/run_apartgems_pipeline.py          # deliberately exits nonzero: this lane is stopped
pytest -q
```

The former private density-exempt uniqueness gate and automatic-promotion runner are retired. Shared literal checks live in `src/gems57/uniqueness.py`; the corrected visible-only mask is `gems57-pooled-hide-v3`. Before a new lane can run, supply an auditable complete accessible registry and same-v3 baseline, rerun all feature canaries, verify external-data provenance, and perform surface gates **before** placement. Do not force predictions into the lattice's uncovered slivers merely to game the overlap rule.


# SESSION MANDATE — read before every work session

The following is the standing project mandate. It defines the objective, the gates,
the budget, and the definition of done. Re-read it at the start of every session.

## Objective

Build a geothermal fault-discovery submission for the DOE GEMS Prize Challenge
(DrivenData competition 306) that places top of the leaderboard. Generate a
UNIQUE TIF submission for the competition. Do not copy a previous submission
unless it is for learning and education; a unique TIF submission must be
generated. It must be obvious whether it is OK to download and submit the
generated TIF submission.

Focus sites: GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31,
GEMSDOE32, GEMSDOE33, GEMSDOE36. Produce an executive summary on every site
that is clear and obvious which is the best submission to submit to obtain a
high score on the leaderboard. Each entry must be unique and not an exact
duplicate of any previous submission from the same GEMSDOE sites. Keep iterating
and testing until the highest-scoring submission exists to download and submit.

The submission page requires a single-band GeoTIFF (.tif), or a .zip containing
a single GeoTIFF, matching the submission format's CRS, shape, and geotransform.
Values must be in range [0, 1]. The file must have a unique name and an optional
note of at most 140 characters (e.g. "clustering with k=25"). There must be an
easy-to-download submission TIF; the download must be obvious at the beginning
of the site / executive summary. Inspection must happen through the project and
be validated for submission without human intervention.

## Reported scores (unverified user claims, not organizer receipts)

GEMSDOE32 h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778 (highest named)
GEMSDOE24: 0.2477 · GEMSDOE25: 0.2600 · GEMSDOE27: 0.2449 · GEMSDOE28: 0.2710 /
0.2649 / 0.2710 / 0.2707 · GEMSDOE30: 0.2600 · GEMSDOE31: 0.2708 · GEMSDOE33:
0.2632 · GEMSDOE36: 0.2750

Current competition leaderboard GEMSDOE high score: 0.4413 (prompt figure; the
official page showed 0.4544 as a team-level public standing on 2026-10-30, not
a file receipt or future estimate).

Key links:
- Competition page: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- About page: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- Data page (login required): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- INGENIOUS: https://gbcge.org/current-projects/ingenious/
- EPSG 32611: https://epsg.io/32611
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- Official rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf

## Parallel-run protocol

1. LANE. Your lane is the single method paragraph. Stay inside it. If your
raster's rank-correlation with any registry raster exceeds 0.90, or more than
70% of your dots fall within 3 px of one registry raster's dots, you have
drifted into another lane: log it as a duplicate and stop. Check on the surface
before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack,
evaluate_holdout.py and submission_writer.py. Holdout = hide-and-recover: withhold
whole fault segments with a buffer, derive every catalogue-based feature only
from the visible faults, mask visible faults pixel-exactly, score pooled DTI
(alpha 0.2, beta = 0.8, 300 m triangular kernel). If a shared tool is wrong, fix
it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld
positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page
receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any
result. AUC above 0.90 means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault
process that could mimic it; holdout DTI + CI; correlation/overlap vs registry;
raster sha256; validator output (no NaN inside the footprint, values in [0,1],
CRS/shape/transform match); submission name + note of at most 140 characters;
verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after 3 experiments or 2 hours. Do not pick submissions:
promotion to a real slot is a separate selector step, within the weekly cap on
the submission page.

## Competition facts (official)

- Task: predict geological faults indicative of geothermal resources; scored
faults are new faults NOT included in the existing USGS fault database.
- Metric: distance-weighted Tversky index, alpha = 0.2, beta = 0.8, triangular
kernel R = 300 m (3 px at 100 m).
- Format: single-band GeoTIFF, float32, values in [0, 1], EPSG:32611, 100 m,
same bounds as training data; data outside the bounds is null or NaN.
- Limits: three submissions per week, one final submission; originality
warranty; generative-AI disclosure in the narrative.

## Known irregularities (flagged for review)

- The DrivenData data page redirects to login; training_features.tif,
labels.tif, sample_submission.tif, 1m_DEM_links.csv cannot be auto-downloaded
here. Bridge files in data/ are owner-mirror copies, not organizer-authenticated.
- The prior candidate overlaps a pinned registry witness at 99.68% (> 70% limit);
the lane is stopped and the prior file is research only, do not submit.
- The portal's acceptance of NaN outside bounds vs the project's all-finite
zeros-outside policy is unresolved ("Predicted values must be in range [0, 1]"
error reported on submission).
- All site score claims are unverified user reports without organizer receipts.

## Definition of done for a session

Executive summary subpage with an obvious one-click download of a unique,
format-validated TIF; a table listing file to download, estimated score (labelled
as projection or unverified claim), and uniqueness vs the other GEMSDOE sites;
clear statement of whether the file is OK to download and submit; run-card JSON
with verdict; hypothesis ranked against alternatives; no unverified score claimed
as a score. Commit, open a PR from the working branch, and merge to main.

