from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "docs"


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []
    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag == "a" and "href" in fields:
            self.paths.append(fields["href"])
        if tag in ("link", "script", "img") and ("href" in fields or "src" in fields):
            self.paths.append(fields.get("href", fields.get("src")))


def test_static_local_links_resolve():
    pages = list(ROOT.rglob("*.html"))
    assert len(pages) >= 12
    for page in pages:
        parser = LinkCollector()
        parser.feed(page.read_text())
        for href in parser.paths:
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (page.parent / unquote(url.path)).resolve()
            assert target.is_file(), f"{page.relative_to(ROOT)} points to missing {href}"


def test_legacy_pages_root_has_a_working_static_fallback():
    repository = ROOT.parent
    redirect = (repository / "index.html").read_text()
    assert 'url=docs/' in redirect and 'href="docs/index.html"' in redirect
    assert (repository / ".nojekyll").is_file() and (ROOT / "index.html").is_file()
