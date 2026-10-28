"""Regression tests for incomplete and blanket registry references."""
import json
import numpy as np
import pytest
from apartgems import uniqueness as u


def test_empty_registry_never_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(u, 'CACHE_REG', tmp_path)
    (tmp_path / 'registry_manifest.json').write_text(json.dumps({'entries': []}))
    a = np.ones((4, 4), dtype=np.float32)
    with pytest.raises(ValueError, match='empty'):
        u.check_surface_uniqueness(a, a > 0)
    with pytest.raises(ValueError, match='empty'):
        u.check_final_raster_uniqueness(a, a > 0)


def test_blanket_reference_cannot_pass_even_with_low_sample_overlap(tmp_path, monkeypatch):
    monkeypatch.setattr(u, 'CACHE_REG', tmp_path)
    sample = np.arange(100, dtype=np.int64)
    np.save(tmp_path / 'fp_sample_flat.npy', sample)
    ref = np.zeros(100, dtype=np.float32)
    ref[0] = 1
    np.savez(tmp_path / 'ref.npz', pos_flat=np.array([0]), vals_sub=ref)
    entry = {'cache_npz': 'ref.npz', 'decoded_fp_sha256': 'not-candidate',
             'primary_repo': 'example', 'primary_rel': 'lattice.tif',
             'is_blanket_or_continuous_surface': True, 'positive_pixels': 1,
             'halo_3px_footprint_coverage': 1.0}
    (tmp_path / 'registry_manifest.json').write_text(json.dumps({'entries': [entry]}))
    cand = np.zeros((10, 10), dtype=np.float32)
    cand[9, 9] = 1
    result = u.check_final_raster_uniqueness(cand, np.ones_like(cand, dtype=bool))
    assert result['passed'] is False
    assert result['blanket_surfaces_disclosed'] == 1
    assert 'unverified' in result['blanket_gate_status']
