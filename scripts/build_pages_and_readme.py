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
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.update_public_feed import is_fresh_observation

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
<footer>Research decisions are automated; a local preflight is not an organizer receipt. <a href="data/run_card_20261030.json">Current review card</a> · <a href="data/run_card.json">Prior lane card</a> · <a href="research-sources.html">Source register</a></footer>
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
    review_card = json.loads((ROOT / 'evidence/run_card_20261030.json').read_text())
    audit = json.loads((ROOT / 'evidence/literal_witness_audit.json').read_text())
    focus = json.loads((ROOT / 'evidence/focus9_reaudit.json').read_text())
    focus_witness = json.loads((ROOT / 'evidence/focus_overlap_review_2026-10-30.json').read_text())
    h6 = json.loads((ROOT / 'evidence/run_card_h6_otsp.json').read_text())
    leaderboard = json.loads((ROOT / 'evidence/leaderboard_observation_20261030.json').read_text())
    rules = json.loads((ROOT / 'evidence/official_rules_check.json').read_text())
    feed = json.loads((DOCS / 'data/public_feed.json').read_text())
    if (card['verdict'] != 'negative' or review_card['verdict'] != 'negative'
            or h6['verdict'] != 'negative' or not audit['stop_required'] or focus['errors']):
        raise RuntimeError('Dashboard builder cannot publish a release or ignore an incomplete audit')
    if review_card['raster_sha256'] != audit['candidate_sha256'] or review_card['holdout_dti']['label'] != 'HOLDOUT-DTI':
        raise RuntimeError('Current review card does not match the negative audit evidence')
    if leaderboard.get('evidence_class') != 'OFFICIAL PUBLIC LEADERBOARD OBSERVATION; NOT A SUBMISSION RECEIPT':
        raise RuntimeError('Dashboard builder refuses unclassified leaderboard data')
    if leaderboard.get('source') != 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/':
        raise RuntimeError('Dashboard builder refuses a non-official leaderboard source')
    rank1 = next((r for r in leaderboard.get('observations', []) if r.get('rank') == 1), None)
    reference = next((r for r in leaderboard.get('observations', []) if r.get('public_dw_tversky') == 0.3195), None)
    if not rank1 or rank1.get('public_dw_tversky') is None or not reference or reference.get('rank') != 48:
        raise RuntimeError('Leaderboard observation is incomplete or does not contain the documented comparison')
    if rules.get('leaderboard_observed', {}).get('top_public_dti') != rank1['public_dw_tversky']:
        raise RuntimeError('Dated leaderboard observation disagrees with the official-rules evidence record')
    required_rule_ids = {'R1-format', 'R2-crs-resolution', 'R3-metric', 'R7-originality-warranty', 'R8-genai-disclosure'}
    recorded_rule_ids = {item.get('id') for item in rules.get('claims', [])}
    if not required_rule_ids.issubset(recorded_rule_ids):
        raise RuntimeError('Official rules evidence is incomplete')
    if focus['prior_candidate_sha256'] != audit['candidate_sha256']:
        raise RuntimeError('Focus audit and literal witness audit refer to different candidates')
    prior_basename = Path(audit['candidate_file']).name
    focus_witness_scores = [item['within_3px_of_witness'] for name, item in focus_witness['rasters'].items()
                            if name != prior_basename]
    if len(focus_witness_scores) != 9 or min(focus_witness_scores) <= .70:
        raise RuntimeError('Pinned-witness audit does not prove the stated focus-nine overlap stop')
    if (focus_witness.get('witness', {}).get('sha256') != audit['witness']['sha256']
            or len(focus_witness.get('input_sources', [])) != 10):
        raise RuntimeError('Focus overlap audit lacks the pinned witness or all input provenance records')
    focus_witness_range = (min(focus_witness_scores) * 100, max(focus_witness_scores) * 100)
    rows = sorted(focus['sites'], key=lambda r: int(r['site'].replace('GEMSDOE', '')))
    best_reported = max(rows, key=lambda r: r['prompt_reported_claim'])
    peer_values = [r['max_forward_overlap_3px_among_focus9'] * 100 for r in rows]
    peer_overlap_range = (min(peer_values), max(peer_values))
    top_public_score = rank1['public_dw_tversky']
    reference_rank = reference['rank']
    feed_status = feed.get('status', 'unavailable')
    feed_is_current = is_fresh_observation(feed)
    feed_summary = (f"Scheduled feed currently reports {float(feed['top_public_dti']):.4f} "
                    f"(observed {feed.get('observed_utc', 'date unavailable')})." if feed_is_current
                    else f"Scheduled feed is {feed_status}; {feed.get('reason') or feed.get('caveat', 'no live value is recorded')}.")
    table = []
    md_rows = []
    for r in rows:
        peer_value = r.get('max_forward_overlap_3px_among_focus9')
        peer_overlap = 'not measured' if peer_value is None else f'{peer_value * 100:.2f}%'
        peer = r.get('closest_focus_site') or 'no peer recorded'
        prior_value = r.get('prior_candidate_forward_overlap_3px')
        prior_overlap = 'not checked' if prior_value is None else f'{prior_value * 100:.2f}%'
        historical = f"{r['prompt_reported_claim']:.4f}"
        research = r['owner_git_url'] + '?raw=1'
        duplicate = r.get('unique_among_focus9') is False and peer_value is not None and peer
        decision = 'DO NOT SUBMIT — historical; not unique under the stated gate' if duplicate else 'DO NOT SUBMIT — uniqueness not certified'
        table.append(f'''<tr>
          <td><strong><a href="https://{esc('buffedlizard55-lab')}.github.io/{esc(r['site'])}/">{esc(r['site'])}</a></strong></td>
          <td><a class="file" href="{esc(research)}">{esc(r['filename'])}</a><br><small>Historical file · research only</small></td>
          <td>{esc(r['method_summary'])}</td>
          <td><strong>{historical}</strong><br><small>user-reported; unconfirmed</small></td>
          <td>Not defensibly estimable<br><small>No comparable holdout-to-leaderboard calibration</small></td>
          <td><span class="tag stop">NO · focus-nine overlap exceeds 70%</span><br><small>{peer_overlap} within 3 px of {esc(peer)}. This is a directed spatial-near-duplicate flag, not byte identity.</small></td>
          <td>{prior_overlap}<br><small>Overlap with the prior ApartGEMSDOE1 candidate; not the focus-nine test.</small></td>
          <td><span class="tag stop">DO NOT SUBMIT</span></td>
        </tr>''')
        md_rows.append(f"| [{r['site']}](https://buffedlizard55-lab.github.io/{r['site']}/) | [`{r['filename']}`]({research}) | {r['method_summary']} | {historical} (user claim, unconfirmed) | Not defensibly estimable | NO · focus-nine overlap exceeds 70%; {peer_overlap} within 3 px of {peer} | Prior candidate overlap {prior_overlap} (diagnostic only) | DO NOT SUBMIT |")
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
    feature_cache_dir = ROOT / '.cache/features'
    cached_feature_bands = len(list(feature_cache_dir.glob('band-*.npy'))) if feature_cache_dir.is_dir() else 0
    has_training_stack = (ROOT / 'data/official/training_features.tif').is_file()
    feature_cache_status = (f"{cached_feature_bands}/19 cached feature bands; "
                            f"{'training_features.tif present' if has_training_stack else 'training_features.tif absent'}")
    source_links = '''<ul class="source-list">
        <li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData · problem &amp; metric ↗</a></li>
        <li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData · public leaderboard ↗</a></li>
        <li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">DOE · official prize rules ↗</a></li>
        <li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS · GeoDAWN release ↗</a></li>
        <li><a href="https://gdr.openei.org/submissions/1391">DOE GDR · INGENIOUS data ↗</a></li>
        <li><a href="https://www.usgs.gov/3d-elevation-program">USGS · 3DEP elevation ↗</a></li>
        <li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">DrivenData · reference solution ↗</a></li>
        <li><a href="data/official_rules_check.json">Quoted official rules and dated leaderboard evidence ↗</a></li>
      </ul>'''
    official_rule_panel = '''<section class="panel" id="official-rules"><p class="eyebrow">Official rules · verified from source text</p><h2>Does the archived TIFF meet the submission specification?</h2>
      <div class="table-wrap"><table><thead><tr><th scope="col">Requirement</th><th scope="col">Official requirement</th><th scope="col">Archived audit TIFF</th><th scope="col">Status</th></tr></thead><tbody>
      <tr><td>CRS and resolution</td><td>EPSG 32611; 100 m</td><td>Matches the stored owner-mirror grid (3730 × 3292). Official data-page access is not available here.</td><td><span class="tag warn">LOCAL ONLY</span></td></tr>
      <tr><td>Bands and values</td><td>Single-band float32; values in [0,1]</td><td>One float32 band; finite range [0,1]</td><td><span class="tag ok">LOCAL PASS</span></td></tr>
      <tr><td>Outside the bounds</td><td>Null or NaN</td><td>Zeros outside the stored sample footprint</td><td><span class="tag stop">MISMATCH</span></td></tr>
      <tr><td>Originality</td><td>Entire submission must be the competitor's original work (official rules A.5)</td><td>Historical audit file; do not copy or resubmit</td><td><span class="tag stop">NOT APPROVED</span></td></tr>
      <tr><td>Generative-AI disclosure</td><td>Describe use in the submission narrative (official rules §3.2)</td><td>No submission narrative prepared</td><td><span class="tag warn">PENDING</span></td></tr>
      <tr><td>Weekly cap / final choice</td><td>Up to three submissions per week; one final submission</td><td>Zero slots used; no selector approval</td><td><span class="tag ok">NO SLOT USED</span></td></tr>
      </tbody></table></div>
      <p class="subtle">The official page says outside-bounds data must be null/NaN. The checked sample raster also stores NaN outside its footprint; an automated local variant matches that mask, but neither is a portal acceptance receipt. <a href="data/official_rules_check.json">Review quoted rules and evidence ↗</a></p></section>'''
    index = f'''<section class="hero">
      <div><p class="eyebrow">Research operations / Geothermal fault discovery</p>
        <h1>A clear decision before a submission.</h1>
        <p class="lead">An auditable review of the nine requested GEMSDOE sites, the competition metric, and our latest candidate. No leaderboard score is forecast from a local holdout.</p>
        <div class="actions"><a class="button primary" href="executive-summary.html">Read submission guide →</a><a class="button secondary" href="#sites">Compare the nine sites</a></div>
      </div>
      <aside class="status-card" aria-label="Current release decision"><span class="status-label"><span class="status-dot"></span> Mandatory stop</span>
        <strong>No file is ready to submit.</strong><p>The existing candidate fails the literal registry overlap rule. No new GeoTIFF was generated and no competition slot was used. Archived H-APART-6 v2 experiments predated discovery of the witness.</p></aside>
    </section>
    <div class="metric-grid" aria-label="Release gates">
      <div class="metric"><span class="label">Format · official rule check</span><strong class="danger-text">MISMATCH</strong><small>Local float32/range/grid checks pass; archived TIFF writes zeros outside the footprint, while the official page requires null/NaN.</small></div>
      <div class="metric"><span class="label">Literal uniqueness</span><strong class="danger-text">FAIL · {overlap:.2f}%</strong><small>Forward 3-pixel overlap; limit 70%.</small></div>
      <div class="metric"><span class="label">Current holdout</span><strong>Not run</strong><small>v3 proxy score unavailable after stop.</small></div>
      <div class="metric"><span class="label">Weekly slot</span><strong>Not selected</strong><small>Separate selector approval required.</small></div>
    </div>
    <p class="callout" style="margin-bottom:20px"><strong>Leaderboard correction ({leaderboard['observed_utc']} UTC):</strong> the official public table showed <strong>{top_public_score:.4f} at rank 1</strong>; the cited <strong>0.3195 appeared at rank {reference_rank}</strong>, not as the leader. The user-cited 0.4413 was not displayed in the fetched top 50. These are team standings, not a score for a TIFF in this repository. {esc(feed_summary)} <a href="data/leaderboard_observation_20261030.json">View the dated observation.</a></p>
    <section class="panel" id="decision"><div class="section-heading"><div><p class="eyebrow">01 / Executive decision</p><h2>What can I download?</h2></div></div>
      <p><strong>No competition-ready file is available.</strong> The previous MAW-GSI TIFF remains accessible only to reproduce the negative audit. Do not upload it or any already-submitted historical file as a new entry.</p>
      <p class="subtle"><strong>Audit-only file:</strong> <code>{esc(file_name)}</code> · SHA-256 <code>{digest}</code></p>
      <div class="actions"><a class="button secondary" href="{esc(research_path)}" download>Download prior TIFF · research only</a><a class="button secondary" href="data/literal_witness_audit.json">View audit evidence</a><a class="button secondary" href="data/official_rules_check.json">View official-rule check</a><a class="button secondary" href="data/run_card_20261030.json">View current review card</a></div>
      <div class="callout" style="margin-top:20px"><strong>Why stop?</strong> {audit['final_dot_gate']['candidate_dots_within_3px']:,} of {audit['final_dot_gate']['candidate_dots']:,} dots lie within three pixels of the <a href="{esc(witness['url'])}">registered 13GEMSDOE lattice</a>. This is a protocol duplicate, not proof that the two rasters are byte-identical.</div>
    </section>
    <section class="panel" id="sites"><div class="section-heading"><div><p class="eyebrow">02 / The focus nine</p><h2>Historical file comparison</h2><p>Highest historical file named for each site in your prompt. GEMSDOE32 has the highest user-reported claim ({best_reported['prompt_reported_claim']:.4f}), but it is unconfirmed. All nine fail the focus-nine 70% directed-overlap uniqueness gate. New submission estimates are not defensibly available.</p></div></div>
      <div class="table-wrap"><table><thead><tr><th scope="col">Site</th><th scope="col">Highest historical TIFF · research only</th><th scope="col">Method · owner-described</th><th scope="col">Prompt-reported score</th><th scope="col">New-file score estimate</th><th scope="col">Unique among focus nine? (closest peer)</th><th scope="col">Prior candidate overlap (diagnostic)</th><th scope="col">Recommendation</th></tr></thead><tbody>{''.join(table)}</tbody></table></div>
      <p class="subtle" style="margin-top:14px">The focus-nine percentage is directed from each historical file's positive cells to its closest peer's 3-pixel halo; all nine exceed the 70% cap ({peer_overlap_range[0]:.4f}%–{peer_overlap_range[1]:.4f}%). The separate prior-candidate overlap is diagnostic only and does not define focus-nine uniqueness. These are spatial near-duplicate flags, not claims of identical file bytes; the nine-file audit cannot certify uniqueness against a complete registry.</p>
    </section>
    <div class="two-col"><section class="panel"><p class="eyebrow">03 / Mechanism, not proof</p><h2>Why did GEMSDOE32 stand out?</h2>
      <p>GEMSDOE32 has the highest of the nine user-reported claims at <strong>0.2778</strong>, versus GEMSDOE25's reported <strong>0.2600</strong> (claimed difference +0.0178); neither has a submission-page receipt, so neither is ORGANIZER-CONFIRMED. The pixel audit shows B2's support equals GEMSDOE25's support after removing pixels within two pixels of the mapped-fault catalogue; GEMSDOE25 and GEMSDOE30 have identical support.</p>
      <p>The official DTI weights false negatives by 0.8 and false positives by 0.2, with 300 m triangular support. True-positive credit is a per-truth-pixel maximum, so extra nearby dots can have diminishing benefit while off-fault mass adds false-positive cost. Collar pruning is therefore a plausible mechanism only if it removes low-value mass without losing needed coverage; hidden labels and absent receipts prevent causal attribution or a claim that the method will improve future scores.</p>
      <p class="subtle">GEMSDOE25 and GEMSDOE30 also have identical footprint values despite different file encodings. <a href="data/focus9_reaudit.json">Inspect the pixel audit →</a></p></section>
    <section class="panel"><p class="eyebrow">04 / Holdout correction</p><h2>Local evidence is not a leaderboard score.</h2>
      <p>The previous run recorded <strong>HOLDOUT-DTI {holdout}</strong> ({esc(hist['evaluator_version'])}, {hist['withheld_positive_pixels']:,} withheld positives, 95% CI). That historical result is <strong>not comparable</strong> to the corrected evaluator and has not been rerun here.</p>
      <p>The previous mask also excluded catalogue cells removed from the model’s visible context by the buffer. The shared v3 evaluator now masks only visible catalogue pixels; buffer-removed cells remain unlabelled and are conservatively counted if predicted.</p>
      <p class="subtle">The original pre-placement surface was not saved, and the older canaries did not separately cover every stage-2 feature. <a href="data/v3_mask_regression.json">View mask-only regression</a> · <a href="data/run_card_20261030.json">Open current review card →</a></p></section></div>
    <section class="panel"><p class="eyebrow">05 / Archived negative experiment</p><h2>H-APART-6 OTSP did not clear promotion.</h2>
      <p>Before the lattice witness was discovered, exactly three orientation-transport experiments were measured. The best was <strong>HOLDOUT-DTI {h6_score}</strong> ({esc(h6_holdout['evaluator_version'])}, {h6_holdout['withheld_positive_pixels']:,} withheld positives, 95% CI), below its historical v2 comparator. Maximum feature-canary symmetric AUC was {h6['leakage_canary']['max_symmetric_auc']:.6f}, below the 0.90 suspicion threshold.</p>
      <p><strong>This result is archived and non-comparable to v3.</strong> No H-APART-6 raster was written, the later literal witness mandates a stop, and zero weekly slots were used.</p>
      <div class="actions"><a class="button secondary" href="data/run_card_h6_otsp.json">H6 run card</a><a class="button secondary" href="data/experiments_h6_otsp.json">Three-arm evidence</a></div></section>
    <section class="panel"><p class="eyebrow">06 / Research and next steps</p><h2>Evidence before another slot</h2>
      <ol><li>Do not resume this lane after the duplicate stop. Establish a separately assigned method lane and a complete, hash-pinned accessible registry.</li><li>Restore the feature cache, rebuild catalogue-based features from visible faults, run all feature-only canaries, and compare against a same-v3 holdout baseline with a paired confidence interval.</li><li>Check literal registry thresholds on every pre-placement surface and on final dots; write a GeoTIFF only after local range/grid checks. A separate selector controls any slot.</li></ol>
      <p><strong>Input readiness:</strong> {esc(feature_cache_status)} in this checkout. The cache receipt in evidence is historical; without the actual 19-band stack, feature canaries and model holdout cannot be run here.</p>
      <p class="subtle" style="margin-top:14px">The witness leaves {audit['budget_feasibility']['uncovered_allowed_pixels']:,} allowed pixels outside its 3-pixel halo. At most {audit['budget_feasibility']['max_dots_for_possible_70pct_pass']:,} distinct dots could possibly meet the 70% rule against this one witness; this necessary bound is not a quality or uniqueness guarantee.</p>
      <div class="actions"><a class="button secondary" href="next-hypotheses.html">Read future hypotheses</a><a class="button secondary" href="research-sources.html">View research source register</a></div></section>
    <section class="panel"><p class="eyebrow">07 / Official sources</p><h2>Trace the evidence.</h2><p class="subtle" id="public-feed" aria-live="polite">Public leaderboard observation unavailable or updating.</p>{source_links}</section>'''
    guide = f'''<section class="hero"><div><p class="eyebrow">Submission guide / Read before uploading</p><h1>Not yet. Here is the path to a valid submission.</h1>
      <p class="lead">The project must pass automated scientific, novelty, and file-format gates before a separate selector uses a weekly slot. No manual image inspection is required for this negative decision.</p></div>
      <aside class="status-card"><span class="status-label"><span class="status-dot"></span> Do not submit</span><strong>Current candidate is blocked.</strong><p>{overlap:.2f}% 3-pixel overlap exceeds the 70% limit. A format pass alone does not authorize an upload.</p></aside></section>
    <section class="panel" id="status-table"><p class="eyebrow">Answer first</p><h2>Can I download and submit a file today?</h2><p class="lead"><strong>No.</strong> No file in this repository is cleared for upload. No new TIFF was generated and no competition slot was used. No new-file score estimate is defensible.</p><div class="table-wrap"><table><thead><tr><th scope="col">File class</th><th scope="col">Score evidence</th><th scope="col">Uniqueness / format</th><th scope="col">OK to submit?</th></tr></thead><tbody><tr><td>Prior MAW-GSI candidate</td><td>No corrected v3 holdout or organizer receipt</td><td>{overlap:.2f}% of dots overlap the pinned witness within 3 px; zero outside footprint mismatches official null/NaN convention</td><td><span class="tag stop">NO · DO NOT SUBMIT</span></td></tr><tr><td>Nine historical focus TIFFs</td><td>User-reported scores only; all unconfirmed</td><td>Each fails the 70% focus-nine uniqueness gate; separate witness overlap is {focus_witness_range[0]:.2f}–{focus_witness_range[1]:.2f}%</td><td><span class="tag stop">NO · DO NOT SUBMIT</span></td></tr><tr><td>New candidate</td><td>Not estimated; no holdout model run</td><td>Not generated or checked against a complete registry</td><td><span class="tag stop">NOT AVAILABLE</span></td></tr></tbody></table></div></section>
    <p class="callout" style="margin-bottom:20px"><strong>Leaderboard correction ({leaderboard['observed_utc']} UTC):</strong> the official public table showed <strong>{top_public_score:.4f} at rank 1</strong>; the cited <strong>0.3195 appeared at rank {reference_rank}</strong>, not as the leader. The user-cited 0.4413 was not displayed in the fetched top 50. This is a dated public-standings observation, not a score for this repository's TIFF. {esc(feed_summary)} <a href="data/leaderboard_observation_20261030.json">View the evidence.</a></p>
    {official_rule_panel}
    <section class="panel"><p class="eyebrow">Executive summary / nine requested sites</p><h2>Best reported history is not a submission recommendation</h2>
      <p>GEMSDOE32 has the highest user-reported score among these nine ({best_reported['prompt_reported_claim']:.4f}), but the claim is unconfirmed. Every listed file fails the 70% directed-overlap uniqueness gate against at least one of the other eight; none is approved for submission.</p>
      <div class="table-wrap"><table><thead><tr><th scope="col">Site</th><th scope="col">Historical TIFF · research only</th><th scope="col">Method · owner-described</th><th scope="col">Prompt-reported score</th><th scope="col">New-file score estimate</th><th scope="col">Unique among focus nine? (closest peer)</th><th scope="col">Prior candidate overlap (diagnostic)</th><th scope="col">Recommendation</th></tr></thead><tbody>{''.join(table)}</tbody></table></div>
      <p class="subtle" style="margin-top:14px">The focus-nine test measures the fraction of each raster's positive cells within 3 pixels of its closest peer. The separate prior-candidate column is diagnostic only. A spatial near-duplicate flag is not an assertion that the TIFF bytes are identical. A separate one-witness audit found {focus_witness_range[0]:.2f}–{focus_witness_range[1]:.2f}% of each of these nine files' dots within 3 px of the pinned lattice; one witness proves failure but does not certify a complete registry. <a href="data/focus_overlap_review_2026-10-30.json">View the full overlap audit.</a> Future score estimates are withheld because no current same-version holdout result is linked to leaderboard calibration.</p></section>
    <section class="panel"><p class="eyebrow">Current file / audit only</p><h2>One-click research artifact</h2>
      <p>The prior <code>{esc(file_name)}</code> is locally finite and in range on the owner-mirror grid, but it writes zeros outside the footprint where the official page requires null/NaN. It is also a protocol duplicate and is <strong>not approved to submit</strong>.</p>
      <p class="subtle">SHA-256: <code>{digest}</code><br>Prior name: <code>{current_name}</code></p>
      <div class="actions"><a class="button secondary" href="{esc(research_path)}" download>Download prior TIFF · research only</a><a class="button secondary" href="data/literal_witness_audit.json">View validation report</a></div></section>
    <section class="panel"><p class="eyebrow">Automated gate checklist</p><h2>What must be true first?</h2>
      <div class="table-wrap"><table><thead><tr><th scope="col">Gate</th><th scope="col">Current status</th><th scope="col">Meaning</th></tr></thead><tbody>
      <tr><td>Format and range</td><td><span class="tag stop">OFFICIAL RULE MISMATCH</span></td><td>Local single-band float32, finite [0,1], and owner-mirror grid checks pass. The prior file writes zeros outside the footprint, contrary to the official null/NaN outside-bounds instruction. Portal behavior remains untested.</td></tr>
      <tr><td>Surface and final uniqueness</td><td><span class="tag stop">FAIL</span></td><td>Final dots fail against a pinned registry raster; original pre-placement surface is unavailable.</td></tr>
      <tr><td>Leakage canary and holdout</td><td><span class="tag stop">NOT CLEARED</span></td><td>No corrected v3 result against a same-evaluator best; previous v2 numbers are historical only.</td></tr>
      <tr><td>Separate selector</td><td><span class="tag stop">NOT APPROVED</span></td><td>Do not use a weekly slot until all gates pass and a separate selector chooses a candidate.</td></tr></tbody></table></div></section>
    <section class="panel"><p class="eyebrow">Only after a future selector approval</p><h2>How to submit on DrivenData</h2>
      <ol class="steps"><li><div><strong>Download the newly approved file.</strong><br>Use the exact filename and SHA-256 in that future run card. The research file above is not that file.</div></li>
      <li><div><strong>Open the competition.</strong><br>Sign in to <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData</a>, open the submissions page, and check the current weekly cap and available slot.</div></li>
      <li><div><strong>Choose the file.</strong><br>Upload the single-band GeoTIFF using the submission form, if the current portal instructions permit it. Use the authenticated organizer template and current rules to verify the grid and outside-bounds policy.</div></li>
      <li><div><strong>Use the future run card’s note.</strong><br>Paste its distinct comment of at most 140 characters into the optional Note field; the filename identifies the file. Do not reuse this negative audit’s note as an approval.</div></li>
      <li><div><strong>Record the receipt.</strong><br>Only the submission-page result tied to the file hash is an ORGANIZER-CONFIRMED score. A local holdout or a public team standing is not a receipt for this file.</div></li></ol></section>
    <section class="panel"><p class="eyebrow">Limitations</p><h2>What still needs access?</h2><p>The organizer data page redirects to login; the current bridge files are owner mirrors. This sandbox cannot authenticate the organizer template, see hidden labels, read your weekly quota, or upload on your behalf. External dataset catalogs were reviewed, but raw official provenance and licensing still need verification before use.</p><p><strong>Feature data:</strong> {esc(feature_cache_status)}. The recorded feature-cache receipt is historical, not the stack itself, so no feature-only canary or corrected v3 score was run in this checkout.</p>{source_links}</section>'''
    DOCS.mkdir(exist_ok=True)
    (DOCS/'data').mkdir(exist_ok=True)
    for evidence_name in ('leaderboard_observation_20261030.json', 'run_card_20261030.json',
                          'official_rules_check.json', 'focus_overlap_review_2026-10-30.json'):
        shutil.copyfile(ROOT / 'evidence' / evidence_name, DOCS / 'data' / evidence_name)
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

