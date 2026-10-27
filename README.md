# ApartGEMSDOE1 — evidence-first GEMS fault discovery

**Start each session here.** The [executive summary](index.html) is the static landing source; GitHub Pages deployment is not verified. See [research hypotheses](hypotheses.md), [research review](docs/REVIEW_AND_PROTOCOL.md), and the [submission guide](docs/SUBMISSION.md).

## Standing project brief

Maximize the probability of a valid, scientifically defensible GEMS submission; own the outcome end to end. Review prior work before proposing experiments. Focus the historical review on GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36. Distinguish user-reported historical values, holdout measurements, and organizer receipts. Give each candidate a name and a note no longer than 140 characters. A unique filename/hash does not prove a unique raster or scientific approach.

The eventual deliverable is a single-band GeoTIFF in the exact official template grid with probabilities in [0,1]. The site must clearly state whether a file is approved to download and submit. Do not copy or cosmetically perturb an earlier submission. Do not call an inspection/demo artifact submit-ready.

### Parallel-run constraints

- Stay inside the method lane explicitly assigned to this run. **No lane paragraph was supplied in this checkout's prompt**, so no scientific candidate has been tested or promoted.
- Reuse the canonical template's cached feature stack, holdout evaluator, and submission writer. Withhold whole fault segments plus a buffer; derive catalogue-based features only from visible faults; mask visible faults pixel-exactly. Do not maintain a private fork of a shared evaluator.
- Pool DTI with alpha 0.2, beta 0.8, and a 300 m triangular kernel. Canary every feature alone; AUC >0.90 is a leakage warning. Label project scores **HOLDOUT-DTI** with evaluator version, withheld-positive count, and 95% CI, or **ORGANIZER-CONFIRMED** with submission-page receipt. A projection or unverified historical assertion is neither.
- Check the surface before point placement and final dots against registry rasters. Reject as duplicate if rank correlation >0.90 or >70% of dots fall within 3 px of a registry's dots. Missing registry pixels mean uniqueness is unknown.
- Stop after 3 experiments or 2 hours. Negative results are valid. Do not spend a weekly slot; a separate selector owns that decision.
- Validate the saved file against the official template: one float32 band, exact CRS/shape/transform, finite values in [0,1] inside the footprint, and null/NaN outside. Keep raw/private data under ignored `data/`.

## Current submission decision

# **DO NOT SUBMIT ANY TIF IN THIS REPOSITORY.**

There is a small, explicitly **synthetic research-demo** GeoTIFF at `docs/assets/gemsdoe1-h1-blind-conduit-20261027T212428Z-06281cc7efb3-zeros.tif`. Its generator uses Gaussian blobs and synthetic catalogue traces because no official raster inputs are present. It is not a prediction from GeoDAWN/DEM data, has no verified sample-template origin, no prescribed holdout-DTI, no leakage canary, and no registry correlation/overlap audit. Its hash proves byte identity only; it does not prove scientific uniqueness. Keep it for format/code inspection only; it is **not OK to submit**.

The documented competition data page is login-gated. This checkout does not contain the authorized training/label/sample rasters, cached feature-stack bytes, complete registry, or installed canonical `gems32` runtime. The sibling evaluator/writer snapshots under `research/gems32/` import a missing `src/gems32` package and are not an approved runtime. The root demo evaluator/writer must not be used as a substitute for the shared evaluator.

## Scores and GEMSDOE32

The nine-site table in the executive summary transcribes the prompt's site values as unverified user reports; there are no submission receipts in this checkout. The pinned GEMSDOE32 owner-maintained page snapshot describes the cited file as “D2.8 with B2 catalogue-apron pruning” and labels the 0.2778 result owner-reported. A plausible mechanism is thinning a dotted surface and pruning points near catalogue traces to lower false-positive mass while retaining distance-tolerant coverage near withheld faults; this is not a causal explanation. That snapshot warns that the entry was already scored and makes overlap claims that are not independently reproducible from the absent raster files. Do not resubmit it.

The user prompt's asserted global highs (0.3195 and 0.4413) conflict. Separately, the official [public leaderboard page](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) was fetched on 2026-10-27 and displayed 0.4544 at rank one. This is a dated public-leaderboard observation, **not** a receipt for our submission and not a holdout estimate. It does not calibrate a new candidate's score.

The official [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) was fetched and reviewed on 2026-10-27. It describes fault prediction, expert-labeled faults beyond the public catalogue, distance-weighted Tversky with alpha 0.2 / beta 0.8 and 300 m triangular support, and a single float32 GeoTIFF in [0,1] on the 100 m UTM 11N / EPSG:32611 grid with outside-bounds values null/NaN. This does not establish why any historical score occurred.

## Repository map

- `index.html` — static fail-closed overview; do not advertise the demo as a submit-ready download.
- `docs/executive-summary.html` — nine-site comparison.
- `docs/sites/` — pinned source-linked historical site summaries.
- `hypotheses.md` and `docs/research.md` — planning proposals only; no measured benefit is claimed.
- `run_card.json` — current demo run card with negative verdict; prior session cards remain under `evidence/` / `docs/` as historical records.
- `scripts/validate_submission.py` — automatic format validator. It requires the actual sample template and does not estimate score/novelty.
- `scripts/evaluate_holdout.py` — currently **not trusted as the canonical evaluator**; it is blocked pending installation of the shared template because its present implementation does not match the specified segment-buffered hide-and-recover protocol.
- `scripts/generate_submission.py` — retired synthetic-only generator, now fail-closed and creates nothing; the already-generated demo is retained solely for inspection.
- `research/gems32/` — read-only sibling snapshots and owner-reported evidence; not organizer-authenticated data or a runnable template.
- `data/` — ignored; do not commit competition inputs or large datasets.

## Verification and next steps

Install `requirements.txt`, then run `python -m unittest discover -s tests -v`. Tests are synthetic and validate software behavior only. `python scripts/readiness.py` should report blockers; preflight never authorizes a submission slot.

1. Recover the exact method paragraph and approved canonical template package; authenticate provenance for the feature stack, labels, sample raster, and registry.
2. Replace/disable the custom root evaluator with a wrapper around the shared implementation. Do not report a DTI until segment withholding, buffer, visible-only features, pixel-exact mask, pooled metric, evaluator version, withheld count, and spatial 95% CI are implemented correctly.
3. Fix the data preflight to distinguish metadata-only checks from real template validation; test [0,1], float32, CRS, shape, affine, nodata, NaN/Inf, and outside-footprint handling on saved bytes.
4. Preregister one in-lane hypothesis, run feature-alone leakage canaries, and compare to a reproducible matched incumbent. Stop at the experiment/time budget.
5. Test candidate surfaces and final dots against the complete registry. Only a measured holdout improvement and all release gates can authorize an artifact for the separate weekly-cap selector.
6. Keep a current-feed updater distinct from the static site. Do not label the GitHub Pages deployment or leaderboard feed live until deployment and refresh are verified.

## Sources and evidence boundary

- [Competition overview/rules](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution); a pinned README provenance record is stored in `evidence/official_source.json`.
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS/GDR 1391](https://gdr.openei.org/submissions/1391), and [NLR report PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).

The DrivenData problem description and leaderboard page were reviewed in this session. The login-gated data page, USGS/GDR/NLR contents, source raster bytes, and organizer receipts were not independently reviewed. The site is static; no automated live leaderboard feed or verified Pages deployment is provided.
