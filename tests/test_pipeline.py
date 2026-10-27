from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from scipy.spatial import cKDTree

from apartgems.policy import assess_readiness
from apartgems.scarp_normal import build_fields, dequantize, normal_contrast, spaced_dots
from gems import holdout, metric, novelty, submission

ROOT = Path(__file__).resolve().parents[1]


def test_shared_template_bytes_unchanged():
    pins = json.loads((ROOT / "vendor/template-pins.json").read_text())
    for entry in pins["files"]:
        assert hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]


def test_metric_matches_organizer_example():
    assert metric.verify_organizer_worked_example()["matches_0_60"]


def test_dti_exact_fast_and_pixel_mask():
    truth = np.zeros((25, 25), bool)
    truth[7:18, 11] = True
    prediction = np.zeros_like(truth)
    prediction[7:18:2, 12] = True
    known = np.zeros_like(truth)
    known[2, 2] = True
    prediction[2, 2] = True
    valid = np.ones_like(truth)
    a = metric.dti_score_fast(prediction, truth, valid, known)
    b = metric.dti_components_exact(prediction, truth, valid, known)
    assert a["dti"] == pytest.approx(b["dti"], rel=1e-10)
    # Removing an exactly masked prediction has no influence.
    prediction[2, 2] = False
    assert metric.dti_score_fast(prediction, truth, valid, known)["dti"] == a["dti"]
    # A near-known but unmasked pixel remains an ordinary prediction.
    prediction[2, 3] = True
    assert metric.dti_score_fast(prediction, truth, valid, known)["FP_w"] == pytest.approx(a["FP_w"] + 1)


def test_whole_components_hidden_and_buffered():
    fp = np.ones((100, 100), bool)
    labels = np.zeros_like(fp)
    for y, x in [(12, 12), (12, 72), (72, 12), (72, 72)]:
        labels[y:y + 9, x] = True
    labels[45:55, 49] = True  # Crosses a quadrant boundary.
    context = holdout.SegmentHoldout(fp, labels, buffer_px=5)
    assert sum(int(f["truth"].sum()) for f in context.folds) == int(labels.sum())
    for fold in context.folds:
        assert not (fold["train"] & fold["valid"]).any()
        assert not np.isin(context.components[fold["visible"]], fold["hidden_component_ids"]).any()
        assert not (fold["train"] & np.isin(context.components, fold["hidden_component_ids"])).any()


def test_leakage_canary_rejects_truth_and_inverse_truth():
    fp = np.ones((80, 80), bool)
    labels = np.zeros_like(fp)
    for y, x in [(10, 10), (10, 60), (60, 10), (60, 60)]:
        labels[y:y + 5, x] = True
    context = holdout.SegmentHoldout(fp, labels, buffer_px=3)
    result = context.canary({"leaked": labels.astype(float), "inverse": (~labels).astype(float)}, max_per_class=50)
    assert not result["passed"]
    assert result["features"]["leaked"]["leakage_suspected"]
    assert result["features"]["inverse"]["leakage_suspected"]


def test_pooled_dti_is_not_mean_fold_ratios():
    rows = np.array([[10, 1, 0], [1, 10, 100]])
    expected = 11 / (11 + 0.2 * 11 + 0.8 * 100 + metric.EPS)
    assert holdout.pooled_dti(rows) == pytest.approx(expected)
    individual = [holdout.pooled_dti(row[None]) for row in rows]
    assert holdout.pooled_dti(rows) != pytest.approx(np.mean(individual))


def test_dequantization_and_missingness():
    q = np.array([0, 1, 128, 255], dtype=np.uint8)
    values = dequantize(q, 300)
    assert np.isnan(values[0])
    assert values[1:].tolist() == [0, 75, 300]


def test_strike_normal_uses_north_clockwise_convention():
    yy, xx = np.indices((25, 25), dtype=np.float32)
    north_strike = np.zeros(xx.shape, dtype=np.float32)
    east_strike = np.ones(xx.shape, dtype=np.float32) * np.pi / 2
    assert normal_contrast(xx, north_strike)[12, 12] == pytest.approx(6)
    assert normal_contrast(xx, east_strike)[12, 12] == pytest.approx(0, abs=1e-5)
    assert normal_contrast(yy, east_strike)[12, 12] == pytest.approx(6)


