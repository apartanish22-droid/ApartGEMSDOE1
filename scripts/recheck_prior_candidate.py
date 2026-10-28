#!/usr/bin/env python3
"""Reproduce the counterexample to the old overlap gate; no new experiment."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
import rasterio
from apartgems.uniqueness import fast_near_3px
from gems57 import load_grid
from gems57.validate import sha256, validate

PIN = '24f56b4bf31c62590a9192e1f38b398531a6edc4'
HASH = 'b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2'
REL = 'inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif'
CANDIDATE = ROOT / 'docs/downloads/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif'


def main():
    lattice = ROOT / '.cache/review/lattice.tif'
    lattice.parent.mkdir(parents=True, exist_ok=True)
    if not lattice.exists():
        with lattice.open('wb') as out:
            subprocess.run(['gh', 'api', f'repos/buffedlizard55-lab/GEMSDOE24/contents/{REL}?ref={PIN}',
                            '-H', 'Accept: application/vnd.github.raw+json'], stdout=out, check=True)
    if sha256(lattice) != HASH:
        raise ValueError('registry raster hash mismatch')
    grid = load_grid()
    with rasterio.open(lattice) as ref, rasterio.open(CANDIDATE) as candidate:
        if (ref.shape != candidate.shape or ref.crs != candidate.crs
                or ref.transform != candidate.transform):
            raise ValueError('candidate and registry raster grids do not match')
        r, a = ref.read(1), candidate.read(1)
    dots = (a > 0) & grid.footprint
    if not dots.any():
        raise ValueError('candidate contains no dots')
    overlap = float(fast_near_3px(np.isfinite(r) & (r > 0) & grid.footprint)[dots].mean())
    result = {'registry_repo': 'buffedlizard55-lab/GEMSDOE24', 'registry_commit': PIN,
              'registry_path': REL, 'registry_sha256': HASH,
              'candidate_sha256': sha256(CANDIDATE), 'candidate_positive_pixels': int(dots.sum()),
              'fraction_within_3_pixels': overlap, 'limit': 0.70,
              'duplicate': overlap > 0.70,
              'local_format': validate(CANDIDATE, grid.footprint, grid.catalogue),
              'note': 'One counterexample proves failure; it does not establish a complete registry.'}
    (ROOT / 'evidence/recheck_20261028.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
