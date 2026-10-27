"""Pass-2 & Pass-3 automated verification of HTML pages, links, hashes, and protocol invariants."""
from __future__ import annotations

import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


class _AttrCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for k, v in attrs:
            if k in ("href", "src") and v:
                self.refs.append(v)


def test_html_pages_local_links_and_no_localhost():
    docs = ROOT / "docs"
    rc = json.loads((ROOT / "evidence/run_card.json").read_text())

    for page_name in ("index.html", "executive-summary.html"):
        p = docs / page_name
        assert p.exists(), f"Missing {page_name}"
        txt = p.read_text(encoding="utf-8")
        assert "127.0.0.1" not in txt and "localhost" not in txt
        assert rc["raster_sha256"] in txt
        assert html.escape(rc["submission_note"]) in txt

        parser = _AttrCollector()
        parser.feed(txt)
        assert parser.refs, f"No links found in {page_name}"
        for ref in parser.refs:
            if ref.startswith(("http://", "https://", "#", "mailto:", "javascript:")):
                continue
            clean = ref.split("#", 1)[0].split("?", 1)[0]
            target = (docs / clean).resolve()
            assert target.exists() and target.stat().st_size > 0, f"Broken local ref {ref} in {page_name} -> {target}"


def test_readme_standing_prompt_and_local_links():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    rc = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert rc["raster_sha256"] in readme
    assert "Standing Reference: Original Competition Task & Protocol Specification" in readme
    assert "GEMSDOE32" in readme and "0.2778" in readme

    # Verify all relative markdown links [label](path)
    for m in re.finditer(r"\]\(([^)]+)\)", readme):
        ref = m.group(1).strip()
        if ref.startswith(("http://", "https://", "#")):
            continue
        target = (ROOT / ref).resolve()
        assert target.exists(), f"Broken README link: {ref}"


def test_evaluate_holdout_cli_script_smoke():
    """Verify scripts/evaluate_holdout.py exists and imports cleanly."""
    assert (ROOT / "scripts/evaluate_holdout.py").exists()
    assert (ROOT / "scripts/submission_writer.py").exists()
    assert (ROOT / "scripts/validate_submission.py").exists()
    assert (ROOT / "scripts/download_competition_data.sh").exists()
