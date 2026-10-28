from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from scripts import prepare_data


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, 'w', driver='GTiff', height=data.shape[0], width=data.shape[1],
                       count=1, dtype='float32', crs='EPSG:32611',
                       transform=from_origin(200_000, 4_000_000, 100, 100)) as ds:
        ds.write(data.astype(np.float32), 1)
        ds.set_band_description(1, 'fixture')


def test_cache_is_hash_checked_and_corruption_rebuilt(tmp_path, monkeypatch):
    source = tmp_path / 'data/official/training_features.tif'
    sample = tmp_path / 'data/official/sample_submission.tif'
    a = np.arange(100, dtype=np.float32).reshape(10, 10)
    a[1, 1] = -3.4028235e38
    write(source, a)
    write(sample, np.zeros((10, 10), np.float32))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(prepare_data, 'TRAINING_FEATURES_SHA256', digest)
    first = prepare_data.cache_bands(tmp_path)
    cached = tmp_path / '.cache/features/band-01.npy'
    original = np.load(cached).copy()
    assert np.isnan(original[1, 1]) and original[2, 2] == 22
    assert first['shape'] == [10, 10] and first['bands'][0]['sentinel_or_missing_in_footprint'] == 1
    corrupted = original.copy()
    corrupted[2, 2] = 12345
    np.save(cached, corrupted)
    second = prepare_data.cache_bands(tmp_path)
    np.testing.assert_array_equal(np.load(cached), original)
    assert second['bands'][0]['sha256'] == first['bands'][0]['sha256']
    monkeypatch.setattr(prepare_data, 'TRAINING_FEATURES_SHA256', '0' * 64)
    with pytest.raises(ValueError, match='pinned mirror'):
        prepare_data.cache_bands(tmp_path)


def test_symlink_helper_never_replaces_existing_user_data(tmp_path):
    link = tmp_path / 'data.tif'
    link.write_bytes(b'user file')
    with pytest.raises(FileExistsError):
        prepare_data.ensure_symlink(link, 'target.tif')
    assert link.read_bytes() == b'user file'
    link.unlink()
    prepare_data.ensure_symlink(link, 'target.tif')
    prepare_data.ensure_symlink(link, 'target.tif')
    with pytest.raises(FileExistsError):
        prepare_data.ensure_symlink(link, 'different.tif')
    assert link.is_symlink()
