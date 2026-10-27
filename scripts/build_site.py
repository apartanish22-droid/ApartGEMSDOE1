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
    for n, token, reported in DATA:
        site = 'GEMSDOE'+n
        item = inventories[site]
        matches = [p for p in item['rasters'] if token in p and p.endswith('.tif')]
        links = '<br>'.join('<a href="https://github.com/buffedlizard55-lab/'+site+'/blob/'+item['ref']+'/'+p+'">'+html.escape(Path(p).name)+'</a>' for p in matches) or 'Exact historical file not resolved in current tree'
        detail = f'<h1>{site} executive summary</h1><p class="warning"><strong>DO NOT SUBMIT: historical reference only.</strong> No new approved file.</p><p>Highest result in the supplied user history: {reported} — USER-REPORTED, not ORGANIZER-CONFIRMED. This is not a projection or a new HOLDOUT-DTI measurement.</p><h2>Historical files for research</h2><p>{links}</p><p>Uniqueness: NOT VERIFIED against the complete registry. A different filename or hash is insufficient. Do not resubmit previous entries.</p><p>Estimated leaderboard result for a new submission: unavailable. No local candidate was trained or evaluated.</p><p><a href="{item["source"]}">Pinned source site snapshot</a> · <a href="../../index.html">Portfolio summary</a></p>'
        (ROOT/f'docs/sites/{site}.html').write_text(page(site,detail))
    # Root index is the current Pages fallback, not an output of this legacy builder.


if __name__ == '__main__':
    main()
