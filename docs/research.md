# Preregistered ideas — not experiments or assigned lanes

> **Earlier parallel review — historical snapshot, not current status.** For the latest decision, owner-mirror provenance and the invalid synthetic demo, see the [current executive summary](executive-summary.html) and [saved-byte report](data/parallel-demo-validation.json).

None is authorized to run until a single lane is assigned. Novelty is provisional: this checkout initially had no implementation, while the reviewed sibling already implements curvature, magnetic edges, radiometry, thermal conduits and dot thinning. No quantitative DTI improvement is estimated. Ranking below is scientific prioritization, not a measured benefit. No new external dataset is assumed obtainable.

| Rank / relative cost | Layers and transform | Physical hypothesis and missing-catalogue rationale | Named mimic / distinction |
|---|---|---|---|
| 1 / medium | Cached RTP/TMI and gravity; multiscale gradient-normal displacement with directional sign-consistency | A persistent lateral offset between deep magnetic and shallow gravity contact responses could indicate an inclined buried fault under alluvium, absent from surface mapping. Require coherent offsets along strike, not isolated edges. | Dipping intrusive contact can mimic it. Differs from a high-edge-magnitude fusion by estimating signed cross-layer displacement. Must inspect band metadata first; not viable if gravity layer is only a derivative with unknown provenance. |
| 2 / medium | DEM and radiometric K/Th channels; asymmetric across-ridge profile residual after matching elevation and slope | A cross-scarp chemical discontinuity that persists after terrain correction could identify low-relief buried structural boundaries. | Sedimentary facies contact or moisture attenuation. Unlike raw radiometric/curvature concordance, tests matched cross-strike asymmetry; novel in this checkout, not proven globally novel. |
| 3 / high | DEM plus magnetic edge orientation; along-strike spectral phase discontinuities across adjacent profiles | Repeated displaced landform profiles aligned with a subsurface edge may identify distributed slip in unmapped piedmont. | Paleochannel avulsion or fan deposition. Targets displacement phase, not ridge strength or tip extrapolation. DEM resolution/coverage must be confirmed before viability. |
| 4 / high | Thermal-related cached channel, DEM and magnetic structure; terrain-conditioned residual graph bottlenecks | A thermal residual concentrated where independent structural corridors intersect may reveal concealed permeable breaks missed by surface catalogue. | Shallow groundwater convergence or solar aspect. Unlike a thermal threshold, requires conditional residuals and graph bottlenecks. Channel meaning must be established; no claim it measures heat flow. |

## Required experiment design

Use only the canonical template. Withhold whole segments with a buffer; recompute every catalogue-derived feature from visible faults within each fold. Fit normalization and calibration on training blocks only. Run feature-alone AUC canaries, including missingness and coverage; stop on AUC >0.90 pending diagnosis. Keep the exact incumbent and candidate on the same evaluation footprint and folds. Pool DTI components before forming the ratio; report evaluator version, withheld positives, and block-bootstrap 95% CI. Compare paired candidate-minus-incumbent intervals, not raw scores from different evaluators. Evaluate the unmodified surface against every registry raster before placement, then final dots using the stipulated proximity gate. A duplicate ends this lane, rather than prompting cosmetic perturbation.

## Why the historical GEMSDOE32 file may have helped

The sibling README describes dot thinning followed by catalogue-flank removal. Where known catalogue pixels are excluded from scoring, removing predictions with low incremental truth credit can reduce false-positive mass while retaining spatial coverage of hidden faults. This is a plausible mechanism, not a causal explanation of a private result. The file's historical result is owner-reported, not receipt-confirmed. Reproducing its geometry would violate this request's uniqueness objective.

The sibling README explicitly reports disagreement between static and visible-gated holdout evaluations of that same champion. Do not extrapolate either to the leaderboard or compare unmatched evaluator versions. Its latest headline holdout improvement also remains marked negative because other gates fail. Those are warnings against selecting by the largest isolated number.

## Sources and evidence boundaries

- [Official DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution): retrieved README and pinned SHA in `evidence/official_source.json`; verifies CPU/GPU setup options and need to obtain competition data, not sibling score claims.
- [Competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/): user-provided official URLs, not live-verified here.
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [GDR 1391](https://gdr.openei.org/submissions/1391), [NLR rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf): user-provided sources, blocked by network policy here; no specific geological conclusion is attributed to unread pages.
- `research/gems32/registry/data_manifest.json` describes reachable, hash-pinned GitHub mirrors, explicitly **not organizer authenticated**. `feature_receipt.json` describes a cached stack but does not supply its bytes. Therefore data placement is not the only blocker.

These are hypotheses, not discoveries of geothermal vents; fault prediction is not confirmation of a geothermal resource.
