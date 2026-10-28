"""Mirror integrity and source-bound cache tests; no remote access."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from scripts import prepare_data
from gems57 import grid


def write_raster(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if data.ndim == 2:
        data = data[None, ...]
    with rasterio.open(path, 'w', driver='GTiff', height=data.shape[1], width=data.shape[2],
                       count=data.shape[0], dtype='float32', crs='EPSG:32611',
                       transform=from_origin(0, 400, 100, 100)) as dst:
        dst.write(data.astype(np.float32))


def test_all_mirror_sources_have_fixed_sha_and_unpinned_fetch_is_rejected(tmp_path):
    old = json.loads((Path(__file__).resolve().parents[1] / 'evidence/data_preparation.json').read_text())
    digests = {x['name']: x['sha256'] for x in old['external_files']}
    for entry in prepare_data.EXTERNAL_PINS:
        assert len(entry['sha256']) == 64
        assert entry['sha256'] == digests[entry['name']]
    with pytest.raises(ValueError, match='unpinned'):
        prepare_data.fetch_raw('any/repo', 'file', 'HEAD', tmp_path / 'file')


def test_missing_feature_input_fails_without_a_success_receipt(tmp_path, monkeypatch):
    (tmp_path / 'data/bridge').mkdir(parents=True)
    (tmp_path / 'data/official').mkdir(parents=True)
    # Reduce the fixture core to one genuinely hash-checked byte string.
    src = tmp_path / 'data/bridge/test.tif'; src.write_bytes(b'known')
    monkeypatch.setattr(prepare_data, 'ROOT', tmp_path)
    monkeypatch.setattr(prepare_data, 'CORE_PINS', {'data/bridge/test.tif': ('repo', 'ref', 'path', hashlib.sha256(b'known').hexdigest())})
    monkeypatch.setattr(sys, 'argv', ['prepare_data', '--no-cache-bands'])
    with pytest.raises(FileNotFoundError, match='training feature cache missing'):
        prepare_data.main()
    assert not (tmp_path / 'evidence/data_preparation.json').exists()


def test_band_cache_requires_source_and_content_hash_match(tmp_path):
    feature = tmp_path / 'data/official/training_features.tif'; sample = tmp_path / 'data/official/sample_submission.tif'
    a = np.arange(32, dtype=np.float32).reshape(2, 4, 4)
    write_raster(feature, a); write_raster(sample, np.ones((4, 4), np.float32))
    first = prepare_data.cache_bands(tmp_path)
    cache = tmp_path / '.cache/features/band-01.npy'
    assert np.array_equal(np.load(cache), a[0])
    provenance = json.loads((tmp_path / '.cache/features/cache_provenance.json').read_text())
    assert provenance['source_sha256'] == prepare_data.sha256(feature)
    # Same shape/dtype alone must not cause a corrupted cache to be trusted.
    np.save(cache, np.full((4, 4), 777, np.float32))
    second = prepare_data.cache_bands(tmp_path)
    assert np.array_equal(np.load(cache), a[0])
    assert first['bands'][0]['sha256'] == second['bands'][0]['sha256']
    a[0, 0, 0] = 42
    write_raster(feature, a)
    third = prepare_data.cache_bands(tmp_path)
    assert np.array_equal(np.load(cache), a[0])
    assert third['source_sha256'] != first['source_sha256']
    assert third['bands'][0]['sha256'] != first['bands'][0]['sha256']


def test_grid_rejects_tampered_owner_mirror(tmp_path):
    (tmp_path / 'existing_faults.tif').write_bytes(b'tampered')
    (tmp_path / 'sample_submission.tif').write_bytes(b'tampered')
    with pytest.raises(ValueError, match='pinned owner mirror'):
        grid.load_grid(tmp_path)


def test_symlinks_never_overwrite_existing_user_data(tmp_path):
    p = tmp_path / 'existing'; p.write_text('keep me')
    with pytest.raises(FileExistsError, match='refusing to replace'):
        prepare_data.ensure_symlink(p, 'target')
    assert p.read_text() == 'keep me'
