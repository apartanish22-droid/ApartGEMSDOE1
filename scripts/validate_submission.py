#!/usr/bin/env python3
"""Validate a single-band prediction GeoTIFF against the official reference grid.

This checks file-format/grid compatibility and [0, 1] finite values inside the
reference footprint. It does not estimate score, prove uniqueness, or submit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(prediction_path: Path, reference_path: Path) -> dict[str, Any]:
    try:
        import numpy as np
        import rasterio
    except ImportError as exc:
        raise RuntimeError(
            "Missing geospatial dependencies. Install them with: "
            "python -m pip install -r requirements.txt"
        ) from exc

    if not prediction_path.is_file():
        raise ValueError(f"Prediction file does not exist: {prediction_path}")
    if not reference_path.is_file():
        raise ValueError(f"Reference file does not exist: {reference_path}")

    with rasterio.open(reference_path) as reference, rasterio.open(prediction_path) as pred:
        if reference.count != 1:
            raise ValueError(f"Reference must be single-band; found {reference.count} bands")
        if pred.count != 1:
            raise ValueError(f"Prediction must be single-band; found {pred.count} bands")
        if reference.crs is None or pred.crs is None:
            raise ValueError("Both rasters must declare a CRS")
        if pred.crs != reference.crs:
            raise ValueError(f"CRS mismatch: prediction={pred.crs}, reference={reference.crs}")
        if (pred.height, pred.width) != (reference.height, reference.width):
            raise ValueError(
                "Shape mismatch: "
                f"prediction={(pred.height, pred.width)}, "
                f"reference={(reference.height, reference.width)}"
            )
        if pred.transform != reference.transform:
            raise ValueError(
                f"Transform mismatch: prediction={pred.transform}, reference={reference.transform}"
            )

        footprint = reference.read_masks(1) != 0
        footprint_count = int(np.count_nonzero(footprint))
        if footprint_count == 0:
            raise ValueError("Reference footprint is empty (all pixels are masked)")

        prediction = pred.read(1, masked=False)
        prediction_mask = pred.read_masks(1) != 0
        if np.any(footprint & ~prediction_mask):
            missing = int(np.count_nonzero(footprint & ~prediction_mask))
            raise ValueError(f"Prediction is masked/nodata at {missing} reference-footprint pixels")

        values = prediction[footprint]
        finite = np.isfinite(values)
        if not np.all(finite):
            bad = int(values.size - np.count_nonzero(finite))
            raise ValueError(f"Prediction contains {bad} non-finite values inside reference footprint")
        minimum = float(np.min(values))
        maximum = float(np.max(values))
        if minimum < 0.0 or maximum > 1.0:
            raise ValueError(
                f"Predicted values must be in range [0, 1] inside the reference footprint; "
                f"observed min={minimum}, max={maximum}"
            )

        return {
            "status": "PASS",
            "prediction": str(prediction_path),
            "reference": str(reference_path),
            "sha256": _sha256(prediction_path),
            "bands": int(pred.count),
            "crs": pred.crs.to_string(),
            "shape": [int(pred.height), int(pred.width)],
            "transform": list(pred.transform)[:6],
            "footprint_pixels_checked": footprint_count,
            "finite_inside_footprint": True,
            "value_range_inside_footprint": [minimum, maximum],
            "scope_note": "Structural/range validation only; no score, uniqueness, or organizer acceptance is certified.",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prediction", type=Path, help="candidate single-band prediction GeoTIFF")
    parser.add_argument("reference", type=Path, help="official sample-submission/reference GeoTIFF")
    args = parser.parse_args()
    try:
        result = validate(args.prediction, args.reference)
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
