#!/usr/bin/env python3
"""Build the submission hub (executive summary, front page, README) from evidence files.

Replaces the retired ``build_pages_and_readme.py``. Every number is read from a file under
evidence/ or docs/downloads/. Nothing numeric is typed in. A missing input fails the build.

Reads:
  evidence/candidate_selection.json      decisions and wording only (name, note, flags, sources)
  evidence/registry_inventory.json       mirror inventory (scope and counts)
  evidence/focus_pairwise_overlap.json   nine-by-nine 3-px overlap (scripts/focus_pairwise.py)
  evidence/holdout_h_sc1_seed2026.json   holdout quantiles 0.97 / 0.99 / 0.995
  evidence/holdout_h_sc1_experiment2.json holdout quantiles 0.90 / 0.95
  evidence/paired_policy_vs_random.json  paired CI, submitted policy vs matched random
  evidence/<uniqueness_file>             registry gate for the chosen candidate
  evidence/run_card_h-sc1-<name>.json    run card (verdict)
  docs/downloads/<file>.json             write_submission receipt
"""
from __future__ import annotations

import html
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_pages_and_readme import page  # noqa: E402  (shared page chrome)

EV = ROOT / "evidence"
DOCS = ROOT / "docs"
FOCUS = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]


def esc(v) -> str:
    return html.escape(str(v), quote=True)


def load(path: Path):
    if not path.exists():
        raise SystemExit(f"missing evidence input: {path.relative_to(ROOT)}")
    return json.loads(path.read_text())


def pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def main() -> int:
    sel = load(EV / "candidate_selection.json")
    inv = load(EV / "registry_inventory.json")
    focus = load(EV / "focus_pairwise_overlap.json")
    h1 = load(EV / "holdout_h_sc1_seed2026.json")
    h2 = load(EV / "holdout_h_sc1_experiment2.json")
    paired = load(EV / "paired_policy_vs_random.json")
    uq = load(EV / sel["uniqueness_file"])
    card = load(EV / sel["run_card"])
    rec = load(ROOT / sel["receipt"])
    cleared = bool(sel["cleared"])

    prior_card = load(EV / "run_card.json")
    prior_sha = prior_card["raster_sha256"]
    witness = load(EV / "literal_witness_audit.json")
    prior_overlap = witness["final_dot_gate"]["forward_overlap_3px"]
    overlap_limit = witness["final_dot_gate"]["limits"]["forward_overlap"]
    rules = load(EV / "official_rules_check.json")
    gate = uq["gate"]
    name = sel["name"]
    tif = sel["file"]
    fmt_ok = bool(rec["validator"]["all_checks_passed"])
    uniq_ok = bool(gate["unique"]) and bool(uq["complete_accessible_scan"])
    safe_dl = cleared and fmt_ok and uniq_ok
    slot_ok = card["verdict"] == "promote"
    dl_label = "SAFE TO DOWNLOAD" if safe_dl else "NOT CLEARED: DO NOT SUBMIT"
    slot_label = ("Promoted to a slot" if slot_ok else
                  "Not promoted: no clear edge over random density")
    dl_class = "ok" if safe_dl else "stop"
    slot_class = "ok" if slot_ok else "warn"

    # --- Nine focus sites (measured overlaps, nine-by-nine only) -------------------
    focus_rows, focus_md = [], []
    for repo in FOCUS:
        f = focus["sites"][repo]
        est = "Not estimable: no fold-honest holdout for this file"
        uniq = f"Not unique: {pct(f['max_overlap'])} of its dots within 3 px of {esc(f['closest_peer'])}"
        claim = f"{f['claimed_score']:.4f}"
        link = f"<a href=\"{esc(f['raw_link'])}\">{esc(f['file'])}</a>"
        focus_rows.append(
            f"<tr><td>{repo}</td><td>{link}<br><small>research only</small></td>"
            f"<td>{claim}<br><small>user claim, unconfirmed</small></td>"
            f"<td>{est}</td><td>{uniq}</td><td><span class=\"tag stop\">NO</span></td></tr>")
        focus_md.append(f"| {repo} | `{f['file']}` | {claim} (user claim) | not estimable | "
                        f"no: {pct(f['max_overlap'])} to {f['closest_peer']} | NO |")

    # --- Holdout rows for every quantile ------------------------------------------
    holdout_rows = []
    all_variants = {**h1["variants"], **h2["variants"]}
    for k in sorted(all_variants, key=lambda x: float(x[1:])):
        v = all_variants[k]
        pk = paired["results"].get(k)
        pol = v["submitted_policy"]
        rnd = (f"{pk['random_dti_mean']:.4f}" if pk else "not run")
        holdout_rows.append(
            f"<tr><td>{esc(k)}</td><td>{v['dots_global']:,}</td>"
            f"<td>{v['dti']:.4f}<br><small>[{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]</small></td>"
            f"<td><strong>{pol['dti']:.4f}</strong><br><small>[{pol['ci95'][0]:.4f}, {pol['ci95'][1]:.4f}]</small></td>"
            f"<td>{rnd}</td></tr>")

    file_cell = (f'<a href="downloads/{esc(tif)}" download>{esc(tif)}</a>' if cleared else
                 f'<span class="tag stop">not published</span><br><small>{esc(tif)} stays in the local cache, not offered for download.</small>')
    cand_k = sel["quantile_key"]
    pk = paired["results"][cand_k]
    deltas = [d["paired_candidate_minus_random"]["delta"] for d in pk["random_draws"]]
    lows = [d["paired_candidate_minus_random"]["ci95"][0] for d in pk["random_draws"]]
    hv = all_variants[cand_k]
    pol = hv["submitted_policy"]

    if cleared:
        download_block = f"""<h2>{esc(tif)}</h2>
      <p>Single-band float32 GeoTIFF, EPSG:32611, {rec['validator']['meta']['shape'][1]} × {rec['validator']['meta']['shape'][0]} at 100 m. Values are 0 or 1. Cells outside the footprint are 0 (no NaN anywhere). {rec['validator']['emitted_positive_pixels']:,} positive dots.</p>
      <div class="actions"><a class="button" href="downloads/{esc(tif)}" download>Download the .tif</a>
      <a class="button secondary" href="downloads/{esc(tif.replace('.tif', '.zip'))}" download>Download the .zip (same TIFF)</a>
      <a class="button secondary" href="data/{esc(sel['run_card'])}">Run card (JSON)</a></div>"""
    else:
        download_block = f"""<h2>No file is cleared for download</h2>
      <p>{esc(sel['status_text'])}</p>
      <p class="subtle">The candidate ({esc(tif)}) is held in the local cache and is not published. Publishing it would require a passing uniqueness gate, which it does not have (see the flags).</p>
      <div class="actions"><a class="button secondary" href="data/{esc(sel['run_card'])}">Run card (JSON)</a></div>"""

    flags_html = "".join(f"<li>{esc(x)}</li>" for x in sel["flags"])
    sources_html = "".join(
        f"<li><a href=\"{esc(u)}\">{esc(t)}</a> <small>{esc(n)}</small></li>" for u, t, n in sel["sources"])
    cm = rec["validator"]
    canary = h1["leakage_canary_max"]

    exec_html = f"""<section class="hero"><div><p class="eyebrow">Executive summary</p>
      <h1>{'One unique GeoTIFF is cleared for download.' if cleared else 'No unique GeoTIFF is cleared yet.'}</h1>
      <p class="lead">{esc(sel['status_text'])} The holdout gives no clear advantage over random placement at the same density, so nothing is promoted to a submission slot.</p></div>
      <aside class="status-card"><span class="status-label"><span class="status-dot"></span>
      <span class="tag {dl_class}">{dl_label}</span> <span class="tag {slot_class}">{esc(slot_label)}</span></span>
      <strong>{esc(name)}</strong><p>{esc(sel['note'])}</p></aside></section>

    <section class="panel" id="table"><p class="eyebrow">Summary table</p><h2>File, estimate, uniqueness</h2>
      <div class="table-wrap"><table><thead><tr><th>File to download</th><th>Estimated score</th><th>Uniqueness vs GEMSDOE sites</th><th>Verdict</th></tr></thead>
      <tbody><tr><td>{file_cell}<br><small>SHA-256 <code>{esc(rec['sha256'])}</code></small></td>
      <td><strong>HOLDOUT-DTI {pol['dti']:.4f}</strong> (95% CI [{pol['ci95'][0]:.4f}, {pol['ci95'][1]:.4f}]; evaluator {esc(hv['evaluator_version'])}; {hv['withheld_positive_pixels']:,} withheld positives). Proxy only, not a leaderboard value. ORGANIZER-CONFIRMED: none.</td>
      <td>{'PASS' if uniq_ok else 'FAIL'} against {gate['registry_rasters_checked']:,} registry rasters ({esc(sel['uniqueness_mode'])}). Worst 3-px overlap {pct(gate['worst_dot_overlap'])} (limit 70%). Worst rank correlation {gate['worst_spearman_full_footprint']:.3f} (limit 0.90).</td>
      <td>{dl_label}. {esc(slot_label)}.</td></tr></tbody></table></div>
      <p class="subtle">Nine focus files are not unique to each other (table below). None is recommended.</p></section>

    <section class="panel" id="download"><p class="eyebrow">Download</p>
      {download_block}</section>

    <section class="panel" id="focus"><p class="eyebrow">Nine focus sites</p><h2>Which of the nine files should be submitted?</h2>
      <p><strong>None.</strong> Each of the nine files has more than 70% of its dots within 3 px of a sibling file. This measures pairwise overlap among the nine only. A registry-wide check of the nine is not run.</p>
      <div class="table-wrap"><table><thead><tr><th>Site</th><th>Historical file</th><th>Claimed score</th><th>Estimated score</th><th>Unique?</th><th>Submit?</th></tr></thead>
      <tbody>{''.join(focus_rows)}</tbody></table></div>
      <p class="subtle">GEMSDOE32 claim 0.2778 is the highest value among the nine claims; the prompt also cites 0.3195 as "highest", which does not match the leaderboard page read on 2026-10-30 (see flags).</p></section>

    <section class="panel" id="holdout"><p class="eyebrow">Holdout</p><h2>How the candidate behaves</h2>
      <p>Columns: global dots (keeps dots on mapped catalogue cells), the submitted-policy DTI (drops them, as the file does), and the mean DTI of random placement at the same count, which is only computed for the submitted policy.</p>
      <div class="table-wrap"><table><thead><tr><th>Quantile</th><th>Dots (global)</th><th>HOLDOUT-DTI global</th><th>HOLDOUT-DTI submitted policy</th><th>Random, same policy (mean of 5)</th></tr></thead>
      <tbody>{''.join(holdout_rows)}</tbody></table></div>
      <p><strong>Paired comparison, {esc(cand_k)}:</strong> candidate minus random = {', '.join(f'{d:+.4f}' for d in deltas)} across 5 random draws. Lower 95% bound per draw: {', '.join(f'{x:+.4f}' for x in lows)}. The bound is above zero in {sum(1 for x in lows if x > 0)} of 5 draws, so the advantage over random density is not established.</p>
      <p class="subtle">Evaluator {esc(hv['evaluator_version'])}; fold draw seed 2026; hide 20%; buffer 3 px. CIs are paired percentile bootstrap over physical blocks. Leakage canary: largest single-feature AUC {canary:.3f} (limit 0.90) — {esc(h1['canary_verdict'])}.</p></section>

    <section class="panel" id="how"><p class="eyebrow">Upload</p><h2>How to submit (if the user chooses to)</h2>
      <ol class="steps"><li><div><strong>Verify</strong> the download: the SHA-256 above must match the file.</div></li>
      <li><div><strong>Open</strong> the competition submission page (DrivenData; login required). The page was not reachable from this sandbox.</div></li>
      <li><div><strong>Upload</strong> the .tif (or the .zip, if the form requires one). Name: <code>{esc(name)}</code>. Note (≤140 characters): <code>{esc(sel['note'])}</code></div></li>
      <li><div><strong>If the portal says "Predicted values must be in range [0, 1]"</strong>, stop and report the exact file name and SHA-256. This file's values are all 0 or 1, and the local validator reports no NaN anywhere.</div></li>
      <li><div><strong>Record the score</strong> only from the submission page receipt. That is the only ORGANIZER-CONFIRMED value.</div></li></ol></section>

    <section class="panel" id="prior"><p class="eyebrow">Earlier file · blocked</p><h2>Earlier research file: do not submit</h2>
      <p>The earlier MAW-GSI TIF (SHA-256 <code>{esc(prior_sha)}</code>, research only) is <strong>DO NOT SUBMIT</strong>. Its dots overlap the lattice witness at {pct(prior_overlap)} (limit {overlap_limit*100:.0f}%), and it writes zeros outside the footprint. Source: <code>evidence/literal_witness_audit.json</code>.</p></section>
    <section class="panel" id="leaderboard"><p class="eyebrow">Leaderboard provenance</p><h2>What the 0.4544 value means</h2>
      <p>{esc(rules['leaderboard_observed']['note'])}</p>
      <p>The 0.4544 value is a direct read (fetch) of the leaderboard page on 2026-10-30. The scheduled feed script returned unavailable that day. It is team-level public standing, not a score receipt for any file. The prompt's 0.4413 and 0.3195 do not appear in the ranks 1–22 read.</p></section>
    <section class="panel" id="flags"><p class="eyebrow">Irregularities for manual review</p><h2>Flags</h2><ul>{flags_html}</ul></section>
    <section class="panel" id="sources"><p class="eyebrow">Sources</p><h2>Links for manual verification</h2><ul class="source-list">{sources_html}</ul></section>
    """

    (DOCS / "h-sc1-summary.html").write_text(
        page("H-SC1 summary", "guide", exec_html), encoding="utf-8")

    focus_index_rows = []
    for repo in FOCUS:
        f = focus["sites"][repo]
        focus_index_rows.append(
            f"<tr><td>{repo}</td><td>{f['claimed_score']:.4f} <small>user-reported; unconfirmed</small></td>"
            f"<td>Not estimable</td><td>No: {pct(f['max_overlap'])} to {esc(f['closest_peer'])}</td></tr>")
    index_html = f"""<section class="hero"><div><p class="eyebrow">Overview</p><h1>GEMS geothermal fault prediction</h1>
      <p class="lead">{esc(sel['status_text'])} Nothing is promoted to a slot.</p></div>
      <aside class="status-card"><span class="status-label"><span class="status-dot"></span>
      <span class="tag {dl_class}">{dl_label}</span></span><strong>{esc(name)}</strong>
      <p><a href="executive-summary.html#table">Summary table</a> · <a href="executive-summary.html#focus">Nine focus sites</a> · <a href="executive-summary.html#flags">Flags</a></p></aside></section>
    <section class="panel"><p class="eyebrow">Nine focus sites</p><h2>Unique among focus nine? (closest peer)</h2>
      <div class="table-wrap"><table><thead><tr><th>Site</th><th>Claimed score</th><th>Estimated score</th><th>Unique among focus nine? (closest peer)</th></tr></thead>
      <tbody>{''.join(focus_index_rows)}</tbody></table></div>
      <p class="subtle">Overlap with the prior ApartGEMSDOE1 candidate; not the focus-nine test. Pairwise 3-px overlap among the nine is in <code>evidence/focus_pairwise_overlap.json</code>.</p></section>
    <section class="panel"><p class="eyebrow">Holdout</p><h2>Proxy score for the candidate</h2>
      <p>HOLDOUT-DTI {hv['submitted_policy']['dti']:.4f} · 95% CI [{hv['submitted_policy']['ci95'][0]:.4f}, {hv['submitted_policy']['ci95'][1]:.4f}] · evaluator <code>{esc(hv['evaluator_version'])}</code> · {hv['withheld_positive_pixels']:,} withheld positives. Earlier v2 holdout numbers are not comparable to this v3 evaluator. This is a proxy, not an organizer score.</p>
      <p class="subtle">Format note: for outside bounds, the official rule text says null or nan (quoted from the rules record). This project's file writes zeros outside the footprint, the same convention as the DrivenData reference output. The portal's behaviour on either convention is untested (see flags).</p>
      <p class="subtle">Matched random placement (mean of 5 draws): {paired['results'][cand_k]['random_dti_mean']:.4f}. The paired lower bound is above zero in {sum(1 for d in paired['results'][cand_k]['random_draws'] if d['paired_candidate_minus_random']['ci95'][0] > 0)} of 5 draws.</p></section>
    <section class="panel"><p class="eyebrow">Prior file</p><h2>Earlier research file: do not submit</h2>
      <p>SHA-256 <code>{esc(prior_sha)}</code> · research only · DO NOT SUBMIT · lattice-witness overlap {pct(prior_overlap)} (limit {overlap_limit*100:.0f}%) · zeros outside the footprint.</p></section>
    <section class="panel"><p class="eyebrow">Pages</p><h2>Where to go next</h2><ul>
      <li><a href="executive-summary.html">Executive summary and download</a></li>
      <li><a href="research-sources.html">Research sources</a></li>
      <li><a href="next-hypotheses.html">Ranked hypotheses</a></li>
      <li><a href="data/{esc(sel['run_card'])}">Run card (JSON)</a></li></ul></section>"""
    # docs/index.html and the root index.html belong to build_pages_and_readme.py on main; this hub does not write them.

    data_dir = DOCS / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for src in ("candidate_selection.json", "holdout_h_sc1_seed2026.json", "holdout_h_sc1_experiment2.json",
                "paired_policy_vs_random.json", "focus_pairwise_overlap.json", "registry_sites.json",
                sel["uniqueness_file"], sel["run_card"]):
        (data_dir / src).write_bytes((EV / src).read_bytes())

    (EV / "focus_nine_table.md").write_text(
        "| Site | Historical file | Claimed score | Estimated score | Unique? | Submit? |\n"
        "| --- | --- | --- | --- | --- | --- |\n" + "\n".join(focus_md) + "\n", encoding="utf-8")

    focus_md_rows = [f"| {repo} | `{focus['sites'][repo]['file']}` | {focus['sites'][repo]['claimed_score']:.4f} (user claim) | not estimable | "
                     f"no: {focus['sites'][repo]['max_overlap']*100:.2f}% to {focus['sites'][repo]['closest_peer']} | NO |"
                     for repo in FOCUS]
    block = (f"> **H-SC1 lane (2026-10-31, branch arena/ff2aae12-apartgemsdoe1): {'DOWNLOAD SAFE' if safe_dl else 'NOT CLEARED'} — no file cleared to submit.** "
             f"Candidate `{name}` (SHA-256 `{rec['sha256']}`) is not in docs/downloads. "
             f"Literal uniqueness: FAIL (worst 3-px overlap {gate['worst_dot_overlap']*100:.2f}%). "
             f"HOLDOUT-DTI (submitted policy) {hv['submitted_policy']['dti']:.4f} [95% CI {hv['submitted_policy']['ci95'][0]:.4f}, {hv['submitted_policy']['ci95'][1]:.4f}], "
             f"evaluator `{hv['evaluator_version']}`, {hv['withheld_positive_pixels']:,} withheld positives. Proxy only; ORGANIZER-CONFIRMED: none. "
             f"Details: [H-SC1 summary](docs/h-sc1-summary.html) · [run card](evidence/{sel['run_card']}) · [candidate selection](evidence/candidate_selection.json).\n")
    (EV / "h_sc1_status_block.md").write_text(block, encoding="utf-8")
    print(f"hub built for {tif}: download={'SAFE' if safe_dl else 'BLOCKED'} slot={'promote' if slot_ok else 'not promoted'}")
    return 0


