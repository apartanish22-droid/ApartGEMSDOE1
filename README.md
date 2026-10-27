# ApartGEMSDOE1 — evidence-first GEMS fault discovery

**Start each session here.** The [executive summary source](index.html) is the static landing page; whether GitHub Pages currently publishes it was not verified. See the [research plan](docs/research.md) and [submission workflow](docs/SUBMISSION.md) for details.

## Standing project brief

Maximize the probability of a valid, scientifically defensible GEMS submission; own the outcome end to end. Review prior work before proposing experiments. Focus the historical review on GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36. Report what is known about their strongest entries, but distinguish user-reported history from holdout measurements and organizer receipts. Give every new candidate a unique name and a <=140-character note. A unique filename/hash is not scientific uniqueness.

The final product should be a single-band GeoTIFF prediction surface, in the exact official template grid and with predictions in [0,1]. The landing page must clearly state whether a file is approved to download and submit. Do not produce a dummy or copied/perturbed prior submission. Do not call an audit artifact submit-ready.

## Mandatory experiment and release protocol

- Work only in the method lane explicitly assigned to this run. **No lane paragraph was present in the prompt supplied to this checkout**, so hypotheses remain proposals and no candidate may be placed until the lane is recovered.
- Reuse the canonical template's cached feature stack, holdout evaluator, and submission writer. Withhold whole fault segments plus a buffer; derive catalogue-based features only from visible faults; mask visible faults pixel-exactly. Do not maintain a private fork of a shared evaluator.
- Evaluate pooled DTI with alpha 0.2, beta 0.8, and a 300 m triangular kernel. Canary each feature alone; AUC >0.90 is a leakage warning until explained. Report measured results as **HOLDOUT-DTI** (evaluator version, withheld-positive count, 95% CI) or **ORGANIZER-CONFIRMED** (submission-page receipt). A projection or an unverified user-reported number is not a score in either category.
- Before placement and on final dots, compare against registry rasters. Stop/log duplicate if surface rank correlation exceeds 0.90 or >70% of candidate dots lie within 3 px of one registry's dots. Missing registries mean novelty is unknown.
- Limit work to 3 experiments or 2 hours. Negative results are valid. A separate selector—not this research run—decides whether to spend a weekly submission slot.
- Validate the saved artifact against the official sample: one float32 band, matching CRS/shape/transform, no NaN/Inf inside the footprint, values in [0,1], and null/NaN outside the footprint. Keep private/large source data under ignored `data/`; a deliberately approved submission artifact may be published.

## Current decision: no submit-ready TIF

**DO NOT SUBMIT any file from this repository.** `index.html` intentionally presents no approved download. This checkout includes pinned website/source snapshots, a negative preflight/run card, the submission-format validator, and synthetic validator tests, but it has no authorized official competition bundle, cached feature stack bytes, runnable canonical `gems32` package, registry raster set, or candidate GeoTIFF. The evidence wrappers under `research/gems32/scripts/` import `gems32` from a missing `src/` package; they are not a self-contained or verified template installation. The format validator does not estimate DTI or certify novelty.

The dataset mirror manifest is integrity-pinned but explicitly owner-supplied and **not organizer-authenticated**. Do not silently treat those mirrors as official competition data. The exact official data and sample grid, complete registry, canonical evaluator/writer plus dependencies, and assigned lane must be authenticated/recovered before a scientific run. The competition website and leaderboard are not authenticated in this environment.

### Score history and GEMSDOE32

The executive summary transcribes scores from the user prompt as **unverified user reports**, not as leaderboard receipts. The prompt gives 0.2778 for GEMSDOE32, but separately gives 0.3195 and 0.4413 as “current” highs; without a dated official snapshot or receipt, the global maximum is unresolved. The filename alone cannot explain why the reported 0.2778 occurred. Any mechanism (for example, sparse placement and catalogue-flank suppression) is a hypothesis until the exact raster, code, evaluator context, labels, and receipt are verified. A score above the reported value is possible but cannot be promised or estimated from this repository.

The official [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) was fetched and reviewed on 2026-10-27: it describes the target as fault prediction, expert-labeled test faults beyond the public fault catalogue, the weighted Tversky score and the GeoTIFF format. Its page specifies alpha 0.2, beta 0.8, a 300 m triangular kernel, probability range [0,1], single float32 band, 100 m UTM zone 11N / EPSG:32611, and null/NaN outside bounds. This official metric makes false negatives more costly than false positives, but does not establish what drove any historical entry's score.

## Project map

- `index.html` — static, fail-closed executive summary; no competition-ready file is advertised.
- `docs/sites/` — nine source-linked historical entry subpages; user-reported scores remain unverified.
- `docs/research.md` — four ranked, provisional hypothesis proposals and leakage-safe design; no numeric score projection.
- `docs/SUBMISSION.md` — competition form instructions and validator scope.
- `evidence/` — pinned site inventory, source provenance, readiness report, and current negative run card. `evidence/run_card.json` is the current card; `docs/run_card.json` is an older negative card, not authorization.
- `research/gems32/` — pinned sibling-project snapshots and prior reports for audit only, not a runnable canonical template and not organizer-confirmed evidence.
- `scripts/readiness.py` — fail-closed existence preflight; never authorizes a competition slot.
- `scripts/validate_submission.py` — saved-file geometry/dtype/range validator against a supplied template.
- `tests/` — readiness, site integrity, and synthetic GeoTIFF validation checks.

## Verification and next steps

Run `python -m pip install -r requirements.txt`, then `python -m unittest discover -s tests -v`. The format tests use synthetic rasters only and do not validate a competition candidate. Run `python scripts/readiness.py`; it should report blockers until the actual lane, canonical assets and datasets are in place.

1. Resolve the missing method lane and authenticate the official competition data/sample grid; record hashes, license and provenance.
2. Restore the complete canonical template package and dependencies, not just the sibling wrappers; recover the full raster registry and verify its provenance.
3. Audit template footprint, nodata, and whether the writer outputs probabilities or binary dots. Fix shared-tool defects in the canonical template once.
4. Pre-register one in-lane hypothesis, derive fold-local visible-only features, run leakage canaries and matched spatial holdout; stay within the budget. Do not infer score improvement from leaderboard history.
5. Only if measured holdout improves over a reproducible matched incumbent, novelty checks pass, and saved-file validation passes, generate and label an artifact for a separate weekly-cap selector.
6. Keep the landing page gated, preserve the exact TIF hash and short note, and record any organizer receipt. Do not claim that this static site is an automatically refreshed leaderboard feed.

## Source links and evidence boundary

- [Competition rules/overview](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution); its README was retrieved from the pinned commit recorded in `evidence/official_source.json`.
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS/GDR submission 1391](https://gdr.openei.org/submissions/1391), and [NLR report PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).

Only the official DrivenData problem-description page and GitHub reference-solution README provenance were directly reviewed for this session. The login-gated data page, live leaderboard, external scientific links, mirrored raster bytes, and organizer receipts were not independently verified. No automated current-leaderboard feed is implemented. See `evidence/three_pass_review.md` for the review boundary and remaining work.
