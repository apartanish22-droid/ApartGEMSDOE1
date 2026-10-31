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
    for site in (24, 25, 27, 28, 30, 31, 32, 33, 36):
        assert f'GEMSDOE{site}' in index
    assert '0.2778' in index and 'user-reported; unconfirmed' in index
    assert 'Latest negative run card · 2026-10-31' in index
    assert 'Latest repository review · 2026-10-31' in index
    assert 'apartgems1-stepover-relay-dots-20261031.tif' in index
    assert 'Existing geometry-only candidate — duplicate stop' in index
    assert 'New unique candidate generated this session' not in index
    assert '99.93%' in index and 'fixed-mask catalogue-proxy' in index
    assert 'do not submit' in index.lower() and 'null/NaN' in index
    assert 'Highest reported claim in this nine-site set: GEMSDOE32 · 0.2778' in index
    assert 'Unique among focus nine? (closest peer)' in index
    assert 'Overlap with the prior ApartGEMSDOE1 candidate; not the focus-nine test' in index
    audit = json.loads((ROOT / 'evidence/focus9_reaudit.json').read_text())
    assert all(r['max_forward_overlap_3px_among_focus9'] > .70 for r in audit['sites'])
    assert all(r['closest_focus_site'] for r in audit['sites'])
    assert 'not comparable' in index and '11,360' in index
    guide = (docs / 'executive-summary.html').read_text()
    assert '0.4544' in guide and 'direct read' in guide and 'scheduled feed separately remains unavailable' in guide
    assert 'team-level public standing' in guide and 'not a score receipt for any file' in guide
    assert 'outside bounds' in index.lower() and 'zeros' in index.lower()
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
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert card['raster_sha256'] in text
    assert 'Future-session start-up: read before every run' in text
    dec = json.loads((ROOT / 'evidence/submission_decision_2026-10-31.json').read_text())
    assert dec['candidate']['sha256'] in text and 'No. Do not submit the new GeoTIFF' in text
    assert 'docs/PROJECT_BRIEF.md' in text and 'docs/download-and-submit.html' in text
    assert 'not measured' in text.lower()
    assert 'Latest repository review 2026-10-31' in text
    assert 'run_card_2026-10-31.json' in text
    assert 'Current lane status — stop' in text and 'single method' in text
    assert 'AUC >0.90 is leakage' in text and 'three experiments or two hours' in text
    assert 'Unique among focus nine? (closest peer)' in text
    assert 'Prior candidate overlap (diagnostic)' in text
    assert 'GEMSDOE32' in text and '0.2778' in text and 'no linked organizer receipt' in text
    assert 'apartgems1-stepover-relay-dots-20261031.tif' in text
    assert '2,765/2,767' in text and '99.93%' in text
    assert 'not fold-honest and not a leaderboard estimate' in text
    assert 'does not demonstrate an improvement over the unverified 0.2778 claim' in text
    assert 'The highest reported claim among these nine is **GEMSDOE32 · 0.2778**' in text
    assert 'HOLDOUT-DTI' in text and '11,360' in text and '95% CI' in text
    for m in re.finditer(r'\]\(([^)]+)\)', text):
        ref = m.group(1).strip()
        if ref.startswith(('http://', 'https://', '#')):
            continue
        assert (ROOT / ref).resolve().exists(), f'broken README link: {ref}'


def test_public_run_card_mirrors_match_canonical_evidence():
    canonical = (ROOT / 'evidence/run_card_2026-10-31.json').read_bytes()
    card = json.loads(canonical)
    assert card['verdict'] == 'negative'
    assert card['branch'].startswith('arena/')
    assert card['hypothesis']['status'] == 'NOT TESTED'
    other = card['additional_repository_candidate_review']
    assert other['verdict'] == 'negative' and other['ok_to_download_and_submit'] is False
    assert other['registry_comparison']['forward_overlap_3px'] > .70
    assert other['holdout_dti']['evidence_class'] == 'HOLDOUT-DTI'
    assert json.loads((ROOT / 'evidence/run_card.json').read_text())['verdict'] == 'negative'
    for name in ('run_card.json', 'current-run-card.json', 'run_card_2026-10-31.json'):
        assert (ROOT / 'docs/data' / name).read_bytes() == canonical


def test_direct_leaderboard_read_is_dated_and_distinct_from_failed_feed():
    observed = json.loads((ROOT / 'evidence/official_rules_check.json').read_text())['leaderboard_observed']
    feed = json.loads((ROOT / 'docs/data/public_feed.json').read_text())
    assert observed['observed_utc'] == '2026-10-31'
    assert observed['top_rank'] == 1 and observed['top_participant'] == 'xiaofanhu'
    assert observed['top_public_dti'] == 0.4544
    assert 'not the scheduled feed' in observed['method']
    assert feed['status'] == 'unavailable' and feed['top_public_dti'] is None
    assert observed['top_public_dti'] != feed['top_public_dti']


