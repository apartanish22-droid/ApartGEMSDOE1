# ApartGEMSDOE1 — evidence-first fault discovery

**Start every session here. [Executive summary](https://apartanish22-droid.github.io/ApartGEMSDOE1/) · [Research plan](docs/research.md)**

## Standing user brief (consolidated from the repeated 2026-10-27 prompt)

Maximize P(Win) and own the outcome: build an auditable, useful geothermal fault-discovery project, not a misleading download button. Review previous work first. Focus on GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36. Explain their strongest historical submissions; provide clear file, estimate, uniqueness and submit-status tables. Generate genuinely new single-band competition GeoTIFFs, not renamed or perturbed copies. Keep predictions finite and in [0,1], matching the template CRS, shape and transform. Give each candidate a unique name and a note <=140 characters. Make approved downloads obvious in the executive summary; never label inspection artifacts submit-ready.

Use only the assigned method lane. Stop as duplicate if surface rank correlation exceeds 0.90 or final-dot overlap within 3 px exceeds 70% against any registry raster; check both stages. Reuse cached features and canonical evaluate_holdout.py/submission_writer.py; never privately fork the metric. Hide whole fault segments with a buffer; derive catalogue features from visible faults only; mask visible faults exactly; pool DTI using alpha=0.2, beta=0.8 and a 300 m triangular kernel. Test each feature alone: AUC >0.90 is a leakage alarm. Label measured numbers HOLDOUT-DTI with evaluator version, withheld count and 95% CI, or ORGANIZER-CONFIRMED with receipt. Projections are not scores; user assertions remain unverified reports, not either evidence category.

Before implementing rank 3–5 distinct physical hypotheses by expected benefit and cost; name layers, signature, missing-fault rationale, non-fault confounder and difference from existing work. Verify external official data availability before treating it as viable. Stop at three experiments or two hours. Never spend a weekly slot: separate promotion/selector step must compare against the current matched holdout best and verify the submission cap. Finish with a JSON run card, including negative outcomes. Automate validation without pretending unperformed checks passed.

Maintain official source links, evidence provenance, irregularities and limitations. Build a clean GitHub Pages executive summary with submission instructions. Review in three passes (implementation, bugs/edge cases, original requirements). Create a PR and merge after checks. Continue missing work next session. Do not solicit secrets. Do not claim a highest achievable leaderboard score from historical results.

This is a **consolidation, not a verbatim archive** of the duplicated prompt. Conflicting user-supplied leaderboard values (0.3195 and 0.4413) are not verified current standings.

## Actual checkout audit

Initial commit contained only a 15-byte README. Claims in the prompt that an existing full pipeline is ready do not apply to this checkout. No previous-session next-step files existed. No single method/lane paragraph was provided. No experiment or competition submission was performed. No new TIF was generated; no score is estimated.

Run `python -m unittest discover -s tests -v` and `python scripts/readiness.py`. Preflight exits 2 while inputs are missing; it checks existence only, not scientific readiness. The shared sources under `research/gems32/` are read-only evidence snapshots, **not an installed template**. See `evidence/` for pinned inventories and the negative run card.

## Next session

1. Resolve the missing lane before any placement experiment.
2. Integrate the canonical template with its full dependencies and pinned provenance (not just CLI wrappers); restore its cached stack and complete raster registry using its documented GitHub mirrors. Those mirrors are obtainable but are not organizer-authenticated data.
3. Validate template/label provenance; audit nodata footprint and continuous-vs-binary writer semantics. Fix shared-tool defects upstream once, not in a private evaluator.
4. Rebuild fold-local features and matched incumbent predictions; canary each feature; test at most three experiments, compute paired spatial-bootstrap CIs, then check surface and dot uniqueness against the entire registry.
5. Write a TIF only after tests permit it, validate bytes on disk, publish hash and <=140-character note. Separate selector must authorize a real slot after verifying the current cap.

Official reference solution supports CPU execution; a GPU is helpful, not a universal prerequisite. GitHub is reachable here; DrivenData, Dropbox, USGS and other hosts are outside the environment's outbound allowlist, so their live content, login status, leaderboard and weekly cap were not checked.

## Parallel-session integration

During PR merge, `main` advanced through PR #1. Its format-only `scripts/validate_submission.py`, requirements and Markdown submission guides were retained. `docs/run_card.json` is that session's historical negative card; `evidence/run_card.json` is this session's card. Neither is a submission authorization. The retained validator checks the template footprint only; it does not certify whole-grid finiteness, registry uniqueness or scientific performance. This session did not execute it against a real competition TIF.
