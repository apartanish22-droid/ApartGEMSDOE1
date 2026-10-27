# Apart GEMS — evidence before submission

**Current decision: NOT READY. Do not submit a historical file or a renamed copy. This audit generated no candidate TIFF; a parallel synthetic demo exists but fails the pinned template grid check.** The automatic preflight finds that the registered lattice forces at least 82.34% three-pixel overlap for any 37,654-dot candidate, exceeding the requested 70% stop threshold. This is a geometry bound, not a score. It does not rule out all lower budgets. No assigned method lane was specified. See the [executive summary](docs/executive-summary.html), [forensics](research/forensics-2026-10-27.md), [three review passes](evidence/review-passes-2026-10-27.md) and [negative JSON run card](docs/data/run-card.json).

## Working brief — read at the start of every session

This is the user's project brief, consolidated from repeated passages of the original request; the values and historical filenames for the nine priority sites are preserved in [`config/inputs.json`](config/inputs.json). The objective is to build a clear, auditable, autonomous research and submission system for the [DOE GEMS Prize](https://www.drivendata.org/competitions/306/competition-doe-gems/), discover physically defensible unmapped faults associated with geothermal resources, and ultimately compete near the top of the leaderboard. **Maximize P(Win)** by treating evidence and scarce slots as valuable; **Own the Outcome** by finding and reporting blockers, defects and negative results rather than hiding them.

The requested focus is GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. Explain each site's strongest supplied historical file, make the file and decision unambiguous, distinguish an estimate from a measured score, and never resubmit or disguise an old file as unique. Produce a genuinely new single-band float32 GeoTIFF only when the stated gates permit it. It must have the correct CRS, shape and transform, finite values within [0,1] in the footprint, and a unique name and short note. A format pass does not imply organizer acceptance, uniqueness, a high score or permission to use a weekly slot. A GitHub Pages dashboard should put the decision first, show the nine-site evidence, provide a submission guide, cite official sources, and refresh source freshness without fabricating a live leaderboard feed.

Before a geological implementation, rank 3–5 plausible, distinct hypotheses by expected value and cost; identify specific layers, physical signatures, non-fault mimics, why missing faults might be found, how each differs from known work and whether official data are obtainable. The current [research slate](research/hypotheses-2026-10-27.md) is explicitly untested. Validate the assigned method against the matched current best on a leakage-safe, spatially blocked holdout before any submission. Verify claims against official sources, preserve caveats, work autonomously, and disclose missing access. Complete three passes: implementation/verification, bug and edge-case review, and requirements/accuracy review. Open a PR from this fixed Arena branch and merge it only when checks and repository policy permit.

### Parallel-run protocol — binding limits

1. **Lane:** use only the explicitly assigned single method. Before placement and again on final dots, stop on any registry rank correlation >0.90 or if >70% of candidate dots are within 3 pixels of one registry raster. Do not silently exclude a comparator. The current prompt did not supply a single assigned method paragraph.
2. **Reuse:** use the shared cached feature stack, `evaluate_holdout.py` and `submission_writer.py`, not a private evaluator/writer fork. Hide whole fault segments with a buffer, derive all catalogue-based features solely from visible faults per fold, mask visible fault pixels exactly, and evaluate pooled distance-weighted Tversky with α=0.2, β=0.8 and a 300 m triangular kernel. Fix a shared-tool defect in the canonical template, not a private copy. The GEMSDOE32 wrapper's handling of continuous probabilities is flagged in the [forensics](research/forensics-2026-10-27.md) and [upstream issue #51](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/51). The pinned upstream 57GEMSDOE writer separately preserved a synthetic 0.25 in a round-trip test; this is not portal acceptance.
3. **Evidence:** label measured holdout outcomes `HOLDOUT-DTI` with evaluator version, withheld positives and 95% CI; label a file-specific result `ORGANIZER-CONFIRMED` only with a submission-page receipt. Historical user/owner claims without receipts remain explicitly unverified, never a projection dressed up as a score.
4. **Leakage canary:** test each feature alone on the holdout; AUC >0.90 is leakage until proven otherwise. Never score a model trained using hidden labels or full-catalogue derived features.
5. **Run card:** record hypothesis, mechanism, named non-fault mimic, holdout DTI and CI, registry correlation/overlap, raster SHA-256, saved-byte validator details, name, note ≤140 characters and `promote`/`negative` verdict. Unrun values must be null. Negative results are deliverables.
6. **Budget and selection:** stop after at most three experiments or two hours. No live submission slot is chosen or spent during research. A separate selector operates within the official weekly limit shown on the submission page.

