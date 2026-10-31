"""Geophysical corroboration planes from the pinned ``training_features.tif``.

Lane extension (session 2, hypothesis block H57-G1/G2/G3/G5)
-----------------------------------------------------------
The fitted fault-zone-anatomy intensity is a *prior* for where secondary strands
sit.  These planes are the *likelihood*: independent geophysical edge/ridge,
curvature, conductivity, basement-edge and strain evidence, sampled from the
competition's own training-features stack (sha256-pinned in ``data/README.md``,
19 bands, EPSG:32611, identical grid to the submission format).

Every plane is robust-z scored inside the submission footprint
(``(x - median) / (1.4826 * MAD)``, clipped to ±10) so the GBM sees comparable
scales and so no band is trusted on its raw units.  Nothing here is derived from
the fault catalogue, so withholding catalogue segments cannot leak through these
features -- but the leakage canary is still run on every column, as required.

Band numbers are 1-based positions in ``training_features.tif`` as verified with
rasterio on the pinned bytes (2026-10-09):

    1 mag_anom            8 geod_dilaterate       15 depth_to_base_surf
    2 rtp                 9 tmi_vg                16 ieq_n100a15
    3 tmi_hg             10 deq_n100a15           17 cond_surf
    4 geod_2ndinv        11 iso_grav_anom_vg      18 iso_grav_anom_hg
    5 iso_grav_anom_slope 12 det_elev             19 det_elev_slope
    6 tc                 13 iso_grav_anom
    7 geod_shearrate     14 tmi
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "official"
FEATURES_PATH = DATA_DIR / "training_features.tif"

# 1-based band indices in training_features.tif
_BAND = {
    "tmi_hg": 3, "geod_2ndinv": 4, "iso_grav_anom_slope": 5, "tc": 6,
    "geod_shearrate": 7, "det_elev": 12, "depth_to_base_surf": 15,
    "cond_surf": 17, "iso_grav_anom_hg": 18, "det_elev_slope": 19,
}

# The feature block appended to gems57.anatomy.FEATURES when geo planes are used.
GEO_FEATURES = (
    "g_tmi_hg",     # H57-G1: magnetic horizontal-gradient edge/ridge
    "g_tc",         # H57-G1: tilt-derivative edge
    "g_slope",      # H57-G1: detrended-elevation slope (scarp)
    "g_grav_hg",    # H57-G1: isostatic-gravity horizontal-gradient edge
    "g_curv",       # H57-G1: curvature (Laplacian of detrended elevation)
    "g_edge_max",   # H57-G1: multi-method edge consensus (max of the four)
    "g_cond",       # H57-G2: conductivity surface (clay-cap / alteration)
    "g_base_edge",  # H57-G3: gradient magnitude of depth-to-basement
    "g_strain",     # H57-G5: geodetic second invariant (strain-rate magnitude)
)

_ROBUST_CLIP = 10.0


def _robust_z(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Median/MAD z-score inside ``mask``, clipped to ±10; 0 outside."""
    v = a[mask].astype(np.float64)
    v = v[np.isfinite(v)]
    out = np.zeros(a.shape, np.float32)
    if v.size == 0:
        return out
    med = np.median(v)
    mad = np.median(np.abs(v - med)) * 1.4826
    if not np.isfinite(mad) or mad <= 0:
        mad = max(float(np.std(v)), 1e-6)
    z = (a.astype(np.float64) - med) / mad
    np.clip(z, -_ROBUST_CLIP, _ROBUST_CLIP, out=z)
    out[mask] = z[mask].astype(np.float32)
    return out


def load_planes(footprint: np.ndarray, path: Path | None = None) -> dict[str, np.ndarray]:
    """Load and robust-z score every plane in :data:`GEO_FEATURES`.

    ``footprint`` is the submission footprint (finite cells of
    ``sample_submission.tif``); the robust statistics are computed on it only, so
    nodata cells outside the study area never influence the scaling.
    """
    p = Path(path) if path else FEATURES_PATH
    if not p.exists():
        raise FileNotFoundError(
            f"{p} missing — run scripts/prepare_data.py --fetch to assemble the "
            "pinned feature stack from the sha256-verified bridge parts")
    fp = np.asarray(footprint, bool)
    raw: dict[str, np.ndarray] = {}
    with rasterio.open(p) as src:
        if (src.height, src.width) != fp.shape:
            raise ValueError(f"feature stack grid {src.shape} != footprint {fp.shape}")
        for name, bidx in _BAND.items():
            raw[name] = src.read(bidx)
    planes = {
        "g_tmi_hg": _robust_z(raw["tmi_hg"], fp),
        "g_tc": _robust_z(raw["tc"], fp),
        "g_slope": _robust_z(raw["det_elev_slope"], fp),
        "g_grav_hg": _robust_z(raw["iso_grav_anom_hg"], fp),
        "g_cond": _robust_z(raw["cond_surf"], fp),
        "g_strain": _robust_z(raw["geod_2ndinv"], fp),
    }
    # Derived transforms.  Two numerical traps, both hit in the first smoke run:
    # the stack carries huge sentinels outside the footprint and float32
    # differencing overflows on them.  Scrub non-finite/sentinel cells to the
    # in-footprint median and difference in float64.
    def _clean(a: np.ndarray) -> np.ndarray:
        v = a.astype(np.float64)
        bad = ~np.isfinite(v) | (np.abs(v) > 1e18)
        fill = float(np.median(v[fp & np.isfinite(v) & (np.abs(v) <= 1e18)])) \
            if (fp & np.isfinite(v) & (np.abs(v) <= 1e18)).any() else 0.0
        v[bad] = fill
        return v

    elev = _clean(raw["det_elev"])
    lap = ndi.laplace(elev)
    planes["g_curv"] = _robust_z(lap, fp)
    # basement-cover contrast: gradient magnitude of the depth-to-basement surface
    base = _clean(raw["depth_to_base_surf"])
    gy, gx = np.gradient(base)
    planes["g_base_edge"] = _robust_z(np.hypot(gy, gx), fp)
    # multi-method edge consensus: max of the four robust-z edge planes
    planes["g_edge_max"] = np.maximum.reduce(
        [planes["g_tmi_hg"], planes["g_tc"], planes["g_slope"], planes["g_grav_hg"]])
    out = {k: planes[k] for k in GEO_FEATURES}
    for k, v in out.items():
        if v.shape != fp.shape or v.dtype != np.float32:
            raise ValueError(f"plane {k} has wrong shape/dtype")
    return out


