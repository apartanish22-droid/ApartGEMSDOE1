#!/usr/bin/env python3
"""Reproducible 3-pixel overlap audit for focus-site rasters (no model, no submission).

Inputs are local GeoTIFFs (for example, the nine focus-site files fetched at the
commits cited in README.md, plus the 13GEMSDOE lattice witness). For every raster it
reports:

* the number of positive dots (value > 0, finite);
* the directed share of each raster's dots within 3 px (Euclidean) of another raster's dots;
* the share of each raster's dots within 3 px of the witness positives;
* the number of footprint cells farther than 3 px from the witness, and the largest
  dot budget N for which a 70% overlap cap could still be satisfied (0.3 * N <= cap).

The 70% and 3 px thresholds come from the project protocol in README.md; they are not
organiser rules. The organiser's scoring rules are in the public problem description
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).

Usage:
    python scripts/audit_focus_overlap.py --witness path/to/witness.tif \
        --footprint data/official/sample_submission.tif \
        --catalogue data/official/labels.tif \
        RASTER1.tif RASTER2.tif ...
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

RADIUS_PX = 3.0


def positives(path: Path) -> np.ndarray:
    arr = rasterio.open(path).read(1).astype(np.float64)
    return np.isfinite(arr) & (arr > 0)


def within(dist: np.ndarray, mask: np.ndarray) -> float:
    return float((dist[mask] <= RADIUS_PX).mean()) if mask.any() else float('nan')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('rasters', nargs='+', type=Path)
    ap.add_argument('--witness', type=Path, required=True)
    ap.add_argument('--footprint', type=Path, required=True, help='Raster whose finite cells define the study footprint')
    ap.add_argument('--catalogue', type=Path, help='Raster whose value 1 marks mapped catalogue faults')
    ap.add_argument('--json-out', type=Path)
    args = ap.parse_args()

    pos = {p.name: positives(p) for p in args.rasters}
    dist = {name: ndimage.distance_transform_edt(~m) for name, m in pos.items()}
    witness = positives(args.witness)
    witness_dist = ndimage.distance_transform_edt(~witness)
    footprint = np.isfinite(rasterio.open(args.footprint).read(1))
    catalogue = (rasterio.open(args.catalogue).read(1) == 1) if args.catalogue else np.zeros_like(footprint)

    report: dict = {'radius_px': RADIUS_PX, 'witness': {'path': str(args.witness), 'positives': int(witness.sum())},
                    'rasters': {}, 'pairwise_directed_within_3px': {}, 'feasibility': {}}
    for name, m in pos.items():
        report['rasters'][name] = {'dots': int(m.sum()), 'within_3px_of_witness': within(witness_dist, m)}
    for a in pos:
        for b in pos:
            if a != b:
                report['pairwise_directed_within_3px'][f'{a} -> {b}'] = within(dist[b], pos[a])

    outside = footprint & (witness_dist > RADIUS_PX)
    outside_noncat = outside & ~catalogue
    report['feasibility'] = {
        'footprint_cells': int(footprint.sum()),
        'footprint_cells_beyond_3px_of_witness': int(outside.sum()),
        'of_which_not_catalogue': int(outside_noncat.sum()),
        'max_budget_for_70pct_cap_using_non_catalogue_outside_cells': int(outside_noncat.sum() / 0.3),
    }

    text = json.dumps(report, indent=2)
    print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
