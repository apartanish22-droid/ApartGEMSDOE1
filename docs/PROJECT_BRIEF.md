# Project brief · read before every session

**Condensed standing brief, written 2026-10-31 from the user's request.** This is a faithful summary of the requirements, not a verbatim copy of the chat prompt. Where a sentence is quoted, it is quoted exactly. Any wording the user adds later supersedes this file.

## 1. Goal

Win the DrivenData **GEMS Prize Challenge** (competition 306, "Geologic Enhanced Mapping System").

* Competition page: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
* Leaderboard: <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>
* Rules (PDF): <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
* Reference solution: <https://github.com/drivendataorg/gems-prize-reference-solution>

The deliverable is **one GeoTIFF** that a person can download with one click and submit. The site must make this obvious on arrival. The executive summary must say, in one table, which file to download, its estimated score, whether it is unique, and whether it is OK to submit.

## 2. Non-negotiable output rules

1. **Format.** Official text: *"Your submission contains a single layer with datatype of 32-bit float (`float32`) with values between 0 and 1"* and *"data outside the bounds is null or nan."* The repository's template-format writer (`write_template_submission`) reproduces the official sample's NaN mask exactly.
2. **Portal error.** The user reported *"Predicted values must be in range [0, 1]"*. The cause has not been established. Keep every in-footprint value finite and within [0,1], and never write NaN inside the footprint.
3. **Uniqueness.** The user requires a file that is not an exact copy of any previous submission from the listed GEMSDOE sites. Check exact copies by git blob hash across the whole owner inventory, and check spatial overlap against the submission outputs.
4. **Labels.** Every number is either `HOLDOUT-DTI` (evaluator version, number of withheld positives, 95% CI) or `ORGANIZER-CONFIRMED` (copied from a submission-page receipt). A projection is never written as a score.
5. **Named submission.** Each file has a unique name and a note of at most 140 characters.
6. **Weekly cap.** Three submissions per week. One final submission (rules §3.2, §3.4). Choosing a slot is a separate selector step.

## 3. Parallel-run protocol (summary)

* **Lane.** One method per session. If another lane's raster correlates above 0.90 (Spearman) or more than 70% of dots fall within 3 px of another raster's dots, log a duplicate and stop.
* **Reuse.** Use the shared feature stack, the shared holdout evaluator (`gems57.evaluate_holdout`) and the shared writers. Fix shared tools once, in the template, and report the fix. Do not keep private forks.
* **Holdout.** Hide whole fault segments with a buffer. Derive catalogue features only from visible faults. Mask visible faults pixel-exactly. Pooled DTI with α=0.2, β=0.8 and a 300 m triangular kernel.
* **Leakage canary.** Test each feature alone on the holdout. AUC above 0.90 means leakage until proven otherwise.
* **Run card.** Hypothesis, mechanism, a named non-fault process that could mimic it, holdout DTI and CI, registry overlap, raster SHA-256, validator output, submission name and note, verdict (promote or negative).
* **Budget.** At most 3 experiments or 2 hours. Negative results are deliverables.

## 4. Verification rules

* Work line by line and verify against official sources. Link every source for manual review.
* No manual input. Flag irregularities for review. No hallucinated values.
* Run three passes: implement and verify; review for bugs and assumptions; recheck against the request.

## 5. Known irregularities (keep current)

* The 0.2778, 0.2449–0.2708 and other site scores are **user-reported, unconfirmed**. No organizer receipt has been provided.
* The public leaderboard top read on 2026-10-30 was **0.4544** (direct fetch, not the scheduled feed). The prompt's 0.4413 and 0.3195 do not match that page.
* The "official" files in `data/official/` are **owner-mirror copies** from `buffedlizard55-lab/6GEMSDOE`, not organizer downloads. Login-gated data was not obtained.
* The repository's old all-finite writer uses zeros outside the footprint. The official rule says null or NaN. The template writer follows the rule.
* The new raster **fails the uniqueness gate** (186 registry rasters exceed 70% 3-px forward overlap; 137 sparse dot sets, 49 dense surfaces). Not cleared. See `evidence/submission_decision_2026-10-31.json`.
* The **holdout measured a different allocation** from the emitted file (per-cell 281,318 dots vs one full-footprint 30,562 dots), so the new file has no measured score.
* `prepare_data.py --fetch` rewrote `evidence/feature_cache.json`, dropping the "historical_only" warning and rewording a band-6 finding. The committed versions were restored; the rewrite is unreviewed.
* The holdout uses the USGS catalogue, but the scored test faults are **new faults** not in that catalogue (rules page). The holdout is a proxy. See `evidence/leakage_audit_2026-10-31.md` for the catalogue-proximity leakage found on 2026-10-31.

## 6. Session checklist

1. Read this brief, the latest run card (`evidence/submission_decision_2026-10-31.json`) and the leakage audit.
2. Confirm the lane and the remaining budget.
3. Restore the feature stack with `python scripts/prepare_data.py --fetch` (needs `gh` auth and about 0.5 GB of disk).
4. Run the tests: `pytest -q`.
5. Only then generate, validate, and check registry overlap.
6. Update the executive summary and run card before merging.

## 7. Future work (suggested, not yet done)

* A complete, hash-pinned registry of every submitted raster (not only `docs/downloads/`), with organizer-confirmed scores where available.
* An organizer-confirmed NaN-outside test: one upload decision, owned by the user.
* A leakage-free holdout design with a buffer that also removes visible context near each withheld segment, and a scored domain that excludes that buffer.
* Data sources not yet checked for coverage: USGS 3DEP DEM tiles, GDR INGENIOUS temperature probes, NASA ASTER GED emissivity. See `evidence/next_hypotheses.md`.
