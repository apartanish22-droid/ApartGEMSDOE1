#!/usr/bin/env python3
"""Fast, low-memory pixel-exact audit of Focus-9 GEMSDOE sites + Fleet Uniqueness Registry builder."""
from __future__ import annotations

from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

from gems57 import evaluate_holdout as EH
from gems57 import load_grid
from gems57.holdout import buffered_component_draw
from gems57.metric import OFF_DX, OFF_DY

RESEARCH_DIR = Path("/tmp/research")
CACHE_REG = ROOT / ".cache/registry_index"

FOCUS_9_SPECS = [
    {
        "site": "GEMSDOE32",
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE32",
        "submission_id": "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros",
        "tif_rel": "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "download_url": "https://buffedlizard55-lab.github.io/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "user_reported_score": 0.2778,
        "latest_20261027_rel": "docs/downloads/gemsdoe32-H-GEO-VENT-28000-20261027T174146Z-3c5837e9-zeros.tif",
        "method_summary": "H19-5 4-pillar multi-physics ridge network thinned at d=2.8 px (44,090 dots) minus 6,436 dots within <=200 m (2 px) of mapped catalogue faults (37,654 dots, all-finite zeros).",
    },
    {
        "site": "GEMSDOE36",
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE36/docs/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE36",
        "submission_id": "anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros",
        "tif_rel": "docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
        "download_url": "https://buffedlizard55-lab.github.io/GEMSDOE36/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
        "user_reported_score": 0.2750,
        "latest_20261027_rel": "docs/downloads/gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif",
        "method_summary": "GEMSDOE32 B2 (37,654 dots) augmented with +1,200 Andersonian normal-fault geothermal PINN dots (38,854 total; 97.58% 3-px overlap with B2/D2.8). Later KPL36 scored 0.1647 user-reported.",
    },
    {
        "site": "GEMSDOE28",
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE28/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE28",
        "submission_id": "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan",
        "tif_rel": "docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
        "download_url": "https://buffedlizard55-lab.github.io/GEMSDOE28/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
        "user_reported_score": 0.2710,
        "latest_20261027_rel": "docs/downloads/gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite.tif",
        "method_summary": "D2.8 dotted H19-5 pruned by r=1px collar + blind step-over rung additions (37,660 dots, NaN outside). Later S18 (0.0217) & S21 PU-HGB (0.0206) over-concentrated near known faults.",
    },
    {
        "site": "GEMSDOE31",
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE31/docs/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE31",
        "submission_id": "h27-4-solo-d28-20261004-8acb75e1-nan",
        "tif_rel": "docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
        "download_url": "https://buffedlizard55-lab.github.io/GEMSDOE31/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
        "user_reported_score": 0.2708,
        "latest_20261027_rel": "docs/downloads/gems31-xfcoh31-xfield-coherence-37654-20261026-zeros.tif",
        "method_summary": "D2.8 dotted H19-5 with isolated solo/1-px near-catalogue dots pruned (40,199 dots, pixel-identical dot set to GEMSDOE28 h27-4-r1-solo-d2-8; NaN outside).",
    },
    {
        "site": "GEMSDOE33",
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE33/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE33",
        "submission_id": "h33d-analog-tip-stepover-r30-20261004-cb490425926e",
        "tif_rel": "docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
        "download_url": "https://buffedlizard55-lab.github.io/GEMSDOE33/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
        "user_reported_score": 0.2632,
        "latest_20261027_rel": "docs/downloads/gemsdoe33-s33-seisdil-strain-seismicity-37654-20261026-3463540a7e02-zeros.tif",
        "method_summary": "D2.8 lineage with analog fault-tip & step-over r=30 additions. Later S33-SEISDIL strain/seismicity standalone scored 0.0963 user-reported.",
    },
    {
        "site": "GEMSDOE25",
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE25/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE25",
        "submission_id": "dotted-h19-5-d2-8-20261002-e56ea318af89-nan",
        "tif_rel": "docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "download_url": "https://buffedlizard55-lab.github.io/GEMSDOE25/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "user_reported_score": 0.2600,
        "latest_20261027_rel": "docs/downloads/gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif",
        "method_summary": "Parent D2.8 Poisson-disk thinning (d=2.8 px = 280 m) of 19GEMSDOE H19-5 ridges (44,090 dots; 100% pixel-identical dot set to GEMSDOE30). Later H66 scored 0.0742.",
    },
    {
        "site": "GEMSDOE30",
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE30/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE30",
        "submission_id": "d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca",
        "tif_rel": "docs/downloads/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "download_url": "https://buffedlizard55-lab.github.io/GEMSDOE30/docs/downloads/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "user_reported_score": 0.2600,
        "latest_20261027_rel": "docs/downloads/gems30-CSR1-44090-20261026-502fb5948335-zeros.tif",
        "method_summary": "Exact duplicate dot array (44,090 dots) of GEMSDOE25 D2.8 (0.2600 user-reported). Later MSDB1 edge-44090 scored 0.1462 user-reported.",
    },
    {
        "site": "GEMSDOE24",
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE24/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE24",
        "submission_id": "h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan",
        "tif_rel": "docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        "download_url": "https://buffedlizard55-lab.github.io/GEMSDOE24/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        "user_reported_score": 0.2477,
        "latest_20261027_rel": "docs/downloads/gems24-gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-zeros.tif",
        "method_summary": "First dotted thinning of H19-5 at d=1.5 px (60,069 dots; jumped +0.0555 over solid H19-5 0.1922 by cutting redundant kernel overlap). Later GVC1 scored 0.0859.",
    },
    {
        "site": "GEMSDOE27",
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE27/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE27",
        "submission_id": "topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan",
        "tif_rel": "docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
        "download_url": "https://buffedlizard55-lab.github.io/GEMSDOE27/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
        "user_reported_score": 0.2449,
        "latest_20261027_rel": "docs/downloads/gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite.tif",
        "method_summary": "D1.5 dotted H19-5 + 1,259 topographic gap-closure pixels (61,328 dots). Later genuine non-H19-5 architecture H31-1 DRCG-WL CELF scored 0.2250 user-reported.",
    },
]

