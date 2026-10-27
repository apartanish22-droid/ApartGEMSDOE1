#!/usr/bin/env python3
"""Restore immutable, hash-pinned owner mirrors for audit or model research.

No platform login or scraping is performed. Historical rasters are for learning
and duplicate checks only. A mirror hash proves integrity, not official origin.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems_audit.rasters import sha256_file, verify_file  # noqa: E402


def safe_dest(root: Path, dest: str) -> Path:
    p = PurePosixPath(dest)
    if p.is_absolute() or not p.parts or any(part in (".", "..") for part in p.parts):
        raise ValueError("Unsafe destination path in manifest")
    target = root.joinpath(*p.parts)
    # Do not follow an existing symlink outside the selected root.
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Destination escapes input root")
    return target


def validate_source(entry: dict) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", entry["repo"]):
        raise ValueError("Unsafe repository in manifest")
    if not re.fullmatch(r"[0-9a-f]{40}", entry["ref"]):
        raise ValueError("Source must be pinned to a full commit SHA")
    if not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
        raise ValueError("A full expected SHA-256 is required")
    if not isinstance(entry["bytes"], int) or entry["bytes"] <= 0:
        raise ValueError("Expected byte size must be positive")
    for item in entry.get("parts", [entry.get("path", "")]):
        p = PurePosixPath(item)
        if p.is_absolute() or not item or any(x in (".", "..") for x in p.parts) or "?" in item or "#" in item:
            raise ValueError("Unsafe source path")


def restore(entry: dict, root: Path) -> str:
    validate_source(entry)
    dest = safe_dest(root, entry["dest"])
    if dest.is_file():
        try:
            verify_file(dest, entry)
            return "present"
        except ValueError:
            # Keep the old file until the replacement has passed verification.
            pass
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".restore-", suffix=".partial", dir=dest.parent)
    tmp = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as out:
            for source_path in entry.get("parts", [entry.get("path")]):
                # GitHub CLI may transcode binary output in some runner locales.
                # Stream the public API response as bytes and authenticate only if
                # a caller already supplied an Actions token; never persist it.
                url = (f"https://api.github.com/repos/{entry['repo']}/contents/"
                       f"{quote(source_path, safe='/')}?ref={entry['ref']}")
                headers = {"Accept": "application/vnd.github.raw+json",
                           "User-Agent": "Apart-GEMS-Audit/1.0",
                           "X-GitHub-Api-Version": "2022-11-28"}
                token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                with urlopen(Request(url, headers=headers), timeout=120) as source:
                    while chunk := source.read(1024 * 1024):
                        if out.tell() + len(chunk) > entry["bytes"]:
                            raise ValueError(f"Downloaded size exceeds pin for {entry['id']}")
                        out.write(chunk)
        verify_file(tmp, entry)
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)
    return "restored"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / ".cache" / "inputs")
    parser.add_argument("--group", choices=("light", "model", "all"), default="light",
                        help="light: template, labels, lattice and historical artifacts; model: large feature mirror")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "config" / "inputs.json").read_text())
    groups = {"audit", "history"} if args.group == "light" else ({"model"} if args.group == "model" else {"audit", "history", "model"})
    try:
        for e in manifest["files"]:
            if e["group"] in groups:
                result = restore(e, args.data_dir)
                print(f"{result:8} {e['id']:20} {e['sha256'][:12]}", flush=True)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Restore stopped; no permission to submit was inferred: {exc}", file=sys.stderr)
        return 1
    print("Owner-mirror integrity verified; official provenance and upload authorization remain unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
