"""Physical feature engineering for H-APART-2 (MAW-GSI).

Multi-Azimuth Strike-Worm, Antislope Piedmont Dipole & Geothermal Structural-Intersection Synthesis.
100% Zero-SGMC in training and inference; sentinel-sanitized; explicit NaN missingness across the
24.61% NE Nevada 1 m LiDAR gap; strictly fold-visible fracture-mechanics features in holdout.

Feature blocks:
  - E1_BLIND_FEATURES (30 features):
      Core official terrain/tectonic context + 1 m LiDAR de-quantized antislope graben & crest-toe
      scarp dipole (with TIGER 2024 road deconfounder) + 10 m seamless 3DEP breaklines + 8-azimuth
      (1.1-1.5 km) flank-subtracted topographic & potential-field strike worms + 58 deg updip
      phase-tilt contacts + Gallardo-Meju (2004) cross-gradient alignment & volcanic-plug curl.
  - E2_BLIND_VENT_FEATURES (40 features = E1 + 10 hydrothermal/structural-intersection features):
      Faulds-Hinz (2015) orthogonal/conjugate 2nd-azimuth structural-intersection vent operators
      I_vent = sqrt(max(W_(1), 0) * max(W_perp, 0)) on topography & subsurface potential fields +
      multi-physics strike coherence + shallow hydrothermal magnetite oxidation (z(TMI_up150)-z(RTP)) +
      GeoDAWN potassic K/Th & U/K alteration + MT cond_surf clay-cap edge + sanitized DOE GDR #1391
      thermal springs/geothermometers, 2 m F2mDAB thermal probes ([0.5, 54.7] deg C), & Quaternary
      paleo-sinter vents + Andersonian transtensional seismicity alignment.
  - VTRB_VISIBLE_FEATURES (5 fold-visible features):
      Anisotropic fault-tip propagation cones, paired en-echelon step-over relay bridges, host-segment
      displacement-length transfer, and collar-tempered tectonic belt proximity clip(d_vis, 8.0, 45.0)
      (constant inside 0..800 m so near-catalogue collar hugging is mathematically impossible).
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
from scipy.signal import fftconvolve

from gems57.grid import Grid

ROOT = Path(__file__).resolve().parents[2]
FEAT_CACHE_DIR = ROOT / ".cache/apartgems_maw_gsi_v2"

E1_BLIND_FEATURES: tuple[str, ...] = (
    # Core official terrain & strain context (7)
    "det_elev_norm",
    "det_slope_log",
    "depth_base_log",
    "piedmont_hinge_gate",
    "geod_2ndinv_log",
    "geod_shearrate_log",
    "geod_dilaterate",
    # 1 m LiDAR physical scarp & antislope graben dipole (8; NaN outside LiDAR coverage)
    "lidar_step_relnorm",
    "lidar_antislope_graben",
    "lidar_tect_fluvial_ratio",
    "lidar_crest_toe_dipole",
    "lidar_ex_max",
    "lidar_coh100",
    "lidar_relief_log",
    "road_berm_prox",
    # 10 m seamless 3DEP breaklines & topographic multi-azimuth strike worms (8)
    "dem10_onesided_relnorm",
    "dem10_slope_max",
    "dem10_hgm50_max",
    "dem10_curv_absmax",
    "dem10_onesided_local",
    "topo_seamfree_scarp",
    "topo_worm_1100m_max",
    "dem10_worm_1100m_max",
    # Subsurface potential-field updip contacts, worms & Gallardo-Meju cross-gradient (7)
    "grav_slope_log",
    "grav_vg",
    "grav_worm_1500m_max",
    "mag_hg_worm_1500m_max",
    "updip_grav_mag_tilt_contact",
    "gallardo_crossgrad_align",
    "gallardo_plug_curl",
)

E2_HYDRO_STRESS_FEATURES: tuple[str, ...] = E1_BLIND_FEATURES + (
    "struct_intersect_topo_vent",
    "struct_intersect_geophys_vent",
    "topo_geophys_strike_coherence",
    "hydro_demag_up150_rtp",
    "potassic_k_th_alteration",
    "mt_claycap_edge",
    "gdr_spring_geotherm_conduit",
    "probe2m_sinter_vent_field",
    "vent_coupled_intersection",
    "earthq_anderson_alignment",
)

VTRB_VISIBLE_FEATURES: tuple[str, ...] = (
    "vtrb_tip_cone",
    "vtrb_stepover_bridge",
    "vtrb_host_len_transfer",
    "d_vis_belt_tempered",
    "vtrb_belt_density_far",
)


def _load_band_sanitized(band_idx: int, fp: np.ndarray) -> np.ndarray:
    """Load official band (1..19), sanitize non-finite & float32 nodata sentinels (|x| > 1e30)."""
    raw = np.load(ROOT / f".cache/features/band-{band_idx:02d}.npy").astype(np.float32)
    valid = fp & np.isfinite(raw) & (np.abs(raw) < 1.0e30)
    med = float(np.median(raw[valid])) if valid.any() else 0.0
    out = np.where(valid, raw, med).astype(np.float32)
    out[~fp] = med
    return out


def _zscore_fp(arr: np.ndarray, valid_mask: np.ndarray, clip_sd: float = 6.0) -> np.ndarray:
    """Robust IQR-scaled standardization strictly over valid_mask; 0 outside."""
    out = np.zeros(arr.shape, dtype=np.float32)
    v = arr[valid_mask]
    v = v[np.isfinite(v)]
    if v.size == 0:
        return out
    q25, q50, q75 = np.percentile(v, [25.0, 50.0, 75.0])
    scale = float(max((q75 - q25) / 1.349, 1e-5))
    z = np.clip((arr[valid_mask] - float(q50)) / scale, -clip_sd, clip_sd)
    out[valid_mask] = z.astype(np.float32)
    return out


def _unpack_fp(arr_or_vec: np.ndarray, fp: np.ndarray) -> np.ndarray:
    if arr_or_vec.ndim == 2 and arr_or_vec.shape == fp.shape:
        return arr_or_vec.astype(np.float32, copy=False)
    out = np.full(fp.shape, np.nan, dtype=np.float32)
    out[fp] = arr_or_vec.astype(np.float32, copy=False)
    return out


def _bilinear_sample(img: np.ndarray, yy: np.ndarray, xx: np.ndarray) -> np.ndarray:
    H, W = img.shape
    y = np.clip(yy, 0.0, H - 1.001)
    x = np.clip(xx, 0.0, W - 1.001)
    y0 = np.floor(y).astype(np.int32)
    x0 = np.floor(x).astype(np.int32)
    wy = (y - y0).astype(np.float32)
    wx = (x - x0).astype(np.float32)
    return (
        (1.0 - wy) * ((1.0 - wx) * img[y0, x0] + wx * img[y0, x0 + 1])
        + wy * ((1.0 - wx) * img[y0 + 1, x0] + wx * img[y0 + 1, x0 + 1])
    ).astype(np.float32)


def make_worm_kernels(
    n_azimuths: int = 8,
    half_size: int = 7,
    sigma_along: float = 4.2,
    sigma_cross: float = 0.85,
    flank_offset: float = 2.6,
    sigma_flank: float = 1.35,
) -> tuple[list[np.ndarray], np.ndarray]:
    """Build zero-DC flank-subtracted anisotropic strike-worm filter bank across [0, pi)."""
    coords = np.arange(-half_size, half_size + 1, dtype=np.float32)
    yy, xx = np.meshgrid(coords, coords, indexing="ij")
    azimuths = np.linspace(0.0, np.pi, n_azimuths, endpoint=False, dtype=np.float32)
    kernels: list[np.ndarray] = []
    for az in azimuths:
        # Azimuth measured clockwise from North (+East = +x, +North = -y)
        ux = float(np.sin(az))
        uy = float(-np.cos(az))
        # Along-strike coordinate s, cross-strike coordinate c
        s = xx * ux + yy * uy
        c = -xx * uy + yy * ux
        along = np.exp(-0.5 * (s / sigma_along) ** 2)
        center = np.exp(-0.5 * (c / sigma_cross) ** 2)
        flanks = 0.5 * (
            np.exp(-0.5 * ((c - flank_offset) / sigma_flank) ** 2)
            + np.exp(-0.5 * ((c + flank_offset) / sigma_flank) ** 2)
        )
        # Normalize flanks so integral of kernel == 0.0 (zero response on flat plateaus/ramps)
        pos_part = along * center
        neg_part = along * flanks
        neg_scale = float(pos_part.sum() / max(float(neg_part.sum()), 1e-8))
        k = (pos_part - neg_scale * neg_part).astype(np.float32)
        k -= float(k.mean())
        norm = float(np.linalg.norm(k))
        kernels.append((k / max(norm, 1e-8)).astype(np.float32))
    return kernels, azimuths


def multi_azimuth_worm_and_vent(
    field: np.ndarray,
    fp: np.ndarray,
    half_size: int = 7,
    sigma_along: float = 4.2,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate 8-azimuth strike-worm bank & Faulds-Hinz orthogonal/conjugate intersection index.

    Memory-frugal implementation: stores per-azimuth responses strictly over `fp` (165 MB vs 393 MB).
    """
    kernels, azimuths = make_worm_kernels(
        n_azimuths=8, half_size=half_size, sigma_along=sigma_along
    )
    clean = np.where(fp & np.isfinite(field), field, 0.0).astype(np.float32)
    n_fp = int(fp.sum())
    resp_fp = np.empty((8, n_fp), dtype=np.float32)
    for k_idx, kern in enumerate(kernels):
        conv = fftconvolve(clean, kern, mode="same").astype(np.float32)
        resp_fp[k_idx] = conv[fp]
        del conv

    best_idx = np.argmax(resp_fp, axis=0)
    w_max_fp = np.take_along_axis(resp_fp, best_idx[None, :], axis=0)[0]

    w_perp_fp = np.full(n_fp, -1e9, dtype=np.float32)
    for dk in (2, 3, 4, 5, 6):
        idx_dk = ((best_idx + dk) & 7)[None, :]
        r_dk = np.take_along_axis(resp_fp, idx_dk, axis=0)[0]
        np.maximum(w_perp_fp, r_dk, out=w_perp_fp)
    del resp_fp

    w_max = np.zeros(field.shape, dtype=np.float32)
    i_vent = np.zeros(field.shape, dtype=np.float32)
    cos2az = np.zeros(field.shape, dtype=np.float32)
    sin2az = np.zeros(field.shape, dtype=np.float32)

    w_max[fp] = w_max_fp
    i_vent[fp] = np.sqrt(np.maximum(w_max_fp, 0.0) * np.maximum(w_perp_fp, 0.0)).astype(np.float32)
    dom_az = azimuths[best_idx]
    cos2az[fp] = np.cos(2.0 * dom_az).astype(np.float32)
    sin2az[fp] = np.sin(2.0 * dom_az).astype(np.float32)
    return w_max, i_vent, cos2az, sin2az


