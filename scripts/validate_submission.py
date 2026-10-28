#!/usr/bin/env python3
"""Fail-closed local format and literal-registry preflight; never submits a file.

Use --format-only to check TIFF bytes alone. Otherwise an incomplete or absent
registry, missing pre-placement surface, unverified holdout, or missing selector
approval prevents a submission-ready claim. A successful local range check is
not an organizer receipt and does not prove the portal will accept a file.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import numpy as np
import rasterio
from gems57 import load_grid
from gems57.uniqueness import compare_array_to_registry
from gems57.validate import validate


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('tif', type=Path, help='GeoTIFF to inspect; no submission occurs')
    ap.add_argument('--format-only', action='store_true', help='Return success on local format alone (not upload approval)')
    ap.add_argument('--registry', type=Path, help='Full hash-pinned registry inventory JSON')
    ap.add_argument('--surface', type=Path, help='Pre-placement main surface as a 2-D .npy file')
    ap.add_argument('--vent-surface', type=Path, help='Pre-placement specialist surface as a 2-D .npy file, if used')
    ap.add_argument('--json-out', type=Path)
    args = ap.parse_args()
    result = {'validator_version': 'apartgems-local-preflight-v2',
              'file': str(args.tif), 'format': None, 'surface_registry': None,
              'vent_surface_registry': None, 'final_registry': None,
              'registry_gate': ('pending complete hash-pinned --registry scan' if args.registry else
                                'BLOCKED: no full hash-pinned registry inventory was provided; '
                                'a partial or missing scan cannot clear uniqueness.'),
              'holdout_gate': 'not evaluated by this preflight',
              'selector_approval': False, 'ok_to_submit': False,
              'note': 'A local format pass is neither organizer acceptance nor selector approval.'}
    try:
        grid = load_grid()
        result['format'] = validate(args.tif, footprint=grid.footprint, catalogue=grid.catalogue)
        if args.registry:
            with rasterio.open(args.tif) as src:
                array = src.read(1)
            expected = (grid.shape, grid.crs, grid.transform)
            result['final_registry'] = compare_array_to_registry(
                array, args.registry, grid.footprint, file_sha256=result['format']['sha256'],
                expected_grid=expected, include_reverse=False)
            result['registry_gate'] = ('BLOCKED: final raster failed or inventory is incomplete'
                                       if not result['final_registry']['unique'] else
                                       'final raster checked; pre-placement and holdout remain separate')
            # A final duplicate is a stop: do not continue to other phases.
            if not result['final_registry']['duplicate_count']:
                for field, path in (('surface_registry', args.surface), ('vent_surface_registry', args.vent_surface)):
                    if path is not None:
                        surface = np.load(path, allow_pickle=False)
                        result[field] = compare_array_to_registry(
                            surface, args.registry, grid.footprint, expected_grid=expected,
                            include_reverse=False, phase='surface')
                        if result[field]['duplicate_count']:
                            break
    except (OSError, ValueError, KeyError, rasterio.errors.RasterioError) as exc:
        result['error'] = str(exc)
        result['registry_gate'] = 'BLOCKED: preflight could not complete; see error'
    text = json.dumps(result, indent=2, allow_nan=False)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + '\n')
    print(text)
    format_ok = bool(result['format'] and result['format']['all_checks_passed'] and 'error' not in result)
    # Only format-only can pass this preflight. Selector eligibility requires
    # separately verified canaries, same-evaluator holdout and both surface and
    # final gates; this command does not pretend to perform those steps.
    return 0 if args.format_only and format_ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
