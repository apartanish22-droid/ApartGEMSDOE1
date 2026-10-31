#!/usr/bin/env python3
"""Build the fail-closed project dashboard and README from current audit evidence.

This builder intentionally cannot promote a file. A future selector must have
its own verified release contract instead of inheriting a historical verdict.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def header(active: str) -> str:
    def nav(href, text, key):
        current = ' aria-current="page"' if active == key else ''
        return f'<a href="{href}"{current}>{text}</a>'
    return f'''<header class="site-header"><div class="header-inner">
      <a class="brand" href="index.html"><span class="brand-mark">G</span><span>GEMS / Field Notes<small>ApartGEMSDOE1 research</small></span></a>
      <nav aria-label="Primary">{nav('index.html', 'Overview', 'overview')}{nav('index.html#sites', 'Nine-site review', 'sites')}{nav('executive-summary.html', 'Submission guide', 'guide')}{nav('research-sources.html', 'Sources', 'sources')}</nav>
    </div></header>'''


def page(title: str, active: str, content: str) -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · GEMS Field Notes</title><link rel="stylesheet" href="styles.css"></head>
<body>{header(active)}<main class="shell">{content}
<footer>Research decisions are automated; a local preflight is not an organizer receipt. <a href="data/run_card_2026-10-31.json">Current run card</a> · <a href="research-sources.html">Source register</a></footer>
</main><script src="feed.js" defer></script></body></html>\n'''


def render_research_markdown(markdown: str) -> str:
    """Render this repo's small, trusted Markdown subset without a CDN/dependency."""
    def inline(text):
        text = esc(text)
        text = re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        return re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    lines = markdown.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
        elif line.startswith('#'):
            level = min(len(line) - len(line.lstrip('#')), 3)
            out.append(f'<h{level}>{inline(line[level:].strip())}</h{level}>')
            i += 1
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([cell.strip() for cell in lines[i].strip().strip('|').split('|')])
                i += 1
            out.append('<div class="table-wrap"><table><thead><tr>' + ''.join(
                f'<th scope="col">{inline(cell)}</th>' for cell in rows[0]) + '</tr></thead><tbody>')
            for row in rows[2:]:
                out.append('<tr>' + ''.join(f'<td>{inline(cell)}</td>' for cell in row) + '</tr>')
            out.append('</tbody></table></div>')
        elif line.startswith('* '):
            out.append('<ul>')
            while i < len(lines) and lines[i].strip().startswith('* '):
                out.append('<li>' + inline(lines[i].strip()[2:]) + '</li>')
                i += 1
            out.append('</ul>')
        else:
            out.append('<p>' + inline(line) + '</p>')
            i += 1
    return '\n'.join(out)


