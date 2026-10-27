# Executive summary — evidence before submission

## Decision now

# **DO NOT SUBMIT. No approved prediction GeoTIFF exists.**

A synthetic demo GeoTIFF is present for software inspection, but it was generated from artificial Gaussian blobs and synthetic fault traces, not the competition feature stack. Its UTM origin is unverified; it has no valid holdout-DTI, leakage canary, or reproduced registry novelty result. Do not treat its filename, SHA-256, geometry, or format check as proof of a competition prediction. The file is explicitly `RESEARCH_ONLY_DO_NOT_SUBMIT` in its sidecar/run card.

## Nine requested sites

Values below are **user-reported historical figures** from the prompt; they are not HOLDOUT-DTI and not ORGANIZER-CONFIRMED because submission receipts were not provided. “Candidate to submit” is none for every site. New score estimates are not estimable without the authorized data and required holdout. Uniqueness is unknown without comparing the exact raster files against the full registry.

| Site | User-reported historical leader | User-reported value (unverified) | File to download and submit | New score estimate | Unique vs other sites? |
|---|---|---:|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | None approved | Not estimable | Unknown |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | None approved | Not estimable | Unknown |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | None approved | Not estimable | Unknown |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | None approved | Not estimable | Unknown |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | None approved | Not estimable | Unknown |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | None approved | Not estimable | Unknown |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | None approved; do not resubmit | Not estimable | Unknown; source snapshot has unverified overlap claims |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | None approved | Not estimable | Unknown |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | None approved | Not estimable | Unknown |

The largest user-reported value among these nine is GEMSDOE32's 0.2778; GEMSDOE36's 0.2750 is next. The global highs quoted by the prompt (0.3195 and 0.4413) conflict. The official [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) was fetched on 2026-10-27 and showed a public rank-one value of 0.4544. This is a leaderboard observation, not a submission receipt for our project and not a holdout estimate. It makes clear the nine-site historical leader is not the current overall leader.

## GEMSDOE32: what the evidence supports

The pinned owner-maintained GEMSDOE32 page snapshot calls the cited file “D2.8 with B2 catalogue-apron pruning” and labels 0.2778 `OWNER-REPORTED`; no organizer receipt linking that score to the raster hash is present here. A plausible mechanism is thinning predictions to a fixed point budget and pruning predictions near known catalogue traces. Under a distance-tolerant score, that could suppress low-credit false positives while retaining useful coverage near unmapped faults. This is a hypothesis, not a causal explanation of the historical score.

The same source snapshot warns that the entry is already scored and contains overlap statements. A separate audit snapshot compares different site candidates and yields different overlap figures; the corresponding raster bytes are not in this checkout, so the calculation has not been independently reproduced. **Do not resubmit GEMSDOE32's file or infer uniqueness from its name.**

The official [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) was reviewed on 2026-10-27. It identifies fault prediction as the target, describes expert-labeled faults absent from the public catalogue, and specifies distance-weighted Tversky with alpha 0.2, beta 0.8 and a 300 m triangular kernel. The submission page specifies a single float32 layer in [0,1] at 100 m / UTM 11N EPSG:32611, with outside-bounds data null/NaN. The greater false-negative weight makes recall valuable, but cannot identify why this particular historical file received its owner-reported result.

## Provisional hypotheses — not assigned or tested

The prompt's lane-defining method paragraph is absent. These proposals are not established as novel across all prior repositories and must not be implemented until the lane and registries are recovered. No numeric expected score or DTI gain is stated because none has been measured.

| Rank for a first falsifiable test | Candidate layers and signature | Why it might find uncatalogued faults | Confounder / distinction | Cost and expected DTI |
|---:|---|---|---|---|
| 1 | Multiscale magnetic–gravity edge displacement/orientation persistence from official GeoDAWN potential-field channels | Cross-scale, cross-channel structural offsets may persist beneath alluvium away from mapped Quaternary traces. | Dipping intrusive/lithologic contacts can mimic faults; test displacement/orientation rather than raw edge magnitude. | Medium; benefit unknown until holdout. |
| 2 | Terrain-matched radiometric K/Th cross-strike residuals plus DEM curvature context | Persistent chemical contrasts after matching slope/elevation may reveal concealed alteration boundaries. | Moisture, lithology, and survey seams; differ from raw radiometric intensity and generic scarp proximity. | Medium; benefit unknown. |
| 3 | DEM profile/plan curvature asymmetry and drainage deflection conditioned on mapped geology | Fault-controlled relief/drainage may register structures with weak scarps. | Fan deposition, channel migration, landslides; distinct from a simple elevation-rank or scarp detector. | High; viability depends on authorized DEM coverage. |
| 4 | Magnetic lineament terminations/intersections with a continuity-aware graph statistic | Relay zones and fault tips may create coherent lineament bends outside catalogue traces. | Dikes and lithologic contacts; prior sibling site names include tip/stepover work, so novelty is especially uncertain. | High; benefit unknown. |

All are contingent on bands actually present in the shared cache. If a proposal needs new data, document and test the specific official source's asset availability/license before calling it viable. The competition problem page lists potential-field and other feature families, but the login-gated raster package is absent here.

## Submission and remaining work

1. Obtain and provenance-check the official `sample_submission.tif`, labels, training features, fault catalogue, and DEM links. Do not treat owner-supplied GitHub mirrors as organizer-authenticated.
2. Recover the exact lane and canonical template package, including the shared evaluator/writer and complete registry. The root custom evaluator in this checkout does **not** implement the required segment-buffered protocol and must not be used to report DTI.
3. Run per-feature leakage canaries, then hide/recover whole segments with buffer, visible-only catalogue features, exact visible-fault masking, pooled DTI, evaluator version, withheld-positive count and spatial 95% CI. Stay within the experiment/time budget.
4. Compare the candidate surface before placement and final dots against all registry rasters. Fail closed if correlation/overlap exceeds the lane thresholds.
5. Reopen and validate saved bytes against the official sample. Only a positive matched holdout and passed novelty/format gates may go to the separate weekly-slot selector.
6. Keep a visible **DO NOT SUBMIT** warning until then. The synthetic demo can be downloaded for code/format inspection only; its original (0,0) affine origin is unverified and its biology/geophysics are synthetic.

No holdout experiment or competition upload was run in this review. The root [`run_card.json`](../run_card.json) is the current demo card with a negative verdict; historical cards under `docs/` and `evidence/` are not authorizations. Static Pages deployment and an automated current leaderboard feed remain unverified/not implemented.
