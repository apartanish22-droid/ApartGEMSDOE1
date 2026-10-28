"""Zero-leakage, zero-SGMC 44-channel multi-physics feature stack for H-APART-5 (PLKC-DualOOF-CELF).

Architecture & Strict Protocol Invariants:
  1. ZERO SGMC ACCESS: ``derived_sgmc_faults_100m.tif`` and ``sgmc_faults_100m.tif`` are NEVER
     referenced or opened anywhere in feature construction or model training.
  2. ZERO CATALOGUE LEAKAGE IN BLIND STACK: ``ensure_blind_feature_cache`` computes 44 purely
     physical earth-observation channels stored as footprint-packed float32 vectors ``(5167373,)``
     in ``.cache/apartgems_s2_features/`` (~20.7 MB/channel, peak RAM < 450 MB).
  3. PRESERVED-NaN 1m LiDAR: The 4 1m USGS 3DEP LiDAR channels (``E1_LIDAR_FEATURES``) preserve
     exact ``np.nan`` outside valid interior LiDAR coverage (75.3% of footprint) so the Dual-Regime
     ``M_Full`` head splits natively on LiDAR availability while ``M_Sub`` never touches LiDAR.
  4. EXPLICIT NON-FAULT MIMIC DECONFOUNDERS: Includes orthometric elevation ``chi_zmean_m`` and
     ``mimic_pluvial_bench`` (Pleistocene Lake Lahontan 1,330 m & Lake Bonneville 1,463/1,558 m
     shoreline benches with zero basement step) plus ``mimic_tiger_road_dist`` and GeoDAWN
     ``acquisition_block_id_100m.tif`` survey-seam suppression.
"""
from __future__ import annotations

import csv
import gc
import json
from pathlib import Path
import struct
import zipfile

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform
from scipy import ndimage as ndi

from gems57.grid import Grid

ROOT = Path(__file__).resolve().parents[2]
FEAT_CACHE_DIR = ROOT / ".cache/apartgems_s2_features"

E1_SUB_FEATURES: tuple[str, ...] = (
    # Official 19-band high-pass & crustal geometry (14)
    "b02_rtp_hp8",
    "b03_tmi_hg_hp10",
    "b05_grav_slope_hp10",
    "b06_mag_tc",
    "b09_tmi_vg",
    "b11_grav_vg",
    "b12_det_elev",
    "b12_piedmont_pos",
    "b13_iso_grav_hp12",
    "b15_depth_base",
    "b15_base_grad",
    "b18_grav_hg",
    "b19_det_slope",
    "kin_strain_seis",
    # Dip-projected potential-field updip contacts & GeoDAWN aeromag (5)
    "udpc_grav_tilt_zero",
    "udpc_grav_updip_60deg",
    "udpc_mag_updip_60deg",
    "geodawn_tmi_up150_hp6",
    "geodawn_tmi_hgm",
    # 10m seamless USGS 3DEP scarp & morphometrics (9)
    "t10_onesided3",
    "t10_hgm50_max",
    "t10_resid_range",
    "t10_slope_p90",
    "t10_slope_hp8",
    "t10_curv_prof",
    "t10_aspect_coh",
    "t10_hs_lineament",
    "t10_drainage_orth",
    # 10m fluvial chi/ksn knickzones & explicit mimic deconfounders (6)
    "chi_step_max",
    "chi_ksn_max",
    "chi_ksn_hp8",
    "chi_zmean_m",
    "mimic_pluvial_bench",
    "mimic_tiger_road_dist",
)

E1_LIDAR_FEATURES: tuple[str, ...] = (
    "lid_ex_max",
    "lid_step_max",
    "lid_coh100",
    "lid_scarp_crest",
)

E2_HYDRO_ADDON_FEATURES: tuple[str, ...] = (
    "hyd_gdr_spring_geotherm",
    "hyd_f2mdab_sinter_vent",
    "hyd_geodawn_k_th_adularia",
    "hyd_geodawn_u_th_redox",
    "hyd_mag_destruction",
    "hyd_mt_claycap_edge",
)

E1_FULL_FEATURES: tuple[str, ...] = E1_SUB_FEATURES + E1_LIDAR_FEATURES
E2_SUB_FEATURES: tuple[str, ...] = E1_SUB_FEATURES + E2_HYDRO_ADDON_FEATURES
E2_FULL_FEATURES: tuple[str, ...] = E1_SUB_FEATURES + E1_LIDAR_FEATURES + E2_HYDRO_ADDON_FEATURES
ALL_BLIND_FEATURES: tuple[str, ...] = E2_FULL_FEATURES

