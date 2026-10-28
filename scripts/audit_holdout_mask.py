#!/usr/bin/env python3
"""Rebuild one holdout split to audit masks only; no model, score or submission."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from gems57 import load_grid
from gems57.evaluate_holdout import VERSION, implementation_hashes
from gems57.holdout import buffered_component_draw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'evidence/v3_mask_regression.json')
    args = parser.parse_args()
    grid = load_grid()
    folds, _ = buffered_component_draw(grid, seed=2026)
    hidden = folds[0]['hidden_all']
    visible = folds[0]['visible']
    removed = grid.catalogue & ~hidden & ~visible
    receipt = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'evidence_class': 'MASK-REGRESSION (not a model score)',
        'evaluator_version': VERSION,
        'split_seed': 2026,
        'withheld_positive_pixels': int(hidden.sum()),
        'buffer_removed_nonhidden_catalogue_pixels': int(removed.sum()),
        'buffer_removed_nonhidden_in_scored_regions': int(sum((f['region'] & removed).sum() for f in folds)),
        'visible_equals_score_mask_all_folds': all(np.array_equal(f['masked_known'], f['visible']) for f in folds),
        'model_score_run': False,
        'note': 'Buffer-removed catalogue pixels are not confirmed negatives; they remain unmasked in the conservative v3 proxy.',
        'implementation_sha256': implementation_hashes(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(json.dumps(receipt, indent=2, allow_nan=False))
    return 0 if receipt['visible_equals_score_mask_all_folds'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
