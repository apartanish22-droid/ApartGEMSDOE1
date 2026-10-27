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
<td data-label="Source"><div><a class="file-link" href="{esc(row['site_url'])}">{esc(site)}</a><span class="feed-state">Freshness not checked</span></div></td>
<td data-label="Research file"><div><a class="file-link" href="{esc(file_url)}">Historical .tif ↗</a><span class="file-name">{esc(filename)}</span><span class="fine">SHA-256 {esc(row['sha256'][:12])}… · research only</span></div></td>
<td data-label="Supplied claim"><div><strong>{esc(row['reported_value'])}</strong><span class="file-name">USER-REPORTED<br>Not receipt-verified</span></div></td>
<td data-label="Estimate"><div class="text-muted">Not estimable</div></td>
<td data-label="Unique vs peers?"><div><span class="text-negative">No</span><span class="file-name">{worst['fraction']*100:.2f}% within 3 px of {esc(worst['site'])}</span></div></td>
<td data-label="Submit?"><div><span class="text-negative">NO</span><span class="file-name">Historical / already reported</span></div></td></tr>''')
    return f'''<div class="data-wrap"><table><caption class="sr-only">Historical reference files from nine sites. None is approved for submission.</caption><thead><tr>
<th scope="col">Source / freshness</th><th scope="col">Research file to download</th><th scope="col">Highest supplied claim</th><th scope="col">Estimated score</th><th scope="col">Unique vs peers?</th><th scope="col">Submit?</th></tr></thead><tbody>{''.join(lines)}</tbody></table></div>
<div class="feed gap-top"><button id="refresh-sources" type="button">Refresh GitHub freshness ↻</button><span id="feed-summary" class="fine" aria-live="polite">JavaScript not enabled or freshness not yet checked. This is not a score feed.</span></div>
<p class="fine">Audit: {esc(audit['generated_utc'][:19].replace('T', ' '))} UTC. Claims are supplied by the owner, not organizer-confirmed receipts. The table covers one pinned historical raster per site, not all possible submissions. Directed overlap is measured against the other eight references. A changed GitHub head does not re-audit its new content.</p>'''


def build(manifest: dict, audit: dict) -> None:
    bound = audit["lattice"]["budget_37654_lower_bound"]["minimum_fraction"] * 100
    historical_count = len(audit["historical_references"])
    stop_count = sum(v["duplicate_stop"] for v in audit["peer_comparisons"].values())
    common_table_root = table(manifest, audit, "")
    common_table_docs = table(manifest, audit, "../")
    home = f'''
<section class="hero"><div class="shell hero-grid"><div><p class="eyebrow">GEMS PRIZE · RESEARCH DECISION DESK</p>
<h1>Better evidence.<br><em>Better decisions.</em></h1>
<p class="hero-copy">We are building a reproducible path to a genuinely new geothermal fault prediction. Right now, the evidence does not support spending a submission slot.</p>
<div class="actions"><a class="button primary" href="docs/executive-summary.html">Open submission brief <span aria-hidden="true">→</span></a><a class="button ghost" href="docs/research.html">Explore the evidence</a></div></div>
<aside class="hero-card" aria-label="Submission status"><span class="pill light-negative"><span class="dot"></span>Not ready to submit</span>
<h2>No new file is approved.</h2><p>No candidate TIFF or reliable score estimate exists in this checkout. Historical files below are for research only.</p><div class="rule"></div>
<div class="mini"><span>Research status</span><strong>Blocked preflight</strong></div><div class="mini"><span>Weekly slots used</span><strong>None</strong></div></aside></div></section>
<section class="section tight"><div class="shell"><div class="metrics">
<div class="metric"><span class="metric-top">Submission clearance</span><strong class="flag">None</strong><p>No file is approved to upload.</p></div>
<div class="metric"><span class="metric-top">Priority sites reviewed</span><strong>{historical_count:02d}</strong><p>One pinned historical file per site.</p></div>
<div class="metric"><span class="metric-top">Lattice preflight</span><strong>{bound:.2f}%</strong><p>Minimum overlap at 37,654 dots; not a score.</p></div>
<div class="metric"><span class="metric-top">Best supplied claim</span><strong>0.2778</strong><p>USER-REPORTED · not receipt-verified.</p></div></div></div></section>
<section class="section"><div class="shell"><div class="section-heading"><div><p class="overline">01 / THE DECISION</p><h2>What stands in the way?</h2><p>Format validity, scientific performance and uniqueness are separate questions. None can stand in for the others.</p></div></div>
<div class="grid-2"><article class="card"><p class="overline">PARALLEL-RUN PROTOCOL</p><h3>A lane and a complete registry are missing.</h3><p>The prompt refers to an assigned method paragraph, but no such paragraph is present. We did not invent one or run a holdout. The historical registry here is only a small, pinned subset.</p><a class="text-link" href="docs/research.html">See the blockers and next steps →</a></article>
<article class="card"><p class="overline">INDEPENDENT GEOMETRY CHECK</p><h3>The literal overlap rule has a conflict.</h3><p>A registered calibration lattice forces at least {bound:.2f}% overlap at the usual dot budget, above the 70% stop threshold. The bound is conditional on the mirrored footprint; it is not a performance result.</p><a class="text-link" href="docs/research/decision-2026-10-27.md">Read the reproducible proof →</a></article></div></div></section>
<section class="section"><div class="shell"><div class="section-heading"><div><p class="overline">02 / HISTORICAL REFERENCES</p><h2>Nine sites, one honest comparison.</h2><p>These are the highest values supplied for each site, not verified organizer receipts. No row is a recommended upload.</p></div><a class="text-link" href="docs/executive-summary.html">Full submission guide →</a></div>{common_table_root}</div></section>
<section class="section tight"><div class="shell"><div class="callout"><p class="overline">SCIENTIFIC INTERPRETATION</p><h2>Why the GEMSDOE32 claim may have improved</h2><p>Its historical raster is a subset of the GEMSDOE25 dots after near-catalogue dots were removed. Sparse placement and pruning can reduce redundant prediction mass under the distance-weighted metric, but hidden truth is unavailable; the mechanism and claimed score are not proven. A close-to-catalogue exclusion can also miss real new faults.</p><p><a class="text-link" href="docs/research.html">Read the limitations and sources →</a></p></div></div></section>
'''
    summary = f'''