EXCLUDE_SUBSTRINGS = (
    "training_features",
    "numerical-features",
    "existing_faults",
    "labels.tif",
    "sample_submission",
    "example_submission",
    "geodawn_",
    "lidar_scarp",
    "sgmc_",
    "tiger_road",
    "acquisition_block",
    "blm_closed",
    "format_test",
)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fast_near_3px(pos_mask: np.ndarray) -> np.ndarray:
    """Exact <= 3.0 px Euclidean dilation using the 37 integer offsets with dy^2+dx^2 <= 9."""
    H, W = pos_mask.shape
    out = np.zeros((H, W), dtype=bool)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dy * dy + dx * dx > 9:
                continue
            ys0, ys1 = max(0, dy), min(H, H + dy)
            xs0, xs1 = max(0, dx), min(W, W + dx)
            out[ys0:ys1, xs0:xs1] |= pos_mask[max(0, -dy) : min(H, H - dy), max(0, -dx) : min(W, W - dx)]
    return out


def find_focus_tif(repo_dir: Path, preferred_rel: str, sub_id: str) -> Path | None:
    cand = repo_dir / preferred_rel
    if cand.exists():
        return cand
    key = sub_id.split("-2026")[0]
    matches = [p for p in repo_dir.rglob("*.tif") if key in p.name]
    if matches:
        return sorted(matches)[0]
    return None


