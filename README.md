# ApartGEMSDOE1 · Geothermal fault discovery

> **STOP — NO FILE IS READY TO SUBMIT.** The prior MAW-GSI GeoTIFF is locally format-valid against an owner-mirror template, but 99.68% of its dots overlap a registered lattice within three pixels, exceeding the 70% protocol limit. The surface gate is unverified. No new GeoTIFF or competition submission was made; archived H-APART-6 v2 experiments predated discovery of the witness.
>
> [Open the dashboard](docs/index.html) · [Executive summary and submission guide](docs/executive-summary.html) · [Current negative run card](evidence/run_card.json) · [Reproducible witness audit](evidence/literal_witness_audit.json) · [Three-pass review](evidence/review_passes.md) · [Repo review 2026-10-30](evidence/repo_review_2026-10-30.md)
>
> [Download the **prior TIFF for research only — do not submit**](docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif) · SHA-256 `09fa04bd481d896a4dcbb808e4ef8136f8e6d0e0d88cebe9afd957db2779d62f`

## Standing reference: task and parallel-run protocol (read first)

The user’s standing objective is to develop an original, competition-format GeoTIFF for mapping faults relevant to geothermal exploration, with autonomous, reproducible validation and no fabricated scores. Review the nine focus sites, present the download and status clearly, test scientific hypotheses on a spatial holdout, preserve source links, perform three review passes, and use a separate selector before spending a weekly slot. The long repeated site ledger in the request is summarized in the audited table below; the protocol is retained here as the governing operating charter.

1. **LANE.** Stay inside the assigned single method. If rank correlation with any registry raster exceeds 0.90 or more than 70% of candidate dots fall within three pixels of one registry raster’s dots, log a duplicate and stop. Check the surface before placement and final dots; no density exemptions.
2. **REUSE, DON’T REBUILD.** Reuse the template feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Hide whole fault segments with a buffer; derive catalogue-based features only from visible faults; mask visible faults pixel-exactly; use pooled DTI with α=0.2, β=0.8 and a 300 m triangular kernel. Fix shared tools rather than maintaining a private fork.
3. **EVIDENCE LABELS.** A measured model result is HOLDOUT-DTI with evaluator version, withheld-positive count and 95% CI. ORGANIZER-CONFIRMED means a submission-page receipt; an unverified prompt claim or projection is not such a receipt or a future score.
4. **LEAKAGE CANARY.** Test each feature alone on holdout; AUC above 0.90 is leakage until proven otherwise.
5. **RUN CARD.** Record hypothesis, mechanism, named non-fault mimic, holdout DTI and CI, registry correlations/overlaps, raster SHA-256, range/footprint/grid validation, submission name and ≤140-character note, and promote/negative verdict. Negative results are deliverables.
6. **BUDGET.** Stop after at most three experiments or two hours, and stop immediately on duplication. A separate selector chooses a real slot within the current weekly cap.

Before implementation, the user requests 3–5 previously untried geological hypotheses, ranked by expected DTI improvement and cost, with layers, physical signature, catalogue-missing rationale, differences from this repo, mimics, and official data availability. [Future hypotheses are recorded here](evidence/next_hypotheses.md); none was run after the stop.

**Core values:** *Maximize P(Win)* means weigh tradeoffs and risk rather than spending a slot on an unsupported claim. *Own the Outcome* means report failure and correct the shared pipeline, not hide it. Review changes in at least three passes, document limitations, and use official sources for claims. Keep the current feed and guides fail-closed.

## Executive summary · nine requested sites

These are the highest historical files **named in the user prompt**, not a complete census. Prompt values are unverified user reports; no submission-page receipts were found. The future leaderboard estimate is unavailable for every row. “Prior candidate” overlap is directed from the prior MAW-GSI dots to the site's dots. Each historical file fails the focus-nine spatial-uniqueness rule and must not be resubmitted as new.