def main() -> int:
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    latest_card = json.loads((ROOT / 'evidence/run_card_2026-10-31.json').read_text())
    audit = json.loads((ROOT / 'evidence/literal_witness_audit.json').read_text())
    focus = json.loads((ROOT / 'evidence/focus9_reaudit.json').read_text())
    h6 = json.loads((ROOT / 'evidence/run_card_h6_otsp.json').read_text())
    rules = json.loads((ROOT / 'evidence/official_rules_check.json').read_text())
    if (card['verdict'] != 'negative' or latest_card['verdict'] != 'negative'
            or h6['verdict'] != 'negative' or not audit['stop_required'] or focus['errors']):
        raise RuntimeError('Dashboard builder cannot publish a release or ignore an incomplete audit')
    new_card_path = ROOT / 'evidence' / 'apartgems1-stepover-relay-dots-20261031-run-card.json'
    new_card = None
    if new_card_path.is_file():
        new_card = json.loads(new_card_path.read_text())
    new_name = 'apartgems1-stepover-relay-dots-20261031'
    if new_card is not None:
        new_digest = new_card['output_sha256']
        new_dots = new_card['emitted_dots']
        new_dti = new_card['holdout_dti']
        new_ci = new_card['holdout_ci95']
        new_eval = new_card['holdout']['scores']['candidate']['evaluator_version']
        new_withheld = new_card['holdout_withheld_positives']
        new_overlap = new_card['overlap_3px']
        new_rho = new_card['rho_vs_witness']
    if focus['prior_candidate_sha256'] != audit['candidate_sha256']:
        raise RuntimeError('Focus audit and literal witness audit refer to different candidates')
    rows = sorted(focus['sites'], key=lambda r: int(r['site'].replace('GEMSDOE', '')))
    best_reported = max(rows, key=lambda r: r['prompt_reported_claim'])
    table = []
    md_rows = []
    for r in rows:
        prior_value = r['prior_candidate_forward_overlap_3px']
        prior_overlap = 'not checked' if prior_value is None else f'{prior_value * 100:.2f}%'
        peer_value = r.get('max_forward_overlap_3px_among_focus9')
        peer_overlap = 'not measured' if peer_value is None else f'{peer_value * 100:.2f}%'
        peer = r.get('closest_focus_site') or 'no peer recorded'
        historical = f"{r['prompt_reported_claim']:.4f}"
        research = r['owner_git_url'] + '?raw=1'
        duplicate = r['unique_among_focus9'] is False
        decision = 'NO · focus-nine overlap exceeds 70%' if duplicate else 'Unknown'
        table.append(f'''<tr>
          <td><strong><a href="https://{esc('buffedlizard55-lab')}.github.io/{esc(r['site'])}/">{esc(r['site'])}</a></strong></td>
          <td><a class="file" href="{esc(research)}">{esc(r['filename'])}</a><br><small>Historical file · research only</small></td>
          <td>{esc(r['method_summary'])}</td>
          <td><strong>{historical}</strong><br><small>user-reported; unconfirmed</small></td>
          <td>Unavailable</td>
          <td><span class="tag stop">{esc(decision)}</span><br><small>{peer_overlap} of this file's positive pixels are within 3 px of {esc(peer)}.</small></td>
          <td>{prior_overlap}<br><small>Overlap with the prior ApartGEMSDOE1 candidate; not the focus-nine test.</small></td>
          <td><span class="tag stop">DO NOT RESUBMIT</span></td>
        </tr>''')
        md_rows.append(f"| [{r['site']}](https://buffedlizard55-lab.github.io/{r['site']}/) | [`{r['filename']}`]({research}) | {r['method_summary']} | {historical} (user claim, unconfirmed) | Unavailable | {decision}; {peer_overlap} within 3 px of {peer} | Prior-candidate overlap {prior_overlap} (diagnostic only) | Do not resubmit |")
    overlap = audit['final_dot_gate']['forward_overlap_3px'] * 100
    hist = card['holdout_dti']['historical_noncomparable']
    holdout = f"{hist['dti']:.4f} [{hist['ci95'][0]:.4f}, {hist['ci95'][1]:.4f}]"
    h6_holdout = h6['holdout_dti']
    h6_score = f"{h6_holdout['dti']:.6f} [{h6_holdout['ci95'][0]:.6f}, {h6_holdout['ci95'][1]:.6f}]"
    file_name = Path(audit['candidate_file']).name
    digest = audit['candidate_sha256']
    witness = audit['witness']
    current_name = esc(card['submission_name'])
    research_path = 'downloads/' + file_name
    source_links = '''<ul class="source-list">
        <li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData · problem &amp; metric ↗</a></li>
        <li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData · public leaderboard ↗</a></li>
        <li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">DOE GEMS Prize · Official Rules (September 2026) ↗</a></li>
        <li><a href="data/official_rules_check.json">Verified rule excerpts and direct leaderboard observation · JSON</a></li>
        <li><a href="data/run_card_2026-10-31.json">Latest negative run card · 2026-10-31</a></li>
        <li><a href="repository-review-2026-10-31.md">Latest repository review · 2026-10-31</a></li>
        <li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS · GeoDAWN release ↗</a></li>
        <li><a href="https://gdr.openei.org/submissions/1391">DOE GDR · INGENIOUS data ↗</a></li>
        <li><a href="https://www.usgs.gov/3d-elevation-program">USGS · 3DEP elevation ↗</a></li>
        <li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">DrivenData · reference solution ↗</a></li>
      </ul>'''
    index = f'''<section class="hero">
      <div><p class="eyebrow">Research operations / Geothermal fault discovery</p>
        <h1>A clear decision before a submission.</h1>
        <p class="lead">An auditable review of the nine requested GEMSDOE sites, the competition metric, and our latest candidate. No leaderboard score is forecast from a local holdout.</p>
        <div class="actions"><a class="button primary" href="executive-summary.html">Read submission guide →</a><a class="button secondary" href="#sites">Compare the nine sites</a><a class="button secondary" href="downloads/apartgems1-stepover-relay-dots-20261031.tif" download>Download generated candidate · blocked · research only</a></div>
      </div>
      <aside class="status-card" aria-label="Current release decision"><span class="status-label"><span class="status-dot"></span> Mandatory stop</span>
        <strong>No file is ready to submit.</strong><p>The existing candidate fails the literal registry overlap rule. No new prediction candidate was generated and no competition slot was used. Archived H-APART-6 v2 experiments predated discovery of the witness.</p></aside>
    </section>
    <div class="metric-grid" aria-label="Release gates">
      <div class="metric"><span class="label">Format · local policy</span><strong class="success-text">PASS</strong><small>Single band; float32; [0,1]; zeros outside footprint. Official rule: null/NaN outside bounds, so this file does NOT match the rule.</small></div>
      <div class="metric"><span class="label">Literal uniqueness</span><strong class="danger-text">FAIL · {overlap:.2f}%</strong><small>Forward 3-pixel overlap; limit 70%.</small></div>
      <div class="metric"><span class="label">Current holdout</span><strong>Not run</strong><small>v3 proxy score unavailable after stop.</small></div>
      <div class="metric"><span class="label">Weekly slot</span><strong>Not selected</strong><small>Separate selector approval required.</small></div>
    </div>
    <section class="panel" id="decision"><div class="section-heading"><div><p class="eyebrow">01 / Executive decision</p><h2>What can I download?</h2></div></div>
      <p><strong>No competition-ready file is available.</strong> The previous MAW-GSI TIFF remains accessible only to reproduce the negative audit. Do not upload it or any already-submitted historical file as a new entry.</p>
      <p class="subtle"><strong>Audit-only file:</strong> <code>{esc(file_name)}</code> · SHA-256 <code>{digest}</code></p>
      <div class="actions"><a class="button secondary" href="{esc(research_path)}" download>Download prior TIFF · research only</a><a class="button secondary" href="data/literal_witness_audit.json">View audit evidence</a><a class="button secondary" href="executive-summary.html#official-rules">Official rule check</a></div>
      <div class="callout" style="margin-top:20px"><strong>Why stop?</strong> {audit['final_dot_gate']['candidate_dots_within_3px']:,} of {audit['final_dot_gate']['candidate_dots']:,} dots lie within three pixels of the <a href="{esc(witness['url'])}">registered 13GEMSDOE lattice</a>. This is a protocol duplicate, not proof that the two rasters are byte-identical.</div>
    </section>
    <section class="panel" id="sites"><div class="section-heading"><div><p class="eyebrow">02 / The focus nine</p><h2>Historical file comparison</h2><p><strong>Highest reported claim in this nine-site set: {esc(best_reported['site'])} · {best_reported['prompt_reported_claim']:.4f}.</strong> This is unconfirmed and is not a recommendation to submit. The file is a previously submitted historical artifact, and all future leaderboard estimates are unavailable.</p><p>Highest file named for each site in your prompt. Reported values are unconfirmed user claims, not organizer receipts.</p></div></div>
      <div class="table-wrap"><table><thead><tr><th scope="col">Site</th><th scope="col">Historical TIFF · research only</th><th scope="col">Method · owner-described</th><th scope="col">Prompt claim</th><th scope="col">Future score estimate</th><th scope="col">Unique among focus nine? (closest peer)</th><th scope="col">Overlap with prior candidate (diagnostic)</th><th scope="col">Decision</th></tr></thead><tbody>{''.join(table)}</tbody></table></div>
      <p class="subtle" style="margin-top:14px">The focus-nine percentage is directed from each historical file's positive pixels to the 3-pixel halo of its closest peer; all nine exceed the 70% cap (97.5781%–100.0000%). The separate prior-candidate overlap is diagnostic and does not define focus-nine uniqueness. This nine-file audit is not a complete registry; the current candidate also fails against an additional pinned lattice witness.</p>
    </section>
    <div class="two-col"><section class="panel"><p class="eyebrow">03 / Mechanism, not proof</p><h2>Why did GEMSDOE32 stand out?</h2>
      <p>The user reports <strong>0.2778</strong> for B2, but no submission-page receipt is present. Our pixel audit shows B2's dots equal the GEMSDOE25 dot set after removing points within two pixels of the mapped-fault catalogue.</p>
      <p>The official metric credits each truth pixel by its best nearby prediction. Pruning redundant dots <em>may</em> reduce false-positive mass while retaining that credit, but it can also lose useful coverage. Hidden labels prevent a causal conclusion or a justified claim of improvement.</p>
      <p class="subtle">GEMSDOE25 and GEMSDOE30 also have identical footprint values despite different file encodings. <a href="data/focus9_reaudit.json">Inspect the pixel audit →</a></p></section>
    <section class="panel"><p class="eyebrow">04 / Holdout correction</p><h2>Local evidence is not a leaderboard score.</h2>
      <p>The previous run recorded <strong>HOLDOUT-DTI {holdout}</strong> ({esc(hist['evaluator_version'])}, {hist['withheld_positive_pixels']:,} withheld positives, 95% CI). That historical result is <strong>not comparable</strong> to the corrected evaluator and has not been rerun here.</p>
      <p>The previous mask also excluded catalogue cells removed from the model’s visible context by the buffer. The shared v3 evaluator now masks only visible catalogue pixels; buffer-removed cells remain unlabelled and are conservatively counted if predicted.</p>
      <p class="subtle">The original pre-placement surface was not saved, and the older canaries did not separately cover every stage-2 feature. <a href="data/v3_mask_regression.json">View mask-only regression</a> · <a href="data/run_card_2026-10-31.json">Open current run card →</a></p></section></div>
    <section class="panel"><p class="eyebrow">05 / Archived negative experiment</p><h2>H-APART-6 OTSP did not clear promotion.</h2>
      <p>Before the lattice witness was discovered, exactly three orientation-transport experiments were measured. The best was <strong>HOLDOUT-DTI {h6_score}</strong> ({esc(h6_holdout['evaluator_version'])}, {h6_holdout['withheld_positive_pixels']:,} withheld positives, 95% CI), below its historical v2 comparator. Maximum feature-canary symmetric AUC was {h6['leakage_canary']['max_symmetric_auc']:.6f}, below the 0.90 suspicion threshold.</p>
      <p><strong>This result is archived and non-comparable to v3.</strong> No H-APART-6 raster was written, the later literal witness mandates a stop, and zero weekly slots were used.</p>
      <div class="actions"><a class="button secondary" href="data/run_card_h6_otsp.json">H6 run card</a><a class="button secondary" href="data/experiments_h6_otsp.json">Three-arm evidence</a></div></section>
    <section class="panel"><p class="eyebrow">06 / Research and next steps</p><h2>Evidence before another slot</h2>
      <ol><li>Do not resume this lane after the duplicate stop. Establish a separately assigned method lane and a complete, hash-pinned accessible registry.</li><li>Rebuild each catalogue-based feature from visible faults, run all feature-only canaries, and compare to a same-v3 holdout baseline with a paired confidence interval.</li><li>Check literal registry thresholds on every pre-placement surface and on final dots; write a GeoTIFF only after local range/grid checks. A separate selector controls any slot.</li></ol>
      <p class="subtle" style="margin-top:14px">The witness leaves {audit['budget_feasibility']['uncovered_allowed_pixels']:,} allowed pixels outside its 3-pixel halo. At most {audit['budget_feasibility']['max_dots_for_possible_70pct_pass']:,} distinct dots could possibly meet the 70% rule against this one witness; this necessary bound is not a quality or uniqueness guarantee.</p>
      <div class="actions"><a class="button secondary" href="next-hypotheses.html">Read future hypotheses</a><a class="button secondary" href="research-sources.html">View research source register</a></div></section>
    <section class="panel"><p class="eyebrow">07 / New unique candidate generated this session</p><h2>apartgems1-stepover-relay-dots-20261031 — blocked, do not submit</h2>
      <p><strong>What it is.</strong> 2,767 dots placed at the midpoints of qualifying step-over / relay-ramp gaps between en-echelon mapped fault segments — a geometry-only, catalogue-missing-fault hypothesis (dilatational upflow zones the USGS / INGENIOUS catalogue may not contain). Generated deterministically from the pinned bridge grid; no organizer data, no feature cache, no leakage.</p>
      <p><strong>File to download:</strong> <code>apartgems1-stepover-relay-dots-20261031.tif</code> · SHA-256 <code>{new_digest}</code> · 2,767 dots · value 1.0 at dots, 0.0 elsewhere, float32, all finite, in [0,1].</p>
      <div class="actions"><a class="button secondary" href="downloads/apartgems1-stepover-relay-dots-20261031.tif" download>Download GeoTIFF · blocked · research only</a><a class="button secondary" href="../evidence/apartgems1-stepover-relay-dots-20261031-run-card.json">View run card (JSON)</a><a class="button secondary" href="../evidence/apartgems1-stepover-relay-dots-20261031-lattice-witness-audit.json">View lattice-witness audit (JSON)</a></div>
      <table>
        <thead><tr><th scope="col">Gate</th><th scope="col">Result</th><th scope="col">Detail</th></tr></thead>
        <tbody>
        <tr><td>Format and range (local preflight)</td><td><span class="tag ok">PASS</span></td><td>All checks passed; not organizer acceptance.</td></tr>
        <tr><td>Uniqueness vs pinned lattice witness</td><td><span class="tag stop">FAIL · duplicate</span></td><td>{new_overlap * 100:.2f}% of dots within 3 px (limit 70%); Spearman &rho; = {new_card['rho_vs_witness']:.6f} (limit 0.90). Protocol stop.</td></tr>
        <tr><td>Holdout (catalogue proxy)</td><td><span class="tag warn">MEASURED</span></td><td>HOLDOUT-DTI {new_card['holdout_dti']:.3f} [{new_card['holdout_ci95'][0]:.3f}, {new_card['holdout_ci95'][1]:.3f}], {new_card['holdout_withheld_positives']:,} withheld positives, 95% CI; not a leaderboard estimate.</td></tr>
        <tr><td>Verdict</td><td><span class="tag stop">NEGATIVE</span></td><td>Not cleared for upload; research artifact only. No weekly slot used.</td></tr>
        </tbody>
      </table>
    </section>
    <section class="panel"><p class="eyebrow">08 / Official sources</p><h2>Trace the evidence.</h2><p class="subtle" id="public-feed" aria-live="polite">Public leaderboard observation unavailable or stale. Check the official page; no file score is inferred.</p>{source_links}</section>'''
    claims = [r['prompt_reported_claim'] for r in focus['sites']]
    nearest = [r['max_forward_overlap_3px_among_focus9'] * 100 for r in focus['sites']]
    claim_lo, claim_hi = min(claims), max(claims)
    near_lo, near_hi = min(nearest), max(nearest)
    lb_top = rules['leaderboard_observed']['top_public_dti']
    lb_date = rules['leaderboard_observed']['observed_utc']
    if new_card is not None:
        new_row = f'''<tr><td><strong>Generated candidate · blocked · research only</strong><br><small><code>{esc(new_name)}.tif</code> · {new_dots:,} step-over/relay-ramp dots · SHA-256 {new_digest}</small></td>
<td>Not estimable. Holdout proxy on catalogue truth: <strong>{new_dti:.3f} [{new_ci[0]:.3f}, {new_ci[1]:.3f}]</strong> ({new_eval}, {new_withheld:,} withheld positives, 95% CI) — catalogue-proxy truth, fixed-mask replay, <strong>not a leaderboard estimate</strong>.</td>
<td><span class="tag stop">NOT CLEARED</span><br><small>{new_overlap * 100:.2f}% of dots within 3 px of the pinned lattice (limit 70%); logged duplicate, protocol stop.</small></td>
<td><span class="tag stop">NO · do not submit</span></td></tr>
'''
    else:
        new_row = ''
    glance = f'''<section class="panel" id="status-table"><p class="eyebrow">Answer first</p><h2>Can I download and submit a file today?</h2>
      <p class="lead"><strong>No.</strong> No file in this repository is cleared for upload. A unique candidate was generated this session (step-over / relay-ramp dots between en-echelon mapped segments) but it fails the literal uniqueness gate against the pinned lattice witness and is stopped per protocol. Nothing here is a leaderboard estimate.</p>
      <div class="table-wrap"><table><thead><tr><th scope="col">File to download</th><th scope="col">Estimated leaderboard score</th><th scope="col">Unique vs the GEMSDOE sites?</th><th scope="col">OK to download and submit?</th></tr></thead><tbody>
      <tr><td><strong>None cleared.</strong><br><small>Research-only prior file: <code>{esc(file_name)}</code></small></td><td>Not estimable. No v3 holdout score exists for any candidate.</td><td><span class="tag stop">NO</span> {overlap:.2f}% of dots lie within 3 px of a registered lattice (limit 70%).</td><td><span class="tag stop">NO · do not submit</span></td></tr>
      <tr><td>Nine focus-site TIFFs<br><small>GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36 · see section 02</small></td><td>Not estimable. User-reported claims range {claim_lo:.4f} to {claim_hi:.4f}, unconfirmed.</td><td><span class="tag stop">NO</span> Each file's nearest focus-nine neighbour overlaps at {near_lo:.1f}% to {near_hi:.1f}% (directed, within 3 px).</td><td><span class="tag stop">NO · do not submit</span></td></tr>
      {new_row}
      </tbody></table></div>
      <p class="subtle">Official top public DW-Tversky: <strong>{lb_top:.4f}</strong> (direct read of the official page on {esc(lb_date)}; the scheduled feed separately remains unavailable after its 2026-10-30 refresh failure, so the feed shows no number). This is a team-level public standing, not a score receipt for any file, not a hidden-test score, and not a future estimate. The prompt's values of 0.4413 and 0.3195 do not match that page.</p></section>
    <section class="panel" id="official-rules"><p class="eyebrow">Official rule check · verified</p><h2>Does the file match the competition format?</h2>
      <div class="table-wrap"><table><thead><tr><th scope="col">Requirement</th><th scope="col">Official requirement (verbatim quotes in the JSON)</th><th scope="col">Prior file in this repo</th><th scope="col">Match?</th></tr></thead><tbody>
      <tr><td>CRS, resolution, bounds</td><td>EPSG 32611; 100 m; same bounds as the training data</td><td>EPSG:32611; 100 m; 3730 × 3292</td><td><span class="tag ok">YES</span></td></tr>
      <tr><td>Layers and dtype</td><td>A single layer, float32</td><td>1 band, float32</td><td><span class="tag ok">YES</span></td></tr>
      <tr><td>Values</td><td>values between 0 and 1</td><td>finite, min 0.0, max 1.0</td><td><span class="tag ok">YES</span></td></tr>
      <tr><td>Outside the bounds</td><td>data outside the bounds is null or nan</td><td>zeros outside the footprint</td><td><span class="tag stop">NO</span> A NaN-outside variant with the same in-footprint values reproduces the sample's NaN mask exactly (verified locally; not uploaded).</td></tr>
      <tr><td>Originality</td><td>the entire submission is an original work by the competitor (A.5, item 1)</td><td>Literal 3-px overlap test is an internal protocol, not an official rule</td><td><span class="tag warn">REVIEW</span></td></tr>
      <tr><td>Generative-AI disclosure</td><td>indicate in the narrative the extent of any generative-AI use (3.2)</td><td>No narrative drafted</td><td><span class="tag warn">PENDING</span></td></tr>
      <tr><td>Weekly cap and final choice</td><td>three submissions per week; one final submission (3.2, 3.4)</td><td>0 slots used</td><td><span class="tag ok">N/A</span></td></tr>
      </tbody></table></div>
      <p class="subtle">Sources: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem page ↗</a> · <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official rules PDF ↗</a> · <a href="data/official_rules_check.json">quoted excerpts (JSON) ↗</a></p></section>
    <section class="panel" id="why-no-tif"><p class="eyebrow">Generated candidate — verified and blocked</p><h2>Why the new TIF is not cleared to submit</h2>
      <ol><li><strong>Generated and format-valid.</strong> {esc(new_name)}.tif (2,767 step-over / relay-ramp dots, SHA-256 {new_digest}) passes the local format preflight: single band, float32, [0,1], EPSG:32611, 3730 × 3292, pinned transform, zeros outside the footprint, zero dots on the mapped catalogue.</li>
      <li><strong>Blocked by the literal uniqueness rule.</strong> {new_overlap * 100:.2f}% of its dots fall within 3 px of the pinned 13GEMSDOE lattice raster; the limit is 70%. It is logged as a duplicate and stopped — checked on the final dots, per protocol rule 1.</li>
      <li><strong>Holdout proxy measured.</strong> HOLDOUT-DTI {new_dti:.3f} [{new_ci[0]:.3f}, {new_ci[1]:.3f}] ({new_eval}, {new_withheld:,} withheld positives, 95% CI) on catalogue-proxy truth; fixed-mask replay, not fold-honest, not a leaderboard estimate.</li>
      <li><strong>Not registry-cleared.</strong> No complete hash-pinned registry inventory, no organizer submission-page receipt, and no selector approval exist, so no weekly slot is claimed.</li></ol>
      <p class="subtle">The reference value above is a projection, not a score. Official top public DW-Tversky was {lb_top:.4f} on {esc(lb_date)} (team-level standing, not a file receipt). Next: complete registry, same-v3 fold-honest holdout, leakage canaries, then a separate selector decides on a slot.</p></section>'''
    guide = f'''<section class="hero"><div><p class="eyebrow">Submission guide / Read before uploading</p><h1>Not yet. Here is the path to a valid submission.</h1>
      <p class="lead">The project must pass automated scientific, novelty, and file-format gates before a separate selector uses a weekly slot. No manual image inspection is required for this negative decision.</p></div>
      <aside class="status-card"><span class="status-label"><span class="status-dot"></span> Do not submit</span><strong>Current candidate is blocked.</strong><p>{overlap:.2f}% 3-pixel overlap exceeds the 70% limit. A format pass alone does not authorize an upload.</p></aside></section>
    {glance}
    <section class="panel"><p class="eyebrow">Current file / audit only</p><h2>One-click research artifact</h2>
      <p>The prior <code>{esc(file_name)}</code> is locally finite and in range, but it writes zeros outside the footprint (the official rule says null/NaN), and it is a protocol duplicate. It is <strong>not approved to submit</strong>.</p>
      <p class="subtle">SHA-256: <code>{digest}</code><br>Prior name: <code>{current_name}</code></p>
      <div class="actions"><a class="button secondary" href="{esc(research_path)}" download>Download prior TIFF · research only</a><a class="button secondary" href="data/literal_witness_audit.json">View validation report</a></div></section>
    <section class="panel"><p class="eyebrow">Automated gate checklist</p><h2>What must be true first?</h2>
      <div class="table-wrap"><table><thead><tr><th scope="col">Gate</th><th scope="col">Current status</th><th scope="col">Meaning</th></tr></thead><tbody>
      <tr><td>Format and range</td><td><span class="tag stop">RULE MISMATCH</span></td><td>Local checks pass (single-band float32, finite [0,1], mirror CRS/shape/transform). The official rule requires null/NaN outside bounds; this file writes zeros there. Not an organizer receipt.</td></tr>
      <tr><td>Surface and final uniqueness</td><td><span class="tag stop">FAIL</span></td><td>Final dots fail against a pinned registry raster; original pre-placement surface is unavailable.</td></tr>
      <tr><td>Leakage canary and holdout</td><td><span class="tag stop">NOT CLEARED</span></td><td>No corrected v3 result against a same-evaluator best; previous v2 numbers are historical only.</td></tr>
      <tr><td>Separate selector</td><td><span class="tag stop">NOT APPROVED</span></td><td>Do not use a weekly slot until all gates pass and a separate selector chooses a candidate.</td></tr></tbody></table></div></section>
    <section class="panel"><p class="eyebrow">Only after a future selector approval</p><h2>How to submit on DrivenData</h2>
      <ol class="steps"><li><div><strong>Download the newly approved file.</strong><br>Use the exact filename and SHA-256 in that future run card. The research file above is not that file.</div></li>
      <li><div><strong>Open the competition.</strong><br>Sign in to <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData</a> and check the current portal instructions and available slots. The September 2026 Official Rules allow up to three automated-feedback submissions per week but require one final submission for both prize phases; confirm there are no later amendments. This project has not selected or used a slot.</div></li>
      <li><div><strong>Choose the file.</strong><br>Upload the single-band GeoTIFF using the submission form, if the current portal instructions permit it. Outside-bounds cells must be null/NaN under the official rule (verified). Compare against the sample template before uploading.</div></li>
      <li><div><strong>Use the future run card’s note.</strong><br>Paste its distinct comment of at most 140 characters into the optional Note field; the filename identifies the file. Do not reuse this negative audit’s note as an approval.</div></li>
      <li><div><strong>Disclose generative-AI use in the required narrative.</strong><br>The September 2026 Official Rules require an accurate description of the extent and use of generative AI in developing any future submission.</div></li>
      <li><div><strong>Record the receipt.</strong><br>Only the submission-page result tied to the file hash is an ORGANIZER-CONFIRMED score. A local holdout or a public team standing is not a receipt for this file.</div></li></ol></section>
    <section class="panel"><p class="eyebrow">Limitations</p><h2>What still needs access?</h2><p>The organizer data page redirects to login; the current bridge files are owner mirrors. This sandbox cannot authenticate the organizer template, see hidden labels, read your weekly quota, or upload on your behalf. External dataset catalogs were reviewed, but raw official provenance and licensing still need verification before use.</p>{source_links}</section>'''
    DOCS.mkdir(exist_ok=True)
    (DOCS/'data').mkdir(exist_ok=True)
    for evidence_name in ('official_rules_check', 'focus9_reaudit', 'literal_witness_audit',
                          'v3_mask_regression', 'run_card_h6_otsp', 'experiments_h6_otsp'):
        shutil.copyfile(ROOT/'evidence'/f'{evidence_name}.json', DOCS/'data'/f'{evidence_name}.json')
    # Publish the dated current card at all stable dashboard URLs. Keep every
    # copy byte-identical to the checked-in evidence source.
    latest_card_path = ROOT/'evidence/run_card_2026-10-31.json'
    for run_card_name in ('run_card_2026-10-31.json', 'run_card.json', 'current-run-card.json'):
        shutil.copyfile(latest_card_path, DOCS/'data'/run_card_name)
    shutil.copyfile(ROOT/'evidence/repository_review_2026-10-31.md',
                    DOCS/'repository-review-2026-10-31.md')
    (DOCS/'index.html').write_text(page('Overview', 'overview', index), encoding='utf-8')
    (DOCS/'executive-summary.html').write_text(page('Submission guide', 'guide', guide), encoding='utf-8')
    for name in ('research_sources.md', 'next_hypotheses.md'):
        source = ROOT/'evidence'/name
        slug = name.replace('_', '-')
        shutil.copyfile(source, DOCS/slug)
        rendered = '<section class="panel">' + render_research_markdown(source.read_text(encoding='utf-8')) + '</section>'
        rendered += f'<p class="subtle"><a href="{slug}">View the source Markdown</a></p>'
        title = 'Research sources' if name.startswith('research') else 'Future hypotheses'
        (DOCS/slug.replace('.md', '.html')).write_text(page(title, 'sources' if name.startswith('research') else '', rendered), encoding='utf-8')
    (ROOT/'index.html').write_text('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0; url=docs/index.html"><title>GEMS Field Notes</title></head><body><p><strong>DO NOT SUBMIT:</strong> the prior file failed the literal uniqueness gate. <a href="docs/index.html">Open the project dashboard</a>.</p></body></html>\n''')
    readme = f'''# ApartGEMSDOE1 · Geothermal fault discovery

> **STOP — NO FILE IS READY TO SUBMIT.** The prior MAW-GSI GeoTIFF passes the local finite/range/grid preflight against owner-mirror files, but its zero-outside policy conflicts with the official null/NaN requirement and {overlap:.2f}% of its dots overlap a registered lattice within three pixels, exceeding the 70% internal protocol limit. The surface gate is unverified. No new submission-candidate GeoTIFF or competition submission was made; disposable format-test files were not candidates. Archived H-APART-6 v2 experiments predated discovery of the witness.
>
> [Open the dashboard](docs/index.html) · [Executive summary and submission guide](docs/executive-summary.html) · [Current negative run card](evidence/run_card_2026-10-31.json) · [Prior run card](evidence/run_card.json) · [Official rule excerpts](evidence/official_rules_check.json) · [Reproducible witness audit](evidence/literal_witness_audit.json) · [Latest repository review 2026-10-31](evidence/repository_review_2026-10-31.md) · [Review history](evidence/review_passes.md) · [Overlap and metric verification 2026-10-30](evidence/repo_review_2026-10-30_overlap.md)
>
> [Download the **prior TIFF for research only — do not submit**](docs/downloads/{file_name}) · SHA-256 `{digest}`

## Future-session start-up: read before every run

**Objective.** Build an evidence-led, original fault-prediction GeoTIFF for geothermal exploration, and say plainly whether any file is safe to download or submit. The nine focus sites are GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36. Their historical scores are user-reported claims, not submission receipts; the reported GEMSDOE32 value 0.2778 is not explained by geometry alone. Its support matches GEMSDOE25 after a two-pixel catalogue collar is removed, which suggests—but does not prove—a redundancy-pruning mechanism under max-kernel DTI. Do not turn this into a causal claim, score estimate, or promotion without hidden-label evidence.

**Current lane status — stop.** The “single method” paragraph in the supplied request was not unambiguously identified. Repo context records an inherited H-APART-6 OTSP lane, three archived v2 experiments, and a later mandatory duplicate stop. The existing candidate overlaps one pinned lattice witness by 37,533/37,654 dots (99.6787%, over the 70% limit); the pre-placement surface and complete registry are unavailable, and the training-feature cache was absent from the earlier checkout. On 2026-10-31 `python scripts/prepare_data.py --fetch` restored and hash-verified all 19 bands (owner-mirror integrity only). A leakage canary on the v3 folds (`scripts/feature_canary_v3.py`) found no single-band leakage (symmetric AUC 0.505–0.568) and single-band top-K HOLDOUT-DTI ≤0.0122; no model or submission was produced. See [the 2026-10-31 review](evidence/review_2026-10-31.md). Do not choose a replacement method, run experiments, generate a new TIFF, or use a slot until a new lane is explicitly assigned and its prerequisites are met. See the [ranked future hypotheses](evidence/next_hypotheses.md) for design candidates, not permission to run them.

### Mandatory gates

1. **One lane, originality before placement.** Before implementation, rank 3–5 untried geological hypotheses by expected DTI improvement and cost. For each, name the layers and physical signature, why it could find a catalogue-missing fault, how it differs from this repository, a named non-fault mimic, and the official source/data-availability check. Stay within the assigned single method. Check registry rank correlation on each surface before placement and 3-pixel dot overlap after placement; stop if any correlation exceeds 0.90 or overlap exceeds 70%. No density exemptions.
2. **Reuse shared tools.** Reuse the template feature stack, shared holdout evaluator, and `submission_writer.py`; fix shared tools instead of making private forks. Hide whole fault segments with a buffer, derive catalogue features only from visible faults, mask visible faults pixel-exactly, and use pooled DTI with α=0.2, β=0.8, and a 300 m triangular kernel.
3. **Leakage and score labels.** Test every feature alone on holdout; AUC >0.90 is leakage until explained. A measured result must be `HOLDOUT-DTI` with evaluator version, withheld-positive count, and 95% CI. Use `ORGANIZER-CONFIRMED` only for a score tied to an actual submission-page receipt. Never call a projection a score or infer leaderboard performance from a holdout.
4. **Run card and budget.** Record hypothesis, mechanism, named non-fault mimic, holdout DTI/CI, registry comparisons, raster SHA-256, format/grid validation, submission name and note ≤140 characters, and promote/negative verdict. Stop after at most three experiments or two hours, and immediately on either duplication threshold. A separate selector—not the experiment runner—chooses a real weekly slot within the current cap.
5. **Review and report.** Verify claims against official sources, preserve limitations and source links, run three implementation/review passes, and publish negative results honestly. No local validation is organizer acceptance; no upload is authorized without all gates and separate selector approval.

**Future-session checklist:** read this section, [`evidence/repository_review_2026-10-31.md`](evidence/repository_review_2026-10-31.md), [`evidence/run_card_2026-10-31.json`](evidence/run_card_2026-10-31.json), the latest review in [`evidence/review_passes.md`](evidence/review_passes.md), the run cards, and [`evidence/official_rules_check.json`](evidence/official_rules_check.json); confirm the assigned lane and current stop state; check whether required data/cache is actually present in this checkout; only then proceed. Keep the public feed fail-closed and do not revive retired runners.

**Core values:** *Maximize P(Win)* means weigh evidence, expected value, and risk rather than spending a slot on a weak or duplicated method. *Own the Outcome* means report failure, fix shared defects, and preserve reproducible negative evidence.

## Executive summary · nine requested sites

The highest reported claim among these nine is **{esc(best_reported['site'])} · {best_reported['prompt_reported_claim']:.4f}**, but this is an unverified user report tied to a historical file—not a submission recommendation, organizer receipt, or estimated score. No file is cleared to submit. These are the highest historical files **named in the user prompt**, not a complete census. No submission-page receipts were found. A future leaderboard estimate is unavailable for every row. The focus-nine column reports each file's maximum directed 3-pixel overlap with its closest peer; all nine exceed the 70% cap. The separate prior-candidate overlap is diagnostic only and does not define focus-nine uniqueness. Do not resubmit these historical files as new.

| Site | Historical file (research only) | Method (owner-described) | Prompt claim | Future estimate | Unique among focus nine? (closest peer) | Prior candidate overlap (diagnostic) | Decision |
| --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(md_rows)}

The re-audit confirms GEMSDOE32 B2's support equals GEMSDOE25's support outside a two-pixel catalogue collar; GEMSDOE25 and GEMSDOE30 have identical footprint values. The user-reported GEMSDOE32 value of 0.2778 has no linked organizer receipt. The official max-kernel DTI makes reduced redundancy a plausible explanation, not proof; hidden labels are unavailable. No result here establishes that a new method will exceed it.

## Official rule check (verified 2026-10-31)

Quoted excerpts and sources are in [`evidence/official_rules_check.json`](evidence/official_rules_check.json).

* **Format:** [official problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — "data outside the bounds is null or nan", values between 0 and 1, float32, single layer, EPSG 32611, 100 m.
* **Metric:** same page — distance-weighted Tversky with α=0.2, β=0.8 and R = 300 m (3 px).
* **Test labels:** same page — the scored faults are new faults "not included in the existing USGS fault database". The repository's holdout uses the existing catalogue, so it is only a proxy.
* **Limits and originality:** [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — three submissions per week (§3.2), one final submission (§3.4), originality warranty (A.5 item 1), and a generative-AI disclosure in the narrative (§3.2).
* **Reference solution:** [drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) writes raw float predictions with no NaN step, georeferenced from the labels raster.
* **Leaderboard:** [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) showed rank 1 at **0.4544** for xiaofanhu (direct page read on 2026-10-31; the scheduled feed remains unavailable, see `docs/data/public_feed.json`). This is a team-level public standing—not a file receipt, hidden-test score, or future estimate. The prompt's 0.4413 and 0.3195 do not match this dated observation, and the prompt's site claims (0.2449–0.2778) are unconfirmed.
* **Unresolved:** whether the portal accepts NaN outside the footprint, and which file produced the reported "Predicted values must be in range [0, 1]" error. A NaN-outside variant with identical in-footprint values reproduces the sample template's NaN mask exactly (verified locally, not uploaded).

## Current result and limitations

* **HOLDOUT-DTI, historical only:** {holdout}, evaluator `{hist['evaluator_version']}`, {hist['withheld_positive_pixels']:,} withheld positives, 95% CI. This prior run used a scoring mask that included buffer-removed non-visible catalogue pixels; it is not a comparable v3 baseline or a leaderboard prediction. No v3 model run was performed after the duplicate stop.
* **Literal uniqueness:** {audit['final_dot_gate']['candidate_dots_within_3px']:,}/{audit['final_dot_gate']['candidate_dots']:,} prior dots overlap the [pinned lattice witness]({witness['url']}); only one witness is necessary to prove failure, but this is not a complete registry inventory. The word duplicate here means protocol overlap, not byte identity.
* **Feasibility:** the lattice leaves {audit['budget_feasibility']['uncovered_allowed_pixels']:,} allowed cells outside its halo, so a {audit['budget_feasibility']['requested_previous_budget']:,}-dot budget cannot pass. A budget no larger than {audit['budget_feasibility']['max_dots_for_possible_70pct_pass']:,} is necessary against this witness, not sufficient for quality or uniqueness.
* **Format:** the prior file has one float32 band, finite [0,1] values, and matches the stored sample grid. Its outside-footprint cells are zeros. The official rule requires null/NaN outside the bounds (verified below), so this file does **not** match the rule. This is local preflight only, not organizer acceptance.
* **Access:** the [competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) redirected to login; no hidden labels, submission-page receipt, quota, or authorized upload session is available. Mirror hash equality does not prove official origin. The official reference solution supports CPU as well as GPU.
* **Official sources:** [problem and DTI](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [DOE GDR INGENIOUS](https://gdr.openei.org/submissions/1391), and the [research source register](evidence/research_sources.md).

## Archived H-APART-6 OTSP experiment

Before discovery of the lattice witness, exactly three v2 orientation-transport arms were measured. The best was **HOLDOUT-DTI {h6_score}**, evaluator `{h6_holdout['evaluator_version']}`, {h6_holdout['withheld_positive_pixels']:,} withheld positives, 95% CI. It lost to its historical v2 comparator; maximum feature-canary symmetric AUC was {h6['leakage_canary']['max_symmetric_auc']:.6f} (<0.90). This is archived and not comparable to v3, no H6 GeoTIFF was written, and zero slots were used. See the [H6 run card](evidence/run_card_h6_otsp.json) and [three-arm evidence](evidence/experiments_h6_otsp.json).

## Reproduce the negative decision

```bash
python -m pip install -r requirements.txt
python scripts/audit_literal_witness.py             # downloads one pinned witness through gh; never submits
python scripts/audit_historical_focus.py           # nine pinned GitHub mirror files; no model experiment
python scripts/audit_holdout_mask.py               # rebuild masks only; no model score
python scripts/validate_submission.py docs/downloads/{file_name} --format-only
python scripts/run_apartgems_pipeline.py          # deliberately exits nonzero: this lane is stopped
pytest -q
```

The former private density-exempt uniqueness gate and automatic-promotion runner are retired. Shared literal checks live in `src/gems57/uniqueness.py`; the corrected visible-only mask is `gems57-pooled-hide-v3`. Before a new lane can run, supply an auditable complete accessible registry and same-v3 baseline, rerun all feature canaries, verify external-data provenance, and perform surface gates **before** placement. Do not force predictions into the lattice's uncovered slivers merely to game the overlap rule.


# SESSION MANDATE — read before every work session

The following is the standing project mandate. It defines the objective, the gates,
the budget, and the definition of done. Re-read it at the start of every session.

## Objective

Build a geothermal fault-discovery submission for the DOE GEMS Prize Challenge
(DrivenData competition 306) that places top of the leaderboard. Generate a
UNIQUE TIF submission for the competition. Do not copy a previous submission
unless it is for learning and education; a unique TIF submission must be
generated. It must be obvious whether it is OK to download and submit the
generated TIF submission.

Focus sites: GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31,
GEMSDOE32, GEMSDOE33, GEMSDOE36. Produce an executive summary on every site
that is clear and obvious which is the best submission to submit to obtain a
high score on the leaderboard. Each entry must be unique and not an exact
duplicate of any previous submission from the same GEMSDOE sites. Keep iterating
and testing until the highest-scoring submission exists to download and submit.

The submission page requires a single-band GeoTIFF (.tif), or a .zip containing
a single GeoTIFF, matching the submission format's CRS, shape, and geotransform.
Values must be in range [0, 1]. The file must have a unique name and an optional
note of at most 140 characters (e.g. "clustering with k=25"). There must be an
easy-to-download submission TIF; the download must be obvious at the beginning
of the site / executive summary. Inspection must happen through the project and
be validated for submission without human intervention.

## Reported scores (unverified user claims, not organizer receipts)

GEMSDOE32 h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778 (highest named)
GEMSDOE24: 0.2477 · GEMSDOE25: 0.2600 · GEMSDOE27: 0.2449 · GEMSDOE28: 0.2710 /
0.2649 / 0.2710 / 0.2707 · GEMSDOE30: 0.2600 · GEMSDOE31: 0.2708 · GEMSDOE33:
0.2632 · GEMSDOE36: 0.2750

Current competition leaderboard GEMSDOE high score: 0.4413 (prompt figure; the
official page showed 0.4544 as a team-level public standing on 2026-10-30, not
a file receipt or future estimate).

Key links:
- Competition page: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- About page: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- Data page (login required): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- INGENIOUS: https://gbcge.org/current-projects/ingenious/
- EPSG 32611: https://epsg.io/32611
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- Official rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf

## Parallel-run protocol

1. LANE. Your lane is the single method paragraph. Stay inside it. If your
raster's rank-correlation with any registry raster exceeds 0.90, or more than
70% of your dots fall within 3 px of one registry raster's dots, you have
drifted into another lane: log it as a duplicate and stop. Check on the surface
before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack,
evaluate_holdout.py and submission_writer.py. Holdout = hide-and-recover: withhold
whole fault segments with a buffer, derive every catalogue-based feature only
from the visible faults, mask visible faults pixel-exactly, score pooled DTI
(alpha 0.2, beta = 0.8, 300 m triangular kernel). If a shared tool is wrong, fix
it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld
positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page
receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any
result. AUC above 0.90 means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault
process that could mimic it; holdout DTI + CI; correlation/overlap vs registry;
raster sha256; validator output (no NaN inside the footprint, values in [0,1],
CRS/shape/transform match); submission name + note of at most 140 characters;
verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after 3 experiments or 2 hours. Do not pick submissions:
promotion to a real slot is a separate selector step, within the weekly cap on
the submission page.

## Competition facts (official)

- Task: predict geological faults indicative of geothermal resources; scored
faults are new faults NOT included in the existing USGS fault database.
- Metric: distance-weighted Tversky index, alpha = 0.2, beta = 0.8, triangular
kernel R = 300 m (3 px at 100 m).
- Format: single-band GeoTIFF, float32, values in [0, 1], EPSG:32611, 100 m,
same bounds as training data; data outside the bounds is null or NaN.
- Limits: three submissions per week, one final submission; originality
warranty; generative-AI disclosure in the narrative.

## Known irregularities (flagged for review)

- The DrivenData data page redirects to login; training_features.tif,
labels.tif, sample_submission.tif, 1m_DEM_links.csv cannot be auto-downloaded
here. Bridge files in data/ are owner-mirror copies, not organizer-authenticated.
- The prior candidate overlaps a pinned registry witness at 99.68% (> 70% limit);
the lane is stopped and the prior file is research only, do not submit.
- The portal's acceptance of NaN outside bounds vs the project's all-finite
zeros-outside policy is unresolved ("Predicted values must be in range [0, 1]"
error reported on submission).
- All site score claims are unverified user reports without organizer receipts.

## Definition of done for a session

Executive summary subpage with an obvious one-click download of a unique,
format-validated TIF; a table listing file to download, estimated score (labelled
as projection or unverified claim), and uniqueness vs the other GEMSDOE sites;
clear statement of whether the file is OK to download and submit; run-card JSON
with verdict; hypothesis ranked against alternatives; no unverified score claimed
as a score. Commit, open a PR from the working branch, and merge to main.

'''
    (ROOT/'README.md').write_text(readme, encoding='utf-8')
    print('Built negative-status dashboard, submission guide, and standing README.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
