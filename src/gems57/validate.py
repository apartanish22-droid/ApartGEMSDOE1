"""Local preflight validation for a GEMS submission GeoTIFF.

The organizer's public specification requires finite float32 predictions in
[0, 1] on the valid footprint and null/NaN outside it.  The pinned owner-mirror
sample uses NaN nodata outside its finite footprint.  A local pass is not an
organizer receipt, proof of source authenticity, or uniqueness clearance.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import rasterio

from .grid import EPSG, HEIGHT, WIDTH, TRANSFORM

SENTINELS = (-9999.0, -999.0, 9999.0, -3.4e38, 1e30)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _nodata_json_value(value):
    """Represent NaN nodata without emitting non-standard JSON NaN tokens."""
    if value is None:
        return None
    value = float(value)
    return "NaN" if np.isnan(value) else value


def validate(path: Path, footprint: np.ndarray | None = None,
             catalogue: np.ndarray | None = None) -> dict:
    """Re-read one GeoTIFF and report template, footprint, and range checks.

    NaNs are allowed only outside an explicitly supplied footprint.  Without a
    footprint, the validator cannot distinguish valid outside-bounds nodata
    from an in-footprint missing prediction, so it fails closed on all NaNs.
    Infinite values are never accepted.
    """
    path = Path(path)
    with rasterio.open(path) as ds:
        a = ds.read(1)
        nodata = ds.nodata
        meta = dict(crs=str(ds.crs), shape=[ds.height, ds.width], dtype=ds.dtypes[0],
                    count=ds.count, nodata=_nodata_json_value(nodata),
                    transform=list(tuple(ds.transform)[:6]),
                    profile_compress=ds.profile.get("compress"))
        desc = ds.descriptions
        h, w = ds.height, ds.width

    if a.ndim != 2:
        raise ValueError('prediction TIFF must contain a 2-D first band')
    for mask_name, mask in (("footprint", footprint), ("catalogue", catalogue)):
        if mask is not None and np.asarray(mask).shape != a.shape:
            raise ValueError(f"{mask_name} shape {np.asarray(mask).shape} != raster shape {a.shape}")
    footprint = None if footprint is None else np.asarray(footprint, dtype=bool)
    catalogue = None if catalogue is None else np.asarray(catalogue, dtype=bool)

    finite = np.isfinite(a)
    nan = np.isnan(a)
    infinite = np.isinf(a)
    finite_values = a[finite]
    lo = float(finite_values.min()) if finite_values.size else None
    hi = float(finite_values.max()) if finite_values.size else None
    mean = float(finite_values.mean()) if finite_values.size else None
    finite_range = bool(finite_values.size and lo >= 0.0 and hi <= 1.0)
    checks = {
        "single_band": meta["count"] == 1,
        "dtype_float32": meta["dtype"] == "float32",
        f"dimensions_{HEIGHT}x{WIDTH}": (h, w) == (HEIGHT, WIDTH),
        f"crs_epsg_{EPSG}": meta["crs"] == f"EPSG:{EPSG}",
        "transform_matches_sample_submission": meta["transform"] == list(tuple(TRANSFORM)[:6]),
        "no_inf_anywhere": bool(not infinite.any()),
        "no_sentinel_values_in_finite_data": bool(not np.isin(finite_values, SENTINELS).any()),
    }
    if footprint is not None:
        n_fp = int(footprint.sum())
        inside = a[footprint]
        outside = a[~footprint]
        checks["footprint_nonempty"] = n_fp > 0
        checks["no_nan_inside_footprint"] = bool(n_fp > 0 and np.isfinite(inside).all())
        checks["values_in_0_1_inside_footprint"] = bool(
            n_fp > 0 and np.isfinite(inside).all()
            and (inside >= 0.0).all() and (inside <= 1.0).all())
        checks["outside_footprint_is_nan"] = bool(np.isnan(outside).all())
        checks["nodata_tag_is_nan"] = bool(nodata is not None and np.isnan(float(nodata)))
        # With the required exterior mask, all finite values should be inside
        # the footprint; this general range check is retained as a regression.
        checks["all_finite_values_in_0_1"] = finite_range
        if catalogue is not None:
            checks["zero_dots_on_mapped_catalogue"] = int((a[catalogue] > 0).sum()) == 0
    else:
        checks["no_nan_without_footprint"] = bool(not nan.any())
        checks["all_finite_values_in_0_1"] = finite_range
        if catalogue is not None:
            checks["zero_dots_on_mapped_catalogue"] = int((a[catalogue] > 0).sum()) == 0

    receipt = {
        "file": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "meta": meta,
        "band_description": list(desc),
        "n_finite": int(finite.sum()),
        "n_nan": int(nan.sum()),
        "n_infinite": int(infinite.sum()),
        "min": lo, "max": hi, "mean": mean,
        "emitted_positive_pixels": int(((a > 0) & finite).sum()),
        "checks": checks,
        "all_checks_passed": bool(all(checks.values())),
        "validation_class": "local format/range preflight; not organizer acceptance or uniqueness clearance",
    }
    if catalogue is not None:
        receipt["on_catalogue_positive_pixels"] = int((a[catalogue] > 0).sum())
    if footprint is not None:
        n_fp = int(footprint.sum())
        receipt["in_footprint_positive_pixels"] = int(((a > 0) & footprint).sum())
        receipt["footprint_pixels"] = n_fp
        receipt["outside_footprint_pixels"] = int((~footprint).sum())
        receipt["footprint_fraction"] = float(n_fp / footprint.size) if footprint.size else 0.0
        receipt["outside_footprint_nan_pixels"] = int(np.isnan(a[~footprint]).sum())
    return receipt


def assert_submittable(receipt: dict) -> None:
    """Raise unless every local format/range check passed (not organizer acceptance)."""
    bad = [k for k, v in receipt["checks"].items() if not v]
    if bad:
        raise AssertionError(f"submission fails the local format/range preflight: {bad}")
