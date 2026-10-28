# ApartGEMSDOE1 — fault-discovery research

> **DO NOT SUBMIT: no candidate has passed the current protocol.** The previous
> E3 TIFF is a research artifact, not an approved submission. A fresh check found
> 98.95% of its dots within three pixels of a registry lattice, exceeding the
> 70% cap. Its TIFF passes local format checks; that does **not** establish
> uniqueness, leaderboard performance, official acceptance, or slot approval.
> [Open the executive summary](docs/index.html) · [Submission guide](docs/executive-summary.html)

## Start here: standing project brief

At the beginning of each session, reread this brief and the original request in
session history. The goal is a scientifically defensible, genuinely new,
competition-format GeoTIFF, with an easy-to-find status, a truthful score
estimate, a short submission note, reproducible provenance, and an auditable
comparison with GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. Work
independently, cite primary sources, expose limitations, and do not spend a
weekly submission slot without a separate selector step. Maximize P(Win) and
own the outcome; do not substitute a format pass for a scientific or uniqueness
pass. Perform multiple review passes. Open/merge a PR when requested.

**Parallel-run protocol:** work only in the assigned method lane; stop if
Spearman rank correlation exceeds 0.90 against a registry raster or over 70%
of dots are within three pixels of one registry raster. Check the surface before
placement and dots afterward. Reuse cached features, the shared holdout evaluator
and submission writer. Hide whole fault components with a buffer; derive
catalogue features only from visible faults; mask visible faults pixel-exactly;
score pooled DTI (alpha 0.2, beta 0.8, triangular radius 300 m). Test each
feature alone for leakage (AUC > 0.90 is a warning). Label local results
HOLDOUT-DTI with evaluator version, positive count and CI; use
ORGANIZER-CONFIRMED only for actual organizer receipts. Never call projections
scores. Cap at three experiments or two hours. End with a JSON run card; a
negative result is a deliverable. Promote to a real slot only through a
separate selector.

The request refers to a “single method paragraph below” but does not identify
one. This session did not invent a lane or rerun the prior three-experiment
lane. It performed a non-experimental forensic check and stopped on a duplicate.
No newly generated, unique submission is available.

## Current review

The prior [E3 artifact](docs/downloads/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif)
may be downloaded **for research only**. Its SHA-256 is
`16f7101f41dd0331ac6076d6f55c906b7c1aa9fc7180258361450e9ecf87eede`.
Rechecked locally against the bridged sample: a single `float32` band, matching
CRS, shape and transform, all finite, range [0,1]. The bridged sample is a
third-party mirror, not independently authenticated against the organizer's
file. [Format receipt](evidence/format_recheck_20261028.json).

[Duplicate recheck](evidence/recheck_20261028.json) compares raw positive support
of a commit-pinned GEMSDOE24 calibration lattice with this TIFF. The old gate
ignored dense binary lattices and replaced large supports with top-K, in
contradiction to the stated protocol. That old PASS and promotion are superseded.
The raw-support rule applied literally to a near-blanket lattice is very
restrictive; do not silently exempt it. A separate protocol decision would be
needed to change its scope. The registry is incomplete, so no global uniqueness
claim is possible. Previous evidence files are historical; the 2026-10-28
recheck and [current run card](evidence/run_card_20261028.json) take precedence.

The user also reported a prior E3 submission result of 0.0525; no organizer receipt is available here, so it is not organizer-confirmed.

The previous run reported **HOLDOUT-DTI 0.052331**, evaluator
`gems57-pooled-hide-v2`, 11,360 withheld positive pixels, 95% CI
[0.037549, 0.068701]. This is a historical local estimate, not a predicted
leaderboard score, and was not rerun this session. Existing catalogue-based
static peer scores are not directly comparable to a retrained hide-and-recover
model. No organizer receipt was available to independently verify user-provided
leaderboard numbers.

### Why the GEMSDOE32 result may have been stronger

