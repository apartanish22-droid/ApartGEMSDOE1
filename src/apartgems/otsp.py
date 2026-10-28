"""H-APART-6 Orientation-Transported Scale Persistence (OTSP).

This module stays in the pre-registered MAW-GSI structural-lineament lane.  It uses
only (a) blind, independently measured topography/gravity layers and (b) a fault
mask supplied by the caller.  Holdout callers MUST pass only ``fold['visible']``;
live inference may pass the complete catalogue.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from gems57.grid import Grid
from .features import _load_band_sanitized, _unpack_fp

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache/apartgems_otsp_v3"
STATIC_NAMES = (
    "topo_c2",
    "topo_s2",
    "topo_persistence",
    "topo_strength",
    "grav_c2",
    "grav_s2",
    "grav_persistence",
    "grav_strength",
    "topo_grav_coherence",
)


def _robust01(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Robustly map finite values to [0, 1] without catalogue information."""
    out = np.zeros(a.shape, dtype=np.float32)
    v = a[mask & np.isfinite(a)]
    if v.size == 0:
        return out
    lo, hi = np.percentile(v, [35.0, 98.5])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return out
    out[mask] = np.clip((a[mask] - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)
    return out


def _gradient_tangent(field: np.ndarray, fp: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return axial tangent cos(2 theta), sin(2 theta), and gradient strength."""
    finite = fp & np.isfinite(field)
    fill = float(np.median(field[finite])) if finite.any() else 0.0
    clean = np.where(finite, field, fill).astype(np.float32)
    gy = ndi.gaussian_filter(clean, sigma=sigma, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(clean, sigma=sigma, order=(0, 1), mode="nearest")
    den = gx * gx + gy * gy
    safe = den + np.float32(1e-12)
    # Gradient is normal to a scalar-field contact; negate its doubled-angle
    # vector to rotate by 90 degrees and obtain the axial contact tangent.
    c2 = -((gx * gx - gy * gy) / safe)
    s2 = -((2.0 * gx * gy) / safe)
    strength = np.sqrt(den).astype(np.float32)
    c2[~fp] = 0.0
    s2[~fp] = 0.0
    strength[~fp] = 0.0
    return c2.astype(np.float32), s2.astype(np.float32), strength


def _multiscale_orientation(
    field: np.ndarray,
    fp: np.ndarray,
    scales: tuple[float, ...],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Strength-weighted axial orientation, scale persistence and strength."""
    sum_c = np.zeros(field.shape, dtype=np.float32)
    sum_s = np.zeros(field.shape, dtype=np.float32)
    sum_w = np.zeros(field.shape, dtype=np.float32)
    strength_max = np.zeros(field.shape, dtype=np.float32)
    for sigma in scales:
        c2, s2, strength = _gradient_tangent(field, fp, sigma)
        w = _robust01(strength, fp)
        sum_c += w * c2
        sum_s += w * s2
        sum_w += w
        np.maximum(strength_max, w, out=strength_max)
        del c2, s2, strength, w
    resultant = np.hypot(sum_c, sum_s)
    persistence = np.divide(resultant, sum_w + 1e-6, out=np.zeros_like(resultant), where=sum_w > 0)
    c_dom = np.divide(sum_c, resultant + 1e-6, out=np.zeros_like(sum_c), where=resultant > 0)
    s_dom = np.divide(sum_s, resultant + 1e-6, out=np.zeros_like(sum_s), where=resultant > 0)
    for arr in (c_dom, s_dom, persistence, strength_max):
        arr[~fp] = 0.0
    return c_dom, s_dom, np.clip(persistence, 0.0, 1.0), strength_max


def ensure_otsp_static_cache(grid: Grid, force: bool = False) -> dict[str, Path]:
    """Build catalogue-independent multi-scale topographic/gravity axial fields."""
    CACHE.mkdir(parents=True, exist_ok=True)
    paths = {name: CACHE / f"{name}.fp.f32.npy" for name in STATIC_NAMES}
    manifest_path = CACHE / "static_manifest.json"
    if not force and manifest_path.exists() and all(p.exists() for p in paths.values()):
        return paths

    fp = grid.footprint
    det_elev = _load_band_sanitized(12, fp)
    gravity = _load_band_sanitized(13, fp)
    topo_c2, topo_s2, topo_p, topo_strength = _multiscale_orientation(
        det_elev, fp, (2.0, 5.0, 10.0)
    )
    grav_c2, grav_s2, grav_p, grav_strength = _multiscale_orientation(
        gravity, fp, (2.5, 6.0, 12.0)
    )
    axial_dot = np.clip(topo_c2 * grav_c2 + topo_s2 * grav_s2, -1.0, 1.0)
    topo_grav = (0.5 * (1.0 + axial_dot) * np.sqrt(topo_p * grav_p)).astype(np.float32)

    arrays = {
        "topo_c2": topo_c2,
        "topo_s2": topo_s2,
        "topo_persistence": topo_p,
        "topo_strength": topo_strength,
        "grav_c2": grav_c2,
        "grav_s2": grav_s2,
        "grav_persistence": grav_p,
        "grav_strength": grav_strength,
        "topo_grav_coherence": topo_grav,
    }
    manifest: dict[str, dict[str, float]] = {}
    for name, arr in arrays.items():
        vec = arr[fp].astype(np.float32)
        np.save(paths[name], vec)
        manifest[name] = {
            "finite_fraction": float(np.isfinite(vec).mean()),
            "min": float(np.min(vec)),
            "max": float(np.max(vec)),
        }
    manifest_path.write_text(json.dumps({
        "method": "H-APART-6 OTSP catalogue-independent static cache",
        "topographic_scales_px": [2.0, 5.0, 10.0],
        "gravity_scales_px": [2.5, 6.0, 12.0],
        "pixel_m": 100,
        "features": manifest,
    }, indent=2) + "\n")
    return paths


def _visible_tangent_transport(visible: np.ndarray, fp: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Estimate visible-fault tangents and transport the nearest tangent off trace.

    The structure tensor is computed only from the caller-supplied visible mask.
    Distance is collar-tempered (constant from 0 through 800 m), preventing the
    feature from encoding a narrow 200--600 m catalogue halo.
    """
    vis = np.asarray(visible, dtype=bool) & fp
    if not vis.any():
        z = np.zeros(fp.shape, dtype=np.float32)
        return z, z.copy(), z.copy(), np.full(fp.shape, 999.0, dtype=np.float32)

    blur = ndi.gaussian_filter(vis.astype(np.float32), sigma=1.2, mode="constant")
    gy, gx = np.gradient(blur)
    jxx = ndi.gaussian_filter(gx * gx, sigma=3.0, mode="constant")
    jyy = ndi.gaussian_filter(gy * gy, sigma=3.0, mode="constant")
    jxy = ndi.gaussian_filter(gx * gy, sigma=3.0, mode="constant")
    delta = np.sqrt((jxx - jyy) ** 2 + 4.0 * jxy * jxy).astype(np.float32)
    # Principal structure-tensor eigenvector is the line normal. Rotate by 90°
    # in doubled-angle space by changing both signs.
    c2_local = -((jxx - jyy) / (delta + 1e-9)).astype(np.float32)
    s2_local = -((2.0 * jxy) / (delta + 1e-9)).astype(np.float32)
    coherence_local = (delta / (jxx + jyy + 1e-9)).astype(np.float32)

    d_vis, nearest = ndi.distance_transform_edt(~vis, return_indices=True)
    c2 = c2_local[nearest[0], nearest[1]]
    s2 = s2_local[nearest[0], nearest[1]]
    coherence = coherence_local[nearest[0], nearest[1]]
    for arr in (c2, s2, coherence):
        arr[~fp] = 0.0
    return c2, s2, np.clip(coherence, 0.0, 1.0), d_vis.astype(np.float32)


def compute_otsp_surfaces(
    visible: np.ndarray,
    grid: Grid,
    static_paths: dict[str, Path] | None = None,
) -> dict[str, np.ndarray]:
    """Compute three pre-registered OTSP surfaces from the supplied visible mask."""
    fp = grid.footprint
    paths = static_paths or ensure_otsp_static_cache(grid)
    static = {name: _unpack_fp(np.load(path, mmap_mode="r"), fp) for name, path in paths.items()}
    v_c2, v_s2, v_coh, d_vis = _visible_tangent_transport(visible, fp)

    topo_match = 0.5 * (1.0 + np.clip(v_c2 * static["topo_c2"] + v_s2 * static["topo_s2"], -1.0, 1.0))
    grav_match = 0.5 * (1.0 + np.clip(v_c2 * static["grav_c2"] + v_s2 * static["grav_s2"], -1.0, 1.0))
    # Inner 800 m is exactly flat in this term. It cannot distinguish 200 m from
    # 600 m and therefore cannot create a narrow catalogue-collar ring.
    d_tempered = np.clip(d_vis, 8.0, 45.0)
    belt = np.exp(-(d_tempered - 8.0) / 34.0).astype(np.float32)
    structural_strength = np.sqrt(
        np.clip(static["topo_strength"], 0.0, 1.0)
        * (0.20 + 0.80 * np.clip(static["grav_strength"], 0.0, 1.0))
    ).astype(np.float32)
    visible_quality = (0.25 + 0.75 * v_coh).astype(np.float32)

    topo_only = (
        topo_match
        * (0.25 + 0.75 * static["topo_persistence"])
        * (0.20 + 0.80 * static["topo_strength"])
        * visible_quality
        * belt
    ).astype(np.float32)
    cross_physics = (
        (0.62 * topo_match + 0.38 * grav_match)
        * (0.20 + 0.80 * np.sqrt(static["topo_persistence"] * static["grav_persistence"]))
        * (0.15 + 0.85 * structural_strength)
        * visible_quality
        * belt
    ).astype(np.float32)
    persistent = (
        cross_physics
        * (0.30 + 0.70 * static["topo_grav_coherence"])
    ).astype(np.float32)

    allowed = fp & (d_vis > 2.05)
    return {
        "otsp_topographic": np.where(allowed, topo_only, 0.0).astype(np.float32),
        "otsp_cross_physics": np.where(allowed, cross_physics, 0.0).astype(np.float32),
        "otsp_persistent": np.where(allowed, persistent, 0.0).astype(np.float32),
        "distance_to_visible_px": d_vis,
    }
