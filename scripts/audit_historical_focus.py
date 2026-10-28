#!/usr/bin/env python3
"""Re-measure the nine prompt-named historical rasters; no training or submission.

The owner-mirror files are fetched from GitHub at recorded commits and verified
against Git blob IDs. The prompt's score claims are not authenticated receipts.
The cache is disposable and the output explicitly limits its inventory scope.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt
from gems57 import load_grid

OWNER = "buffedlizard55-lab"
MANIFEST = ROOT / "evidence/focus9_manifest.json"
CACHE = ROOT / ".cache/focus9_reaudit"
DEFAULT_OUT = ROOT / "evidence/focus9_reaudit.json"


def gh(*args: str, binary: bool = False):
    p = subprocess.run(["gh", "api", *args], check=True, capture_output=True, timeout=90)
    return p.stdout if binary else p.stdout.decode("utf-8").strip()


def fetch(spec):
    repo = f"{OWNER}/{spec['site']}"
    commit = spec['commit']
    if len(commit) != 40 or len(spec['sha256']) != 64:
        raise ValueError(f"{spec['site']}: missing immutable commit or SHA256 pin")
    endpoint = f"repos/{repo}/contents/{spec['path']}?ref={commit}"
    meta = json.loads(gh(endpoint, "--jq", '{"sha":.sha,"size":.size}'))
    target = CACHE / spec['site'] / commit / Path(spec['path']).name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        blob = target.read_bytes()
    else:
        blob = gh(endpoint, "-H", "Accept: application/vnd.github.raw+json", binary=True)
    git_hash = hashlib.sha1(f"blob {len(blob)}\0".encode() + blob).hexdigest()
    if git_hash != meta['sha'] or len(blob) != meta['size']:
        raise ValueError(f"{spec['site']}: Git blob hash or length mismatch")
    if hashlib.sha256(blob).hexdigest() != spec['sha256']:
        raise ValueError(f"{spec['site']}: SHA256 pin mismatch")
    if not target.exists():
        target.write_bytes(blob)
    return {**spec, "commit": commit, "git_blob_sha1": git_hash,
            "sha256": hashlib.sha256(blob).hexdigest(), "local_cache": target}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text())['sites']
    grid = load_grid()
    fp = grid.footprint
    data = []
    errors = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = [pool.submit(fetch, spec) for spec in manifest]
        for spec, future in zip(manifest, results):
            try:
                data.append(future.result())
            except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
                errors.append({"site": spec['site'], "error": str(exc)})

    support = {}
    rows = []
    for d in data:
        with rasterio.open(d['local_cache']) as src:
            same_grid = bool(src.shape == grid.shape and src.crs == grid.crs and src.transform == grid.transform)
            count = src.count
            dtype = src.dtypes[0]
            a = src.read(1)
        if not same_grid or count != 1:
            errors.append({"site": d['site'], "error": "grid or band-count mismatch"})
            continue
        finite = np.isfinite(a)
        v = a[finite]
        in_range = bool(v.size and v.min() >= 0 and v.max() <= 1)
        inside_finite = bool(finite[fp].all())
        b = finite & (a > 0) & fp
        support[d['site']] = b
        canonical = np.where(finite & fp, a, 0).astype('<f4', copy=False)
        rows.append({
            "site": d['site'], "filename": Path(d['path']).name,
            "owner_git_url": f"https://github.com/{OWNER}/{d['site']}/blob/{d['commit']}/{d['path']}",
            "pages_download_url": f"https://{OWNER}.github.io/{d['site']}/{d['path']}",
            "commit": d['commit'], "git_blob_sha1": d['git_blob_sha1'], "sha256": d['sha256'],
            "decoded_footprint_sha256": hashlib.sha256(canonical[fp].tobytes()).hexdigest(),
            "prompt_reported_claim": d['reported_claim'],
            "method_summary": d['method_summary'],
            "method_evidence": "Owner-described construction except explicitly measured support identities; not an independently rebuilt model.",
            "score_evidence": "USER-REPORTED claim; no submission-page receipt found; not ORGANIZER-CONFIRMED",
            "estimated_leaderboard_score": None,
            "prediction_support_pixels": int(b.sum()),
            "local_format": {"grid_matches_owner_mirror": same_grid, "bands": count,
                "dtype": dtype, "all_finite": bool(finite.all()),
                "inside_footprint_finite": inside_finite, "finite_values_in_0_1": in_range,
                "strict_all_finite_range_policy_pass": bool(same_grid and count == 1 and dtype == 'float32' and finite.all() and in_range)},
        })
        del a, canonical

    yy, xx = np.ogrid[-3:4, -3:4]
    kernel = yy * yy + xx * xx <= 9
    halos = {site: binary_dilation(mask, structure=kernel) for site, mask in support.items()}
    previous_path = ROOT / 'docs/downloads/apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif'
    previous = None
    previous_sha = None
    if previous_path.is_file():
        with rasterio.open(previous_path) as ds:
            if ds.count != 1 or ds.shape != grid.shape or ds.crs != grid.crs or ds.transform != grid.transform:
                errors.append({'site': 'ApartGEMSDOE1 prior file', 'error': 'grid or band-count mismatch'})
            else:
                candidate = ds.read(1)
                previous = np.isfinite(candidate) & (candidate > 0) & fp
                previous_sha = hashlib.sha256(previous_path.read_bytes()).hexdigest()
    for row in rows:
        site = row['site']
        mine = support[site]
        pairs = {other: float(halo[mine].mean()) if mine.any() else None
                 for other, halo in halos.items() if other != site}
        usable = {k: v for k, v in pairs.items() if v is not None}
        nearest = max(usable, key=usable.get) if usable else None
        row['max_forward_overlap_3px_among_focus9'] = usable.get(nearest) if nearest else None
        row['closest_focus_site'] = nearest
        row['unique_among_focus9'] = (False if nearest and usable[nearest] > 0.70
                                     else None)  # partial inventory can prove failure, never universal uniqueness
        row['prior_candidate_forward_overlap_3px'] = (float(halos[site][previous].mean())
                                                       if previous is not None and previous.any() else None)
        row['decision'] = 'DO NOT RESUBMIT: historical file, not a new candidate'

    proof = None
    if all(s in support for s in ('GEMSDOE25', 'GEMSDOE30', 'GEMSDOE32')):
        dcat = distance_transform_edt(~grid.catalogue)
        predicted_b2 = support['GEMSDOE25'] & (dcat > 2.0)
        proof = {
            "b2_identity": "GEMSDOE32 support == GEMSDOE25 support AND distance-to-catalogue > 2 pixels",
            "xor_differing_pixels": int(np.count_nonzero(predicted_b2 ^ support['GEMSDOE32'])),
            "gems25_vs_gems30_support_xor": int(np.count_nonzero(support['GEMSDOE25'] ^ support['GEMSDOE30'])),
            "interpretation": "Geometry does not establish the cause of the user-reported scores; hidden test labels and receipts are unavailable."
        }

    report = {"generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "PIXEL-EXACT MIRROR AUDIT; USER CLAIMS ARE NOT RECEIPTS",
        "scope": "Only the nine historical files named in the prompt, not a complete site or organizer inventory.",
        "prior_candidate_sha256": previous_sha,
        "fetched_and_checked": len(rows), "errors": errors, "sites": rows, "geometry_proof": proof}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "checked": len(rows), "errors": errors, "geometry_proof": proof}, indent=2))
    return 1 if errors or len(rows) != len(manifest) else 0


if __name__ == "__main__":
    raise SystemExit(main())
