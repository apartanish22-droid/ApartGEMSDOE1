# Repository review — 2026-10-31 UTC

## Executive decision

**Negative: no TIFF in this checkout is approved to download and submit.** I did not create a new raster, spend a competition slot, or claim a higher score. This is not a discretionary delay: the inherited candidate exceeds the prompt's explicit duplicate threshold, the pre-placement surface cannot be independently cleared, the complete registry and feature stack are absent, and the approved parallel-run process requires stopping instead of changing lanes or placing points to evade the test.

The highest *reported* focus-nine result is GEMSDOE32's `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`, claimed score **0.2778**. It is not an organizer-confirmed receipt and is not an estimate for a new file. The geometry re-audit shows the raster's support equals the GEMSDOE25 support with cells within two pixels of the mapped-fault catalogue removed. That is consistent with a plausible max-kernel-DTI precision/coverage tradeoff, but geometry alone cannot show the cause of the claimed score or establish superiority on hidden expert labels.

The official public leaderboard's direct page read on 2026-10-31 showed rank 1, xiaofanhu, at **0.4544**. This is a team-level public standing, not a file receipt, a hidden-test score for this repo, or a forecast. The automated project feed remains `unavailable`; it is intentionally not being presented as a current refreshed feed.

## Answer-first download table

| File | Score label / estimate | Unique versus the nine focus sites? | Download and submit? |
|---|---|---|---|
| **None cleared.** Prior artifact: `docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif` (SHA-256 `09fa04bd481d896a4dcbb808e4ef8136f8e6d0e0d88cebe9afd957db2779d62f`) | No current `HOLDOUT-DTI` for a candidate; no leaderboard estimate. Historical v2 score is explicitly non-comparable. | **No for the prior candidate:** 37,533/37,654 positive pixels (99.6787%) lie within 3 px of one pinned lattice witness, over the 70% stop. Focus-nine pair tests also fail the 70% directed-overlap limit for all nine historical rasters. | **Not OK.** Research/audit only. Its zeros outside the study footprint also conflict with the recorded official rule's null/NaN requirement. |
| GEMSDOE32 historical file above | 0.2778 is **USER-REPORTED**, not `ORGANIZER-CONFIRMED`; estimated score for any new file: unavailable. | **No** within focus nine: 100.00% of its positive cells are within 3 px of GEMSDOE24 in the directed audit. | **Do not resubmit.** Historical work is not a unique new entry. |

The full nine-row file/method/claimed-score/closest-peer table remains in [README](../README.md) and the [public dashboard](../docs/index.html); supporting immutable mirror hashes and pixel comparisons are in [`focus9_reaudit.json`](focus9_reaudit.json). The nine-site audit is exactly those pinned owner-mirror files, not a complete competition-wide registry. Scores supplied in the prompt remain claims because no receipt was available for matching file hashes.

## Why GEMSDOE32 may have led the nine (not a causal finding)

1. The metric described on the official [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) is distance-weighted Tversky with α=0.2, β=0.8, and a 300 m triangular kernel. Nearby duplicate predictions may add little marginal true-positive credit while adding false-positive weight; pruning a mapped-fault collar could therefore improve precision without sacrificing nearby kernel coverage.
2. The local support audit finds GEMSDOE32's positive-cell set is exactly GEMSDOE25's set after removing cells at catalogue distance ≤2 px (XOR = 0). GEMSDOE25 and GEMSDOE30 have identical in-footprint support (XOR = 0). These are geometric identities, not score-mechanism experiments.
3. No hidden test labels, receipt-to-TIFF hash match, or controlled paired organizer comparison is present. It is therefore **not possible to establish why the claimed 0.2778 occurred**, or to conclude a replacement will beat it. The public leader at 0.4544 is a separate participant/team result and cannot validate the GEMSDOE32 claim.

## Ranked untried hypothesis queue

This review selects **no lane** and runs **zero experiments**. These four candidates are the repo's preregistered future queue, not permission to proceed. “Untried” here means not experimentally validated in this checkout; it does not establish global novelty across all sibling sites or competitors. The full descriptions and source checks are in [`next_hypotheses.md`](next_hypotheses.md), [`research_sources.md`](research_sources.md), and the original preregistration evidence. Priority is qualitative; no expected DTI gains are measured or projected.