> **STOP — NO FILE IS READY TO SUBMIT.** The prior MAW-GSI GeoTIFF passes local float32/range/grid checks but writes zeros outside the footprint, contrary to the official null/NaN outside-bounds instruction. Also, {overlap:.2f}% of its dots overlap a registered lattice within three pixels, exceeding the 70% protocol limit. The pre-placement surface gate is unverified. No new GeoTIFF or competition submission was made; archived H-APART-6 v2 experiments predated discovery of the witness.
>
> [Open the dashboard](docs/index.html) · [Executive summary and submission guide](docs/executive-summary.html) · [Current review run card](evidence/run_card_20261030.json) · [Prior lane card](evidence/run_card.json) · [Reproducible witness audit](evidence/literal_witness_audit.json) · [Three-pass review](evidence/review_passes.md) · [Official-rule check](evidence/official_rules_check.json) · [Focus-raster overlap data](evidence/focus_overlap_review_2026-10-30.json) · [2026-10-30 overlap review](evidence/repo_review_2026-10-30_overlap.md) · [Official-rules repo review](evidence/repo_review_2026-10-30.md)
>
> [Download the **prior TIFF for research only — do not submit**](docs/downloads/{file_name}) · SHA-256 `{digest}`

## Future-session start-up: read before every run

**Objective.** Create an original, evidence-led GeoTIFF for geological-fault prediction relevant to geothermal exploration, and state plainly whether any file is safe to download or submit. Fault predictions are not direct geothermal-vent detections. Review GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36; their historical score claims are user-reported, not receipts. GEMSDOE32's claimed 0.2778 is not explained by geometry alone: B2's support equals GEMSDOE25 after a two-pixel catalogue-collar removal, a possible but unproven redundancy-pruning mechanism.

