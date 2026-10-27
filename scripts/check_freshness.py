#!/usr/bin/env python3
"""Check public GitHub source heads, not DrivenData pages or private scores.

A moved source is marked changed, never treated as freshly audited. A failed
lookup writes an explicit unknown state instead of preserving an old success.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def query(entry: dict) -> dict:
    try:
        data = subprocess.run(["gh", "api", f"repos/{entry['repo']}/commits/main", "--jq", ".sha"],
                              check=True, capture_output=True, text=True, timeout=30)
        head = data.stdout.strip()
        if len(head) != 40 or any(ch not in "0123456789abcdef" for ch in head):
            raise ValueError("invalid commit SHA from GitHub")
        return {"site": entry["id"], "audited_commit": entry["ref"], "current_commit": head,
                "state": "unchanged" if head == entry["ref"] else "changed; not re-audited"}
    except (subprocess.SubprocessError, ValueError, OSError):
        return {"site": entry["id"], "audited_commit": entry["ref"], "current_commit": None,
                "state": "unknown; lookup failed"}


def write_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".freshness-", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, indent=2, allow_nan=False)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "docs/data/freshness.json")
    ap.add_argument("--allow-unknown", action="store_true", help="Publish explicit unknown states; errors writing the report still fail")
    args = ap.parse_args()
    entries = [e for e in json.loads((ROOT / "config/inputs.json").read_text())["files"] if e["group"] == "history"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(query, entries))
    report = {"checked_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "scope": "GitHub source heads only; not a DrivenData leaderboard or submission feed.",
              "sources": results,
              "changed_count": sum(r["state"].startswith("changed") for r in results),
              "unknown_count": sum(r["current_commit"] is None for r in results)}
    write_atomic(args.out, report)
    print(json.dumps({k: report[k] for k in ("checked_utc", "changed_count", "unknown_count")}))
    return 0 if report["unknown_count"] == 0 or args.allow_unknown else 1


if __name__ == "__main__":
    raise SystemExit(main())
