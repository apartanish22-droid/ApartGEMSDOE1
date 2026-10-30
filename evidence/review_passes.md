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

## Session review — 2026-10-30 UTC

No new hypothesis experiment or submission candidate was started. The inherited lane already has a mandatory duplicate stop, the original pre-placement surface is missing, and no complete registry or current v3 baseline is available.

### Pass 1 — inspect and re-verify evidence

* Re-read the README charter, generated dashboard, data-preparation path, shared uniqueness/holdout/format validators, run cards, and focus-nine manifest. Confirmed that `.cache/training_features.tif` and cached feature bands are absent in this checkout; the checked-in `data/manifest.json` is a historical receipt, not proof that those ignored cache files are present now.
* Re-fetched all nine immutable focus-site rasters through GitHub at their manifest-pinned commits. All 9/9 fetched, Git blob IDs and SHA-256 pins matched, grid metadata matched, and the audit reported zero errors. No organizer receipt or hidden target labels were available.
* Re-fetched the immutable 13GEMSDOE lattice witness and re-ran the negative candidate audit: 37,533/37,654 prior dots are within three pixels (99.6787% directed overlap, above the 70% stop). The original surface gate and complete registry remain unavailable; this single witness proves failure but cannot certify any other candidate's uniqueness.
* Reconfirmed the focus-nine pairwise nearest-peer overlaps: 97.5781%–100.0000%, all above 70%. GEMSDOE32 support is pixel-exactly GEMSDOE25 support after removing cells within two pixels of the catalogue; GEMSDOE25 and GEMSDOE30 supports are identical. This establishes geometry, not why their user-reported scores differ.

### Pass 2 — fix review findings

* Replaced the confusing focus-nine table label: it now gives the exact directed overlap and closest peer separately from the prior ApartGEMSDOE1 candidate comparison. The prior-candidate overlap is explicitly diagnostic and is not misrepresented as the focus-nine uniqueness test.
* Found that the archived H-APART-6 runner imported NumPy/SciPy/scikit-learn before checking the mandatory stop. Replaced it with a standard-library-only retired-runner tombstone that exits before scientific imports; missing or malformed audit evidence also fails closed. No historical experiment can be relaunched by this entry point.
* Added a 24-hour freshness rule to the leaderboard feed. The stored 2026-10-28 observation (0.4544) is now marked historical, not current; the current value is null/unavailable, and the browser hides stale or out-of-range values. The 0.3195 and 0.4413 figures in the request conflict with each other and were not independently verified in this sandbox.
* Added a pull-request / main-branch CI workflow that installs the documented Python stack, checks Python and browser JavaScript syntax, and runs the automated test suite.

### Pass 3 — regression and final decision

* `27 passed, 12 warnings` with `.venv/bin/python -m pytest -q`; warnings are rasterio/Affine pending deprecations. `node --check docs/feed.js`, Python `compileall`, and `git diff --check` passed.
* The archived H-APART-6 command exited 2 under `python -S` (no third-party packages on `sys.path`) with the duplicate-stop message. The H-APART-2 runner also exited 2 before an experiment.
* The existing TIFF passed local single-band/grid/float32/finiteness/[0,1] checks, SHA-256 `09fa04bd481d896a4dcbb808e4ef8136f8e6d0e0d88cebe9afd957db2779d62f`, but `ok_to_submit=false` because uniqueness/holdout/selector gates are not cleared. No new TIFF, holdout DTI, projection, organizer receipt, upload, or weekly slot was produced.
* Decision: **negative; do not download or submit the archived TIFF**. A future candidate requires an assigned method lane, present/source-bound feature cache, same-v3 holdout baseline and feature canaries, pre-placement and final checks against a complete accessible registry, and authenticated organizer template/outside-bounds behavior before separate selector review.
