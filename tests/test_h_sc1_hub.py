"""H-SC1 lane guards: no candidate may be cleared or published while its evidence says otherwise."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / 'evidence'
DOCS = ROOT / 'docs'


def test_candidate_not_cleared_and_run_card_negative():
    sel = json.loads((EV / 'candidate_selection.json').read_text(encoding='utf-8'))
    card = json.loads((EV / 'run_card_h-sc1-hsc1_q090.json').read_text(encoding='utf-8'))
    assert sel['cleared'] is False
    assert card['verdict'] == 'negative'


def test_candidate_not_in_downloads():
    sel = json.loads((EV / 'candidate_selection.json').read_text(encoding='utf-8'))
    stem = Path(sel['name']).name
    hits = [p.name for p in (DOCS / 'downloads').glob('*') if stem in p.name or 'hsc1' in p.name]
    assert hits == [], hits


def test_h_sc1_summary_states_blocked_and_links_resolve():
    text = (DOCS / 'h-sc1-summary.html').read_text(encoding='utf-8')
    assert 'NOT CLEARED' in text or 'BLOCKED' in text
    assert 'ready to submit' not in text.lower()
    for href in re.findall(r'href="([^"#]+)"', text):
        if href.startswith(('http://', 'https://', 'mailto:')):
            continue
        assert (DOCS / href).resolve().exists() or (ROOT / href).resolve().exists(), href


def test_h_sc1_banner_on_readme_and_dashboard():
    assert 'H-SC1 lane' in (ROOT / 'README.md').read_text(encoding='utf-8')
    assert 'id="h-sc1"' in (DOCS / 'index.html').read_text(encoding='utf-8')
