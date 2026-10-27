# Review and protocol status

**Review date:** 2026-10-27 UTC. **Repository:** `apartanish22-droid/ApartGEMSDOE1`, working branch `arena/b1713cdf-apartgemsdoe1`. This review reconciles the branch with `origin/main`; it does not claim an experiment, competition upload, or submission receipt.

## Executive findings

| Area | Verified local state | Consequence |
|---|---|---|
| Data and template | No authorized competition sample, labels, feature rasters, or official origin are available in `data/`. | No competition-grid validation or holdout result can be produced. |
| Demo artifact | One synthetic TIFF is retained in `docs/assets/`; its checksum is recorded in `run_card.json`. It is artificial data, not a prediction. | Inspection-only download, never submit; uniqueness remains unknown. |
| Shared runtime | The canonical `gems32` package, feature-stack bytes, complete registry, lane, and shared evaluator/writer are absent. | Root demo evaluator and writer are fail-closed; no substitute scoring or writing. |
| Current evaluator | The incoming custom implementation did not perform whole-fault-segment buffered withholding or visible-only catalogue-feature recomputation and had incorrect metric/array operations. | It is disabled. This is a static code-review conclusion, not a runtime score result. |
| Format validator | The root validator requires a candidate and authoritative sample; it checks serialized grid/dtype/band/range/footprint and reports the hash. | It proves format only when supplied an authentic template; it never proves scientific validity or eligibility. |
| Competition scores | User-reported site scores have no receipts in this checkout. The official public leaderboard was fetched 2026-10-27 and displayed 0.4544 at rank one. | Leaderboard observation is not this project's score, holdout, or receipt. |
| Deployment | Static HTML exists; Pages settings/deployment were not verified. | Do not claim the site is published or auto-refreshing. |

## Nine-site history and GEMSDOE32

The [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) records the requested GEMSDOE24/25/27/28/30/31/32/33/36 values as user-reported, and marks all new score estimates and registry uniqueness as unknown. The highest value in that supplied nine-site history is GEMSDOE32's 0.2778, still unverified without a receipt.

A pinned owner-maintained site snapshot describes the cited GEMSDOE32 entry as D2.8 with B2 catalogue-apron pruning. Reduced prediction mass near already catalogued faults could plausibly reduce low-credit false positives while retaining distance-tolerant coverage; that is a possible mechanism, not a measured causal explanation. The exact raster bytes are absent, and the sibling audit snapshots compare different candidate pairs with differing reported overlap. Do not resubmit the entry or treat any overlap assertion as independently reproduced here.

## Ranked hypothesis plan

[`hypotheses.md`](../hypotheses.md) is the single ranked list of four proposals, with data channels, physical signatures, missing-catalogue rationale, repository-novelty caveats, confounders, qualitative expected DTI benefit, implementation cost, and checked official source availability. No numerical gain is projected. The assigned lane is not in the prompt/context supplied to this checkout; none is authorized to run until recovered.

USGS source checks on 2026-10-27 found public GeoDAWN magnetic/radiometric products, USGS 3DEP products advertised as free/public domain (with tile-dependent coverage), and the GDR 1391 Great Basin compilation under CC BY 4.0. Exact raster coverage, bands, overlap, provenance, and competition-rule compatibility are not yet checked. See links in the ranked plan.

## Three-pass review and remaining work

1. **Evidence/site pass:** reconcile the nine requested sites, keep supplied scores separate from organizer receipts, and replace blanket duplicate assertions with `UNKNOWN` where raster bytes/registries are missing.
2. **Code/protocol pass:** disable the invalid incoming evaluator, unsafe mirror-download implementation, auto-running synthetic generator, and noncanonical writer. Make data readiness distinguish file presence from official provenance and actual template-based validation.
3. **Release/site pass:** ensure every public page labels the demo `DO NOT SUBMIT`, remove unsupported numeric gain forecasts, make the format validator fail closed without a sample, and state all blockers and non-promotion decisions clearly.

Next required steps, in order:

1. Recover the assigned method lane, authenticated official package, actual sample grid, labels/features, complete registry, and canonical shared runtime. Record provenance and hashes without committing restricted or large data.
2. Audit canonical source/version and fix any shared-tool defect upstream or in the canonical template, not as a private evaluator fork.
3. Preregister the first in-lane hypothesis. Withhold whole fault segments plus a buffer, rebuild catalogue features using visible faults only, mask visible faults pixel-exactly, run feature-alone leakage canaries, and use pooled DTI alpha 0.2/beta 0.8 with a 300 m triangular kernel.
4. Compare candidate surfaces before placement and final dots against the complete registry; stop on correlation >0.90 or >70% within 3 px.
5. Respect the three-experiment/two-hour budget. Report HOLDOUT-DTI with evaluator version, withheld-positive count, and spatial 95% CI, or report no result. No weekly slot is spent by research.
6. Validate saved bytes against the official sample and route only a promoted, unique candidate to a separate weekly-cap selector. Keep the visible DO NOT SUBMIT banner until every gate passes.

## Sources and evidence limits

- [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) were fetched/reviewed 2026-10-27.
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services), and [DOE/INL GDR 1391](https://gdr.openei.org/submissions/1391) were checked for data-description/access claims on 2026-10-27. They do not authenticate competition inputs or guarantee coverage.
- The DrivenData login-gated data page, actual competition rasters/template, canonical package, and organizer receipts were not retrieved. The `research/gems32/` mirrors are owner-supplied and are not organizer-authenticated.

No score, competition receipt, final candidate, or slot selection was produced in this review.