# ---------------------------------------------------------------------------
# Opt-in signed paired-flank block (research queue rank 1, 2026-10-31).
#
# Local Pearson correlation, over a 7x7 cell window (700 m), between the
# detrended elevation and two potential-field planes: reduced-to-pole magnetics
# (band 2) and isostatic gravity anomaly (band 13).  Unlike the unsigned edge
# planes above, the sign records polarity: a buried basin margin that offsets
# both the topographic step and the potential-field contrast in the same sense
# gives a coherent sign; a lithologic contact with no relief generally does not.
# These are static rasters, not catalogue-derived, so they cannot leak the
# withholding mask; they still pass through the leakage canary like every column.
# This block is opt-in and is NOT part of GEO_FEATURES, so the shipped geo
# matrix and its recorded results are unchanged.
# ---------------------------------------------------------------------------

PAIRED_FEATURES = (
    "p_corr_elev_mag",   # signed local r(det_elev, rtp), window 7x7
    "p_corr_elev_grav",  # signed local r(det_elev, iso_grav_anom), window 7x7
)
_PAIRED_BAND = {"rtp": 2, "iso_grav_anom": 13}
_PAIRED_WIN = 7


def _local_pearson(a: np.ndarray, b: np.ndarray, valid: np.ndarray,
                   win: int = _PAIRED_WIN) -> np.ndarray:
    """Signed Pearson r in a ``win`` x ``win`` box over ``valid`` cells only; 0 elsewhere."""
    w = valid.astype(np.float64)
    a = np.where(valid, a, 0.0)
    b = np.where(valid, b, 0.0)
    cnt = ndi.uniform_filter(w, size=win, mode="constant") * (win * win)
    cnt = np.maximum(cnt, 1.0)
    ma = ndi.uniform_filter(a, size=win, mode="constant") * (win * win) / cnt
    mb = ndi.uniform_filter(b, size=win, mode="constant") * (win * win) / cnt
    saa = ndi.uniform_filter(a * a, size=win, mode="constant") * (win * win) / cnt - ma * ma
    sbb = ndi.uniform_filter(b * b, size=win, mode="constant") * (win * win) / cnt - mb * mb
    sab = ndi.uniform_filter(a * b, size=win, mode="constant") * (win * win) / cnt - ma * mb
    denom = np.sqrt(np.maximum(saa, 0.0) * np.maximum(sbb, 0.0))
    r = np.where(denom > 1e-12, sab / np.maximum(denom, 1e-12), 0.0)
    r = np.clip(r, -1.0, 1.0)
    r[~valid] = 0.0
    return r.astype(np.float32)


def paired_planes(footprint: np.ndarray, path: Path | None = None) -> dict[str, np.ndarray]:
    """Signed paired-flank correlation planes (opt-in, see block comment above)."""
    p = Path(path) if path else FEATURES_PATH
    if not p.exists():
        raise FileNotFoundError(f"{p} missing -- run scripts/prepare_data.py --fetch")
    fp = np.asarray(footprint, bool)
    raw = {}
    with rasterio.open(p) as src:
        if (src.height, src.width) != fp.shape:
            raise ValueError(f"feature stack grid {src.shape} != footprint {fp.shape}")
        for name, bidx in (("det_elev", 12), *_PAIRED_BAND.items()):
            raw[name] = src.read(bidx).astype(np.float64)

    def _clean(v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        ok = fp & np.isfinite(v) & (np.abs(v) <= 1e18)
        fill = float(np.median(v[ok])) if ok.any() else 0.0
        out = np.where(ok, v, fill)
        return out, ok

    elev, ok_e = _clean(raw["det_elev"])
    rtp, ok_r = _clean(raw["rtp"])
    grav, ok_g = _clean(raw["iso_grav_anom"])
    # Only cells where all three fields are real take part in the correlation.
    valid = fp & ok_e & ok_r & ok_g
    return {
        "p_corr_elev_mag": _local_pearson(elev, rtp, valid),
        "p_corr_elev_grav": _local_pearson(elev, grav, valid),
    }