**Current lane status — stop.** The request does not unambiguously assign a fresh untried method; repo evidence identifies the inherited H-APART-2 candidate, which overlaps a pinned registry lattice by 37,533/37,654 dots ({overlap:.2f}%), above the 70% stop. Its pre-placement surface and the complete registry are unavailable. This checkout has no feature cache; a separate scratch-copy restore used owner mirrors, not organizer-origin data. Do not run more experiments, generate a new TIFF, estimate a leaderboard score, or spend a slot in this stopped lane.

### Mandatory gates

1. **Hypotheses before implementation.** Rank 3–5 untried geological hypotheses by expected DTI improvement and cost. For each, name layers, physical signature, catalogue-missing rationale, differences from this repo, a non-fault mimic, and official data availability. [Future hypotheses are recorded here](evidence/next_hypotheses.md); they are not permission to run them.
2. **One lane; surface before placement.** Stay within the assigned single method. Compare every pre-placement surface and final dots with the complete pinned registry. Stop immediately if Spearman rank correlation exceeds 0.90 or over 70% of dots fall within 3 px of any registry raster. No density exemptions.
3. **Reuse shared tools.** Reuse the template feature stack, shared holdout evaluator, and `submission_writer.py`; fix shared tools rather than keeping a private fork. Hold out whole fault segments with a buffer, derive catalogue features only from visible faults, mask visible faults pixel-exactly, and use pooled DTI (α=0.2, β=0.8; 300 m triangular kernel).
4. **Leakage canary.** Run every feature alone through holdout; **AUC >0.90 is leakage** until proven otherwise.
5. **Score labels.** Label measured model results `HOLDOUT-DTI` with evaluator version, withheld-positive count, and 95% CI. Use `ORGANIZER-CONFIRMED` only for a score on an actual submission-page receipt. Never present projections as scores.
6. **Run card.** Record hypothesis, mechanism, named non-fault mimic, holdout DTI/CI, registry correlations/overlaps, raster SHA-256, validator output, submission name, ≤140-character note, and promote/negative verdict.
7. **Budget and selector.** Stop after at most **three experiments or two hours**, and stop at once on duplication. A separate selector—not the experiment runner—chooses any real submission slot within the weekly cap.
8. **Review and report.** Use official sources, preserve limitations, run three review passes, and report negative results. Local validation is not organizer acceptance; no slot without all gates and selector approval.

