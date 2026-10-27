import hashlib
import json
import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links += [v for k, v in attrs if k == 'href']


class SiteTest(unittest.TestCase):
    def test_local_links(self):
        pages = [ROOT/'index.html', *ROOT.glob('docs/*.html'), *ROOT.glob('docs/sites/*.html')]
        for path in pages:
            parser = Links()
            parser.feed(path.read_text())
            for link in parser.links:
                url = urlsplit(link)
                if not url.scheme and not url.netloc and url.path:
                    self.assertTrue((path.parent / unquote(url.path)).is_file(), (path, link))

    def test_negative_card_labels_demo_and_has_no_fake_metrics(self):
        card = json.loads((ROOT/'run_card.json').read_text())
        self.assertEqual(card['verdict'], 'negative')
        self.assertEqual(card['raster_sha256'], '397648e33ad640acd32c2fedcdcdefaf7815fa21bd276264bd2bcdff61af6e9a')
        self.assertIsNone(card['holdout_dti']['value'])
        self.assertIsNone(card['correlation_overlap_vs_registry']['rank_correlation'])
        self.assertLessEqual(len(card['submission_note']), 140)
        self.assertIn('DO NOT SUBMIT', card['submission_note'])

    def test_nine_site_sources_pinned(self):
        entries = json.loads((ROOT/'evidence/site_inventory.json').read_text())
        self.assertEqual(len(entries), 9)
        for entry in entries:
            self.assertEqual(len(entry['ref']), 40)
            self.assertEqual(len(entry['page_sha256']), 64)
            self.assertTrue((ROOT/f'docs/sites/{entry["repo"]}.html').is_file())
            snapshot = ROOT/f'research/sites/{entry["repo"]}.html'
            self.assertTrue(snapshot.is_file())
            digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
            self.assertEqual(digest, entry['page_sha256'], entry['repo'])
