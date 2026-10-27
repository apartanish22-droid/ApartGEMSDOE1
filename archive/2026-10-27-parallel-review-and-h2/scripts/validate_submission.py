#!/usr/bin/env python3
<<<<<<< HEAD
"""APARTGEMSDOE1 submission validator + Parallel-Run Protocol lane checks.

1. 12-point GeoTIFF audit (reuses gems32.submission.audit_geotiff): CRS EPSG:32611,
   shape 3730x3292, transform matching sample_submission.tif, float32, values in [0,1]
   inside the footprint, zero NaN/sentinel inside the footprint (zeros variant: zero
   NaN anywhere), zero on catalogue faults.
2. LANE check (Protocol Rule 1): rank (Spearman) correlation of our raster against every
   restored registry/scored raster; flag if any |rho| > 0.90. Also flag if >70% of our
   emitted dots fall within 3 px of one registry raster's dots.
   Duplicates are logged and the run card verdict must not be "promote".
=======
"""Inspect a GeoTIFF against a supplied template, without authorizing upload.

Template provenance and organizer acceptance are never established by this
checker. It validates saved bytes, exact grid, one float32 band, finite [0, 1]
values inside the reference footprint, and null/masked cells outside that
footprint as described in the official format. An outside-null vs all-finite
portal-encoding discrepancy remains unresolved. No value is silently repaired.

