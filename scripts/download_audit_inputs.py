#!/usr/bin/env python3
"""Fetch pinned, research-only reference rasters via GitHub's API.

The manifest pins both commit and SHA-256. A hash match verifies bytes, not
organizer provenance, data licensing, prediction quality, or slot permission.
Existing environment authentication is used only for GitHub requests and is never persisted.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "catalog/reference_sources.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_entry(entry: dict) -> None:
    for key in ("owner", "repo"):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", entry[key]):
            raise ValueError(f"Invalid {key}")
    if not re.fullmatch(r"[0-9a-f]{40}", entry["ref"]):
        raise ValueError("Source ref must be an immutable 40-character commit")
    if not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
        raise ValueError("Source SHA-256 must be a 64-character lowercase digest")
    if (not re.fullmatch(r"[A-Za-z0-9_./-]+", entry["path"])
            or Path(entry["path"]).is_absolute()
            or any(x in {".", "..", ""} for x in entry["path"].split("/"))):
        raise ValueError("Unsafe source path")
    ident = entry.get("id", entry.get("site"))
    if not isinstance(ident, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", ident):
        raise ValueError("Unsafe local identifier")
    if not isinstance(entry["bytes"], int) or entry["bytes"] <= 0:
        raise ValueError("Invalid expected file size")


def fetch_entry(entry: dict, destination: Path, timeout: int = 180) -> Path:
    """Use the byte-preserving pinned downloader for the fleet manifest too."""
    from restore_inputs import restore
    check_entry(entry)
    ident = entry.get("id", entry.get("site"))
    item = {"id": ident, "repo": f"{entry['owner']}/{entry['repo']}",
            "ref": entry["ref"], "path": entry["path"], "dest": f"{ident}.tif",
            "sha256": entry["sha256"], "bytes": entry["bytes"]}
    restore(item, destination, timeout=timeout)
    return destination / item["dest"]


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported manifest schema")
    entries = manifest["support"] + manifest["reference_sites"]
    ids = []
    for entry in entries:
        check_entry(entry)
        ids.append(entry.get("id", entry.get("site")))
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate source identifier")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--directory", type=Path, default=ROOT / ".cache/audit-inputs")
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        entries = manifest["support"] + manifest["reference_sites"]
        errors = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(fetch_entry, e, args.directory): e for e in entries}
            for future in as_completed(futures):
                entry = futures[future]
                ident = entry.get("id", entry.get("site"))
                try:
                    print(f"VERIFIED {ident}: {future.result()}")
                except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
                    errors.append(f"{ident}: {exc}")
        if errors:
            for error in errors:
                print(f"ERROR {error}", file=sys.stderr)
            return 1
        return 0
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
