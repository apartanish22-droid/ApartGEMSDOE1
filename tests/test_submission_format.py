"""Regression tests for the official outside-footprint NaN/nodata contract."""
from __future__ import annotations

import json
from pathlib import Path
import zipfile

import numpy as np
import pytest
import rasterio

from gems57 import load_grid
from gems57.gates import format_report
from gems57.grid import write_geotiff
from gems57.submission_writer import write_submission
from gems57.validate import assert_submittable, validate

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / 'data/bridge/sample_submission.tif'
LEGACY = ROOT / 'docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif'


def test_owner_mirror_sample_has_positive_catalogue_support_despite_official_absence_description():
    grid = load_grid()
    with rasterio.open(SAMPLE) as ds:
        sample = ds.read(1)
        mask = ds.dataset_mask() > 0
        assert ds.nodata is not None and np.isnan(ds.nodata)
        assert np.array_equal(mask, grid.footprint)
    sample_positive = np.isfinite(sample) & (sample > 0)
    assert int(sample_positive.sum()) == 60_988
    assert np.array_equal(sample_positive, grid.catalogue)


def test_legacy_candidate_fails_only_exterior_nodata_policy_under_new_format_gate():
    grid = load_grid()
    report = validate(LEGACY, footprint=grid.footprint, catalogue=grid.catalogue)
    assert report['checks']['single_band']
    assert report['checks']['dtype_float32']
    assert report['checks']['crs_epsg_32611']
    assert report['checks']['values_in_0_1_inside_footprint']
    assert report['checks']['no_nan_inside_footprint']
    assert not report['checks']['outside_footprint_is_nan']
    assert not report['checks']['nodata_tag_is_nan']
    assert not report['all_checks_passed']
    assert report['outside_footprint_pixels'] == 7_111_787
    assert report['outside_footprint_nan_pixels'] == 0
    with pytest.raises(AssertionError, match='outside_footprint_is_nan'):
        assert_submittable(report)


def test_shared_writer_emits_exact_grid_and_nan_nodata_outside(tmp_path):
    grid = load_grid()
    prediction = np.zeros(grid.shape, dtype=np.float32)
    eligible = np.flatnonzero(grid.footprint & ~grid.catalogue)
    assert eligible.size
    prediction.flat[int(eligible[0])] = 0.75

    path = tmp_path / 'candidate.tif'
    receipt = write_submission(
        path,
        prediction,
        SAMPLE,
        grid.footprint,
        name='unit-test-format-candidate',
        note='Test-only; not a competition candidate.',
        catalogue=grid.catalogue,
    )
    assert receipt['approved_for_weekly_slot'] is False
    assert receipt['promoted'] is False
    assert receipt['validator']['all_checks_passed']
    assert receipt['validator']['outside_footprint_nan_pixels'] == int((~grid.footprint).sum())
    assert receipt['validator']['meta']['nodata'] == 'NaN'
    with rasterio.open(path) as ds:
        saved = ds.read(1)
        assert ds.count == 1 and ds.dtypes == ('float32',)
        assert ds.crs == grid.crs and ds.transform == grid.transform
        assert ds.nodata is not None and np.isnan(ds.nodata)
        assert np.isfinite(saved[grid.footprint]).all()
        assert np.isnan(saved[~grid.footprint]).all()
        assert saved[tuple(np.unravel_index(int(eligible[0]), grid.shape))] == pytest.approx(0.75)
    assert_submittable(validate(path, grid.footprint, grid.catalogue))
    on_disk = format_report(path, SAMPLE, footprint=grid.footprint)
    assert on_disk['ok'] and on_disk['nodata_tag_is_nan']
    assert on_disk['outside_footprint_nan_pixels'] == int((~grid.footprint).sum())
    with zipfile.ZipFile(path.with_suffix('.zip')) as archive:
        assert archive.namelist() == [path.name]
        assert archive.read(path.name) == path.read_bytes()
    sidecar = json.loads(path.with_suffix('.json').read_text())
    assert sidecar['validator']['all_checks_passed']
    assert sidecar['approved_for_weekly_slot'] is False
    json.dumps(sidecar, allow_nan=False)  # no non-standard JSON NaN tokens


def test_shared_writer_rejects_invalid_predictions_without_partial_outputs(tmp_path):
    grid = load_grid()
    valid_index = tuple(np.argwhere(grid.footprint & ~grid.catalogue)[0])
    outside_index = tuple(np.argwhere(~grid.footprint)[0])
    cases = []

    nan_inside = np.zeros(grid.shape, dtype=np.float32)
    nan_inside[valid_index] = np.nan
    cases.append((nan_inside, 'NaN inside'))

    below_range = np.zeros(grid.shape, dtype=np.float32)
    below_range[valid_index] = -0.001
    cases.append((below_range, 'finite prediction values'))

    above_range = np.zeros(grid.shape, dtype=np.float32)
    above_range[valid_index] = 1.001
    cases.append((above_range, 'finite prediction values'))

    infinite = np.zeros(grid.shape, dtype=np.float32)
    infinite[outside_index] = np.inf
    cases.append((infinite, 'infinity'))

    positive_outside = np.zeros(grid.shape, dtype=np.float32)
    positive_outside[outside_index] = 0.1
    cases.append((positive_outside, 'outside the valid footprint'))

    for index, (bad, message) in enumerate(cases):
        out = tmp_path / f'bad-{index}.tif'
        with pytest.raises(ValueError, match=message):
            write_submission(
                out, bad, SAMPLE, grid.footprint,
                name=f'bad-{index}', note='invalid test field', catalogue=grid.catalogue,
            )
        assert not out.exists()
        assert not out.with_suffix('.zip').exists()
        assert not out.with_suffix('.json').exists()


def test_low_level_writer_requires_footprint_for_nan_nodata(tmp_path):
    grid = load_grid()
    values = np.zeros(grid.shape, dtype=np.float32)
    values[0, 0] = np.nan
    with pytest.raises(ValueError, match='explicit footprint'):
        write_geotiff(tmp_path / 'no-mask.tif', values, nodata=float('nan'))
    assert not (tmp_path / 'no-mask.tif').exists()
