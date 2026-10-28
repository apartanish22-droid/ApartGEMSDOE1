"""Export rejects bad probabilities; CLI preflight never grants a slot."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from gems57 import grid as gridmod, validate as validmod, gates, submission_writer as writer

ROOT = Path(__file__).resolve().parents[1]
SHAPE = (20, 20)
TRANSFORM = from_origin(200_000, 4_000_000, 100, 100)


def sample(path):
    with rasterio.open(path, 'w', driver='GTiff', height=SHAPE[0], width=SHAPE[1],
                       count=1, dtype='float32', crs='EPSG:32611', transform=TRANSFORM) as ds:
        ds.write(np.zeros(SHAPE, np.float32), 1)
    return path


@pytest.fixture
def small_grid(tmp_path, monkeypatch):
    for module, key, value in (
        (gridmod, 'SHAPE', SHAPE), (gridmod, 'HEIGHT', SHAPE[0]), (gridmod, 'WIDTH', SHAPE[1]),
        (gridmod, 'TRANSFORM', TRANSFORM), (gridmod, 'CRS_EPSG', 'EPSG:32611'),
        (validmod, 'HEIGHT', SHAPE[0]), (validmod, 'WIDTH', SHAPE[1]), (validmod, 'TRANSFORM', TRANSFORM),
        (gates, 'SHAPE', SHAPE), (gates, 'TRANSFORM', TRANSFORM),
    ):
        monkeypatch.setattr(module, key, value)
    ref = sample(tmp_path / 'sample.tif')
    fp = np.ones(SHAPE, bool)
    fp[0, 0] = False
    cat = np.zeros(SHAPE, bool)
    cat[2, 2] = True
    return ref, fp, cat


def test_valid_writer_roundtrip_is_only_a_local_format_receipt(tmp_path, small_grid):
    ref, fp, cat = small_grid
    pred = np.zeros(SHAPE, np.float32)
    pred[5, 5], pred[12, 13] = .4, 1
    path = tmp_path / 'research.tif'
    receipt = writer.write_submission(path, pred, ref, fp, catalogue=cat, name='research', note='Not slot approved.')
    assert receipt['validator']['all_checks_passed'] and receipt['template_report']['ok']
    assert not receipt['approved_for_weekly_slot'] and not receipt['promoted']
    assert 'format/range check only' in receipt['status']
    with rasterio.open(path) as ds:
        assert ds.dtypes == ('float32',) and (ds.read(1) == pred).all()
    with zipfile.ZipFile(path.with_suffix('.zip')) as z:
        assert z.namelist() == [path.name] and z.read(path.name) == path.read_bytes()
    with pytest.raises(FileExistsError):
        writer.write_submission(path, pred, ref, fp, catalogue=cat, name='research', note='Not slot approved.')


@pytest.mark.parametrize('bad', [np.nan, np.inf, -0.1, 1.00000001])
def test_writer_rejects_invalid_values_without_creating_artifacts(tmp_path, small_grid, bad):
    ref, fp, cat = small_grid
    pred = np.zeros(SHAPE, np.float64)
    pred[5, 5] = bad
    path = tmp_path / 'bad.tif'
    with pytest.raises(ValueError, match='finite and in'):
        writer.write_submission(path, pred, ref, fp, catalogue=cat, name='bad', note='No.')
    assert not any(tmp_path.glob('bad.*'))


def test_writer_never_overwrites_racing_file(tmp_path, small_grid, monkeypatch):
    ref, fp, cat = small_grid
    pred = np.zeros(SHAPE, np.float32)
    pred[5, 5] = 1
    path = tmp_path / 'race.tif'
    original_link = writer.os.link
    def race(src, dst):
        Path(dst).write_bytes(b'another process owns this file')
        return original_link(src, dst)
    monkeypatch.setattr(writer.os, 'link', race)
    with pytest.raises(FileExistsError):
        writer.write_submission(path, pred, ref, fp, catalogue=cat, name='race', note='No.')
    assert path.with_suffix('.zip').read_bytes() == b'another process owns this file'
    assert not path.exists()


def test_validator_cli_fails_closed_without_saved_surface_and_registry():
    tif = ROOT / 'docs/downloads/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif'
    cmd = [sys.executable, str(ROOT / 'scripts/validate_submission.py')]
    normal = subprocess.run([*cmd, str(tif)], text=True, capture_output=True, check=False)
    assert normal.returncode == 1, normal.stderr
    receipt = json.loads(normal.stdout)
    assert not receipt['local_checks_passed'] and not receipt['submission_ready']
    assert not receipt['weekly_slot_approved']
    assert any('registry' in e for e in receipt['errors'])
    assert any('surface' in e for e in receipt['errors'])
    formatted = subprocess.run([*cmd, '--format-only', str(tif)], text=True, capture_output=True, check=False)
    assert formatted.returncode == 0, formatted.stderr
    receipt = json.loads(formatted.stdout)
    assert receipt['diagnostic_format_only'] and receipt['local_checks_passed']
    assert not receipt['submission_ready'] and not receipt['weekly_slot_approved']


def test_surface_failure_stops_before_final_dot_gate(monkeypatch, capsys, tmp_path):
    spec = importlib.util.spec_from_file_location('validator_cli_test', ROOT / 'scripts/validate_submission.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    class Grid:
        footprint = np.ones(SHAPE, bool)
        catalogue = np.zeros(SHAPE, bool)
        shape = SHAPE
    monkeypatch.setattr(mod, 'load_grid', lambda: Grid())
    monkeypatch.setattr(mod, 'validate', lambda *a, **kw: {'all_checks_passed': True})
    monkeypatch.setattr(mod, 'format_report', lambda *a, **kw: {'ok': True})
    monkeypatch.setattr(mod, 'read_aligned', lambda *a: np.zeros(SHAPE))
    phases = []
    def gate(*args, phase, **kwargs):
        phases.append(phase)
        return {'ok': False}
    monkeypatch.setattr(mod, 'lane_uniqueness_report', gate)
    monkeypatch.setattr(sys, 'argv', ['validate_submission', str(tmp_path/'candidate.tif'), '--surface', str(tmp_path/'surface.tif'), '--registry-index', str(tmp_path/'index.json')])
    assert mod.main() == 1
    receipt = json.loads(capsys.readouterr().out)
    assert phases == ['surface'] and receipt['final_raster_gate'] is None
    assert not receipt['submission_ready'] and any('stop before dot' in e for e in receipt['errors'])
