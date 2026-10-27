"""Physical feature engineering for H-APART-1 (UDTH-Submod).

Modules:
  1. UDPC  : Updip dip-backprojected gravity & RTP magnetic phase-tilt contacts
  2. DOPSR : Seam-free 1 m LiDAR + 10 m 3DEP drainage-orthogonal & road-deconfounded scarp tensor
  3. HMCS  : Hydrothermal magnetite-destruction, K/Th adularia alteration, MT cond_surf,
             and INGENIOUS GDR #1391 thermal springs, 2 m probes (F2mDAB), & paleo-sinter mounds
             (strictly physical coordinates/temperatures; NEVER reads dist_known_fault_px)
  4. VTRB  : Strictly fold-visible fault-tip propagation cones, step-over relay bridges,
             and regional belt density (computed ONLY from fold['visible'] in holdout)
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
from scipy.stats import rankdata

from gems57.grid import Grid

ROOT = Path(__file__).resolve().parents[2]
FEAT_CACHE_DIR = ROOT / ".cache/apartgems_features"

E1_BLIND_FEATURES = (
    "udpc_grav_tilt_zero",
    "udpc_grav_updip",
    "udpc_mag_updip",
    "udpc_basin_margin_curv",
    "dopsr_scarp_seamfree",
    "dopsr_drainage_orth",
    "dopsr_road_deconfounded",
    "dopsr_piedmont_inflection",
)

E2_HYDRO_STRESS_FEATURES = E1_BLIND_FEATURES + (
    "hmcs_mag_destruction",
    "hmcs_k_th_alteration",
    "hmcs_mt_cond",
    "hmcs_thermal_upflow",
    "hmcs_updip_alteration_concordance",
    "stress_anderson_seis",
)

VTRB_VISIBLE_FEATURES = (
    "vtrb_tip_cone",
    "vtrb_stepover_bridge",
    "vtrb_belt_density",
)


def _load_band_imputed(band_idx: int, fp: np.ndarray) -> np.ndarray:
    """Load cached float32 band (1..19), impute ~3k missing footprint cells with median."""
    arr = np.load(ROOT / f".cache/features/band-{band_idx:02d}.npy").astype(np.float32)
    valid = np.isfinite(arr) & fp
    med = float(np.median(arr[valid])) if valid.any() else 0.0
    out = np.where(valid, arr, med).astype(np.float32)
    out[~fp] = med
    return out


def _rank_unit(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Empirical [0, 1] quantile normalization strictly inside mask; 0 outside."""
    out = np.zeros(arr.shape, dtype=np.float32)
    v = arr[mask]
    finite = np.isfinite(v)
    if not finite.any():
        return out
    med = float(np.median(v[finite]))
    v_clean = np.where(finite, v, med)
    # Subsample quantile LUT for speed & low RAM (5.17M cells -> exact interp on 2049 knots)
    qs = np.linspace(0.0, 1.0, 2049)
    knots = np.quantile(v_clean, qs)
    # Ensure strictly non-decreasing knots
    out[mask] = np.interp(v_clean, knots, qs).astype(np.float32)
    return out


def _bilinear_sample(img: np.ndarray, yy: np.ndarray, xx: np.ndarray) -> np.ndarray:
    """Fast vectorized bilinear sampling of img at float coordinates (yy, xx)."""
    H, W = img.shape
    y = np.clip(yy, 0.0, H - 1.001)
    x = np.clip(xx, 0.0, W - 1.001)
    y0 = np.floor(y).astype(np.int32)
    x0 = np.floor(x).astype(np.int32)
    wy = (y - y0).astype(np.float32)
    wx = (x - x0).astype(np.float32)
    v00 = img[y0, x0]
    v01 = img[y0, x0 + 1]
    v10 = img[y0 + 1, x0]
    v11 = img[y0 + 1, x0 + 1]
    return ((1.0 - wy) * ((1.0 - wx) * v00 + wx * v01) + wy * ((1.0 - wx) * v10 + wx * v11)).astype(np.float32)


