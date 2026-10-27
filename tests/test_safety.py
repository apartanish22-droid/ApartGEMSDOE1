"""Regression tests for failures found while integrating parallel work."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

import numpy as np
import rasterio
from rasterio.transform import from_origin

import scripts.validate_submission as validator
from scripts.validate_submission import validate
from scripts.prepare_data import inspect_raster

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / 'docs/assets/gemsdoe1-h1-blind-conduit-20261027T212428Z-06281cc7efb3-zeros.tif'


def write_tif(path, values, transform, nodata=np.nan):
    with rasterio.open(path, 'w', driver='GTiff', count=1, dtype='float32',
                       height=values.shape[0], width=values.shape[1],
                       crs='EPSG:32611', transform=transform, nodata=nodata) as ds:
        ds.write(values.astype('float32'), 1)


def test_parallel_demo_audit_is_not_a_competition_grid():
    report = json.loads((ROOT / 'evidence/parallel_demo_audit.json').read_text())
    assert hashlib.sha256(DEMO.read_bytes()).hexdigest() == report['sha256']
    with rasterio.open(DEMO) as ds:
        assert ds.crs.to_epsg() == 32611 and ds.shape == (3730, 3292)
        assert tuple(ds.transform) == tuple(report['checks']['candidate']['transform'])
        assert (ds.transform.c, ds.transform.f) == (0, 0)
    assert report['checks']['template']['transform'][2:6:3] == [243350.0, 4508550.0]
    assert report['checks']['template_transform_match'] is False
    assert report['checks']['aligned_for_footprint'] is False
    assert report['checks']['finite_in_footprint'] is None
    assert not report['format_pass'] and not report['slot_approved']


def test_outside_null_template_is_distinct_from_slot_approval(tmp_path, monkeypatch):
    # Exercise a miniature synthetic grid without treating it as a competition grid.
    monkeypatch.setattr(validator, 'EXPECTED_SHAPE', (2, 2))
    t = from_origin(500, 600, 100, 100)
    template = tmp_path / 'template.tif'
    candidate = tmp_path / 'candidate.tif'
    reference = np.array([[0, 0], [0, np.nan]], dtype='float32')
    write_tif(template, reference, t)
    assert inspect_raster(template)['dtypes'] == ['float32']
    json.dumps(inspect_raster(template), allow_nan=False)
    write_tif(candidate, np.array([[0, .25], [1, np.nan]]), t)
    result = validate(candidate, template)
    assert result['format_pass'] and result['checks']['outside_null']
    assert not result['slot_approved'] and not result['organizer_acceptance_established']
    assert result['template_organizer_authenticated'] is None
    write_tif(candidate, np.array([[0, .25], [1, 0]]), t)
    result = validate(candidate, template)
    assert not result['format_pass'] and not result['checks']['outside_null']
    assert 'nonnull cells outside the template footprint' in result['errors']
    write_tif(candidate, np.array([[0, .25], [1, np.inf]]), t)
    assert not validate(candidate, template)['format_pass']
    assert not validate(candidate)['format_pass']
    # A NaN in a template without a nodata tag is still outside its footprint.
    write_tif(template, reference, t, nodata=None)
    write_tif(candidate, np.array([[0, .25], [1, np.nan]]), t, nodata=None)
    result = validate(candidate, template)
    assert result['format_pass'] and result['checks']['inside_pixels'] == 3


def test_unsafe_parallel_entrypoints_are_disabled(tmp_path):
    for name in ('generate_submission.py', 'evaluate_holdout.py', 'submission_writer.py'):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts' / name)], cwd=tmp_path,
                                capture_output=True, text=True, check=False)
        assert result.returncode == 2, (name, result.stdout, result.stderr)
        assert 'STOP' in result.stderr
    assert not list(tmp_path.iterdir())


def test_run_card_copies_agree():
    canonical = json.loads((ROOT / 'evidence/run_card.json').read_text())
    for path in (ROOT / 'run_card.json', ROOT / 'docs/run_card.json'):
        assert json.loads(path.read_text()) == canonical
    assert canonical['verdict'] == 'negative'
    assert canonical['parallel_demo']['format_pass'] is False
    assert canonical['raster_sha256'] is None
