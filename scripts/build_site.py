#!/usr/bin/env python3
"""Sanity-check static evidence pages without regenerating or altering them."""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DownloadLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "a":
            values = dict(attrs)
            if values.get("href", "").lower().endswith((".tif", ".tiff", ".zip")):
                self.hrefs.append(values["href"])


def main() -> int:
    problems: list[str] = []
    index = ROOT / "index.html"
    if not index.is_file():
        problems.append("root index.html is missing")
    else:
        text = index.read_text(encoding="utf-8").lower()
        if "do not submit any tif" not in text:
            problems.append("landing page must prominently mark every repository TIF DO NOT SUBMIT")
        if "research-demo" not in text and "research demo" not in text:
            problems.append("landing page must label the downloadable demo as research-only")
        parser = DownloadLinks()
        parser.feed(index.read_text(encoding="utf-8"))
        for href in parser.hrefs:
            if href.startswith(("http://", "https://")):
                continue
            if not (index.parent / href).is_file():
                problems.append(f"local artifact link is missing: {href}")

    for required in (ROOT / "docs" / "EXECUTIVE_SUMMARY.md", ROOT / "docs" / "SUBMISSION.md", ROOT / "run_card.json"):
        if not required.is_file():
            problems.append(f"required evidence page is missing: {required.relative_to(ROOT)}")

    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    print("PASS: static site labels research artifact DO NOT SUBMIT; no pages regenerated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
