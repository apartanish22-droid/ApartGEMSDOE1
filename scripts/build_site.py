#!/usr/bin/env python3
"""Build the static Pages site from pinned claims and the measured fleet audit.

No organizer website is scraped. Historical values remain explicitly unverified;
no local measurement can turn a claim into an organizer submission receipt.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, active: str, prefix: str, content: str) -> str:
    nav = [("overview", "Overview", "index.html"),
           ("summary", "Executive summary", "docs/executive-summary.html"),
           ("research", "Research & sources", "docs/research.html")]
    links = "".join(f'<a href="{prefix}{path}"' + (' aria-current="page"' if key == active else '') + f'>{label}</a>'
                    for key, label, path in nav)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Evidence-led GEMS fault-mapping research and submission readiness.">
<title>{esc(title)} · Apart GEMS</title><link rel="stylesheet" href="{prefix}docs/assets/style.css">
<script defer src="{prefix}docs/assets/feed.js"></script></head>
<body><a class="skip" href="#main">Skip to content</a><header class="header"><div class="shell header-inner">
<a class="brand" href="{prefix}index.html" aria-label="Apart GEMS research overview"><span class="brand-mark" aria-hidden="true">✳</span><span class="brand-name">APART / GEMS<small>RESEARCH DESK</small></span></a>
<nav class="nav" aria-label="Main navigation">{links}</nav>
<a class="header-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition ↗</a>
</div></header><main id="main">{content}</main>
<footer class="footer"><div class="shell footer-inner"><span>APART / GEMS &nbsp;·&nbsp; Evidence before upload.</span><span><a href="{prefix}evidence/run_card.json">Run card</a> &nbsp;·&nbsp; <a href="{prefix}evidence/fleet_audit.json">Audit data</a> &nbsp;·&nbsp; <a href="https://github.com/apartanish22-droid/ApartGEMSDOE1">Repository</a></span></div></footer></body></html>\n'''


def table(manifest: dict, audit: dict, prefix: str) -> str:
    lines = []
    for row in manifest["reference_sites"]:
        site = row["site"]
        measure = audit["historical_references"][site]
        worst = measure["maximum_peer_overlap"]
        file_url = f'https://github.com/{row["owner"]}/{row["repo"]}/raw/{row["ref"]}/{quote(row["path"], safe="/")}'
        filename = row["path"].split("/")[-1]
        lines.append(f'''<tr data-review-repo="{esc(site)}" data-review-head="{esc(row['review_head'])}">
  <td data-label="Source"><div><a class="file-link" href="{esc(row['site_url'])}">{esc(site)}</a><span class="feed-state">Freshness not checked</span><a class="file-name" href="{esc(prefix)}docs/sites/{esc(site)}.html">Local site review →</a></div></td>
<td data-label="Research file"><div><a class="file-link" href="{esc(file_url)}">Historical .tif ↗</a><span class="file-name">{esc(filename)}</span><span class="fine">SHA-256 {esc(row['sha256'][:12])}… · research only</span></div></td>
<td data-label="Supplied claim"><div><strong>{esc(row['reported_value'])}</strong><span class="file-name">USER-REPORTED<br>Not receipt-verified</span></div></td>
<td data-label="Estimate"><div class="text-muted">Not estimable</div></td>
<td data-label="Unique vs peers?"><div><span class="text-negative">No</span><span class="file-name">{worst['fraction']*100:.2f}% within 3 px of {esc(worst['site'])}</span></div></td>
<td data-label="Submit?"><div><span class="text-negative">NO</span><span class="file-name">Historical / already reported</span></div></td></tr>''')
    return f'''<div class="data-wrap"><table><caption class="sr-only">Historical reference files from nine sites. None is approved for submission.</caption><thead><tr>
<th scope="col">Source / freshness</th><th scope="col">Research file to download</th><th scope="col">Highest supplied claim</th><th scope="col">Estimated score</th><th scope="col">Unique vs peers?</th><th scope="col">Submit?</th></tr></thead><tbody>{''.join(lines)}</tbody></table></div>
<div class="feed gap-top"><button id="refresh-sources" type="button">Refresh GitHub freshness ↻</button><span id="feed-summary" class="fine" aria-live="polite">JavaScript not enabled or freshness not yet checked. This is not a score feed.</span></div>
<p class="fine">Audit: {esc(audit['generated_utc'][:19].replace('T', ' '))} UTC. Claims are supplied by the owner, not organizer-confirmed receipts. The table covers one pinned historical raster per site, not all possible submissions. Directed overlap is measured against the other eight references. A changed GitHub head does not re-audit its new content.</p>'''


def site_page(row: dict, audit: dict) -> str:
    site = row['site']
    measured = audit['historical_references'][site]
    peer = measured['maximum_peer_overlap']
    file_url = f'https://github.com/{row["owner"]}/{row["repo"]}/raw/{row["ref"]}/{quote(row["path"], safe="/")}'
    content = f'''
<section class="subhero"><div class="shell"><p class="overline">NINE-SITE REVIEW / {esc(site)}</p><h1>{esc(site)}: historical evidence.</h1><p>This is a pinned research snapshot, not a recommended competition upload or a verified score receipt.</p></div></section>
<section class="section tight"><div class="shell"><div class="notice"><strong>DO NOT SUBMIT.</strong> This historical file already belongs to the reported submission history and exceeds the requested dot-overlap threshold against a pinned peer. No new file is approved.</div></div></section>
<section class="section"><div class="shell"><div class="grid-2"><article class="card"><p class="overline">SUPPLIED CLAIM</p><h3>{esc(row['reported_value'])}</h3><p>USER-REPORTED; no artifact-linked organizer receipt was obtained. A new leaderboard estimate is not available.</p><p><a class="text-link" href="{esc(row['site_url'])}">Open source site ↗</a> · <a class="text-link" href="{esc(file_url)}">Historical TIFF for research only ↗</a></p><p class="fine">SHA-256 {esc(row['sha256'])}</p></article>
<article class="card"><p class="overline">MEASURED GEOMETRY</p><h3>{peer['fraction'] * 100:.2f}% within 3 pixels of {esc(peer['site'])}</h3><p>{measured['inside_positive_pixels']:,} positive pixels in the mirrored footprint. {measured['versus_lattice']['fraction'] * 100:.2f}% are within 3 pixels of the pinned lattice. These are directional geometry measurements, not performance scores or a complete-registry clearance.</p><a class="text-link" href="../../evidence/fleet_audit.json">Full machine-readable audit ↗</a></article></div></div></section>
<section class="section tight"><div class="shell"><div class="callout"><h2>Next step</h2><p>Use an assigned lane and authenticated inputs, then evaluate a new method using the prescribed segment-buffered holdout and complete registry. A separate selector must approve any future slot.</p><a class="text-link" href="../executive-summary.html">Return to the full submission guide →</a></div></div></section>
'''
    return page(f'{site} review', 'summary', '../../', content)


def build(manifest: dict, audit: dict) -> None:
    # Preserve the current dashboard and canonical cards. Regenerate only the
    # legacy uppercase URLs using the independent parallel fleet audit.
    (ROOT / "docs/sites").mkdir(parents=True, exist_ok=True)
    for row in manifest["reference_sites"]:
        (ROOT / "docs/sites" / f"{row['site']}.html").write_text(site_page(row, audit), encoding="utf-8")


def main() -> None:
    manifest = json.loads((ROOT / "catalog/reference_sources.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "evidence/fleet_audit.json").read_text(encoding="utf-8"))
    if set(audit["historical_references"]) != {entry["site"] for entry in manifest["reference_sites"]}:
        raise ValueError("Historical audit and pinned manifest must contain the same sites")
    build(manifest, audit)
    print("Built uppercase historical site reviews")


if __name__ == "__main__":
    main()
