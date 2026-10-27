# ApartGEMSDOE1 — GEMS fault-prediction research

> **Current decision: NO TIF IS APPROVED FOR SUBMISSION.** This checkout contains only this README. It has no competition rasters, cached feature stack, fault catalogue, holdout evaluator, submission writer, validator, or registry rasters. Creating a compliant GeoTIFF or estimating a holdout score from this checkout would require inventing data/results. Do not submit a placeholder.

## Executive summary

The immediate objective is a reproducible, spatially blocked, hide-and-recover evaluation—not a speculative leaderboard-score promise. A submission is eligible for a separate selection decision only after the exact artifact has passed the scientific holdout, novelty/registry, and file-format gates below. A holdout result is an estimate, never an organizer-confirmed leaderboard score. Weekly submission slots must not be spent by this project; selection belongs to the separate selector and is subject to the competition's current cap.

### Prior results supplied in the project request

The table below transcribes the best result stated by the user for each requested site. These are **user-reported values, not verified receipts**; no downloadable raster, submission-page receipt, or registry manifest is present in this repository. Thus none is presented as an independently confirmed score or as a score estimate for a new artifact.

| Site | User-reported best entry | User-reported score | New artifact / estimated score | Decision |
|---|---|---:|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | None / **not estimable** | No file to recommend |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | None / **not estimable** | No file to recommend |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | None / **not estimable** | No file to recommend |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | None / **not estimable** | No file to recommend |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | None / **not estimable** | No file to recommend |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | None / **not estimable** | No file to recommend |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | None / **not estimable** | Highest in the supplied nine-site list; not independently verified |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | None / **not estimable** | No file to recommend |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | None / **not estimable** | Second-highest in the supplied nine-site list; not independently verified |

**Irregularities in the supplied record:** the request separately names 0.2778, 0.3195, and 0.4413 as high scores without a dated leaderboard snapshot or submission-page receipts. They are inconsistent as descriptions of the same “current” maximum. The site scores above are not enough to establish which raster was scored, its exact file contents, or whether two differently named entries are byte-identical or highly correlated. Treat every such figure as user-provided until a receipt or official leaderboard snapshot is archived. Do not compare projected values to these figures as if they were scores.

## Submission gate — must all pass before any “OK to download and submit” label

1. **Inputs and provenance:** use the competition's official data and exact sample-submission grid; record source, file hashes, dimensions, CRS and transform. Do not silently substitute a web-map or derived raster.
2. **Leakage-safe hide-and-recover:** withhold whole fault segments plus a spatial buffer; derive every catalogue-based feature only from visible faults; mask visible-fault pixels exactly. Keep the cached feature stack and the shared `evaluate_holdout.py` / `submission_writer.py` implementation in the template—do not create a private evaluator fork.
3. **Leakage canary:** test every input feature alone on the same holdout. AUC > 0.90 is a leakage alarm until explained and independently resolved.
4. **Metric:** pooled DTI with alpha 0.2, beta 0.8, and a 300 m triangular kernel. Record evaluator version, withheld-positive count, and a 95% confidence interval. Label every result either **HOLDOUT-DTI** (with all three details) or **ORGANIZER-CONFIRMED** (copied from a submission-page receipt). Never label a projection as a score.
5. **Novelty lane:** compare both the candidate surface before point placement and the final point set against every available registry raster. Reject/log as duplicate if rank correlation is > 0.90 or if >70% of candidate dots are within 3 pixels of one registry's dots. Missing registry files mean novelty is **unknown**, not passed. Also record SHA-256 and exact/near-duplicate checks.
6. **Artifact validator:** single-band GeoTIFF; exact CRS, shape, and geotransform; no NaN inside the submission footprint; every predicted value finite and in [0, 1]. Preserve legitimate outside-footprint nodata only if the official sample raster specifies it. Re-open the written file and validate the file itself, not just the in-memory array.
7. **Decision:** promote only if the candidate improves the agreed current holdout best under the same evaluator and protocol, is not a duplicate, and passes artifact validation. Otherwise retain the negative result and do not use a submission slot.

No step above has been executed in this checkout: the required inputs and shared tools are absent. Consequently there is currently **no downloadable TIF, no validated estimate, and no “OK to submit” candidate**.

## Hypothesis shortlist before implementation

