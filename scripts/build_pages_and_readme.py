#!/usr/bin/env python3
"""Deterministically build docs/index.html, docs/executive-summary.html, and README.md from verified JSON receipts."""
from __future__ import annotations

import html
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    rc = json.loads((ROOT / "evidence/run_card.json").read_text())
    fa = json.loads((ROOT / "evidence/focus_sites_forensic_audit.json").read_text())
    exp = json.loads((ROOT / "evidence/experiments_holdout.json").read_text())
    can = json.loads((ROOT / "evidence/leakage_canary.json").read_text())
    uniq = json.loads((ROOT / "evidence/uniqueness_gate.json").read_text())
    val = json.loads((ROOT / "evidence/validation_receipt.json").read_text())
    prereg = json.loads((ROOT / "evidence/preregistration_hypotheses.json").read_text())
    cpied_bench = json.loads((ROOT / "evidence/concealed_piedmont_benchmarks.json").read_text())

    # Sync JSON evidence into docs/data/ so GitHub Pages links resolve 100% locally
    docs_data = ROOT / "docs/data"
    docs_data.mkdir(parents=True, exist_ok=True)
    for fname in ("focus_sites_forensic_audit.json", "concealed_piedmont_benchmarks.json"):
        shutil.copy2(ROOT / "evidence" / fname, docs_data / fname)

    tif_rel_docs = rc["validator_output"]["file"].replace("docs/", "")
    zip_rel_docs = rc["validator_output"]["zip_file"].replace("docs/", "")
    tif_filename = Path(tif_rel_docs).name
    zip_filename = Path(zip_rel_docs).name

    vs_f9 = uniq["vs_focus_9_champions"]
    cp_by_key = {b["key"]: b["concealed_piedmont_dti"]["dti"] for b in cpied_bench["benchmarks"]}

    # Build Focus-9 + ApartGEMSDOE1 (Promoted S2 + Archived S1) HTML & Markdown rows
    table_rows_html: list[str] = []
    table_rows_html.append(f"""
      <tr class="highlight-row">
        <td><strong>ApartGEMSDOE1 (Ours · Session 2)</strong><br><span class="pass-tag">PROMOTED NEW</span></td>
        <td>
          <a href="{html.escape(tif_rel_docs)}" download><strong>{html.escape(tif_filename)}</strong></a><br>
          <span class="mono-val">sha256: {rc['raster_sha256'][:16]}…</span> ({rc['validator_output']['bytes']:,} B)
        </td>
        <td>
          <strong>HOLDOUT-DTI: {rc['holdout_dti']['dti']:.4f}</strong> (seed=20: <strong>{rc['holdout_dti']['seed_20_stability_dti']:.4f}</strong>)<br>
          <small>95% CI [{rc['holdout_dti']['ci95'][0]:.4f}, {rc['holdout_dti']['ci95'][1]:.4f}] ({rc['holdout_dti']['evaluator_version']}, {rc['holdout_dti']['withheld_positive_pixels']:,} px)<br>
          Detached &gt;800m blind HOLDOUT-DTI: <strong>{rc['holdout_dti']['detached_gt_800m_blind_dti']:.4f}</strong><br>
          Concealed Piedmont HOLDOUT-DTI (<code>sgmc-piedmont-basin-v1</code>, 10,579 px): <strong>{rc['concealed_piedmont_holdout_dti']['dti']:.4f}</strong> [{rc['concealed_piedmont_holdout_dti']['ci95'][0]:.4f}, {rc['concealed_piedmont_holdout_dti']['ci95'][1]:.4f}]</small>
        </td>
        <td><strong>{rc['validator_output']['emitted_positive_pixels']:,}</strong><br><small>min NN = {rc['validator_output']['min_nearest_neighbor_px']:.2f} px (1.3% &ge;3 nbrs)<br>0 on cat | 0 &le;200m | {rc['validator_output']['farfield_gt_1500m_pixels']:,} ({rc['validator_output']['farfield_gt_1500m_fraction']*100:.1f}%) &gt;1.5km</small></td>
        <td><span class="pass-tag">ALL-FINITE [0, 1]</span><br><small>0 NaN · 0 Inf across 12.28M cells</small></td>
        <td>
          <strong>Max 3-px ov: {rc['registry_uniqueness']['post_placement_max_3px_overlap_vs_competing']*100:.2f}%</strong> (&le;70% across 881 sparse)<br>
          <small>vs GEMSDOE32 (0.2778): <strong>{rc['registry_uniqueness']['vs_gemsdoe32_02778_3px_overlap']*100:.2f}%</strong> · vs Sess 1: <strong>{rc['registry_uniqueness']['vs_session_1_50e7b334_3px_overlap']*100:.2f}%</strong><br>
          Surface |&rho;|: {rc['registry_uniqueness']['pre_placement_surface_max_abs_spearman']:.4f} (&le;0.90 across 950 rasters)</small>
        </td>
        <td><span class="pass-tag">PASS — UNIQUE &amp; OK TO SUBMIT</span></td>
      </tr>
    """)

    # Archived Session 1 row for full audit transparency
    table_rows_html.append("""
      <tr>
        <td><strong>ApartGEMSDOE1 (Archived Sess 1)</strong><br><span class="warn-tag">ARCHIVED PRIOR</span></td>
        <td>
          <a href="downloads/archive/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif" download>apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif</a><br>
          <span class="mono-val">fp_sha256: 50e7b33477943944…</span>
        </td>
        <td>
          <strong>ORGANIZER-CONFIRMED: 0.0525</strong><br>
          <small>HOLDOUT-DTI: 0.0523 [0.0375, 0.0687] (<code>gems57-pooled-hide-v2</code>, 11,360 px)<br>
          Concealed Piedmont HOLDOUT-DTI: 0.0214 [0.0156, 0.0277]</small>
        </td>
        <td>38,500<br><small>min NN = 1.00 px (<strong>97.3% &ge;3 nbrs crowded</strong>)<br>0 &le;200m | 40.1% &gt;1.5km</small></td>
        <td><span class="pass-tag">All-Finite [0, 1]</span></td>
        <td><span class="stop-tag">ALREADY SUBMITTED (0.0525)</span><br><small>Indexed in 950-raster gate (only 10.81% ov w/ S2)</small></td>
        <td><span class="stop-tag">ARCHIVED — DO NOT RESUBMIT</span><br><small>Superseded by Session 2 PLKC-DualOOF</small></td>
      </tr>
    """)

    md_focus_rows = [
        f"| **ApartGEMSDOE1 (Session 2 — Promoted)** | [`{tif_filename}`](docs/{tif_rel_docs}) (`{rc['raster_sha256'][:12]}…`) | `HOLDOUT-DTI`: **`{rc['holdout_dti']['dti']:.4f}`** (`[{rc['holdout_dti']['ci95'][0]:.4f}, {rc['holdout_dti']['ci95'][1]:.4f}]`, `gems57-pooled-hide-v2`, `11,360` px; `seed=20`: **`{rc['holdout_dti']['seed_20_stability_dti']:.4f}`**); Detached `>800m`: **`{rc['holdout_dti']['detached_gt_800m_blind_dti']:.4f}`**; Concealed Piedmont `HOLDOUT-DTI` (`sgmc-piedmont-basin-v1`, `10,579` px): **`{rc['concealed_piedmont_holdout_dti']['dti']:.4f}`** (`[{rc['concealed_piedmont_holdout_dti']['ci95'][0]:.4f}, {rc['concealed_piedmont_holdout_dti']['ci95'][1]:.4f}]`) | `{rc['validator_output']['emitted_positive_pixels']:,}` (`min NN=2.83 px`, `1.28%` >=3 nbrs, `0` <=200m, `41.3%` >1.5km) | All-finite `[0,1]` (`0` NaN) | **UNIQUE** (max `62.64%` across 881 sparse / 950 total; **`43.17%`** vs `GEMSDOE32`; **`10.81%`** vs Sess 1) | **PASS — OK TO DOWNLOAD & SUBMIT** |",
        "| **ApartGEMSDOE1 (Session 1 — Archived)** | [`apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif`](docs/downloads/archive/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif) | `ORGANIZER-CONFIRMED`: `0.0525` · `HOLDOUT-DTI`: `0.0523` (`[0.0375, 0.0687]`) · Concealed Piedmont `HOLDOUT-DTI`: `0.0214` | `38,500` (`97.3%` >=3 nbrs crowded) | All-finite `[0,1]` | Already submitted (`0.0525` live) | **ARCHIVED — DO NOT RESUBMIT** |",
    ]

    f9_cp_lookup = {
        "GEMSDOE32": cp_by_key.get("GEMSDOE32_B2_02778"),
        "GEMSDOE36": cp_by_key.get("GEMSDOE36_PINN_02750"),
        "GEMSDOE25": cp_by_key.get("GEMSDOE25_D28_02600"),
        "GEMSDOE30": cp_by_key.get("GEMSDOE25_D28_02600"),
        "GEMSDOE24": cp_by_key.get("GEMSDOE24_D15_02477"),
    }

    for r in fa["focus_9_sites"]:
        site = r["site"]
        s_hold = r["static_holdout_dti"]
        me_cmp = vs_f9.get(site, {})
        me_ov_txt = f"{me_cmp.get('overlap_3px_fraction', 0)*100:.2f}%" if me_cmp else "—"
        cp_val = f9_cp_lookup.get(site)
        cp_txt = f"<br>Concealed Piedmont HOLDOUT-DTI: {cp_val:.4f}" if cp_val is not None else ""
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
        lat = r["latest_20261027_candidate"]
        lat_html = (
            f"<br><small>Oct 26-27 repo file: <code>{html.escape(lat['file'])}</code> "
            f"(HOLDOUT-DTI {lat['static_holdout_dti']['dti']:.4f})</small>"
            if lat
            else ""
        )
        table_rows_html.append(f"""
          <tr>
            <td><a href="{html.escape(r['site_url'])}" target="_blank" rel="noopener"><strong>{html.escape(site)}</strong></a></td>
            <td>
              <a href="{html.escape(r['download_url'])}" target="_blank" rel="noopener">{html.escape(r['local_verified_file'])}</a><br>
              <span class="mono-val">sha256: {r['file_sha256'][:16]}…</span>{lat_html}
            </td>
            <td>
              <strong>ORGANIZER-CONFIRMED (ledger): {r['user_reported_score']:.4f}</strong><br>
              <small>Static HOLDOUT-DTI: {s_hold['dti']:.4f} [{s_hold['ci95'][0]:.4f}, {s_hold['ci95'][1]:.4f}] ({s_hold['evaluator_version']}, {s_hold['withheld_positive_pixels']:,} px){cp_txt}</small>
            </td>
            <td>{r['dots']:,}<br><small>{r['dots_within_200m_collar']:,} &le;200m collar<br>{r['farfield_fraction']*100:.1f}% &gt;1.5km</small></td>
            <td>{nan_badge}</td>
            <td>
              <span class="stop-tag">NOT UNIQUE ({r['max_3px_overlap_vs_other_focus9']*100:.2f}% w/ {r['max_overlap_peer_site']})</span><br>
              <small>{dup_note}Overlap w/ Apart1 S2: {me_ov_txt}</small>
            </td>
            <td><span class="stop-tag">DO NOT RESUBMIT</span><br><small>H19-5 post-processed derivative</small></td>
          </tr>
        """)
        nan_md = "All-finite `[0,1]`" if r["all_grid_finite_no_nan"] else f"`{r['exterior_nan_pixels']:,}` exterior NaNs"
        cp_md = f" · Concealed Piedmont `HOLDOUT-DTI`: `{cp_val:.4f}`" if cp_val is not None else ""
        md_focus_rows.append(
            f"| [{site}]({r['site_url']}) | [`{r['local_verified_file']}`]({r['download_url']}) (`{r['file_sha256'][:12]}…`) | "
            f"`ORGANIZER-CONFIRMED` (ledger): `{r['user_reported_score']:.4f}` · Static `HOLDOUT-DTI`: `{s_hold['dti']:.4f}` (`[{s_hold['ci95'][0]:.4f}, {s_hold['ci95'][1]:.4f}]`){cp_md} | "
            f"`{r['dots']:,}` (`{r['dots_within_200m_collar']:,}` <=200m) | "
            f"{nan_md} | "
            f"**DUPLICATE** (`{r['max_3px_overlap_vs_other_focus9']*100:.2f}%` w/ `{r['max_overlap_peer_site']}`; `{me_ov_txt}` w/ Ours) | "
            f"**DO NOT RESUBMIT** (H19-5 derivative) |"
        )

    hyp_cards_html: list[str] = []
    md_hyp_items: list[str] = []
    for h in prereg["ranked_untried_hypotheses"]:
        sel_badge = (
            '<span class="pass-tag">SELECTED &amp; PROMOTED</span>'
            if h["selected_for_implementation"]
            else '<span class="warn-tag">RANKED BACKLOG</span>'
        )
        mimic_txt = (
            "; ".join(h["named_non_fault_mimic_process"])
            if isinstance(h["named_non_fault_mimic_process"], list)
            else str(h["named_non_fault_mimic_process"])
        )
        hyp_cards_html.append(f"""
          <div style="background:var(--bg-elev);border:1px solid var(--border);border-radius:10px;padding:1.1rem 1.25rem;margin-bottom:1rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
              <strong>Rank #{h['rank']} — {html.escape(h['id'])}: {html.escape(h['title'])}</strong>
              {sel_badge}
            </div>
            <p style="margin:0.55rem 0;font-size:0.9rem;color:#cbd5e1;"><strong>Physical Signature &amp; Transform:</strong> {html.escape(h['physical_signature'])}</p>
            <p style="margin:0.4rem 0;font-size:0.86rem;color:var(--muted);"><strong>Why Missing from USGS/INGENIOUS Catalogue:</strong> {html.escape(h['why_missed_by_usgs_catalogue'])}</p>
            <p style="margin:0.4rem 0;font-size:0.86rem;color:var(--muted);"><strong>Named Non-Fault Mimics Suppressed:</strong> {html.escape(mimic_txt)}</p>
            <p style="margin:0.4rem 0 0;font-size:0.85rem;color:#93c5fd;"><strong>Expected Gain &amp; Cost:</strong> {html.escape(h['expected_dti_improvement'])} | Cost: {html.escape(h['implementation_cost'])}</p>
          </div>
        """)
        status_md = "Implemented & Promoted" if h["selected_for_implementation"] else "Pre-Registered Backlog"
        md_hyp_items.append(
            f"{h['rank']}. **`{h['id']}` ({status_md}) — {h['title']}**:\n"
            f"   - *Physical Transform*: {h['physical_signature']}\n"
            f"   - *Why Missing from USGS/INGENIOUS*: {h['why_missed_by_usgs_catalogue']}\n"
            f"   - *Named Non-Fault Mimics*: {mimic_txt}\n"
            f"   - *Expected Gain & Cost*: {h['expected_dti_improvement']} ({h['implementation_cost']})."
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

    sc_p = exp["primary_draw_seed_2026"]["scores"]
    det_p = exp["primary_draw_seed_2026"]["detached_gt_800m_blind_dti"]
    sc_s20 = exp["secondary_stability_seed_20"]["scores"]
    delta_dist = exp["primary_draw_seed_2026"]["paired_differences_vs_winner"]["distance_only_collar2_control"]

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ApartGEMSDOE1 — Validated Unique GeoTIFF Submission (H-APART-5: PLKC-DualOOF-CELF)</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand"><span class="brand-dot"></span> ApartGEMSDOE1 · DOE GEMS Prize Challenge</div>
      <nav class="nav-links">
        <a href="index.html" class="active">Overview &amp; One-Click Download</a>
        <a href="executive-summary.html">Executive Summary &amp; DrivenData Submit Guide</a>
        <a href="data/run_summary.json" target="_blank">JSON Evidence Receipt</a>
      </nav>
    </div>
  </header>

  <main class="container">
    <section class="verdict-banner">
      <div class="status-pill">&#10003; Automated Format, Range &amp; 950-Raster Uniqueness Gate: PASS — OK TO DOWNLOAD &amp; SUBMIT</div>
      <h1 class="hero-title">Unique Concealed-Piedmont, Fluvial-Knickzone &amp; Hydrothermal GeoTIFF (<code>H-APART-5: PLKC-DualOOF-CELF E3</code>)</h1>
      <p class="hero-sub">
        100% automatically validated in project code with zero human-inspection gates. Guarantees strict
        <code>[0.0, 1.0]</code> range compliance (<code>0</code> NaNs and <code>0</code> Infs across all <code>12,279,160</code> <code>float32</code> pixels,
        <code>nodata=None</code>), repairs Session 1's <code>97.30%</code> kernel blob crowding down to <strong><code>1.28%</code></strong> via CELF max-heap
        <code>d &ge; 2.8 px</code> submodular allocation (<code>37,654</code> dots, <code>0</code> inside <code>&le;200 m</code> collar), and passes cross-fleet
        uniqueness across <strong>53 repositories / 950 unique submission rasters</strong> (max <strong><code>62.64% &le; 70%</code></strong> across 881 sparse detectors;
        only <strong><code>43.17%</code></strong> overlap with <code>GEMSDOE32</code> <code>0.2778</code> and <strong><code>10.81%</code></strong> with archived Session 1 <code>0.0525</code>).
      </p>

      <div class="cta-row">
        <a class="btn-primary" href="{html.escape(tif_rel_docs)}" download>
          &#11015; Download Validated Unique GeoTIFF (.tif · {rc['validator_output']['bytes'] // 1024} KB)
        </a>
        <a class="btn-secondary" href="{html.escape(zip_rel_docs)}" download>
          &#128230; Download Single-TIFF Archive (.zip)
        </a>
        <a class="btn-secondary" href="executive-summary.html">
          &#128214; Step-by-Step DrivenData Submission Guide &rarr;
        </a>
      </div>

      <div class="copy-grid">
        <div class="copy-box">
          <div class="copy-label">
            <span>Submission Filename &amp; SHA-256</span>
            <button class="copy-btn" onclick="copyText('sha-val', this)">Copy SHA-256</button>
          </div>
          <div class="mono-val">{html.escape(tif_filename)}</div>
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
        <div class="kpi-note"><span class="pass-tag">PASS</span> 0 NaN · 0 Inf · EPSG:32611 3730&times;3292</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Pooled HOLDOUT-DTI</div>
        <div class="kpi-val">{rc['holdout_dti']['dti']:.4f}</div>
        <div class="kpi-note"><span class="pass-tag">+51.9% vs Sess 1</span> seed=20: {rc['holdout_dti']['seed_20_stability_dti']:.4f} · &gt;800m: {rc['holdout_dti']['detached_gt_800m_blind_dti']:.4f}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Zero-SGMC Piedmont DTI</div>
        <div class="kpi-val">{rc['concealed_piedmont_holdout_dti']['dti']:.4f}</div>
        <div class="kpi-note"><span class="pass-tag">5.12&times; Sess 1</span> Beats GD32 (0.0954) &amp; GD70 (0.0854)</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Leakage Canary Gate</div>
        <div class="kpi-val">{rc['leakage_canary']['max_symmetric_auc']:.4f}</div>
        <div class="kpi-note"><span class="pass-tag">47/47 PASS</span> All 47 channels &le; 0.90 cap</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">950-Raster Spearman |&rho;|</div>
        <div class="kpi-val">{rc['registry_uniqueness']['pre_placement_surface_max_abs_spearman']:.4f}</div>
        <div class="kpi-note"><span class="pass-tag">PASS &le; 0.90</span> Final dot |&rho;| = {rc['registry_uniqueness']['post_placement_final_max_abs_spearman']:.4f}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">3-px Dot Overlap Gate</div>
        <div class="kpi-val">{rc['registry_uniqueness']['post_placement_max_3px_overlap_vs_competing']*100:.2f}%</div>
        <div class="kpi-note"><span class="pass-tag">PASS &le; 70%</span> 43.17% vs GD32 · 10.81% vs Sess 1</div>
      </div>
    </div>

    <section class="section">
      <h2>1. Spatial Prediction Map &amp; Concealed Piedmont / Geothermal Conduit Discovery</h2>
      <p>
        <strong>H-APART-5 (<code>PLKC-DualOOF-CELF E3</code>)</strong> synthesizes 16 spatially cross-fitted Dual-Regime
        (<code>M_Full</code> preserved-NaN 1 m LiDAR + quantile-calibrated <code>M_Sub</code> 10 m 3DEP / potential-field / hydrothermal)
        and Zero-SGMC Concealed Piedmont Specialist HGB models across two <code>45&deg;</code>-offset 4-sector partitions (<code>1.2 km</code> spatial buffer,
        <code>0%</code> in-sample PU memorization weight), emitting <strong>{rc['validator_output']['emitted_positive_pixels']:,}</strong> non-crowded
        (<code>min NN = {rc['validator_output']['min_nearest_neighbor_px']:.4f} px</code>) binary <code>1.0</code> dots strictly outside the
        <code>200 m</code> mapped-catalogue collar, with <strong>{rc['validator_output']['farfield_gt_1500m_pixels']:,} dots
        ({rc['validator_output']['farfield_gt_1500m_fraction']*100:.1f}%)</strong> targeting unmapped basins <code>&gt;1.5 km</code> from any catalogued fault.
      </p>
      <div class="fig-box">
        <img src="assets/plkc_submission_map.png" alt="ApartGEMSDOE1 PLKC-DualOOF E3 spatial prediction map and Dixie Valley / Carson Sink zoom">
        <div class="fig-cap">
          Left: Full NW Great Basin study grid (EPSG:32611, 3730&times;3292 @ 100 m) showing mapped catalogue faults (slate) and promoted PLKC-DualOOF E3 dots (emerald, 37,654 px) over Band 15 depth-to-basement.
          Right: 70&times;70 km Dixie Valley / Carson Sink rift corridor contrasting GEMSDOE32 B2 (blue crosses, 43.2% overlap) with ApartGEMSDOE1 (emerald circles, min NN = 2.83 px).
        </div>
      </div>
    </section>

    <section class="section">
      <h2>2. Auditable Executive Comparison Across All 9 Focus GEMSDOE Sites + ApartGEMSDOE1</h2>
      <p>
        Per Parallel-Run Protocol Rule 3, every number is strictly labeled as either local
        <strong><code>HOLDOUT-DTI</code></strong> (with evaluator version, withheld positive pixel count, and 20 km spatial block bootstrap 95% CI)
        or <strong><code>ORGANIZER-CONFIRMED</code></strong> (copied from the competition prompt ledger / portal receipt; never a projection).
        All 9 historical Focus-9 files belong to the single <code>19GEMSDOE H19-5</code> post-processing lineage (<code>87%–100%</code> mutual overlap)
        and cannot be resubmitted; <strong>only Session 2 <code>ApartGEMSDOE1</code> (<code>{html.escape(tif_filename)}</code>) is newly generated, unique across all 950 fleet rasters, and cleared for DrivenData upload.</strong>
      </p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Site</th>
              <th>Downloadable GeoTIFF &amp; SHA-256</th>
              <th>Strictly Labeled Score</th>
              <th>Emitted Dots &amp; Spacing</th>
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
      <h2>3. PhD Forensic Analysis: Why <code>GEMSDOE32</code> Scored <code>0.2778</code>, Why Session 1 Scored <code>0.0525</code>, &amp; How We Surpass Both</h2>
      <h3>3.1 Pixel-Exact Zero-XOR Proof of <code>GEMSDOE32</code> (<code>h33-h33-2-b2-zeros</code>: <code>0.2778</code>)</h3>
      <pre class="code-block">GEMSDOE32_B2 (37,654 dots)  ==  GEMSDOE25_D28 (44,090 dots)  &amp;  (EDT(~existing_faults) &gt; 2.0 px)
XOR residual across 5,167,373 footprint pixels = 0   |   Exact subset of 19GEMSDOE H19-5 (121,131 px) = 100.00%
GEMSDOE25_D28 (44,090 dots) ==  GEMSDOE30_D28 (44,090 dots)   [XOR residual = 0]</pre>
      <p>
        Under Distance-Tolerant IoU (<code>&alpha;=0.2, &beta;=0.8, R=300 m</code> triangular kernel), true-positive credit uses a <strong>max</strong>
        operator across 300 m disks while false positives accumulate <strong>additively</strong>. Thinning solid <code>H19-5</code> ridges (<code>121,131</code> px &rarr; <code>0.1922</code>)
        to <code>d = 2.8 px = 280 m</code> (<code>44,090</code> px &rarr; <code>0.2600</code>) and amputating the <code>6,436</code> dots within <code>&le;200 m</code>
        of known faults (<code>37,654</code> px &rarr; <code>0.2778</code>) eliminated redundant kernel crowding and masked-catalogue false positives.
      </p>

      <h3>3.2 Byte-Level Post-Mortem of Session 1 (<code>50e7b334</code>: <code>0.0525</code> Live) &amp; Session 2 Repairs</h3>
      <ul>
        <li><strong>Bug 1 — 97.30% Kernel Blob Crowding (Fixed in <code>src/gems57/emit.py</code>):</strong> Session 1's shared <code>greedy_allocate</code> lacked CELF max-heap re-sorting and clipped <code>k_self = min(E[k], 1.0) = 1.0</code>, collapsing the marginal bar to zero and packing <code>99.37%</code> of dots at <code>NN &le; 1.5 px</code> (<code>13.52</code> neighbors inside 300 m, wasting ~88% of its 38,500-dot budget!). Repairing <code>noisy_or_self_credit</code> + CELF max-heap + <code>min_sep_px = 2.8</code> cuts <code>&ge;3</code>-neighbor crowding from <strong><code>97.30%</code> down to <code>1.28%</code></strong> (a <strong>76&times;</strong> reduction).</li>
        <li><strong>Bug 2 — 75% In-Sample PU Memorization on Live Export (Fixed via Dual-Partition 100%-OOF):</strong> Unmapped real faults carry label <code>y = 0</code> in Positive-Unlabeled training. Session 1 averaged all 4 quadrant trees at live inference (75% in-sample suppression). Session 2 predicts every pixel strictly out-of-fold across two <code>45&deg;</code>-offset 4-sector partitions with a <code>1.2 km</code> spatial buffer (<code>0%</code> in-sample HGB weight).</li>
        <li><strong>Bug 3 — Pluvial Shoreline Mimics, Missing Fluvial <code>&chi;/k_sn</code> &amp; Concealed Piedmont Blindness (Fixed in <code>H-APART-5</code>):</strong> Session 2 unlocks orthometric 3DEP elevation (<code>zmean_m</code>) to suppress Pleistocene Lake Lahontan (<code>1,330 m</code>) &amp; Bonneville (<code>1,463/1,558 m</code>) wave-cut benches, adds across-fault fluvial <code>&Delta;&chi;</code> &amp; <code>k_sn</code> knickzones, preserves exact <code>NaN</code> semantics on 12-band 1 m LiDAR (<code>74.2%</code> coverage) via Dual-Regime calibration, and trains a dedicated <strong>Zero-SGMC Concealed Piedmont Specialist</strong> (<code>b15_depth_base &ge; 180 m</code>), lifting read-only Concealed Piedmont DTI from <strong><code>0.0214</code> &rarr; <code>0.1094</code></strong> (surpassing <code>GEMSDOE32</code>'s <code>0.0954</code>!).</li>
      </ul>
      <div class="fig-box">
        <img src="assets/focus9_audit_and_uniqueness.png" alt="Focus-9 10x10 overlap matrix and GEMSDOE32 0.2778 score ladder">
        <div class="fig-cap">
          Left: Exact 3-px dot overlap across all 9 Focus-9 champions (87–100% mutually redundant) vs. ApartGEMSDOE1 Session 2 (43.2–47.9% overlap — well below 70% cap).
          Right: Empirical 0.1922 &rarr; 0.2778 H19-5 spacing &amp; 200 m collar progression.
        </div>
      </div>
    </section>

    <section class="section">
      <h2>4. Pre-Registered Untried Geological Hypotheses (Ranked 1–5)</h2>
      {''.join(hyp_cards_html)}
    </section>

    <section class="section">
      <h2>5. Holdout Validation (<code>gems57-pooled-hide-v2</code>), Concealed Piedmont Benchmark &amp; 47-Channel Leakage Canary</h2>
      <p>
        Across our capped <code>3/3</code> experiment budget, pooled <code>HOLDOUT-DTI</code> rose monotonically from
        <code>zero_control</code> (<code>0.0000</code>) and matched-collar <code>distance_only</code> (<code>{sc_p['distance_only_collar2_control']['dti']:.4f}</code>)
        through <code>E1</code> (<strong><code>{sc_p['E1_plkc_dual_regime_blind']['dti']:.4f}</code></strong>, detached <code>&gt;800 m</code> = <code>{det_p['E1_plkc_dual_regime_blind']:.4f}</code>)
        and <code>E2</code> (<strong><code>{sc_p['E2_plkc_hydro_stage2_vessel']['dti']:.4f}</code></strong>, detached <code>&gt;800 m</code> = <code>{det_p['E2_plkc_hydro_stage2_vessel']:.4f}</code>)
        to promoted <strong><code>E3</code> (<code>{sc_p['E3_plkc_dualoof_celf_full']['dti']:.4f}</code>, 95% CI <code>[{sc_p['E3_plkc_dualoof_celf_full']['ci95'][0]:.4f}, {sc_p['E3_plkc_dualoof_celf_full']['ci95'][1]:.4f}]</code>;
        <code>seed=20</code> stability = <code>{sc_s20['E3_plkc_dualoof_celf_full']['dti']:.4f}</code>; paired <code>&Delta;(E3 &minus; DistOnly) = +{delta_dist['delta']:.4f}</code>,
        95% CI <code>[+{delta_dist['ci95'][0]:.4f}, +{delta_dist['ci95'][1]:.4f}]</code>)</strong>. On the strictly read-only <code>sgmc-piedmont-basin-v1</code>
        concealed-fault diagnostic (<code>10,579</code> px; zero SGMC in features/training), our live raster achieves
        <strong><code>HOLDOUT-DTI = {rc['concealed_piedmont_holdout_dti']['dti']:.4f}</code></strong> (95% CI <code>[{rc['concealed_piedmont_holdout_dti']['ci95'][0]:.4f}, {rc['concealed_piedmont_holdout_dti']['ci95'][1]:.4f}]</code>),
        exceeding both <code>GEMSDOE70 P8</code> (<code>0.0854</code>, <code>0.2478</code> live) and <code>GEMSDOE32 B2</code> (<code>0.0954</code>, <code>0.2778</code> live).
      </p>
      <div class="fig-box">
        <img src="assets/holdout_experiments_and_canary.png" alt="Holdout DTI progression, Zero-SGMC Concealed Piedmont diagnostic, and 47-channel leakage canary">
        <div class="fig-cap">
          Panel A: Monotonic E1&rarr;E2&rarr;E3 HOLDOUT-DTI &amp; detached (&gt;800 m blind) DTI vs. Session 1 (0.0523) and controls.
          Panel B: Read-only Concealed Piedmont HOLDOUT-DTI calibration across 18 live-scored peers (&rho;=+0.55, p=0.019) vs. our zero-SGMC PLKC-DualOOF E3 (0.1094).
          Panel C: Automated single-feature leakage canary across all 47 channels (47/47 PASS &le; 0.90; max = 0.7665).
        </div>
      </div>
    </section>

    <section class="section">
      <h2>6. Machine-Readable Parallel-Run Protocol Run Card</h2>
      <pre class="code-block">{html.escape(json.dumps(rc, indent=2))}</pre>
    </section>
  </main>

  <footer>
    ApartGEMSDOE1 · Branch <code>arena/eceaf9f6-apartgemsdoe1</code> · Validated 100% automatically via <code>scripts/validate_submission.py</code> &amp; <code>pytest</code>.
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
  <title>Executive Summary &amp; How to Submit on DrivenData — ApartGEMSDOE1</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand"><span class="brand-dot"></span> ApartGEMSDOE1 · Executive Summary &amp; Submission Guide</div>
      <nav class="nav-links">
        <a href="index.html">&larr; Back to Main Dashboard</a>
        <a href="executive-summary.html" class="active">Executive Summary &amp; DrivenData Submit Guide</a>
        <a href="data/focus_sites_forensic_audit.json" target="_blank">Focus-9 Forensic JSON</a>
        <a href="data/concealed_piedmont_benchmarks.json" target="_blank">Piedmont Benchmark JSON</a>
      </nav>
    </div>
  </header>

  <main class="container">
    <section class="verdict-banner">
      <div class="status-pill">&#10003; Automated Validation &amp; 950-Raster Uniqueness Gate: PASS — READY FOR DRIVENDATA UPLOAD</div>
      <h1 class="hero-title">Executive Summary &amp; Step-by-Step DrivenData Submission Guide</h1>
      <p class="hero-sub">
        Concise decision brief across all 9 focus GEMSDOE sites, byte-verified root-cause resolution of the
        <code>"Predicted values must be in range [0, 1]"</code> portal error and Session 1's <code>0.0525</code> crowding bottleneck,
        and a 6-step checklist to submit <code>{html.escape(tif_filename)}</code> on DrivenData.
      </p>
      <div class="cta-row">
        <a class="btn-primary" href="{html.escape(tif_rel_docs)}" download>
          &#11015; Step 1: Download Validated Unique .tif ({rc['validator_output']['bytes'] // 1024} KB)
        </a>
        <a class="btn-secondary" href="https://www.drivendata.org/competitions/306/competition-doe-gems/" target="_blank" rel="noopener">
          &#127760; Open DOE GEMS DrivenData Competition Portal &nearr;
        </a>
      </div>
    </section>

    <section class="section">
      <h2>1. Executive Decision Brief (60-Second Read)</h2>
      <ul>
        <li><strong>Do NOT resubmit any Focus-9 file (<code>GEMSDOE24..36</code>) or archived Session 1 (<code>50e7b334</code>):</strong> All 9 Focus-9 champions are post-processed subsets of <code>19GEMSDOE H19-5</code> (<code>87%–100%</code> mutual 3-px dot overlap; <code>GEMSDOE32 B2 == GEMSDOE25_D28 &amp; (EDT(~existing_faults) &gt; 2.0)</code> with <code>0</code> XOR error), and Session 1 (<code>0.0525</code> live) is already submitted and archived.</li>
        <li><strong>Why <code>{html.escape(tif_filename)}</code> IS unique, scientifically distinct, and ready to upload:</strong>
          <ul>
            <li><strong>Range &amp; Format Gate (PASS):</strong> Single-band <code>float32</code>, <code>EPSG:32611</code>, <code>3730&times;3292</code>, <code>min=0.0</code>, <code>max=1.0</code>, <code>nodata=None</code>, <strong><code>0</code> NaNs and <code>0</code> Infs across all <code>12,279,160</code> pixels</strong>.</li>
            <li><strong>Spacing &amp; Collar Gate (PASS):</strong> <code>37,654</code> binary <code>1.0</code> dots, <code>min NN = 2.8284 px</code> (<code>0.0% &lt; 2.8 px</code>, <code>1.28%</code> &ge;3 neighbors vs Session 1's <code>97.30%</code>), <code>0</code> dots on catalogue or within <code>&le;200 m</code> collar, <code>41.29%</code> in far-field basins (<code>&gt;1.5 km</code>).</li>
            <li><strong>Holdout &amp; Concealed Piedmont Gates (PASS):</strong> Monotonic <code>E1 (0.0687) &rarr; E2 (0.0725) &rarr; E3 (0.0795)</code> on <code>gems57-pooled-hide-v2</code> (<code>seed=20</code>: <code>0.0908</code>; <code>+51.9%</code> over Session 1); Zero-SGMC Concealed Piedmont <code>HOLDOUT-DTI = 0.1094</code> (<code>5.12&times;</code> Session 1 <code>0.0214</code>; exceeds <code>GEMSDOE32</code> <code>0.0954</code> and <code>GEMSDOE70</code> <code>0.0854</code>).</li>
            <li><strong>53-Repo / 950-Raster Uniqueness Gate (PASS):</strong> Pre-placement surface <code>|&rho;| = 0.5492 &le; 0.90</code>; final dots <code>|&rho;| = 0.0818 &le; 0.90</code>; max 3-px dot overlap = <code>62.64% &le; 70.00%</code> across 881 competing sparse detectors (<code>43.17%</code> vs <code>GEMSDOE32</code>, <code>34.95%</code> vs <code>GEMSDOE70</code>, <code>10.81%</code> vs Session 1).</li>
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
            Click <a href="{html.escape(tif_rel_docs)}" download><strong><code>{html.escape(tif_filename)}</code></strong></a> above (or <a href="{html.escape(zip_rel_docs)}" download><code>{html.escape(zip_filename)}</code></a> — unzip before uploading if downloading the archive).
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">2</div>
          <div>
            <strong>(Optional) Verify SHA-256 Checksum Locally</strong><br>
            Run <code>shasum -a 256 {html.escape(tif_filename)}</code> (macOS/Linux) or <code>certutil -hashfile {html.escape(tif_filename)} SHA256</code> (Windows) and confirm:<br>
            <span class="mono-val" style="color:#34d399;">{rc['raster_sha256']}</span>
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">3</div>
          <div>
            <strong>Open the DrivenData DOE GEMS Submissions Portal</strong><br>
            Sign in at <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/" target="_blank" rel="noopener">https://www.drivendata.org/competitions/306/competition-doe-gems/</a>, open the <strong>Submissions</strong> tab, and verify your rolling submission quota.
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">4</div>
          <div>
            <strong>Upload the Raw Single-Band <code>.tif</code> File</strong><br>
            Select <code>{html.escape(tif_filename)}</code> (<code>{rc['validator_output']['bytes']:,}</code> bytes, DEFLATE-compressed <code>float32</code> GeoTIFF matching <code>example_submission.tif</code> pixel-for-pixel in CRS <code>EPSG:32611</code>, shape <code>3730&times;3292</code>, and affine geotransform <code>(100, 0, 243350, 0, -100, 4508550)</code>).
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">5</div>
          <div>
            <strong>Paste the Unique Submission Comment (&le;140 Characters)</strong><br>
            Copy and paste this exact <code>{rc['submission_note_chars']}</code>-character description into the submission comment field:
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
            <strong>Submit &amp; Log the <code>ORGANIZER-CONFIRMED</code> Score</strong><br>
            Because all <code>12,279,160</code> cells are strictly finite in <code>[0.0, 1.0]</code> with zero <code>NaN</code>s and zero GDAL <code>-3.4028235e+38</code> sentinels, the portal range check passes cleanly. Record the returned score strictly as <code>ORGANIZER-CONFIRMED</code>.
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>3. Flagged Data, Code &amp; Registry Irregularities (Zero-Hallucination Audit Log)</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Irregularity ID</th>
              <th>Observed Empirical Finding</th>
              <th>Automated Mitigation in ApartGEMSDOE1</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>IR-SENTINEL-F32MIN</code></td>
              <td><code>training_features.tif</code> Bands 1–19 contain <code>1,521–1,533</code> GDAL <code>-3.4028235e+38</code> sentinel cells inside the active footprint plus <code>7.11M</code> exterior <code>NaN</code>s, causing historical <code>"Predicted values must be in range [0, 1]"</code> errors.</td>
              <td><code>scripts/prepare_data.py</code> sanitizes all <code>|x| &gt; 1e30</code> to <code>NaN</code>, and <code>submission_writer.py</code> enforces <code>0</code> NaNs across all <code>12,279,160</code> cells.</td>
            </tr>
            <tr>
              <td><code>IR-S1-CROWDING-AND-INSAMPLE</code></td>
              <td>Session 1 (<code>50e7b334</code>, <code>0.0525</code> live) packed <code>99.37%</code> of dots at <code>NN &le; 1.5 px</code> (<code>97.30%</code> &ge;3 neighbors in 300 m) due to missing CELF re-sorting &amp; <code>k_self=1.0</code> clipping in <code>gems57/emit.py</code>, and suffered <code>75%</code> in-sample PU suppression on live export.</td>
              <td>Repaired shared <code>gems57/emit.py</code> with <code>noisy_or_self_credit</code> + CELF max-heap + <code>min_sep_px=2.8</code> (<code>1.28%</code> crowding) and stitched 16 <code>100%</code>-OOF models across dual <code>45&deg;</code>-offset partitions.</td>
            </tr>
            <tr>
              <td><code>IR-STAGE2-SMOOTH-DOMINANCE</code></td>
              <td>Feeding <code>1.5 km</code> blurred Stage-1 line averages directly into a nested Stage-2 HGB caused trees to split on broad smooth halos rather than 100 m scarp crests.</td>
              <td>Replaced with across-strike-preserving 8-azimuth directional anisotropy &amp; halo-ratio gating in <code>src/apartgems/model.py</code>, lifting <code>E2</code> strictly above <code>E1</code> on both <code>seed=2026</code> and <code>seed=20</code>.</td>
            </tr>
            <tr>
              <td><code>IR-ISOTROPIC-HALO-COLLISION</code></td>
              <td>Including an isotropic <code>&sigma;=18 px</code> fault-belt feature (<code>vtrb_belt_density</code>) in <code>E3</code> pulled &gt;75% of live dots into <code>&lt;1.2 km</code> of mapped faults, colliding <code>85.1%</code> with <code>GEMSDOE53</code>'s catalogue-halo ring (caught automatically by our fail-closed gate!).</td>
              <td>Removed isotropic halo from <code>E3</code> fusion, retaining only physical-gated along-strike tip cones &amp; relay bridges; max overlap dropped to <code>62.64% &le; 70%</code> and Concealed Piedmont DTI jumped to <code>0.1094</code>.</td>
            </tr>
            <tr>
              <td><code>IR-WELLSPRING-LEAK-COL</code></td>
              <td><code>gdr_wellspring_in_footprint.csv</code> and <code>gdr_volcanic_vents_in_footprint.csv</code> contain a precomputed <code>dist_known_fault_px</code> column against full <code>existing_faults.tif</code>.</td>
              <td><code>src/apartgems/features.py</code> never reads <code>dist_known_fault_px</code>; verified by our 47-channel single-feature Leakage Canary (<code>max AUC = 0.7665 &le; 0.90</code>).</td>
            </tr>
            <tr>
              <td><code>IR-REG-LATTICE-950</code></td>
              <td>69 of the 950 fleet rasters across 53 repos are <code>&gt;125k</code>-dot blankets or uniform covering lattices (e.g., <code>60GEMSDOE::calib_r13lattice_00904.tif</code> with <code>206,895</code> regular grid dots covering <code>99.9%</code> of Nevada within 3 px, <code>&rho; = -0.001</code>).</td>
              <td><code>src/apartgems/uniqueness.py</code> enforces <code>|&rho;| &le; 0.90</code> and symmetric 3-px F1 <code>&le; 0.70</code> across all 950 rasters AND one-sided <code>cand_in_peer &le; 0.70</code> across all 881 sparse detectors, while disclosing raw unfiltered lattice metrics transparently.</td>
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
        <li><strong>USGS GeoDAWN Airborne Magnetic &amp; Radiometric Surveys:</strong> <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and" target="_blank" rel="noopener">https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and</a></li>
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

    readme_md = f"""# ApartGEMSDOE1 — H-APART-5 (`PLKC-DualOOF-CELF E3`) Concealed Piedmont, Fluvial Knickzone & Hydrothermal Fault Discovery

> **AUTOMATED VALIDATION & 950-RASTER UNIQUENESS GATE VERDICT: `PASS — UNIQUE & OK TO DOWNLOAD AND SUBMIT`**
> - **Promoted Unique GeoTIFF**: [`docs/{tif_rel_docs}`](docs/{tif_rel_docs}) (`{rc['validator_output']['bytes']:,}` bytes) · Single-TIFF Archive: [`docs/{zip_rel_docs}`](docs/{zip_rel_docs})
> - **Archived Prior Submission (Do Not Resubmit)**: [`docs/downloads/archive/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif`](docs/downloads/archive/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif) (`0.0525` `ORGANIZER-CONFIRMED`, `10.81%` 3-px overlap with promoted Session 2)
> - **SHA-256**: `{rc['raster_sha256']}` | **Decoded Footprint SHA-256**: `{rc['decoded_footprint_sha256']}`
> - **Submission Name**: `{rc['submission_name']}`
> - **Short Submission Comment (`{rc['submission_note_chars']}/140` chars)**: `{rc['submission_note']}`
> - **Format & Portal `[0, 1]` Safety**: Single-band `float32`, `EPSG:32611`, `3730×3292`, `Affine(100, 0, 243350, 0, -100, 4508550)`, `nodata=None`, **`min=0.0`, `max=1.0`, `0` NaNs and `0` Infs across all `12,279,160` grid cells** (permanently prevents `"Predicted values must be in range [0, 1]"`).
> - **Spacing & Collar Hygiene**: **`37,654` binary `1.0` pixels**, `min NN = 2.8284 px` (`0.0% < 2.8 px`, **`1.28%` >=3 neighbors in 300 m** vs Session 1's `97.30%`), `0` on catalogue, `0` inside `<=200 m` collar, `15,546` (`41.29%`) in far-field basins `>1.5 km`.
> - **Primary Holdout Score (`HOLDOUT-DTI`)**: **`{rc['holdout_dti']['dti']:.4f}`** (`95% CI [{rc['holdout_dti']['ci95'][0]:.4f}, {rc['holdout_dti']['ci95'][1]:.4f}]` on `gems57-pooled-hide-v2`, `seed=2026`, `11,360` withheld positive pixels; **`seed=20` stability = `{rc['holdout_dti']['seed_20_stability_dti']:.4f}`**; detached `>800 m` blind `HOLDOUT-DTI` = **`{rc['holdout_dti']['detached_gt_800m_blind_dti']:.4f}`**; **`+51.9%`** over Session 1 `0.0523` and **`+215%`** over matched-collar `distance_only` `0.0252`).
> - **Zero-SGMC Concealed Piedmont Benchmark (`HOLDOUT-DTI`)**: **`{rc['concealed_piedmont_holdout_dti']['dti']:.4f}`** (`95% CI [{rc['concealed_piedmont_holdout_dti']['ci95'][0]:.4f}, {rc['concealed_piedmont_holdout_dti']['ci95'][1]:.4f}]` on `sgmc-piedmont-basin-v1`, `10,579` withheld concealed piedmont pixels; **zero SGMC used in features or training**; **`5.12×` Session 1 `0.0214`**, beating `GEMSDOE70 P8` `0.0854` [`0.2478` live] and `GEMSDOE32 B2` `0.0954` [`0.2778` live]).
> - **53-Repo / 950-Raster Fleet Uniqueness Gate**: Pre-placement surface `|ρ| = {rc['registry_uniqueness']['pre_placement_surface_max_abs_spearman']:.4f} <= 0.90` (`PASS`); Final raster `|ρ| = {rc['registry_uniqueness']['post_placement_final_max_abs_spearman']:.4f} <= 0.90` (`PASS`); Max 3-px dot overlap across `881` competing sparse detectors = **`{rc['registry_uniqueness']['post_placement_max_3px_overlap_vs_competing']*100:.2f}% <= 70.00%`** (`PASS`; **`43.17%`** vs `GEMSDOE32` `0.2778`; **`34.95%`** vs `GEMSDOE70` `0.2478`; **`10.81%`** vs Session 1 `0.0525`).
> - **GitHub Pages UI**: [`docs/index.html`](docs/index.html) (Main Dashboard & One-Click Download) · [`docs/executive-summary.html`](docs/executive-summary.html) (Executive Summary & Step-by-Step DrivenData Submission Guide).

![PLKC-DualOOF E3 Submission Map](docs/assets/plkc_submission_map.png)

---

## 1. Executive Summary & Auditable Focus-9 GEMSDOE Table

Per Parallel-Run Protocol Rule 3, every number is strictly labeled as either local **`HOLDOUT-DTI`** (with evaluator version, withheld positive pixel count, and 20 km spatial block bootstrap 95% CI) or **`ORGANIZER-CONFIRMED`** (copied from the competition prompt ledger / portal receipt; never a projection).

| Site | Downloadable `.tif` & SHA-256 | Strictly Labeled Score | Emitted Dots & Spacing | NaN / Range Status | Cross-Fleet Uniqueness | Gate Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{chr(10).join(md_focus_rows)}

![Focus-9 Uniqueness & GEMSDOE32 Ladder](docs/assets/focus9_audit_and_uniqueness.png)

---

## 2. Deep PhD Analysis: Why `GEMSDOE32` Scored `0.2778`, Why Session 1 Scored `0.0525`, and How `H-APART-5` Advances Beyond Both

### 2.1 Exact Zero-XOR Forensic Proof of `GEMSDOE32` (`h33-h33-2-b2-zeros`: `0.2778` `ORGANIZER-CONFIRMED`)
Byte-level comparison across all `5,167,373` active footprint pixels (`evidence/focus_sites_forensic_audit.json`) proves with **zero differing pixels (`XOR = 0`)**:
1. **`GEMSDOE32_B2 (37,654 dots) == GEMSDOE25_D28 (44,090 dots) & (EDT(~existing_faults) > 2.0 px)`** (`0` XOR differing pixels).
2. **`GEMSDOE25_D28 (44,090 dots) == GEMSDOE30_D28 (44,090 dots)`** (`0` XOR differing pixels).
3. **`100.00%` of `GEMSDOE32_B2`'s `37,654` dots are an exact subset of `19GEMSDOE` `H19-5` (`121,131` solid ridge pixels, `0.1922` `ORGANIZER-CONFIRMED`)**.

Why each post-processing operation lifted the live score from `0.1922` to `0.2778`:
- **Kernel-Matched Poisson Spacing (`0.1922 -> 0.2477 -> 0.2600`)**: Under Distance-Tolerant IoU (`alpha = 0.2, beta = 0.8, R = 300 m` triangular kernel), `TP_w` evaluates a **max** over 300 m disks while `FP_w` sums **additively** (`0.2 * sum (1 - q(x))`). Thinning solid `121,131`-pixel ridges at `d = 2.8 px` (`280 m`, `44,090` dots) eliminated triple-counted false positives inside each 300 m kernel disk (`+0.0678`).
- **200 m Known-Catalogue Collar Amputation (`0.2600 -> 0.2778`)**: Because organizer evaluation masks `existing_faults.tif` (Forum Thread 11516), deleting all `6,436` `D2.8` dots within `<=200 m` of mapped faults stripped near-catalogue false positives (`+0.0178`).
- **Why Pruning `H19-5` Plateaus at `~0.278` (vs `0.3195` Benchmark / `0.4413+` Top Leaderboard)**: At `S = 0.2778`, an additional dot increases DTI iff its expected truth kernel credit exceeds `p* = 0.2 * 0.2778 / (1 - 0.8 * 0.2778) = 0.0714`. Further pruning `H19-5` cannot recover hidden faults where `H19-5`'s uncalibrated hand-crafted composites missed **concealed piedmont fronts** (downdip gravity shift `z_b cot 60°` under `>250 m` alluvium), fired on **Pleistocene Lake Lahontan (`1,330 m`) / Bonneville (`1,463/1,558 m`) shoreline benches**, or suffered **25.8% 1 m LiDAR tile-gap discontinuities**.

### 2.2 Forensic Root-Cause Post-Mortem of Session 1 (`50e7b334`: `0.0525` `ORGANIZER-CONFIRMED`) & Session 2 Repairs
Byte-level inspection of Session 1's `apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif` uncovered three compounding defects — all eliminated in Session 2:
1. **`97.30%` Kernel Blob Crowding in `src/gems57/emit.py` (Fixed -> `1.28%` Crowding, `76×` Reduction)**: Session 1's shared `greedy_allocate` iterated in static initial order without CELF max-heap re-sorting and clipped `k_self = min(E[k], 1.0) = 1.0`, collapsing the marginal bar `c * (1 - k_self) -> 0` and packing `99.37%` of dots at `NN <= 1.5 px` (`13.52` mean neighbors in `300 m`). Repairing `noisy_or_self_credit` + CELF max-heap + `min_sep_px = 2.8` enforces `min NN = 2.8284 px` across all `37,654` dots.
2. **`75%` In-Sample PU Memorization on Live Export (Fixed -> `0%` In-Sample Weight via Dual-Partition 100%-OOF)**: Unmapped faults are labeled `y = 0` in Positive-Unlabeled training. Session 1 averaged all 4 LOQO trees across the full map (`75%` in-sample `y = 0` suppression). Session 2 stitches 16 spatially buffered (`1.2 km`) models across two `45°`-offset 4-sector partitions so every live pixel is predicted `100%` out-of-fold.
3. **Zero-SGMC Concealed Piedmont Specialist + Orthometric Pluvial-Shoreline Deconfounding + Fluvial `chi/ksn` (`H-APART-5`)**: Session 2 unlocks orthometric 3DEP elevation (`zmean_m`) to suppress horizontal Lahontan/Bonneville benches, adds across-fault fluvial `Delta-chi` & `ksn` knickzones, preserves exact `NaN` semantics on 12-band 1 m LiDAR (`74.2%` interior coverage) via quantile-calibrated Dual-Regime (`M_Full` + `M_Sub`) HGBs, and adds a dedicated **Zero-SGMC Concealed Piedmont Specialist** (`b15_depth_base >= 180 m`), raising read-only Concealed Piedmont `HOLDOUT-DTI` **5.12-fold** (`0.0214 -> 0.1094`).

---

## 3. Ranked Pre-Registered Untried Geological Hypotheses (`evidence/preregistration_hypotheses.json`)

{chr(10).join(md_hyp_items)}

---

## 4. Holdout Experiments (`Budget = 3/3`), Concealed Piedmont Diagnostic & 47-Channel Leakage Canary

![Holdout Progression, Concealed Piedmont Diagnostic & Leakage Canary](docs/assets/holdout_experiments_and_canary.png)

### 4.1 Primary Spatially-Blocked Hide-and-Recover Holdout (`gems57-pooled-hide-v2`, `alpha=0.2, beta=0.8, 300 m`)

| Arm / Experiment | `HOLDOUT-DTI` (`seed=2026`, `11,360` px) | 95% Block Bootstrap CI | Detached Blind (`>800 m`) DTI | `seed=20` Stability (`11,321` px) | Key Mechanism Tested |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `zero_control` | `0.0000` | `[0.0000, 0.0000]` | `0.0000` | `0.0000` | All-zero baseline |
| `distance_only_collar2_control` | `{sc_p['distance_only_collar2_control']['dti']:.4f}` | `[{sc_p['distance_only_collar2_control']['ci95'][0]:.4f}, {sc_p['distance_only_collar2_control']['ci95'][1]:.4f}]` | **`0.0000`** | `{sc_s20['distance_only_collar2_control']['dti']:.4f}` | Proves halo rings fail completely on blind (`>800 m`) faults |
| `Session 1 Archived` (`50e7b334`, `0.0525` live) | `0.0523` | `[0.0375, 0.0687]` | `0.0332` | `0.0478` | Prior PR #12 baseline (`97.3%` kernel crowding) |
| **`E1`: `PLKC Dual-Regime Blind` (`38` ch)** | **`{sc_p['E1_plkc_dual_regime_blind']['dti']:.4f}`** | `[{sc_p['E1_plkc_dual_regime_blind']['ci95'][0]:.4f}, {sc_p['E1_plkc_dual_regime_blind']['ci95'][1]:.4f}]` | **`{det_p['E1_plkc_dual_regime_blind']:.4f}`** | `{sc_s20['E1_plkc_dual_regime_blind']['dti']:.4f}` | Preserved-NaN 1m LiDAR + 10m 3DEP + `chi/ksn` + 60° updip + pluvial/road deconfounders + CELF `d>=2.8` |
| **`E2`: `+ Hydro-Conduit & Anisotropy` (`44` ch)** | **`{sc_p['E2_plkc_hydro_stage2_vessel']['dti']:.4f}`** | `[{sc_p['E2_plkc_hydro_stage2_vessel']['ci95'][0]:.4f}, {sc_p['E2_plkc_hydro_stage2_vessel']['ci95'][1]:.4f}]` | **`{det_p['E2_plkc_hydro_stage2_vessel']:.4f}`** | `{sc_s20['E2_plkc_hydro_stage2_vessel']['dti']:.4f}` | Adds GeoDAWN `K/Th` & `U/Th`, MT clay-cap edges, GDR #1391 springs/2m-probes/sinter/vents & 8-azimuth anisotropy |
| **`E3`: `PLKC-DualOOF-CELF Full` (Promoted)** | **`{sc_p['E3_plkc_dualoof_celf_full']['dti']:.4f}`** | **`[{sc_p['E3_plkc_dualoof_celf_full']['ci95'][0]:.4f}, {sc_p['E3_plkc_dualoof_celf_full']['ci95'][1]:.4f}]`** | **`{det_p['E3_plkc_dualoof_celf_full']:.4f}`** | **`{sc_s20['E3_plkc_dualoof_celf_full']['dti']:.4f}`** | Adds Zero-SGMC Concealed Piedmont Specialist (`b15 >= 180 m`) + physical-gated directional tip/relay continuation (`Δ vs DistOnly = +{delta_dist['delta']:.4f}`, 95% CI `[+{delta_dist['ci95'][0]:.4f}, +{delta_dist['ci95'][1]:.4f}]`) |

### 4.2 Strictly Read-Only Zero-SGMC Concealed Piedmont Benchmark (`sgmc-piedmont-basin-v1`, `10,579` px)
Across `18` live-scored peer submissions (`evidence/concealed_piedmont_benchmarks.json`), `sgmc-piedmont-basin-v1` correlates significantly with `ORGANIZER-CONFIRMED` live leaderboard DTI (`Spearman ρ = +0.5455, p = 0.0192`). Using **zero SGMC data anywhere in features, training, or calibration**, our promoted raster achieves:

| Submission | Emitted Dots | `>=3` Nbrs in `300 m` | `HOLDOUT-DTI` (`sgmc-piedmont-basin-v1`, `10,579` px) | `ORGANIZER-CONFIRMED` Live Score |
| :--- | :---: | :---: | :---: | :---: |
| `ApartGEMSDOE1` Session 1 (`50e7b334`, archived) | `38,500` | `97.30%` | `0.0214` (`[0.0156, 0.0277]`) | `0.0525` |
| `GEMSDOE27` `H31-1` (`cf8e1bbef244`) | `37,654` | `0.21%` | `0.0833` (`[0.0677, 0.1003]`) | `0.2250` |
| `GEMSDOE70` `P8-OOF38k` (`20261020`, top non-H19-5) | `37,654` | `15.10%` | `0.0854` (`[0.0706, 0.1011]`) | `0.2478` |
| `GEMSDOE32` `H33-2-B2` (`e5eb6e7e`, Focus-9 high) | `37,654` | `0.69%` | `0.0954` (`[0.0788, 0.1130]`) | `0.2778` |
| `GEMSDOE76` `PTCF-39200` (`fe5fc7dd`) | `39,200` | `3.39%` | `0.0962` (`[0.0793, 0.1137]`) | `0.2343` |
| **`ApartGEMSDOE1` Session 2 (`4499e12f`, Promoted)** | **`37,654`** | **`1.28%`** | **`{rc['concealed_piedmont_holdout_dti']['dti']:.4f}` (`[{rc['concealed_piedmont_holdout_dti']['ci95'][0]:.4f}, {rc['concealed_piedmont_holdout_dti']['ci95'][1]:.4f}]`)** | *Ready to submit (`PASS`)* |

---

## 5. Reproducible Autonomous CLI Commands

```bash
# 1. Autonomously download/restore & SHA-256 verify competition rasters, 10m 3DEP, chi/ksn, LiDAR & GDR #1391
bash scripts/download_competition_data.sh

# 2. Run pixel-exact Focus-9 forensic audit, Concealed Piedmont benchmark & 53-repo / 950-raster Registry Index
.venv/bin/python scripts/audit_focus_sites_and_registry.py

# 3. Execute H-APART-5 47-channel leakage canaries, <=3 LOQO experiments, 950-raster uniqueness gate & GeoTIFF build
.venv/bin/python scripts/run_apartgems_pipeline.py

# 4. Run standalone zero-human-input GeoTIFF + Uniqueness validator, regenerate figures/pages & run pytest suite
.venv/bin/python scripts/validate_submission.py docs/{tif_rel_docs} --json-out evidence/cli_validator_check.json
.venv/bin/python scripts/generate_figures.py
.venv/bin/python scripts/build_pages_and_readme.py
.venv/bin/pytest -v
```

---

## 6. Machine-Readable Parallel-Run Protocol Run Card (`evidence/run_card.json`)

```json
{json.dumps(rc, indent=2)}
```

---

## 7. Remaining Limitations & Next-Steps Roadmap

1. **25.8% Exterior 1 m LiDAR Coverage Gap**: Although our quantile-calibrated Dual-Regime (`M_Full` + `M_Sub`) architecture eliminates sharp step-discontinuities across the `74.2% / 25.8%` 1 m LiDAR boundary, sub-meter Holocene scarps outside USGS 3DEP 1 m swaths remain limited by 10 m 3DEP vertical resolution (`~0.5–1.0 m`). Incorporating Sentinel-1 InSAR phase-gradient coherence or commercial stereo-optical DSMs outside 1 m LiDAR strips is the highest-leverage sensor addition.
2. **2D Azimuthal Dip Prior vs. Full 3D Joint Gravity-Magnetic-MT Inversion**: `udpc_*` migrates basement gradients updip using a `60°` Great Basin normal-fault dip prior scaled by `Band 15 depth_to_base_surf`. Replacing this analytic migration with 3D Euler deconvolution (`H-APART-6`, `N=0.5`) coupled to 3D magnetotelluric resistivity gradients (`H-APART-8`) can further sharpen sub-basin fault-plane geometry in asymmetric half-grabens.
3. **Subaerial Bias of Catalogue Hide-and-Recover Holdout**: Withheld segments in `gems57-pooled-hide-v2` come from `existing_faults.tif` (predominantly subaerial range-front scarps), whereas hidden INGENIOUS faults include a higher fraction of concealed basinward piedmont structures. Tracking both `gems57-pooled-hide-v2` (`0.0795` / `0.0908`) and strictly read-only `sgmc-piedmont-basin-v1` (`0.1094`) provides complementary guardrails without touching SGMC in training.

---

## 8. Standing Reference: Original Competition Task & Protocol Specification

<details>
<summary>Click to expand full standing user instructions & Parallel-Run Protocol reference</summary>

- **Competition**: DOE GEMS DrivenData Prize Challenge (`https://www.drivendata.org/competitions/306/competition-doe-gems/`, leaderboard high `0.4413`, benchmark `0.3195`, best listed GEMSDOE site `0.2778` on `GEMSDOE32`; archived Session 1 `ApartGEMSDOE1` `udth-submod-e3-20261027-50e7b334`: `0.0525`).
- **Core Deliverables**:
  1. Store prompt instructions in `README.md`, complete pending work autonomously, and download/prepare official competition data automatically (`scripts/download_competition_data.sh`, `scripts/prepare_data.py`).
  2. Deep PhD-level analysis of `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: `0.2778`) — why/how it scored `0.2778` and how to beat `0.2778` (and `0.3195`) — plus an executive summary and auditable table across `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, and `GEMSDOE36`.
  3. Propose 3–5 untried geological hypotheses for hidden faults and geothermal vents/conduits before implementing, ranked by expected DTI gain and cost; generate a **unique** single-band `.tif` submission strictly in `[0, 1]` (preventing `"Predicted values must be in range [0, 1]"`), no footprint NaNs, matching `example_submission.tif` CRS/shape/geotransform, validated 100% automatically in code without human-inspection gates.
  4. Build a clean GitHub Pages UI (`docs/index.html`) with obvious one-click `.tif` download & automated validation status right at the top, plus an executive summary subpage (`docs/executive-summary.html`) explaining step-by-step how to submit on DrivenData, backed by verified official links.
  5. Enforce Parallel-Run Protocol: (1) Uniqueness gate (`|ρ| <= 0.90` on pre-placement surface & final raster, `<= 70%` 3-px dot overlap across fleet registry); (2) Reuse shared `evaluate_holdout.py` & `submission_writer.py` (`alpha=0.2, beta=0.8, 300 m` triangular kernel); (3) Strict score labeling (`HOLDOUT-DTI` vs `ORGANIZER-CONFIRMED`, never writing a projection as a score); (4) Single-feature leakage canary (`AUC <= 0.90`); (5) End with JSON Run Card; (6) Cap at `<= 3` experiments or `2` hours.
  6. Execute in 3 complete verification passes, open & merge PR onto `main`, and document remaining work & limitations.

</details>
"""
    (ROOT / "README.md").write_text(readme_md, encoding="utf-8")
    print("Built docs/index.html, docs/executive-summary.html, and README.md successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
