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


def test_html_pages_are_negative_have_local_links_and_no_localhost():
    docs = ROOT / 'docs'
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert card['verdict'] == 'negative'
    for name in ('index.html', 'executive-summary.html'):
        text = (docs / name).read_text()
        assert 'localhost' not in text and '127.0.0.1' not in text
        assert card['raster_sha256'] in text
        assert 'do not submit' in text.lower() or 'do not upload' in text.lower()
        assert 'research only' in text.lower()
        assert 'ready to submit' not in text.lower() or 'no file is ready to submit' in text.lower()
        assert '99.68%' in text and '70%' in text
        assert 'ORGANIZER-CONFIRMED means' not in text  # no blanket file-level confirmation claim
        parser = AttrCollector(); parser.feed(text)
        assert parser.refs
        for ref in parser.refs:
            if ref.startswith(('http://', 'https://', '#', 'mailto:')):
                continue
            clean = ref.split('#', 1)[0].split('?', 1)[0]
            target = (docs / clean).resolve()
            assert target.exists() and target.stat().st_size > 0, f'broken {ref} in {name}'
    index = (docs / 'index.html').read_text()
    assert 'outside_footprint' in (docs / 'data/format_irregularity_audit.json').read_text()
    assert 'FAIL' in index and 'NaN' in index and 'DO NOT SUBMIT' in index
    for site in (24, 25, 27, 28, 30, 31, 32, 33, 36):
        assert f'GEMSDOE{site}' in index
    assert '0.2778' in index and 'user-reported; unconfirmed' in index
    assert 'not comparable' in index and '11,360' in index
    public = json.loads((docs / 'data/public_feed.json').read_text())
    assert public['top_public_dti'] == 0.4544
    assert public['evidence_class'] == 'OFFICIAL PUBLIC LEADERBOARD OBSERVATION; NOT A SUBMISSION RECEIPT'
    assert 'top_public_dti' in (docs / 'feed.js').read_text()


def test_research_pages_are_rendered_and_linked_without_score_projections():
    docs = ROOT / 'docs'
    sources = (docs / 'research-sources.html').read_text()
    hypotheses = (docs / 'next-hypotheses.html').read_text()
    assert '<table>' in sources and 'AG100' in sources and '100 m' in sources
    assert 'not run in this stopped lane' in hypotheses.lower()
    assert 'flight-line repeatability' in hypotheses.lower()
    for name, text in [('research-sources.html', sources), ('next-hypotheses.html', hypotheses)]:
        parser = AttrCollector(); parser.feed(text)
        for ref in parser.refs:
            if ref.startswith(('http://', 'https://', '#', 'mailto:')):
                continue
            assert (docs / ref.split('#')[0].split('?')[0]).resolve().exists(), f'broken {ref} in {name}'


def test_archived_h6_cannot_promote_after_literal_stop():
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
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert card['raster_sha256'] in text
    assert 'Standing reference: task and parallel-run protocol' in text
    assert 'GEMSDOE32' in text and '0.2778' in text and 'no linked organizer receipt' in text
    assert 'HOLDOUT-DTI' in text and '11,360' in text and '95% CI' in text
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
    canonical = json.loads((ROOT / 'evidence/run_card.json').read_text())
    for p in (ROOT / 'docs/data/run_card.json', ROOT / 'docs/data/current-run-card.json'):
        published = json.loads(p.read_text())
        assert published['verdict'] == 'negative'
        assert published['raster_sha256'] == canonical['raster_sha256']
        assert published['validator_output']['checks']['outside_footprint_is_nan'] is False
    public_receipt = json.loads((ROOT / 'docs/data/validation_receipt.json').read_text())
    assert public_receipt['evidence_status'] == 'SUPERSEDED_HISTORICAL_ALL_FINITE_POLICY'
    assert public_receipt['format_policy_status'] == 'SUPERSEDED_HISTORICAL_ALL_FINITE_ZERO_EXTERIOR_POLICY'
    assert public_receipt['current_format_validation']['current_format_pass'] is False
    assert public_receipt['current_format_validation']['current_format_failure_checks'] == [
        'outside_footprint_is_nan', 'nodata_tag_is_nan'
    ]
    assert 'DO_NOT_SUBMIT' in public_receipt['ready_to_submit_verdict']
    sidecar = next((ROOT / 'docs/downloads').glob('*maw-gsi*.json'))
    assert json.loads(sidecar.read_text())['approved_for_weekly_slot'] is False


def test_regenerators_and_preflight_cannot_promote(tmp_path):
    builder = subprocess.run([sys.executable, str(ROOT / 'scripts/build_pages_and_readme.py')],
                             cwd=ROOT, capture_output=True, text=True)
    assert builder.returncode == 0, builder.stderr
    assert 'No file is ready to submit' in (ROOT / 'docs/index.html').read_text()
    figures = subprocess.run([sys.executable, str(ROOT / 'scripts/generate_figures.py')], capture_output=True, text=True)
    assert figures.returncode != 0 and 'stopped' in figures.stderr.lower()
    assert not (ROOT / 'src/apartgems/uniqueness.py').exists()
    text = (ROOT / 'src/apartgems/features.py').read_text()
    assert 'derived_sgmc_faults' not in text  # not silently used as a feature