VTRB_VISIBLE_FEATURES: tuple[str, ...] = (
    "vtrb_tip_cone",
    "vtrb_stepover_bridge",
    "vtrb_belt_density",
)


def _load_band_imputed(band_idx: int, fp: np.ndarray) -> np.ndarray:
    arr = np.load(ROOT / f".cache/features/band-{band_idx:02d}.npy").astype(np.float32)
    valid = fp & np.isfinite(arr)
    med = float(np.median(arr[valid])) if valid.any() else 0.0
    arr[~np.isfinite(arr)] = med
    return arr


def _unpack_fp(arr_or_vec: np.ndarray, fp: np.ndarray, fill: float = np.nan) -> np.ndarray:
    if arr_or_vec.ndim == 2 and arr_or_vec.shape == fp.shape:
        return arr_or_vec.astype(np.float32, copy=False)
    out = np.full(fp.shape, fill, dtype=np.float32)
    out[fp] = arr_or_vec.astype(np.float32, copy=False)
    return out


def _save_fp_vec(name: str, arr2d: np.ndarray, fp: np.ndarray, preserve_nan: bool = False) -> tuple[Path, dict]:
    p = FEAT_CACHE_DIR / f"{name}.fp.f32.npy"
    vec = arr2d[fp].astype(np.float32, copy=False)
    if not preserve_nan:
        fin = np.isfinite(vec)
        med = float(np.median(vec[fin])) if fin.any() else 0.0
        vec = np.where(fin, vec, med).astype(np.float32)
    np.save(p, vec)
    fin_v = vec[np.isfinite(vec)]
    stats = {
        "n_valid_in_fp": int(fin_v.size),
        "nan_frac_in_fp": round(float(1.0 - fin_v.size / max(vec.size, 1)), 5),
        "min_in_fp": float(fin_v.min()) if fin_v.size else 0.0,
        "median_in_fp": float(np.median(fin_v)) if fin_v.size else 0.0,
        "max_in_fp": float(fin_v.max()) if fin_v.size else 0.0,
    }
    return p, stats


def _geodawn_seam_weight(fp: np.ndarray) -> np.ndarray:
    """Suppress GeoDAWN survey-block boundary stitching seams (DOI:10.5066/P93LGLVQ)."""
    with rasterio.open(ROOT / ".cache/external/acquisition_block_id_100m.tif") as ds:
        blk = ds.read(1)
    mx = ndi.maximum_filter(blk, size=3)
    mn = ndi.minimum_filter(blk, size=3)
    seam = (mx != mn) & fp
    dist_seam = ndi.distance_transform_edt(~seam).astype(np.float32)
    return np.clip(dist_seam / 3.0, 0.0, 1.0).astype(np.float32)


def _dequant_u8_linear(q: np.ndarray, lo: float, hi: float) -> tuple[np.ndarray, np.ndarray]:
    valid = q > 0
    out = np.zeros(q.shape, dtype=np.float32)
    out[valid] = np.float32(lo) + ((q[valid].astype(np.float32) - 1.0) / 254.0) * np.float32(hi - lo)
    return out, valid


def _impute_smooth(arr: np.ndarray, valid: np.ndarray, fp: np.ndarray) -> np.ndarray:
    m = valid & fp & np.isfinite(arr)
    med = float(np.median(arr[m])) if m.any() else 0.0
    return np.where(m, arr, med).astype(np.float32)


