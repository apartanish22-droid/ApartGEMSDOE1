"""Leakage Canary + Nested LOQO Experiments (E1, E2, E3) + Exact 300 m Minoux CELF Allocation for H-APART-2 (MAW-GSI)."""
from __future__ import annotations

from dataclasses import dataclass
import gc
import hashlib
import heapq
from pathlib import Path
import pickle

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from gems57 import evaluate_holdout as EH
from gems57.grid import Grid
from gems57.holdout import FOLD_NAMES, quadrant_ids, visible_score_mask
from gems57.metric import OFF_DX, OFF_DY, OFF_K

from .features import (
    E1_BLIND_FEATURES,
    E2_HYDRO_STRESS_FEATURES,
    VTRB_VISIBLE_FEATURES,
    compute_visible_relay_features,
    multi_azimuth_worm_and_vent,
)


def submodular_celf_allocate_300m(
    score_surface: np.ndarray,
    visible_catalogue: np.ndarray,
    allowed_domain: np.ndarray,
    target_dots: int,
    collar_px: float = 2.05,
    tail_quantile: float = 0.942,
    convex_gamma: float = 2.4,
) -> np.ndarray:
    """Exact 300 m triangular-kernel Minoux (1978) lazy-greedy submodular coverage (CELF).

    Why convex top-decile thresholding + Minoux priority queue beats greedy_allocate:
      1. Zeroing bottom `tail_quantile` (91%) prevents 29-pixel 300 m disks from summing diffuse
         low-probability background noise over genuine 100 m fault/vent crests.
      2. Exact Minoux priority queue (`heapq`) always pops the global maximum marginal gain
         `dT(p | S) = sum_{d<=3} w(p+d) * max(0, K(d) - cover(p+d))` across the entire map,
         naturally spacing dots at ~280-300 m along crests instead of clumping adjacent 100 m cells.
    """
    H, W = score_surface.shape
    d_vis = ndi.distance_transform_edt(~visible_catalogue).astype(np.float32)
    elig = allowed_domain & (d_vis > collar_px) & np.isfinite(score_surface)
    vals = score_surface[elig]
    if vals.size == 0 or target_dots <= 0:
        return np.zeros((H, W), dtype=bool)

    ranks = rankdata(vals, method="average").astype(np.float64) / float(vals.size)
    excess = np.clip((ranks - tail_quantile) / max(1.0 - tail_quantile, 1e-6), 0.0, 1.0)
    w_elig = (excess ** convex_gamma).astype(np.float32)

    # Pad arrays by 3 px so inner CELF loop requires zero boundary checks
    pad = 3
    w_pad = np.zeros((H + 2 * pad, W + 2 * pad), dtype=np.float32)
    ey, ex = np.nonzero(elig)
    pos_mask = w_elig > 0.0
    cy = ey[pos_mask] + pad
    cx = ex[pos_mask] + pad
    w_pos = w_elig[pos_mask]
    if cy.size == 0:
        return np.zeros((H, W), dtype=bool)
    w_pad[cy, cx] = w_pos

    # Candidate centers: any eligible off-collar pixel whose 300 m disk has positive ridge weight
    # Restrict to top 320,000 initial-gain candidates for fast exact lazy greedy
    init_gain = np.zeros((H + 2 * pad, W + 2 * pad), dtype=np.float32)
    for dy, dx, kw in zip(OFF_DY, OFF_DX, OFF_K):
        oy, ox = int(dy), int(dx)
        init_gain[pad : pad + H, pad : pad + W] += (
            w_pad[pad + oy : pad + H + oy, pad + ox : pad + W + ox] * np.float32(kw)
        )

    cand_y, cand_x = ey + pad, ex + pad
    g0 = init_gain[cand_y, cand_x]
    keep = g0 > 1e-7
    cand_y, cand_x, g0 = cand_y[keep], cand_x[keep], g0[keep]
    if cand_y.size == 0:
        return np.zeros((H, W), dtype=bool)
    if cand_y.size > 320_000:
        top_k = np.argpartition(g0, -320_000)[-320_000:]
        cand_y, cand_x, g0 = cand_y[top_k], cand_x[top_k], g0[top_k]

    # Build Minoux max-heap (negated gains for Python min-heap; tie-break by candidate index)
    heap: list[tuple[float, int]] = [(-float(g0[i]), int(i)) for i in range(cand_y.size)]
    heapq.heapify(heap)

    cov_pad = np.zeros((H + 2 * pad, W + 2 * pad), dtype=np.float32)
    emitted = np.zeros((H, W), dtype=bool)
    off_dy_list = [int(v) for v in OFF_DY]
    off_dx_list = [int(v) for v in OFF_DX]
    off_k_arr = OFF_K.astype(np.float32)
    off_dy_arr = OFF_DY.astype(np.int32)
    off_dx_arr = OFF_DX.astype(np.int32)

    n_sel = 0
    while n_sel < target_dots and heap:
        neg_g, idx = heapq.heappop(heap)
        py = int(cand_y[idx])
        px = int(cand_x[idx])
        if emitted[py - pad, px - pad]:
            continue
        ny = py + off_dy_arr
        nx = px + off_dx_arr
        wv = w_pad[ny, nx]
        cv = cov_pad[ny, nx]
        diff = off_k_arr - cv
        # Exact submodular marginal gain
        cur_g = float(np.dot(wv, np.where(diff > 0.0, diff, 0.0)))
        if cur_g <= 1e-9:
            continue
        next_upper = -heap[0][0] if heap else -1.0
        if cur_g >= next_upper - 1e-9:
            emitted[py - pad, px - pad] = True
            cov_pad[ny, nx] = np.maximum(cv, off_k_arr)
            n_sel += 1
        else:
            heapq.heappush(heap, (-cur_g, idx))

    del w_pad, cov_pad, init_gain, off_dy_list, off_dx_list
    return emitted


