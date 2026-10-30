# Three-pass implementation and review record

Original implementation review date: 2026-10-28 UTC. That review performed no model experiment, replacement candidate, submission, or slot selection; the negative result was the release decision.

Follow-up repository review: 2026-10-30 UTC. The newer review ran 24 tests, refreshed the leaderboard feed to explicit unavailable status after a TLS failure, rechecked the non-submission decision and local format-only TIFF validation, and confirms no new TIFF or experiment was produced. See [`repository_review_2026-10-30.md`](repository_review_2026-10-30.md).

## Pass 1 — inventory, scientific assumptions, and stop witness

* Compared the inherited documentation, run card, format receipt, private gate, feature paths, and published pages. Found a contradiction: the prior private gate reweighted/ignored dense reference support and called E3 unique, while the stored raw 13GEMSDOE overlap was above the literal cap. It also checked a surface only after placement.
* Independently fetched the 13GEMSDOE lattice at an immutable commit and checked its SHA-256. Recomputed the prior candidate's Euclidean 3-pixel directed overlap: 37,533 of 37,654 positive pixels, or 0.9967865299835342. This one witness proves the protocol failure even though the wider inventory remains incomplete. See `literal_witness_audit.json`.
* Fetched and hashed the nine named owner-mirror rasters at recorded commits. Verified B2's support is exactly GEMSDOE25 outside the two-pixel catalogue collar, and GEMSDOE25/30 footprint values are equal. No hidden-label, submission-page receipt, or causal-score proof was found.
* Found that the inherited seed-2026 v2 score mask excluded 1,094 non-hidden catalogue pixels removed from feature context by the buffer, of which 1,088 were in scored regions. This is not pixel-identical to the visible catalogue.

## Pass 2 — shared safety repairs and research provenance

* Changed the shared holdout mask to pixel-exact visible context, rejected mismatched masks, and versioned the evaluator `gems57-pooled-hide-v3`. Buffer-removed cells remain unlabelled, so their treatment as negatives in this proxy is a documented conservative limitation. Historical v2 scores are not comparable to v3.
* Removed the private density-exempt gate; the shared gate now checks literal thresholds, a nonempty complete pinned inventory, valid finite values, grid metadata, nonconstant rank comparisons, and early duplicate stops. Placement requires exact matching surface attestations; the stopped H-APART-2 experiment, cache, surface-generation, and placement entry points cannot resume this lane.
* Preserved the existing TIFF for research-only audit, made all current run cards negative, and rewrote the dashboard/README generators so they cannot produce an approved-file status. Historical figures with invalid gate claims were removed from the published site. Local format validation is explicitly not an organizer receipt or selector approval.
* Bound reusable band caches to source and cache content hashes, refused unpinned downloads or missing inputs, pinned prior mirror observations and immutable commits, and corrected misleading historical verification flags. Some hashes are first-observed mirror pins, not independently authenticated official data. Retired the old derived-feature cache until it is source-bound.
* Replaced falsely labeled organizer scores and causal conclusions with unverified claim classifications. Recorded four future hypotheses, their named mimics and qualitative tradeoffs; official metadata was reviewed, but raw official downloads and candidate viability are not established.

## Pass 3 — independent recheck and delivery gates

* Rebuilt the v3 split without fitting a model: 11,360 withheld positive pixels, 1,094 context-only catalogue removals, and an exactly visible-only mask in every fold (`v3_mask_regression.json`). No v3 model score was calculated.
* Automated regression suite: **23 passed**, including synthetic soft-DTI against the literal brute-force formula, whole-component/buffer holdout, >70% dense/lattice witness, empty/partial/unpinned/undefined-rank registry failures, pre-placement hash attestations, source-bound cache rebuilds, negative runner, local preflight, page links and fresh-feed parser. Twelve rasterio/Affine deprecation warnings were emitted; no test failed.
* `python -m compileall -q src scripts tests`, `node --check docs/feed.js`, and `git diff --check` passed. The local static preview served the root, dashboard, audit-only TIFF and feed over HTTP. The local GeoTIFF preflight passed format checks but returned `ok_to_submit=false`.
* GitHub repository metadata reported push/admin permission and a legacy Pages site rooted at `main:/`; branch-protection and Actions-permissions reads returned HTTP 403. Concurrent PRs #23 and #24 repeated the superseded promotion claims. PR #25 merged the corrective negative audit; its Pages workflow completed and the public dashboard was independently observed with the stop verdict. The feed refresh ran but returned unavailable because the leaderboard HTML could not be parsed on the runner; a successful deployment is not evidence of a successful refresh. No slot was used.

