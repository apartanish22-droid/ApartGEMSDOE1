#!/usr/bin/env python3
"""Build the decision dashboard and README from the current pinned audit.

This renderer never promotes a file. It deliberately fails if the audit is not
negative; a future approved release must use a new, independently tested renderer
and a separate selector rather than inheriting historical PASS text.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ESC = lambda value: html.escape(str(value), quote=True)


def shell(title: str, active: str, body: str) -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="An evidence-first decision dashboard for the DOE GEMS challenge.">
<title>{ESC(title)} · Apart GEMS</title><link rel="stylesheet" href="styles.css"><script src="feed.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="topbar-inner"><a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">A<span>·</span></span><span>APART <b>GEMS</b><small>RESEARCH DESK</small></span></a>
<nav aria-label="Main navigation"><a {'aria-current="page"' if active == 'overview' else ''} href="index.html">Overview</a><a {'aria-current="page"' if active == 'summary' else ''} href="executive-summary.html">Executive summary</a><a href="data/current-run-card.json">Run card ↗</a></nav>
<a class="nav-source" href="https://github.com/apartanish22-droid/ApartGEMSDOE1">View repository <span aria-hidden="true">↗</span></a></div></header>
<main id="main">{body}</main>
<footer><div class="footer-inner"><div><strong>APART GEMS</strong><p>Evidence before upload. Research in service of better fault mapping.</p></div><div class="footer-links"><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Official challenge ↗</a><a href="data/review_20261028.json">Audit data ↗</a><a href="research/2026-10-28-review-passes.md">Review passes ↗</a><a href="research/2026-10-28-preregistration.md">Research plan ↗</a></div><p class="footer-note">Static research dashboard · no competition submission is made by this site</p></div></footer></body></html>'''


def main() -> int:
    audit = json.loads((ROOT / "evidence/review_20261028.json").read_text(encoding="utf-8"))
    card = json.loads((ROOT / "evidence/run_card_20261028.json").read_text(encoding="utf-8"))
    if audit["verdict"] != "negative" or card["verdict"] != "negative":
        raise ValueError("This renderer only supports the current negative decision")
    previous = audit["previous_apart_submission"]
    parallel_path = ROOT / "evidence/run_card_cah.json"
    parallel = json.loads(parallel_path.read_text(encoding="utf-8"))
    if parallel["verdict"] != "negative":
        raise ValueError("Parallel historical card must be negative for this renderer")
    (DOCS / "data/parallel-run-card.json").write_text(parallel_path.read_text(encoding="utf-8"), encoding="utf-8")
    (DOCS / "data/parallel-static-holdout.json").write_text(
        (ROOT / "evidence/concordance_holdout.json").read_text(encoding="utf-8"), encoding="utf-8")
    cah_score = parallel["holdout_dti"]["dti"]
    cah_ci = parallel["holdout_dti"]["ci95"]
    cah_overlap = parallel["correlation_overlap_vs_registry"]["vs_GEMSDOE32_B2"]["dot_overlap_3px_frac"]
    prior_file = Path(previous["file"]).name
    prior_url = "downloads/" + prior_file
    lattice_pct = previous["forward_overlap_3px_with_lattice"] * 100
    min_pct = audit["lattice_witness"]["lower_bound_at_prior_dot_count"] * 100
    rows = sorted(audit["focus_sites"], key=lambda r: r["owner_reported_historical_result"], reverse=True)

    table_rows = []
    md_rows = []
    for row in rows:
        label = row["site"].replace("GEMSDOE", "")
        score = row["owner_reported_historical_result"]
        pct = row["forward_3px_overlap_worst_focus9"] * 100
        peer = row["worst_focus9_peer"].replace("GEMSDOE", "")
        fmt = "All cells finite and in [0,1]" if row["all_grid_finite_0_1_local_policy"] else "Exterior NaNs · local all-finite policy fails"
        table_rows.append(f'''<tr><td><a class="site-number" href="{ESC(row["source_url"])}">{ESC(row["site"])}</a></td>
<td class="file-cell"><a href="{ESC(row["download_url"])}">{ESC(row["research_file"])}</a><small>Research copy · SHA-256 {ESC(row["sha256"][:12])}…<br>{ESC(fmt)}</small></td>
<td><strong>{score:.4f}</strong><small>OWNER-REPORTED<br>not receipt-confirmed</small></td><td><span class="muted">Unavailable</span></td>
<td><strong class="negative">No</strong><small>{pct:.1f}% near site {ESC(peer)}</small></td><td><span class="tag danger">DO NOT SUBMIT</span></td></tr>''')
        md_rows.append(f'| [{row["site"]}]({row["download_url"]}) | `{row["research_file"]}` | {score:.4f} owner-reported, unverified | Unavailable | No; {pct:.1f}% near GEMSDOE{peer} | Do not resubmit |')
    table_html = "\n".join(table_rows)
    md_table = "\n".join(md_rows)

    shared_table = f'''<div class="table-wrap" role="region" aria-label="Nine-site comparison; scroll horizontally for all columns" tabindex="0"><table><caption class="sr-only">Nine historical site files; research only and not approved for submission</caption>
<thead><tr><th scope="col">Site</th><th scope="col">Pinned research file</th><th scope="col">Reported result</th><th scope="col">Future estimate</th><th scope="col">Unique vs focus 9?</th><th scope="col">Decision</th></tr></thead><tbody>{table_html}</tbody></table></div>'''

    body = f'''<section class="hero wrap"><div class="hero-copy"><div class="eyebrow"><span></span> DOE GEMS / DECISION BRIEF</div>
<div class="status"><span aria-hidden="true">●</span> NOT READY TO SUBMIT</div><h1>Better evidence<br><em>before upload.</em></h1>
<p class="lead">No new GeoTIFF is cleared. The previous file passes a local format check, but fails the required literal uniqueness rule. No competition slot was used.</p>
<div class="actions"><a class="button primary" href="executive-summary.html">Open executive summary <span aria-hidden="true">↗</span></a><a class="button secondary" href="data/current-run-card.json">View the run card <span aria-hidden="true">↗</span></a></div>
<p class="micro">Last complete saved-byte audit · 28 OCT 2026 &nbsp; / &nbsp; <a href="data/review_20261028.json">See evidence</a></p></div>
<aside class="decision-card" aria-label="Release gate status"><div class="card-top"><div><span class="kicker">RELEASE GATES</span><h2>Current decision</h2></div><span class="card-icon" aria-hidden="true">↗</span></div>
<div class="gate"><span class="gate-icon ok">✓</span><div><strong>Historical format</strong><small>Locally valid against mirror template</small></div><span class="gate-result">PASS</span></div>
<div class="gate"><span class="gate-icon bad">×</span><div><strong>Literal uniqueness</strong><small>{lattice_pct:.2f}% of old dots near a registry lattice</small></div><span class="gate-result bad-text">FAIL</span></div>
<div class="gate"><span class="gate-icon wait">–</span><div><strong>New holdout &amp; canaries</strong><small>No new experiment after the stop</small></div><span class="gate-result">NOT RUN</span></div>
<div class="gate"><span class="gate-icon wait">–</span><div><strong>Weekly slot selection</strong><small>A separate step, never automatic here</small></div><span class="gate-result">NOT APPROVED</span></div>
<div class="card-bottom"><span>DECISION</span><strong>Negative · do not upload</strong></div></aside></section>

<section class="snapshot wrap" aria-label="Research snapshot"><div class="section-line"><span class="kicker">THE SNAPSHOT</span><span>01 / STATUS</span></div>
<div class="metrics"><article><span class="metric-label">BEST FOCUS-SITE REPORT</span><strong>0.2778</strong><p>GEMSDOE32 · owner-reported, not receipt-confirmed</p></article>
<article><span class="metric-label">OLD FILE / LATTICE</span><strong>{lattice_pct:.2f}%</strong><p>of old dots within 3 pixels · literal limit 70%</p></article>
<article><span class="metric-label">PUBLIC LEADERBOARD</span><strong id="public-score">—</strong><p id="public-feed-state">Loading dated official observation…</p></article>
<article><span class="metric-label">EXPERIMENTS THIS REVIEW</span><strong>0 <i>/ 3</i></strong><p>0 slots used · a parallel historical run used 3 arms</p></article></div></section>

<section class="section wrap" id="decision"><div class="section-heading"><div><span class="kicker">THE DECISION</span><h2>A valid file is not<br><em>a valid submission.</em></h2></div><p>Format, scientific performance, uniqueness and slot selection are different gates. The old green “OK to submit” banner was incorrect and has been withdrawn.</p></div>
<div class="insight-grid"><article class="insight accent"><span class="card-number">01</span><h3>What we verified</h3><p>The previously shipped TIFF is single-band float32; all its cells are finite and in [0, 1]. Its grid matches the committed mirror sample. This is a local preflight, not organizer acceptance.</p><a href="{ESC(prior_url)}" download>Download historical TIFF for research only ↗</a><small class="hash">SHA-256 {ESC(previous["sha256"])}</small></article>
<article class="insight"><span class="card-number">02</span><h3>Why we stopped</h3><p>A registered discrete lattice catches {lattice_pct:.2f}% of its dots. A separate registered continuous raster covers every allowed cell under the shared literal positive-support definition. No exemption was applied.</p><a href="data/review_20261028.json">Inspect both witnesses ↗</a></article>
<article class="insight"><span class="card-number">03</span><h3>What a score means</h3><p>No defensible leaderboard forecast exists. A hide-and-recover score tests withheld mapped faults, not the organizer’s hidden new-fault set. Scores from different splits are not interchangeable.</p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Read the official metric ↗</a></article></div>
<div class="notice"><strong>Protocol conflict, made explicit.</strong> At the old 38,500-dot budget the discrete lattice alone imposes a minimum {min_pct:.2f}% overlap even with optimal placement. The dense-witness interpretation is also a universal blocker under literal positive support. Do not game the few lattice holes or silently exempt registry files.</div></section>

<section class="section wrap" id="focus-sites"><div class="section-heading compact"><div><span class="kicker">THE COMPARISON</span><h2>Nine sites, <em>one clear decision.</em></h2></div><p>Historical leaders are useful for learning, not new submissions. Their reported results are not organizer-confirmed receipts, and no row has a validated future leaderboard estimate.</p></div>
{shared_table}<p class="table-note">On small screens, scroll the table horizontally to see every column. Pinned research copies may use different exterior-NaN packaging from the reported upload. Directional 3-pixel overlaps are measured for these nine copies only; they are not a complete current registry. <a href="data/review_20261028.json">Full measurements ↗</a></p></section>

<section class="section analysis-band"><div class="wrap analysis-grid"><div><span class="kicker light">THE SCIENCE</span><h2>Why did the<br><em>GEMSDOE32</em> family lead?</h2><p>We can verify the construction, not the hidden causal story. The pinned GEMSDOE32 support equals the GEMSDOE25 dot set after removing all 6,436 dots within 200 m of the visible catalogue; the comparison has zero differing support pixels. The GEMSDOE25 and GEMSDOE30 dot sets are also identical.</p><p>The official metric uses maximum kernel credit per truth pixel, but accumulates false-positive mass across predictions. Thinning redundant dots and removing unhelpful near-catalogue predictions could improve that trade-off. Hidden labels are unavailable, so the observed score change does not prove this mechanism.</p><a class="inline-light" href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2">Organizer clarification on known-fault masking ↗</a></div>
<div class="evidence-box"><span class="kicker light">VERIFIED PIXEL RELATION</span><div class="formula">GEMSDOE32 B2 <span>=</span><br>GEMSDOE25 D2.8<br><small>minus dots ≤ 2 px from the catalogue</small></div><div class="evidence-stats"><div><strong>44,090</strong><small>parent dots</small></div><div><strong>37,654</strong><small>remaining dots</small></div><div><strong>0</strong><small>support differences</small></div></div><p>Geometric comparison of pinned research copies, not a leaderboard-score receipt.</p></div></div></section>

<section class="section wrap" id="research"><div class="section-heading compact"><div><span class="kicker">NEXT HYPOTHESES</span><h2>Contrarian, <em>but testable.</em></h2></div><p>Four ideas were ranked before implementation. The top candidate is provisional only: no assigned lane was supplied, and the mandatory registry rule stops the run before training or placement.</p></div>
<div class="research-list"><a href="research/2026-10-28-preregistration.md"><span>01</span><div><strong>Gravity–magnetic axial consensus</strong><small>Multi-scale aligned gradients in low-relief terrain; unfaulted contacts are a mimic.</small></div><b>READ PLAN ↗</b></a>
<a href="research/2026-10-28-preregistration.md"><span>02</span><div><strong>Conductance contrast across a structural edge</strong><small>Potential buried contacts; clay and salinity can mimic the signal.</small></div><b>READ PLAN ↗</b></a>
<a href="research/2026-10-28-preregistration.md"><span>03</span><div><strong>Radiometric change-point asymmetry</strong><small>Requires authoritative aligned channel metadata before validation.</small></div><b>DATA NEEDED ↗</b></a>
<a href="research/2026-10-28-preregistration.md"><span>04</span><div><strong>Paleolake shoreline counterfactual</strong><small>Official maps are listed; aligned layers and coverage are not yet verified.</small></div><b>DATA NEEDED ↗</b></a></div>
<div class="notice"><strong>Parallel research, also negative.</strong> A separate historical concordance run recorded three static-file arms; its leading arm had HOLDOUT-DTI {cah_score:.4f} (95% CI [{cah_ci[0]:.4f}, {cah_ci[1]:.4f}], <code>gems57-pooled-hide-v2</code>, 11,360 withheld positives) and {cah_overlap*100:.2f}% overlap with GEMSDOE32. It was not independently replayed here, used full-catalogue-derived predecessor rasters rather than fold-local reconstructions, and cannot approve a slot or forecast a leaderboard score. <a href="data/parallel-run-card.json">Parallel run card ↗</a></div></section>

<section class="section wrap sources" id="sources"><div class="section-line"><span class="kicker">SOURCES &amp; LIMITATIONS</span><span>04 / PROVENANCE</span></div><div class="source-grid"><div><h2>Trace the evidence.</h2><p>The cached feature stack was restored and hash-checked from a public owner mirror. That proves mirror integrity, not identity with authenticated organizer data. The official data page redirects to login here.</p><p>The contest asks for fault probabilities; a predicted anomaly is not proof of a geothermal vent. The official rules require disclosure of generative-AI use in the narrative where applicable.</p></div><ul><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData · task, metric &amp; format ↗</a></li><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData · live public leaderboard ↗</a></li><li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR · official rules &amp; weekly limit ↗</a></li><li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS · GeoDAWN data release ↗</a></li><li><a href="https://gdr.openei.org/submissions/1391">DOE GDR · INGENIOUS compilation ↗</a></li><li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">DrivenData · reference solution ↗</a></li></ul></div></section>'''

    summary = f'''<section class="page-hero wrap"><a class="back" href="index.html">← Back to overview</a><div class="eyebrow"><span></span> EXECUTIVE SUMMARY / 28 OCT 2026</div><div class="status"><span aria-hidden="true">●</span> NO FILE APPROVED</div><h1>Submission guide,<br><em>without the guesswork.</em></h1><p class="lead">The scientifically honest action today is to wait. A locally valid TIFF is available for research, but it fails the literal uniqueness gate and must not be uploaded as a new submission.</p><div class="actions"><a class="button secondary" href="{ESC(prior_url)}" download>Download old TIFF · research only ↗</a><a class="button ghost" href="data/current-run-card.json">Current JSON run card ↗</a></div><p class="micro">Historical file SHA-256 · <span class="hash">{ESC(previous["sha256"])}</span></p></section>
<section class="section wrap"><div class="section-heading compact"><div><span class="kicker">EXECUTIVE SCORECARD</span><h2>What to download <em>and why.</em></h2></div><p>The best owner-reported result among the nine sites is GEMSDOE32, but it is already a historical submission and not unique under the requested rule. No future leaderboard score can be estimated reliably from these records.</p></div>{shared_table}<p class="table-note">On small screens, scroll the table horizontally to see every column. All links are for research only. The numeric historical results are owner-reported / unverified; linked files may be alternative NaN/zero packaging. No personal submission-page receipt is available.</p></section>
<section class="section wrap"><div class="section-heading compact"><div><span class="kicker">WHEN A FILE PASSES</span><h2>The upload <em>checklist.</em></h2></div><p>These are instructions for a future, separately selected file—not permission to upload the current research artifacts.</p></div><div class="steps">
<div><span>01</span><div><h3>Confirm every automated gate</h3><p>Check the saved surface and final dots against the complete registry, every feature-only leakage canary, and a buffered whole-component holdout against a matched best. A format pass alone is not enough.</p></div></div>
<div><span>02</span><div><h3>Check the exact file</h3><p>Validate a single-band float32 GeoTIFF, CRS, shape and transform against the authenticated organizer template; inspect all prediction values for the [0, 1] range. The local all-finite/zero-exterior policy is conservative and does not guarantee portal acceptance.</p></div></div>
<div><span>03</span><div><h3>Confirm eligibility and quota</h3><p>The published rules say three submissions per week; the remaining account-specific quota is unknown here. A separate selector must approve the candidate. Review the rules and AI-use disclosure requirements.</p></div></div>
<div><span>04</span><div><h3>Submit the selected file</h3><p>Sign in to <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData</a>, choose Submit → Make new submission, select the approved .tif, and add the generated short note (at most 140 characters). No filename or note is assigned to this negative run.</p></div></div>
<div><span>05</span><div><h3>Save the receipt</h3><p>Record the submitted file’s SHA-256, exact note, timestamp and organizer receipt. Only then may that result be labeled ORGANIZER-CONFIRMED; keep the public and private rounds distinct.</p></div></div></div></section>
<section class="section wrap"><div class="notice"><strong>Known limitations.</strong> Organizer data and individual receipts require authentication; the full parallel registry is not present in this checkout. Prior E3 canaries omitted its composite crest feature and its E1 arm also consumed a hydrothermal composite. Its earlier promotion is withdrawn. Band-15 basement-thickness assumptions require authoritative metadata. A separate parallel concordance run recorded three static-file arms and failed uniqueness at {cah_overlap*100:.2f}% overlap; its inputs were not rebuilt fold-locally. <a href="data/parallel-run-card.json">Historical parallel card ↗</a></div><p><a href="research/2026-10-28-preregistration.md">Read the preregistered research directions ↗</a> &nbsp; · &nbsp; <a href="data/review_20261028.json">Read the saved-byte audit ↗</a></p></section>'''

    (DOCS / "index.html").write_text(shell("Decision dashboard", "overview", body), encoding="utf-8")
    (DOCS / "executive-summary.html").write_text(shell("Executive summary", "summary", summary), encoding="utf-8")

    readme = f'''# ApartGEMSDOE1 — evidence before upload

> **NOT READY TO SUBMIT.** No new TIFF was generated and no weekly slot was used in this run. The previously shipped file passes a local format preflight but fails the literal 3-pixel uniqueness rule. Its previous “PASS — OK TO SUBMIT” recommendation is withdrawn.
>
> [Open the decision dashboard](docs/index.html) · [Executive summary and future submission instructions](docs/executive-summary.html) · [Current run card](evidence/run_card_20261028.json) · [Reproducible audit](evidence/review_20261028.json) · [Three review passes](docs/research/2026-10-28-review-passes.md)

The [historical TIFF]({previous["file"]}) is available **for research only**. SHA-256 `{previous["sha256"]}`. The user reports an earlier result for the same submission ID, but no organizer receipt links it to these bytes. Do not upload it as a new candidate.

## Executive summary — nine focus sites

All scores in this table are **OWNER-REPORTED / UNVERIFIED**, not ORGANIZER-CONFIRMED; the linked immutable research copies may use alternative exterior packaging. There is no defensible estimate of a new file's hidden leaderboard score. Uniqueness here is measured only against these nine pinned copies, using the requested directional 3-pixel rule.

| Site | Research file; do not submit | Historical reported result | Future leaderboard estimate | Unique vs other focus sites? | Decision |
| --- | --- | --- | --- | --- | --- |
{md_table}

The public leaderboard can change; use the [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) or the timestamped dashboard feed, which is a public observation, not a submission receipt.

## Why GEMSDOE32 reported 0.2778

The pinned GEMSDOE32 dot support is exactly the pinned GEMSDOE25 D2.8 support with all dots at distance ≤2 pixels from the catalogue removed: 44,090 → 37,654, with **zero differing support pixels**. The pinned GEMSDOE25 and GEMSDOE30 supports also match exactly. The official [distance-weighted Tversky metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) gives each truth pixel its maximum nearby credit and accumulates false-positive weight; thinning redundant dots and removing unhelpful near-catalogue dots is a plausible explanation, not proof of causation. [DrivenData staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2) state that pixels corresponding to known faults are masked. Hidden labels and personal receipts are unavailable, so improvement above 0.2778 cannot be promised or estimated.

## Why the previous release is blocked

* Fresh saved-byte check: the prior Apart TIFF has {lattice_pct:.2f}% of its dots within 3 pixels of the [pinned registered lattice]({audit["lattice_witness"]["source_url"]}), exceeding the literal 70% limit. Its earlier audit excluded that lattice from the controlling gate.
* The lattice leaves {audit["lattice_witness"]["uncovered_allowed_pixels"]:,} allowed cells uncovered; at the old 38,500-dot budget, even optimally placing distinct dots would produce at least {min_pct:.2f}% overlap. This is a geometric lower bound, not a score.
* A [registered continuous raster]({audit["continuous_witness"]["source_url"]}) covers every allowed cell under the shared finite-positive support definition. Under that literal interpretation every nonempty candidate is blocked. Do not silently exempt it or place dots in lattice holes to manufacture a PASS.
* The previous run's **HOLDOUT-DTI** was recorded as 0.0523, 95% CI [0.0375, 0.0687], `gems57-pooled-hide-v2`, 11,360 withheld positives. It was not replayed here; its canary omitted `crest_prominence`, and E1 also used that hydrothermal composite. It is not a leaderboard estimate or a current promotion gate.
* The user did not supply the single assigned method paragraph referenced in the protocol. This run preregistered a **provisional** direction for discussion but did not run a new experiment after the blocking preflight. The full current registry and organizer-authenticated template are not available.

## Parallel historical concordance run

A separate session recorded **three exploratory static-raster arms** and no submission file. Its leading arm recorded **HOLDOUT-DTI {cah_score:.6f}**, 95% CI [{cah_ci[0]:.6f}, {cah_ci[1]:.6f}], `gems57-pooled-hide-v2`, 11,360 withheld positives, but had **{cah_overlap*100:.2f}%** directional overlap with GEMSDOE32 B2 and a negative verdict. Its predecessor TIFFs were built with the full catalogue, not rebuilt using fold-visible inputs; the static replay is not a clean model holdout. The measured score and CI are retained without treating them as a leaderboard forecast or an approved release. See the [historical card](evidence/run_card_cah.json) and [diagnostic terms](evidence/concordance_holdout.json). Its runner is retired; this review performed zero further experiments and spent zero slots. Preserve the separate [concurrent review card](evidence/run_card_20261028_concurrent_review.json) and [one-witness lattice check](evidence/lattice_stop.json).

## Research and source inventory

[Four ranked geological hypotheses](docs/research/2026-10-28-preregistration.md) identify layers, signatures, missing-fault rationale, mimics, and cost. The first proposes multi-scale gravity–magnetic gradient alignment with low-relief weighting; it is not validated. The task predicts faults, not proven geothermal vents.

| Source | Verified scope / limitation |
| --- | --- |
| [DrivenData problem and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Official objective, single-band float32 format and distance-weighted Tversky metric. |
| [Competition data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Redirected to login in this review; organizer-origin bytes are not independently authenticated here. |
| [Reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | Official baseline; supports both CPU and GPU environments. |
| [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Public magnetic/radiometric data, described as CC0 by USGS. |
| [DOE INGENIOUS](https://gdr.openei.org/submissions/1391) | Public regional compilation; CC BY 4.0 attribution applies. |
| [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) | Free elevation products; coverage and exact inputs must be checked. |
| [USGS MF-2323](https://pubs.usgs.gov/mf/1999/mf-2323/) | Lake-extent shapefile downloads listed; alignment and use are not validated. |
| [NLR official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Three submissions per week; eligible submissions require applicable generative-AI disclosure. |

The feature stack was restored from a pinned owner mirror, not an authenticated organizer download. Large data live under ignored `.cache/`; `data/manifest.json` records what is actually present. “Band 15 is sedimentary basement thickness” is not established by the organizer's published feature description; the historical dip-backprojection interpretation needs metadata verification.

## Reproduce this negative review

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# Fetches immutable, SHA-256-pinned public GitHub witnesses; --offline reuses verified cached copies.
.venv/bin/python scripts/audit_focus_sites_and_registry.py
.venv/bin/python scripts/build_pages_and_readme.py
.venv/bin/pytest -q
# Diagnostic only; this never authorizes an upload.
.venv/bin/python scripts/validate_submission.py --format-only {previous["file"]}
```

`scripts/run_apartgems_pipeline.py` is intentionally retired: it checked uniqueness after placement, exempted dense priors, used an arbitrary threshold instead of the same-evaluator best, and could publish unconditional approval. `scripts/submission_writer.py` remains a format-only writer; it is not a selector. A static TIFF holdout replay is diagnostic, not a fold-local model validation.

## Next work and limitations

1. Resolve the literal registry rule's saturation and obtain an explicit single lane; never silently change the threshold or definition of a dot.
2. Authenticate the organizer template, obtain authoritative feature metadata, complete an immutable current registry, and preserve per-feature canaries including derived features.
3. Re-run a fold-local candidate and current best on identical buffered whole-component folds, with paired spatial-bootstrap confidence intervals. Only a scientifically passing candidate may enter a separate weekly-slot selector.
4. Revisit the cached input provenance and licensing, validate all external channels, and keep any data too large for Git in ignored/external storage. The scheduled Pages workflow refreshes the public leaderboard observation; a failed refresh explicitly shows unavailable.

## Standing Reference: Original Competition Task & Protocol Specification

Read this standing brief at the start of future work. It is a consolidated reference, not a verbatim copy of the full conversation. Core values: **Maximize P(Win)** by weighing risk and tradeoffs; **Own the Outcome** end to end. The goal is a uniquely generated, auditable competition TIFF and an obvious submission decision, not a renamed previous upload or a fabricated score. Focus on GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36; report their highest supplied historical results, provenance and uniqueness honestly.

**Parallel-run protocol (standing instructions):**

1. **LANE.** Stay within the assigned single method. If rank correlation with any registry raster exceeds 0.90, or more than 70% of candidate dots lie within 3 pixels of one registry raster's dots, log the duplicate and stop. Check both before placement and on final dots.
2. **REUSE.** Use the shared cached feature stack, `evaluate_holdout.py` and `submission_writer.py`. Hide whole fault segments with a buffer, derive all catalogue-based features only from visible faults, mask visible faults pixel-exactly, and score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). Fix shared tools once, not via a private fork.
3. **EVIDENCE.** Label a measured holdout number HOLDOUT-DTI with evaluator version, withheld positives and 95% CI, or label a number ORGANIZER-CONFIRMED only when copied from a submission-page receipt. A projection is never a score; owner reports remain explicitly unverified.
4. **LEAKAGE CANARY.** Test each feature alone on the holdout; AUC above 0.90 means leakage until disproved.
5. **RUN CARD.** Record hypothesis, mechanism, named non-fault mimic, holdout DTI + CI, correlation/overlap vs registry, raster SHA-256, validator output, submission name and ≤140-character note, and `promote` or `negative`. Negative results are deliverables.
6. **BUDGET.** Stop after three experiments or two hours. A real weekly submission slot is selected separately; do not select or spend one in a research run.

Before implementing, rank 3–5 untried geological hypotheses and name the relevant data, physical signature, missing-fault rationale, difference from this repo, mimics and cost; validate the top candidate on a spatially blocked holdout before using a slot. Use official sources and label unverifiable claims; require no human inspection for automated validation. Make the dashboard and executive submission instructions clear, record limitations, perform three review passes, and create and merge a pull request when possible.
'''
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("Built negative-decision dashboard, executive summary, and standing README.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
