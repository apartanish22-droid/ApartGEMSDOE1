# Apart GEMS · evidence-led fault discovery

> **START HERE EVERY SESSION.** The goal is an original, scientifically grounded GeoTIFF that could compete in the DOE GEMS Prize. **Current decision: no new submission exists; do not upload any historical file.** [Executive summary and submission guide](docs/executive-summary.html) · [Research and official sources](docs/research.html) · [Negative run card](evidence/run_card.json)

## User's operating brief

This is a consolidated, non-verbatim record of the user's lengthy, repeated prompt; the non-negotiable parallel-run protocol is preserved below. Review it before doing project work. The user asks for autonomous research and automated inspection; an easy, unambiguous download only after a genuinely new GeoTIFF is safe to submit; an executive comparison of GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36; documented official sources; a unique file name and short note; and evidence, not a fabricated estimate. The current scientific task is fault identification relevant to geothermal exploration, not direct proof of a geothermal vent. Historical submissions are for education and comparison only, never to be copied or relabeled as new.

**Core values:** Maximize P(Win): evaluate tradeoffs, risk, and evidence to improve the chance of success. Own the Outcome: take responsibility end to end, surface defects, and learn from negative results. Neither value justifies an unverified claim or a wasted submission slot.

### Parallel-run protocol (user's wording)

1. **LANE.** Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.
2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack, `evaluate_holdout.py` and `submission_writer.py`. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.
3. **LABEL EVERY NUMBER** as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.
4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.
5. **RUN CARD.** End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.
6. **BUDGET.** Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

The task also asks for 3–5 ranked new geological hypotheses, with layers, mechanisms, confounders, incremental value, cost, and source availability **before** fitting. Validate the top authorized candidate on a spatially blocked holdout against a frozen current best. Check complete registry uniqueness before placement and on final dots. Perform three review passes; fix defects and explicitly disclose remaining limitations. Never present a local DTI as an estimated private/public score without validated transfer calibration. A high-scoring previous raster is not automatically unique or submit-ready.

## Current outcome

- **No file is cleared to download for competition submission.** This review ran no geological experiment, holdout, canary, new prediction, or slot selection. The message refers to a single method paragraph, but none is supplied; the complete registry is also unavailable. The [four ranked proposals](docs/research/hypotheses-2026-10-27.md) are unassigned and untested. A separate parallel synthetic demo was inspected and rejected below.
- The repo initially had only its one-line README. It was not a ready-to-train pipeline. We restored a **third-party, hash-pinned 19-band feature mirror** and cached it via the unchanged upstream template; this does not establish organizer authentication or a license. The large data and caches are ignored by Git and may not persist. The connected GitHub account has read-only access to all nine external repositories, so their pages were not modified; the comparison and individual site reviews are consolidated here.
- Parallel work added a [synthetic demo](docs/assets/gemsdoe1-h1-blind-conduit-20261027T212428Z-06281cc7efb3-zeros.tif), not a real geological prediction. It has origin `(0,0)`, which fails the pinned mirror's `(243350,4508550)` grid; the mirror itself is not organizer-authenticated. **DO NOT SUBMIT.** Its whole-array values are finite in `[0,1]`; footprint and registry overlap are not meaningfully comparable on a different grid. [Validation receipt](evidence/parallel_demo_audit.json).
- Our independent [nine-file audit](evidence/fleet_audit.json) measured all 72 directional peer comparisons above the 70% threshold. On the mirrored footprint, the user-listed 13GEMSDOE lattice forces at least 82.34% overlap for any distinct 37,654-dot candidate; this is **geometry, not a score**, and applies only to that footprint and budget. The proof does not rule out every possible raster. [Details and reproduction](docs/research/decision-2026-10-27.md).
- GEMSDOE32's **0.2778 USER-REPORTED claim** is the highest supplied among the nine, but we have no artifact-linked organizer receipt. Its historical support is the GEMSDOE25 support minus 6,436 dots within two pixels of the mirrored mapped catalogue. This cannot establish causality or forecast another model's score. The other historical figures in the site are explicitly unverified user claims, not HOLDOUT-DTI or ORGANIZER-CONFIRMED results.
- The [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) displayed 0.4544 when observed on 2026-10-27 around 21:14 UTC; that public display is not a submission-page receipt for any file here. It may change, so follow the link. DrivenData's terms prohibit automated monitoring; the site's freshness feed only checks public GitHub repository heads and does not update scores or audit new files.
- Official data access redirected to login, and the mirrored sample has the same positive pixels as the mirrored training labels although the organizer describes its sample as predicting total absence. Treat all geometry and format checks as conditional until the organizer's actual template is authenticated. The earlier portal range error's cause is unknown.

