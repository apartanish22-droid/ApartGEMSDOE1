# Preregistered hypothesis slate — 2026-10-27

Written before implementing or measuring any new candidate. The initial checkout contains only `README.md`; consequently none of these methods has been implemented **in this repository**. Related methods exist in peers: this is not a claim of global scientific novelty. Peer filenames, hypotheses and source pins were inspected before this slate. Numerical DTI gains cannot responsibly be forecast from the heterogeneous historical score claims; the ranking below is qualitative scientific judgment, not a score prediction.

## Lane irregularity and budget

The brief refers to a “single method paragraph below” but supplies no unique lane assignment. Provisional research lane **AP1-SNRC: scarp-normal radiometric contrast** is explicitly recorded here. Missing lane assignment blocks promotion. No competition upload or slot selection is authorized. Up to three fixed contrast-strength arms (exponents 0.5, 1, 2), one mechanism only; at most two hours. **A duplicate at either stage stops the lane immediately; do not try the other arms or alter the registry/budget to evade a failure.** The first arm uses 20,000 full-region dots with deterministic 3-pixel separation. This is a fixed precision-focused emission budget, not a claimed optimum.

## Ranked candidates

| Rank | Hypothesis | Expected improvement (judgment, not measured DTI) | Implementation cost | Data feasibility |
|---|---|---|---|---|
| 1 | AP1-SNRC: scarp-normal radiometric contrast | Moderate plausibility as a precision filter; high uncertainty; may reduce recall | Low–medium, CPU | Restored cached GeoDAWN radiometrics + LiDAR + RTP; input integrity verified, mirror provenance not independently authenticated |
| 2 | AP1-CPR: opposite-curvature scarplet pairs | Moderate plausibility for weak scarps, vulnerable to erosional mimics | Low, CPU | Cached LiDAR negative/positive Laplacian, step, strike and coherence channels |
| 3 | AP1-EOD: paired gravity/magnetic edge-offset dispersion | Low–moderate plausibility for concealed contacts; lower localization precision | Medium, CPU | Restored competition isostatic gravity and RTP; no new external data |
| 4 | AP1-DCF: drainage-capture elbow chains with a scarp-profile veto | Potentially useful independent geometry; currently not runnable | High: hydrologic conditioning and raw DEM tile acquisition | CONDITIONAL, NOT VIABLE HERE: needs unmodified USGS 3DEP 1 m DEM tiles, not detrended elevation or aggregated scarp channels |

### 1. AP1-SNRC — executed first

**Specific layers:** cached `geodawn_rad_u8.tif` K and Th (bands 1 and 2); `lidar_scarp_features_u8.tif` excess slope, step, negative/positive Laplacian, relief, coherence and strike (bands 1, 3, 4, 5, 9, 10, 11; band 12 is availability); competition RTP (band 2). Do not use ambiguous `tc`, earthquake aliases, or the disputed basement/conductive-base description.

**Physical signature:** use local, label-free rank contrast in K relative to Th, then measure its absolute difference across the LiDAR strike normal at ±300 m. Corroborate this cross-profile contrast with a LiDAR step and paired signed-curvature amplitudes; use RTP gradient magnitude only as a soft corroborator. Fixed Gaussian smoothing scales: radiometric background 1.2 km, RTP smoothing 100 m. Normalize descriptors by finite in-footprint percentiles without labels. These are quantized radiometric descriptors: never interpret byte ratios or byte differences as physical K/Th concentrations. Exclude unavailable LiDAR and source-boundary neighborhoods independently of fault labels.

**Why it could recover missing faults:** a short scarp and its cross-scarp material/alteration contrast may survive where regional mapping omitted a subtle break. No known-fault proximity, trace, predicted raster or holdout truth enters the field. This is a hypothesis, not evidence that all such features are faults or thermal conduits. It will miss deeply buried faults without a surface expression.

**Distinctness:** the empty local repo has no detector. Peer GEMSDOE32 H38-G2 and H44-3 already discuss lithology-deconfounded potassic alteration; many peers already use LiDAR amplitudes. The proposed distinction is the *spatially paired scarp-normal contrast*, not a novel claim about potassium or magnetic gradients. Pixel-level registry comparison decides whether this distinction is sufficient. No champion raster is a feature or output parent.

**Named non-fault mimics:** alluvial provenance/lithologic contacts, fluvial terrace risers, paleolake shorelines and mine cuts. Potassic alteration can accompany mineralization without an active fault or geothermal reservoir.

