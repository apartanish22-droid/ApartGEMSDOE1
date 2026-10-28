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


def test_html_pages_local_links_status_banner_and_no_localhost():
    docs = ROOT / "docs"
    rc = json.loads((ROOT / "evidence/run_card.json").read_text())

    for page_name in ("index.html", "executive-summary.html"):
        p = docs / page_name
        assert p.exists(), f"Missing {page_name}"
        txt = p.read_text(encoding="utf-8")
        assert "127.0.0.1" not in txt and "localhost" not in txt
        assert rc["raster_sha256"] in txt
        assert html.escape(rc["submission_note"]) in txt
        assert "PASS" in txt
        assert "https://www.drivendata.org/competitions/306/competition-doe-gems/" in txt or page_name == "index.html"

        parser = _AttrCollector()
        parser.feed(txt)
        assert parser.refs, f"No links found in {page_name}"
        for ref in parser.refs:
            if ref.startswith(("http://", "https://", "#", "mailto:", "javascript:")):
                continue
            clean = ref.split("#", 1)[0].split("?", 1)[0]
            target = (docs / clean).resolve()
            assert target.exists() and target.stat().st_size > 0, f"Broken local ref {ref} in {page_name} -> {target}"

    idx_txt = (docs / "index.html").read_text(encoding="utf-8")
    for s in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        assert s in idx_txt
    assert "HOLDOUT-DTI" in idx_txt and "ORGANIZER-CONFIRMED" in idx_txt

    exec_txt = (docs / "executive-summary.html").read_text(encoding="utf-8")
    for official_url in (
        "https://www.drivendata.org/competitions/306/competition-doe-gems/",
        "https://docs.nlr.gov/docs/fy26osti/96647.pdf",
        "https://github.com/drivendataorg/gems-prize-reference-solution",
        "https://gbcge.org/current-projects/ingenious/",
        "https://gdr.openei.org/submissions/1391",
    ):
        assert official_url in exec_txt


def test_readme_standing_prompt_focus9_and_local_links():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    rc = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert rc["raster_sha256"] in readme
    assert rc["submission_note"] in readme
    assert "Standing Reference: Original Competition Task & Protocol Specification" in readme
    for s in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        assert s in readme
    assert "HOLDOUT-DTI" in readme and "ORGANIZER-CONFIRMED" in readme
    for hid in ("H-APART-5", "H-APART-6", "H-APART-7", "H-APART-8", "H-APART-9"):
        assert hid in readme

    for m in re.finditer(r"\]\(([^)]+)\)", readme):
        ref = m.group(1).strip()
        if ref.startswith(("http://", "https://", "#")):
            continue
        target = (ROOT / ref).resolve()
        assert target.exists(), f"Broken README link: {ref}"


def test_cli_scripts_exist_and_compile():
    for rel in (
        "scripts/download_competition_data.sh",
        "scripts/prepare_data.py",
        "scripts/audit_focus_sites_and_registry.py",
        "scripts/run_apartgems_pipeline.py",
        "scripts/evaluate_holdout.py",
        "scripts/submission_writer.py",
        "scripts/validate_submission.py",
        "scripts/generate_figures.py",
        "scripts/build_pages_and_readme.py",
    ):
        assert (ROOT / rel).exists(), f"Missing {rel}"
