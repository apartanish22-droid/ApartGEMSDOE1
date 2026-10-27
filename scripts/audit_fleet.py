#!/usr/bin/env python3
"""Reproduce the historical nine-file / lattice geometry audit, not a model score.

The reference grid and labels are pinned third-party mirrors and are not proof
of organizer origin. This script checks only these ten comparators, not a complete
registry. A single duplicate witness is enough to stop; absence of one is not
approval. No surface, HOLDOUT-DTI, score estimate, or GeoTIFF is generated here.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from download_audit_inputs import DEFAULT_MANIFEST, load_manifest, sha256_file

ROOT = Path(__file__).resolve().parents[1]


def validate_pins(entries: list[dict], directory: Path) -> None:
    for entry in entries:
        ident = entry.get("id", entry.get("site"))
        p = directory / f"{ident}.tif"
        if not p.is_file() or p.stat().st_size != entry["bytes"] or sha256_file(p) != entry["sha256"]:
            raise ValueError(f"Missing or corrupt pinned raster: {ident}. Run download_audit_inputs.py")


def lower_bound(overlap_free_cells: int, dots: int) -> dict:
    """Conservative one-way overlap bound; equality at 70% is allowed."""
    if not isinstance(overlap_free_cells, int) or overlap_free_cells < 0:
        raise ValueError("uncovered cells must be a non-negative integer")
    if not isinstance(dots, int) or dots <= 0:
        raise ValueError("dot budget must be a positive integer")
    n_match = max(0, dots - overlap_free_cells)
    return {"dots": dots, "uncovered_cells": overlap_free_cells,
            "minimum_matches": n_match, "minimum_fraction": n_match / dots,
            "forced_duplicate_stop": 10 * n_match > 7 * dots}


def nearby_to(reference: np.ndarray, radius: float = 3.0) -> np.ndarray:
    reference = np.asarray(reference, dtype=bool)
    if reference.ndim != 2 or not reference.any() or not np.isfinite(radius) or radius < 0:
        raise ValueError("A nonempty 2-D reference and finite nonnegative radius are required")
    return distance_transform_edt(~reference) <= radius


def overlap_fraction(candidate: np.ndarray, nearby_reference: np.ndarray) -> dict:
    candidate = np.asarray(candidate, dtype=bool)
    nearby_reference = np.asarray(nearby_reference, dtype=bool)
    if candidate.ndim != 2 or candidate.shape != nearby_reference.shape:
        raise ValueError("Candidate/reference grids must be matching 2-D arrays")
    n = int(candidate.sum())
    if n == 0:
        raise ValueError("Cannot calculate a directed overlap for zero dots")
    hits = int(np.count_nonzero(candidate & nearby_reference))
    return {"candidate_dots": n, "within_radius": hits, "fraction": hits / n,
            "duplicate_stop": 10 * hits > 7 * n}


def binary_spearman(a: np.ndarray, b: np.ndarray, valid: np.ndarray) -> float | None:
    """Spearman rho for binary arrays with average ranks for ties (the phi coefficient)."""
    if a.shape != b.shape or a.shape != valid.shape:
        raise ValueError("Correlation grids must agree")
    n = int(valid.sum())
    na = int(np.count_nonzero(a & valid))
    nb = int(np.count_nonzero(b & valid))
    both = int(np.count_nonzero(a & b & valid))
    denominator = math.sqrt(float(na) * (n - na) * nb * (n - nb))
    if denominator == 0:
        return None
    return (n * both - na * nb) / denominator


def raster_snapshot(path: Path, shape: tuple[int, int], crs, transform, foot: np.ndarray):
    with rasterio.open(path) as src:
        if src.count != 1 or src.shape != shape or src.crs != crs or src.transform != transform:
            raise ValueError(f"Reference grid/band mismatch: {path.name}")
        a = src.read(1)
        inside = a[foot]
        finite = np.isfinite(inside)
        if not finite.all() or (inside < 0).any() or (inside > 1).any():
            raise ValueError(f"Reference has non-finite or out-of-range values inside footprint: {path.name}")
        if not np.all((inside == 0) | (inside == 1)):
            raise ValueError(f"This dot-mask audit requires a binary reference: {path.name}")
        positive = foot & np.isfinite(a) & (a > 0)
        if not positive.any():
            raise ValueError(f"Reference contains no positive cells: {path.name}")
        outside = a[~foot]
        raw = np.ascontiguousarray(np.packbits(positive, bitorder="little"))
        result = {
            "sha256": sha256_file(path), "dtype": src.dtypes[0], "shape": list(src.shape),
            "crs": str(src.crs), "transform": list(src.transform)[:6],
            "finite_inside": int(finite.sum()), "nonfinite_inside": int((~finite).sum()),
            "inside_min": float(inside.min()), "inside_max": float(inside.max()),
            "inside_positive_pixels": int(positive.sum()),
            "outside_nonfinite": int((~np.isfinite(outside)).sum()),
            "outside_finite": int(np.isfinite(outside).sum()),
            "outside_positive": int(np.count_nonzero(np.isfinite(outside) & (outside > 0))),
            "support_sha256_packbits_little": hashlib.sha256(raw).hexdigest(),
        }
        return result, positive


def audit(manifest: dict, directory: Path) -> dict:
    entries = manifest["support"] + manifest["reference_sites"]
    validate_pins(entries, directory)
    with rasterio.open(directory / "sample_submission.tif") as template:
        if template.count != 1 or template.crs is None:
            raise ValueError("Reference template is not a single-band georeferenced grid")
        sample = template.read(1)
        foot = np.isfinite(sample)
        if not foot.any() or foot.all():
            raise ValueError("Expected a finite in-footprint / NaN outside mirror template")
        shape, crs, transform = template.shape, template.crs, template.transform
    with rasterio.open(directory / "labels.tif") as labels_ds:
        if labels_ds.count != 1 or labels_ds.shape != shape or labels_ds.crs != crs or labels_ds.transform != transform:
            raise ValueError("Mapped-fault mirror does not match the sample grid")
        label_array = labels_ds.read(1)
        labels = foot & np.isfinite(label_array) & (label_array > 0)
        sample_is_labels = bool(np.array_equal((sample > 0) & foot, labels))
    lattice_info, lattice = raster_snapshot(directory / "lattice.tif", shape, crs, transform, foot)
    near_lattice = nearby_to(lattice)
    n_inside = int(foot.sum())
    covered = int(np.count_nonzero(foot & near_lattice))
    uncovered = n_inside - covered
    files, masks = {}, {}
    for entry in manifest["reference_sites"]:
        site = entry["site"]
        files[site], masks[site] = raster_snapshot(directory / f"{site}.tif", shape, crs, transform, foot)
        files[site]["versus_lattice"] = overlap_fraction(masks[site], near_lattice)
        files[site]["lattice_binary_spearman"] = binary_spearman(masks[site], lattice, foot)

    comparisons = {}
    for reference, reference_mask in masks.items():
        near = nearby_to(reference_mask)
        for candidate, candidate_mask in masks.items():
            if candidate == reference:
                continue
            result = overlap_fraction(candidate_mask, near)
            result["binary_spearman"] = binary_spearman(candidate_mask, reference_mask, foot)
            result["identical_positive_support"] = bool(np.array_equal(candidate_mask, reference_mask))
            comparisons[f"{candidate}->{reference}"] = result
    for site in masks:
        peers = [(key.split("->")[1], value) for key, value in comparisons.items() if key.startswith(site + "->")]
        worst_site, worst_value = max(peers, key=lambda row: row[1]["fraction"])
        files[site]["maximum_peer_overlap"] = {"site": worst_site, **worst_value}

    d25, d30, d31, d32, d36 = (masks[s] for s in ("GEMSDOE25", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE36"))
    dist_labels = distance_transform_edt(~labels)
    removed25 = d25 & ~d32
    result = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "DATA-MEASUREMENT, NOT A SCORE",
        "scope": manifest["scope"],
        "provenance_warning": "Pinned third-party mirrors; matching bytes do not authenticate organizer data. No holdout or surface was evaluated.",
        "grid": {"shape": list(shape), "crs": str(crs), "transform": list(transform)[:6],
                 "footprint_pixels": n_inside, "sample_positive_equals_mapped_fault_mirror": sample_is_labels,
                 "sample_positive_pixels": int(np.count_nonzero((sample > 0) & foot))},
        "lattice": {**lattice_info, "radius_pixels": 3, "covered_footprint_pixels": covered,
                    "uncovered_footprint_pixels": uncovered,
                    "budget_37654_lower_bound": lower_bound(uncovered, 37654),
                    "first_budget_proven_over_70_percent": (10 * uncovered) // 3 + 1},
        "historical_references": files,
        "peer_comparisons": comparisons,
        "lineage": {
            "g25_g30_identical_positive_support": bool(np.array_equal(d25, d30)),
            "g32_added_vs_g25": int(np.count_nonzero(d32 & ~d25)),
            "g32_removed_vs_g25": int(np.count_nonzero(removed25)),
            "g32_removed_within_2_pixels_of_mapped_mirror": int(np.count_nonzero(removed25 & (dist_labels <= 2.0))),
            "g32_added_vs_g31": int(np.count_nonzero(d32 & ~d31)),
            "g32_removed_vs_g31": int(np.count_nonzero(d31 & ~d32)),
            "g36_added_vs_g32": int(np.count_nonzero(d36 & ~d32)),
            "g36_removed_vs_g32": int(np.count_nonzero(d32 & ~d36)),
        },
        "limitations": ["No artifact-specific organizer receipts or hidden truth.",
                        "No pre-placement surface or complete registry checked.",
                        "Format diagnostics are not organizer acceptance or slot authorization.",
                        "The lattice counting bound applies only to distinct positive pixels inside this mirrored footprint."],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--directory", type=Path, default=ROOT / ".cache/audit-inputs")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/fleet_audit.json")
    args = parser.parse_args()
    try:
        report = audit(load_manifest(args.manifest), args.directory)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".audit.", suffix=".json", dir=args.output.parent)
        tmp = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, allow_nan=False)
                f.write("\n")
            os.replace(tmp, args.output)
        finally:
            tmp.unlink(missing_ok=True)
        print(f"Wrote {args.output}; {len(report['historical_references'])} pinned references checked.")
        print(f"Lattice uncovered: {report['lattice']['uncovered_footprint_pixels']}; "
              f"37,654-dot lower bound: {report['lattice']['budget_37654_lower_bound']['minimum_fraction']:.6f}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError, rasterio.errors.RasterioError) as exc:
        print(f"AUDIT FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
