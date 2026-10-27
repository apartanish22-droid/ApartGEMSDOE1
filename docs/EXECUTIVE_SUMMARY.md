# Executive summary — evidence-first status

## Decision now

**DO NOT DOWNLOAD/SUBMIT a candidate from this checkout.** There is no GeoTIFF or competition data in the repository, and no scientifically valid candidate can be scored or template-validated here. The validator added here only assesses format against a supplied official template; it cannot estimate leaderboard performance. Creating a random or guessed raster would be misleading and risks an invalid submission.

The filenames and purported score reports in the prompt are not independently verified from organizer receipts. To honor the run-card score-label rule, no unverified numeric results are reproduced as scores here. The prompt contains inconsistent claimed leaderboard highs and a claimed GEMSDOE32 result; these require dated organizer-receipt/leaderboard verification before quantitative analysis.

## Requested site comparison

| Site | User-provided top relevant candidate | Estimated score | Current decision |
|---|---|---|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | Not estimable; no local holdout | Historical lead only; `nan` suffix is a warning, not proof of invalid pixels; inspect file |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | Not estimable; no local holdout | Historical lead only; inspect file |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | Not estimable; no local holdout | Historical lead only; inspect file |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | Not estimable; no local holdout | Top supplied entry for this site only; inspect file |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | Not estimable; no local holdout | Historical lead only |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | Not estimable; no local holdout | Historical lead only; inspect file |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | Not estimable; no local holdout | Top supplied entry among these sites only; uniqueness and submission readiness unknown |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | Not estimable; no local holdout | Historical lead only |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | Not estimable; no local holdout | Historical lead only |

The entries and ordering are copied from the prompt and are not independently validated. The estimated-score column is intentionally unavailable: a score requires the authorized holdout data and shared evaluator. No metric is inferred from filenames or public-site descriptions.

### GEMSDOE32: what can and cannot be inferred

The prompt identifies the GEMSDOE32 item as its strongest reported entry among these selected sites. Its name suggests a method label, but names are not reproducible methods. Without the site's methods, code, raster, evaluator definition, split protocol, and organizer receipt, we cannot establish why it scored that way, whether the result is comparable, or whether it is an exact/near duplicate. A higher score is possible in principle, but cannot be promised or estimated from this evidence. The relevant next step is reproducibility and strict spatial holdout—not extrapolation from leaderboard results.

## Candidate hypotheses for a later, bounded test

These are candidate ideas, not demonstrated discoveries. Test only against existing cached layers and the shared segment holdout; do not fetch or imply access to unavailable layers. Scores and expected gain are deliberately qualitative.

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

- Only README existed at initial review; no data, application/site, tests, cached stack, holdout evaluator, submission writer, or TIFF.
- No DrivenData authentication or organizer receipt was available in the workspace; no live leaderboard or page claims have been verified in this work.
- The prompt gives conflicting leaderboard-high claims and an unverified GEMSDOE32 result; none is shown to be the official global high without dated organizer evidence.
- `nan` suffixes in several listed artifact names are a warning, not proof of NaN pixels. Actual file validation is required.
- Surface uniqueness cannot be certified from filenames or SHA-256 alone; pixel-level correlation and point-overlap require registry rasters and dot sets.
- No holdout result, confidence interval, score estimate, or candidate TIF is claimed.
