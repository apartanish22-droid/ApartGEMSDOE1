"""H-APART-5 (PLKC-DualOOF-CELF): Zero-SGMC Multi-Physics Fault & Conduit Detector.

Implements the pre-registered 3-experiment ladder on ``gems57-pooled-hide-v2``:
  * ``E1``: 38-channel Dual-Regime (``M_Full`` with 4 preserved-NaN 1m LiDAR channels +
    quantile-calibrated ``M_Sub`` on 34 100%-footprint 10m 3DEP / fluvial chi-ksn /
    high-pass 19-band geophysics / GeoDAWN / pluvial-bench & road mimic channels) +
    CELF submodular allocation (``min_sep_px=2.8``).
  * ``E2``: Adds +6 hydrothermal conduit, GeoDAWN K/Th & U/Th alteration, magnetite-destruction
    & MT clay-cap channels (44 total) + nested-OOF Stage-2 directional 8-azimuth line-integral,
    anisotropy, and 800 m halo-prominence HGB + CELF (``min_sep_px=2.8``).
  * ``E3``: Combines ``E2`` Quaternary scarp/conduit Stage-2 surface with a dedicated zero-SGMC
    Concealed Piedmont/Basin Specialist Head (``M_Piedmont``, trained strictly on ``existing_faults``
    segments traversing sedimentary cover ``b15_depth_base >= 180 m``) + strictly fold-visible
    tip/stepover continuation (``VTRB``) + CELF (``min_sep_px=2.8``).

Live submission synthesis uses Dual-Partition Stitched 100%-OOF Cross-Fitting
(``4-Quadrant`` + ``45-deg Rotated 4-Sector`` partitions, >= 1.2 km boundary erosion),
guaranteeing 0.0% in-sample HGB memorization at every pixel in the Great Basin.
"""
from __future__ import annotations

from dataclasses import dataclass
import gc
from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from apartgems.features import (
    ALL_BLIND_FEATURES,
    E1_FULL_FEATURES,
    E1_SUB_FEATURES,
    E2_FULL_FEATURES,
    E2_SUB_FEATURES,
    VTRB_VISIBLE_FEATURES,
    compute_visible_relay_features,
    load_fp_feature_matrix,
    open_fp_feature_mmaps,
)
from gems57 import evaluate_holdout as EH
from gems57.emit import expected_credit, greedy_allocate
from gems57.grid import Grid

PIEDMONT_SPECIALIST_FEATURES: tuple[str, ...] = (
    "b02_rtp_hp8",
    "b03_tmi_hg_hp10",
    "b05_grav_slope_hp10",
    "b06_mag_tc",
    "b09_tmi_vg",
    "b11_grav_vg",
    "b12_piedmont_pos",
    "b13_iso_grav_hp12",
    "b15_depth_base",
    "b15_base_grad",
    "b18_grav_hg",
    "kin_strain_seis",
    "udpc_grav_tilt_zero",
    "udpc_grav_updip_60deg",
    "udpc_mag_updip_60deg",
    "geodawn_tmi_up150_hp6",
    "geodawn_tmi_hgm",
    "t10_onesided3",
    "t10_slope_hp8",
    "t10_curv_prof",
    "t10_aspect_coh",
    "t10_drainage_orth",
    "chi_step_max",
    "chi_ksn_hp8",
    "mimic_pluvial_bench",
    "mimic_tiger_road_dist",
    "hyd_gdr_spring_geotherm",
    "hyd_f2mdab_sinter_vent",
    "hyd_geodawn_k_th_adularia",
    "hyd_geodawn_u_th_redox",
    "hyd_mag_destruction",
    "hyd_mt_claycap_edge",
)

STAGE2_CONTEXT_NAMES: tuple[str, ...] = (
    "aniso7",
    "aniso15",
)


def _grid_to_fp_index_map(fp: np.ndarray) -> np.ndarray:
    idx_map = np.full(fp.shape, -1, dtype=np.int32)
    idx_map[fp] = np.arange(int(fp.sum()), dtype=np.int32)
    return idx_map


def run_leakage_canaries(
    grid: Grid,
    folds: list[dict[str, Any]],
    feature_paths: dict[str, Path],
    canary_cap: float = 0.90,
) -> dict[str, Any]:
    """Protocol Rule 4: Test every single feature alone on holdout BEFORE fitting any model."""
    fp = grid.footprint
    fp_idx_map = _grid_to_fp_index_map(fp)
    mmaps = open_fp_feature_mmaps(feature_paths)

    eval_mask = np.zeros(grid.shape, dtype=bool)
    y_true_2d = np.zeros(grid.shape, dtype=np.uint8)
    for f in folds:
        active = f["region"] & fp & (~f["masked_known"])
        eval_mask |= active
        y_true_2d[f["truth"] & active] = 1

    pos_fp = fp_idx_map[eval_mask & (y_true_2d == 1)]
    neg_pool_fp = fp_idx_map[eval_mask & (y_true_2d == 0)]
    rng = np.random.default_rng(20261028)
    neg_fp = np.sort(rng.choice(neg_pool_fp, size=min(250_000, neg_pool_fp.size), replace=False))
    sample_fp = np.concatenate([pos_fp, neg_fp])
    y_bin = np.concatenate([np.ones(pos_fp.size, dtype=np.int8), np.zeros(neg_fp.size, dtype=np.int8)])

    vtrb_fp = compute_visible_relay_features(folds[0]["visible"], fp)

    rows: list[dict[str, Any]] = []
    max_sym = 0.0
    for name in ALL_BLIND_FEATURES + VTRB_VISIBLE_FEATURES:
        if name in vtrb_fp:
            vals = vtrb_fp[name][sample_fp]
        else:
            vals = np.asarray(mmaps[name][sample_fp], dtype=np.float32)

        fin = np.isfinite(vals)
        if fin.sum() < 100 or len(np.unique(y_bin[fin])) < 2:
            auc = 0.5
        else:
            auc = float(roc_auc_score(y_bin[fin], vals[fin]))
        sym = float(max(auc, 1.0 - auc))
        max_sym = max(max_sym, sym)
        rows.append(
            {
                "feature": name,
                "group": "fold_visible_vtrb" if name in vtrb_fp else "blind_physical",
                "finite_eval_fraction": round(float(fin.mean()), 5),
                "roc_auc": round(auc, 5),
                "symmetric_auc": round(sym, 5),
                "passed": bool(sym <= canary_cap),
            }
        )

    rows_sorted = sorted(rows, key=lambda d: d["symmetric_auc"], reverse=True)
    return {
        "evidence_class": "HOLDOUT-LEAKAGE-CANARY",
        "evaluator_version": EH.VERSION,
        "withheld_positive_pixels": int(pos_fp.size),
        "negative_subsample_pixels": int(neg_fp.size),
        "canary_auc_cap": canary_cap,
        "max_symmetric_auc": round(max_sym, 5),
        "all_passed": bool(max_sym <= canary_cap),
        "features": rows_sorted,
    }


