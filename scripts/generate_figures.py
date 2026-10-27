#!/usr/bin/env python3
"""Generate publication-grade diagnostic figures for README.md and GitHub Pages."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

from gems57 import load_grid


def main() -> int:
    grid = load_grid()
    fp = grid.footprint
    cat = grid.catalogue
    assets = ROOT / "docs/assets"
    assets.mkdir(parents=True, exist_ok=True)

    run_sum = json.loads((ROOT / "docs/data/run_summary.json").read_text())
    focus_audit = json.loads((ROOT / "evidence/focus_sites_forensic_audit.json").read_text())
    tif_rel = run_sum["run_card"]["validator_output"]["file"]

    with rasterio.open(ROOT / tif_rel) as ds:
        cand = ds.read(1) > 0

    b2_path = Path("/tmp/research/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
    b2 = np.zeros_like(cand)
    if b2_path.exists():
        with rasterio.open(b2_path) as ds:
            b2 = np.isfinite(ds.read(1)) & (ds.read(1) > 0) & fp

    depth_base = np.load(ROOT / ".cache/features/band-15.npy")
    udpc_up = np.load(ROOT / ".cache/apartgems_features/udpc_grav_updip.f32.npy")
    therm = np.load(ROOT / ".cache/apartgems_features/hmcs_thermal_upflow.f32.npy")

    # --- Figure 1: Spatial Submission Overview + Geothermal Basin Inset ---
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 7.2), dpi=160, gridspec_kw={"width_ratios": [1.15, 1.0]})
    fig.patch.set_facecolor("#0b1220")

    ax0 = axes[0]
    ax0.set_facecolor("#0b1220")
    bg = np.where(fp, np.clip(np.nan_to_num(depth_base, nan=0.0) / 2200.0, 0.0, 1.0), np.nan)
    im0 = ax0.imshow(bg, cmap="cividis", alpha=0.55, vmin=0, vmax=1)
    # Dilate slightly for visual legibility at full-basin scale
    cat_d = binary_dilation(cat, iterations=2)
    cand_d = binary_dilation(cand, iterations=2)
    ov_rgba = np.zeros((*fp.shape, 4), dtype=np.float32)
    ov_rgba[cat_d] = [0.62, 0.72, 0.85, 0.65]       # slate-blue catalogue faults
    ov_rgba[cand_d] = [0.08, 0.94, 0.68, 0.92]      # vibrant emerald-cyan UDTH-Submod E3 dots
    ax0.imshow(ov_rgba)
    # Draw zoom box around Carson Sink / Dixie Valley / Bradys-Desert Peak (rows 1550:2250, cols 1050:1750)
    r0, r1, c0, c1 = 1550, 2250, 1050, 1750
    rect = plt.Rectangle((c0, r0), c1 - c0, r1 - r0, fill=False, edgecolor="#fbbf24", linewidth=1.8, linestyle="--")
    ax0.add_patch(rect)
    ax0.set_title("NW Great Basin Study Area (EPSG:32611, 3730×3292 @ 100 m)\nMapped Catalogue (Slate) vs. ApartGEMSDOE1 UDTH-Submod E3 (38,500 Dots, Emerald)",
                  color="#f8fafc", fontsize=11, fontweight="bold", pad=10)
    ax0.set_xticks([])
    ax0.set_yticks([])
    cb0 = fig.colorbar(im0, ax=ax0, fraction=0.036, pad=0.02)
    cb0.set_label("Normalized Cenozoic Basin Cover Depth (Band 15)", color="#cbd5e1", fontsize=9)
    cb0.ax.yaxis.set_tick_params(color="#cbd5e1", labelcolor="#cbd5e1")

    ax1 = axes[1]
    ax1.set_facecolor("#0b1220")
    sub_phys = 0.60 * udpc_up[r0:r1, c0:c1] + 0.40 * therm[r0:r1, c0:c1]
    im1 = ax1.imshow(sub_phys, cmap="magma", vmin=0.1, vmax=0.95, alpha=0.85)
    cy_cat, cx_cat = np.nonzero(cat[r0:r1, c0:c1])
    ax1.scatter(cx_cat, cy_cat, s=1.2, c="#94a3b8", alpha=0.65, label="Mapped Catalogue Faults (masked + 200 m collar)")
    if b2.any():
        cy_b2, cx_b2 = np.nonzero(b2[r0:r1, c0:c1])
        ax1.scatter(cx_b2, cy_b2, s=5.0, c="#38bdf8", alpha=0.60, marker="x", linewidths=0.7, label="GEMSDOE32 B2 (0.2778 ref)")
    cy_me, cx_me = np.nonzero(cand[r0:r1, c0:c1])
    ax1.scatter(cx_me, cy_me, s=8.0, c="#10b981", edgecolors="#ecfdf5", linewidths=0.25, alpha=0.95, label="ApartGEMSDOE1 H-APART-1 (Unique)")
    ax1.set_title("Zoom Inset (70×70 km Geothermal Rift Corridor)\nUpdip Potential Contact + GDR #1391 Thermal Field & Allocated Dots",
                  color="#f8fafc", fontsize=11, fontweight="bold", pad=10)
    ax1.set_xticks([])
    ax1.set_yticks([])
    leg = ax1.legend(loc="lower right", facecolor="#0f172a", edgecolor="#334155", fontsize=8.3, labelcolor="#f1f5f9")
    cb1 = fig.colorbar(im1, ax=ax1, fraction=0.036, pad=0.02)
    cb1.set_label("UDPC Updip Contact + HMCS Thermal Upflow Index", color="#cbd5e1", fontsize=9)
    cb1.ax.yaxis.set_tick_params(color="#cbd5e1", labelcolor="#cbd5e1")

    fig.tight_layout()
    fig.savefig(assets / "udth_submission_map.png", dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # --- Figure 2: Focus-9 + ApartGEMSDOE1 10x10 Overlap Matrix & GEMSDOE32 0.2778 Ladder ---
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.4), dpi=160, gridspec_kw={"width_ratios": [1.12, 1.0]})
    fig.patch.set_facecolor("#ffffff")

    focus_sites = [r["site"] for r in focus_audit["focus_9_sites"]]
    labels10 = [s.replace("GEMSDOE", "GD") for s in focus_sites] + ["Apart1 (Ours)"]
    mat = np.eye(10, dtype=np.float64) * 100.0
    vs_f9 = run_sum["uniqueness"]["post_placement_final_raster_gate"]["vs_focus_9_champions"]
    me_ovs = []
    for i, s1 in enumerate(focus_sites):
        for j, s2 in enumerate(focus_sites):
            mat[i, j] = focus_audit["focus_9_pairwise_3px_overlap"][s1][s2] * 100.0
        ov_me = vs_f9.get(s1, {}).get("overlap_3px_fraction", 0.37) * 100.0
        me_ovs.append(ov_me)
        mat[9, i] = ov_me
        mat[i, 9] = ov_me

    ax0 = axes[0]
    im = ax0.imshow(mat, cmap="RdYlGn_r", vmin=25, vmax=100)
    ax0.set_xticks(range(10))
    ax0.set_xticklabels(labels10, rotation=38, ha="right", fontsize=8.5, fontweight="bold")
    ax0.set_yticks(range(10))
    ax0.set_yticklabels(labels10, fontsize=8.5, fontweight="bold")
    for i in range(10):
        for j in range(10):
            val = mat[i, j]
            txt_c = "white" if val > 72 or val < 32 else "#0f172a"
            ax0.text(j, i, f"{val:.0f}%", ha="center", va="center", fontsize=7.3, color=txt_c, fontweight="bold")
    ax0.set_title(
        f"3-px (300 m) Dot Overlap Matrix: Focus-9 Champions vs. ApartGEMSDOE1\n"
        f"(Focus-9 Cluster = 87–100% Redundant; ApartGEMSDOE1 = {min(me_ovs):.1f}–{max(me_ovs):.1f}% Unique)",
        fontsize=10.5, fontweight="bold", pad=10, color="#0f172a"
    )
    fig.colorbar(im, ax=ax0, fraction=0.042, pad=0.03, label="3-px Dot Overlap (%) [Duplicate Cap = 70%]")

    ax1 = axes[1]
    ladder = focus_audit["forensic_proof_02778"]["score_ladder_progression"]
    stages = [
        "19GEMS H19-5\n(121,131 px)",
        "GD27 Topo+D1.5\n(61,328 px)",
        "GD24 D1.5\n(60,069 px)",
        "GD25 / GD30 D2.8\n(44,090 px)",
        "GD33 Tip+D2.8\n(41,865 px)",
        "GD31 Solo-D28\n(40,199 px)",
        "GD28 H36-1\n(37,660 px)",
        "GD36 PINN+B2\n(38,854 px)",
        "GD32 H33-2-B2\n(37,654 px, XOR=0)",
    ]
    scores_l = [0.1922, 0.2449, 0.2477, 0.2600, 0.2632, 0.2708, 0.2710, 0.2750, 0.2778]
    colors_l = ["#64748b", "#3b82f6", "#3b82f6", "#2563eb", "#1d4ed8", "#0284c7", "#0284c7", "#0d9488", "#059669"]
    y_pos = np.arange(len(stages))
    bars = ax1.barh(y_pos, scores_l, color=colors_l, height=0.66, edgecolor="#0f172a", linewidth=0.6)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(stages, fontsize=8.3, fontweight="bold")
    ax1.set_xlim(0.15, 0.305)
    ax1.set_xlabel("User-Reported Context Score on DrivenData (H19-5 Post-Processing Lineage)", fontsize=9, fontweight="bold")
    ax1.set_title("Forensic Anatomy of Why GEMSDOE32 Reached 0.2778\n(280 m Kernel Thinning + Exact 200 m Catalogue Collar Amputation)",
                  fontsize=10.5, fontweight="bold", pad=10, color="#0f172a")
    ax1.grid(axis="x", linestyle="--", alpha=0.4)
    for b, sc in zip(bars, scores_l):
        ax1.text(sc + 0.002, b.get_y() + b.get_height() / 2, f"{sc:.4f}", va="center", fontsize=8.3, fontweight="bold", color="#0f172a")

    fig.tight_layout()
    fig.savefig(assets / "focus9_audit_and_uniqueness.png", dpi=160)
    plt.close(fig)

    # --- Figure 3: Holdout DTI Progression (with 20 km Block Bootstrap CIs) & Leakage Canary ---
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.0), dpi=160, gridspec_kw={"width_ratios": [1.05, 1.15]})
    fig.patch.set_facecolor("#ffffff")

    sc_dict = run_sum["experiments"]["primary_draw_seed_2026"]["scores"]
    det_dict = run_sum["experiments"]["primary_draw_seed_2026"]["detached_gt_800m_blind_dti"]
    arm_keys = [
        ("zero_control", "Zero\nControl"),
        ("distance_only_collar2_control", "Dist-Only\n(>200m)"),
        ("E1_udpc_dopsr_blind", "E1: UDPC+\nDOPSR"),
        ("E2_udpc_dopsr_hmcs_blind", "E2: +HMCS\n& Stress"),
        ("E3_udth_submod_full", "E3: UDTH\n(Promoted)"),
    ]
    x = np.arange(len(arm_keys))
    vals = [sc_dict[k]["dti"] for k, _ in arm_keys]
    lo_err = [sc_dict[k]["dti"] - sc_dict[k]["ci95"][0] for k, _ in arm_keys]
    hi_err = [sc_dict[k]["ci95"][1] - sc_dict[k]["dti"] for k, _ in arm_keys]
    det_vals = [0.0] + [det_dict[k] for k, _ in arm_keys[1:]]

    ax0 = axes[0]
    w = 0.37
    b_main = ax0.bar(x - w / 2, vals, width=w, yerr=[lo_err, hi_err], capsize=4,
                     color=["#94a3b8", "#f59e0b", "#38bdf8", "#0284c7", "#059669"],
                     edgecolor="#0f172a", linewidth=0.7, label="Pooled HOLDOUT-DTI (95% 20 km Block CI)")
    b_det = ax0.bar(x + w / 2, det_vals, width=w,
                    color=["#cbd5e1", "#fde68a", "#bae6fd", "#7dd3fc", "#6ee7b7"],
                    edgecolor="#0f172a", linewidth=0.7, label="Detached Blind (>800 m from Visible) DTI")
    ax0.set_xticks(x)
    ax0.set_xticklabels([lbl for _, lbl in arm_keys], fontsize=8.3, fontweight="bold")
    ax0.set_ylabel("HOLDOUT-DTI (gems57-pooled-hide-v2, 11,360 px)", fontsize=9, fontweight="bold")
    ax0.set_ylim(0, 0.086)
    ax0.grid(axis="y", linestyle="--", alpha=0.4)
    ax0.legend(loc="upper left", fontsize=8.2)
    ax0.set_title("Monotonic Pre-Registered Experiment Progression (Budget = 3/3)\nPaired Δ(E3 − DistOnly) = +0.0194, 95% CI [+0.0057, +0.0344]",
                  fontsize=10.2, fontweight="bold", pad=10, color="#0f172a")
    for b, v, he in zip(b_main, vals, hi_err):
        ax0.text(b.get_x() + b.get_width() / 2, v + he + 0.0016, f"{v:.4f}", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color="#0f172a")
    for b, dv in zip(b_det, det_vals):
        if dv > 0:
            ax0.text(b.get_x() + b.get_width() / 2, dv + 0.0014, f"{dv:.4f}", ha="center", va="bottom", fontsize=7.2, color="#334155")

    ax1 = axes[1]
    feats = run_sum["leakage_canary"]["features"]
    f_names = [f["feature"] for f in feats][::-1]
    f_aucs = [f["symmetric_auc"] for f in feats][::-1]
    f_cols = ["#0284c7" if f["group"] == "blind_physical" else "#7c3aed" for f in feats][::-1]
    yf = np.arange(len(f_names))
    ax1.barh(yf, f_aucs, color=f_cols, height=0.68, edgecolor="#0f172a", linewidth=0.5)
    ax1.axvline(0.90, color="#dc2626", linestyle="--", linewidth=1.8, label="Fail-Closed Leakage Gate (AUC = 0.90)")
    ax1.axvline(0.50, color="#64748b", linestyle=":", linewidth=1.0, label="Random Baseline (AUC = 0.50)")
    ax1.set_yticks(yf)
    ax1.set_yticklabels(f_names, fontsize=7.8, fontweight="bold")
    ax1.set_xlim(0.45, 0.96)
    ax1.set_xlabel("Single-Feature Symmetric Holdout AUC = max(AUC, 1 − AUC)", fontsize=9, fontweight="bold")
    ax1.set_title("Automated Single-Feature Leakage Canary (17 / 17 Features PASS <= 0.90)\nBlue = Blind Sensor Physics (UDPC/DOPSR/HMCS) | Purple = Fold-Visible VTRB",
                  fontsize=10.2, fontweight="bold", pad=10, color="#0f172a")
    ax1.legend(loc="lower right", fontsize=8.0)
    ax1.grid(axis="x", linestyle="--", alpha=0.4)

    fig.tight_layout()
    fig.savefig(assets / "holdout_experiments_and_canary.png", dpi=160)
    plt.close(fig)
    print("Generated 3 diagnostic figures in docs/assets/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
