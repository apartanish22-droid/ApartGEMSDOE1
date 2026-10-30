# Three-pass implementation and review record

Review date: 2026-10-28 UTC. No model experiment, replacement candidate, submission, or slot selection was performed in this review. The negative result is the release decision.

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
