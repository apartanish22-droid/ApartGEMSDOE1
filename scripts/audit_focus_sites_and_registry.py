#!/usr/bin/env python3
"""Autonomously maintain the 53-repo fleet registry index and compute C_pied benchmarks.

1. Ensures ``.cache/registry_index/`` indexes all unique submission GeoTIFFs across all
   52 peer/sibling repositories plus ``docs/downloads/archive/`` (ApartGEMSDOE1 S1 ``50e7b334``),
   strictly excluding ``data/`` input labels/samples.
2. Evaluates all 9 Focus Sites (prompt-ledger best files + 2026-10-27 independent detectors)
   and key live non-H19-5 benchmarks (GEMSDOE70 ``0.2478``, GEMSDOE76 ``0.2343``,
   GEMSDOE63 ``0.2303``, GEMSDOE27 H31 ``0.2250``, ApartGEMSDOE1 S1 ``0.0525``) on the
   zero-leaderboard-fit ``sgmc-piedmont-basin-v1`` concealed piedmont/basin benchmark
   plus crowding/spacing diagnostics, writing ``evidence/concealed_piedmont_benchmarks.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

from apartgems.piedmont_eval import EVALUATOR_VERSION as PIED_VER, build_concealed_piedmont_fold
from apartgems.uniqueness import EXCLUDE_BASENAME_SUBSTRINGS, clone_and_index_peer_fleet
from gems57 import evaluate_holdout as EH, load_grid

ROOT = Path(__file__).resolve().parents[1]
PEER_CACHE = ROOT / ".cache/peer_repos"
REG_DIR = ROOT / ".cache/registry_index"
EVIDENCE_DIR = ROOT / "evidence"

BENCHMARK_ROSTER: list[dict[str, Any]] = [
    # Focus-9 Prompt-Ledger Highs
    {
        "key": "GEMSDOE32_B2_02778",
        "site": "GEMSDOE32",
        "role": "focus_9_ledger_high",
        "path": ".cache/peer_repos/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "organizer_confirmed_score": 0.2778,
        "family": "H19-5 d=2.8 + >200m collar prune (37,654 dots; highest listed GEMSDOE site)",
    },
    {
        "key": "GEMSDOE36_PINN_02750",
        "site": "GEMSDOE36",
        "role": "focus_9_ledger_high",
        "path": ".cache/peer_repos/GEMSDOE36/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
        "organizer_confirmed_score": 0.2750,
        "family": "GEMSDOE32 B2 + 1,200 Anderson PINN dots (38,854 dots)",
    },
    {
        "key": "GEMSDOE28_H36_02710",
        "site": "GEMSDOE28",
        "role": "focus_9_ledger_high",
        "path": ".cache/peer_repos/GEMSDOE28/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif",
        "organizer_confirmed_score": 0.2710,
        "family": "H19-5 1-px prune + stepover rungs (37,660 dots)",
    },
    {
        "key": "GEMSDOE31_SOLOD28_02708",
        "site": "GEMSDOE31",
        "role": "focus_9_ledger_high",
        "path": ".cache/peer_repos/GEMSDOE31/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif",
        "organizer_confirmed_score": 0.2708,
        "family": "H19-5 + H27-4 solo d=2.8 1-px prune (40,199 dots)",
    },
    {
        "key": "GEMSDOE33_H33D_02632",
        "site": "GEMSDOE33",
        "role": "focus_9_ledger_high",
        "path": ".cache/peer_repos/GEMSDOE33/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
        "organizer_confirmed_score": 0.2632,
        "family": "H19-5 + H33D analog tip-stepover (44,120 dots)",
    },
    {
        "key": "GEMSDOE25_D28_02600",
        "site": "GEMSDOE25",
        "role": "focus_9_ledger_high",
        "path": ".cache/peer_repos/GEMSDOE25/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif",
        "organizer_confirmed_score": 0.2600,
        "family": "H19-5 thinned at d=2.8 px without 2-px collar prune (44,090 dots)",
    },
    {
        "key": "GEMSDOE30_D28_02600",
        "site": "GEMSDOE30",
        "role": "focus_9_ledger_high",
        "path": ".cache/peer_repos/GEMSDOE30/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
        "organizer_confirmed_score": 0.2600,
        "family": "Byte-identical footprint support to GEMSDOE25 D2.8 (44,090 dots)",
    },
    {
        "key": "GEMSDOE24_D15_02477",
        "site": "GEMSDOE24",
        "role": "focus_9_ledger_high",
        "path": ".cache/peer_repos/GEMSDOE24/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif",
        "organizer_confirmed_score": 0.2477,
        "family": "H19-5 thinned at d=1.5 px (60,069 dots)",
    },
    {
        "key": "GEMSDOE27_TV2_02449",
        "site": "GEMSDOE27",
        "role": "focus_9_ledger_high",
        "path": ".cache/peer_repos/GEMSDOE27/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif",
        "organizer_confirmed_score": 0.2449,
        "family": "H19-5 d=1.5 + topographic gap closure T-v2",
    },
    # Independent Non-H19-5 Live Detectors (Genuine Out-of-Fold / Multi-Physics Benchmarks)
    {
        "key": "GEMSDOE70_P8_02478",
        "site": "GEMSDOE70",
        "role": "independent_non_h19_5_live",
        "path": ".cache/peer_repos/GEMSDOE70/docs/downloads/gems70-p5-dual-submod300-oof38k-20261020.tif",
        "organizer_confirmed_score": 0.2478,
        "family": "P8 Dual-Submod300 OOF HGB (37,654 dots; highest independent non-H19-5 live detector)",
    },
    {
        "key": "GEMSDOE76_PTCF_02343",
        "site": "GEMSDOE76",
        "role": "independent_non_h19_5_live",
        "path": ".cache/peer_repos/GEMSDOE76/docs/downloads/gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d-zeros.tif",
        "organizer_confirmed_score": 0.2343,
        "family": "PTCF potential-field tilt worm + submodular 39k",
    },
    {
        "key": "GEMSDOE63_CVAR_02303",
        "site": "GEMSDOE63",
        "role": "independent_non_h19_5_live",
        "path": ".cache/peer_repos/GEMSDOE63/docs/downloads/gems63-cvar-pruned-dotted-d3p2-36057-20261011T2200Z-allfinite.tif",
        "organizer_confirmed_score": 0.2303,
        "family": "CVaR robust greedy pruned d=3.2 px (36,057 dots)",
    },
    {
        "key": "GEMSDOE27_H31_02250",
        "site": "GEMSDOE27",
        "role": "independent_non_h19_5_live",
        "path": ".cache/peer_repos/GEMSDOE27/docs/downloads/gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite.tif",
        "organizer_confirmed_score": 0.2250,
        "family": "H31 Dual-Regime LiDAR+Sub quantile-calibrated 2-stage OOF + CELF d>=2.8",
    },
    {
        "key": "GEMSDOE36_KPL36_01647",
        "site": "GEMSDOE36",
        "role": "independent_non_h19_5_live",
        "path": ".cache/peer_repos/GEMSDOE36/docs/downloads/gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif",
        "organizer_confirmed_score": 0.1647,
        "family": "KPL36 OOF HGB before S2D spacing fix (42.6% >=3-nbr crowding)",
    },
    {
        "key": "GEMSDOE36_S2D36_UNSUB",
        "site": "GEMSDOE36",
        "role": "independent_non_h19_5_candidate",
        "path": ".cache/peer_repos/GEMSDOE36/docs/downloads/gemsdoe36-s2d36-exp2-20261027-31189d084a83-zeros.tif",
        "organizer_confirmed_score": None,
        "family": "S2D36 Stage-2 directional OOF + 300 m spacing (4.5% crowding)",
    },
    {
        "key": "GEMSDOE30_MSDB1_01462",
        "site": "GEMSDOE30",
        "role": "independent_non_h19_5_live",
        "path": ".cache/peer_repos/GEMSDOE30/docs/downloads/gems30-MSDB1-edge44090-20261025-e7856ec3f14a.tif",
        "organizer_confirmed_score": 0.1462,
        "family": "MSDB-1 multi-scale boundary OOF (44,090 dots)",
    },
    {
        "key": "GEMSDOE33_S33_00963",
        "site": "GEMSDOE33",
        "role": "independent_non_h19_5_live",
        "path": ".cache/peer_repos/GEMSDOE33/docs/downloads/gemsdoe33-s33-seisdil-strain-seismicity-37654-20261026-3463540a7e02-zeros.tif",
        "organizer_confirmed_score": 0.0963,
        "family": "S33 seismogenic dilation OOF (37,654 dots)",
    },
    {
        "key": "GEMSDOE25_H66_00742",
        "site": "GEMSDOE25",
        "role": "independent_non_h19_5_live",
        "path": ".cache/peer_repos/GEMSDOE25/docs/downloads/gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif",
        "organizer_confirmed_score": 0.0742,
        "family": "H66 magnetic gradient flank detector",
    },
    {
        "key": "ApartGEMSDOE1_S1_00525",
        "site": "ApartGEMSDOE1",
        "role": "archived_session1_baseline",
        "path": "docs/downloads/archive/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif",
        "organizer_confirmed_score": 0.0525,
        "family": "Session-1 UDTH-Submod-E3 (pre-CELF-fix, 99.37% NN<=1.5px blob crowding, 75% in-sample PU)",
    },
]


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _prune_non_submission_entries_in_place(reg_dir: Path) -> dict[str, Any]:
    """Remove any input data/labels/smoke entries from cached registry_index without re-cloning."""
    mpath = reg_dir / "manifest.json"
    manifest = json.loads(mpath.read_text())
    entries = manifest["entries"]
    probe_mat = np.load(reg_dir / "probe_vals.npy")

    keep_idx: list[int] = []
    new_entries: list[dict[str, Any]] = []
    for i, e in enumerate(entries):
        rel_low = ("/" + e["rel_path"].lower() + "/")
        name_low = e["name"].lower()
        if "/data/" in rel_low or any(k in name_low for k in EXCLUDE_BASENAME_SUBSTRINGS):
            continue
        e_copy = dict(e)
        e_copy["index"] = len(new_entries)
        keep_idx.append(i)
        new_entries.append(e_copy)

    if len(keep_idx) != len(entries):
        probe_mat = probe_mat[keep_idx]
        np.save(reg_dir / "probe_vals.npy", probe_mat)
        manifest["entries"] = new_entries
        manifest["n_indexed"] = len(new_entries)
        mpath.write_text(json.dumps(manifest, indent=2))
    return manifest


def _crowding_stats(arr: np.ndarray, d_cat: np.ndarray, lidar_valid: np.ndarray) -> dict[str, Any]:
    ys, xs = np.nonzero(arr > 0.5)
    n = int(ys.size)
    if n == 0:
        return {"n_dots": 0}
    pts = np.column_stack([ys, xs]).astype(np.float64)
    tree = cKDTree(pts)
    dists, _ = tree.query(pts, k=min(3, n))
    nn1 = dists[:, 1] if n > 1 else np.full(n, 999.0)
    nbrs_3px = np.array([len(v) - 1 for v in tree.query_ball_point(pts, r=3.000001)], dtype=np.float64)
    dc = d_cat[ys, xs]
    lv = lidar_valid[ys, xs]
    return {
        "n_dots": n,
        "min_nn_px": round(float(np.min(nn1)), 4),
        "median_nn_px": round(float(np.median(nn1)), 4),
        "frac_nn_le_1_5px": round(float(np.mean(nn1 <= 1.5001)), 5),
        "frac_nn_lt_2_8px": round(float(np.mean(nn1 < 2.7999)), 5),
        "frac_ge3_neighbors_in_3px": round(float(np.mean(nbrs_3px >= 3)), 5),
        "mean_neighbors_in_3px": round(float(np.mean(nbrs_3px)), 4),
        "frac_in_lidar": round(float(np.mean(lv)), 5),
        "frac_gt_1500m_farfield": round(float(np.mean(dc > 15.0)), 5),
        "frac_le_200m_collar": round(float(np.mean(dc <= 2.0)), 5),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh-registry", action="store_true")
    args = ap.parse_args()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    if args.refresh_registry or not (REG_DIR / "manifest.json").exists():
        reg_manifest = clone_and_index_peer_fleet(
            PEER_CACHE, REG_DIR, local_archive_dirs=[ROOT / "docs/downloads/archive"]
        )
    else:
        reg_manifest = _prune_non_submission_entries_in_place(REG_DIR)

    print(f"Verified fleet registry index: {reg_manifest['n_indexed']} unique submission rasters across {reg_manifest.get('n_repos_scanned', 53)} repos.", flush=True)

    grid = load_grid()
    fp, cat = grid.footprint, grid.catalogue
    d_cat = distance_transform_edt(~cat)
    with rasterio.open(ROOT / ".cache/external/lidar_scarp_features_u8.tif") as ds:
        lidar_valid = (ds.read(12) > 0) & fp

    cpied_fold = build_concealed_piedmont_fold(ROOT)
    terms_cpied: dict[str, np.ndarray] = {}
    rows: list[dict[str, Any]] = []

    for spec in BENCHMARK_ROSTER:
        p = ROOT / spec["path"]
        if not p.exists():
            print(f"  [WARN] Missing {p}", flush=True)
            continue
        with rasterio.open(p) as ds:
            raw = ds.read(1).astype(np.float32)
        eval_arr = np.where(np.isfinite(raw) & fp, np.clip(raw, 0.0, 1.0), 0.0).astype(np.float32)
        _, t_cp = EH.evaluate(eval_arr, cpied_fold, fp)
        terms_cpied[spec["key"]] = t_cp
        crowd = _crowding_stats(eval_arr, d_cat, lidar_valid)
        rows.append(
            {
                "key": spec["key"],
                "site": spec["site"],
                "role": spec["role"],
                "file": p.name,
                "sha256": _sha256(p),
                "organizer_confirmed_score": spec["organizer_confirmed_score"],
                "score_label": (
                    "ORGANIZER-CONFIRMED (prompt ledger)"
                    if spec["organizer_confirmed_score"] is not None
                    else "UNSUBMITTED"
                ),
                "family": spec["family"],
                "geometry": crowd,
            }
        )

    pooled = EH.pooled_summary(terms_cpied, draws=1000, seed=520810, candidate="GEMSDOE32_B2_02778")
    live_pairs_x: list[float] = []
    live_pairs_y: list[float] = []
    for r in rows:
        sc = pooled["scores"][r["key"]]
        r["concealed_piedmont_dti"] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": PIED_VER,
            "dti": round(sc["dti"], 6),
            "ci95": [round(x, 6) for x in sc["ci95"]],
            "withheld_positive_pixels": sc["withheld_positive_pixels"],
        }
        if r["organizer_confirmed_score"] is not None:
            live_pairs_x.append(sc["dti"])
            live_pairs_y.append(float(r["organizer_confirmed_score"]))

    from scipy.stats import spearmanr
    rho_cal, p_cal = spearmanr(live_pairs_x, live_pairs_y)

    out = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": PIED_VER,
        "concealed_piedmont_positive_pixels": cpied_fold["n_truth"],
        "registry_summary": {
            "n_indexed_unique_submission_rasters": reg_manifest["n_indexed"],
            "n_repos_scanned": reg_manifest.get("n_repos_scanned", 53),
            "spearman_cap": reg_manifest["spearman_cap"],
            "overlap_3px_cap": reg_manifest["overlap_3px_cap"],
        },
        "instrument_calibration_spearman_vs_live": {
            "n_live_submissions": len(live_pairs_x),
            "spearman_rho": round(float(rho_cal), 5),
            "p_value": float(p_cal),
        },
        "benchmarks": rows,
    }
    out_path = EVIDENCE_DIR / "concealed_piedmont_benchmarks.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Instrument calibration across {len(live_pairs_x)} live scores: Spearman rho = {rho_cal:+.4f} (p={p_cal:.2e})", flush=True)
    for r in rows:
        cp_v = r["concealed_piedmont_dti"]["dti"]
        lv = r["organizer_confirmed_score"]
        lv_s = f"{lv:.4f}" if lv is not None else "  N/A "
        g = r["geometry"]
        print(
            f"  {r['key']:25s} | live={lv_s} | C_pied={cp_v:.4f} | dots={g['n_dots']:6d} | "
            f"crowd>=3={g['frac_ge3_neighbors_in_3px']*100:5.1f}% | far={g['frac_gt_1500m_farfield']*100:5.1f}%"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
