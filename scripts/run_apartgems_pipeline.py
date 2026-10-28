#!/usr/bin/env python3
"""End-to-end automated execution of H-APART-1 (UDTH-Submod) under the Parallel-Run Protocol."""
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
from scipy.ndimage import distance_transform_edt

from apartgems.features import ensure_blind_feature_cache
from apartgems.model import (
    build_final_live_submission_arrays,
    run_leakage_canaries,
    run_three_loqo_experiments,
)
from apartgems.uniqueness import check_final_raster_uniqueness, check_surface_uniqueness
from gems57 import evaluate_holdout as EH
from gems57 import load_grid
from gems57.emit import greedy_allocate
from gems57.holdout import buffered_component_draw
from gems57.submission_writer import write_submission
from gems57.validate import assert_submittable, validate


def evaluate_distance_only_control(grid, folds) -> tuple[np.ndarray, float, int]:
    """Evaluate canonical distance-only halo control (p ~ exp(-d_vis / 10)) with >2px collar."""
    fp = grid.footprint
    vis = folds[0]["visible"]
    d_vis = distance_transform_edt(~vis).astype(np.float32)
    p_dist = (0.04 * np.exp(-d_vis / 9.0)).astype(np.float32)

    emit_all = np.zeros(grid.shape, dtype=bool)
    terms_sum = None
    for q, fold in enumerate(folds):
        other_qs = [i for i in range(4) if i != q]
        n_w = sum(int(folds[i]["truth"].sum()) for i in other_qs)
        n_a = sum(int((folds[i]["region"] & fp & ~folds[i]["masked_known"]).sum()) for i in other_qs)
        test_active = fold["region"] & fp & ~fold["masked_known"]
        k_est = (n_w / max(n_a, 1)) * float(test_active.sum())
        alloc = greedy_allocate(p_dist, test_active & (d_vis > 2.0), k_truth=max(k_est, 50.0), floor=0.008, max_dots=9500)
        emit_all |= alloc.emitted
        _, bt = EH.evaluate(alloc.emitted.astype(np.float32), fold, fp)
        terms_sum = bt if terms_sum is None else (terms_sum + bt)

    det_tp = det_fp = det_fn = 0.0
    for fold in folds:
        det_fold = dict(fold)
        det_fold["truth"] = fold["truth"] & (d_vis > 8.0)
        if det_fold["truth"].any():
            dsc, _ = EH.evaluate(emit_all.astype(np.float32), det_fold, fp)
            det_tp += dsc["tpw"]
            det_fp += dsc["fpw"]
            det_fn += dsc["fnw"]
    det_dti = float(det_tp / (det_tp + 0.2 * det_fp + 0.8 * det_fn + 1e-12))
    return terms_sum, det_dti, int(emit_all.sum())


def _require_surface_unique(surface, footprint):
    result = check_surface_uniqueness(surface, footprint)
    if not result["passed"]:
        raise RuntimeError(f"pre-placement surface is a duplicate: {result}")
    return result