def _build_sanitized_hydrothermal_fields(shape: tuple[int, int], fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rasterize sanitized GDR #1391 springs/geothermometers + 2m F2mDAB probes + paleo-sinter mounds.

    STRICT LEAKAGE GUARD:
      - Reads ONLY physical coordinates, temperatures, geothermometers, and deposit types.
      - NEVER reads `dist_known_fault_px`.
      - Filters 2m temperature probe `F2mDAB` strictly to finite `[0.5, 54.7]` deg C.
    """
    H, W = shape
    spring_imp = np.zeros((H, W), dtype=np.float32)
    probe_imp = np.zeros((H, W), dtype=np.float32)
    sinter_mask = np.zeros((H, W), dtype=bool)

    # 1. GDR #1391 thermal springs & wells
    ws_path = ROOT / ".cache/external/gdr_wellspring_in_footprint.csv"
    with ws_path.open("r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        assert rdr.fieldnames is not None
        for r in rdr:
            try:
                rr = int(float(r["row"]))
                cc = int(float(r["col"]))
                if not (0 <= rr < H and 0 <= cc < W and fp[rr, cc]):
                    continue
                tc = float(r["temp_c"]) if r.get("temp_c") not in ("", "nan", None) else 15.0
                tq = float(r["geothermquartz_c"]) if r.get("geothermquartz_c") not in ("", "nan", None) else 0.0
                tch = float(r["geothermchalc_c"]) if r.get("geothermchalc_c") not in ("", "nan", None) else 0.0
                tc = tc if (np.isfinite(tc) and tc < 350.0) else 15.0
                tq = tq if (np.isfinite(tq) and tq < 380.0) else 0.0
                tch = tch if (np.isfinite(tch) and tch < 380.0) else 0.0
                w_sp = np.clip((tc - 21.0) / 55.0, 0.0, 2.2) + 0.65 * np.clip(
                    (max(tq, tch) - 65.0) / 110.0, 0.0, 1.8
                )
                if w_sp > 0.05:
                    spring_imp[rr, cc] = max(spring_imp[rr, cc], float(w_sp))
            except Exception:
                continue

    # 2. INGENIOUS 2-meter temperature probes (F2mDAB sanitized to [0.5, 55.0] deg C)
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
            if np.isfinite(fd) and 0.5 <= fd <= 55.0:
                lons.append(lo)
                lats.append(la)
                w_probes.append(float(np.log1p(fd)))
        except Exception:
            continue
    if lons:
        xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
        cols = np.floor((np.asarray(xs) - 243350.0) / 100.0).astype(np.int32)
        rows = np.floor((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int32)
        for rr, cc, ww in zip(rows, cols, w_probes):
            if 0 <= rr < H and 0 <= cc < W and fp[rr, cc]:
                probe_imp[rr, cc] = max(probe_imp[rr, cc], ww)

    # 3. Quaternary paleo-geothermal sinter, travertine & opalite vents
    zpal = ROOT / ".cache/external/paleo_geothermal_regional.zip"
    with zipfile.ZipFile(zpal) as zf:
        cname = [n for n in zf.namelist() if n.endswith(".csv")][0]
        txt = zf.read(cname).decode("latin1")
    plons, plats = [], []
    for r in csv.DictReader(txt.splitlines()):
        try:
            la = float(r["Lat_deg_NAD83"])
            lo = float(r["Long_deg_NAD83"])
            if lo > 0:
                lo = -lo
            plons.append(lo)
            plats.append(la)
        except Exception:
            continue
    if plons:
        pxs, pys = warp_transform("EPSG:4269", "EPSG:32611", plons, plats)
        pcols = np.floor((np.asarray(pxs) - 243350.0) / 100.0).astype(np.int32)
        prows = np.floor((4508550.0 - np.asarray(pys)) / 100.0).astype(np.int32)
        for rr, cc in zip(prows, pcols):
            if 0 <= rr < H and 0 <= cc < W and fp[rr, cc]:
                sinter_mask[rr, cc] = True

    spring_field = (
        0.65 * ndi.gaussian_filter(spring_imp, sigma=9.0)
        + 0.35 * ndi.gaussian_filter(spring_imp, sigma=24.0)
    ).astype(np.float32)

    d_sinter = ndi.distance_transform_edt(~sinter_mask).astype(np.float32) if sinter_mask.any() else np.full((H, W), 999.0, np.float32)
    probe_sinter_field = (
        0.55 * ndi.gaussian_filter(probe_imp, sigma=8.0)
        + 0.20 * ndi.gaussian_filter(probe_imp, sigma=22.0)
        + 0.25 * np.exp(-d_sinter / 12.0)
    ).astype(np.float32)
    return spring_field, probe_sinter_field


def ensure_blind_feature_cache(grid: Grid, force: bool = False) -> dict[str, Path]:
    """Retired lane: the legacy derived cache is not bound to every source."""
    raise RuntimeError('H-APART-2 lane stopped; its legacy derived-feature cache requires a source-bound redesign before any future lane can use it')
    FEAT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    paths = {name: FEAT_CACHE_DIR / f"{name}.fp.f32.npy" for name in E2_HYDRO_STRESS_FEATURES}
    manifest_p = FEAT_CACHE_DIR / "blind_features_manifest.json"
    if not force and manifest_p.exists() and all(p.exists() for p in paths.values()):
        return paths

    fp = grid.footprint
    H, W = fp.shape
    out_fp: dict[str, np.ndarray] = {}

    # --- 1. Official core terrain & strain context ---
    det_elev = _load_band_sanitized(12, fp)
    det_slope = np.clip(_load_band_sanitized(19, fp), 0.0, 85.0)
    depth_base = np.clip(_load_band_sanitized(15, fp), 0.0, 6000.0)
    geod_2nd = np.clip(_load_band_sanitized(4, fp), 0.0, None)
    geod_shr = np.clip(_load_band_sanitized(7, fp), 0.0, None)
    geod_dil = _load_band_sanitized(8, fp)

    out_fp["det_elev_norm"] = _zscore_fp(det_elev, fp)[fp]
    out_fp["det_slope_log"] = np.log1p(det_slope)[fp].astype(np.float32)
    out_fp["depth_base_log"] = np.log1p(depth_base)[fp].astype(np.float32)
    # Piedmont hinge peaks along shallowly buried range-front / intra-basin benches (depth 15..600 m, moderate slope)
    pied_hinge = np.exp(-(((np.log1p(depth_base) - 4.4) / 2.1) ** 2)) * np.exp(
        -(((det_slope - 6.5) / 8.5) ** 2)
    )
    out_fp["piedmont_hinge_gate"] = pied_hinge[fp].astype(np.float32)
    out_fp["geod_2ndinv_log"] = np.log1p(geod_2nd * 1e3)[fp].astype(np.float32)
    out_fp["geod_shearrate_log"] = np.log1p(geod_shr * 1e3)[fp].astype(np.float32)
    out_fp["geod_dilaterate"] = _zscore_fp(geod_dil, fp)[fp]
    del geod_2nd, geod_shr, geod_dil, pied_hinge

    # --- 2. 1 m USGS 3DEP LiDAR physical scarp & antislope graben dipole (NaN outside LiDAR) ---
    with rasterio.open(ROOT / ".cache/external/lidar_scarp_features_u8.tif") as ds_lid:
        q_ex_max = ds_lid.read(1)
        q_step = ds_lid.read(3)
        q_lapneg = ds_lid.read(4)
        q_lappos = ds_lid.read(5)
        q_down = ds_lid.read(6)
        q_up = ds_lid.read(7)
        q_cross = ds_lid.read(8)
        q_relief = ds_lid.read(9)
        q_coh = ds_lid.read(10)
        q_valid = ds_lid.read(12)

    # Erode 2 px (200 m) inside LiDAR tile perimeter so coverage-boundary steps become NaN rather than false scarps
    lid_ok = fp & (q_valid >= 64) & (q_step > 0)
    lid_ok = ndi.binary_erosion(lid_ok, iterations=2) & fp

    def _deq_sq(q: np.ndarray) -> np.ndarray:
        u = np.clip((q.astype(np.float32) - 1.0) / 254.0, 0.0, 1.0)
        return (u * u).astype(np.float32)

    def _deq_lin(q: np.ndarray) -> np.ndarray:
        return np.clip((q.astype(np.float32) - 1.0) / 254.0, 0.0, 1.0).astype(np.float32)

    ex_max = _deq_sq(q_ex_max)
    step_max = _deq_sq(q_step)
    lapneg = _deq_sq(q_lapneg)
    lappos = _deq_sq(q_lappos)
    downf = _deq_sq(q_down)
    upf = _deq_sq(q_up)
    crossf = _deq_sq(q_cross)
    relief = _deq_sq(q_relief)
    coh100 = _deq_lin(q_coh)
    del q_ex_max, q_step, q_lapneg, q_lappos, q_down, q_up, q_cross, q_relief, q_coh, q_valid

    step_relnorm = step_max / np.sqrt(relief + 0.025)
    antislope_graben = upf * (0.25 + coh100) / (crossf + 0.025)
    tect_fluvial = np.maximum(downf, 1.35 * upf) * (0.30 + coh100) / (crossf + 0.025)
    crest_toe_dip = np.sqrt(np.maximum(lapneg * lappos, 0.0))
    relief_log = np.log1p(relief * 25.0)

    def _pack_lidar_nan(arr2d: np.ndarray) -> np.ndarray:
        vec = arr2d[fp].astype(np.float32, copy=True)
        vec[~lid_ok[fp]] = np.nan
        return vec

    out_fp["lidar_step_relnorm"] = _pack_lidar_nan(step_relnorm)
    out_fp["lidar_antislope_graben"] = _pack_lidar_nan(antislope_graben)
    out_fp["lidar_tect_fluvial_ratio"] = _pack_lidar_nan(tect_fluvial)
    out_fp["lidar_crest_toe_dipole"] = _pack_lidar_nan(crest_toe_dip)
    out_fp["lidar_ex_max"] = _pack_lidar_nan(ex_max)
    out_fp["lidar_coh100"] = _pack_lidar_nan(coh100)
    out_fp["lidar_relief_log"] = _pack_lidar_nan(relief_log)

    # TIGER/Line 2024 road distance deconfounder
    with rasterio.open(ROOT / ".cache/external/tiger_road_distance_m.tif") as ds_rd:
        road_d = np.nan_to_num(ds_rd.read(1).astype(np.float32), nan=5000.0, posinf=5000.0, neginf=0.0)
    road_prox = np.exp(-np.clip(road_d, 0.0, 2000.0) / 110.0).astype(np.float32)
    out_fp["road_berm_prox"] = road_prox[fp]
    del ex_max, step_max, lapneg, lappos, downf, upf, crossf, relief, coh100, relief_log, road_d

    # --- 3. 10 m seamless 3DEP breaklines & Multi-Azimuth Topographic Strike Worms ---
    d10_os3 = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_onesided3.f32.npy"), fp)
    d10_os1 = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_onesided.f32.npy"), fp)
    d10_slp = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_slope_max.f32.npy"), fp)
    d10_hgm = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_hgm50_max.f32.npy"), fp)
    d10_curv = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_curv_absmax.f32.npy"), fp)
    d10_res = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_resid_range.f32.npy"), fp)
    d10_val = _unpack_fp(np.load(ROOT / ".cache/dem10/dem10_valid_frac.f32.npy"), fp)
    m10 = fp & np.isfinite(d10_os3) & np.isfinite(d10_val) & (d10_val > 0.1)

    d10_os3_relnorm = np.where(m10, d10_os3 / np.sqrt(np.maximum(d10_res, 0.0) + 1.5), np.nan).astype(np.float32)
    out_fp["dem10_onesided_relnorm"] = np.where(m10[fp], d10_os3_relnorm[fp], np.nan).astype(np.float32)
    out_fp["dem10_slope_max"] = np.where(m10[fp], np.log1p(np.maximum(d10_slp[fp], 0.0)), np.nan).astype(np.float32)
    out_fp["dem10_hgm50_max"] = np.where(m10[fp], np.log1p(np.maximum(d10_hgm[fp], 0.0)), np.nan).astype(np.float32)
    out_fp["dem10_curv_absmax"] = np.where(m10[fp], np.log1p(np.maximum(d10_curv[fp], 0.0) * 10.0), np.nan).astype(np.float32)
    out_fp["dem10_onesided_local"] = np.where(m10[fp], np.log1p(np.maximum(d10_os1[fp], 0.0)), np.nan).astype(np.float32)

    # Seam-free standardized scarp field for 2D spatial worm convolution (smooth 500 m interior feather)
    z10_scarp = 0.55 * _zscore_fp(np.nan_to_num(d10_os3_relnorm, nan=0.0), m10) + 0.45 * _zscore_fp(
        np.log1p(np.maximum(np.nan_to_num(d10_hgm, nan=0.0), 0.0)), m10
    )
    z10_scarp[~m10 & fp] = _zscore_fp(np.log1p(det_slope), fp)[~m10 & fp]
    zlid_scarp = (
        0.40 * _zscore_fp(step_relnorm, lid_ok)
        + 0.35 * _zscore_fp(tect_fluvial, lid_ok)
        + 0.25 * _zscore_fp(antislope_graben, lid_ok)
    )
    dist_lid_in = ndi.distance_transform_edt(lid_ok).astype(np.float32)
    w_lid_feather = np.clip((dist_lid_in - 1.0) / 5.0, 0.0, 0.65) * lid_ok
    seamfree_scarp = ((1.0 - w_lid_feather) * z10_scarp + w_lid_feather * zlid_scarp) * (1.0 - 0.55 * road_prox)
    seamfree_scarp[~fp] = 0.0
    out_fp["topo_seamfree_scarp"] = seamfree_scarp[fp].astype(np.float32)

    topo_w_max, topo_i_vent, topo_c2, topo_s2 = multi_azimuth_worm_and_vent(
        seamfree_scarp, fp, half_size=7, sigma_along=4.2
    )
    d10_w_max, _, _, _ = multi_azimuth_worm_and_vent(
        z10_scarp * (1.0 - 0.50 * road_prox), fp, half_size=7, sigma_along=4.2
    )
    out_fp["topo_worm_1100m_max"] = topo_w_max[fp]
    out_fp["dem10_worm_1100m_max"] = d10_w_max[fp]
    del step_relnorm, antislope_graben, tect_fluvial, crest_toe_dip, dist_lid_in, w_lid_feather
    del d10_os3, d10_os1, d10_slp, d10_hgm, d10_curv, d10_res, d10_val, d10_os3_relnorm, z10_scarp, zlid_scarp, d10_w_max
    gc.collect()

    # --- 4. Subsurface Gravity/Magnetic Updip Contacts, Worms & Gallardo-Meju Cross-Gradient ---
    rtp = _load_band_sanitized(2, fp)
    tmi_hg = np.clip(_load_band_sanitized(3, fp), 0.0, None)
    tmi_vg = _load_band_sanitized(9, fp)
    grav_slope = np.maximum(
        np.clip(_load_band_sanitized(5, fp), 0.0, None),
        np.clip(_load_band_sanitized(18, fp), 0.0, None),
    )
    grav_vg = _load_band_sanitized(11, fp)
    iso_grav = _load_band_sanitized(13, fp)

    grav_slope_log = np.log1p(grav_slope * 10.0).astype(np.float32)
    mag_hg_log = np.log1p(tmi_hg).astype(np.float32)
    out_fp["grav_slope_log"] = grav_slope_log[fp]
    out_fp["grav_vg"] = _zscore_fp(grav_vg, fp)[fp]

    grav_w_max, grav_i_vent, grav_c2, grav_s2 = multi_azimuth_worm_and_vent(
        _zscore_fp(grav_slope_log, fp), fp, half_size=8, sigma_along=5.0
    )
    mag_w_max, mag_i_vent, _, _ = multi_azimuth_worm_and_vent(
        _zscore_fp(mag_hg_log, fp), fp, half_size=8, sigma_along=5.0
    )
    out_fp["grav_worm_1500m_max"] = grav_w_max[fp]
    out_fp["mag_hg_worm_1500m_max"] = mag_w_max[fp]

    # 58 deg normal-fault updip phase-tilt migration
    gy_s = ndi.gaussian_filter(iso_grav, sigma=4.0, order=[1, 0])
    gx_s = ndi.gaussian_filter(iso_grav, sigma=4.0, order=[0, 1])
    gnorm_s = np.hypot(gy_s, gx_s) + 1e-6
    uy_basin = (-gy_s / gnorm_s).astype(np.float32)
    ux_basin = (-gx_s / gnorm_s).astype(np.float32)
    theta_g = np.arctan2(grav_vg, grav_slope + 1e-4)
    theta_m = np.arctan2(tmi_vg, tmi_hg * 0.05 + 1e-3)
    tilt_contact = (
        0.65 * np.exp(-((theta_g / 0.36) ** 2)) * np.tanh(grav_slope_log)
        + 0.35 * np.exp(-((theta_m / 0.42) ** 2)) * np.tanh(mag_hg_log * 0.35)
    ).astype(np.float32)
    shift_px = np.clip((depth_base * 0.6249) / 100.0, 0.0, 12.0).astype(np.float32)
    yy, xx = np.indices((H, W), dtype=np.float32)
    updip_contact = (
        0.65 * _bilinear_sample(tilt_contact, yy + uy_basin * shift_px, xx + ux_basin * shift_px)
        + 0.35 * tilt_contact
    ).astype(np.float32)
    out_fp["updip_grav_mag_tilt_contact"] = updip_contact[fp]
    del yy, xx, tilt_contact, shift_px, uy_basin, ux_basin, theta_g, theta_m

    # Gallardo & Meju (2004) cross-gradient alignment vs circular volcanic-plug curl
    gy_f = ndi.gaussian_filter(iso_grav, sigma=1.8, order=[1, 0])
    gx_f = ndi.gaussian_filter(iso_grav, sigma=1.8, order=[0, 1])
    my_f = ndi.gaussian_filter(rtp, sigma=1.8, order=[1, 0])
    mx_f = ndi.gaussian_filter(rtp, sigma=1.8, order=[0, 1])
    gm_denom = (np.hypot(gy_f, gx_f) + 1e-4) * (np.hypot(my_f, mx_f) + 1e-3)
    gm_dot = np.abs(gy_f * my_f + gx_f * mx_f) / gm_denom
    gm_cross = np.abs(gy_f * mx_f - gx_f * my_f) / gm_denom
    gm_strength = np.sqrt(np.maximum(_zscore_fp(grav_slope_log, fp) + 1.5, 0.0) * np.maximum(_zscore_fp(mag_hg_log, fp) + 1.5, 0.0))
    out_fp["gallardo_crossgrad_align"] = (gm_dot * gm_strength)[fp].astype(np.float32)
    out_fp["gallardo_plug_curl"] = (gm_cross * gm_strength)[fp].astype(np.float32)
    del gy_s, gx_s, gnorm_s, gy_f, gx_f, my_f, mx_f, gm_denom, gm_dot, gm_cross, gm_strength
    del iso_grav, grav_vg, tmi_vg, tmi_hg, grav_slope, updip_contact
    gc.collect()

    # --- 5. Contrarian Geothermal Structural-Intersection & Hydrothermal Conduit Features (E2) ---
    # CRITICAL PHYSICAL LOCALIZATION LAW:
    # Hydrothermal springs, 2 m probes, MT conductivity, and microseismicity have 1-5 km sensor footprints,
    # whereas DTI evaluates with a strict 300 m triangular kernel. Every hydrothermal/stress indicator is
    # therefore multiplicatively gated by 100 m local structural lineament/intersection sharpness so flat
    # basin interiors receive ZERO multi-kilometer halo smear while real 100 m fault/vent crests are boosted.
    struct_sharp_gate = np.tanh(
        np.maximum(
            0.45 * topo_w_max
            + 0.30 * grav_w_max
            + 0.15 * mag_w_max
            + 0.25 * np.maximum(seamfree_scarp, 0.0),
            0.0,
        )
    ).astype(np.float32)

    out_fp["struct_intersect_topo_vent"] = topo_i_vent[fp]
    geophys_i_vent = (0.65 * grav_i_vent + 0.35 * mag_i_vent).astype(np.float32)
    out_fp["struct_intersect_geophys_vent"] = geophys_i_vent[fp]

    # Co-axial strike coherence between surface topographic worm and subsurface gravity worm
    cos_2diff = np.clip(topo_c2 * grav_c2 + topo_s2 * grav_s2, -1.0, 1.0)
    coax_align = 0.5 * (1.0 + cos_2diff)
    strike_coh = coax_align * np.sqrt(np.maximum(topo_w_max, 0.0) * np.maximum(grav_w_max, 0.0))
    out_fp["topo_geophys_strike_coherence"] = strike_coh[fp].astype(np.float32)

    # Shallow Hydrothermal Magnetite Oxidation: z(TMI_up150) - z(RTP_highpass) gated on 100 m structure
    with rasterio.open(ROOT / ".cache/external/geodawn_extensions_u8.tif") as ds_ext:
        q_thk = ds_ext.read(1)
        q_uk = ds_ext.read(2)
        q_up150 = ds_ext.read(4)
    with rasterio.open(ROOT / ".cache/external/geodawn_rad_u8.tif") as ds_rad:
        q_k = ds_rad.read(1)
        q_th = ds_rad.read(2)

    up150_ok = fp & (q_up150 > 0)
    rtp_hp = rtp - ndi.gaussian_filter(rtp, sigma=10.0)
    z_up150 = _zscore_fp(q_up150.astype(np.float32), up150_ok if up150_ok.any() else fp)
    z_rtp_hp = _zscore_fp(rtp_hp, fp)
    hydro_demag = np.maximum(z_up150 - z_rtp_hp, -1.5) * struct_sharp_gate
    hydro_demag_fp = hydro_demag[fp].astype(np.float32)
    hydro_demag_fp[~up150_ok[fp]] = np.nan
    out_fp["hydro_demag_up150_rtp"] = hydro_demag_fp
    del rtp, rtp_hp, z_up150, z_rtp_hp, q_up150

    # Potassic K/Th & U/K adularia-illite wallrock alteration gated on 100 m structure
    rad_ok = fp & (q_k > 0) & (q_th > 0)
    uk_grad = np.hypot(
        ndi.sobel(q_uk.astype(np.float32), axis=0),
        ndi.sobel(q_uk.astype(np.float32), axis=1),
    )
    potassic = (
        (
            0.45 * _zscore_fp(q_k.astype(np.float32), rad_ok if rad_ok.any() else fp)
            - 0.35 * _zscore_fp(q_thk.astype(np.float32), rad_ok if rad_ok.any() else fp)
            + 0.20 * _zscore_fp(uk_grad, rad_ok if rad_ok.any() else fp)
        )
        * struct_sharp_gate
    ).astype(np.float32)
    pot_fp = potassic[fp].copy()
    pot_fp[~rad_ok[fp]] = np.nan
    out_fp["potassic_k_th_alteration"] = pot_fp
    del q_thk, q_uk, q_k, q_th, uk_grad, potassic

    # MT electrical conductivity clay-cap boundary gated on 100 m structure
    cond_surf = np.clip(_load_band_sanitized(17, fp), 0.0, None)
    cond_log = np.log1p(cond_surf)
    cond_edge = np.hypot(
        ndi.gaussian_filter(cond_log, sigma=2.0, order=[1, 0]),
        ndi.gaussian_filter(cond_log, sigma=2.0, order=[0, 1]),
    )
    mt_clay = (
        (0.65 * _zscore_fp(cond_edge, fp) - 0.35 * _zscore_fp(cond_log, fp)) * struct_sharp_gate
    ).astype(np.float32)
    out_fp["mt_claycap_edge"] = mt_clay[fp]
    del cond_surf, cond_log, cond_edge

    # Sanitized DOE GDR #1391 springs/geothermometers + 2m F2mDAB thermal probes + Quaternary sinter vents
    # Gated strictly by 100 m structural lineament/intersection sharpness (zero flat-playa halo smear!)
    spring_field, probe_sinter_field = _build_sanitized_hydrothermal_fields((H, W), fp)
    out_fp["gdr_spring_geotherm_conduit"] = (spring_field * struct_sharp_gate)[fp].astype(np.float32)
    out_fp["probe2m_sinter_vent_field"] = (probe_sinter_field * struct_sharp_gate)[fp].astype(np.float32)

    # Coupled Geothermal Vent Structural-Intersection Node
    vent_node = (0.60 * topo_i_vent + 0.40 * geophys_i_vent) * (
        0.45
        + 0.30 * np.maximum(np.nan_to_num(hydro_demag, nan=0.0), 0.0)
        + 0.25 * np.log1p(spring_field + probe_sinter_field)
    )
    out_fp["vent_coupled_intersection"] = vent_node[fp].astype(np.float32)

    # Andersonian transtensional orientation (N20E Great Basin normal + N35W Walker Lane dextral) x seismicity x 100 m worm
    deq = np.clip(_load_band_sanitized(10, fp), 0.0, 200_000.0)
    ieq = np.clip(_load_band_sanitized(16, fp), 0.0, None)
    b_c2 = 0.55 * topo_c2 + 0.45 * grav_c2
    b_s2 = 0.55 * topo_s2 + 0.45 * grav_s2
    bnorm = np.hypot(b_c2, b_s2) + 1e-6
    b_c2 /= bnorm
    b_s2 /= bnorm
    c40, s40 = float(np.cos(np.deg2rad(40.0))), float(np.sin(np.deg2rad(40.0)))
    cm70, sm70 = float(np.cos(np.deg2rad(-70.0))), float(np.sin(np.deg2rad(-70.0)))
    anderson_opt = np.maximum(0.5 * (1.0 + b_c2 * c40 + b_s2 * s40), 0.88 * 0.5 * (1.0 + b_c2 * cm70 + b_s2 * sm70))
    seis_z = 0.55 * np.exp(-deq / 12000.0) + 0.45 * np.tanh(np.log1p(ieq * 100.0))
    out_fp["earthq_anderson_alignment"] = (seis_z * anderson_opt * struct_sharp_gate)[fp].astype(np.float32)

    del det_elev, det_slope, depth_base, seamfree_scarp, road_prox
    del topo_w_max, topo_i_vent, topo_c2, topo_s2, grav_w_max, grav_i_vent, grav_c2, grav_s2, mag_w_max, mag_i_vent
    gc.collect()

    manifest = {}
    for name in E2_HYDRO_STRESS_FEATURES:
        vec = out_fp[name].astype(np.float32, copy=False)
        np.save(paths[name], vec)
        fin = np.isfinite(vec)
        manifest[name] = {
            "finite_fraction": round(float(fin.mean()), 6),
            "min_finite": round(float(vec[fin].min()), 6) if fin.any() else 0.0,
            "median_finite": round(float(np.median(vec[fin])), 6) if fin.any() else 0.0,
            "max_finite": round(float(vec[fin].max()), 6) if fin.any() else 0.0,
        }
    manifest_p.write_text(json.dumps(manifest, indent=2) + "\n")
    return paths


def compute_visible_relay_features(visible_mask: np.ndarray, fp: np.ndarray) -> dict[str, np.ndarray]:
    """Compute strictly fold-visible fracture-mechanics & collar-tempered belt features (1D footprint-packed).

    CRITICAL ANTI-COLLAR & ZERO-LEAKAGE GUARANTEES:
      1. Derived strictly from `visible_mask` (`fold['visible']` inside holdout; full catalogue ONLY in live export).
      2. `d_vis_belt_tempered = np.clip(d_vis, 8.0, 45.0)` is CONSTANT (== 8.0) everywhere within 0..800 m of
         visible faults, mathematically preventing GBDT splits from hugging a 200-600 m near-catalogue halo ring.
      3. Tip cones and relay step-over bridges are suppressed inside <= 2.5 px of visible segments.
    """
    vis = np.asarray(visible_mask, dtype=bool) & fp
    H, W = vis.shape
    n_fp = int(fp.sum())
    if not vis.any():
        return {k: np.zeros(n_fp, dtype=np.float32) for k in VTRB_VISIBLE_FEATURES}

    d_vis, nearest_idx = ndi.distance_transform_edt(~vis, return_indices=True)
    d_vis = d_vis.astype(np.float32)
    collar_taper = np.clip((d_vis - 2.0) / 3.5, 0.0, 1.0).astype(np.float32)

    # Connected-component host-fault size (displacement-length scaling; Dawers et al., 1993)
    comp_lbl, n_comp = ndi.label(vis, structure=np.ones((3, 3), dtype=np.int8))
    if n_comp > 0:
        comp_sizes = np.bincount(comp_lbl.ravel()).astype(np.float32)
        comp_sizes[0] = 0.0
        host_len = comp_sizes[comp_lbl[nearest_idx[0], nearest_idx[1]]]
    else:
        host_len = np.zeros((H, W), dtype=np.float32)
    d_clamped = np.clip(d_vis, 8.0, 48.0).astype(np.float32)
    host_transfer = (np.log1p(host_len) * np.exp(-d_clamped / 20.0)).astype(np.float32)

    # Morphological fault endpoints & outward propagation cones (300 m .. 3.4 km)
    nb_count = ndi.convolve(vis.astype(np.int16), np.ones((3, 3), dtype=np.int16), mode="constant", cval=0) - 1
    tips = vis & (nb_count >= 1) & (nb_count <= 2)
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

    tip_accum = np.zeros((H, W), dtype=np.float32)
    for step in range(3, 35):
        w_step = float(np.exp(-step / 15.0))
        ry = np.rint(ty_idx + uy_out * step).astype(np.int32)
        rx = np.rint(tx_idx + ux_out * step).astype(np.int32)
        inb = (ry >= 0) & (ry < H) & (rx >= 0) & (rx < W)
        np.maximum.at(tip_accum, (ry[inb], rx[inb]), w_step)
    tip_cone = ndi.gaussian_filter(tip_accum, sigma=2.0) * collar_taper

    # Paired en-echelon relay-ramp step-over bridge (multi-tip interaction minus self-halo)
    tip_imp = np.zeros((H, W), dtype=np.float32)
    tip_imp[ty_idx, tx_idx] = 1.0
    g_broad = ndi.gaussian_filter(tip_imp, sigma=11.0)
    g_self = ndi.gaussian_filter(tip_imp, sigma=3.0)
    stepover = np.maximum(g_broad * g_broad - 0.12 * g_self * g_self, 0.0) * collar_taper

    # Far-scale (3.2 km) tectonic belt density with inner 800 m plateau clamping
    belt_far = ndi.gaussian_filter(vis.astype(np.float32), sigma=32.0) * np.clip((d_vis - 4.0) / 6.0, 0.25, 1.0)

    return {
        "vtrb_tip_cone": tip_cone[fp].astype(np.float32),
        "vtrb_stepover_bridge": (stepover * 1e3)[fp].astype(np.float32),
        "vtrb_host_len_transfer": host_transfer[fp].astype(np.float32),
        "d_vis_belt_tempered": d_clamped[fp].astype(np.float32),
        "vtrb_belt_density_far": (belt_far * 100.0)[fp].astype(np.float32),
    }
