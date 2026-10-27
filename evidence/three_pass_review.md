# Three-pass repository review — 2026-10-27

## Pass 1 — repository and evidence inventory

- Reconciled the active branch with the main-branch additions rather than overwriting their source snapshots and site inventory. The repository contains research/site scaffolding, not an executable competition pipeline.
- Kept the root README as the persistent charter and reconciled the landing page, nine-site summary, submission guide, and current run card to a fail-closed status.
- Distinguished user-reported historical results, the official public-leaderboard snapshot, potential holdout measurements, and organizer receipts. No project score or receipt is established.
- Retained one synthetic demo TIFF for inspection only. Its artificial inputs, unverified (0,0) affine origin, and lack of official-template comparison are prominently disclosed.

## Pass 2 — implementation and edge-case audit

- Replaced the conflicted GeoTIFF validator with an official-template-required validator. It checks one float32 band, exact CRS/shape/affine, finite [0,1] values inside the template footprint, null/masked/NaN values outside, and SHA-256. Synthetic tests cover valid output, range/nonfinite failures, outside mask failures, grid mismatches, dtype, and band count.
- The incoming evaluator was found not to implement whole-segment buffered holdout, visible-only catalogue recomputation, correct masking, or the specified pooled metric. Disabled it instead of emitting a misleading score. The noncanonical writer and synthetic generator also fail closed.
- Removed unsafe/unverified mirror-download behavior and made the download-named script report the login-gated-data blocker and inventory local files only.
- Fixed readiness logic so file presence cannot be presented as experiment readiness or slot authorization. The preflight now reports the missing official sample/labels, canonical runtime, registry, and lane; `data/prepare_data.json` likewise reports validation not ready.
- Updated site build handling so CI checks static pages without regenerating or overwriting the status landing page.

## Pass 3 — requirements and public-claim audit

- Confirmed all nine requested sites are summarized; reported values are labeled user-reported/unverified, new estimates are not estimable, and raster uniqueness is unknown absent exact raster comparisons.
- GEMSDOE32's potential sparse/catalogue-pruning mechanism is described only as a hypothesis. Its score is not independently tied to an organizer receipt or reproduced from its absent raster.
- Ranked four untested hypotheses with layers/signatures, missing-catalogue rationale, confounders, repository-novelty caveats, qualitative expected DTI benefit, costs, and official-source availability checks. No numeric gain is projected.
- Public pages label the synthetic artifact `DO NOT SUBMIT`; root/docs landing pages and run card consistently distinguish inspection from submission. No weekly slot was selected or spent.
- Checked official USGS GeoDAWN and 3DEP and GDR 1391 source descriptions/access on 2026-10-27. Exact footprints, channels, source raster provenance, and competition-rule compatibility still need investigation. Reviewed the official DrivenData problem page and public leaderboard; the retrieved leaderboard snapshot displayed 0.4544 at rank one, which is not a project score/receipt.

## Validation performed

- `./.venv/bin/python -m unittest discover -s tests -v`: **17 tests passed**, using synthetic raster fixtures for software behavior only.
- `./.venv/bin/python scripts/build_site.py`: passed static-site safety sanity checks; no files regenerated.
- `./.venv/bin/python scripts/readiness.py`: expected blocked exit status 2; official files, shared runtime, registry, and lane are absent.
- `bash -n scripts/download_competition_data.sh`, Python bytecode compilation, JSON parsing, and `git diff --check` passed.
- Independently inspected the saved demo TIFF's local metadata/value array. It is one-band float32 EPSG:32611, 3730×3292, 100 m pixels, affine origin (0,0), finite [0,1], with 37,654 positive cells. The origin was not compared with an official sample. SHA-256: `397648e33ad640acd32c2fedcdcdefaf7815fa21bd276264bd2bcdff61af6e9a`. These checks do not validate a GEMS prediction.

## Remaining blockers

The assigned lane; authenticated official data/template and provenance; canonical runtime and cache; complete raster registry; a leakage-safe, matched segment-buffered holdout and confidence interval; and, for any actual score, an organizer receipt. No competition prediction, HOLDOUT-DTI, submission-ready file, upload, or live leaderboard feed is delivered. A separate selector must decide any weekly slot only after all scientific and format gates pass.
