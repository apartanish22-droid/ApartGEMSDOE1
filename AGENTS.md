# Repository working agreement

Read `README.md` first, then `evidence/run-card.json` and `evidence/experiment.json`.
The user charter in README is the starting point for future work.

- AP1-SNRC is a completed **negative** experiment with a mandatory duplicate STOP.
  Do not rerun it, tune placement, remove calibration controls, change its frozen
  registry, delete its record, or consume a competition slot.
- Shared evaluation/writer/cache files are byte-pinned in
  `vendor/template-pins.json`. Do not create private metric/writer forks.
- Keep research evidence and source pins immutable. Current release verification
  is `python scripts/verify_release.py`; success means a consistent **negative
  research release**, not upload authorization. Run `pytest -q` as well.
- `scripts/build_site.py` deterministically generates the current dashboard.
  Do not hand-edit generated pages; edit the builder and rebuild. A public source
  link is not a scientific measurement, receipt or data-license grant.
- Keep large data/caches/browser artifacts ignored. Exact public mirrors can be
  restored autonomously with `scripts/restore_data.py`; authentication against
  organizer bytes remains a distinct missing gate.
- Preserve concurrent work and historical evidence; do not confuse archived
  origin-zero H1 scaffolds with the measured AP1 result. Work only on the branch
  assigned by the current Arena session.
- Before any later experiment: explicit new lane/run identity, preregistered
  physical mechanism/mimic, verified data availability, spatially blocked whole
  segments, feature-alone canaries, pooled DTI + CI, and both novelty checks.
- Never upload/select a real submission in a research run. Follow the user's
  metric-label, experiment/time-budget and single-final-JSON-run-card rules.
