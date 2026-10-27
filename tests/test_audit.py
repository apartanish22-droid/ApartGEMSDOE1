from pathlib import Path
import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from scipy.stats import spearmanr

from audit_fleet import binary_spearman, lower_bound, nearby_to, overlap_fraction, raster_snapshot, validate_pins
from download_audit_inputs import check_entry, load_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_budget_bound_is_strict_at_seventy_percent():
    assert lower_bound(3, 10)["minimum_fraction"] == pytest.approx(0.7)
    assert not lower_bound(3, 10)["forced_duplicate_stop"]
    assert lower_bound(2, 10)["forced_duplicate_stop"]
    assert not lower_bound(6649, 22163)["forced_duplicate_stop"]
    assert lower_bound(6649, 22164)["forced_duplicate_stop"]
    assert lower_bound(6649, 37654)["minimum_matches"] == 31005
    assert lower_bound(50, 3)["minimum_fraction"] == 0
    with pytest.raises(ValueError):
        lower_bound(0, 0)
    with pytest.raises(ValueError):
        lower_bound(-1, 1)


def test_euclidean_radius_and_directional_overlap():
    ref = np.zeros((11, 11), dtype=bool)
    ref[5, 5] = True
    near = nearby_to(ref, 3)
    assert near[8, 5]             # exactly 3 pixels, inclusive
    assert not near[8, 6]         # sqrt(10) pixels, outside
    dots = np.zeros_like(ref)
    dots[8, 5] = dots[8, 6] = True
    assert overlap_fraction(dots, near) == {"candidate_dots": 2, "within_radius": 1,
                                            "fraction": 0.5, "duplicate_stop": False}
    with pytest.raises(ValueError):
        nearby_to(np.zeros((3, 3), bool))
    with pytest.raises(ValueError):
        nearby_to(ref, float("nan"))
    with pytest.raises(ValueError):
        overlap_fraction(np.zeros_like(ref), near)


def test_binary_spearman_respects_ties_and_constant_inputs():
    a = np.array([[0, 1, 0, 1], [1, 0, 1, 0]], dtype=bool)
    b = np.array([[0, 1, 1, 1], [0, 0, 1, 0]], dtype=bool)
    valid = np.array([[1, 1, 1, 0], [1, 1, 1, 1]], dtype=bool)
    expected = spearmanr(a[valid].astype(int), b[valid].astype(int)).statistic
    assert binary_spearman(a, b, valid) == pytest.approx(expected)
    assert binary_spearman(np.zeros_like(a), b, valid) is None
    with pytest.raises(ValueError):
        binary_spearman(a, b[:, :2], valid)


def write_tif(path, array, transform=None, crs="EPSG:32611"):
    with rasterio.open(path, "w", driver="GTiff", height=array.shape[0], width=array.shape[1],
                       count=1, dtype="float32", crs=crs,
                       transform=transform or from_origin(100, 100, 1, 1), nodata=np.nan) as dst:
        dst.write(array.astype("float32"), 1)


def test_saved_raster_diagnostics_and_invalid_inputs(tmp_path):
    foot = np.array([[0, 1, 1], [0, 1, 1], [0, 1, 1]], dtype=bool)
    array = np.array([[np.nan, 0, 0], [np.nan, 1, 0], [np.nan, 0, 0]], dtype="float32")
    transform = from_origin(100, 100, 1, 1)
    path = tmp_path / "reference.tif"
    write_tif(path, array, transform)
    result, positive = raster_snapshot(path, (3, 3), rasterio.crs.CRS.from_epsg(32611), transform, foot)
    assert result["inside_positive_pixels"] == 1 and positive[1, 1]
    assert result["nonfinite_inside"] == 0 and result["outside_nonfinite"] == 3
    assert result["inside_min"] == 0 and result["inside_max"] == 1
    assert len(result["sha256"]) == 64

    with pytest.raises(ValueError, match="grid/band mismatch"):
        raster_snapshot(path, (3, 3), rasterio.crs.CRS.from_epsg(32611), from_origin(101, 100, 1, 1), foot)
    for invalid in (np.nan, np.inf, -0.1, 1.1):
        bad = array.copy()
        bad[0, 1] = invalid
        write_tif(path, bad, transform)
        with pytest.raises(ValueError, match="non-finite or out-of-range"):
            raster_snapshot(path, (3, 3), rasterio.crs.CRS.from_epsg(32611), transform, foot)
    bad = array.copy()
    bad[1, 1] = 0.2
    write_tif(path, bad, transform)
    with pytest.raises(ValueError, match="requires a binary reference"):
        raster_snapshot(path, (3, 3), rasterio.crs.CRS.from_epsg(32611), transform, foot)


def test_manifest_checks_and_missing_pins_fail_closed(tmp_path):
    manifest = load_manifest(ROOT / "catalog/reference_sources.json")
    entry = manifest["support"][0].copy()
    check_entry(entry)
    for key, value in [("path", "../secrets"), ("path", "data/a.tif?ref=evil"),
                       ("ref", "main"), ("sha256", "abc"), ("owner", "../../evil")]:
        bad = entry.copy()
        bad[key] = value
        with pytest.raises(ValueError):
            check_entry(bad)
    with pytest.raises(ValueError, match="Missing or corrupt"):
        validate_pins([entry], tmp_path)


def test_saved_audit_and_run_card_are_not_misrepresented_as_results():
    audit = json.loads((ROOT / "evidence/fleet_audit.json").read_text())
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert audit["evidence_class"] == "DATA-MEASUREMENT, NOT A SCORE"
    assert audit["lattice"]["uncovered_footprint_pixels"] == 6649
    assert audit["lattice"]["first_budget_proven_over_70_percent"] == 22164
    assert len(audit["historical_references"]) == 9
    assert len(audit["peer_comparisons"]) == 72
    assert all(x["duplicate_stop"] for x in audit["peer_comparisons"].values())
    assert audit["lineage"]["g25_g30_identical_positive_support"]
    assert audit["lineage"]["g32_added_vs_g25"] == 0
    assert audit["lineage"]["g32_removed_vs_g25"] == 6436
    assert audit["lineage"]["g32_removed_within_2_pixels_of_mapped_mirror"] == 6436
    assert card["verdict"] == "negative"
    assert card["raster_sha256"] is None
    assert card["holdout"]["value"] is None and card["holdout"]["ci95"] is None
    assert card["registry"]["surface_rank_correlation"] is None
    assert card["submission"]["slot_selected"] is False
