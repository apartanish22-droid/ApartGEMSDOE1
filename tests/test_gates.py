"""Regression tests for prior-raster discovery safety.

These tests do not load model data or clear uniqueness. They ensure broad file
scans cannot mistake competition inputs for previous submissions.
"""
from pathlib import Path

from gems57.gates import find_priors


def _large_placeholder(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"test raster placeholder\n" * 128)
    return path


def test_find_priors_excludes_competition_inputs(tmp_path):
    input_paths = [
        tmp_path / "data/bridge/existing_faults.tif",
        tmp_path / "data/official/labels.tif",
        tmp_path / "data/official/sample_submission.tif",
        tmp_path / "data/official/training_features.tif",
        tmp_path / "data/raw/labels.tif",
        tmp_path / "data/external/derived_layer.tif",
        tmp_path / "data/dem10/slope.tif",
    ]
    for path in input_paths:
        _large_placeholder(path)

    prior = _large_placeholder(tmp_path / "docs/downloads/prior-submission.tif")
    renamed_prior = _large_placeholder(tmp_path / "registry/renamed.tif")

    assert find_priors([tmp_path / "data"]) == []
    found = find_priors([tmp_path])
    assert found == [prior, renamed_prior]
    assert find_priors([tmp_path], exclude=prior) == [renamed_prior]
