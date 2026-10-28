"""Zero-leaderboard-fit Concealed Piedmont/Basin Geological Evaluator (``sgmc-piedmont-basin-v1``).

Strictly read-only diagnostic benchmark on USGS State Geologic Map Compilation (SGMC,
Horton et al. 2017, DOI:10.3133/ds1052) concealed piedmont/basin fault traces that lie:
  * inside the competition footprint,
  * strictly outside ``d_cat <= 2.5 px`` (``> 250 m``) of ``existing_faults.tif``,
  * beneath ``depth_to_base_surf >= 250 m`` (Band 15 Cenozoic basin cover), and
  * in subdued topography (``relief_local <= p75(cat)``, ``slope_p90 <= p80(cat)``).

INVARIANT: ``derived_sgmc_faults_100m.tif`` is NEVER imported or read by
``apartgems.features`` or ``apartgems.model`` (enforced by automated AST/grep tests).
Every score from this module is labeled ``HOLDOUT-DTI (sgmc-piedmont-basin-v1)``
with withheld positive pixel count and 20 km spatial block bootstrap 95% CI.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from gems57 import evaluate_holdout as EH, load_grid

EVALUATOR_VERSION = "sgmc-piedmont-basin-v1"


def build_concealed_piedmont_fold(root: Path | None = None) -> dict[str, Any]:
    """Construct the ``sgmc-piedmont-basin-v1`` read-only evaluation fold."""
    base = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    grid = load_grid()
    fp = grid.footprint
    cat = grid.catalogue

    sgmc_path = base / ".cache/external/derived_sgmc_faults_100m.tif"
    topo_path = base / ".cache/external/topo_10m_derived_100m_u8.tif"
    b15_path = base / ".cache/features/band-15.npy"

    with rasterio.open(sgmc_path) as ds:
        sgmc = (ds.read(1) > 0) & fp
    with rasterio.open(topo_path) as ds:
        slp_u8 = ds.read(1).astype(np.float32)
        rel_u8 = ds.read(5).astype(np.float32)
    depth_base = np.load(b15_path, mmap_mode="r")

    d_cat = distance_transform_edt(~cat)
    p75_rel = float(np.quantile(rel_u8[cat], 0.75))
    p80_slp = float(np.quantile(slp_u8[cat], 0.80))

    truth_cpied = (
        sgmc
        & (~cat)
        & (d_cat > 2.5)
        & (rel_u8 <= p75_rel)
        & (slp_u8 <= p80_slp)
        & np.isfinite(depth_base)
        & (depth_base >= 250.0)
    )
    return {
        "region": fp,
        "truth": truth_cpied,
        "visible": cat,
        "masked_known": cat,
        "footprint": fp,
        "p75_rel_u8": p75_rel,
        "p80_slp_u8": p80_slp,
        "n_truth": int(truth_cpied.sum()),
    }


def score_concealed_piedmont(
    predictions: dict[str, np.ndarray],
    *,
    candidate_key: str,
    fold: dict[str, Any] | None = None,
    draws: int = 1000,
    seed: int = 520810,
) -> dict[str, Any]:
    """Score one or more full-basin prediction surfaces on ``sgmc-piedmont-basin-v1``."""
    f = fold if fold is not None else build_concealed_piedmont_fold()
    fp = f["footprint"]
    terms_by_arm: dict[str, np.ndarray] = {}
    raw_by_arm: dict[str, dict[str, Any]] = {}
    for name, pred in predictions.items():
        arr = np.where(fp & np.isfinite(pred), np.clip(pred, 0.0, 1.0), 0.0).astype(np.float32)
        sc, terms = EH.evaluate(arr, f, fp)
        sc["evaluator_version"] = EVALUATOR_VERSION
        terms_by_arm[name] = terms
        raw_by_arm[name] = sc

    pooled = EH.pooled_summary(terms_by_arm, draws=draws, seed=seed, candidate=candidate_key)
    pooled["evaluator_version"] = EVALUATOR_VERSION
    for v in pooled["scores"].values():
        v["evaluator_version"] = EVALUATOR_VERSION
    for v in pooled["paired_differences"].values():
        v["evaluator_version"] = EVALUATOR_VERSION
    pooled["per_arm_exact"] = raw_by_arm
    return pooled
