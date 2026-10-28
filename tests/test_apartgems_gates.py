"""Automated pytest gate suite for ApartGEMSDOE1 (100% automated, zero human inspection required)."""
from __future__ import annotations

import json
from pathlib import Path
import zipfile

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

from gems57 import load_grid
from gems57.emit import greedy_allocate, noisy_or_self_credit
from gems57.metric import dti_bruteforce, dti_exact
from gems57.validate import assert_submittable, validate

ROOT = Path(__file__).resolve().parents[1]


def test_dti_exact_matches_bruteforce_on_synthetic_patch():
    rng = np.random.default_rng(42)
    pred = (rng.random((45, 50)) < 0.04).astype(np.float32)
    truth = rng.random((45, 50)) < 0.03
    valid = np.ones((45, 50), dtype=bool)
    known = np.zeros((45, 50), dtype=bool)
    known[10:15, 20] = True
    r_fast = dti_exact(pred, truth, valid=valid, known=known)
    r_bf = dti_bruteforce(pred * (~known), truth & (~known))
    assert np.isclose(r_fast["dti"], r_bf["dti"], atol=1e-9)


def test_celf_greedy_allocate_enforces_min_sep_and_noisy_or():
    rng = np.random.default_rng(7)
    p = (rng.random((60, 60)) * 0.25).astype(np.float32)
    allowed = np.ones((60, 60), dtype=bool)
    q_self = noisy_or_self_credit(p)
    assert float(q_self.max()) < 1.0
    res = greedy_allocate(p, allowed, k_truth=80.0, floor=0.01, max_dots=60, min_sep_px=2.8, use_marginal_bar=False)
    ys, xs = np.nonzero(res.emitted)
    assert ys.size == 60
    pts = np.column_stack([ys, xs]).astype(np.float64)
    d2, _ = cKDTree(pts).query(pts, k=2)
    assert float(d2[:, 1].min()) >= 2.7999


def test_zero_sgmc_and_no_leak_column_in_training_code():
    import ast

    for rel in ("src/apartgems/features.py", "src/apartgems/model.py"):
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        # Strip module/function/class docstring Expr nodes and inspect all executable string constants
        doc_nodes: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                    doc_nodes.add(id(first.value))
        code_strings = [
            n.value.lower()
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc_nodes
        ]
        for s in code_strings:
            assert "dist_known_fault_px" not in s, f"Forbidden leak col in {rel}: {s}"
            assert "derived_sgmc" not in s and "sgmc_faults" not in s, f"Forbidden SGMC ref in {rel}: {s}"


def test_focus9_forensic_zero_xor_and_audit_table():
    audit_p = ROOT / "evidence/focus_sites_forensic_audit.json"
    assert audit_p.exists()
    audit = json.loads(audit_p.read_text())
    proof = audit["forensic_proof_02778"]
    assert proof["xor_differing_pixels_across_5167373_footprint"] == 0
    assert proof["xor_gemsdoe25_vs_gemsdoe30"] == 0
    assert proof["b2_dots"] == 37654
    assert proof["parent_dots"] == 44090
    assert proof["removed_collar_dots"] == 6436

    sites = {r["site"] for r in audit["focus_9_sites"]}
    expected = {
        "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28",
        "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
    }
    assert sites == expected
    for r in audit["focus_9_sites"]:
        assert r["max_3px_overlap_vs_other_focus9"] > 0.70
        assert r["ok_to_resubmit_as_new"] is False


