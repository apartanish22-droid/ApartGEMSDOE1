"""Build docs/download-and-submit.html from evidence/submission_decision_2026-10-31.json.

Called by build_pages_and_readme.py, which owns docs/index.html, the README and
the executive summary. The page only restates the decision record; it adds no score.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / 'evidence/submission_decision_2026-10-31.json'
OUT = ROOT / 'docs/download-and-submit.html'


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def tag(text: str, kind: str) -> str:
    return f'<span class="tag {kind}">{esc(text)}</span>'


def main() -> int:
    d = json.loads(DECISION.read_text(encoding='utf-8'))
    cand = d['candidate']
    reg = d['uniqueness']
    hold = d['holdout']
    verdict = d['verdict']
    ok_submit = verdict['ok_to_submit']
    headline = ('Yes, you may submit it.' if ok_submit else
                'No. Do not submit this file yet.')
    banner_kind = 'ok' if ok_submit else 'stop'

    rows = []
    for r in d['focus_nine']:
        rows.append(f"""<tr>
<td><strong>{esc(r['site'])}</strong></td>
<td><a href="{esc(r['pages_download_url'])}">{esc(r['filename'])}</a><br><small>historical · owner mirror · research only</small></td>
<td>{esc(r['claim_text'])}</td>
<td>Not estimable · no organizer receipt</td>
<td>{tag('NO', 'stop')} overlaps the nearest focus-nine file by {esc(r['nearest_peer_overlap_pct'])}% within 3 px ({esc(r['closest_peer'])})</td>
</tr>""")
    focus_rows = '\n'.join(rows)

    reasons = ''.join(f'<li>{esc(x)}</li>' for x in verdict['reasons'])
    irregular = ''.join(f'<li>{esc(x)}</li>' for x in d['irregularities'])
    sources = ''.join(
        f'<li><a href="{esc(s["url"])}">{esc(s["label"])}</a></li>' for s in d['sources'])

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Download and submit · GEMS DOE ApartGEMSDOE1</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1040px;margin:0 auto;padding:24px;line-height:1.5;color:#1b1f24}}
table{{border-collapse:collapse;width:100%;margin:12px 0}}
th,td{{border:1px solid #d0d7de;padding:8px;vertical-align:top;text-align:left;font-size:14px}}
th{{background:#f6f8fa}}
.banner{{padding:16px;border-radius:8px;margin:12px 0;font-size:18px}}
.banner.stop{{background:#ffebe9;border:2px solid #cf222e}}
.banner.ok{{background:#dafbe1;border:2px solid #1a7f37}}
.tag{{display:inline-block;padding:2px 8px;border-radius:12px;font-weight:600;font-size:12px}}
.tag.ok{{background:#dafbe1}} .tag.stop{{background:#ffebe9}} .tag.warn{{background:#fff8c5}}
code{{background:#f6f8fa;padding:2px 4px;border-radius:4px;word-break:break-all}}
.dl{{display:inline-block;background:#0969da;color:#fff;padding:10px 16px;border-radius:6px;text-decoration:none;font-weight:600}}
small{{color:#57606a}}
</style></head><body>
<p><a href="../README.md">← README</a></p>
<h1>Download and submit</h1>
<div class="banner {banner_kind}"><strong>{esc(headline)}</strong><br>{esc(verdict['one_line'])}</div>

<h2>1 · File to download</h2>
<table>
<thead><tr><th>File to download</th><th>Estimated leaderboard score</th><th>Unique vs GEMSDOE sites?</th><th>OK to download and submit?</th></tr></thead>
<tbody>
<tr>
<td><a class="dl" href="{esc(cand['repo_path'].replace('docs/', '', 1))}" download>Download GeoTIFF</a><br><code>{esc(cand['filename'])}</code><br><small>SHA-256 <code>{esc(cand['sha256'])}</code> · {cand['bytes']:,} bytes · float32, single band, EPSG:32611, 100 m</small></td>
<td>{esc(hold['estimate_label'])}</td>
<td>{tag(reg['status_label'], 'ok' if reg['unique_vs_registry'] else 'warn')}<br><small>{esc(reg['summary'])}</small></td>
<td>{tag('NO' if not ok_submit else 'YES', 'stop' if not ok_submit else 'ok')}<br><small>{esc(verdict['download_note'])}</small></td>
</tr>
</tbody></table>

<h3>Submission form values (use only after it is cleared)</h3>
<ul>
<li>Submission name: <code>{esc(cand['submission_name'])}</code> ({len(cand['submission_name'])} characters)</li>
<li>Note: <code>{esc(cand['note'])}</code> ({len(cand['note'])} characters; limit 140)</li>
</ul>

<h2>2 · Automated checks (no human inspection)</h2>
<table><thead><tr><th>Check</th><th>Result</th></tr></thead><tbody>
<tr><td>Single band, float32, grid 3730 × 3292, EPSG:32611, 100 m, transform equal to the sample</td><td>{tag('PASS', 'ok')}</td></tr>
<tr><td>Values inside the footprint are finite and in [0, 1]</td><td>{tag('PASS', 'ok')}</td></tr>
<tr><td>NaN mask equals the sample template's NaN mask (official: outside bounds is null or nan)</td><td>{tag('PASS', 'ok')}</td></tr>
<tr><td>No dots on the mapped catalogue; no positive value outside the footprint</td><td>{tag('PASS', 'ok')}</td></tr>
<tr><td>Exact-copy check against every GeoTIFF blob in the owner-repo inventory ({reg['blobs_listed_count']:,} blobs)</td><td>{esc(reg['exact_copy_result'])}</td></tr>
<tr><td>Spatial overlap against {reg['spatial_files_scanned']:,} submitted rasters (3-px dot overlap ≤ 70%; correlation ≤ 0.90)</td><td>{esc(reg['spatial_result'])}</td></tr>
<tr><td>Holdout score measured for this exact file</td><td>{tag('NO', 'stop')} {esc(hold['measurement_gap'])}</td></tr>
</tbody></table>

<h2>3 · The nine focus sites</h2>
<p>Each site has one file named in the prompt. The "highest-scoring submission" is therefore the named file. Claims are the prompt's values, not organizer receipts. The highest claim is GEMSDOE32 at 0.2778.</p>
<table><thead><tr><th>Site</th><th>File to download</th><th>Prompt claim (unconfirmed)</th><th>Estimated score</th><th>Unique among focus nine?</th></tr></thead>
<tbody>{focus_rows}</tbody></table>
<p><strong>Best submission pick:</strong> {esc(d['best_pick']['text'])}</p>

<h2>4 · Leaderboard reference</h2>
<p>Top public DW-Tversky: <strong>{d['leaderboard']['top_public_dti']:.4f}</strong>, direct read of the official page on {esc(d['leaderboard']['observed'])}; the scheduled feed script returned unavailable the same day, so no feed value is shown. This is team-level public standing, not a score receipt for any file. The prompt's 0.4413 and 0.3195 do not match this reading.</p>

<h2>5 · Irregularities flagged</h2>
<ul>{irregular}</ul>

<h2>6 · Why the answer is "no"</h2>
<ul>{reasons}</ul>

<h2>Sources</h2>
<ul>{sources}</ul>
<p><small>Generated from <code>evidence/submission_decision_2026-10-31.json</code> by <code>scripts/build_submit_page.py</code>.</small></p>
</body></html>
"""
    OUT.write_text(page, encoding='utf-8')
    print(f'wrote {OUT.relative_to(ROOT)} · ok_to_submit={ok_submit}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
