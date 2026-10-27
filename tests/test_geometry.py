import numpy as np
import pytest
from scipy.stats import spearmanr

from gems_audit.geometry import binary_spearman, disk, feasibility, overlap, within_radius


def test_disk_has_exact_inclusive_euclidean_boundary():
    d = disk(3)
    assert d[3, 6] and d[6, 3] and d[5, 5]  # distance 3 and sqrt(8)
    assert not d[4, 6] and not d[6, 6]       # sqrt(10) and sqrt(18)
    with pytest.raises(ValueError):
        disk(-1)


def test_overlap_direction_and_empty_candidate():
    cand = np.zeros((12, 12), bool)
    ref = np.zeros_like(cand)
    cand[4, 4] = cand[4, 7] = cand[10, 10] = True
    ref[4, 4] = True
    assert overlap(cand, ref, 3) == {"candidate_dots": 3, "within_radius": 2, "fraction": 2 / 3}
    assert overlap(ref, cand, 3)["fraction"] == 1
    assert overlap(np.zeros_like(cand), ref)["fraction"] is None
    with pytest.raises(ValueError):
        overlap(cand, ref[:1])


def test_spearman_binary_ties_and_constant_fields():
    a = np.array([[0, 1, 0], [1, 0, 1]], dtype=bool)
    b = np.array([[1, 1, 0], [1, 0, 0]], dtype=bool)
    f = np.ones_like(a, dtype=bool)
    assert binary_spearman(a, b, f) == pytest.approx(spearmanr(a.ravel(), b.ravel()).statistic)
    assert binary_spearman(a, ~a, f) == pytest.approx(-1)
    assert binary_spearman(a, np.zeros_like(a), f) is None
    with pytest.raises(ValueError):
        binary_spearman(a, b[:1], f)


def test_lattice_bound_is_strictly_greater_than_seventy_percent():
    f = np.ones((1, 10), dtype=bool)
    ref = np.array([[1] * 7 + [0] * 3], dtype=bool)
    result = feasibility(f, ref, 10, radius=0)
    assert result["min_overlap_count"] == 7
    assert result["min_overlap_fraction"] == .7
    assert not result["certain_failure"]
    f = np.ones((1, 11), dtype=bool)
    ref = np.array([[1] * 8 + [0] * 3], dtype=bool)
    result = feasibility(f, ref, 11, radius=0)
    assert result["certain_failure"]
    assert result["largest_budget_not_forced_to_fail_by_this_witness"] == 10
    for bad in (0, -1, 12, True, 1.5):
        with pytest.raises(ValueError):
            feasibility(f, ref, bad, radius=0)


def test_registry_dots_outside_footprint_can_cover_an_inside_cell():
    f = np.array([[False, True, True, True]], dtype=bool)
    ref = np.array([[True, False, False, False]], dtype=bool)
    report = feasibility(f, ref, 3, radius=1)
    assert report["covered_cells"] == 1
    assert report["reference_positive_outside_footprint"] == 1
    assert within_radius(ref, 1)[0, 1]


def test_geometry_rejects_unvalidated_numeric_masks():
    ref = np.array([[False, True]])
    with pytest.raises(ValueError, match="boolean"):
        within_radius(np.array([[0.0, np.nan]]))
    with pytest.raises(ValueError, match="boolean"):
        overlap(np.array([[0, 1]]), ref)