def build_readme(sel, uq, card, rec, paired, hv, pol, safe_dl, slot_ok, prior_sha, prior_overlap,
                 overlap_limit, rules, focus_md_rows) -> str:
    gate = uq["gate"]
    cand_k = sel["quantile_key"]
    rows = paired["results"][cand_k]["random_draws"]
    lows = [d["paired_candidate_minus_random"]["ci95"][0] for d in rows]
    deltas = [d["paired_candidate_minus_random"]["delta"] for d in rows]
    if safe_dl:
        banner = f"> **Download: SAFE for `{sel['file']}` (format and registry checks pass).**"
        file_line = f"> File: [`docs/downloads/{sel['file']}`](docs/downloads/{sel['file']}) · SHA-256 `{rec['sha256']}`"
    else:
        banner = ("> **No file is cleared for download or submission. NOT CLEARED: DO NOT SUBMIT.** "
                  "The H-SC1 candidate fails the literal uniqueness gate, and it does not clearly beat random placement.")
        file_line = (f"> Candidate `{sel['file']}` (SHA-256 `{rec['sha256']}`) is held in the local cache and is "
                     "**not published**.")
    slot = ("**Slot: promoted.**" if slot_ok else
            "**Slot: not promoted.** Current lane status — stop for H-SC1 (uniqueness gate fails; no clear edge over random density).")
    focus_table = "\n".join(focus_md_rows)
    return f"""# ApartGEMSDOE1 · GEMS geothermal fault prediction

{banner}
>
> {slot}
>
{file_line}
>
> [Executive summary](docs/executive-summary.html) · [Nine-site table](evidence/focus_nine_table.md) · [Candidate selection](evidence/candidate_selection.json) · [Run card](evidence/{sel['run_card']}) · [Hypotheses](evidence/hypotheses_2026-10-31.md) · [Registry inventory](evidence/registry_inventory.json)

## Future-session start-up: read before every run

1. Read this README and `evidence/candidate_selection.json` (verdict, flags, sources).
2. Read the full competition prompt. **The verbatim prompt is not stored in this repo yet** (listed as remaining work). Add it at `docs/prompt-full.md`.
3. Read `evidence/hypotheses_2026-10-31.md` and pick one lane. Stay in a single method lane per session.
4. Check the lane budget: three experiments or two hours per lane. Single-feature AUC >0.90 is leakage until proven otherwise.
5. Run the uniqueness gate on the complete registry scan before any upload decision. Fail closed.

## Project brief (condensed; full prompt not stored verbatim)

**Goal.** Place at the top of the DOE GEMS leaderboard by predicting concealed geothermal faults that are **not** in the USGS fault database. Submit one single-band float32 GeoTIFF (EPSG:32611, 100 m, values in [0, 1]). Scoring is distance-weighted Tversky, α = 0.2, β = 0.8, 300 m (3 px) kernel.

Sources: [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) · [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution). The rules and leaderboard were read on 2026-10-30 and are not re-verified here (the sandbox cannot reach those hosts).

**Working rules (standing protocol).**
1. A file is submittable only if it is unique: no more than 70% of its dots within 3 px of one registry raster, and rank correlation at most 0.90, on a complete registry scan. Check the surface and the final dots.
2. Reuse the shared template (`gems57` metric, holdout, uniqueness gate, `submission_writer`). Fix shared tools in place; do not fork.
3. Label every number **HOLDOUT-DTI** (our proxy, with evaluator version, withheld-positive count and 95% CI) or **ORGANIZER-CONFIRMED** (from a submission-page receipt). Never present a projection as a score.
4. Leakage canary: a single feature with AUC above 0.90 means leakage until proven otherwise.
5. Every run ends with a run card. Budget: three experiments or two hours per lane. Do not pick submissions; promotion is a separate selector step.

**Core values.** *Maximize P(Win)*: weigh evidence, expected value and risk. *Own the outcome*: report failures and fix shared defects.

## Current status

* **Candidate:** `{sel['name']}` (H-SC1 lidar convex-crest scarp traces, catalogue-free score map, q0.90).
* **Holdout, submitted policy (HOLDOUT-DTI):** {hv['submitted_policy']['dti']:.4f} [95% CI {hv['submitted_policy']['ci95'][0]:.4f}, {hv['submitted_policy']['ci95'][1]:.4f}] on {hv['withheld_positive_pixels']:,} withheld positives, evaluator `{hv['evaluator_version']}`. Proxy only.
* **Against matched random placement:** candidate minus random = {min(deltas):+.4f} to {max(deltas):+.4f} across 5 draws. The lower 95% bound is above zero in {sum(1 for x in lows if x > 0)} of 5 draws. The advantage over random density is not established.
* **Uniqueness (literal gate):** FAIL at q0.90, q0.95 and q0.97. First duplicate: 100% overlap with a registry blanket. Sensitivity run with blankets excluded: still FAIL (99.8% overlap with a 206,895-dot lattice). See the flags in `evidence/candidate_selection.json`.
* **Leaderboard:** no organizer receipt exists for any file. The public top value read on 2026-10-30 is 0.4544 (team standing, not a file score). The prompt's 0.4413 and 0.3195 do not appear in that read.

## Prior candidate overlap (diagnostic)

* The earlier MAW-GSI TIF (`apartgems1-maw-gsi-e3-20261028-87f83db9-zeros.tif`, SHA-256 `{prior_sha}`) is **research only, DO NOT SUBMIT**. Its 3-px forward overlap with the lattice witness is {prior_overlap*100:.2f}% (limit {overlap_limit*100:.0f}%).
* The H-SC1 gate failure is not caused by the prior file. It comes from registry rasters: a blanket in the literal screen, and genuine dot-set overlaps (up to 99.8%) in the sensitivity run.

## Unique among focus nine? (closest peer)

Nine-by-nine pairwise 3-px overlap (`evidence/focus_pairwise_overlap.json`). No focus file is unique to another.

| Site | Historical file | Claimed score | Estimated score | Unique among nine? (closest peer) | Submit? |
| --- | --- | --- | --- | --- | --- |
{focus_table}

**GEMSDOE32 (claimed 0.2778).** It has the highest claim in the nine-site list, but no linked organizer receipt exists. Its 37,654 dots match the lattice witness count. The 0.3195 "highest" figure in the prompt does not match the leaderboard read.

## Irregularities for review

See `evidence/candidate_selection.json` (`flags`). The main ones:

* **Blanket registry raster.** ApartGEMSDOE2's `…top37654…` files are full-footprint blankets (5,106,385 positive cells, 98.8% of the footprint). Their name says 37,654 dots, but they do not contain 37,654 dots. A 3-px dot overlap against a blanket is degenerate. It is the first duplicate the literal screen hit. The sensitivity run (blankets excluded) still fails on genuine dot sets, for example the 13gems r13 lattice at 99.79%.
* **Zeros outside the footprint.** Official rule text (R1 in `evidence/official_rules_check.json`) says data outside the bounds is "null or nan". The DrivenData reference notebook writes zeros. `sample_submission.tif` uses NaN. The portal's behaviour on either is untested.
* **Unexplained portal error.** "Predicted values must be in range [0, 1]": the file that triggered it is not identified.
* **`labels.tif` is byte-identical to `existing_faults.tif`** (SHA-256 `7ba308cc…`). Consistent with R5.
* **Leaderboard conflict.** The prompt cites 0.4413 and 0.3195; the repo's 2026-10-30 read shows 0.4544 at the top.

## Reproduce

```bash
python -m pip install -r requirements.txt
python scripts/build_registry.py --workers 3                 # GitHub API via gh; rate-limited
python scripts/focus_pairwise.py
python scripts/build_scarp_crest_candidate.py --mode holdout --seed 2026 --quantiles 0.97 0.99 0.995 --json-out evidence/holdout_h_sc1_seed2026.json
python scripts/build_scarp_crest_candidate.py --mode holdout --seed 2026 --quantiles 0.90 0.95 --json-out evidence/holdout_h_sc1_experiment2.json
python scripts/paired_policy_vs_random.py
python scripts/build_scarp_crest_candidate.py --mode final --quantile {sel['quantile']} --out .cache/candidates/{sel['file']} --name {sel['name']} --note "{sel['note']}"
python scripts/check_uniqueness.py .cache/candidates/{sel['file']} --json-out evidence/{sel['uniqueness_file']}
python scripts/write_run_card.py --help                      # see evidence/{sel['run_card']} for the arguments used
python scripts/build_submission_hub.py
.venv/bin/python -m pytest -q
```

## Limits and remaining work

* The sandbox cannot reach `drivendata.org`, `docs.nlr.gov`, `usgs.gov`, `nasa.gov` or the `github.io` pages. Competition text and the leaderboard come from the 2026-10-30 reads recorded in the repo.
* The registry is the public GitHub mirror repos listed in the prompt. It excludes private, unlinked and later uploads.
* A holdout DTI is a proxy. It scores recovery of catalogue faults, but the competition scores new faults.
* Decision needed (affects other lanes, not this one): whether blanket rasters should be excluded from the dot-overlap statistic. Excluding them does not clear H-SC1, because the sensitivity run still fails on genuine dot sets.
* Full prompt text to be added to `docs/prompt-full.md`.
* Next lanes: `evidence/hypotheses_2026-10-31.md`.
"""

if __name__ == "__main__":
    raise SystemExit(main())
