"""Hash checks, bridge-grid handling and independent saved-byte inspection."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import rasterio


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, entry: dict) -> None:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing {entry['id']}: {path}")
    if path.stat().st_size != entry["bytes"]:
        raise ValueError(f"Size mismatch for {entry['id']}: {path}")
    if sha256_file(path) != entry["sha256"]:
        raise ValueError(f"SHA-256 mismatch for {entry['id']}: {path}")


def template_info(path: Path) -> dict:
    with rasterio.open(path) as src:
        if src.driver != "GTiff" or src.count != 1 or src.crs is None:
            raise ValueError("Template must be a single-band georeferenced GeoTIFF")
        arr = src.read(1)
        foot = np.isfinite(arr) & (src.read_masks(1) != 0)
        if not foot.any():
            raise ValueError("Template footprint is empty")
        return {"crs": src.crs, "transform": src.transform, "shape": src.shape,
                "footprint": foot, "values": arr, "count": src.count}


def aligned(path: Path, grid: dict) -> None:
    with rasterio.open(path) as src:
        if (src.driver != "GTiff" or src.count != 1 or src.shape != grid["shape"]
                or src.crs != grid["crs"] or src.transform != grid["transform"]):
            raise ValueError(f"Incompatible single-band raster grid: {path}")


def positive_mask(path: Path, grid: dict) -> np.ndarray:
    aligned(path, grid)
    with rasterio.open(path) as src:
        arr = src.read(1)
        return grid["footprint"] & np.isfinite(arr) & (src.read_masks(1) != 0) & (arr > 0)


def inspect_candidate(path: Path, grid: dict) -> dict:
    """Inspect saved bytes. Format checks do not authorize a weekly submission.

    The official text refers to null/NaN outside the *bounds*. The irregular
    footprint of the owner mirror makes handling of zero outside it ambiguous;
    both profiles are reported separately rather than claiming portal acceptance.
    """
    path = Path(path)
    report = {"path": str(path), "sha256": sha256_file(path),
              "organizer_accepted": False, "approved_to_submit": False}
    f = grid["footprint"]
    with rasterio.open(path) as src:
        checks = {
            "geotiff": src.driver == "GTiff",
            "single_band": src.count == 1,
            "float32": src.count == 1 and src.dtypes[0] == "float32",
            "crs_match": src.crs == grid["crs"],
            "shape_match": src.shape == grid["shape"],
            "transform_match": src.transform == grid["transform"],
        }
        report["checks"] = checks
        report["footprint_comparison"] = (
            "georeferenced grid matches" if checks["shape_match"] and checks["crs_match"] and checks["transform_match"]
            else "array-index diagnostic only; grid mismatch prevents geospatial comparison"
        )
        if not checks["single_band"] or not checks["shape_match"]:
            report["basic_checks_passed"] = False
            report["reason"] = "Cannot check footprint pixels: candidate has wrong band count or shape."
            return report
        a = src.read(1)
        valid_mask = src.read_masks(1) != 0
        inside = a[f]
        inside_masks = valid_mask[f]
        finite = np.isfinite(inside)
        inrange = finite & (inside >= 0) & (inside <= 1)
        checks["inside_all_finite"] = bool(finite.all())
        checks["inside_in_range_0_1"] = bool(inrange.all())
        checks["inside_not_nodata"] = bool(inside_masks.all())
        outside = a[~f]
        outside_masks = valid_mask[~f]
        masked_or_nan = ~outside_masks | np.isnan(outside)
        zero_and_finite = np.isfinite(outside) & (outside == 0)
        outside_positive = int(np.count_nonzero(np.isfinite(outside) & outside_masks & (outside > 0)))
        checks["no_unmasked_positive_outside_footprint"] = outside_positive == 0
        allfinite_range = bool(np.isfinite(a).all() and ((a >= 0) & (a <= 1)).all())
        vals = inside[finite]
        report.update({
            "inside_nan": int(np.isnan(inside).sum()),
            "inside_infinite": int(np.isinf(inside).sum()),
            "inside_nodata": int((~inside_masks).sum()),
            "inside_out_of_range_or_nonfinite": int((~inrange).sum()),
            "inside_min": float(vals.min()) if vals.size else None,
            "inside_max": float(vals.max()) if vals.size else None,
            "outside_cells": int(outside.size),
            "outside_masked_or_nan": int(masked_or_nan.sum()),
            "outside_finite_zero": int(zero_and_finite.sum()),
            "outside_positive": outside_positive,
            "strict_irregular_footprint_null": bool(masked_or_nan.all()),
            "whole_array_finite_in_range": allfinite_range,
            "nodata": None if src.nodata is None else str(src.nodata),
            "dtype": src.dtypes[0],
            "crs": str(src.crs),
            "shape": list(src.shape),
            "transform": list(src.transform)[:6],
        })
    report["basic_checks_passed"] = all(checks.values())
    report["interpretation"] = (
        "Saved-byte checks only. Neither an all-finite profile nor a null-outside "
        "profile proves portal acceptance, uniqueness, holdout success or slot approval."
    )
    return report
