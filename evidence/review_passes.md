# Three-pass implementation and review record

## Prior implementation review — 2026-10-28 UTC

No model experiment, replacement candidate, submission, or slot selection was performed. The negative result is the release decision.

### Pass 1 — inventory, scientific assumptions, and stop witness

* Compared inherited docs, run card, format receipt, private gate, feature paths, and published pages. The prior private gate reweighted/ignored dense reference support while calling E3 unique, despite stored raw overlap above the literal cap; it also checked a surface only after placement.
* Independently fetched the 13GEMSDOE lattice at an immutable commit and recomputed directed Euclidean 3-pixel overlap: 37,533/37,654 positive pixels, or 0.9967865299835342. One witness proves the protocol failure even though the wider inventory is incomplete.
* Re-fetched and hashed the nine named owner-mirror rasters. GEMSDOE32 support is exactly GEMSDOE25 after excluding the two-pixel mapped-catalogue collar; GEMSDOE25 and GEMSDOE30 have identical in-footprint support. No hidden-label, submission-page receipt, or causal-score proof was found.
* The inherited seed-2026 v2 score mask excluded 1,094 non-hidden catalogue pixels removed from feature context by the buffer, 1,088 in scored regions. That mask is not pixel-identical to visible catalogue context.

### Pass 2 — shared safety repairs and research provenance

* Corrected shared holdout masking to pixel-exact visible context, rejected mismatched masks, and versioned `gems57-pooled-hide-v3`. Buffer-removed cells remain unlabelled; historical v2 scores are not comparable to v3.
* Removed the private density-exempt gate. Shared gates now check literal thresholds, complete pinned inventories, finite values, grid metadata, nonconstant rank comparisons, and early duplicate stops. Retired H-APART-2 experiment/cache/surface/placement entry points cannot resume that legacy lane.
* Preserved the existing TIFF as research-only audit, made run cards negative, and rewrote the dashboard/README generators so they cannot produce an approved-file status. Local format validation is not organizer acceptance or selector approval.
* Bound reusable feature caches to source/content hashes, refused unpinned downloads or missing inputs, and retired the old derived-feature cache until source-bound. Some mirror pins are not independently authenticated official data.
* Reclassified historical scores as unverified claims and recorded four future geological hypotheses with mimics, qualitative tradeoffs, and access status. Raw official downloads and candidate viability were not established.

### Pass 3 — independent recheck and delivery gates

* Rebuilt v3 split masks without fitting a model: 11,360 withheld positive pixels, 1,094 context-only catalogue removals, and exact visible-only masks (`v3_mask_regression.json`). No v3 model score was calculated.
* The then-current test suite passed 23 tests. `compileall`, `node --check docs/feed.js`, and `git diff --check` passed. The local TIFF preflight passed format checks but returned `ok_to_submit=false`.
* Earlier PR #25 merged the corrective negative audit. A Pages workflow completion did not establish a successful public-feed refresh or organizer acceptance.

## Continuation review — 2026-10-30 UTC

No model experiment, fold-honest holdout evaluation, or new submission-candidate raster was produced; no weekly slot was used, no upload was made, and no organizer receipt was obtained. Disposable format-test rasters were limited to test temporary directories.

### Pass 1 — fresh audits, official sources, and access

