#!/usr/bin/env python3
"""Literal uniqueness gate for a candidate GeoTIFF against the mirror registry.

Reuses the shared gate ``gems57.uniqueness.compare_array_to_registry`` (rho > 0.90,
3-px dot overlap > 70%, byte/decoded identity). This script only builds the registry
index from ``evidence/registry_inventory.json`` and records every excluded raster
with its reason. Exclusions are listed, never silent.

Which rasters count as registry submissions?
  * single-band float32 GeoTIFF on the competition grid (EPSG:32611, 3730 x 3292,
    transform 100 m), with at least one positive cell; zip files are unpacked to their
    single TIFF member.
  * Feature rasters, labels and uint8 layers are excluded (listed with the reason).
A submission-like raster that fails the shared checks (for example NaN or out-of-range
values inside the footprint) makes the gate report an invalid row. That blocks the
uniqueness clearance, which is the fail-closed behaviour the protocol requires.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio

from gems57 import load_grid
from gems57.uniqueness import compare_array_to_registry

INVENTORY = ROOT / "evidence" / "registry_inventory.json"
CACHE = ROOT / ".cache" / "registry"
MEMBER_CACHE = ROOT / ".cache" / "registry_members"


def _member_file(zip_cache: Path, member_bytes: bytes, label: str) -> Path:
    MEMBER_CACHE.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(member_bytes).hexdigest()
    out = MEMBER_CACHE / f"{digest}.tif"
    if not out.exists():
        out.write_bytes(member_bytes)
    return out


BLANKET_FRACTION = 0.5


def build_index(inv: dict, grid, *, exclude_blanket: bool = False) -> dict:
    records, excluded, errors = [], [], []
    fp_cells = int(grid.footprint.sum())
    seen_sha: dict[str, str] = {}
    for site in inv["sites"]:
        if site.get("error"):
            errors.append(f"{site['owner']}/{site['repo']}: {site['error']}")
        for r in site.get("rasters", []):
            label = f"{site['owner']}/{site['repo']}:{r['path']}"
            # Sub-KB blobs that GDAL/zipfile cannot open are not rasters. Two kinds were found in
            # the 2026-10-31 full scan: (a) git symlinks, whose blob is only a text target path;
            # (b) a truncated 110-byte TIFF header (smoke test). Each exclusion records the reason.
            # Any other error stays blocking (fail closed).
            if "error" in r and int(r.get("size", 1 << 30)) < 1024:
                blob = CACHE / f"{site['owner']}__{site['repo']}__{r['blob_sha']}"
                head = blob.read_bytes() if blob.exists() else b""
                if head and b"\x00" not in head and head.isascii():
                    reason = f"git symlink or text pointer ({len(head)} bytes): {head.decode()[:120]}"
                elif head[:4] in (b"II*\x00", b"MM\x00*"):
                    reason = f"truncated TIFF header, no image data ({len(head)} bytes; {r['error'][:80]})"
                else:
                    reason = None
                if reason:
                    excluded.append(dict(source=label, reason=reason))
                    continue
            if "error" in r or "skipped" in r:
                errors.append(f"{label}: {r.get('error') or r.get('skipped')}")
                continue
            source_url = r["blob_url"]
            if r["path"].lower().endswith(".zip"):
                z = r.get("zip", {})
                member = z.get("member")
                if not member:
                    excluded.append(dict(source=label, reason="zip without a single TIFF member"))
                    continue
                if not (member.get("dtype") == "float32" and member.get("count") == 1
                        and member.get("grid_matches_template")):
                    excluded.append(dict(source=label, reason="zip member is not a float32 single-band template-grid TIFF"))
                    continue
                if member.get("n_positive", 0) == 0:
                    excluded.append(dict(source=label, reason="zip member has no positive cells"))
                    continue
                if exclude_blanket and member["n_positive"] / fp_cells > BLANKET_FRACTION:
                    excluded.append(dict(source=label, reason=(
                        f"blanket raster (zip member): {member['n_positive']:,} positive cells = "
                        f"{member['n_positive'] / fp_cells:.1%} of footprint (sensitivity exclusion, not the literal gate)")))
                    continue
                cache_zip = CACHE / f"{site['owner']}__{site['repo']}__{r['blob_sha']}"
                if not cache_zip.exists():
                    errors.append(f"{label}: zip blob not cached")
                    continue
                with zipfile.ZipFile(io.BytesIO(cache_zip.read_bytes())) as zf:
                    tif_name = z["tif_members"][0]
                    tif_bytes = zf.read(tif_name)
                sha = hashlib.sha256(tif_bytes).hexdigest()
                path = _member_file(cache_zip, tif_bytes, label)
            else:
                t = r.get("tif")
                if not t:
                    excluded.append(dict(source=label, reason="no TIFF measurement"))
                    continue
                if t.get("dtype") != "float32" or t.get("count") != 1 or not t.get("grid_matches_template"):
                    excluded.append(dict(source=label,
                                         reason=f"not a float32 single-band template-grid raster (dtype={t.get('dtype')}, bands={t.get('count')}, grid_ok={t.get('grid_matches_template')})"))
                    continue
                if t.get("n_positive", 0) == 0:
                    excluded.append(dict(source=label, reason="no positive cells (not a dot submission)"))
                    continue
                if exclude_blanket and t["n_positive"] / fp_cells > BLANKET_FRACTION:
                    excluded.append(dict(source=label, reason=(
                        f"blanket raster: {t['n_positive']:,} positive cells = "
                        f"{t['n_positive'] / fp_cells:.1%} of footprint; its dots are not defined "
                        f"(sensitivity exclusion, not the literal gate)")))
                    continue
                path = CACHE / f"{site['owner']}__{site['repo']}__{r['blob_sha']}"
                sha = r["sha256"]
                if not path.exists():
                    errors.append(f"{label}: blob not cached")
                    continue
            if sha in seen_sha:
                excluded.append(dict(source=label, reason=f"duplicate bytes of {seen_sha[sha]} (kept once)"))
                continue
            seen_sha[sha] = label
            records.append(dict(repo_first=f"{site['owner']}/{site['repo']}", submission=label,
                                sources=[source_url], cache_file=str(path), sha256=sha))
    return dict(rasters=records, excluded=excluded, errors=errors,
                complete_accessible_scan=not errors)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tif", type=Path, help="candidate GeoTIFF")
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--inventory", type=Path, default=INVENTORY)
    ap.add_argument("--exclude-blanket", action="store_true",
                    help="SENSITIVITY ONLY: exclude registry rasters positive over >50%% of the footprint "
                         "(their dot overlap is undefined). Reported as such; not the literal gate.")
    ap.add_argument("--stop-on-duplicate", action="store_true",
                    help="screening mode: stop at the first registry raster that breaks a limit "
                         "(a FAIL is still a FAIL; a PASS always scans every raster)")
    args = ap.parse_args()
    inv = json.loads(args.inventory.read_text())
    grid = load_grid()
    index = build_index(inv, grid, exclude_blanket=args.exclude_blanket)
    with rasterio.open(args.tif) as src:
        array = src.read(1)
    candidate_sha = hashlib.sha256(args.tif.read_bytes()).hexdigest()
    expected = (grid.shape, grid.crs, grid.transform)
    result = compare_array_to_registry(
        array, index, grid.footprint, file_sha256=candidate_sha,
        expected_grid=expected, include_reverse=False, stop_on_duplicate=args.stop_on_duplicate,
        phase="final",
    )
    # Keep the full row table small: summary + the worst rows.
    rows = result.pop("rows")
    rows_sorted = sorted(rows, key=lambda r: -(r.get("my_dots_within_3px_of_theirs") or 0))
    out = dict(
        candidate=str(args.tif), candidate_file_sha256=candidate_sha,
        registry_inventory=str(args.inventory.relative_to(ROOT)),
        registry_inventory_generated_utc=inv.get("generated_utc"),
        registry_sites=inv.get("n_sites"), registry_rasters_inventoried=inv.get("n_rasters"),
        registry_rasters_indexed=len(index["rasters"]),
        registry_excluded=index["excluded"], registry_errors=index["errors"],
        complete_accessible_scan=index["complete_accessible_scan"],
        gate=result,
        top_rows_by_dot_overlap=rows_sorted[:25],
        evidence_class="REGISTRY-MEASUREMENT (mirror files; not organizer data)",
        literal_gate=not args.exclude_blanket,
        sensitivity_exclude_blanket=args.exclude_blanket,
    )
    text = json.dumps(out, indent=1, allow_nan=False, default=float)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(text + "\n")
    print(json.dumps({k: out[k] for k in ("registry_rasters_indexed", "complete_accessible_scan")}, indent=1))
    print(json.dumps({k: result[k] for k in ("unique", "duplicate_count", "worst_dot_overlap",
                                              "worst_overlap_submission", "worst_spearman_full_footprint",
                                              "worst_rho_submission", "missing_or_invalid",
                                              "registry_rasters_checked")}, indent=1, default=float))
    return 0 if result["unique"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
