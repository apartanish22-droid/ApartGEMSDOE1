#!/usr/bin/env python3
"""Inventory every GeoTIFF/ZIP that the listed GEMSDOE GitHub mirrors publish.

Why this exists
---------------
The user prompt lists ~114 GitHub Pages sites. Each site is a GitHub repo whose
default branch hosts the submitted rasters. Pages are not reachable from this
sandbox, but the GitHub API is. This script reads the repo git trees through
api.github.com (authenticated via the local `gh` login), downloads each raster
blob, and records hashes, grid metadata, value checks and the user's claimed
score. It never submits anything and never writes rasters into Git.

Outputs (committed, small):
  evidence/registry_inventory.json   one row per raster, with links and checks
Cache (git-ignored, large):
  .cache/registry/<owner>__<repo>__<blob_sha>.tif

Evidence classes: every number here is a MEASUREMENT of a mirror file. A claimed
score is copied from the prompt and labelled USER-CLAIM. Nothing here is an
organizer receipt (ORGANIZER-CONFIRMED) or a holdout estimate.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CACHE = ROOT / ".cache" / "registry"
SITES = ROOT / "evidence" / "registry_sites.json"
OUT = ROOT / "evidence" / "registry_inventory.json"
GRID_CRS = "EPSG:32611"
GRID_SHAPE = (3730, 3292)
GRID_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
MAX_BYTES = 60_000_000


def gh_api(path: str, *, raw: bool = False):
    cmd = ["gh", "api", "-H", "Accept: application/vnd.github+json", path]
    out = subprocess.run(cmd, check=True, capture_output=True)
    return out.stdout if raw else json.loads(out.stdout)


def load_sites():
    data = json.loads(SITES.read_text())
    merged: dict[tuple[str, str], dict] = {}
    for s in data["sites"]:
        key = (s["owner"], s["repo"])
        entry = merged.setdefault(key, {"owner": s["owner"], "repo": s["repo"], "claims": {}})
        entry["claims"].update(s["claims"])
    return list(merged.values())


def list_rasters(owner: str, repo: str):
    meta = gh_api(f"repos/{owner}/{repo}")
    branch = meta["default_branch"]
    head = gh_api(f"repos/{owner}/{repo}/commits/{branch}")
    tree = gh_api(f"repos/{owner}/{repo}/git/trees/{head['sha']}?recursive=1")
    rows = []
    for node in tree.get("tree", []):
        p = node["path"]
        if node["type"] != "blob":
            continue
        low = p.lower()
        if not (low.endswith(".tif") or low.endswith(".tiff") or low.endswith(".zip")):
            continue
        rows.append(dict(path=p, blob_sha=node["sha"], size=node.get("size", 0)))
    return dict(default_branch=branch, commit=head["sha"], html_url=meta["html_url"],
                pushed_at=meta.get("pushed_at"), rasters=rows, truncated=tree.get("truncated", False))


def fetch_blob(owner: str, repo: str, blob_sha: str) -> bytes:
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / f"{owner}__{repo}__{blob_sha}"
    if cached.exists():
        return cached.read_bytes()
    obj = gh_api(f"repos/{owner}/{repo}/git/blobs/{blob_sha}")
    data = base64.b64decode(obj["content"]) if obj.get("encoding") == "base64" else obj["content"].encode()
    cached.write_bytes(data)
    return data


def measure_tif(data: bytes, sample_footprint=None) -> dict:
    """Read a single GeoTIFF from memory and summarize format and value checks."""
    import tempfile
    import rasterio
    fd, tmp = tempfile.mkstemp(suffix=".tif")
    os.close(fd)
    try:
        Path(tmp).write_bytes(data)
        with rasterio.open(tmp) as src:
            info = dict(
                count=src.count, dtype=src.dtypes[0], crs=str(src.crs),
                height=src.height, width=src.width,
                transform=[float(v) for v in tuple(src.transform)[:6]],
                nodata=None if src.nodata is None else (None if np.isnan(src.nodata) else float(src.nodata)),
                nodata_is_nan=bool(src.nodata is not None and np.isnan(src.nodata)),
            )
            info["grid_matches_template"] = bool(
                info["crs"] == GRID_CRS and (info["height"], info["width"]) == GRID_SHAPE
                and tuple(info["transform"]) == GRID_TRANSFORM)
            a = src.read(1)
            if a.dtype.kind == 'f':
                a = a.astype(np.float32, copy=False)
        finite = np.isfinite(a)
        vals = a[finite].astype(np.float64)
        info.update(
            n_cells=int(a.size),
            n_nan=int(np.isnan(a).sum()),
            n_inf=int(np.isinf(a).sum()),
            n_finite=int(finite.sum()),
            n_finite_outside_0_1=int(((vals < 0) | (vals > 1)).sum()) if vals.size else 0,
            n_negative_finite=int((vals < 0).sum()) if vals.size else 0,
            n_gt_1=int((vals > 1).sum()) if vals.size else 0,
            n_exact_minus1=int((a == -1).sum()),
            min_finite=float(vals.min()) if vals.size else None,
            max_finite=float(vals.max()) if vals.size else None,
            n_positive=int((vals > 0).sum()) if vals.size else 0,
            n_equal_one=int((vals == 1).sum()) if vals.size else 0,
            positive_sha256_of_cells=None,
        )
        pos = np.flatnonzero(np.nan_to_num(a, nan=0.0) > 0).astype(np.int64)
        info["positive_sha256_of_cells"] = hashlib.sha256(pos.tobytes()).hexdigest()
        del pos
        info["sum_finite"] = float(vals.sum()) if vals.size else 0.0
        info["range_ok_for_portal_rule"] = bool(
            info["n_finite_outside_0_1"] == 0 and info["n_inf"] == 0)
        info["nan_outside_footprint_convention"] = bool(info["n_nan"] > 0)
        info["zero_outside_convention"] = bool(info["n_nan"] == 0 and info["n_positive"] < info["n_cells"])
        return info
    finally:
        Path(tmp).unlink(missing_ok=True)


def measure_zip(data: bytes) -> dict:
    import io
    import zipfile
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        tifs = [n for n in names if n.lower().endswith((".tif", ".tiff"))]
        out = dict(zip_members=names, tif_members=tifs)
        if len(tifs) == 1:
            out["member"] = measure_tif(z.read(tifs[0]))
    return out


def process_site(site: dict) -> dict:
    owner, repo = site["owner"], site["repo"]
    try:
        info = list_rasters(owner, repo)
    except subprocess.CalledProcessError as exc:
        return dict(owner=owner, repo=repo, error=(exc.stderr or b"").decode(errors="replace")[:300],
                    claims=site["claims"], rasters=[])
    rows = []
    for r in info["rasters"]:
        base = dict(owner=owner, repo=repo, path=r["path"], blob_sha=r["blob_sha"], size=r["size"],
                    commit=info["commit"], branch=info["default_branch"],
                    blob_url=f"https://github.com/{owner}/{repo}/blob/{info['commit']}/{r['path']}",
                    raw_link=f"https://github.com/{owner}/{repo}/blob/{info['commit']}/{r['path']}?raw=1",
                    pages_url=f"https://{owner}.github.io/{repo}/")
        if r["size"] > MAX_BYTES:
            base["skipped"] = f"size {r['size']} exceeds cap {MAX_BYTES}"
            rows.append(base)
            continue
        try:
            data = fetch_blob(owner, repo, r["blob_sha"])
            base["sha256"] = hashlib.sha256(data).hexdigest()
            base["bytes"] = len(data)
            if r["path"].lower().endswith(".zip"):
                base["zip"] = measure_zip(data)
            else:
                base["tif"] = measure_tif(data)
        except Exception as exc:  # record, never silently drop
            base["error"] = f"{type(exc).__name__}: {exc}"[:300]
        rows.append(base)
    return dict(owner=owner, repo=repo, html_url=info["html_url"], commit=info["commit"],
                branch=info["default_branch"], pushed_at=info["pushed_at"],
                truncated_tree=info["truncated"], claims=site["claims"], rasters=rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--only", nargs="*", help="owner/repo filters for a quick run")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    sites = load_sites()
    if args.only:
        keep = set(args.only)
        sites = [s for s in sites if f"{s['owner']}/{s['repo']}" in keep]
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process_site, s): s for s in sites}
        for fut in as_completed(futs):
            results.append(fut.result())
    results.sort(key=lambda r: (r["owner"], r["repo"]))
    n_rasters = sum(len(r["rasters"]) for r in results)
    doc = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        method="GitHub git-tree listing + blob fetch via api.github.com (gh CLI). Pages sites themselves are not reachable from the sandbox.",
        grid=dict(crs=GRID_CRS, shape=list(GRID_SHAPE), transform=list(GRID_TRANSFORM)),
        evidence_note=("MEASURED = computed from mirror bytes. USER-CLAIM = score copied from the prompt. "
                       "No organizer receipt exists in this inventory."),
        n_sites=len(results), n_rasters=n_rasters, sites=results,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=1, allow_nan=False) + "\n")
    print(f"sites={len(results)} rasters={n_rasters} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
