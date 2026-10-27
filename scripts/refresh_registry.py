#!/usr/bin/env python3
"""Restore immutable peer prediction bytes via GitHub; never use them as features.

The inventory covers TIFFs under docs/, inputs/, archive/ and evidence/ in the
nine requested repositories. Nonprediction grids are recorded, not silently
included as comparison rasters. Large raw inputs and caches remain gitignored.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
SITES = (24, 25, 27, 28, 30, 31, 32, 33, 36)
PREFIXES = ("docs/", "inputs/", "archive/", "evidence/")


def api(endpoint: str) -> dict:
    result = subprocess.run(["gh", "api", endpoint], check=True, capture_output=True, text=True, timeout=90)
    return json.loads(result.stdout)


def save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def download(row: dict) -> dict:
    target = ROOT / ".cache/registry/blobs" / (row["blob_sha"] + ".tif")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        if not target.exists() or target.stat().st_size != row["bytes"]:
            partial = target.with_suffix(".partial")
            with partial.open("wb") as handle:
                subprocess.run(
                    ["gh", "api", "-H", "Accept: application/vnd.github.raw+json",
                     f"repos/{row['repo']}/git/blobs/{row['blob_sha']}"],
                    stdout=handle, stderr=subprocess.PIPE, check=True, timeout=90,
                )
            if partial.stat().st_size != row["bytes"]:
                raise ValueError("Downloaded size differs from pinned Git tree")
            blob = hashlib.sha1(b"blob " + str(partial.stat().st_size).encode() + b"\0" + partial.read_bytes()).hexdigest()
            if blob != row["blob_sha"]:
                raise ValueError("Downloaded bytes differ from pinned Git blob")
            partial.replace(target)
        # Always revalidate existing cache too, rather than trusting its size.
        payload = target.read_bytes()
        if hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest() != row["blob_sha"]:
            raise ValueError("Cached Git blob checksum mismatch")
        return {**row, "cache_path": str(target.relative_to(ROOT)), "sha256": hashlib.sha256(payload).hexdigest(), "fetch_status": "ok"}
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return {**row, "fetch_status": "failed", "error": str(exc)}


def build_manifest(*, refresh: bool = False) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    pins = json.loads((ROOT / "evidence/source-pins.json").read_text())
    inventory = []
    for n in SITES:
        repo = f"buffedlizard55-lab/GEMSDOE{n}"
        pin = next(x for x in pins if x["repo"] == repo)
        if refresh:
            commit = api(f"repos/{repo}/commits/HEAD")
            pin.update(snapshot_commit=commit["sha"], snapshot_tree=commit["commit"]["tree"]["sha"],
                       latest_commit_at_check=commit["sha"], fresh_at_check=True, retrieved_utc=now)
            tree = api(f"repos/{repo}/git/trees/{commit['sha']}?recursive=1")
            save(ROOT / f"evidence/sources/buffedlizard55-lab__GEMSDOE{n}_tree.json", tree)
        else:
            tree = json.loads((ROOT / f"evidence/sources/buffedlizard55-lab__GEMSDOE{n}_tree.json").read_text())
        if tree.get("truncated"):
            raise ValueError(f"Truncated inventory for {repo}; cannot certify coverage")
        for entry in tree["tree"]:
            path = entry["path"]
            if entry["type"] == "blob" and path.lower().endswith(".tif") and path.startswith(PREFIXES):
                inventory.append({
                    "id": f"GEMSDOE{n}:{path}", "site": f"GEMSDOE{n}", "repo": repo,
                    "ref": pin["snapshot_commit"], "file": path, "blob_sha": entry["sha"],
                    "bytes": entry["size"], "source_url": f"https://github.com/{repo}/blob/{pin['snapshot_commit']}/{path}",
                })
    # Fetch each content blob once even if many names refer to the same bytes.
    unique = {row["blob_sha"]: row for row in inventory}
    fetched = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for i, row in enumerate(pool.map(download, unique.values()), 1):
            fetched[row["blob_sha"]] = row
            if i % 25 == 0:
                print(f"Restored {i}/{len(unique)} registry blobs", flush=True)
    with rasterio.open(ROOT / "data/bridge/sample_submission.tif") as template:
        footprint = np.isfinite(template.read(1))
        shape, crs, transform = template.shape, template.crs, template.transform
    validated = {}
    for key, row in fetched.items():
        if row["fetch_status"] != "ok":
            continue
        try:
            with rasterio.open(ROOT / row["cache_path"]) as dataset:
                if (dataset.count, dataset.shape, dataset.crs, dataset.transform) != (1, shape, crs, transform):
                    raise ValueError("not an aligned single-band prediction raster")
                values = dataset.read(1)[footprint]
            if not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
                raise ValueError("not a finite [0,1] in-footprint prediction raster")
            row["footprint_sha256"] = hashlib.sha256(np.asarray(values, dtype="<f4").tobytes()).hexdigest()
            row["positive_pixels"] = int(np.count_nonzero(values > 0))
            row["status"] = "comparable"
            validated[key] = row
        except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
            row["status"] = "incompatible"
            row["error"] = str(exc)
    rows = []
    for alias in inventory:
        result = fetched[alias["blob_sha"]]
        rows.append({**result, **alias})
    # Distinct filenames, compression and exterior encodings are not new predictions.
    raster_groups = {}
    for row in rows:
        if row.get("status") == "comparable":
            raster_groups.setdefault(row["footprint_sha256"], []).append(row)
    comparisons = []
    for digest, group in raster_groups.items():
        representative = dict(group[0])
        representative["aliases"] = [{k: alias[k] for k in ("id", "site", "file", "ref", "source_url", "sha256")} for alias in group]
        comparisons.append(representative)
    result = {
        "schema": "apartgems-registry-v1", "retrieved_utc": now,
        "scope": "All .tif files in docs/, inputs/, archive/, evidence/ in the nine requested repository snapshots; other linked projects are NOT exhaustively inventoried.",
        "source_pins": pins, "inventory_count": len(rows), "unique_byte_blobs": len(fetched),
        "unique_prediction_rasters": len(comparisons),
        "failed_fetches": sum(row["fetch_status"] != "ok" for row in rows),
        "incompatible_rasters": sum(row.get("status") == "incompatible" for row in rows),
        "global_all_sites_certified": False, "calibration_controls_exempted": False,
        "entries": comparisons, "inventory": rows,
    }
    save(ROOT / "evidence/registry.json", result)
    save(ROOT / "evidence/source-pins.json", pins)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Resolve and freeze current peer HEADs first")
    args = parser.parse_args()
    if (ROOT / "evidence/experiment.json").exists():
        parser.error("Frozen AP1 registry: a recorded experiment exists. Use scripts/source_health.py --github-only for non-mutating drift diagnostics; do not rewrite the stopped run's snapshot.")
    result = build_manifest(refresh=args.refresh)
    print(json.dumps({k: v for k, v in result.items() if k not in ("inventory", "entries", "source_pins")}, indent=2))
