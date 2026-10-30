"""Regression tests for the official GeoTIFF format, the CLI writer, and evidence records.

No network access. These tests use only the pinned owner-mirror sample grid in
data/bridge/ and the existing single-band prior file. They verify local format
facts; they do not establish organizer acceptance.
"""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from gems57 import grid  # noqa: E402

PRIOR = ROOT / 'docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif'


def test_cli_writer_runs_on_fresh_checkout_grid(tmp_path):
    """Regression: the CLI used to point at data/sample_submission.tif, which exists only after prepare_data.py."""
    arr = tmp_path / 'zeros.npy'
    np.save(arr, np.zeros((grid.HEIGHT, grid.WIDTH), dtype=np.float32))
    out = tmp_path / 'cli_regression.tif'
    proc = subprocess.run(
        [sys.executable, str(ROOT / 'scripts/submission_writer.py'), str(arr), str(out),
         '--name', 'cli-regression', '--note', 'cli path regression check'],
        capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    receipt = json.loads(proc.stdout)
    assert receipt['approved_for_weekly_slot'] is False
    assert receipt['submission_slots_used'] == 0
    assert receipt['validator']['checks']['outside_footprint_nan'] is True
    assert receipt['template_report']['ok'] is True
    assert out.is_file() and out.with_suffix('.zip').is_file() and out.with_suffix('.json').is_file()


def test_nan_outside_variant_reproduces_official_sample_nan_mask(tmp_path):
    """Official rule: data outside the bounds is null or nan. The sample template uses NaN outside its footprint."""
    with rasterio.open(ROOT / 'data/bridge/sample_submission.tif') as src:
        sample = src.read(1)
        assert np.isnan(src.nodata)
    footprint = grid.load_grid().footprint
    assert np.array_equal(np.isfinite(sample), footprint)
    assert int(footprint.sum()) == 5_167_373

    with rasterio.open(PRIOR) as src:
        prior = src.read(1)
    variant = np.where(footprint, prior, np.float32('nan')).astype(np.float32)
    out = tmp_path / 'nan_variant.tif'
    receipt = grid.write_submission(out, variant)
    assert receipt['mode'] == 'nan'
    assert receipt['nodata'] == 'NaN'  # JSON-safe nodata tag
    with rasterio.open(out) as src:
        written = src.read(1)
    assert np.array_equal(np.isnan(written), np.isnan(sample))
    assert np.array_equal(written[footprint], prior[footprint])
    assert float(np.nanmin(written)) >= 0.0 and float(np.nanmax(written)) <= 1.0


def test_gated_writer_emits_nan_only_outside_sample_footprint(tmp_path):
    """The shared writer must follow the documented null/NaN mask without changing in-footprint predictions."""
    from gems57.submission_writer import write_submission
    sample_path = grid.DATA_DIR / 'sample_submission.tif'
    footprint = grid.load_grid().footprint
    values = np.zeros((grid.HEIGHT, grid.WIDTH), dtype=np.float32)
    out = tmp_path / 'nan_outside.tif'
    receipt = write_submission(out, values, sample_path, footprint, name='format-regression',
                               note='NaN only outside sample footprint')
    assert receipt['template_report']['ok'] is True
    assert receipt['validator']['all_checks_passed'] is True
    assert receipt['validator']['checks']['no_nan_inside_footprint'] is True
    assert receipt['validator']['checks']['outside_footprint_nan'] is True
    with rasterio.open(out) as src:
        written = src.read(1)
        assert np.isnan(src.nodata)
    assert np.array_equal(np.isnan(written), ~footprint)
    assert np.array_equal(written[footprint], values[footprint])

    invalid = values.copy()
    inside_y, inside_x = np.argwhere(footprint)[0]
    invalid[inside_y, inside_x] = np.nan
    with pytest.raises(ValueError, match='finite throughout the valid footprint'):
        write_submission(tmp_path / 'inside_nan.tif', invalid, sample_path, footprint,
                         name='invalid', note='NaN inside')
    invalid = values.copy()
    invalid[~footprint] = 0.25
    with pytest.raises(ValueError, match='outside-footprint input'):
        write_submission(tmp_path / 'positive_outside.tif', invalid, sample_path, footprint,
                         name='invalid', note='positive outside')

    wrong_mask = footprint.copy()
    wrong_mask[inside_y, inside_x] = False
    with pytest.raises(ValueError, match="footprint differs from the sample"):
        write_submission(tmp_path / 'wrong_mask.tif', values, sample_path, wrong_mask,
                         name='invalid', note='wrong mask')


def test_official_rules_record_contains_verified_quotes_and_sources():
    rec = json.loads((ROOT / 'evidence/official_rules_check.json').read_text())
    assert rec['verification_method'].startswith('fetch_page tool')
    assert rec['checked_utc'].startswith('2026-10-30')
    quotes = ' '.join(c['quote'] for c in rec['claims'])
    assert 'data outside the bounds is null or nan' in quotes
    assert 'values between 0 and 1' in quotes
    assert 'original work by the competitor' in quotes
    assert 'three submissions per week' in quotes
    for claim in rec['claims']:
        assert claim['source_url'].startswith('https://')
    assert rec['leaderboard_observed']['top_public_dti'] == 0.4544
    assert rec['user_claims_not_on_leaderboard']['0.4413'] and rec['user_claims_not_on_leaderboard']['0.3195']


def test_review_record_declares_no_experiment_and_no_slot():
    text = (ROOT / 'evidence/repo_review_2026-10-30.md').read_text()
    assert 'experiments run: 0' in text.lower()
    assert 'slots used: 0' in text.lower()
    assert 'ok to download and submit: no' in text.lower()
