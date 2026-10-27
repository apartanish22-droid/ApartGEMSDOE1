# ApartGEMSDOE1 — GEMS fault-prediction research

## Project charter (read before each experiment)

**Aim:** maximize the probability of a scientifically defensible, valid, competitive DOE GEMS submission. Own the outcome end to end: preserve source lineage, use spatially independent validation, test leakage, report uncertainty, and never present a projection as an organizer-confirmed score.

A submission slot is a separate selector decision. Do not consume one unless the exact candidate beats the reproducible current holdout best, clears the novelty lane, and passes the artifact validator. A new filename or hash is not evidence of scientific uniqueness.

### Required protocol

1. Work only in the explicitly assigned method lane. Compare the prediction surface before dot placement and final dots against registry rasters. Flag as duplicate/drift if rank correlation is >0.90 or >70% of candidate dots are within 3 pixels of any registry dot set.
2. Reuse the template's cached feature stack and shared holdout evaluator/writer. Withhold whole fault segments plus a buffer; derive catalogue-based features only from visible faults; mask visible faults pixel-exactly. Evaluate pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). Test each feature alone; AUC >0.90 is a leakage alarm until explained.
3. Label results as **HOLDOUT-DTI** with evaluator version, withheld-positive count, and 95% CI, or **ORGANIZER-CONFIRMED** copied from a submission-page receipt. Unverified user-provided leaderboard values are not either kind of project score. Never label a projection as a score.
4. Stop after at most 3 experiments or 2 hours. Negative results are valid deliverables. Do not select or spend a weekly slot.
5. Any candidate marked **OK TO SUBMIT** must be a single-band GeoTIFF matching the official template's CRS, shape, and transform, with finite values in [0,1] throughout its valid footprint. Reopen and validate the written file. Do not create a dummy file when data/template/evidence is missing.

## Current readiness

**DO NOT DOWNLOAD OR SUBMIT A CANDIDATE FROM THIS CHECKOUT.** The repository now contains documentation and `scripts/validate_submission.py`, but it has no competition rasters, cached feature stack, segment holdout evaluator, submission writer, registry rasters, actual candidate TIFF, or experiment results. The format validator is not a score estimator and cannot establish scientific uniqueness. No holdout estimate or organizer-confirmed result was produced here.

The exact method paragraph defining this parallel run's lane is not present in the supplied project material. Until it is recovered, candidate proposals must remain planning-only. See [the executive summary](docs/EXECUTIVE_SUMMARY.md), [submission workflow](docs/SUBMISSION.md), and [negative run card](docs/run_card.json).

## Official references for review

- [Competition overview/rules](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), and [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login may be required).
- [DrivenData GEMS reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
- [USGS GeoDawn airborne magnetic and radiometric data record](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/).
- [NLR report PDF supplied in the project brief](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
- [EPSG:32611](https://epsg.io/32611) (a reference only; use the official sample raster's CRS rather than assuming this CRS).
- [Competition leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

The official [DrivenData problem description and metric page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) was fetched and reviewed on 2026-10-27 for its stated fault target, DTI parameters/kernel, and GeoTIFF format requirements. Other linked pages, the live leaderboard, the login-gated data page, and organizer receipts have not been independently verified in this work.

## Repository contents and next steps

- `docs/EXECUTIVE_SUMMARY.md` — requested-site comparison, status, and candidate-hypothesis shortlist.
- `docs/SUBMISSION.md` — manual competition submission steps and validator scope.
- `docs/run_card.json` — structured negative result; no experiment was run.
- `scripts/validate_submission.py` — format/range validator requiring `rasterio` and `numpy`; it requires the official template and candidate raster.
- `tests/test_validate_submission.py` — synthetic regression cases for valid output and key grid, dtype, footprint, NaN, and range failures.

Before modeling, place authorized competition data and the shared template assets in the documented ignored data area; recover the exact lane paragraph and shared evaluator/writer; obtain registry rasters; verify sources and hashes. Then test a single in-lane hypothesis with feature-alone leakage canaries and the specified spatial hide-and-recover holdout. The one checked-in validator must be tested on real and synthetic rasters before labeling any artifact submit-ready. Keep large/private data out of Git and send a passed candidate to the separate weekly-slot selector only.

**Evidence boundary:** The user supplied historic entry names/scores, but this checkout does not contain their receipts or rasters. See the executive summary for clearly labeled transcription and irregularities. Do not infer exact/near-duplicate status from names or scores.
