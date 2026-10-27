# Three-pass repository review — 2026-10-27

## Pass 1 — implement and inventory

- Inspected the actual checkout and remote history. The branch started from a one-file README snapshot; `main` advanced concurrently through other PRs adding an executive site, nine site summaries, source snapshots, readiness checks, and sibling-repository evidence. Merged that work into this branch instead of overwriting it.
- Consolidated the standing brief into the root README; preserved the static executive page and per-site summaries; documented four preregistered hypotheses as proposals only; recorded an explicitly negative run card because no lane is assigned and no competition candidate exists.
- Reviewed the official DrivenData problem description on 2026-10-27 for target, metric, kernel, and output format. Reviewed the pinned DrivenData reference-solution README. Did not claim to have checked the login-gated data page, live leaderboard, outside sources, receipts, or authenticity of owner-supplied raster mirrors.

## Pass 2 — bug, edge-case, and evidence audit

- Found that the existing GeoTIFF validator checked band count, grid, and [0,1] values, but did not enforce the official float32 requirement or null/NaN outside the sample footprint. Extended it and added handling for templates whose outside cells are NaN without GDAL nodata metadata.
- Added synthetic tests for valid files, wrong CRS/shape/transform/dtype, multiple bands, NaN and out-of-range values inside the footprint, finite values outside, valid outside nodata/NaN, and malformed multi-band templates.
- Found the GitHub Actions workflow ran those raster tests without installing their declared NumPy/rasterio dependencies; added dependency installation.
- Flagged evidence gaps: the checked-in sibling wrappers import a `src/gems32` package that is not present; feature receipts describe but do not include cache bytes; the mirrored competition data is owner-supplied and not organizer-authenticated; the complete novelty registry is not in this checkout; and sibling README links to candidate binaries that are absent here. None of the sibling numerical claims or files is labeled as this project's verified submission.
- Kept the site fail-closed. No TIF is called downloadable for submission; historical site values remain user-reported unless backed by a receipt.

## Pass 3 — original-requirement recheck

- Confirmed the nine requested sites each have a linked summary and that the landing page shows historical result evidence, no new-file estimate, uniqueness unknown, and **DO NOT SUBMIT** status.
- Confirmed the prompt's 0.3195 and 0.4413 global-maximum assertions conflict and were not silently reconciled; GEMSDOE32's 0.2778 is only the largest user-reported number among the supplied nine.
- Confirmed four scientific hypotheses identify layers, signatures, missing-catalogue rationale, confounders, relative cost, and why novelty remains provisional. Because the required lane paragraph is absent, no hypothesis was tested or treated as assigned.
- Confirmed the structured run card records null holdout/registry/raster/real-artifact fields and a negative verdict. No competition slot or upload was used.
- Validation: `python -m unittest discover -s tests -v` passes all 12 synthetic raster tests plus readiness and site tests; the site suite verifies all nine downloaded HTML snapshot SHA-256 values; `python scripts/build_site.py` is deterministic; both run-card JSON files parse. The imported source snapshots are preserved byte-for-byte and contain original trailing whitespace, so a blanket `git diff --check` flags those specific snapshot lines; edited project documents/code have no whitespace errors. These tests validate code/docs only, not any real GEMS TIF or score.

## Remaining blockers

Official competition data/template access and provenance; exact lane; full canonical runtime/dependencies; validated registry rasters; a leakage-safe matched incumbent and holdout; and a receipt if a real score claim is made. A high-scoring, unique, submit-ready TIF and automatic live leaderboard feed are **not delivered** by this review. The next step is evidence acquisition and restoration of the canonical template, not manufacturing a projection.
