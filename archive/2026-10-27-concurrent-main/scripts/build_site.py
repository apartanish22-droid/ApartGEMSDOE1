"""Render a static, evidence-labelled executive summary; no external JS."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = [
 ('24','989f59505db1','0.2477'), ('25','e56ea318af89','0.2600'),
 ('27','5512495c6bd1','0.2449'), ('28','b531dae0a36f','0.2710'),
 ('30','91eae1ca','0.2600'), ('31','8acb75e1','0.2708'),
 ('32','e5eb6e7e','0.2778'), ('33','cb490425926e','0.2632'),
 ('36','9b9ea4e6','0.2750')]
STYLE = '''<style>body{font:16px/1.65 system-ui;max-width:1160px;margin:40px auto;padding:0 24px;color:#21313e;background:#f6f8fa}h1{font-size:2.4rem;line-height:1.2}a{color:#1258aa}table{border-collapse:collapse;width:100%;background:white}td,th{padding:12px;text-align:left;border-bottom:1px solid #ddd;vertical-align:top} .warning{border-left:6px solid #ad2538;padding:20px;background:#fff0f0} .scroll{overflow:auto}small{color:#516170}</style>'''


def page(title, body):
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title>'+STYLE+'<main>'+body+'</main></html>\n'


def main():
    inventories = {s['repo']:s for s in json.loads((ROOT/'evidence/site_inventory.json').read_text())}
    rows = []
    for n, token, reported in DATA:
        site = 'GEMSDOE'+n
        item = inventories[site]
        matches = [p for p in item['rasters'] if token in p and p.endswith('.tif')]
        links = '<br>'.join('<a href="https://github.com/buffedlizard55-lab/'+site+'/blob/'+item['ref']+'/'+p+'">'+html.escape(Path(p).name)+'</a>' for p in matches) or 'Exact historical file not resolved in current tree'
        detail = f'<h1>{site} executive summary</h1><p class="warning"><strong>DO NOT SUBMIT: historical reference only.</strong> No new approved file.</p><p>Highest result in the supplied user history: {reported} — USER-REPORTED, not ORGANIZER-CONFIRMED. This is not a projection or a new HOLDOUT-DTI measurement.</p><h2>Historical files for research</h2><p>{links}</p><p>Uniqueness: NOT VERIFIED against the complete registry. A different filename or hash is insufficient. Do not resubmit previous entries.</p><p>Estimated leaderboard result for a new submission: unavailable. No local candidate was trained or evaluated.</p><p><a href="{item["source"]}">Pinned source site snapshot</a> · <a href="../../index.html">Portfolio summary</a></p>'
        (ROOT/f'docs/sites/{site}.html').write_text(page(site,detail))
        rows.append(f'<tr><td><a href="docs/sites/{site}.html">{site}</a></td><td>{reported}<br><small>USER-REPORTED historical result</small></td><td>No approved download<br><small>Historical files on site summary</small></td><td>Unavailable</td><td>Not verified</td><td>NO</td></tr>')
    body = '''<p>APARTGEMSDOE1 / RESEARCH CONTROL DESK / 27 OCT 2026</p><h1>Evidence before submission.</h1><p class="warning"><strong>DO NOT SUBMIT — no approved new TIF exists.</strong><br>No download is presented as competition-ready. Experiments are blocked by a missing method lane, canonical runtime, cached data, and complete raster registry. No weekly slot was used.</p><p><a href="docs/research.md">Hypotheses & scientific review</a> · <a href="evidence/run_card.json">JSON run card</a> · <a href="README.md">Standing brief & next steps</a></p><h2>Nine-site executive summary</h2><p>The historical results below were supplied by the user; no organizer receipts were retrieved. They are deliberately not labelled ORGANIZER-CONFIRMED or HOLDOUT-DTI. GEMSDOE32 has the highest result in this supplied nine-site history, not a proven best future submission. No reliable estimate is available for a new file.</p><div class="scroll"><table><thead><tr><th>Site summary</th><th>Historical result / evidence</th><th>File to download & submit</th><th>New estimate</th><th>Unique?</th><th>Submit?</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table></div><h2>Why GEMSDOE32 may have helped</h2><p>Its source describes sparse dot placement and removal of catalogue-adjacent predictions. This can preserve coverage while cutting low-credit prediction mass. Hidden truth and score receipts are unavailable: this mechanism is plausible, not proven. The source also reports conflicting holdout evaluations, so its historical result cannot calibrate a new leaderboard estimate.</p><h2>How an approved entry will be submitted</h2><ol><li>Obtain a candidate that beats the matched incumbent on buffered whole-segment holdout; publish evaluator version, withheld count and spatial 95% CI.</li><li>Pass every feature leakage canary and both surface and final-dot registry gates. Distinct bytes alone do not mean unique science.</li><li>Use the canonical writer, then validate the saved single-band TIF against the real template: finite values in [0,1], exact CRS, shape and transform. Publish SHA-256, unique name and note of at most 140 characters.</li><li>A separate selector verifies the current weekly cap and authorizes promotion. No slot is authorized by this page.</li><li>Only then use the competition New submission form, choose the approved .tif (or single-TIF ZIP), paste the note, and retain the organizer receipt linked to the exact file hash.</li></ol><h2>Irregularities & limits</h2><ul><li>Repository initially had only a README; no prior training pipeline exists here.</li><li>No method lane was supplied. No geological experiment was run.</li><li>The shared writer inspected in the sibling converts positive probabilities into binary dots. Its docstring does not describe that distinction clearly. No private replacement was made.</li><li>The mirror manifest explicitly disclaims organizer authentication; feature cache bytes are absent.</li><li>The prompt supplied conflicting current leaderboard figures; neither was verified. Live competition cap and standings are unknown.</li><li>Only this repository is modified. The nine external sites have local review subpages here, not changes deployed to their repositories.</li></ul><h2>Audit trail</h2><p><a href="evidence/site_inventory.json">Nine pinned GitHub trees and source-page hashes</a> · <a href="evidence/official_source.json">Official reference provenance</a> · <a href="evidence/readiness.json">Automated preflight</a></p><p><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Official reference solution</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition</a></p><small>Official reference README retrieved via GitHub. Competition and scientific external links are provided for review, not claimed live-verified. This static page is not an automatically refreshed leaderboard feed.</small>'''
    (ROOT/'index.html').write_text(page('ApartGEMSDOE1 | Executive summary',body))


if __name__ == '__main__':
    main()
