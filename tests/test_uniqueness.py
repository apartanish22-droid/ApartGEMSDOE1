"""Synthetic, no-network regressions for literal and fail-closed registry gates."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from gems57.uniqueness import compare_array_to_registry, saturation_certificate, summarize_registry_rows

SHAPE = (20, 20)
CRS = rasterio.crs.CRS.from_epsg(32611)
TRANSFORM = from_origin(200_000, 4_000_000, 100, 100)
EXPECTED = (SHAPE, CRS, TRANSFORM)


def write(path: Path, arr, *, crs=CRS, transform=TRANSFORM):
    arr = np.asarray(arr)
    with rasterio.open(path, 'w', driver='GTiff', height=arr.shape[0], width=arr.shape[1],
                       count=1, dtype=arr.dtype, crs=crs, transform=transform) as ds:
        ds.write(arr, 1)
    return path


def inventory(path, *, sha=True, expected=1, scope='pinned test fixture', complete=True):
    digest = hashlib.sha256(path.read_bytes()).hexdigest() if sha else None
    return {'rasters': [{'repo_first': 'test/repo', 'sources': ['fixture'],
                         'cache_file': str(path), 'sha256': digest}],
            'registry_rasters_expected': expected, 'inventory_scope': scope,
            'complete_accessible_scan': complete, 'errors': []}


def candidate():
    a = np.zeros(SHAPE, dtype=np.float32)
    a[2, 2], a[17, 17] = .25, .8
    return a


def distant():
    a = np.zeros(SHAPE, dtype=np.float32)
    a[2, 17] = 1
    return a


def run(a, idx, fp=None):
    return compare_array_to_registry(a, idx, np.ones(SHAPE, bool) if fp is None else fp, expected_grid=EXPECTED)


def test_complete_scoped_fixture_can_clear_only_that_inventory(tmp_path):
    path = write(tmp_path / 'distant.tif', distant())
    result = run(candidate(), inventory(path))
    assert result['complete_accessible_scan'] and result['unique']
    assert result['worst_dot_overlap'] == 0.0
    assert result['verdict'] == 'promote-to-selector-only'
    assert 'not a complete organizer registry' in result['scope']


def test_exact_overlap_boundary_uses_strict_greater_than(tmp_path):
    points = [(y, x) for y in (3, 13) for x in (1, 5, 9, 13, 17)]
    mine = np.zeros(SHAPE, np.float32)
    for p in points:
        mine[p] = 1
    ref = np.zeros(SHAPE, np.float32)
    for p in points[:7]:
        ref[p] = 1
    seven = write(tmp_path / 'seven.tif', ref)
    r7 = run(mine, inventory(seven))
    assert r7['worst_dot_overlap'] == .7 and r7['unique']
    ref[points[7]] = 1
    eight = write(tmp_path / 'eight.tif', ref)
    r8 = run(mine, inventory(eight))
    assert r8['worst_dot_overlap'] == .8 and not r8['unique']


def test_dense_prior_cannot_be_exempted_from_literal_rule(tmp_path):
    prior = np.full(SHAPE, .2, np.float32)
    path = write(tmp_path / 'continuous.tif', prior)
    result = run(candidate(), inventory(path))
    witness = saturation_certificate(path, np.ones(SHAPE, bool), expected_grid=EXPECTED)
    assert witness['universal_overlap_blocker'] and witness['uncovered_allowed_pixels'] == 0
    assert result['worst_dot_overlap'] == 1.0
    assert result['rows'][0]['duplicate_by_overlap']
    assert not result['unique'] and result['stop_required']


@pytest.mark.parametrize('mutate', [
    lambda idx: idx.update(registry_rasters_expected=2),
    lambda idx: idx.pop('registry_rasters_expected'),
    lambda idx: idx.pop('inventory_scope'),
    lambda idx: idx.update(complete_accessible_scan=False),
    lambda idx: idx.update(errors=['network discovery failed']),
])
def test_incomplete_inventories_never_clear(tmp_path, mutate):
    path = write(tmp_path / 'distant.tif', distant())
    idx = inventory(path)
    mutate(idx)
    result = run(candidate(), idx)
    assert not result['unique'] and not result['complete_accessible_scan'] and result['stop_required']


def test_legacy_list_empty_inventory_and_unpinned_entries_never_clear(tmp_path):
    path = write(tmp_path / 'distant.tif', distant())
    idx = inventory(path, sha=False)
    result = run(candidate(), idx)
    assert not result['unique'] and 'SHA256 pin' in result['rows'][0]['error']
    idx['rasters'][0]['sha256'] = 'f' * 64
    assert 'pin mismatch' in run(candidate(), idx)['rows'][0]['error']
    legacy = [dict(file=str(path), repo='test', submission='legacy', sha256=hashlib.sha256(path.read_bytes()).hexdigest())]
    assert not run(candidate(), legacy)['unique']
    empty = summarize_registry_rows([], registry_rasters_expected=0, complete_accessible_scan=True,
                                    source_errors=[], candidate_meta={'my_dots': 2, 'candidate_rank_variation': True}, scope='empty')
    assert not empty['unique']


@pytest.mark.parametrize('bad', [np.nan, np.inf, -0.1, 1.00000001])
def test_corrupt_interior_never_silently_becomes_zero(tmp_path, bad):
    arr = distant().astype(np.float64)
    arr[8, 8] = bad
    path = write(tmp_path / 'bad.tif', arr)
    result = run(candidate(), inventory(path))
    assert not result['unique'] and 'inside the footprint' in result['rows'][0]['error']
    with pytest.raises(ValueError, match='inside the footprint'):
        saturation_certificate(path, np.ones(SHAPE, bool), expected_grid=EXPECTED)


def test_missing_exterior_is_permitted_but_wrong_georeferencing_is_not(tmp_path):
    fp = np.ones(SHAPE, bool)
    fp[0, 0] = False
    arr = distant()
    arr[0, 0] = np.nan
    path = write(tmp_path / 'exterior.tif', arr)
    assert run(candidate(), inventory(path), fp)['unique']
    wrong = write(tmp_path / 'wrong.tif', distant(), transform=from_origin(200_100, 4_000_000, 100, 100))
    result = run(candidate(), inventory(wrong), fp)
    assert not result['unique'] and 'CRS/transform' in result['rows'][0]['error']


def test_original_precision_is_not_rounded_before_checks(tmp_path):
    path = write(tmp_path / 'near.tif', distant())
    a = candidate().astype(np.float64)
    a[0, 0] = 1.00000001
    with pytest.raises(ValueError, match='finite in'):
        run(a, inventory(path))
    # Tiny positive float64 dots must remain in support (not underflow to zero).
    a = np.zeros(SHAPE, np.float64)
    a[2, 17] = 1e-50
    result = run(a, inventory(path))
    assert result['my_dots'] == 1 and result['worst_dot_overlap'] == 1.0
    assert not result['unique']
