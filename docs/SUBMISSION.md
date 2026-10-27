# Submission workflow

## Current readiness

**No approved submission file is available. Do not submit an unverified file.** A parallel synthetic demo exists but fails the pinned mirrored grid; it is for research only. The mirror is not organizer-authenticated. See the [current executive summary](executive-summary.html) and [demo validation receipt](../evidence/parallel_demo_audit.json). Format validation alone does not establish scientific quality, uniqueness, or score.

## When a candidate and official template exist

1. Review current [competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/) and the official [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/). Confirm the acceptable submission format, template geometry, and current weekly submission allowance.
2. Run the shared holdout evaluator on the candidate before selecting a real submission slot. Preserve evaluator version, withheld-positive count, pooled DTI, 95% CI, leakage canary results, and registry correlation/overlap.
3. Generate with the shared submission writer; validate against the official template with the included command:

   ```bash
   python scripts/validate_submission.py path/to/candidate.tif --template path/to/sample_submission.tif
   ```

4. Submit the resulting single-band GeoTIFF only if both the format gate and scientific promotion gates pass. On the competition's New submission form, choose the `.tif`, enter the short note from the run card (maximum 140 characters), and review the receipt. Do not automate account actions or claim an organizer-confirmed score until the receipt reports it.

## Validator scope

The script checks one float32 band, dimensions, CRS, affine transform, finite unmasked values in the supplied template's valid footprint, range [0,1], and null outside that footprint. It prints the candidate's SHA-256 and fails closed when a template is absent or the grid differs. The official null-outside wording versus a previous portal range rejection remains unresolved; neither local format success nor the supplied template's provenance is organizer acceptance. It does not inspect scientific leakage, DTI, dot placement/uniqueness, zip contents, competition authentication, or leaderboard score.