def test_all_evidence_json_strict_and_unsafe_receipts_not_promoted():
    for folder in (ROOT / 'evidence', ROOT / 'docs/data'):
        for path in folder.rglob('*.json'):
            obj = json.loads(path.read_text(), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
            assert obj is not None, path
    latest_text = (ROOT / 'evidence/run_card_2026-10-31.json').read_text()
    for p in (ROOT / 'docs/data/run_card.json', ROOT / 'docs/data/current-run-card.json',
              ROOT / 'docs/data/run_card_2026-10-31.json'):
        assert json.loads(p.read_text())['verdict'] == 'negative'
        assert p.read_text() == latest_text
    for name in ('focus9_reaudit.json', 'literal_witness_audit.json'):
        assert json.loads((ROOT / 'docs/data' / name).read_text()) == json.loads((ROOT / 'evidence' / name).read_text())
    assert (ROOT / 'docs/repository-review-2026-10-31.md').read_text() == (ROOT / 'evidence/repository_review_2026-10-31.md').read_text()
    assert 'DO_NOT_SUBMIT' in json.loads((ROOT / 'docs/data/validation_receipt.json').read_text())['ready_to_submit_verdict']
    sidecar = next((ROOT / 'docs/downloads').glob('*maw-gsi*.json'))
    assert json.loads(sidecar.read_text())['approved_for_weekly_slot'] is False


def test_regenerators_and_preflight_cannot_promote(tmp_path):
    builder = subprocess.run([sys.executable, str(ROOT / 'scripts/build_pages_and_readme.py')],
                             cwd=ROOT, capture_output=True, text=True)
    assert builder.returncode == 0, builder.stderr
    generated_index = (ROOT / 'docs/index.html').read_text()
    assert 'No file is ready to submit' in generated_index
    assert '99.93%' in generated_index and 'research only' in generated_index.lower()
    assert 'No. Do not submit the new GeoTIFF' in generated_index and 'download-and-submit.html' in generated_index
    generated_readme = (ROOT / 'README.md').read_text()
    assert 'apartgems1-stepover-relay-dots-20261031.tif' in generated_readme
    assert 'not safe to submit' in generated_readme.lower()
    assert 'No. Do not submit the new GeoTIFF' in generated_readme
    decision_bytes = (ROOT / 'evidence/submission_decision_2026-10-31.json').read_bytes()
    assert (ROOT / 'docs/data/submission_decision_2026-10-31.json').read_bytes() == decision_bytes
    assert 'No. Do not submit this file yet.' in (ROOT / 'docs/download-and-submit.html').read_text()
    current_card = (ROOT / 'evidence/run_card_2026-10-31.json').read_bytes()
    for name in ('run_card_2026-10-31.json', 'run_card.json', 'current-run-card.json'):
        assert (ROOT / 'docs/data' / name).read_bytes() == current_card
    assert (ROOT / 'docs/repository-review-2026-10-31.md').read_bytes() == (ROOT / 'evidence/repository_review_2026-10-31.md').read_bytes()
    figures = subprocess.run([sys.executable, str(ROOT / 'scripts/generate_figures.py')], capture_output=True, text=True)
    assert figures.returncode != 0 and 'stopped' in figures.stderr.lower()
    assert not (ROOT / 'src/apartgems/uniqueness.py').exists()
    text = (ROOT / 'src/apartgems/features.py').read_text()
    assert 'derived_sgmc_faults' not in text  # not silently used as a feature


def test_submission_decision_record_and_page_are_consistent():
    """The new E3 GeoTIFF is not cleared: format passes, uniqueness gate fails, holdout not measured."""
    import hashlib
    docs = ROOT / 'docs'
    dec = json.loads((ROOT / 'evidence/submission_decision_2026-10-31.json').read_text())
    assert dec['verdict']['ok_to_submit'] is False
    assert dec['uniqueness']['exact_copy_found'] is False
    assert dec['uniqueness']['unique_vs_registry'] is False
    assert dec['uniqueness']['spatial_duplicate_flags'] == 186
    assert dec['uniqueness']['spatial_duplicate_flags_sparse_dot_files'] + dec['uniqueness']['spatial_duplicate_flags_dense_surfaces'] == 186
    cand = ROOT / dec['candidate']['repo_path']
    assert cand.is_file() and cand.stat().st_size == dec['candidate']['bytes']
    assert hashlib.sha256(cand.read_bytes()).hexdigest() == dec['candidate']['sha256']
    assert len(dec['candidate']['submission_name']) <= 140 and len(dec['candidate']['note']) <= 140
    page = (docs / 'download-and-submit.html').read_text()
    assert 'localhost' not in page and '127.0.0.1' not in page
    assert dec['candidate']['sha256'] in page and 'No. Do not submit the new GeoTIFF' not in page
    assert 'No. Do not submit this file yet.' in page
    assert 'unconfirmed' in page.lower() and '0.2778' in page and '0.4544' in page
    for site in (24, 25, 27, 28, 30, 31, 32, 33, 36):
        assert f'GEMSDOE{site}' in page
    parser = AttrCollector(); parser.feed(page)
    for ref in parser.refs:
        if ref.startswith(('http://', 'https://', '#', 'mailto:')):
            continue
        clean = ref.split('#', 1)[0].split('?', 1)[0]
        assert (docs / clean).resolve().exists(), f'broken {ref} in download-and-submit.html'
    audit = json.loads((ROOT / 'evidence/focus9_reaudit.json').read_text())
    assert all(r['max_forward_overlap_3px_among_focus9'] > .70 for r in audit['sites'])
    xor = audit['geometry_proof']['xor_differing_pixels']
    assert xor == 0
