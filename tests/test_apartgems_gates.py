"""Scientific and release-gate regressions. No network or model training."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin
from scipy.ndimage import label

from gems57 import load_grid
from gems57.evaluate_holdout import VERSION, evaluate
from gems57.grid import Grid
from gems57.holdout import buffered_component_draw, visible_score_mask
from gems57.metric import dti_bruteforce, dti_exact
from gems57.uniqueness import compare_array_to_registry, is_blanket_or_lattice, summarize_registry_rows
from gems57.validate import assert_submittable, validate
from apartgems import model

ROOT = Path(__file__).resolve().parents[1]


def test_soft_dti_matches_literal_bruteforce_and_rejects_bad_masks():
    rng = np.random.default_rng(42)
    pred = (rng.random((30, 30)) < .04) * rng.random((30, 30))
    truth = rng.random((30, 30)) < .03
    valid = np.ones((30, 30), dtype=bool)
    known = np.zeros((30, 30), dtype=bool)
    known[10:15, 20] = True
    fast = dti_exact(pred, truth, valid=valid, known=known)
    literal = dti_bruteforce(pred * ~known, truth & ~known)
    for key in ('dti', 'tp', 'fp', 'fn'):
        assert np.isclose(fast[key], literal[key], atol=1e-9)
    with pytest.raises(ValueError, match='grid shape'):
        dti_exact(pred, truth, valid=valid, known=np.zeros((1, 30)))


def test_visible_only_mask_penalizes_removed_but_not_withheld_pixel():
    fp = np.ones((12, 12), bool)
    truth = np.zeros_like(fp); truth[2, 2] = True
    visible = np.zeros_like(fp); visible[9, 9] = True
    # (7,2) represents a catalogue pixel removed only from visible context.
    pred = np.zeros(fp.shape, np.float32)
    pred[2, 2] = pred[7, 2] = pred[9, 9] = 1
    fold = {'region': fp, 'truth': truth, 'visible': visible, 'masked_known': visible.copy()}
    result, terms = evaluate(pred, fold, fp, block_side=4)
    assert VERSION == 'gems57-pooled-hide-v3'
    assert result['n_truth'] == 1 and result['n_emitted'] == 2
    assert result['tp'] == pytest.approx(1.0)
    assert result['fp'] == pytest.approx(1.0)
    assert result['dti'] == pytest.approx(1 / 1.2)
    assert terms.sum(axis=0).tolist() == pytest.approx([1, 1, 0, 1])
    old_mask = visible.copy(); old_mask[7, 2] = True
    with pytest.raises(ValueError, match='pixel-exactly'):
        evaluate(pred, {**fold, 'masked_known': old_mask}, fp)
    with pytest.raises(ValueError, match='visible catalogue'):
        visible_score_mask({'masked_known': visible})


def test_buffer_draw_hides_whole_components_and_masks_only_context():
    shape = (96, 96)
    fp = np.ones(shape, dtype=bool)
    cat = np.zeros(shape, dtype=bool)
    for y, x in ((10, 10), (10, 58), (58, 10), (58, 58)):
        cat[y:y + 4, x] = True
        cat[y:y + 4, x + 3] = True  # separate component within the 3px feature buffer
        cat[y + 13:y + 17, x + 13] = True
    grid = Grid(fp, cat, CRS.from_epsg(32611), from_origin(0, 9600, 100, 100), *shape)
    folds, _ = buffered_component_draw(grid, seed=2026, hide_frac=.2, buffer_px=3, boundary_px=4)
    hidden = folds[0]['hidden_all']
    components, n = label(cat, np.ones((3, 3), bool))
    for i in range(1, n + 1):
        part = hidden[components == i]
        assert part.all() or not part.any(), 'must never clip a selected component'
    assert sum(f['receipt']['withheld_positive_pixels'] for f in folds) == int(hidden.sum())
    assert (cat & ~hidden & ~folds[0]['visible']).any()  # actual context-only removal
    for f in folds:
        assert np.array_equal(f['masked_known'], f['visible'])
        assert not (hidden & f['visible']).any()
        assert f['receipt']['nearest_visible_to_truth_px'] > 3
        assert f['receipt']['split_version'].endswith('-v3')


def raster(path: Path, a: np.ndarray, transform=None):
    transform = transform or from_origin(0, 10000, 100, 100)
    with rasterio.open(path, 'w', driver='GTiff', height=a.shape[0], width=a.shape[1],
                       count=1, dtype='float32', crs='EPSG:32611', transform=transform) as dst:
        dst.write(a.astype(np.float32), 1)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index(path, digest, *, complete=True):
    return {'complete_accessible_scan': complete, 'errors': [], 'rasters': [
        {'repo_first': 'test', 'sources': ['test/file'], 'cache_file': str(path), 'sha256': digest}]}


def test_dense_or_lattice_witness_cannot_be_exempted(tmp_path):
    fp = np.ones((100, 100), bool)
    lattice = np.zeros(fp.shape, np.float32); lattice[::5, ::5] = 1
    mine = np.zeros_like(lattice); mine[7:90:8, 8:90:8] = 1
    path = tmp_path / 'dense.tif'; digest = raster(path, lattice)
    expected = (fp.shape, CRS.from_epsg(32611), from_origin(0, 10000, 100, 100))
    assert is_blanket_or_lattice(lattice, fp)['is_blanket']
    result = compare_array_to_registry(mine, index(path, digest), fp, expected_grid=expected)
    assert result['worst_dot_overlap'] > .70
    assert result['duplicate_count'] == 1 and result['stop_required']
    assert result['unique'] is False and result['verdict'] == 'negative'
    assert result['rows'][0]['duplicate_by_overlap']


def test_incomplete_unpinned_invalid_and_wrong_grid_fail_closed(tmp_path):
    fp = np.ones((40, 40), bool)
    mine = np.zeros(fp.shape, np.float32); mine[30, 30] = 1
    prior = np.zeros_like(mine); prior[2, 2] = 1
    p = tmp_path / 'prior.tif'; digest = raster(p, prior)
    expected = (fp.shape, CRS.from_epsg(32611), from_origin(0, 10000, 100, 100))
    good = compare_array_to_registry(mine, index(p, digest), fp, expected_grid=expected, phase='surface')
    assert good['unique'] and good['phase'] == 'surface'
    assert not compare_array_to_registry(mine, index(p, digest, complete=False), fp, expected_grid=expected)['unique']
    assert not compare_array_to_registry(mine, index(p, None), fp, expected_grid=expected)['unique']
    assert not compare_array_to_registry(mine, [], fp, expected_grid=expected)['unique']
    with pytest.raises(ValueError, match='explicit'):
        compare_array_to_registry(mine, index(p, digest), fp)
    shifted = (fp.shape, CRS.from_epsg(32611), from_origin(1, 10000, 100, 100))
    assert not compare_array_to_registry(mine, index(p, digest), fp, expected_grid=shifted)['unique']
    prior[10, 10] = np.nan; digest = raster(p, prior)
    bad = compare_array_to_registry(mine, index(p, digest), fp, expected_grid=expected)
    assert not bad['unique'] and 'non-finite' in bad['rows'][0]['error']
    prior[10, 10] = 1.5; digest = raster(p, prior)
    bad = compare_array_to_registry(mine, index(p, digest), fp, expected_grid=expected)
    assert not bad['unique'] and 'out-of-range' in bad['rows'][0]['error']
    digest = raster(p, np.zeros_like(prior))
    undefined = compare_array_to_registry(mine, index(p, digest), fp, expected_grid=expected)
    assert not undefined['unique'] and undefined['missing_or_invalid'] == 1
    assert undefined['rows'][0]['rank_comparison_defined'] is False


def test_summary_rederives_thresholds_and_empty_registry_never_passes():
    meta = {'my_dots': 10, 'candidate_rank_variation': True, 'candidate_decoded_sha256': 'a' * 64}
    row = {'submission': 'prior', 'sha256': 'b' * 64,
           'my_dots_within_3px_of_theirs': .70, 'spearman_full_footprint': .90,
           'jaccard_dot_sets': .2, 'duplicate_by_overlap': False, 'duplicate_by_rho': False}
    def summarize(rows, expected):
        return summarize_registry_rows(rows, registry_rasters_expected=expected, complete_accessible_scan=True,
                                       source_errors=[], candidate_meta=meta, scope='unit test')
    assert summarize([row], 1)['unique']  # strict > rule, exactly on thresholds
    assert not summarize([], 0)['unique']
    assert not summarize([{**row, 'my_dots_within_3px_of_theirs': .700001}], 1)['unique']
    assert not summarize([{**row, 'spearman_full_footprint': .900001}], 1)['unique']
    assert not summarize([{**row, 'my_dots_within_3px_of_theirs': float('nan')}], 1)['unique']
    assert not summarize([{**row, 'sha256': None}], 1)['unique']


def test_placement_requires_exact_complete_surface_gates_then_respects_lane_stop(monkeypatch):
    shape = (8, 8)
    grid = SimpleNamespace(shape=shape, footprint=np.ones(shape, bool), catalogue=np.zeros(shape, bool))
    winner = SimpleNamespace(exp_id='E1')
    main = np.zeros(shape, np.float32); main[2, 2] = .5
    vent = np.zeros(shape, np.float32); vent[3, 3] = .7
    def gate(a):
        return {'phase': 'surface', 'unique': True, 'complete_accessible_scan': True,
                'candidate_decoded_sha256': hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()}
    calls = []
    monkeypatch.setattr(model, 'submodular_celf_allocate_300m', lambda *a, **k: calls.append(1))
    with pytest.raises(ValueError, match='pre-placement'):
        model.place_final_live_submission(grid, winner, main, vent, surface_gate={}, vent_surface_gate=gate(vent))
    with pytest.raises(ValueError, match='pre-placement'):
        model.place_final_live_submission(grid, winner, main + .01, vent, surface_gate=gate(main), vent_surface_gate=gate(vent))
    with pytest.raises(ValueError, match='pre-placement'):
        model.place_final_live_submission(grid, winner, main, vent, surface_gate=gate(main),
                                          vent_surface_gate={**gate(vent), 'complete_accessible_scan': False})
    with pytest.raises(RuntimeError, match='mandatory duplicate stop'):
        model.place_final_live_submission(grid, winner, main, vent, surface_gate=gate(main), vent_surface_gate=gate(vent))
    assert not calls
    with pytest.raises(RuntimeError, match='mandatory duplicate stop'):
        model.run_three_loqo_experiments(None, [], {})
    with pytest.raises(RuntimeError, match='mandatory duplicate stop'):
        model.build_final_live_submission_surfaces(None, winner, {})


def test_current_negative_card_and_historical_format_are_not_a_promotion():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    review = json.loads((ROOT / 'evidence/run_card_20261030.json').read_text())
    witness = json.loads((ROOT / 'evidence/literal_witness_audit.json').read_text())
    assert card['verdict'] == 'negative' and witness['stop_required'] is True
    assert review['verdict'] == 'negative' and review['branch'] == 'arena/4cab7700-apartgemsdoe1'
    assert review['session_kind'].startswith('repository_review_only')
    assert review['holdout_dti']['label'] == 'HOLDOUT-DTI'
    assert review['holdout_dti']['evaluator_version'] == 'gems57-pooled-hide-v3'
    assert review['holdout_dti']['withheld_positive_pixels'] == 11360
    assert review['holdout_dti']['dti'] is None and review['holdout_dti']['ci95'] is None
    assert review['raster_sha256'] == witness['candidate_sha256']
    assert review['correlation_overlap_vs_registry']['final_dots']['forward_overlap_3px'] > .70
    assert review['validator_output']['all_local_format_checks_passed'] is True
    assert review['validator_output']['full_preflight_ok_to_submit'] is False
    assert len(review['submission_note']) == review['submission_note_chars'] <= 140
    assert card['holdout_dti']['dti'] is None and card['holdout_dti']['ci95'] is None
    hist = card['holdout_dti']['historical_noncomparable']
    assert hist['evaluator_version'].endswith('-v2') and len(hist['ci95']) == 2
    assert card['submission_note_chars'] == len(card['submission_note']) <= 140
    assert witness['final_dot_gate']['candidate_dots_within_3px'] == 37533
    assert witness['final_dot_gate']['candidate_dots'] == 37654
    assert witness['final_dot_gate']['forward_overlap_3px'] > .70
    assert witness['budget_feasibility']['uncovered_allowed_pixels'] == 6514
    assert witness['budget_feasibility']['max_dots_for_possible_70pct_pass'] == 21713
    assert not witness['surface_gate']['tested'] and not witness['complete_registry_checked']
    grid = load_grid()
    tif = ROOT / card['validator_output']['file']
    report = validate(tif, footprint=grid.footprint, catalogue=grid.catalogue)
    assert_submittable(report)
    assert report['sha256'] == card['raster_sha256']
    assert report['n_nan'] == report['n_infinite'] == 0
    assert report['min'] == 0 and report['max'] == 1
    assert not json.loads((ROOT / 'evidence/uniqueness_gate.json').read_text())['overall_uniqueness_passed']


def test_nine_site_audit_and_stopped_cli():
    audit = json.loads((ROOT / 'evidence/focus9_reaudit.json').read_text())
    assert audit['fetched_and_checked'] == 9 and not audit['errors']
    assert {r['site'] for r in audit['sites']} == {f'GEMSDOE{n}' for n in (24, 25, 27, 28, 30, 31, 32, 33, 36)}
    assert all(r['unique_among_focus9'] is False for r in audit['sites'])
    assert all('USER-REPORTED' in r['score_evidence'] and 'not ORGANIZER-CONFIRMED' in r['score_evidence'] for r in audit['sites'])
    assert audit['geometry_proof']['xor_differing_pixels'] == 0
    assert audit['geometry_proof']['gems25_vs_gems30_support_xor'] == 0
    p = subprocess.run([sys.executable, str(ROOT / 'scripts/run_apartgems_pipeline.py')], capture_output=True, text=True)
    assert p.returncode != 0 and 'STOP' in p.stderr and 'No model experiment' in p.stderr
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    tif = ROOT / card['validator_output']['file']
    validator = [sys.executable, str(ROOT / 'scripts/validate_submission.py'), str(tif)]
    ordinary = subprocess.run(validator, capture_output=True, text=True)
    result = json.loads(ordinary.stdout)
    assert ordinary.returncode != 0 and result['ok_to_submit'] is False
    assert result['format']['all_checks_passed'] and result['selector_approval'] is False
    format_only = subprocess.run([*validator, '--format-only'], capture_output=True, text=True)
    assert format_only.returncode == 0 and json.loads(format_only.stdout)['ok_to_submit'] is False
