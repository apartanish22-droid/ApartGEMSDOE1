#!/usr/bin/env python3
"""End-to-end automated execution of H-APART-5 (PLKC-DualOOF-CELF) under the Parallel-Run Protocol.

Executes in one deterministic pass (< 6 minutes on 2 CPUs, < 650 MB RAM):
  1. Verifies/builds the 44-channel blind physical feature cache (zero SGMC, preserved-NaN 1m LiDAR).
  2. Builds canonical ``gems57-pooled-hide-v2`` holdout (seed=2026) + stability seed=20.
  3. Runs single-feature Leakage Canaries across all 47 channels (cap <= 0.90).
  4. Runs the frozen <= 3 Pre-Registered Holdout Experiments (E1, E2, E3) + controls + archived S1 baseline.
  5. Synthesizes the 100%-OOF Dual-Partition Stitched live surface & 37,654-dot CELF d>=2.8 GeoTIFF,
     evaluates read-only ``sgmc-piedmont-basin-v1`` concealed-fault DTI, and enforces the 950-raster
     53-repo Uniqueness & Duplicate Gate + fail-closed GeoTIFF/ZIP validation.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

from apartgems.features import ensure_blind_feature_cache
from apartgems.model import (
    build_final_live_submission_arrays,
    run_leakage_canaries,
    run_three_loqo_experiments,
)
from apartgems.piedmont_eval import build_concealed_piedmont_fold, score_concealed_piedmont
from apartgems.uniqueness import audit_candidate_against_registry
from gems57 import evaluate_holdout as EH
from gems57 import load_grid
from gems57.emit import greedy_allocate
from gems57.holdout import buffered_component_draw
from gems57.submission_writer import write_submission
from gems57.validate import assert_submittable, validate


def evaluate_distance_only_control(grid, folds) -> tuple[np.ndarray, float, int]:
    """Evaluate canonical distance-only halo control (p ~ exp(-d_vis / 9)) with >2px collar & d>=2.8."""
    fp = grid.footprint
    vis = folds[0]["visible"]
    d_vis = distance_transform_edt(~vis).astype(np.float32)
    p_dist = (0.04 * np.exp(-d_vis / 9.0)).astype(np.float32)

    emit_all = np.zeros(grid.shape, dtype=bool)
    terms_sum = None
    det_tp = det_fp = det_fn = 0.0
    for q, fold in enumerate(folds):
        other_qs = [i for i in range(4) if i != q]
        n_w = sum(int(folds[i]["truth"].sum()) for i in other_qs)
        n_a = sum(int((folds[i]["region"] & fp & (~folds[i]["masked_known"])).sum()) for i in other_qs)
        test_active = fold["region"] & fp & (~fold["masked_known"])
        k_est = (n_w / max(n_a, 1)) * float(test_active.sum())
        fold_cap = max(int(round(1.25 * k_est)), 1500)
        alloc = greedy_allocate(
            p_dist,
            test_active & (d_vis > 2.0),
            k_truth=max(k_est, 50.0),
            floor=0.008,
            max_dots=fold_cap,
            min_sep_px=2.8,
        )
        emit_all |= alloc.emitted
        _, t = EH.evaluate(alloc.emitted.astype(np.float32), fold, fp)
        terms_sum = t if terms_sum is None else (terms_sum + t)
        det_truth = fold["truth"] & (d_vis > 8.0)
        if det_truth.any():
            dfold = {**fold, "truth": det_truth}
            dsc, _ = EH.evaluate(alloc.emitted.astype(np.float32), dfold, fp)
            det_tp += dsc["tpw"]
            det_fp += dsc["fpw"]
            det_fn += dsc["fnw"]
    det_dti = float(det_tp / (det_tp + 0.2 * det_fp + 0.8 * det_fn + 1e-12))
    return terms_sum, det_dti, int(emit_all.sum())


def _crowding_metrics(binary_arr: np.ndarray) -> dict:
    ys, xs = np.nonzero(binary_arr > 0.5)
    n = int(ys.size)
    if n < 2:
        return {"n_dots": n, "min_nn_px": 0.0, "frac_nn_lt_2_8px": 0.0, "frac_ge3_neighbors_in_3px": 0.0, "mean_neighbors_in_3px": 0.0}
    pts = np.column_stack([ys, xs]).astype(np.float64)
    tree = cKDTree(pts)
    d2, _ = tree.query(pts, k=2)
    nn1 = d2[:, 1]
    nbrs3 = np.array([len(v) - 1 for v in tree.query_ball_point(pts, r=3.000001)], dtype=np.float64)
    return {
        "n_dots": n,
        "min_nn_px": round(float(nn1.min()), 4),
        "median_nn_px": round(float(np.median(nn1)), 4),
        "frac_nn_le_1_5px": round(float(np.mean(nn1 <= 1.5001)), 6),
        "frac_nn_lt_2_8px": round(float(np.mean(nn1 < 2.7999)), 6),
        "frac_ge3_neighbors_in_3px": round(float(np.mean(nbrs3 >= 3)), 6),
        "mean_neighbors_in_3px": round(float(np.mean(nbrs3)), 4),
    }


def main() -> int:
    t0 = time.time()
    grid = load_grid()
    fp = grid.footprint

    print(f"[1/6] Ensuring 44-channel blind physical feature cache ({time.time()-t0:.1f}s)...", flush=True)
    feat_paths = ensure_blind_feature_cache(grid, force=False)

    print(f"[2/6] Building canonical gems57-pooled-hide-v2 holdout (seed=2026) ({time.time()-t0:.1f}s)...", flush=True)
    folds, _ = buffered_component_draw(grid, seed=2026, hide_frac=0.20, buffer_px=3)

    print(f"[3/6] Running single-feature Leakage Canaries across all 47 channels (cap <= 0.90) ({time.time()-t0:.1f}s)...", flush=True)
    canary_report = run_leakage_canaries(grid, folds, feat_paths, canary_cap=0.90)
    (ROOT / "evidence/leakage_canary.json").write_text(json.dumps(canary_report, indent=2) + "\n")
    print(f"      Canary max symmetric AUC = {canary_report['max_symmetric_auc']:.4f} (all_passed={canary_report['all_passed']})", flush=True)
    if not canary_report["all_passed"]:
        raise RuntimeError(f"LEAKAGE CANARY FAILED (>0.90): {canary_report}")

    print(f"[4/6] Executing <= 3 Pre-Registered Holdout Experiments (E1, E2, E3) + Controls ({time.time()-t0:.1f}s)...", flush=True)
    import pickle
    ckpt_2026 = ROOT / ".cache/apartgems_s2_features/ckpt_exp_seed2026.pkl"
    if ckpt_2026.exists():
        with ckpt_2026.open("rb") as fh:
            exp_results = pickle.load(fh)
        print("      Loaded seed=2026 checkpoint.", flush=True)
    else:
        exp_results = run_three_loqo_experiments(grid, folds, feat_paths)
        with ckpt_2026.open("wb") as fh:
            pickle.dump(exp_results, fh, protocol=pickle.HIGHEST_PROTOCOL)
    zero_terms = sum(EH.evaluate(np.zeros(grid.shape, np.float32), f, fp)[1] for f in folds)
    dist_terms, dist_det_dti, dist_emitted = evaluate_distance_only_control(grid, folds)

    key_by_id = {
        "E1": "E1_plkc_dual_regime_blind",
        "E2": "E2_plkc_hydro_stage2_vessel",
        "E3": "E3_plkc_dualoof_celf_full",
    }
    terms_map = {
        "zero_control": zero_terms,
        "distance_only_collar2_control": dist_terms,
        key_by_id["E1"]: exp_results["E1"].block_terms,
        key_by_id["E2"]: exp_results["E2"].block_terms,
        key_by_id["E3"]: exp_results["E3"].block_terms,
    }
    prelim = EH.pooled_summary(terms_map, draws=100, seed=520810, candidate=key_by_id["E3"])
    winner_id = max(("E1", "E2", "E3"), key=lambda eid: prelim["scores"][key_by_id[eid]]["dti"])
    winner = exp_results[winner_id]
    pooled_win = EH.pooled_summary(terms_map, draws=1000, seed=520810, candidate=key_by_id[winner_id])
    winner_score = pooled_win["scores"][key_by_id[winner_id]]

    for k, s in pooled_win["scores"].items():
        print(f"      {k:32s}: HOLDOUT-DTI = {s['dti']:.4f}  95% CI [{s['ci95'][0]:.4f}, {s['ci95'][1]:.4f}]", flush=True)
    for eid in ("E1", "E2", "E3"):
        r = exp_results[eid]
        print(f"      {eid} detached (>800m blind) DTI = {r.detached_dti:.4f}, emitted_oof_dots = {r.n_emitted_total}", flush=True)
    print(f"      distance_only detached (>800m blind) DTI = {dist_det_dti:.4f}, emitted_oof_dots = {dist_emitted}", flush=True)

    # Secondary seed=20 stability verification (same frozen pipeline, zero extra tuning)
    print(f"      Running secondary stability draw (seed=20) ({time.time()-t0:.1f}s)...", flush=True)
    folds_s20, _ = buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    ckpt_20 = ROOT / ".cache/apartgems_s2_features/ckpt_exp_seed20.pkl"
    if ckpt_20.exists():
        with ckpt_20.open("rb") as fh:
            exp_s20 = pickle.load(fh)
        print("      Loaded seed=20 checkpoint.", flush=True)
    else:
        exp_s20 = run_three_loqo_experiments(grid, folds_s20, feat_paths)
        with ckpt_20.open("wb") as fh:
            pickle.dump(exp_s20, fh, protocol=pickle.HIGHEST_PROTOCOL)
    zero_s20 = sum(EH.evaluate(np.zeros(grid.shape, np.float32), f, fp)[1] for f in folds_s20)
    dist_s20, _, _ = evaluate_distance_only_control(grid, folds_s20)
    pooled_s20 = EH.pooled_summary(
        {
            "zero_control": zero_s20,
            "distance_only_collar2_control": dist_s20,
            key_by_id["E1"]: exp_s20["E1"].block_terms,
            key_by_id["E2"]: exp_s20["E2"].block_terms,
            key_by_id["E3"]: exp_s20["E3"].block_terms,
        },
        draws=1000,
        seed=520810,
        candidate=key_by_id[winner_id],
    )
    print(f"      Seed-20 winner ({winner_id}) HOLDOUT-DTI = {pooled_s20['scores'][key_by_id[winner_id]]['dti']:.4f}", flush=True)

    exp_report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": EH.VERSION,
        "session_1_archived_holdout_dti": 0.052328,
        "experiment_budget_used": 3,
        "experiment_budget_cap": 3,
        "primary_draw_seed_2026": {
            "scores": pooled_win["scores"],
            "paired_differences_vs_winner": pooled_win["paired_differences"],
            "bootstrap": pooled_win["bootstrap"],
            "detached_gt_800m_blind_dti": {
                "distance_only_collar2_control": round(dist_det_dti, 6),
                key_by_id["E1"]: round(exp_results["E1"].detached_dti, 6),
                key_by_id["E2"]: round(exp_results["E2"].detached_dti, 6),
                key_by_id["E3"]: round(exp_results["E3"].detached_dti, 6),
            },
            "per_fold_details": {eid: exp_results[eid].per_fold for eid in ("E1", "E2", "E3")},
        },
        "secondary_stability_seed_20": {
            "scores": pooled_s20["scores"],
            "paired_differences_vs_winner": pooled_s20["paired_differences"],
        },
        "selected_winner": winner_id,
    }

    print(f"[5/6] Synthesizing Dual-Partition 100%-OOF live submission for {winner_id} (target=37,654 dots) ({time.time()-t0:.1f}s)...", flush=True)
    live_surface, final_arr, oof_diag = build_final_live_submission_arrays(
        grid, winner, folds, feat_paths, target_dots=37_654
    )

    # Read-only diagnostic benchmark on Concealed Piedmont/Basin SGMC faults (zero-SGMC training!)
    cpied_fold = build_concealed_piedmont_fold(ROOT)
    cpied_preds: dict[str, np.ndarray] = {"candidate_plkc": final_arr}
    for ref_key, ref_rel in (
        ("ApartGEMSDOE1_S1_00525", "docs/downloads/archive/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif"),
        ("GEMSDOE32_B2_02778", ".cache/peer_repos/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"),
        ("GEMSDOE70_P8_02478", ".cache/peer_repos/GEMSDOE70/docs/downloads/gems70-p5-dual-submod300-oof38k-20261020.tif"),
        ("GEMSDOE27_H31_02250", ".cache/peer_repos/GEMSDOE27/docs/downloads/gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite.tif"),
    ):
        rp = ROOT / ref_rel
        if rp.exists():
            with rasterio.open(rp) as ds:
                raw_r = ds.read(1).astype(np.float32)
            cpied_preds[ref_key] = np.where(np.isfinite(raw_r) & fp, np.clip(raw_r, 0.0, 1.0), 0.0)
    cpied_summary = score_concealed_piedmont(cpied_preds, candidate_key="candidate_plkc", fold=cpied_fold)
    cand_cpied = cpied_summary["scores"]["candidate_plkc"]
    print(
        f"      Zero-SGMC Concealed Piedmont DTI (sgmc-piedmont-basin-v1) = {cand_cpied['dti']:.4f} "
        f"95% CI [{cand_cpied['ci95'][0]:.4f}, {cand_cpied['ci95'][1]:.4f}] "
        f"(vs S1=0.0214, G70_P8=0.0854, G32_B2=0.0954)",
        flush=True,
    )
    exp_report["concealed_piedmont_sgmc_v1_readonly"] = {
        "scores": cpied_summary["scores"],
        "paired_differences_vs_candidate": cpied_summary["paired_differences"],
    }
    (ROOT / "evidence/experiments_holdout.json").write_text(json.dumps(exp_report, indent=2, allow_nan=False) + "\n")

    # Run automated 950-raster 53-repo Lane & Duplicate Gate
    reg_dir = ROOT / ".cache/registry_index"
    uniq_audit = audit_candidate_against_registry(live_surface, final_arr, reg_dir)

    # Extract specific peer comparisons (GEMSDOE32 0.2778, ApartGEMSDOE1 S1 0.0525, GEMSDOE70 P8 0.2478)
    # and max overlap vs genuine <=125k-dot detectors (excluding 200k+ uniform calibration lattices)
    competing_list = [
        c for c in uniq_audit["top_10_by_3px_overlap"]
        if c["peer_dots"] <= 125_000 and "calib_" not in c["peer"].lower()
    ]
    max_ov_competing = competing_list[0]["overlap_3px_cand_in_peer"] if competing_list else uniq_audit["max_3px_overlap_cand_in_peer"]

    print(
        f"      950-raster Uniqueness Gate: is_unique={uniq_audit['is_unique_pass']} | "
        f"max |rho_surf|={abs(uniq_audit['max_pre_placement_spearman']):.4f} | "
        f"max |rho_dots|={abs(uniq_audit['max_final_dots_spearman']):.4f} | "
        f"max 3px overlap (all 950)={uniq_audit['max_3px_overlap_cand_in_peer']*100:.2f}% | "
        f"max 3px overlap (competing <=125k)={max_ov_competing*100:.2f}%",
        flush=True,
    )
    if not uniq_audit["is_unique_pass"]:
        raise RuntimeError(f"PROTOCOL RULE 1 UNIQUENESS GATE FAILED: {uniq_audit}")

    # Compute exact 3-px dot overlap against all 9 Focus-9 champions + Session 1 + GEMSDOE70
    cy_me, cx_me = np.nonzero(final_arr > 0.5)
    pts_me = np.column_stack([cy_me, cx_me]).astype(np.float64)
    tree_me = cKDTree(pts_me)

    def _pair_ov3(ref_tif: Path) -> dict[str, float]:
        if not ref_tif.exists():
            return {"overlap_3px_fraction": 0.0, "peer_in_cand_3px": 0.0, "symmetric_f1_3px": 0.0}
        with rasterio.open(ref_tif) as ds_r:
            ar = ds_r.read(1)
        ry, rx = np.nonzero(np.isfinite(ar) & fp & (ar > 0.5))
        pts_r = np.column_stack([ry, rx]).astype(np.float64)
        tree_r = cKDTree(pts_r)
        c2p = float(np.mean(np.isfinite(tree_r.query(pts_me, distance_upper_bound=3.000001)[0])))
        p2c = float(np.mean(np.isfinite(tree_me.query(pts_r, distance_upper_bound=3.000001)[0])))
        f1 = (2.0 * c2p * p2c / (c2p + p2c)) if (c2p + p2c) > 0 else 0.0
        return {
            "overlap_3px_fraction": round(c2p, 5),
            "peer_in_cand_3px": round(p2c, 5),
            "symmetric_f1_3px": round(f1, 5),
        }

    focus_audit = json.loads((ROOT / "evidence/focus_sites_forensic_audit.json").read_text())
    vs_focus9: dict[str, dict[str, float]] = {}
    for row_f9 in focus_audit["focus_9_sites"]:
        site = row_f9["site"]
        vs_focus9[site] = _pair_ov3(ROOT / ".cache/peer_repos" / site / row_f9["tif_rel"])

    vs_s1 = _pair_ov3(ROOT / "docs/downloads/archive/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif")
    vs_g70 = _pair_ov3(ROOT / ".cache/peer_repos/GEMSDOE70/docs/downloads/gems70-p5-dual-submod300-oof38k-20261020.tif")

    decoded_fp_sha = hashlib.sha256(np.ascontiguousarray(final_arr[fp], dtype=np.float32).tobytes()).hexdigest()
    uniq_full = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "overall_uniqueness_passed": uniq_audit["is_unique_pass"],
        "decoded_footprint_sha256": decoded_fp_sha,
        "max_3px_overlap_vs_competing_detectors": max_ov_competing,
        "vs_focus_9_champions": vs_focus9,
        "vs_session_1_archived_50e7b334": vs_s1,
        "vs_gemsdoe70_p8_02478": vs_g70,
        "registry_audit": uniq_audit,
    }
    (ROOT / "evidence/uniqueness_gate.json").write_text(json.dumps(uniq_full, indent=2, allow_nan=False) + "\n")

    print(f"[6/6] Packaging fail-closed GeoTIFF & running automated validator ({time.time()-t0:.1f}s)...", flush=True)
    fp_short = decoded_fp_sha[:8]
    dl_dir = ROOT / "docs/downloads"
    dl_dir.mkdir(parents=True, exist_ok=True)
    for old_f in dl_dir.glob("apartgems1-*"):
        if old_f.is_file():
            old_f.unlink()

    tif_name = f"apartgems1-plkc-dualoof-{winner_id.lower()}-20261028-{fp_short}-zeros.tif"
    tif_path = dl_dir / tif_name
    sub_name = f"apartgems1-plkc-dualoof-{winner_id.lower()}-{fp_short}"
    n_dots_emit = int((final_arr > 0.5).sum())
    sub_note = (
        f"H-APART-5 PLKC-DualOOF ({winner_id}): Dual-OOF 1m/10m chi+updip+GDR1391+piedmont; "
        f"CELF d>=2.8, [0,1] zeros ({n_dots_emit} px)."
    )
    assert len(sub_name) <= 140 and len(sub_note) <= 140

    writer_receipt = write_submission(
        tif_path,
        final_arr,
        ROOT / "data/sample_submission.tif",
        fp,
        name=sub_name,
        note=sub_note,
        catalogue=grid.catalogue,
        metadata={
            "hypothesis": "H-APART-5 (PLKC-DualOOF-CELF)",
            "winner_experiment": winner_id,
            "holdout_dti_seed2026": winner_score["dti"],
            "holdout_ci95_seed2026": winner_score["ci95"],
            "concealed_piedmont_dti_sgmc_v1": cand_cpied["dti"],
            "surface_max_abs_spearman": abs(uniq_audit["max_pre_placement_spearman"]),
            "dot_max_3px_overlap_all950": uniq_audit["max_3px_overlap_cand_in_peer"],
        },
    )

    val_receipt = validate(tif_path, footprint=fp, catalogue=grid.catalogue)
    assert_submittable(val_receipt)

    crowd = _crowding_metrics(final_arr)
    assert crowd["frac_nn_lt_2_8px"] == 0.0, f"Expected 0 dots with NN < 2.8 px, got {crowd}"

    edt_cat = distance_transform_edt(~grid.catalogue)
    collar_dots = int(((final_arr > 0) & (edt_cat <= 2.0)).sum())
    farfield_dots = int(((final_arr > 0) & (edt_cat > 15.0)).sum())
    assert collar_dots == 0, f"Expected 0 dots inside <=200m collar, got {collar_dots}"

    validation_full = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "submission_file": f"docs/downloads/{tif_name}",
        "submission_zip": f"docs/downloads/{tif_path.with_suffix('.zip').name}",
        "submission_name": sub_name,
        "submission_note": sub_note,
        "submission_note_chars": len(sub_note),
        "writer_receipt": writer_receipt,
        "validator_receipt": val_receipt,
        "crowding_diagnostics": crowd,
        "oof_synthesis_diagnostics": oof_diag,
        "collar_le_200m_dots": collar_dots,
        "farfield_gt_1500m_dots": farfield_dots,
        "farfield_gt_1500m_fraction": round(farfield_dots / max(val_receipt["emitted_positive_pixels"], 1), 6),
        "uniqueness_passed": uniq_audit["is_unique_pass"],
        "ready_to_submit_verdict": "PASS_OK_TO_DOWNLOAD_AND_SUBMIT",
    }
    (ROOT / "evidence/validation_receipt.json").write_text(json.dumps(validation_full, indent=2, allow_nan=False) + "\n")

    beats_s1 = winner_score["dti"] > 0.052328 and cand_cpied["dti"] > 0.021384
    verdict = "promote" if (
        beats_s1
        and canary_report["all_passed"]
        and uniq_audit["is_unique_pass"]
        and val_receipt["all_checks_passed"]
        and crowd["frac_nn_lt_2_8px"] == 0.0
    ) else "negative"

    run_card = {
        "protocol": "GEMS Parallel-Run Protocol v1",
        "branch": "arena/eceaf9f6-apartgemsdoe1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "H-APART-5 (PLKC-DualOOF-CELF): Pluvial-Shoreline-Deconfounded 1m/10m Scarp + Fluvial Chi/Ksn Knickzone + 60-deg Updip Gravity/Magnetic & Hydrothermal Conduit Dual-Regime Nested-OOF + Zero-SGMC Concealed Piedmont Specialist + CELF Noisy-OR d>=2.8 Allocation",
        "mechanism": "Combines preserved-NaN 1m LiDAR scarps (74.2% interior coverage) with quantile-calibrated 10m 3DEP slope/curvature, across-fault fluvial chi/ksn knickzones, 60-deg updip-migrated gravity/RTP-magnetic contacts, GeoDAWN K/Th & U/Th alteration, GDR #1391 thermal springs/2m-probes/sinter/vents, Stage-2 8-azimuth directional line-integrals, a dedicated zero-SGMC basin-cover specialist head (b15_depth_base >= 180 m), and fold-visible tip/relay continuation across two 45-deg-offset 4-sector 100%-OOF partitions, emitted via CELF max-heap submodular allocation at min_sep_px=2.8 (>200 m catalogue collar).",
        "named_non_fault_mimic_process": "Pleistocene Lake Lahontan (1,330 m) and Lake Bonneville/Provo (1,463 m / 1,558 m) wave-cut paleoshoreline benches, radial alluvial-fan incised washes, US Census TIGER highway/rail embankments, GeoDAWN aeromagnetic/radiometric flight-block stitching seams, and circular volcanic/erosional knobs (suppressed via orthometric pluvial-bench x zero-basement-gradient deconfounder, drainage-orthogonal alignment, TIGER road distance, acquisition_block_id seam weighting, and Stage-2 1.5 km directional anisotropy).",
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": winner_score["evaluator_version"],
            "split": "gems57-pooled-hide-v2 (seed=2026, buffer_px=3, 20 km spatial block bootstrap)",
            "withheld_positive_pixels": winner_score["withheld_positive_pixels"],
            "dti": round(winner_score["dti"], 6),
            "ci95": [round(winner_score["ci95"][0], 6), round(winner_score["ci95"][1], 6)],
            "session_1_archived_holdout_dti": 0.052328,
            "detached_gt_800m_blind_dti": round(winner.detached_dti, 6),
            "seed_20_stability_dti": round(pooled_s20["scores"][key_by_id[winner_id]]["dti"], 6),
            "experiments_progression": {
                key_by_id["E1"]: round(pooled_win["scores"][key_by_id["E1"]]["dti"], 6),
                key_by_id["E2"]: round(pooled_win["scores"][key_by_id["E2"]]["dti"], 6),
                key_by_id["E3"]: round(pooled_win["scores"][key_by_id["E3"]]["dti"], 6),
            },
        },
        "concealed_piedmont_holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": cand_cpied["evaluator_version"],
            "note": "Strictly read-only diagnostic on concealed USGS SGMC piedmont/basin faults (>250m from catalogue, depth_to_base >= 250m); zero SGMC used in features or training.",
            "withheld_positive_pixels": cand_cpied["withheld_positive_pixels"],
            "dti": round(cand_cpied["dti"], 6),
            "ci95": [round(cand_cpied["ci95"][0], 6), round(cand_cpied["ci95"][1], 6)],
            "vs_session_1_00525": 0.021384,
            "vs_gemsdoe70_p8_02478": round(cpied_summary["scores"].get("GEMSDOE70_P8_02478", {}).get("dti", 0.0), 6),
            "vs_gemsdoe32_b2_02778": round(cpied_summary["scores"].get("GEMSDOE32_B2_02778", {}).get("dti", 0.0), 6),
        },
        "leakage_canary": {
            "features_tested": len(canary_report["features"]),
            "max_symmetric_auc": canary_report["max_symmetric_auc"],
            "cap": 0.90,
            "all_passed": canary_report["all_passed"],
        },
        "registry_uniqueness": {
            "repositories_checked": uniq_audit["n_repos_scanned"],
            "unique_rasters_checked": uniq_audit["n_registry_rasters_checked"],
            "competing_sparse_detectors_checked": uniq_audit["n_competing_sparse_detectors_checked"],
            "pre_placement_surface_max_abs_spearman": abs(uniq_audit["max_pre_placement_spearman"]),
            "pre_placement_nearest_peer": uniq_audit["max_pre_placement_spearman_peer"],
            "post_placement_final_max_abs_spearman": abs(uniq_audit["max_final_dots_spearman"]),
            "post_placement_max_3px_overlap_all_950": uniq_audit["max_3px_overlap_cand_in_peer"],
            "post_placement_max_3px_overlap_vs_competing": max_ov_competing,
            "post_placement_max_3px_symmetric_f1_all_950": uniq_audit["max_3px_symmetric_f1_all_950"],
            "vs_gemsdoe32_02778_3px_overlap": vs_focus9.get("GEMSDOE32", {}).get("overlap_3px_fraction", 0.0),
            "vs_session_1_50e7b334_3px_overlap": vs_s1["overlap_3px_fraction"],
            "vs_gemsdoe70_02478_3px_overlap": vs_g70["overlap_3px_fraction"],
            "nearest_3px_overlap_peer": uniq_audit["nearest_3px_overlap_peer"],
            "spearman_cap": 0.90,
            "overlap_3px_cap": 0.70,
            "passed": uniq_audit["is_unique_pass"],
        },
        "raster_sha256": val_receipt["sha256"],
        "decoded_footprint_sha256": decoded_fp_sha,
        "validator_output": {
            "file": f"docs/downloads/{tif_name}",
            "zip_file": f"docs/downloads/{tif_path.with_suffix('.zip').name}",
            "bytes": val_receipt["bytes"],
            "crs": val_receipt["meta"]["crs"],
            "shape": val_receipt["meta"]["shape"],
            "transform": val_receipt["meta"]["transform"],
            "dtype": val_receipt["meta"]["dtype"],
            "nodata": val_receipt["meta"]["nodata"],
            "min": val_receipt["min"],
            "max": val_receipt["max"],
            "n_nan": val_receipt["n_nan"],
            "n_infinite": val_receipt["n_infinite"],
            "emitted_positive_pixels": val_receipt["emitted_positive_pixels"],
            "on_catalogue_positive_pixels": val_receipt["on_catalogue_positive_pixels"],
            "within_200m_collar_pixels": collar_dots,
            "farfield_gt_1500m_pixels": farfield_dots,
            "farfield_gt_1500m_fraction": round(farfield_dots / max(val_receipt["emitted_positive_pixels"], 1), 6),
            "min_nearest_neighbor_px": crowd["min_nn_px"],
            "frac_ge3_neighbors_in_3px": crowd["frac_ge3_neighbors_in_3px"],
            "all_checks_passed": val_receipt["all_checks_passed"],
        },
        "submission_name": sub_name,
        "submission_note": sub_note,
        "submission_note_chars": len(sub_note),
        "verdict": verdict,
    }
    (ROOT / "evidence/run_card.json").write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n")
    (ROOT / "docs/data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs/data/run_summary.json").write_text(json.dumps({
        "run_card": run_card,
        "experiments": exp_report,
        "leakage_canary": canary_report,
        "uniqueness": uniq_full,
        "validation": validation_full,
    }, indent=2, allow_nan=False) + "\n")

    print(f"[COMPLETE in {time.time()-t0:.1f}s] Promoted: docs/downloads/{tif_name} | verdict={verdict}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