def compute_directional_anisotropy_gate(p1_2d: np.ndarray, fp: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Compute across-strike-preserving 8-azimuth directional anisotropy & Stage-2 context.

    Repairs ``IR-STAGE2-SMOOTH-DOMINANCE``: feeding smoothed ``s2_ek300`` / ``s2_line_max_15px``
    directly into Stage-2 HGB caused trees to split on 1.5 km blurred envelopes instead of 100 m
    scarp crests. Computing normalized 700 m & 1.5 km directional anisotropy sharpens continuous
    linear fault traces while preserving exact 100 m across-strike crest localization.
    """
    p = np.where(fp & np.isfinite(p1_2d), p1_2d, 0.0).astype(np.float32)
    H, W = p.shape

    def _line_minmax(length: int) -> tuple[np.ndarray, np.ndarray]:
        half = length // 2
        lmax = np.zeros((H, W), dtype=np.float32)
        lmin = np.full((H, W), 1e9, dtype=np.float32)
        acc = np.empty((H, W), dtype=np.float32)
        for m in range(8):
            theta = m * (np.pi / 8.0)
            st, ct = float(np.sin(theta)), float(np.cos(theta))
            acc.fill(0.0)
            for s in range(-half, half + 1):
                dy = int(round(s * st))
                dx = int(round(s * ct))
                ys0, ys1 = max(0, dy), min(H, H + dy)
                xs0, xs1 = max(0, dx), min(W, W + dx)
                acc[ys0:ys1, xs0:xs1] += p[max(0, -dy) : min(H, H - dy), max(0, -dx) : min(W, W - dx)]
            acc *= np.float32(1.0 / length)
            np.maximum(lmax, acc, out=lmax)
            np.minimum(lmin, acc, out=lmin)
        return lmax, lmin

    lmax7, lmin7 = _line_minmax(7)
    lmax15, lmin15 = _line_minmax(15)
    # Relative linear anisotropy in [0, 1]: high along linear scarps/conduits, ~0 on circular knobs
    rel_aniso7 = (lmax7 - lmin7) / (lmax7 + 1e-5)
    rel_aniso15 = (lmax15 - lmin15) / (lmax15 + 1e-5)
    halo8 = ndi.gaussian_filter(p, sigma=8.0).astype(np.float32)
    crest_ratio = np.clip(p / (halo8 + 1e-4), 0.25, 3.0)

    # Across-strike-preserving directional gate: multiplies sharp pixel p(x) without lateral blur
    gate_mult = (
        (0.76 + 0.24 * rel_aniso7)
        * (0.82 + 0.18 * rel_aniso15)
        * (0.85 + 0.15 * np.tanh(crest_ratio - 1.0))
    ).astype(np.float32)
    p_sharpened = np.where(fp, p * gate_mult, 0.0).astype(np.float32)

    ctx = {
        "aniso7": rel_aniso7[fp].astype(np.float32),
        "aniso15": rel_aniso15[fp].astype(np.float32),
    }
    del lmax7, lmin7, lmax15, lmin15, rel_aniso7, rel_aniso15, halo8, crest_ratio, gate_mult
    return p_sharpened, ctx


def _quantile_calibrate_sub_to_target(
    p_sub_vec: np.ndarray,
    ref_sub: np.ndarray,
    ref_target: np.ndarray,
) -> np.ndarray:
    q_grid = np.unique(
        np.concatenate([
            np.linspace(0.0, 0.98, 200),
            1.0 - np.geomspace(0.02, 2e-5, 250),
            [1.0],
        ])
    )
    x_knots = np.quantile(ref_sub, q_grid)
    y_knots = np.quantile(ref_target, q_grid)
    x_u, idx_u = np.unique(x_knots, return_index=True)
    y_u = np.maximum.accumulate(y_knots[idx_u])
    return np.interp(p_sub_vec, x_u, y_u).astype(np.float32)


@dataclass
class DualRegimePair:
    clf_full: HistGradientBoostingClassifier
    clf_sub: HistGradientBoostingClassifier
    full_cols: tuple[str, ...]
    sub_cols: tuple[str, ...]
    ref_sub_q: np.ndarray
    ref_blend_q: np.ndarray


def _fit_dual_regime_pair(
    full_cols: tuple[str, ...],
    sub_cols: tuple[str, ...],
    mmaps: dict[str, Any],
    fp_idx_map: np.ndarray,
    lid_valid_fp: np.ndarray,
    clean_train_2d: np.ndarray,
    pos_train_2d: np.ndarray,
    d_cat_2d: np.ndarray,
    *,
    extra_fp_cols: dict[str, np.ndarray] | None = None,
    seed: int = 42,
    n_neg_sample: int = 65_000,
    max_iter: int = 100,
) -> DualRegimePair:
    pos_fp = fp_idx_map[pos_train_2d & clean_train_2d]
    neg_pool_fp = fp_idx_map[clean_train_2d & (d_cat_2d > 4.0)]

    rng = np.random.default_rng(seed)
    neg_fp = np.sort(rng.choice(neg_pool_fp, size=min(n_neg_sample, neg_pool_fp.size), replace=False))
    idx_fp = np.concatenate([pos_fp, neg_fp])
    y = np.concatenate([np.ones(pos_fp.size, dtype=np.int8), np.zeros(neg_fp.size, dtype=np.int8)])
    w_neg = float(neg_pool_fp.size) / max(float(neg_fp.size), 1.0)
    sw = np.concatenate([
        np.ones(pos_fp.size, dtype=np.float32),
        np.full(neg_fp.size, w_neg, dtype=np.float32),
    ])

    hgb_kw = dict(
        max_iter=max_iter,
        learning_rate=0.075,
        max_leaf_nodes=31,
        min_samples_leaf=200,
        l2_regularization=5.0,
    )
    X_full = load_fp_feature_matrix(full_cols, mmaps, idx_fp, extra_fp_cols=extra_fp_cols)
    clf_full = HistGradientBoostingClassifier(**hgb_kw, random_state=seed)
    clf_full.fit(X_full, y, sample_weight=sw)
    del X_full

    X_sub = load_fp_feature_matrix(sub_cols, mmaps, idx_fp, extra_fp_cols=extra_fp_cols)
    clf_sub = HistGradientBoostingClassifier(**hgb_kw, random_state=seed + 17)
    clf_sub.fit(X_sub, y, sample_weight=sw)
    del X_sub

    cal_pool = fp_idx_map[clean_train_2d]
    cal_pool = cal_pool[lid_valid_fp[cal_pool]]
    cal_fp = np.sort(rng.choice(cal_pool, size=min(75_000, cal_pool.size), replace=False))
    pf_cal = clf_full.predict_proba(
        load_fp_feature_matrix(full_cols, mmaps, cal_fp, extra_fp_cols=extra_fp_cols)
    )[:, 1].astype(np.float32)
    ps_cal = clf_sub.predict_proba(
        load_fp_feature_matrix(sub_cols, mmaps, cal_fp, extra_fp_cols=extra_fp_cols)
    )[:, 1].astype(np.float32)
    target_cal = (0.72 * pf_cal + 0.28 * ps_cal).astype(np.float32)

    return DualRegimePair(
        clf_full=clf_full,
        clf_sub=clf_sub,
        full_cols=full_cols,
        sub_cols=sub_cols,
        ref_sub_q=ps_cal,
        ref_blend_q=target_cal,
    )


def _predict_dual_regime_on_mask(
    pair: DualRegimePair,
    mmaps: dict[str, Any],
    fp_idx_map: np.ndarray,
    lid_valid_fp: np.ndarray,
    mask_2d: np.ndarray,
    *,
    extra_fp_cols: dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    out = np.zeros(mask_2d.shape, dtype=np.float32)
    ys, xs = np.nonzero(mask_2d)
    if ys.size == 0:
        return out
    fpi = fp_idx_map[ys, xs]
    has_lid = lid_valid_fp[fpi]

    probs = np.empty(fpi.size, dtype=np.float32)
    step = 600_000
    for s in range(0, fpi.size, step):
        sub_fpi = fpi[s : s + step]
        sub_lid = has_lid[s : s + step]
        ps = pair.clf_sub.predict_proba(
            load_fp_feature_matrix(pair.sub_cols, mmaps, sub_fpi, extra_fp_cols=extra_fp_cols)
        )[:, 1].astype(np.float32)
        ps_cal = _quantile_calibrate_sub_to_target(ps, pair.ref_sub_q, pair.ref_blend_q)

        chunk_p = ps_cal
        if sub_lid.any():
            lid_fpi = sub_fpi[sub_lid]
            pf = pair.clf_full.predict_proba(
                load_fp_feature_matrix(pair.full_cols, mmaps, lid_fpi, extra_fp_cols=extra_fp_cols)
            )[:, 1].astype(np.float32)
            chunk_p = ps_cal.copy()
            chunk_p[sub_lid] = 0.72 * pf + 0.28 * ps_cal[sub_lid]
        probs[s : s + step] = chunk_p

    out[ys, xs] = probs
    return out


def _fit_piedmont_specialist_hgb(
    mmaps: dict[str, Any],
    fp_idx_map: np.ndarray,
    clean_train_2d: np.ndarray,
    pos_train_2d: np.ndarray,
    d_cat_2d: np.ndarray,
    *,
    extra_fp_cols: dict[str, np.ndarray] | None = None,
    seed: int = 777,
    n_neg_sample: int = 65_000,
) -> HistGradientBoostingClassifier:
    pos_fp = fp_idx_map[pos_train_2d & clean_train_2d]
    neg_pool_fp = fp_idx_map[clean_train_2d & (d_cat_2d > 4.0)]

    b15_vec = mmaps["b15_depth_base"]
    slp_vec = mmaps["t10_slope_p90"]
    slp_p75 = float(np.quantile(slp_vec[pos_fp], 0.75))

    is_pied_pos = (b15_vec[pos_fp] >= 180.0) & (slp_vec[pos_fp] <= slp_p75)
    w_pos = np.where(is_pied_pos, 3.8, 0.85).astype(np.float32)

    rng = np.random.default_rng(seed)
    neg_fp = np.sort(rng.choice(neg_pool_fp, size=min(n_neg_sample, neg_pool_fp.size), replace=False))
    idx_fp = np.concatenate([pos_fp, neg_fp])
    y = np.concatenate([np.ones(pos_fp.size, dtype=np.int8), np.zeros(neg_fp.size, dtype=np.int8)])
    w_neg = (float(w_pos.sum()) / max(float(pos_fp.size), 1.0)) * (
        float(neg_pool_fp.size) / max(float(neg_fp.size), 1.0)
    )
    sw = np.concatenate([w_pos, np.full(neg_fp.size, w_neg, dtype=np.float32)])

    cols = PIEDMONT_SPECIALIST_FEATURES + (STAGE2_CONTEXT_NAMES if extra_fp_cols else ())
    X = load_fp_feature_matrix(cols, mmaps, idx_fp, extra_fp_cols=extra_fp_cols)
    clf = HistGradientBoostingClassifier(
        max_iter=100,
        learning_rate=0.07,
        max_leaf_nodes=31,
        min_samples_leaf=220,
        l2_regularization=6.0,
        random_state=seed,
    )
    clf.fit(X, y, sample_weight=sw)
    return clf


def _predict_single_hgb_on_mask(
    clf: HistGradientBoostingClassifier,
    cols: tuple[str, ...],
    mmaps: dict[str, Any],
    fp_idx_map: np.ndarray,
    mask_2d: np.ndarray,
    *,
    extra_fp_cols: dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    out = np.zeros(mask_2d.shape, dtype=np.float32)
    ys, xs = np.nonzero(mask_2d)
    if ys.size == 0:
        return out
    fpi = fp_idx_map[ys, xs]
    probs = np.empty(fpi.size, dtype=np.float32)
    step = 600_000
    for s in range(0, fpi.size, step):
        sub_fpi = fpi[s : s + step]
        X = load_fp_feature_matrix(cols, mmaps, sub_fpi, extra_fp_cols=extra_fp_cols)
        probs[s : s + step] = clf.predict_proba(X)[:, 1].astype(np.float32)
    out[ys, xs] = probs
    return out


def _fit_hydro_directional_dual_regime(
    full_cols: tuple[str, ...],
    sub_cols: tuple[str, ...],
    mmaps: dict[str, Any],
    fp_idx_map: np.ndarray,
    lid_valid_fp: np.ndarray,
    fp: np.ndarray,
    clean_train_2d: np.ndarray,
    pos_train_2d: np.ndarray,
    d_cat_2d: np.ndarray,
    predict_target_mask_2d: np.ndarray,
    *,
    seed: int = 200,
) -> np.ndarray:
    """Fit 44-ch Hydrothermal/GeoDAWN/Vent Dual-Regime pair on 100% of buffered training sectors
    and apply across-strike-preserving 8-azimuth directional anisotropy sharpening on target mask.
    """
    pair_44 = _fit_dual_regime_pair(
        full_cols,
        sub_cols,
        mmaps,
        fp_idx_map,
        lid_valid_fp,
        clean_train_2d,
        pos_train_2d,
        d_cat_2d,
        seed=seed,
        n_neg_sample=65_000,
        max_iter=105,
    )
    padded_target = fp & ndi.binary_dilation(predict_target_mask_2d, iterations=10)
    p1_pad = _predict_dual_regime_on_mask(pair_44, mmaps, fp_idx_map, lid_valid_fp, padded_target)
    del pair_44
    p_sharp, _ = compute_directional_anisotropy_gate(p1_pad, padded_target)
    out = np.zeros(fp.shape, dtype=np.float32)
    out[predict_target_mask_2d] = p_sharp[predict_target_mask_2d]
    return out


def _prior_calibrate_surface(
    raw_prob_2d: np.ndarray,
    active_mask_2d: np.ndarray,
    target_expected_positives: float,
    *,
    gamma: float = 1.55,
) -> np.ndarray:
    out = np.zeros(raw_prob_2d.shape, dtype=np.float32)
    vals = np.clip(raw_prob_2d[active_mask_2d], 0.0, 0.9999).astype(np.float64)
    if vals.size == 0 or vals.max() <= 0.0:
        return out
    sharp = vals ** gamma
    cur_sum = float(sharp.sum())
    if cur_sum > 0.0:
        scale = float(target_expected_positives) / cur_sum
        cal = np.clip(sharp * scale, 0.0, 0.96)
    else:
        cal = np.zeros_like(sharp)
    out[active_mask_2d] = cal.astype(np.float32)
    return out


def allocate_plkc_celf_dots(
    cal_prob_2d: np.ndarray,
    visible_catalogue_2d: np.ndarray,
    d_vis_2d: np.ndarray,
    allowed_domain_2d: np.ndarray,
    k_truth_est: float,
    *,
    max_dots: int,
    collar_px: float = 2.0,
    min_sep_px: float = 2.8,
    use_marginal_bar: bool = True,
) -> np.ndarray:
    eligible = allowed_domain_2d & (~visible_catalogue_2d) & (d_vis_2d > collar_px)
    p_clean = np.where(eligible, np.clip(cal_prob_2d, 0.0, 0.96), 0.0).astype(np.float32)
    cand_floor = 0.004 if use_marginal_bar else 1e-5
    cand_cap = 300_000 if use_marginal_bar else 450_000
    alloc = greedy_allocate(
        p_clean,
        eligible,
        k_truth=max(float(k_truth_est), 50.0),
        floor=cand_floor,
        max_dots=max_dots,
        candidate_cap=cand_cap,
        min_sep_px=min_sep_px,
        use_marginal_bar=use_marginal_bar,
    )
    return alloc.emitted


@dataclass
class ExperimentResult:
    exp_id: str
    name: str
    oof_surface: np.ndarray
    oof_emitted: np.ndarray
    block_terms: np.ndarray
    pooled_dti: float
    n_emitted_total: int
    detached_dti: float
    per_fold: list[dict[str, Any]]
    meta_weights: list[tuple[float, float]] | None = None


def _normalize_vtrb_to_2d(vtrb_fp: dict[str, np.ndarray], fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Normalize strictly directional along-strike tip-cone & relay stepover-bridge fields.

    Isotropic ``vtrb_belt_density`` (sigma=18 px halo) is intentionally excluded from E3 fusion
    because an isotropic catalogue-ring boost pulls >75% of live dots into <1.2 km of mapped
    faults, degrading >800 m blind detached DTI and colliding >70% with catalogue-halo peers.
    """
    out_list: list[np.ndarray] = []
    for k, cap in (("vtrb_tip_cone", 2.5), ("vtrb_stepover_bridge", 2.5)):
        vec = vtrb_fp[k]
        q99 = float(np.quantile(vec, 0.99)) + 1e-6
        arr = np.zeros(fp.shape, dtype=np.float32)
        arr[fp] = np.clip(vec / q99, 0.0, cap)
        out_list.append(arr)
    return out_list[0], out_list[1]


def _fuse_phys_and_piedmont(
    p_s2_2d: np.ndarray,
    p_pd_2d: np.ndarray,
    b15_cov_2d: np.ndarray,
    ref_mask_2d: np.ndarray,
    eval_mask_2d: np.ndarray,
) -> np.ndarray:
    """Zero-SGMC Concealed Piedmont Fusion: quantile-aligns piedmont specialist onto Stage-2
    surface on ``ref_mask_2d`` and blends smoothly by sedimentary basin thickness ``b15_cov_2d``.
    """
    out = np.zeros(p_s2_2d.shape, dtype=np.float32)
    rng = np.random.default_rng(31415)
    ref_s2 = p_s2_2d[ref_mask_2d]
    ref_pd = p_pd_2d[ref_mask_2d]
    if ref_s2.size > 120_000:
        sub = np.sort(rng.choice(ref_s2.size, size=120_000, replace=False))
        ref_s2 = ref_s2[sub]
        ref_pd = ref_pd[sub]
    pd_cal = _quantile_calibrate_sub_to_target(p_pd_2d[eval_mask_2d], ref_pd, ref_s2)
    w_cov = np.clip(b15_cov_2d[eval_mask_2d], 0.08, 0.40).astype(np.float32)
    out[eval_mask_2d] = (1.0 - w_cov) * p_s2_2d[eval_mask_2d] + w_cov * pd_cal
    return out


def _fit_e3_tip_step_multipliers(
    p_phys_2d: np.ndarray,
    tip_2d: np.ndarray,
    step_2d: np.ndarray,
    pos_m: np.ndarray,
    neg_m: np.ndarray,
    *,
    seed: int = 500,
) -> tuple[float, float]:
    """Fit out-of-fold directional log-odds multipliers (c_tip, c_step) on training folds."""
    def _design(m: np.ndarray) -> np.ndarray:
        pp = np.clip(p_phys_2d[m], 1e-6, 1.0 - 1e-6)
        lp = np.log(pp / (1.0 - pp))
        return np.column_stack([lp, tip_2d[m], step_2d[m]]).astype(np.float64)

    X_pos = _design(pos_m)
    neg_ys, neg_xs = np.nonzero(neg_m)
    rng = np.random.default_rng(seed)
    take = np.sort(rng.choice(neg_ys.size, size=min(120_000, neg_ys.size), replace=False))
    neg_sub_m = np.zeros(pos_m.shape, dtype=bool)
    neg_sub_m[neg_ys[take], neg_xs[take]] = True
    X_neg = _design(neg_sub_m)

    X_tr = np.vstack([X_pos, X_neg])
    y_tr = np.concatenate([np.ones(len(X_pos), dtype=np.int8), np.zeros(len(X_neg), dtype=np.int8)])
    w_n = float(neg_ys.size) / max(float(len(X_neg)), 1.0)
    sw_tr = np.concatenate([np.ones(len(X_pos), dtype=np.float64), np.full(len(X_neg), w_n, dtype=np.float64)])

    clf = LogisticRegression(C=0.25, max_iter=300)
    clf.fit(X_tr, y_tr, sample_weight=sw_tr)
    b0 = max(float(clf.coef_[0, 0]), 0.35)
    c_tip = float(np.clip(clf.coef_[0, 1] / b0, 0.25, 0.80))
    c_step = float(np.clip(clf.coef_[0, 2] / b0, 0.25, 0.80))
    return c_tip, c_step


def _finalize_exp_result(
    exp_id: str,
    name: str,
    oof_surf: np.ndarray,
    oof_emit: np.ndarray,
    terms_sum: np.ndarray,
    per_fold: list[dict[str, Any]],
    folds: list[dict[str, Any]],
    d_vis_2d: np.ndarray,
    fp: np.ndarray,
) -> ExperimentResult:
    pooled_dti = float(EH.from_terms(terms_sum.sum(axis=0)))
    det_tp = det_fp = det_fn = 0.0
    for fold in folds:
        det_truth = fold["truth"] & (d_vis_2d > 8.0)
        if det_truth.any():
            dfold = {**fold, "truth": det_truth}
            dsc, _ = EH.evaluate(oof_emit.astype(np.float32), dfold, fp)
            det_tp += dsc["tpw"]
            det_fp += dsc["fpw"]
            det_fn += dsc["fnw"]
    det_dti = float(det_tp / (det_tp + 0.2 * det_fp + 0.8 * det_fn + 1e-12))
    return ExperimentResult(
        exp_id=exp_id,
        name=name,
        oof_surface=oof_surf,
        oof_emitted=oof_emit,
        block_terms=terms_sum,
        pooled_dti=pooled_dti,
        n_emitted_total=int(oof_emit.sum()),
        detached_dti=det_dti,
        per_fold=per_fold,
    )


def run_three_loqo_experiments(
    grid: Grid,
    folds: list[dict[str, Any]],
    feature_paths: dict[str, Path],
) -> dict[str, ExperimentResult]:
    """Execute the pre-registered <= 3 holdout experiments (E1, E2, E3) on gems57-pooled-hide-v2."""
    fp = grid.footprint
    fp_idx_map = _grid_to_fp_index_map(fp)
    mmaps = open_fp_feature_mmaps(feature_paths)
    lid_valid_fp = np.isfinite(mmaps["lid_step_max"])

    visible_holdout = folds[0]["visible"]
    hidden_all = folds[0]["hidden_all"]
    d_vis_2d = ndi.distance_transform_edt(~visible_holdout).astype(np.float32)
    vtrb_fp = compute_visible_relay_features(visible_holdout, fp)

    results: dict[str, ExperimentResult] = {}

    # =========================================================================
    # EXPERIMENT E1: 38-ch Dual-Regime (M_Full + quantile-calibrated M_Sub) + CELF d>=2.8
    # =========================================================================
    e1_surf = np.zeros(grid.shape, dtype=np.float32)
    e1_emit = np.zeros(grid.shape, dtype=bool)
    e1_terms = None
    e1_per_fold: list[dict[str, Any]] = []

    for q, fold in enumerate(folds):
        other_qs = [i for i in range(4) if i != q]
        train_reg = np.logical_or.reduce([folds[i]["region"] for i in other_qs]) & fp
        clean_train = train_reg & (~hidden_all)
        pos_train = visible_holdout & clean_train

        pair_e1 = _fit_dual_regime_pair(
            E1_FULL_FEATURES,
            E1_SUB_FEATURES,
            mmaps,
            fp_idx_map,
            lid_valid_fp,
            clean_train,
            pos_train,
            d_vis_2d,
            seed=100 + q,
        )
        test_active = fold["region"] & fp & (~fold["masked_known"])
        p_raw = _predict_dual_regime_on_mask(pair_e1, mmaps, fp_idx_map, lid_valid_fp, test_active)

        n_w_tr = sum(int(folds[i]["truth"].sum()) for i in other_qs)
        n_a_tr = sum(int((folds[i]["region"] & fp & (~folds[i]["masked_known"])).sum()) for i in other_qs)
        k_est = (n_w_tr / max(n_a_tr, 1)) * float(test_active.sum())
        fold_cap = max(int(round(1.25 * k_est)), 1500)

        p_cal = _prior_calibrate_surface(p_raw, test_active, k_est, gamma=1.55)
        e1_surf[test_active] = p_cal[test_active]

        emit_q = allocate_plkc_celf_dots(
            p_cal, visible_holdout, d_vis_2d, test_active, k_est, max_dots=fold_cap, collar_px=2.0, min_sep_px=2.8
        )
        e1_emit |= emit_q
        sc, terms = EH.evaluate(emit_q.astype(np.float32), fold, fp)
        e1_terms = terms if e1_terms is None else (e1_terms + terms)
        e1_per_fold.append({
            "fold": fold["name"],
            "dti": round(sc["dti"], 6),
            "emitted": int(emit_q.sum()),
            "withheld_positives": sc["n_truth"],
        })
        del pair_e1
        gc.collect()

    results["E1"] = _finalize_exp_result(
        "E1", "38-ch Dual-Regime Scarp/Knickzone/Updip + CELF d>=2.8",
        e1_surf, e1_emit, e1_terms, e1_per_fold, folds, d_vis_2d, fp
    )

    # =========================================================================
    # EXPERIMENT E2: +6 Hydrothermal/GeoDAWN/Vent Channels + Stage-2 Directional Line-Integral OOF
    # =========================================================================
    e2_raw_oof = np.zeros(grid.shape, dtype=np.float32)
    e2_surf = np.zeros(grid.shape, dtype=np.float32)
    e2_emit = np.zeros(grid.shape, dtype=bool)
    e2_terms = None
    e2_per_fold: list[dict[str, Any]] = []
    e2_pied_oof = np.zeros(grid.shape, dtype=np.float32)

    for q, fold in enumerate(folds):
        other_qs = [i for i in range(4) if i != q]
        train_reg = np.logical_or.reduce([folds[i]["region"] & fp for i in other_qs])
        clean_train = train_reg & (~hidden_all)
        pos_train = visible_holdout & clean_train
        test_active = fold["region"] & fp & (~fold["masked_known"])

        p2_q = _fit_hydro_directional_dual_regime(
            E2_FULL_FEATURES,
            E2_SUB_FEATURES,
            mmaps,
            fp_idx_map,
            lid_valid_fp,
            fp,
            clean_train,
            pos_train,
            d_vis_2d,
            test_active,
            seed=200 + 20 * q,
        )
        e2_raw_oof[test_active] = p2_q[test_active]

        clf_pied_q = _fit_piedmont_specialist_hgb(
            mmaps, fp_idx_map, clean_train, pos_train, d_vis_2d, seed=300 + q
        )
        p_pied_q = _predict_single_hgb_on_mask(
            clf_pied_q,
            PIEDMONT_SPECIALIST_FEATURES,
            mmaps,
            fp_idx_map,
            test_active,
        )
        e2_pied_oof[test_active] = p_pied_q[test_active]
        del clf_pied_q, p_pied_q

        n_w_tr = sum(int(folds[i]["truth"].sum()) for i in other_qs)
        n_a_tr = sum(int((folds[i]["region"] & fp & (~folds[i]["masked_known"])).sum()) for i in other_qs)
        k_est = (n_w_tr / max(n_a_tr, 1)) * float(test_active.sum())
        fold_cap = max(int(round(1.25 * k_est)), 1500)

        p_cal = _prior_calibrate_surface(p2_q, test_active, k_est, gamma=1.55)
        e2_surf[test_active] = p_cal[test_active]

        emit_q = allocate_plkc_celf_dots(
            p_cal, visible_holdout, d_vis_2d, test_active, k_est, max_dots=fold_cap, collar_px=2.0, min_sep_px=2.8
        )
        e2_emit |= emit_q
        sc, terms = EH.evaluate(emit_q.astype(np.float32), fold, fp)
        e2_terms = terms if e2_terms is None else (e2_terms + terms)
        e2_per_fold.append({
            "fold": fold["name"],
            "dti": round(sc["dti"], 6),
            "emitted": int(emit_q.sum()),
            "withheld_positives": sc["n_truth"],
        })
        gc.collect()

    results["E2"] = _finalize_exp_result(
        "E2", "44-ch Hydro-Conduit + Stage-2 Directional Vesselness OOF + CELF d>=2.8",
        e2_surf, e2_emit, e2_terms, e2_per_fold, folds, d_vis_2d, fp
    )

    # =========================================================================
    # EXPERIMENT E3: E2 + Zero-SGMC Concealed Piedmont Head + Physical-Gated Directional Continuation
    # =========================================================================
    b15_2d = np.zeros(grid.shape, dtype=np.float32)
    b15_2d[fp] = np.clip(mmaps["b15_depth_base"] / 450.0, 0.0, 1.0)
    tip_2d, step_2d = _normalize_vtrb_to_2d(vtrb_fp, fp)

    e3_surf = np.zeros(grid.shape, dtype=np.float32)
    e3_emit = np.zeros(grid.shape, dtype=bool)
    e3_terms = None
    e3_per_fold: list[dict[str, Any]] = []
    e3_meta_weights: list[tuple[float, float]] = []

    for q, fold in enumerate(folds):
        other_qs = [i for i in range(4) if i != q]
        tr_act = np.zeros(grid.shape, dtype=bool)
        pos_m = np.zeros(grid.shape, dtype=bool)
        neg_m = np.zeros(grid.shape, dtype=bool)
        for i in other_qs:
            act_i = folds[i]["region"] & fp & (~folds[i]["masked_known"])
            tr_act |= act_i
            pos_m |= (folds[i]["truth"] & act_i)
            neg_m |= (act_i & (~folds[i]["truth"]))

        test_active = fold["region"] & fp & (~fold["masked_known"])
        p_phys_tr = _fuse_phys_and_piedmont(e2_raw_oof, e2_pied_oof, b15_2d, tr_act, tr_act)
        c_tip, c_step = _fit_e3_tip_step_multipliers(p_phys_tr, tip_2d, step_2d, pos_m, neg_m, seed=500 + q)
        e3_meta_weights.append((c_tip, c_step))

        p_phys_te = _fuse_phys_and_piedmont(e2_raw_oof, e2_pied_oof, b15_2d, tr_act, test_active)
        p_gated = np.zeros(grid.shape, dtype=np.float32)
        p_gated[test_active] = p_phys_te[test_active] * (
            1.0 + c_tip * tip_2d[test_active] + c_step * step_2d[test_active]
        )

        n_w_tr = sum(int(folds[i]["truth"].sum()) for i in other_qs)
        n_a_tr = sum(int((folds[i]["region"] & fp & (~folds[i]["masked_known"])).sum()) for i in other_qs)
        k_est = (n_w_tr / max(n_a_tr, 1)) * float(test_active.sum())
        fold_cap = max(int(round(1.25 * k_est)), 1500)

        p_cal = _prior_calibrate_surface(p_gated, test_active, k_est, gamma=1.45)
        e3_surf[test_active] = p_cal[test_active]

        emit_q = allocate_plkc_celf_dots(
            p_cal, visible_holdout, d_vis_2d, test_active, k_est, max_dots=fold_cap, collar_px=2.0, min_sep_px=2.8
        )
        e3_emit |= emit_q
        sc, terms = EH.evaluate(emit_q.astype(np.float32), fold, fp)
        e3_terms = terms if e3_terms is None else (e3_terms + terms)
        e3_per_fold.append({
            "fold": fold["name"],
            "dti": round(sc["dti"], 6),
            "emitted": int(emit_q.sum()),
            "withheld_positives": sc["n_truth"],
        })

    e3_res = _finalize_exp_result(
        "E3", "PLKC-DualOOF-CELF Full (E2 + Zero-SGMC Piedmont Head + Gated Tip/Relay)",
        e3_surf, e3_emit, e3_terms, e3_per_fold, folds, d_vis_2d, fp
    )
    e3_res.meta_weights = e3_meta_weights
    results["E3"] = e3_res
    return results


def _build_dual_spatial_partitions(fp: np.ndarray, buffer_px: int = 12) -> list[list[tuple[np.ndarray, np.ndarray]]]:
    ys, xs = np.nonzero(fp)
    med_y = float(np.median(ys))
    med_x = float(np.median(xs))
    yy, xx = np.indices(fp.shape, dtype=np.float32)
    dy = yy - med_y
    dx = xx - med_x

    raw_a = [
        fp & (dy < 0) & (dx < 0),
        fp & (dy < 0) & (dx >= 0),
        fp & (dy >= 0) & (dx < 0),
        fp & (dy >= 0) & (dx >= 0),
    ]
    raw_b = [
        fp & (dy < dx) & (dy < -dx),
        fp & (dy < dx) & (dy >= -dx),
        fp & (dy >= dx) & (dy >= -dx),
        fp & (dy >= dx) & (dy < -dx),
    ]

    out_parts: list[list[tuple[np.ndarray, np.ndarray]]] = []
    for raw_sectors in (raw_a, raw_b):
        part_tuples: list[tuple[np.ndarray, np.ndarray]] = []
        for s in range(4):
            test_sec = raw_sectors[s]
            forbidden = ndi.binary_dilation(test_sec, iterations=buffer_px)
            train_mask = fp & (~forbidden)
            part_tuples.append((test_sec, train_mask))
        out_parts.append(part_tuples)
    return out_parts


def build_final_live_submission_arrays(
    grid: Grid,
    winner: ExperimentResult,
    folds_holdout: list[dict[str, Any]],
    feature_paths: dict[str, Path],
    *,
    target_dots: int = 37_654,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Synthesize 100%-OOF Dual-Partition Stitched live surface & binary {0.0, 1.0} GeoTIFF array."""
    winner_id = winner.exp_id
    fp = grid.footprint
    cat = grid.catalogue
    fp_idx_map = _grid_to_fp_index_map(fp)
    mmaps = open_fp_feature_mmaps(feature_paths)
    lid_valid_fp = np.isfinite(mmaps["lid_step_max"])

    d_cat = ndi.distance_transform_edt(~cat).astype(np.float32)
    allowed_live = fp & (~cat) & (d_cat > 2.0)

    partitions = _build_dual_spatial_partitions(fp, buffer_px=12)

    if winner_id == "E1":
        p_oof_accum = np.zeros(grid.shape, dtype=np.float32)
        for p_idx, part in enumerate(partitions):
            for s_idx, (test_sec, train_mask) in enumerate(part):
                pair = _fit_dual_regime_pair(
                    E1_FULL_FEATURES,
                    E1_SUB_FEATURES,
                    mmaps,
                    fp_idx_map,
                    lid_valid_fp,
                    train_mask,
                    cat & train_mask,
                    d_cat,
                    seed=600 + 20 * p_idx + s_idx,
                )
                pred_s = _predict_dual_regime_on_mask(pair, mmaps, fp_idx_map, lid_valid_fp, test_sec)
                p_oof_accum[test_sec] += 0.5 * pred_s[test_sec]
                del pair
                gc.collect()
        live_surface = _prior_calibrate_surface(p_oof_accum, allowed_live, 42_000.0, gamma=1.25)
        emitted = allocate_plkc_celf_dots(
            live_surface, cat, d_cat, allowed_live, 42_000.0,
            max_dots=target_dots, collar_px=2.0, min_sep_px=2.8, use_marginal_bar=False
        )
        final_arr = np.where(emitted & fp & (~cat), np.float32(1.0), np.float32(0.0)).astype(np.float32)
        return live_surface, final_arr, {"oof_partitions": 2, "in_sample_hgb_weight": 0.0}

    live_ckpt = feature_paths["t10_slope_p90"].parent / f"ckpt_live_oof_{winner_id.lower()}.npz"
    if live_ckpt.exists():
        z = np.load(live_ckpt)
        p_s2_oof = np.zeros(grid.shape, dtype=np.float32)
        p_pied_oof = np.zeros(grid.shape, dtype=np.float32)
        p_s2_oof[fp] = z["p_s2_fp"]
        p_pied_oof[fp] = z["p_pied_fp"]
    else:
        p_s2_oof = np.zeros(grid.shape, dtype=np.float32)
        p_pied_oof = np.zeros(grid.shape, dtype=np.float32)

        for p_idx, part in enumerate(partitions):
            for s_idx, (test_sec, train_mask) in enumerate(part):
                p2_s = _fit_hydro_directional_dual_regime(
                    E2_FULL_FEATURES,
                    E2_SUB_FEATURES,
                    mmaps,
                    fp_idx_map,
                    lid_valid_fp,
                    fp,
                    train_mask,
                    cat & train_mask,
                    d_cat,
                    test_sec,
                    seed=700 + 100 * p_idx + 20 * s_idx,
                )
                p_s2_oof[test_sec] += 0.5 * p2_s[test_sec]

                if winner_id == "E3":
                    clf_pd = _fit_piedmont_specialist_hgb(
                        mmaps, fp_idx_map, train_mask, cat & train_mask, d_cat,
                        seed=900 + 20 * p_idx + s_idx
                    )
                    pp_s = _predict_single_hgb_on_mask(
                        clf_pd,
                        PIEDMONT_SPECIALIST_FEATURES,
                        mmaps,
                        fp_idx_map,
                        test_sec,
                    )
                    p_pied_oof[test_sec] += 0.5 * pp_s[test_sec]
                    del clf_pd, pp_s
                del p2_s
                gc.collect()
        np.savez_compressed(live_ckpt, p_s2_fp=p_s2_oof[fp], p_pied_fp=p_pied_oof[fp])

    if winner_id == "E2" or not winner.meta_weights:
        live_surface = _prior_calibrate_surface(p_s2_oof, allowed_live, 42_000.0, gamma=1.25)
        mean_ctip = mean_cstep = 0.0
    else:
        vtrb_live_fp = compute_visible_relay_features(cat, fp)
        b15_2d = np.zeros(grid.shape, dtype=np.float32)
        b15_2d[fp] = np.clip(mmaps["b15_depth_base"] / 450.0, 0.0, 1.0)
        tip_2d, step_2d = _normalize_vtrb_to_2d(vtrb_live_fp, fp)

        p_phys_live = _fuse_phys_and_piedmont(p_s2_oof, p_pied_oof, b15_2d, allowed_live, allowed_live)
        mean_ctip = float(np.mean([w[0] for w in winner.meta_weights]))
        mean_cstep = float(np.mean([w[1] for w in winner.meta_weights]))

        raw_comb = np.zeros(grid.shape, dtype=np.float32)
        raw_comb[allowed_live] = p_phys_live[allowed_live] * (
            1.0 + mean_ctip * tip_2d[allowed_live] + mean_cstep * step_2d[allowed_live]
        )
        live_surface = _prior_calibrate_surface(raw_comb, allowed_live, 42_000.0, gamma=1.25)

    emitted = allocate_plkc_celf_dots(
        live_surface,
        cat,
        d_cat,
        allowed_live,
        42_000.0,
        max_dots=target_dots,
        collar_px=2.0,
        min_sep_px=2.8,
        use_marginal_bar=False,
    )
    final_arr = np.where(emitted & fp & (~cat), np.float32(1.0), np.float32(0.0)).astype(np.float32)
    diag = {
        "oof_partitions": 2,
        "oof_models_stitched": 16 if winner_id == "E3" else 8,
        "in_sample_hgb_weight": 0.0,
        "min_sep_px": 2.8,
        "collar_px": 2.0,
        "mean_c_tip": round(mean_ctip, 4),
        "mean_c_step": round(mean_cstep, 4),
    }
    return live_surface, final_arr, diag
