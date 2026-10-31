# Ranked geological hypotheses · 2026-10-31

Written before the lidar candidate was implemented, as the session protocol asks.
Ranking is by expected DTI improvement per unit cost, **after** checking whether each
input is reachable from this sandbox. Only the sandbox allowlist hosts were used
(`github.com`, `api.github.com`, `codeload.github.com`, `pypi.org`, `registry.npmjs.org`,
`files.pythonhosted.org`). The `github.io` pages, DrivenData, `docs.nlr.gov`, USGS and NASA
hosts could not be reached from here, so any input that exists only on those hosts is
marked **blocked**.

Scoring language: **HOLDOUT-DTI** = our fold-honest proxy (evaluator `gems57-pooled-hide-v3`,
paired physical-cluster bootstrap 95% CI). Nothing here is a leaderboard estimate.

| Rank | Hypothesis | Layers and physical signature | Why it could find a catalogue-missing fault | Named non-fault mimic | Difference from this repo | Data gate (verified 2026-10-31) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **H-SC1 convex-crest scarp traces (lidar-only score).** | USGS 3DEP-derived 2 m lidar channels `step_max` (10 m-scale slope minus 50 m slope), `lapneg_max` (crest convexity, −LoG 6 m), gated by `coh100` (100 m coherence). Signature: convex crest with a steep step, coherent along strike. | Scarp expression survives thin alluvial cover where the USGS catalogue has no trace. The score never reads the catalogue, so withheld faults cannot shape it. | Road cut-banks, canal and channel banks, terrace risers, field edges (convex crest, steep step, low coherence). | Registry has lidar-scarp families (e.g. `lidarscarp-ridge-top2pct`, `h60-lidarscarp`, `h64-lidar-scarp-cv`). Uniqueness is measured, not assumed. | `data/external/lidar_scarp_features_u8.tif` in GEMSDOE24 mirror at ref `07345ea…`; SHA-256 `d580bb8b…` matches manifest; decoding rule from its JSON descriptor. **Reachable.** | **Implemented and holdout-tested (experiments 1 and 2).** Signal alone is weak; density drives most of the DTI. |
| 2 | **Thermal anomaly corridors from shallow probes.** | DOE GDR #1391 "2 m temperature probes" (`2m_temperature_probe_INGENIOUS_regional_data.zip`) and "well and spring" points. Signature: shallow thermal excess aligned with a structural corridor. | Upflow along an unmapped fault can warm the shallow subsurface without a surface scarp. | Shallow groundwater, vegetation, aspect and soil moisture. | Repo has geothermal-proximity and thermal families. Uniqueness is measured. | Both zips/CSVs are in the GEMSDOE24 mirror and hash-pinned in the manifest. Samples are sparse; interpolation is a large assumption. **Reachable, high method cost.** | Not implemented this session (budget). |
| 3 | **Paired-flank signed agreement.** (Prior queue item 1.) | Detrended elevation and magnetic anomaly on opposite flanks of a candidate line; the sign of the flank contrast. | A real fault gives opposing-sign flank contrasts; a topographic ridge does not. | Erosional terraces and dike contacts. | Not in repo. | Needs the official `training_features.tif` stack. It is absent from this checkout and the 6GEMSDOE bridge parts were not inspected. **Unverified.** | Not implemented. |
| 4 | **Flight-line repeatability weighting.** (Prior queue item 2.) | Original USGS GeoDAWN magnetic flight-line measurements. | Consistent anomalies across crossing lines are less likely to be survey artefacts. | Survey-line noise and levelling errors. | Not in repo. | USGS GeoDAWN page and flight-line CSVs are not reachable from this sandbox. **Blocked.** | Not validated. |
| 5 | **ASTER emissivity contrast along independent edges.** (Prior queue item 4.) | NASA ASTER GED 100 m emissivity and LST climatology. | Thermal-infrared contrast can mark altered or exposed fault zones. | Lithology change and soil type. | Not in repo. | NASA ASTER hosts are not on the allowlist and the product was not fetched. **Blocked.** | Not validated. |

## What the holdout already tells us

* The v3 holdout uses the fold draw `seed=2026`, `hide_frac=0.20`, `buffer_px=3`, with **11,360** withheld positives. The same number appears in the repo's earlier v2 runs, which is a consistency check on the fold draw.
* Random dots at the **same count** as H-SC1 score almost as well (see `evidence/holdout_h_sc1_experiment2.json`). The lidar crest signal adds only a small margin over density. Dot count is the dominant lever on this proxy.
* Canary: every decoded lidar channel alone has holdout AUC 0.47–0.58, far below the 0.90 leakage threshold. This is weak evidence on its own, not a leakage failure.

## Next actions

1. Measure uniqueness of any candidate against the full registry inventory (`scripts/check_uniqueness.py`). Do not clear uniqueness from a partial list.
2. Test hypothesis 2 only if the sparse probe data can be placed on the 100 m grid without a truth-shaped interpolation step.
3. Keep the density-matched random control as a standing comparator in every future holdout.