## Re-review — 2026-10-30 UTC

### Pass 1 — inspect current branch, evidence, and user-facing feed

* Read the project charter, nine-site table, current run card, uniqueness witness, hypothesis queue, shared evaluator/writer, data manifest, feed parser, workflow, and tests. The existing duplicate stop remains mandatory; the only downloadable TIFF is labeled research-only.
* Found a live-feed freshness gap: the checked-in successful snapshot is date-only `2026-10-28`, while this review is `2026-10-30`. The browser displayed any `status: ok` observation regardless of age, and the failure serializer used `observed_utc` for an unsuccessful refresh. The request itself gives inconsistent leaderboard claims (0.3195 and 0.4413); the repository snapshot's historical public observation is 0.4544 on 2026-10-28. None is a file-level receipt or a current value verified by this review.
* Found a focus-table clarity bug: the README's “Unique among focus nine?” cell showed the prior candidate's overlap with each site rather than that historical file's maximum overlap with its eight peers. The HTML said “duplicate family” but omitted the measured peer and percentage, so it did not make the uniqueness result auditable at a glance.
* GitHub reports the scheduled Pages run `40984509692` completed successfully on 2026-10-30, but the workflow deliberately wraps refresh failure in `|| echo`, so success of the run does not prove a successful parse. The job log and uploaded artifact could not be retrieved in this sandbox; no current leaderboard number was inferred.
* The 19-band feature cache and raw feature stack are described in old manifests but absent from this checkout (`.cache/features/` and `data/official/training_features.tif` are not present). The four queued hypotheses remain preregistered, not tested. Search found no exact paired-flank, raw flight-line repeatability, depth-normalized paired thermal-gradient, or ASTER-emissivity implementation in this repository; this is repository-relative novelty only, not a claim about other teams. External official datasets were not downloaded or re-verified in this review.

### Pass 2 — correct feed labeling and preserve the standing charter

* Added a 24-hour client-side freshness gate, a small future-clock-skew allowance, and [0,1] score validation. A stale value is now hidden and labeled stale rather than presented as current; invalid/future data fails closed. Moved the public-feed status to the dashboard hero and added a direct official leaderboard link.
* Changed the feed schema so every refresh has `checked_utc`, but `observed_utc` is null unless a rank-one score was actually parsed. Added regression coverage for stale, out-of-range, future, valid, and failed-refresh cases; corrected the HTML test fixture to be well-formed.
* Rebuilt the site comparison cell to report each historical TIFF's maximum directed 3px overlap, the closest peer site, and the strict 70% decision. The builder now fails if its displayed `unique_among_focus9` flag disagrees with the measured overlap. Labels explicitly mean spatial similarity under the protocol, not byte identity.
* Expanded the generated README charter with the nine-site goal, score-evidence classes, the 3–5-hypothesis gate, the stop rules, 24-hour feed policy, core values, and current missing-input/stop status. No model lane was resumed and no replacement raster was written.

### Pass 3 — independently re-run implementation and release checks