<section class="subhero"><div class="shell"><p class="overline">EXECUTIVE SUMMARY / 27 OCT 2026</p><h1>Know exactly what is safe to submit.</h1><p>Submission decisions are evidence-led and automatic. A historic download, a valid TIFF or an attractive local number is not approval to use a weekly slot.</p></div></section>
<section class="section tight"><div class="shell"><div class="notice"><strong>SUBMISSION DOWNLOAD: UNAVAILABLE · DO NOT SUBMIT.</strong><br>No new candidate, holdout result, complete registry check, validated file, name or note exists for this session. The downloads below are previous files for research only. A separate selector must approve any future file.</div></div></section>
<section class="section tight"><div class="shell"><div class="section-heading"><div><p class="overline">01 / FILE DECISION</p><h2>What can I download?</h2><p>Historical files can be inspected for learning; they are not unique new submissions. A leaderboard estimate is unavailable without validated calibration.</p></div></div>
<div class="card"><span class="pill negative"><span class="dot"></span>Do not submit</span><h3 class="gap-top">New competition TIFF</h3><p>Not generated. No hidden-score estimate, submission name or portal note can be supplied honestly.</p><button class="button disabled" type="button" disabled>Submission download unavailable</button> <a class="text-link" href="../evidence/run_card.json">Open the negative run card ↗</a></div></div></section>
<section class="section"><div class="shell"><div class="section-heading"><div><p class="overline">02 / NINE-SITE REVIEW</p><h2>Historical evidence, not a shortlist.</h2><p>Each historical row is a supplied, unconfirmed claim; all {stop_count} directed comparisons among these pinned examples exceed the requested overlap limit.</p></div></div>{common_table_docs}</div></section>
<section class="section"><div class="shell"><div class="section-heading"><div><p class="overline">03 / SUBMISSION PLAYBOOK</p><h2>When a candidate is eventually cleared</h2><p>These are future instructions, not permission to submit anything today. No manual visual inspection is required by this project.</p></div></div><div class="steps">
<article class="step"><span class="step-number">01</span><h3>Pass the gates</h3><p>A lane, leakage canaries, blocked holdout win, complete registry checks, exact-byte validation and a separate selector approval must all be recorded.</p></article>
<article class="step"><span class="step-number">02</span><h3>Download the cleared file</h3><p>Only a future approved single-band GeoTIFF will be offered here with its exact SHA-256, unique name and note of at most 140 characters.</p></article>
<article class="step"><span class="step-number">03</span><h3>Use the contest form</h3><p>On DrivenData, open Submit → Make new submission, choose the cleared file and paste its note. Check the current limit displayed on the form.</p></article>
<article class="step"><span class="step-number">04</span><h3>Keep the receipt</h3><p>Record the organizer's submission-page receipt against the file hash. Choose one final submission for both prize rounds before the deadline.</p></article></div>
<p class="fine gap-top">Format details and known uncertainties: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">official submission format</a> · <a href="https://community.drivendata.org/t/submission-amount-question/11553/2">organizer quota clarification</a> · <a href="research/decision-2026-10-27.md">our format irregularities</a>.</p></div></section>
'''
    research = f'''