| Relative rank | Candidate / layers | Target signature and why it might find catalogue-missing structure | Named non-fault mimic | Difference from implemented repo | Data status / cost |
|---|---|---|---|---|---|
| 1 | Signed paired-flank agreement: competition elevation, magnetic/RTP and isostatic gravity; optional USGS 3DEP | Stable signed topographic step paired with magnetic/gravity flank contrast at multiple scales, potentially exposing a subtle buried basin margin or scarp | Lithologic contact; alluvial-fan channel; erosional scarp | Adds signed, polarity-stable paired flank statistics; current MAW-GSI uses multi-azimuth worms and unsigned cross-gradient alignment | **Not runnable here; medium.** Training feature stack absent. Owner-mirror availability does not authenticate organizer origin. Official sources to check: DrivenData data page (login recorded), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program). |
| 2 | Flight-line repeatability: official USGS GeoDAWN magnetic line measurements plus acquisition/flight-line metadata and released grid | Require an anomaly/gradient to repeat across overlapping or crossing acquisition lines, reducing acquisition-direction/terrain-clearance artifacts while retaining blind structures | Regional magnetic gradient; lithologic boundary; leveling artifact | Uses line-level data as a repeatability test; repo uses gridded magnetic products and spatial filters | **Raw line files not downloaded or coverage-tested; high.** Official source: [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). |
| 3 | Depth-normalized paired thermal gradients: DOE GDR #1391 2 m probes and well/spring temperature-chemistry data, with independent structural context | Test local depth/temperature gradient breaks rather than broad thermal point-density halos; a blind upflow or groundwater barrier may mark an unmapped structure | Groundwater flow; uneven sampling; seasonality; lithology-controlled conductivity | Would pair observations with depth/uncertainty metadata; existing code smooths/rasterizes thermal points | **Metadata coverage unknown; high/sparse-data risk.** Official source: [DOE GDR INGENIOUS #1391](https://gdr.openei.org/submissions/1391). |
| 4 | ASTER GED AG100 V3 emissivity contrast with independent DEM/geophysical edges | Look for persistent emissivity boundaries that spatially coincide with independent lineaments, not treating thermal signal as a direct vent measurement | Surface cover, vegetation/albedo, quartz-rich dunes, unrelated lithology | Adds a satellite emissivity product absent from the repo's airborne/terrain/point-temperature stack | **Not downloaded or area-tested; speculative/high.** Official source: [NASA LP DAAC ASTER GED catalog](https://lpdaac.usgs.gov/products/ast_08v004/). |

### Why none can currently be promoted

The user-specified single-lane stop rule precludes switching to a different hypothesis after a duplicate stop. Also, `data/` contains the small bridge/official label/template/fault rasters but not `training_features.tif` or a cached feature stack. Independently re-hashed `data/official/labels.tif` and `data/official/existing_faults.tif`: both are byte-identical at SHA-256 `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093`. Treat this as a mirror irregularity: these files are not independent evidence of concealed labels. The manifest identifies owner-mirror data and cannot establish official provenance. A complete synchronized registry is not present. Consequently the feature-only leakage canaries, the surface rank-correlation checks, and a fold-honest v3 holdout with a 95% CI cannot be run honestly here. No `HOLDOUT-DTI` result exists for a new candidate, and a score estimate is unavailable.

## Three review passes and verification

### Pass 1 — inventory and evidence

- Read the project README startup protocol, generated dashboard/submission guide, evidence/run cards, source register, four-candidate hypothesis queue, shared evaluator/writer/validator, scripts, and tests.
- Re-ran the pinned, immutable nine-site owner-mirror audit: **9 fetched/checked, 0 errors**. Reproduced GEMSDOE32/GEMSDOE25 collar identity and GEMSDOE25/GEMSDOE30 support identity. This does not authenticate reported site scores or cover every registry entry.
- Re-fetched the pinned 13GEMSDOE lattice witness. Its SHA-256 matches the recorded pin. The inherited candidate still has **37,533 / 37,654 = 99.678652998%** of positive cells within 3 pixels. The one-witness result proves this candidate fails, not that the scan is complete.
- Re-read the official [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) on 2026-10-31: rank 1 xiaofanhu, 0.4544. Updated the dated direct observation only; kept the automated feed `unavailable` after its recorded TLS/SSL failure.

