"""Dashboard, standing mission and fail-closed publication checks."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


class AttrCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                self.refs.append(value)


def test_submission_pages_state_the_current_decision():
    docs = ROOT / 'docs'
    dec = json.loads((ROOT / 'evidence/submission_decision_2026-10-31.json').read_text())
    assert dec['verdict']['ok_to_submit'] is False
    assert dec['uniqueness']['unique_vs_registry'] is False
    assert dec['uniqueness']['exact_copy_found'] is False
    assert dec['uniqueness']['spatial_duplicate_flags'] == 186
    sha = dec['candidate']['sha256']
    cand = ROOT / dec['candidate']['repo_path']
    assert cand.is_file() and cand.stat().st_size == dec['candidate']['bytes']
    import hashlib
    assert hashlib.sha256(cand.read_bytes()).hexdigest() == sha
    for name in ('index.html', 'download-and-submit.html'):
        text = (docs / name).read_text()
        assert 'localhost' not in text and '127.0.0.1' not in text
        assert 'No. Do not submit this file yet.' in text
        assert sha in text and 'NOT-CLEARED' in text
        assert 'research only' in text.lower()
        assert 'user-reported; unconfirmed' in text or 'unconfirmed' in text.lower()
        assert '0.2778' in text and '0.4544' in text
        parser = AttrCollector(); parser.feed(text)
        assert parser.refs
        for ref in parser.refs:
            if ref.startswith(('http://', 'https://', '#', 'mailto:')):
                continue
            clean = ref.split('#', 1)[0].split('?', 1)[0]
            target = (docs / clean).resolve()
            assert target.exists() and target.stat().st_size > 0, f'broken {ref} in {name}'
    text = (docs / 'download-and-submit.html').read_text()
    for site in (24, 25, 27, 28, 30, 31, 32, 33, 36):
        assert f'GEMSDOE{site}' in text
    assert (docs / 'index.html').read_text() == text
    assert 'download-and-submit.html#sites' in (docs / 'executive-summary.html').read_text()
    audit = json.loads((ROOT / 'evidence/focus9_reaudit.json').read_text())
    assert all(r['max_forward_overlap_3px_among_focus9'] > .70 for r in audit['sites'])
    assert all(r['closest_focus_site'] for r in audit['sites'])
    assert 'outside bounds' in text.lower() or 'null or nan' in text.lower()
    assert 'top_public_dti' in (docs / 'feed.js').read_text()


def test_research_pages_are_rendered_and_linked_without_score_projections():
    docs = ROOT / 'docs'
    sources = (docs / 'research-sources.html').read_text()
    hypotheses = (docs / 'next-hypotheses.html').read_text()
    assert '<table>' in sources and 'AG100' in sources and '100 m' in sources
    assert 'none validated here' in hypotheses.lower() and 'not viable for a holdout run' in hypotheses.lower()
    assert 'flight-line repeatability' in hypotheses.lower()
    for name, text in [('research-sources.html', sources), ('next-hypotheses.html', hypotheses)]:
        parser = AttrCollector(); parser.feed(text)
        for ref in parser.refs:
            if ref.startswith(('http://', 'https://', '#', 'mailto:')):
                continue
            assert (docs / ref.split('#')[0].split('?')[0]).resolve().exists(), f'broken {ref} in {name}'


def test_archived_h6_cannot_promote_after_literal_stop():
    guard = subprocess.run([sys.executable, '-S', str(ROOT / 'scripts/run_h6_otsp_experiments.py')],
                           cwd=ROOT, capture_output=True, text=True)
    assert guard.returncode == 2 and 'H-APART-6 is stopped' in guard.stderr
    assert 'no experiment was started' in guard.stderr or 'must not be promoted or rerun' in guard.stderr
    exp = json.loads((ROOT / 'evidence/experiments_h6_otsp.json').read_text())
    card = json.loads((ROOT / 'evidence/run_card_h6_otsp.json').read_text())
    assert exp['experiment_budget_used'] == exp['experiment_budget_cap'] == 3
    assert exp['leakage_canary']['all_passed'] is True
    assert exp['selector_verdict'] == 'negative_stop_archived_v2'
    assert exp['subsequent_registry_stop']['stop_required'] is True
    assert card['verdict'] == 'negative'
    assert card['raster_sha256'] is None and card['submission_name'] is None
    assert card['current_release_decision'] == 'NO FILE READY TO SUBMIT'
    assert 'ARCHIVED-NONCOMPARABLE' in card['evidence_status']


def test_readme_standing_protocol_and_links():
    text = (ROOT / 'README.md').read_text()
    dec = json.loads((ROOT / 'evidence/submission_decision_2026-10-31.json').read_text())
    assert dec['candidate']['sha256'] in text
    assert 'Future-session start-up: read before every run' in text
    assert 'Current lane status — stop' in text and 'Single method per lane' in text
    assert 'AUC >0.90 is leakage' in text and 'three experiments or two hours' in text
    assert 'Unique vs the other focus sites' in text
    assert 'GEMSDOE32' in text and '0.2778' in text and 'no linked organizer receipt' in text
    assert 'HOLDOUT-DTI' in text and '95% CI' in text
    assert 'docs/PROJECT_BRIEF.md' in text
    assert 'Not measured' in text or 'not measured' in text
    assert 'OK to submit?' in text and '**No**' in text
    assert (ROOT / 'docs/PROJECT_BRIEF.md').is_file()
    for m in re.finditer(r'\]\(([^)]+)\)', text):
        ref = m.group(1).strip()
        if ref.startswith(('http://', 'https://', '#')):
            continue
        assert (ROOT / ref).resolve().exists(), f'broken README link: {ref}'


def test_all_evidence_json_strict_and_unsafe_receipts_not_promoted():
    for folder in (ROOT / 'evidence', ROOT / 'docs/data'):
        for path in folder.rglob('*.json'):
            obj = json.loads(path.read_text(), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
            assert obj is not None, path
    for p in (ROOT / 'docs/data/run_card.json', ROOT / 'docs/data/current-run-card.json'):
        assert json.loads(p.read_text())['verdict'] == 'negative'
    assert 'DO_NOT_SUBMIT' in json.loads((ROOT / 'docs/data/validation_receipt.json').read_text())['ready_to_submit_verdict']
    sidecar = next((ROOT / 'docs/downloads').glob('*maw-gsi*.json'))
    assert json.loads(sidecar.read_text())['approved_for_weekly_slot'] is False


def test_regenerators_and_preflight_cannot_promote(tmp_path):
    old = subprocess.run([sys.executable, str(ROOT / 'scripts/build_pages_and_readme.py')],
                         cwd=ROOT, capture_output=True, text=True)
    assert old.returncode != 0 and 'superseded' in old.stderr
    before = (ROOT / 'docs/index.html').read_text()
    run1 = subprocess.run([sys.executable, str(ROOT / 'scripts/build_submit_page.py')], cwd=ROOT, capture_output=True, text=True)
    assert run1.returncode == 0, run1.stderr
    assert (ROOT / 'docs/index.html').read_text() == before  # regenerating reproduces the same page
    assert 'No. Do not submit this file yet.' in before
    figures = subprocess.run([sys.executable, str(ROOT / 'scripts/generate_figures.py')], capture_output=True, text=True)
    assert figures.returncode != 0 and 'stopped' in figures.stderr.lower()
    assert not (ROOT / 'src/apartgems/uniqueness.py').exists()
    text = (ROOT / 'src/apartgems/features.py').read_text()
    assert 'derived_sgmc_faults' not in text  # not silently used as a feature