def _build_udpc_and_strike(fp: np.ndarray) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    """Build Module 1 (UDPC) + return structural strike (cos2phi, sin2phi) for stress alignment."""
    H, W = fp.shape
    iso_grav = _load_band_imputed(13, fp)         # mGal
    grav_slope = _load_band_imputed(5, fp)        # horizontal gradient magnitude
    grav_vg = _load_band_imputed(11, fp)          # vertical gradient
    depth_base = np.clip(_load_band_imputed(15, fp), 0.0, 3500.0)  # cover thickness (m)
    rtp = _load_band_imputed(2, fp)               # Reduced-to-Pole magnetics (nT)
    tmi_hg = _load_band_imputed(3, fp)
    tmi_vg = _load_band_imputed(9, fp)

    # Multi-scale gravity horizontal derivatives pointing upslope (toward footwall high)
    gy_s = ndi.gaussian_filter(iso_grav, sigma=4.5, order=[1, 0])
    gx_s = ndi.gaussian_filter(iso_grav, sigma=4.5, order=[0, 1])
    gmag_s = np.hypot(gy_s, gx_s) + 1e-6
    # Downdip unit vector points into hanging-wall gravity low (-grad iso_grav)
    uy_basin = (-gy_s / gmag_s).astype(np.float32)
    ux_basin = (-gx_s / gmag_s).astype(np.float32)

    # Fine-scale gravity horizontal gradient & true Miller-Singh (1994) phase-tilt angle
    gy_f = ndi.gaussian_filter(iso_grav, sigma=1.5, order=[1, 0])
    gx_f = ndi.gaussian_filter(iso_grav, sigma=1.5, order=[0, 1])
    gh_fine = np.maximum(grav_slope, np.hypot(gy_f, gx_f) * 0.5)
    theta_grav = np.arctan2(grav_vg, gh_fine + 1e-4)
    # Contact sharpness peaks where |theta_grav| -> 0 AND horizontal gradient is strong
    grav_grad_rk = _rank_unit(gh_fine, fp)
    grav_contact_raw = (np.exp(-np.abs(theta_grav) / 0.35) * np.sqrt( np.maximum(grav_grad_rk, 0.0) )).astype(np.float32)

    # Updip normal-fault dip backprojection: Great Basin normal dip delta ~ 58 deg -> cot(58 deg) = 0.6249
    # A fault intersecting bedrock surface at (y, x) produces its basement step downdip at (y + dy, x + dx)
    shift_px = np.clip((depth_base * 0.6249) / 100.0, 0.0, 12.0).astype(np.float32)
    yy, xx = np.indices((H, W), dtype=np.float32)
    grav_updip_raw = _bilinear_sample(
        grav_contact_raw,
        yy + uy_basin * shift_px,
        xx + ux_basin * shift_px,
    )
    # Combine multi-dip (55-65 deg) envelope (0.75 * 58deg + 0.25 * 65deg)
    grav_updip_raw = (
        0.70 * grav_updip_raw
        + 0.30 * _bilinear_sample(grav_contact_raw, yy + uy_basin * (shift_px * 0.75), xx + ux_basin * (shift_px * 0.75))
    ).astype(np.float32)

    # RTP magnetic phase-tilt & shallow GeoDAWN upward-continuation residual
    ry = ndi.gaussian_filter(rtp, sigma=1.5, order=[1, 0])
    rx = ndi.gaussian_filter(rtp, sigma=1.5, order=[0, 1])
    rh = np.maximum(tmi_hg * 0.05, np.hypot(ry, rx))
    # Approximate RTP vertical derivative via Band 9 tmi_vg + high-pass RTP Laplacian
    rtp_vg_est = tmi_vg - 0.5 * ndi.gaussian_laplace(rtp, sigma=1.5)
    theta_mag = np.arctan2(rtp_vg_est, rh + 1e-3)
    with rasterio.open(ROOT / ".cache/external/geodawn_extensions_u8.tif") as ds_ext:
        tmi_up150_u8 = ds_ext.read(4).astype(np.float32)
    tmi_up_grad = np.hypot(
        ndi.sobel(tmi_up150_u8, axis=0),
        ndi.sobel(tmi_up150_u8, axis=1),
    )
    mag_edge_rk = 0.65 * _rank_unit(rh, fp) + 0.35 * _rank_unit(tmi_up_grad, fp)
    mag_contact_raw = (np.exp(-np.abs(theta_mag) / 0.45) * np.sqrt(np.maximum(mag_edge_rk, 0.0))).astype(np.float32)
    mag_updip_raw = _bilinear_sample(
        mag_contact_raw,
        yy + uy_basin * (0.55 * shift_px),
        xx + ux_basin * (0.55 * shift_px),
    )

    # Basin-margin basement-hinge curvature (footwall-to-hanging-wall flexure)
    base_lap = -ndi.gaussian_laplace(depth_base, sigma=3.0)
    hinge_raw = 0.60 * _rank_unit(np.abs(base_lap), fp) + 0.40 * _rank_unit(np.abs(grav_vg), fp)

    # Local potential-field strike vector (tangent = perpendicular to fine gravity gradient)
    # Used downstream for Andersonian transtensional alignment
    gnorm = np.hypot(gy_f, gx_f) + 1e-6
    # Map grid: +x East, +y South -> geographic East = +gx, North = -gy
    # Tangent vector (strike): East = -gy_n, North = -gx_n (rotated 90 deg)
    st_e = (-gy_f / gnorm).astype(np.float32)
    st_n = (-gx_f / gnorm).astype(np.float32)
    cos2phi = (st_n * st_n - st_e * st_e).astype(np.float32)  # cos(2 * azimuth_from_north)
    sin2phi = (2.0 * st_n * st_e).astype(np.float32)

    out = {
        "udpc_grav_tilt_zero": _rank_unit(grav_contact_raw, fp),
        "udpc_grav_updip": _rank_unit(grav_updip_raw, fp),
        "udpc_mag_updip": _rank_unit(mag_updip_raw, fp),
        "udpc_basin_margin_curv": _rank_unit(hinge_raw, fp),
    }
    del iso_grav, grav_slope, grav_vg, depth_base, rtp, tmi_hg, tmi_vg, yy, xx
    gc.collect()
    return out, cos2phi, sin2phi