### Pass 2 — execution and compliance

- Installed the declared Python requirements into ignored `.venv/` (not tracked). `pytest` was initially absent from the environment; did not change global packages.
- `scripts/run_apartgems_pipeline.py` returned the intended stop (exit 2): no model experiment, prediction write, or submission.
- `scripts/validate_submission.py ... --format-only` confirmed the old TIFF is one float32 band, EPSG:32611, 3730×3292, matching the stored template transform, finite and within [0,1]. It returns `ok_to_submit=false`: no complete registry, no holdout gate, and no selector approval. It also records zeros outside the footprint; local format preflight is not portal acceptance.
- No training-feature cache found in the checkout. No feature canary, new model holdout, surface candidate, new TIFF, organizer upload, receipt, or weekly slot was produced.

### Pass 3 — independent consistency checks

- Confirmed the dated official leaderboard record and scheduled-feed status are separate evidence sources; kept 0.4544 labelled a team public standing, not a file score or forecast.
- Reconciled claims in the README, dashboard, run card, validation report, focus audit, and negative pipeline outcome. The historical candidate is labelled research-only; all nine named site files are marked do-not-resubmit; score estimates remain unavailable. Added a freshness-limited dashboard fallback that displays the dated direct leaderboard page observation only while fresh and explicitly distinguishes it from the unavailable scheduled feed. A post-merge Actions run showed the scheduled-page parser still failed closed and would overwrite the fallback snapshot; updated the refresh script to preserve a source-identified direct observation only while it remains within 24 hours, while keeping scheduled-feed status/value unavailable. Stale, malformed, or wrong-source observations are discarded.
- Full suite after post-merge feed hardening: **41 passed**, 16 Rasterio/Affine pending-deprecation warnings. `compileall`, `node --check docs/feed.js`, strict parsing of all evidence/docs JSON, and `git diff --check` passed on this review's run. At that earlier checkpoint, the then-current run card and its two public mirrors were byte-identical and branch-matched. The follow-up below supersedes those public mirrors with the dated card for the current Arena branch. The current report itself was checked for the main stated hashes, site names, and decisions against the run cards and focus audit.

## Run card essentials from the prior checkpoint

- **Hypothesis:** inherited MAW-GSI candidate lane, stopped on literal duplicate witness.
- **Mechanism:** geophysical/topographic aligned lineaments are a fault-discovery hypothesis, not demonstrated here.
- **Named non-fault mimic:** alluvial-fan channels/erosional scarps and lithologic magnetic/gravity contacts.
- **HOLDOUT-DTI:** no current v3 value, no 95% CI, no new candidate; the prior v2 historical value 0.117438 [0.099365, 0.136129] is not comparable and is not a leaderboard estimate (evaluator `gems57-pooled-hide-v2`, 11,360 withheld positives).
- **Registry comparison:** pre-placement surface correlation untested for the archived candidate; final dots overlap the pinned witness 99.6787%, above 70%; registry incomplete.
- **Raster SHA-256:** `09fa04bd481d896a4dcbb808e4ef8136f8e6d0e0d88cebe9afd957db2779d62f` (old audit-only raster).
- **Validator:** local finite [0,1] and stored-grid checks pass; outside-footprint zeros mismatch the official null/NaN text; no NaN inside footprint; CRS EPSG:32611, shape 3730×3292 and transform match the stored template; full submission validation is **false**.
- **Submission:** prior name `apartgems1-maw-gsi-e3-20261028-87f83db9`; note `Historical MAW-GSI E3; audit only; literal 3px overlap duplicate; DO NOT SUBMIT.` (80 characters).
- **Verdict:** negative.

## Remaining work / limitations

