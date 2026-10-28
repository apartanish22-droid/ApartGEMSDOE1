"""Additional edge and ordering checks for the shared gate and model."""
import numpy as np
import pytest
from gems57.uniqueness import dot_overlap


def test_three_pixel_halo_works_for_small_grids():
    candidate = np.ones((2, 2), dtype=np.float32)
    registry = np.array([[1, 0], [0, 0]], dtype=np.float32)
    assert dot_overlap(candidate, registry) == 1.0


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
    with pytest.raises(ValueError, match='did not return a passing'):
        model.build_final_live_submission_arrays(grid, winner, {}, np.ones((5, 5)), before_placement=lambda *_: {'unique': False})
    with pytest.raises(ValueError, match='pre-placement uniqueness gate is required'):
        model.build_final_live_submission_arrays(grid, winner, {}, np.ones((5, 5)))