* Re-fetched all nine immutable owner-mirror files and recomputed the focus-nine audit at 2026-10-30T01:55:22Z. All nine fetched/hashed without errors; the exact B2/GEMSDOE25 collar identity and GEMSDOE25/GEMSDOE30 support identity remain. Each file is non-unique against at least one other focus-nine file. Claims remain unreceipted.
* Re-fetched and re-hashed the prior audit TIFF and one immutable 13GEMSDOE lattice witness. The literal overlap remains 37,533/37,654 = **99.67865299835342%**, above the 70% internal stop. This one witness is enough to stop, but is not a complete registry certificate. The internal threshold is not an official competition rule; the Official Rules contain a separate originality warranty.
* Read the official problem page, full seven-chunk September 2026 rules PDF, public leaderboard, government sources, and NASA catalogs. The official format text says null/NaN outside bounds; the prior file and shared writer use zeros outside the bridge footprint. A local NaN-outside diagnostic reproduces the sample template's NaN mask, but portal acceptance remains untested.
* A fetch-tool direct read of the official public page showed rank 1 at **0.4544** on 2026-10-30. The automated scheduled feed separately failed with a TLS/SSL EOF; that feed remains explicitly `unavailable`. The direct observation is saved in `evidence/official_rules_check.json` and is not a feed value, file receipt, hidden-test score, or future estimate. The official data page redirected to login.
* A parallel repository review verified that the large feature stack can be restored from the owner mirror in a scratch copy. It is not present in this checkout and is not authenticated organizer data.

### Pass 2 — code, rules, and hypothesis review

* Re-read the metric, buffered whole-component holdout, pooled v3 evaluator, writer, validator, gates, data preparation, feed updater, documentation generator, and tests.
* Fixed `scripts/evaluate_holdout.py` to validate one-band float32 and exact grid metadata; reject NaN/Inf or out-of-range in-footprint values and positive outside mass; and label any saved-raster replay `STATIC-REPLAY-DTI`, not fold-honest HOLDOUT-DTI. It reports no leaderboard estimate and explicitly marks that no model is retrained per fold. Added strict-input and evidence-label regression tests; no holdout was run after the duplicate stop.
* Merged the verified fresh-checkout CLI-writer path fix. The shared gated writer still refuses NaN, while the explicit diagnostic `mode="nan"` can reproduce the public sample mask; no default policy was silently changed.
* Integrated the latest main-branch hardening: scheduled-feed age is capped at 24 hours and failed refreshes have null observation/score; stale feed values are hidden in the browser. The archived H-APART-6 command is a standard-library-only stop tombstone, and a pull-request CI workflow runs syntax and test checks.
* Ranked four previously unrun geological hypotheses with layers, mechanism, catalogue-missing rationale, a named non-fault mimic, repository distinction, qualitative priority/cost, and official source-access status. These are a research queue only: H-APART-2 paths remain retired, H-APART-6 OTSP is archived after the duplicate stop, and no active lane is authorized. The top signed paired-flank idea cannot be validated without a provenance-checked feature stack and separate lane assignment.

### Pass 3 — build, tests, and release decision

* Kept the scheduled feed status `unavailable`; exposed the date-stamped official page read separately and labelled its provenance. Generated README, dashboard, and submission guide from fail-closed source evidence; added an answer-first download/submit decision, official format/rules check, AI-disclosure reminder, and exact submission steps for any future selector-approved file.
* After rebasing onto the latest `main` changes and rebuilding the generated pages, the full regression suite passed: **37 passed**, 16 rasterio/Affine deprecation warnings. `compileall`, `node --check docs/feed.js`, staged and unstaged `git diff --check`, strict TOML parsing, and strict parsing of all **46** evidence/docs JSON files passed. The first post-rebase test run exposed one stale assertion that expected the date-stamped direct leaderboard read on the dashboard rather than the executive summary; the assertion was corrected to preserve the direct-read/feed distinction. Local test success does not clear registry, holdout, selector, or official portal gates.
* Final release decision: **no file is cleared for download-and-submit**. No full registry, v3 model HOLDOUT-DTI/95% CI, selector approval, newly written GeoTIFF, upload, or organizer receipt exists. Do not resume the duplicate lane.

## Related auditable records

* `evidence/repo_review_2026-10-30.md` and `evidence/repository_review_2026-10-30.md`: parallel full-repository reviews.
* `evidence/repo_review_2026-10-30_overlap.md` and `evidence/focus_overlap_review_2026-10-30.json`: independent overlap/metric review.
* `evidence/official_rules_check.json`: verbatim official rule excerpts, direct leaderboard observation, feed failure, and source gaps.
* `evidence/run_card.json`: current negative run card with current branch, raster hash, witness metrics, validator output, and zero-experiment/zero-slot status.

