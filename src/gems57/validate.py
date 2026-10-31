"""Local preflight validation for a GEMS submission GeoTIFF.

Checks grid metadata and the project's conservative all-finite, ``[0,1]``
export policy. The portal error's cause remains unproven (IR-57-NAN-02); zero
outside the mirror footprint may not satisfy the organizer's outside-bounds
null/NaN instruction. A local PASS is not organizer acceptance or uniqueness.
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


def validate(path: Path, footprint: np.ndarray | None = None,
             catalogue: np.ndarray | None = None) -> dict:
    """Run local format/range checks on one GeoTIFF; return a receipt dict."""
    path = Path(path)
    with rasterio.open(path) as ds:
        a = ds.read(1)
        meta = dict(crs=str(ds.crs), shape=[ds.height, ds.width], dtype=ds.dtypes[0],
                    count=ds.count, nodata=None if ds.nodata is None else float(ds.nodata),
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
    has_finite = bool(finite.any())
    finite_values = a[finite]
    lo = float(finite_values.min()) if has_finite else None
    hi = float(finite_values.max()) if has_finite else None
    mean = float(finite_values.mean()) if has_finite else None
    in_range = bool(has_finite and lo >= 0.0 and hi <= 1.0)
    checks = {
        "single_band": meta["count"] == 1,
        "dtype_float32": meta["dtype"] == "float32",
        f"dimensions_{HEIGHT}x{WIDTH}": (h, w) == (HEIGHT, WIDTH),
        f"crs_epsg_{EPSG}": meta["crs"] == f"EPSG:{EPSG}",
        "transform_matches_sample_submission": meta["transform"] == list(tuple(TRANSFORM)[:6]),
        "no_nan_anywhere": bool(finite.all()),
        "no_inf_anywhere": bool(not np.isinf(a).any()),
        "no_sentinel_values": bool(not np.isin(finite_values, SENTINELS).any()),
        "range_0_1_guaranteed": in_range,
        "min_ge_0": bool(has_finite and lo >= 0.0),
        "max_le_1": bool(has_finite and hi <= 1.0),
    }
    if footprint is not None:
        n_fp = int(footprint.sum())
        checks["in_footprint_all_finite"] = bool(n_fp > 0 and finite[footprint].all())
        checks["in_footprint_range_0_1"] = bool(
            n_fp > 0 and np.isfinite(a[footprint]).all()
            and (a[footprint] >= 0.0).all() and (a[footprint] <= 1.0).all())
        checks["outside_footprint_zero"] = bool(np.all(a[~footprint] == 0.0))
    if catalogue is not None:
        checks["zero_dots_on_mapped_catalogue"] = int((a[catalogue] > 0).sum()) == 0

    receipt = {
        "file": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "meta": meta,
        "band_description": list(desc),
        "n_finite": int(finite.sum()),
        "n_nan": int(np.isnan(a).sum()),
        "n_infinite": int(np.isinf(a).sum()),
        "min": lo, "max": hi, "mean": mean,
        "emitted_positive_pixels": int((a > 0).sum()),
        "checks": checks,
        "all_checks_passed": bool(all(checks.values())),
        "validation_class": "local format/range preflight; not organizer acceptance or uniqueness clearance",
    }
    if catalogue is not None:
        receipt["on_catalogue_positive_pixels"] = int((a[catalogue] > 0).sum())
    if footprint is not None:
        n_fp = int(footprint.sum())
        receipt["in_footprint_positive_pixels"] = int((a[footprint] > 0).sum())
        receipt["footprint_fraction"] = float(receipt["in_footprint_positive_pixels"] / n_fp) if n_fp else 0.0
    return receipt


def assert_submittable(receipt: dict) -> None:
    """Raise unless every local format/range check passed (not organizer acceptance)."""
    bad = [k for k, v in receipt["checks"].items() if not v]
    if bad:
        raise AssertionError(f"submission fails the local format/range preflight: {bad}")


def validate_template(path: Path, footprint: np.ndarray, catalogue: np.ndarray | None = None,
                      sample: Path | None = None) -> dict:
    """Validate the OFFICIAL-TEMPLATE convention (outside bounds = NaN).

    The published rule says data outside the bounds is null or NaN, and the
    official sample template has NaN exactly outside the footprint with nodata NaN.
    This validator requires the same NaN mask as the sample template (when
    ``sample`` is given) or as ``~footprint``, finite float32 values in [0,1]
    inside the footprint, no infinities or sentinels, and no positive dots on the
    mapped catalogue. It does not clip, fill, or repair anything.
    A PASS here is a local format check, not organizer acceptance.
    """
    path = Path(path)
    with rasterio.open(path) as ds:
        a = ds.read(1)
        # NaN is written as the string "NaN": the receipt is strict JSON (allow_nan=False).
        nd = ds.nodata
        nodata_repr = None if nd is None else ("NaN" if np.isnan(nd) else float(nd))
        meta = dict(crs=str(ds.crs), shape=[ds.height, ds.width], dtype=ds.dtypes[0],
                    count=ds.count, nodata=nodata_repr,
                    transform=list(tuple(ds.transform)[:6]))
    fp = np.asarray(footprint, dtype=bool)
    if a.shape != fp.shape:
        raise ValueError(f"raster shape {a.shape} != footprint {fp.shape}")
    nan = np.isnan(a)
    inside = a[fp]
    checks = {
        "single_band": meta["count"] == 1,
        "dtype_float32": meta["dtype"] == "float32",
        f"dimensions_{HEIGHT}x{WIDTH}": (a.shape == (HEIGHT, WIDTH)),
        f"crs_epsg_{EPSG}": meta["crs"] == f"EPSG:{EPSG}",
        "transform_matches_sample_submission": meta["transform"] == list(tuple(TRANSFORM)[:6]),
        "nodata_is_nan": meta["nodata"] == "NaN",
        "no_inf_anywhere": bool(not np.isinf(a).any()),
        "inside_footprint_all_finite": bool(np.isfinite(inside).all()),
        "inside_footprint_range_0_1": bool(np.isfinite(inside).all() and (inside >= 0.0).all()
                                           and (inside <= 1.0).all()),
        "outside_footprint_all_nan": bool(nan[~fp].all()),
        "nan_mask_equals_footprint_complement": bool(np.array_equal(nan, ~fp)),
        "no_sentinel_values": bool(not np.isin(inside, SENTINELS).any()),
        "no_positive_on_catalogue": True,
    }
    if sample is not None:
        with rasterio.open(sample) as ref:
            ref_nan = np.isnan(ref.read(1))
        checks["nan_mask_equals_sample_template"] = bool(np.array_equal(nan, ref_nan))
    if catalogue is not None:
        cat = np.asarray(catalogue, dtype=bool)
        checks["no_positive_on_catalogue"] = int((np.nan_to_num(a, nan=0.0)[cat] > 0).sum()) == 0
    receipt = {
        "file": str(path), "sha256": sha256(path), "bytes": path.stat().st_size,
        "meta": meta, "checks": checks,
        "all_checks_passed": bool(all(checks.values())),
        "n_positive_dots": int((np.nan_to_num(a, nan=0.0) > 0).sum()),
        "n_inside_footprint": int(fp.sum()),
        "policy": "official-template NaN outside bounds (validate_template)",
    }
    return receipt
