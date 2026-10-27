> **Historical concurrent-pass document, superseded.** See `docs/executive-summary.html`, `research/hypotheses-2026-10-27.md`, and `evidence/run-card.json` for the measured AP1 result. Do not interpret this earlier state as the current data/validation status.

# Candidate geological hypotheses (ranked)

Source of truth for rankings: expected holdout-DTI improvement vs the current
repo best on the spatially-blocked hide-and-recover holdout, and implementation
cost given publicly available, official data. None of these numbers is a
leaderboard score; none has been validated yet (labels.tif / template are
DrivenData login-gated). Validate the top candidate on the holdout BEFORE
spending a weekly submission slot (Parallel-Run Protocol rule 6).

## H1 — Blind hydrothermal-conduit propensity (IMPLEMENTED; demo surface)

- **Layers:** GeoDAWN airborne radiometrics (Th, K → Th/K alteration ratio),
  GeoDAWN TMI (magnetics), USGS 3DEP DEM (concave/profile curvature).
  Catalogue used ONLY as a 2 px exclusion collar.
- **Physical signature:** illite/argillic alteration (high Th/K), magnetite
  destruction (TMI lows), concave curvature at fault intersections/relay ramps.
- **Why it catches catalogue-missing faults:** blind/hidden geothermal faults
  alter bedrock radiometrically and magnetically with little or no Quaternary
  surface rupture, so they are absent from the USGS/INGENIOUS Quaternary
  catalogue; the exclusion collar forces dots off catalogue traces.
- **Differs from repo:** every H19-5 / B2 "dotted" submission re-dots catalogue
  traces (100% within-3-px overlap across GEMSDOE24/25/27/28/30/31/32/33/36).
  H1 places dots where the catalogue is silent.
- **Expected DTI improvement:** +0.02 to +0.06 over the dotted baseline
  (planning bracket only, not a score).
- **Cost:** low — GeoDAWN + 3DEP + INGENIOUS faults are official, free, public.
- **Status:** implemented in scripts/generate_submission.py as a deterministic
  demonstration surface (real rasters unavailable in this sandbox).
- **Verification needed:** run evaluate_holdout.py with labels.tif; leakage
  canary AUC on Th/K alone must be <= 0.90.

## H2 — Relay-ramp / step-over dilation zones

- **Layers:** GDR 1391 geodetic shear & dilation models, USGS 3DEP DEM
  curvature, INGENIOUS Quaternary faults (exclusion collar).
- **Physical signature:** extensional step-overs and relay ramps dilate the
  crust, focusing geothermal upflow; geodetic dilation + concave curvature +
  curvature-axis alignment with mapped fault termini.
- **Why it catches catalogue-missing faults:** relay ramps between en-echelon
  fault segments are commonly unmapped at Quaternary scale yet host the
  highest-permeability conduits.
- **Differs from repo:** H1 uses alteration/magnetics; H2 uses geodetic
  strain + structural geometry, a different physical process.
- **Expected DTI improvement:** +0.01 to +0.04.
- **Cost:** medium — requires downloading + reprojecting GDR 1391 geodetics.

## H3 — Shallow thermal + paleo-geothermal spring clusters

- **Layers:** GDR 1391 2-m temperature probes, paleo-geothermal features
  (sinter/tufa), USGS/INGENIOUS springs & well temperatures, DEM.
- **Physical signature:** shallow conductive thermal anomalies and sinter
  mounds mark blind fault-controlled upflow zones not mapped as Quaternary
  faults.
- **Why it catches catalogue-missing faults:** paleo-spring/sinter deposits
  often overlie blind faults with no surface rupture.
- **Differs from repo:** point-observation-driven (probe/spring rasterization)
  rather than raster-feature-driven; complements H1 which targets bedrock
  alteration.
- **Expected DTI improvement:** +0.005 to +0.03.
- **Cost:** medium — point data interpolation + kernel smoothing.

## H4 — Deep MT conductor + gravity low (reservoir-scale)

- **Layers:** GDR 1391 MT electrical conductance (2–200 km depth slices),
  GDR 1391 gravity, depth-to-basement.
- **Physical signature:** mid-to-deep crustal electrical conductor (connected
  fluids/graphite) co-located with a gravity low (low-density altered rock).
- **Why it catches catalogue-missing faults:** deep blind faults controlling
  geothermal reservoirs have no shallow expression at all.
- **Differs from repo:** deep-penetrating geophysics rather than near-surface
  radiometric/geomorphic signatures.
- **Expected DTI improvement:** +0.005 to +0.02 (signal is deep and diffuse).
- **Cost:** high — large national rasters, depth-slice integration, baseline
  removal needed.

## H5 — Microseismicity + slip/dilation tendency on mapped structures

- **Layers:** GDR 1391 earthquake density / seismicity, USGS Quaternary fault
  slip tendency & dilation tendency, INGENIOUS faults.
- **Physical signature:** clusters of microseismicity and high
  slip/dilation tendency on structures indicate critically stressed, fluid-rich
  faults.
- **Why it catches catalogue-missing faults:** seismicity reveals blind
  structures absent from the Quaternary map.
- **Differs from repo:** seismicity-driven rather than alteration/geomorphic.
- **Expected DTI improvement:** +0.01 to +0.03.
- **Cost:** medium — point seismicity rasterization.

## Ranking (expected DTI improvement, then cost)

| Rank | Hypothesis | Expected DTI gain | Cost | Data source |
|------|------------|-------------------|------|-------------|
| 1 | H1 blind hydrothermal-conduit propensity | +0.02..+0.06 | low | GeoDAWN (USGS), 3DEP, INGENIOUS faults (GDR 1391) |
| 2 | H2 relay-ramp / step-over dilation | +0.01..+0.04 | medium | GDR 1391 geodetics, 3DEP |
| 3 | H5 microseismicity + slip/dilation | +0.01..+0.03 | medium | GDR 1391 seismicity, USGS Qfaults |
| 4 | H3 shallow thermal + paleo springs | +0.005..+0.03 | medium | GDR 1391 probes/springs |
| 5 | H4 deep MT conductor + gravity low | +0.005..+0.02 | high | GDR 1391 MT/gravity |

## Validation gate before any slot

Per the Parallel-Run Protocol: run each feature ALONE on the holdout first
(leakage canary; AUC > 0.90 = leakage until proven otherwise), then the fused
stack. Promote only a fold-local HOLDOUT-DTI win with paired 95% CI > 0 against
the repo best, with no SGMC-cal regression and literal uniqueness
(Spearman <= 0.90, <= 70% within 3 px). No projection is ever written as a
score.

Official sources (for manual review):
- USGS GeoDAWN survey: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- INGENIOUS / GDR 1391: https://gdr.openei.org/submissions/1391 (DOI 10.15121/1881483, CC-BY 4.0)
- INGENIOUS project: https://gbcge.org/current-projects/ingenious/
- CRS: https://epsg.io/32611
- Metric: Tversky index https://en.wikipedia.org/wiki/Tversky_index