## What this checkout actually does

- Restores hash-pinned **owner-hosted mirrors** of the sample, labels, nine historical rasters and a registered lattice into an ignored cache; can separately restore the 19-band feature mirror. These hashes establish integrity, **not organizer authentication**.
- Runs an independent read-only geometry/lineage audit and a saved-byte TIFF inspection. It does not implement a replacement holdout evaluator or submission writer. Legacy parallel demo generator/evaluator/writer entry points are disabled safety stubs; their earlier source remains in Git history.
- Uses the unmodified, pinned GEMSDOE32 preparation script after an extra grid/hash preflight. A 19-band mirror was restored and prepared in this session; the large data and prepared arrays are deliberately not in Git. This is data preparation, not a trained model or an experiment.
- Publishes static executive and per-site pages, a source-freshness check for public GitHub refs, and a negative run card. The [DrivenData Terms of Use](https://www.drivendata.org/termsofuse/) restrict automated/manual monitoring or copying without written consent; the dashboard does not scrape or auto-refresh its leaderboard.

## Reproduce the audit

Python 3.10+, `gh`, and network access to GitHub and PyPI are required. The commands below use a local virtual environment; no credentials are stored by the scripts.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/restore_inputs.py --group light
python scripts/audit.py --run-card-out docs/data/run-card.json
python scripts/check_freshness.py
python scripts/build_site_pages.py
python -m pytest
npm ci --ignore-scripts
npm test
```

Optional, larger model-data preparation (roughly 400 MB download and about 1 GB temporary arrays):

```bash
python scripts/restore_inputs.py --group model
python scripts/prepare_mirrors.py
# Optional: restore the pinned shared 57GEMSDOE tools and run synthetic tests only
python scripts/check_shared_template.py --report .cache/shared-tool-checks.json
```

This last command retrieves the pinned shared source archive, checks its SHA-256, extracts only the untouched shared preparation files into `.cache/`, validates the three source grids and invokes the shared preparation script. It does **not** build the shared cached feature stack, train a model or override the duplicate stop. A parallel run already committed a synthetic research-only TIFF; its origin is `(0, 0)`, not the pinned mirror’s `(243350, 4508550)`. Its [saved-byte audit](docs/data/parallel-demo-validation.json) fails the grid check, and uniqueness/holdout remain unverified. Do not submit it. The original competition data is available from the [authenticated data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) when authorized; the mirrored sources are not an official substitute.

To inspect saved raster bytes without approving a slot:

```bash
python scripts/validate_raster.py path/to/candidate.tif
```

This checks the owner-mirror template hash, single band, float32, geometry, footprint finite/range/nodata and outside encoding. A previous portal error, “Predicted values must be in range [0, 1],” is not enough to identify the cause. The official description mentions null/NaN outside bounds; whether zeros outside the irregular mirrored footprint are accepted is unverified. The tool reports both policies and never asserts portal acceptance. Its default exit status uses the conservative null-outside-footprint profile; use `--profile all-finite` only to diagnose the alternative.

## Remaining blockers and next steps

1. Resolve the missing lane assignment and literal lattice conflict with the protocol owner; do not evade it by targeting lattice holes. Refresh a complete registry including concurrent runs.
2. Establish the canonical cached stack and a frozen same-evaluator best; resolve the reported GEMSDOE32 wrapper defect centrally or use the verified shared implementation only after the protocol gates. Define a leakage-safe spatial holdout and feature canaries.
3. Establish official-origin provenance for the competition files, permitted external-data licenses, and any required credentials/access. The mirrored sample contains the label positives even though the organizer describes an all-absence sample; treat this as a mirror discrepancy, not proof about the official file. Compare against actual organizer receipts rather than user-reported values. Public expert-hidden truth and a validated holdout-to-leaderboard calibration remain unavailable.
4. Only after an explicit lane passes all gates should the independent selector consider a weekly slot; then generate and re-open the candidate TIFF, publish the name/note and clearly show its authorization state.

Primary sources: [problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS/GDR](https://gdr.openei.org/submissions/1391), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services).
