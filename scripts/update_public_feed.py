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
# The public leaderboard page loads its rows from this public fragment; the
# response has appeared as either an HTML table or a rendered pipe table.
PARTIAL_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard_partial/"
MAX_AGE_SECONDS = 24 * 60 * 60
FUTURE_CLOCK_TOLERANCE_SECONDS = 300


def is_fresh_observation(snapshot: dict, *, now: datetime | None = None) -> bool:
    """Return whether a stored public observation is recent enough to present as current.

    Date-only timestamps are interpreted as UTC midnight, conservatively. Invalid,
    future-dated, unavailable, or older-than-one-day records fail closed.
    """
    if not isinstance(snapshot, dict) or snapshot.get('status') != 'ok':
        return False
    score = snapshot.get('top_public_dti')
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
        return False
    try:
        value = str(snapshot['observed_utc'])
        observed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        age = (current.astimezone(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds()
        configured_age = snapshot.get('max_age_seconds', MAX_AGE_SECONDS)
        if isinstance(configured_age, bool) or not isinstance(configured_age, (int, float)):
            return False
        max_age = min(float(configured_age), float(MAX_AGE_SECONDS))
        return -FUTURE_CLOCK_TOLERANCE_SECONDS <= age <= max_age
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


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


def _rank_one_score(rows: list[list[str]]) -> list[float]:
    """Extract rank-one Tversky values from normalized table rows."""
    if not rows:
        return []
    header = " ".join(rows[0]).casefold()
    if "rank" not in header or "tversky" not in header:
        return []
    found = []
    for cells in rows[1:]:
        if not cells or not re.fullmatch(r"#?\s*1", cells[0].strip()):
            continue
        values = [float(cell.strip()) for cell in cells[1:]
                  if re.fullmatch(r"(?:0\.\d+|1\.0+)", cell.strip())]
        if len(values) != 1:
            raise ValueError("rank-one score is ambiguous")
        found.extend(values)
    return found


def _markdown_tables(content: str) -> list[list[list[str]]]:
    """Parse simple pipe-delimited tables for rendered leaderboard fragments."""
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in content.splitlines():
        line = line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            if current:
                tables.append(current)
                current = []
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        current.append(cells)
    if current:
        tables.append(current)
    return tables


def parse_public_leaderboard(content: str) -> float:
    """Extract only an unambiguous rank-one score from a labeled Tversky table.

    DrivenData has served both HTML table fragments and rendered pipe-table
    fragments. Accept either representation, but require an explicit rank and
    Tversky header and exactly one rank-one score.
    """
    parser = TableParser()
    parser.feed(content)
    found = []
    for table in parser.tables:
        found.extend(_rank_one_score(table))
    if not parser.tables:
        for table in _markdown_tables(content):
            found.extend(_rank_one_score(table))
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
            "max_age_seconds": MAX_AGE_SECONDS,
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
    """Record a failed refresh without inventing a leaderboard observation time."""
    return {
        "status": "unavailable",
        "checked_utc": checked_utc or datetime.now(timezone.utc).isoformat(),
        "observed_utc": None,
        "max_age_seconds": MAX_AGE_SECONDS,
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