<section class="subhero"><div class="shell"><p class="overline">RESEARCH / SCIENCE &amp; PROVENANCE</p><h1>Explore the science. Keep the uncertainty.</h1><p>The objective is fault mapping relevant to geothermal exploration, not a direct inventory of geothermal vents. A catalogue holdout and an organizer's hidden test set are different populations.</p></div></section>
<section class="section tight"><div class="shell"><div class="grid-2"><article class="card"><p class="overline">POSSIBLE MECHANISM</p><h3>What the historical bytes show</h3><p>The pinned GEMSDOE32 support is the GEMSDOE25 support minus 6,436 dots, all within two pixels of the mirrored catalogue. That geometry, not the hidden reason for a claimed score, is observable.</p><p>Because the official metric takes maximum nearby credit for each truth pixel, less redundant placement is plausible; pruning may also remove real corrections near mapped faults.</p><a class="text-link" href="research/decision-2026-10-27.md">Full forensic analysis →</a></article>
<article class="card"><p class="overline">WHAT WE DO NOT KNOW</p><h3>Can it beat the historical claim?</h3><p>The official public leaderboard has displayed a higher result, but no method in this repository has been evaluated to establish that it can. Historical owner claims lack artifact-linked organizer receipts. No leaderboard prediction is justified.</p><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Open the official leaderboard ↗</a></article></div></div></section>
<section class="section"><div class="shell"><div class="section-heading"><div><p class="overline">01 / NEXT HYPOTHESES</p><h2>Four ideas, none selected.</h2><p>Qualitative priorities only. The task's referenced single method lane is absent, and parallel work prevents us from inventing one.</p></div><a class="text-link" href="research/hypotheses-2026-10-27.md">Read the complete slate →</a></div>
<div class="grid-2"><article class="card"><p class="overline">01 · MODERATE COST</p><h3>Dual-step persistence</h3><p>Look for consistent, co-oriented magnetic and gravity steps at multiple scales. Mimics include lithologic contacts and survey artifacts. A hash-pinned third-party feature mirror was restored; it is not organizer-authenticated.</p></article>
<article class="card"><p class="overline">02 · HIGH COST</p><h3>Multi-channel drainage disruption</h3><p>Test repeated stream deflections and slope breaks against an independent geophysical edge. Erosion, roads, lithology and lava dams can imitate this signal; suitable DEM coverage is not downloaded.</p></article>
<article class="card"><p class="overline">03 · MODERATE / HIGH COST</p><h3>Hydrothermal disequilibrium transects</h3><p>Contrast spring/well chemistry across lineaments against matched nonthermal sites. Fluid mixing and biased sampling are major confounders. The official archive metadata is public; its bytes were not fetched here.</p></article>
<article class="card"><p class="overline">04 · MODERATE COST</p><h3>Conductance-depth discordance</h3><p>Compare aligned conductivity and depth-to-base gradients with the regional gravity trend. Clay, lake deposits and inversion artifacts can mimic a fault; the depth-band description needs clarification.</p></article></div></div></section>
<section class="section"><div class="shell"><div class="section-heading"><div><p class="overline">02 / SOURCE LEDGER</p><h2>Official sources, transparent limits.</h2><p>Links are for review. The GitHub source freshness indicator on the overview does not scrape the competition site.</p></div></div><div class="sources">
<div class="source"><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData · problem &amp; metric ↗</a><p>Authoritative task, data description, scoring formula and submission format.</p></div>
<div class="source"><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR · official rules ↗</a><p>Eligibility, required narrative, two rounds, selection and deadlines.</p></div>
<div class="source"><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS · GeoDAWN release ↗</a><p>Airborne magnetic and radiometric survey; release page states CC0.</p></div>
<div class="source"><a href="https://www.usgs.gov/3d-elevation-program">USGS · 3DEP ↗</a><p>Elevation data; USGS says the products are free without use restrictions.</p></div>
<div class="source"><a href="https://gdr.openei.org/submissions/1391">GDR · INGENIOUS compilation ↗</a><p>Public regional geology and geothermal compilation, CC BY 4.0; maintain attribution.</p></div>
<div class="source"><a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">DrivenData · known-fault masking ↗</a><p>Staff clarification: mapped labels are pixel-exactly masked; new fault labels may lie nearby.</p></div></div>
<div class="notice gap-top"><strong>Irregularities:</strong> the mirrored sample contains mapped-fault positives despite the organizer's zero-prediction sample description; the public and PDF deadline wording differ; portal acceptance and current quota are unknown. <a href="research/decision-2026-10-27.md">See details</a>.</div></div></section>
'''
    (ROOT / "index.html").write_text(page("Overview", "overview", "", home), encoding="utf-8")
    (ROOT / "docs/executive-summary.html").write_text(page("Executive summary", "summary", "../", summary), encoding="utf-8")
    (ROOT / "docs/research.html").write_text(page("Research & sources", "research", "../", research), encoding="utf-8")


def main() -> None:
    manifest = json.loads((ROOT / "catalog/reference_sources.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "evidence/fleet_audit.json").read_text(encoding="utf-8"))
    if set(audit["historical_references"]) != {entry["site"] for entry in manifest["reference_sites"]}:
        raise ValueError("Historical audit and pinned manifest must contain the same sites")
    build(manifest, audit)
    print("Built index.html, docs/executive-summary.html, docs/research.html")


if __name__ == "__main__":
    main()
