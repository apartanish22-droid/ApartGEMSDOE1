#!/usr/bin/env python3
"""Restore, SHA-256-verify, and cache the DOE GEMS competition & public-domain feature stack.

Reuses the canonical 57GEMSDOE pinned bridge (buffedlizard55-lab/6GEMSDOE @ e2fe3f41c6)
plus hash-pinned public-domain USGS 3DEP (1m LiDAR + seamless 10m DEM), USGS GeoDAWN
radiometric/magnetic extensions, DOE GDR #1391 INGENIOUS thermal/geochemical tables,
USGS SGMC bedrock fault layers, and US Census TIGER 2024 road distance rasters.

All large binary rasters and band caches reside in git-ignored `.cache/` with clean
relative symlinks in `data/` so Git and turn snapshots remain lightweight.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

BRIDGE_REPO = "buffedlizard55-lab/6GEMSDOE"
BRIDGE_COMMIT = "e2fe3f41c6f5dd2dcb2fc91958ee67698f114ada"

CORE_PINS = {
    "data/bridge/existing_faults.tif": (
        BRIDGE_REPO,
        BRIDGE_COMMIT,
        "data/bridge/existing_faults.tif",
        "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    ),
    "data/bridge/sample_submission.tif": (
        BRIDGE_REPO,
        BRIDGE_COMMIT,
        "data/bridge/example_submission.tif",
        "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    ),
    "data/official/labels.tif": (
        BRIDGE_REPO,
        BRIDGE_COMMIT,
        "data/bridge/existing_faults.tif",
        "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    ),
    "data/official/existing_faults.tif": (
        BRIDGE_REPO,
        BRIDGE_COMMIT,
        "data/bridge/existing_faults.tif",
        "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    ),
    "data/official/sample_submission.tif": (
        BRIDGE_REPO,
        BRIDGE_COMMIT,
        "data/bridge/example_submission.tif",
        "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    ),
}

TRAINING_FEATURES_SHA256 = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
PARTS = [
    (94371840, "0a330f8951af6c921029e25c84a579319d2db554d62d30d894d6ddc97f98cff7"),
    (94371840, "3c98037b2c997e3bbfcdfc2d9a982e8b820a77410dd7404b05cdb80594922c50"),
    (94371840, "c375c4dbc40c59bbaece572b5e348700b75935f9a30c879c82b6417e0836f31c"),
    (94371840, "b164159e6d0cb2595bc9f63a948af2646b124114a9c5921880c7516092137320"),
    (41425484, "fa0a6f9c936fac1d6f20ca37f5929b2d60bf7a80f3d477dcab886f941aee2696"),
]

EXTERNAL_PINS = [
    {
        "name": "derived_sgmc_faults_100m.tif",
        "repo": "buffedlizard55-lab/57GEMSDOE",
        "ref": "HEAD",
        "path": "data/external/derived_sgmc_faults_100m.tif",
        "sha256": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
        "official_source": "https://pubs.usgs.gov/ds/1052/",
    },
    {
        "name": "sgmc_faults_100m.tif",
        "repo": "buffedlizard55-lab/57GEMSDOE",
        "ref": "HEAD",
        "path": "data/external/sgmc_faults_100m.tif",
        "sha256": "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c",
        "official_source": "https://pubs.usgs.gov/ds/1052/",
    },
    {
        "name": "lidar_scarp_features_u8.tif",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/lidar_scarp_features_u8.tif",
        "sha256": None,
        "official_source": "https://www.usgs.gov/3d-elevation-program",
    },
    {
        "name": "lidar_scarp_features.json",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/lidar_scarp_features.json",
        "sha256": None,
        "official_source": "https://www.usgs.gov/3d-elevation-program",
    },
    {
        "name": "geodawn_rad_u8.tif",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/geodawn_rad_u8.tif",
        "sha256": None,
        "official_source": "https://www.sciencebase.gov/catalog/item/61955dcad34eb622f6908d6c",
    },
    {
        "name": "geodawn_rad.json",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/geodawn_rad.json",
        "sha256": None,
        "official_source": "https://www.sciencebase.gov/catalog/item/61955dcad34eb622f6908d6c",
    },
    {
        "name": "geodawn_extensions_u8.tif",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/geodawn_extensions_u8.tif",
        "sha256": None,
        "official_source": "https://www.sciencebase.gov/catalog/item/61955dcad34eb622f6908d6c",
    },
    {
        "name": "geodawn_extensions.json",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/geodawn_extensions.json",
        "sha256": None,
        "official_source": "https://www.sciencebase.gov/catalog/item/61955dcad34eb622f6908d6c",
    },
    {
        "name": "gdr_wellspring_in_footprint.csv",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/gdr_wellspring_in_footprint.csv",
        "sha256": None,
        "official_source": "https://gdr.openei.org/submissions/1391",
    },
    {
        "name": "2m_temperature_probe_INGENIOUS_regional_data.zip",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/2m_temperature_probe_INGENIOUS_regional_data.zip",
        "sha256": None,
        "official_source": "https://gdr.openei.org/submissions/1391",
    },
    {
        "name": "paleo_geothermal_regional.zip",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/paleo_geothermal_regional.zip",
        "sha256": None,
        "official_source": "https://gdr.openei.org/submissions/1391",
    },
    {
        "name": "tiger_road_distance_m.tif",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "9da8a18381e179530c3b878d073314feaa26a20c",
        "path": "data/external/audit_sources/tiger_road_distance_m.tif",
        "sha256": "e5350423508968fa2d32b0a6ae0d3fb4ae3ea645e3b8736f0c8e7ad9ff2f2988",
        "official_source": "https://www2.census.gov/geo/tiger/TIGER2024/PRISECROADS/",
    },
]

# Hashes measured in the previous mirror-restoration receipt. They pin cached
# bytes; they do not authenticate provenance back to the listed official source.
EXTERNAL_SHA256 = {
    "lidar_scarp_features_u8.tif": "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568",
    "lidar_scarp_features.json": "9ef0df6e87598a8b0cd52fe821661e5fdb3a00568c5d9b1c5d61fd6b242dcd41",
    "geodawn_rad_u8.tif": "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
    "geodawn_rad.json": "d917fd08f89c160d2a0ba91af9c3321c8c8b5677fcdba39b10e684384cbc7488",
    "geodawn_extensions_u8.tif": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
    "geodawn_extensions.json": "56556f24c051043fd7a85587786118f8064624f2ad0604aaa3e6614f1a9f6d2f",
    "gdr_wellspring_in_footprint.csv": "122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea",
    "2m_temperature_probe_INGENIOUS_regional_data.zip": "1301f70d230058e616ea5d34d1c7a32fabf7d49198172f376c59c89bd652eca3",
    "paleo_geothermal_regional.zip": "faffcf697f32dbbf6cbb317cd1effb3e305538ce38eb239d72d0c6fa071e91ca",
}
for _item in EXTERNAL_PINS:
    if _item["sha256"] is None:
        _item["sha256"] = EXTERNAL_SHA256[_item["name"]]

DEM10_REPO = "buffedlizard55-lab/GEMSDOE10"
DEM10_REF = "91d6566ecc86141eca9e81c259057678930e596f"
DEM10_WANTED = {
    "dem10_onesided3": "bca9faf8e0c572ecb1e77b6c94b0cb96c41e824873cb7747e0ece28b531598d2",
    "dem10_onesided": "02d1d241de9534d307f314d0b2f8a857ceb1ce0d099fd7dee8872a83bd0271f8",
    "dem10_slope_max": "fd46738e9a58a6f40c130c3c70f645525dbfc12d27b6ed149e596e6a379cbfaa",
    "dem10_hgm50_max": "1cca42538ec0c91951b578136893eb5d90cd1414c45257d2a72ebe80b29f0f40",
    "dem10_curv_absmax": "58e82f1301032b46b10344b9299b83e6ce5bed1ca83e320f078fa57321bff632",
    "dem10_resid_range": "bbcf8a462ace31a80964ba8a7ab76fcbcb347deb4f4d2919166b3eda5c721b0c",
    "dem10_valid_frac": "35d7ef0719bfed93f9aed927afd8c51882283fc7316cab0f8c219c9302b92122",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_raw(repo: str, source: str, ref: str, dest: Path,
              expected_sha: str | None = None, expected_bytes: int | None = None) -> None:
    if dest.exists() and (expected_sha is None or sha256(dest) == expected_sha):
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".partial")
    endpoint = f"repos/{repo}/contents/{source}?ref={ref}"
    try:
        with tmp.open("wb") as stream:
            res = subprocess.run(
                ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw+json"],
                stdout=stream,
                stderr=subprocess.PIPE,
                timeout=240,
                check=False,
            )
        if res.returncode != 0:
            raise RuntimeError(f"gh api failed for {repo}:{source}: {res.stderr.decode()[:200]}")
        if expected_bytes is not None and tmp.stat().st_size != expected_bytes:
            raise ValueError(f"size mismatch on {source}: {tmp.stat().st_size} != {expected_bytes}")
        if expected_sha is not None and sha256(tmp) != expected_sha:
            raise ValueError(f"sha256 mismatch on {source}: {sha256(tmp)} != {expected_sha}")
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)


def ensure_symlink(link: Path, target_rel: str) -> None:
    """Create a convenience link without replacing user-provided data."""
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        if os.readlink(link) == target_rel:
            return
        raise FileExistsError(f"refusing to replace an existing symlink: {link}")
    if link.exists():
        raise FileExistsError(f"refusing to replace an existing data file or directory: {link}")
    link.symlink_to(target_rel)


def assemble_features(root: Path) -> dict:
    cache_target = root / ".cache" / "training_features.tif"
    if not (cache_target.exists() and sha256(cache_target) == TRAINING_FEATURES_SHA256):
        part_dir = root / ".cache" / "source_parts"
        paths = [part_dir / f"gems-geodawn-numerical-features.tif.part-{i:03d}" for i in range(5)]

        def dl(i: int) -> dict:
            sz, dig = PARTS[i]
            fetch_raw(BRIDGE_REPO, f"data/bridge/{paths[i].name}", BRIDGE_COMMIT, paths[i], dig, sz)
            return {"part": paths[i].name, "bytes": sz, "sha256": dig}

        with ThreadPoolExecutor(max_workers=4) as pool:
            part_receipts = list(pool.map(dl, range(5)))
        tmp = cache_target.with_suffix(".tif.partial")
        cache_target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with tmp.open("wb") as out:
                for p in paths:
                    with p.open("rb") as inp:
                        shutil.copyfileobj(inp, out, length=1 << 20)
            if sha256(tmp) != TRAINING_FEATURES_SHA256:
                raise ValueError("reassembled training_features.tif hash mismatch")
            os.replace(tmp, cache_target)
        finally:
            tmp.unlink(missing_ok=True)
    else:
        part_receipts = [{"part": f"part-{i:03d}", "bytes": PARTS[i][0], "sha256": PARTS[i][1]} for i in range(5)]

    ensure_symlink(root / "data/official/training_features.tif", "../../.cache/training_features.tif")
    ensure_symlink(root / "data/training_features.tif", "../.cache/training_features.tif")
    return {
        "source_repo": BRIDGE_REPO,
        "source_commit": BRIDGE_COMMIT,
        "assembled_sha256": TRAINING_FEATURES_SHA256,
        "bytes": cache_target.stat().st_size,
        "parts": part_receipts,
    }


def cache_bands(root: Path) -> dict:
    import numpy as np
    import rasterio
    from rasterio.windows import Window

    feature_tif = root / "data/official/training_features.tif"
    sample_tif = root / "data/official/sample_submission.tif"
    cache_dir = root / ".cache/features"
    cache_dir.mkdir(parents=True, exist_ok=True)

    source_hash = sha256(feature_tif)
    if source_hash != TRAINING_FEATURES_SHA256:
        raise ValueError("training feature stack does not match its pinned mirror SHA-256")
    prior_hashes = {}
    prior_receipt = root / "evidence/feature_cache.json"
    if prior_receipt.exists():
        old = json.loads(prior_receipt.read_text())
        if old.get("source_sha256") == source_hash:
            prior_hashes = {b["band"]: b["sha256"] for b in old.get("bands", []) if "sha256" in b}

    bands = []
    with rasterio.open(feature_tif) as src, rasterio.open(sample_tif) as sample:
        if src.shape != sample.shape or src.crs != sample.crs or src.transform != sample.transform:
            raise ValueError("training_features.tif grid does not match sample_submission.tif")
        source_grid = {"shape": list(src.shape), "crs": str(src.crs), "transform": list(tuple(src.transform)[:6])}
        fp = np.isfinite(sample.read(1))
        for number, description in enumerate(src.descriptions, 1):
            path = cache_dir / f"band-{number:02d}.npy"
            if path.exists() and prior_hashes.get(number) and sha256(path) == prior_hashes[number]:
                arr_existing = np.load(path, mmap_mode="r")
                if arr_existing.shape == src.shape and arr_existing.dtype == np.float32:
                    n_missing = int((~np.isfinite(arr_existing)).sum())
                    n_fp_missing = int((~np.isfinite(arr_existing[fp])).sum())
                    bands.append({
                        "band": number,
                        "description": description,
                        "cache_file": str(path.relative_to(root)),
                        "missing_pixels_total": n_missing,
                        "sentinel_or_missing_in_footprint": n_fp_missing,
                        "sha256": sha256(path),
                    })
                    continue
            a = np.lib.format.open_memmap(path, mode="w+", dtype="float32", shape=src.shape)
            n_missing = 0
            n_fp_missing = 0
            for y in range(0, src.height, 256):
                h = min(256, src.height - y)
                b = src.read(number, window=Window(0, y, src.width, h), masked=True).filled(np.nan).astype("float32")
                # Represent GDAL Float32-min and other extreme input sentinels as missing.
                # Output probabilities still require independent validation.
                bad = (~np.isfinite(b)) | (np.abs(b) > 1e30)
                b[bad] = np.nan
                n_missing += int(bad.sum())
                n_fp_missing += int((bad & fp[y : y + h]).sum())
                a[y : y + h] = b
            a.flush()
            del a
            bands.append({
                "band": number,
                "description": description,
                "cache_file": str(path.relative_to(root)),
                "missing_pixels_total": n_missing,
                "sentinel_or_missing_in_footprint": n_fp_missing,
                "sha256": sha256(path),
            })

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "DATA-MEASUREMENT",
        "source_sha256": source_hash,
        **source_grid,
        "count": len(bands),
        "bands": bands,
        "irregularity_flags": [
            {
                "id": "IR-SENTINEL-F32MIN",
                "detail": "Input band cache maps non-finite and extreme-magnitude cells to NaN. See each band's measured in-footprint missing count; model inputs must impute them explicitly, and output validity requires its own check.",
            },
            {
                "id": "IR-BAND6-TC-RADIOMETRIC",
                "detail": "The mirrored band-6 description conflicts with a prior radiometric interpretation. Values alone do not establish physical units or identity; verify authoritative metadata before using this band scientifically.",
            },
        ],
        "provenance": "Hash-verified public mirror bridge; organizer DrivenData login receipt not present in sandbox.",
    }
    (root / "evidence").mkdir(exist_ok=True)
    (root / "evidence/feature_cache.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true", help="Fetch missing core, external, and 10m 3DEP layers")
    ap.add_argument("--cache-bands", action="store_true", default=True, help="Extract 19 float32 band caches")
    args = ap.parse_args()

    receipt: dict = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "OWNER-MIRROR-INTEGRITY",
        "provenance_note": "SHA-256 pins verify selected owner-mirror bytes, not their identity with authenticated organizer downloads or the listed official source releases.",
        "core_files": [],
        "external_files": [],
        "dem10_files": [],
    }

    for rel, (repo, ref, src_path, expected_sha) in CORE_PINS.items():
        dest = ROOT / rel
        if args.fetch and not dest.exists():
            fetch_raw(repo, src_path, ref, dest, expected_sha)
        if not dest.is_file():
            raise FileNotFoundError(f"missing core file: {rel}")
        # Never overwrite an existing user-provided file just because it does
        # not match a third-party mirror. Stop and report the mismatch.
        actual = sha256(dest)
        if actual != expected_sha:
            raise ValueError(f"Core file hash mismatch: {rel}")
        receipt["core_files"].append({"path": rel, "bytes": dest.stat().st_size, "sha256": actual, "verified": True})

    # Convenience symlinks in data/
    ensure_symlink(ROOT / "data/labels.tif", "official/labels.tif")
    ensure_symlink(ROOT / "data/existing_faults.tif", "official/existing_faults.tif")
    ensure_symlink(ROOT / "data/sample_submission.tif", "official/sample_submission.tif")
    ensure_symlink(ROOT / "data/external", "../.cache/external")
    ensure_symlink(ROOT / "data/dem10", "../.cache/dem10")

    tf_path = ROOT / ".cache/training_features.tif"
    if args.fetch or not tf_path.exists():
        receipt["training_features_assembly"] = assemble_features(ROOT)
    else:
        actual_training_sha = sha256(tf_path)
        if actual_training_sha != TRAINING_FEATURES_SHA256:
            raise ValueError("cached training feature stack does not match its pinned mirror SHA-256")
        ensure_symlink(ROOT / "data/official/training_features.tif", "../../.cache/training_features.tif")
        ensure_symlink(ROOT / "data/training_features.tif", "../.cache/training_features.tif")
        receipt["training_features_assembly"] = {
            "assembled_sha256": actual_training_sha,
            "bytes": tf_path.stat().st_size,
            "verified": True,
        }

    ext_dir = ROOT / ".cache/external"
    ext_dir.mkdir(parents=True, exist_ok=True)
    for item in EXTERNAL_PINS:
        dest = ext_dir / item["name"]
        if args.fetch and not dest.exists():
            fetch_raw(item["repo"], item["path"], item["ref"], dest, item["sha256"])
        if dest.exists():
            actual = sha256(dest)
            if item["sha256"] and actual != item["sha256"]:
                raise ValueError(f"External file hash mismatch: {item['name']}")
            receipt["external_files"].append({
                "name": item["name"],
                "bytes": dest.stat().st_size,
                "sha256": actual,
                "official_source": item["official_source"],
                "verified": True,
            })

    dem10_dir = ROOT / ".cache/dem10"
    dem10_dir.mkdir(parents=True, exist_ok=True)
    if args.fetch:
        def dl_dem10(kv: tuple[str, str]) -> dict:
            ch, dig = kv
            dest = dem10_dir / f"{ch}.f32.npy"
            fetch_raw(DEM10_REPO, f"{ch}.f32.npy", DEM10_REF, dest, dig)
            return {"channel": ch, "bytes": dest.stat().st_size, "sha256": dig, "verified": True}

        with ThreadPoolExecutor(max_workers=4) as pool:
            receipt["dem10_files"] = list(pool.map(dl_dem10, list(DEM10_WANTED.items())))
    else:
        for ch, dig in DEM10_WANTED.items():
            dest = dem10_dir / f"{ch}.f32.npy"
            if dest.exists():
                actual = sha256(dest)
                if actual != dig:
                    raise ValueError(f"DEM10 hash mismatch: {ch}")
                receipt["dem10_files"].append({"channel": ch, "bytes": dest.stat().st_size, "sha256": actual, "verified": True})

    missing_external = [x["name"] for x in EXTERNAL_PINS if not (ext_dir / x["name"]).is_file()]
    missing_dem10 = [name for name in DEM10_WANTED if not (dem10_dir / f"{name}.f32.npy").is_file()]
    receipt["missing_external"] = missing_external
    receipt["missing_dem10"] = missing_dem10
    receipt["all_pins_verified"] = not (missing_external or missing_dem10)
    receipt["official_origin_authenticated"] = False
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence/data_preparation.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    (ROOT / "data/manifest.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")

    if args.cache_bands:
        band_report = cache_bands(ROOT)
        print(f"[prepare_data] Cached & verified {band_report['count']} bands in .cache/features/")

    if receipt["all_pins_verified"]:
        print("[prepare_data] All listed mirror pins are present and hash-verified; official origin is not authenticated.")
    else:
        print(f"[prepare_data] Core stack available; missing {len(missing_external)} external and {len(missing_dem10)} DEM10 files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
