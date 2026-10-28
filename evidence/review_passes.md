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
* GitHub repository metadata reported push/admin permission and an existing legacy Pages site rooted at `main:/`; the integration was not permitted to read the branch-protection or Actions-permissions endpoints (HTTP 403). Concurrent PRs #23 and #24 reached main during this review and repeated the superseded promotion claims; this negative audit is intended to correct them. Treat merge and Pages deployment as separate operations whose outcomes require explicit confirmation. A scheduled Action exists for the public feed, but on the legacy branch-based Pages configuration its scheduled deployment has not been proven.
