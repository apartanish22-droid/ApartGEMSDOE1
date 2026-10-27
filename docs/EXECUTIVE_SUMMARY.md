# Executive summary — evidence-first status

## Decision now

**DO NOT DOWNLOAD/SUBMIT a candidate from this checkout.** There is no GeoTIFF or competition data in the repository, and no scientifically valid candidate can be scored or template-validated here. The included validator only assesses format against a supplied official template; it cannot estimate leaderboard performance. Creating a random or guessed raster would be misleading and risks an invalid submission.

The scores and filenames below are transcribed from the user-provided prompt, not independently verified from organizer receipts. They are therefore **unverified user-provided figures**, not HOLDOUT-DTI and not ORGANIZER-CONFIRMED. The prompt has conflicting purported leaderboard highs (0.3195 and 0.4413), while the cited GEMSDOE32 score is 0.2778. These require receipt/leaderboard verification before analysis.

## Requested site comparison

**No file in this repository is approved for download/submission.** The table identifies the historical entry the prompt reports as each site's leader; it does not claim that those TIFFs are available or safe to reuse. The score figures are **unverified user-provided values** (not HOLDOUT-DTI and not ORGANIZER-CONFIRMED because no receipt is present). A new candidate's score estimate is **not estimable** until the prescribed holdout is run. Exact/near uniqueness is **unknown** without the raster registry and raster files.

| Site | User-reported historical leader | User-reported value (unverified) | New file to download / score estimate | Unique vs other listed sites? |
|---|---|---:|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | None / not estimable | Unknown; no candidate raster/registry |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | None / not estimable | Unknown; no candidate raster/registry |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | None / not estimable | Unknown; no candidate raster/registry |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | None / not estimable | Unknown; no candidate raster/registry |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | None / not estimable | Unknown; no candidate raster/registry |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | None / not estimable | Unknown; no candidate raster/registry |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | None / not estimable | Unknown; no candidate raster/registry |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | None / not estimable | Unknown; no candidate raster/registry |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | None / not estimable | Unknown; no candidate raster/registry |

The **largest value in this supplied nine-site list** is GEMSDOE32's unverified 0.2778; GEMSDOE36's unverified 0.2750 is next. These are historical user-reported values only and do not estimate performance of a new submission. The prompt separately gives 0.3195 and 0.4413 as “current” leaderboard highs. Those claims cannot both describe the same leaderboard snapshot; without a dated official snapshot/receipt, neither is asserted here as the current maximum. Several filenames end in `nan`; that suffix is a warning to validate the actual raster, not proof that its footprint contains NaN.

For GEMSDOE32, the entry name alone does not explain its score or prove its modeling method. The site page, method/code, raster, evaluator/split, and receipt would need independent review. A higher score is possible in principle but cannot be promised or estimated from these unverified values; a leakage-safe, spatially blocked holdout is the appropriate test.

The official [DrivenData problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) was reviewed for this summary on 2026-10-27. It says the target is faults, that the challenge includes expert-labeled faults absent from the existing public USGS database, and that the metric is distance-weighted Tversky: alpha 0.2, beta 0.8, with a linearly decreasing triangular kernel of 300 m support. This weighs false negatives more heavily than false positives in the metric denominator, so spatially useful recall can matter; it does **not** prove what made this particular historical entry score as reported. The same official page specifies submission predictions in [0,1], a single float32 layer, 100 m resolution and UTM zone 11N / EPSG:32611, with outside-bounds data null/NaN. The validator and its synthetic tests now cover those stated artifact constraints insofar as they are expressible relative to the provided sample template; no actual competition artifact has been checked.

## Candidate hypotheses for a later, bounded test

These are proposals, not demonstrated discoveries or a claim of novelty across the cited GEMSDOE sites. The required single-method lane paragraph is absent from the supplied prompt, and no prior site raster/code registry or cached features are in this checkout. Therefore they are planning-only until the lane is recovered and a registry search shows they are permissible. Test only with authorized layers already in the shared feature stack; do not fetch or imply access to unavailable layers. Expected gain is deliberately qualitative, not a score estimate.

