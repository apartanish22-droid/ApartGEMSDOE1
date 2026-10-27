# Three review and fix passes

These are reviews of research infrastructure, not geological experiments or submissions. This audit produced no candidate or holdout score. A parallel run had already committed a synthetic demo, which was reviewed separately.

## 1. Implement, reproduce, and verify evidence

- Restored all 12 light inputs into an empty cache through GitHub, checked size and SHA-256, and reran the audit. Preflight, lineage, nine-site matrix and run card matched the prior run. The optional 19-band mirror was hash- and grid-checked and prepared with byte-identical pinned shared code.
- Corrected the geometric bound so reference positives just outside a footprint can still cover inside cells; added a synthetic boundary regression. Stopped the champion-sized plan at the literal lattice witness, without asserting that smaller budgets are impossible.
- Recorded owner-mirror provenance, actual sources, missing receipts, missing lane/stack/complete registry, and the shared writer's continuous-to-Boolean behavior. Absolute machine paths were removed from the committed preparation receipt.

## 2. Bug, negative-case, and interface review

- Added validation against non-boolean geometry inputs, empty/misaligned rasters, hidden nodata, nonfinite/out-of-range values, positive outside pixels, incorrect CRS/shape/transform/bands/dtype, and exact inclusive radius behavior. A non-authorizing CLI now defaults to a conservative null-outside-footprint policy; the all-finite alternative is diagnostic only.
- Added offline, malformed-data and unsafe-link/injection frontend tests. In a real headless Chromium session, opened all 12 dashboard pages at 1440 px and 390 px: no page errors, failed resource responses or viewport overflow. Made wide tables keyboard-scrollable and added a mobile scroll hint.
- Local automated checks at this pass: 48 Python tests and 5 frontend tests passed. Synthetic failures, a checked historical TIFF, and the independent pinned audit were used; no new geological prediction was made.

## 3. Requirements, publication, and operational review

- Verified that the historical values are labeled unverified, no scores are invented, the candidate link is disabled, all relative local HTML links resolve, and the run card and dashboard agree. The page lists nine selected historical files, not every file in the complete registry.
- Anchored the root data ignore so `docs/data/*.json` is published; kept large caches out of Git. Added stale/invalid GitHub-head detection, a scheduled Pages workflow, CI, and a legacy-root redirect fallback. A lookup failure publishes an explicit unknown; an error writing freshness now fails the workflow rather than silently deploying an old snapshot.
- Disabled the unsafe legacy parallel demo generator, private evaluator and writer entry points rather than using them in place of canonical tools; historical code remains in Git history. Presence-only readiness now stays blocked.
- A concurrently merged synthetic H1 demo failed the pinned mirror transform check and remains research-only; the 3,602 outside-positive cells are an array-index diagnostic, not a geospatial match. Its separate saved-byte report is `docs/data/parallel-demo-validation.json`.
- The GitHub workflow definitions had not run remotely at the time this review was recorded. Source-head changes are not automatically re-audited; the public site says so. The portal's outside-footprint behavior, shared-tool repair, official data identity, file-specific organizer receipts, future slot availability, and leaderboard score remain unresolved.
