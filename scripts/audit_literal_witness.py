#!/usr/bin/env python3
"""Reproduce the mandatory stop against one pinned registry witness.

This is a diagnostic, not a full uniqueness clearance. It performs no model
experiment and cannot authorize a competition slot. Fetches use gh, not
stored credentials; the public blob and SHA-256 are pinned below.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import numpy as np
import rasterio
from gems57 import load_grid
from gems57.uniqueness import compare_array_to_registry, saturation_certificate
from gems57.validate import validate

REPO = 'buffedlizard55-lab/13GEMSDOE'
COMMIT = '92ee6f074323f161eed837b80ec3ee5b662e26f5'
REMOTE = 'docs/downloads/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif'
WITNESS_SHA256 = 'b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2'
CANDIDATE = ROOT / 'docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif'
DEFAULT_WITNESS = ROOT / '.cache/independent_audit/13gems-lattice.tif'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ensure_witness(path: Path) -> None:
    if path.is_file() and sha256(path.read_bytes()) == WITNESS_SHA256:
        return
    endpoint = f'repos/{REPO}/contents/{REMOTE}?ref={COMMIT}'
    p = subprocess.run(['gh', 'api', endpoint, '-H', 'Accept: application/vnd.github.raw+json'],
                       capture_output=True, check=True, timeout=90)
    if sha256(p.stdout) != WITNESS_SHA256:
        raise ValueError('Pinned witness SHA-256 mismatch; refusing to audit')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.partial')
    temporary.write_bytes(p.stdout)
    temporary.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--witness', type=Path, default=DEFAULT_WITNESS)
    ap.add_argument('--candidate', type=Path, default=CANDIDATE)
    ap.add_argument('--out', type=Path, default=ROOT / 'evidence/literal_witness_audit.json')
    args = ap.parse_args()
    ensure_witness(args.witness)
    grid = load_grid()
    receipt = validate(args.candidate, footprint=grid.footprint, catalogue=grid.catalogue)
    if args.candidate.resolve().is_relative_to(ROOT):
        receipt['file'] = str(args.candidate.resolve().relative_to(ROOT))
    with rasterio.open(args.candidate) as ds:
        candidate = ds.read(1).astype(np.float32)
    # The one-file index can prove a duplicate, never universal uniqueness.
    index = {'rasters': [{'repo_first': REPO, 'sources': [REMOTE],
                           'cache_file': str(args.witness.resolve()), 'sha256': WITNESS_SHA256}],
             'complete_accessible_scan': False,
             'errors': ['This witness-only inventory is not a complete registry.']}
    report = compare_array_to_registry(candidate, index, grid.footprint,
        file_sha256=receipt['sha256'], include_reverse=False,
        expected_grid=(grid.shape, grid.crs, grid.transform))
    saturation = saturation_certificate(args.witness, grid.footprint, grid.catalogue,
                                        expected_grid=(grid.shape, grid.crs, grid.transform))
    dots = int(((candidate > 0) & grid.footprint).sum())
    uncovered = saturation['uncovered_allowed_pixels']
    # N - U <= 0.7N is necessary to pass. Exact integer arithmetic avoids
    # floating point rounding at the strict >0.70 decision threshold.
    max_budget = 10 * uncovered // 3
    row = report['rows'][0]
    if 'error' in row:
        raise RuntimeError(f"Witness audit failed: {row['error']}")
    output = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'evidence_class': 'REGISTRY-MEASUREMENT; witness-only duplicate proof',
        'candidate_file': str(args.candidate.relative_to(ROOT)) if args.candidate.is_relative_to(ROOT) else str(args.candidate),
        'candidate_sha256': receipt['sha256'],
        'witness': {'repository': REPO, 'commit': COMMIT, 'path': REMOTE,
                    'url': f'https://github.com/{REPO}/blob/{COMMIT}/{REMOTE}',
                    'sha256': WITNESS_SHA256},
        'format_validation': receipt,
        'final_dot_gate': {
            'candidate_dots': dots,
            'candidate_dots_within_3px': round(row['my_dots_within_3px_of_theirs'] * dots),
            'forward_overlap_3px': row['my_dots_within_3px_of_theirs'],
            'spearman_full_footprint': row['spearman_full_footprint'],
            'limits': {'forward_overlap': 0.70, 'spearman': 0.90},
            'duplicate': bool(row['duplicate_by_overlap'] or row['duplicate_by_rho']),
        },
        'surface_gate': {'tested': False,
                         'reason': 'Original pre-placement surface is not persisted; prior sampled/density-exempt audit cannot clear it.'},
        'budget_feasibility': {**saturation, 'witness_file': REMOTE,
            'max_dots_for_possible_70pct_pass': max_budget,
            'requested_previous_budget': dots,
            'lower_bound_overlap_for_that_budget': max(0, dots - uncovered) / dots if dots else None,
            'explanation': 'At most U distinct allowed pixels lie outside the witness halo; 0.3*N <= U is necessary, not sufficient.'},
        'complete_registry_checked': False,
        'verdict': 'negative',
        'stop_required': bool(row['duplicate_by_overlap'] or row['duplicate_by_rho']),
        'note': 'The existing candidate was generated in a prior session; no new raster or experiment was created in this audit.',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'file': output['candidate_file'], 'sha256': receipt['sha256'],
        'format_ok': receipt['all_checks_passed'], 'overlap': output['final_dot_gate']['forward_overlap_3px'],
        'duplicate': output['final_dot_gate']['duplicate'], 'max_budget_necessary': max_budget,
        'verdict': output['verdict']}, indent=2))
    # This command completed its audit even when the candidate fails.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
