import hashlib
import json
import numpy as np
import pytest
from apartgems import uniqueness as u


def registry(tmp_path, monkeypatch, reference):
    monkeypatch.setattr(u, 'CACHE_REG', tmp_path)
    fp = np.ones(reference.shape, dtype=bool)
    values = reference.astype('float32')[fp]
    digest = hashlib.sha256(values.tobytes()).hexdigest()
    pos = np.flatnonzero(reference.ravel() > 0).astype('int32')
    np.savez_compressed(tmp_path / 'r.npz', vals_fp=values, pos_flat=pos)
    (tmp_path / 'registry_manifest.json').write_text(json.dumps({'entries': [{
        'primary_repo':'test', 'primary_rel':'lattice.tif', 'positive_pixels':len(pos),
        'decoded_fp_sha256':digest, 'cache_npz':'r.npz', 'full_support_and_ranks':True,
        'is_blanket_or_continuous_surface': True}]}))
    return fp


def test_dense_lattice_is_not_exempt(tmp_path, monkeypatch):
    ref = np.zeros((20, 20), dtype='float32')
    ref[::5, ::5] = 1
    fp = registry(tmp_path, monkeypatch, ref)
    candidate = np.zeros_like(ref)
    candidate[1::5, 1::5] = 1
    result = u.check_final_raster_uniqueness(candidate, fp)
    assert result['max_3px_overlap_vs_competing_detectors'] == 1
    assert not result['passed']


def test_old_topk_or_sampled_cache_fails_closed(tmp_path, monkeypatch):
    ref = np.eye(8, dtype='float32')
    fp = registry(tmp_path, monkeypatch, ref)
    p = tmp_path / 'registry_manifest.json'
    doc = json.loads(p.read_text()); doc['entries'][0]['full_support_and_ranks'] = False
    p.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match='incomplete or sampled'):
        u.check_surface_uniqueness(ref, fp)


def test_tampered_support_and_empty_registry_fail_closed(tmp_path, monkeypatch):
    ref = np.eye(8, dtype='float32')
    fp = registry(tmp_path, monkeypatch, ref)
    np.savez_compressed(tmp_path / 'r.npz', vals_fp=ref[fp], pos_flat=np.arange(8))
    with pytest.raises(ValueError, match='support'):
        u.check_final_raster_uniqueness(ref, fp)
    (tmp_path / 'registry_manifest.json').write_text('{"entries": []}')
    with pytest.raises(ValueError, match='empty registry'):
        u.check_surface_uniqueness(ref, fp)


def test_nonfinite_and_constant_candidate_fail_closed(tmp_path, monkeypatch):
    fp = registry(tmp_path, monkeypatch, np.eye(8, dtype='float32'))
    candidate = np.ones((8, 8), dtype='float32')
    with pytest.raises(ValueError, match='constant'):
        u.check_surface_uniqueness(candidate, fp)
    candidate[0,0] = np.nan
    with pytest.raises(ValueError, match='non-finite'):
        u.check_surface_uniqueness(candidate, fp)


def test_surface_gate_runs_before_placement(monkeypatch):
    from types import SimpleNamespace
    from apartgems import model
    grid = SimpleNamespace(footprint=np.ones((5, 5), bool), catalogue=np.zeros((5, 5), bool), shape=(5, 5))
    winner = SimpleNamespace(exp_id='E1', blind_models=[object()], meta_models=None)
    monkeypatch.setattr(model, '_predict_blind_hgb_on_mask', lambda *a: np.ones((5, 5), dtype='float32'))
    def never_place(*args, **kwargs):
        pytest.fail('placement ran before surface gate rejected the candidate')
    monkeypatch.setattr(model, 'allocate_udth_dots', never_place)
    def reject(surface, footprint):
        raise ValueError('surface duplicate')
    with pytest.raises(ValueError, match='surface duplicate'):
        model.build_final_live_submission_arrays(grid, winner, {}, np.ones((5, 5)), before_placement=reject)


def test_three_pixel_halo_works_for_small_grids():
    p = np.array([[True, False], [False, False]])
    assert u.fast_near_3px(p).all()