**Core values:** *Maximize P(Win)* means weigh evidence, expected value, and risk; *Own the Outcome* means report failure, fix shared defects, and preserve reproducible evidence.

## Official public leaderboard observation

On **{leaderboard['observed_utc']} UTC**, the official public table showed **{top_public_score:.4f} at rank 1** and **0.3195 at rank {reference_rank}**. The prompt's 0.3195 value is therefore not the leader in this observation; 0.4413 was not present in the displayed top 50. These are public team standings, not file-level submission receipts and not score estimates for this repository. The scheduled feed status in this checkout is **{feed_status}** ({esc(feed.get('reason') or feed.get('caveat', 'a dated manual observation is recorded separately'))}); it must not be conflated with this direct, date-stamped observation. See the [dated observation record](evidence/leaderboard_observation_20261030.json), [feed snapshot](docs/data/public_feed.json), and [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

## Executive summary · nine requested sites

These are the highest historical files **named in the user prompt**, not a complete census. GEMSDOE32 has the highest user-reported historical score among the nine (**0.2778**, unconfirmed); no linked organizer receipt was found. A new-file leaderboard estimate is **not defensibly available** for any row because there is no same-version holdout-to-leaderboard calibration. The uniqueness value is the maximum directed share of each raster's dots within three pixels of one of the other eight focus-site rasters. All nine exceed the protocol's 70% threshold and are therefore **not unique under that spatial rule**; this does not mean every pair is byte-identical. None should be resubmitted as a new submission.