## Reproduce the current review

These commands do not train a model or produce a competition submission. Python 3.11, `gh`, a working GitHub connection and internet access to GitHub/PyPI are required.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/download_audit_inputs.py      # small, pinned historical raster mirrors
.venv/bin/python scripts/audit_fleet.py                 # rewrites the geometry receipt
.venv/bin/python scripts/check_shared_template.py       # upstream metric/writer synthetic tests
.venv/bin/python scripts/bootstrap_shared_data.py      # ~419 MB feature mirror + cached bands
.venv/bin/python scripts/build_site.py                  # rebuild after changing a receipt/manifest
.venv/bin/pytest -q
python -m http.server 8000 --bind 0.0.0.0
```

The bootstrap fetches and hash-verifies the original shared template before running it. Parallel scaffolds at `scripts/generate_submission.py`, `scripts/evaluate_holdout.py` and `scripts/submission_writer.py` are deliberately **disabled**: they respectively generated synthetic wrong-grid data, computed a non-protocol metric, and guessed a grid origin. Use the restored, unmodified shared evaluator/writer only after implementing the required gates. The central `scripts/validate_submission.py` checks saved pixels and exact template geometry but never approves a slot or authenticates its reference. [Data receipt](evidence/data_preparation.json) · [Shared synthetic-test receipt](evidence/shared_tool_checks.json) · [Pinned source manifest](catalog/reference_sources.json). No synthetic test validates a geological hypothesis or grants upload permission. The full training pipeline and automatic selector are not yet implemented here.

To reproduce the demo's expected format **failure**, after the input download above:

```bash
.venv/bin/python scripts/validate_submission.py docs/assets/gemsdoe1-h1-blind-conduit-20261027T212428Z-06281cc7efb3-zeros.tif --template .cache/audit-inputs/sample_submission.tif
# exits 1: transform mismatch; the mirror is not an authenticated organizer template
```

## What must happen next

1. Clarify the missing assigned method lane and the literal registry policy (including the calibration lattice); never silently exempt a comparator or game its holes. Refresh and hash-pin the **complete** applicable registry.
2. Authenticate the actual organizer template and input provenance/rights; examine the contradictory sample metadata and current submission-page quota. The source host restriction prevents direct fetch of some official USGS/GDR archives from this sandbox.
3. Use the shared cached features and shared evaluator/writer for an authorized lane, with leakage-safe whole-segment buffered folds, standalone feature canaries, a same-evaluator best control, pooled HOLDOUT-DTI and paired 95% spatial CI. Stop on duplicate or budget limits.
4. Validate exact saved bytes: one float32 band, matching organizer CRS/shape/geotransform, finite and in [0,1] inside the valid footprint; inspect outside-footprint encoding separately against current official rules. The older GEMSDOE32 wrapper binarizes positive probabilities ([upstream issue #51](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/51)), so use the actual shared writer for continuous fields and resolve the wrapper centrally before use. No portal acceptance is implied by local checks.
5. Run a separate automated selector, then provide a name, ≤140-character note, SHA-256 and a clearly marked download only if every gate passes. Capture an organizer submission-page receipt after a real upload. Do not auto-scrape DrivenData or spend a slot on an unvalidated idea.

See the [decision record](docs/research/decision-2026-10-27.md) for the official links, deadline wording discrepancy, data scope, provenance caveats, and reproducible geometry proof. The official [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) supports CPU as well as GPU execution; GPU is an acceleration option, not a proven absolute requirement.
