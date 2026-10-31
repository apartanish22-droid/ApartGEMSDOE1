# ApartGEMSDOE1 · GEMS DOE geothermal fault discovery

> **Answer: No. Do not submit the new GeoTIFF.** It is valid in format, but it **fails the project's uniqueness gate** (186 registry rasters exceed 70% 3-px overlap), and **its own score has not been measured**. Full decision and automated checks: **[Download and submit](docs/download-and-submit.html)** (also the Pages home).

## Start-up · read before every session

This repository carries a standing brief. Read **[`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md)** first. It is a condensed copy of the user's standing requirements (goal, format rules, parallel-run gates, labels, budget, verification passes, irregularities, and a session checklist). The rules below are copied from it and must be kept in sync.

- **Future-session start-up: read before every run.** Read the brief, the decision record [`evidence/submission_decision_2026-10-31.json`](evidence/submission_decision_2026-10-31.json), and the [leakage audit](evidence/leakage_audit_2026-10-31.md).
- **Current lane status — stop.** The E3 lane (geo+paired-static) stopped at the uniqueness gate; its raster is not cleared.
- **Single method per lane.** Each session runs one preregistered method; a duplicate of another lane stops.
- **AUC >0.90 is leakage** until explained. The leakage canary flagged E1 (`d`, `d_perp`), which is therefore invalid.
- **Budget:** at most three experiments or two hours. Both are spent (E1, E2, E3).
- **Labels:** every number is `HOLDOUT-DTI` (evaluator, withheld-positive count, 95% CI) or `ORGANIZER-CONFIRMED`. Projections are never scores.
- **Gates:** lane assignment; correlation ≤0.90 and 3-pixel overlap ≤70% against the registry; submission name and note ≤140 characters; format per the official rule (values in [0,1]; null/NaN outside bounds).

## Executive summary · nine focus sites

Each site has one historical file named in the prompt, so the highest-scoring file per site is that file. **The scores are user-reported and unconfirmed.** The leaderboard estimate is unavailable for every row.

| Site | File to download (historical, research only) | Prompt claim (unconfirmed) | Estimated score | Unique vs the other focus sites? (closest peer) | Decision |
| --- | --- | --- | --- | --- | --- |
| GEMSDOE24 | [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif`](https://buffedlizard55-lab.github.io/GEMSDOE24/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) | 0.2477 (user-reported) | Not estimable (no organizer receipt; not holdout-measured) | **No** · 100.00% of its dots within 3 px of GEMSDOE25 | **Do not submit** (not unique) |
| GEMSDOE25 | [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`](https://buffedlizard55-lab.github.io/GEMSDOE25/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) | 0.2600 (user-reported) | Not estimable (no organizer receipt; not holdout-measured) | **No** · 100.00% of its dots within 3 px of GEMSDOE24 | **Do not submit** (not unique) |
| GEMSDOE27 | [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif`](https://buffedlizard55-lab.github.io/GEMSDOE27/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) | 0.2449 (user-reported) | Not estimable (no organizer receipt; not holdout-measured) | **No** · 98.02% of its dots within 3 px of GEMSDOE24 | **Do not submit** (not unique) |
| GEMSDOE28 | [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`](https://buffedlizard55-lab.github.io/GEMSDOE28/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) | 0.2710 (user-reported) | Not estimable (no organizer receipt; not holdout-measured) | **No** · 100.00% of its dots within 3 px of GEMSDOE24 | **Do not submit** (not unique) |
| GEMSDOE30 | [`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`](https://buffedlizard55-lab.github.io/GEMSDOE30/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | 0.2600 (user-reported) | Not estimable (no organizer receipt; not holdout-measured) | **No** · 100.00% of its dots within 3 px of GEMSDOE24 | **Do not submit** (not unique) |
| GEMSDOE31 | [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif`](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) | 0.2708 (user-reported) | Not estimable (no organizer receipt; not holdout-measured) | **No** · 100.00% of its dots within 3 px of GEMSDOE24 | **Do not submit** (not unique) |
| GEMSDOE32 | [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | 0.2778 (user-reported) | Not estimable (no organizer receipt; not holdout-measured) | **No** · 100.00% of its dots within 3 px of GEMSDOE24 | **Do not submit** (not unique) |
| GEMSDOE33 | [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](https://buffedlizard55-lab.github.io/GEMSDOE33/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | 0.2632 (user-reported) | Not estimable (no organizer receipt; not holdout-measured) | **No** · 99.71% of its dots within 3 px of GEMSDOE27 | **Do not submit** (not unique) |
| GEMSDOE36 | [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | 0.2750 (user-reported) | Not estimable (no organizer receipt; not holdout-measured) | **No** · 97.58% of its dots within 3 px of GEMSDOE27 | **Do not submit** (not unique) |

**Best submission pick:** none cleared. Highest user-reported value: **GEMSDOE32 at 0.2778**, with no linked organizer receipt. GEMSDOE25 and GEMSDOE30 have identical footprint values; GEMSDOE32's support equals GEMSDOE25's outside a two-pixel catalogue collar.

Official top public DW-Tversky read directly from the [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) on 2026-10-30: **0.4544** (team-level; not a receipt for any file). The prompt's values 0.4413 and 0.3195 do not match this reading.

## The new GeoTIFF · decision

| Item | Value |
| --- | --- |
| File | [`docs/downloads/apartgems-e3-geo-paired-static-30562dots-NOT-CLEARED-20261031.tif`](docs/downloads/apartgems-e3-geo-paired-static-30562dots-NOT-CLEARED-20261031.tif) |
| SHA-256 | `c4d504b8a09f94a6f0b2a757eda60bc69095b21bc95cfae0a626dfd4bf76468e` |
| Submission name / note | `apartgems-e3-paired-static-30562dots` · geo+paired-static full-footprint dots n=30562; not holdout-measured; uniqueness gate failed |
| Format (template validator, against the official sample) | **PASS**: float32, 1 band, EPSG:32611, 3730×3292, 100 m, transform equal, NaN outside footprint, values {0,1} inside, no catalogue dots |
| Exact copy (git blob, 3,273 GeoTIFF blobs, 92 owner repos) | **None** |
| Spatial gate (1,817 `docs/downloads` rasters; 3-px forward overlap ≤70%, ρ ≤0.90) | **FAIL**: 186 flagged (137 sparse dot sets, 49 dense surfaces); 24 rasters could not be compared; 1,456 other GeoTIFFs not spatially scanned |
| Holdout score for this file | **Not measured.** The holdout allocated dots per cell (281,318 dots); the file uses one full-footprint allocation (30,562 dots). |
| OK to download? | For inspection and records only |
| **OK to submit?** | **No** |

Evidence: [`evidence/registry/uniqueness_geo_paired_static_dots.json`](evidence/registry/uniqueness_geo_paired_static_dots.json) (scan), [`evidence/registry/github_tree_enumeration.json`](evidence/registry/github_tree_enumeration.json) (inventory).

## GEMSDOE32 · why 0.2778 is highest, and whether higher is possible

**Verified:** support(GEMSDOE32) = support(GEMSDOE25) outside a two-pixel catalogue collar (0 differing pixels; [`evidence/focus9_reaudit.json`](evidence/focus9_reaudit.json)). GEMSDOE32 therefore appears to be GEMSDOE25 with dots within two pixels of the mapped catalogue removed.

**Mechanism (hypothesis, not proven):** the DW-Tversky metric (α=0.2 for false positives, β=0.8 for missed truth, R = 300 m) credits each truth pixel by its nearest prediction. Removing catalogue-adjacent dots reduces false-positive mass and keeps the credited coverage, if the new faults are not adjacent to the catalogue. Whether that is what drives 0.2778 cannot be tested: hidden labels and organizer receipts are unavailable.

**Can we exceed it?** Not shown. Our only leak-free estimate is a holdout proxy (E2 0.0635; E3 0.0704, both `HOLDOUT-DTI`, `gems57-pooled-hide-v3`). It is on a different scale from the leaderboard and does not measure any submission file. The catalogue-adjacent E1 result (0.3323) is invalid leakage. The holdout cannot yet say whether any candidate beats 0.2778.

## Holdout and leakage (evidence)

| Run | Features | HOLDOUT-DTI (arm all) | 95% CI | Canary | Status |
| --- | --- | --- | --- | --- | --- |
| E1 | base (catalogue-proximity features) | 0.3323 | [0.2966, 0.3681] | flags `d`, `d_perp` | **Invalid** (leakage) |
| E2 | geo-static | 0.0635 | [0.0514, 0.0757] | none | Leak-free baseline |
| E3 | geo + paired-static | 0.0704 | [0.0595, 0.0813] | none | Leak-free; weak +0.0069 over E2 (8 cells); not this file's score |

Details: [`evidence/leakage_audit_2026-10-31.md`](evidence/leakage_audit_2026-10-31.md). Experiments: `evidence/experiments/`.

## Untried hypotheses (ranked; none validated here)

Full table with layers, signatures, mimics and data gates: [`evidence/next_hypotheses.md`](evidence/next_hypotheses.md). Ranking is qualitative; no DTI gain is claimed.

1. **Signed paired-flank agreement** — detrended elevation, magnetic anomaly and isostatic gravity; a fault shows matched flank contrasts. Named mimics: lithologic contacts, incised alluvial-fan channels, erosional scarps. **Top one: not run.** Its holdout check would need a fourth experiment, which the budget does not allow.
2. **Flight-line repeatability weighting** — USGS GeoDAWN flight-line measurements and line metadata. Named mimics: lithologic boundaries, regional magnetic gradients, survey-leveling artifacts.
3. **Depth-normalized paired thermal gradients** — DOE GDR temperature probes. Named mimics: uneven drilling/sampling, groundwater flow, seasonal effects, lithology-controlled conductivity.
4. **ASTER emissivity contrast along independent edges** — NASA ASTER GED. Named mimics: quartz-rich dunes, exposed lithologic units, vegetation/albedo differences, surface-cover effects.

## Official rules and sources

* Problem, format and metric: [DrivenData competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — "data outside the bounds is null or nan", values 0–1, float32, single layer, EPSG 32611, 100 m; DW-Tversky α=0.2, β=0.8, R=300 m; test faults are "not included in the existing USGS fault database".
* Rules: [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — three submissions per week (§3.2), one final submission (§3.4), originality warranty (A.5), generative-AI disclosure (§3.2).
* Leaderboard: [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) (0.4544 on 2026-10-30).
* Data: [competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) redirects to login; not obtained.
* [Reference solution](https://github.com/drivendataorg/gems-prize-reference-solution); [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and); [DOE GDR INGENIOUS](https://gdr.openei.org/submissions/1391).

Structured record: [`evidence/official_rules_check.json`](evidence/official_rules_check.json).

## Remaining work

1. Obtain organizer-confirmed scores for any historical file (submission-page receipts); none exist here.
2. Assign a lane and run the top hypothesis (signed paired-flank agreement) on the leak-free holdout, with a per-cell allocation that matches the emitted file, before any slot is used.
3. Scan the other 1,456 GeoTIFF blobs spatially; resolve the 24 unreadable or mismatched rasters.
4. Decide the 3-px forward-overlap rule for dense surfaces (the gate is currently applied as written).
5. Confirm the portal's NaN-outside handling and the "Predicted values must be in range [0, 1]" error with the organizers.
6. Verify the GitHub Pages URL for this repository (links here are relative).

## Limitations

* Holdout is a proxy: it uses the USGS catalogue, while the scored test faults are new faults outside it.
* Holdout uses eight paired cells for the E3 vs E2 gain; treat it as weak.
* The emitted file's score is unmeasured (different allocation from the holdout).
* Owner-mirror data (`6GEMSDOE`) are not organizer downloads; hashes verify mirror equality only.
* Registry scan covers `docs/downloads` only; the exact-copy check covers all 3,273 GeoTIFF blobs.
* The generative-AI disclosure required by the rules has not been drafted.

## Reproduce

```bash
python -m pip install -r requirements.txt
python scripts/download_competition_data.sh   # needs DrivenData login; not available here
python scripts/prepare_data.py --fetch        # owner mirror, pinned hashes
python scripts/registry_scan.py --enumerate   # GitHub tree listing (needs gh auth)
python scripts/registry_scan.py docs/downloads/apartgems-e3-geo-paired-static-30562dots-NOT-CLEARED-20261031.tif --out evidence/registry/uniqueness_geo_paired_static_dots.json
python scripts/validate_submission.py docs/downloads/apartgems-e3-geo-paired-static-30562dots-NOT-CLEARED-20261031.tif --format-only
python scripts/build_submit_page.py           # regenerate docs/index.html and the submit page from the decision record
pytest -q
```

The former `build_pages_and_readme.py` generator has been retired for this page; it still writes the old negative status and now exits with a message.