| Rank | Hypothesis / layers | Target signature and missed-fault rationale | Difference to test / likely confound | Cost; expected DTI change |
|---|---|---|---|---|
| 1 | Multi-scale curvature ridge-breaks in DEM-derived profile/plan curvature and local relief | Fault scarps and fault-controlled drainage may create aligned curvature discontinuities; off-catalogue structures could retain a geomorphic signature | Derive multi-scale signed curvature and orientation coherence, then mask visible catalogue pixels. Distinguish from prior DEM scarp/ridge approaches in the listed results by emphasizing cross-scale curvature breaks, not elevation rank alone. Confound: lithologic contacts, landslides, stream incision | Low if DEM derivatives are cached; moderate upside, uncertain |
| 2 | Magnetic analytic-signal gradient and directional edge coherence from GeoDawn magnetic channels | Abrupt magnetic-source boundaries and aligned gradients may indicate concealed basement structures beyond mapped surface faults | Use orientation-consistent edges and require spatially coherent multi-channel evidence; unlike a generic magnetic edge, explicitly test off-catalogue, spatially blocked segments. Confound: dikes, pluton contacts, survey seams | Low/medium if layers cached; moderate/uncertain |
| 3 | Radiometric K/U/Th ratio residuals conditioned on lithology/topography | Hydrothermal alteration or fluid-rock interaction may perturb radiometric ratios along unmapped structures | Test robust within-neighborhood residuals and ratio contrasts rather than raw radiometric intensity. Confound: soil moisture, cover, lithology, flight-line artifacts | Medium; low-to-moderate/uncertain |
| 4 | Drainage-network angular anomalies plus terrain-position transitions | Fracture-controlled drainage alignments or deflections may reveal unmapped structures | A network-geometry feature, distinct from simple ridge/scarp proximity; require agreement across drainage scales. Confound: ordinary fluvial controls, roads, DEM artifacts | Medium; low/uncertain |

All can be attempted only if the named raster layers are already available in the project's feature stack. If absent, do not claim viability or download external data under this plan; first document an official source, license, exact layer, spatial coverage, resolution, and obtainable URL, then add an independent validation plan. No candidate is promoted absent a measured improvement and full leakage/duplication gates.

## Required next evidence

1. Place the official `sample_submission.tif`, labels, feature stack and any provided cached stack in the expected `data/` location; do not commit sensitive or large data.
2. Recover the shared evaluator/writer and registry records from the approved template/repository. This checkout has neither; do not privately fork a shared tool.
3. Verify historical leaderboard entries using organizer receipts and obtain actual candidate rasters plus methodology/metadata from the listed sites.
4. Run exactly the prescribed segment-buffered holdout, feature-alone leakage canaries, 95% CI, correlation/3-pixel overlap screening, and template validator; record evaluator version and withheld-positive count.
5. Only after best holdout beats the existing holdout best, unique-lane checks pass, and raster validator passes should a separate slot selector decide whether to use a weekly competition submission.

## Limits and irregularities

- No competition data, application/site, cached stack, holdout evaluator, submission writer, registry rasters, or candidate TIFF is present. Synthetic format/range tests exist for the included validator; they do not validate any competition artifact.
- No DrivenData authentication or organizer receipt was available in the workspace. The official problem-description page was reviewed for metric and format requirements; the live leaderboard and historic receipts have not been verified in this work.
- The prompt's leaderboard-high claims conflict (0.3195 vs 0.4413); 0.2778 is not shown to be the official global high.
- `nan` suffixes in several listed artifact names are a warning, not proof of NaN pixels. Actual file validation is required.
- Surface uniqueness cannot be certified from filenames or SHA-256 alone; pixel-level correlation and point-overlap require registry rasters and dot sets.
- No holdout result, confidence interval, score estimate, or candidate TIF is claimed.