Exit 0: matches the *supplied* template and local format checks, not approval.
Exit 1: format failure. Exit 2: template absent or an input could not be read.
>>>>>>> origin/main
"""
from __future__ import annotations

import argparse
<<<<<<< HEAD
=======
import hashlib
>>>>>>> origin/main
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
<<<<<<< HEAD
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gems32.paths import data_dir, downloads_dir  # noqa: E402
from gems32.submission import audit_geotiff  # noqa: E402
from gems32.grid import read_labels, sha256  # noqa: E402


def rho_safe(a: np.ndarray, b: np.ndarray) -> float:
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 10:
        return float("nan")
    try:
        return float(spearmanr(a[m], b[m])[0])
    except Exception:
        return float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("geotiff", type=Path, help="-zeros.tif submission to validate")
    ap.add_argument("--registry", type=Path, default=None,
                    help="Directory of registry/scored rasters (default: data/scored)")
    ap.add_argument("--template", type=Path, default=None)
    args = ap.parse_args()

    ddir = data_dir()
    template = args.template or (ddir / "sample_submission.tif")
    registry_dir = args.registry or (ddir / "scored")

    import rasterio as _rio
    with _rio.open(template) as tpl:
        foot = np.isfinite(tpl.read(1))
    labels = read_labels(ddir / "labels.tif") & foot

    with _rio.open(args.geotiff) as src:
        arr = src.read(1).astype(np.float64)
        crs = src.crs
        transform = src.transform

    report = audit_geotiff(args.geotiff, foot, labels, mode="zeros", template_tif=template)

    # ---- LANE checks ----
    lane = {"registry_rasters_checked": [], "max_abs_rho": 0.0, "lane_violation": False,
            "dot_overlap_violation": False, "degenerate_references": []}
    registry_paths = sorted(registry_dir.glob("*.tif")) if registry_dir.exists() else []
    our_dots = (arr > 0) & foot
    if our_dots.any():
        d_to_our = distance_transform_edt(~our_dots)
    for rp in registry_paths:
        try:
            with _rio.open(rp) as ds:
                reg = ds.read(1).astype(np.float64)
            reg_same_grid = (ds.shape == arr.shape and ds.transform == transform)
        except Exception as exc:
            lane["registry_rasters_checked"].append({"file": rp.name, "error": str(exc)})
            continue
        rho = rho_safe(arr, reg)
        entry = {
            "file": rp.name, "same_grid": bool(reg_same_grid),
            "spearman_rho": None if np.isnan(rho) else round(rho, 4),
            "flag_rho_gt_090": bool(not np.isnan(rho) and abs(rho) > 0.90),
        }
        if not np.isnan(rho) and abs(rho) > 0.90:
            lane["lane_violation"] = True
        lane["max_abs_rho"] = max(lane["max_abs_rho"], abs(rho) if not np.isnan(rho) else 0.0)
        if our_dots.any() and (reg > 0).any():
            reg_dots = (reg > 0)
            reg_density = float(reg_dots.sum() / float(foot.sum()))
            entry["registry_dot_density"] = round(reg_density, 4)
            # A near-universal lattice / background reference overlaps every dotted field by
            # construction; it is not a submission lane, so it is logged rather than tripped.
            if reg_density > 0.02:
                entry["degenerate_reference"] = True
                lane["degenerate_references"].append(rp.name)
            else:
                d_reg = distance_transform_edt(~reg_dots)
                near = float((d_reg[our_dots] <= 3.0).mean())
                entry["our_dots_within_3px_of_registry_dots"] = round(near, 4)
                entry["flag_overlap_gt_70pct"] = bool(near > 0.70)
                if near > 0.70:
                    lane["dot_overlap_violation"] = True
        lane["registry_rasters_checked"].append(entry)

    verdict = "promote" if (report["all_checks_passed"] and not lane["lane_violation"]
                            and not lane["dot_overlap_violation"]) else "negative"
    out = {"schema_version": "apartgemsdoe1-validate-v1",
           "file": str(args.geotiff), "sha256": sha256(args.geotiff), "bytes": args.geotiff.stat().st_size,
           "crs": str(crs), "transform": [round(float(v), 4) for v in transform][:6],
           "audit": report, "lane": lane, "verdict": verdict}
    print(json.dumps(out, indent=2))
    sidecar = args.geotiff.with_suffix(".validate.json")
    sidecar.write_text(json.dumps(out, indent=2) + "\n")
    print(f"[VALIDATE] verdict={verdict} sidecar={sidecar}")
    return 0 if verdict == "promote" else 1


if __name__ == "__main__":
=======

EXPECTED_CRS = 'EPSG:32611'
EXPECTED_SHAPE = (3730, 3292)
EXPECTED_PIXEL_M = 100.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def signature(ds) -> dict:
    return {'crs': str(ds.crs) if ds.crs else None,
            'shape': [int(ds.height), int(ds.width)],
            'transform': list(ds.transform),
            'count': int(ds.count), 'dtype': str(ds.dtypes[0])}


def validate(candidate: Path, template: Path | None = None) -> dict:
    """Return strict machine-readable checks; both paths are untrusted inputs."""
    candidate = Path(candidate)
    report = {
        'file': str(candidate), 'sha256': sha256_file(candidate),
        'template_file': str(template) if template is not None else None,
        'template_sha256': sha256_file(Path(template)) if template is not None else None,
        'template_organizer_authenticated': None,
        'template_provenance_note': 'Caller supplied; organizer origin not established by this check.',
        'slot_approved': False, 'organizer_acceptance_established': False,
        'checks': {}, 'errors': [], 'format_pass': False, 'verdict': None,
        'outside_encoding_caveat': (
            'Official wording describes null outside the footprint; prior portal range '
            'rejection makes actual acceptance unresolved. This is not a portal receipt.'),
    }
    with rasterio.open(candidate) as ds:
        sig = signature(ds)
        arr = ds.read(1, masked=False)
        valid_mask = ds.read_masks(1) > 0
    checks, errors = report['checks'], report['errors']
    checks['candidate'] = sig
    checks['single_band'] = sig['count'] == 1
    checks['float32'] = sig['dtype'] == 'float32'
    checks['competition_crs'] = sig['crs'] == EXPECTED_CRS
    checks['competition_shape'] = tuple(sig['shape']) == EXPECTED_SHAPE
    a, b, _, d, e, _ = sig['transform'][:6]
    checks['competition_pixel_geometry'] = (a == EXPECTED_PIXEL_M and e == -EXPECTED_PIXEL_M
                                             and b == 0.0 and d == 0.0)
    whole_finite = np.isfinite(arr)
    checks['n_nan_whole_array'] = int(np.isnan(arr).sum())
    checks['n_inf_whole_array'] = int(np.isinf(arr).sum())
    checks['positive_pixels_whole_array'] = int((whole_finite & (arr > 0)).sum())
    finite_values = arr[whole_finite]
    checks['value_min_finite_whole_array'] = float(finite_values.min()) if finite_values.size else None
    checks['value_max_finite_whole_array'] = float(finite_values.max()) if finite_values.size else None
    checks['all_values_finite_and_in_range_whole_array'] = bool(
        whole_finite.all() and (arr >= 0).all() and (arr <= 1).all())
    if not checks['single_band']:
        errors.append('candidate must have exactly one band')
    if not checks['float32']:
        errors.append('candidate must use float32 dtype')
    if not checks['competition_crs']:
        errors.append('CRS differs from documented EPSG:32611')
    if not checks['competition_shape']:
        errors.append('shape differs from documented competition grid')
    if not checks['competition_pixel_geometry']:
        errors.append('pixel geometry differs from unrotated 100 m grid')
    if checks['n_inf_whole_array']:
        errors.append('infinity is not a valid null or prediction')

    if template is None:
        checks['template_crs_match'] = None
        checks['template_shape_match'] = None
        checks['template_transform_match'] = None
        checks['finite_in_footprint'] = None
        checks['in_range_in_footprint'] = None
        checks['outside_null'] = None
        report['verdict'] = 'RESEARCH_ONLY_TEMPLATE_REQUIRED' if not errors else 'DO_NOT_SUBMIT_FORMAT_FAILURE'
        return report

    with rasterio.open(template) as ds:
        template_sig = signature(ds)
        # Some references store NaNs without a nodata tag. Such cells cannot
        # define a valid footprint even when GDAL reports their mask as valid.
        foot = (ds.read_masks(1) > 0) & np.isfinite(ds.read(1, masked=False))
    checks['template'] = template_sig
    checks['template_crs_match'] = bool(sig['crs'] is not None and sig['crs'] == template_sig['crs'])
    checks['template_shape_match'] = sig['shape'] == template_sig['shape']
    checks['template_transform_match'] = sig['transform'] == template_sig['transform']
    checks['template_single_band'] = template_sig['count'] == 1
    checks['template_footprint_nonempty'] = bool(foot.any())
    for key, message in [
        ('template_crs_match', 'CRS mismatch'),
        ('template_shape_match', 'shape mismatch'),
        ('template_transform_match', 'transform mismatch'),
        ('template_single_band', 'template must have exactly one band'),
        ('template_footprint_nonempty', 'template footprint is empty'),
    ]:
        if not checks[key]:
            errors.append(message)

    # A footprint in another CRS, affine origin or shape is NOT an aligned mask.
    aligned = all(checks[key] for key in ('template_crs_match', 'template_shape_match',
                                          'template_transform_match', 'template_footprint_nonempty'))
    checks['aligned_for_footprint'] = aligned
    if aligned:
        inside = arr[foot]
        finite = np.isfinite(inside)
        checks['inside_pixels'] = int(inside.size)
        checks['finite_in_footprint'] = bool(finite.all())
        checks['n_nonfinite_in_footprint'] = int((~finite).sum())
        checks['masked_cells_in_footprint'] = int((~valid_mask[foot]).sum())
        checks['in_range_in_footprint'] = bool(finite.all() and (inside >= 0).all() and (inside <= 1).all())
        checks['value_min_inside'] = float(inside[finite].min()) if finite.any() else None
        checks['value_max_inside'] = float(inside[finite].max()) if finite.any() else None
        outside = ~foot
        # Nodata masks and NaNs are null representations; infinity is rejected
        # everywhere. The interior remains strictly finite and unmasked.
        outside_is_null = (~valid_mask[outside]) | np.isnan(arr[outside])
        checks['outside_pixels'] = int(outside.sum())
        checks['outside_nonnull_pixels'] = int((~outside_is_null).sum())
        checks['outside_null'] = bool(outside_is_null.all())
        if not checks['finite_in_footprint']:
            errors.append('NaN or infinity inside footprint')
        if checks['masked_cells_in_footprint']:
            errors.append('masked/invalid cells inside footprint')
        if not checks['in_range_in_footprint']:
            errors.append('values outside [0,1] or non-finite inside footprint')
        if not checks['outside_null']:
            errors.append('nonnull cells outside the template footprint')
    else:
        for key in ('inside_pixels', 'finite_in_footprint', 'n_nonfinite_in_footprint',
                    'masked_cells_in_footprint', 'in_range_in_footprint', 'value_min_inside',
                    'value_max_inside', 'outside_pixels', 'outside_nonnull_pixels', 'outside_null'):
            checks[key] = None

    report['format_pass'] = not errors
    report['verdict'] = 'FORMAT_MATCH_ONLY_NOT_AUTHORIZED' if not errors else 'DO_NOT_SUBMIT_FORMAT_FAILURE'
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--template', type=Path, help='reference grid and valid footprint (not automatically authenticated)')
    parser.add_argument('--json-out', type=Path, help='also save the machine-readable report')
    args = parser.parse_args()
    try:
        report = validate(args.candidate, args.template)
        encoded = json.dumps(report, indent=2, allow_nan=False) + '\n'
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(encoded, encoding='utf-8')
        print(encoded, end='')
        if args.template is None:
            print('STOP: supplied template required; no format clearance', file=sys.stderr)
            return 2
        if report['format_pass']:
            c = report['checks']
            print(f"PASS (format only, not upload approval): min={c['value_min_inside']:g} "
                  f"max={c['value_max_inside']:g} sha256={report['sha256']}")
            return 0
        if report['errors']:
            print('FAIL: ' + '; '.join(report['errors']), file=sys.stderr)
            return 1
        print('STOP: supplied template required; no format clearance', file=sys.stderr)
        return 2
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        print(f'FAIL: unable to inspect raster or template: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
>>>>>>> origin/main
    raise SystemExit(main())
