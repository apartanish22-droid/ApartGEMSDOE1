#!/usr/bin/env python3
"""Check saved GeoTIFF bytes and, optionally, literal two-phase registry gates.

A format PASS is not an organizer acceptance, proof of high DTI, proof of
uniqueness, or a weekly-slot selection. By default both a saved pre-placement
surface and a complete, hash-pinned registry inventory are required. Missing
inputs fail closed. `--format-only` is explicitly diagnostic and cannot approve
an upload. This command never submits anything to DrivenData.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import rasterio

from gems57 import load_grid
from gems57.gates import format_report, lane_uniqueness_report
from gems57.validate import validate


def read_aligned(path: Path, grid):
    with rasterio.open(path) as ds:
        if ds.count != 1 or (ds.shape, ds.crs, ds.transform) != (grid.shape, grid.crs, grid.transform):
            raise ValueError(f"{path}: single band / CRS / shape / transform mismatch")
        return ds.read(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tif", type=Path, help="Candidate GeoTIFF")
    parser.add_argument("--surface", type=Path, help="Saved, aligned pre-placement surface GeoTIFF")
    parser.add_argument("--registry-index", type=Path, help="Full hash-pinned shared registry inventory JSON")
    parser.add_argument("--format-only", action="store_true", help="Check format only; never authorize submission")
    parser.add_argument("--json-out", type=Path, help="Write the full diagnostic receipt")
    args = parser.parse_args()
    if args.format_only and (args.surface or args.registry_index):
        parser.error("--format-only cannot be combined with registry gate options")

    errors = []
    report = {
        "validator_version": "apartgems-fail-closed-v2",
        "file": str(args.tif),
        "format_preflight": None,
        "template_preflight": None,
        "preplacement_surface_gate": None,
        "final_raster_gate": None,
        "submission_ready": False,
        "weekly_slot_approved": False,
        "caveat": "Checks are local and bridge-relative. Holdout performance, organizer acceptance, complete external history and the separate slot selector are not established here.",
    }
    grid = None
    try:
        grid = load_grid()
        report["format_preflight"] = validate(args.tif, footprint=grid.footprint, catalogue=grid.catalogue)
        report["template_preflight"] = format_report(
            args.tif, ROOT / "data/bridge/sample_submission.tif", footprint=grid.footprint
        )
        if not report["format_preflight"]["all_checks_passed"] or not report["template_preflight"]["ok"]:
            errors.append("local format/range preflight failed")
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        errors.append(f"format preflight could not be completed: {exc}")

    if not args.format_only:
        if args.registry_index is None:
            errors.append("complete hash-pinned registry index not supplied")
        if args.surface is None:
            errors.append("saved pre-placement surface not supplied")
        if not errors:
            try:
                surface = read_aligned(args.surface, grid)
                # This shared gate uses literal finite-positive support for all
                # registry entries and will not pass an incomplete inventory.
                report["preplacement_surface_gate"] = lane_uniqueness_report(
                    surface, grid.footprint, sample=ROOT / "data/bridge/sample_submission.tif",
                    phase="surface", registry_index=args.registry_index,
                )
                if not report["preplacement_surface_gate"]["ok"]:
                    errors.append("pre-placement surface uniqueness failed or registry is incomplete; stop before dot gate")
                else:
                    final = read_aligned(args.tif, grid)
                    report["final_raster_gate"] = lane_uniqueness_report(
                        final, grid.footprint, sample=ROOT / "data/bridge/sample_submission.tif",
                        phase="dots", registry_index=args.registry_index,
                    )
                    if not report["final_raster_gate"]["ok"]:
                        errors.append("final raster uniqueness failed or registry is incomplete")
            except (OSError, ValueError, KeyError, RuntimeError, rasterio.errors.RasterioError) as exc:
                errors.append(f"literal uniqueness audit could not be completed: {exc}")

    report["local_checks_passed"] = not errors
    report["diagnostic_format_only"] = args.format_only
    report["errors"] = errors
    out = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(out, encoding="utf-8")
    print(out, end="")
    return 0 if report["local_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
