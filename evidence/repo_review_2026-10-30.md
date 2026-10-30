# Repository review · 2026-10-30 (UTC)

**Status: NO FILE IS READY TO SUBMIT.** This review generated no new GeoTIFF, ran no model experiment, used zero weekly submission slots, and did not promote or upload anything. The earlier negative verdict stands and was independently reproduced.

Every number below is labelled with one of the project's evidence classes:

* **MEASURED-REPO** — recomputed from raster bytes in this session, with the commit or hash shown.
* **OFFICIAL-SOURCE** — read from an organiser or DOE page, with a link.
* **USER-CLAIM** — copied from the prompt; not confirmed by any organiser receipt.
* **NOT-MEASURED** — no evaluation was possible here.

No holdout-DTI score was produced, so no estimated leaderboard score is given for any file.

---

## 1. Executive summary

| Question | Answer | Evidence |
| --- | --- | --- |
| Which file should be downloaded for submission? | **None.** The only candidate in the repo, `apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif`, is marked *DO NOT SUBMIT*. | [run card](run_card.json), [literal witness audit](literal_witness_audit.json) |
| Estimated leaderboard score | **NOT-MEASURED.** No holdout-DTI could be computed (see §4). | §4 |
| Is it unique versus the nine focus sites? | **No.** Under the protocol's 3 px rule, the file overlaps the same registry lattice as the nine focus files. | §3 table |
| Does the top user-reported file (GEMSDOE32, 0.2778) pass the uniqueness gate? | **No.** 99.92% of its dots lie within 3 px of the 13GEMSDOE witness. | §3 |
| Is the 70% overlap cap satisfiable at the 37,654-dot budget? | **No.** Only 6,514 non-catalogue footprint cells lie outside the witness halo, so the cap is satisfiable only for budgets ≤ 21,713 dots. | §3 |
| Current leaderboard top score | **OFFICIAL-SOURCE:** 0.4544 (#1 xiaofanhu) at fetch time. The prompt's 0.4413 and 0.3195 conflict with it and are unverified. | §2, §5 |

**Recommendation.** Do not submit any file from this repo or the nine focus sites under the protocol. The next lane needs (a) the organiser's training features, which this sandbox cannot reach, and (b) an explicit decision about whether the 13GEMSDOE lattice counts as a registry for uniqueness. Without (a), no holdout score is possible. Without (b), the protocol is unsatisfiable at full budget (§3).

---

## 2. Official sources checked this session

| Claim | Source | Result |
| --- | --- | --- |
| Metric is a distance-weighted Tversky index, α=0.2, β=0.8, triangular kernel with 300 m (3 px) support | [Problem description, Performance metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | **Verified.** The formula matches `src/gems57/metric.py` (TP_w = Σ_g max_x p(x)k; FP_w = Σ_x p(x)[1−max_g k]; FN_w = |G|−TP_w). |
| Submission must be float32, one band, values in [0, 1], same CRS/shape/bounds; "data outside the bounds is null or nan" | [Problem description, Submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | **Verified text.** See irregularity **I-2** below: the repo's validator requires 0 outside the footprint, not NaN. |
| Known USGS/INGENIOUS fault pixels are masked from scoring | [DrivenData forum thread 11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) (chrisk-dd, staff, Sep 16) | **Verified.** The repo's catalogue-masking assumption is correct. |
| Reference solution uses Tversky α=0.2, β=0.8 and writes a float raster | [gems-prize-reference-solution, notebook](https://github.com/drivendataorg/gems-prize-reference-solution/blob/main/unet-mc-cv-reference-solution.ipynb) (commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b`, cloned from GitHub) | **Verified.** The reference treats `data/labels.tif` as "Known Faults". |
| Data download requires login | [Competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | **Verified this session.** The page redirects to a login form. Training features are therefore unavailable here. |
| Leaderboard | [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | **Verified snapshot.** #1 xiaofanhu 0.4544; #2 cfld__ 0.3916; #3 Batik Shirt Brothers 0.3911; #4 BrandenKMurray 0.3841; #5 op01 0.3642. Snapshot time is not shown on the page. |

---

## 3. Measured overlap (MEASURED-REPO)

All rasters were fetched from GitHub (git clone of each repository, then checkout of the commit cited in the README table). Only those pinned bytes were used. The witness is `buffedlizard55-lab/13GEMSDOE` at `92ee6f074323f161eed837b80ec3ee5b662e26f5`. Its SHA-256 `b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2` matches the stored value.

**Share of each file's dots within 3 px (Euclidean) of the 13GEMSDOE witness:**

| File (pinned commit in README) | Dots | Within 3 px of witness | SHA-256 (first 16) |
| --- | ---: | ---: | --- |
| GEMSDOE24 `gems24-h25-1-dotted-h19-5-d1-5-…-nan.tif` | 60,069 | 99.92% | `68d0e2e4fcc594f9` |
| GEMSDOE25 `gems25-dotted-h19-5-d2-8-…-nan.tif` | 44,090 | 99.92% | `91eae1ca42ec845e` |
| GEMSDOE27 `gems27-topo-gap-closure-…-nan.tif` | 61,328 | 99.92% | `33003374335d84bf` |
| GEMSDOE28 `gems28-h36-1-rung30-blind-r1-…-nan.tif` | 37,660 | 99.91% | `5556aa1438fd6737` |
| GEMSDOE30 `gemsdoe30-d28-poisson300m-offcat-44090-…tif` | 44,090 | 99.92% | `8cf893ead5667df2` |
| GEMSDOE31 `gemsdoe31-h27-4-solo-d28-…-nan.tif` | 40,199 | 99.92% | `07b6db440535404b` |
| **GEMSDOE32 `gemsdoe32-h33-h33-2-b2-…-zeros.tif`** (user-reported top, 0.2778) | 37,654 | **99.92%** | `c55bafc470054e82` |
| GEMSDOE33 `GEMSDOE33-h33d-analog-tip-stepover-…tif` | 41,865 | 99.91% | `87f857d505e23247` |
| GEMSDOE36 `gemsdoe36-anderson-geothermal-pinn-…-zeros.tif` | 38,854 | 99.92% | `e15891020b9c5705` |
| MAW candidate in this repo (`docs/downloads/apartgems1-maw-gsi-e3-…-zeros.tif`) | 37,654 | 99.68% | `09fa04bd481d896a` |

Machine-readable output: [`focus_overlap_review_2026-10-30.json`](focus_overlap_review_2026-10-30.json) (it records file names, dot counts and overlaps, not hashes). The script is [`scripts/audit_focus_overlap.py`](../scripts/audit_focus_overlap.py).

Full SHA-256 values of the nine focus rasters, in README order:

* GEMSDOE24 `68d0e2e4fcc594f9a23f56c44b885fee733d026d39be55e18ad2a07289525310`
* GEMSDOE25 `91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8`
* GEMSDOE27 `33003374335d84bf885f2d8f5e9dd4c57044c8ec58fa6a0d7fa581e8bc41c11d`
* GEMSDOE28 `5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641`
* GEMSDOE30 `8cf893ead5667df21d3288a9968c35fd5385c425b029d82ee71d311715b129fd`
* GEMSDOE31 `07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40`
* GEMSDOE32 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`
* GEMSDOE33 `87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757`
* GEMSDOE36 `e15891020b9c57056ac7fa874a5e506fbd6ed9314a4ea8e73af0753887a3708a`

**Directed overlap between focus files (share of row's dots within 3 px of column's dots).** Row GEMSDOE32 → column GEMSDOE25 = **1.0000**, while GEMSDOE25 → GEMSDOE32 = 0.8817. Every GEMSDOE32 dot therefore lies within 3 px of a GEMSDOE25 dot. This is not a strict subset, but it is the same family. Across all 72 directed pairs among the nine focus files, the values range from 0.8672 (GEMSDOE27 → GEMSDOE32) to 1.0000. The README's "duplicate family" wording is supported.

**Share of each focus file's dots within 3 px of the MAW candidate:** 46.7–50.9%. The README's per-site "prior candidate %" column reproduces exactly for all nine sites, for example 48.56% for GEMSDOE25 and 46.71% for GEMSDOE32.

**Feasibility of the protocol's 70% cap.** Footprint = 5,167,373 cells (finite cells of `sample_submission.tif`). Cells more than 3 px from the witness: 6,649, of which 6,514 are outside the catalogue. For a budget N, at least 0.3N dots must lie in those 6,514 cells, so N ≤ 21,713. The README's figure is reproduced exactly.

**What this means for "why 0.2778".** Verified facts only:
* GEMSDOE32 has the same 37,654 positive dots as the MAW candidate.
* GEMSDOE32 sits in the GEMSDOE25 family with 14.6% fewer dots (37,654 vs 44,090), and each of its dots is within 3 px of a GEMSDOE25 dot. GEMSDOE25 and GEMSDOE30 both score 0.2600 in user claims, and their positive sets are identical inside the footprint.
* Its gain over GEMSDOE25 (0.2600 → 0.2778) is consistent with removing dots near the catalogue. This is a hypothesis, not a proof: under the DTI with α=0.2, dropping dots that add more FP_w mass than TP_w gain raises the score. The hidden test labels are not available here, so this cannot be tested.
* No organiser receipt confirms 0.2778. Every per-site score is a USER-CLAIM.

---

## 4. Holdout score

**NOT-MEASURED.** Training needs `training_features.tif` (19 layers, EPSG:32611, 100 m). It is not in the repo, the DrivenData data page requires login, and the Dropbox links in the prompt are on hosts this sandbox cannot reach. Without features, neither the feature canary, the holdout, nor a model can run. No estimated leaderboard score is given.

---

## 5. Irregularities for manual review

| ID | Severity | Finding | Evidence | Action proposed |
| --- | --- | --- | --- | --- |
| **I-1** | High | **Leaderboard figures conflict.** The prompt cites 0.4413 and 0.3195 as the top score. The fetched leaderboard shows #1 at 0.4544 and #2 at 0.3916, with no snapshot time. | [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Confirm the current top value from a logged-in view before setting any target. |
| **I-2** | High | **Outside-footprint convention.** The organiser says outside-bounds data "is null or nan", and the sample submission uses NaN outside. The repo's validator requires 0 outside and the MAW file uses 0. Among the focus files, 30, 32, 33 and 36 use 0 outside and 24, 25, 27, 28 and 31 use NaN. The user reports scores for both groups, which suggests the portal accepts zeros, but that is unconfirmed. The user's earlier error "Predicted values must be in range [0, 1]" is unexplained. | Problem page, format section; `src/gems57/validate.py`; per-file NaN counts | Confirm the accepted convention from the submission-page validator before any upload. Do not change the validator on inference alone. |
| **I-3** | High | **Uniqueness protocol is unsatisfiable at full budget.** Against the 13GEMSDOE witness, the 70% cap caps the budget at 21,713 dots, while 37,654-dot files are standard. Every focus file is ≥ 99.9% covered. | §3 | Decide whether a 5-px lattice from a third-party repo counts as "registry". If it does, the protocol needs a smaller budget or an explicit exemption. Do not silently change the threshold. |
| **I-4** | Medium | **Labels equal catalogue.** `data/official/labels.tif` is byte-identical to `existing_faults.tif` (SHA-256 `7ba308cc…`). The organiser's notebook calls `labels.tif` "Known Faults", so this is consistent with the public catalogue. It means the local "labels" are not hidden test labels. | §2; `data/manifest.json` | Keep the label as catalogue only. Holdout results cannot be used as leaderboard predictions. |
| **I-5** | Medium | **Stale test-file references.** `metric.py` cited `tests/test_metric.py`, and `gates.py` cited `tests/test_gates.py`. Neither exists. The gates.py regression for IR-52-027 is not in the repo. | `ls tests/` | Fixed in this session for the metric docstring and the gates comment. The missing gates regression remains open. |
| **I-6** | Low | **Test count.** `review_passes.md` says 23 tests passed. This session's run gives **24 passed** (`pytest -q` in `.venv`). | §6 | Historical record left unchanged; this review gives the current count. |
| **I-7** | Low | **Mirror provenance.** `data/official/*.tif` and `data/bridge/*.tif` are GitHub mirror bytes, not organiser-authenticated downloads. The manifest says so. | `data/manifest.json` | None. Already disclosed. |
| **I-8** | Low | **GEMSDOE25 vs GEMSDOE30.** Both have identical positive sets inside the footprint. GEMSDOE25 uses NaN outside and GEMSDOE30 uses 0. The README's "footprint values equal" wording is correct only inside the footprint. | §3 | Clarified here. |
| **I-9** | Info | **Third-party claims.** The 13GEMSDOE witness, the nine focus rasters, and the user-reported scores are from other participants' repositories. They are not official sources. | README | Treat them as unverified inputs. |

---

## 6. Changes made in this session

1. `src/gems57/metric.py`: corrected the stale test reference to `tests/test_apartgems_gates.py`, which holds the brute-force DTI test. Docstring only.
2. `src/gems57/gates.py`: replaced the claim of a regression test in the non-existent `tests/test_gates.py` with an open-item note. Comment only.
3. `scripts/audit_focus_overlap.py`: new, read-only audit script (no submission, no model). Reproduces every figure in §3.
4. `evidence/focus_overlap_review_2026-10-30.json`: its output.
5. `evidence/repo_review_2026-10-30.md`: this document.
6. `README.md`: link to this review.

Test suite after the changes: **24 passed**. `scripts/run_apartgems_pipeline.py` still exits 2 by design. `scripts/validate_submission.py --format-only` passes on the MAW file. The full validator returns `ok_to_submit=false`.

---

## 7. Limitations and what is needed

* **Training features** (`training_features.tif`) from the DrivenData data page, which needs a login. Without them there is no holdout and no model.
* **Organiser submission-page receipt** for any score; none exists in the repo.
* **Decision on the 13GEMSDOE lattice** as a registry (I-3).
* **Accepted outside-footprint convention** (I-2).
* **Hosts:** this sandbox reaches only GitHub, PyPI and npm. DrivenData and Dropbox are not on the list, so the official data cannot be fetched from here.

## 8. Suggested next steps

1. Get the organiser's features through a logged-in account, then rebuild the feature stack from official bytes and record new SHA-256 values.
2. Settle I-2 from the submission-page validator. Do not upload to test it without a slot decision.
3. Re-run the holdout with `gems57-pooled-hide-v3` on the rebuilt stack, with the three-experiment budget and the leakage canary. Only then consider a novel lane.
4. Restore the missing gates regression test for IR-52-027 (I-5).

---

```json
{
  "protocol": "GEMS Parallel-Run Protocol; repo review, no experiment",
  "date_utc": "2026-10-30",
  "hypothesis": "Not tested. Review question: is any existing file uniquely submittable and what is the best known file?",
  "mechanism": "Not applicable; no new model.",
  "named_non_fault_mimic_process": "Alluvial-fan channels, erosional scarps and lithologic contacts (unchanged from prior runs).",
  "holdout_dti": {"label": "NOT-MEASURED", "evaluator_version": "gems57-pooled-hide-v3", "withheld_positive_pixels": null, "dti": null, "ci95": null, "reason": "training_features.tif unavailable (DrivenData login; Dropbox not allowlisted)"},
  "correlation_overlap_vs_registry": {"witness": "buffedlizard55-lab/13GEMSDOE@92ee6f074323f161eed837b80ec3ee5b662e26f5 sha256 b4570b40…", "maw_candidate_within_3px": 0.9967865299835342, "focus_nine_within_3px_min": 0.9991, "focus_nine_within_3px_max": 0.9992, "threshold": 0.70, "duplicate": true},
  "raster_sha256": {"apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif": "09fa04bd481d896a4dcbb808e4ef8136f8e6d0e0d88cebe9afd957db2779d62f"},
  "validator_output": {"format_only": "pass", "full_preflight_ok_to_submit": false, "nan_in_footprint": 0, "range_0_1": true, "crs": "EPSG:32611", "shape": [3730, 3292], "transform_matches_sample": true},
  "submission_name": "none",
  "submission_note": "No submission generated; see evidence/repo_review_2026-10-30.md",
  "experiments_started_this_session": 0,
  "submission_slots_used_this_session": 0,
  "verdict": "negative",
  "reason": "No holdout score possible without training features; all candidates duplicate the 13GEMSDOE lattice under the protocol's 3 px rule; 70% cap infeasible above 21,713 dots."
}
```
