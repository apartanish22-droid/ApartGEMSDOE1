# ApartGEMSDOE1 — GEMS Prize Challenge submission system

**Mission:** place top of the DOE GEMS Prize Challenge leaderboard
(https://www.drivendata.org/competitions/306/competition-doe-gems/) with a
unique, validated, competition-format GeoTIFF submission. Repo branch:
`arena/f4d3d0af-apartgemsdoe1`.

> Read this README at the start of every work session. It is the project
> constitution: maximize P(Win), own the outcome, no hallucinations, verify
> line by line against official sources.

## The prompt (authoritative)

<details>
<summary>Full working prompt (read every session)</summary>

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

Leaderboard (verified live 2026-10-27): #1 xiaofanhu 0.4544 DW-Tversky
(public). The prompt's earlier figures (0.4413 / 0.3195) are stale.

Submission format: single-band GeoTIFF (.tif) or .zip containing one GeoTIFF;
must match the submission format's CRS, shape and geotransform; predicted
values must be in range [0, 1]. Unique name + note (<= 140 chars, e.g.
"clustering with k=25"). DrivenData data tab is login-gated; official training
templates were NOT downloadable from this sandbox.

Core values: Maximize P(Win); Own the Outcome.
</details>

## Repository contents

| Path | Purpose |
|------|---------|
| `scripts/download_competition_data.sh` | Fetch public mirrors + document the DrivenData login-gated files |
| `scripts/prepare_data.py` | Audit data/; record the submission template signature (CRS/shape/transform) or flag origin unverified |
| `scripts/generate_submission.py` | Generate the unique submission TIF (H1 blind-conduit lane) |
| `scripts/evaluate_holdout.py` | Hide-and-recover pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel) |
| `scripts/validate_submission.py` | Automated pre-submission gate: single-band float32, finite, [0,1], CRS EPSG:32611, 3730x3292, 100 m, template match |
| `scripts/submission_writer.py` | Write + self-validate a submission GeoTIFF with sha256 sidecar |
| `hypotheses.md` | 5 ranked candidate hypotheses (H1..H5) with layers, mimics, cost |
| `run_card.json` | Parallel-Run Protocol JSON card for the generated TIF |
| `website/` | GitHub Pages site: index.html (download), executive-summary.html (9 sites) |
| `website/assets/*.tif` | Generated unique submission TIF + JSON sidecar |
| `data/` | Competition inputs (place DrivenData login-gated files here manually) |

## How to run the pipeline

```bash
# 1. Data (DrivenData login-gated files must be copied in manually)
bash scripts/download_competition_data.sh
cp /path/to/sample_submission.tif data/   # required for template-origin verification
cp /path/to/labels.tif data/              # required for holdout-DTI

# 2. Audit data / template signature
python scripts/prepare_data.py

# 3. Generate the unique submission TIF
python scripts/generate_submission.py   # writes website/assets/*.tif + .json

# 4. Validate (no human intervention)
python scripts/validate_submission.py website/assets/<generated>.tif data/sample_submission.tif

# 5. Holdout (requires labels.tif)
python scripts/evaluate_holdout.py
```

## Current state (2026-10-27)

- Generated unique TIF: `website/assets/gemsdoe1-h1-blind-conduit-20261027T212114Z-06281cc7efb3-zeros.tif`
  - sha256: `397648e33ad640acd32c2fedcdcdefaf7815fa21bd276264bd2bcdff61af6e9a`
  - 37,654 dots, float32, EPSG:32611, 3730x3292, 100 m, values in [0,1], 0 NaN
- Validator: **format_pass = true** on every checkable gate; verdict
  `RESEARCH_ONLY_ORIGIN_UNVERIFIED` because `sample_submission.tif`
  (geotransform origin) is DrivenData login-gated and was not downloadable
  here.
- Verdict: **DOWNLOAD OK for research/inspection — DO NOT upload to
  DrivenData until `labels.tif` is present (holdout-DTI) and the template
  origin is verified.** See `run_card.json` and the website.

## Blocker

`training_features.tif`, `labels.tif`, `sample_submission.tif` require
DrivenData login (https://www.drivendata.org/competitions/306/competition-doe-gems/data/).
Dropbox mirrors return empty from this sandbox egress. Manual placement on an
authenticated machine unblocks training, holdout-DTI, and template-origin
verification.

## Official sources (verified, for manual review)

- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- About: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- Data tab (login): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Submission rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- INGENIOUS / GDR 1391: https://gdr.openei.org/submissions/1391 (DOI 10.15121/1881483)
- INGENIOUS project: https://gbcge.org/current-projects/ingenious/
- CRS EPSG:32611: https://epsg.io/32611
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