def _build_and_save_all_blind_features(fp: np.ndarray) -> tuple[dict[str, Path], dict[str, dict]]:
    H, W = fp.shape
    paths: dict[str, Path] = {}
    manifest: dict[str, dict] = {}

    def _emit(name: str, arr: np.ndarray, preserve_nan: bool = False) -> None:
        pth, st = _save_fp_vec(name, arr, fp, preserve_nan=preserve_nan)
        paths[name] = pth
        manifest[name] = st

    # --- Block 1: Official 19-band geophysical + updip potential-field contacts ---
    b02_rtp = _load_band_imputed(2, fp)
    b02_hp8 = (b02_rtp - ndi.gaussian_filter(b02_rtp, sigma=8.0)).astype(np.float32)
    _emit("b02_rtp_hp8", b02_hp8)

    b03_tmi_hg = np.maximum(_load_band_imputed(3, fp), 0.0)
    _emit("b03_tmi_hg_hp10", b03_tmi_hg - ndi.gaussian_filter(b03_tmi_hg, sigma=10.0))

    b05_gslp = np.maximum(_load_band_imputed(5, fp), 0.0)
    _emit("b05_grav_slope_hp10", b05_gslp - ndi.gaussian_filter(b05_gslp, sigma=10.0))
    del b05_gslp

    _emit("b06_mag_tc", _load_band_imputed(6, fp))
    _emit("b09_tmi_vg", _load_band_imputed(9, fp))

    b11_gvg = _load_band_imputed(11, fp)
    _emit("b11_grav_vg", b11_gvg)

    b12_elev = _load_band_imputed(12, fp)
    _emit("b12_det_elev", b12_elev)
    _emit("b12_piedmont_pos", b12_elev - ndi.gaussian_filter(b12_elev, sigma=25.0))

    b13_igrav = _load_band_imputed(13, fp)
    _emit("b13_iso_grav_hp12", b13_igrav - ndi.gaussian_filter(b13_igrav, sigma=12.0))

    b15_depth = np.clip(_load_band_imputed(15, fp), 0.0, 8000.0)
    _emit("b15_depth_base", b15_depth)
    db_y = ndi.gaussian_filter(b15_depth, sigma=1.5, order=[1, 0])
    db_x = ndi.gaussian_filter(b15_depth, sigma=1.5, order=[0, 1])
    b15_grad = np.hypot(db_y, db_x).astype(np.float32)
    _emit("b15_base_grad", b15_grad)
    del db_y, db_x

    b18_ghg = np.maximum(_load_band_imputed(18, fp), 0.0)
    _emit("b18_grav_hg", b18_ghg)

    b19_slp = np.maximum(_load_band_imputed(19, fp), 0.0)
    _emit("b19_det_slope", b19_slp)
    del b19_slp

    b04 = np.maximum(_load_band_imputed(4, fp), 0.0)
    b10 = np.maximum(_load_band_imputed(10, fp), 0.0)
    b16 = np.maximum(_load_band_imputed(16, fp), 0.0)
    p99_b04 = float(np.quantile(b04[fp], 0.99)) + 1e-12
    p99_b16 = float(np.quantile(b16[fp], 0.99)) + 1e-12
    kin = np.log1p(b04 / p99_b04) + 0.5 * np.log1p(b16 / p99_b16) + 0.5 * np.exp(-b10 / 12000.0)
    _emit("kin_strain_seis", kin.astype(np.float32))
    del b04, b10, b16, kin

    # Updip 60-degree fault-plane projection for gravity & RTP magnetics
    ghg_med = float(np.median(b18_ghg[fp])) + 1e-6
    tilt_g = np.arctan2(b11_gvg, b18_ghg + 0.05 * ghg_med)
    grav_tz = (np.cos(tilt_g) * np.log1p(b18_ghg / ghg_med)).astype(np.float32)
    _emit("udpc_grav_tilt_zero", grav_tz)
    del tilt_g, b11_gvg, grav_tz

    gy = ndi.gaussian_filter(b13_igrav, sigma=2.5, order=[1, 0])
    gx = ndi.gaussian_filter(b13_igrav, sigma=2.5, order=[0, 1])
    gnorm = np.hypot(gy, gx) + 1e-6
    shift_px = np.clip((b15_depth * 0.57735) / 100.0, 0.8, 7.5).astype(np.float32)
    yy, xx = np.indices((H, W), dtype=np.float32)
    src_y_g = np.clip(yy - (gy / gnorm) * shift_px, 0.0, H - 1.0)
    src_x_g = np.clip(xx - (gx / gnorm) * shift_px, 0.0, W - 1.0)
    grav_updip = ndi.map_coordinates(b18_ghg, [src_y_g, src_x_g], order=1, mode="nearest").astype(np.float32)
    _emit("udpc_grav_updip_60deg", grav_updip)
    del b13_igrav, gy, gx, gnorm, src_y_g, src_x_g, grav_updip

    my = ndi.gaussian_filter(b02_rtp, sigma=2.5, order=[1, 0])
    mx = ndi.gaussian_filter(b02_rtp, sigma=2.5, order=[0, 1])
    mnorm = np.hypot(my, mx) + 1e-6
    src_y_m = np.clip(yy - (my / mnorm) * shift_px, 0.0, H - 1.0)
    src_x_m = np.clip(xx - (mx / mnorm) * shift_px, 0.0, W - 1.0)
    mag_updip = ndi.map_coordinates(b03_tmi_hg, [src_y_m, src_x_m], order=1, mode="nearest").astype(np.float32)
    _emit("udpc_mag_updip_60deg", mag_updip)
    del b02_rtp, b03_tmi_hg, my, mx, mnorm, shift_px, yy, xx, src_y_m, src_x_m, mag_updip, b15_depth
    gc.collect()

    # Seam-suppressed GeoDAWN TMI_up150 + radiometrics
    seam_w = _geodawn_seam_weight(fp)
    with rasterio.open(ROOT / ".cache/external/geodawn_extensions_u8.tif") as ds_gx:
        q_uth = ds_gx.read(3)
        q_tmi150 = ds_gx.read(4)
    tmi150, v_tmi = _dequant_u8_linear(q_tmi150, -1200.0, 1200.0)
    tmi150 = _impute_smooth(tmi150, v_tmi, fp)
    tmi150_hp6 = ((tmi150 - ndi.gaussian_filter(tmi150, sigma=6.0)) * seam_w).astype(np.float32)
    tmi150_hgm = (
        np.hypot(
            ndi.gaussian_filter(tmi150, sigma=1.2, order=[1, 0]),
            ndi.gaussian_filter(tmi150, sigma=1.2, order=[0, 1]),
        )
        * seam_w
    ).astype(np.float32)
    _emit("geodawn_tmi_up150_hp6", tmi150_hp6)
    _emit("geodawn_tmi_hgm", tmi150_hgm)
    del q_tmi150, tmi150, v_tmi, tmi150_hp6, tmi150_hgm

    # --- Block 2: 10m Seamless USGS 3DEP Scarp & Morphometric Channels ---
    d10_os3 = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_onesided3.f32.npy"), fp, fill=0.0)
    d10_hgm = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_hgm50_max.f32.npy"), fp, fill=0.0)
    d10_res = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_resid_range.f32.npy"), fp, fill=0.0)
    _emit("t10_onesided3", d10_os3)
    _emit("t10_hgm50_max", d10_hgm)
    _emit("t10_resid_range", d10_res)
    del d10_hgm, d10_res

    topo_man = json.loads((ROOT / ".cache/external/topo_10m_derived_100m_u8.manifest.json").read_text())
    bmeta = {b["index"]: b for b in topo_man["bands"]}
    with rasterio.open(ROOT / ".cache/external/topo_10m_derived_100m_u8.tif") as ds_t10:
        slp_p90, vp1 = _dequant_u8_linear(ds_t10.read(1), bmeta[1]["lo"], bmeta[1]["hi"])
        slp_max, vp2 = _dequant_u8_linear(ds_t10.read(2), bmeta[2]["lo"], bmeta[2]["hi"])
        curv_pr, vp6 = _dequant_u8_linear(ds_t10.read(6), bmeta[6]["lo"], bmeta[6]["hi"])
        asp_coh, vp7 = _dequant_u8_linear(ds_t10.read(7), bmeta[7]["lo"], bmeta[7]["hi"])
        hs_lin, vp8 = _dequant_u8_linear(ds_t10.read(8), bmeta[8]["lo"], bmeta[8]["hi"])
    slp_p90 = _impute_smooth(slp_p90, vp1, fp)
    slp_max = _impute_smooth(slp_max, vp2, fp)
    curv_pr = _impute_smooth(curv_pr, vp6, fp)
    asp_coh = _impute_smooth(asp_coh, vp7, fp)
    hs_lin = _impute_smooth(hs_lin, vp8, fp)

    _emit("t10_slope_p90", slp_p90)
    _emit("t10_slope_hp8", slp_max - ndi.gaussian_filter(slp_max, sigma=8.0))
    _emit("t10_curv_prof", curv_pr)
    _emit("t10_aspect_coh", asp_coh)
    _emit("t10_hs_lineament", hs_lin)
    del slp_p90, slp_max, curv_pr, asp_coh, hs_lin, vp1, vp2, vp6, vp7, vp8

    # Drainage-orthogonal scarp component (suppresses radial alluvial-fan washes)
    ry_reg = ndi.gaussian_filter(b12_elev, sigma=12.0, order=[1, 0])
    rx_reg = ndi.gaussian_filter(b12_elev, sigma=12.0, order=[0, 1])
    rnorm = np.hypot(ry_reg, rx_reg) + 1e-5
    fy_s = ndi.gaussian_filter(np.nan_to_num(d10_os3, nan=0.0), sigma=1.2, order=[1, 0])
    fx_s = ndi.gaussian_filter(np.nan_to_num(d10_os3, nan=0.0), sigma=1.2, order=[0, 1])
    fnorm = np.hypot(fy_s, fx_s) + 1e-6
    cos_align = np.abs((fy_s / fnorm) * (ry_reg / rnorm) + (fx_s / fnorm) * (rx_reg / rnorm))
    _emit("t10_drainage_orth", (np.nan_to_num(d10_os3, nan=0.0) * (cos_align ** 1.5)).astype(np.float32))
    del b12_elev, d10_os3, ry_reg, rx_reg, rnorm, fy_s, fx_s, fnorm, cos_align
    gc.collect()

    # --- Block 3: 10m Fluvial chi/ksn Knickzones + Pluvial Bench & TIGER Road Mimics ---
    with rasterio.open(ROOT / ".cache/external/dem10_chi_100m_i16.tif") as ds_chi:
        c_step = ds_chi.read(1)
        c_ksn = ds_chi.read(3)
        c_zm = ds_chi.read(5)
    v_c1 = c_step != -32768
    v_c3 = c_ksn != -32768
    v_c5 = c_zm != -32768
    chi_step = _impute_smooth(c_step.astype(np.float32) * 0.001, v_c1, fp)
    chi_ksn = _impute_smooth(c_ksn.astype(np.float32), v_c3, fp)
    chi_zm = _impute_smooth(c_zm.astype(np.float32), v_c5, fp)
    _emit("chi_step_max", chi_step)
    _emit("chi_ksn_max", chi_ksn)
    _emit("chi_ksn_hp8", chi_ksn - ndi.gaussian_filter(chi_ksn, sigma=8.0))
    _emit("chi_zmean_m", chi_zm)
    del c_step, c_ksn, c_zm, v_c1, v_c3, v_c5, chi_step, chi_ksn

    # Pluvial shoreline bench mimic indicator (Lahontan 1330m, Bonneville Provo 1463m & Bonneville 1558m)
    w_lah = np.exp(-(((chi_zm - 1330.0) / 18.0) ** 2))
    w_provo = np.exp(-(((chi_zm - 1463.0) / 15.0) ** 2))
    w_bonn = np.exp(-(((chi_zm - 1558.0) / 18.0) ** 2))
    p75_bg = float(np.quantile(b15_grad[fp], 0.75)) + 1e-6
    pluv_mimic = (np.maximum(w_lah, np.maximum(w_provo, w_bonn)) * np.exp(-b15_grad / p75_bg)).astype(np.float32)
    _emit("mimic_pluvial_bench", pluv_mimic)
    del chi_zm, w_lah, w_provo, w_bonn, b15_grad, pluv_mimic

    with rasterio.open(ROOT / ".cache/external/tiger_road_distance_m.tif") as ds_rd:
        rd_raw = ds_rd.read(1).astype(np.float32)
    rd_clean = np.clip(np.where(np.isfinite(rd_raw), rd_raw, 5000.0), 0.0, 5000.0)
    _emit("mimic_tiger_road_dist", np.log1p(rd_clean).astype(np.float32))
    del rd_raw, rd_clean
    gc.collect()

    # --- Block 4: Preserved-NaN 1m USGS 3DEP LiDAR Scarp Channels (M_Full ONLY) ---
    with rasterio.open(ROOT / ".cache/external/lidar_scarp_features_u8.tif") as ds_lid:
        q_ex = ds_lid.read(1)
        q_st = ds_lid.read(3)
        q_co = ds_lid.read(10)
        q_vl = ds_lid.read(12)
    # Erode valid mask by 2 px (200 m) to suppress LiDAR acquisition survey boundary steps
    lid_ok = fp & ndi.binary_erosion(q_vl > 0, iterations=2) & (q_ex > 0) & (q_st > 0) & (q_co > 0)
    lid_ex = np.full((H, W), np.nan, dtype=np.float32)
    lid_st = np.full((H, W), np.nan, dtype=np.float32)
    lid_co = np.full((H, W), np.nan, dtype=np.float32)
    lid_ex[lid_ok] = (((q_ex[lid_ok].astype(np.float32) - 1.0) / 254.0) ** 2) * 1.5
    lid_st[lid_ok] = (((q_st[lid_ok].astype(np.float32) - 1.0) / 254.0) ** 2) * 1.0
    lid_co[lid_ok] = (q_co[lid_ok].astype(np.float32) - 1.0) / 254.0

    prod_sc = np.where(lid_ok, lid_st * lid_co, 0.0).astype(np.float32)
    w_ok = lid_ok.astype(np.float32)
    bg_sc = ndi.gaussian_filter(prod_sc, sigma=6.0) / np.maximum(ndi.gaussian_filter(w_ok, sigma=6.0), 1e-4)
    lid_crest = np.full((H, W), np.nan, dtype=np.float32)
    lid_crest[lid_ok] = prod_sc[lid_ok] - bg_sc[lid_ok]

    _emit("lid_ex_max", lid_ex, preserve_nan=True)
    _emit("lid_step_max", lid_st, preserve_nan=True)
    _emit("lid_coh100", lid_co, preserve_nan=True)
    _emit("lid_scarp_crest", lid_crest, preserve_nan=True)
    del q_ex, q_st, q_co, q_vl, lid_ok, lid_ex, lid_st, lid_co, prod_sc, w_ok, bg_sc, lid_crest
    gc.collect()

    # --- Block 5: E2 Hydrothermal Conduits, GeoDAWN Alteration & Volcanic Vents (+6) ---
    sp_fine = np.zeros((H, W), dtype=np.float32)
    sp_broad = np.zeros((H, W), dtype=np.float32)
    ws_path = ROOT / ".cache/external/gdr_wellspring_in_footprint.csv"
    with ws_path.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                rr, cc = int(float(r["row"])), int(float(r["col"]))
                if not (0 <= rr < H and 0 <= cc < W and fp[rr, cc]):
                    continue
                tc = float(r["temp_c"]) if r.get("temp_c") not in ("", "nan", None) else 15.0
                tq = float(r["geothermquartz_c"]) if r.get("geothermquartz_c") not in ("", "nan", None) else 0.0
                tch = float(r["geothermchalc_c"]) if r.get("geothermchalc_c") not in ("", "nan", None) else 0.0
                tc = tc if np.isfinite(tc) else 15.0
                tq = tq if np.isfinite(tq) else 0.0
                tch = tch if np.isfinite(tch) else 0.0
                w_sp = np.clip((tc - 20.0) / 55.0, 0.0, 2.5) + 0.7 * np.clip((max(tq, tch) - 70.0) / 110.0, 0.0, 2.0)
                if w_sp > 0.05:
                    sp_fine[rr, cc] = max(sp_fine[rr, cc], float(w_sp))
                    sp_broad[rr, cc] += float(w_sp)
            except Exception:
                continue
    hyd_sp = (
        0.65 * ndi.gaussian_filter(sp_fine, sigma=3.5)
        + 0.35 * ndi.gaussian_filter(np.log1p(sp_broad), sigma=10.0)
    ).astype(np.float32)
    _emit("hyd_gdr_spring_geotherm", hyd_sp)
    del sp_fine, sp_broad, hyd_sp

    # 2m F2mDAB temperature probes + paleo sinter/travertine + Quaternary/Neogene volcanic vents
    pv_fine = np.zeros((H, W), dtype=np.float32)
    pv_broad = np.zeros((H, W), dtype=np.float32)
    with zipfile.ZipFile(ROOT / ".cache/external/2m_temperature_probe_INGENIOUS_regional_data.zip") as zf:
        dbf_name = [n for n in zf.namelist() if n.endswith(".dbf")][0]
        raw_dbf = zf.read(dbf_name)
    num_rec, header_len, rec_len = struct.unpack("<IHH", raw_dbf[4:12])
    fields = []
    pos = 32
    while raw_dbf[pos] != 0x0D:
        fname = raw_dbf[pos : pos + 11].split(b"\x00", 1)[0].decode("ascii")
        fields.append((fname, raw_dbf[pos + 16]))
        pos += 32
    lons, lats, w_pr = [], [], []
    off = header_len
    for _ in range(num_rec):
        rec = raw_dbf[off : off + rec_len]
        off += rec_len
        if rec[0] == 0x2A:
            continue
        p = 1
        row_d = {}
        for fn, fl in fields:
            row_d[fn] = rec[p : p + fl].decode("latin1").strip()
            p += fl
        try:
            la = float(row_d["LatDegreeN"])
            lo = -abs(float(row_d["LongDegree"]))
            fd = float(row_d["F2mDAB"]) if row_d["F2mDAB"] else 0.0
            if np.isfinite(fd) and fd > 0.25:
                lons.append(lo)
                lats.append(la)
                w_pr.append(min(fd / 4.5, 2.5))
        except Exception:
            continue
    if lons:
        xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
        for rr, cc, ww in zip(
            np.floor((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int32),
            np.floor((np.asarray(xs) - 243350.0) / 100.0).astype(np.int32),
            w_pr,
        ):
            if 0 <= rr < H and 0 <= cc < W and fp[rr, cc]:
                pv_fine[rr, cc] = max(pv_fine[rr, cc], float(ww))
                pv_broad[rr, cc] += float(ww)

    with zipfile.ZipFile(ROOT / ".cache/external/paleo_geothermal_regional.zip") as zf:
        cname = [n for n in zf.namelist() if n.endswith(".csv")][0]
        txt = zf.read(cname).decode("latin1")
    plons, plats, pw = [], [], []
    for r in csv.DictReader(txt.splitlines()):
        try:
            la = float(r["Lat_deg_NAD83"])
            lo = -abs(float(r["Long_deg_NAD83"]))
            dt = (r.get("Deposit_type") or "").lower()
            pw.append(2.2 if ("sinter" in dt or "travertine" in dt or "opal" in dt) else 1.2)
            plons.append(lo)
            plats.append(la)
        except Exception:
            continue
    if plons:
        pxs, pys = warp_transform("EPSG:4269", "EPSG:32611", plons, plats)
        for rr, cc, ww in zip(
            np.floor((4508550.0 - np.asarray(pys)) / 100.0).astype(np.int32),
            np.floor((np.asarray(pxs) - 243350.0) / 100.0).astype(np.int32),
            pw,
        ):
            if 0 <= rr < H and 0 <= cc < W and fp[rr, cc]:
                pv_fine[rr, cc] = max(pv_fine[rr, cc], float(ww))
                pv_broad[rr, cc] += float(ww)

    # Volcanic vents (STRICT LEAKAGE GUARD: read ONLY row, col, rock_type; NEVER read dist_known_fault_px)
    vent_path = ROOT / ".cache/external/gdr_volcanic_vents_in_footprint.csv"
    with vent_path.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                rr, cc = int(float(r["row"])), int(float(r["col"]))
                if 0 <= rr < H and 0 <= cc < W and fp[rr, cc]:
                    pv_fine[rr, cc] = max(pv_fine[rr, cc], 1.8)
                    pv_broad[rr, cc] += 1.8
            except Exception:
                continue

    hyd_pv = (
        0.65 * ndi.gaussian_filter(pv_fine, sigma=3.5)
        + 0.35 * ndi.gaussian_filter(np.log1p(pv_broad), sigma=10.0)
    ).astype(np.float32)
    _emit("hyd_f2mdab_sinter_vent", hyd_pv)
    del pv_fine, pv_broad, hyd_pv, raw_dbf

    # GeoDAWN K/Th adularia & U/Th redox high-pass (seam-suppressed)
    with rasterio.open(ROOT / ".cache/external/geodawn_rad_u8.tif") as ds_rad:
        q_k = ds_rad.read(1)
        q_th = ds_rad.read(2)
    rad_k, vk = _dequant_u8_linear(q_k, 0.0, 5.0)
    rad_th, vth = _dequant_u8_linear(q_th, 0.0, 30.0)
    vr = vk & vth & fp
    k_th = _impute_smooth(rad_k / (rad_th + 1.5), vr, fp)
    _emit("hyd_geodawn_k_th_adularia", ((k_th - ndi.gaussian_filter(k_th, sigma=8.0)) * seam_w).astype(np.float32))
    del q_k, q_th, rad_k, rad_th, vk, vth, vr, k_th

    uth, v_uth = _dequant_u8_linear(q_uth, 0.0, 1.0)
    uth = _impute_smooth(uth, v_uth, fp)
    _emit("hyd_geodawn_u_th_redox", ((uth - ndi.gaussian_filter(uth, sigma=8.0)) * seam_w).astype(np.float32))
    del q_uth, uth, v_uth, seam_w

    # Magnetite destruction along gravity-flanked conduits + MT clay-cap gradient
    ghg_m = float(np.median(b18_ghg[fp])) + 1e-6
    mag_destr = (np.maximum(-b02_hp8, 0.0) * np.log1p(b18_ghg / ghg_m)).astype(np.float32)
    _emit("hyd_mag_destruction", mag_destr)
    del b02_hp8, b18_ghg, mag_destr

    b17_cond = np.log10(np.clip(_load_band_imputed(17, fp), 1e-4, 1e4)).astype(np.float32)
    mt_grad = np.hypot(
        ndi.gaussian_filter(b17_cond, sigma=2.0, order=[1, 0]),
        ndi.gaussian_filter(b17_cond, sigma=2.0, order=[0, 1]),
    )
    mt_hp = b17_cond - ndi.gaussian_filter(b17_cond, sigma=15.0)
    _emit("hyd_mt_claycap_edge", (mt_grad + 0.5 * np.maximum(mt_hp, 0.0)).astype(np.float32))
    del b17_cond, mt_grad, mt_hp
    gc.collect()

    return paths, manifest


def ensure_blind_feature_cache(grid: Grid, force: bool = False) -> dict[str, Path]:
    """Compute (or load from ``.cache/apartgems_s2_features/``) all 44 footprint-packed float32 channels."""
    FEAT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    paths = {name: FEAT_CACHE_DIR / f"{name}.fp.f32.npy" for name in ALL_BLIND_FEATURES}
    if not force and all(p.exists() for p in paths.values()):
        return paths
    paths, manifest = _build_and_save_all_blind_features(grid.footprint)
    (FEAT_CACHE_DIR / "blind_features_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return paths


def open_fp_feature_mmaps(feature_paths: dict[str, Path]) -> dict[str, np.ndarray]:
    """Open persistent read-only memory maps for all cached footprint feature vectors."""
    return {name: np.load(p, mmap_mode="r") for name, p in feature_paths.items()}


def load_fp_feature_matrix(
    feature_names: tuple[str, ...],
    feature_sources: dict[str, Any],
    fp_indices: np.ndarray,
    extra_fp_cols: dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    """Load ``(len(fp_indices), len(feature_names))`` float32 matrix from mmap'd footprint vectors."""
    X = np.empty((len(fp_indices), len(feature_names)), dtype=np.float32)
    for j, name in enumerate(feature_names):
        if extra_fp_cols and name in extra_fp_cols:
            X[:, j] = extra_fp_cols[name][fp_indices]
        else:
            src = feature_sources[name]
            vec = np.load(src, mmap_mode="r") if isinstance(src, Path) else src
            X[:, j] = vec[fp_indices]
    return X


def compute_visible_relay_features(visible_mask: np.ndarray, fp: np.ndarray) -> dict[str, np.ndarray]:
    """Compute strictly fold-visible VTRB structural continuation features as footprint-packed vectors.

    Uses ONLY ``visible_mask`` (``fold['visible']`` inside holdout; full ``existing_faults.tif``
    ONLY at final live export, strictly cross-fitted per partition). Suppresses ``<= 2.5 px``
    collar hugging so continuation extends forward off mapped fault tips and across relay ramps.
    """
    vis = np.asarray(visible_mask, dtype=bool) & fp
    H, W = vis.shape
    n_fp = int(fp.sum())
    if not vis.any():
        return {k: np.zeros(n_fp, dtype=np.float32) for k in VTRB_VISIBLE_FEATURES}

    nb_count = ndi.convolve(vis.astype(np.int16), np.ones((3, 3), dtype=np.int16), mode="constant", cval=0) - 1
    tips = vis & (nb_count >= 1) & (nb_count <= 2)

    yy, xx = np.indices((H, W), dtype=np.float32)
    w_sum = ndi.uniform_filter(vis.astype(np.float32), size=11, mode="constant") * 121.0 + 1e-6
    cy = ndi.uniform_filter((vis * yy).astype(np.float32), size=11, mode="constant") * 121.0 / w_sum
    cx = ndi.uniform_filter((vis * xx).astype(np.float32), size=11, mode="constant") * 121.0 / w_sum
    del yy, xx, w_sum

    ty_idx, tx_idx = np.nonzero(tips)
    dy_out = ty_idx.astype(np.float32) - cy[ty_idx, tx_idx]
    dx_out = tx_idx.astype(np.float32) - cx[ty_idx, tx_idx]
    del cy, cx
    dnorm = np.hypot(dy_out, dx_out)
    good = dnorm > 0.4
    ty_idx, tx_idx = ty_idx[good], tx_idx[good]
    uy_out = (dy_out[good] / dnorm[good]).astype(np.float32)
    ux_out = (dx_out[good] / dnorm[good]).astype(np.float32)

    tip_accum = np.zeros((H, W), dtype=np.float32)
    for step in range(3, 36):
        w_step = float(np.exp(-step / 18.0))
        ry = np.rint(ty_idx + uy_out * step).astype(np.int32)
        rx = np.rint(tx_idx + ux_out * step).astype(np.int32)
        inb = (ry >= 0) & (ry < H) & (rx >= 0) & (rx < W)
        np.maximum.at(tip_accum, (ry[inb], rx[inb]), w_step)
    tip_cone = ndi.gaussian_filter(tip_accum, sigma=2.0)
    del tip_accum

    tip_imp = np.zeros((H, W), dtype=np.float32)
    tip_imp[ty_idx, tx_idx] = 1.0
    g_broad = ndi.gaussian_filter(tip_imp, sigma=11.0)
    g_self = ndi.gaussian_filter(tip_imp, sigma=3.0)
    stepover_raw = np.maximum(g_broad * g_broad - 0.12 * g_self * g_self, 0.0)
    del tip_imp, g_broad, g_self

    d_vis = ndi.distance_transform_edt(~vis).astype(np.float32)
    collar_suppress = (1.0 - np.exp(-((d_vis / 2.8) ** 2))).astype(np.float32)
    belt_raw = ndi.gaussian_filter(vis.astype(np.float32), sigma=26.0) * collar_suppress
    del d_vis

    return {
        "vtrb_tip_cone": (tip_cone * collar_suppress)[fp].astype(np.float32),
        "vtrb_stepover_bridge": (stepover_raw * collar_suppress)[fp].astype(np.float32),
        "vtrb_belt_density": belt_raw[fp].astype(np.float32),
    }
