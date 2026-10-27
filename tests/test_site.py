from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key == "href" and value:
                self.hrefs.append(value)


class SiteTests(unittest.TestCase):
    def test_internal_links_resolve_within_pages_artifact(self) -> None:
        for page in sorted(DOCS.rglob("*.html")):
            parser = LinkCollector()
            parser.feed(page.read_text(encoding="utf-8"))
            for href in parser.hrefs:
                parsed = urlsplit(href)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = (page.parent / parsed.path).resolve()
                self.assertTrue(
                    target.is_relative_to(DOCS.resolve()),
                    f"{page.relative_to(ROOT)} links outside docs/: {href}",
                )
                self.assertTrue(
                    target.exists(),
                    f"{page.relative_to(ROOT)} has a broken internal link: {href}",
                )

    def test_root_landing_routes_to_the_executive_summary(self) -> None:
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('url=docs/', page)
        self.assertIn("NOT APPROVED — NO SUBMISSION TIFF", page)
        self.assertTrue((DOCS / "index.html").exists())

    def test_no_tiff_or_zip_is_offered_for_download(self) -> None:
        for page in DOCS.rglob("*.html"):
            parser = LinkCollector()
            parser.feed(page.read_text(encoding="utf-8"))
            for href in parser.hrefs:
                path = urlsplit(href).path.lower()
                self.assertFalse(
                    path.endswith((".tif", ".tiff", ".zip")),
                    f"Unapproved artifact link in {page.relative_to(ROOT)}: {href}",
                )

    def test_executive_summary_is_fail_closed_and_covers_nine_sites(self) -> None:
        page = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertIn("NOT APPROVED — NO SUBMISSION TIFF", page)
        self.assertIn("No leaderboard score is estimated", page)
        for site in (
            "GEMSDOE24",
            "GEMSDOE25",
            "GEMSDOE27",
            "GEMSDOE28",
            "GEMSDOE30",
            "GEMSDOE31",
            "GEMSDOE32",
            "GEMSDOE33",
            "GEMSDOE36",
        ):
            self.assertIn(site, page)
        self.assertEqual(page.count("Not estimated — no compliant holdout"), 9)
        self.assertIn("Not estimated — no compliant holdout for this checkout", page)

    def test_submission_guide_explains_range_and_no_current_upload(self) -> None:
        page = (DOCS / "submit.html").read_text(encoding="utf-8")
        self.assertIn("Current status: DO NOT SUBMIT", page)
        self.assertIn("Predicted values must be in range [0, 1]", page)
        self.assertIn("maximum <code>140</code> characters", page)
        self.assertIn("ORGANIZER-CONFIRMED", page)

    def test_registry_audit_has_nine_files_and_no_unique_promotion(self) -> None:
        audit = json.loads((DOCS / "data/focus-site-audit.json").read_text(encoding="utf-8"))
        self.assertEqual(len(audit["artifacts"]), 9)
        self.assertEqual(len(audit["pairwise"]), 72)
        self.assertTrue(
            all(not row["passes_final_dot_uniqueness_gate_vs_selected_registry"] for row in audit["artifacts"])
        )
        self.assertEqual(
            {(x["site_a"], x["site_b"]) for x in audit["exact_prediction_mask_duplicates"]},
            {("GEMSDOE25", "GEMSDOE30")},
        )
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) for row in audit["artifacts"]))

    def test_run_card_is_negative_without_fabricated_measurements(self) -> None:
        card = json.loads((DOCS / "data/run-card.json").read_text(encoding="utf-8"))
        self.assertEqual(card["verdict"], "negative")
        self.assertEqual(card["holdout_dti"]["label"], "HOLDOUT-DTI")
        self.assertEqual(card["holdout_dti"]["status"], "NOT RUN")
        self.assertIsNone(card["holdout_dti"]["pooled_dti"])
        self.assertIsNone(card["raster_sha256"])
        self.assertIsNone(card["submission_name"])
        self.assertLessEqual(len(card["submission_note"]), 140)

    def test_project_charter_and_session_instructions_are_present(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Read this entire README before planning", readme)
        self.assertIn("HOLDOUT-DTI", readme)
        self.assertIn("Maximize P(Win)", readme)
        self.assertIn("read the entire root `README.md`", agents)
        self.assertIn("do not infer one", agents)


if __name__ == "__main__":
    unittest.main()
