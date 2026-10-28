#!/usr/bin/env python3
"""Validate local format and the literal full-inventory uniqueness gate.

Local checks cannot grant organizer acceptance or select a weekly slot.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import rasterio
from gems57 import load_grid
from gems57.gates import format_report
from gems57.uniqueness import compare_array_to_registry
from gems57.validate import validate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('tif', type=Path)
    p.add_argument('--registry-index', type=Path, required=True,
                   help='complete accessible inventory for shared literal gate')
    p.add_argument('--json-out', type=Path)
    args = p.parse_args()
    grid = load_grid()
    receipt = validate(args.tif, footprint=grid.footprint, catalogue=grid.catalogue)
    fmt = format_report(args.tif, ROOT / 'data/bridge/sample_submission.tif', footprint=grid.footprint)
    with rasterio.open(args.tif) as ds:
        arr = ds.read(1)
    uniq = compare_array_to_registry(arr, args.registry_index, grid.footprint,
                                     file_sha256=receipt['sha256'],
                                     expected_grid=(grid.shape, grid.crs, grid.transform))
    result = {'format_and_range_receipt': receipt, 'template_check': fmt, 'uniqueness_gate': uniq,
              'all_automated_gates_passed': bool(receipt['all_checks_passed'] and fmt['ok'] and uniq['unique']),
              'slot_approved': False}
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text)
    print(text, end='')
    return 0 if result['all_automated_gates_passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
