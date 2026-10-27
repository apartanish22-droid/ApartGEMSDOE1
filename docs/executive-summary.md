# ApartGEMSDOE1 — executive summary

**DO NOT SUBMIT the new candidate.** It is a technically valid, independently generated research TIFF, not a protocol-unique or high-performing approved submission.

- [Download the new research TIFF](downloads/apartgems1-snrc-e1-20000-20261027-735ea04bc35d-DO-NOT-SUBMIT.tif) (research only; 915,864 bytes).
- SHA-256: `73fa21b7c558cd48dea20d1d63ddd43efd2ea8b9e57bbc98972153212625987a`.
- Name: `apartgems1-snrc-e1-20000-20261027-735ea04bc35d-DO-NOT-SUBMIT`.
- Note (115/140 characters): `AP1 SNRC e1; scarp-normal K-v-Th contrast, 20k dots; holdout-only; DO NOT SUBMIT: automatic gates pending/negative.`.
- HOLDOUT-DTI: **0.0456 · 95% CI 0.0393–0.0524**, evaluator `gems-segment-pooled-v1`, 60,988 withheld positive pixels.
- Matched-budget ablation HOLDOUT-DTI: **0.0481 · 95% CI 0.0414–0.0549**, same evaluator/positives.
- Paired HOLDOUT-DTI delta: -0.002486; 95% CI [-0.005273, +0.000233]; 0/4 fold wins.
- Byte-unique and prediction-distinct vs 237 compatible registry arrays: **yes**. Protocol-unique: **no**.
- Final-dot overlap: **100.00%** vs lattice, **85.89%** vs a non-lattice LiDAR submission. The strict threshold is 70%; no exemption was applied.
- Leaderboard estimate: **not estimable**. No organizer-confirmed result for this file.
- One experiment completed; stopped on duplicate final dots. No further arms, slot selections or competition uploads.

## Nine-site decisions

All historical values below are **unverified user reports, not organizer receipts or local HOLDOUT-DTI**. Every historical file is reference-only, not a new-file recommendation.

| Site | Historical best claim | File inspected | Protocol-unique vs other leaders? | Estimated leaderboard score | New approved file |
|---|---|---|---|---|---|
| [GEMSDOE24](sites/GEMSDOE24.html) | No exact-file receipt | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | No | Not estimable | None |
| [GEMSDOE25](sites/GEMSDOE25.html) | No exact-file receipt | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | No | Not estimable | None |
| [GEMSDOE27](sites/GEMSDOE27.html) | No exact-file receipt | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | No | Not estimable | None |
| [GEMSDOE28](sites/GEMSDOE28.html) | No exact-file receipt | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | No | Not estimable | None |
| [GEMSDOE30](sites/GEMSDOE30.html) | No exact-file receipt | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | No | Not estimable | None |
| [GEMSDOE31](sites/GEMSDOE31.html) | No exact-file receipt | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | No | Not estimable | None |
| [GEMSDOE32](sites/GEMSDOE32.html) | No exact-file receipt | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | No | Not estimable | None |
| [GEMSDOE33](sites/GEMSDOE33.html) | No exact-file receipt | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | No | Not estimable | None |
| [GEMSDOE36](sites/GEMSDOE36.html) | No exact-file receipt | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | No | Not estimable | None |

## Why GEMSDOE32 led the reported family

The restored H33-B2 prediction is exactly the 44,090-dot D2.8 mask after removing 6,436 dots within 200 m of the public catalogue. It contains 37,654 dots and zero new locations. Removing false-positive mass can increase DTI if weighted TP coverage is preserved. This is a plausible metric mechanism, not proof of the hidden cause or an authenticated exact-file receipt. New faults can exist within 300 m of known traces, so flank pruning is not universally safe.

The public leaderboard was inspected on 2026-10-27 and did not match the two inherited top-value claims. Its observation is recorded in the source ledger, not presented as an exact-file organizer receipt. No leaderboard number is used to estimate this file’s performance.

## Exact forensic findings

- GEMSDOE25 and GEMSDOE30: identical in-footprint predictions despite different TIFF bytes.
- GEMSDOE28 H27 and GEMSDOE31 H27: identical in-footprint predictions.
- GEMSDOE36 contains all 37,654 H33-B2 pixels plus 1,200 others.
- Current GEMSDOE28 rung file has 37,660 positives and current GEMSDOE33 analog file has 41,865; their older peer ancestry/count descriptions do not match the restored bytes.
- All nine historical leaders violate the near-dot overlap threshold against at least one other focus leader.

## Format and access

The new file is a single float32 GeoTIFF, EPSG:32611, shape 3730×3292, exact template transform, with no NaN/Inf and all raw values in [0,1]. An internal validity mask marks only the exterior as null on masked reads. This interpretation of the organizer’s null/NaN rule has not been portal-tested; the cause of the previously reported upload error is unknown without the rejected bytes/receipt.

Public source pages were read, but account receipts and remaining weekly quota redirect to login. Raw inputs are checksum-pinned owner mirrors, not independently organizer-authenticated. Two incompatible peer TIFFs and the other listed repositories prevent a global uniqueness certification. The method paragraph/lane assignment is absent. The separate selector was not invoked. These are automated evidence outcomes, not a request for human inspection.

## Next steps

1. Start a different, explicitly assigned lane; do not tune the stopped lane.
2. Bind historical organizer receipts to exact file hashes and establish a common current-best holdout benchmark.
3. Authenticate raw-data provenance and resolve shared-code redistribution/prize-use rights.
4. Investigate independent concealed-structure observables and verify concrete official data downloads before adoption.
5. Maintain the entity-wide authenticated slot ledger (rules: up to three per week).

## Evidence and official sources

- [Complete run card](data/run-card.json)
- [Experiment, evaluator version and CI details](data/experiment.json)
- [Pairwise nine-site audit](data/focus-audit.json)
- [Preregistered hypothesis slate](research/hypotheses-2026-10-27.md)
- [Official sources and their evidence limits](sources.html)
- [Competition problem/metric/format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Staff pixel-exact masking clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4)
- [Official rules, section 3](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

This repository hosts nine site-specific executive subpages. It does not claim to have edited the nine independent external websites.