| Site | Historical file (research only) | Method (owner-described) | Prompt claim | Future estimate | Unique among focus nine? | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/9e185929eeaa6244f96c3022cf3462faa8ca4de0/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif?raw=1) | Owner-described 1.5-pixel thinning of H19-5 ridges. | 0.2477 (user claim, unconfirmed) | Unavailable | NO · duplicate family; prior candidate 49.94% | Do not resubmit |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/fb1db37274776a29dbc48abe55b2e531f2ba6aad/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif?raw=1) | Owner-described 2.8-pixel thinning of H19-5 ridges. | 0.2600 (user claim, unconfirmed) | Unavailable | NO · duplicate family; prior candidate 48.56% | Do not resubmit |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/6704fa2a5133e751df2516feb2e32565ad5fc1df/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif?raw=1) | Owner-described topographic gap closure added to a D1.5 dotted map. | 0.2449 (user claim, unconfirmed) | Unavailable | NO · duplicate family; prior candidate 50.85% | Do not resubmit |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/9509b73eaf35f66d0b23fce63b2540ceff2a88e0/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif?raw=1) | Owner-described one-pixel collar prune plus blind step-over rungs on D2.8. | 0.2710 (user claim, unconfirmed) | Unavailable | NO · duplicate family; prior candidate 47.36% | Do not resubmit |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | [`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/31696c6541cfc54620ff850a748c51625461f27f/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif?raw=1) | Owner-described D2.8 Poisson-disk baseline; footprint values equal GEMSDOE25. | 0.2600 (user claim, unconfirmed) | Unavailable | NO · duplicate family; prior candidate 48.56% | Do not resubmit |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/) | [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/06930b9d03473a9313094a4f2312c4fc6efd4fbb/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif?raw=1) | Owner-described solo / one-pixel catalogue-collar pruning on D2.8. | 0.2708 (user claim, unconfirmed) | Unavailable | NO · duplicate family; prior candidate 47.88% | Do not resubmit |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/) | [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/97597a066d1c61d2c226fdba349716f41b30c1c6/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif?raw=1) | D2.8 set minus points at distance ≤2 pixels from mapped catalogue (verified support identity). | 0.2778 (user claim, unconfirmed) | Unavailable | NO · duplicate family; prior candidate 46.71% | Do not resubmit |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/3eaf85efb49f364b84f8be04e8b084b12d0303b9/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif?raw=1) | Owner-described analog fault-tip and step-over additions on D2.8. | 0.2632 (user claim, unconfirmed) | Unavailable | NO · duplicate family; prior candidate 48.36% | Do not resubmit |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/) | [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/e280188adbbe762e6b7ac6f3b8e105e8e7915026/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif?raw=1) | Owner-described Andersonian geothermal PINN additions to the B2 base. | 0.2750 (user claim, unconfirmed) | Unavailable | NO · duplicate family; prior candidate 47.41% | Do not resubmit |

The re-audit confirms GEMSDOE32 B2's support equals GEMSDOE25's support outside a two-pixel catalogue collar; GEMSDOE25 and GEMSDOE30 have identical footprint values. The user-reported GEMSDOE32 value of 0.2778 has no linked organizer receipt. The official max-kernel DTI makes reduced redundancy a plausible explanation, not proof; hidden labels are unavailable. No result here establishes that a new method will exceed it.

## Current result and limitations

* **HOLDOUT-DTI, historical only:** 0.1174 [0.0994, 0.1361], evaluator `gems57-pooled-hide-v2`, 11,360 withheld positives, 95% CI. This prior run used a scoring mask that included buffer-removed non-visible catalogue pixels; it is not a comparable v3 baseline or a leaderboard prediction. No v3 model run was performed after the duplicate stop.
* **Literal uniqueness:** 37,533/37,654 prior dots overlap the [pinned lattice witness](https://github.com/buffedlizard55-lab/13GEMSDOE/blob/92ee6f074323f161eed837b80ec3ee5b662e26f5/docs/downloads/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif); only one witness is necessary to prove failure, but this is not a complete registry inventory. The word duplicate here means protocol overlap, not byte identity.
* **Feasibility:** the lattice leaves 6,514 allowed cells outside its halo, so a 37,654-dot budget cannot pass. A budget no larger than 21,713 is necessary against this witness, not sufficient for quality or uniqueness.
* **Format:** the prior file has one float32 band, finite [0,1] values, and matches the stored sample grid. This is local preflight only, not organizer acceptance. The authenticated organizer template and outside-bounds policy have not been independently verified here.
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
