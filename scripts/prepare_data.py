#!/usr/bin/env python3
"""Restore and hash-check pinned *owner-mirror* bytes; not organizer authentication.

Pinned mirror features may describe USGS, DOE or Census source data, but their
scientific derivation and licenses have not been independently reconstructed.
Some pins are historical first-observed digests rather than official checksums.
Large binaries and band caches stay in git-ignored `.cache/`.
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
        "ref": "822a0ce5546c7b6749cdd82eb145b6b3e616603d",
        "path": "data/external/derived_sgmc_faults_100m.tif",
        "sha256": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
        "official_source": "https://pubs.usgs.gov/ds/1052/",
    },
    {
        "name": "sgmc_faults_100m.tif",
        "repo": "buffedlizard55-lab/57GEMSDOE",
        "ref": "822a0ce5546c7b6749cdd82eb145b6b3e616603d",
        "path": "data/external/sgmc_faults_100m.tif",
        "sha256": "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c",
        "official_source": "https://pubs.usgs.gov/ds/1052/",
    },
    {
        "name": "lidar_scarp_features_u8.tif",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/lidar_scarp_features_u8.tif",
        "sha256": "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568",
        "official_source": "https://www.usgs.gov/3d-elevation-program",
    },
    {
        "name": "lidar_scarp_features.json",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/lidar_scarp_features.json",
        "sha256": "9ef0df6e87598a8b0cd52fe821661e5fdb3a00568c5d9b1c5d61fd6b242dcd41",
        "official_source": "https://www.usgs.gov/3d-elevation-program",
    },
    {
        "name": "geodawn_rad_u8.tif",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/geodawn_rad_u8.tif",
        "sha256": "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
        "official_source": "https://www.sciencebase.gov/catalog/item/61955dcad34eb622f6908d6c",
    },
    {
        "name": "geodawn_rad.json",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/geodawn_rad.json",
        "sha256": "d917fd08f89c160d2a0ba91af9c3321c8c8b5677fcdba39b10e684384cbc7488",
        "official_source": "https://www.sciencebase.gov/catalog/item/61955dcad34eb622f6908d6c",
    },
    {
        "name": "geodawn_extensions_u8.tif",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/geodawn_extensions_u8.tif",
        "sha256": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
        "official_source": "https://www.sciencebase.gov/catalog/item/61955dcad34eb622f6908d6c",
    },
    {
        "name": "geodawn_extensions.json",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/geodawn_extensions.json",
        "sha256": "56556f24c051043fd7a85587786118f8064624f2ad0604aaa3e6614f1a9f6d2f",
        "official_source": "https://www.sciencebase.gov/catalog/item/61955dcad34eb622f6908d6c",
    },
    {
        "name": "gdr_wellspring_in_footprint.csv",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/gdr_wellspring_in_footprint.csv",
        "sha256": "122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea",
        "official_source": "https://gdr.openei.org/submissions/1391",
    },
    {
        "name": "2m_temperature_probe_INGENIOUS_regional_data.zip",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/2m_temperature_probe_INGENIOUS_regional_data.zip",
        "sha256": "1301f70d230058e616ea5d34d1c7a32fabf7d49198172f376c59c89bd652eca3",
        "official_source": "https://gdr.openei.org/submissions/1391",
    },
    {
        "name": "paleo_geothermal_regional.zip",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/paleo_geothermal_regional.zip",
        "sha256": "faffcf697f32dbbf6cbb317cd1effb3e305538ce38eb239d72d0c6fa071e91ca",
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
    {
        "name": "topo_10m_derived_100m_u8.tif",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "ref": "156e7486b5b22c34bf9d7b8d90a714545d63f15a",
        "path": "data/external/topo_10m_derived_100m_u8.tif",
        "sha256": "a6398d9950965dec6aae6ccecdaa6ced48645d133eab222cbdd11def9bdabfa4",
        "official_source": "https://www.usgs.gov/3d-elevation-program",
    },
    {
        "name": "topo_10m_derived_100m_u8.manifest.json",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "ref": "156e7486b5b22c34bf9d7b8d90a714545d63f15a",
        "path": "data/external/topo_10m_derived_100m_u8.manifest.json",
        "sha256": "181d5527ba7ed2990031918a8b6c9d5d94e3998b2daf656de0c33322ca94120a",
        "official_source": "https://www.usgs.gov/3d-elevation-program",
    },
    {
        "name": "dem10_chi_100m_i16.tif",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "ref": "156e7486b5b22c34bf9d7b8d90a714545d63f15a",
        "path": "data/external/dem10_chi_100m_i16.tif",
        "sha256": "8897ba9c30ef1cd7ad5f23c16c6dfd7bb070e7e757f36fd9486eb45edfd973a5",
        "official_source": "https://www.usgs.gov/3d-elevation-program",
    },
    {
        "name": "gdr_volcanic_vents_in_footprint.csv",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/gdr_volcanic_vents_in_footprint.csv",
        "sha256": "f91bafbaccaaf2754e71d60434fc0f9eb2c7b880c6e714883f4974542ff6a0bf",
        "official_source": "https://gdr.openei.org/submissions/1391",
    },
    {
        "name": "acquisition_block_id_100m.tif",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "9da8a18381e179530c3b878d073314feaa26a20c",
        "path": "data/external/audit_sources/acquisition_block_id_100m.tif",
        "sha256": "2c0785c4b3ec46c734d1be7a7aedbb3e816201100ab358033a3af074418c894a",
        "official_source": "https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7",
    },
]

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
    if (not isinstance(expected_sha, str) or len(expected_sha) != 64
            or any(c not in '0123456789abcdef' for c in expected_sha)):
        raise ValueError(f'refusing unpinned source: {repo}:{source}')
    if dest.is_file() and sha256(dest) == expected_sha:
        if expected_bytes is not None and dest.stat().st_size != expected_bytes:
            raise ValueError(f'cached size mismatch on {source}')
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
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() or link.exists():
        if link.is_symlink() and os.readlink(link) == target_rel:
            return
        raise FileExistsError(f'refusing to replace existing data path: {link}')
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
        part_receipts = [{
            "part": f"gems-geodawn-numerical-features.tif.part-{i:03d}",
            "bytes": PARTS[i][0],
            "sha256": PARTS[i][1],
        } for i in range(5)]

    ensure_symlink(root / "data/official/training_features.tif", "../../.cache/training_features.tif")
    ensure_symlink(root / "data/training_features.tif", "../.cache/training_features.tif")
    return {
        "source_repo": BRIDGE_REPO,
        "source_commit": BRIDGE_COMMIT,
        "assembled_sha256": TRAINING_FEATURES_SHA256,
        "bytes": cache_target.stat().st_size,
        "parts": part_receipts,
        "verified": True,
        "verification_scope": "matches pinned owner-mirror bytes, not an organizer-origin receipt",
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
    provenance_file = cache_dir / 'cache_provenance.json'
    try:
        previous = json.loads(provenance_file.read_text())
    except (OSError, ValueError):
        previous = {}
    previous_hashes = previous.get('band_sha256', {}) if previous.get('source_sha256') == source_hash else {}
    bands = []
    with rasterio.open(feature_tif) as src, rasterio.open(sample_tif) as sample:
        if src.shape != sample.shape or src.crs != sample.crs or src.transform != sample.transform:
            raise ValueError("training_features.tif grid does not match sample_submission.tif")
        grid_metadata = {'shape': list(src.shape), 'crs': str(src.crs),
                         'transform': list(tuple(src.transform)[:6])}
        fp = np.isfinite(sample.read(1))
        for number, description in enumerate(src.descriptions, 1):
            path = cache_dir / f"band-{number:02d}.npy"
            expected_cache_hash = previous_hashes.get(str(number))
            if path.is_file() and expected_cache_hash and sha256(path) == expected_cache_hash:
                try:
                    arr_existing = np.load(path, mmap_mode="r", allow_pickle=False)
                    if arr_existing.shape == src.shape and arr_existing.dtype == np.float32:
                        n_missing = int((~np.isfinite(arr_existing)).sum())
                        n_fp_missing = int((~np.isfinite(arr_existing[fp])).sum())
                        bands.append({
                            "band": number,
                            "description": description,
                            "cache_file": str(path.relative_to(root)),
                            "missing_pixels_total": n_missing,
                            "sentinel_or_missing_in_footprint": n_fp_missing,
                            "sha256": expected_cache_hash,
                        })
                        continue
                except (OSError, ValueError):
                    pass  # a corrupt cache is rebuilt from the pinned source
            a = np.lib.format.open_memmap(path, mode="w+", dtype="float32", shape=src.shape)
            n_missing = 0
            n_fp_missing = 0
            for y in range(0, src.height, 256):
                h = min(256, src.height - y)
                b = src.read(number, window=Window(0, y, src.width, h), masked=True).filled(np.nan).astype("float32")
                # Represent extreme feature sentinels as NaN; the writer must still validate model output.
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
        **grid_metadata,
        "count": len(bands),
        "bands": bands,
        "irregularity_flags": [
            {
                "id": "IR-SENTINEL-F32MIN",
                "detail": "Non-finite and extreme source values are converted to NaN in the feature cache; per-band counts above are measured, not a guarantee about model outputs.",
            },
            {
                "id": "IR-BAND6-TC-AMBIGUOUS",
                "detail": "The mirror's description and physical interpretation of band 6 require independent source-metadata verification; do not assume a particular measurement.",
            },
        ],
        "provenance": "Hash-verified public mirror bridge; organizer DrivenData login receipt not present in sandbox.",
    }
    provenance_file.write_text(json.dumps({
        'source_sha256': source_hash,
        'band_sha256': {str(b['band']): b['sha256'] for b in bands},
    }, indent=2, allow_nan=False) + '\n')
    # Regenerated receipts go to git-ignored .cache/receipts/. The tracked
    # evidence/feature_cache.json is audited and carries historical-only warnings
    # that a regeneration would silently drop, so it is never overwritten here.
    receipts = root / ".cache" / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    (receipts / "feature_cache.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true", help="Fetch missing core, external, and 10m 3DEP layers")
    ap.add_argument("--cache-bands", action=argparse.BooleanOptionalAction, default=True,
                    help="Extract sanitized float32 band caches; use --no-cache-bands to skip")
    args = ap.parse_args()

    receipt: dict = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "OWNER-MIRROR-INTEGRITY",
        "provenance_note": "SHA-256 checks verify pinned GitHub mirror bytes only. Derived layers have not been independently rebuilt or authenticated against official sources; no organizer receipt is available.",
        "core_files": [],
        "external_files": [],
        "dem10_files": [],
    }

    for rel, (repo, ref, src_path, expected_sha) in CORE_PINS.items():
        dest = ROOT / rel
        if args.fetch and (not dest.exists() or sha256(dest) != expected_sha):
            fetch_raw(repo, src_path, ref, dest, expected_sha)
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
    if args.fetch:
        receipt["training_features_assembly"] = assemble_features(ROOT)
    else:
        if not tf_path.is_file():
            raise FileNotFoundError('training feature cache missing; use --fetch to restore the pinned mirror')
        actual_tf_sha = sha256(tf_path)
        if actual_tf_sha != TRAINING_FEATURES_SHA256:
            raise ValueError('cached training feature SHA256 differs from the pinned mirror')
        ensure_symlink(ROOT / "data/official/training_features.tif", "../../.cache/training_features.tif")
        ensure_symlink(ROOT / "data/training_features.tif", "../.cache/training_features.tif")
        receipt["training_features_assembly"] = {
            "assembled_sha256": actual_tf_sha,
            "bytes": tf_path.stat().st_size,
            "verified": True,
            "verification_scope": "matches pinned owner-mirror bytes, not an organizer-origin receipt",
        }

    ext_dir = ROOT / ".cache/external"
    ext_dir.mkdir(parents=True, exist_ok=True)
    for item in EXTERNAL_PINS:
        dest = ext_dir / item["name"]
        if args.fetch and (
            not dest.exists() or sha256(dest) != item["sha256"]
        ):
            fetch_raw(item["repo"], item["path"], item["ref"], dest, item["sha256"])
        if not dest.is_file():
            raise FileNotFoundError(f"External mirror missing: {item['name']}; use --fetch")
        if not item["sha256"]:
            raise ValueError(f"External mirror has no trusted SHA256 pin: {item['name']}")
        actual = sha256(dest)
        if actual != item["sha256"]:
            raise ValueError(f"External file hash mismatch: {item['name']}")
        receipt["external_files"].append({
            "name": item["name"],
            "bytes": dest.stat().st_size,
            "sha256": actual,
            "official_source": item["official_source"],
            "verified": True,
            "verification_scope": "matches pinned owner-mirror bytes; official derivation not independently verified",
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
            if not dest.is_file():
                raise FileNotFoundError(f"DEM10 mirror missing: {ch}; use --fetch")
            actual = sha256(dest)
            if actual != dig:
                raise ValueError(f"DEM10 hash mismatch: {ch}")
            receipt["dem10_files"].append({"channel": ch, "bytes": dest.stat().st_size, "sha256": actual, "verified": True})

    receipt["all_pins_verified"] = bool(
        len(receipt["core_files"]) == len(CORE_PINS)
        and receipt["training_features_assembly"]["verified"]
        and len(receipt["external_files"]) == len(EXTERNAL_PINS)
        and len(receipt["dem10_files"]) == len(DEM10_WANTED)
        and all(x["verified"] for x in receipt["core_files"] + receipt["external_files"] + receipt["dem10_files"])
    )
    if not receipt["all_pins_verified"]:
        raise RuntimeError('incomplete mirror verification; refusing a success receipt')
    # Written to git-ignored .cache/receipts/ only; tracked audited evidence and the
    # tracked data/manifest.json are not overwritten by a fetch (see review 2026-10-31, I-6).
    receipts = ROOT / ".cache" / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    (receipts / "data_preparation.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    (receipts / "manifest.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")

    if args.cache_bands:
        band_report = cache_bands(ROOT)
        print(f"[prepare_data] Cached & verified {band_report['count']} bands in .cache/features/")

    print("[prepare_data] ALL PINS & CACHES VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