def test_leakage_canary_and_holdout_progression():
    canary = json.loads((ROOT / "evidence/leakage_canary.json").read_text())
    assert canary["all_passed"] is True
    assert canary["max_symmetric_auc"] <= 0.90
    assert len(canary["features"]) == 47

    exp = json.loads((ROOT / "evidence/experiments_holdout.json").read_text())
    assert exp["experiment_budget_used"] <= 3
    sc = exp["primary_draw_seed_2026"]["scores"]
    assert sc["zero_control"]["dti"] == 0.0
    assert sc["distance_only_collar2_control"]["dti"] > 0.0
    # Strict monotonic progression & beating Session 1 archived 0.052328
    assert sc["E1_plkc_dual_regime_blind"]["dti"] > 0.052328
    assert sc["E1_plkc_dual_regime_blind"]["dti"] > sc["distance_only_collar2_control"]["dti"]
    assert sc["E2_plkc_hydro_stage2_vessel"]["dti"] > sc["E1_plkc_dual_regime_blind"]["dti"]
    assert sc["E3_plkc_dualoof_celf_full"]["dti"] > sc["E2_plkc_hydro_stage2_vessel"]["dti"]

    # Detached blind (>800 m) DTI must strictly beat distance_only (0.0000) and Session 1 (0.0332)
    det = exp["primary_draw_seed_2026"]["detached_gt_800m_blind_dti"]
    assert det["distance_only_collar2_control"] == 0.0
    assert det["E3_plkc_dualoof_celf_full"] > 0.060

    # Paired bootstrap CI vs distance_only strictly > 0
    delta_ci = exp["primary_draw_seed_2026"]["paired_differences_vs_winner"]["distance_only_collar2_control"]["ci95"]
    assert delta_ci[0] > 0.0

    # Secondary seed=20 stability check confirms monotonic winner > Session 1
    sc20 = exp["secondary_stability_seed_20"]["scores"]
    assert sc20["E3_plkc_dualoof_celf_full"]["dti"] > sc20["E2_plkc_hydro_stage2_vessel"]["dti"]
    assert sc20["E2_plkc_hydro_stage2_vessel"]["dti"] > sc20["E1_plkc_dual_regime_blind"]["dti"]

    # Read-only Zero-SGMC Concealed Piedmont benchmark beats Session 1, GEMSDOE70, and GEMSDOE32
    cp = exp["concealed_piedmont_sgmc_v1_readonly"]["scores"]
    assert cp["candidate_plkc"]["dti"] > cp["ApartGEMSDOE1_S1_00525"]["dti"] * 4.0
    assert cp["candidate_plkc"]["dti"] > cp["GEMSDOE70_P8_02478"]["dti"]
    assert cp["candidate_plkc"]["dti"] > cp["GEMSDOE32_B2_02778"]["dti"]


def test_promoted_geotiff_submission_crowding_and_950_raster_uniqueness():
    rc = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert rc["verdict"] == "promote"
    assert rc["submission_note_chars"] <= 140
    assert len(rc["submission_name"]) <= 140

    tif_path = ROOT / rc["validator_output"]["file"]
    zip_path = ROOT / rc["validator_output"]["zip_file"]
    arch_s1 = ROOT / "docs/downloads/archive/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif"
    assert tif_path.exists()
    assert zip_path.exists()
    assert arch_s1.exists()

    # Ensure only the newly promoted submission sits at top level of docs/downloads/
    top_tifs = list((ROOT / "docs/downloads").glob("*.tif"))
    assert top_tifs == [tif_path]

    grid = load_grid()
    receipt = validate(tif_path, footprint=grid.footprint, catalogue=grid.catalogue)
    assert_submittable(receipt)
    assert receipt["sha256"] == rc["raster_sha256"]
    assert receipt["n_nan"] == 0
    assert receipt["n_infinite"] == 0
    assert receipt["min"] == 0.0
    assert receipt["max"] == 1.0
    assert receipt["emitted_positive_pixels"] == 37654
    assert receipt["on_catalogue_positive_pixels"] == 0

    with rasterio.open(tif_path) as ds:
        arr = ds.read(1)
        assert str(ds.crs) == "EPSG:32611"
        assert (ds.height, ds.width) == (3730, 3292)
        assert list(tuple(ds.transform)[:6]) == [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
        assert ds.nodata is None

    # Verify strict binary {0.0, 1.0}, >200m collar, and >=2.8 px minimum spacing
    uvals = np.unique(arr)
    assert set(uvals.tolist()).issubset({0.0, 1.0})
    edt_cat = distance_transform_edt(~grid.catalogue)
    assert int(((arr > 0) & (edt_cat <= 2.0)).sum()) == 0

    ys, xs = np.nonzero(arr > 0.5)
    pts = np.column_stack([ys, xs]).astype(np.float64)
    tree = cKDTree(pts)
    d2, _ = tree.query(pts, k=2)
    assert float(d2[:, 1].min()) >= 2.7999
    nbrs3 = np.array([len(v) - 1 for v in tree.query_ball_point(pts, r=3.000001)])
    assert float(np.mean(nbrs3 >= 3)) < 0.03

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert zf.read(tif_path.name) == tif_path.read_bytes()

    uniq = json.loads((ROOT / "evidence/uniqueness_gate.json").read_text())
    ra = uniq["registry_audit"]
    assert uniq["overall_uniqueness_passed"] is True
    assert ra["n_repos_scanned"] >= 50
    assert ra["n_registry_rasters_checked"] >= 900
    assert abs(ra["max_pre_placement_spearman"]) <= 0.90
    assert abs(ra["max_final_dots_spearman"]) <= 0.90
    assert ra["max_3px_overlap_cand_in_peer"] <= 0.70
    assert ra["max_3px_symmetric_f1_all_950"] <= 0.70
    assert uniq["vs_session_1_archived_50e7b334"]["overlap_3px_fraction"] <= 0.70
    assert uniq["vs_focus_9_champions"]["GEMSDOE32"]["overlap_3px_fraction"] <= 0.70
