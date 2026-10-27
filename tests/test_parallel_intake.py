"""Read-only checks of concurrent artifacts; no model generation or evaluation."""
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

from gems.footprint import load_footprint

ROOT = Path(__file__).resolve().parents[1]


def record():
    return json.loads((ROOT / "evidence/parallel-intake.json").read_text())


def test_other_lane_promotion_is_preserved_but_not_authorized():
    r = record()
    original = ROOT / r["original_card_path"]
    assert hashlib.sha256(original.read_bytes()).hexdigest() == r["original_card_sha256"]
    assert json.loads(original.read_text())["submission"]["verdict"] == "promote"
    assert r["original_promotion"] == "promote" and r["verdict"] == "negative"
    assert not r["submission_authorized"] and not r["controls_exempted"]
    assert r["new_experiments"] == r["slots_selected_or_uploaded"] == 0
    assert not r["holdout_recomputed"] and r["stopped_after_first_witness"]


def test_exact_h2_bytes_have_the_measured_count_not_the_stale_card_count():
    r = record()
    path = ROOT / r["candidate"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == r["raster_sha256"]
    with rasterio.open(path) as src:
        values = src.read(1)
    assert np.isfinite(values).all() and ((values >= 0) & (values <= 1)).all()
    assert int(np.count_nonzero(values[load_footprint()] > 0)) == r["actual_positive_pixels"] == 44090
    assert r["original_validator_positive_pixels"] == 40308
    assert not r["original_validator_count_matches"]


def test_one_witness_proves_stop_without_further_rank_checks_or_holdout():
    r = record()
    lower = (44090 - 6649) / 44090
    assert r["independent_geometry_lower_bound"] == lower > 0.7
    assert r["directional_overlap"]["candidate_within_3px_of_reference"] >= lower
    assert r["directional_overlap"]["candidate_dots"] == 44090
    assert r["duplicate_stop"] and r["rank_correlation"] is None
    assert r["format"]["checks"]["finite_inside"] and r["format"]["checks"]["range_inside"]
    assert not r["format"]["format_pass"] and not r["format"]["checks"]["exterior_null"]
    assert not r["organizer_acceptance_tested"]


def test_all_active_card_aliases_are_the_same_negative_ap1_record():
    canonical = (ROOT / "evidence/run-card.json").read_bytes()
    for alias in ("run_card.json", "run-card.json", "docs/run_card.json", "docs/data/run-card.json"):
        assert (ROOT / alias).read_bytes() == canonical
    assert json.loads(canonical)["verdict"] == "negative"
