# Repository review, evidence, and next-step protocol

**Review date:** 2026-10-27 (UTC). **Scope:** inspected local checkout at `d681f75` on `arena/8564b8df-apartgemsdoe1`; only tracked file at review start was a 15-byte README. No changes or prior sessions were present in this repository.

## Executive review

| Area | Finding | Consequence |
|---|---|---|
| Code and tests | No application, model, evaluator, writer, website, or tests exist in this checkout. | There is no implementation here to run line-by-line or repair. |
| Data | No `data/` directory or GeoTIFFs exist. `numpy` and `rasterio` are not installed in the environment. | No raster can be evaluated or written against the required grid. |
| Shared template | No cached feature stack or shared holdout/writer code exists. | The requested “reuse, don't rebuild” workflow cannot be executed from this checkout. Do not silently substitute a private evaluator. |
| Competition access | No DrivenData credentials/data are available in this environment. | The competition data page is access-controlled according to the supplied project context; no authenticated download was attempted. |
| Existing candidate registry | The user supplied historical names and score-like values, but there are no registry rasters, receipts, or machine-readable records in the repo. | Cannot verify duplicates, reproduce the values, or label them ORGANIZER-CONFIRMED. |
| Submission deliverable | No sample grid or inputs. | No TIF is generated. Any guessed or fabricated grid would be unsafe to submit. |

### Highest-score question (what can and cannot be concluded)

The supplied record identifies `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` as the top reported GEMSDOE32 entry. It also gives inconsistent current-leaderboard claims in different parts of the prompt. Those are **user-provided, unverified reports**, not scores independently confirmed from organizer receipts. Reconcile them against a dated leaderboard snapshot. The GEMSDOE32 submission may be a useful candidate for study, but its name and reported result alone cannot establish why it scored well: one would need its actual raster, code/config, feature lineage, target/metric receipt, and comparable spatial holdout results.

At most, the title and surrounding user-supplied result descriptions suggest a “h33 / b2” method with an all-zero outside convention; the semantics of `h33`, `b2`, and `zeros` are **not established here**. Do not infer the algorithm from a filename. The reported value is not evidence that a newly created raster will exceed it. No score estimate is available in this repository.

## In-scope site summary (from the user's pasted record only)

“Top supplied entry” reproduces the user-provided ordering, not an independently verified ranking. The score estimate is **not estimable** without the authorized holdout data and evaluator; no numeric score is represented as HOLDOUT-DTI or ORGANIZER-CONFIRMED here. “Best reported” is descriptive only; it is **not a recommendation to select or submit**. This table cannot establish raster uniqueness.

| Site / supplied index | Top supplied entry | Estimated score | Unique vs other requested sites? | Download/submit decision |
|---|---|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | Not estimable—no local holdout | Unknown—no rasters to compare | **NO**—not locally validated |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | Not estimable—no local holdout | Unknown—no rasters to compare | **NO**—not locally validated |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | Not estimable—no local holdout | Unknown—no rasters to compare | **NO**—not locally validated |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | Not estimable—no local holdout | Unknown—no rasters to compare | **NO**—not locally validated |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | Not estimable—no local holdout | Unknown—no rasters to compare | **NO**—not locally validated |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | Not estimable—no local holdout | Unknown—no rasters to compare | **NO**—not locally validated |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | Not estimable—no local holdout | Unknown—no rasters to compare | **NO**—not locally validated |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | Not estimable—no local holdout | Unknown—no rasters to compare | **NO**—not locally validated |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | Not estimable—no local holdout | Unknown—no rasters to compare | **NO**—not locally validated |

No score value in this table is presented as HOLDOUT-DTI or ORGANIZER-CONFIRMED. No numeric score estimate is offered.

## Candidate hypotheses for a future, authorized holdout run

These are **candidate designs only**, not implemented, not validated, and not asserted to be novel versus the absent code/raster registry. Expected improvement is unknown and must not be interpreted as a projected score. The rank below prioritizes falsifiability and practical cost, not a claim of better DTI. Exact band names/resolution/coverage must first be checked against the local official raster metadata and the GeoDAWN release inventory.

| Rank for initial investigation | Candidate / required layers | Physical signature and rationale for potentially uncatalogued faults | Difference to inspect against repo/registry | Expected DTI improvement | Relative implementation cost |
|---|---|---|---|---|---|
| 1 | **Multiscale magnetic edge-orientation persistence** — official GeoDAWN magnetic field grid(s), plus catalogue only for holdout masking | Compare edge orientations across scales (e.g. normalized horizontal-gradient orientation coherence), focusing on long, internally consistent linear boundaries away from mapped traces. Faults can juxtapose magnetic units or alter basement structure; persistence may help separate coherent structure from isolated noise. | Not just single-scale edge amplitude: persistence + orientation-consistency statistic. Yet prior registry names include geophysical/edge candidates, so novelty is unproven. | Unknown; likely measurable at low cost using existing magnetic grids. | Low–medium after grid inventory. |
| 2 | **Cross-channel radiometric contact disagreement** — official K, eTh, eU channels or released equivalent, and magnetic grid | Rank locations where independent radiometric channel boundaries and magnetic gradients intersect or diverge coherently. A concealed structure may create a contact discontinuity in multiple physical properties without lying on known catalogue geometry. | Cross-channel boundary agreement/disagreement, not simple radiometric magnitude or a generic fused score. Existing user-listed names mention radiometric fusion; inspect actual registry before proceeding. | Unknown; moderate plausibility and inexpensive if bands are already stacked. | Medium; ratios, masks, scale harmonization, and canary tests required. |
| 3 | **Terrain-conditioned geophysical residual lineaments** — DEM-derived local relief/slope/curvature and GeoDAWN magnetic/radiometric grids | Regress out broad terrain-correlated signal, then test residual geophysical lineaments that remain coherent across ridges/valleys. This targets structure hidden by topographic expression and reduces terrain illumination as a confounder. | Explicit nuisance conditioning and residual stability versus existing topographic-gap / scarp approaches; not a raw DEM ridge detector. | Unknown; may fail where terrain is not the controlling nuisance. | Medium–high; requires spatial folds and careful no-leakage processing. |
| 4 | **Scale-space junctions at fault termini** — magnetic/radiometric gradients and DEM curvature, no catalogue-derived predictor except visible faults in holdout | Seek repeated, compact lineament bends/termination patterns that may indicate relay zones or stepovers associated with unexposed fault segments; require support across at least two independent channels. | Local junction morphology rather than adding dots to known lines. User-supplied past names include tip/stepover approaches, so distinctness is especially uncertain. | Unknown; high risk of confusing drainage, lithologic contacts, and acquisition artifacts. | High; feature extraction, null controls, and extensive error analysis. |
| 5 | **Long-wavelength magnetic gradient discontinuity conditioned on survey geometry** — magnetic grid plus flight-line/metadata layers if officially supplied | Test whether broad, cross-line-consistent gradients retain lineament structure after removing acquisition-direction striping. A hidden basement structure could persist across flight lines; striping would mimic it. | Survey-geometry artifact correction + lineament persistence, not a new external geologic label. Requires published line data or metadata. | Unknown; not viable until official line geometry and downloadable assets are confirmed locally. | High; metadata/coverage integration and artifact diagnostics. |

