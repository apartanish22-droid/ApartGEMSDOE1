#!/usr/bin/env python3
"""Recheck the existing raster against one pinned public registry witness.

This establishes a duplicate, not a complete registry clearance. Obtain the
reference Git blob described in evidence/lattice_stop.json before running.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from gems57 import load_grid
from gems57.gates import format_report
from gems57.validate import validate

CANDIDATE = ROOT / 'docs/downloads/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif'
REF_SHA = 'c12533bb980234c3a706af641d4f1d514bbbe482714b2ebcac3b10f3e72a7a3f'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def audit(reference):
    if digest(reference) != REF_SHA:
        raise ValueError('Registry witness SHA-256 mismatch')
    grid = load_grid()
    with rasterio.open(CANDIDATE) as c, rasterio.open(reference) as r:
        if c.count != 1 or r.count != 1 or (c.shape, c.crs, c.transform) != (r.shape, r.crs, r.transform):
            raise ValueError('Registry witness grid mismatch')
        a, b = c.read(1), r.read(1)
    candidate = np.isfinite(a) & (a > 0) & grid.footprint
    prior = np.isfinite(b) & (b > 0) & grid.footprint
    n = int(candidate.sum())
    if not n or not prior.any():
        raise ValueError('Empty candidate or registry witness')
    near = distance_transform_edt(~prior) <= 3.0
    count = int((near & candidate).sum())
    val = validate(CANDIDATE, grid.footprint, grid.catalogue)
    fmt = format_report(CANDIDATE, ROOT / 'data/bridge/sample_submission.tif', footprint=grid.footprint)
    return {
        'candidate': str(CANDIDATE.relative_to(ROOT)), 'candidate_sha256': digest(CANDIDATE),
        'reference': 'buffedlizard55-lab/13GEMSDOE:docs/downloads/13gems_20261001_r13-lattice-s5_v2_zerofill.tif',
        'reference_commit': '92ee6f074323f161eed837b80ec3ee5b662e26f5',
        'reference_git_blob': '5c1a159439735522659ee78969df3f34efddcdde',
        'reference_sha256': REF_SHA, 'candidate_positive_pixels': n,
        'reference_positive_pixels_in_footprint': int(prior.sum()),
        'candidate_dots_within_3px': count, 'forward_overlap': count / n,
        'overlap_limit': 0.7, 'duplicate': count / n > 0.7,
        'format_local': {'all_checks_passed': val['all_checks_passed'], 'sample_grid_matches': fmt['ok'],
                         'nan': val['n_nan'], 'infinite': val['n_infinite'],
                         'min': val['min'], 'max': val['max'], 'metadata': val['meta']},
        'scope': 'Single pinned witness; not a complete registry scan or organizer acceptance.',
        'verdict': 'negative', 'submission_slots_used': 0,
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('reference', type=Path)
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    result = audit(args.reference)
    s = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.out: args.out.write_text(s)
    print(s, end='')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
