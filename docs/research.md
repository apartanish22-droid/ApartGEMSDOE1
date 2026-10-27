# Research review and protocol

## Candidate hypotheses

The current ranked candidate list, including physical signatures, missing-catalogue rationale, confounders, repository-novelty caveats, expected qualitative DTI benefit, cost, and official external-source availability checks, is maintained in [`hypotheses.md`](../hypotheses.md). That file is the single source of truth for rankings. No hypothesis is assigned or tested: the exact method lane is absent, and the canonical feature cache, evaluator/writer, competition labels, and complete raster registry are not present.

## GEMSDOE32: cautious interpretation

The pinned owner-maintained GEMSDOE32 site snapshot (`research/gems32/sites/GEMSDOE32.html`) identifies `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` as “D2.8 with B2 catalogue-apron pruning” and labels 0.2778 `OWNER-REPORTED`. No organizer receipt linking that score to the raster hash is available in this checkout. A sparse/thinned point pattern with catalogue-adjacency pruning could reduce low-credit false-positive mass while retaining distance-tolerant coverage near withheld truth. This is a plausible metric mechanism, **not a demonstrated causal explanation**.

That site snapshot says not to resubmit its already-scored file. The sibling forensic report compares different raster candidates and reports different overlap figures. The exact raster bytes are absent here; therefore none of those overlap calculations has been reproduced in this review. Do not claim the historical candidate is unique or duplicate based only on its filename or a different pair's audit.

The sibling README reports disagreement between static and visible-gated holdout evaluations of its champion. Do not extrapolate either value to the leaderboard or compare unmatched evaluator versions. Historic values remain user/owner-reported unless a receipt is supplied.

## Evaluator and artifact review

The incoming root `scripts/evaluate_holdout.py` is not a valid substitute for the specified shared implementation. Inspection found incorrect false-positive/false-negative weighting relative to the stated alpha 0.2/beta 0.8 convention, a bitwise operation on floating-point score arrays, vertical image strips instead of whole-fault-segment buffered withholding, no visible-only catalogue-feature recomputation, and no paired spatial CI against a matched incumbent. It is now fail-closed and must not emit HOLDOUT-DTI. This is a static code-review finding; the evaluator was not run to produce a score.

The incoming download script also used `eval` to build download commands, had incorrect wget output-option casing, and did not require curl HTTP failure status. The competition's authorized files remain unavailable; this script must not be treated as a reliable authenticated download mechanism. The synthetic demo TIFF is not a model prediction, and its sidecar's historical format claims do not verify the official template origin.

## Official-source review and freshness

- The official [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) was fetched/reviewed on 2026-10-27 for task, metric, kernel, and file-format statements. It does not supply this repository's score evidence.
- The official [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) was fetched on 2026-10-27; the retrieved snapshot displayed 0.4544 at rank one. This is a public-page observation, not a submission receipt for this project.
- USGS GeoDAWN, USGS 3DEP, and GDR 1391 availability/license descriptions were checked on 2026-10-27; exact tile coverage, channel availability, provenance, and competition-rule compatibility remain unverified. The links and limited source observations are documented in [`hypotheses.md`](../hypotheses.md).
- The login-gated DrivenData data page, actual sample/label rasters, canonical package, and organizer receipts were not retrieved. The mirror manifest under `research/gems32/` is explicitly owner-supplied and does not authenticate mirrored raster bytes.

The hypotheses concern fault prediction, not confirmation of geothermal resources. Static site deployment is not verified, and no automated live leaderboard feed exists.
