"""Leakage Canary + Nested LOQO Experiments (E1, E2, E3) + Submodular Ridge Allocation for H-APART-1."""
from __future__ import annotations

from dataclasses import dataclass
import gc
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout as EH
from gems57.emit import expected_credit, greedy_allocate
from gems57.grid import Grid
from gems57.holdout import FOLD_NAMES

from .features import (
    E1_BLIND_FEATURES,
    E2_HYDRO_STRESS_FEATURES,
    VTRB_VISIBLE_FEATURES,
    compute_visible_relay_features,
)


def compute_ridge_crest_prominence(
    udpc_grav_updip: np.ndarray,
    dopsr_road_deconf: np.ndarray,
    udpc_mag_updip: np.ndarray,
    hmcs_mag_destr: np.ndarray,
    fp: np.ndarray,
) -> np.ndarray:
    """Compute narrow 100-200 m fault/conduit ridge-crest prominence in [0, 1].

    Suppresses broad kilometer-scale plateaus so allocated dots concentrate on true
    structural/hydrothermal lineament crests rather than diffuse blobs or collars.
    """
    comp = (
        0.38 * udpc_grav_updip
        + 0.32 * dopsr_road_deconf
        + 0.15 * udpc_mag_updip
        + 0.15 * hmcs_mag_destr
    ).astype(np.float32)
    # Local ridge prominence above 600 m Gaussian neighborhood + local 3x3 peakness
    smooth_bg = ndi.gaussian_filter(comp, sigma=6.0)
    local_max = ndi.maximum_filter(comp, size=5)
    prom = np.clip(comp - 0.75 * smooth_bg, 0.0, 1.0)
    is_near_crest = np.exp(-np.maximum(local_max - comp, 0.0) / 0.06)
    crest = (comp * (0.35 + 0.65 * is_near_crest) * (0.40 + 1.20 * prom)).astype(np.float32)
    out = np.zeros_like(comp)
    v = crest[fp]
    q995 = float(np.quantile(v, 0.995)) if v.size else 1.0
    out[fp] = np.clip(v / max(q995, 1e-6), 0.0, 1.0)
    return out


