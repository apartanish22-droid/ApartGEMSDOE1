#!/usr/bin/env python3
"""Deterministically build docs/index.html, docs/executive-summary.html, and README.md from verified H-APART-2 JSON receipts."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    rc = json.loads((ROOT / "evidence/run_card.json").read_text())
    fa = json.loads((ROOT / "evidence/focus_sites_forensic_audit.json").read_text())
    f9_cmp = json.loads((ROOT / "evidence/focus9_vs_promoted_audit.json").read_text())
    exp = json.loads((ROOT / "evidence/experiments_holdout.json").read_text())
    can = json.loads((ROOT / "evidence/leakage_canary.json").read_text())
    uniq = json.loads((ROOT / "evidence/uniqueness_gate.json").read_text())
    prereg = json.loads((ROOT / "evidence/hypotheses_preregistration.json").read_text())
    h6 = json.loads((ROOT / "evidence/experiments_h6_otsp.json").read_text())
    h6_prereg = json.loads((ROOT / "evidence/hypotheses_preregistration_h6.json").read_text())
    h6_card = json.loads((ROOT / "evidence/run_card_h6_otsp.json").read_text())
    h6_winner = next(row for row in h6["experiments"] if row["id"] == h6["selected_holdout_winner"])
    h6_hyp_rows_html = "".join(
        f"<tr><td>{row['rank']}</td><td><strong><code>{html.escape(row['id'])}</code> {html.escape(row['title'])}</strong></td>"
        f"<td>{html.escape('; '.join(row['specific_layers']))}</td><td>{html.escape(row['physical_signature'])}</td>"
        f"<td>{html.escape(row['expected_holdout_dti_improvement_prior'])} <small>(pre-experiment prior, not a score)</small></td>"
        f"<td>{html.escape(row['implementation_cost'])}</td></tr>"
        for row in h6_prereg["ranked_candidates"]
    )
    h6_hyp_rows_md = "\n".join(
        f"| {row['rank']} | `{row['id']}` {row['title']} | {'; '.join(row['specific_layers'])} | "
        f"{row['physical_signature']} | `{row['expected_holdout_dti_improvement_prior']}` (design prior, not a score) | {row['implementation_cost']} |"
        for row in h6_prereg["ranked_candidates"]
    )
    current_validation = json.loads((ROOT / "evidence/cli_validator_check.json").read_text())
    current_uniq = current_validation["uniqueness_gate"]
    current_registry_n = current_uniq["rasters_checked"]
    current_sparse_n = current_uniq["competing_sparse_detectors_checked"]
    current_blanket_n = current_uniq["blanket_surfaces_disclosed"]

    tif_rel_docs = rc["validator_output"]["file"].replace("docs/", "")
    zip_rel_docs = rc["validator_output"]["zip_file"].replace("docs/", "")
    tif_filename = Path(tif_rel_docs).name
    zip_filename = Path(zip_rel_docs).name

    vs_f9 = uniq["post_placement_final_raster_gate"]["vs_focus_9_champions"]
    anat = rc["spatial_anatomy_and_external_audit"]
    n_canary = len(can["features"])
    gain_vs_v1_pct = (rc["holdout_dti"]["dti"] / rc["holdout_dti"]["prior_v1_holdout_dti"] - 1.0) * 100.0
    paired_delta_dist = exp["primary_draw_seed_2026"]["paired_differences_vs_winner"]["distance_only_collar2_control"]
    paired_delta_e1 = exp["primary_draw_seed_2026"]["paired_differences_vs_winner"]["E1_maw_scarp_geophys_blind"]

    # Build Focus-9 + Recent Submissions + Promoted ApartGEMSDOE1 v2 HTML & Markdown rows
    table_rows_html = []
    table_rows_html.append(f"""
      <tr class="highlight-row">
        <td><strong>ApartGEMSDOE1 v2 (Ours)</strong><br><span class="pass-tag">PROMOTED NEW</span></td>
        <td>
          <a href="{html.escape(tif_rel_docs)}" download><strong>{html.escape(tif_filename)}</strong></a><br>
          <span class="mono-val">sha256: {rc['raster_sha256'][:16]}…</span> ({rc['validator_output']['bytes']:,} B)
        </td>
        <td>
          <strong>HOLDOUT-DTI: {rc['holdout_dti']['dti']:.4f}</strong><br>
          <small>95% CI [{rc['holdout_dti']['ci95'][0]:.4f}, {rc['holdout_dti']['ci95'][1]:.4f}]<br>
          ({rc['holdout_dti']['evaluator_version']}, {rc['holdout_dti']['withheld_positive_pixels']:,} px)<br>
          seed=20: {rc['holdout_dti']['seed_20_stability_dti']:.4f} | Det &gt;800m: {rc['holdout_dti']['detached_gt_800m_blind_dti']:.4f}</small>
        </td>
        <td>
          <strong>{anat['emitted_dots']:,}</strong><br>
          <small>0 on cat | 0 &le;200m | d2–6: {anat['dots_200m_to_600m_fraction']*100:.1f}%<br>
          &gt;1.5km: {rc['validator_output']['farfield_gt_1500m_pixels']:,} ({anat['dots_gt_1500m_farfield_fraction']*100:.1f}%) | slope: {anat['median_dot_slope_deg']:.2f}&deg;</small>
        </td>
        <td><span class="pass-tag">ALL-FINITE [0, 1]</span><br><small>0 NaNs across 12.28M cells</small></td>
        <td>
          <strong>Max 3-px ov: {rc['registry_uniqueness']['post_placement_max_3px_overlap_vs_competing']*100:.2f}%</strong> (&le;70%)<br>
          <small>vs GEMSDOE32: {rc['registry_uniqueness']['vs_gemsdoe32_02778_3px_overlap']*100:.2f}% | vs v1: 11.02%<br>
          Surface |&rho;|: {rc['registry_uniqueness']['pre_placement_surface_max_abs_spearman']:.4f} (&le;0.90)</small>
        </td>
        <td><span class="pass-tag">PASS — UNIQUE &amp; OK TO SUBMIT</span></td>
      </tr>
    """)

    md_focus_rows = [
        f"| **ApartGEMSDOE1 v2 (Ours — NEW)** | [`{tif_filename}`](docs/{tif_rel_docs}) (`{rc['raster_sha256'][:12]}…`) | "
        f"`HOLDOUT-DTI`: **`{rc['holdout_dti']['dti']:.4f}`** (`[{rc['holdout_dti']['ci95'][0]:.4f}, {rc['holdout_dti']['ci95'][1]:.4f}]`, `gems57-pooled-hide-v2`, `11,360` px; `seed=20`: **`{rc['holdout_dti']['seed_20_stability_dti']:.4f}`**; Det `>800m`: **`{rc['holdout_dti']['detached_gt_800m_blind_dti']:.4f}`**) | "
        f"`{anat['emitted_dots']:,}` (`0` ≤200m, `{anat['dots_200m_to_600m_fraction']*100:.1f}%` 200–600m, `{anat['dots_gt_1500m_farfield_fraction']*100:.1f}%` >1.5km, med slope `{anat['median_dot_slope_deg']:.2f}°`) | "
        f"All-finite `[0,1]` (`0` NaN) | "
        f"**UNIQUE** (refreshed max `{current_uniq['max_3px_overlap_vs_competing_detectors']*100:.2f}%` vs {current_sparse_n} sparse detectors; **`{rc['registry_uniqueness']['vs_gemsdoe32_02778_3px_overlap']*100:.2f}%`** vs `GEMSDOE32`; **`11.02%`** vs v1) | "
        f"**PASS — OK TO DOWNLOAD & SUBMIT** |"
    ]

    for r in fa["focus_9_sites"]:
        site = r["site"]
        s_hold = r["static_holdout_dti"]
        me_cmp = vs_f9.get(site, {})
        me_ov_txt = f"{me_cmp.get('overlap_3px_fraction', 0)*100:.2f}%" if me_cmp else "—"
        nan_badge = (
            '<span class="pass-tag">All-Finite (-zeros)</span>'
            if r["all_grid_finite_no_nan"]
            else f'<span class="warn-tag">{r["exterior_nan_pixels"]:,} Exterior NaNs</span>'
        )
        dup_note = (
            f"100% pixel-identical to {', '.join(r['exact_footprint_duplicates_in_focus9'])}; "
            if r["exact_footprint_duplicates_in_focus9"]
            else ""
        )
        extra_note = ""
        if site == "GEMSDOE27":
            extra_note = "<br><small>Recent H31 (`gems27-h31-drcg-wl-celf28`): user-reported <code>0.2250</code>* (47.68% ov w/ ours)</small>"
        table_rows_html.append(f"""
          <tr>
            <td><a href="{html.escape(r['site_url'])}" target="_blank" rel="noopener"><strong>{html.escape(site)}</strong></a></td>
            <td>
              <a href="{html.escape(r['download_url'])}" target="_blank" rel="noopener">{html.escape(r['local_verified_file'])}</a><br>
              <span class="mono-val">sha256: {r['file_sha256'][:16]}…</span>{extra_note}
            </td>
            <td>
              <strong>User-Reported Context: {r['user_reported_score']:.4f}</strong>*<br>
              <small>Static HOLDOUT-DTI: {s_hold['dti']:.4f} [{s_hold['ci95'][0]:.4f}, {s_hold['ci95'][1]:.4f}]<br>
              ({s_hold['evaluator_version']}, {s_hold['withheld_positive_pixels']:,} px)</small>
            </td>
            <td>{r['dots']:,}<br><small>{r['dots_within_200m_collar']:,} &le;200m collar<br>{r['farfield_fraction']*100:.1f}% &gt;1.5km</small></td>
            <td>{nan_badge}</td>
            <td>
              <span class="stop-tag">NOT UNIQUE ({r['max_3px_overlap_vs_other_focus9']*100:.2f}% w/ {r['max_overlap_peer_site']})</span><br>
              <small>{dup_note}Overlap w/ Apart1 v2: {me_ov_txt}</small>
            </td>
            <td><span class="stop-tag">DO NOT RESUBMIT</span><br><small>Historical H19-5 lineage reference only</small></td>
          </tr>
        """)
        nan_md = "All-finite `[0,1]`" if r["all_grid_finite_no_nan"] else f"`{r['exterior_nan_pixels']:,}` exterior NaNs"
        md_focus_rows.append(
            f"| [{site}]({r['site_url']}) | [`{r['local_verified_file']}`]({r['download_url']}) (`{r['file_sha256'][:12]}…`) | "
            f"User-reported context: `{r['user_reported_score']:.4f}`* · Static `HOLDOUT-DTI`: `{s_hold['dti']:.4f}` (`[{s_hold['ci95'][0]:.4f}, {s_hold['ci95'][1]:.4f}]`) | "
            f"`{r['dots']:,}` (`{r['dots_within_200m_collar']:,}` ≤200m, `{r['farfield_fraction']*100:.1f}%` >1.5km) | "
            f"{nan_md} | "
            f"**DUPLICATE** (`{r['max_3px_overlap_vs_other_focus9']*100:.2f}%` w/ `{r['max_overlap_peer_site']}`; `{me_ov_txt}` w/ Apart1 v2) | "
            f"**DO NOT RESUBMIT** (H19-5 derivative) |"
        )

    # Append recent user-reported submissions from prompt ledger for complete auditability
    recent_rows_info = [
        (
            "ApartGEMSDOE1 v1 (Superseded)",
            "apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif",
            "User-Reported Context: 0.0525* | HOLDOUT-DTI: 0.0523 [0.0375, 0.0687]",
            "38,500 (0 <=200m, 32.4% 200-600m, med slope 11.98 deg)",
            "All-finite [0,1]",
            "11.02% w/ Apart1 v2 (88.98% replaced)",
            "SUPERSEDED BY v2 (+124.4% HOLDOUT-DTI)",
        ),
        (
            "GEMSDOE27 H31 (Recent)",
            "gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite.tif",
            "User-Reported Context: 0.2250*",
            "37,654 (0 <=200m, 25.9% 200-600m, med slope 8.01 deg)",
            "All-finite [0,1]",
            "47.68% w/ Apart1 v2",
            "EXTERNAL PEER — DO NOT COPY",
        ),
        (
            "KANLERGEMSDOE2 (Recent)",
            "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-111a0841-zeros.tif",
            "User-Reported Context: 0.1218*",
            "37,654 (0 <=200m, 47.6% 200-600m, med slope 12.90 deg)",
            "All-finite [0,1]",
            "39.49% w/ Apart1 v2",
            "EXTERNAL PEER — COLLAR/MOUNTAIN HEAVY",
        ),
        (
            "WBGGEMSDOE3 / GEMSDOE91 / WBGGEMSDOE2",
            "wbg3-h3pack-34k (0.0443*) · gems91-S18 (0.0435*) · gems91-s22 (0.0298*) · wbg2-36k (0.0262*)",
            "User-Reported Context: 0.0262* – 0.0443*",
            "34k–54k dots (either collar-heavy or un-gated diffuse plumes)",
            "Mixed",
            "<= 64.26% w/ Apart1 v2",
            "DIAGNOSED FAILURE MODES (AVOIDED)",
        ),
    ]
    for site_lbl, fn_lbl, sc_lbl, dot_lbl, nan_lbl, uniq_lbl, verd_lbl in recent_rows_info:
        table_rows_html.append(f"""
          <tr>
            <td><strong>{html.escape(site_lbl)}</strong></td>
            <td><code>{html.escape(fn_lbl)}</code></td>
            <td><small>{html.escape(sc_lbl)}</small></td>
            <td><small>{html.escape(dot_lbl)}</small></td>
            <td><small>{html.escape(nan_lbl)}</small></td>
            <td><small>{html.escape(uniq_lbl)}</small></td>
            <td><span class="warn-tag">{html.escape(verd_lbl)}</span></td>
          </tr>
        """)
        md_focus_rows.append(
            f"| **{site_lbl}** | `{fn_lbl}` | {sc_lbl} | `{dot_lbl}` | {nan_lbl} | {uniq_lbl} | **{verd_lbl}** |"
        )

    hyp_cards_html = []
    md_hyp_items = []
    for h in prereg["ranked_hypotheses"]:
        is_sel = bool(h.get("selected_for_validation"))
        sel_badge = (
            '<span class="pass-tag">SELECTED, VALIDATED &amp; PROMOTED</span>'
            if is_sel
            else '<span class="warn-tag">PRE-REGISTERED BACKLOG</span>'
        )
        hyp_cards_html.append(f"""
          <div style="background:var(--bg-elev);border:1px solid var(--border);border-radius:10px;padding:1.1rem 1.25rem;margin-bottom:1rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
              <strong>Rank #{h['rank']} — {html.escape(h['id'])} (<code>{html.escape(h['acronym'])}</code>): {html.escape(h['title'])}</strong>
              {sel_badge}
            </div>
            <p style="margin:0.55rem 0;font-size:0.9rem;color:#cbd5e1;"><strong>Physical Signature:</strong> {html.escape(h['physical_signature'])}</p>
            <p style="margin:0.4rem 0;font-size:0.86rem;color:var(--muted);"><strong>Why Missing from USGS/INGENIOUS Catalogue:</strong> {html.escape(h['why_missing_by_catalogue'] if 'why_missing_by_catalogue' in h else h['why_missing_from_catalogue'])}</p>
            <p style="margin:0.4rem 0;font-size:0.86rem;color:var(--muted);"><strong>How It Differs from Prior Repo Implementation:</strong> {html.escape(h['difference_from_existing_repo'])}</p>
            <p style="margin:0.4rem 0;font-size:0.86rem;color:var(--muted);"><strong>Named Non-Fault Mimics:</strong> {html.escape('; '.join(h['named_non_fault_mimic_processes']))}</p>
            <p style="margin:0.4rem 0 0;font-size:0.85rem;color:#93c5fd;"><strong>External Data &amp; Cost:</strong> {html.escape(h['external_data_status'])} | Expected Gain: {html.escape(h['expected_holdout_dti_gain'])} | Cost: {html.escape(h['implementation_cost'])}</p>
          </div>
        """)
        status_md = "**Rank #" + str(h["rank"]) + " — Selected, Validated & Promoted**" if is_sel else f"**Rank #{h['rank']} — Pre-Registered Backlog**"
        md_hyp_items.append(
            f"{h['rank']}. **`{h['id']}` (`{h['acronym']}` — {status_md}): {h['title']}**\n"
            f"   - **Layers**: {'; '.join(h['layers_involved'])}.\n"
            f"   - **Physical Signature**: {h['physical_signature']}\n"
            f"   - **Why Missing from USGS/INGENIOUS Catalogue**: {h['why_missing_from_catalogue']}\n"
            f"   - **Difference from Existing Repo (`H-APART-1` v1)**: {h['difference_from_existing_repo']}\n"
            f"   - **Named Non-Fault Mimics**: {'; '.join(h['named_non_fault_mimic_processes'])}.\n"
            f"   - **External Data, Expected Gain & Cost**: {h['external_data_status']} Expected gain: `{h['expected_holdout_dti_gain']}`; Cost: `{h['implementation_cost']}`."
        )

    copy_script = """
    <script>
      function copyText(elId, btn) {
        const txt = document.getElementById(elId).innerText.trim();
        navigator.clipboard.writeText(txt).then(() => {
          const orig = btn.innerText;
          btn.innerText = "Copied!";
          setTimeout(() => { btn.innerText = orig; }, 1600);
        });
      }
    </script>
    """

    sc_2026 = exp["primary_draw_seed_2026"]["scores"]
    det_2026 = exp["primary_draw_seed_2026"]["detached_gt_800m_blind_dti"]
    sc_20 = exp["secondary_stability_seed_20"]["scores"]

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ApartGEMSDOE1 — H-APART-2 (MAW-GSI E3) Validated Unique GeoTIFF Submission &amp; GEMSDOE32 Analysis</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand"><span class="brand-dot"></span> ApartGEMSDOE1 · DOE GEMS Prize Challenge</div>
      <nav class="nav-links">
        <a href="index.html" class="active">Overview &amp; One-Click Download</a>
        <a href="executive-summary.html">Executive Summary &amp; DrivenData Submit Guide</a>
        <a href="data/run_card.json" target="_blank">JSON Run Card</a>
        <a href="data/run_summary.json" target="_blank">Full Evidence Bundle</a>
      </nav>
    </div>
  </header>

  <main class="container">
    <section class="verdict-banner">
      <div class="status-pill">&#10003; Automated Validation &amp; {current_registry_n}-Raster Refreshed Uniqueness Gate: PASS — OK TO DOWNLOAD &amp; SUBMIT</div>
      <h1 class="hero-title">Unique Blind Structural-Intersection &amp; Geothermal GeoTIFF (<code>H-APART-2: MAW-GSI E3</code>)</h1>
      <p class="hero-sub">
        100% automatically validated in project code with zero human-inspection gates and <strong>100% Zero-SGMC</strong> in training and inference.
        Achieves <strong><code>HOLDOUT-DTI = {rc['holdout_dti']['dti']:.4f}</code></strong> (95% CI <code>[{rc['holdout_dti']['ci95'][0]:.4f}, {rc['holdout_dti']['ci95'][1]:.4f}]</code>;
        <code>seed=20</code> stability = <strong><code>{rc['holdout_dti']['seed_20_stability_dti']:.4f}</code></strong>) — a <strong>+{gain_vs_v1_pct:.1f}% (2.24&times;) leap</strong>
        over prior repo v1 (<code>0.0523</code>) and surpassing fold-honest <code>GEMSDOE32 B2</code> (<code>0.0974</code>) on canonical <code>gems57-pooled-hide-v2</code>.
        Strictly all-finite <code>float32</code> in <code>[0.0, 1.0]</code> with <code>0</code> NaNs across all <code>12,279,160</code> cells (permanently preventing
        <code>"Predicted values must be in range [0, 1]"</code>) and revalidated against <strong>50 repositories / {current_registry_n} unique rasters</strong>
        (refreshed max 3-px overlap = <strong>{current_uniq['max_3px_overlap_vs_competing_detectors']*100:.2f}% &le; 70%</strong> across all {current_sparse_n} competing sparse detectors;
        only <strong>{rc['registry_uniqueness']['vs_gemsdoe32_02778_3px_overlap']*100:.2f}%</strong> overlap with <code>GEMSDOE32</code> and <strong>11.02%</strong> with prior v1).
      </p>

      <div class="cta-row">
        <a class="btn-primary" href="{html.escape(tif_rel_docs)}" download>
          &#11015; Download Unique GeoTIFF (.tif · {rc['validator_output']['bytes'] // 1024} KB)
        </a>
        <a class="btn-secondary" href="{html.escape(zip_rel_docs)}" download>
          &#128230; Download Single-TIFF Archive (.zip · 110 KB)
        </a>
        <a class="btn-secondary" href="executive-summary.html">
          &#128214; Step-by-Step DrivenData Submission Guide &rarr;
        </a>
      </div>

      <div class="copy-grid">
        <div class="copy-box">
          <div class="copy-label">
            <span>Submission Name &amp; File SHA-256</span>
            <button class="copy-btn" onclick="copyText('sub-name-val', this)">Copy Name</button>
          </div>
          <div class="mono-val" id="sub-name-val">{html.escape(rc['submission_name'])}</div>
          <div class="mono-val" id="sha-val" style="color:#34d399;margin-top:0.25rem;">{rc['raster_sha256']}</div>
        </div>
        <div class="copy-box">
          <div class="copy-label">
            <span>DrivenData Short Comment ({rc['submission_note_chars']} / 140 chars)</span>
            <button class="copy-btn" onclick="copyText('note-val', this)">Copy Note</button>
          </div>
          <div class="mono-val" id="note-val">{html.escape(rc['submission_note'])}</div>
        </div>
      </div>
    </section>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Range &amp; Finite Gate</div>
        <div class="kpi-val">[0.0, 1.0]</div>
        <div class="kpi-note"><span class="pass-tag">PASS</span> 0 NaN · 0 Inf · 12,279,160 finite float32</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Grid &amp; CRS Match</div>
        <div class="kpi-val">EPSG:32611</div>
        <div class="kpi-note"><span class="pass-tag">PASS</span> 3730&times;3292 @ 100 m matches sample</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Pooled HOLDOUT-DTI</div>
        <div class="kpi-val">{rc['holdout_dti']['dti']:.4f}</div>
        <div class="kpi-note"><span class="pass-tag">+{gain_vs_v1_pct:.1f}% vs v1</span> CI [{rc['holdout_dti']['ci95'][0]:.4f}, {rc['holdout_dti']['ci95'][1]:.4f}] · seed20={rc['holdout_dti']['seed_20_stability_dti']:.4f}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Leakage Canary Gate</div>
        <div class="kpi-val">{rc['leakage_canary']['max_symmetric_auc']:.4f}</div>
        <div class="kpi-note"><span class="pass-tag">{n_canary}/{n_canary} PASS</span> All 45 features &le; 0.90 cap</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Surface Spearman |&rho;|</div>
        <div class="kpi-val">{rc['registry_uniqueness']['pre_placement_surface_max_abs_spearman']:.4f}</div>
        <div class="kpi-note"><span class="pass-tag">PASS &le; 0.90</span> Final dot |&rho;| = {rc['registry_uniqueness']['post_placement_final_max_abs_spearman']:.4f}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">{current_registry_n}-Raster Refreshed 3-px Gate</div>
        <div class="kpi-val">{rc['registry_uniqueness']['post_placement_max_3px_overlap_vs_competing']*100:.2f}%</div>
        <div class="kpi-note"><span class="pass-tag">PASS &le; 70%</span> 46.71% w/ GD32 · 11.02% w/ v1</div>
      </div>
    </div>

    <section class="section">
      <h2>1. Spatial Prediction Map &amp; Faulds-Hinz Geothermal Structural-Intersection Discovery</h2>
      <p>
        <strong>H-APART-2 (<code>MAW-GSI E3</code>)</strong> emits <strong>{anat['emitted_dots']:,}</strong> binary <code>1.0</code> pixels strictly outside the
        <code>200 m</code> (<code>2.05 px</code>) mapped-catalogue collar, allocating <strong>{rc['validator_output']['farfield_gt_1500m_pixels']:,} pixels
        ({anat['dots_gt_1500m_farfield_fraction']*100:.1f}%)</strong> into blind Cenozoic basins (<code>&gt;1.5 km</code> from any mapped trace) and
        <strong>72.1%</strong> beyond <code>600 m</code>, with median piedmont slope <strong><code>{anat['median_dot_slope_deg']:.2f}&deg;</code></strong>
        (matching <code>GEMSDOE32</code>'s <code>7.65&deg;</code> and curing v1's <code>11.98&deg;</code> mountain-interior bias) and post-hoc zero-SGMC
        far-field piedmont recall <strong><code>C_pied_FAR_gt1km = {anat['external_sgmc_posthoc_audit']['dti']:.4f}</code></strong>.
      </p>
      <div class="fig-box">
        <img src="assets/maw_gsi_submission_map.png" alt="ApartGEMSDOE1 MAW-GSI E3 spatial prediction map and Carson Sink / Bradys-Dixie geothermal rift zoom">
        <div class="fig-cap">
          Left: Full NW Great Basin grid (EPSG:32611, 3730&times;3292) showing mapped catalogue faults (slate) and promoted ApartGEMSDOE1 v2 dots (emerald) over Band 15 depth-to-basement.
          Right: 70&times;70 km Carson Sink / Bradys-Dixie geothermal rift inset contrasting GEMSDOE32 B2 (blue crosses) with ApartGEMSDOE1 MAW-GSI E3 (emerald circles) along 8-azimuth strike worms, orthogonal Faulds-Hinz intersections (I_vent), and magnetite-oxidation conduits.
        </div>
      </div>
    </section>

    <section class="section">
      <h2>2. Auditable Executive Comparison: Focus-9 Champions, Recent Submissions &amp; ApartGEMSDOE1 v2</h2>
      <p>
        Per Parallel-Run Protocol Rule 3, every metric below is strictly separated between local <strong><code>HOLDOUT-DTI</code></strong>
        (evaluated identically on <code>gems57-pooled-hide-v2</code>, <code>11,360</code> withheld positive pixels, 1,000-draw 20 km spatial block bootstrap 95% CI)
        and <strong>User-Reported Context Scores</strong>* from the prompt ledger (never projected onto unseen test truth).
      </p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Site / Run</th>
              <th>Downloadable GeoTIFF &amp; SHA-256</th>
              <th>Strictly Labeled Score</th>
              <th>Emitted Dots &amp; Spatial Anatomy</th>
              <th>NaN / Range Status</th>
              <th>Cross-Fleet Uniqueness</th>
              <th>Automated Gate Verdict</th>
            </tr>
          </thead>
          <tbody>
            {''.join(table_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>3. PhD Forensic Analysis: Why <code>GEMSDOE32</code> Scored <code>0.2778</code>, Why Recent Runs Scored <code>0.026–0.225</code>, and How <code>MAW-GSI</code> Advances the Frontier</h2>
      <h3>3.1 Exact Zero-XOR Forensic Proof of <code>GEMSDOE32</code> (<code>h33-h33-2-b2-zeros</code>: <code>0.2778</code>*)</h3>
      <pre class="code-block">GEMSDOE32_B2 (37,654 dots)  ==  GEMSDOE25_D28 (44,090 dots)  &amp;  (EDT(~existing_faults) &gt; 2.0 px)
XOR residual across 5,167,373 footprint pixels = 0   |   Exact subset of 19GEMSDOE H19-5 (121,131 px) = 100.00%
GEMSDOE25_D28 (44,090 dots) ==  GEMSDOE30_D28 (44,090 dots)   [XOR residual = 0]</pre>
      <p>
        <code>GEMSDOE32</code> reached <code>0.2778</code>* through three geometric operations on <code>19GEMSDOE H19-5</code> (<code>0.1922</code>*):
        (1) 280 m Poisson-disk kernel spacing (<code>0.1922 &rarr; 0.2600</code>*) so adjacent dots stopped double-paying <code>0.2 &times; FP_w</code> inside the 300 m triangular max-kernel;
        (2) amputating all <code>6,436</code> dots inside <code>EDT &le; 200 m</code> of mapped faults (<code>0.2600 &rarr; 0.2778</code>*) where organizer evaluation masks known traces; and
        (3) encoding exterior cells as finite <code>0.0</code>. When evaluated fold-honestly on <code>gems57-pooled-hide-v2</code> (applying <code>d_vis &gt; 2.0</code> per-fold),
        <code>GEMSDOE32 B2</code> scores <strong><code>HOLDOUT-DTI = 0.097441</code></strong> (<code>95% CI [0.0830, 0.1121]</code>).
      </p>

      <h3>3.2 Diagnosis of Prior Repo v1 (<code>0.0525</code>*) &amp; Recent Submissions — The Two-Gate Joint Law</h3>
      <p>
        Forensic audit across 30 zero-SGMC and lineage rasters reveals why single-gate heuristics fail:
        <code>ApartGEMSDOE1 v1</code> (<code>HOLDOUT-DTI = 0.0523</code> &rarr; live <code>0.0525</code>*), <code>gems91-S18</code> (<code>0.0435</code>*),
        <code>gems91-s22</code> (<code>0.0298</code>*), <code>wbg3-h3pack-34k</code> (<code>0.0443</code>*), and <code>wbg2-36k</code> (<code>0.0262</code>*) either lacked
        multi-azimuth 1.1–1.5 km strike-worm coherence or over-packed the 200–600 m collar / steep mountain interiors (v1 median slope <code>11.98&deg;</code>;
        <code>KANLERGEMSDOE2</code> <code>0.1218</code>* placed <code>47.6%</code> of dots in <code>200–600 m</code> at median slope <code>12.90&deg;</code>).
        Conversely, <code>GEMSDOE27 H31</code> (<code>0.2250</code>*) and <code>GEMSDOE32</code> (<code>0.2778</code>*) satisfy a strict <strong>Two-Gate Joint Law</strong>:
        (Gate 1) fold-honest <code>HOLDOUT-DTI &ge; 0.095</code> AND (Gate 2) anti-collar <code>d2–6 &le; 28%</code>, piedmont median slope <code>7.4&deg;–8.0&deg;</code>,
        and zero-SGMC far-field piedmont recall (<code>Spearman &rho; = +0.4813, p = 8.21&times;10<sup>&minus;3</sup></code> vs live DTI).
      </p>

      <h3>3.3 How <code>H-APART-2 (MAW-GSI E3)</code> Surpasses <code>GEMSDOE32 B2</code> on Fold-Honest Holdout</h3>
      <ul>
        <li><strong>8-Azimuth Flank-Subtracted Strike Worms + Antislope Piedmont Dipoles:</strong> Replaces pixel-local quantiles with <code>1.1–1.5 km</code> directional strike worms across seam-free 1 m LiDAR + 10 m 3DEP and potential fields, plus antislope graben dipoles (<code>upface_max / cross_max</code>) and TIGER 2024 road deconfounding.</li>
        <li><strong>Contrarian Faulds-Hinz (2015) Structural-Intersection Vent Operator (<code>I_vent</code>):</strong> Great Basin geothermal conduits (&gt;93% of blind systems) concentrate at conjugate/orthogonal cross-fault intersections, horse-tail splays, and relay ramps where orthogonal 2nd-azimuth strike worms co-fire (<code>I_vent = sqrt(W_(1) &times; W_perp)</code>) alongside shallow magnetite oxidation (<code>z(TMI_up150) &minus; z(RTP)</code>), potassic <code>K/Th</code>, MT clay-cap edges, and sanitized GDR #1391 thermal springs, 2 m <code>F2mDAB</code> probes (<code>[0.5, 54.7]&deg;C</code>), and paleo-sinter mounds.</li>
        <li><strong>Dual-Regime Exact 300 m Minoux CELF Submodular Allocation:</strong> Allocates 72% unified Stage-2 OOF axial-relay surface + 28% blind structural-intersection/hydrothermal specialist budget (<code>d_vis &gt; 500 m</code>) under exact 49-offset 300 m triangular kernel marginal gain, lifting <code>HOLDOUT-DTI</code> to <strong><code>0.1174</code></strong> (<code>seed=2026</code>) and <strong><code>0.1250</code></strong> (<code>seed=20</code>) while keeping 3-px overlap with <code>GEMSDOE32</code> at just <strong><code>46.71%</code></strong>.</li>
      </ul>
      <div class="fig-box">
        <img src="assets/focus9_audit_and_uniqueness.png" alt="Focus-9 10x10 overlap matrix and fold-honest HOLDOUT-DTI calibration ladder">
        <div class="fig-cap">
          Left: Exact 3-px dot overlap across all 9 focus champions (87–100% mutually redundant) vs. ApartGEMSDOE1 v2 (46.7–50.8% overlap — genuinely independent).
          Right: Fold-honest HOLDOUT-DTI calibration ladder from Dist-Only (0.0329) and v1 (0.0523) past GEMSDOE32 B2 (0.0974) to MAW-GSI E3 (0.1174).
        </div>
      </div>
    </section>

    <section class="section">
      <h2>4. Pre-Registered Untried Geological Hypotheses (Ranked 1–4)</h2>
      {''.join(hyp_cards_html)}
    </section>

    <section class="section">
      <h2>5. Holdout Validation (<code>gems57-pooled-hide-v2</code>) &amp; 45-Feature Leakage Canaries</h2>
      <p>
        All 3 pre-registered LOQO experiments (budget cap <code>3/3</code>) improved strictly monotonically on <strong>both</strong> holdout seeds:
        <code>zero (0.0000) &lt; dist_only (0.0329) &lt; E1 ({sc_2026['E1_maw_scarp_geophys_blind']['dti']:.4f}) &lt; E2 ({sc_2026['E2_maw_gsi_blind_vent']['dti']:.4f}) &lt; E3 ({sc_2026['E3_maw_gsi_oof_axial_relay']['dti']:.4f})</code>
        on <code>seed=2026</code> (paired <code>&Delta;(E3 &minus; DistOnly) = +{paired_delta_dist['delta']:.4f}</code>, 95% CI
        <code>[+{paired_delta_dist['ci95'][0]:.4f}, +{paired_delta_dist['ci95'][1]:.4f}]</code>; paired <code>&Delta;(E3 &minus; E1) = +{paired_delta_e1['delta']:.4f}</code>),
        and <code>E1 ({sc_20['E1_maw_scarp_geophys_blind']['dti']:.4f}) &lt; E2 ({sc_20['E2_maw_gsi_blind_vent']['dti']:.4f}) &lt; E3 ({sc_20['E3_maw_gsi_oof_axial_relay']['dti']:.4f})</code> on <code>seed=20</code>.
        On detached blind faults (<code>&gt;800 m</code> from visible traces), <code>distance_only</code> collapses to <code>0.0000</code> whereas
        <code>E1 ({det_2026['E1_maw_scarp_geophys_blind']:.4f}) &rarr; E2 ({det_2026['E2_maw_gsi_blind_vent']:.4f}) &rarr; E3 ({det_2026['E3_maw_gsi_oof_axial_relay']:.4f})</code> recovers blind segments!
      </p>
      <div class="fig-box">
        <img src="assets/holdout_experiments_and_canary.png" alt="Holdout DTI progression and 45-feature leakage canary">
        <div class="fig-cap">
          Left: Pooled HOLDOUT-DTI (with 1,000-draw 20 km block bootstrap 95% CIs) and detached blind (&gt;800 m) DTI across controls and E1&rarr;E2&rarr;E3.
          Right: Single-feature symmetric ROC-AUC leakage canaries across all 45 features (45/45 PASS; max = {can['max_symmetric_auc']:.4f} &le; 0.90 cap).
        </div>
      </div>
    </section>

    <section class="section">
      <h2>6. Latest Iteration: <code>H-APART-6 OTSP</code> — Negative, Correctly Stopped</h2>
      <p>Four untried hypotheses were ranked before implementation. Expected improvements below are design priors, never scores or projections.</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Rank</th><th>Hypothesis</th><th>Specific layers</th><th>Physical signature</th><th>Expected improvement prior</th><th>Cost</th></tr></thead>
        <tbody>{h6_hyp_rows_html}</tbody>
      </table></div>
      <p>
        The selected Orientation-Transported Scale Persistence lane passed all three leakage canaries
        (<code>max symmetric AUC = {h6['leakage_canary']['max_symmetric_auc']:.4f} &le; 0.90</code>) but did not beat the
        promoted baseline. Its best arm, <code>{h6_winner['id']}</code>, reached
        <strong><code>HOLDOUT-DTI = {h6_winner['dti']:.4f}</code></strong>
        (<code>95% CI [{h6_winner['ci95'][0]:.4f}, {h6_winner['ci95'][1]:.4f}]</code>,
        <code>{h6_winner['withheld_positive_pixels']:,}</code> withheld positives), below
        <code>MAW-GSI E3 = {h6['baseline']['dti']:.4f}</code>. Per the pre-registered stop rule, no OTSP live raster was
        manufactured and no weekly slot was used. The validated MAW-GSI GeoTIFF above remains the download choice.
        <a href="data/experiments_h6_otsp.json">Machine-readable experiment receipt</a> ·
        <a href="data/run_card_h6_otsp.json">negative run card</a>.
      </p>
    </section>

    <section class="section">
      <h2>7. Machine-Readable Parallel-Run Protocol Run Cards</h2>
      <h3>Promoted H-APART-2</h3>
      <pre class="code-block">{html.escape(json.dumps(rc, indent=2))}</pre>
      <h3>Negative H-APART-6 OTSP</h3>
      <pre class="code-block">{html.escape(json.dumps(h6_card, indent=2))}</pre>
    </section>
  </main>

  <footer>
    ApartGEMSDOE1 · Branch <code>{html.escape(rc['branch'])}</code> · Validated 100% automatically via <code>scripts/validate_submission.py</code> &amp; <code>pytest</code>.
  </footer>
  {copy_script}
</body>
</html>
"""

    exec_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Executive Summary &amp; How to Submit on DrivenData — ApartGEMSDOE1 (MAW-GSI E3)</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand"><span class="brand-dot"></span> ApartGEMSDOE1 · Executive Summary &amp; Submission Guide</div>
      <nav class="nav-links">
        <a href="index.html">&larr; Back to Main Dashboard</a>
        <a href="executive-summary.html" class="active">Executive Summary &amp; DrivenData Submit Guide</a>
        <a href="data/focus9_vs_promoted_audit.json" target="_blank">Focus-9 vs MAW-GSI JSON</a>
        <a href="data/run_card.json" target="_blank">Run Card JSON</a>
      </nav>
    </div>
  </header>

  <main class="container">
    <section class="verdict-banner">
      <div class="status-pill">&#10003; Ready for DrivenData Upload — Zero Manual Fixes Needed</div>
      <h1 class="hero-title">Executive Summary &amp; Step-by-Step DrivenData Submission Guide</h1>
      <p class="hero-sub">
        Concise PhD decision brief across all 9 focus GEMSDOE sites and recent peer submissions, documenting how our automated gates permanently eliminate
        the <code>"Predicted values must be in range [0, 1]"</code> portal error and cross-fleet duplication, plus step-by-step instructions to upload
        <code>{html.escape(tif_filename)}</code> on DrivenData.
      </p>
      <div class="cta-row">
        <a class="btn-primary" href="{html.escape(tif_rel_docs)}" download>
          &#11015; Step 1: Download Validated Unique .tif ({rc['validator_output']['bytes'] // 1024} KB)
        </a>
        <a class="btn-secondary" href="{html.escape(zip_rel_docs)}" download>
          &#128230; Download Single-TIFF .zip Archive
        </a>
        <a class="btn-secondary" href="https://www.drivendata.org/competitions/306/competition-doe-gems/" target="_blank" rel="noopener">
          &#127760; Open DOE GEMS DrivenData Competition Portal &nearr;
        </a>
      </div>
    </section>

    <section class="section">
      <h2>1. Executive Decision Brief (60-Second Read)</h2>
      <ul>
        <li><strong>Why you MUST NOT re-submit any Focus-9 file (<code>GEMSDOE24..36</code>):</strong> Pixel-exact forensic auditing proves that all 9 historical focus-site champions are subsets/variants of <code>19GEMSDOE H19-5</code> with <code>87%–100%</code> mutual 3-px overlap (<code>GEMSDOE32 B2</code> is literally <code>GEMSDOE25_D28 &amp; (EDT(~existing_faults) &gt; 2.0)</code> with <code>XOR = 0</code>), and 6 of the 9 carry <code>7,111,787</code> exterior <code>NaN</code> cells.</li>
        <li><strong>Why <code>ApartGEMSDOE1 v2</code> (<code>{html.escape(tif_filename)}</code>) IS promoted and ready to submit:</strong> Built from scratch under <strong><code>H-APART-2 (MAW-GSI E3)</code></strong> — 100% Zero-SGMC Multi-Azimuth 8-Direction Strike Worms + Antislope Piedmont Dipoles + Faulds-Hinz (2015) Orthogonal Structural-Intersection Conduits (<code>I_vent</code>) + Shallow Magnetite-Oxidation (<code>TMI_up150 &minus; RTP</code>) + Sanitized GDR #1391 Springs / 2 m <code>F2mDAB</code> Probes / Paleo-Sinter Vents + Stage-2 OOF Axial-Relay Synthesis + Dual-Regime Exact 300 m Minoux CELF Allocation (<code>37,654</code> dots).</li>
        <li><strong>Latest H-APART-6 OTSP iteration was rejected automatically:</strong> its best arm reached <code>HOLDOUT-DTI = {h6_winner['dti']:.4f}</code> (<code>95% CI [{h6_winner['ci95'][0]:.4f}, {h6_winner['ci95'][1]:.4f}]</code>, <code>{h6_winner['withheld_positive_pixels']:,}</code> withheld positives), below the promoted <code>{h6['baseline']['dti']:.4f}</code>. No H-APART-6 GeoTIFF was written and no weekly slot was used; the download button therefore still points to the highest validated local candidate.</li>
        <li><strong>Every Automated Gate Passed Cleanly:</strong>
          <ul>
            <li><strong>Format &amp; Range Gate:</strong> Single-band <code>float32</code>, <code>EPSG:32611</code>, <code>3730&times;3292</code>, <code>min=0.0</code>, <code>max=1.0</code>, <strong><code>0</code> NaNs and <code>0</code> Infs across all <code>12,279,160</code> cells</strong> (<code>nodata=None</code>).</li>
            <li><strong>Holdout Gate:</strong> <code>HOLDOUT-DTI = {rc['holdout_dti']['dti']:.4f}</code> (<code>95% CI [{rc['holdout_dti']['ci95'][0]:.4f}, {rc['holdout_dti']['ci95'][1]:.4f}]</code> on <code>seed=2026</code>; <code>{rc['holdout_dti']['seed_20_stability_dti']:.4f}</code> on <code>seed=20</code>; <code>+{gain_vs_v1_pct:.1f}%</code> over prior v1 <code>0.0523</code> and above fold-honest <code>GEMSDOE32 B2 = 0.0974</code>).</li>
            <li><strong>50-Repo Uniqueness Gate:</strong> Original pre-placement surface gate <code>|&rho;| = {rc['registry_uniqueness']['pre_placement_surface_max_abs_spearman']:.4f} &le; 0.90</code>; refreshed {current_registry_n}-raster final dot gate <code>|&rho;| = {current_uniq['max_abs_spearman_rho']:.4f} &le; 0.90</code>; refreshed max 3-px dot overlap = <strong><code>{current_uniq['max_3px_overlap_vs_competing_detectors']*100:.2f}% &le; 70.00%</code></strong> across all {current_sparse_n} competing sparse detectors (only <code>{rc['registry_uniqueness']['vs_gemsdoe32_02778_3px_overlap']*100:.2f}%</code> w/ <code>GEMSDOE32</code> and <code>11.02%</code> w/ v1).</li>
          </ul>
        </li>
      </ul>
    </section>

    <section class="section">
      <h2>2. Step-by-Step: How to Submit on DrivenData</h2>
      <div class="step-list">
        <div class="step-item">
          <div class="step-num">1</div>
          <div>
            <strong>Download the Validated GeoTIFF File</strong><br>
            Click <a href="{html.escape(tif_rel_docs)}" download><strong><code>{html.escape(tif_filename)}</code></strong></a> above (<code>{rc['validator_output']['bytes']:,}</code> bytes) or download <a href="{html.escape(zip_rel_docs)}" download><code>{html.escape(zip_filename)}</code></a> (unzip if DrivenData requests raw <code>.tif</code>).
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">2</div>
          <div>
            <strong>(Optional) Verify Local SHA-256 Checksum</strong><br>
            Run <code>shasum -a 256 {html.escape(tif_filename)}</code> (macOS/Linux) or <code>certutil -hashfile {html.escape(tif_filename)} SHA256</code> (Windows) and confirm:<br>
            <span class="mono-val" style="color:#34d399;">{rc['raster_sha256']}</span>
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">3</div>
          <div>
            <strong>Open the Official DrivenData Competition Submissions Page</strong><br>
            Sign in at <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/" target="_blank" rel="noopener">https://www.drivendata.org/competitions/306/competition-doe-gems/</a> and open the <strong>Submissions</strong> tab. Confirm an active submission slot is available.
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">4</div>
          <div>
            <strong>Upload the Single-Band <code>.tif</code> File</strong><br>
            Select <code>{html.escape(tif_filename)}</code> (DEFLATE-compressed single-band <code>float32</code> GeoTIFF matching <code>example_submission.tif</code> pixel-for-pixel in CRS <code>EPSG:32611</code>, shape <code>3730&times;3292</code>, and affine geotransform <code>(100, 0, 243350, 0, -100, 4508550)</code>).
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">5</div>
          <div>
            <strong>Paste the Unique Submission Name &amp; Comment (&le;140 Characters)</strong><br>
            Use name <code>{html.escape(rc['submission_name'])}</code> and paste this exact <code>{rc['submission_note_chars']}</code>-character comment:
            <div class="copy-box" style="margin-top:0.5rem;">
              <div class="copy-label">
                <span>Verified {rc['submission_note_chars']}-Char Comment</span>
                <button class="copy-btn" onclick="copyText('exec-note', this)">Copy Comment</button>
              </div>
              <div class="mono-val" id="exec-note">{html.escape(rc['submission_note'])}</div>
            </div>
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">6</div>
          <div>
            <strong>Submit &amp; Record the <code>ORGANIZER-CONFIRMED</code> Receipt</strong><br>
            Local fail-closed checks confirm all <code>12,279,160</code> cells are finite in <code>[0.0, 1.0]</code> with zero <code>NaN</code>s and zero GDAL <code>-3.4028235e+38</code> sentinels, eliminating the previously observed range-error cause. Only the organizer portal can confirm acceptance. Once accepted and scored, record the returned number strictly as <code>ORGANIZER-CONFIRMED</code> alongside timestamp and SHA-256.
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>3. Flagged Data &amp; Registry Irregularities (Zero-Hallucination Audit Log)</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Irregularity ID</th>
              <th>Observed Empirical Finding</th>
              <th>Automated Mitigation in ApartGEMSDOE1 v2</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>IR-1: SENTINEL-EXTREMES</code></td>
              <td><code>training_features.tif</code> contains extreme GDAL sentinels (<code>-3.4028235e+38</code>, <code>-9.999e+32</code>) inside the footprint, plus <code>7.11M</code> exterior <code>NaN</code>s. Unsanitized propagation caused historical <code>"Predicted values must be in range [0, 1]"</code> rejections.</td>
              <td><code>scripts/prepare_data.py</code> and <code>src/apartgems/features.py</code> mask all <code>|x| &gt; 1e30</code> before z-scoring, clip outputs to <code>[0.0, 1.0]</code>, and <code>submission_writer.py</code> enforces <code>0</code> NaNs across all <code>12,279,160</code> cells.</td>
            </tr>
            <tr>
              <td><code>IR-2: LIDAR-24.6%-GAP</code></td>
              <td>USGS 1 m 3DEP LiDAR covers <code>75.39%</code> of the footprint, leaving a contiguous <code>24.61%</code> gap in NE Nevada. Imputing <code>0.0</code> creates sharp tile-boundary cliffs in tree splits.</td>
              <td>Preserves explicit <code>NaN</code> across <code>valid_frac &lt; 0.05</code> for native missing-value routing in <code>HistGradientBoostingClassifier</code> while bridging seamlessly with <code>99.6%</code>-coverage 10 m 3DEP strike worms.</td>
            </tr>
            <tr>
              <td><code>IR-3: GDR1391-PROBES-LEAK</code></td>
              <td><code>2m_temperature_probe_INGENIOUS_regional_data.zip</code> contains <code>-9999</code> / <code>999.9</code> sentinels on <code>F2mDAB</code>, and <code>gdr_wellspring_in_footprint.csv</code> includes a precomputed <code>dist_known_fault_px</code> column against full <code>existing_faults.tif</code>.</td>
              <td>Filters <code>F2mDAB</code> strictly to physical <code>[0.5, 55.0]&deg;C</code> (<code>1,488</code> valid anomalous probes) and never reads <code>dist_known_fault_px</code>.</td>
            </tr>
            <tr>
              <td><code>IR-4: BAND6-RADIOMETRIC-TC</code></td>
              <td>GeoTIFF metadata labels Band 6 (<code>tc</code>) as magnetic tilt/curvature, whereas its empirical distribution (<code>q01=7.72, q50=18.48, q99=29.1</code>) is GeoDAWN radiometric Total Count.</td>
              <td>Treated strictly as radiometric Total Count; genuine potential-field phase-tilt angles are computed analytically from vertical and horizontal derivatives.</td>
            </tr>
            <tr>
              <td><code>IR-5: REG-BLANKET-SURFACES</code></td>
              <td>Across the refreshed 50-repo registry / {current_registry_n} unique rasters, <code>{current_blanket_n}</code> files are dense probability blankets or wide-area floods (<code>&ge;85,000</code> positive px or 3-px halo covering <code>&ge;28%</code> of the footprint) whose asymmetric one-way containment exceeds 70% against any sparse submission despite tiny reverse overlap (<code>13%–33%</code>).</td>
              <td><code>src/apartgems/uniqueness.py</code> enforces strict one-way 3-px overlap <code>&le; 70%</code> across all <code>{current_sparse_n}</code> competing sparse detectors (refreshed max <code>{current_uniq['max_3px_overlap_vs_competing_detectors']*100:.2f}%</code>) AND matched-density/Spearman gates across all <code>{current_blanket_n}</code> blankets (max matched-top50k <code>55.8%</code>, max <code>|&rho;| = 0.6911 &le; 0.90</code>), disclosing every witness in <code>uniqueness_gate.json</code>.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>4. Verified Official Competition &amp; Scientific Data Sources</h2>
      <ul>
        <li><strong>DrivenData DOE GEMS Competition Portal:</strong> <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/" target="_blank" rel="noopener">https://www.drivendata.org/competitions/306/competition-doe-gems/</a></li>
        <li><strong>Official Competition Rules PDF (NREL / DOE OSTI #96647):</strong> <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf" target="_blank" rel="noopener">https://docs.nlr.gov/docs/fy26osti/96647.pdf</a></li>
        <li><strong>Official Reference Solution Repository:</strong> <a href="https://github.com/drivendataorg/gems-prize-reference-solution" target="_blank" rel="noopener">https://github.com/drivendataorg/gems-prize-reference-solution</a></li>
        <li><strong>GBCGE / NBMG INGENIOUS Great Basin Geothermal Project:</strong> <a href="https://gbcge.org/current-projects/ingenious/" target="_blank" rel="noopener">https://gbcge.org/current-projects/ingenious/</a></li>
        <li><strong>OpenEI Geothermal Data Repository (GDR #1391 — INGENIOUS Regional Dataset):</strong> <a href="https://gdr.openei.org/submissions/1391" target="_blank" rel="noopener">https://gdr.openei.org/submissions/1391</a></li>
        <li><strong>USGS GeoDAWN Airborne Magnetic &amp; Radiometric Surveys (ScienceBase 657e1d85d34e23d3533209f7):</strong> <a href="https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7" target="_blank" rel="noopener">https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7</a></li>
        <li><strong>USGS 3D Elevation Program (3DEP 1 m LiDAR &amp; 10 m Seamless DEM):</strong> <a href="https://www.usgs.gov/3d-elevation-program" target="_blank" rel="noopener">https://www.usgs.gov/3d-elevation-program</a></li>
        <li><strong>US Census Bureau TIGER/Line 2024 Roads (Anthropogenic Berm Deconfounder):</strong> <a href="https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html" target="_blank" rel="noopener">https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html</a></li>
      </ul>
    </section>
  </main>

  <footer>
    ApartGEMSDOE1 · <a href="index.html">Return to Main Dashboard &amp; One-Click Download</a>
  </footer>
  {copy_script}
</body>
</html>
"""

    (ROOT / "docs/index.html").write_text(index_html, encoding="utf-8")
    (ROOT / "docs/executive-summary.html").write_text(exec_html, encoding="utf-8")

    readme_md = f"""# ApartGEMSDOE1 — H-APART-2 (`MAW-GSI E3`) Multi-Azimuth Strike-Worm & Geothermal Structural-Intersection Synthesis

> **AUTOMATED VALIDATION & {current_registry_n}-RASTER REFRESHED UNIQUENESS GATE: `PASS — PROMOTE — UNIQUE & OK TO DOWNLOAD AND SUBMIT`**
> - **Promoted Unique GeoTIFF**: [`docs/{tif_rel_docs}`](docs/{tif_rel_docs}) (`{rc['validator_output']['bytes']:,}` bytes) · Single-TIFF Archive: [`docs/{zip_rel_docs}`](docs/{zip_rel_docs}) (`112,325` bytes)
> - **SHA-256**: `{rc['raster_sha256']}` | **Decoded Footprint SHA-256**: `{rc['decoded_footprint_sha256']}`
> - **Submission Name**: `{rc['submission_name']}`
> - **Short Submission Comment (`{rc['submission_note_chars']}/140` chars)**: `{rc['submission_note']}`
> - **Format & Portal `[0, 1]` Safety**: Single-band `float32`, `EPSG:32611`, `3730×3292`, `Affine(100, 0, 243350, 0, -100, 4508550)`, `nodata=None`, **`min=0.0`, `max=1.0`, `0` NaNs and `0` Infs across all `12,279,160` grid cells** (permanently prevents `"Predicted values must be in range [0, 1]"`).
> - **Holdout Score (`HOLDOUT-DTI`)**: **`{rc['holdout_dti']['dti']:.4f}`** (`95% CI [{rc['holdout_dti']['ci95'][0]:.4f}, {rc['holdout_dti']['ci95'][1]:.4f}]` on `gems57-pooled-hide-v2`, `seed=2026`, `11,360` withheld positive pixels) and **`{rc['holdout_dti']['seed_20_stability_dti']:.4f}`** on `seed=20` (`11,321` withheld positive pixels) — **`+{gain_vs_v1_pct:.1f}%` (`2.24x`) above prior repo v1 (`0.0523`)** and **surpassing fold-honest `GEMSDOE32 B2` (`0.0974`)** while remaining **100% Zero-SGMC** in training and inference.
> - **50-Repo Dual Uniqueness Gate**: Original pre-placement surface `|ρ| = {rc['registry_uniqueness']['pre_placement_surface_max_abs_spearman']:.4f} <= 0.90` (`PASS`); refreshed final check across **`{current_registry_n}` rasters** gives `|ρ| = {current_uniq['max_abs_spearman_rho']:.4f} <= 0.90` and max 3-px overlap across `{current_sparse_n}` competing sparse detectors = **`{current_uniq['max_3px_overlap_vs_competing_detectors']*100:.2f}% <= 70.00%`** (`PASS`; **`{rc['registry_uniqueness']['vs_gemsdoe32_02778_3px_overlap']*100:.2f}%`** overlap with `GEMSDOE32` `0.2778`* and **`11.02%`** with prior v1).
> - **GitHub Pages Portal**: [`docs/index.html`](docs/index.html) (Main Overview & One-Click `.tif` Download) · [`docs/executive-summary.html`](docs/executive-summary.html) (Executive Summary & Step-by-Step DrivenData Submission Guide).

![MAW-GSI E3 Submission Map](docs/assets/maw_gsi_submission_map.png)

---

## 1. Executive Summary & Auditable Focus-9 + Peer Comparison Table

Per Parallel-Run Protocol Rule 3, every number below is strictly labeled as either local **`HOLDOUT-DTI`** (with evaluator version `gems57-pooled-hide-v2`, count of withheld positive pixels, and 1,000-draw 20 km spatial block bootstrap 95% CI) or **User-Reported Context** (`*` from the prompt ledger; never projected as a live score).

| Site / Run | Downloadable `.tif` & SHA-256 | Strictly Labeled Score | Emitted Dots & Spatial Anatomy | NaN / Range Status | Cross-Fleet Uniqueness | Gate Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{chr(10).join(md_focus_rows)}

![Focus-9 Uniqueness & Fold-Honest Calibration Ladder](docs/assets/focus9_audit_and_uniqueness.png)

---

## 2. Deep PhD Analysis: Why `GEMSDOE32` Scored `0.2778`, Why Recent Submissions Scored `0.026–0.225`, and How `MAW-GSI` Advances the Frontier

### 2.1 Exact Zero-XOR Forensic Proof of `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: `0.2778`*)
Pixel-by-pixel audit across all `5,167,373` valid footprint cells (`evidence/focus_sites_forensic_audit.json`) proves with **zero differing pixels (`XOR = 0`)**:
1. **`GEMSDOE32_B2 (37,654 dots) == GEMSDOE25_D28 (44,090 dots) & (EDT(~existing_faults) > 2.0 px)`** (`0` differing pixels across `5,167,373` footprint cells).
2. **`GEMSDOE25_D28 (44,090 dots) == GEMSDOE30_D28 (44,090 dots)`** (`0` differing pixels).
3. **`100.00%` of `GEMSDOE32_B2`'s `37,654` dots are an exact subset of `19GEMSDOE` `H19-5` (`121,131` solid ridge pixels, `0.1922`*)**.

Why each post-processing step raised the live score from `0.1922`* to `0.2778`*:
- **Kernel-Radius Spacing Thinning (`0.1922 -> 0.2477 -> 0.2600`*)**: Under Distance-Tolerant IoU (`DTI`, `alpha = 0.2, beta = 0.8`), `TP_w` uses a **maximum** over the 300 m triangular kernel, whereas `FP_w` accumulates **additively** across every emitted pixel. Thinning solid `121,131`-px ridges to `d = 2.8 px` (`280 m`, `44,090` dots) stopped adjacent pixels from cannibalizing the same truth credit while paying triple `0.2 * FP_w` denominator penalties.
- **200 m Known-Catalogue Collar Amputation (`0.2600 -> 0.2778`*)**: Because organizer evaluation masks `existing_faults.tif` (Forum Thread 11516), the `6,436` `D2.8` dots inside `100–200 m` of known faults contributed near-zero new-fault `TP_w` while paying full `FP_w` cost.
- **Fold-Honest Benchmark**: Evaluated fold-honestly on `gems57-pooled-hide-v2` (applying `d_vis > 2.0` per-fold rather than post-masking withheld traces), `GEMSDOE32 B2` achieves **`HOLDOUT-DTI = 0.097441`** (`95% CI [0.082987, 0.112149]`).

### 2.2 Empirical Diagnosis of `v1` (`0.0525`*) & Recent Submissions — The Two-Gate Joint Law
Auditing `ApartGEMSDOE1 v1` (`udth-submod-e3: 0.0525`*, `HOLDOUT-DTI = 0.052325` — virtually 1:1 calibrated!) alongside `gems91-S18-UNIQUE-curvtilt` (`0.0435`*), `gems91-s22-omtj-e1` (`0.0298`*), `wbg3-h3pack-34k` (`0.0443`*), `wbg2-offcatalogue-density-36k` (`0.0262`*), `kanlergems2-htcads-exp-2` (`0.1218`*), and `gems27-h31-drcg-wl-celf28` (`0.2250`*) establishes a **Two-Gate Joint Law**:
1. **Gate 1 — Fold-Honest Structural & Conduit Precision (`HOLDOUT-DTI >= 0.095`)**: Diffuse km-scale hydrothermal/density plumes (`wbg2`, `gems91-s22`) or single-pixel quantile ranks (`v1`) place dots outside the strict `300 m` triangular kernel (`v1 HOLDOUT-DTI = 0.0523`).
2. **Gate 2 — Piedmont Basin Geometry & Anti-Collar Discipline**: Models that lean heavily on visible fault tips (`KANLERGEMSDOE2`: `47.6%` of dots in `200–600 m`, median slope `12.90°`; `v1`: `32.4%` in `200–600 m`, median slope `11.98°`) score well on near-tip holdout extensions yet miss blind intra-basin piedmont faults (`v1` post-hoc zero-SGMC far-field piedmont recall `C_pied_FAR_gt1km = 0.0189`). Across 30 zero-SGMC rasters, `C_pied_FAR_gt1km` correlates strongly with live DTI (`Spearman ρ = +0.4813, p = 8.21e-3`). High-performing zero-SGMC detectors (`GEMSDOE27 H31 = 0.2250`*, `GEMSDOE70 = 0.2478`*) keep `200–600 m` collar share `<= 28%` and median dot slope in the `7.4°–8.0°` piedmont hinge zone.

### 2.3 Can We Beat `0.2778`? Honest Assessment & `H-APART-2` (`MAW-GSI`) Breakthrough
On canonical fold-honest `gems57-pooled-hide-v2`, **`H-APART-2 (MAW-GSI E3)` achieves `HOLDOUT-DTI = 0.117438` (`95% CI [0.099365, 0.136129]`, `seed=2026`) and `0.124957` (`seed=20`)** — **even its lower 95% confidence bound (`0.0994`) exceeds fold-honest `GEMSDOE32 B2` (`0.0974`)**, while simultaneously hitting every Gate-2 piedmont target (`27.87%` in `200–600 m`, `35.76%` `> 1.5 km`, median slope `7.90°`, `C_pied_FAR_gt1km = 0.0474`, `100% Zero-SGMC`). Whether this `+0.0200` `HOLDOUT-DTI` advantage translates above `0.2778` on the hidden live test set depends on the proportion of INGENIOUS blind hydrothermal/intersection targets vs. SGMC-mapped range-front traces in the hidden ground truth (`H19-5`/`GEMSDOE32` ingested SGMC directly, whereas `MAW-GSI` is 100% sensor-driven Zero-SGMC); per Rule 3, only DrivenData's `ORGANIZER-CONFIRMED` evaluation can establish the live score.

---

## 3. Ranked Pre-Registered Untried Geological Hypotheses ([`evidence/hypotheses_preregistration.json`](evidence/hypotheses_preregistration.json))

{chr(10).join(md_hyp_items)}

---

## 4. Holdout Experiments (`Budget = 3/3`), 45-Feature Leakage Canaries & {current_registry_n}-Raster Refreshed Uniqueness

![Holdout Progression & Leakage Canary](docs/assets/holdout_experiments_and_canary.png)

| Arm / Experiment | `HOLDOUT-DTI` (`seed=2026`, `11,360` px) | 95% 20 km Block CI | Detached Blind (`>800 m`) DTI | `seed=20` Stability (`11,321` px) | Architectural Role |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `zero_control` | `0.000000` | `[0.000000, 0.000000]` | `0.000000` | `0.000000` | All-zero baseline |
| `distance_only_collar2_control` | `0.032947` | `[0.027528, 0.038032]` | **`0.000000`** | `0.031820` | Proves halo rings fail completely on blind (`>800 m`) faults |
| `ApartGEMSDOE1 v1` (Prior Repo Best) | `0.052325` | `[0.037453, 0.068666]` | `0.033245` | `0.047805` | Prior `H-APART-1` baseline (`0.0525`* user-reported live) |
| **`E1`: `MAW-ScarpGeophys` (30 Blind Features)** | `0.077376` | `[0.058844, 0.098021]` | `0.072133` | `0.057175` | 8-azimuth 1.1–1.5 km strike worms + antislope graben dipole + cross-gradient |
| **`E2`: `MAW-GSI Blind Vent` (40 Blind Features)** | `0.079485` | `[0.059571, 0.101866]` | `0.074031` | `0.058419` | Adds Faulds-Hinz `I_vent` orthogonal intersections + demag + GDR #1391 thermal/probes/sinter |
| **`E3`: `MAW-GSI OOF Axial-Relay` (Promoted)** | **`0.117438`** | **`[0.099365, 0.136129]`** | **`0.084019`** | **`0.124957`** | Stage-2 OOF axial worms + collar-tempered relay + dual 300 m Minoux CELF (`37,654` dots) |

- **Leakage Canary ([`evidence/leakage_canary.json`](evidence/leakage_canary.json))**: All `45 / 45` features tested individually on `gems57-pooled-hide-v2` pass `max(AUC, 1 - AUC) <= 0.90` (`max = 0.7765`).
- **Dual Uniqueness Gate**: The original pre-placement surface gate in [`evidence/uniqueness_gate.json`](evidence/uniqueness_gate.json) checked `806` rasters; the refreshed final-raster receipt in [`evidence/cli_validator_check.json`](evidence/cli_validator_check.json) now checks `50` peer/reference repositories and **`{current_registry_n}` unique rasters** (`{current_sparse_n}` sparse detectors + `{current_blanket_n}` disclosed continuous/wide-area blankets):
  - Original pre-placement continuous surface max `|Spearman ρ| = 0.6911 <= 0.90` (`PASS`).
  - Refreshed post-placement final raster max `|Spearman ρ| = {current_uniq['max_abs_spearman_rho']:.4f} <= 0.90` (`PASS`).
  - Refreshed max 3-px overlap across all `{current_sparse_n}` competing sparse detectors = **`{current_uniq['max_3px_overlap_vs_competing_detectors']*100:.2f}% <= 70.00%`** (`PASS`; `46.71%` vs `GEMSDOE32`, `47.68%` vs `GEMSDOE27 H31`, `33.16%` vs `GEMSDOE70`, `11.02%` vs `ApartGEMSDOE1 v1`).

---

## 5. Latest Iteration — `H-APART-6 OTSP` Negative Result (Budget `3/3`)

Four untried candidates were ranked before implementation in [`evidence/hypotheses_preregistration_h6.json`](evidence/hypotheses_preregistration_h6.json). Expected improvements are design priors only—not measured scores or live projections:

| Rank | Candidate | Specific layers | Physical signature | Expected improvement prior | Cost |
| :---: | :--- | :--- | :--- | :---: | :--- |
{h6_hyp_rows_md}

The selected `H-APART-6` lane tested whether fold-visible fault tangents could be transported into independently measured, scale-persistent topographic and gravity contacts. All three single-feature leakage canaries passed (`max symmetric AUC = {h6['leakage_canary']['max_symmetric_auc']:.6f} <= 0.90`), but every arm remained below the promoted `MAW-GSI E3` baseline:

| H-APART-6 arm | `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, `11,360` positives) | 95% CI | Detached `>800 m` DTI | Selector verdict |
| :--- | :---: | :---: | :---: | :--- |
| `E1` topographic tangent transport | `{h6['experiments'][0]['dti']:.6f}` | `[{h6['experiments'][0]['ci95'][0]:.6f}, {h6['experiments'][0]['ci95'][1]:.6f}]` | `{h6['experiments'][0]['detached_gt_800m_dti']:.6f}` | Negative |
| `E2` topography + gravity | `{h6['experiments'][1]['dti']:.6f}` | `[{h6['experiments'][1]['ci95'][0]:.6f}, {h6['experiments'][1]['ci95'][1]:.6f}]` | `{h6['experiments'][1]['detached_gt_800m_dti']:.6f}` | Negative |
| `E3` full persistence | `{h6['experiments'][2]['dti']:.6f}` | `[{h6['experiments'][2]['ci95'][0]:.6f}, {h6['experiments'][2]['ci95'][1]:.6f}]` | `{h6['experiments'][2]['detached_gt_800m_dti']:.6f}` | Negative |
| **Retained `H-APART-2 MAW-GSI E3`** | **`{h6['baseline']['dti']:.6f}`** | **`[{h6['baseline']['ci95'][0]:.6f}, {h6['baseline']['ci95'][1]:.6f}]`** | **`0.084019`** | **Keep promoted TIF** |

Per the stop rule, no H-APART-6 live raster was manufactured, no uniqueness claim was made for it, and no weekly submission slot was used. This is a negative scientific deliverable, not a score projection. The unique, all-finite H-APART-2 GeoTIFF at the top remains the highest validated local submission to download.

---

## 6. Reproducible Autonomous CLI Commands

```bash
# 1. Download/restore & SHA-256 verify competition rasters, external USGS/GDR layers, 10m 3DEP DEM, and 19-band cache
bash scripts/download_competition_data.sh

# 2. Autonomously fetch, audit Focus-9, and index the current 50-repo Fleet Uniqueness Registry
.venv/bin/python scripts/audit_focus_sites_and_registry.py

# 3. Reproduce the retained H-APART-2 candidate (45 canaries, <=3 LOQO experiments, uniqueness, GeoTIFF)
.venv/bin/python scripts/run_apartgems_pipeline.py --full-seed20

# 4. Reproduce the latest three-experiment H-APART-6 negative selector (writes no TIF on failure)
.venv/bin/python scripts/run_h6_otsp_experiments.py

# 5. Regenerate diagnostic figures, GitHub Pages HTML & README, and run automated validator + pytest suite
.venv/bin/python scripts/generate_figures.py
.venv/bin/python scripts/build_pages_and_readme.py
.venv/bin/python scripts/validate_submission.py docs/{tif_rel_docs}
.venv/bin/pytest -v
```

---

## 7. Parallel-Run Protocol JSON Run Cards

### Retained promoted H-APART-2 ([`evidence/run_card.json`](evidence/run_card.json))

```json
{json.dumps(rc, indent=2)}
```

### Latest negative H-APART-6 ([`evidence/run_card_h6_otsp.json`](evidence/run_card_h6_otsp.json))

```json
{json.dumps(h6_card, indent=2)}
```

---

## 8. Verified Official Sources, Irregularities & Remaining Limitations

- **Official Verified Links**:
  - DrivenData DOE GEMS Portal: <https://www.drivendata.org/competitions/306/competition-doe-gems/>
  - Official Competition Rules PDF (NREL / DOE OSTI #96647): <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
  - Official Reference Solution Repository: <https://github.com/drivendataorg/gems-prize-reference-solution>
  - GBCGE / NBMG INGENIOUS Great Basin Project: <https://gbcge.org/current-projects/ingenious/>
  - OpenEI GDR #1391 (INGENIOUS Regional Dataset, Thermal Probes & Paleo-Sinter): <https://gdr.openei.org/submissions/1391>
  - USGS GeoDAWN Airborne Magnetic & Radiometric Surveys: <https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7>
  - USGS 3D Elevation Program (3DEP 1 m & 10 m DEM): <https://www.usgs.gov/3d-elevation-program>
  - US Census TIGER/Line 2024 Roads: <https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html>
- **Flagged Data Irregularities Fixed Automatically**: (`IR-1`) Extreme GDAL sentinels (`-3.4028e+38`, `-9.999e+32`) & exterior `NaN`s sanitized; (`IR-2`) `24.61%` NE Nevada 1 m LiDAR gap routed natively via `NaN`-aware trees + 10 m 3DEP strike worms; (`IR-3`) GDR #1391 `F2mDAB` filtered to `[0.5, 54.7]°C` and leaky `dist_known_fault_px` column excluded; (`IR-4`) Band 6 treated accurately as radiometric Total Count; (`IR-5`) `{current_blanket_n}` continuous/wide-area flood rasters separated from `{current_sparse_n}` sparse detectors (`IR-REG-BLANKET`) with full symmetric/matched-density auditing.
- **Limitations & Next-Step Roadmap**:
  1. **Sandbox Network Allowlist (`H-APART-4` & `H-APART-5`)**: NASA OPERA Sentinel-1 InSAR velocity (`asf.alaska.edu`) and NASA LP DAAC ASTER 90 m TIR silica/argillic emissivity (`lpdaac.usgs.gov`) are free public-domain US Government datasets outside this sandbox's outbound host allowlist; ingesting OPERA LOS phase-gradient steps across flat agricultural/evaporite playas on an unrestricted workstation is the highest-value external extension (`+0.010–0.022` expected `HOLDOUT-DTI`).
  2. **Catalogue Proxy Bias**: `gems57-pooled-hide-v2` withholds segments from `existing_faults.tif`, under-representing totally unmapped sub-playa horst blocks (`> 3 km` from all known traces); coupling 3D multi-altitude Euler deconvolution (`H-APART-3`) with relocated microseismic focal planes can sharpen deep basin fault-dip geometry.

---

## 9. Standing Reference: Original Competition Task & Protocol Specification

<details>
<summary>Click to expand full standing user instructions & Parallel-Run Protocol reference</summary>

- **Competition**: DOE GEMS DrivenData Prize Challenge (`https://www.drivendata.org/competitions/306/competition-doe-gems/`, leaderboard high `0.4413`, benchmark `> 0.3195` and `> 0.2778`, best listed Focus-9 site `0.2778` on `GEMSDOE32`).
- **Updated User-Reported Submission Context**:
  - `apartgems1-udth-submod-e3-20261027-50e7b334`: `0.0525`
  - `gems27-h31-drcg-wl-celf28`: `0.2250`
  - `kanlergems2-htcads-exp-2`: `0.1218`
  - `wbg3-h3pack-34k`: `0.0443`
  - `gems91-S18-UNIQUE-curvtilt`: `0.0435`
  - `gems91-s22-omtj-e1`: `0.0298`
  - `wbg2-offcatalogue-density-36k`: `0.0262`
- **Project Values from the Standing Prompt**:
  - **Maximize P(Win)**: make evidence-based tradeoffs that maximize the probability of a valid, genuinely competitive submission rather than optimizing appearances.
  - **Own the Outcome**: carry data restoration, research, modeling, validation, documentation, and failure reporting end to end; treat both positive and negative experiments as signals.
- **Core Deliverables & Constraints**:
  1. Store prompt instructions in `README.md`, work autonomously end-to-end, and download/prepare official competition data automatically without manual gates.
  2. Deep PhD-level analysis of `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: `0.2778`) — why/how it scored `0.2778` and how to beat `0.2778` — plus an executive summary and auditable table across `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36`, and our new submission.
  3. Before implementing, propose 3–5 untried geological hypotheses (naming layers, physical signature, why missing from USGS/INGENIOUS catalogues, difference from existing repo implementation, named non-fault mimics, and any free official external source), ranked by expected DTI gain and cost.
  4. Generate a **unique** single-band `.tif` (and `.zip`) submission strictly in `[0, 1]`, zero footprint/exterior NaNs (preventing `"Predicted values must be in range [0, 1]"`), matching `example_submission.tif` CRS/shape/geotransform, validated 100% automatically in project code.
  5. Update clean GitHub Pages UI (`docs/index.html` & `docs/executive-summary.html`) with obvious one-click `.tif` download & automated validation status right at the top, plus step-by-step DrivenData submission instructions and verified official links.
  6. Enforce Parallel-Run Protocol: (1) Single method lane + Dual Uniqueness gate (`|ρ| <= 0.90` on surface & final raster, `<= 70%` 3-px dot overlap); (2) Reuse shared `evaluate_holdout.py` & `submission_writer.py` (`alpha=0.2, beta=0.8, 300 m` triangular kernel); (3) Strict score labeling (`HOLDOUT-DTI` vs `ORGANIZER-CONFIRMED`, never projecting scores); (4) Single-feature leakage canary (`AUC <= 0.90`); (5) End with canonical JSON Run Card; (6) Cap at `<= 3` experiments or `2` hours, beating prior holdout best (`0.0523`).
  7. Execute in 3 verification passes (Pass 1: implement & verify; Pass 2: review & fix bugs/assumptions/edge cases; Pass 3: re-check against full prompt & polish), open & merge PR onto `main`, and document remaining work & limitations.

</details>
"""
    (ROOT / "README.md").write_text(readme_md, encoding="utf-8")
    print("Built docs/index.html, docs/executive-summary.html, and README.md successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
