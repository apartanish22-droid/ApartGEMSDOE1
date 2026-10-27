#!/usr/bin/env python3
"""Prepare restored data using the unmodified, pinned GEMSDOE32 shared script.

This is data preparation only. It creates neither a feature stack nor a model,
experiment, candidate TIFF or slot approval. Source files are extracted from a
hash-pinned archive into the ignored cache, not copied into this repository.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems_audit.rasters import aligned, sha256_file, template_info, verify_file  # noqa: E402

SHARED_COMMIT = "73485f27cf230af770167397c2b72cb9ce3b3f25"
ARCHIVE_SHA256 = "c3c72cd5d9be1aea6d449ea95df6c3137b27b03c94cbfc740934b9c6cfd5002d"
ARCHIVE_URL = f"https://codeload.github.com/buffedlizard55-lab/GEMSDOE32/tar.gz/{SHARED_COMMIT}"
NEEDED = {"scripts/prepare_data.py", "src/gems32/__init__.py", "src/gems32/paths.py"}


def download_archive(path: Path) -> None:
    if path.is_file() and sha256_file(path) == ARCHIVE_SHA256:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".template-", suffix=".partial", dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as out, urllib.request.urlopen(ARCHIVE_URL, timeout=120) as source:
            while chunk := source.read(1024 * 1024):
                out.write(chunk)
        if sha256_file(tmp) != ARCHIVE_SHA256:
            raise ValueError("Shared template archive hash mismatch")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def extract_needed(archive: Path, target: Path) -> None:
    if sha256_file(archive) != ARCHIVE_SHA256:
        raise ValueError("Shared template archive hash mismatch")
    found = set()
    with tarfile.open(archive, "r:gz") as tf:
        for member in tf:
            parts = member.name.split("/", 1)
            if len(parts) != 2 or parts[1] not in NEEDED:
                continue
            if parts[1] in found or not member.isfile():
                raise ValueError("Duplicate or unsafe shared-template member")
            f = tf.extractfile(member)
            if f is None:
                raise ValueError("Unreadable shared-template member")
            destination = target / parts[1]
            if not destination.resolve().is_relative_to(target.resolve()):
                raise ValueError("Shared-template destination escapes cache")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(f.read())
            found.add(parts[1])
    if found != NEEDED:
        raise ValueError(f"Shared-template archive missing {sorted(NEEDED - found)}")


def check_inputs(data: Path) -> None:
    entries = {e["id"]: e for e in json.loads((ROOT / "config/inputs.json").read_text())["files"]}
    for item in ("training_features", "labels", "sample"):
        e = entries[item]
        verify_file(data / e["dest"], e)
    grid = template_info(data / entries["sample"]["dest"])
    aligned(data / entries["labels"]["dest"], grid)
    with rasterio.open(data / entries["training_features"]["dest"]) as src:
        if (src.driver != "GTiff" or src.count != 19 or any(t != "float32" for t in src.dtypes) or src.shape != grid["shape"]
                or src.crs != grid["crs"] or src.transform != grid["transform"]):
            raise ValueError("Features do not match the template grid and 19-band contract")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=ROOT / ".cache/inputs")
    ap.add_argument("--work-dir", type=Path, default=ROOT / ".cache/prepared")
    ap.add_argument("--template-dir", type=Path, default=ROOT / ".cache/template32")
    ap.add_argument("--archive", type=Path, default=ROOT / ".cache/template32.tar.gz")
    args = ap.parse_args()
    try:
        check_inputs(args.data_dir)
        download_archive(args.archive)
        extract_needed(args.archive, args.template_dir)
        env = dict(os.environ, GEMS_DATA_DIR=str(args.data_dir.resolve()), GEMS_WORK_DIR=str(args.work_dir.resolve()))
        subprocess.run([sys.executable, str(args.template_dir / "scripts/prepare_data.py")], env=env, check=True)
    except (OSError, ValueError, tarfile.TarError, subprocess.SubprocessError) as exc:
        print(f"Preparation failed closed: {exc}", file=sys.stderr)
        return 1
    print("Prepared mirrored inputs with the shared script; no new experiment or TIFF was authorized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
