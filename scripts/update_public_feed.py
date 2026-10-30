#!/usr/bin/env python3
"""Refresh a small public leaderboard snapshot for the static GitHub Pages site.

This reads the *public leaderboard*, not a submission-page receipt, and never
submits, logs in, or estimates a future score. On failure the output is marked
unavailable rather than retaining a stale value as if it were current.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
# The public leaderboard page loads its table from this public HTML fragment;
# requesting the page shell alone does not include the leaderboard rows.
PARTIAL_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard_partial/"


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.table = []
        elif self.depth == 1 and tag == "tr":
            self.row = []
        elif self.depth == 1 and self.row is not None and tag in ("td", "th"):
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if self.depth == 1 and tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        elif self.depth == 1 and tag == "tr" and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.depth:
            if self.depth == 1 and self.table is not None:
                self.tables.append(self.table)
                self.table = None
            self.depth -= 1


def parse_public_leaderboard(html: str) -> float:
    """Extract only an unambiguous rank-one score from a labeled Tversky table."""
    parser = TableParser()
    parser.feed(html)
    found = []
    for table in parser.tables:
        if not table:
            continue
        header = " ".join(table[0]).casefold()
        if "rank" not in header or "tversky" not in header:
            continue
        for cells in table[1:]:
            if not cells or not re.fullmatch(r"#?\s*1", cells[0].strip()):
                continue
            values = [float(cell.strip()) for cell in cells[1:]
                      if re.fullmatch(r"(?:0\.\d+|1\.0+)", cell.strip())]
            if len(values) != 1:
                raise ValueError("rank-one score is ambiguous")
            found.extend(values)
    if len(found) != 1:
        raise ValueError("no unique rank-one Tversky score in a labeled leaderboard table")
    return found[0]


def table_diagnostics(html: str) -> dict:
    """Record only public table structure, never participant names or page HTML."""
    parser = TableParser()
    parser.feed(html)
    tables = []
    for table in parser.tables[:5]:
        # First-row categories and rank-shaped cells only: no participant names.
        rank_cells = [row[0] for row in table[1:4] if row and re.fullmatch(r'[#\s0-9]+', row[0])]
        categories = []
        for cell in (table[0] if table else []):
            lower = cell.casefold()
            categories.append([word for word in ('rank', 'tversky', 'participant', 'team') if word in lower])
        tables.append({'header_categories': categories, 'first_rank_cells': rank_cells})
    return {'response_bytes': len(html.encode('utf-8')),
            'response_sha256': hashlib.sha256(html.encode('utf-8')).hexdigest(),
            'table_count': len(parser.tables), 'tables': tables}


def make_snapshot(html: str, *, now: datetime | None = None) -> dict:
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    try:
        return {
            "status": "ok",
            "checked_utc": stamp,
            "observed_utc": stamp,
            "source": URL,
            "data_endpoint": PARTIAL_URL,
            "evidence_class": "OFFICIAL PUBLIC LEADERBOARD OBSERVATION; NOT A SUBMISSION RECEIPT",
            "top_public_dti": parse_public_leaderboard(html),
            "caveat": "Public leaderboard only; not a forecast, private score, or a score for a file in this repository.",
        }
    except ValueError as exc:
        result = unavailable(str(exc), checked_utc=stamp)
        result['parse_diagnostics'] = table_diagnostics(html)
        return result


def unavailable(reason: str, *, checked_utc: str | None = None) -> dict:
    """Represent a failed refresh without falsely dating it as an observation."""
    return {
        "status": "unavailable",
        "checked_utc": checked_utc or datetime.now(timezone.utc).isoformat(),
        "observed_utc": None,
        "source": URL,
        "data_endpoint": PARTIAL_URL,
        "evidence_class": "OFFICIAL PUBLIC LEADERBOARD OBSERVATION; NOT A SUBMISSION RECEIPT",
        "top_public_dti": None,
        "reason": reason,
        "caveat": "Refresh failed. Do not treat an earlier number as current; use the linked official leaderboard.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--html", type=Path, help="Parse a local HTML fixture instead of making a request")
    ap.add_argument("--out", type=Path, default=ROOT / "docs/data/public_feed.json")
    args = ap.parse_args()
    try:
        if args.html:
            html = args.html.read_text(encoding="utf-8")
        else:
            request = urllib.request.Request(PARTIAL_URL, headers={"User-Agent": "ApartGEMSDOE1-public-feed/1.0"})
            with urllib.request.urlopen(request, timeout=25) as response:
                html = response.read(5_000_001).decode("utf-8", errors="replace")
            if len(html) > 5_000_000:
                raise ValueError("leaderboard response exceeds size limit")
        snapshot = make_snapshot(html)
    except (OSError, ValueError) as exc:
        snapshot = unavailable(f"{type(exc).__name__}: {exc}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    temporary.write_text(json.dumps(snapshot, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(args.out)
    print(json.dumps(snapshot, indent=2, allow_nan=False))
    if snapshot["status"] != "ok" and os.environ.get("GITHUB_ACTIONS") == "true":
        # Expose only the non-sensitive failure reason in the workflow's
        # annotation, so a blocked refresh is diagnosable without raw logs.
        reason = str(snapshot.get("reason", "unknown")).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::warning title=Public leaderboard refresh failed::{reason}")
    return 0 if snapshot["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
