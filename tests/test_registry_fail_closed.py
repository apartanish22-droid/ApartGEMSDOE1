"""Incomplete and empty registries cannot clear a lane."""
import numpy as np
import pytest
from apartgems import uniqueness as u


def test_missing_registry_never_passes():
    a = np.ones((4, 4), dtype=np.float32)
    for check in (u.check_surface_uniqueness, u.check_final_raster_uniqueness):
        with pytest.raises(RuntimeError, match='Full registry index'):
            check(a, a > 0)


def test_empty_registry_never_passes():
    a = np.zeros((4, 4), dtype=np.float32)
    a[1, 1] = 1
    registry = {'complete_accessible_scan': True, 'errors': [], 'rasters': []}
    for check in (u.check_surface_uniqueness, u.check_final_raster_uniqueness):
        result = check(a, np.ones_like(a, dtype=bool), registry_index=registry)
        assert not result['unique']
        assert result['stop_required']
