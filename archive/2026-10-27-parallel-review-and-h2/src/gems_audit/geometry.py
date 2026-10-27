"""Literal registry-geometry checks. These are not holdout or leaderboard scores."""
from __future__ import annotations

import math

import numpy as np
from scipy.ndimage import binary_dilation


def disk(radius: int) -> np.ndarray:
    if isinstance(radius, bool) or not isinstance(radius, int) or radius < 0:
        raise ValueError("radius must be a non-negative integer")
    yy, xx = np.mgrid[-radius:radius + 1, -radius:radius + 1]
    return xx * xx + yy * yy <= radius * radius


def _mask(value: np.ndarray) -> np.ndarray:
    out = np.asarray(value)
    if out.dtype != np.dtype(bool):
        raise ValueError("geometry inputs must be boolean masks, not unvalidated raster values")
    return out


def within_radius(reference: np.ndarray, radius: int = 3) -> np.ndarray:
    ref = _mask(reference)
    if ref.ndim != 2:
        raise ValueError("reference must be 2-D")
    return binary_dilation(ref, structure=disk(radius))


def overlap(candidate: np.ndarray, reference: np.ndarray, radius: int = 3) -> dict:
    """Fraction of candidate cells within <=radius Euclidean pixels of reference.

    Direction matters: the denominator is candidate support, not reference support.
    Undefined for empty candidate support; it must never be treated as a pass.
    """
    cand = _mask(candidate)
    ref = _mask(reference)
    if cand.ndim != 2 or cand.shape != ref.shape:
        raise ValueError("matching 2-D grids required")
    count = int(cand.sum())
    matched = int(np.count_nonzero(cand & within_radius(ref, radius)))
    return {"candidate_dots": count, "within_radius": matched,
            "fraction": matched / count if count else None}


def binary_spearman(a: np.ndarray, b: np.ndarray, footprint: np.ndarray) -> float | None:
    """Spearman rho of binary fields over the footprint, including tied zeros.

    For binary variables Pearson/phi is identical to Spearman. Undefined for a
    constant field; do not substitute zero or treat an undefined value as a pass.
    """
    a = _mask(a)
    b = _mask(b)
    f = _mask(footprint)
    if a.ndim != 2 or a.shape != b.shape or a.shape != f.shape:
        raise ValueError("matching 2-D grids required")
    n = int(f.sum())
    ca = int(np.count_nonzero(a & f))
    cb = int(np.count_nonzero(b & f))
    both = int(np.count_nonzero(a & b & f))
    den2 = ca * (n - ca) * cb * (n - cb)
    if den2 == 0:
        return None
    return (n * both - ca * cb) / math.sqrt(den2)


def feasibility(footprint: np.ndarray, reference: np.ndarray, budget: int,
                radius: int = 3) -> dict:
    """Lower bound on overlap of any distinct in-footprint dots of given budget.

    If U footprint cells are more than radius pixels from the reference, at most
    U candidate cells can avoid proximity. Thus >= max(0, budget-U) must overlap.
    This is a necessary condition only; a pass is not proof of uniqueness.
    """
    f = _mask(footprint)
    ref = _mask(reference)
    if f.ndim != 2 or f.shape != ref.shape or not f.any():
        raise ValueError("nonempty footprint and matching 2-D reference required")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0 or budget > int(f.sum()):
        raise ValueError("budget must be a positive number of distinct footprint cells")
    # A registry dot just outside the footprint can still be close to an inside dot.
    near = f & within_radius(ref, radius)
    count = int(f.sum())
    covered = int(near.sum())
    uncovered = count - covered
    lower_count = max(0, budget - uncovered)
    # Strict failure is >70%, including at exactly 70% as not a failure.
    certain_failure = lower_count * 10 > budget * 7
    return {
        "footprint_cells": count,
        "reference_positive_cells": int(np.count_nonzero(ref & f)),
        "reference_positive_outside_footprint": int(np.count_nonzero(ref & ~f)),
        "covered_cells": covered,
        "uncovered_cells": uncovered,
        "covered_fraction": covered / count,
        "distance_rule": f"Euclidean distance <= {radius} pixels",
        "budget": budget,
        "min_overlap_count": lower_count,
        "min_overlap_fraction": lower_count / budget,
        "threshold_fraction": 0.7,
        "certain_failure": certain_failure,
        # Necessary condition only; other registry entries can impose more limits.
        "largest_budget_not_forced_to_fail_by_this_witness": min(count, (uncovered * 10) // 3),
    }
