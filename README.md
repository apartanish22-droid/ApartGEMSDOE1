# ApartGEMSDOE1 — DOE GEMS fault-discovery research

> **Submission decision: NOT APPROVED. There is no submission GeoTIFF in this repository. Do not download or submit any file from this repository or the linked research archives as a competition entry.**
>
> This is a fail-closed decision, not a claim that no model could work. The checkout has no competition rasters, cached feature stack, holdout evaluator, shared submission writer, registry rasters, or generated candidate. The designated single-method lane is also absent from the request. A plausible score or a format-valid TIFF must never be substituted for those missing gates.

## Read this first at the start of every project session

Read this entire README before planning, researching, editing, training, or generating an artifact. `AGENTS.md` repeats this requirement for coding agents. Keep this brief as the durable project charter; duplicate and repeated instructions from the original prompt are consolidated here without treating unverified leaderboard claims as facts.

## Standing project brief

### Objective

Build an auditable, current, low-friction workflow to identify previously unmapped faults relevant to geothermal systems in the DOE GEMS prize area; evaluate methods honestly; and, only after every required gate passes, make one uniquely named single-band GeoTIFF available for download. The executive summary must appear immediately on the project site and state plainly whether a file is safe to download and submit. The project should help maximize the probability of winning, not maximize the number of experiments or submissions.

Focus the historical comparison on **GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36**. The H33/B2 file from GEMSDOE32 is an audit subject, not a file to copy or resubmit. Historical scores supplied in prompts or owner-maintained sites are not organizer-confirmed without a submission-page receipt bound to the exact raster bytes.

### Non-negotiable parallel-run and validation protocol

1. **Lane:** use only the single method paragraph explicitly assigned to the current session. If the lane paragraph is missing, stop before experiment or TIFF generation; do not infer a lane from a prior session. Compare the candidate surface against every registry surface before placement and compare final dots after placement. If absolute rank-correlation exceeds `0.90`, or more than `70%` of candidate dots lie within `3 px` of one registry raster's dots, record a duplicate and stop.
2. **Reuse shared tools; do not rebuild or privately fork them.** Use the designated template's cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. If a shared tool is wrong, fix it in the shared template and report the fix. Catalogue-derived features and placement must be recomputed inside each fold using only visible faults. Hide whole fault segments with a buffer, mask visible faults pixel-exactly, and score pooled distance-weighted Tversky (alpha `0.2`, beta `0.8`, triangular kernel radius `300 m`).
3. **Leakage canary:** score every feature alone on the same spatial holdout before trusting a combination. AUC above `0.90` is leakage until proven otherwise.
4. **Evidence labels:** every claimed performance number must be either:
   - **HOLDOUT-DTI**, with evaluator version, withheld-positive count, and 95% CI; or
   - **ORGANIZER-CONFIRMED**, copied from a submission-page receipt that identifies the submission.

   A projection is never a score. A user/owner report, historical README, TIFF hash, model estimate, or public leaderboard snapshot is not an organizer receipt. If provenance is absent, say so and do not use the number to promote a file.
5. **Budget and slot control:** stop after at most `3` experiments or `2` hours. A candidate must beat the current holdout best before a separate selector considers a real weekly slot. Do not choose or spend a slot in the experiment stage. Negative results are valid deliverables.
6. **Run card:** end each experiment report with one JSON card containing hypothesis, mechanism, named non-fault mimic, HOLDOUT-DTI + CI, correlation/overlap vs registry, raster SHA-256, validator output (no NaN inside footprint, values in `[0,1]`, CRS/shape/transform match), submission name, note of at most `140` characters, and verdict `promote` or `negative`.

### Candidate selection and research

Before implementing an experiment, rank `3–5` geological hypotheses not already demonstrated as completed. Each must name exact input layer(s), the physical transform/signature, why it could find an off-catalogue fault rather than a mapped fault, what prior method it differs from, a plausible non-fault mimic, expected improvement (qualitative unless measured), and implementation/data cost. If new external data are needed, name a specific free official source and verify availability before calling that candidate viable. Validate the highest-ranked candidate on the spatially blocked holdout before any submission slot is considered.

### Submission format and user experience

- Competition upload is expected to be a single-band GeoTIFF, or a ZIP containing one GeoTIFF, in the exact submission grid (CRS, dimensions, and affine transform) and with predictions in `[0,1]`.
- Validate the saved bytes automatically, including finiteness/range, no NaN inside the footprint, CRS/shape/transform, band count, and SHA-256. Keep the generated filename and short note unique and reproducible; the note must be at most `140` characters.
- The site must show a prominent red/green decision, one-click download only after approval, an executive summary table (file, estimated score, uniqueness), and a subpage with exact portal steps. No human inspection may be a required validation gate. No upload or credentials are automated without explicit, authorized integration.
- The reported portal error “Predicted values must be in range [0, 1]” is a release blocker until a saved-byte validator catches it.

### Data and evidence

The task refers to DriveData data including `training_features.tif`, `labels.tif`, `sample_submission.tif`, and `1m_DEM_links.csv`. This checkout contains none of these files and no cached feature stack. The user reports that the competition data page requires sign-in and that this environment has no DriveData authentication. Do not claim to have downloaded or validated those files. Use free public official external sources only when relevant, and record whether the exact source was actually reachable and coverage checked.

