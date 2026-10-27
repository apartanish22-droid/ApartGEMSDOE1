#!/usr/bin/env python3
"""Inventory local input files without treating mirrors as official data."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import rasterio

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_raster(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"present": False}
    result: dict[str, Any] = {
        "present": True,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    try:
        with rasterio.open(path) as ds:
            result.update({
                "readable": True,
                "crs": str(ds.crs) if ds.crs is not None else None,
                "width": ds.width,
                "height": ds.height,
                "count": ds.count,
                "dtypes": list(ds.dtypes),
                "transform": list(ds.transform),
                "nodata": (None if ds.nodata is None else
                           (float(ds.nodata) if math.isfinite(ds.nodata) else str(ds.nodata))),
            })
    except Exception as exc:  # inventory malformed local files; don't crash report
        result.update({"readable": False, "error": f"{type(exc).__name__}: {exc}"})
    return result


def inspect_data(data_dir: Path) -> dict[str, Any]:
    names = {
        "training_features": "training_features.tif",
        "labels": "labels.tif",
        "sample_submission": "sample_submission.tif",
        "example_submission": "example_submission.tif",
        "existing_faults": "existing_faults.tif",
        "geodawn_features": "gems-geodawn-numerical-features.tif",
        "candidate": "candidate.tif",
    }
    files = {key: inspect_raster(data_dir / filename) for key, filename in names.items()}
    sample = files["sample_submission"]
    training_inputs = all(
        files[key].get("present") and files[key].get("readable")
        for key in ("training_features", "labels", "sample_submission")
    )
    validation_inputs = (
        sample.get("present") and sample.get("readable")
        and files["candidate"].get("present") and files["candidate"].get("readable")
    )
    return {
        "schema_version": 2,
        "data_dir": str(data_dir.relative_to(REPO)) if data_dir.is_relative_to(REPO) else str(data_dir),
        "provenance": "Local-file inventory only; presence does not authenticate organizer provenance.",
        "files": files,
        "template_signature": (
            {
                "source": "locally supplied sample_submission.tif; organizer authenticity must be verified separately",
                "crs": sample.get("crs"),
                "width": sample.get("width"),
                "height": sample.get("height"),
                "transform": sample.get("transform"),
                "count": sample.get("count"),
                "dtypes": sample.get("dtypes"),
                "origin_verified": False,
                "local_transform_inspected": True,
            }
            if sample.get("present") and sample.get("readable")
            else {"source": None, "origin_verified": False, "status": "NO READABLE SAMPLE TEMPLATE"}
        ),
        "ready_for_training_inputs": bool(training_inputs),
        "ready_for_template_validation": bool(validation_inputs),
        "submission_authorized": False,
        "submission_blocker": "A file inventory never establishes scientific validity, registry novelty, or weekly-slot authorization.",
    }


def main() -> int:
    report = inspect_data(DATA)
    print(json.dumps(report, indent=2))
    return 0 if report["ready_for_training_inputs"] else 1


if __name__ == "__main__":
    sys.exit(main())