## Continuation review — 2026-10-31 UTC

No model experiment, candidate prediction raster, weekly slot, or competition upload was made. The explicit duplicate stop remains active.

### Pass 1 — current sources and evidence refresh

* Re-read the supplied persistent mission contract in `README.md`, dashboard and submission guide, focus-nine manifest/audit, source register, hypothesis queue, run cards, shared tool code, and test suite.
* Re-ran the pinned owner-mirror audit for GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36: 9/9 files fetched and hash-checked, no errors. Reconfirmed GEMSDOE32 support equals GEMSDOE25 support after a two-pixel catalogue collar is removed (XOR 0); GEMSDOE25/GEMSDOE30 support XOR is 0. Reported scores remain unverified claims.
* Re-fetched the pinned 13GEMSDOE witness and reran the literal duplicate audit. The candidate still has 37,533/37,654 positive pixels within 3 pixels (99.6787%); the incomplete registry cannot certify any alternative.
* Directly re-read the official leaderboard with the fetch tool on 2026-10-31: rank 1 xiaofanhu at 0.4544. This is recorded as a dated team standing, not a file receipt or future estimate. The scheduled feed remains `unavailable` following its 2026-10-30 TLS/SSL EOF; the direct read was not inserted into the feed.

### Pass 2 — edits, execution, and discovered assertion drift

* Updated the date-stamped official-page observation, corrected the run card's branch to the active Arena branch, refreshed the README/dashboard, and made the highest focus-nine reported claim explicit: GEMSDOE32 0.2778, unconfirmed and not submission-cleared.
* Added a freshness-limited display for the direct official-page observation while preserving `status=unavailable` and `top_public_dti=null` for the failed scheduled feed. The fallback labels the value as a team-level page read, states the scheduler is unavailable, and hides the date-only value after 24 hours.
* Added regression checks distinguishing the direct leaderboard read from the unavailable scheduled feed and checking that the best historical claim is clearly labelled. Fixed stale test assertions that assumed the 2026-10-30 source date and same-day feed failure. The first test run after changing the observation exposed the stale date assertion; the second exposed the stale generated-page wording assertion. Both were corrected to preserve factual dates/provenance rather than weakening the new checks.
* Ran the stopped pipeline (expected exit 2, no experiment/raster), and the existing prior TIFF's format-only validator. The local format check is true for its recorded checks but `ok_to_submit=false` because the outside-footprint policy is zeros and registry/selector/holdout gates are not cleared.
* Four future geological candidates remain a research queue only: signed paired-flank agreement, flight-line repeatability, depth-normalized paired thermal gradients, and ASTER emissivity contrast. No lane was selected and no holdout was attempted because the inherited lane is stopped, the training-feature stack is absent from this checkout, and registry completeness is unavailable.

### Pass 3 — full regression and release decision

* Final checks: **39 passed**, 16 Rasterio/Affine pending-deprecation warnings; `compileall`, `node --check docs/feed.js`, and `git diff --check` passed. Test suite includes output-link checks and strict JSON parsing, plus fresh/stale browser rendering checks for the direct page fallback.
* Reported 0.2778 and the direct public 0.4544 remain separated by evidence class. The prior v2 `HOLDOUT-DTI` remains explicitly historical/non-comparable and no new estimate is asserted.
* Release verdict: **negative**. The only locally downloadable TIFF is marked audit/research only and **not OK to download and submit**. The explicit protocol stop precludes producing a unique TIFF in this lane; no alternative lane was silently substituted.

See `evidence/repository_review_2026-10-31.md` for the complete current executive summary, nine-site decision, evidence-linked hypotheses, validator interpretation, run-card summary, and remaining work.
