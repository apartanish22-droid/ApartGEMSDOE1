"""AP1-SNRC: label-free scarp-normal radiometric contrast; no registry inputs.

Only the placement function accepts a visible-catalogue mask, to exclude those
pixels exactly. No held-out labels are used for transforms or normalization.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, map_coordinates


def normalized(values, valid, lower=5.0, upper=99.5):
    values = np.asarray(values, dtype=np.float32)
    valid = np.asarray(valid, dtype=bool) & np.isfinite(values)
    out = np.zeros(values.shape, dtype=np.float32)
    if not valid.any():
        return out
    lo, hi = np.percentile(values[valid], [lower, upper])
    if hi > lo:
        out[valid] = np.clip((values[valid] - lo) / (hi - lo), 0, 1)
    return out


def weighted_smooth(values, valid, sigma):
    values = np.asarray(values, dtype=np.float32)
    valid = np.asarray(valid, dtype=bool) & np.isfinite(values)
    weight = gaussian_filter(valid.astype(np.float32), sigma, mode="nearest")
    numerator = gaussian_filter(np.where(valid, values, 0), sigma, mode="nearest")
    return np.divide(numerator, weight, out=np.zeros_like(numerator), where=weight > 1e-6)


def dequantize(q, scale, *, squared=True):
    """Invert the documented LiDAR monotone quantization; missing is NaN."""
    q = np.asarray(q)
    unit = np.maximum(q.astype(np.float32) - 1, 0) / 254
    values = (unit**2 if squared else unit) * scale
    return np.where(q > 0, values, np.nan).astype(np.float32)


def normal_contrast(values, azimuth, distance_px=3.0):
    """Paired difference normal to strike (clockwise from north).

    Grid normal is (row=sin(strike), col=cos(strike)). Source convention was
    checked in 7GEMSDOE scripts/dem_merge.py derive(), not inferred from a name.
    """
    values = np.asarray(values, dtype=np.float32)
    azimuth = np.asarray(azimuth, dtype=np.float32)
    if values.ndim != 2 or azimuth.shape != values.shape:
        raise ValueError("Aligned 2D contrast/azimuth arrays required")
    yy, xx = np.indices(values.shape, dtype=np.float32)
    dy, dx = distance_px * np.sin(azimuth), distance_px * np.cos(azimuth)
    a = map_coordinates(values, [yy + dy, xx + dx], order=1, mode="nearest", prefilter=False)
    b = map_coordinates(values, [yy - dy, xx - dx], order=1, mode="nearest", prefilter=False)
    return np.abs(a - b).astype(np.float32)


def build_fields(*, footprint, lidar, potassium, thorium, rtp, contrast_exponent=0.5):
    """Build the preregistered field. Inputs deliberately have no catalogue argument."""
    fp = np.asarray(footprint, dtype=bool)
    if fp.ndim != 2 or min(fp.shape) < 2:
        raise ValueError("A two-dimensional footprint with dimensions >= 2 is required")
    if set(lidar) != {"ex", "step", "crest", "toe", "relief", "coherence", "strike", "valid"}:
        raise ValueError("Exactly the declared LiDAR descriptors are required")
    if any(np.shape(v) != fp.shape for v in [*lidar.values(), potassium, thorium, rtp]):
        raise ValueError("All source channels must be aligned")
    if not np.isfinite(contrast_exponent) or contrast_exponent <= 0:
        raise ValueError("Contrast exponent must be positive and finite")
    rtp = np.asarray(rtp, dtype=np.float32)
    available = fp & (np.asarray(lidar["valid"]) > 0) & (potassium > 0) & (thorium > 0) & np.isfinite(rtp)
    for name in ("ex", "step", "crest", "toe", "relief", "coherence", "strike"):
        available &= np.isfinite(lidar[name])
    if not available.any():
        raise ValueError("No common source support; do not fabricate a prediction")
    # Do not let missing data create a high-contrast padding silhouette.
    supported = available & (distance_transform_edt(available) > 5)
    if not supported.any():
        raise ValueError("No interior support after source-boundary exclusion")
    k = np.asarray(potassium, dtype=np.float32) / 255
    th = np.asarray(thorium, dtype=np.float32) / 255
    # This is a difference of rank proxies, not a physical K/Th concentration.
    residual = (k - weighted_smooth(k, available, 12)) - (th - weighted_smooth(th, available, 12))
    theta = np.deg2rad(np.nan_to_num(lidar["strike"], nan=0))
    cross = normalized(normal_contrast(residual, theta), supported)
    ex = normalized(lidar["ex"], supported)
    step = normalized(lidar["step"], supported)
    crest = normalized(lidar["crest"], supported)
    toe = normalized(lidar["toe"], supported)
    paired_curvature = np.sqrt(crest * toe)
    coherence = np.clip(np.nan_to_num(lidar["coherence"], nan=0), 0, 1)
    relief = np.maximum(np.nan_to_num(lidar["relief"], nan=0), 0)
    scarp = np.cbrt(ex * step * paired_curvature) * (0.25 + 0.75 * coherence) / (1 + relief / 100)
    smoothed_rtp = weighted_smooth(rtp, np.isfinite(rtp) & fp, 1)
    gy, gx = np.gradient(smoothed_rtp, 100)
    magnetic = normalized(np.hypot(gx, gy), supported)
    candidate = scarp * (0.15 + 0.85 * cross**contrast_exponent) * (0.5 + 0.5 * magnetic)
    scarp = np.where(supported, scarp, 0).astype(np.float32)
    candidate = np.where(supported, candidate, 0).astype(np.float32)
    # All descriptors and the actual output field are checked independently.
    canary = {
        "K_rank_source": np.where(available, k, np.nan),
        "Th_rank_source": np.where(available, th, np.nan),
        "rtp_source": np.where(fp, rtp, np.nan),
        **{f"lidar_{name}": np.where(available, lidar[name], np.nan)
           for name in ("ex", "step", "crest", "toe", "relief", "coherence")},
        "strike_cos2": np.where(available, np.cos(2 * theta), np.nan),
        "strike_sin2": np.where(available, np.sin(2 * theta), np.nan),
        "rank_residual": np.where(available, residual, np.nan),
        "normal_contrast": np.where(supported, cross, np.nan),
        "paired_curvature": np.where(supported, paired_curvature, np.nan),
        "magnetic_gradient": np.where(supported, magnetic, np.nan),
        "source_support": supported.astype(np.float32),
        "scarp_ablation": scarp,
        "candidate_field": candidate,
    }
    return {"candidate": candidate, "baseline": scarp, "support": supported, "canary_features": canary}


def spaced_dots(score, eligible, budget, *, separation_px=3.0):
    """Deterministic greedy field sampling, no truth/registry-based gap filling."""
    score = np.asarray(score)
    eligible_raw = np.asarray(eligible)
    if score.ndim != 2 or eligible_raw.shape != score.shape or not np.isin(eligible_raw, (0, 1)).all():
        raise ValueError("Aligned score and finite binary eligibility required")
    if type(budget) is not int or budget < 0 or not np.isfinite(separation_px) or separation_px <= 0:
        raise ValueError("Nonnegative integer budget and positive finite separation required")
    if not np.isfinite(score[eligible_raw.astype(bool)]).all():
        raise ValueError("Eligible scores must be finite")
    eligible = eligible_raw.astype(bool)
    ids = np.flatnonzero(eligible & (score > 0))
    out = np.zeros(score.shape, dtype=bool)
    if budget == 0 or not len(ids):
        return out
    order = np.lexsort((ids, -score.ravel()[ids]))
    blocked = np.zeros(score.shape, dtype=bool)
    radius = int(np.ceil(separation_px))
    offsets = [(dy, dx) for dy in range(-radius, radius + 1) for dx in range(-radius, radius + 1)
               if dy * dy + dx * dx < separation_px**2]
    h, w = score.shape
    selected = 0
    for index in ids[order]:
        y, x = divmod(int(index), w)
        if blocked[y, x]:
            continue
        out[y, x] = True
        selected += 1
        if selected == budget:
            break
        for dy, dx in offsets:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                blocked[yy, xx] = True
    return out
