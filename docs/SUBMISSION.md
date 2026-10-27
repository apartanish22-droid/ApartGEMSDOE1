# Submission workflow

## Current readiness

# **DO NOT SUBMIT.**

A synthetic research-demo GeoTIFF exists in `docs/assets/`, but it is not a competition prediction. It was generated from artificial blobs/traces, has no verified official-template origin, and has not passed holdout-DTI, leakage, or registry novelty gates. The official sample/template and authorized competition labels/features are absent. There is therefore no approved submission file available. Format validation alone cannot establish scientific quality, uniqueness, or score.

## Release gates

When authentic competition inputs and the canonical runtime are recovered:

1. Review current [competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/) and official [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/). Authenticate the template, grid, source files, licenses, and current weekly submission allowance; record SHA-256 hashes and provenance.
2. Recover the assigned method lane and shared cached feature stack, evaluator, writer, and complete registry. Do not use the current root `scripts/evaluate_holdout.py` as a substitute; its custom implementation does not meet the protocol.
3. Run the required leakage canaries and segment-buffered hide-and-recover evaluation. Preserve the evaluator version, withheld-positive count, pooled DTI, spatial 95% CI, and registry correlation/overlap. Compare both candidate surface and final dots.
4. Generate only with the canonical writer and validate the saved bytes against the official sample. Require one float32 band, exact CRS/shape/transform, predictions in [0,1] with no NaN/Inf inside the footprint, and null/NaN outside it.
5. Submit only if both format and scientific promotion gates pass and a separate weekly-slot selector authorizes the slot. On DrivenData's New submission form, choose the `.tif`, enter the run-card note (maximum 140 characters), then retain the receipt. Do not automate account actions or claim an organizer-confirmed score without that receipt.

## Format validator scope

Run the local software check with:

```bash
python scripts/validate_submission.py path/to/candidate.tif --template path/to/sample_submission.tif
```

The validator checks one band, float32 dtype, raster dimensions, CRS, affine transform, finite in-range [0,1] predictions throughout the template footprint, and null/NaN outside it. It fails closed when the template has no usable footprint or the grids differ. It prints the candidate SHA-256 for audit. The supplied sample must be the authoritative official template; a synthetic substitute proves only code behavior. The validator does not inspect scientific leakage, DTI, dot placement/uniqueness, ZIP contents, competition authentication, or leaderboard score. Requires `rasterio` and `numpy`; run synthetic regression tests with `python -m unittest discover -s tests -v`.