def run_leakage_canaries(
    grid: Grid,
    folds: list[dict],
    feature_paths: dict[str, Path],
    canary_cap: float = 0.90,
) -> dict:
    """Test every single feature alone on holdout BEFORE fitting any model (Protocol Rule 4).

    Computes pooled ROC AUC and symmetric max(AUC, 1 - AUC) across all scored holdout domains
    (with visible faults masked pixel-exactly). Fails closed if any feature exceeds 0.90.
    """
    fp = grid.footprint
    eval_mask = np.zeros(grid.shape, dtype=bool)
    y_true_map = np.zeros(grid.shape, dtype=np.uint8)
    for f in folds:
        active = f["region"] & fp & ~f["masked_known"]
        eval_mask |= active
        y_true_map[f["truth"] & active] = 1

    # Stratified subsample of negatives for fast exact ROC-AUC (all 11,360 positives + 250,000 negatives)
    pos_idx = np.flatnonzero(eval_mask & (y_true_map == 1))
    neg_pool = np.flatnonzero(eval_mask & (y_true_map == 0))
    rng = np.random.default_rng(20261027)
    neg_idx = np.sort(rng.choice(neg_pool, size=min(250_000, len(neg_pool)), replace=False))
    sample_idx = np.concatenate([pos_idx, neg_idx])
    y_sub = np.concatenate([np.ones(len(pos_idx), dtype=np.int8), np.zeros(len(neg_idx), dtype=np.int8)])

    rows = []
    # Check all 14 blind features
    for name in E2_HYDRO_STRESS_FEATURES:
        arr = np.load(feature_paths[name], mmap_mode="r")
        vals = arr.ravel()[sample_idx].astype(np.float64)
        auc = float(roc_auc_score(y_sub, vals))
        sym_auc = max(auc, 1.0 - auc)
        rows.append({
            "feature": name,
            "group": "blind_physical",
            "roc_auc": round(auc, 6),
            "symmetric_auc": round(sym_auc, 6),
            "canary_cap": canary_cap,
            "passed": bool(sym_auc <= canary_cap),
        })

    # The model also consumes the composite crest feature, not just its
    # constituent maps. It must have its own canary before fitting.
    crest_inputs = [np.load(feature_paths[name], mmap_mode="r") for name in (
        "udpc_grav_updip", "dopsr_road_deconfounded", "udpc_mag_updip", "hmcs_mag_destruction"
    )]
    crest = compute_ridge_crest_prominence(*crest_inputs, fp)
    crest_auc = float(roc_auc_score(y_sub, crest.ravel()[sample_idx]))
    crest_sym = max(crest_auc, 1.0 - crest_auc)
    rows.append({
        "feature": "crest_prominence",
        "group": "blind_composite",
        "roc_auc": round(crest_auc, 6),
        "symmetric_auc": round(crest_sym, 6),
        "canary_cap": canary_cap,
        "passed": bool(crest_sym <= canary_cap),
    })
    del crest, crest_inputs

    # buffered_component_draw supplies the same global withheld catalogue to
    # each quadrant. Refuse a different fold scheme instead of accidentally
    # deriving catalogue features from another fold's visible faults.
    if any(not np.array_equal(f["visible"], folds[0]["visible"]) for f in folds[1:]):
        raise ValueError("canaries require a shared buffered visible catalogue across folds")
    vtrb_maps = compute_visible_relay_features(folds[0]["visible"], fp)
    for name, arr in vtrb_maps.items():
        vals = arr.ravel()[sample_idx].astype(np.float64)
        auc = float(roc_auc_score(y_sub, vals))
        sym_auc = max(auc, 1.0 - auc)
        rows.append({
            "feature": name,
            "group": "fold_visible_vtrb",
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
        "all_passed": passed_all,
        "features": rows,
    }


def _load_feature_matrix_at_indices(
    feature_names: tuple[str, ...],
    feature_paths: dict[str, Path],
    flat_idx: np.ndarray,
    extra_maps: dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    X = np.empty((len(flat_idx), len(feature_names)), dtype=np.float32)
    for j, name in enumerate(feature_names):
        if extra_maps and name in extra_maps:
            X[:, j] = extra_maps[name].ravel()[flat_idx]
        else:
            arr = np.load(feature_paths[name], mmap_mode="r")
            X[:, j] = arr.ravel()[flat_idx]
    return X


def _fit_blind_hgb(
    feature_names: tuple[str, ...],
    feature_paths: dict[str, Path],
    train_domain: np.ndarray,
    pos_mask: np.ndarray,
    crest_map: np.ndarray,
    seed: int,
) -> HistGradientBoostingClassifier:
    """Fit calibrated regularized HistGradientBoostingClassifier on training quadrants."""
    pos_idx = np.flatnonzero((train_domain & pos_mask).ravel())
    neg_pool = np.flatnonzero((train_domain & ~pos_mask).ravel())
    rng = np.random.default_rng(1000 + seed)
    n_neg_sample = min(220_000, len(neg_pool))
    neg_idx = np.sort(rng.choice(neg_pool, size=n_neg_sample, replace=False))

    idx = np.concatenate([pos_idx, neg_idx])
    y = np.concatenate([np.ones(len(pos_idx), dtype=np.int8), np.zeros(len(neg_idx), dtype=np.int8)])
    # Importance weight so predicted probabilities reflect true spatial prior in training domain
    w_neg = float(len(neg_pool)) / max(float(n_neg_sample), 1.0)
    sample_weight = np.concatenate([
        np.ones(len(pos_idx), dtype=np.float32),
        np.full(len(neg_idx), w_neg, dtype=np.float32),
    ])

    cols = feature_names + ("crest_prominence",)
    X = _load_feature_matrix_at_indices(cols, feature_paths, idx, extra_maps={"crest_prominence": crest_map})

    clf = HistGradientBoostingClassifier(
        max_iter=110,
        learning_rate=0.055,
        max_depth=4,
        max_leaf_nodes=15,
        min_samples_leaf=250,
        l2_regularization=12.0,
        random_state=seed,
    )
    clf.fit(X, y, sample_weight=sample_weight)
    return clf


def _predict_blind_hgb_on_mask(
    clf: HistGradientBoostingClassifier,
    feature_names: tuple[str, ...],
    feature_paths: dict[str, Path],
    crest_map: np.ndarray,
    mask: np.ndarray,
) -> np.ndarray:
    out = np.zeros(mask.shape, dtype=np.float32)
    flat_idx = np.flatnonzero(mask.ravel())
    if flat_idx.size == 0:
        return out
    cols = feature_names + ("crest_prominence",)
    # Predict in 400k chunks to keep peak RAM < 300 MB
    probs = np.empty(len(flat_idx), dtype=np.float32)
    step = 400_000
    for s in range(0, len(flat_idx), step):
        sub = flat_idx[s : s + step]
        X_sub = _load_feature_matrix_at_indices(cols, feature_paths, sub, extra_maps={"crest_prominence": crest_map})
        probs[s : s + step] = clf.predict_proba(X_sub)[:, 1].astype(np.float32)
    out.ravel()[flat_idx] = probs
    return out


def allocate_udth_dots(
    prob_surface: np.ndarray,
    crest_map: np.ndarray,
    visible_catalogue: np.ndarray,
    allowed_domain: np.ndarray,
    k_truth_est: float,
    max_dots: int,
    collar_px: float = 2.0,
    blind_farfield_min_frac: float = 0.22,
    blind_prob_surface: np.ndarray | None = None,
) -> np.ndarray:
    """Allocate binary/weighted dots via 300 m kernel-aware submodular greedy coverage.

    Enforces:
      1. `EDT(~visible_catalogue) > collar_px` (200 m collar exclusion per Forum Thread 11516).
      2. Ridge-crest localization so dots lie on sharp structural/geothermal crests.
      3. Minimum far-field blind-basin discovery budget (`> 1.5 km` from visible catalogue)
         when `blind_prob_surface` is supplied, preventing pure near-catalogue collar collapse.
    """
    d_vis = ndi.distance_transform_edt(~visible_catalogue).astype(np.float32)
    off_collar = allowed_domain & (d_vis > collar_px)

    # Sharpen probability along physical crests while preserving calibrated scale
    p_sharp = np.clip(prob_surface * (0.45 + 0.95 * crest_map), 0.0, 0.95).astype(np.float32)

    if blind_prob_surface is not None and blind_farfield_min_frac > 0.0:
        main_cap = max(1, int(round(max_dots * (1.0 - blind_farfield_min_frac))))
        alloc_main = greedy_allocate(
            p_sharp,
            off_collar,
            k_truth=max(k_truth_est, 50.0),
            floor=0.008,
            max_dots=main_cap,
        )
        emitted = alloc_main.emitted.copy()
        rem_budget = max(0, max_dots - int(emitted.sum()))
        if rem_budget > 0:
            # Far-field blind structural + hydrothermal discovery (> 1.5 km from visible traces)
            # AND > 300 m from already-emitted dots so every added dot brings fresh 300 m kernel support!
            d_emit = ndi.distance_transform_edt(~emitted).astype(np.float32) if emitted.any() else np.full_like(d_vis, 999.0)
            far_allowed = off_collar & (d_vis > 15.0) & (d_emit > 3.0)
            p_blind_sharp = np.clip(blind_prob_surface * (0.40 + 1.05 * crest_map), 0.0, 0.95).astype(np.float32)
            alloc_far = greedy_allocate(
                p_blind_sharp,
                far_allowed,
                k_truth=max(k_truth_est * 0.30, 25.0),
                floor=0.006,
                max_dots=rem_budget,
            )
            emitted |= alloc_far.emitted
        return emitted

    alloc = greedy_allocate(
        p_sharp,
        off_collar,
        k_truth=max(k_truth_est, 50.0),
        floor=0.008,
        max_dots=max_dots,
    )
    return alloc.emitted


@dataclass
class ExperimentResult:
    exp_id: str
    name: str
    oof_surface: np.ndarray
    oof_emitted: np.ndarray
    block_terms: np.ndarray
    detached_dti: float
    per_fold: list[dict]
    blind_models: list[HistGradientBoostingClassifier]
    meta_models: list[LogisticRegression] | None = None


def run_three_loqo_experiments(
    grid: Grid,
    folds: list[dict],
    feature_paths: dict[str, Path],
) -> tuple[dict[str, ExperimentResult], np.ndarray]:
    """Execute the pre-registered <= 3 LOQO experiments (E1, E2, E3) on gems57-pooled-hide-v2."""
    fp = grid.footprint
    udpc_g = np.load(feature_paths["udpc_grav_updip"])
    dopsr_r = np.load(feature_paths["dopsr_road_deconfounded"])
    udpc_m = np.load(feature_paths["udpc_mag_updip"])
    hmcs_d = np.load(feature_paths["hmcs_mag_destruction"])
    crest_map = compute_ridge_crest_prominence(udpc_g, dopsr_r, udpc_m, hmcs_d, fp)
    del udpc_g, dopsr_r, udpc_m, hmcs_d
    gc.collect()

    visible_holdout = folds[0]["visible"]
    vtrb_holdout = compute_visible_relay_features(visible_holdout, fp)

    results: dict[str, ExperimentResult] = {}

    # --- Experiment E1 (UDPC + DOPSR Blind Core) & Experiment E2 (+ HMCS & Stress Blind) ---
    for exp_id, exp_name, feat_cols in (
        ("E1", "UDPC+DOPSR Blind Structural Core", E1_BLIND_FEATURES),
        ("E2", "UDPC+DOPSR+HMCS Blind Structural-Geothermal", E2_HYDRO_STRESS_FEATURES),
    ):
        oof_surf = np.zeros(grid.shape, dtype=np.float32)
        oof_emit = np.zeros(grid.shape, dtype=bool)
        terms_sum = None
        per_fold = []
        models = []

        for q, fold in enumerate(folds):
            # Training domain = union of the 3 OTHER eroded quadrants (strictly >= 2.4 km from test fold)
            train_regions = np.logical_or.reduce([folds[i]["region"] for i in range(4) if i != q]) & fp
            # For 100% blind models (zero catalogue features), visible catalogue traces in the 3 training quadrants
            # are genuine mapped fault positives; withheld buffer in training quadrants excluded from negatives
            pos_train = visible_holdout & train_regions
            clean_train = train_regions & (~folds[0]["hidden_all"])
            clf = _fit_blind_hgb(feat_cols, feature_paths, clean_train, pos_train, crest_map, seed=100 * (1 if exp_id == "E1" else 2) + q)
            models.append(clf)

            # Predict on test fold region
            test_active = fold["region"] & fp & ~fold["masked_known"]
            p_raw = _predict_blind_hgb_on_mask(clf, feat_cols, feature_paths, crest_map, test_active)
            # Scale from full-catalogue rate to 20% withheld rate for calibrated submodular bar
            p_cal = np.clip(p_raw * 0.22, 0.0, 0.95).astype(np.float32)
            oof_surf[test_active] = p_cal[test_active]

            # Estimate hidden truth count purely from training quadrants' withheld rate (no test truth peek!)
            n_withheld_train = sum(int(folds[i]["truth"].sum()) for i in range(4) if i != q)
            n_active_train = sum(int((folds[i]["region"] & fp & ~folds[i]["masked_known"]).sum()) for i in range(4) if i != q)
            k_est = (n_withheld_train / max(n_active_train, 1)) * float(test_active.sum())

            emit_q = allocate_udth_dots(
                p_cal,
                crest_map,
                visible_holdout,
                test_active,
                k_truth_est=k_est,
                max_dots=9500,
                collar_px=2.0,
                blind_farfield_min_frac=0.0,
            )
            oof_emit |= emit_q
            sc, bterms = EH.evaluate(emit_q.astype(np.float32), fold, fp)
            terms_sum = bterms if terms_sum is None else (terms_sum + bterms)
            per_fold.append({
                "fold": FOLD_NAMES[q],
                "emitted": int(emit_q.sum()),
                "dti": sc["dti"],
                "tpw": sc["tpw"],
                "fpw": sc["fpw"],
                "fnw": sc["fnw"],
                "n_truth": sc["n_truth"],
            })

        # Also score on detached blind fault components (> 8 px = 800 m from visible catalogue)
        d_vis_all = ndi.distance_transform_edt(~visible_holdout)
        det_tp = det_fp = det_fn = 0.0
        for fold in folds:
            det_fold = dict(fold)
            det_fold["truth"] = fold["truth"] & (d_vis_all > 8.0)
            if det_fold["truth"].any():
                dsc, _ = EH.evaluate(oof_emit.astype(np.float32), det_fold, fp)
                det_tp += dsc["tpw"]
                det_fp += dsc["fpw"]
                det_fn += dsc["fnw"]
        det_dti = float(det_tp / (det_tp + 0.2 * det_fp + 0.8 * det_fn + 1e-12))

        results[exp_id] = ExperimentResult(
            exp_id=exp_id,
            name=exp_name,
            oof_surface=oof_surf,
            oof_emitted=oof_emit,
            block_terms=terms_sum,
            detached_dti=det_dti,
            per_fold=per_fold,
            blind_models=models,
        )

    # --- Experiment E3: UDTH-Submod Full (E2 Blind + Strictly Fold-Visible VTRB Continuation) ---
    # Note: E2's oof_surface ALREADY contains out-of-quadrant blind predictions inside every quadrant!
    # Wait: let's verify! In E2, `oof_surf[q]` was trained on `{0,1,2,3} \ {q}`. If we used `E2.oof_surface`
    # inside `{i != q}` to fit E3's meta-model for test fold `q`, `E2.oof_surface[i]` had seen `q`'s visible
    # traces during Stage-1 training! To keep E3 100% strictly leak-free wrt test fold `q`, inside each outer fold `q`
    # we compute inner 3-fold OOF Stage-1 blind predictions strictly within `{i != q}`!
    e2_res = results["E2"]
    oof_surf_e3 = np.zeros(grid.shape, dtype=np.float32)
    oof_emit_e3 = np.zeros(grid.shape, dtype=bool)
    terms_e3 = None
    per_fold_e3 = []
    meta_models: list[LogisticRegression] = []

    def _logit(p: np.ndarray) -> np.ndarray:
        c = np.clip(p, 1e-5, 1.0 - 1e-5)
        return np.log(c / (1.0 - c)).astype(np.float32)

    for q, fold in enumerate(folds):
        other_qs = [i for i in range(4) if i != q]
        inner_blind = np.zeros(grid.shape, dtype=np.float32)
        for hold_i in other_qs:
            trn_qs = [j for j in other_qs if j != hold_i]
            trn_reg = np.logical_or.reduce([folds[j]["region"] for j in trn_qs]) & fp
            pos_trn = visible_holdout & trn_reg
            clean_trn = trn_reg & (~folds[0]["hidden_all"])
            inner_clf = _fit_blind_hgb(
                E2_HYDRO_STRESS_FEATURES,
                feature_paths,
                clean_trn,
                pos_trn,
                crest_map,
                seed=300 + 10 * q + hold_i,
            )
            val_active = folds[hold_i]["region"] & fp & ~folds[hold_i]["masked_known"]
            inner_blind[val_active] = _predict_blind_hgb_on_mask(
                inner_clf, E2_HYDRO_STRESS_FEATURES, feature_paths, crest_map, val_active
            )[val_active]

        # Fit Stage-2 meta-logistic strictly on WITHHELD components in the 3 training quadrants (other_qs)
        meta_domain = np.logical_or.reduce([folds[i]["region"] & fp & ~folds[i]["masked_known"] for i in other_qs])
        # Exclude <=2px collar around visible_holdout so meta-calibration matches the >200m deployment domain
        d_vis = ndi.distance_transform_edt(~visible_holdout).astype(np.float32)
        meta_domain &= d_vis > 2.0
        pos_meta_idx = np.flatnonzero((meta_domain & folds[0]["hidden_all"]).ravel())
        neg_meta_pool = np.flatnonzero((meta_domain & ~folds[0]["hidden_all"]).ravel())
        rng = np.random.default_rng(400 + q)
        n_neg_m = min(180_000, len(neg_meta_pool))
        neg_meta_idx = np.sort(rng.choice(neg_meta_pool, size=n_neg_m, replace=False))

        m_idx = np.concatenate([pos_meta_idx, neg_meta_idx])
        y_m = np.concatenate([np.ones(len(pos_meta_idx), dtype=np.int8), np.zeros(len(neg_meta_idx), dtype=np.int8)])
        w_neg_m = float(len(neg_meta_pool)) / max(float(n_neg_m), 1.0)
        sw_m = np.concatenate([
            np.ones(len(pos_meta_idx), dtype=np.float32),
            np.full(len(neg_meta_idx), w_neg_m, dtype=np.float32),
        ])

        def _build_meta_X(flat_indices: np.ndarray, blind_prob_map: np.ndarray) -> np.ndarray:
            b = blind_prob_map.ravel()[flat_indices]
            cr = crest_map.ravel()[flat_indices]
            tc = vtrb_holdout["vtrb_tip_cone"].ravel()[flat_indices]
            sb = vtrb_holdout["vtrb_stepover_bridge"].ravel()[flat_indices]
            return np.column_stack([
                _logit(b),
                cr,
                cr * (tc ** 2),
                cr * (sb ** 2),
                b * (tc ** 2),
            ]).astype(np.float64)

        X_m = _build_meta_X(m_idx, inner_blind)
        meta_clf = LogisticRegression(C=0.5, max_iter=300)
        meta_clf.fit(X_m, y_m, sample_weight=sw_m)
        meta_models.append(meta_clf)

        # Predict on outer test quadrant q using outer E2 blind model `e2_res.blind_models[q]`
        test_active = fold["region"] & fp & ~fold["masked_known"]
        p_blind_outer = _predict_blind_hgb_on_mask(
            e2_res.blind_models[q], E2_HYDRO_STRESS_FEATURES, feature_paths, crest_map, test_active
        )
        t_idx = np.flatnonzero(test_active.ravel())
        X_test = _build_meta_X(t_idx, p_blind_outer)
        p_meta = np.zeros(grid.shape, dtype=np.float32)
        p_meta.ravel()[t_idx] = meta_clf.predict_proba(X_test)[:, 1].astype(np.float32)
        oof_surf_e3[test_active] = p_meta[test_active]

        n_withheld_train = sum(int(folds[i]["truth"].sum()) for i in other_qs)
        n_active_train = sum(int((folds[i]["region"] & fp & ~folds[i]["masked_known"]).sum()) for i in other_qs)
        k_est = (n_withheld_train / max(n_active_train, 1)) * float(test_active.sum())

        emit_q = allocate_udth_dots(
            p_meta,
            crest_map,
            visible_holdout,
            test_active,
            k_truth_est=k_est,
            max_dots=9500,
            collar_px=2.0,
            blind_farfield_min_frac=0.35,
            blind_prob_surface=np.clip(p_blind_outer * 0.22, 0.0, 0.95),
        )
        oof_emit_e3 |= emit_q
        sc, bterms = EH.evaluate(emit_q.astype(np.float32), fold, fp)
        terms_e3 = bterms if terms_e3 is None else (terms_e3 + bterms)
        per_fold_e3.append({
            "fold": FOLD_NAMES[q],
            "emitted": int(emit_q.sum()),
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
            dsc, _ = EH.evaluate(oof_emit_e3.astype(np.float32), det_fold, fp)
            det_tp += dsc["tpw"]
            det_fp += dsc["fpw"]
            det_fn += dsc["fnw"]
    det_dti_e3 = float(det_tp / (det_tp + 0.2 * det_fp + 0.8 * det_fn + 1e-12))

    results["E3"] = ExperimentResult(
        exp_id="E3",
        name="UDTH-Submod Full (Updip Potential + Seam-Free Scarp + Hydrothermal/Vents + Visible Tip/Relay)",
        oof_surface=oof_surf_e3,
        oof_emitted=oof_emit_e3,
        block_terms=terms_e3,
        detached_dti=det_dti_e3,
        per_fold=per_fold_e3,
        blind_models=e2_res.blind_models,
        meta_models=meta_models,
    )
    return results, crest_map


def build_final_live_submission_arrays(
    grid: Grid,
    winner: ExperimentResult,
    feature_paths: dict[str, Path],
    crest_map: np.ndarray,
    target_dots: int = 38_500,
    before_placement=None,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate full-footprint continuous probability surface + final all-finite [0, 1] GeoTIFF array.

    Historical code path, not an approved pipeline. The required callback must
    return a passing shared-gate receipt before any dot placement. A format or
    inventory-scope pass is not a holdout win or a weekly-slot approval.
    """
    fp = grid.footprint
    cat = grid.catalogue
    allowed_live = fp & ~cat
    if before_placement is None:
        raise ValueError("pre-placement uniqueness gate is required")

    def require_surface_clear(surface):
        receipt = before_placement(surface, fp)
        if (not isinstance(receipt, dict) or receipt.get("unique") is not True
                or receipt.get("complete_accessible_scan") is not True
                or receipt.get("stop_required") is not False):
            raise ValueError("pre-placement uniqueness gate did not return a passing complete-scope receipt")

    feat_cols = E1_BLIND_FEATURES if winner.exp_id == "E1" else E2_HYDRO_STRESS_FEATURES
    p_blind_ens = np.zeros(grid.shape, dtype=np.float32)
    for clf in winner.blind_models:
        p_blind_ens += _predict_blind_hgb_on_mask(clf, feat_cols, feature_paths, crest_map, allowed_live)
    p_blind_ens /= float(len(winner.blind_models))

    if winner.exp_id == "E3" and winner.meta_models is not None:
        vtrb_live = compute_visible_relay_features(cat, fp)
        flat_idx = np.flatnonzero(allowed_live.ravel())
        b_live = p_blind_ens.ravel()[flat_idx]
        c_clip = np.clip(b_live, 1e-5, 1.0 - 1e-5)
        logit_b = np.log(c_clip / (1.0 - c_clip))
        cr = crest_map.ravel()[flat_idx]
        tc = vtrb_live["vtrb_tip_cone"].ravel()[flat_idx]
        sb = vtrb_live["vtrb_stepover_bridge"].ravel()[flat_idx]
        X_live = np.column_stack([logit_b, cr, cr * (tc ** 2), cr * (sb ** 2), b_live * (tc ** 2)]).astype(np.float64)

        p_meta_ens = np.zeros(len(flat_idx), dtype=np.float32)
        for mclf in winner.meta_models:
            p_meta_ens += mclf.predict_proba(X_live)[:, 1].astype(np.float32)
        p_meta_ens /= float(len(winner.meta_models))

        # Historical scaling and truth budget were assumptions, not verified
        # organizer hidden-label counts; this path remains research-only.
        surface = np.zeros(grid.shape, dtype=np.float32)
        surface.ravel()[flat_idx] = np.clip(p_meta_ens * 1.45, 0.0, 0.98)
        require_surface_clear(surface)
        emitted_mask = allocate_udth_dots(
            surface,
            crest_map,
            cat,
            allowed_live,
            k_truth_est=42_000.0,
            max_dots=target_dots,
            collar_px=2.0,
            blind_farfield_min_frac=0.40,
            blind_prob_surface=np.clip(p_blind_ens * 0.35, 0.0, 0.95),
        )
    else:
        surface = np.clip(p_blind_ens * 0.35, 0.0, 0.98).astype(np.float32)
        surface[~allowed_live] = 0.0
        require_surface_clear(surface)
        emitted_mask = allocate_udth_dots(
            surface,
            crest_map,
            cat,
            allowed_live,
            k_truth_est=42_000.0,
            max_dots=target_dots,
            collar_px=2.0,
            blind_farfield_min_frac=0.0,
        )

    # This historical implementation emits binary values. Their optimality is
    # not established; multi-truth credit and overlapping predictions make
    # pointwise break-even claims inadequate for general soft predictions.
    final_arr = np.where(emitted_mask & fp & ~cat, np.float32(1.0), np.float32(0.0)).astype(np.float32)
    return surface, final_arr
