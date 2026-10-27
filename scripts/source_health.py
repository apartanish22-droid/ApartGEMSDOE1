#!/usr/bin/env python3
"""Check source reachability/snapshot drift without rewriting scientific evidence.

Default is recorded-only (no network). --github-only probes only GitHub, for
restricted environments. --online also checks official URLs. HTTP reachability
is NOT verification of a scientific claim or organizer receipt. Reports never
promote files, refresh the frozen registry, or run an experiment.
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests

ROOT = Path(__file__).resolve().parents[1]


def check_url(url: str, timeout: float = 15) -> dict:
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        return {"url": url, "status": "invalid_source_url", "reachable": False}
    try:
        # Use the system trust store (including a managed sandbox CA) rather than
        # disabling TLS verification or assuming certifi knows the environment.
        ca_bundle = os.environ.get("REQUESTS_CA_BUNDLE") or ssl.get_default_verify_paths().cafile or True
        with requests.get(url, timeout=timeout, allow_redirects=True, stream=True, verify=ca_bundle,
                          headers={"User-Agent": "ApartGEMS-source-health/1.0 (research provenance check)"}) as response:
            # Do not pull large PDF/data bodies just to test their availability.
            login = any(word in urlsplit(response.url).path.lower() for word in ("/login", "/accounts/", "/signin"))
            ok = 200 <= response.status_code < 300 and not login
            return {"url": url, "resolved_url": response.url, "http_status": response.status_code,
                    "reachable": ok, "status": "authentication_required" if login else ("reachable" if ok else "http_error"),
                    "scientific_claims_reverified": False}
    except (requests.RequestException, OSError) as exc:
        return {"url": url, "reachable": None, "status": "unreachable_from_checker",
                "error": str(exc)[:350], "scientific_claims_reverified": False}


def check_snapshot(pin: dict) -> dict:
    repo = pin["repo"]
    pinned = pin.get("snapshot_commit") or pin.get("ref")
    result = {"repo": repo, "pinned_commit": pinned}
    try:
        latest = subprocess.check_output(["gh", "api", f"repos/{repo}/commits/HEAD", "--jq", ".sha"],
                                         text=True, stderr=subprocess.PIPE, timeout=45).strip()
        if len(latest) != 40 or any(c not in "0123456789abcdef" for c in latest):
            raise ValueError("GitHub returned an invalid commit ID")
        result.update(latest_commit=latest, snapshot_matches_head=latest == pinned,
                      status="unchanged" if latest == pinned else "snapshot_drift")
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        result.update(status="unreachable_from_checker", snapshot_matches_head=None, error=str(exc)[:350])
    return result


def build_report(*, online: bool = False, github_only: bool = False) -> dict:
    ledger = json.loads((ROOT / "research/sources.json").read_text())
    pins = json.loads((ROOT / "evidence/source-pins.json").read_text())
    # The ledger contains the original observed source status; never relabel it
    # as a new live verification when this sandbox cannot reach that host.
    results = []
    for source in ledger["sources"]:
        host = urlsplit(source["url"]).hostname
        if host in {"www.drivendata.org", "drivendata.org", "community.drivendata.org"}:
            # Never turn this diagnostic into automated leaderboard monitoring.
            # Preserve dated evidence; no score scraping or account access.
            item = {"url": source["url"], "status": "not_automatically_probed_source_policy", "reachable": None,
                    "scientific_claims_reverified": False, "reason": "No automated DrivenData monitoring; dated source observations only."}
        elif online or (github_only and host in {"github.com", "api.github.com"}):
            item = check_url(source["url"])
        else:
            item = {"url": source["url"], "status": "recorded_only_not_live_probed", "reachable": None,
                    "scientific_claims_reverified": False}
        item.update(id=source["id"], recorded_status=source["status"])
        results.append(item)
    # source-pins.json is a list in this release; tolerate an explicit wrapper
    # for a future schema, without confusing registry inventory rows with pins.
    if isinstance(pins, dict):
        pins = pins.get("sources", pins.get("source_pins", []))
    snapshots = [check_snapshot(pin) for pin in pins] if online or github_only else [
        {"repo": pin["repo"], "pinned_commit": pin.get("snapshot_commit") or pin.get("ref"),
         "status": "recorded_only_not_live_probed", "snapshot_matches_head": None} for pin in pins]
    issues = [item for item in results if item["status"] not in {"reachable", "recorded_only_not_live_probed", "not_automatically_probed_source_policy"}]
    drift = [item for item in snapshots if item["status"] not in {"unchanged", "recorded_only_not_live_probed"}]
    return {"schema": "apartgems-source-health-v1", "checked_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "online" if online else ("github_only" if github_only else "recorded_only"),
            "scope": "Reachability and source-HEAD drift only. Does not authenticate organizer data, validate scientific claims or extend registry coverage.",
            "submission_authorized": False, "scientific_records_modified": False,
            "sources": results, "snapshots": snapshots, "issues_count": len(issues) + len(drift),
            "status": "attention_needed" if issues or drift else "recorded_only" if not online and not github_only else "probe_complete"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--online", action="store_true")
    mode.add_argument("--github-only", action="store_true")
    parser.add_argument("--report", type=Path, default=ROOT / "evidence/source-health.json")
    parser.add_argument("--strict", action="store_true", help="Nonzero exit if any probed source is unavailable or has snapshot drift")
    args = parser.parse_args()
    report = build_report(online=args.online, github_only=args.github_only)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Source health: {report['mode']}; {len(report['sources'])} source rows; {len(report['snapshots'])} pinned repos; {report['issues_count']} issues. No scientific record changed.")
    return 1 if args.strict and report["issues_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
