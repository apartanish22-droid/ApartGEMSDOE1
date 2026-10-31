# Repository review — 2026-10-31 UTC

## Executive decision

**Negative / blocked. No TIFF in this repository is cleared for download-and-submit.** The inherited candidate still fails the required literal 3-pixel uniqueness threshold against a pinned witness. The working lane is stopped. In accordance with the supplied parallel-run protocol, this review did not select a different geological method, train/score another candidate, create a competition candidate TIFF, or use a submission slot.

The archived TIFF is available solely as an audit artifact and should not be submitted. Local format success does not overcome the uniqueness failure, the unresolved official outside-footprint behavior, missing current model evidence, or absent selector approval.

## Three review passes

### Pass 1 — request, repository, and evidence inventory

- Confirmed branch `arena/7b1e19fc-apartgemsdoe1`, clean before review, at the session's supplied base commit. Repository includes a fail-closed dashboard, executive guide, 9-site forensic audit, four ranked future hypotheses, shared holdout/uniqueness/validation tools, and a run card.
- Reviewed the mandatory run protocol and the checked-in `evidence/literal_witness_audit.json`: the archived raster has 37,533 / 37,654 dots within 3 pixels of one pinned 13GEMSDOE lattice, forward overlap 0.9967865299835342, above the 0.70 stop threshold. This single witness is enough to reject that candidate; it is not a complete-registry uniqueness certificate.
- The prompt's single method paragraph is not identifiable as an authorization for a new lane. The existing lane has explicit duplicate-stop evidence. Therefore the protocol's immediate stop takes precedence over the request to create a different TIFF. The 3-experiment / 2-hour budget was not consumed by model experiments.
- The checked-in focus-nine evidence covers the named sites only and records user-reported scores without organizer receipts. It does not support a future score estimate. The GEMSDOE32 0.2778 mechanism remains a plausible redundancy-pruning interpretation, not causal proof.
- The assembled training-feature raster (418,912,844 bytes per the manifest) is absent from this checkout. The checked-in `data/official/labels.tif` is present, but its SHA-256 is exactly the same as `existing_faults.tif`; these are pinned owner-mirror catalogue bytes, not independent training labels or hidden truth. The checked-in source notes say the competition data page redirects to login. No new external source binary was downloaded or treated as organizer-authenticated in this review.

### Pass 2 — execute available safety checks

- Created an ignored local virtual environment from `requirements.txt` because this checkout's base Python had no NumPy or pytest. No dependency files or tracked environment artifacts were added.
- Full regression suite: `.venv/bin/pytest -q` → **37 passed, 16 Rasterio pending-deprecation warnings**.
- Format-only check: `.venv/bin/python scripts/validate_submission.py docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif --format-only` → one float32 band, EPSG:32611, shape 3730×3292, transform matches stored template, finite values in [0,1]. The report explicitly states `ok_to_submit=false`; additionally, this archived file contains zeros outside the footprint whereas the recorded official problem rule specifies null/NaN there.
- `python -m compileall -q src scripts tests`, `node --check docs/feed.js`, strict parsing of all evidence/docs JSON, strict `pyproject.toml` TOML parsing, and `git diff --check` passed.
- The scheduled public leaderboard feed in `docs/data/public_feed.json` is still `unavailable`; it was not refreshed in this review. The separate 0.4544 public-page observation is dated 2026-10-30 and must not be described as today's live leaderboard.

### Pass 3 — adversarial consistency and release decision

- Verified that the published README/dashboard/guide all make the no-submit status prominent and label the old TIFF research-only; none describes a format preflight as organizer acceptance.
- Verified all three run-card mirrors have the current branch name. Updated the canonical run card with this review's audit-only status; no holdout DTI, CI, raster, score estimate, or receipt was fabricated.
- Confirmed the essential blocker is not a failing unit test: it is scientific and procedural—duplicate threshold, absent complete registry, no current same-v3 HOLDOUT-DTI/CI, no separate selector approval, and unresolved portal details.
- No new TIF was emitted. The only linked TIFF remains a historical artifact and its SHA-256 is `09fa04bd481d896a4dcbb808e4ef8136f8e6d0e0d88cebe9afd957db2779d62f`.

## Evidence labels and source limits

- Historical site scores are **user-reported claims**, not organizer receipts.
- The old v2 value in the run card is **HOLDOUT-DTI** for `gems57-pooled-hide-v2`, 11,360 withheld positives, with the recorded 95% CI; it is non-comparable to the corrected v3 evaluator and is not a leaderboard estimate.
- Current v3 is **not evaluated**; DTI and CI are null. No `ORGANIZER-CONFIRMED` file score exists in this repository.
- Official rule excerpts and their links remain in [`official_rules_check.json`](official_rules_check.json). This review checked those saved quotations and local implementation; it did not claim to freshly retrieve the live competition page, leaderboard, rules PDF, or external datasets on 2026-10-31.

## Remaining work / blockers

1. Obtain the competition feature stack, labels, and exact template through authorized access; record trusted provenance and hashes. Do not treat an owner mirror as official provenance.
2. Produce and pin a complete accessible registry inventory and preserve every pre-placement surface. Any one duplicate witness remains an immediate stop.
3. Only after a separately authorized single method lane is defined, run per-feature leakage canaries and the shared visible-only, buffered, spatially blocked v3 holdout. Report DTI, evaluator version, withheld-positive count, and 95% CI; compare to a same-evaluator baseline.
4. Verify all official format/grid requirements with a newly generated candidate, then pass surface and final-dots uniqueness checks. Resolve NaN/outside-footprint portal behavior through authorized format guidance or a safe validation path—not by trial upload.
5. Require separate selector approval under the current weekly cap before any upload. Preserve the submission-page receipt for organizer-confirmed scoring.
6. Restore an authenticated/current leaderboard feed; keep stale values hidden and label direct public standings separately from file receipts.

## Final run-card summary

- Hypothesis: no new hypothesis executed; existing lane remains stopped.
- Mechanism: none tested this review.
- Named non-fault mimic: not applicable to a new experiment; inherited geological candidates and mimics are listed in `evidence/next_hypotheses.md`.
- HOLDOUT-DTI: no current v3 value or CI (not run); historical v2 is non-comparable.
- Registry: archived candidate overlap 99.67865299835342% within 3 px against one pinned witness; surface correlation was not tested; inventory incomplete.
- Raster SHA-256: archived audit-only TIFF `09fa04bd481d896a4dcbb808e4ef8136f8e6d0e0d88cebe9afd957db2779d62f`.
- Validator: local format/grid/range pass only; values finite in [0,1], CRS/shape/transform match; footprint outside-value policy conflicts with saved official rule excerpt; `ok_to_submit=false`.
- Submission name/note: historical `apartgems1-maw-gsi-e3-20261028-87f83db9`; audit-only, do not submit.
- Verdict: **negative**.