**Validation:** reuse GEMSDOE24 `SegmentHoldout` and exact DTI implementation, whole connected fault components hidden with a 1.5 km collar; four spatial quadrants; visible faults masked pixel-exactly. Connected components are a raster proxy for segments, not authenticated trace IDs. Run each source/transformed feature independently through the two-polarity value/missingness AUC canary; any extremity above 0.90 stops the lane. Pooled DTI uses alpha 0.2, beta 0.8, 300 m triangular support; conditional 95% spatial block bootstrap. Compare against a fold-safe LiDAR-only matched-budget ablation, not against precomputed historical maps that saw all labels. A local ablation win is insufficient to establish a portfolio holdout best. Missing comparable current-best predictions is a separate promotion blocker.

### 2. AP1-CPR — proposed, not executed in this lane

**Layers/signature:** cached LiDAR positive/negative Laplacian amplitudes and strike; paired oppositely signed extrema separated across strike, with a coherent step between them rather than simply selecting the largest slope. **Missing-fault rationale:** subtle short scarplets may be represented by curvature pairing when maximum-slope thresholds omit them. **Difference:** tests profile geometry instead of the repeated solid/dotted H19-5 family; related scarp-profile suggestions already exist in GEMSDOE24. **Mimics:** channel banks, terraces, road cuts. No raw sub-100 m profile can be recovered from this aggregate cache, so the interpretation must stay at the grid scale.

### 3. AP1-EOD — proposed, not executed in this lane

**Layers/signature:** competition RTP and isostatic gravity anomaly (bands 2 and 13), Gaussian-derivative edges at several fixed scales; consistent cross-normal edge displacements rather than their pointwise product. **Missing-fault rationale:** a buried density/magnetization boundary may persist without a scarp; jointly constrained offsets may improve localization. **Difference:** displacement/dispersion of paired edge locations, not a new name for a scalar tilt or generic gradient fusion. Peer cross-gradient/Euler/continuation families are related; novelty is unproven. **Mimic:** nonfaulted intrusive or volcanic contacts. Both are potential-field transforms, not statistically independent proof of a fault.

### 4. AP1-DCF — conditional only, no experiment

**Layers/signature:** unmodified bare-earth 3DEP elevation, flow-connected elbows and along-channel concavity change, with LiDAR-profile checks. **Missing-fault rationale:** drainage deflection may reveal low-relief scarps omitted by regional maps. **Difference:** connected drainage geometry, not independent pixel gradients. **Mimics:** lithologic control, fan avulsion and human drainage. **Required official free source:** USGS 3DEP, https://www.usgs.gov/3d-elevation-program/data-tools; the official GeoDAWN page confirms coordinated 3DEP coverage. The cached 100 m summaries and detrended elevation are insufficient for hydrologically sound flow routing. The project has no verified raw-tile download here; this candidate is not labeled viable or ready until specific tile URLs/bytes and coverage are checked. Do not substitute synthetic elevations.

## Evidence boundary and scientific sources

- Official competition problem, metric and format: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (both chunks read). The target is **faults indicative of geothermal resources**, not a geothermal-vent label set.
- USGS GeoDAWN data release, DOI 10.5066/P93LGLVQ: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (read). Magnetic data inform subsurface structure; radiometrics inform shallow geology/soil. Acquisition blocks, line direction and terrain clearance can mimic structures.
- GDR INGENIOUS compilation, DOI 10.15121/1881483, CC BY 4.0: https://gdr.openei.org/submissions/1391 (read; public download links listed). Public metadata availability does not authenticate the local mirrored bytes against the organizer download.
- USGS gamma-ray alteration study: https://www.usgs.gov/publications/gamma-ray-spectrometer-studies-hydro-thermally-altered-rocks. Its altered-rock potassium result concerns particular mineral deposits; it does not prove the proposed GeoDAWN fault detector.
- USGS geophysical caution/context: https://www.usgs.gov/news/state-news-release/bipartisan-infrastructure-law-helps-remap-nevada-critical-minerals. Radiometrics are shallow-composition measurements; magnetic edges can also be intrusions.
- DOE-hosted structural literature: https://www.osti.gov/servlets/purl/1110517 and https://www.osti.gov/servlets/purl/1724082. Structural complexity is relevant to geothermal permeability but does not guarantee a high challenge DTI.

The hypotheses are proposed interpretations. Only subsequently recorded holdout results may be labeled HOLDOUT-DTI. No projected leaderboard score is a measured score, and no historical owner report is ORGANIZER-CONFIRMED without an exact submission-page receipt.
