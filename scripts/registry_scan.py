#!/usr/bin/env python3
"""Uniqueness scan of a candidate raster against the public GEMSDOE owner inventory.

Two tiers, reported separately (never merged into one claim):

1. EXACT copies: git blob SHA-1 of the candidate file against EVERY GeoTIFF blob
   listed in the owner repositories' git trees (no download needed). A match
   means byte-identical content to a previously published file.
2. SPATIAL overlap: the shared gems57.uniqueness comparison (3-px dot overlap,
   Spearman rank correlation, Jaccard) against every GeoTIFF under
   ``docs/downloads/`` in those repositories, the submission-output folder.
   Rasters outside that folder are NOT downloaded in this scan and are listed
   as out of scope.

Inputs: ``evidence/registry/github_tree_enumeration.json`` (captured by
``scripts/registry_scan.py --enumerate``) and the candidate TIFF.
Downloads go to git-ignored ``.cache/registry/``. Nothing is submitted.

Usage::

    python scripts/registry_scan.py --enumerate            # refresh the tree listing (GitHub API)
    python scripts/registry_scan.py CANDIDATE.tif --out evidence/registry/uniqueness_X.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

OWNER = "buffedlizard55-lab"
ENUM_PATH = ROOT / "evidence/registry/github_tree_enumeration.json"
CACHE = ROOT / ".cache/registry"


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def enumerate_repos() -> dict:
    names = subprocess.run(["gh", "repo", "list", OWNER, "--limit", "400", "--json", "name", "-q", ".[].name"],
                           capture_output=True, timeout=120, check=True).stdout.decode().split()
    targets = [n for n in names if "gem" in n.lower() or "bridge" in n.lower()]

    def one(repo: str) -> tuple[str, dict]:
        try:
            tree = subprocess.run(["gh", "api", f"repos/{OWNER}/{repo}/git/trees/HEAD?recursive=1"],
                                  capture_output=True, timeout=120, check=True).stdout
            head = subprocess.run(["gh", "api", f"repos/{OWNER}/{repo}/commits/HEAD", "--jq", ".sha"],
                                  capture_output=True, timeout=60, check=True).stdout.decode().strip()
            t = json.loads(tree)
            tifs = [{"path": e["path"], "blob_sha1": e["sha"], "bytes": e.get("size")}
                    for e in t.get("tree", []) if e["type"] == "blob"
                    and e["path"].lower().endswith((".tif", ".tiff"))]
            return repo, {"commit": head, "tifs": tifs, "tree_truncated": bool(t.get("truncated"))}
        except Exception as exc:  # recorded, never silently dropped
            return repo, {"error": str(exc)[:200]}

    with ThreadPoolExecutor(6) as ex:
        repos = dict(ex.map(one, targets))
    doc = {"generated_utc": datetime.now(timezone.utc).isoformat(), "owner": OWNER,
           "repositories_listed": len(names), "repositories_scanned": len(targets),
           "repos": repos}
    ENUM_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENUM_PATH.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def fetch_blob(repo: str, sha: str, dest: Path) -> Path:
    if dest.is_file():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(["gh", "api", f"repos/{OWNER}/{repo}/git/blobs/{sha}",
                          "-H", "Accept: application/vnd.github.raw+json"],
                         capture_output=True, timeout=300, check=True)
    if git_blob_sha1(res.stdout) != sha:
        raise ValueError(f"blob sha mismatch for {repo}:{sha}")
    tmp = dest.with_name(dest.name + ".partial")
    tmp.write_bytes(res.stdout)
    tmp.replace(dest)
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidate", type=Path, nargs="?")
    ap.add_argument("--enumerate", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    if args.enumerate:
        doc = enumerate_repos()
        print(json.dumps({k: doc[k] for k in ("repositories_listed", "repositories_scanned")}, indent=2))
        n = sum(len(v.get("tifs", [])) for v in doc["repos"].values())
        print(f"tif_blobs_listed={n} errors={sum(1 for v in doc['repos'].values() if 'error' in v)}")
        if not args.candidate:
            return 0
    if not args.candidate:
        ap.error("candidate TIFF required unless --enumerate alone")

    import numpy as np
    import rasterio
    from gems57 import load_grid
    from gems57.uniqueness import compare_array_to_registry

    doc = json.loads(ENUM_PATH.read_text())
    cand_bytes = args.candidate.read_bytes()
    cand_blob = git_blob_sha1(cand_bytes)
    cand_sha = hashlib.sha256(cand_bytes).hexdigest()

    all_tifs, dl_tifs = [], []
    for repo, info in sorted(doc["repos"].items()):
        for t in info.get("tifs", []):
            row = {"repo": repo, "commit": info["commit"], **t}
            all_tifs.append(row)
            if t["path"].startswith("docs/downloads/"):
                dl_tifs.append(row)
    exact_hits = [r for r in all_tifs if r["blob_sha1"] == cand_blob]

    grid = load_grid()
    with rasterio.open(args.candidate) as src:
        mine = src.read(1).astype(np.float32)
    # Only the candidate's own footprint can carry dots: check in-footprint values.
    records = []
    CACHE.mkdir(parents=True, exist_ok=True)

    def get(row):
        dest = CACHE / row["repo"] / row["blob_sha1"][:12] / Path(row["path"]).name
        fetch_blob(row["repo"], row["blob_sha1"], dest)
        return row, dest

    with ThreadPoolExecutor(args.workers) as ex:
        for row, dest in ex.map(get, dl_tifs):
            records.append({"repo_first": row["repo"], "sources": [f"{row['repo']}:{row['path']}"],
                            "cache_file": str(dest), "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                            "git_blob_sha1": row["blob_sha1"], "commit": row["commit"],
                            "owner_url": f"https://github.com/{OWNER}/{row['repo']}/blob/{row['commit']}/{row['path']}"})
    index = {"rasters": records, "complete_accessible_scan": False,
             "scope": "docs/downloads/*.tif in every owner repo whose name contains gem/bridge"}
    result = compare_array_to_registry(
        mine, index, grid.footprint, file_sha256=cand_sha, include_reverse=True,
        expected_grid=(grid.shape, grid.crs, grid.transform), stop_on_duplicate=False)
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": str(args.candidate), "candidate_sha256": cand_sha, "candidate_git_blob_sha1": cand_blob,
        "tier1_exact_copy": {
            "scope": f"all {len(all_tifs)} GeoTIFF blobs in {len({r['repo'] for r in all_tifs})} owner repos (git trees)",
            "matches": exact_hits, "exact_copy_found": bool(exact_hits)},
        "tier2_spatial": {
            "scope": f"{len(records)} docs/downloads GeoTIFFs; {len(all_tifs) - len(dl_tifs)} other GeoTIFFs NOT downloaded",
            "result": result},
    }
    text = json.dumps(report, indent=2, allow_nan=False, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(json.dumps({"exact_copy_found": bool(exact_hits),
                      "tier2_unique": result.get("unique"),
                      "tier2_max_my_dots_within_3px": result.get("max_my_dots_within_3px_of_theirs"),
                      "tier2_max_spearman": result.get("max_spearman_full_footprint"),
                      "scope_rasters": len(records)}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
