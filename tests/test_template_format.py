"""Regression tests for the official-template (NaN outside) writer and validator,
and for the leakage-free static-only geometry control. Added 2026-10-31.

These tests use the committed owner-mirror sample grid (data/bridge), so they run
on a fresh checkout without the 418 MB feature stack.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import load_grid  # noqa: E402
from gems57.grid import DATA_DIR  # noqa: E402
from gems57.submission_writer import write_template_submission  # noqa: E402
from gems57.validate import validate_template  # noqa: E402


@pytest.fixture(scope="module")
def grid():
    return load_grid()


def _dots(grid, n=500, seed=3):
    rng = np.random.default_rng(seed)
    cand = np.flatnonzero((grid.footprint & ~grid.catalogue).ravel())
    pick = rng.choice(cand, size=n, replace=False)
    p = np.zeros(grid.shape, np.float32)
    p.ravel()[pick] = 1.0
    return p


def test_template_writer_matches_sample_nan_mask(grid, tmp_path):
    p = _dots(grid)
    out = tmp_path / "t.tif"
    receipt = write_template_submission(out, p, grid.footprint, grid.catalogue,
                                        name="unit-test", note="synthetic dots")
    assert receipt["validator"]["all_checks_passed"] is True
    with rasterio.open(out) as src, rasterio.open(DATA_DIR / "sample_submission.tif") as ref:
        a = src.read(1)
        assert src.dtypes[0] == "float32" and src.count == 1
        assert src.crs == ref.crs and src.transform == ref.transform and src.shape == ref.shape
        assert np.array_equal(np.isnan(a), np.isnan(ref.read(1)))
    assert np.nanmin(a) >= 0.0 and np.nanmax(a) <= 1.0
    with zipfile.ZipFile(out.with_suffix(".zip")) as z:
        assert z.namelist() == [out.name]
    assert json.loads(out.with_suffix(".json").read_text())["submission_slots_used"] == 0


def test_template_writer_refuses_out_of_range_and_catalogue_dots(grid, tmp_path):
    p = _dots(grid)
    bad = p.copy()
    idx = np.flatnonzero(grid.footprint.ravel())[0]
    bad.ravel()[idx] = 1.5
    with pytest.raises(ValueError):
        write_template_submission(tmp_path / "a.tif", bad, grid.footprint, grid.catalogue,
                                  name="x", note="y")
    on_cat = p.copy()
    cidx = np.flatnonzero(grid.catalogue.ravel())[0]
    on_cat.ravel()[cidx] = 1.0
    with pytest.raises(ValueError):
        write_template_submission(tmp_path / "b.tif", on_cat, grid.footprint, grid.catalogue,
                                  name="x", note="y")
    assert not (tmp_path / "a.tif").exists() and not (tmp_path / "b.tif").exists()


def test_template_writer_refuses_overwrite(grid, tmp_path):
    p = _dots(grid)
    write_template_submission(tmp_path / "c.tif", p, grid.footprint, grid.catalogue,
                              name="x", note="y")
    with pytest.raises(FileExistsError):
        write_template_submission(tmp_path / "c.tif", p, grid.footprint, grid.catalogue,
                                  name="x", note="y")


def test_validate_template_rejects_zeros_outside(grid, tmp_path):
    """A zero-outside file is a DIFFERENT convention and must fail the template check."""
    z = np.where(grid.footprint, _dots(grid), 0.0).astype(np.float32)
    path = tmp_path / "zeros.tif"
    with rasterio.open(path, "w", driver="GTiff", height=z.shape[0], width=z.shape[1], count=1,
                       dtype="float32", crs=grid.crs, transform=grid.transform, nodata=None) as dst:
        dst.write(z, 1)
    rec = validate_template(path, grid.footprint, grid.catalogue, sample=DATA_DIR / "sample_submission.tif")
    assert rec["all_checks_passed"] is False
    assert rec["checks"]["outside_footprint_all_nan"] is False


def test_static_only_geometry_has_no_catalogue_columns(grid):
    """The leakage-free control must read only the static planes."""
    from gems57.anatomy import fold_geometry
    from gems57.holdout import build_holdout
    from gems57.holdout import FOLD_NAMES  # noqa: F401
    ctx = build_holdout(grid, seeds=(20,), modes=("all",))
    cell = ctx.cells[0]
    dom = np.zeros(grid.shape, bool)
    dom[cell.bbox] = cell.active
    planes = {"g_fake": np.zeros(grid.shape, np.float32),
              "g_fake2": np.ones(grid.shape, np.float32)}
    g = fold_geometry(grid, ctx.visible(cell.key), ctx.hidden_by_cell[cell.key], dom,
                      cell.key, geo=planes, static_only=True)
    assert g.feature_names == ("g_fake", "g_fake2")
    assert g.X.shape[1] == 2
    assert int(g.y.sum()) == cell.n_truth


def test_cli_format_only_accepts_official_template_and_stays_strict_json():
    import json
    import subprocess
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    tif = root / 'docs/downloads/apartgems-e3-geo-paired-static-30562dots-NOT-CLEARED-20261031.tif'
    run = subprocess.run([sys.executable, str(root / 'scripts/validate_submission.py'), str(tif), '--format-only'],
                         capture_output=True, text=True, cwd=root)
    assert run.returncode == 0, run.stdout[-500:] + run.stderr[-500:]
    doc = json.loads(run.stdout)  # strict JSON parse
    assert doc['format']['all_checks_passed'] is True
    assert doc['ok_to_submit'] is False  # format pass is never a submission approval
    assert 'BLOCKED' in doc['registry_gate']
    old = subprocess.run([sys.executable, str(root / 'scripts/validate_submission.py'),
                          str(root / 'docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif'), '--format-only'],
                         capture_output=True, text=True, cwd=root)
    assert old.returncode != 0  # zeros outside the footprint violate the official NaN rule
