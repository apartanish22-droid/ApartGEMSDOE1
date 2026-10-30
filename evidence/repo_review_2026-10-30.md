# Repository review · 2026-10-30

Scope: full repo review of `arena/cf36ddec-apartgemsdoe1` (base `351c64c`, `main`). Three passes, as the standing protocol requires.

**Run tally for this session**
- Experiments run: 0 (no model trained, no holdout DTI computed, no candidate generated)
- Submission slots used: 0
- Files changed for the competition: none
- OK to download and submit: NO. No file in this repository is cleared for upload.

Every fact below cites either a file in this repo, an official page (quoted in `evidence/official_rules_check.json`), or a command output recorded here. Anything not checked is labelled.

## Reconciliation with the parallel review on main

Another session added `evidence/repository_review_2026-10-30.md` to `main` (merge of PR #29). It reaches the same decision: negative, do not submit. Differences:

- It records the scripted feed as unavailable (TLS EOF). This review records a fetch-tool read of 0.4544, labelled as a direct read and not as the feed value.
- It reports 24 passing tests. This review reports 29 after the regression tests added here.
- This review adds the CLI fix (F1), the official-rule finding that the zero-outside policy does not match the official null/NaN rule (F2), and the verbatim official excerpts. The other review does not contain these.

Neither review generates or clears a file.

## Pass 1 · Inventory and verification

| Check | Result | Evidence |
| --- | --- | --- |
| Test suite before changes | 24 passed | `pytest -q` in `.venv` (Python 3.11.2; numpy 2.4.6, rasterio 1.4.4, scipy 1.17.1, scikit-learn 1.9.1) |
| Prior TIFF SHA-256 | `09fa04bd481d896a4dcbb808e4ef8136f8e6d0e0d88cebe9afd957db2779d62f` (matches README) | `sha256sum docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif` |
| Local format validator on prior TIFF | exit 0; all 15 format checks true; `ok_to_submit=false` | `scripts/validate_submission.py --format-only` |
| Literal witness audit (reproduced) | overlap `0.9967865299835342`, 37,533 / 37,654 dots, verdict negative | `scripts/audit_literal_witness.py --out /tmp/…` (matches `evidence/literal_witness_audit.json`) |
| Nine focus-site re-audit (reproduced) | all 9 rows identical to committed `evidence/focus9_reaudit.json` (commit, SHA, overlap, closest site, unique flag) | `scripts/audit_historical_focus.py --out /tmp/…` |
| Mirror data restore (scratch copy) | `all_pins_verified: True`: 5 core, 17 external, 7 DEM10, 1 assembled training stack (418,912,844 bytes, SHA-256 `4371c82e…23bc5`) | `prepare_data.py --fetch` run in a `git archive` copy, not in the repo |
| Official submission rules | Verified: float32, single layer, EPSG 32611, 100 m, values 0–1, **outside bounds null or nan** | `evidence/official_rules_check.json` R1, R2 |
| Official metric | Verified: distance-weighted Tversky, α=0.2, β=0.8, R=300 m | R3 |
| Scored labels | Verified: test faults are **new** faults not in the USGS database | R4 |
| Official leaderboard top | 0.4544 (observed 2026-10-30) | `leaderboard_observed` |
| Reference solution | Writes raw float predictions with no NaN step; georeferenced from the labels raster | `reference_solution_check` |
| Sample template NaN pattern | 5,167,373 finite cells = footprint; 7,111,787 NaN cells | computed from `data/bridge/sample_submission.tif` |

## Pass 2 · Defects, irregularities, and fixes

| # | Severity | Finding | Status | Evidence / test |
| --- | --- | --- | --- | --- |
| F1 | High (tooling) | `scripts/submission_writer.py` pointed at `data/sample_submission.tif`, which exists only after `prepare_data.py` creates symlinks. The CLI failed on a fresh checkout with `FileNotFoundError`. | **FIXED**: now uses `grid.DATA_DIR` (the same directory `load_grid` hash-checks). | `tests/test_official_format.py::test_cli_writer_runs_on_fresh_checkout_grid` |
| F2 | High (rule) | The repo's gated writer and validator require all-finite values, which means zeros outside the footprint. The official rule says outside-bounds cells must be null or nan. The sample template uses NaN. The prior file therefore does not match the rule. | **FLAGGED, not changed.** Changing the default policy is a portal-behaviour decision. Verified locally: a NaN-outside variant with identical in-footprint values reproduces the sample's NaN mask exactly. | `tests/test_official_format.py::test_nan_outside_variant_reproduces_official_sample_nan_mask`; the gated writer still refuses NaN (`…gated_writer_still_refuses_nan…`) |
| F3 | High (unknown) | The user-reported portal error "Predicted values must be in range [0, 1]" cannot be tied to a file. The error text is unexplained, and no file in this repo produces it: the prior file is finite and in range. | **OPEN.** Needs the exact file name and SHA-256 that was uploaded, plus the portal message. | Listed in the executive summary |
| F4 | Medium (claims) | The prompt gives 0.4413 as the leaderboard high and 0.3195 as "highest right now". The official public top is 0.4544. The prompt's site claims (0.2449–0.2778) are unconfirmed. | **FLAGGED.** Labelled USER-REPORTED throughout. | `official_rules_check.json` → `user_claims_not_on_leaderboard` |
| F5 | Medium (feed) | On 2026-10-30 the scheduled leaderboard refresh failed (TLS EOF), so `docs/data/public_feed.json` now reads `unavailable`. This sandbox cannot run the script either, because drivendata.org is not on the allowlist. | **FLAGGED.** The feed was not hand-edited. The 0.4544 value was read with a fetch tool, labelled as a direct read, and kept out of the feed. | `scripts/update_public_feed.py`, `.github/workflows/pages.yml` |
| F6 | Medium (API hazard) | Two different `write_submission` functions. `gems57/__init__.py` exports the `grid.py` version (`mode="zeros"|"nan"`). The gated `submission_writer.py` version has a different signature. A caller who imports from the package gets the wrong one. | **FLAGGED.** Rename recommended in the next session; not renamed now to avoid breaking callers. | `src/gems57/__init__.py`, `src/gems57/grid.py`, `src/gems57/submission_writer.py` |
| F7 | Info | `data/official/labels.tif` is byte-identical to `existing_faults.tif` (SHA-256 `7ba308cc…093`). This is consistent with the official rule that training labels are existing fault data. It also means no separate label raster exists. | Verified consistent; noted. | R5 |
| F8 | High (scientific) | The scored test faults are new, not in the USGS catalogue. The repo's hide-and-recover holdout uses the same catalogue. The holdout is a proxy and will not reproduce leaderboard behaviour directly. | **FLAGGED** as a standing limitation. | R4 |
| F9 | High (method) | Static replay of a finished raster on the holdout is not valid for the nine focus files. Those rasters were built from the full catalogue, so their holdout numbers would be leaky. The repo's `evaluate_holdout.py` docstring already says this. | **FLAGGED.** No holdout estimate is given for any historical file. | `scripts/evaluate_holdout.py` docstring |
| F10 | Medium (protocol vs rules) | "Unique" in the repo means a 3-pixel overlap limit against a registry. That is an internal protocol, not an official rule. The official relevant rule is the originality warranty (A.5 item 1). | **FLAGGED for the user.** Both should be cited separately. | R7 |
| F11 | Medium (disclosure) | Official §3.2 requires a generative-AI disclosure in the narrative. No narrative has been drafted for any submission. | **PENDING** (shown on the executive summary). | R8 |
| F12 | Info (data) | The mirror restore (`prepare_data.py --fetch`) works in this sandbox and verifies all pins. The restored bytes are owner-mirror data, not organizer-origin data, so the login-gated official data is still unavailable. (The phrase "single remaining blocker" is in the user's prompt, not in the repo.) | Recorded. The README access section still names the organizer login as the blocker. | Pass 1 |
| F13 | Low | The generated format bullet said the outside-bounds policy was unverified. The rule text is now verified (quoted), and the portal's behaviour is still untested. | **UPDATED** in the generator and README. | `scripts/build_pages_and_readme.py` |

## Pass 3 · Recheck against the request

| Request | Status in this session |
| --- | --- |
| Review the repo | Done (Passes 1–2). |
| Executive summary that says clearly whether a file can be downloaded and submitted | Done: "Answer first" table at the top of the executive summary. Answer: **No**. |
| Estimated score for each file | Not estimable: no v3 holdout score exists. Stated, not invented. |
| Unique vs the GEMSDOE sites | Nine focus files: each has a nearest focus-nine neighbour at 97.6%–100% overlap (directed, 3 px). Complete registry not built. |
| Generate a unique TIF | **Not done.** Reasons are on the executive summary: no holdout score, no complete registry, portal behaviour unknown, and the official top is 0.4544. |
| Official rules and links, line by line | Done for the official pages. Quotes live in `evidence/official_rules_check.json`, and the site renders them. |
| Flag irregularities | Done: F1–F13. |
| Pull request and merge to main | To be done after tests pass (see the session summary). |

## What is still missing (ordered)

1. **The failing file.** The exact file name, SHA-256, and portal message behind "Predicted values must be in range [0, 1]" (F3). The submission page can show this without using a slot.
2. **A complete, pinned registry.** The sites in the prompt, enumerated through the GitHub API, with the SHA-256 of each raster. Only the witness and nine files are checked now.
3. **A v3 holdout run** on a freshly trained candidate, with leakage canaries (AUC above 0.90 means leakage), using the restored feature stack.
4. **A portal test of the NaN convention** (F2). This needs an upload decision, which belongs to the user and the selector.
5. **Rename the duplicate `write_submission`** (F6) in a session that is allowed to touch shared callers.
