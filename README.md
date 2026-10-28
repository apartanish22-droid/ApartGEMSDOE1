# ApartGEMSDOE1 — GEMS competition research

> **STOP — no new TIFF is cleared for submission.** The existing historical TIFF is locally format-valid, but the literal parallel-run uniqueness rule fails. It is also identified in the user's history as already submitted. Do not spend a slot on it. See the [executive summary](docs/executive-summary.html) and [measured stop evidence](evidence/lattice_stop.json) and [current run card](evidence/review_run_card.json).

## Standing project brief — read first

Maximize the probability of winning and own the outcome. Build a reproducible, source-linked, autonomous research and submission workflow for the DOE GEMS competition, not unsupported score promises. Compare the historical leaders at GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36; seek a genuinely new, single-band GeoTIFF with matching competition grid and values in [0,1]. Present format, leakage, uniqueness, holdout and selection status clearly on a simple GitHub Pages site. Scores must be evidence-labelled; a holdout is not a leaderboard projection. Use the official competition sources and record uncertainties. No automatic portal upload or slot use without a separate selector step. Retain negative results. The full conversation prompt has extensive prior submission names and links; this is a consolidated standing brief, not a verbatim copy.

**Parallel-run protocol:** stay in the assigned single-method lane; compare surface and final dots against every registry raster; stop if rank correlation exceeds 0.90 or more than 70% of dots lie within 3 px of one registry raster. Reuse the shared feature stack, `gems57.evaluate_holdout` and `gems57.submission_writer`. Hide entire fault segments with a buffer; derive catalogue features from visible faults only and mask visible faults pixel-exactly; pool DTI with alpha 0.2, beta 0.8 and 300 m triangular kernel. Test features individually for leakage (AUC above 0.90 requires investigation). Label holdout DTI with evaluator, positives and CI; label organizer scores only when copied from a submission receipt. End with a JSON run card. Stop after 3 experiments or 2 hours; a separate selector controls weekly slot promotion.

## Review and outcome

The existing `UDTH-Submod E3` research raster (`docs/downloads/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif`, SHA-256 `16f7101f41dd0331ac6076d6f55c906b7c1aa9fc7180258361450e9ecf87eede`) has 38,095 of 38,500 positive pixels within 3 pixels of the pinned 13GEMSDOE lattice (98.948%). This exceeds the literal 70% limit. A blanket/dense-raster exemption in the previous private gate was not authorized. The old sampled-index gate and legacy promotion pipeline are disabled; shared `gems57.uniqueness` remains the gate. The prior claims of release approval, uniqueness, unqualified provenance and causal proof are superseded. Independent concurrent review artifacts are retained in [format recheck](evidence/format_recheck_20261028.json) and [review card](evidence/run_card_20261028_review.json). Historical evidence remains as historical material, not a current approval.

The local validator found no NaNs or infinities, range [0,1], and single-band grid/CRS/transform matching the local bridge sample. This does not verify the bridge sample's organizer origin or promise portal acceptance. The historical E3 result was **HOLDOUT-DTI 0.052331**, evaluator `gems57-pooled-hide-v2`, 11,360 withheld positives, 95% CI [0.037549, 0.068701]; not reproduced this session and not an expected leaderboard score. The user reports an existing live score for this submission; no organizer receipt is present, so it is not organizer-confirmed.

Previous audit claims GEMSDOE32's historical raster is a spaced and near-catalogue-pruned descendant of H19-5, potentially reducing redundant false-positive mass under the kernel; private truth is unavailable and this does not establish causation or a higher future score. The reported site high of 0.2778 is user-reported, not receipt-verified. The claimed leaderboard values in the prompt differ and cannot be verified from this environment.

## Reproduce the stop