def run_leakage_canaries(
    grid: Grid,
    folds: list[dict],
    feature_paths: dict[str, Path],
    canary_cap: float = 0.90,
) -> dict:
    """Test every single feature alone on holdout BEFORE fitting any model (Protocol Rule 4).

    Evaluates all 40 static blind MAW-GSI features + all 5 fold-visible VTRB features across
    the 11,360 withheld positive pixels and 250,000 negative pixels. Fails closed if max(AUC, 1-AUC) > 0.90.
    """
    fp = grid.footprint
    eval_2d = np.zeros(grid.shape, dtype=bool)
    truth_2d = np.zeros(grid.shape, dtype=bool)
    for f in folds:
        active = f["region"] & fp & ~visible_score_mask(f)
        eval_2d |= active
        truth_2d |= f["truth"] & active

    eval_fp = eval_2d[fp]
    truth_fp = truth_2d[fp]
    pos_idx = np.flatnonzero(eval_fp & truth_fp)
    neg_pool = np.flatnonzero(eval_fp & ~truth_fp)
    rng = np.random.default_rng(20261028)
    neg_idx = np.sort(rng.choice(neg_pool, size=min(250_000, len(neg_pool)), replace=False))
    sample_fp_idx = np.concatenate([pos_idx, neg_idx])
    y_sub = np.concatenate([np.ones(len(pos_idx), dtype=np.int8), np.zeros(len(neg_idx), dtype=np.int8)])

    rows = []
    for name in E2_HYDRO_STRESS_FEATURES:
        vec = np.load(feature_paths[name], mmap_mode="r")
        vals = vec[sample_fp_idx].astype(np.float64)
        fin = np.isfinite(vals)
        med = float(np.median(vals[fin])) if fin.any() else 0.0
        vals_imp = np.where(fin, vals, med)
        auc = float(roc_auc_score(y_sub, vals_imp))
        sym_auc = max(auc, 1.0 - auc)
        rows.append({
            "feature": name,
            "group": "blind_maw_gsi",
            "finite_fraction": round(float(fin.mean()), 6),
            "roc_auc": round(auc, 6),
            "symmetric_auc": round(sym_auc, 6),
            "canary_cap": canary_cap,
            "passed": bool(sym_auc <= canary_cap),
        })

    vtrb_fp = compute_visible_relay_features(folds[0]["visible"], fp)
    for name in VTRB_VISIBLE_FEATURES:
        vals = vtrb_fp[name][sample_fp_idx].astype(np.float64)
        auc = float(roc_auc_score(y_sub, vals))
        sym_auc = max(auc, 1.0 - auc)
        rows.append({
            "feature": name,
            "group": "fold_visible_vtrb",
            "finite_fraction": 1.0,
            "roc_auc": round(auc, 6),
            "symmetric_auc": round(sym_auc, 6),
            "canary_cap": canary_cap,
            "passed": bool(sym_auc <= canary_cap),
        })

    max_sym = max(r["symmetric_auc"] for r in rows)
    passed_all = all(r["passed"] for r in rows)
    return {
        "evidence_class": "LEAKAGE-CANARY-HOLDOUT",
        "evaluator_version": EH.VERSION,
        "withheld_positive_pixels": int(len(pos_idx)),
        "negative_sample_pixels": int(len(neg_idx)),
        "canary_cap": canary_cap,
        "max_symmetric_auc": round(max_sym, 6),
        "tested_features_passed": passed_all,
        "all_passed": False,
        "complete_feature_coverage": False,
        "missing_feature_groups": ["stage-2 axial and interaction features"],
        "reason": "This historical canary covers static and visible-relay inputs only; it cannot clear a model with additional generated features.",
        "features": rows,
    }


def _load_fp_matrix(feature_names: tuple[str, ...], feature_paths: dict[str, Path]) -> np.memmap:
    """Open or build a zero-RAM disk-backed (N_fp, D) float32 memmap (~827 MB on disk, ~0 MB RSS)."""
    cache_dir = next(iter(feature_paths.values())).parent
    mm_path = cache_dir / f"X_matrix_{len(feature_names)}.fp.f32.mmap"
    first = np.load(feature_paths[feature_names[0]], mmap_mode="r")
    n_fp = int(first.shape[0])
    shape = (n_fp, len(feature_names))
    if not mm_path.exists() or mm_path.stat().st_size != n_fp * len(feature_names) * 4:
        mm_w = np.memmap(mm_path, dtype=np.float32, mode="w+", shape=shape)
        for j, name in enumerate(feature_names):
            mm_w[:, j] = np.load(feature_paths[name], mmap_mode="r")
        mm_w.flush()
        del mm_w
    return np.memmap(mm_path, dtype=np.float32, mode="r", shape=shape)


def _fit_stage1_ensemble(
    X_fp: np.ndarray,
    col_slice: int,
    train_fp_mask: np.ndarray,
    pos_fp_mask: np.ndarray,
    seed: int,
    fast_single: bool = False,
) -> list[HistGradientBoostingClassifier]:
    """Fit diverse pair of regularized HistGradientBoostingClassifiers with native NaN handling."""
    pos_idx = np.flatnonzero(train_fp_mask & pos_fp_mask)
    neg_pool = np.flatnonzero(train_fp_mask & ~pos_fp_mask)
    rng = np.random.default_rng(10_000 + seed)
    n_neg = min(80_000 if fast_single else 125_000, len(neg_pool))
    neg_idx = np.sort(rng.choice(neg_pool, size=n_neg, replace=False))

    idx = np.concatenate([pos_idx, neg_idx])
    y = np.concatenate([np.ones(len(pos_idx), dtype=np.int8), np.zeros(len(neg_idx), dtype=np.int8)])
    w_neg = float(len(neg_pool)) / max(float(n_neg), 1.0)
    sw = np.concatenate([
        np.ones(len(pos_idx), dtype=np.float32),
        np.full(len(neg_idx), w_neg, dtype=np.float32),
    ])
    X_tr = np.asarray(X_fp[idx, :col_slice], dtype=np.float32)

    clf_a = HistGradientBoostingClassifier(
        max_iter=80 if fast_single else 115,
        learning_rate=0.065 if fast_single else 0.060,
        max_depth=6,
        max_leaf_nodes=31,
        min_samples_leaf=220,
        l2_regularization=12.0,
        max_features=0.80,
        early_stopping=False,
        random_state=seed,
    )
    clf_a.fit(X_tr, y, sample_weight=sw)
    if fast_single:
        del X_tr
        return [clf_a]

    clf_b = HistGradientBoostingClassifier(
        max_iter=105,
        learning_rate=0.055,
        max_depth=8,
        max_leaf_nodes=51,
        min_samples_leaf=340,
        l2_regularization=18.0,
        max_features=0.70,
        early_stopping=False,
        random_state=seed + 77,
    )
    clf_b.fit(X_tr, y, sample_weight=sw)
    del X_tr
    return [clf_a, clf_b]


