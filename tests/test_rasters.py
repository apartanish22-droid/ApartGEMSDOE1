import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from gems_audit.rasters import inspect_candidate, template_info


def make_tif(path, arr, *, nodata=None, transform=None, crs="EPSG:32611", dtype="float32"):
    data = np.asarray(arr, dtype=dtype)
    if data.ndim == 2:
        data = data[None, ...]
    with rasterio.open(path, "w", driver="GTiff", height=data.shape[1], width=data.shape[2],
                       count=data.shape[0], dtype=dtype, crs=crs,
                       transform=transform or from_origin(100, 200, 100, 100), nodata=nodata) as dst:
        dst.write(data)


@pytest.fixture
def grid(tmp_path):
    sample = np.zeros((4, 5), dtype=np.float32)
    sample[0, 0] = np.nan
    sample[3, 4] = np.nan
    make_tif(tmp_path / "sample.tif", sample, nodata=np.nan)
    return template_info(tmp_path / "sample.tif")


def test_finite_zero_profile_is_reported_without_promising_acceptance(tmp_path, grid):
    a = np.zeros((4, 5), dtype=np.float32)
    a[1, 1] = .42
    path = tmp_path / "candidate.tif"
    make_tif(path, a)
    r = inspect_candidate(path, grid)
    assert r["basic_checks_passed"] and r["whole_array_finite_in_range"]
    assert not r["strict_irregular_footprint_null"]
    assert r["inside_nan"] == 0 and r["inside_min"] == 0 and r["inside_max"] == pytest.approx(.42)
    assert not r["approved_to_submit"] and not r["organizer_accepted"]


def test_nan_outside_profile_is_distinct_from_allfinite(tmp_path, grid):
    a = np.zeros((4, 5), dtype=np.float32)
    a[~grid["footprint"]] = np.nan
    path = tmp_path / "nan.tif"
    make_tif(path, a, nodata=np.nan)
    r = inspect_candidate(path, grid)
    assert r["basic_checks_passed"] and r["strict_irregular_footprint_null"]
    assert not r["whole_array_finite_in_range"]


@pytest.mark.parametrize("bad", [np.nan, np.inf, -3.4028235e38, -0.01, 1.01])
def test_nonfinite_and_out_of_range_inside_fail_without_repair(tmp_path, grid, bad):
    a = np.zeros((4, 5), dtype=np.float32)
    a[1, 1] = bad
    p = tmp_path / "bad.tif"
    make_tif(p, a)
    r = inspect_candidate(p, grid)
    assert not r["basic_checks_passed"]
    assert r["inside_out_of_range_or_nonfinite"] == 1
    with rasterio.open(p) as src:
        observed = src.read(1)[1, 1]
    assert (np.isnan(observed) and np.isnan(bad)) or observed == np.float32(bad)


def test_zero_nodata_marks_inside_cells_invalid(tmp_path, grid):
    path = tmp_path / "masked.tif"
    make_tif(path, np.zeros((4, 5)), nodata=0)
    r = inspect_candidate(path, grid)
    assert not r["checks"]["inside_not_nodata"]
    assert not r["basic_checks_passed"]


def test_positive_outside_footprint_and_misalignment_fail(tmp_path, grid):
    a = np.zeros((4, 5), np.float32)
    a[0, 0] = .5
    p = tmp_path / "outside.tif"
    make_tif(p, a)
    r = inspect_candidate(p, grid)
    assert not r["checks"]["no_unmasked_positive_outside_footprint"]
    assert not r["basic_checks_passed"]
    p = tmp_path / "shifted.tif"
    make_tif(p, np.zeros_like(a), transform=from_origin(101, 200, 100, 100))
    r = inspect_candidate(p, grid)
    assert not r["checks"]["transform_match"] and not r["basic_checks_passed"]
    assert "array-index diagnostic only" in r["footprint_comparison"]


def test_shape_band_dtype_and_crs_are_checked(tmp_path, grid):
    p = tmp_path / "shape.tif"
    make_tif(p, np.zeros((3, 5)))
    assert not inspect_candidate(p, grid)["checks"]["shape_match"]
    p = tmp_path / "bands.tif"
    make_tif(p, np.zeros((2, 4, 5)))
    assert not inspect_candidate(p, grid)["checks"]["single_band"]
    p = tmp_path / "dtype.tif"
    make_tif(p, np.zeros((4, 5)), dtype="uint8")
    assert not inspect_candidate(p, grid)["checks"]["float32"]
    p = tmp_path / "crs.tif"
    make_tif(p, np.zeros((4, 5)), crs="EPSG:4326")
    assert not inspect_candidate(p, grid)["checks"]["crs_match"]


def test_empty_template_fails_closed(tmp_path):
    p = tmp_path / "empty.tif"
    make_tif(p, np.full((2, 2), np.nan), nodata=np.nan)
    with pytest.raises(ValueError, match="empty"):
        template_info(p)


def test_validator_cli_defaults_to_conservative_profile(tmp_path, monkeypatch, capsys):
    import json
    import sys
    from scripts import validate_raster

    sample = np.zeros((3, 3), np.float32)
    sample[0, 0] = np.nan
    template = tmp_path / "sample.tif"
    candidate = tmp_path / "finite.tif"
    make_tif(template, sample, nodata=np.nan)
    make_tif(candidate, np.zeros((3, 3), np.float32))
    # The real CLI verifies the pinned template; exercise policy with a synthetic grid.
    monkeypatch.setattr(validate_raster, "verify_file", lambda *args: None)
    cmd = ["validate_raster.py", str(candidate), "--template", str(template)]
    monkeypatch.setattr(sys, "argv", cmd)
    assert validate_raster.main() == 1
    report = json.loads(capsys.readouterr().out)
    assert not report["profile_passed"] and report["validation_profile"] == "null-outside"
    assert not report["approved_to_submit"]
    monkeypatch.setattr(sys, "argv", [*cmd, "--profile", "all-finite"])
    assert validate_raster.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["profile_passed"] and not report["approved_to_submit"] and not report["organizer_accepted"]