| Site | Historical file (research only) | Method (owner-described) | Prompt claim | Future estimate | Unique among focus nine? (closest peer) | Prior candidate overlap (diagnostic) | Decision |
| --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(md_rows)}

The re-audit confirms GEMSDOE32 B2's support equals GEMSDOE25's support outside a two-pixel catalogue collar; GEMSDOE25 and GEMSDOE30 have identical footprint values. The user-reported claims imply +0.0178 for B2 over GEMSDOE25, but neither is ORGANIZER-CONFIRMED. Under the official DTI (α=0.2 false-positive weight, β=0.8 false-negative weight), the per-truth max kernel gives diminishing benefit to extra nearby dots; pruning might reduce low-value mass, but can also reduce crucial recall. Geometry and reported scores cannot establish causation. No result here establishes that a new method will exceed 0.2778.

A separate pinned-witness audit found {focus_witness_range[0]:.2f}–{focus_witness_range[1]:.2f}% of each of the nine historical focus-site rasters' dots within 3 pixels of the same lattice witness. This is protocol overlap evidence, not byte identity and not a complete registry scan; see [`evidence/focus_overlap_review_2026-10-30.json`](evidence/focus_overlap_review_2026-10-30.json).

## Official rule check · read 2026-10-30

Quoted source excerpts are in [`evidence/official_rules_check.json`](evidence/official_rules_check.json).

