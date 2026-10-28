#!/usr/bin/env python3
"""Automated, zero-human-input GeoTIFF + Uniqueness Gate validator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from apartgems.uniqueness import check_final_raster_uniqueness
from gems57 import load_grid
from gems57.validate import assert_submittable, validate


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate GeoTIFF format, [0,1] range, NaNs, collar, and fleet uniqueness.")
    ap.add_argument("tif", type=Path, help="Candidate GeoTIFF file")
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    grid = load_grid()
    receipt = validate(args.tif, footprint=grid.footprint, catalogue=grid.catalogue)
    assert_submittable(receipt)

    with rasterio.open(args.tif) as ds:
        arr = ds.read(1)

    edt_cat = distance_transform_edt(~grid.catalogue)
    collar_2px_dots = int(((arr > 0) & (edt_cat <= 2.0)).sum())
    farfield_15px_dots = int(((arr > 0) & (edt_cat > 15.0)).sum())
    try:
        uniq = check_final_raster_uniqueness(arr, grid.footprint)
    except FileNotFoundError as exc:
        if "registry_manifest.json" in str(exc):
            raise SystemExit(
                "FLEET-UNIQUENESS GATE BLOCKED: .cache/registry_index/registry_manifest.json is missing. "
                "Format+range checks passed, but the 806-raster fleet uniqueness gate cannot run in this "
                "sandbox (registry rebuild requires downloading peer rasters from hosts outside this "
                "environment's outbound allowlist). Re-run on an unrestricted host via:\n"
                "  bash scripts/download_competition_data.sh\n"
                "  .venv/bin/python scripts/prepare_data.py --cache-bands\n"
                "  .venv/bin/python scripts/audit_focus_sites_and_registry.py\n"
                "  .venv/bin/python scripts/validate_submission.py " + str(args.tif)
            ) from exc
        raise

    full = {
        "validator_version": "apartgems-automated-gate-v1",
        "format_and_range_receipt": receipt,
        "collar_200m_positive_pixels": collar_2px_dots,
        "farfield_gt_1500m_positive_pixels": farfield_15px_dots,
        "farfield_fraction": round(farfield_15px_dots / max(receipt["emitted_positive_pixels"], 1), 6),
        "uniqueness_gate": uniq,
        "all_automated_gates_passed": bool(
            receipt["all_checks_passed"]
            and collar_2px_dots == 0
            and uniq["passed"]
        ),
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(full, indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "file": str(args.tif),
        "all_automated_gates_passed": full["all_automated_gates_passed"],
        "emitted_positive_pixels": receipt["emitted_positive_pixels"],
        "min": receipt["min"],
        "max": receipt["max"],
        "n_nan": receipt["n_nan"],
        "collar_200m_positive_pixels": collar_2px_dots,
        "farfield_fraction": full["farfield_fraction"],
        "max_abs_spearman_rho": uniq["max_abs_spearman_rho"],
        "max_3px_overlap_vs_competing_detectors": uniq["max_3px_overlap_vs_competing_detectors"],
    }, indent=2))
    if not full["all_automated_gates_passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