These are **research proposals, not tested findings**. The prompt's mandatory “single method paragraph” defining this run's lane is not actually included, and the repository has no existing method code or registry rasters. Novelty against all prior GEMSDOE sites cannot therefore be established. The shortlist is a planning aid only; do not implement an out-of-lane idea or call one novel until the lane and registries are available.

| Rank | Candidate hypothesis and layers | Target signature / missing-fault rationale | Difference from this checkout | Expected DTI benefit | Cost / status |
|---:|---|---|---|---|---|
| 1 | Multi-scale magnetic edge coherence from the provided GEODAWN airborne numerical-feature raster, tested jointly with DEM-derived structural context | A fault may offset or juxtapose magnetic units and produce a persistent, scale-stable edge that is not already in a mapped-fault catalogue. Require continuity and cross-scale agreement to suppress isolated lithologic contacts. | No feature transforms or modeling code exist in this checkout; this is a proposal, not a proven repo-level novelty claim. | **Unknown; highest-priority test only if within lane.** Magnetic contacts can be lithologic rather than fault-related. | Medium if the cached magnetic bands are present; otherwise data placement is a blocker. Needs per-feature leakage canaries and blocked holdout. |
| 2 | DEM curvature / local-relief asymmetry paired with GEODAWN radiometric contrasts | A concealed or unmapped structure may create a subtle aligned break in slope/relief and juxtaposed weathering/alteration response. It targets a different observable from a simple sharp scarp. | No terrain/radiometric processing exists in this checkout; prior site names in the request indicate related scarp/radiometric experiments elsewhere, so cross-site novelty is unproven. | **Unknown; plausible complementary signal, high confounding risk.** | Medium–high; depends on exact DEM coverage and cached radiometric bands. Verify source rasters and spatially blocked holdout. |
| 3 | Magnetic lineament termination, bend, and intersection metrics rather than raw edge strength | Fault tips, relays, or intersections may produce organized discontinuities in magnetic lineaments away from catalogue traces. This could recover structural geometry rather than simply rediscover a mapped line. | No lineament extraction or graph-based features exist here. Existing GEMSDOE results named by the user include tip/stepover work, so it is not demonstrably new across the competition. | **Unknown; likely lower than direct edge coherence but potentially complementary.** | High; robust extraction and parameter choices need careful nested holdout to avoid tuning leakage. |
| 4 | DEM drainage-network deflection / channel-alignment residuals conditioned on mapped geology | A previously unmapped fault may divert or align channels through persistent linear relief, while excluding alignments explained by mapped lithologic boundaries. | No hydrography/geomorphometry code exists here. This is not validated as new relative to the full family of cited submissions. | **Unknown; likely modest and spatially selective.** | High; requires reproducible drainage extraction, geology controls, and likely extra official data. Do not call viable until source access is checked. |

No candidate has a numeric expected DTI: assigning one without running the required holdout would be an unsupported projection. The data needed to validate candidates must be sourced from the competition bundle and the cached template stack. If an additional layer is required, document its specific official provider and verify availability and license before use; this checkout cannot currently verify external source access.

## How to submit (only after a candidate is promoted)

1. Download the promoted single-band `.tif` from the project's artifact area; confirm the page labels it **OK TO SUBMIT** and shows its SHA-256, holdout report, novelty report, and validator report.
2. On the competition's **New submission** page, select that `.tif` (or a ZIP containing exactly one GeoTIFF), enter the unique run name and the short note from the run card, then submit. The competition account is required; this repository must not store credentials or claim to submit on the user's behalf.
3. Save the organizer's receipt and leaderboard result back to the run record as **ORGANIZER-CONFIRMED**. Never replace the holdout estimate with an unreceipted claimed score.

At present step 1 cannot be performed: no candidate artifact exists. The competition data page is login-gated according to the project brief; the Dropbox links supplied there are references, not verified local data. A valid submission cannot be manufactured from filenames or leaderboard text.

## Operating charter (read at the start of each project session)

