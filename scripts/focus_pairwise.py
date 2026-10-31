#!/usr/bin/env python3
"""Pairwise 3-px dot overlap among the nine focus GEMSDOE files (shared gate definition).

Uses ``gems57.uniqueness.dot_overlap`` (fraction of MY dots within 3 px of THEIR dots).
For each focus site the historical file is the mirror raster whose path contains the
user-claimed key with the highest claimed score (from evidence/registry_sites.json).
This is a nine-by-nine check only. A registry-wide check of the nine files is NOT done here.

Output: evidence/focus_pairwise_overlap.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio
from rasterio.io import MemoryFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import load_grid  # noqa: E402
from gems57.uniqueness import dot_overlap  # noqa: E402

FOCUS = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]
OWNER = "buffedlizard55-lab"
CACHE = ROOT / ".cache" / "registry"


def focus_record(inv: dict, sites: dict, repo: str) -> dict:
    site = next((s for s in inv["sites"] if s["owner"] == OWNER and s["repo"] == repo), None)
    if site is None:
        raise SystemExit(f"{repo}: not in inventory")
    claims = sites[(OWNER, repo)]
    best = max(((k, v) for k, v in claims.items() if v is not None), key=lambda kv: kv[1])[0]
    hits = [r for r in site["rasters"] if best in r["path"] and "error" not in r
            and r["path"].lower().endswith((".tif", ".zip"))]
    if not hits:
        raise SystemExit(f"{repo}: no readable raster matches claim key {best}")
    return dict(repo=repo, claim_key=best, claimed_score=claims[best], rec=hits[0])


def load_array(rec: dict, grid) -> np.ndarray:
    cache = CACHE / f"{OWNER}__{rec['repo']}__{rec['blob_sha']}"
    if not cache.exists():
        raise SystemExit(f"blob not cached: {cache.name}")
    data = cache.read_bytes()
    if rec["path"].lower().endswith(".zip"):
        with zipfile.ZipFile(__import__("io").BytesIO(data)) as z:
            data = z.read(rec["zip"]["tif_members"][0])
    with MemoryFile(data) as mf, mf.open() as src:
        if (src.shape, src.crs, src.transform) != (grid.shape, grid.crs, grid.transform):
            raise SystemExit(f"{rec['path']}: not on the template grid")
        return src.read(1).astype(np.float32)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inventory", type=Path, default=ROOT / "evidence" / "registry_inventory.json")
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "focus_pairwise_overlap.json")
    args = ap.parse_args()
    inv = json.loads(args.inventory.read_text())
    sites_doc = json.loads((ROOT / "evidence" / "registry_sites.json").read_text())
    sites = {}
    for s in sites_doc["sites"]:
        sites.setdefault((s["owner"], s["repo"]), {}).update(s["claims"])
    grid = load_grid()

    recs = [focus_record(inv, sites, r) for r in FOCUS]
    arrays = {}
    for f in recs:
        a = load_array(f["rec"], grid)
        arrays[f["repo"]] = a
        f["dots"] = int(((a > 0) & np.isfinite(a)).sum())
        f["file"] = f["rec"]["path"]
        f["sha256_mirror_bytes"] = f["rec"]["sha256"]
        f["blob_url"] = f["rec"]["blob_url"]
        f["raw_link"] = f["rec"]["raw_link"]

    out_sites = {}
    for f in recs:
        me = arrays[f["repo"]]
        ov = {}
        for g in recs:
            if g["repo"] == f["repo"]:
                continue
            ov[g["repo"]] = dot_overlap(me, arrays[g["repo"]])
        peer, mx = max(ov.items(), key=lambda kv: kv[1])
        out_sites[f["repo"]] = dict(
            file=f["file"], claim_key=f["claim_key"], claimed_score=f["claimed_score"],
            dots=f["dots"], sha256_mirror_bytes=f["sha256_mirror_bytes"],
            blob_url=f["blob_url"], raw_link=f["raw_link"],
            overlap_with_each_peer=ov, closest_peer=peer, max_overlap=mx,
        )
    doc = dict(
        evidence_class="REGISTRY-MEASUREMENT (nine-by-nine only; not registry-wide)",
        radius_px=3, overlap_definition="fraction of my dots within 3 px of their dots (gems57.uniqueness.dot_overlap)",
        limit=0.70, sites=out_sites,
        all_above_limit=all(v["max_overlap"] > 0.70 for v in out_sites.values()),
    )
    args.out.write_text(json.dumps(doc, indent=1, allow_nan=False) + "\n")
    for k, v in out_sites.items():
        print(f"{k}: closest {v['closest_peer']} overlap {v['max_overlap']:.4f} dots {v['dots']}")
    print("all above 70%:", doc["all_above_limit"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
