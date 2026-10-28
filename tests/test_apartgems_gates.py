"""Automated pytest gate suite for ApartGEMSDOE1 H-APART-2 (MAW-GSI E3) — zero human inspection required."""
from __future__ import annotations

import json
from pathlib import Path
import zipfile

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from gems57 import load_grid
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

    f9_vs_me = json.loads((ROOT / "evidence/focus9_vs_promoted_audit.json").read_text())
    assert len(f9_vs_me) >= 12
    for row in f9_vs_me:
        if "NEW" not in row["site"]:
            assert row["our_3px_overlap_vs_site"] <= 0.70


def test_preregistered_hypotheses_contract():
    prereg = json.loads((ROOT / "evidence/hypotheses_preregistration.json").read_text())
    hyps = prereg["ranked_hypotheses"]
    assert 3 <= len(hyps) <= 5
    selected = [h for h in hyps if h.get("selected_for_validation")]
    assert len(selected) == 1
    assert selected[0]["id"] == "H-APART-2"
    assert selected[0]["acronym"] == "MAW-GSI"
    for h in hyps:
        assert h["layers_involved"]
        assert h["physical_signature"]
        assert h["why_missing_from_catalogue"]
        assert h["named_non_fault_mimic_processes"]
        assert h["difference_from_existing_repo"]


def test_leakage_canary_and_holdout_progression_both_seeds():
    canary = json.loads((ROOT / "evidence/leakage_canary.json").read_text())
    assert canary["all_passed"] is True
    assert canary["max_symmetric_auc"] <= 0.90
    assert len(canary["features"]) == 45

    exp = json.loads((ROOT / "evidence/experiments_holdout.json").read_text())
    assert exp["experiment_budget_used"] <= 3
    sc = exp["primary_draw_seed_2026"]["scores"]
    assert sc["zero_control"]["dti"] == 0.0
    assert sc["distance_only_collar2_control"]["dti"] > 0.0
    assert sc["E1_maw_scarp_geophys_blind"]["dti"] > sc["distance_only_collar2_control"]["dti"]
    assert sc["E1_maw_scarp_geophys_blind"]["dti"] > 0.052325  # beats prior v1 even blind!
    assert sc["E2_maw_gsi_blind_vent"]["dti"] > sc["E1_maw_scarp_geophys_blind"]["dti"]
    assert sc["E3_maw_gsi_oof_axial_relay"]["dti"] > sc["E2_maw_gsi_blind_vent"]["dti"]
    assert sc["E3_maw_gsi_oof_axial_relay"]["ci95"][0] > 0.097441  # lower 95% CI beats fold-honest GEMSDOE32 B2!

    # Detached (>800m blind) monotonic check
    det = exp["primary_draw_seed_2026"]["detached_gt_800m_blind_dti"]
    assert det["distance_only_collar2_control"] == 0.0
    assert 0.0 < det["E1_maw_scarp_geophys_blind"] < det["E2_maw_gsi_blind_vent"] < det["E3_maw_gsi_oof_axial_relay"]

    # Paired bootstrap differences vs winner all exclude zero
    pdiff = exp["primary_draw_seed_2026"]["paired_differences_vs_winner"]
    for baseline_key in ("distance_only_collar2_control", "E1_maw_scarp_geophys_blind", "E2_maw_gsi_blind_vent"):
        assert pdiff[baseline_key]["ci95"][0] > 0.0

    # Secondary seed=20 monotonic stability check
    sc20 = exp["secondary_stability_seed_20"]["scores"]
    assert sc20["E1_maw_scarp_geophys_blind"]["dti"] < sc20["E2_maw_gsi_blind_vent"]["dti"] < sc20["E3_maw_gsi_oof_axial_relay"]["dti"]
    assert sc20["E3_maw_gsi_oof_axial_relay"]["dti"] > 0.10


def test_promoted_geotiff_submission_anatomy_and_806_raster_uniqueness():
    rc = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert rc["verdict"] == "promote"
    assert rc["submission_note_chars"] <= 140
    assert len(rc["submission_note"]) == rc["submission_note_chars"]
    assert len(rc["submission_name"]) <= 140
    assert rc["holdout_dti"]["dti"] > 0.11

    tif_path = ROOT / rc["validator_output"]["file"]
    zip_path = ROOT / rc["validator_output"]["zip_file"]
    assert tif_path.exists()
    assert zip_path.exists()

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
        assert ds.nodata is None
        assert list(tuple(ds.transform)[:6]) == [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
        uniq_vals = np.unique(arr)
        assert np.array_equal(uniq_vals, np.array([0.0, 1.0], dtype=np.float32))

    edt_cat = distance_transform_edt(~grid.catalogue)
    assert int(((arr > 0) & (edt_cat <= 2.0)).sum()) == 0

    anat = rc["spatial_anatomy_and_external_audit"]
    assert anat["dots_le_200m_collar"] == 0
    assert anat["dots_200m_to_600m_fraction"] <= 0.30
    assert 6.5 <= anat["median_dot_slope_deg"] <= 9.0
    assert anat["external_sgmc_posthoc_audit"]["dti"] >= 0.042

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert zf.read(tif_path.name) == tif_path.read_bytes()

    uniq = json.loads((ROOT / "evidence/uniqueness_gate.json").read_text())
    assert uniq["overall_uniqueness_passed"] is True
    assert rc["registry_uniqueness"]["repositories_checked"] >= 50
    assert uniq["pre_placement_surface_gate"]["rasters_checked"] >= 800
    assert uniq["pre_placement_surface_gate"]["max_abs_spearman_rho"] <= 0.90
    assert uniq["post_placement_final_raster_gate"]["max_abs_spearman_rho"] <= 0.90
    assert uniq["post_placement_final_raster_gate"]["max_3px_overlap_vs_competing_detectors"] <= 0.70