The prior [forensic audit](evidence/focus_sites_forensic_audit.json) reports that
the GEMSDOE32 B2 raster equals a thinned GEMSDOE25 raster after removing dots
within a 200 m catalogue collar. Spacing may reduce redundant prediction mass
under a distance-tolerant metric, and removing near-catalogue predictions may
reduce false-positive mass. These are plausible mechanisms, not causal proof;
the private evaluation labels, exact receipt and changed conditions are not
available. A score above the user-reported 0.2778 is not established. The user
also supplied conflicting leaderboard highs (0.3195 and 0.4413); neither is
verified as current here. The nine-site historical table is on the dashboard.

## Next-session research slate — not yet validated or assigned to a lane

These are exploratory rankings by qualitative expected usefulness, not claimed
score gains. All rely on the mirrored feature stack whose provenance still needs
verification; no additional external-data availability is assumed. Whether any
is novel relative to all other repositories has not been established.

1. **Gravity–magnetic edge offset consistency** (medium cost): compare the
   spatial offset and alignment of gravity and magnetic horizontal-gradient
   ridges at multiple scales. Buried basement boundaries may appear in potential
   fields without a mapped scarp; lithological contacts and survey artifacts are
   mimics. Unlike the implemented UDTH dip backprojection, this tests cross-layer
   displacement consistency rather than assuming one dip. First verify layer
   semantics and compare against existing edge/offset implementations.
2. **Radiometric change across gravity edges** (medium cost): compare K/Th
   contrast on both sides of a gravity gradient. A buried structural break with
   surface alteration might be missed by catalogue mapping; sedimentary contacts,
   lithology and instrument noise can mimic it. Unlike UDTH's pointwise K/Th
   corroboration, test a signed cross-edge contrast. Validate ratio availability.
3. **Scale-dependent topographic scarp asymmetry** (medium cost): compare
   paired cross-slope profiles across multiple DEM scales, looking for persistent
   breaks under fan cover. Fan channels and lake shorelines are mimics. Unlike
   the existing drainage-orthogonal scarp tensor, test profile persistence rather
   than local alignment. Verify the cached DEM channel meanings first.
4. **Conductivity contrast across geophysical contacts** (medium/high cost):
   look for conductivity gradients straddling gravity edges as a possible buried
   permeability boundary. Saline groundwater and clay layers are mimics. Unlike
   pointwise conductivity in UDTH, this uses cross-edge asymmetry. Establish
   resolution and missing-data behavior before testing.

None has an estimated leaderboard score or completed holdout. Do not run until
a lane is identified and the full-support registry policy is resolved.

## Reproduce the forensic check

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/recheck_prior_candidate.py
.venv/bin/pytest -q
```

The check uses `gh` to fetch a commit-pinned public GitHub raster if absent,
verifies its SHA-256, checks grid alignment, and computes exact Euclidean
three-pixel overlap. `bash scripts/download_competition_data.sh` restored the
prior mirrored feature stack in this sandbox, but `.cache/` is intentionally not
persisted. Some derived inputs have no pinned expected hash or independently
verified lineage. The preparation receipt now distinguishes these from pinned
mirror checks; a mirror hash alone is not an official-origin verification.

The legacy page generator is disabled because it regenerated false promotion
claims. The legacy experiment entry point is blocked until a valid lane and
selector policy are supplied. Shared registry comparisons now require complete
support and full-footprint ranks; old sampled/top-K caches fail closed.

### Primary sources and limits

* [DrivenData competition](https://www.drivendata.org/competitions/306/competition-doe-gems/),
  [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
  [submission data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/),
  [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
* [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
  provides CPU and GPU setup. Training is not demonstrated in this session.
* [USGS GeoDAWN survey](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
  [DOE GDR INGENIOUS data](https://gdr.openei.org/submissions/1391),
  [USGS 3DEP](https://www.usgs.gov/3d-elevation-program),
  [GEMS report](https://docs.nlr.gov/docs/fy26osti/96647.pdf).

Direct access to DrivenData, DOE, USGS and public GitHub Pages was not available
from this sandbox's outbound allowlist. GitHub API mirror access works, but
cannot independently verify portal receipts, organizer dataset identity, current
leaderboard or external-layer provenance. No upload or score was obtained.