- **Aim:** maximize the probability of a valid, competitive GEMS submission through auditable science, not score claims or artifact volume.
- **Own the outcome:** keep hypotheses, data lineage, evaluation, novelty checks, and final-file validation in one reproducible pipeline; report blockers and negative results explicitly.
- **Focus:** discover geothermal-system-relevant unmapped faults using free, public, scientifically defensible data; maintain a curated source/evidence ledger with official links, access status, license, date checked, and the specific claim supported.
- **Automate honestly:** aim for a clean GitHub Pages executive summary with a prominent, gated download and exact submission steps. Do not display a download button as submit-ready until every gate above passes. The current repository has no site, pipeline, or data, so those capabilities are not yet implemented.
- **Parallel-run constraints:** use only the explicitly assigned method lane; stop on the stated correlation/overlap duplicate thresholds; reuse the template's cached features and shared evaluator/writer; test feature leakage; stop after at most 3 experiments or 2 hours; do not choose or consume a weekly slot.
- **Evidence discipline:** distinguish user-reported history, local holdout measurements, and organizer receipts. Link official primary sources for factual claims; mark unverified claims as unverified. Never invent access, experiments, validation, or score estimates.
- **Prompt gaps to resolve from repository/source material (not by guessing):** the exact method paragraph defining the lane; the template/repository containing cached features and shared scripts; official train/test/sample rasters and labels; current registry rasters for novelty checks; and the metric evaluator/version. These are absent from this checkout.

## Run card for this checkout

```json
{
  "hypothesis": "No experiment run: inputs, template, lane definition, and evaluator are absent.",
  "mechanism": null,
  "named_non_fault_mimic": null,
  "holdout_dti": {
    "label": "HOLDOUT-DTI",
    "value": null,
    "evaluator_version": null,
    "withheld_positives": null,
    "confidence_interval_95": null,
    "status": "not run; required data and shared evaluator absent"
  },
  "correlation_overlap_vs_registry": {
    "rank_correlation": null,
    "fraction_within_3px": null,
    "status": "not assessed; registry rasters and candidate absent"
  },
  "raster_sha256": null,
  "validator": {
    "no_nan_inside_footprint": "not run",
    "values_in_0_1": "not run",
    "crs_shape_transform_match": "not run"
  },
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```

## Official references supplied for the project

These links are recorded for source review; their contents and current availability have **not** been independently checked in this README-only checkout.

- Competition overview/rules: [DrivenData GEMS competition](https://www.drivendata.org/competitions/306/competition-doe-gems/) and [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
- Competition data page (login may be required): [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/).
- Reference implementation: [DrivenData GEMS prize reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
- USGS GeoDawn data reference: [Airborne magnetic and radiometric surveys, northwestern Great Basin, Nevada and Oregon](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
- INGENIOUS project reference: [Great Basin Center for Geothermal Energy](https://gbcge.org/current-projects/ingenious/).
- Competition paper supplied in the request: [NLR report PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
- Projected coordinate reference supplied in the request: [EPSG:32611](https://epsg.io/32611). The correct CRS for a submission must still be read from the official sample raster, not assumed from this link.

## Repository review and next steps

At review time, `git ls-files` contains only `README.md`; the worktree was clean. The repository has no application, tests, workflow, data, source ledger, or generated TIF. The base commit is `d681f75` (`Initial commit`). Therefore this review can improve the project brief and record an honest negative run card, but it cannot verify or implement the requested predictive science from absent inputs.

1. Obtain the authorized competition bundle and template artifacts (`training_features.tif`, `labels.tif`, `sample_submission.tif`, DEM links, registry rasters, and cached feature stack) in the prescribed ignored data locations; record hashes and metadata. Do not commit private or large competition data.
2. Recover the exact lane paragraph and template implementations of the shared holdout evaluator and submission writer. Confirm their metric and masking semantics against the competition rules/reference solution.
3. Build the shared validation/novelty tests and tests with synthetic rasters for CRS/grid, edge footprint, nodata, NaN, and [0,1] failures before any real model run.
4. Select one in-lane hypothesis, run feature-alone leakage checks, then the prescribed blocked holdout. Maximum budget: three experiments or two hours. Compare to a reproducibly measured current holdout best, not user-reported leaderboard values.
5. Only after all gates pass, generate the GeoTIFF, re-open and validate it, produce a run card and hash, and wire a clearly gated download/executive-summary page. Store source metadata and organizer receipts.
6. Ask the separate selector to decide whether to spend a weekly slot; this research pipeline must not select, upload, or consume one itself.
