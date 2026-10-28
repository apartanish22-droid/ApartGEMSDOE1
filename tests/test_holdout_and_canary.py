from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy import ndimage as ndi

from gems57.holdout import buffered_component_draw
from apartgems.features import E2_HYDRO_STRESS_FEATURES
from apartgems import model


def test_component_holdout_hides_whole_components_and_buffers_features():
    shape = (120, 120)
    cat = np.zeros(shape, bool)
    for qy in (0, 60):
        for qx in (0, 60):
            for y, x in ((18, 18), (29, 29), (41, 42)):
                cat[qy + y: qy + y + 3, qx + x] = True
    fp = np.ones(shape, bool)
    grid = SimpleNamespace(catalogue=cat, footprint=fp, shape=shape)
    folds, _ = buffered_component_draw(grid, seed=2026, hide_frac=.20, buffer_px=3, boundary_px=5)
    hidden = folds[0]['hidden_all']
    labels, count = ndi.label(cat, structure=np.ones((3, 3)))
    for c in range(1, count + 1):
        part = hidden[labels == c]
        assert part.all() or not part.any()
    assert hidden.any()
    assert all(np.array_equal(f['visible'], folds[0]['visible']) for f in folds)
    assert not (folds[0]['visible'] & hidden).any()
    assert ndi.distance_transform_edt(~folds[0]['visible'])[hidden].min() > 3
    assert np.array_equal(folds[0]['masked_known'], cat & ~hidden)
    assert all(np.array_equal(f['truth'], hidden & f['region']) for f in folds)


def test_canaries_include_composite_crest_and_reject_mixed_visible_folds(tmp_path, monkeypatch):
    shape = (20, 20)
    fp = np.ones(shape, bool)
    rng = np.random.default_rng(4)
    paths = {}
    for name in E2_HYDRO_STRESS_FEATURES:
        path = tmp_path / f'{name}.npy'
        np.save(path, rng.random(shape).astype(np.float32))
        paths[name] = path
    visible = np.zeros(shape, bool)
    visible[1, 1] = True
    truth = np.zeros(shape, bool)
    truth[5, 5] = truth[6, 6] = truth[12, 12] = True
    folds = [dict(region=fp, truth=truth, masked_known=visible, visible=visible)]
    monkeypatch.setattr(model, 'compute_visible_relay_features', lambda v, f: {'relay': np.zeros(shape, np.float32)})
    result = model.run_leakage_canaries(SimpleNamespace(footprint=fp, shape=shape), folds, paths)
    names = {row['feature'] for row in result['features']}
    assert names == set(E2_HYDRO_STRESS_FEATURES) | {'crest_prominence', 'relay'}
    mixed = np.zeros(shape, bool)
    with pytest.raises(ValueError, match='shared buffered visible catalogue'):
        model.run_leakage_canaries(SimpleNamespace(footprint=fp, shape=shape), folds + [dict(folds[0], visible=mixed)], paths)
