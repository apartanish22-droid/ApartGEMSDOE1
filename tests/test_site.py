import hashlib
import json
import unittest
from pathlib import Path
from html.parser import HTMLParser

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
        for path in [ROOT/'index.html', *ROOT.glob('docs/sites/*.html')]:
            parser = Links()
            parser.feed(path.read_text())
            for link in parser.links:
                if not link.startswith(('https://', 'http://', '#')):
                    self.assertTrue((path.parent/link).is_file(), (path, link))

    def test_negative_card_no_fake_metrics(self):
        card = json.loads((ROOT/'evidence/run_card.json').read_text())
        self.assertEqual(card['verdict'], 'negative')
        self.assertIsNone(card['raster_sha256'])
        self.assertIsNone(card['holdout_dti'])
        self.assertLessEqual(len(card['note']), 140)

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
