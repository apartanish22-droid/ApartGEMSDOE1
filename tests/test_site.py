from html.parser import HTMLParser
from pathlib import Path
import json
import shutil
import subprocess
from urllib.parse import urlparse

import pytest

import build_site

ROOT = Path(__file__).resolve().parents[1]


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"a", "link"} and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "script" and "src" in attrs:
            self.links.append(attrs["src"])


def test_build_is_deterministic_and_all_local_links_exist():
    paths = ([ROOT / "index.html", ROOT / "docs/executive-summary.html", ROOT / "docs/research.html",
              ROOT / "docs/index.html", ROOT / "docs/hypotheses.html"]
             + sorted((ROOT / "docs/sites").glob("GEMSDOE*.html")))
    assert len(list((ROOT / "docs/sites").glob("GEMSDOE*.html"))) == 9
    before = [path.read_bytes() for path in paths]
    build_site.main()
    assert before == [path.read_bytes() for path in paths]
    for path in paths:
        parser = LocalLinks()
        parser.feed(path.read_text(encoding="utf-8"))
        for link in parser.links:
            parsed = urlparse(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            assert (path.parent / parsed.path).resolve().is_file(), f"Broken link {path}: {link}"


def test_nine_rows_never_offer_an_approved_submission():
    focus = json.loads((ROOT / "evidence/focus-audit.json").read_text())
    rendered = build_site.historical_table_rows(focus)
    assert rendered.count('class="table-site"') == 9
    assert rendered.count('Not estimable') == 9
    assert rendered.count('None approved') == 9
    assert rendered.count('No exact-file organizer receipt') == 9
    for row in focus["rows"]:
        assert row["site"] in rendered
        assert row["historical_user_reported_value"] not in rendered
    summary = (ROOT / "docs/executive-summary.html").read_text()
    assert 'DO NOT SUBMIT' in summary
    assert 'Download new research TIF' in summary
    assert 'Local checks passed; portal acceptance untested.' in summary
    artifact = json.loads((ROOT / 'evidence/experiment.json').read_text())['artifact']
    assert artifact['filename'] in summary
    for row in focus["rows"]:
        local = (ROOT / 'docs/sites' / f"{row['site']}.html").read_text()
        assert 'DO NOT SUBMIT' in local and 'no organizer receipt' in local
        assert row['sha256'] in local


def test_github_feed_failure_is_fail_closed_and_labels_changes(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    harness = tmp_path / "feed-test.js"
    feed_path = json.dumps(str(ROOT / "docs/assets/feed.js"))
    harness.write_text(f'''
const assert = require('assert');
const makeRow = (repo, sha) => ({{dataset: {{reviewRepo: repo, reviewHead: sha}}, status: {{textContent: ''}}, querySelector() {{ return this.status; }} }});
const rows = [makeRow('same', 'a'.repeat(40)), makeRow('changed', 'a'.repeat(40)), makeRow('fail', 'a'.repeat(40))];
const button = {{disabled: false, addEventListener() {{}}}};
const summary = {{textContent: ''}};
global.document = {{querySelectorAll: () => rows, getElementById: id => id === 'refresh-sources' ? button : summary}};
global.fetch = async url => url.includes('/fail/') ? ({{ok: false, status: 429}}) : ({{ok: true, json: async () => ({{sha: url.includes('/same/') ? 'a'.repeat(40) : 'b'.repeat(40)}})}});
require({feed_path});
setTimeout(() => {{
  assert.equal(rows[0].status.textContent, 'Head unchanged since review');
  assert.equal(rows[1].status.textContent, 'Head changed since review');
  assert.equal(rows[2].status.textContent, 'Freshness unavailable');
  assert(summary.textContent.includes('1 changed, 1 unchanged, 1 unavailable'));
  assert.equal(button.disabled, false);
}}, 0);
''', encoding="utf-8")
    subprocess.run([node, str(harness)], check=True, timeout=15)