Dependencies: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`. Fetch the pinned public witness via GitHub API, not an unverified third-party URL:

```bash
mkdir -p .cache/audit
gh api repos/buffedlizard55-lab/13GEMSDOE/git/blobs/5c1a159439735522659ee78969df3f34efddcdde --jq .content | base64 -d > .cache/audit/lattice.tif
.venv/bin/python scripts/audit_lattice_stop.py .cache/audit/lattice.tif
.venv/bin/pytest -q
```

This is a one-witness negative test, not a complete registry scan. The formerly generated site builder, registry audit and pipeline intentionally fail closed to avoid reissuing the superseded verdict. For future work, use `scripts/validate_submission.py --registry-index <complete-index> <tif>` with the shared literal gate; this checks neither pre-placement surface nor holdout nor weekly slot selection.

## Next work and limits

1. Resolve the **literal registry saturation conflict**: the public lattice makes the 70% rule difficult to satisfy for essentially any broadly distributed dot set; do not reinterpret the instruction silently. Establish an agreed inventory and pre-placement semantics before restarting the lane.
2. Restore the large cached feature stack and immutable, complete, hash-checked registry. This checkout lacks those caches; `data/bridge` is a public mirror, not authenticated organizer provenance. The `data/official` files in this repository are also mirror copies despite their path.
3. Rebuild the released pipeline around the shared full-inventory gate, ensuring surface check occurs *before* placement, visible-only catalogue features and feature canaries, a matched fold-local incumbent, and an independent slot selector. No experiment was run in this review. Fixed the shared `metric.marginal_accept` denominator for non-complementary alpha/beta (the specified 0.2/0.8 behavior is unchanged); the historical holdout was not recalculated.
4. The historical proposal list in `evidence/preregistration_hypotheses.json` includes unverified numerical gain predictions and assumptions; treat as ideas only. New hypotheses, detailed in [research notes](docs/research-notes.md), are untested and cannot be ranked by demonstrated DTI.
5. Verify licensing/provenance from official sources and authenticate the official sample and training inputs before release. [Competition description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) · [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [GDR INGENIOUS](https://gdr.openei.org/submissions/1391) · [USGS 3DEP](https://www.usgs.gov/3d-elevation-program).

---

## 2026-10-28 (this session) — H-APART-2 Concordance Lane: NEGATIVE, lane closed

New lane tested end-to-end (`scripts/run_concordance_hybrid.py`, `evidence/run_card_cah.json`, `evidence/concordance_holdout.json`; ≤3 experiments, leakage canary sym-AUC 0.5699 ≤ 0.90 PASS):

| Candidate | HOLDOUT-DTI static (`gems57-pooled-hide-v2`, 11,360 withheld px) | Uniqueness vs GEMSDOE32 B2 | Verdict |
| :--- | :--- | :--- | :--- |
| EXP1 Concordance-Anchored Hybrid 38,500 | 0.0043 [0.0035, 0.0051] | **89.06% 3-px overlap (>70% cap)**, ρ=0.865 | ❌ NEGATIVE — duplicate, no file written |
| EXP2 hybrid, own positions only | 0.0007 [0.0004, 0.0011] | not promoted | ❌ NEGATIVE |
| EXP3 B2 concordance-prune 30k | 0.0041 [0.0033, 0.0050] | B2-derived | ❌ NEGATIVE |
| Controls (static): GEMSDOE32 B2 / historical UDTH raster | 0.0042 / 0.0012 | — | controls |

**Irregularities flagged:** (1) concordance ranking mechanically duplicates the proven lineage (89%) — concordance with B2 cannot pass the ≤70% cap at 38.5k budget; lane closed. (2) The historical raster's 0.0523 headline is an *out-of-fold* HOLDOUT-DTI; static scoring of the shipped raster on the same evaluator is 0.0012 — not interchangeable, and no live-score projection or "beats 0.2778" claim is supported. Consistent with the STOP banner above: **no file is cleared for submission this session**; promotion remains a separate selector step. Next ranked untried hypotheses: N1 3D Euler deconvolution contacts (GeoDAWN, sciencebase.gov/catalog/item/61955dcad34eb622f6908d6c), N2 Lahontan bench subtraction (USGS 3DEP + MF-2323), N3 InSAR/geodetic strain localisation, N4 relocated microseismicity lineation (USGS earthquake catalogue).
