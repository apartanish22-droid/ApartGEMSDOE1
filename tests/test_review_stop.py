from pathlib import Path
import hashlib
import json
import subprocess
import sys

import numpy as np
import rasterio
from rasterio.transform import from_origin

from gems57.uniqueness import compare_array_to_registry
from apartgems.uniqueness import check_final_raster_uniqueness
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_recorded_witness_is_a_stop_not_a_slot():
    report = json.loads((ROOT / 'evidence/lattice_stop.json').read_text())
    assert report['candidate_dots_within_3px'] / report['candidate_positive_pixels'] == report['forward_overlap']
    assert report['forward_overlap'] > report['overlap_limit']
    assert report['duplicate'] and report['verdict'] == 'negative'
    assert report['format_local']['all_checks_passed'] and report['format_local']['sample_grid_matches']
    assert report['submission_slots_used'] == 0


def test_dense_lattice_is_not_exempted_from_shared_gate(tmp_path):
    fp = np.ones((20, 20), bool)
    candidate = np.zeros((20, 20), np.float32)
    candidate[2::5, 2::5] = 1
    prior = np.ones((20, 20), np.float32)
    path = tmp_path / 'dense.tif'
    with rasterio.open(path, 'w', driver='GTiff', width=20, height=20, count=1,
                       dtype='float32', crs='EPSG:32611', transform=from_origin(0, 2000, 100, 100)) as ds:
        ds.write(prior, 1)
    index = {'complete_accessible_scan': True, 'errors': [], 'rasters': [
        {'repo_first': 'test', 'sources': ['test'], 'cache_file': str(path),
         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}]}
    result = compare_array_to_registry(candidate, index, fp)
    assert result['worst_dot_overlap'] == 1.0
    assert result['stop_required'] and not result['unique']
    assert result['rows'][0]['duplicate_by_overlap']


def test_old_private_gate_refuses_missing_inventory():
    with pytest.raises(RuntimeError, match='Full registry index'):
        check_final_raster_uniqueness(np.zeros((3, 3)), np.ones((3, 3), bool))


def test_unsafe_historical_runners_fail_closed():
    # The replacement audit and page builder are safe negative-only tools; the
    # two historical candidate generators remain deliberately unavailable.
    for script in ('run_apartgems_pipeline.py', 'run_concordance_hybrid.py'):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts' / script)], capture_output=True, text=True)
        assert result.returncode != 0
        assert any(word in result.stderr.lower() for word in ('retired', 'disabled'))


def test_marginal_accept_works_for_noncomplementary_weights():
    from gems57.metric import marginal_accept, dti_from_components
    for alpha, beta in [(0.2, 0.8), (0.7, 0.4), (0.1, 1.0)]:
        for dt in (0.01, 0.2, 1.2):
            T, M, n, K, k = 2.0, 1.5, 4, 10, 0.4
            before = dti_from_components(T, n-M, K-T, alpha, beta)
            after = dti_from_components(T+dt, n+1-M-k, K-T-dt, alpha, beta)
            assert marginal_accept(dt, k, T, M, n, K, alpha, beta) == (after > before)
