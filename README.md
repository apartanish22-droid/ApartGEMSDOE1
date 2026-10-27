# ApartGEMSDOE1 — GEMS submission research workspace

## Project charter (read before each experiment)

Objective: maximize the probability of a scientifically defensible, valid submission to the DOE GEMS geothermal-favorability competition. Own the end-to-end result: keep sources auditable, use spatially independent validation, test leakage, report uncertainty, and never represent a projection as an organizer-confirmed score. Do not spend a competition submission slot unless a candidate beats the current spatial holdout best and passes format and duplication gates. A unique filename or hash does not make a scientifically duplicate raster unique.

### Required experiment controls

1. Stay within the declared geological hypothesis/lane. Compare candidate scores against registry rasters before placement and on final dots; flag rank correlation >0.90 or >70% of dots within 3 pixels of any registry dot set as duplicate/drift.
2. Reuse the shared cached feature stack, segment-level buffered hide-and-recover holdout evaluator, and shared submission writer. Derive catalogue-based features only from visible faults; mask visible faults pixel-exactly. Score pooled DTI with alpha 0.2, beta 0.8, and 300 m triangular kernel. Leakage-canary each feature alone; AUC >0.90 requires investigation.
3. Label all reported numeric scores as either **HOLDOUT-DTI** (evaluator version, withheld-positive count, 95% CI) or **ORGANIZER-CONFIRMED** (receipt evidence). No score is inferred from public-site descriptions or projection.
4. Maximum per request: three experiments or two hours. Negative results are valid deliverables. Slot selection is separate and must respect the organizer's weekly cap.
5. Any downloadable GeoTIFF must be single-band, match the official template's CRS, shape and affine transform, have finite predictions in [0,1] inside the footprint, and state whether it passed all gates. Do not fabricate a file when the official template, data, or validation evidence is unavailable.

### Current repository status

At initial review the checkout had only this README; this work adds project notes and a format/range validator, but no competition rasters, cached feature stack, shared `evaluate_holdout.py`, shared `submission_writer.py`, registry rasters, or prior experiments. Thus this checkout cannot truthfully produce a template-matched TIF, run the prescribed holdout, estimate DTI, verify uniqueness against raster registries, or claim a promotable submission. See the [executive summary](docs/EXECUTIVE_SUMMARY.md), [submission workflow](docs/SUBMISSION.md), and [detailed repository review](docs/REVIEW_AND_PROTOCOL.md). `scripts/validate_submission.py` is a format/range gate, not a score estimator; tests cover its format gate only.

### Official references

- [Competition overview/rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition data page (login may be required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [About/resources](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDawn data record](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [NREL competition report PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [EPSG:32611](https://epsg.io/32611)
- [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

Review these links for current requirements before relying on prior notes; this repository has not authenticated to DrivenData and did not verify live leaderboard receipts in this checkout.