def main() -> int:
    t0 = time.time()
    grid = load_grid()
    fp = grid.footprint
    cat = grid.catalogue
    n_fp = int(fp.sum())
    edt_cat = distance_transform_edt(~cat).astype(np.float32)
    folds, _ = buffered_component_draw(grid, seed=2026, hide_frac=0.20, buffer_px=3)

    # Clear partial cache from prior run to ensure consistent schema
    CACHE_REG.mkdir(parents=True, exist_ok=True)
    for old_f in CACHE_REG.glob("*.npz"):
        old_f.unlink()

    focus_dots: dict[str, np.ndarray] = {}
    focus_halos: dict[str, np.ndarray] = {}
    focus_ranks: dict[str, np.ndarray] = {}
    focus_rows = []
    block_terms_by_site = {}

    fp_idx = np.flatnonzero(fp.ravel())
    rng = np.random.default_rng(20261027)
    sample_sub = np.sort(rng.choice(len(fp_idx), size=200_000, replace=False))
    fp_sample_flat = fp_idx[sample_sub]

    print(f"[1/4] Auditing Focus-9 sites ({time.time()-t0:.1f}s)...", flush=True)
    for spec in FOCUS_9_SPECS:
        repo_dir = RESEARCH_DIR / spec["site"]
        tif_path = find_focus_tif(repo_dir, spec["tif_rel"], spec["submission_id"])
        if tif_path is None:
            raise FileNotFoundError(f"Could not find focus TIF for {spec['site']}")
        with rasterio.open(tif_path) as src:
            arr = src.read(1)
            crs_ok = str(src.crs) == "EPSG:32611"
            shape_ok = (src.height, src.width) == grid.shape
            tr_ok = tuple(src.transform)[:6] == tuple(grid.transform)[:6]

        finite_all = bool(np.isfinite(arr).all())
        finite_fp = bool(np.isfinite(arr[fp]).all())
        n_nan_total = int(np.isnan(arr).sum())
        clean = np.where(np.isfinite(arr) & fp, np.clip(arr, 0.0, 1.0), 0.0).astype(np.float32)
        dots = clean > 0
        focus_dots[spec["site"]] = dots
        focus_halos[spec["site"]] = fast_near_3px(dots)
        r_vec = rankdata(clean.ravel()[fp_sample_flat]).astype(np.float32)
        r_vec -= r_vec.mean()
        norm = float(np.linalg.norm(r_vec))
        focus_ranks[spec["site"]] = r_vec / (norm if norm > 0 else 1.0)

        terms = sum(EH.evaluate(clean.astype(np.float64), f, fp)[1] for f in folds)
        block_terms_by_site[spec["site"]] = terms

        latest_info = None
        lat_p = repo_dir / spec["latest_20261027_rel"]
        if lat_p.exists():
            with rasterio.open(lat_p) as lsrc:
                larr = lsrc.read(1)
            lclean = np.where(np.isfinite(larr) & fp, np.clip(larr, 0.0, 1.0), 0.0).astype(np.float32)
            lterms = sum(EH.evaluate(lclean.astype(np.float64), f, fp)[1] for f in folds)
            block_terms_by_site[f"{spec['site']}_latest"] = lterms
            latest_info = {
                "file": lat_p.name,
                "sha256": sha256_file(lat_p),
                "dots": int((lclean > 0).sum()),
                "all_finite_0_1": bool(np.isfinite(larr).all() and (larr >= 0).all() and (larr <= 1).all()),
            }
            del larr, lclean

        focus_rows.append({
            **spec,
            "local_verified_file": tif_path.name,
            "file_sha256": sha256_file(tif_path),
            "decoded_fp_sha256": sha256_bytes(clean[fp].tobytes()),
            "dots": int(dots.sum()),
            "dots_on_catalogue": int((dots & cat).sum()),
            "dots_within_200m_collar": int((dots & (edt_cat <= 2.0)).sum()),
            "dots_beyond_1500m_farfield": int((dots & (edt_cat > 15.0)).sum()),
            "farfield_fraction": float((dots & (edt_cat > 15.0)).sum() / max(int(dots.sum()), 1)),
            "crs_shape_transform_ok": bool(crs_ok and shape_ok and tr_ok),
            "in_footprint_finite_0_1": bool(finite_fp and (clean[fp].min() >= 0.0) and (clean[fp].max() <= 1.0)),
            "all_grid_finite_no_nan": finite_all,
            "exterior_nan_pixels": n_nan_total,
            "portal_nan_range_risk": bool(not finite_all),
            "latest_20261027_candidate": latest_info,
        })
        del arr, clean
        gc.collect()

    print(f"[2/4] Computing holdout & pairwise Focus-9 matrix ({time.time()-t0:.1f}s)...", flush=True)
    zero_terms = sum(EH.evaluate(np.zeros(grid.shape, np.float64), f, fp)[1] for f in folds)
    block_terms_by_site["zero_control"] = zero_terms
    holdout_summary = EH.pooled_summary(block_terms_by_site, candidate="GEMSDOE32")

    sites = [r["site"] for r in focus_rows]
    pairwise_overlap = {}
    pairwise_spearman = {}
    for s1 in sites:
        pairwise_overlap[s1] = {}
        pairwise_spearman[s1] = {}
        m1 = focus_dots[s1]
        for s2 in sites:
            if s1 == s2:
                pairwise_overlap[s1][s2] = 1.0
                pairwise_spearman[s1][s2] = 1.0
            else:
                ov = float(focus_halos[s2][m1].mean())
                rho = float(np.dot(focus_ranks[s1], focus_ranks[s2]))
                pairwise_overlap[s1][s2] = round(ov, 6)
                pairwise_spearman[s1][s2] = round(rho, 6)

    for row in focus_rows:
        s = row["site"]
        others = [o for o in sites if o != s]
        max_ov_site = max(others, key=lambda o: pairwise_overlap[s][o])
        max_ov = pairwise_overlap[s][max_ov_site]
        exact_dups = [o for o in others if focus_rows[sites.index(o)]["decoded_fp_sha256"] == row["decoded_fp_sha256"]]
        hs = holdout_summary["scores"][s]
        row["static_holdout_dti"] = {
            "label": "HOLDOUT-DTI",
            "evaluator_version": hs["evaluator_version"],
            "dti": hs["dti"],
            "ci95": hs["ci95"],
            "withheld_positive_pixels": hs["withheld_positive_pixels"],
            "note": "Static post-masked file evaluated directly: files that already collared out full-catalogue pixels erase predictions on withheld catalogue segments.",
        }
        if row["latest_20261027_candidate"] is not None:
            lhs = holdout_summary["scores"][f"{s}_latest"]
            row["latest_20261027_candidate"]["static_holdout_dti"] = {
                "label": "HOLDOUT-DTI",
                "evaluator_version": lhs["evaluator_version"],
                "dti": lhs["dti"],
                "ci95": lhs["ci95"],
                "withheld_positive_pixels": lhs["withheld_positive_pixels"],
            }
        row["max_3px_overlap_vs_other_focus9"] = max_ov
        row["max_overlap_peer_site"] = max_ov_site
        row["exact_footprint_duplicates_in_focus9"] = exact_dups
        row["unique_among_focus9"] = bool(max_ov <= 0.70 and len(exact_dups) == 0)
        row["ok_to_resubmit_as_new"] = False
        row["disposition_reason"] = (
            f"DO NOT RESUBMIT: Already submitted historical H19-5 lineage artifact "
            f"(max 3-px overlap = {max_ov*100:.2f}% with {max_ov_site} > 70% limit"
            + (f"; 100% pixel-identical to {exact_dups}" if exact_dups else "")
            + "). Retained strictly for forensic learning & benchmark comparison."
        )

    print(f"[3/4] Verifying zero-XOR proof of GEMSDOE32 0.2778 ({time.time()-t0:.1f}s)...", flush=True)
    d28_dots = focus_dots["GEMSDOE25"]
    b2_dots = focus_dots["GEMSDOE32"]
    b2_formula = d28_dots & (edt_cat > 2.0)
    xor_b2_vs_formula = int(np.logical_xor(b2_dots, b2_formula).sum())
    xor_25_vs_30 = int(np.logical_xor(focus_dots["GEMSDOE25"], focus_dots["GEMSDOE30"]).sum())

    h19_5_info = None
    h19_5_path = RESEARCH_DIR / "19GEMSDOE/docs/downloads/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif"
    if h19_5_path.exists():
        with rasterio.open(h19_5_path) as s19:
            a19 = s19.read(1)
        m19 = np.isfinite(a19) & (a19 > 0) & fp
        h19_5_info = {
            "file": h19_5_path.name,
            "sha256": sha256_file(h19_5_path),
            "dots": int(m19.sum()),
            "b2_subset_of_h19_5_3px_halo": float(fast_near_3px(m19)[b2_dots].mean()),
            "b2_exact_subset_of_h19_5": float((b2_dots & m19).sum() / max(int(b2_dots.sum()), 1)),
        }
        del a19, m19

    forensic_02778 = {
        "evidence_class": "PIXEL-EXACT-BYTE-MEASUREMENT",
        "target_site": "GEMSDOE32",
        "target_submission": "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros",
        "user_reported_score": 0.2778,
        "score_label": "USER-REPORTED (prompt ledger; no organizer portal receipt file in repo)",
        "parent_site": "GEMSDOE25",
        "parent_submission": "dotted-h19-5-d2-8-20261002-e56ea318af89-nan",
        "parent_user_reported_score": 0.2600,
        "parent_dots": int(d28_dots.sum()),
        "b2_dots": int(b2_dots.sum()),
        "removed_collar_dots": int(d28_dots.sum() - b2_dots.sum()),
        "exact_boolean_identity": "GEMSDOE32_B2 == GEMSDOE25_D28 & (EDT(~existing_faults) > 2.0)",
        "xor_differing_pixels_across_5167373_footprint": xor_b2_vs_formula,
        "xor_gemsdoe25_vs_gemsdoe30": xor_25_vs_30,
        "h19_5_root_parent": h19_5_info,
        "score_ladder_progression": [
            {"stage": "19GEMSDOE H19-5 (solid ridges)", "dots": 121131, "user_reported": 0.1922, "mechanism": "4-pillar physical synthesis (power-law tips + GDR1391 thermal + 1m/10m openness/LRM + geopotential worms)"},
            {"stage": "GEMSDOE24 D1.5 (d=1.5 px thin)", "dots": 60069, "user_reported": 0.2477, "mechanism": "150 m spacing cuts redundant max-kernel overlap by 50.4%, slashing 0.2*FP_w"},
            {"stage": "GEMSDOE25 / GEMSDOE30 D2.8 (d=2.8 px thin)", "dots": 44090, "user_reported": 0.2600, "mechanism": "280 m spacing matches R=300 m kernel diameter, cutting another 15,979 redundant dots"},
            {"stage": "GEMSDOE31 Solo-D28 (1-px collar prune)", "dots": 40199, "user_reported": 0.2708, "mechanism": "Removes 3,891 dots adjacent (d=1 px) to already-mapped faults"},
            {"stage": "GEMSDOE28 H36-1 (1-px prune + blind rungs)", "dots": 37660, "user_reported": 0.2710, "mechanism": "Further trims near-catalogue FP dots + step-over rungs"},
            {"stage": "GEMSDOE36 Anderson-PINN (+1,200 dots on B2)", "dots": 38854, "user_reported": 0.2750, "mechanism": "B2 + 1,200 PINN dots (marginal precision of extra 1,200 dots slightly below 0.2778 break-even)"},
            {"stage": "GEMSDOE32 H33-2-B2 (2-px = 200 m collar amputation, all-finite zeros)", "dots": 37654, "user_reported": 0.2778, "mechanism": "Removes all 6,436 D2.8 dots within <=200 m of existing_faults.tif (zero XOR residual), eliminating near-catalogue FP halo"},
        ],
    }

    del focus_dots, focus_halos, focus_ranks
    gc.collect()

    print(f"[4/4] Scanning peer repositories in /tmp/research for Fleet Uniqueness Registry ({time.time()-t0:.1f}s)...", flush=True)
    seen_fp_hashes: dict[str, dict] = {}
    seen_file_hashes: set[str] = set()
    total_tif_scanned = 0

    for repo_path in sorted(RESEARCH_DIR.iterdir()):
        if not repo_path.is_dir():
            continue
        repo_name = repo_path.name
        for tif in sorted(repo_path.rglob("*.tif")):
            rel_str = str(tif.relative_to(repo_path))
            low = rel_str.lower()
            if any(ex in low for ex in EXCLUDE_SUBSTRINGS):
                continue
            if tif.stat().st_size > 25_000_000:
                continue
            fhash = sha256_file(tif)
            if fhash in seen_file_hashes:
                continue
            seen_file_hashes.add(fhash)
            try:
                with rasterio.open(tif) as ds:
                    if ds.count != 1 or (ds.height, ds.width) != grid.shape:
                        continue
                    a = ds.read(1)
            except Exception:
                continue
            total_tif_scanned += 1
            vals = np.where(np.isfinite(a) & fp, a, 0.0).astype(np.float32)
            del a
            pos = vals > 0
            n_pos = int(pos.sum())
            if n_pos == 0:
                del vals, pos
                continue
            fp_hash = sha256_bytes(vals[fp].tobytes())
            if fp_hash in seen_fp_hashes:
                seen_fp_hashes[fp_hash]["aliases"].append(f"{repo_name}:{rel_str}")
                del vals, pos
                continue

            near_mask = fast_near_3px(pos) & fp
            halo_cov = float(near_mask.sum() / n_fp)
            del near_mask
            is_blanket = bool(halo_cov >= 0.70 or n_pos >= 500_000)

            vals_sub = vals.ravel()[fp_sample_flat].astype(np.float32)
            # Preserve *all* positive pixels and footprint values. A top-K
            # surrogate cannot implement the protocol's any-raster overlap rule.
            pos_flat = np.flatnonzero(pos.ravel()).astype(np.int32)
            vals_fp = vals[fp].astype(np.float32)
            npz_path = CACHE_REG / f"{fp_hash[:20]}.npz"
            np.savez_compressed(npz_path, pos_flat=pos_flat, vals_fp=vals_fp)

            seen_fp_hashes[fp_hash] = {
                "decoded_fp_sha256": fp_hash,
                "file_sha256": fhash,
                "primary_repo": repo_name,
                "primary_rel": rel_str,
                "positive_pixels": n_pos,
                "halo_3px_footprint_coverage": round(halo_cov, 6),
                "is_blanket_or_continuous_surface": is_blanket,
                "cache_npz": npz_path.name,
                "full_support_and_ranks": True,
                "aliases": [],
            }
            del vals, pos
        print(f"  scanned {repo_name:24s} -> unique_rasters={len(seen_fp_hashes)} ({time.time()-t0:.1f}s)", flush=True)

    registry_manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "REGISTRY-MEASUREMENT",
        "repos_scanned": sorted([p.name for p in RESEARCH_DIR.iterdir() if p.is_dir()]),
        "total_valid_grid_tifs_scanned": total_tif_scanned,
        "unique_decoded_rasters": len(seen_fp_hashes),
        "competing_sparse_detectors": sum(1 for v in seen_fp_hashes.values() if not v["is_blanket_or_continuous_surface"]),
        "blanket_or_continuous_rasters": sum(1 for v in seen_fp_hashes.values() if v["is_blanket_or_continuous_surface"]),
        "sample_sub_indices_seed": 20261027,
        "sample_sub_size": int(len(fp_sample_flat)),
        "entries": list(seen_fp_hashes.values()),
    }
    np.save(CACHE_REG / "fp_sample_flat.npy", fp_sample_flat)
    (CACHE_REG / "registry_manifest.json").write_text(json.dumps(registry_manifest, indent=2) + "\n")

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "PIXEL-EXACT-FOCUS9-AND-REGISTRY-AUDIT",
        "forensic_proof_02778": forensic_02778,
        "focus_9_sites": focus_rows,
        "focus_9_pairwise_3px_overlap": pairwise_overlap,
        "focus_9_pairwise_spearman": pairwise_spearman,
        "fleet_registry_summary": {
            "repos_scanned": registry_manifest["repos_scanned"],
            "total_valid_grid_tifs_scanned": total_tif_scanned,
            "unique_decoded_rasters": registry_manifest["unique_decoded_rasters"],
            "competing_sparse_detectors": registry_manifest["competing_sparse_detectors"],
            "blanket_or_continuous_rasters": registry_manifest["blanket_or_continuous_rasters"],
        },
    }
    (ROOT / "evidence/focus_sites_forensic_audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (ROOT / "docs/data/focus_sites_forensic_audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"[DONE in {time.time()-t0:.1f}s] XOR(B2, D2.8 & d>2)={xor_b2_vs_formula}, XOR(25,30)={xor_25_vs_30}, unique_rasters={len(seen_fp_hashes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