1. Obtain organizer-origin `training_features.tif` and the exact template through an authorized competition-data route; record source, license, preprocessing, and hashes. Current login requirement is from the prior documented data-page access check; owner-mirror bytes are not a substitute for provenance.
2. Build a complete, synchronized, pinned, accessible raster registry and preserve all continuous pre-placement surfaces; one duplicate witness can reject a candidate, while partial scans can never certify uniqueness.
3. Only after an authorized new lane and prerequisites: test each feature alone for leakage (AUC >0.90 is suspect), use the shared `gems57-pooled-hide-v3` whole-segment buffered hide-and-recover with visible-only catalogue features and pixel-exact visible masking, pooled α=0.2/β=0.8/300 m DTI, and report withheld positives plus 95% CI. Respect the 3-experiment / 2-hour cap and stop at the first uniqueness breach.
4. Fix the shared writer/validator policy for official outside-footprint null/NaN behavior and verify any future output's range, band, CRS, shape and transform. Portal acceptance still requires the actual portal's response; local tests are not that response.
5. Keep a separate selector for any real weekly submission slot. Record the exact upload receipt before using `ORGANIZER-CONFIRMED` for a file score; check the live competition rules/quota and provide the required AI-use narrative disclosure.
6. Restore scheduled leaderboard feed freshness without publishing stale values when refresh fails.

**Download instruction:** the archived TIFF is present for audit reproducibility only. It is **not OK to download and submit**. No new unique TIFF was generated because the governing protocol's duplicate stop is active and no separately authorized, validated lane can pass the required gates in this checkout.

## Follow-up review — Arena branch `arena/056c9d8d-apartgemsdoe1` (2026-10-31 UTC)

This continuation integrates the prior same-date review on the current branch. It does not refresh external competition pages, alter the recorded leaderboard observation, select a method lane, or authorize a submission.

### Pass 1 — targeted audit of shared release gates

- Reproduced a false-positive in `find_priors([Path("data")])`: known competition input rasters under `data/` were being classified as prior submissions. That distinction affects duplicate-prior discovery, not competition-score evidence.
- Re-ran the pinned historical-focus audit: all nine named focus files were fetched and checked, with zero errors. The GEMSDOE32/GEMSDOE25 two-pixel-collar support identity and GEMSDOE25/GEMSDOE30 support identity remain geometric observations; no score causality follows.
- Re-ran the pinned literal-witness audit: 37,533/37,654 archived-candidate dots (99.678652998%) remain within 3 px of one witness, above the 70% protocol stop. The witness inventory is incomplete, so this rejects the archived file but cannot certify uniqueness of another.

### Pass 2 — repair and publication

- Updated `src/gems57/gates.py` to exclude reserved competition-input directories and known input files from prior discovery; added `tests/test_gates.py` regression coverage. No method lane or experiment was started.
- Updated the fail-closed page/README builder to publish the dated 2026-10-31 run card at the stable docs JSON URLs, copy this review into `docs/`, and synchronize the focus and witness audit JSON mirrors. The dated run card records the active branch, zero experiments/slots, no measured current holdout, and a negative verdict.
- The official-rule/leaderboard record was not freshly fetched in this follow-up. The already-dated 2026-10-31 direct team leaderboard observation remains separate from the scheduled feed, which is still recorded as unavailable; neither is a file receipt or future-score estimate.

### Pass 3 — release decision and validation

- No new TIFF, model experiment, v3 `HOLDOUT-DTI`, upload, organizer receipt, selector approval, or weekly slot was produced. The archived candidate remains research-only and not safe to submit; full preflight remains negative.
- Integrated validation passed: **42 tests**, 16 Rasterio/Affine pending-deprecation warnings; `compileall`, `node --check docs/feed.js`, and strict parsing of all **48** evidence/docs JSON files passed. The builder regenerated the pages and synchronized dated run-card/review copies. Successful repository checks do not clear the scientific, registry, holdout, portal, or selector gates.
- Current run card: [`run_card_2026-10-31.json`](run_card_2026-10-31.json). It supersedes older run-card wording for this follow-up; prior evidence remains retained rather than relabelled as a new experiment.
