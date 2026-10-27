# ApartGEMSDOE1 · evidence-first fault discovery

**Start every work session here.** Read the task charter, the active run card, and the mandatory STOP before changing code. **Maximize P(Win)** means improving defensible evidence, not inventing a leaderboard estimate. **Own the Outcome** means preserving negative findings and making unsafe submissions impossible to mistake for approved ones.

## Current decision — DO NOT SUBMIT

**This AP1 session generated one new GeoTIFF, but the experiment is negative and the lane is stopped.**

- **[Open the executive dashboard](https://apartanish22-droid.github.io/ApartGEMSDOE1/docs/executive-summary.html)** · [nine-site review](docs/sites.html) · [submission instructions](docs/submission-guide.html).
- **[Download the new research-only TIFF](docs/downloads/apartgems1-snrc-e1-20000-20261027-735ea04bc35d-DO-NOT-SUBMIT.tif)** — a single self-contained, single-band float32 GeoTIFF. Download: **yes**. Competition submission: **NO**.
- **HOLDOUT-DTI**: **0.0456031**, 95% CI **[0.0393008, 0.0523862]**, evaluator **`gems-segment-pooled-v1`**, **60,988 withheld positives**. Four spatial folds; whole-component hiding with a 1.5 km buffer; pooled TP/FP/FN; 10 km block bootstrap, 1,999 resamples.
- Matched-budget ablation **HOLDOUT-DTI**: **0.0480894**, 95% CI **[0.0414179, 0.0549179]**, same evaluator and withheld positives. Candidate won **0/4 folds**; paired delta −0.0024863, 95% CI [−0.0052729, 0.0002333]. No demonstrated improvement.
- Surface novelty passed. Final dots failed: **100%** within 3 px of a registry lattice; independently **85.885%** against a genuine GEMSDOE31 LiDAR comparator. Five comparisons exceed the literal 70% stop threshold. No exemptions were made.
- Distinct file bytes and prediction array **do not** establish protocol uniqueness or scientific readiness. No leaderboard forecast is defensible. **No real competition slot or final selection was used.**
- TIFF SHA-256: `73fa21b7c558cd48dea20d1d63ddd43efd2ea8b9e57bbc98972153212625987a`.
- Primary records: [`evidence/experiment.json`](evidence/experiment.json), [`evidence/run-card.json`](evidence/run-card.json). Root `run_card.json` / `run-card.json` and the dashboard copies are exact aliases. The underscore-named `evidence/run_card.json` belongs to an earlier, explicitly historical scaffold.

### Concurrent H2 intake — also blocked

PR 10's other-lane H2 artifacts and original claims are preserved, not re-run or adopted as AP1 performance. Independent read-only intake found **99.966%** directional final-dot overlap with the pinned lattice (3 px). Its promotion card listed that control separately; your no-exemption rule still requires **STOP**. This is a geometric gate failure, not proof of copied physics. The selected zero-exterior file also fails the local null-exterior policy, and its card's 40,308 count disagrees with its exact 44,090 positive pixels. No portal acceptance or H2 holdout re-evaluation is claimed. See [`evidence/parallel-intake.json`](evidence/parallel-intake.json) and the [original snapshots](archive/2026-10-27-parallel-review-and-h2/ARCHIVE.md).

Only the canonical evidence-bound builder publishes the dashboard. The obsolete scheduled publisher was retired: it overwrote the current run-card URL with another review's zero-experiment record. Existing native GitHub Pages publication from `main:/` is retained; source-health automation saves diagnostics, not silent science updates.

## User prompt and task charter

### Working prompt capture

The request captured by an earlier concurrent pass is reproduced below for continuity. It is a working transcription, **not claimed to be a verbatim transcript of every original message**. The full previous README remains [archived](archive/2026-10-27-concurrent-main/PREVIOUS_README.md), including its now-obsolete data/branch assertions. The operating requirements below and measured current decision take precedence over old state claims. The bounded parallel-run STOP overrides unbounded “keep iterating” language.

<details>
<summary>Read the captured working request</summary>

Focus on the highest scoring submissions from GEMSDOE24, GEMSDOE25, GEMSDOE27,
GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36. Produce an
executive summary on every site that makes it clear and obvious which is the
best submission to obtain a high score on the leaderboard; each must be unique
and not an exact duplicate of any previous submission. Keep iterating and
testing until we have the highest scoring submission to download and submit.

**MUST GENERATE A UNIQUE TIF SUBMISSION. DO NOT COPY A PREVIOUS SUBMISSION
unless for learning/education. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD
AND SUBMIT THE GENERATED TIF SUBMISSION.** There must be an easy-to-download
submission TIF (single-band GeoTIFF, values in [0,1], matching the submission
format's CRS/shape/geotransform). Inspection/validation runs through the
project without human intervention.

Parallel-Run Protocol:
1. LANE — one method paragraph; rank-correlation > 0.90 with any registry
   raster, or > 70% of dots within 3 px of one registry raster's dots =>
   duplicate lane: log and stop. Check surface AND final dots.
2. REUSE, DON'T REBUILD — cached feature stack, evaluate_holdout.py and
   submission_writer.py. Holdout = hide-and-recover: withhold whole fault
   segments with a buffer, derive catalogue features only from visible faults,
   mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8,
   300 m triangular kernel).
3. LABEL EVERY NUMBER — HOLDOUT-DTI (evaluator version, withheld positives,
   95% CI) or ORGANIZER-CONFIRMED (submission-page receipt). A projection is
   never written as a score.
4. LEAKAGE CANARY — test each feature alone on the holdout; AUC > 0.90 =
   leakage until proven otherwise.
5. RUN CARD — one JSON card: hypothesis; mechanism; named non-fault mimic;
   holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator
   output; submission name + note <= 140 chars; verdict promote / negative.
6. BUDGET — stop after 3 experiments or 2 hours; no slot picks here.

Generate 3–5 candidate geological hypotheses (layers, physical signature, why
it catches catalogue-missing faults, how it differs from the repo), ranked by
expected DTI improvement and cost; validate the top candidate on the
spatially-blocked holdout before touching a weekly slot. Verify line by line
from official verified sources; provide links; no hallucinations.

Core values: **Maximize P(Win)**; **Own the Outcome**.
</details>

### Complete operating requirements for future sessions

1. **Scope:** prioritize GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36, especially GEMSDOE32 H33. Audit the exact highest-claim artifacts and their lineage, not just filenames. Host a local executive subpage for each; do not imply edits to external websites.
2. **New artifact, honest decision:** generate rather than copy/rename prior predictions. Prominently offer the exact downloadable filename, uniqueness results, local performance evidence, short unique name/note and submission eligibility. Separate format validity, scientific promotion, and upload authorization. No high-score or readiness claim without evidence.
3. **Science first:** preregister 3–5 ranked, untried-in-this-repo geological hypotheses before implementing one. Name exact layers, physical transform, why uncatalogued faults could be detected, differences from peers, confounds, expected value (qualitative if uncalibrated) and cost. Confirm actual free official data availability, not just a dataset landing page.
4. **Single lane:** respect an explicit assignment. This brief supplied no identifiable method paragraph, so AP1-SNRC was a documented **provisional** research lane, not an invented authorized assignment. Missing assignment remains a promotion blocker.
5. **Duplicate STOP:** correlation >0.90 with **any** registry raster, or >70% of final dots within 3 px of one raster's dots, stops the lane. Check both continuous surface before placement and final dots. Never exempt a lattice, change a registry, thin a candidate, or try another arm to evade failure. AP1 has already stopped.
6. **Reuse shared tools:** byte-pinned GEMSDOE24 cached stack, `SegmentHoldout`/metric and `submission_writer.py`; never a private metric or writer fork. Fix any shared defect once upstream/in the shared template, with transparent pin/provenance updates. Current 15 shared files remain unchanged.
7. **Leakage-safe validation:** withhold whole fault segments/components with a buffer, derive all catalogue features solely from visible faults, pixel-exactly mask visible faults, and use **pooled** DTI α=0.2, β=0.8, triangular 300 m kernel. Connected components are a conservative raster proxy, not authenticated segment IDs. Test **each** feature alone, both AUC polarities and missingness; AUC extremity >0.90 is leakage until disproved.
8. **Metric labels:** numerical candidate performance is **HOLDOUT-DTI** (evaluator version, withheld-positive count, 95% CI) or **ORGANIZER-CONFIRMED** (exact-file submission-page receipt). Projections are not scores. Historical user reports are not receipts; dashboard numeric performance is restricted accordingly. Public-board observations in the source ledger are not receipts for local files. The inherited conflicting board-high claims were checked, not adopted as benchmarks.
9. **Budget and slots:** at most three experiments **or** two research hours; a duplicate stops earlier. Do not select, upload or spend any weekly slot in this run. A separate future selector requires beating a verified comparable current-best holdout and all other gates, including authenticated account quota. The published rules allow up to three scoring submissions per week per entity, not per parallel site.
10. **Format:** one float32 band in `.tif`, or a ZIP containing exactly one GeoTIFF, with template CRS/shape/geotransform, no NaN inside the footprint, and [0,1] values. Prevent the previously reported range error with a full-array check. Never fabricate an origin or infer portal acceptance. Exterior-mask interpretation is explicitly untested at the portal.
11. **Autonomous audit:** use verified official sources, links, auditable reusable evidence tables and explicit uncertainty. Automate inspection; do not require a human inspector, ask for credentials, or request manual data placement. Organizer-authenticated provenance is still missing despite successful public-mirror restoration. A claimed pre-existing ready GPU pipeline was unverified and contradicted the initially empty checkout.
12. **Delivery:** three passes (implement/verify; adversarial bug/edge-case review; original-requirements/reliability review), a PR and merge if access permits, clear limitations and prioritized next-session work. End the final report with exactly one JSON run card: hypothesis, mechanism, named mimic, HOLDOUT-DTI + CI/version/count, registry correlation/overlap, raster SHA-256, validator, submission name/note ≤140 characters, `promote` or `negative`.

## Verify the shipped research release (no data download required)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/verify_release.py
.venv/bin/pytest -q
# Local static preview
.venv/bin/python -m http.server 8000 --bind 0.0.0.0
```

`verify_release.py` checks hashes, all shared pins, recorded pooled arithmetic, canaries, stop logic, the TIFF's full raw range/mask/grid and every local site link. **Exit 0 certifies a consistent negative research release, never permission to submit.** Verification reconstructs a zero-filled reference from the pinned footprint; this is not a newly authenticated organizer download. `scripts/evaluate_holdout.py --verify-recorded` delegates to the same check; it does not run another experiment.

### Restore the exact ignored inputs for inspection

```bash
.venv/bin/python scripts/restore_data.py
.venv/bin/python scripts/prepare_data.py
# Restricted-network source/HEAD check; does not rewrite the registry
.venv/bin/python scripts/source_health.py --github-only
```

Restoration streams pinned public GitHub owner mirrors, verifies Git blob IDs and final SHA-256s, and reassembles the numerical stack from five parts. It needs the existing `gh` connection, **not DrivenData credentials**. GitHub Actions' weekly source-health workflow additionally probes permitted official pages and publishes diagnostic artifacts. It never automatically monitors DrivenData pages or leaderboard values. Raw rasters, prepared caches, browsers and screenshots stay ignored. Mirror byte integrity is not independent organizer authentication or a license grant.

The original `scripts/run_experiment.py` is retained with its code hash and refuses to rerun because its evidence exists. The frozen registry is not a target for ongoing refresh. Start a **different explicitly assigned run identity** in a later research session; do not delete this record to bypass STOP.

## What the nine-site forensic review establishes

- All nine nominated historical artifacts violate the literal novelty rule against at least one other leader. Exact-file organizer receipts were unavailable, so their supplied values are metadata rather than measured performance.
- GEMSDOE25 and GEMSDOE30 have identical predictions despite different TIFF bytes. GEMSDOE28's H27 and GEMSDOE31's H27 also match exactly.
- GEMSDOE32 H33-B2 is exactly D2.8 **minus 6,436 near-catalogue dots** (≤200 m), leaving 37,654, with zero new locations. Less false-positive mass can improve DTI **if TP coverage is preserved**. This is a plausible mechanism, not proof of hidden-test causality; new faults can occur near known traces.
- GEMSDOE36 adds 1,200 dots to B2. Restored GEMSDOE28/33 bytes contradict inherited simple-count/ancestry descriptions. See [the pinned audit](evidence/focus-audit.json), not the old narrative.
- Registry scope: 442 paths / 425 byte blobs / 237 compatible distinct predictions across the nine pinned snapshots; two incompatible files and other repositories block global completeness. No worldwide uniqueness certification is claimed.

## Layout and automation

| Path | Role |
|---|---|
| `research/hypotheses-2026-10-27.md` | Immutable preregistration: four hypotheses, lane, budget and mimics |
| `research/sources.json` | Official/source claim ledger with explicit limits and failed links |
| `scripts/restore_data.py`, `scripts/prepare_data.py` | Pinned mirror restoration and shared feature cache |
| `src/gems/`, `vendor/template-pins.json` | Byte-exact shared evaluation/writing template and 15 checksums |
| `src/apartgems/`, `scripts/run_experiment.py` | Catalogue-free physical transform, strict policy and frozen runner |
| `evidence/{experiment,run-card,surface-registry,final-registry,focus-audit}.json` | Measured immutable science, not logs inferred from filenames |
| `scripts/{verify_release,source_health,build_site}.py` | Autonomous release checks, freshness diagnostics and deterministic site |
| `scripts/browser_smoke.mjs` | Desktop/mobile/download/clipboard smoke test; optional browser dependency |
| `.github/workflows/` | Tests/release consistency, weekly source reachability/HEAD drift, browser checks |
| `docs/` | Executive dashboard, nine site pages, guide, evidence downloads and research-only TIFF |
| `archive/2026-10-27-concurrent-main/` | Preserved earlier concurrent scaffold/artifact; **not current or approved** |

Concurrent main had an H1 scaffold with a **(0,0) fallback origin**, no comparable holdout, and an independent evaluator. Its original code/artifact is archived for learning/provenance; active generation/evaluation no longer uses those implementations. Other agents' source inventories, tests and historical evidence were preserved rather than overwritten wholesale. The legacy generator explicitly stops instead of manufacturing another file.

## Limits and prioritized next session

1. Respect the stopped lane; obtain a genuinely distinct explicit lane before any new research arm.
2. Establish a common, verified current-best OOF benchmark and bind organizer receipts to exact TIFF hashes. No leaderboard estimate is currently justified.
3. Resolve shared-code redistribution/prize-use rights and independently authenticate organizer data provenance. A public GitHub mirror/hash alone is not a license grant.
4. Verify concrete official raw-tile endpoints and spatial coverage before adopting a raw-DEM or other new-data hypothesis. The two attempted USGS 3DEP landing URLs returned 404; do not label them working downloads.
5. Maintain an authenticated entity-wide slot ledger only in the separate future selector. Quota, portal mask acceptance and final selection are unknown/unperformed here.

Official references and claim-by-claim boundaries are in the [source ledger](research/sources.json) and [sources page](docs/sources.html). Three-pass release/review evidence is in [`evidence/review-ledger.json`](evidence/review-ledger.json) and [`evidence/three-pass-review.md`](evidence/three-pass-review.md). Final local verification: **100 Python tests + five subtests, five Node DOM tests, 10/10 browser checks**, deterministic rebuild and release inspection. Full mirrored-data restoration was independently verified; this is still a negative, unapproved research release.