A holdout hypothesis must pass: (i) whole-segment spatial holdout plus buffer, (ii) exact catalogue mask and visible-only feature derivation, (iii) per-feature leakage canary, (iv) pooled DTI with the agreed evaluator, and (v) registry correlation/3-pixel overlap checks before and after dot placement. Stop the lane if either duplicate threshold is exceeded. Do not compare pooled DTI values from different evaluators or splits.

## Official source links and access status

| Source | What it supports | Status in this review |
|---|---|---|
| [DrivenData GEMS Prize challenge](https://www.drivendata.org/competitions/306/competition-doe-gems/) | Official competition description; task framing and competition structure. | Public page description surfaced in web search. No login was used. |
| [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Problem-specific overview requested in the project brief. | Link supplied by user; content not verified in this checkout. |
| [DrivenData about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) | Additional challenge context requested in the brief. | Link supplied by user; content not verified in this checkout. |
| [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Authorized input files and submission template. | User reports login required; no credentials or data are present here, so no download attempted. |
| [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) and [DOI](https://doi.org/10.5066/P93LGLVQ) | Official description of released airborne magnetic and radiometric survey products. | Public USGS page description surfaced in search; actual data packages were not downloaded or inspected. |
| [DOE/INL GDR submission 1391](https://gdr.openei.org/submissions/1391) | User-supplied geothermal data-repository reference. | Not independently verified. |
| [GBCGE INGENIOUS](https://gbcge.org/current-projects/ingenious/) | User-supplied project context. | Not independently verified. |
| [EPSG:32611](https://epsg.io/32611) | User-supplied CRS reference (WGS 84 / UTM zone 11N). | Not confirmed as the competition grid CRS; must read sample raster metadata. |
| [Reference solution repository](https://github.com/drivendataorg/gems-prize-reference-solution) | Public baseline implementation. | Link is on an allowed host but source not cloned/inspected in this review. |
| [Challenge rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | User-supplied official rules document. | Host is inaccessible from this environment's network policy; no verification claimed. |

No third-party source is proposed as a currently viable new-data dependency. If later analysis requires missing inputs, first determine whether the data are in the authorized competition package or official USGS GeoDAWN release. Do not describe a data source as obtainable until its specific asset URL and access are confirmed.

## Submission workflow and validator

The competition submission instructions pasted by the user say to upload one single-band GeoTIFF (or a ZIP containing one) matching the submission format's CRS, shape, and geotransform. The actual sample raster is absent here, so those properties cannot be confirmed. `scripts/validate_submission.py` compares these properties against a supplied reference raster, rejects non-finite or out-of-range values inside the reference footprint, and prints a SHA-256. Install dependencies from `requirements.txt`; then run:

```bash
python scripts/validate_submission.py path/to/predictions.tif --template path/to/sample_submission.tif
```

A pass means only that the file passed the implemented structural/range checks. It does not prove scientific validity, uniqueness, high holdout DTI, competition-rule compliance, or organizer acceptance.

### Mandatory next actions before any TIF can be made

1. Restore/provide the shared project template (cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`) and use those exact shared tools.
2. Make the authorized competition package available locally, including `sample_submission.tif`, feature/label rasters, and any required fault catalogue/DEM metadata. Record provenance and hashes without committing restricted/large files.
3. Identify exact band descriptions, masks, CRS, affine, grid shape, nodata conventions, and fault segment IDs from the actual files.
4. Reproduce the current holdout best on the prescribed blocked split and report evaluator version, withheld-positive count, and 95% CI. If impossible, stop rather than fabricate a score.
5. Choose at most three experiments within the stated time budget; test feature-alone AUC leakage canaries and uniqueness before dot placement and on final dots.
6. Run the shared writer, then the validator, save a run card and SHA-256. Keep real-submission promotion as a separate selector step.
7. Build the requested public executive-summary UI only after the evidence/data pipeline exists. The UI must never advertise a download as “OK to submit” unless all configured gates pass; public scores must have receipt provenance and date.

## Run card

The canonical run card for this review is [`docs/run_card.json`](run_card.json). No experiment was run; all unavailable measurements remain `null` rather than being guessed.
