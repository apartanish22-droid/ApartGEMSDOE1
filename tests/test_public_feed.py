from datetime import datetime, timezone
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

import pytest
from scripts import update_public_feed
from scripts.update_public_feed import is_fresh_observation, make_snapshot, parse_public_leaderboard, unavailable

HTML = '''<!doctype html><table><thead><tr><th>Rank</th><th>Team</th><th>Best public DW-Tversky</th></tr></thead>
<tbody><tr><td>#1</td><td>Example team</td><td>0.4544</td></tr><tr><td>#2</td><td>Team B</td><td>0.4200</td></tr></tbody></table>'''
MARKDOWN = '''| Rank | Participant | Best public DW-Tversky | Shared work |
| --- | --- | --- | --- |
| #1 | Leader | 0.4544 | |
| #2 | Runner-up | 0.4200 | |
'''


def test_public_leaderboard_requires_unambiguous_labeled_rank_one():
    assert parse_public_leaderboard(HTML) == .4544
    with pytest.raises(ValueError):
        parse_public_leaderboard(HTML.replace('DW-Tversky', 'unrelated score'))
    with pytest.raises(ValueError):
        parse_public_leaderboard(HTML.replace('<td>0.4544</td>', '<td>0.4544</td><td>0.1234</td>'))
    with pytest.raises(ValueError):
        parse_public_leaderboard(HTML.replace('#1', '#3'))


def test_public_leaderboard_accepts_rendered_pipe_table_but_keeps_strict_rank_check():
    assert parse_public_leaderboard(MARKDOWN) == .4544
    with pytest.raises(ValueError):
        parse_public_leaderboard(MARKDOWN.replace('DW-Tversky', 'other metric'))
    with pytest.raises(ValueError):
        parse_public_leaderboard(MARKDOWN.replace('0.4544', '0.4544 | 0.1234'))


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
    assert feed['checked_utc'] and feed['observed_utc'] is None
    assert feed['parse_diagnostics']['table_count'] == 0
    assert 'not a submission receipt' in feed['evidence_class'].lower()


def test_unavailable_refresh_records_check_time_not_a_fictitious_observation():
    checked = '2026-10-30T00:00:00+00:00'
    feed = unavailable('timeout', checked_utc=checked)
    assert feed['status'] == 'unavailable'
    assert feed['checked_utc'] == checked
    assert feed['observed_utc'] is None
    assert feed['top_public_dti'] is None


def test_public_score_is_not_a_file_level_receipt_or_forecast():
    snap = make_snapshot(HTML, now=datetime(2026, 10, 28, tzinfo=timezone.utc))
    assert snap['status'] == 'ok' and snap['top_public_dti'] == .4544
    assert snap['checked_utc'] == snap['observed_utc'] == '2026-10-28T00:00:00+00:00'
    assert 'NOT A SUBMISSION RECEIPT' in snap['evidence_class']
    assert 'not a forecast' in snap['caveat']
    assert snap['source'].endswith('/leaderboard/')
    assert snap['data_endpoint'].endswith('/leaderboard_partial/')


def test_feed_freshness_fails_closed_for_old_future_and_unavailable_observations():
    from datetime import timedelta

    now = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)
    fresh = make_snapshot(HTML, now=now - timedelta(hours=23))
    stale = make_snapshot(HTML, now=now - timedelta(hours=25))
    future = make_snapshot(HTML, now=now + timedelta(minutes=10))
    unavailable = {"status": "unavailable", "observed_utc": now.isoformat(), "top_public_dti": .99}

    assert fresh["max_age_seconds"] == 24 * 60 * 60
    assert is_fresh_observation(fresh, now=now)
    assert not is_fresh_observation(stale, now=now)
    assert not is_fresh_observation(future, now=now)
    assert not is_fresh_observation(unavailable, now=now)
    assert not is_fresh_observation({"status": "ok", "top_public_dti": .1, "observed_utc": "not-a-date"}, now=now)
    assert not is_fresh_observation({"status": "ok", "top_public_dti": 1.01, "observed_utc": now.isoformat()}, now=now)


def test_checked_in_feed_never_exposes_stale_value_as_current():
    root = Path(__file__).resolve().parents[1]
    feed = json.loads((root / "docs/data/public_feed.json").read_text())
    assert feed["status"] == "unavailable"
    assert feed["checked_utc"] and feed["observed_utc"] is None
    assert feed["top_public_dti"] is None
    assert feed["historical_scheduled_snapshot"]["top_public_dti"] == .4544
    assert "historical" in feed["historical_scheduled_snapshot"]["status"]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is unavailable")
def test_browser_feed_hides_stale_snapshot_and_shows_fresh_observation():
    script = r"""
const target = {textContent: ''};
global.document = {getElementById: () => target};
global.fetch = async () => ({ok: true, json: async () => JSON.parse(process.env.FEED_JSON)});
Date.now = () => Date.parse(process.env.NOW);
require('./docs/feed.js');
setTimeout(() => process.stdout.write(target.textContent), 0);
"""
    base = {"status": "ok", "top_public_dti": .4544, "max_age_seconds": 86400}
    env = {**os.environ, "NOW": "2026-10-30T12:00:00Z"}

    stale = subprocess.run(
        ["node", "-e", script], cwd=Path(__file__).resolve().parents[1],
        env={**env, "FEED_JSON": json.dumps({**base, "observed_utc": "2026-10-28T00:00:00Z"})},
        capture_output=True, text=True, check=True)
    fresh = subprocess.run(
        ["node", "-e", script], cwd=Path(__file__).resolve().parents[1],
        env={**env, "FEED_JSON": json.dumps({**base, "observed_utc": "2026-10-30T11:00:00Z"})},
        capture_output=True, text=True, check=True)

    assert "unavailable or stale" in stale.stdout
    assert "0.4544" not in stale.stdout
    assert "0.4544" in fresh.stdout
    assert "not a file-level submission receipt" in fresh.stdout


def test_fetch_uses_public_html_fragment_not_empty_page_shell(tmp_path, monkeypatch, capsys):
    import io
    requested = []
    def fetch(request, timeout):
        requested.append(request.full_url)
        return io.BytesIO(HTML.encode())
    monkeypatch.setattr(update_public_feed.urllib.request, 'urlopen', fetch)
    out = tmp_path / 'feed.json'
    monkeypatch.setattr(sys, 'argv', ['update_public_feed', '--out', str(out)])
    assert update_public_feed.main() == 0
    assert requested == [update_public_feed.PARTIAL_URL]
    snapshot = json.loads(out.read_text())
    assert snapshot['top_public_dti'] == .4544
    assert snapshot['checked_utc'] == snapshot['observed_utc']
