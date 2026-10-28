"""Strict registry comparison. Missing/full-support data fails closed.

A registry is only as complete as its input inventory: this module does not
assert that the local inventory covers all past submissions. Ranks use every
footprint cell (not a sampled subset), and overlap uses every positive registry
pixel, including dense lattices and continuous surfaces.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
CACHE_REG = ROOT / ".cache/registry_index"


def fast_near_3px(pos_mask: np.ndarray) -> np.ndarray:
    h, w = pos_mask.shape
    out = np.zeros((h, w), dtype=bool)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dy * dy + dx * dx > 9 or abs(dy) >= h or abs(dx) >= w:
                continue
            out[max(0, dy):min(h, h + dy), max(0, dx):min(w, w + dx)] |= pos_mask[
                max(0, -dy):min(h, h - dy), max(0, -dx):min(w, w - dx)]
    return out


def _rank(v):
    r = rankdata(v).astype(np.float64)
    r -= r.mean()
    norm = float(np.linalg.norm(r))
    if not np.isfinite(norm) or norm == 0:
        raise ValueError("constant or non-finite raster: Spearman correlation undefined")
    return r / norm


def _registry(footprint):
    path = CACHE_REG / 'registry_manifest.json'
    if not path.is_file():
        raise FileNotFoundError('registry manifest missing; uniqueness cannot be established')
    manifest = json.loads(path.read_text())
    entries = manifest.get('entries', [])
    if not entries:
        raise ValueError('empty registry cannot establish uniqueness')
    for entry in entries:
        if not entry.get('full_support_and_ranks'):
            raise ValueError('incomplete or sampled registry cache; rebuild with full support and ranks')
        with np.load(CACHE_REG / entry['cache_npz']) as data:
            if not {'vals_fp', 'pos_flat'}.issubset(data.files):
                raise ValueError('registry cache missing full support or full footprint values')
            values = data['vals_fp']
            pos = data['pos_flat']
            if values.size != int(footprint.sum()) or pos.size != entry['positive_pixels']:
                raise ValueError('registry cache is incomplete or has a different footprint')
            if not np.isfinite(values).all():
                raise ValueError('registry cache contains non-finite footprint values')
            if hashlib.sha256(values.astype(np.float32).tobytes()).hexdigest() != entry['decoded_fp_sha256']:
                raise ValueError('registry footprint hash mismatch')
            expected_pos = np.flatnonzero(footprint.ravel())[values > 0]
            if not np.array_equal(pos, expected_pos):
                raise ValueError('registry support does not match footprint values')
    return entries


def _candidate(a, footprint):
    a, fp = np.asarray(a), np.asarray(footprint, bool)
    if a.ndim != 2 or a.shape != fp.shape or not fp.any():
        raise ValueError('candidate/footprint shape mismatch or empty footprint')
    if not np.isfinite(a[fp]).all():
        raise ValueError('candidate has non-finite footprint values')
    return a, fp, _rank(a[fp])


def check_surface_uniqueness(surface, footprint, spearman_cap=0.90):
    a, fp, rank = _candidate(surface, footprint)
    entries = _registry(fp)
    matches = []
    for entry in entries:
        with np.load(CACHE_REG / entry['cache_npz']) as data:
            rho = float(np.dot(rank, _rank(data['vals_fp'])))
        matches.append({'repo': entry['primary_repo'], 'file': entry['primary_rel'],
                        'spearman_rho': rho, 'abs_spearman_rho': abs(rho)})
    matches.sort(key=lambda x: x['abs_spearman_rho'], reverse=True)
    maximum = matches[0]['abs_spearman_rho']
    return {'gate': 'PRE_PLACEMENT_CONTINUOUS_SURFACE', 'rasters_checked': len(entries),
            'spearman_abs_cap': spearman_cap, 'max_abs_spearman_rho': maximum,
            'closest_registry_raster': matches[0], 'top_5_correlations': matches[:5],
            'passed': maximum <= spearman_cap,
            'scope': 'indexed registry only; completeness not established'}


def check_final_raster_uniqueness(final_raster, footprint, spearman_cap=0.90, overlap_cap=0.70):
    a, fp, rank = _candidate(final_raster, footprint)
    if not np.isfinite(a).all() or (a < 0).any() or (a > 1).any():
        raise ValueError('candidate must be finite and in [0,1] everywhere')
    entries = _registry(fp)
    dots = (a > 0) & fp
    n = int(dots.sum())
    if not n:
        raise ValueError('candidate has no positive dots')
    digest = hashlib.sha256(a[fp].astype(np.float32).tobytes()).hexdigest()
    matches = []
    collision = None
    for entry in entries:
        with np.load(CACHE_REG / entry['cache_npz']) as data:
            rho = float(np.dot(rank, _rank(data['vals_fp'])))
            support = np.zeros(a.size, dtype=bool)
            pos = data['pos_flat']
            if pos.size and (pos.min() < 0 or pos.max() >= a.size or np.unique(pos).size != pos.size):
                raise ValueError('invalid registry support indices')
            support[pos] = True
        overlap = float(fast_near_3px(support.reshape(a.shape))[dots].mean())
        matches.append({'repo': entry['primary_repo'], 'file': entry['primary_rel'],
                        'spearman_rho': rho, 'overlap_3px_fraction': overlap})
        if entry['decoded_fp_sha256'] == digest:
            collision = f"{entry['primary_repo']}:{entry['primary_rel']}"
    worst_rho = max(matches, key=lambda x: abs(x['spearman_rho']))
    worst_overlap = max(matches, key=lambda x: x['overlap_3px_fraction'])
    max_rho = abs(worst_rho['spearman_rho'])
    max_overlap = worst_overlap['overlap_3px_fraction']
    return {'gate': 'POST_PLACEMENT_FINAL_RASTER', 'candidate_decoded_fp_sha256': digest,
            'candidate_emitted_dots': n, 'rasters_checked': len(entries),
            'exact_hash_collision': collision, 'spearman_abs_cap': spearman_cap,
            'overlap_3px_cap': overlap_cap, 'max_abs_spearman_rho': max_rho,
            'closest_spearman_raster': worst_rho,
            'max_3px_overlap_vs_competing_detectors': max_overlap,
            'closest_3px_overlap_detector': worst_overlap,
            'scope': 'all positive support in indexed registry; completeness not established',
            'passed': collision is None and max_rho <= spearman_cap and max_overlap <= overlap_cap}