def main() -> int:
    # Prior lane already consumed its experiment budget. The current prompt
    # does not include the promised method paragraph; do not silently rerun it.
    raise RuntimeError("No current lane method paragraph supplied; prior lane budget exhausted. Do not generate or promote a submission.")
    t0 = time.time()
    grid = load_grid()
    fp = grid.footprint

    print(f"[1/6] Building & caching 14 blind physical feature maps ({time.time()-t0:.1f}s)...", flush=True)
    feat_paths = ensure_blind_feature_cache(grid, force=False)

    print(f"[2/6] Building canonical gems57-pooled-hide-v2 holdout (seed=2026) ({time.time()-t0:.1f}s)...", flush=True)
    folds, _ = buffered_component_draw(grid, seed=2026, hide_frac=0.20, buffer_px=3)

    print(f"[3/6] Running single-feature Leakage Canaries (cap <= 0.90) ({time.time()-t0:.1f}s)...", flush=True)
    canary_report = run_leakage_canaries(grid, folds, feat_paths, canary_cap=0.90)
    (ROOT / "evidence/leakage_canary.json").write_text(json.dumps(canary_report, indent=2) + "\n")
    print(f"      Canary max symmetric AUC = {canary_report['max_symmetric_auc']:.4f} (all_passed={canary_report['all_passed']})", flush=True)
    if not canary_report["all_passed"]:
        raise RuntimeError(f"LEAKAGE CANARY FAILED (>0.90): {canary_report}")

    print(f"[4/6] Executing <= 3 Pre-Registered LOQO Experiments (E1, E2, E3) + Controls ({time.time()-t0:.1f}s)...", flush=True)
    exp_results, crest_map = run_three_loqo_experiments(grid, folds, feat_paths)
    zero_terms = sum(EH.evaluate(np.zeros(grid.shape, np.float32), f, fp)[1] for f in folds)
    dist_terms, dist_det_dti, dist_emitted = evaluate_distance_only_control(grid, folds)

    terms_map = {
        "zero_control": zero_terms,
        "distance_only_collar2_control": dist_terms,
        "E1_udpc_dopsr_blind": exp_results["E1"].block_terms,
        "E2_udpc_dopsr_hmcs_blind": exp_results["E2"].block_terms,
        "E3_udth_submod_full": exp_results["E3"].block_terms,
    }
    # Pick highest HOLDOUT-DTI among E1, E2, E3 first, then compute paired bootstrap differences vs winner
    key_by_id = {"E1": "E1_udpc_dopsr_blind", "E2": "E2_udpc_dopsr_hmcs_blind", "E3": "E3_udth_submod_full"}
    prelim = EH.pooled_summary(terms_map, draws=100, seed=520810, candidate="E2_udpc_dopsr_hmcs_blind")
    winner_id = max(("E1", "E2", "E3"), key=lambda eid: prelim["scores"][key_by_id[eid]]["dti"])
    winner = exp_results[winner_id]
    pooled_win = EH.pooled_summary(terms_map, draws=1000, seed=520810, candidate=key_by_id[winner_id])
    winner_score = pooled_win["scores"][key_by_id[winner_id]]

    for k, s in pooled_win["scores"].items():
        print(f"      {k:32s}: HOLDOUT-DTI = {s['dti']:.4f}  95% CI [{s['ci95'][0]:.4f}, {s['ci95'][1]:.4f}]", flush=True)
    for eid in ("E1", "E2", "E3"):
        r = exp_results[eid]
        print(f"      {eid} detached (>800m blind) DTI = {r.detached_dti:.4f}, emitted_oof_dots = {int(r.oof_emitted.sum())}", flush=True)
    print(f"      distance_only detached (>800m blind) DTI = {dist_det_dti:.4f}, emitted_oof_dots = {dist_emitted}", flush=True)

    # Multi-seed robustness check on canonical seed=20 (11,321 withheld positive pixels)
    print(f"      Running multi-seed stability verification (seed=20) ({time.time()-t0:.1f}s)...", flush=True)
    folds_s20, _ = buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    exp_s20, _ = run_three_loqo_experiments(grid, folds_s20, feat_paths)
    zero_s20 = sum(EH.evaluate(np.zeros(grid.shape, np.float32), f, fp)[1] for f in folds_s20)
    dist_s20, _, _ = evaluate_distance_only_control(grid, folds_s20)
    pooled_s20 = EH.pooled_summary(
        {
            "zero_control": zero_s20,
            "distance_only_collar2_control": dist_s20,
            "E1_udpc_dopsr_blind": exp_s20["E1"].block_terms,
            "E2_udpc_dopsr_hmcs_blind": exp_s20["E2"].block_terms,
            "E3_udth_submod_full": exp_s20["E3"].block_terms,
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
        "experiment_budget_used": 3,
        "experiment_budget_cap": 3,
        "primary_draw_seed_2026": {
            "scores": pooled_win["scores"],
            "paired_differences_vs_winner": pooled_win["paired_differences"],
            "bootstrap": pooled_win["bootstrap"],
            "detached_gt_800m_blind_dti": {
                "distance_only_collar2_control": round(dist_det_dti, 6),
                "E1_udpc_dopsr_blind": round(exp_results["E1"].detached_dti, 6),
                "E2_udpc_dopsr_hmcs_blind": round(exp_results["E2"].detached_dti, 6),
                "E3_udth_submod_full": round(exp_results["E3"].detached_dti, 6),
            },
            "per_fold_details": {eid: exp_results[eid].per_fold for eid in ("E1", "E2", "E3")},
        },
        "secondary_stability_seed_20": {
            "scores": pooled_s20["scores"],
            "paired_differences_vs_winner": pooled_s20["paired_differences"],
        },
        "selected_winner": winner_id,
    }
    (ROOT / "evidence/experiments_holdout.json").write_text(json.dumps(exp_report, indent=2, allow_nan=False) + "\n")

    print(f"[5/6] Generating full-footprint live surface & final raster for {winner_id} + Dual Uniqueness Gates ({time.time()-t0:.1f}s)...", flush=True)
    live_surface, final_arr = build_final_live_submission_arrays(grid, winner, feat_paths, crest_map, target_dots=38_500,
        before_placement=lambda surface, footprint: _require_surface_unique(surface, footprint))

    surf_uniq = check_surface_uniqueness(live_surface, fp, spearman_cap=0.90)
    print(f"      Pre-placement surface max |Spearman rho| = {surf_uniq['max_abs_spearman_rho']:.4f} (passed={surf_uniq['passed']})", flush=True)
    if not surf_uniq["passed"]:
        raise RuntimeError(f"PRE-PLACEMENT SURFACE UNIQUENESS GATE FAILED: {surf_uniq}")

    dot_uniq = check_final_raster_uniqueness(final_arr, fp, spearman_cap=0.90, overlap_cap=0.70)
    print(
        f"      Post-placement dots={dot_uniq['candidate_emitted_dots']}, "
        f"max |Spearman rho|={dot_uniq['max_abs_spearman_rho']:.4f}, "
        f"max 3-px overlap={dot_uniq['max_3px_overlap_vs_competing_detectors']*100:.2f}% "
        f"(passed={dot_uniq['passed']})",
        flush=True,
    )
    if not dot_uniq["passed"]:
        raise RuntimeError(f"POST-PLACEMENT DOT UNIQUENESS GATE FAILED: {dot_uniq}")

    uniq_full = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "pre_placement_surface_gate": surf_uniq,
        "post_placement_final_raster_gate": dot_uniq,
        "overall_uniqueness_passed": bool(surf_uniq["passed"] and dot_uniq["passed"]),
    }
    (ROOT / "evidence/uniqueness_gate.json").write_text(json.dumps(uniq_full, indent=2, allow_nan=False) + "\n")

    print(f"[6/6] Packaging fail-closed GeoTIFF & running automated validator ({time.time()-t0:.1f}s)...", flush=True)
    fp_short = dot_uniq["candidate_decoded_fp_sha256"][:8]
    dl_dir = ROOT / "docs/downloads"
    dl_dir.mkdir(parents=True, exist_ok=True)

    tif_name = f"apartgems1-udth-submod-{winner_id.lower()}-20261027-{fp_short}-zeros.tif"
    tif_path = dl_dir / tif_name
    sub_name = f"apartgems1-udth-submod-{winner_id.lower()}-{fp_short}"
    sub_note = (
        f"H-APART-1 UDTH-Submod ({winner_id}): updip grav/mag tilt + 1m/10m scarp + GDR1391 thermal; "
        f"all-finite [0,1], >200m collar ({dot_uniq['candidate_emitted_dots']} px)."
    )
    if len(sub_note) > 140:
        sub_note = f"H-APART-1 UDTH-Submod ({winner_id}): updip grav/mag + 1m/10m scarp + GDR1391 thermal; [0,1] zeros ({dot_uniq['candidate_emitted_dots']} px)."
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
            "hypothesis": "H-APART-1 (UDTH-Submod)",
            "winner_experiment": winner_id,
            "holdout_dti_seed2026": winner_score["dti"],
            "holdout_ci95_seed2026": winner_score["ci95"],
            "surface_max_abs_spearman": surf_uniq["max_abs_spearman_rho"],
            "dot_max_3px_overlap": dot_uniq["max_3px_overlap_vs_competing_detectors"],
        },
    )

    val_receipt = validate(tif_path, footprint=fp, catalogue=grid.catalogue)
    assert_submittable(val_receipt)

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
        "collar_le_200m_dots": collar_dots,
        "farfield_gt_1500m_dots": farfield_dots,
        "farfield_gt_1500m_fraction": round(farfield_dots / max(val_receipt["emitted_positive_pixels"], 1), 6),
        "uniqueness_passed": uniq_full["overall_uniqueness_passed"],
        "ready_to_submit_verdict": "NOT_APPROVED_FOR_WEEKLY_SLOT",
    }
    (ROOT / "evidence/validation_receipt.json").write_text(json.dumps(validation_full, indent=2, allow_nan=False) + "\n")

    # Determine promotion verdict strictly from holdout DTI + gates
    # A fixed arbitrary threshold does not establish improvement over the
    # current comparable holdout best, nor authorize a weekly slot.
    beats_zero = False
    verdict = "promote" if (
        beats_zero
        and canary_report["all_passed"]
        and uniq_full["overall_uniqueness_passed"]
        and val_receipt["all_checks_passed"]
    ) else "negative"

    run_card = {
        "protocol": "GEMS Parallel-Run Protocol v1",
        "branch": "arena/0e7fd28c-apartgemsdoe1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "H-APART-1 (UDTH-Submod): Updip Dip-Backprojected Gravity/Magnetic Phase-Tilt Contacts + Seam-Free 1m LiDAR / 10m 3DEP Drainage-Orthogonal Scarp Tensor + Hydrothermal Magnetite-Destruction / K-Adularia / MT / GDR-1391 Thermal Upflow + Fold-Visible Tip/Step-Over Relay Continuation",
        "mechanism": "Normal faults in the extensional NW Great Basin dip ~55-62 deg into Cenozoic basins, displacing basement gravity/magnetic tilt zero-crossings downdip by z_b*cot(58 deg); backprojecting potential-field contacts updip into alignment with drainage-orthogonal 1m/10m scarps, hydrothermal magnetite destruction + K/Th alteration + MT conductivity + GDR #1391 springs/2m-probes/paleo-sinter vents, and directional visible tip/relay bridges recovers hidden sub-alluvial faults and blind geothermal conduits within the 300 m DTI kernel.",
        "named_non_fault_mimic_process": "Pleistocene Lake Lahontan wave-cut constructional benches (~1,330 m), radial alluvial-fan incised washes, TIGER highway/rail embankments, and unfaulted Tertiary mafic dikes (actively suppressed via drainage-orthogonal strike alignment, TIGER road-corridor deconfounding, and magnetite-destruction vs mafic-dike polarity gating).",
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": winner_score["evaluator_version"],
            "split": "gems57-pooled-hide-v2 (seed=2026, buffer_px=3, 20 km block bootstrap)",
            "withheld_positive_pixels": winner_score["withheld_positive_pixels"],
            "dti": round(winner_score["dti"], 6),
            "ci95": [round(winner_score["ci95"][0], 6), round(winner_score["ci95"][1], 6)],
            "detached_gt_800m_blind_dti": round(winner.detached_dti, 6),
            "seed_20_stability_dti": round(pooled_s20["scores"][key_by_id[winner_id]]["dti"], 6),
            "experiments_progression": {
                "E1_udpc_dopsr_blind": round(pooled_win["scores"]["E1_udpc_dopsr_blind"]["dti"], 6),
                "E2_udpc_dopsr_hmcs_blind": round(pooled_win["scores"]["E2_udpc_dopsr_hmcs_blind"]["dti"], 6),
                "E3_udth_submod_full": round(pooled_win["scores"]["E3_udth_submod_full"]["dti"], 6),
            },
        },
        "leakage_canary": {
            "features_tested": len(canary_report["features"]),
            "max_symmetric_auc": canary_report["max_symmetric_auc"],
            "cap": 0.90,
            "all_passed": canary_report["all_passed"],
        },
        "registry_uniqueness": {
            "repositories_checked": 22,
            "unique_rasters_checked": dot_uniq["rasters_checked"],
            "competing_sparse_detectors_checked": dot_uniq["competing_sparse_detectors_checked"],
            "pre_placement_surface_max_abs_spearman": surf_uniq["max_abs_spearman_rho"],
            "post_placement_final_max_abs_spearman": dot_uniq["max_abs_spearman_rho"],
            "post_placement_max_3px_overlap_vs_competing": dot_uniq["max_3px_overlap_vs_competing_detectors"],
            "vs_gemsdoe32_02778_3px_overlap": dot_uniq["vs_focus_9_champions"].get("GEMSDOE32", {}).get("overlap_3px_fraction"),
            "vs_gemsdoe32_02778_spearman": dot_uniq["vs_focus_9_champions"].get("GEMSDOE32", {}).get("spearman_rho"),
            "spearman_cap": 0.90,
            "overlap_3px_cap": 0.70,
            "passed": uniq_full["overall_uniqueness_passed"],
        },
        "raster_sha256": val_receipt["sha256"],
        "decoded_footprint_sha256": dot_uniq["candidate_decoded_fp_sha256"],
        "validator_output": {
            "file": f"docs/downloads/{tif_name}",
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
            "all_checks_passed": val_receipt["all_checks_passed"],
        },
        "submission_name": sub_name,
        "submission_note": sub_note,
        "submission_note_chars": len(sub_note),
        "verdict": verdict,
    }
    (ROOT / "evidence/run_card.json").write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n")
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