def test_deterministic_spacing_and_budget():
    scores = np.ones((30, 30), dtype=np.float32)
    eligible = np.ones_like(scores, bool)
    first = spaced_dots(scores, eligible, 40)
    assert first.sum() == 40
    assert np.array_equal(first, spaced_dots(scores, eligible, 40))
    points = np.argwhere(first)
    assert cKDTree(points).query(points, k=2)[0][:, 1].min() >= 3
    assert not spaced_dots(scores, eligible, 0).any()
    assert not spaced_dots(np.zeros_like(scores), eligible, 20).any()
    with pytest.raises(ValueError):
        spaced_dots(scores, eligible, -1)
    with pytest.raises(ValueError):
        spaced_dots(scores, np.full(scores.shape, np.nan), 1)


def test_literal_overlap_no_calibration_exemption():
    fp = np.ones((30, 30), bool)
    lattice = np.zeros_like(fp)
    lattice[::3, ::3] = True
    candidate = np.zeros_like(fp)
    candidate[1::7, 1::7] = True
    overlap = novelty.dot_overlap(candidate, lattice)["candidate_within_3px_of_reference"]
    assert overlap > 0.7
    assert novelty.is_duplicate(0.0, overlap)
    assert not novelty.is_duplicate(0.9, 0.7)
    assert novelty.is_duplicate(0.900001, 0.1)


def test_scientific_transform_has_no_labels_or_registry_argument():
    parameters = inspect.signature(build_fields).parameters
    assert not any(word in name for name in parameters for word in ("label", "truth", "catalogue", "registry"))
    n = 45
    fp = np.ones((n, n), bool)
    rng = np.random.default_rng(0)
    q = rng.integers(1, 255, (n, n), dtype=np.uint8)
    lidar = {name: np.ones((n, n), np.float32) * 0.2 for name in ("ex", "step", "crest", "toe", "relief", "coherence", "strike", "valid")}
    fields = build_fields(footprint=fp, lidar=lidar, potassium=q, thorium=np.flipud(q), rtp=q.astype(float))
    assert np.isfinite(fields["candidate"]).all()
    assert ((fields["candidate"] >= 0) & (fields["candidate"] <= 1)).all()
    assert len(fields["canary_features"]) >= 15


def test_writer_rejects_bad_ranges_and_protects_template(tmp_path):
    template = tmp_path / "template.tif"
    sample = np.zeros((10, 10), np.float32)
    sample[:2] = np.nan
    with rasterio.open(template, "w", driver="GTiff", width=10, height=10, count=1, dtype="float32",
                       crs="EPSG:32611", transform=from_origin(243350, 4508550, 100, 100), nodata=np.nan) as ds:
        ds.write(sample, 1)
    bad = np.zeros_like(sample)
    bad[5, 5] = 1.00001
    with pytest.raises(ValueError, match="finite and in"):
        submission.write_submission(bad, template, tmp_path / "bad.tif")
    bad[5, 5] = np.nan
    with pytest.raises(ValueError, match="finite and in"):
        submission.write_submission(bad, template, tmp_path / "bad.tif")
    with pytest.raises(ValueError, match="overwrite"):
        submission.write_submission(np.zeros_like(sample), template, template)
    from run_experiment import masked_geotiff
    checks = masked_geotiff(np.zeros_like(sample), template, tmp_path / "good.tif")
    assert checks["all_values_finite_in_01"]
    assert checks["internal_mask_matches_footprint"]
    assert checks["files_are_single_tiff"]
    assert not checks["format_valid"]  # Tiny self-consistency is NOT organizer-grid validity.


def good_evidence():
    return {
        "validator": {"format_valid": True, "all_values_finite_in_01": True, "internal_mask_matches_footprint": True},
        "byte_unique": True, "prediction_unique": True, "canary": {"passed": True},
        "surface_registry": {"passed": True, "registry_unique_rasters": 200},
        "final_registry": {"passed": True, "registry_unique_rasters": 200},
        "complete_registry": True, "paired_comparison": {"ci95_strictly_positive": True, "fold_wins": 4, "min_fold_delta": 0.001},
        "current_best_comparison": {"verified_same_evaluator_and_split": True, "paired_ci95_strictly_positive": True},
        "assigned_lane": True, "authenticated_data_provenance": True, "selector_approved": True, "weekly_quota_verified": True,
    }


def test_ready_requires_all_gates_not_a_format_pass():
    assert not assess_readiness({})["ok_to_submit"]
    good = good_evidence()
    assert assess_readiness(good)["ok_to_submit"]
    for key in good:
        incomplete = dict(good)
        incomplete.pop(key)
        assert not assess_readiness(incomplete)["ok_to_submit"], key
    bad = good_evidence()
    bad["final_registry"]["passed"] = False
    assert assess_readiness(bad)["verdict"] == "negative"