## Repository review and current evidence (2026-10-27)

This checkout started with one tracked file (`README.md`) and no code, tests, site, competition inputs, cached features, holdout tools, submission writer, or generated TIF. The official [DrivenData reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution) was inspected on GitHub: its README instructs users to place competition feature/label GeoTIFFs in `data/`; its notebook describes a U-Net reference approach using multi-channel geospatial features and patch-based training. That reference is a baseline, not evidence that the requested segment-buffer holdout is already implemented here.

For read-only historical auditing, nine hash-pinned allfinite TIF variants corresponding to the user's named entries were retrieved from the `GEMSDOE32` owner registry and checked against its manifest. Where the prompt named a `-nan` file, its positive-pixel mask was also compared with the allfinite companion; the `-nan` versions contain NaNs outside the footprint. The TIF bytes were used only in `/tmp` for analysis and were **not** copied into this repository. The audit is recorded in [`docs/data/focus-site-audit.json`](docs/data/focus-site-audit.json). It verifies that the allfinite companions share the same stored grid and are finite binary `[0,1]` rasters, and it compares final dot masks. The NaNs in the `-nan` variants may explain a range-validator rejection, but the exact cause of the user's error cannot be established without the exact failed file/hash. This audit does **not** verify the official sample grid, recover pre-placement score surfaces, authenticate any leaderboard score, or create a candidate.

The final-dot uniqueness audit finds that **all nine selected historical masks fail the requested uniqueness gate** against at least one other selected raster. GEMSDOE25 and GEMSDOE30 have exactly identical positive-pixel masks (different TIFF byte hashes); the GEMSDOE32 mask is a strict subset of the GEMSDOE25 and GEMSDOE31 masks and is contained in the GEMSDOE36 mask, which has `1,200` additional positive pixels. This is a registry comparison, not a score. No pre-placement prediction surfaces were present for this audit.

A related, owner-maintained [GEMSDOE32 research repository](https://github.com/buffedlizard55-lab/GEMSDOE32) contains a more recent nine-site report and H48 run card. Its historical submission values are explicitly owner-reported, not linked to organizer receipts. Its H48 card records **HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, `22,232` withheld positives, 95% CI `[0.100168, 0.130524]`) = `0.115341`**; this is an offline holdout result, not a leaderboard score, was not rerun in this checkout, and the related repository's release decision is negative. Do not download/copy that artifact as a submission.

### Site and submission status

GitHub Pages was already enabled for this repository with the legacy main-branch root source when reviewed. The root `index.html` routes visitors to the executive summary at [`docs/index.html`](docs/index.html); the static site includes [`docs/submit.html`](docs/submit.html) and [`docs/research/hypotheses.html`](docs/research/hypotheses.html). This session's machine-readable negative run card is [`docs/data/run-card.json`](docs/data/run-card.json). A static snapshot is not an auto-refreshing score feed. The table reports no score estimate because this checkout cannot run the required holdout. Every historical file is marked audit-only; the download/submit decision is **NO**.

## Sources for review

- [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/) — user-provided official link; not fetched from this sandbox.
- [Problem description and scoring](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — user-provided official link; not fetched from this sandbox.
- [Competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — user-provided official link; data are absent here.
- [Competition rules / DOE-NLR PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — user-provided official link; not fetched here.
- [Official reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution) — inspected on GitHub.
- [USGS GeoDAWN airborne magnetic and radiometric surveys](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) — user-provided official link; not fetched here.
- [DOE GDR submission 1391](https://gdr.openei.org/submissions/1391) and [INGENIOUS project](https://gbcge.org/current-projects/ingenious/) — user-provided links; not fetched here.
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) and [USGS FDSN Event API](https://earthquake.usgs.gov/fdsnws/event/1/) — candidate-source links; availability/coverage not verified from this sandbox.
- [EPSG:32611](https://epsg.io/32611) — CRS reference link supplied by the user; not fetched here.
- [Tversky index](https://en.wikipedia.org/wiki/Tversky_index) — general background only, not an official competition rule.

## Core values

### Maximize P(Win)

Choose experiments and software changes by their expected contribution to a valid, reproducible, high-scoring submission. Prefer a well-powered spatial holdout, leakage control, and sound negative result over optimistic leaderboard projections or a wasted slot.

### Own the Outcome

Own the entire path from source and data provenance through evaluation, saved-byte validation, presentation, and authorized portal receipt. Fix shared tools at the shared source; surface blockers and irregularities rather than hiding them.

## Next work, in order

1. Restore the assigned lane paragraph; do not infer it from a previous branch or external repository.
2. Restore and hash-verify the competition rasters and cached feature stack in their intended shared template.
3. Make the shared evaluator and writer available to this project without a private fork; verify the fold-local feature/label masking and tests.
4. Choose one eligible hypothesis from the preregistered shortlist, run feature-alone leakage canaries, then run the full blocked holdout within the budget.
5. Check the candidate surface against the complete registry before placement and its final dots afterward; stop on either duplicate threshold.
6. Only if it beats the comparable holdout best and passes all format/release gates, publish a new TIF with the run card and SHA. Keep the separate weekly-slot selector and organizer receipt as final authorization.
7. Refresh the feed from pinned source snapshots and keep every score's provenance visible.
