"""Current dashboard, links, and superseded receipts must agree on NO UPLOAD."""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                self.refs.append(value)


def test_pages_have_negative_status_and_working_local_links():
    docs = ROOT / 'docs'
    old_sha = json.loads((ROOT / 'evidence/review_20261028.json').read_text())['previous_apart_submission']['sha256']
    for page in ('index.html', 'executive-summary.html'):
        text = (docs / page).read_text(encoding='utf-8')
        assert 'DO NOT SUBMIT' in text and old_sha in text
        assert 'OWNER-REPORTED' in text and 'Unavailable' in text
        assert 'OK TO SUBMIT' not in text and '127.0.0.1' not in text and 'localhost' not in text
        parser = Collector()
        parser.feed(text)
        assert parser.refs
        for ref in parser.refs:
            if ref.startswith(('http://', 'https://', '#', 'mailto:')):
                continue
            target = docs / ref.split('#', 1)[0].split('?', 1)[0]
            assert target.is_file() and target.stat().st_size > 0, f'Broken {page}: {ref}'


def test_readme_has_standing_protocol_focus_table_and_valid_links():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert 'Standing Reference: Original Competition Task & Protocol Specification' in readme
    assert 'NOT READY TO SUBMIT' in readme and '0.2778' in readme
    assert 'not ORGANIZER-CONFIRMED' in readme
    for site in (24, 25, 27, 28, 30, 31, 32, 33, 36):
        assert f'GEMSDOE{site}' in readme
    for match in re.finditer(r'\]\(([^)]+)\)', readme):
        ref = match.group(1).strip()
        if ref.startswith(('http://', 'https://', '#')):
            continue
        assert (ROOT / ref).exists(), f'Broken README link: {ref}'


def test_new_json_is_consistent_and_historical_approval_is_withdrawn():
    assert json.loads((ROOT/'docs/data/current-run-card.json').read_text()) == json.loads((ROOT/'evidence/run_card_20261028.json').read_text())
    assert json.loads((ROOT/'docs/data/review_20261028.json').read_text()) == json.loads((ROOT/'evidence/review_20261028.json').read_text())
    old = json.loads((ROOT/'evidence/validation_receipt.json').read_text())
    assert not old['uniqueness_passed'] and old['ready_to_submit_verdict'] == 'DO_NOT_SUBMIT'
    assert 'docs/' in (ROOT/'index.html').read_text()


def test_pages_workflow_is_read_only_for_repository_content():
    text = (ROOT/'.github/workflows/pages.yml').read_text()
    assert 'contents: read' in text and 'actions/deploy-pages@' in text
    assert 'git push' not in text and 'workflow_dispatch' in text and 'schedule:' in text