* `.venv/bin/pytest -q`: **26 passed**, 12 existing Rasterio `PendingDeprecationWarning`s. The environment was installed into ignored `.venv/`; no dependency artifacts are tracked.
* `python -m compileall -q src scripts tests`, `node --check docs/feed.js`, generated-page/link tests, and `git diff --check` pass. The local preflight passes only format/range checks for the historical artifact; `ok_to_submit` remains false. The retired pipeline exits nonzero at the duplicate stop as designed.
* **No new model experiment, holdout score, submission TIFF, or weekly-slot selection was performed.** The single pinned witness still places 37,533/37,654 existing candidate dots within 3 px (99.68%), above the 70% cap; that candidate remains DO NOT SUBMIT. The original surface gate and complete registry inventory are unavailable.

## Re-review — 2026-10-30 UTC (merge reconciliation and format-gate correction)

### Pass 1 — reconcile concurrent repository changes and evidence

* After opening PR #33, `main` advanced through PRs #28, #29, #30 and #32, making the feature-table generator conflict. Fetched and merged the updated `origin/main` into this assigned branch, reviewed the incoming changes, and preserved the official-rule evidence, CLI fix, and answer-first executive section. No other branch was checked out or modified.
* Reviewed `evidence/official_rules_check.json`, whose recorded 2026-10-30 fetch-tool excerpts state that outside-bounds data must be null/NaN. The local sample's NaN mask is tested in `tests/test_official_format.py`. These are inherited, dated evidence; this sandbox could not independently refetch the competition portal or current public leaderboard.
* Confirmed the archived MAW-GSI TIFF contains zeros outside the mirrored sample footprint. It therefore passes only the historical local grid/range checks, not the documented outside-mask rule. Its uniqueness stop remains unchanged: 37,533/37,654 dots (99.68%) overlap one pinned witness within 3 px.
* Corrected the public-feed snapshot semantics: the 2026-10-30 failed refresh is recorded as `checked_utc` with `observed_utc: null`; the dated fetch-tool observation of 0.4544 is not put in the live feed or labeled current. The fresh-feed viewer hides successful snapshots at 24 hours.
* Re-audited `focus9_reaudit.json`: every focus-site TIFF fails the 70% directed 3px rule against its closest other focus site. These spatial measurements do not claim byte identity. The training-feature TIFF and feature cache are absent from this checkout; no model work was resumed.

### Pass 2 — correct executive reporting and shared format tooling

* Kept the nine-site executive summary and added each site's measured maximum directed 3px overlap and closest peer to README/dashboard rows. The builder fails closed if a measurement/peer is missing, the nine sites are not distinct, or the stored uniqueness flag disagrees with the 70% threshold.
* Restored the detailed project charter in the README, placed the public-feed status at the top of the dashboard, and labeled 0.4544 as a dated direct observation rather than a current value or file score. The current scheduled feed remains explicitly unavailable.
* Updated the shared writer/validators to preserve every in-footprint prediction, require finite [0,1] values inside the sample footprint, reject infinities and outside positive mass, and serialize NaN exactly outside the sample mask. The validation receipt records the NaN mask in a JSON-safe form. The literal uniqueness gate canonicalizes only outside-mask zero/NaN cells for comparison, so NaN outside does not bypass or weaken the overlap/rank thresholds.
* Added regression coverage for the CLI's grid path, exact sample mask, no NaN inside, no positive mass outside, mask mismatch, and zero-outside versus NaN-outside uniqueness equivalence. The archived TIFF remains unchanged and fails the corrected outside-mask check.

### Pass 3 — test and stop-state verification

* `.venv/bin/pytest -q`: **32 passed**, 15 Rasterio pending-deprecation warnings.
* Python `compileall`, `node --check docs/feed.js`, generated-page/link checks, and `git diff --check` passed. The format-only validator now correctly returns failure on the historical zero-outside TIFF; it also returns `ok_to_submit: false` because uniqueness and selector approval remain blocked.
* `scripts/run_apartgems_pipeline.py` still exits 2 at the mandatory duplicate stop, before model execution or raster generation. No new HOLDOUT-DTI result, TIFF, upload, receipt, or weekly slot was created. PR #33 is the only PR created by this review; do not merge until CI and final branch checks are green.