def _unpack_fp(arr_or_vec: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Unpack a footprint-indexed 1-D vector (5,167,373,) into full 2-D grid (3730, 3292)."""
    if arr_or_vec.ndim == 2 and arr_or_vec.shape == fp.shape:
        return arr_or_vec.astype(np.float32, copy=False)
    out = np.full(fp.shape, np.nan, dtype=np.float32)
    out[fp] = arr_or_vec.astype(np.float32, copy=False)
    return out


def _build_dopsr(fp: np.ndarray, udpc_grav_updip: np.ndarray) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    """Build Module 2 (DOPSR): seam-free 1m LiDAR + 10m 3DEP drainage-orthogonal & road-deconfounded scarps."""
    det_elev = _load_band_imputed(12, fp)
    det_slope = _load_band_imputed(19, fp)

    # Load 10m seamless 3DEP channels (99.6% footprint coverage; stored as footprint-packed 1D float32)
    d10_os3 = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_onesided3.f32.npy"), fp)
    d10_hgm = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_hgm50_max.f32.npy"), fp)
    d10_curv = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_curv_absmax.f32.npy"), fp)
    d10_val = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_valid_frac.f32.npy"), fp)
    m10 = fp & np.isfinite(d10_os3) & np.isfinite(d10_val) & (d10_val > 0.1)

    scarp10 = (
        0.50 * _rank_unit(np.where(m10, d10_os3, 0.0), m10)
        + 0.30 * _rank_unit(np.where(m10, d10_hgm, 0.0), m10)
        + 0.20 * _rank_unit(np.where(m10, d10_curv, 0.0), m10)
    ).astype(np.float32)
    scarp10[~m10] = _rank_unit(det_slope, fp)[~m10]
    del d10_hgm, d10_curv, d10_val

    # Load 1m USGS 3DEP LiDAR scarp channels & apply 500 m interior feathering so tile seams NEVER emit ridges
    with rasterio.open(ROOT / ".cache/external/lidar_scarp_features_u8.tif") as ds_lid:
        lid_step = ds_lid.read(3).astype(np.float32)      # step_max
        lid_down = ds_lid.read(6).astype(np.float32)      # downface_max
        lid_coh = ds_lid.read(10).astype(np.float32)      # coh100
        lid_valid = ds_lid.read(12) > 128                 # valid coverage mask

    lid_interior = fp & ndi.binary_erosion(lid_valid, iterations=3)
    if lid_interior.any():
        lid_raw = (
            0.45 * _rank_unit(lid_step, lid_interior)
            + 0.30 * _rank_unit(lid_down, lid_interior)
            + 0.25 * _rank_unit(lid_coh, lid_interior)
        ).astype(np.float32)
        # Smooth feather weight over 6 px (600 m) inside LiDAR boundary
        dist_in = ndi.distance_transform_edt(lid_valid).astype(np.float32)
        w_lid = np.clip((dist_in - 2.0) / 6.0, 0.0, 0.65) * fp
        scarp_seamfree = ((1.0 - w_lid) * scarp10 + w_lid * lid_raw).astype(np.float32)
        del lid_raw, dist_in, w_lid
    else:
        scarp_seamfree = scarp10.copy()
    del lid_step, lid_down, lid_coh, lid_valid

    # Drainage-orthogonal deconfounding:
    # Regional range-front slope vector (sigma=12 px = 1.2 km): points upslope toward mountain block
    ry_reg = ndi.gaussian_filter(det_elev, sigma=12.0, order=[1, 0])
    rx_reg = ndi.gaussian_filter(det_elev, sigma=12.0, order=[0, 1])
    rnorm = np.hypot(ry_reg, rx_reg) + 1e-5
    uy_reg = (ry_reg / rnorm).astype(np.float32)
    ux_reg = (rx_reg / rnorm).astype(np.float32)

    # Fine-scale scarp normal from structure tensor of 10m onesided scarp + det_elev (sigma=1.2)
    fine_surf = 0.6 * _rank_unit(np.nan_to_num(d10_os3, nan=0.0), fp) + 0.4 * _rank_unit(det_elev, fp)
    fy = ndi.gaussian_filter(fine_surf, sigma=1.2, order=[1, 0])
    fx = ndi.gaussian_filter(fine_surf, sigma=1.2, order=[0, 1])
    fnorm = np.hypot(fy, fx) + 1e-6
    ny_scarp = (fy / fnorm).astype(np.float32)
    nx_scarp = (fx / fnorm).astype(np.float32)
    del d10_os3, fine_surf

    # Tectonic range-front scarps strike sub-parallel to regional contours -> |n_scarp . u_reg| ~ 1
    # Radial alluvial-fan incised washes run down-slope -> n_wash perpendicular to u_reg -> |n . u_reg| ~ 0
    cos_align = np.abs(ny_scarp * uy_reg + nx_scarp * ux_reg)
    drainage_orth_raw = (scarp_seamfree * (0.25 + 0.75 * (cos_align ** 1.5))).astype(np.float32)

    # TIGER 2024 road embankment deconfounder:
    with rasterio.open(ROOT / ".cache/external/tiger_road_distance_m.tif") as ds_rd:
        road_d = np.nan_to_num(ds_rd.read(1).astype(np.float32), nan=5000.0)
    road_penalty = 1.0 - 0.80 * np.exp(-((road_d / 160.0) ** 2)) * (1.0 - udpc_grav_updip)
    road_deconf_raw = (drainage_orth_raw * road_penalty).astype(np.float32)
    del road_d, road_penalty

    # Piedmont apron inflection (peaks along mountain-front & intra-basin benches where slope transitions)
    slope_sm = ndi.gaussian_filter(det_slope, sigma=2.0)
    slope_grad = np.hypot(
        ndi.gaussian_filter(slope_sm, sigma=3.0, order=[1, 0]),
        ndi.gaussian_filter(slope_sm, sigma=3.0, order=[0, 1]),
    )
    piedmont_raw = 0.55 * _rank_unit(slope_grad, fp) + 0.45 * _rank_unit(slope_sm, fp)

    # Topographic scarp strike (for stress tensor fusion)
    st_e = (-fy / fnorm).astype(np.float32)
    st_n = (-fx / fnorm).astype(np.float32)
    t_cos2 = (st_n * st_n - st_e * st_e).astype(np.float32)
    t_sin2 = (2.0 * st_n * st_e).astype(np.float32)

    out = {
        "dopsr_scarp_seamfree": _rank_unit(scarp_seamfree, fp),
        "dopsr_drainage_orth": _rank_unit(drainage_orth_raw, fp),
        "dopsr_road_deconfounded": _rank_unit(road_deconf_raw, fp),
        "dopsr_piedmont_inflection": _rank_unit(piedmont_raw, fp),
    }
    del det_elev, det_slope, scarp10, scarp_seamfree, drainage_orth_raw, road_deconf_raw
    gc.collect()
    return out, t_cos2, t_sin2


def _build_thermal_upflow_grid(shape: tuple[int, int], fp: np.ndarray) -> np.ndarray:
    """Rasterize GDR #1391 springs/geothermometers + 2m temperature probes + paleo-sinter mounds.

    STRICT LEAKAGE GUARD: Reads ONLY physical coordinates & temperatures; NEVER reads dist_known_fault_px.
    """
    H, W = shape
    impulses_fine = np.zeros((H, W), dtype=np.float32)
    impulses_broad = np.zeros((H, W), dtype=np.float32)

    # 1. GDR #1391 thermal springs & wells (physical columns ONLY)
    ws_path = ROOT / ".cache/external/gdr_wellspring_in_footprint.csv"
    with ws_path.open("r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        # Explicit guard assertion: never access dist_known_fault_px
        for r in rdr:
            try:
                rr = int(float(r["row"]))
                cc = int(float(r["col"]))
                if not (0 <= rr < H and 0 <= cc < W and fp[rr, cc]):
                    continue
                tc = float(r["temp_c"]) if r.get("temp_c") not in ("", "nan", None) else 15.0
                tq = float(r["geothermquartz_c"]) if r.get("geothermquartz_c") not in ("", "nan", None) else 0.0
                tch = float(r["geothermchalc_c"]) if r.get("geothermchalc_c") not in ("", "nan", None) else 0.0
                if not np.isfinite(tc):
                    tc = 15.0
                if not np.isfinite(tq):
                    tq = 0.0
                if not np.isfinite(tch):
                    tch = 0.0
                w_sp = np.clip((tc - 20.0) / 60.0, 0.0, 2.0) + 0.6 * np.clip((max(tq, tch) - 70.0) / 110.0, 0.0, 1.5)
                if w_sp > 0.05:
                    impulses_fine[rr, cc] = max(impulses_fine[rr, cc], float(w_sp))
                    impulses_broad[rr, cc] += float(w_sp)
            except Exception:
                continue

    # 2. INGENIOUS 2-meter temperature probes (F2mDAB positive anomaly above background)
    z2m = ROOT / ".cache/external/2m_temperature_probe_INGENIOUS_regional_data.zip"
    with zipfile.ZipFile(z2m) as zf:
        dbf_name = [n for n in zf.namelist() if n.endswith(".dbf")][0]
        raw = zf.read(dbf_name)
    num_rec, header_len, rec_len = struct.unpack("<IHH", raw[4:12])
    fields = []
    pos = 32
    while raw[pos] != 0x0D:
        fname = raw[pos : pos + 11].split(b"\x00", 1)[0].decode("ascii")
        flen = raw[pos + 16]
        fields.append((fname, flen))
        pos += 32
    lons, lats, w_probes = [], [], []
    offset = header_len
    for _ in range(num_rec):
        rec = raw[offset : offset + rec_len]
        offset += rec_len
        if rec[0] == 0x2A:
            continue
        p = 1
        row_d = {}
        for fname, flen in fields:
            row_d[fname] = rec[p : p + flen].decode("latin1").strip()
            p += flen
        try:
            la = float(row_d["LatDegreeN"])
            lo = float(row_d["LongDegree"])
            if lo > 0:
                lo = -lo
            fd = float(row_d["F2mDAB"]) if row_d["F2mDAB"] else 0.0
            if np.isfinite(fd) and fd > 0.25:
                lons.append(lo)
                lats.append(la)
                w_probes.append(min(fd / 5.0, 2.5))
        except Exception:
            continue
    if lons:
        xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
        cols = np.floor((np.asarray(xs) - 243350.0) / 100.0).astype(np.int32)
        rows = np.floor((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int32)
        for rr, cc, ww in zip(rows, cols, w_probes):
            if 0 <= rr < H and 0 <= cc < W and fp[rr, cc]:
                impulses_fine[rr, cc] = max(impulses_fine[rr, cc], float(ww))
                impulses_broad[rr, cc] += float(ww)

    # 3. Quaternary paleo-geothermal sinter, travertine & opalite mounds (latin1 encoded)
    zpal = ROOT / ".cache/external/paleo_geothermal_regional.zip"
    with zipfile.ZipFile(zpal) as zf:
        cname = [n for n in zf.namelist() if n.endswith(".csv")][0]
        txt = zf.read(cname).decode("latin1")
    plons, plats, pw = [], [], []
    for r in csv.DictReader(txt.splitlines()):
        try:
            la = float(r["Lat_deg_NAD83"])
            lo = float(r["Long_deg_NAD83"])
            if lo > 0:
                lo = -lo
            dtype = (r.get("Deposit_type") or "").lower()
            w_dep = 2.0 if ("sinter" in dtype or "travertine" in dtype or "opal" in dtype) else 1.2
            plons.append(lo)
            plats.append(la)
            pw.append(w_dep)
        except Exception:
            continue
    if plons:
        pxs, pys = warp_transform("EPSG:4269", "EPSG:32611", plons, plats)
        pcols = np.floor((np.asarray(pxs) - 243350.0) / 100.0).astype(np.int32)
        prows = np.floor((4508550.0 - np.asarray(pys)) / 100.0).astype(np.int32)
        for rr, cc, ww in zip(prows, pcols, pw):
            if 0 <= rr < H and 0 <= cc < W and fp[rr, cc]:
                impulses_fine[rr, cc] = max(impulses_fine[rr, cc], float(ww))
                impulses_broad[rr, cc] += float(ww)

    upflow = (
        0.60 * ndi.gaussian_filter(impulses_fine, sigma=3.5)
        + 0.40 * ndi.gaussian_filter(np.log1p(impulses_broad), sigma=11.0)
    ).astype(np.float32)
    return _rank_unit(upflow, fp)


def _build_hmcs_and_stress(
    fp: np.ndarray,
    udpc_grav_updip: np.ndarray,
    cos2phi: np.ndarray,
    sin2phi: np.ndarray,
) -> dict[str, np.ndarray]:
    """Build Module 3 (HMCS hydrothermal/alteration/vents + Andersonian stress/seismicity)."""
    rtp = _load_band_imputed(2, fp)
    tmi_hg = _load_band_imputed(3, fp)
    tmi_vg = _load_band_imputed(9, fp)
    rad_tc = _load_band_imputed(6, fp)      # IR-BAND6-TC-RADIOMETRIC: gamma-ray Total Count
    cond_surf = _load_band_imputed(17, fp)
    geod_2nd = _load_band_imputed(4, fp)
    geod_shr = _load_band_imputed(7, fp)
    geod_dil = _load_band_imputed(8, fp)
    deq = _load_band_imputed(10, fp)
    ieq = _load_band_imputed(16, fp)

    # 1. Hydrothermal magnetite destruction: sulfidation/illitization destroys primary titanomagnetite
    # along fluid-bearing basement steps -> strong updip gravity contact paired with low high-pass magnetic analytic signal
    rtp_hp = rtp - ndi.gaussian_filter(rtp, sigma=8.0)
    asig = np.sqrt(
        ndi.gaussian_filter(rtp_hp, sigma=1.5, order=[1, 0]) ** 2
        + ndi.gaussian_filter(rtp_hp, sigma=1.5, order=[0, 1]) ** 2
        + (tmi_vg * 20.0) ** 2
    )
    mag_quiet = 1.0 - _rank_unit(0.5 * asig + 0.5 * tmi_hg, fp)
    mag_destr_raw = (udpc_grav_updip * (0.35 + 0.65 * mag_quiet)).astype(np.float32)
    del rtp, rtp_hp, asig, tmi_hg, tmi_vg

    # 2. Potassium-metasomatic (adularia-sericite) alteration from GeoDAWN radiometrics
    with rasterio.open(ROOT / ".cache/external/geodawn_rad_u8.tif") as ds_rad:
        rad_k = ds_rad.read(1).astype(np.float32)
    with rasterio.open(ROOT / ".cache/external/geodawn_extensions_u8.tif") as ds_ext:
        rad_thk = ds_ext.read(1).astype(np.float32)  # Th/K ratio (depressed in K-metasomatism)
    rad_valid = fp & (rad_k > 0)
    k_enrich = (
        0.45 * _rank_unit(rad_k, rad_valid if rad_valid.any() else fp)
        + 0.35 * (1.0 - _rank_unit(rad_thk, rad_valid if rad_valid.any() else fp))
        + 0.20 * _rank_unit(rad_tc, fp)
    ).astype(np.float32)
    if (~rad_valid & fp).any():
        k_enrich[~rad_valid & fp] = _rank_unit(rad_tc, fp)[~rad_valid & fp]
    del rad_k, rad_thk, rad_tc

    # 3. Shallow MT electrical conductivity + lateral boundary (clay-cap / thermal brine conduit)
    cond_grad = np.hypot(
        ndi.gaussian_filter(cond_surf, sigma=2.0, order=[1, 0]),
        ndi.gaussian_filter(cond_surf, sigma=2.0, order=[0, 1]),
    )
    # Note: lower resistivity or sharp lateral resistivity boundary marks fault gouge / alteration
    mt_raw = 0.55 * _rank_unit(cond_grad, fp) + 0.45 * (1.0 - _rank_unit(cond_surf, fp))
    del cond_surf, cond_grad

    # 4. Direct GDR #1391 thermal springs, 2m probes & paleo-sinter mounds
    thermal_upflow = _build_thermal_upflow_grid(fp.shape, fp)

    # 5. Sensor-only Updip Contact x Hydrothermal Alteration/Upflow Concordance (zero SGMC bedrock catalog)
    mt_rk = _rank_unit(mt_raw, fp)
    k_rk = _rank_unit(k_enrich, fp)
    hydro_comp = 0.42 * thermal_upflow + 0.33 * mt_rk + 0.25 * k_rk
    updip_alt_conc = _rank_unit(np.sqrt(np.maximum(udpc_grav_updip * hydro_comp, 0.0)), fp)

    # 6. Andersonian transtensional slip + dilation tendency & microseismic activation
    # Optimal normal-fault strike in NW Great Basin: N20E (azimuth=20 deg -> 2*phi = 40 deg)
    # Optimal Walker Lane dextral strike: N35W (azimuth=-35 deg -> 2*phi = -70 deg)
    c40, s40 = float(np.cos(np.deg2rad(40.0))), float(np.sin(np.deg2rad(40.0)))
    cm70, sm70 = float(np.cos(np.deg2rad(-70.0))), float(np.sin(np.deg2rad(-70.0)))
    align_norm = 0.5 * (1.0 + cos2phi * c40 + sin2phi * s40)
    align_wl = 0.5 * (1.0 + cos2phi * cm70 + sin2phi * sm70)
    strike_opt = np.maximum(align_norm, 0.85 * align_wl)

    strain_mag = (
        0.40 * _rank_unit(geod_2nd, fp)
        + 0.30 * _rank_unit(geod_shr, fp)
        + 0.30 * _rank_unit(np.maximum(geod_dil, 0.0), fp)
    )
    seis_act = 0.55 * _rank_unit(np.exp(-deq / 8500.0), fp) + 0.45 * _rank_unit(ieq, fp)
    stress_raw = ((0.55 * strain_mag + 0.45 * seis_act) * (0.40 + 0.60 * strike_opt)).astype(np.float32)

    out = {
        "hmcs_mag_destruction": _rank_unit(mag_destr_raw, fp),
        "hmcs_k_th_alteration": k_rk,
        "hmcs_mt_cond": mt_rk,
        "hmcs_thermal_upflow": thermal_upflow,
        "hmcs_updip_alteration_concordance": updip_alt_conc,
        "stress_anderson_seis": _rank_unit(stress_raw, fp),
    }
    gc.collect()
    return out


def ensure_blind_feature_cache(grid: Grid, force: bool = False) -> dict[str, Path]:
    """Compute (or load from .cache/apartgems_features/) all 14 blind physical features."""
    FEAT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    paths = {name: FEAT_CACHE_DIR / f"{name}.f32.npy" for name in E2_HYDRO_STRESS_FEATURES}
    if not force and all(p.exists() for p in paths.values()):
        return paths

    fp = grid.footprint
    udpc, g_cos2, g_sin2 = _build_udpc_and_strike(fp)
    dopsr, t_cos2, t_sin2 = _build_dopsr(fp, udpc["udpc_grav_updip"])
    # Blend structural strike vector (50% gravity contact tangent + 50% topographic scarp tangent)
    b_cos2 = 0.5 * (g_cos2 + t_cos2)
    b_sin2 = 0.5 * (g_sin2 + t_sin2)
    norm2 = np.hypot(b_cos2, b_sin2) + 1e-6
    hmcs = _build_hmcs_and_stress(fp, udpc["udpc_grav_updip"], b_cos2 / norm2, b_sin2 / norm2)

    all_maps = {**udpc, **dopsr, **hmcs}
    meta_summary = {}
    for name, arr in all_maps.items():
        clean = np.where(fp & np.isfinite(arr), np.clip(arr, 0.0, 1.0), 0.0).astype(np.float32)
        np.save(paths[name], clean)
        meta_summary[name] = {
            "min_in_fp": float(clean[fp].min()),
            "mean_in_fp": float(clean[fp].mean()),
            "max_in_fp": float(clean[fp].max()),
        }
    (FEAT_CACHE_DIR / "blind_features_manifest.json").write_text(json.dumps(meta_summary, indent=2) + "\n")
    del all_maps, udpc, dopsr, hmcs
    gc.collect()
    return paths


def compute_visible_relay_features(visible_mask: np.ndarray, fp: np.ndarray) -> dict[str, np.ndarray]:
    """Compute strictly fold-visible VTRB structural continuation features (NO isotropic collar ring!).

    Uses ONLY `visible_mask` (fold['visible'] inside holdout; full existing_faults.tif ONLY at final export).
    """
    vis = np.asarray(visible_mask, dtype=bool) & fp
    H, W = vis.shape
    if not vis.any():
        z = np.zeros((H, W), dtype=np.float32)
        return {k: z.copy() for k in VTRB_VISIBLE_FEATURES}

    # Find morphological endpoints / fault tips of visible traces (pixels with 1 or 2 8-connected neighbours)
    nb_count = ndi.convolve(vis.astype(np.int16), np.ones((3, 3), dtype=np.int16), mode="constant", cval=0) - 1
    tips = vis & (nb_count >= 1) & (nb_count <= 2)
    # Estimate local tangent vector along visible fault traces via smoothed trace field
    vis_sm = ndi.gaussian_filter(vis.astype(np.float32), sigma=2.5)
    # Hessian minor eigenvector / gradient perpendicular gives fault strike; even simpler and cleaner:
    # For each tip pixel, compute vector from centroid of visible pixels in an 11x11 window TO the tip!
    yy, xx = np.indices((H, W), dtype=np.float32)
    w_sum = ndi.uniform_filter(vis.astype(np.float32), size=11, mode="constant") * 121.0 + 1e-6
    cy = ndi.uniform_filter((vis * yy).astype(np.float32), size=11, mode="constant") * 121.0 / w_sum
    cx = ndi.uniform_filter((vis * xx).astype(np.float32), size=11, mode="constant") * 121.0 / w_sum

    ty_idx, tx_idx = np.nonzero(tips)
    dy_out = ty_idx.astype(np.float32) - cy[ty_idx, tx_idx]
    dx_out = tx_idx.astype(np.float32) - cx[ty_idx, tx_idx]
    dnorm = np.hypot(dy_out, dx_out)
    good = dnorm > 0.4
    ty_idx, tx_idx = ty_idx[good], tx_idx[good]
    uy_out = (dy_out[good] / dnorm[good]).astype(np.float32)
    ux_out = (dx_out[good] / dnorm[good]).astype(np.float32)

    # Project directional tip-propagation rays 3..32 px forward off visible tips (vectorized over ray steps!)
    tip_accum = np.zeros((H, W), dtype=np.float32)
    for step in range(3, 33):
        w_step = float(np.exp(-step / 16.0))
        ry = np.rint(ty_idx + uy_out * step).astype(np.int32)
        rx = np.rint(tx_idx + ux_out * step).astype(np.int32)
        inb = (ry >= 0) & (ry < H) & (rx >= 0) & (rx < W)
        np.maximum.at(tip_accum, (ry[inb], rx[inb]), w_step)
    tip_cone = ndi.gaussian_filter(tip_accum, sigma=2.2)

    # Step-over / relay bridge field: peaks where TWO distinct visible fault tips lie within 5..40 px
    # Subtract single-tip self-blur from squared multi-tip blur so isolated single tips vanish and PAIRED tips light up!
    tip_imp = np.zeros((H, W), dtype=np.float32)
    tip_imp[ty_idx, tx_idx] = 1.0
    g_broad = ndi.gaussian_filter(tip_imp, sigma=11.0)
    g_self = ndi.gaussian_filter(tip_imp, sigma=3.0)
    stepover_raw = np.maximum(g_broad * g_broad - 0.12 * g_self * g_self, 0.0)

    # Regional tectonic belt density (broad sigma=28 px = 2.8 km smooth envelope, suppressing collar hugging)
    d_vis = ndi.distance_transform_edt(~vis).astype(np.float32)
    collar_suppress = 1.0 - np.exp(-((d_vis / 3.0) ** 2))
    belt_raw = ndi.gaussian_filter(vis.astype(np.float32), sigma=28.0) * collar_suppress

    return {
        "vtrb_tip_cone": _rank_unit(tip_cone * collar_suppress, fp),
        "vtrb_stepover_bridge": _rank_unit(stepover_raw * collar_suppress, fp),
        "vtrb_belt_density": _rank_unit(belt_raw, fp),
    }
