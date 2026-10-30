"""Regression tests for strict input validation and honest static-replay labels."""
from __future__ import annotations

import numpy as np
import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin

from gems57.grid import Grid
from scripts.evaluate_holdout import load_static_prediction, mark_static_replay


def make_grid(shape=(8, 8)):
    footprint = np.ones(shape, dtype=bool)
    footprint[:2, :2] = False
    catalogue = np.zeros(shape, dtype=bool)
    return Grid(
        footprint=footprint,
        catalogue=catalogue,
        crs=CRS.from_epsg(32611),
        transform=from_origin(0, shape[0] * 100, 100, 100),
        height=shape[0],
        width=shape[1],
    )


def write_raster(path, values, *, crs="EPSG:32611", transform=None, dtype="float32"):
    values = np.asarray(values, dtype=dtype)
    transform = transform or from_origin(0, values.shape[0] * 100, 100, 100)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=values.shape[0],
        width=values.shape[1],
        count=1,
        dtype=dtype,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(values, 1)


def test_static_replay_validates_schema_and_only_masks_permitted_outside_nan(tmp_path):
    grid = make_grid()
    values = np.zeros(grid.shape, dtype=np.float32)
    values[3, 3] = 0.75
    values[:2, :2] = np.nan
    path = tmp_path / "valid.tif"
    write_raster(path, values, transform=grid.transform)

    prediction = load_static_prediction(path, grid)
    assert prediction.dtype == np.float64
    assert prediction[3, 3] == pytest.approx(0.75)
    assert np.all(prediction[~grid.footprint] == 0)
    assert np.isfinite(prediction).all()


def test_static_replay_rejects_invalid_values_without_repair(tmp_path):
    grid = make_grid()
    values = np.zeros(grid.shape, dtype=np.float32)
    values[3, 3] = np.nan
    path = tmp_path / "nan-inside.tif"
    write_raster(path, values, transform=grid.transform)
    with pytest.raises(ValueError, match="inside the footprint"):
        load_static_prediction(path, grid)

    values[3, 3] = 1.01
    write_raster(path, values, transform=grid.transform)
    with pytest.raises(ValueError, match=r"\[0,1\]"):
        load_static_prediction(path, grid)

    values[3, 3] = 0.0
    values[0, 0] = 0.1
    write_raster(path, values, transform=grid.transform)
    with pytest.raises(ValueError, match="outside the footprint"):
        load_static_prediction(path, grid)

    values[0, 0] = np.inf
    write_raster(path, values, transform=grid.transform)
    with pytest.raises(ValueError, match="infinite"):
        load_static_prediction(path, grid)


def test_static_replay_rejects_wrong_grid_and_schema(tmp_path):
    grid = make_grid()
    values = np.zeros(grid.shape, dtype=np.float32)
    path = tmp_path / "wrong.tif"

    write_raster(path, values, transform=from_origin(100, grid.shape[0] * 100, 100, 100))
    with pytest.raises(ValueError, match="transform"):
        load_static_prediction(path, grid)

    write_raster(path, values, crs="EPSG:4326", transform=grid.transform)
    with pytest.raises(ValueError, match="CRS"):
        load_static_prediction(path, grid)

    write_raster(path, values.astype(np.float64), transform=grid.transform, dtype="float64")
    with pytest.raises(ValueError, match="float32"):
        load_static_prediction(path, grid)

    write_raster(path, np.zeros((7, 8), dtype=np.float32), transform=grid.transform)
    with pytest.raises(ValueError, match="shape"):
        load_static_prediction(path, grid)


def test_static_replay_summary_never_claims_holdout_or_leaderboard_score():
    summary = {
        "evidence_class": "HOLDOUT-DTI",
        "scores": {"candidate": {"evidence_class": "HOLDOUT-DTI", "dti": 0.12}},
        "paired_differences": {"control": {"evidence_class": "HOLDOUT-DTI", "delta": 0.01}},
    }
    result = mark_static_replay(summary, candidate_sha256="a" * 64)
    assert result["evidence_class"] == "STATIC-REPLAY-DTI"
    assert result["holdout_contract_fulfilled"] is False
    assert result["fold_honest"] is False
    assert result["model_retrained_per_fold"] is False
    assert "not a fold-honest model CI" in result["confidence_interval_scope"]
    assert result["leaderboard_estimate"] is None
    assert result["candidate_sha256"] == "a" * 64
    assert result["scores"]["candidate"]["evidence_class"] == "STATIC-REPLAY-DTI"
    assert result["paired_differences"]["control"]["evidence_class"] == "STATIC-REPLAY-DTI"
