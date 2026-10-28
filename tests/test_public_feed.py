from datetime import datetime, timezone
from pathlib import Path
import json
import os
import subprocess
import sys

import pytest
from scripts.update_public_feed import make_snapshot, parse_public_leaderboard

HTML = '''<!doctype html><table><thead><tr><th>Rank</th><th>Team</th><th>Best public DW-Tversky</th></tr></thead>
<tbody><tr><td>#1</td><a>Example team</a></td><td>0.4544</td></tr><tr><td>#2</td><td>Team B</td><td>0.4200</td></tr></tbody></table>'''


def test_public_leaderboard_requires_unambiguous_labeled_rank_one():
    assert parse_public_leaderboard(HTML) == .4544
    with pytest.raises(ValueError):
        parse_public_leaderboard(HTML.replace('DW-Tversky', 'unrelated score'))
    with pytest.raises(ValueError):
        parse_public_leaderboard(HTML.replace('<td>0.4544</td>', '<td>0.4544</td><td>0.1234</td>'))
    with pytest.raises(ValueError):
        parse_public_leaderboard(HTML.replace('#1', '#3'))


def test_refresh_failures_clear_score_instead_of_publishing_stale_value(tmp_path):
    out = tmp_path / 'feed.json'
    out.write_text('{"status":"ok","top_public_dti":0.99}')
    fixture = tmp_path / 'login.html'
    fixture.write_text('<html><p>Sign in</p></html>')
    script = Path(__file__).resolve().parents[1] / 'scripts/update_public_feed.py'
    env = {**os.environ, 'GITHUB_ACTIONS': 'true'}
    p = subprocess.run([sys.executable, str(script), '--html', str(fixture), '--out', str(out)], capture_output=True, text=True, env=env)
    assert p.returncode == 1
    assert '::warning title=Public leaderboard refresh failed::' in p.stdout
    feed = json.loads(out.read_text())
    assert feed['status'] == 'unavailable' and feed['top_public_dti'] is None
    assert 'not a submission receipt' in feed['evidence_class'].lower()


def test_public_score_is_not_a_file_level_receipt_or_forecast():
    snap = make_snapshot(HTML, now=datetime(2026, 10, 28, tzinfo=timezone.utc))
    assert snap['status'] == 'ok' and snap['top_public_dti'] == .4544
    assert 'NOT A SUBMISSION RECEIPT' in snap['evidence_class']
    assert 'not a forecast' in snap['caveat']