def _predict_ensemble_fp(
    clfs: list[HistGradientBoostingClassifier],
    X_fp: np.ndarray,
    col_slice: int,
    eval_fp_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Chunked low-RAM prediction on footprint vector (respecting each model's n_features_in_)."""
    n_fp = X_fp.shape[0]
    if eval_fp_mask is None:
        target_idx = np.arange(n_fp, dtype=np.int32)
    else:
        target_idx = np.flatnonzero(eval_fp_mask)
    out = np.zeros(n_fp, dtype=np.float32)
    if target_idx.size == 0:
        return out

    max_cols = max(int(getattr(c, "n_features_in_", col_slice)) for c in clfs)
    preds = np.zeros(target_idx.size, dtype=np.float32)
    step = 550_000
    for s in range(0, target_idx.size, step):
        sub = target_idx[s : s + step]
        X_sub = np.asarray(X_fp[sub, :max_cols], dtype=np.float32)
        acc = np.zeros(sub.size, dtype=np.float32)
        for clf in clfs:
            nc = int(getattr(clf, "n_features_in_", col_slice))
            acc += clf.predict_proba(X_sub[:, :nc])[:, 1].astype(np.float32)
        preds[s : s + step] = acc / float(len(clfs))
        del X_sub
    out[target_idx] = preds
    return out


def _extract_axial_prob_features_fp(prob_fp: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Extract 6 spatial 2D axial continuity & intersection features from Stage-1 probability map."""
    p2d = np.zeros(fp.shape, dtype=np.float32)
    p2d[fp] = np.clip(prob_fp, 1e-6, 1.0 - 1e-6)
    logit2d = np.zeros(fp.shape, dtype=np.float32)
    logit2d[fp] = np.log(p2d[fp] / (1.0 - p2d[fp])).astype(np.float32)
    # Shift logit relative to footprint median so outside-footprint zeros behave neutrally
    med_l = float(np.median(logit2d[fp]))
    l_rel = np.where(fp, logit2d - med_l, 0.0).astype(np.float32)

    w_max, i_vent, _, _ = multi_azimuth_worm_and_vent(l_rel, fp, half_size=7, sigma_along=4.0)
    g_300 = ndi.gaussian_filter(l_rel, sigma=2.2)
    g_900 = ndi.gaussian_filter(l_rel, sigma=7.5)
    local_max3 = ndi.maximum_filter(l_rel, size=3)
    crest_sharp = l_rel - 0.65 * g_900 - 0.50 * np.maximum(local_max3 - l_rel, 0.0)

    return np.column_stack([
        l_rel[fp],
        w_max[fp],
        i_vent[fp],
        g_300[fp],
        (l_rel - g_900)[fp],
        crest_sharp[fp],
    ]).astype(np.float32)


def _refine_blind_axial_score_fp(
    prob_fp: np.ndarray,
    fp: np.ndarray,
    X_full_fp: np.ndarray | None = None,
    include_vent_corroboration: bool = False,
) -> np.ndarray:
    """Sharpen Stage-1 blind OOF surface with 2D axial worm continuity (100% zero-catalogue)."""
    ax = _extract_axial_prob_features_fp(prob_fp, fp)
    # ax columns: [0]=l_rel, [1]=w_max, [2]=i_vent, [3]=g_300, [4]=highpass, [5]=crest_sharp
    score = (
        0.52 * ax[:, 0]
        + 0.22 * ax[:, 1]
        + 0.08 * ax[:, 2]
        + 0.08 * ax[:, 3]
        + 0.10 * ax[:, 5]
    ).astype(np.float32)
    if include_vent_corroboration and X_full_fp is not None:
        idx_vent = E2_HYDRO_STRESS_FEATURES.index("vent_coupled_intersection")
        idx_coh = E2_HYDRO_STRESS_FEATURES.index("topo_geophys_strike_coherence")
        v_node = np.clip(np.asarray(X_full_fp[:, idx_vent], dtype=np.float32), 0.0, 4.0)
        s_coh = np.clip(np.asarray(X_full_fp[:, idx_coh], dtype=np.float32), 0.0, 4.0)
        score = (score + 0.14 * v_node + 0.08 * s_coh).astype(np.float32)
    # Map monotonically to (0, 1) via sigmoid for clean probability surface diagnostics
    return (1.0 / (1.0 + np.exp(-np.clip(score * 0.65, -18.0, 18.0)))).astype(np.float32)


def _rank01_on_mask(vec_fp: np.ndarray, active_fp: np.ndarray) -> np.ndarray:
    """Empirical [0, 1] rank scaling strictly on `active_fp`."""
    out = np.zeros(vec_fp.shape, dtype=np.float32)
    v = vec_fp[active_fp]
    if v.size == 0:
        return out
    r = rankdata(np.nan_to_num(v, nan=-1e9), method="average").astype(np.float64) / float(v.size)
    out[active_fp] = r.astype(np.float32)
    return out


def _maw_gsi_vent_conduit_score_fp(ax_fp: np.ndarray, X_full_fp: np.ndarray) -> np.ndarray:
    """Compute the distinctive H-APART-2 (MAW-GSI) Geothermal Structural-Intersection & Piedmont Conduit score.

    Explicitly weights Faulds-Hinz (2015) orthogonal/conjugate structural-intersection nodes (I_vent),
    shallow hydrothermal magnetite oxidation (z(TMI_up150) - z(RTP)), potassic K/Th + MT clay-cap edges,
    sanitized DOE GDR #1391 thermal/geothermometer/2m-probe/sinter vents, antislope graben dipoles, and
    updip basement contacts so buried geothermal vents and intra-basin splays are prioritized over
    generic range-front slope crests.
    """
    def _col(name: str) -> np.ndarray:
        idx = E2_HYDRO_STRESS_FEATURES.index(name)
        return np.nan_to_num(np.asarray(X_full_fp[:, idx], dtype=np.float32), nan=0.0)

    v_node = np.clip(_col("vent_coupled_intersection"), 0.0, 5.0)
    i_topo = np.clip(_col("struct_intersect_topo_vent"), 0.0, 5.0)
    i_geop = np.clip(_col("struct_intersect_geophys_vent"), 0.0, 5.0)
    s_coh = np.clip(_col("topo_geophys_strike_coherence"), 0.0, 5.0)
    demag = np.clip(_col("hydro_demag_up150_rtp"), -1.0, 4.5)
    potas = np.clip(_col("potassic_k_th_alteration"), -1.0, 4.5)
    mt_ed = np.clip(_col("mt_claycap_edge"), -1.0, 4.5)
    sprng = np.clip(_col("gdr_spring_geotherm_conduit"), 0.0, 4.5)
    prb_s = np.clip(_col("probe2m_sinter_vent_field"), 0.0, 4.5)
    anti_g = np.clip(_col("lidar_antislope_graben"), 0.0, 4.0)
    pied_h = np.clip(_col("piedmont_hinge_gate"), 0.0, 1.5)
    updip = np.clip(_col("updip_grav_mag_tilt_contact"), 0.0, 1.5)
    road_p = np.clip(_col("road_berm_prox"), 0.0, 1.0)

    # Require structural worm/intersection support AND amplify hydrothermal/intersection/piedmont nodes
    axial_base = 0.36 * ax_fp[:, 0] + 0.24 * ax_fp[:, 1] + 0.18 * ax_fp[:, 2] + 0.12 * ax_fp[:, 5]
    vent_hydro_boost = (
        0.55 * v_node
        + 0.35 * i_topo
        + 0.30 * i_geop
        + 0.25 * s_coh
        + 0.28 * np.maximum(demag, 0.0)
        + 0.18 * np.maximum(potas, 0.0)
        + 0.18 * np.maximum(mt_ed, 0.0)
        + 0.32 * sprng
        + 0.32 * prb_s
        + 0.25 * anti_g
        + 0.45 * pied_h * (0.4 + updip)
    )
    raw = (axial_base + 0.85 * vent_hydro_boost) * (1.0 - 0.35 * road_p)
    return (1.0 / (1.0 + np.exp(-np.clip(raw * 0.50, -18.0, 18.0)))).astype(np.float32)


def allocate_maw_gsi_dual_submodular(
    unified_surface_2d: np.ndarray,
    vent_conduit_surface_2d: np.ndarray,
    visible_catalogue: np.ndarray,
    allowed_domain: np.ndarray,
    target_dots: int,
    vent_specialist_frac: float = 0.28,
    collar_px: float = 2.05,
) -> np.ndarray:
    """Two-tier exact 300 m Minoux CELF submodular allocation:
      1. Primary tier (72% budget): unified Stage-2 axial + collar-tempered relay + MAW-GSI surface.
      2. Vent & blind-piedmont specialist tier (28% budget): Faulds-Hinz conjugate intersections (I_vent),
         hydrothermally demagnetized / altered fault conduits, GDR #1391 2m-probe/sinter vents, and
         antislope piedmont grabens strictly >= 3.6 px outside already-emitted primary dots.
    """
    n_primary = int(round(target_dots * (1.0 - vent_specialist_frac)))
    em_primary = submodular_celf_allocate_300m(
        unified_surface_2d,
        visible_catalogue,
        allowed_domain,
        target_dots=n_primary,
        collar_px=collar_px,
        tail_quantile=0.945,
        convex_gamma=2.4,
    )
    n_rem = max(0, target_dots - int(em_primary.sum()))
    if n_rem == 0:
        return em_primary

    d_em = ndi.distance_transform_edt(~em_primary).astype(np.float32) if em_primary.any() else np.full_like(unified_surface_2d, 999.0)
    d_vis = ndi.distance_transform_edt(~visible_catalogue).astype(np.float32)
    # Specialist tier explores off-primary (>360 m) AND beyond immediate near-catalogue belt (>500 m)
    vent_allowed = allowed_domain & (d_em > 3.6) & (d_vis > 5.0)
    em_vent = submodular_celf_allocate_300m(
        vent_conduit_surface_2d,
        visible_catalogue,
        vent_allowed,
        target_dots=n_rem,
        collar_px=collar_px,
        tail_quantile=0.935,
        convex_gamma=2.2,
    )
    return em_primary | em_vent


STAGE2_PHYS_ANCHOR_NAMES: tuple[str, ...] = (
    "piedmont_hinge_gate",
    "depth_base_log",
    "det_slope_log",
    "road_berm_prox",
    "topo_worm_1100m_max",
    "grav_worm_1500m_max",
    "struct_intersect_topo_vent",
    "struct_intersect_geophys_vent",
    "hydro_demag_up150_rtp",
    "probe2m_sinter_vent_field",
)


@dataclass
class Stage2ModelBundle:
    hgb: HistGradientBoostingClassifier
    scaler: StandardScaler
    logreg: LogisticRegression


def _slice_stage2_rows(
    ax_fp: np.ndarray,
    X_full_fp: np.ndarray,
    vtrb_fp: dict[str, np.ndarray],
    idx: np.ndarray,
) -> np.ndarray:
    """Assemble Stage-2 rows ONLY for `idx` (~40 MB peak instead of 475 MB full footprint)."""
    anchor_indices = [E2_HYDRO_STRESS_FEATURES.index(nm) for nm in STAGE2_PHYS_ANCHOR_NAMES]
    ax_sub = ax_fp[idx]
    anchors_sub = np.asarray(X_full_fp[idx][:, anchor_indices], dtype=np.float32)

    tc = vtrb_fp["vtrb_tip_cone"][idx]
    sb = vtrb_fp["vtrb_stepover_bridge"][idx]
    hl = vtrb_fp["vtrb_host_len_transfer"][idx]
    db = vtrb_fp["d_vis_belt_tempered"][idx]
    bf = vtrb_fp["vtrb_belt_density_far"][idx]

    p_pos = np.maximum(ax_sub[:, 0], 0.0)
    tip_x_p1 = tc * (0.5 + p_pos)
    relay_x_p1 = sb * (0.5 + p_pos)

    return np.column_stack([
        ax_sub,
        anchors_sub,
        tc,
        sb,
        hl,
        db,
        bf,
        tip_x_p1,
        relay_x_p1,
    ]).astype(np.float32)


def _fit_stage2_bundle(
    ax_fp: np.ndarray,
    X_full_fp: np.ndarray,
    vtrb_fp: dict[str, np.ndarray],
    train_fp_mask: np.ndarray,
    withheld_pos_fp_mask: np.ndarray,
    seed: int,
) -> Stage2ModelBundle:
    """Fit regularized HGB + L2 Logistic blend on strictly withheld fault components in training quadrants."""
    pos_idx = np.flatnonzero(train_fp_mask & withheld_pos_fp_mask)
    neg_pool = np.flatnonzero(train_fp_mask & ~withheld_pos_fp_mask)
    rng = np.random.default_rng(20_000 + seed)
    n_neg = min(200_000, len(neg_pool))
    neg_idx = np.sort(rng.choice(neg_pool, size=n_neg, replace=False))

    idx = np.concatenate([pos_idx, neg_idx])
    y = np.concatenate([np.ones(len(pos_idx), dtype=np.int8), np.zeros(len(neg_idx), dtype=np.int8)])
    w_neg = float(len(neg_pool)) / max(float(n_neg), 1.0)
    sw = np.concatenate([
        np.ones(len(pos_idx), dtype=np.float32),
        np.full(len(neg_idx), w_neg, dtype=np.float32),
    ])

    X_tr = _slice_stage2_rows(ax_fp, X_full_fp, vtrb_fp, idx)
    hgb = HistGradientBoostingClassifier(
        max_iter=105,
        learning_rate=0.045,
        max_depth=4,
        max_leaf_nodes=15,
        min_samples_leaf=260,
        l2_regularization=24.0,
        max_features=0.75,
        early_stopping=False,
        random_state=seed,
    )
    hgb.fit(X_tr, y, sample_weight=sw)

    X_lin = np.nan_to_num(X_tr, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float64)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_lin)
    logreg = LogisticRegression(C=0.25, max_iter=300)
    logreg.fit(X_scaled, y, sample_weight=sw)
    del X_tr, X_lin, X_scaled
    return Stage2ModelBundle(hgb=hgb, scaler=scaler, logreg=logreg)


def _predict_stage2_bundle(
    bundle: Stage2ModelBundle,
    ax_fp: np.ndarray,
    X_full_fp: np.ndarray,
    vtrb_fp: dict[str, np.ndarray],
    eval_fp_mask: np.ndarray | None = None,
) -> np.ndarray:
    n_fp = ax_fp.shape[0]
    target_idx = np.arange(n_fp, dtype=np.int32) if eval_fp_mask is None else np.flatnonzero(eval_fp_mask)
    out = np.zeros(n_fp, dtype=np.float32)
    if target_idx.size == 0:
        return out
    preds = np.zeros(target_idx.size, dtype=np.float32)
    step = 450_000
    for s in range(0, target_idx.size, step):
        sub = target_idx[s : s + step]
        X_sub = _slice_stage2_rows(ax_fp, X_full_fp, vtrb_fp, sub)
        p_hgb = bundle.hgb.predict_proba(X_sub)[:, 1].astype(np.float32)
        X_lin = bundle.scaler.transform(np.nan_to_num(X_sub, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float64))
        p_lr = bundle.logreg.predict_proba(X_lin)[:, 1].astype(np.float32)
        preds[s : s + step] = 0.65 * p_hgb + 0.35 * p_lr
        del X_sub, X_lin
    out[target_idx] = preds
    return out


@dataclass
class ExperimentResult:
    exp_id: str
    name: str
    oof_surface: np.ndarray
    oof_emitted: np.ndarray
    block_terms: np.ndarray
    detached_dti: float
    per_fold: list[dict]
    stage1_models: list[list[HistGradientBoostingClassifier]]
    stage2_bundles: list[Stage2ModelBundle] | None = None


def _score_emitted_and_detached(
    emitted_2d: np.ndarray,
    folds: list[dict],
    visible_holdout: np.ndarray,
    fp: np.ndarray,
) -> tuple[np.ndarray, float, list[dict]]:
    terms_sum = None
    per_fold = []
    pred_f32 = emitted_2d.astype(np.float32)
    for q, fold in enumerate(folds):
        sc, bterms = EH.evaluate(pred_f32, fold, fp)
        terms_sum = bterms if terms_sum is None else (terms_sum + bterms)
        per_fold.append({
            "fold": FOLD_NAMES[q],
            "emitted": int((emitted_2d & fold["region"] & fp).sum()),
            "dti": sc["dti"],
            "tpw": sc["tpw"],
            "fpw": sc["fpw"],
            "fnw": sc["fnw"],
            "n_truth": sc["n_truth"],
        })

    d_vis_all = ndi.distance_transform_edt(~visible_holdout)
    det_tp = det_fp = det_fn = 0.0
    for fold in folds:
        det_fold = dict(fold)
        det_fold["truth"] = fold["truth"] & (d_vis_all > 8.0)
        if det_fold["truth"].any():
            dsc, _ = EH.evaluate(pred_f32, det_fold, fp)
            det_tp += dsc["tpw"]
            det_fp += dsc["fpw"]
            det_fn += dsc["fnw"]
    det_dti = float(det_tp / (det_tp + 0.2 * det_fp + 0.8 * det_fn + 1e-12))
    return terms_sum, det_dti, per_fold


def run_three_loqo_experiments(
    grid: Grid,
    folds: list[dict],
    feature_paths: dict[str, Path],
    live_target_dots: int = 37_654,
    fast_stability: bool = False,
) -> dict[str, ExperimentResult]:
    """Retired H-APART-2 experiment entry point; the duplicate stop is final."""
    raise RuntimeError('H-APART-2 hit the mandatory duplicate stop; no further experiments may run in this lane')
    fp = grid.footprint
    quad_fp = quadrant_ids(fp)[fp]
    X_full_fp = _load_fp_matrix(E2_HYDRO_STRESS_FEATURES, feature_paths)

    visible_holdout = folds[0]["visible"]
    hidden_all_fp = folds[0]["hidden_all"][fp]
    vis_fp = visible_holdout[fp]
    # Exclude 1-px dilation of visible traces from negative training pool to avoid rasterization edge noise
    vis_dil1_fp = ndi.binary_dilation(visible_holdout, iterations=1)[fp]

    eval_union_2d = np.zeros(grid.shape, dtype=bool)
    for f in folds:
        eval_union_2d |= f["region"] & fp & ~f["masked_known"]

    d_vis_2d = ndi.distance_transform_edt(~visible_holdout).astype(np.float32)
    d_cat_live_2d = ndi.distance_transform_edt(~grid.catalogue).astype(np.float32)
    n_eval_offcollar = int((eval_union_2d & (d_vis_2d > 2.05)).sum())
    n_live_offcollar = int((fp & (d_cat_live_2d > 2.05)).sum())
    # Matched spatial dot density between eroded holdout evaluation domain and full live deployment footprint
    holdout_target_dots = int(round(live_target_dots * (n_eval_offcollar / max(n_live_offcollar, 1))))

    # Deterministic model checkpoint keyed by visible_holdout mask + stability mode so re-runs / Pass 2-3 take < 45s
    cache_dir = next(iter(feature_paths.values())).parent
    vis_sig = hashlib.sha256(np.packbits(vis_fp).tobytes()).hexdigest()[:12]
    ckpt_path = cache_dir / f"loqo_models_{vis_sig}_{'fast' if fast_stability else 'full'}.pkl"
    ckpt_data = None
    if ckpt_path.exists():
        try:
            ckpt_data = pickle.loads(ckpt_path.read_bytes())
        except Exception:
            ckpt_data = None

    results: dict[str, ExperimentResult] = {}

    # --- Experiments E1 (30 blind features) & E2 (40 blind MAW-GSI features stacked on E1) ---
    e1_oof_raw_fp: np.ndarray | None = None
    for exp_id, exp_name, n_cols, base_seed in (
        ("E1", "MAW-ScarpGeophys Blind (Multi-Azimuth Worms + Antislope Dipole + Cross-Gradient)", len(E1_BLIND_FEATURES), 1100),
        ("E2", "MAW-GSI Blind Vent (+ Faulds-Hinz Intersection I_vent + Demag + GDR1391 Thermal/Sinter)", len(E2_HYDRO_STRESS_FEATURES), 2200),
    ):
        if ckpt_data is not None and exp_id in ckpt_data:
            oof_raw_fp = ckpt_data[exp_id]["oof_raw_fp"]
            stage1_models = ckpt_data[exp_id]["stage1_models"]
        else:
            oof_raw_fp = np.zeros(X_full_fp.shape[0], dtype=np.float32)
            stage1_models = []

            for q, fold in enumerate(folds):
                train_reg_2d = np.logical_or.reduce([folds[i]["region"] for i in range(4) if i != q]) & fp
                train_reg_fp = train_reg_2d[fp]
                pos_trn_fp = vis_fp & train_reg_fp
                train_pool_fp = train_reg_fp & (~hidden_all_fp) & (pos_trn_fp | (~vis_dil1_fp))

                clfs_new = _fit_stage1_ensemble(
                    X_full_fp, n_cols, train_pool_fp, pos_trn_fp, seed=base_seed + 10 * q, fast_single=fast_stability
                )
                q_mask_fp = quad_fp == q
                p_new = _predict_ensemble_fp(clfs_new, X_full_fp, n_cols, q_mask_fp)[q_mask_fp]
                if exp_id == "E2" and e1_oof_raw_fp is not None:
                    clfs_combined = results["E1"].stage1_models[q] + clfs_new
                    stage1_models.append(clfs_combined)
                    oof_raw_fp[q_mask_fp] = 0.50 * e1_oof_raw_fp[q_mask_fp] + 0.50 * p_new
                else:
                    stage1_models.append(clfs_new)
                    oof_raw_fp[q_mask_fp] = p_new

        if exp_id == "E1":
            e1_oof_raw_fp = oof_raw_fp.copy()

        oof_refined_fp = _refine_blind_axial_score_fp(
            oof_raw_fp, fp, X_full_fp=X_full_fp, include_vent_corroboration=(exp_id == "E2")
        )
        oof_surf_2d = np.zeros(grid.shape, dtype=np.float32)
        oof_surf_2d[fp] = oof_refined_fp
        oof_surf_2d[~eval_union_2d] = 0.0

        oof_emit = submodular_celf_allocate_300m(
            oof_surf_2d,
            visible_holdout,
            eval_union_2d,
            target_dots=holdout_target_dots,
            collar_px=2.05,
        )
        terms_sum, det_dti, per_fold = _score_emitted_and_detached(oof_emit, folds, visible_holdout, fp)
        print(f"        [{exp_id}] OOF dots={int(oof_emit.sum())}, det_DTI={det_dti:.4f}", flush=True)
        results[exp_id] = ExperimentResult(
            exp_id=exp_id,
            name=exp_name,
            oof_surface=oof_surf_2d,
            oof_emitted=oof_emit,
            block_terms=terms_sum,
            detached_dti=det_dti,
            per_fold=per_fold,
            stage1_models=stage1_models,
            stage2_bundles=None,
        )
        if ckpt_data is None:
            results[exp_id]._raw_fp = oof_raw_fp  # type: ignore[attr-defined]
        gc.collect()

    # --- Experiment E3: Full Two-Stage OOF MAW-GSI + Collar-Tempered Visible Tip/Relay Synthesis ---
    vtrb_holdout_fp = compute_visible_relay_features(visible_holdout, fp)
    e2_res = results["E2"]

    if ckpt_data is not None and "E3" in ckpt_data:
        oof_p2_raw_fp = ckpt_data["E3"]["oof_p2_raw_fp"]
        oof_vent_fp = ckpt_data["E3"]["oof_vent_fp"]
        stage2_bundles = ckpt_data["E3"]["stage2_bundles"]
    else:
        oof_p2_raw_fp = np.zeros(X_full_fp.shape[0], dtype=np.float32)
        oof_vent_fp = np.zeros(X_full_fp.shape[0], dtype=np.float32)
        stage2_bundles = []

        d_vis_fp = d_vis_2d[fp]
        for q, fold in enumerate(folds):
            other_qs = [i for i in range(4) if i != q]
            inner_p1_fp = np.zeros(X_full_fp.shape[0], dtype=np.float32)

            for hold_i in other_qs:
                trn_qs = [j for j in other_qs if j != hold_i]
                trn_reg_fp = (np.logical_or.reduce([folds[j]["region"] for j in trn_qs]) & fp)[fp]
                pos_trn_fp = vis_fp & trn_reg_fp
                trn_pool_fp = trn_reg_fp & (~hidden_all_fp) & (pos_trn_fp | (~vis_dil1_fp))
                inner_clfs = _fit_stage1_ensemble(
                    X_full_fp,
                    len(E2_HYDRO_STRESS_FEATURES),
                    trn_pool_fp,
                    pos_trn_fp,
                    seed=3300 + 20 * q + hold_i,
                    fast_single=True,
                )
                val_fp = quad_fp == hold_i
                inner_p1_fp[val_fp] = _predict_ensemble_fp(
                    inner_clfs, X_full_fp, len(E2_HYDRO_STRESS_FEATURES), val_fp
                )[val_fp]
                del inner_clfs

            q_reg_fp = quad_fp == q
            inner_p1_fp[q_reg_fp] = _predict_ensemble_fp(
                e2_res.stage1_models[q], X_full_fp, len(E2_HYDRO_STRESS_FEATURES), q_reg_fp
            )[q_reg_fp]

            ax_fold_fp = _extract_axial_prob_features_fp(inner_p1_fp, fp)

            s2_trn_domain_fp = (
                np.logical_or.reduce([folds[i]["region"] & fp & ~folds[i]["masked_known"] for i in other_qs])[fp]
                & (d_vis_fp > 2.05)
            )
            withheld_trn_pos_fp = np.logical_or.reduce([folds[i]["truth"] for i in other_qs])[fp] & s2_trn_domain_fp
            bundle = _fit_stage2_bundle(ax_fold_fp, X_full_fp, vtrb_holdout_fp, s2_trn_domain_fp, withheld_trn_pos_fp, seed=4400 + q)
            stage2_bundles.append(bundle)

            test_active_fp = (fold["region"] & fp & ~fold["masked_known"])[fp]
            oof_p2_raw_fp[test_active_fp] = _predict_stage2_bundle(bundle, ax_fold_fp, X_full_fp, vtrb_holdout_fp, test_active_fp)[test_active_fp]
            oof_vent_fp[test_active_fp] = _maw_gsi_vent_conduit_score_fp(ax_fold_fp, X_full_fp)[test_active_fp]
            del ax_fold_fp, inner_p1_fp
            gc.collect()

        # Persist fitted models + raw OOF vectors cleanly
        save_payload = {
            "E1": {"oof_raw_fp": getattr(results["E1"], "_raw_fp"), "stage1_models": results["E1"].stage1_models},
            "E2": {"oof_raw_fp": getattr(results["E2"], "_raw_fp"), "stage1_models": results["E2"].stage1_models},
            "E3": {"oof_p2_raw_fp": oof_p2_raw_fp, "oof_vent_fp": oof_vent_fp, "stage2_bundles": stage2_bundles},
        }
        ckpt_path.write_bytes(pickle.dumps(save_payload, protocol=pickle.HIGHEST_PROTOCOL))

    # Rank-matched synthesis on each quadrant's active evaluation domain (zero cross-quadrant rank peek!)
    oof_unified_fp = np.zeros(X_full_fp.shape[0], dtype=np.float32)
    for q, fold in enumerate(folds):
        test_active_fp = (fold["region"] & fp & ~fold["masked_known"])[fp]
        r_s2 = _rank01_on_mask(oof_p2_raw_fp, test_active_fp)
        r_vn = _rank01_on_mask(oof_vent_fp, test_active_fp)
        oof_unified_fp[test_active_fp] = 0.52 * r_s2[test_active_fp] + 0.48 * r_vn[test_active_fp]

    oof_surf_e3 = np.zeros(grid.shape, dtype=np.float32)
    oof_surf_e3[fp] = oof_unified_fp
    oof_surf_e3[~eval_union_2d] = 0.0

    oof_vent_2d = np.zeros(grid.shape, dtype=np.float32)
    oof_vent_2d[fp] = oof_vent_fp
    oof_vent_2d[~eval_union_2d] = 0.0

    oof_emit_e3 = allocate_maw_gsi_dual_submodular(
        oof_surf_e3,
        oof_vent_2d,
        visible_holdout,
        eval_union_2d,
        target_dots=holdout_target_dots,
        vent_specialist_frac=0.28,
        collar_px=2.05,
    )
    terms_e3, det_dti_e3, per_fold_e3 = _score_emitted_and_detached(oof_emit_e3, folds, visible_holdout, fp)
    print(f"        [E3] OOF dots={int(oof_emit_e3.sum())}, det_DTI={det_dti_e3:.4f}", flush=True)
    results["E3"] = ExperimentResult(
        exp_id="E3",
        name="MAW-GSI Full OOF Axial-Worm + Vent/Intersection + Collar-Tempered Relay Synthesis",
        oof_surface=oof_surf_e3,
        oof_emitted=oof_emit_e3,
        block_terms=terms_e3,
        detached_dti=det_dti_e3,
        per_fold=per_fold_e3,
        stage1_models=e2_res.stage1_models,
        stage2_bundles=stage2_bundles,
    )
    del X_full_fp
    gc.collect()
    return results


def build_final_live_submission_surfaces(
    grid: Grid,
    winner: ExperimentResult,
    feature_paths: dict[str, Path],
) -> tuple[np.ndarray, np.ndarray]:
    """Generate both continuous surfaces, without placing any dots.

    Both surfaces must pass the literal shared registry gate before the
    separate placement function can be called. A returned surface is not a
    submission and has not been cleared for any weekly slot.
    """
    raise RuntimeError('H-APART-2 hit the mandatory duplicate stop; no live surfaces may be generated in this lane')
    fp = grid.footprint
    cat = grid.catalogue
    allowed_live = fp & ~cat
    allowed_live_fp = allowed_live[fp]

    feat_cols = E1_BLIND_FEATURES if winner.exp_id == "E1" else E2_HYDRO_STRESS_FEATURES
    X_full_fp = _load_fp_matrix(E2_HYDRO_STRESS_FEATURES, feature_paths)
    n_cols = len(feat_cols)

    cache_dir = next(iter(feature_paths.values())).parent
    live_p1_cache = cache_dir / f"live_p1_ens_{winner.exp_id}.f32.npy"
    if live_p1_cache.exists():
        p1_ens_fp = np.load(live_p1_cache)
    else:
        all_s1_clfs = [c for clfs in winner.stage1_models for c in clfs]
        p1_ens_fp = _predict_ensemble_fp(all_s1_clfs, X_full_fp, n_cols)
        np.save(live_p1_cache, p1_ens_fp)

    ax_live_fp = _extract_axial_prob_features_fp(p1_ens_fp, fp)
    vent_live_fp = _maw_gsi_vent_conduit_score_fp(ax_live_fp, X_full_fp)

    if winner.exp_id == "E3" and winner.stage2_bundles is not None:
        vtrb_live_fp = compute_visible_relay_features(cat, fp)
        p2_ens_fp = np.zeros(X_full_fp.shape[0], dtype=np.float32)
        for bundle in winner.stage2_bundles:
            p2_ens_fp += _predict_stage2_bundle(bundle, ax_live_fp, X_full_fp, vtrb_live_fp)
        p2_ens_fp /= float(len(winner.stage2_bundles))
        r_s2 = _rank01_on_mask(p2_ens_fp, allowed_live_fp)
        r_vn = _rank01_on_mask(vent_live_fp, allowed_live_fp)
        final_score_fp = (0.52 * r_s2 + 0.48 * r_vn).astype(np.float32)
        del vtrb_live_fp, p2_ens_fp
    else:
        final_score_fp = _refine_blind_axial_score_fp(
            p1_ens_fp, fp, X_full_fp=X_full_fp, include_vent_corroboration=(winner.exp_id == "E2")
        )
    del ax_live_fp, p1_ens_fp, X_full_fp
    gc.collect()

    surface = np.zeros(grid.shape, dtype=np.float32)
    surface[fp] = np.clip(final_score_fp, 0.0, 1.0)
    surface[~allowed_live] = 0.0

    vent_surf_2d = np.zeros(grid.shape, dtype=np.float32)
    vent_surf_2d[fp] = np.clip(vent_live_fp, 0.0, 1.0)
    vent_surf_2d[~allowed_live] = 0.0
    return surface, vent_surf_2d


def place_final_live_submission(
    grid: Grid,
    winner: ExperimentResult,
    surface: np.ndarray,
    vent_surf_2d: np.ndarray,
    *,
    surface_gate: dict,
    vent_surface_gate: dict,
    target_dots: int = 37_654,
) -> np.ndarray:
    """Place dots only after each exact surface cleared a complete literal audit.

    The gate attests the full float32 array hash. A proof from a different
    surface, a partial inventory, or a duplicate cannot be reused here. The
    returned dots still need an independently passing final-dot gate and
    writer validation; this function never approves a submission slot.
    """
    fp = grid.footprint
    cat = grid.catalogue
    allowed_live = fp & ~cat
    for name, values, gate in (("surface", surface, surface_gate),
                                ("vent surface", vent_surf_2d, vent_surface_gate)):
        a = np.asarray(values, dtype=np.float32)
        digest = hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
        if a.shape != grid.shape or not np.isfinite(a).all() or (a < 0).any() or (a > 1).any():
            raise ValueError(f"{name} must be a finite, grid-aligned [0,1] surface")
        if not (gate.get('phase') == 'surface' and gate.get('unique') is True
                and gate.get('complete_accessible_scan') is True
                and gate.get('candidate_decoded_sha256') == digest):
            raise ValueError(f"{name} needs a matching complete literal pre-placement gate")

    raise RuntimeError('H-APART-2 hit the mandatory duplicate stop; placement is disabled in this lane')
    if winner.exp_id == "E3":
        emitted_mask = allocate_maw_gsi_dual_submodular(
            surface,
            vent_surf_2d,
            cat,
            allowed_live,
            target_dots=target_dots,
            vent_specialist_frac=0.28,
            collar_px=2.05,
        )
    else:
        emitted_mask = submodular_celf_allocate_300m(
            surface,
            cat,
            allowed_live,
            target_dots=target_dots,
            collar_px=2.05,
        )
    final_arr = np.where(emitted_mask & fp & ~cat, np.float32(1.0), np.float32(0.0)).astype(np.float32)
    return final_arr
