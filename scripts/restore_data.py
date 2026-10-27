#!/usr/bin/env python3
"""Restore the exact public owner mirrors used by the shared template.

No DrivenData credentials or login bypass. Mirrors are integrity-pinned, NOT
independently organizer-authenticated. Raw rasters remain ignored by Git.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_REPO = "buffedlizard55-lab/GEMSDOE"
ORIGINAL_REF = "c0c06ac82178f26b94fce3397036ef8f12a2f3a0"
MIRROR_REPO = "buffedlizard55-lab/GEMSDOE24"
MIRROR_REF = "07345ea0604953d7efb858d9cfbc21e20c7aca0b"
PRODUCTS = [
    ("data/bridge/labels.tif", "data/bridge/labels.tif", "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    ("data/bridge/sample_submission.tif", "data/bridge/sample_submission.tif", "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
    ("data/external/lidar_scarp_features_u8.tif", "data/external/lidar_scarp_features_u8.tif", "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568"),
    ("data/external/geodawn_rad_u8.tif", "data/external/geodawn_rad_u8.tif", "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682"),
    ("data/external/geodawn_extensions_u8.tif", "data/external/geodawn_extensions_u8.tif", "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b"),
]


def checksum(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def tree(repo, ref):
    output = subprocess.check_output(["gh", "api", f"repos/{repo}/git/trees/{ref}?recursive=1"], text=True, timeout=90)
    obj = json.loads(output)
    if obj.get("truncated"):
        raise ValueError("Refusing a truncated source inventory")
    return {x["path"]: x for x in obj["tree"] if x["type"] == "blob"}


def restore_blob(repo, entry, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = dest.with_suffix(dest.suffix + ".partial")
    try:
        with temp.open("wb") as handle:
            subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw+json",
                            f"repos/{repo}/git/blobs/{entry['sha']}"], stdout=handle, check=True, timeout=180)
        if temp.stat().st_size != entry["size"]:
            raise ValueError(f"Byte size mismatch: {dest}")
        # Streaming Git SHA-1 avoids buffering a 90 MiB part twice.
        digest = hashlib.sha1(b"blob " + str(temp.stat().st_size).encode() + b"\0")
        with temp.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != entry["sha"]:
            raise ValueError(f"Git blob mismatch: {dest}")
        temp.replace(dest)
    finally:
        temp.unlink(missing_ok=True)


def main():
    mirrored = tree(MIRROR_REPO, MIRROR_REF)
    receipt = {"provenance": "public owner mirrors; integrity verified, not organizer-authenticated", "files": []}
    for source, dest_name, expected in PRODUCTS:
        dest = ROOT / dest_name
        if not dest.exists() or checksum(dest) != expected:
            restore_blob(MIRROR_REPO, mirrored[source], dest)
        if checksum(dest) != expected:
            raise ValueError(f"SHA-256 mismatch: {dest_name}")
        receipt["files"].append({"path": dest_name, "sha256": expected, "repo": MIRROR_REPO, "ref": MIRROR_REF, "source_path": source})
        print("Verified", dest_name, flush=True)
    for name in ("geodawn_rad.json", "geodawn_extensions.json", "lidar_scarp_features.json"):
        restore_blob(MIRROR_REPO, mirrored[f"data/external/{name}"], ROOT / f"data/external/{name}")
    training = ROOT / "data/training_features.tif"
    expected = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
    if not training.exists() or checksum(training) != expected:
        original = tree(ORIGINAL_REPO, ORIGINAL_REF)
        parts = sorted(name for name in original if name.startswith("data/bridge/gems-geodawn-numerical-features.tif.part-"))
        if len(parts) != 5:
            raise ValueError("Expected exactly five original feature-stack parts")
        partial = training.with_suffix(".partial.tif")
        with partial.open("wb") as output:
            for i, name in enumerate(parts):
                cached = ROOT / f".cache/restore/part-{i}"
                restore_blob(ORIGINAL_REPO, original[name], cached)
                with cached.open("rb") as handle:
                    shutil.copyfileobj(handle, output)
                cached.unlink()
        if checksum(partial) != expected:
            partial.unlink()
            raise ValueError("Reassembled feature-stack SHA-256 mismatch")
        partial.replace(training)
    receipt["files"].append({"path": "data/training_features.tif", "sha256": expected, "repo": ORIGINAL_REPO, "ref": ORIGINAL_REF, "source": "five ordered bridge parts"})
    (ROOT / "evidence/data-restoration.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("Restored pinned mirrored inputs; organizer authentication remains unverified")


if __name__ == "__main__":
    main()
