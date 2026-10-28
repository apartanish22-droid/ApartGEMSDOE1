#!/usr/bin/env python3
"""Autonomously restore the peer-repository corpus used by the uniqueness gate.

Only public GitHub repositories listed in the committed audit evidence are fetched.
Clones are shallow and blob-filtered; checked-out GeoTIFFs are still available to
``audit_focus_sites_and_registry.py``.  The destination defaults to /tmp because
this corpus is reproducible cache material and must not enter Git.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEST = Path("/tmp/research")

SPECIAL_OWNERS = {
    "ApartGEMSDOE2": ("apartanish22-droid", "ApartGEMSDOE2"),
    "ApartGEMSDOE3": ("apartanish22-droid", "ApartGEMSDOE3"),
    "GEMSDOESASS1": ("sassnarep3-star", "GEMSDOESASS1"),
    "GEMSDOESASS3": ("sassnarep3-star", "GEMSDOESASS3"),
    "GEMSDOEkarage1": ("karagemop466-tech", "GEMSDOEkarage1"),
    "KANLERGEMSDOE2": ("kanlerxz87-cyber", "KANLERGEMSDOE2"),
    "KANLERGEMSDOE3": ("kanlerxz87-cyber", "KANLERGEMSDOE3"),
    "WBGGEMSDOE3": ("wingbangboozle1-lang", "WBGGEMSDOE3"),
    "gems-prize-reference-solution": ("drivendataorg", "gems-prize-reference-solution"),
}


def _registry_names() -> list[str]:
    evidence = json.loads((ROOT / "evidence/focus_sites_forensic_audit.json").read_text())
    names = list(evidence["fleet_registry_summary"]["repos_scanned"])
    # Historical v1 is reconstructed from the immutable archived deliverable.
    # The registry intentionally reproduces the exact pre-H-APART-2 comparison
    # inventory recorded in the committed audit evidence.
    names = [name for name in names if name != "ApartGEMSDOE1_v1_historical"]
    return sorted(names)


def _remote_for(name: str) -> tuple[str, str]:
    if name in SPECIAL_OWNERS:
        return SPECIAL_OWNERS[name]
    return "buffedlizard55-lab", name


def _is_checkout(path: Path) -> bool:
    return path.is_dir() and (path / ".git").is_dir()


def _clone_one(dest: Path, name: str) -> dict:
    path = dest / name
    if _is_checkout(path):
        return {"name": name, "status": "cached", "path": str(path)}
    if path.exists():
        shutil.rmtree(path)
    owner, repo = _remote_for(name)
    proc = subprocess.run(
        [
            "gh", "repo", "clone", f"{owner}/{repo}", str(path), "--",
            "--depth", "1", "--filter=blob:none", "--quiet",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=600,
        check=False,
    )
    if proc.returncode != 0:
        shutil.rmtree(path, ignore_errors=True)
        return {
            "name": name,
            "status": "failed",
            "remote": f"https://github.com/{owner}/{repo}",
            "error": proc.stderr.strip()[-500:],
        }
    return {
        "name": name,
        "status": "cloned",
        "remote": f"https://github.com/{owner}/{repo}",
        "path": str(path),
    }


def _restore_historical_v1(dest: Path) -> dict:
    target = dest / "ApartGEMSDOE1_v1_historical" / "docs" / "downloads"
    target.mkdir(parents=True, exist_ok=True)
    source_dir = ROOT / "docs/downloads/archive"
    copied = []
    for source in source_dir.glob("apartgems1-udth-*.tif"):
        shutil.copy2(source, target / source.name)
        copied.append(source.name)
    if not copied:
        raise FileNotFoundError("Archived H-APART-1 GeoTIFF is missing from docs/downloads/archive")
    return {"name": "ApartGEMSDOE1_v1_historical", "status": "restored_from_committed_archive", "files": copied}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--list", action="store_true", help="Print the deterministic repository plan without cloning")
    args = parser.parse_args()

    names = _registry_names()
    plan = [{"local_name": name, "github": "/".join(_remote_for(name))} for name in names]
    if args.list:
        print(json.dumps(plan, indent=2))
        return 0

    args.dest.mkdir(parents=True, exist_ok=True)
    # Remove a stale directory produced by an earlier development-only inventory;
    # audit_focus_sites_and_registry scans every directory under the destination.
    shutil.rmtree(args.dest / "ApartGEMSDOE1_v2_current", ignore_errors=True)
    results = [_restore_historical_v1(args.dest)]
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(_clone_one, args.dest, name): name for name in names}
        for future in as_completed(futures):
            rec = future.result()
            results.append(rec)
            print(f"[{rec['status']}] {rec['name']}", flush=True)

    failed = [r for r in results if r["status"] == "failed"]
    receipt = {
        "destination": str(args.dest),
        "repositories_requested": len(names),
        "historical_archives_restored": 1,
        "failed": failed,
        "results": sorted(results, key=lambda r: r["name"]),
    }
    receipt_path = args.dest / "fetch_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"Receipt: {receipt_path}")
    if failed:
        print(json.dumps(failed, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
