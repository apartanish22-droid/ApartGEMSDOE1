#!/usr/bin/env python3
"""CLI wrapper around the shared fail-closed GeoTIFF submission_writer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from gems57 import load_grid
from gems57.submission_writer import write_submission


def main() -> int:
    ap = argparse.ArgumentParser(description="Write a validated float32 [0,1] GeoTIFF with NaN nodata outside the valid footprint.")
    ap.add_argument("npy", type=Path, help="Input 2-D float32 numpy array")
    ap.add_argument("out_tif", type=Path, help="Output GeoTIFF path")
    ap.add_argument("--name", required=True, help="Submission name (<=140 chars)")
    ap.add_argument("--note", required=True, help="Submission note (<=140 chars)")
    args = ap.parse_args()

    grid = load_grid()
    arr = np.load(args.npy)
    receipt = write_submission(
        args.out_tif,
        arr,
        ROOT / "data/sample_submission.tif",
        grid.footprint,
        name=args.name,
        note=args.note,
        catalogue=grid.catalogue,
    )
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
