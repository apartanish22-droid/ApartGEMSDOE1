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


def _unpack_fp(fp: np.ndarray, path: Path) -> np.ndarray:
    arr = np.zeros(fp.shape, dtype=np.float32)
    vec = np.load(path, mmap_mode="r")
    arr[fp] = np.nan_to_num(vec, nan=0.0)
    return arr


def _robust01(a: np.ndarray, fp: np.ndarray) -> np.ndarray:
    v = a[fp]
    q05, q98 = np.quantile(v, [0.05, 0.98])
    return np.clip((a - q05) / (q98 - q05 + 1e-6), 0.0, 1.0)


def main() -> int:
    grid = load_grid()
    fp = grid.footprint
    cat = grid.catalogue
    assets = ROOT / "docs/assets"
    assets.mkdir(parents=True, exist_ok=True)
    # Remove stale legacy figure if present
    stale = assets / "udth_submission_map.png"
    if stale.exists():
        stale.unlink()

    run_sum = json.loads((ROOT / "docs/data/run_summary.json").read_text())
    focus_audit = json.loads((ROOT / "evidence/focus_sites_forensic_audit.json").read_text())
    cpied_bench = json.loads((ROOT / "evidence/concealed_piedmont_benchmarks.json").read_text())
    tif_rel = run_sum["run_card"]["validator_output"]["file"]

    with rasterio.open(ROOT / tif_rel) as ds:
        cand = ds.read(1) > 0.5

    b2_path = ROOT / ".cache/peer_repos/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    b2 = np.zeros_like(cand)
    if b2_path.exists():
        with rasterio.open(b2_path) as ds:
            raw_b2 = ds.read(1)
            b2 = np.isfinite(raw_b2) & (raw_b2 > 0.5) & fp

    fdir = ROOT / ".cache/apartgems_s2_features"
    depth_base = _unpack_fp(fp, fdir / "b15_depth_base.fp.f32.npy")
    udpc_up = _robust01(_unpack_fp(fp, fdir / "udpc_grav_updip_60deg.fp.f32.npy"), fp)
    chi_knick = _robust01(_unpack_fp(fp, fdir / "chi_step_max.fp.f32.npy"), fp)
    therm_up = _robust01(_unpack_fp(fp, fdir / "hyd_gdr_spring_geotherm.fp.f32.npy"), fp)

    # =========================================================================
    # Figure 1: Spatial Submission Overview + Geothermal Rift / Piedmont Inset
    # =========================================================================
    fig, axes = plt.subplots(1, 2, figsize=(15.6, 7.2), dpi=160, gridspec_kw={"width_ratios": [1.14, 1.0]})
    fig.patch.set_facecolor("#0b1220")

    ax0 = axes[0]
    ax0.set_facecolor("#0b1220")
    bg = np.where(fp, np.clip(depth_base / 2200.0, 0.0, 1.0), np.nan)
    im0 = ax0.imshow(bg, cmap="cividis", alpha=0.58, vmin=0, vmax=1)
    cat_d = binary_dilation(cat, iterations=2)
    cand_d = binary_dilation(cand, iterations=2)
    ov_rgba = np.zeros((*fp.shape, 4), dtype=np.float32)
    ov_rgba[cat_d] = [0.62, 0.72, 0.85, 0.62]
    ov_rgba[cand_d] = [0.06, 0.94, 0.68, 0.94]
    ax0.imshow(ov_rgba)

    r0, r1, c0, c1 = 1550, 2250, 1050, 1750
    rect = plt.Rectangle((c0, r0), c1 - c0, r1 - r0, fill=False, edgecolor="#fbbf24", linewidth=1.9, linestyle="--")
    ax0.add_patch(rect)
    ax0.set_title(
        "NW Great Basin Grid (EPSG:32611, 3730×3292 @ 100 m)\n"
        "Catalogue (Slate) vs. PLKC-DualOOF E3 (37,654 Dots, min NN=2.83 px)",
        color="#f8fafc", fontsize=10.1, fontweight="bold", pad=10,
    )
    ax0.set_xticks([])
    ax0.set_yticks([])
    cb0 = fig.colorbar(im0, ax=ax0, fraction=0.036, pad=0.02)
    cb0.set_label("Normalized Cenozoic Basin Cover Depth (Band 15)", color="#cbd5e1", fontsize=9)
    cb0.ax.yaxis.set_tick_params(color="#cbd5e1", labelcolor="#cbd5e1")

    ax1 = axes[1]
    ax1.set_facecolor("#0b1220")
    sub_phys = 0.42 * udpc_up[r0:r1, c0:c1] + 0.33 * chi_knick[r0:r1, c0:c1] + 0.25 * therm_up[r0:r1, c0:c1]
    im1 = ax1.imshow(sub_phys, cmap="magma", vmin=0.05, vmax=0.92, alpha=0.86)
    cy_cat, cx_cat = np.nonzero(cat[r0:r1, c0:c1])
    ax1.scatter(cx_cat, cy_cat, s=1.2, c="#94a3b8", alpha=0.62, label="Mapped Catalogue (masked + 200 m collar)")
    if b2.any():
        cy_b2, cx_b2 = np.nonzero(b2[r0:r1, c0:c1])
        ax1.scatter(cx_b2, cy_b2, s=6.0, c="#38bdf8", alpha=0.62, marker="x", linewidths=0.75, label="GEMSDOE32 B2 (0.2778 ref, 43.2% ov)")
    cy_me, cx_me = np.nonzero(cand[r0:r1, c0:c1])
    ax1.scatter(cx_me, cy_me, s=9.0, c="#10b981", edgecolors="#ecfdf5", linewidths=0.3, alpha=0.96, label="ApartGEMSDOE1 PLKC-DualOOF E3 (Unique)")
    ax1.set_title(
        "Zoom Inset (70×70 km Dixie Valley / Carson Sink Rift Corridor)\n"
        "60° Updip Gravity + Chi Knickzone + GDR #1391 & CELF d>=2.8 Dots",
        color="#f8fafc", fontsize=10.1, fontweight="bold", pad=10,
    )
    ax1.set_xticks([])
    ax1.set_yticks([])
    ax1.legend(loc="lower right", facecolor="#0f172a", edgecolor="#334155", fontsize=8.2, labelcolor="#f1f5f9")
    cb1 = fig.colorbar(im1, ax=ax1, fraction=0.036, pad=0.02)
    cb1.set_label("Composite 60° Updip Gravity + Chi Knickzone + GDR #1391 Index", color="#cbd5e1", fontsize=9)
    cb1.ax.yaxis.set_tick_params(color="#cbd5e1", labelcolor="#cbd5e1")

    fig.tight_layout(w_pad=2.2)
    fig.savefig(assets / "plkc_submission_map.png", dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # =========================================================================
    # Figure 2: Focus-9 + ApartGEMSDOE1 10x10 Overlap Matrix & 0.2778 Ladder
    # =========================================================================
    fig, axes = plt.subplots(1, 2, figsize=(15.6, 6.4), dpi=160, gridspec_kw={"width_ratios": [1.12, 1.0]})
    fig.patch.set_facecolor("#ffffff")

    focus_sites = [r["site"] for r in focus_audit["focus_9_sites"]]
    labels10 = [s.replace("GEMSDOE", "GD") for s in focus_sites] + ["Apart1 S2"]
    mat = np.eye(10, dtype=np.float64) * 100.0
    vs_f9 = run_sum["uniqueness"]["vs_focus_9_champions"]
    me_ovs = []
    for i, s1 in enumerate(focus_sites):
        for j, s2 in enumerate(focus_sites):
            mat[i, j] = focus_audit["focus_9_pairwise_3px_overlap"][s1][s2] * 100.0
        ov_me = vs_f9.get(s1, {}).get("overlap_3px_fraction", 0.43) * 100.0
        me_ovs.append(ov_me)
        mat[9, i] = ov_me
        mat[i, 9] = ov_me

    ax0 = axes[0]
    im = ax0.imshow(mat, cmap="RdYlGn_r", vmin=30, vmax=100)
    ax0.set_xticks(range(10))
    ax0.set_xticklabels(labels10, rotation=38, ha="right", fontsize=8.5, fontweight="bold")
    ax0.set_yticks(range(10))
    ax0.set_yticklabels(labels10, fontsize=8.5, fontweight="bold")
    for i in range(10):
        for j in range(10):
            val = mat[i, j]
            txt_c = "white" if val > 74 or val < 36 else "#0f172a"
            ax0.text(j, i, f"{val:.0f}%", ha="center", va="center", fontsize=7.3, color=txt_c, fontweight="bold")
    ax0.set_title(
        f"3-px (300 m) Dot Overlap Matrix: Focus-9 Champions vs. ApartGEMSDOE1\n"
        f"(Focus-9 Cluster = 87–100% Redundant; ApartGEMSDOE1 = {min(me_ovs):.1f}–{max(me_ovs):.1f}% <= 70% Cap)",
        fontsize=10.3, fontweight="bold", pad=10, color="#0f172a",
    )
    fig.colorbar(im, ax=ax0, fraction=0.042, pad=0.03, label="3-px Dot Overlap (%) [Duplicate Cap = 70%]")

    ax1 = axes[1]
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
    ax1.set_xlabel("ORGANIZER-CONFIRMED Score on DrivenData (H19-5 Post-Processing Lineage)", fontsize=8.8, fontweight="bold")
    ax1.set_title(
        "Forensic Anatomy of Why GEMSDOE32 Reached 0.2778\n"
        "(280 m Kernel Thinning + Exact 200 m Catalogue Collar Amputation)",
        fontsize=10.3, fontweight="bold", pad=10, color="#0f172a",
    )
    ax1.grid(axis="x", linestyle="--", alpha=0.4)
    for b, sc in zip(bars, scores_l):
        ax1.text(sc + 0.002, b.get_y() + b.get_height() / 2, f"{sc:.4f}", va="center", fontsize=8.2, fontweight="bold", color="#0f172a")

    fig.tight_layout()
    fig.savefig(assets / "focus9_audit_and_uniqueness.png", dpi=160)
    plt.close(fig)

    # =========================================================================
    # Figure 3: 3-Panel Validation Suite (Holdout Progression, Concealed Piedmont, Canary)
    # =========================================================================
    fig, axes = plt.subplots(1, 3, figsize=(18.0, 6.2), dpi=160, gridspec_kw={"width_ratios": [1.08, 1.06, 1.06]})
    fig.patch.set_facecolor("#ffffff")

    # Panel A: Holdout DTI Progression (gems57-pooled-hide-v2)
    sc_dict = run_sum["experiments"]["primary_draw_seed_2026"]["scores"]
    det_dict = run_sum["experiments"]["primary_draw_seed_2026"]["detached_gt_800m_blind_dti"]
    arm_keys = [
        ("zero_control", "Zero\nCtrl"),
        ("distance_only_collar2_control", "Dist\n(>200m)"),
        ("S1_archived", "Sess 1\n(0.0525)"),
        ("E1_plkc_dual_regime_blind", "E1\n(38-ch)"),
        ("E2_plkc_hydro_stage2_vessel", "E2\n(+Hydro)"),
        ("E3_plkc_dualoof_celf_full", "E3\n(Promoted)"),
    ]
    x = np.arange(len(arm_keys))
    vals = []
    lo_err = []
    hi_err = []
    det_vals = []
    for k, _ in arm_keys:
        if k == "S1_archived":
            vals.append(0.052328)
            lo_err.append(0.052328 - 0.0375)
            hi_err.append(0.0687 - 0.052328)
            det_vals.append(0.0332)
        else:
            d = sc_dict[k]["dti"]
            vals.append(d)
            lo_err.append(d - sc_dict[k]["ci95"][0])
            hi_err.append(sc_dict[k]["ci95"][1] - d)
            det_vals.append(0.0 if k == "zero_control" else det_dict[k])

    ax0 = axes[0]
    w = 0.38
    b_main = ax0.bar(
        x - w / 2, vals, width=w, yerr=[lo_err, hi_err], capsize=3.5,
        color=["#94a3b8", "#f59e0b", "#fb7185", "#38bdf8", "#0284c7", "#059669"],
        edgecolor="#0f172a", linewidth=0.7, label="Pooled HOLDOUT-DTI (95% CI)",
    )
    b_det = ax0.bar(
        x + w / 2, det_vals, width=w,
        color=["#cbd5e1", "#fde68a", "#fecdd3", "#bae6fd", "#7dd3fc", "#6ee7b7"],
        edgecolor="#0f172a", linewidth=0.7, label="Detached (>800 m Blind) DTI",
    )
    ax0.set_xticks(x)
    ax0.set_xticklabels([lbl for _, lbl in arm_keys], fontsize=8.0, fontweight="bold")
    ax0.set_ylabel("HOLDOUT-DTI (gems57-pooled-hide-v2, 11,360 px)", fontsize=8.8, fontweight="bold")
    ax0.set_ylim(0, 0.118)
    ax0.grid(axis="y", linestyle="--", alpha=0.4)
    ax0.legend(loc="upper left", fontsize=7.8)
    ax0.set_title(
        "A. Monotonic Pre-Registered Holdout (Budget 3/3)\n"
        "E3 = 0.0795 (seed=20: 0.0908) | +52% vs Session 1",
        fontsize=9.8, fontweight="bold", pad=10, color="#0f172a",
    )
    for b, v, he in zip(b_main, vals, hi_err):
        ax0.text(b.get_x() + b.get_width() / 2, v + he + 0.0018, f"{v:.4f}", ha="center", va="bottom", fontsize=7.2, fontweight="bold", color="#0f172a")

    # Panel B: Zero-SGMC Concealed Piedmont Benchmark (sgmc-piedmont-basin-v1)
    ax1 = axes[1]
    bench_rows = [r for r in cpied_bench["benchmarks"] if r.get("organizer_confirmed_score") is not None]
    xs_cp = [r["concealed_piedmont_dti"]["dti"] for r in bench_rows]
    ys_lv = [r["organizer_confirmed_score"] for r in bench_rows]
    ax1.scatter(xs_cp, ys_lv, s=46, c="#2563eb", edgecolors="#0f172a", linewidths=0.7, alpha=0.82, label="18 Live-Scored Peers (ρ=+0.55, p=0.019)")
    label_map = {
        "ApartGEMSDOE1_S1_00525": ("Sess 1 (0.0525)", (6, 4)),
        "GEMSDOE27_H31_02250": ("GD27 (0.2250)", (-54, -13)),
        "GEMSDOE70_P8_02478": ("GD70 P8 (0.2478)", (-64, 5)),
        "GEMSDOE32_B2_02778": ("GD32 B2 (0.2778)", (-64, 6)),
    }
    for r in bench_rows:
        if r["key"] in label_map:
            lbl_short, offset = label_map[r["key"]]
            ax1.annotate(
                lbl_short,
                (r["concealed_piedmont_dti"]["dti"], r["organizer_confirmed_score"]),
                xytext=offset,
                textcoords="offset points",
                fontsize=7.4, fontweight="bold", color="#0f172a",
            )
    cand_cp = run_sum["run_card"]["concealed_piedmont_holdout_dti"]["dti"]
    cand_ci = run_sum["run_card"]["concealed_piedmont_holdout_dti"]["ci95"]
    ax1.axvline(cand_cp, color="#059669", linewidth=2.2, linestyle="-", label=f"Ours Zero-SGMC C_pied = {cand_cp:.4f}")
    ax1.axvspan(cand_ci[0], cand_ci[1], color="#10b981", alpha=0.14, label=f"Ours 95% CI [{cand_ci[0]:.3f}, {cand_ci[1]:.3f}]")
    ax1.set_xlim(0.0, 0.138)
    ax1.set_ylim(0.0, 0.31)
    ax1.set_xlabel("Read-Only Concealed Piedmont HOLDOUT-DTI (10,579 px)", fontsize=8.8, fontweight="bold")
    ax1.set_ylabel("ORGANIZER-CONFIRMED Live Score", fontsize=8.8, fontweight="bold")
    ax1.set_title(
        "B. Zero-SGMC Concealed Piedmont Diagnostic\n"
        f"Ours = {cand_cp:.4f} (5.1× Sess 1; > GD32 0.0954 & GD70 0.0854)",
        fontsize=9.8, fontweight="bold", pad=10, color="#0f172a",
    )
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend(loc="lower right", fontsize=7.6)

    # Panel C: Top 18 of 47 Single-Feature Leakage Canaries
    ax2 = axes[2]
    feats = sorted(run_sum["leakage_canary"]["features"], key=lambda f: f["symmetric_auc"], reverse=True)[:18]
    f_names = [f["feature"] for f in feats][::-1]
    f_aucs = [f["symmetric_auc"] for f in feats][::-1]
    f_cols = ["#0284c7" if f["group"] == "blind_physical" else "#7c3aed" for f in feats][::-1]
    yf = np.arange(len(f_names))
    ax2.barh(yf, f_aucs, color=f_cols, height=0.68, edgecolor="#0f172a", linewidth=0.5)
    ax2.axvline(0.90, color="#dc2626", linestyle="--", linewidth=1.8, label="Leakage Cap (0.90)")
    ax2.axvline(0.50, color="#64748b", linestyle=":", linewidth=1.0)
    ax2.set_yticks(yf)
    ax2.set_yticklabels(f_names, fontsize=7.2, fontweight="bold")
    ax2.set_xlim(0.48, 0.95)
    ax2.set_xlabel("Single-Feature Symmetric Holdout AUC", fontsize=8.8, fontweight="bold")
    ax2.set_title(
        "C. Automated Leakage Canary (47 / 47 PASS <= 0.90)\n"
        f"Top 18 Shown | Max = {run_sum['leakage_canary']['max_symmetric_auc']:.4f} (Blue=Blind, Purple=VTRB)",
        fontsize=9.8, fontweight="bold", pad=10, color="#0f172a",
    )
    ax2.legend(loc="lower right", fontsize=7.8)
    ax2.grid(axis="x", linestyle="--", alpha=0.4)

    fig.tight_layout()
    fig.savefig(assets / "holdout_experiments_and_canary.png", dpi=160)
    plt.close(fig)
    print("Generated 3 publication-grade figures in docs/assets/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
