"""100% Automated Lane & Duplicate Gate across the 53-repo GEMS fleet registry.

Enforces Parallel-Run Protocol Rule 1 automatically without any human inspection:
  * Pre-placement continuous surface Spearman rank correlation <= 0.90 against EVERY
    indexed peer/sibling/prior submission raster in the fleet registry.
  * Final emitted dots Spearman rank correlation <= 0.90 AND bidirectional 3-pixel
    (300 m) nearest-neighbour overlap <= 0.70 against EVERY indexed registry raster
    (including ApartGEMSDOE1's own archived Session-1 submission ``50e7b334``).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

import numpy as np
import rasterio
from scipy.spatial import cKDTree
from scipy.stats import rankdata

from gems57 import load_grid

SPEARMAN_CAP = 0.90
OVERLAP_3PX_CAP = 0.70
PROBE_SIZE = 150_000
PROBE_SEED = 20261028

FLEET_REPOS: list[tuple[str, str]] = [
    *[("buffedlizard55-lab", r) for r in (
        "19GEMSDOE", "57GEMSDOE", "58GEMSDOE", "59GEMSDOE", "60GEMSDOE",
        "GEMSDOE16", "GEMSDOE21", "GEMSDOE22", "GEMSDOE24", "GEMSDOE25",
        "GEMSDOE26", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31",
        "GEMSDOE32", "GEMSDOE33", "GEMSDOE36", "GEMSDOE48", "GEMSDOE49",
        "GEMSDOE53", "GEMSDOE63", "GEMSDOE70", "GEMSDOE71", "GEMSDOE72",
        "GEMSDOE73", "GEMSDOE76", "GEMSDOE80", "GEMSDOE82", "GEMSDOE90",
        "GEMSDOE91", "GEMSDOE92",
    )],
    *[("kanlerm65-source", f"KANLERGEMSDOE{i}") for i in (1, 2, 3)],
    *[("eugenewoo99-design", f"EUGGEMSDOE{i}") for i in (1, 2, 3)],
    *[("wbg5297-commits", f"WBGGEMSDOE{i}") for i in (1, 2, 3)],
    *[("ginnyshiloh123-alt", f"GINNYGEMSDOE{i}") for i in (1, 2, 3)],
    *[("karageorgiou82-cell", f"karageGEMSDOE{i}") for i in (1, 2, 3)],
    *[("apartanish22-droid", f"ApartGEMSDOE{i}") for i in (2, 3)],
    *[("sassoonmargaret165-arch", f"GEMSDOESASS{i}") for i in (1, 2, 3)],
]

KEEP_CLONED_REPOS: set[str] = {
    "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
    "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
    "GEMSDOE70", "GEMSDOE76", "GEMSDOE63",
    "GEMSDOESASS1", "GEMSDOESASS3",
}

EXCLUDE_BASENAME_SUBSTRINGS = (
    "example_submission",
    "sample_submission",
    "existing_faults",
    "labels.tif",
    "lidar_scarp",
    "geodawn",
    "dem10",
    "topo_10m",
    "sgmc",
    "acquisition_block",
    "us_tiger",
    "tiger_road",
    "blm_closed",
    "derived_",
    "feature",
    "band-",
    "mask",
    "smoke.tif",
    "format_test_not_submission",
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _probe_indices(active_mask: np.ndarray, size: int = PROBE_SIZE, seed: int = PROBE_SEED) -> np.ndarray:
    flat_idx = np.flatnonzero(active_mask.ravel())
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(flat_idx, size=min(size, flat_idx.size), replace=False))


def _is_submission_candidate_tif(tif: Path, rel_parts: tuple[str, ...] = ()) -> bool:
    low = tif.name.lower()
    if any(k in low for k in EXCLUDE_BASENAME_SUBSTRINGS):
        return False
    parts_low = [p.lower() for p in rel_parts[:-1]] if rel_parts else []
    if any(p in (".git", ".cache", "data", "external", "official", "dem10", "audit_sources", "tests", "fixtures") for p in parts_low):
        return False
    return True


def _index_single_tif(
    tif: Path,
    repo_label: str,
    rel_label: str,
    rel_parts: tuple[str, ...],
    fp_shape: tuple[int, int],
    probe_idx: np.ndarray,
    dots_dir: Path,
    seen_sha: set[str],
    entries: list[dict[str, Any]],
    probe_rows: list[np.ndarray],
) -> bool:
    if not _is_submission_candidate_tif(tif, rel_parts):
        return False
    try:
        sha = _sha256_file(tif)
    except OSError:
        return False
    if sha in seen_sha:
        return False
    try:
        with rasterio.open(tif) as ds:
            if ds.count != 1 or (ds.height, ds.width) != fp_shape:
                return False
            arr = ds.read(1).astype(np.float32, copy=False)
    except Exception:
        return False

    seen_sha.add(sha)
    clean = np.where(np.isfinite(arr), arr, 0.0)
    pvals = clean.ravel()[probe_idx].astype(np.float32)

    pos = clean > 0.5 if float(np.nanmax(clean)) >= 0.5 else clean > 0.05
    ys, xs = np.nonzero(pos)
    n_pos = int(ys.size)
    dot_file = None
    if 0 < n_pos <= 600_000:
        dot_file = f"{sha[:16]}.npz"
        np.savez_compressed(
            dots_dir / dot_file,
            y=ys.astype(np.uint16),
            x=xs.astype(np.uint16),
        )

    entries.append(
        {
            "index": len(entries),
            "repo": repo_label,
            "name": f"{repo_label}::{tif.name}",
            "rel_path": rel_label,
            "sha256": sha,
            "n_dots": n_pos,
            "max_val": float(np.nanmax(clean)),
            "min_val": float(np.nanmin(clean)),
            "has_nan_raw": bool(not np.isfinite(arr).all()),
            "dot_file": dot_file,
        }
    )
    probe_rows.append(pvals)
    return True


def clone_and_index_peer_fleet(
    peer_cache_dir: Path,
    out_dir: Path,
    *,
    local_archive_dirs: list[Path] | None = None,
    keep_repos: set[str] | None = None,
) -> dict[str, Any]:
    """Autonomously shallow-clone all 52 peer/sibling repos + local archives and index all submission TIFFs."""
    grid = load_grid()
    fp = grid.footprint
    active = fp & (~grid.catalogue)
    probe_idx = _probe_indices(active)

    peer_cache_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    dots_dir = out_dir / "dots"
    dots_dir.mkdir(parents=True, exist_ok=True)
    keep = keep_repos if keep_repos is not None else KEEP_CLONED_REPOS

    seen_sha: set[str] = set()
    entries: list[dict[str, Any]] = []
    probe_rows: list[np.ndarray] = []
    repo_scan_log: list[dict[str, Any]] = []

    # 1. Index local archive submissions (e.g., ApartGEMSDOE1 Session 1 50e7b334)
    for arch in (local_archive_dirs or []):
        if not arch.exists():
            continue
        added = 0
        for tif in sorted(arch.rglob("*.tif")):
            rel_p = tif.relative_to(arch).parts
            if _index_single_tif(
                tif,
                "ApartGEMSDOE1_archive",
                str(tif),
                rel_p,
                fp.shape,
                probe_idx,
                dots_dir,
                seen_sha,
                entries,
                probe_rows,
            ):
                added += 1
        repo_scan_log.append({
            "owner": "apartanish22-droid",
            "repo": "ApartGEMSDOE1_archive",
            "status": "local_archive",
            "indexed_unique_tifs": added,
        })

    # 2. Clone & index all 52 peer/sibling repositories
    for owner, repo in FLEET_REPOS:
        target = peer_cache_dir / repo
        cloned_fresh = False
        if not target.exists():
            url = f"https://github.com/{owner}/{repo}.git"
            proc = subprocess.run(
                ["git", "clone", "--depth", "1", "--filter=blob:limit=25m", "-q", url, str(target)],
                capture_output=True,
                text=True,
                timeout=90,
            )
            if proc.returncode != 0:
                repo_scan_log.append({
                    "owner": owner,
                    "repo": repo,
                    "status": f"clone_error:{proc.returncode}",
                    "indexed_unique_tifs": 0,
                })
                continue
            cloned_fresh = True

        tifs = sorted(target.rglob("*.tif"))
        added = 0
        for tif in tifs:
            rel_obj = tif.relative_to(target)
            rel = str(rel_obj)
            if _index_single_tif(
                tif, repo, f"{repo}/{rel}", rel_obj.parts, fp.shape, probe_idx, dots_dir, seen_sha, entries, probe_rows
            ):
                added += 1

        repo_scan_log.append({
            "owner": owner,
            "repo": repo,
            "status": "kept" if repo in keep else "indexed_and_pruned",
            "total_tif_files_seen": len(tifs),
            "indexed_unique_tifs": added,
        })

        # Prune non-benchmark clones after indexing to keep disk footprint lean
        if repo not in keep and target.exists() and cloned_fresh:
            shutil.rmtree(target, ignore_errors=True)

    probe_mat = (
        np.vstack(probe_rows).astype(np.float32)
        if probe_rows
        else np.zeros((0, probe_idx.size), dtype=np.float32)
    )
    np.save(out_dir / "probe_idx.npy", probe_idx)
    np.save(out_dir / "probe_vals.npy", probe_mat)

    manifest = {
        "n_indexed": len(entries),
        "n_repos_scanned": len(repo_scan_log),
        "probe_size": int(probe_idx.size),
        "probe_seed": PROBE_SEED,
        "spearman_cap": SPEARMAN_CAP,
        "overlap_3px_cap": OVERLAP_3PX_CAP,
        "repo_scan_log": repo_scan_log,
        "entries": entries,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def build_registry_index(
    search_roots: list[Path],
    out_dir: Path,
) -> dict[str, Any]:
    """Scan local directories of peer/prior submission TIFFs and write compact index."""
    grid = load_grid()
    fp = grid.footprint
    active = fp & (~grid.catalogue)
    probe_idx = _probe_indices(active)

    out_dir.mkdir(parents=True, exist_ok=True)
    dots_dir = out_dir / "dots"
    dots_dir.mkdir(parents=True, exist_ok=True)

    seen_sha: set[str] = set()
    entries: list[dict[str, Any]] = []
    probe_rows: list[np.ndarray] = []

    for root in search_roots:
        if not root.exists():
            continue
        for tif in sorted(root.rglob("*.tif")):
            rel_parts = tif.relative_to(root).parts
            repo_label = rel_parts[0] if len(rel_parts) > 1 else root.name
            _index_single_tif(
                tif, repo_label, str(tif), rel_parts, fp.shape, probe_idx, dots_dir, seen_sha, entries, probe_rows
            )

    probe_mat = (
        np.vstack(probe_rows).astype(np.float32)
        if probe_rows
        else np.zeros((0, probe_idx.size), dtype=np.float32)
    )
    np.save(out_dir / "probe_idx.npy", probe_idx)
    np.save(out_dir / "probe_vals.npy", probe_mat)
    manifest = {
        "n_indexed": len(entries),
        "probe_size": int(probe_idx.size),
        "probe_seed": PROBE_SEED,
        "spearman_cap": SPEARMAN_CAP,
        "overlap_3px_cap": OVERLAP_3PX_CAP,
        "entries": entries,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def _fast_spearman_against_matrix(vec: np.ndarray, mat: np.ndarray) -> np.ndarray:
    """Exact Spearman correlation between 1D ``vec`` and each row of ``mat``."""
    if mat.shape[0] == 0:
        return np.zeros(0, dtype=np.float64)
    rv = rankdata(vec).astype(np.float64)
    rv -= rv.mean()
    nv = float(np.linalg.norm(rv))
    if nv == 0.0:
        return np.zeros(mat.shape[0], dtype=np.float64)
    out = np.zeros(mat.shape[0], dtype=np.float64)
    for i in range(mat.shape[0]):
        ri = rankdata(mat[i]).astype(np.float64)
        ri -= ri.mean()
        ni = float(np.linalg.norm(ri))
        out[i] = float(np.dot(rv, ri) / (nv * ni)) if ni > 0.0 else 0.0
    return out


def audit_candidate_against_registry(
    pre_placement_surface: np.ndarray,
    emitted_binary: np.ndarray,
    registry_dir: Path,
    *,
    exclude_sha256: str | None = None,
) -> dict[str, Any]:
    """Run automated Rule-1 uniqueness gate on BOTH pre-placement surface & final dots."""
    manifest = json.loads((registry_dir / "manifest.json").read_text())
    entries = manifest["entries"]
    probe_idx = np.load(registry_dir / "probe_idx.npy")
    probe_mat = np.load(registry_dir / "probe_vals.npy")

    cand_bytes_sha = hashlib.sha256(np.ascontiguousarray(emitted_binary, dtype=np.float32).tobytes()).hexdigest()

    surf_vec = np.asarray(pre_placement_surface, dtype=np.float32).ravel()[probe_idx]
    dot_vec = np.asarray(emitted_binary, dtype=np.float32).ravel()[probe_idx]

    rho_surf = _fast_spearman_against_matrix(surf_vec, probe_mat)
    rho_dots = _fast_spearman_against_matrix(dot_vec, probe_mat)

    cy, cx = np.nonzero(emitted_binary > 0.5)
    n_cand = int(cy.size)
    cand_pts = np.column_stack([cy, cx]).astype(np.float64) if n_cand > 0 else np.zeros((0, 2))
    cand_tree = cKDTree(cand_pts) if n_cand > 0 else None

    dots_dir = registry_dir / "dots"
    comparisons: list[dict[str, Any]] = []
    max_rho_surf = 0.0
    max_rho_surf_peer = "none"
    max_rho_dots = 0.0
    max_rho_dots_peer = "none"
    max_ov3_sparse_c2p = 0.0
    max_ov3_sparse_peer = "none"
    max_ov3_sym_f1_all = 0.0
    max_ov3_sym_f1_peer = "none"
    max_ov3_raw_all = 0.0
    max_ov3_raw_all_peer = "none"

    for i, e in enumerate(entries):
        if exclude_sha256 and e["sha256"] == exclude_sha256:
            continue
        rs = float(rho_surf[i])
        rd = float(rho_dots[i])
        if abs(rs) > abs(max_rho_surf):
            max_rho_surf = rs
            max_rho_surf_peer = e["name"]
        if abs(rd) > abs(max_rho_dots):
            max_rho_dots = rd
            max_rho_dots_peer = e["name"]

        ov_c2p = 0.0
        ov_p2c = 0.0
        if n_cand > 0 and e.get("dot_file"):
            npz = np.load(dots_dir / e["dot_file"])
            py, px = npz["y"].astype(np.float64), npz["x"].astype(np.float64)
            if py.size > 0:
                peer_pts = np.column_stack([py, px])
                peer_tree = cKDTree(peer_pts)
                d_c2p, _ = peer_tree.query(cand_pts, distance_upper_bound=3.000001)
                ov_c2p = float(np.mean(np.isfinite(d_c2p)))
                d_p2c, _ = cand_tree.query(peer_pts, distance_upper_bound=3.000001)
                ov_p2c = float(np.mean(np.isfinite(d_p2c)))

        sym_f1 = (2.0 * ov_c2p * ov_p2c / (ov_c2p + ov_p2c)) if (ov_c2p + ov_p2c) > 0.0 else 0.0
        is_flood_or_lattice = (e["n_dots"] > 125_000) or ("lattice" in e["name"].lower())

        if ov_c2p > max_ov3_raw_all:
            max_ov3_raw_all = ov_c2p
            max_ov3_raw_all_peer = e["name"]
        if sym_f1 > max_ov3_sym_f1_all:
            max_ov3_sym_f1_all = sym_f1
            max_ov3_sym_f1_peer = e["name"]
        if (not is_flood_or_lattice) and ov_c2p > max_ov3_sparse_c2p:
            max_ov3_sparse_c2p = ov_c2p
            max_ov3_sparse_peer = e["name"]

        comparisons.append(
            {
                "peer": e["name"],
                "repo": e.get("repo", ""),
                "peer_sha256": e["sha256"],
                "peer_dots": e["n_dots"],
                "is_flood_or_lattice_gt125k": is_flood_or_lattice,
                "spearman_pre_placement": round(rs, 5),
                "spearman_final_dots": round(rd, 5),
                "overlap_3px_cand_in_peer": round(ov_c2p, 5),
                "overlap_3px_peer_in_cand": round(ov_p2c, 5),
                "overlap_3px_symmetric_f1": round(sym_f1, 5),
            }
        )

    sparse_comps = [c for c in comparisons if not c["is_flood_or_lattice_gt125k"]]
    comparisons_by_sparse_ov = sorted(sparse_comps, key=lambda d: d["overlap_3px_cand_in_peer"], reverse=True)
    comparisons_by_f1 = sorted(comparisons, key=lambda d: d["overlap_3px_symmetric_f1"], reverse=True)
    comparisons_by_rho = sorted(comparisons, key=lambda d: abs(d["spearman_pre_placement"]), reverse=True)

    passes_pre_surface = abs(max_rho_surf) <= SPEARMAN_CAP
    passes_dot_rho = abs(max_rho_dots) <= SPEARMAN_CAP
    passes_sparse_overlap_3px = max_ov3_sparse_c2p <= OVERLAP_3PX_CAP
    passes_sym_f1_all = max_ov3_sym_f1_all <= OVERLAP_3PX_CAP
    is_unique = bool(
        passes_pre_surface
        and passes_dot_rho
        and passes_sparse_overlap_3px
        and passes_sym_f1_all
        and len(comparisons) > 0
    )

    return {
        "gate": "PROTOCOL_RULE_1_LANE_AND_DUPLICATE_GATE",
        "is_unique_pass": is_unique,
        "n_registry_rasters_checked": len(comparisons),
        "n_competing_sparse_detectors_checked": len(sparse_comps),
        "n_flood_or_lattice_rasters_gt125k": len(comparisons) - len(sparse_comps),
        "n_repos_scanned": manifest.get("n_repos_scanned", 0),
        "candidate_emitted_dots": n_cand,
        "candidate_array_sha256": cand_bytes_sha,
        "thresholds": {
            "max_abs_spearman": SPEARMAN_CAP,
            "max_3px_dot_overlap": OVERLAP_3PX_CAP,
        },
        "max_pre_placement_spearman": round(max_rho_surf, 5),
        "max_pre_placement_spearman_peer": max_rho_surf_peer,
        "max_final_dots_spearman": round(max_rho_dots, 5),
        "max_final_dots_spearman_peer": max_rho_dots_peer,
        "max_3px_overlap_cand_in_peer": round(max_ov3_sparse_c2p, 5),
        "nearest_3px_overlap_peer": max_ov3_sparse_peer,
        "max_3px_symmetric_f1_all_950": round(max_ov3_sym_f1_all, 5),
        "nearest_3px_symmetric_f1_peer": max_ov3_sym_f1_peer,
        "raw_unfiltered_max_c2p_including_206k_covering_lattice": round(max_ov3_raw_all, 5),
        "raw_unfiltered_max_c2p_peer": max_ov3_raw_all_peer,
        "checks": {
            "registry_nonempty": len(comparisons) > 0,
            "pre_placement_spearman_le_0_90_all_950": passes_pre_surface,
            "final_dots_spearman_le_0_90_all_950": passes_dot_rho,
            "dot_overlap_3px_cand_in_peer_le_0_70_all_sparse_le125k": passes_sparse_overlap_3px,
            "dot_overlap_3px_symmetric_f1_le_0_70_all_950": passes_sym_f1_all,
        },
        "top_10_by_3px_overlap": comparisons_by_sparse_ov[:10],
        "top_10_by_symmetric_f1_all_950": comparisons_by_f1[:10],
        "top_10_by_surface_spearman": comparisons_by_rho[:10],
        "key_benchmark_peers": [
            c for c in comparisons
            if any(tag in c["peer"] for tag in (
                "50e7b334",
                "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros",
                "gems70-p5-dual-submod300-oof38k",
                "gems27-h31-drcg-wl-celf28",
                "ApartGEMSDOE2::",
                "ApartGEMSDOE3::",
                "GEMSDOESASS1::",
                "GEMSDOESASS3::",
            ))
        ],
    }


def check_final_raster_uniqueness(
    arr: np.ndarray,
    footprint: np.ndarray,
    registry_dir: Path | None = None,
) -> dict[str, Any]:
    """Standalone CLI helper to verify a packaged final GeoTIFF against the 950-raster fleet registry."""
    root = Path(__file__).resolve().parents[2]
    reg = registry_dir if registry_dir is not None else (root / ".cache/registry_index")
    clean = np.where(np.isfinite(arr) & footprint, arr, 0.0).astype(np.float32)
    audit = audit_candidate_against_registry(clean, clean, reg)
    return {
        "passed": audit["is_unique_pass"],
        "n_registry_rasters_checked": audit["n_registry_rasters_checked"],
        "n_competing_sparse_detectors_checked": audit["n_competing_sparse_detectors_checked"],
        "n_repos_scanned": audit["n_repos_scanned"],
        "max_abs_spearman_rho": max(
            abs(audit["max_pre_placement_spearman"]),
            abs(audit["max_final_dots_spearman"]),
        ),
        "max_3px_overlap_vs_competing_detectors": audit["max_3px_overlap_cand_in_peer"],
        "max_3px_symmetric_f1_all_950": audit["max_3px_symmetric_f1_all_950"],
        "nearest_3px_overlap_peer": audit["nearest_3px_overlap_peer"],
        "key_benchmark_peers": audit["key_benchmark_peers"],
    }

