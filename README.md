# ApartGEMSDOE1 — GEMS Prize research & submission workbench

## Project north star

Build an auditable, reproducible system for discovering previously unmapped faults that may improve geothermal and critical-mineral mapping in the DOE GEMS Prize challenge. Optimize for evidence of generalization, not leaderboard anecdotes. Own the outcome: record negative results, validate every exported raster, and never claim a score or uniqueness without the corresponding measurement.

The competition's stated task is to generate enhanced geologic fault datasets. The challenge description also states that the same submission is scored against a private expert-labeled test set and later an expanded label set; see the [official DrivenData challenge page](https://www.drivendata.org/competitions/306/competition-doe-gems/). The [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) describes airborne magnetic and radiometric data for geologic and geophysical mapping (DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)). These are source descriptions, not evidence that this checkout contains the competition data.

## Read this before every project session

1. **Inspect first.** Check the current branch and worktree, then inspect repository contents and existing tools. Reuse the shared template's cached feature stack, holdout evaluator, and submission writer when present; do not create a private fork of shared tools.
2. **No unsupported claims.** Distinguish organizer-confirmed leaderboard receipts from local holdout estimates and from scores merely reported by a user. A projection is never a score. Attach evaluator version, withheld-positive count, and 95% CI to every holdout DTI result.
3. **Hold out spatially.** Withhold whole fault segments plus a buffer; derive catalogue-based features only from visible faults; mask visible faults pixel-exactly; evaluate pooled DTI with alpha 0.2, beta 0.8, and a 300 m triangular kernel. Test every feature alone first; AUC > 0.90 is a leakage alarm until explained.
4. **Stay in the assigned experimental lane.** Before placement and on final dots, compare rank-correlation against each registry raster and the fraction of dots within 3 pixels. Correlation > 0.90 or overlap > 70% means duplicate/drift: log it and stop. Do not spend a weekly submission slot; a separate selector controls promotions under the competition's current cap.
5. **No submission without gates.** Validate single-band GeoTIFF, CRS, dimensions and affine transform against the official sample-submission raster; require finite predictions within [0, 1] throughout the valid footprint. Record the file SHA-256. Do not publish a download link until this passes and uniqueness checks pass. A valid file is not a high-scoring file, and neither is an organizer-confirmed result.
6. **Bound experiments.** Stop after 3 experiments or 2 hours for a run. End each run with the JSON run card specified in `docs/REVIEW_AND_PROTOCOL.md`; negative results are deliverables.
7. **Own the outcome.** In the spirit of the Arena values supplied in the project brief, maximize the probability of a sound result, report blockers plainly, and carry findings forward.

## Current checkout status

This repository currently has no model, data, cached feature stack, shared evaluator/writer, website, or existing submission raster. The only tests now cover the standalone validator scaffold. Consequently it is **not currently possible** to reproduce any listed experiment, estimate a defensible holdout DTI, compare a candidate to registry rasters, or produce a submission GeoTIFF matching the competition grid. Do not submit a synthetic or guessed-grid raster. The evaluator and submit-generation tasks are blocked until the authorized competition assets and shared template are available locally.

A standalone validator scaffold is provided at [`scripts/validate_submission.py`](scripts/validate_submission.py). It does not generate predictions or certify score/uniqueness. See [`docs/REVIEW_AND_PROTOCOL.md`](docs/REVIEW_AND_PROTOCOL.md) for the repository audit, supplied-score review, candidate hypotheses, sources, and blockers.

## Getting started once authorized data and shared tools are placed

1. Place the official competition inputs and the shared template assets in the documented paths; record their source, version, and checksums. Do not commit private competition data or large generated rasters.
2. Install `requirements.txt` and first run the template's data-integrity checks.
3. Use the shared holdout evaluator and writer. Establish the current holdout best before changing features. Run the leakage canary and duplicate checks before considering any output.
4. Validate an output against the official `sample_submission.tif`:
   ```bash
   python scripts/validate_submission.py candidate.tif data/sample_submission.tif
   ```
5. Only the separate selector, with current weekly-cap and organizer rules checked, may promote a passing candidate to a real competition slot. The validator does not pick or submit it.

## Submission status

**No downloadable submission is currently available.** The repository has neither raster inputs nor an official sample grid. The “download and submit” gate must remain closed until a candidate is generated from authorized data, passes holdout and uniqueness criteria, and passes the GeoTIFF validator. See the report for detailed blockers and next steps.
