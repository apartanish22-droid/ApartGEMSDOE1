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

## Three-pass repository review — 2026-10-30 UTC

No new model experiment, candidate raster, selector action, or competition submission was made. The protocol's existing duplicate stop remained controlling.

### Pass 1 — reproduce the high-risk evidence and inspect the published claims

* Installed the declared Python dependencies in an ignored local `.venv` only; no project dependency files or data were changed by installation.
* Re-ran `scripts/audit_historical_focus.py`: all nine pinned owner-mirror rasters resolved with no errors. Every one of the nine has more than 70% of its positive cells within three pixels of at least one of the other eight named rasters (`unique_among_focus9=false`). The audit remains limited to these nine mirrors, not the complete competition registry.
* Re-ran `scripts/audit_literal_witness.py`: the historical ApartGEMSDOE1 raster remains a protocol duplicate against the hash-pinned 13GEMSDOE lattice: 37,533 / 37,654 dots, forward 3-pixel overlap 0.9967865299835342. The one-witness result proves failure but cannot certify uniqueness.
* Re-ran `scripts/audit_holdout_mask.py`: v3 mask regression reproduced 11,360 withheld positives and an exact visible-only mask; this is a mask check, not a HOLDOUT-DTI model result.
* Re-read the official DrivenData problem page and public leaderboard on 2026-10-30. The task is geological-fault prediction (not direct vent detection); DTI uses α=0.2 for false positives, β=0.8 for false negatives, and a 300 m triangular kernel. The public table showed 0.4544 at rank 1; 0.3195 at rank 48; 0.4413 was absent from the displayed top 50. Stored a date-stamped observation and labeled it as public standings, not a file receipt.
* Confirmed the actual cached feature stack is absent in this checkout: 0 of 19 `.cache/features/band-*.npy` arrays and no `data/official/training_features.tif`. The old feature-cache JSON is a historical report, not usable features.
* Found a published-summary defect: the audit recorded all nine focus-site uniqueness flags as `false`, while the generated executive table displayed “Unavailable” and said those nine comparisons were below the threshold. This contradicted the underlying audited measurements.

### Pass 2 — correct the decision surface without bypassing the stop

* Fixed the README/dashboard generator to render each focus site's maximum directed 3-pixel overlap, its closest listed site, the 70% gate, and “DO NOT SUBMIT”; clarified that this is spatial near-duplicate status, not byte identity.
* Added the same auditable nine-site table to the executive-summary/submission-guide page. The table distinguishes user-reported historical claims from a new-file score estimate; the latter remains unavailable because no same-version holdout-to-leaderboard calibration exists.
* Corrected the user-cited leaderboard figures in the pages and current public-feed snapshot, and added `evidence/leaderboard_observation_20261030.json`. The official top public standing is not presented as a score for this repository's TIFF.
* Hardened the scheduled feed parser to accept either the official HTML table or a rendered pipe-table fragment while still requiring one labeled rank-one Tversky value; corrected the malformed HTML unit fixture.
* Added a generated input-readiness disclosure for the missing feature stack. Kept all historical TIFF download links explicitly labeled research-only; generated no new TIFF and did not spend a slot.
* Added regression tests for all nine uniqueness rows, the no-estimate state, the dated leaderboard observation, both HTML summary pages, and HTML/pipe-table feed parsing.

### Pass 3 — independently re-check the final state

* `pytest -q`: **27 passed**, with 12 rasterio/Affine pending-deprecation warnings. The new tests verify each row's overlap against the checked audit JSON, ensure a public leaderboard observation cannot be mistaken for a file score, and cover both feed encodings.
* `python -m compileall -q src scripts tests`, `node --check docs/feed.js`, the page generator, HTML/README link tests, and `git diff --check` all passed.
* `validate_submission.py ... --format-only` returned a local format/range pass for the **historical** TIFF (one float32 band, EPSG:32611, shape 3730×3292, matching stored sample transform, finite [0,1]); the full preflight still reports `ok_to_submit=false`, no registry clearance, no holdout evaluation, and no selector approval.
* Added `evidence/run_card_20261030.json` as the current review-only negative card; it references the existing audit TIFF and explicitly records that no new raster or model score was produced. The older `evidence/run_card.json` remains the historical lane card.
* Final status remains **negative / no file ready**. The candidate's pre-placement surface is still unavailable, the complete registry is still inaccessible, the 19-band cache is absent, and no corrected v3 HOLDOUT-DTI run was authorized after the literal duplicate stop. The 2026-10-28 v2 holdout result remains historical and non-comparable; no new leader-score estimate is made.
