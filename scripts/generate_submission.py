#!/usr/bin/env python3
"""Archived synthetic demonstration, NOT a geological model or a submission.

The prior parallel run used simulated Gaussian fields and simulated faults;
its TIFF had a guessed (0, 0) origin and fails the pinned mirrored grid. A new
hash alone does not establish lane uniqueness. The CLI is intentionally
disabled: it must not manufacture further incorrect submission-looking files.
The internal helpers remain solely as historical research code.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"

# Competition format spec (GEMSDOE family format receipts; e.g.
# GEMSDOE31: "EPSG:32611 · 3730x3292 · float32 · 0 NaN · 37,654 binary dots")
HEIGHT, WIDTH = 3730, 3292
RES_M = 100.0
NDOTS = 37_654
MIN_SEP_PX = 2.8          # minimum dot separation (px)
CELF_RADIUS_M = 300.0     # competitive-local-emission radius (m)
CATALOGUE_COLLAR_PX = 2.0 # dots excluded within this distance of catalogue
SEED = 20261027

DEMO = True  # becomes False once real feature rasters exist in data/


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_bytes(buf: bytes) -> str:
    return hashlib.sha256(buf).hexdigest()


def _rng() -> np.random.Generator:
    return np.random.default_rng(SEED)


def _normalise01(a: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    a = np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0)
    lo, hi = float(np.min(a)), float(np.max(a))
    if hi - lo < eps:
        return np.zeros_like(a)
    return np.clip((a - lo) / (hi - lo), 0.0, 1.0)


def _build_demo_surface(rng: np.random.Generator) -> np.ndarray:
    """
    Deterministic demonstration propensity surface (REPLACE WITH REAL FEATURES).

    Physical motivation encoded as smooth, structure-like anomalies:
    * broad radiometric alteration highs (Th/K proxy)
    * coincident magnetic lows (magnetite destruction proxy)
    * concave curvature nodes (relay/intersection proxy)
    blended for illustration; no leakage canary was run.
    """
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float64)

    def gauss_blob(cx, cy, sx, sy, amp):
        return amp * np.exp(-(((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2) / 2.0)

    # Several blind-conduit candidates distributed across the study area;
    # none coincides with any catalogue trace (catalogue is synthetic here too).
    thk = (
        gauss_blob(0.22 * WIDTH, 0.30 * HEIGHT, 0.07 * WIDTH, 0.09 * HEIGHT, 0.9)
        + gauss_blob(0.71 * WIDTH, 0.62 * HEIGHT, 0.05 * WIDTH, 0.06 * HEIGHT, 0.7)
        + gauss_blob(0.48 * WIDTH, 0.15 * HEIGHT, 0.04 * WIDTH, 0.05 * HEIGHT, 0.5)
    )
    tmi = (
        -gauss_blob(0.22 * WIDTH, 0.30 * HEIGHT, 0.09 * WIDTH, 0.11 * HEIGHT, 0.8)
        - gauss_blob(0.66 * WIDTH, 0.41 * HEIGHT, 0.06 * WIDTH, 0.07 * HEIGHT, 0.6)
    )
    curv = (
        gauss_blob(0.22 * WIDTH, 0.30 * HEIGHT, 0.03 * WIDTH, 0.04 * HEIGHT, 0.6)
        + gauss_blob(0.71 * WIDTH, 0.62 * HEIGHT, 0.025 * WIDTH, 0.035 * HEIGHT, 0.5)
    )

    surface = _normalise01(0.5 * thk + 0.3 * _normalise01(-tmi) + 0.2 * _normalise01(curv))
    # Gentle large-scale background so the surface is not purely blob-like.
    bg = 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * xx / WIDTH) * np.cos(2 * np.pi * yy / HEIGHT))
    surface = _normalise01(0.85 * surface + 0.15 * bg)
    return np.clip(surface, 0.0, 1.0).astype(np.float32)


def _build_catalogue_mask(rng: np.random.Generator) -> np.ndarray:
    """Demonstration catalogue (REPLACE WITH USGS/INGENIOUS existing_faults.tif).

    Synthetic traces that deliberately AVOID the blind-conduit anomalies so
    the exclusion-collar logic is exercised: dots placed off-catalogue target
    structures missing from the catalogue.
    """
    mask = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    for cx, cy, angle_deg, length_frac in [
        (0.10 * WIDTH, 0.50 * HEIGHT, 20.0, 0.55),
        (0.85 * WIDTH, 0.15 * HEIGHT, -15.0, 0.50),
        (0.45 * WIDTH, 0.80 * HEIGHT, 70.0, 0.40),
    ]:
        angle = math.radians(angle_deg)
        L = length_frac * max(WIDTH, HEIGHT)
        t = np.linspace(-L / 2, L / 2, int(L / RES_M) + 1)
        dx = (t * np.cos(angle)).astype(int)
        dy = (-(t * np.sin(angle))).astype(int)
        xs = np.clip(int(cx) + dx, 0, WIDTH - 1)
        ys = np.clip(int(cy) + dy, 0, HEIGHT - 1)
        mask[ys, xs] = 1
    # Dilate the traces by CATALOGUE_COLLAR_PX to form the exclusion collar.
    from scipy.ndimage import binary_dilation  # type: ignore

    return binary_dilation(mask.astype(bool),
                           iterations=int(math.ceil(CATALOGUE_COLLAR_PX)))


def _celf_dots(surface: np.ndarray, exclude_mask: np.ndarray, n_dots: int,
               min_sep_px: float, rng: np.random.Generator) -> np.ndarray:
    """
    Competitive-local-emission dotted placement (CELF-300 m).

    Vectorised implementation:
      1. Weight candidates by surface value (outside the catalogue collar).
      2. Sample oversampled candidate points via inverse-CDF (non-lattice).
      3. Greedy non-maximum suppression sorted by surface value, using a
         spatial grid hash for O(1) min-separation checks.
    Returns a binary dots array.
    """
    surface = np.asarray(surface, dtype=np.float64)
    avail = np.where(exclude_mask, 0.0, surface)
    total = float(avail.sum())
    if total <= 0.0 or n_dots <= 0:
        return np.zeros_like(surface, dtype=np.uint8)

    flat = avail.ravel()
    cdf = np.cumsum(flat)
    cdf /= cdf[-1]

    # Oversample to compensate for NMS rejection, but stay far below a
    # regular lattice: points are inverse-CDF samples, not a grid.
    n_candidates = min(surface.size, max(n_dots * 20, 200_000))
    u = rng.random(n_candidates)
    idx = np.searchsorted(cdf, u)
    np.clip(idx, 0, surface.size - 1, out=idx)
    cand_y = idx // WIDTH
    cand_x = idx % WIDTH
    cand_vals = flat[idx]

    order = np.argsort(-cand_vals, kind="stable")
    cand_y = cand_y[order]
    cand_x = cand_x[order]
    cand_vals = cand_vals[order]

    dots = np.zeros_like(surface, dtype=np.uint8)
    cell = max(min_sep_px, 1.0)
    grid: dict[tuple[int, int], list[tuple[int, int]]] = {}
    min_sep_sq = min_sep_px * min_sep_px

    placed = 0
    for cy, cx, _v in zip(cand_y.tolist(), cand_x.tolist(), cand_vals.tolist()):
        if placed >= n_dots:
            break
        gy, gx = int(cy // cell), int(cx // cell)
        near = False
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for ty, tx in grid.get((gy + dy, gx + dx), ()):
                    if (cy - ty) ** 2 + (cx - tx) ** 2 <= min_sep_sq:
                        near = True
                        break
                if near:
                    break
            if near:
                break
        if near:
            continue
        dots[cy, cx] = 1
        grid.setdefault((gy, gx), []).append((cy, cx))
        placed += 1
    return dots


def _write_geotiff(path: Path, arr: np.ndarray, crs, transform) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff", "dtype": "float32", "count": 1,
        "height": arr.shape[0], "width": arr.shape[1],
        "crs": crs, "transform": transform,
        "tiled": False, "compress": "deflate", "nodata": None,
    }
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(arr.astype(np.float32), 1)
        ds.set_band_description(1, "blind-conduit propensity [0,1] (research demo)")


def main() -> int:
    print("STOP: synthetic demo generation is disabled; it is not a geological "
          "model and its previous TIFF failed the mirrored grid. No new file was written.",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
