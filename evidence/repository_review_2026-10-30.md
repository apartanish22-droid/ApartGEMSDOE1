# Repository review — 2026-10-30 UTC

## Decision

**Negative / blocked. Do not submit any TIFF from this repository.** The protocol's mandatory duplicate stop remains in force. No new experiment, model score, prediction raster, or slot selection was made in this review. The prior TIFF is retained for audit only.

## Findings, highest impact first

1. **Release blocker — uniqueness cannot pass.** The inherited MAW-GSI candidate has 37,533 of 37,654 positive pixels within 3 px of one pinned registry witness (forward overlap 0.9967865; limit 0.70). The pre-placement surface was not preserved, and the registry scan is expressly incomplete. One witness proves that candidate fails; it cannot certify any new candidate. Evidence: [`literal_witness_audit.json`](literal_witness_audit.json), [`run_card.json`](run_card.json).
2. **No comparable holdout result or estimate exists.** The corrected evaluator is `gems57-pooled-hide-v3`; its holdout DTI and CI are null because the duplicate stop prevents the next run. Historical v2 values are explicitly non-comparable. The claimed GEMSDOE32 0.2778 and the other prompt scores have no submission-page receipts in this repo, so they remain user-reported, not organizer-confirmed. Do not translate a holdout statistic into a leaderboard projection.
3. **Leaderboard feed freshness is currently unavailable.** The checked-in feed had an observation dated 2026-10-28 with top public DTI 0.4544. A refresh attempted on 2026-10-30 failed with a TLS EOF, so the feed has been replaced by an explicit `unavailable` observation; stale 0.4544 is no longer presented as current. The user's 0.3195 claim is not reconciled with that prior public observation. The official leaderboard link is provided for a live check. This runtime cannot access DrivenData directly; no claim is made about today's leaderboard.
4. **Organizer data and submission authorization are not available here.** The repository contains small owner-mirror rasters but not `training_features.tif`; the official competition data page requires login per the recorded access audit. Consequently this review did not train a model or reproduce an official-template preflight. No organizer upload or receipt is available. Local TIFF format validation does not imply portal acceptance.
5. **External-source provenance remains a research gate.** Owner-mirror content hashes and public-source links do not authenticate every raster's official origin, license, coverage, or processing lineage. The four preregistered future hypotheses in `docs/next-hypotheses.md` are design candidates only, not validated improvements. Their raw-input provenance and any new external-data viability must be verified before a future assigned lane starts.

## Scope and verification

- Checked the nine-focus audit for sites GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36. The saved audit says nine files were fetched and examined, records no fetch errors, and classifies each score as a user claim; it is a pinned mirror audit, not a full global registry.
- Ran the retired pipeline entry point: it exited with the expected stop code and did not run an experiment or write a TIFF.
- Ran the local format-only check against the archived TIFF: one float32 band; EPSG:32611; shape 3730×3292; matching stored sample transform; all pixels finite; values in [0,1]. The report correctly returned `ok_to_submit=false` without registry and selector clearance.
- Installed requirements in the ignored `.venv` and ran `.venv/bin/python -m pytest -q`: **24 passed**, 12 Rasterio pending-deprecation warnings. Also ran `compileall`, `node --check docs/feed.js`, and `git diff --check` successfully.
- Refreshed `docs/data/public_feed.json` on 2026-10-30. Result: `status=unavailable`, `top_public_dti=null`, caused by TLS EOF. This is a refresh failure, not a competition-side statement.

## Three review passes

1. **Inventory pass:** examined repository docs, evidence/run cards, focus-nine audit, pipeline stop, format validator, feed code, and workflow. Confirmed existing work already documents the negative result and ranked hypotheses; no basis to choose or emit a new submission.
2. **Execution pass:** ran the automated tests, syntax/compile checks, stopped-pipeline check, format-only TIFF validator, and an actual leaderboard refresh. Tests pass; the refresh failure was caught fail-closed and the stale snapshot cleared.
3. **Independent consistency pass:** checked that the UI labels the archived file research-only, distinguishes the public leaderboard observation from an upload receipt, does not expose the old score as current after failure, and that the run card, literal witness evidence, CLI, and tests all continue to say negative / not submit-ready. No contradictory promotion instruction found in the reviewed paths.

## Next work (requires a genuinely new, separately assigned method lane)

1. Obtain the official competition feature raster, labels and exact submission template using an authorized route; record provenance and checksums. Do not substitute an unauthenticated mirror as proof of official origin.
2. Assemble an accessible, versioned, hash-pinned registry inventory and retain every pre-placement surface. A complete accessible scan is a minimum gate, not proof that every private/unlinked entry has been found.
3. Select one preregistered hypothesis, rederive catalogue features fold-locally, run each feature-only leakage canary, and compare with a same-v3 baseline using the shared evaluator and 95% CI. Budget at most three experiments/two hours and stop immediately on either uniqueness threshold.
4. Only if the surface passes, place points and rerun literal uniqueness plus format/range/grid validation. Then use a separate selector within the live weekly cap; preserve the organizer receipt as the only source of an organizer-confirmed score.
5. Repair leaderboard refresh availability in the Pages runner if it persists; preserve explicit unavailable status rather than a stale numeric value.

**Download instruction:** the archived TIFF is a research artifact only. It is **not OK to download and submit** as a competition entry. No new unique TIFF was generated because the governing protocol requires an immediate stop on the observed duplicate, and there is not a validated alternative lane or holdout win.
