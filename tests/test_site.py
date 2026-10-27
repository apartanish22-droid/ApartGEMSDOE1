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
    paths = [ROOT / "index.html", ROOT / "docs/executive-summary.html", ROOT / "docs/research.html"]
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
    manifest = json.loads((ROOT / "catalog/reference_sources.json").read_text())
    audit = json.loads((ROOT / "evidence/fleet_audit.json").read_text())
    rendered = build_site.table(manifest, audit, "")
    assert rendered.count('data-review-repo=') == 9
    assert rendered.count('Not estimable') == 9
    assert rendered.count('USER-REPORTED') == 9
    assert rendered.count('research only') == 9
    assert rendered.count('Historical / already reported') == 9
    for field in ('Source', 'Research file', 'Supplied claim', 'Estimate', 'Unique vs peers?', 'Submit?'):
        assert rendered.count(f'data-label="{field}"') == 9
    assert all(row["site"] in rendered for row in manifest["reference_sites"])
    summary = (ROOT / "docs/executive-summary.html").read_text()
    assert "SUBMISSION DOWNLOAD: UNAVAILABLE" in summary
    assert 'type="button" disabled>Submission download unavailable' in summary


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
