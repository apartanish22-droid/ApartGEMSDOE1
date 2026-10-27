"""Automated Dual Uniqueness Gate against the 22-repo / 352-raster Fleet Registry.

Enforces Parallel-Run Protocol Rule 1 automatically in code:
  1. Pre-placement continuous surface check: |Spearman rho| <= 0.90 vs every registry raster.
  2. Post-placement final dot check:
     - |Spearman rho| <= 0.90 vs every registry raster, AND
     - <= 0.70 fraction of emitted dots within 3 px (300 m) of any competing sparse detector's dots
       (plus matched-budget top-K 3-px overlap <= 0.70 against the 10 blanket/continuous surfaces,
        with raw `a > 0` blanket witnesses disclosed transparently per IR-REG-BLANKET).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
CACHE_REG = ROOT / ".cache/registry_index"


def fast_near_3px(pos_mask: np.ndarray) -> np.ndarray:
    """Exact <= 3.0 px Euclidean dilation (37 integer offsets with dy^2+dx^2 <= 9)."""
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


def _unit_rank_vec(v: np.ndarray) -> np.ndarray:
    r = rankdata(v).astype(np.float64)
    r -= r.mean()
    n = float(np.linalg.norm(r))
    return (r / n) if n > 0 else np.zeros_like(r)


def check_surface_uniqueness(
    surface: np.ndarray,
    footprint: np.ndarray,
    spearman_cap: float = 0.90,
) -> dict:
    """Pre-placement continuous probability surface uniqueness gate across all 352 registry rasters."""
    manifest_p = CACHE_REG / "registry_manifest.json"
    if not manifest_p.exists():
        raise FileNotFoundError("Missing .cache/registry_index/registry_manifest.json; run audit_focus_sites_and_registry.py")
    manifest = json.loads(manifest_p.read_text())
    fp_sample_flat = np.load(CACHE_REG / "fp_sample_flat.npy")

    surf_clean = np.where(footprint & np.isfinite(surface), surface, 0.0).astype(np.float32)
    r_cand = _unit_rank_vec(surf_clean.ravel()[fp_sample_flat])

    max_abs_rho = 0.0
    worst_entry = None
    top_matches = []
    for entry in manifest["entries"]:
        d = np.load(CACHE_REG / entry["cache_npz"])
        r_ref = _unit_rank_vec(d["vals_sub"])
        rho = float(np.dot(r_cand, r_ref))
        abs_rho = abs(rho)
        rec = {
            "repo": entry["primary_repo"],
            "file": entry["primary_rel"],
            "spearman_rho": round(rho, 6),
            "abs_spearman_rho": round(abs_rho, 6),
            "is_blanket": entry["is_blanket_or_continuous_surface"],
        }
        top_matches.append(rec)
        if abs_rho > max_abs_rho:
            max_abs_rho = abs_rho
            worst_entry = rec

    top_matches.sort(key=lambda x: x["abs_spearman_rho"], reverse=True)
    passed = bool(max_abs_rho <= spearman_cap)
    return {
        "gate": "PRE_PLACEMENT_CONTINUOUS_SURFACE",
        "evidence_class": "REGISTRY-UNIQUENESS-GATE",
        "rasters_checked": len(manifest["entries"]),
        "spearman_abs_cap": spearman_cap,
        "max_abs_spearman_rho": round(max_abs_rho, 6),
        "closest_registry_raster": worst_entry,
        "top_5_correlations": top_matches[:5],
        "passed": passed,
    }


def check_final_raster_uniqueness(
    final_raster: np.ndarray,
    footprint: np.ndarray,
    spearman_cap: float = 0.90,
    overlap_cap: float = 0.70,
) -> dict:
    """Post-placement final raster uniqueness gate (Spearman + 3-px dot overlap across 352 rasters)."""
    manifest = json.loads((CACHE_REG / "registry_manifest.json").read_text())
    fp_sample_flat = np.load(CACHE_REG / "fp_sample_flat.npy")
    H, W = final_raster.shape

    clean = np.where(footprint & np.isfinite(final_raster), np.clip(final_raster, 0.0, 1.0), 0.0).astype(np.float32)
    fp_hash = hashlib.sha256(clean[footprint].tobytes()).hexdigest()
    cand_dots = clean > 0
    n_cand = int(cand_dots.sum())
    if n_cand == 0:
        raise ValueError("Candidate final raster has zero positive pixels!")

    r_cand = _unit_rank_vec(clean.ravel()[fp_sample_flat])

    max_abs_rho = 0.0
    worst_rho_entry = None
    max_sparse_overlap = 0.0
    worst_sparse_entry = None
    max_blanket_matched_overlap = 0.0
    blanket_disclosures = []
    exact_hash_collision = None
    top_sparse = []
    focus_site_comparisons = {}

    focus_audit_p = ROOT / "evidence/focus_sites_forensic_audit.json"
    focus_hash_to_site = {}
    if focus_audit_p.exists():
        fa = json.loads(focus_audit_p.read_text())
        for r in fa["focus_9_sites"]:
            focus_hash_to_site.setdefault(r["decoded_fp_sha256"], []).append(r["site"])

    for entry in manifest["entries"]:
        if entry["decoded_fp_sha256"] == fp_hash:
            exact_hash_collision = f"{entry['primary_repo']}:{entry['primary_rel']}"
        d = np.load(CACHE_REG / entry["cache_npz"])
        r_ref = _unit_rank_vec(d["vals_sub"])
        rho = float(np.dot(r_cand, r_ref))
        abs_rho = abs(rho)
        if abs_rho > max_abs_rho:
            max_abs_rho = abs_rho
            worst_rho_entry = {
                "repo": entry["primary_repo"],
                "file": entry["primary_rel"],
                "spearman_rho": round(rho, 6),
                "abs_spearman_rho": round(abs_rho, 6),
            }

        ref_mask = np.zeros(H * W, dtype=bool)
        ref_mask[d["pos_flat"]] = True
        ref_halo = fast_near_3px(ref_mask.reshape(H, W))
        ov = float(ref_halo[cand_dots].mean())

        if entry["is_blanket_or_continuous_surface"]:
            # Distinguish continuous float surfaces (positive_pixels > 600k, pos_flat holds top-50k ranked crests)
            # from constant-value (val == 1.0) uniform calibration lattices (e.g. r13-lattice-s5 covering 99.87%
            # of the footprint with zero positive value variation, so top-50k ranking is undefined).
            v_pos_sub = d["vals_sub"][d["vals_sub"] > 0]
            has_pos_var = bool(v_pos_sub.size > 1 and float(v_pos_sub.max() - v_pos_sub.min()) > 1e-6)
            if entry["positive_pixels"] > 600_000 or has_pos_var:
                max_blanket_matched_overlap = max(max_blanket_matched_overlap, ov)
                b_kind = "continuous_soft_surface_top50k_checked"
            else:
                b_kind = "constant_value_uniform_lattice_blanket_disclosed"
            blanket_disclosures.append({
                "repo": entry["primary_repo"],
                "file": entry["primary_rel"],
                "blanket_type": b_kind,
                "positive_pixels": entry["positive_pixels"],
                "halo_3px_footprint_coverage": entry["halo_3px_footprint_coverage"],
                "top50k_or_raw_overlap": round(ov, 6),
                "raw_a_gt_0_halo_coverage_witness": entry["halo_3px_footprint_coverage"],
                "spearman_rho": round(rho, 6),
            })
        else:
            rec = {
                "repo": entry["primary_repo"],
                "file": entry["primary_rel"],
                "positive_pixels": entry["positive_pixels"],
                "overlap_3px_fraction": round(ov, 6),
                "spearman_rho": round(rho, 6),
            }
            top_sparse.append(rec)
            if ov > max_sparse_overlap:
                max_sparse_overlap = ov
                worst_sparse_entry = rec

        if entry["decoded_fp_sha256"] in focus_hash_to_site:
            for site_name in focus_hash_to_site[entry["decoded_fp_sha256"]]:
                focus_site_comparisons[site_name] = {
                    "overlap_3px_fraction": round(ov, 6),
                    "spearman_rho": round(rho, 6),
                    "peer_dots": entry["positive_pixels"],
                    "peer_file": entry["primary_rel"],
                }

    top_sparse.sort(key=lambda x: x["overlap_3px_fraction"], reverse=True)
    passed = bool(
        exact_hash_collision is None
        and max_abs_rho <= spearman_cap
        and max_sparse_overlap <= overlap_cap
        and max_blanket_matched_overlap <= overlap_cap
    )
    return {
        "gate": "POST_PLACEMENT_FINAL_RASTER",
        "evidence_class": "REGISTRY-UNIQUENESS-GATE",
        "candidate_decoded_fp_sha256": fp_hash,
        "candidate_emitted_dots": n_cand,
        "rasters_checked": len(manifest["entries"]),
        "competing_sparse_detectors_checked": sum(1 for e in manifest["entries"] if not e["is_blanket_or_continuous_surface"]),
        "blanket_surfaces_disclosed": len(blanket_disclosures),
        "exact_hash_collision": exact_hash_collision,
        "spearman_abs_cap": spearman_cap,
        "overlap_3px_cap": overlap_cap,
        "max_abs_spearman_rho": round(max_abs_rho, 6),
        "closest_spearman_raster": worst_rho_entry,
        "max_3px_overlap_vs_competing_detectors": round(max_sparse_overlap, 6),
        "closest_3px_overlap_detector": worst_sparse_entry,
        "max_matched_top50k_overlap_vs_blanket_surfaces": round(max_blanket_matched_overlap, 6),
        "vs_focus_9_champions": dict(sorted(focus_site_comparisons.items())),
        "top_10_competing_overlaps": top_sparse[:10],
        "ir_reg_blanket_disclosures": blanket_disclosures,
        "passed": passed,
    }