* **Task:** the competition target is geological fault prediction, not direct geothermal-vent detection. The new expert-labeled test faults are described as not included in the existing USGS database; a holdout on mapped faults is a proxy, not a calibrated estimate of the hidden test.
* **Metric:** DTI uses α=0.2 for false positives, β=0.8 for false negatives, and a 300 m triangular kernel. The false-negative term is weighted four times the false-positive term; removing dots can improve or worsen score depending on coverage.
* **Raster:** a single float32 band, values in [0,1], same bounds/resolution/CRS as training data (EPSG:32611, 100 m), and null/NaN outside bounds. The prior file's zero fill outside the stored sample footprint violates that documented outside-bounds convention; its local mirror-grid/range pass is not organizer acceptance.
* **Rules:** up to three submissions per week and one final submission; the official rules include an originality warranty and require disclosure of generative-AI use in the narrative. No slot was used and no narrative/receipt exists.
* **Unresolved:** the organizer data page is login-gated and portal acceptance has not been tested. The reference sample uses NaN outside its footprint; an automated variant reproduces that mask locally but was not uploaded.

## Current result and limitations

* **HOLDOUT-DTI, historical only:** {holdout}, evaluator `{hist['evaluator_version']}`, {hist['withheld_positive_pixels']:,} withheld positives, 95% CI. This prior run used a scoring mask that included buffer-removed non-visible catalogue pixels; it is not a comparable v3 baseline or a leaderboard prediction. No v3 model run was performed after the duplicate stop.
* **Literal uniqueness:** {audit['final_dot_gate']['candidate_dots_within_3px']:,}/{audit['final_dot_gate']['candidate_dots']:,} prior dots overlap the [pinned lattice witness]({witness['url']}); only one witness is necessary to prove failure, but this is not a complete registry inventory. The word duplicate here means protocol overlap, not byte identity.
* **Feasibility:** the lattice leaves {audit['budget_feasibility']['uncovered_allowed_pixels']:,} allowed cells outside its halo, so a {audit['budget_feasibility']['requested_previous_budget']:,}-dot budget cannot pass. A budget no larger than {audit['budget_feasibility']['max_dots_for_possible_70pct_pass']:,} is necessary against this witness, not sufficient for quality or uniqueness.
* **Format:** the prior file has one float32 band, finite [0,1] values, and matches the stored owner-mirror sample grid. Local format-only preflight passes, but its zero fill outside the footprint does not match the documented official null/NaN convention. This file is not safe to submit.
* **Inputs/access:** the [competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) redirects to login; no hidden labels, submission-page receipt, quota, or authorized upload session is available. In this checkout, {esc(feature_cache_status)}; a separate scratch-copy restore from pinned owner mirrors is recorded in `evidence/repo_review_2026-10-30.md`, but those bytes are not organizer-origin data. `evidence/feature_cache.json` is a historical receipt, not the tensors in this checkout.
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
'''
    (ROOT/'README.md').write_text(readme, encoding='utf-8')
    print('Built negative-status dashboard, submission guide, and standing README.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
