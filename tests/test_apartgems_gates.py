"""Regression tests for the negative decision and official-formula arithmetic."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from gems57 import load_grid
from gems57.metric import dti_bruteforce, dti_exact, marginal_accept, dti_from_components
from gems57.validate import assert_submittable, validate

ROOT = Path(__file__).resolve().parents[1]


def test_dti_exact_matches_bruteforce_for_soft_predictions_and_known_mask():
    rng = np.random.default_rng(42)
    pred = (rng.random((25, 28)) < 0.09) * rng.random((25, 28))
    truth = rng.random((25, 28)) < 0.04
    valid = rng.random((25, 28)) > 0.1
    known = rng.random((25, 28)) < 0.03
    active = valid & ~known
    fast = dti_exact(pred, truth, valid=valid, known=known)
    brute = dti_bruteforce(pred * active, truth & active)
    for name in ('tp', 'fp', 'fn', 'dti'):
        assert fast[name] == pytest.approx(brute[name], abs=1e-9)
    assert fast['n_truth'] == int((truth & active).sum())


def test_invalid_scored_probability_raises_instead_of_being_repaired():
    pred = np.zeros((4, 4))
    pred[0, 0] = 1.00000001
    with pytest.raises(ValueError, match='finite and in'):
        dti_exact(pred, np.zeros_like(pred, dtype=bool))


def test_marginal_accept_matches_two_full_component_scores():
    # A new dot can improve credit on more than one truth pixel.
    T, M, n, K, dT, k = 2.0, 1.0, 3, 8, 1.4, 0.7
    old = dti_from_components(T, n - M, K - T)
    new = dti_from_components(T + dT, n + 1 - M - k, K - T - dT)
    assert marginal_accept(dT, k, T, M, n, K) == (new > old)


def test_reproduced_bounded_audit_is_negative():
    audit = json.loads((ROOT / 'evidence/review_20261028.json').read_text())
    card = json.loads((ROOT / 'evidence/run_card_20261028.json').read_text())
    assert audit['verdict'] == card['verdict'] == 'negative'
    assert audit['new_experiments'] == audit['submission_slots_used'] == 0
    assert not audit['new_raster_generated'] and card['raster_sha256'] is None
    assert card['holdout_dti']['value'] is None and card['holdout_dti']['ci95'] is None
    assert card['submission_name'] is None and len(card['submission_note']) <= 140
    assert audit['previous_apart_submission']['forward_overlap_3px_with_lattice'] == pytest.approx(0.9894805194805195)
    assert audit['previous_apart_submission']['forward_overlap_3px_with_continuous'] == 1.0
    assert audit['continuous_witness']['uncovered_allowed_pixels'] == 0
    assert audit['lattice_witness']['uncovered_allowed_pixels'] == 6514
    proof = audit['forensic_32']
    assert (proof['parent_25_dots'], proof['gems32_dots'], proof['removed_parent_dots']) == (44090, 37654, 6436)
    assert proof['gems25_vs_gems30_differing_support_pixels'] == 0
    assert proof['gems32_vs_gems25_excluding_le_2px_catalogue_differing_support_pixels'] == 0
    assert len(audit['focus_sites']) == 9
    for row in audit['focus_sites']:
        assert not row['unique_vs_other_focus9_under_literal_rule']
        assert row['forward_3px_overlap_worst_focus9'] > 0.70
        assert row['leaderboard_estimate'] is None
        assert row['score_evidence_class'] == 'OWNER-REPORTED / UNVERIFIED'
    for candidate, peers in audit['directional_focus9_3px_overlap'].items():
        for peer, overlap in peers.items():
            if peer != candidate:
                assert overlap > 0.70


def test_old_format_pass_is_not_a_promotion():
    current = json.loads((ROOT / 'evidence/run_card_20261028.json').read_text())
    old = json.loads((ROOT / 'evidence/run_card.json').read_text())
    canary = json.loads((ROOT / 'evidence/leakage_canary.json').read_text())
    gate = json.loads((ROOT / 'evidence/uniqueness_gate.json').read_text())
    assert old['verdict'] == 'negative' and old['historical_original_verdict'] == 'promote'
    assert not old['registry_uniqueness']['passed'] and not gate['overall_uniqueness_passed']
    assert not canary['complete_for_model'] and canary['omitted_feature'] == 'crest_prominence'
    grid = load_grid()
    tif = ROOT / old['validator_output']['file']
    receipt = validate(tif, footprint=grid.footprint, catalogue=grid.catalogue)
    assert_submittable(receipt)
    assert receipt['sha256'] == current['validator_output']['previous_raster_sha256']
    assert receipt['n_nan'] == receipt['n_infinite'] == 0
    assert (receipt['min'], receipt['max']) == (0.0, 1.0)
    assert receipt['on_catalogue_positive_pixels'] == 0


def test_grid_rejects_unpinned_files(tmp_path):
    (tmp_path / 'existing_faults.tif').write_bytes(b'not the pinned data')
    (tmp_path / 'sample_submission.tif').write_bytes(b'not the pinned sample')
    with pytest.raises(ValueError, match='SHA-256 mismatch'):
        load_grid(tmp_path)
