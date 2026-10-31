# Three passes · 2026-10-31

## Pass 1 · implement

* Restored the feature stack and caches; installed the environment; confirmed pins.
* Ran the three permitted experiments: E1 base (invalid, catalogue-proximity leakage), E2 geo-static (leak-free baseline), E3 geo+paired-static (leak-free). Budget spent.
* Emitted one GeoTIFF from E3 (30,562 dots, SHA-256 `c4d504b8…`).
* Built a registry enumeration (3,273 GeoTIFF blobs, 92 owner repos) and a two-tier uniqueness scan (`scripts/registry_scan.py`).
* Built the decision record, the decision page (`docs/download-and-submit.html`, also the Pages home), the README, the project brief and this review.

## Pass 2 · review and fix

Defects found and fixed in this pass:

| # | Finding | Fix |
|---|---|---|
| 1 | Receipt JSON contained NaN (nodata) and failed strict JSON | Stored as the string `"NaN"` |
| 2 | Receipt reported the temporary validator path | `write_template_submission` sets the committed name |
| 3 | `compare_array_to_registry` rejected NaN outside the footprint (official rule), so the scan crashed | Strict in-footprint check; outside cells set to 0 for scoring only; positive mass outside still refused |
| 4 | `validate_submission.py` used the all-finite (zeros-outside) policy and crashed on NaN JSON | Uses `validate_template` against the official sample; `_jsonable` keeps the report strict JSON |
| 5 | `prepare_data.py --fetch` rewrote `evidence/feature_cache.json`, dropping the "historical_only" warning and rewording a band-6 finding | Committed versions restored; flagged as an irregularity |
| 6 | **Holdout allocation differs from the emitted allocation.** Holdout: per-cell, 281,318 dots. File: one full-footprint allocation, 30,562 dots. The E3 score does not describe this file | Verdict set to "not measured"; recorded in the decision record and README |
| 7 | **The uniqueness gate fails**: 186 registry rasters flagged at >70% forward 3-px overlap (137 sparse, 49 dense). My first hypothesis, that all flags were dense surfaces, was wrong. Checked and corrected | Verdict set to "not cleared" |
| 8 | Old generator rewrote the index and README with the stop banner | Generator now refuses to run; the page is built from the decision record |
| 9 | Tests pinned the old negative page, the old validator policy, and the zeros-outside file as passing | Assertions updated to the new decision; the MAW file is now expected to fail format |

Verification after fixes: `pytest -q` → 43 passed. `validate_submission.py --format-only` on the new file → exit 0, `ok_to_submit: false`, registry gate blocked. The same command on the prior MAW file → exit 1 (zeros outside).

## Pass 3 · re-check against the request

| Request | Status |
|---|---|
| Executive summary for nine sites with highest-scoring file, pick, and table (file, estimate labelled as estimate, unique vs others) | **Done**, with the caveat that the named file is the only one identified per site and every score is user-reported. Estimates: "not estimable". |
| Generate a unique GeoTIFF; in-range; grid/CRS/transform match; no NaN in footprint; downloadable; clear "OK to submit?" | **Partly.** Generated, format-valid, downloadable. **Not unique** (gate fails). Answer: **No**. |
| Explain GEMSDOE32 (0.2778) with PhD-level reasoning, verified line by line | **Partly.** Pixel identity verified (xor 0). Mechanism is a hypothesis; hidden labels make causal claims impossible. |
| Beat the leaderboard high (0.4544) | **Not achieved and not shown.** No measured candidate exceeds 0.2778 or 0.4544. |
| 3–5 untried hypotheses; holdout check on the top one before a slot | **Hypotheses listed (4), ranked.** **Top one not holdout-checked:** budget spent. |
| Put the full prompt into the README as a standing start-up section | **Partly.** `docs/PROJECT_BRIEF.md` is a *condensed* brief, linked from the README start-up section. The verbatim prompt was not pasted. |
| Core values | Applied as framing: the file is withheld rather than spending a slot on an unmeasured duplicate-risk candidate. |
| Clean Pages site, submission path at the top; executive-summary subpage on how to submit | **Built** (`docs/index.html` = `docs/download-and-submit.html`). **Pages URL not verified.** |
| Data: run `download_competition_data.sh` then `prepare_data.py` | **Not possible**: competition data needs a DrivenData login. The owner-mirror fetch (`prepare_data.py --fetch`) was used instead. |
| Gates: lane, correlation ≤0.90, 3-px overlap ≤70%, leakage canary, HOLDOUT-DTI with CI, run card, budget, name/note ≤140 | **Applied**; the lane is stopped at the uniqueness gate. Name and note are under 140 characters. |
| Create a PR and merge to main; list remaining work and limitations | **In progress** (this turn). Remaining work and limitations are in the README. |
| Do not reuse holdout outputs as leaderboard predictions; do not submit the MAW file | **Respected.** |
| Flag irregularities; cite official sources with links; verify line by line | **Done**: irregularities in the decision record and the brief; sources linked. |

Open items: a verbatim copy of the user's prompt is not in the repo; the top hypothesis is not checked on the holdout; the Pages URL is unverified; the 1,456 other GeoTIFF blobs are not spatially scanned.
