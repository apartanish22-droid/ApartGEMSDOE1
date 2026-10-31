#!/usr/bin/env python3
"""H-SC1 lidar scarp-crest candidate: score, fold-honest holdout, and final GeoTIFF.

Hypothesis (run card in evidence/run_card_h-sc1.json)
-----------------------------------------------------
Concealed or young normal-fault scarps express as a convex crest (LoG crest
convexity) with a steep 10 m-scale step, coherent over 100 m.  Crest maxima of
the product of step and crest-convexity, gated by 100 m coherence, mark scarp
traces at the 2 m-derived USGS 3DEP scale.  Mimics: road cut-banks, canal and
channel banks, terrace risers, and agricultural field edges.

Leakage contract
----------------
* The SCORE MAP uses only the 3DEP-derived lidar channels (no catalogue).  It is
  therefore identical in every hide-and-recover fold, so no withheld fault can
  shape it.  ``test_scarp_crest.py`` asserts this by hashing the score map.
* The catalogue enters in exactly two places: (a) fold scoring removes only the
  VISIBLE catalogue for that fold (the shared v3 protocol); (b) the final file
  removes exact catalogue cells, as the shared writer requires.
* A per-channel leakage canary (AUC on withheld truth vs other active cells)
  is reported; AUC > 0.90 would mean leakage until explained.

Outputs
-------
* ``--mode holdout``: HOLDOUT-DTI per variant (evaluator gems57-pooled-hide-v3),
  withheld-positive count, paired-bootstrap 95% CI, and canary AUCs.
* ``--mode final``: writes a validated GeoTIFF via gems57.submission_writer.

Every number written here is HOLDOUT-DTI (proxy), never a leaderboard score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout as EH
from gems57 import load_grid
from gems57.holdout import buffered_component_draw
from gems57.submission_writer import write_submission

LIDAR = ROOT / ".cache" / "inputs" / "lidar_scarp_features_u8.tif"
LIDAR_SHA256 = "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568"
# Band order and decoding rule from buffered metadata of the GEMSDOE24 mirror:
# q = 1 + round(254 * t), t = sqrt(clip(x/xmax)) for 'sqrt' or linear; q = 0 is no lidar.
BANDS = {  # name: (xmax, kind)
    "ex_max": (1.5, "sqrt"), "ex_mean": (0.3, "sqrt"), "step_max": (1.0, "sqrt"),
    "lapneg_max": (0.05, "sqrt"), "lappos_max": (0.05, "sqrt"),
    "downface_max": (1.0, "sqrt"), "upface_max": (1.0, "sqrt"), "cross_max": (1.0, "sqrt"),
    "relief": (300.0, "sqrt"), "coh100": (1.0, "linear"), "strike": (180.0, "linear"),
    "valid": (1.0, "linear"),
}
BAND_ORDER = list(BANDS)
MIN_SEP_PX = 3.0            # greedy spacing: accepted dots are >= 3 px apart
SCORE_NAME = "S_crest"
CANDIDATE_NAME_PREFIX = "apartgems1-scs1-lidar-crest"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def decode_band(raw: np.ndarray, index: int, name: str) -> np.ndarray:
    xmax, kind = BANDS[name]
    q = raw[index].astype(np.float32)
    t = (q - 1.0) / 254.0
    x = xmax * (t if kind == "linear" else t * t)
    return np.where(q > 0, x, np.nan).astype(np.float32)


def read_raw_lidar(path: Path = LIDAR) -> np.ndarray:
    """Read the uint8 quantised lidar stack once after SHA-256 pin check (memory-conscious)."""
    if sha256_file(path) != LIDAR_SHA256:
        raise ValueError("lidar raster SHA-256 does not match the pinned mirror bytes")
    with rasterio.open(path) as src:
        if src.count != len(BAND_ORDER):
            raise ValueError("unexpected band count")
        return src.read()


def decode_lidar(names=None, raw=None) -> dict:
    """Decode selected quantised 2 m lidar channels to physical units; NaN where no lidar."""
    raw = read_raw_lidar() if raw is None else raw
    names = BAND_ORDER if names is None else list(names)
    return {n: decode_band(raw, BAND_ORDER.index(n), n) for n in names}


def crest_score(dec: dict, valid: np.ndarray) -> np.ndarray:
    """Label-free crest score in [0,1]: coherence x geometric mean of normalised step and crest convexity.

    Normalisation uses the 99th percentile over lidar-valid footprint cells, which
    involves no catalogue information.
    """
    step = dec["step_max"]
    lap = dec["lapneg_max"]
    coh = dec["coh100"]
    ok = valid & np.isfinite(step) & np.isfinite(lap) & np.isfinite(coh)
    p99_step = float(np.percentile(step[ok], 99))
    p99_lap = float(np.percentile(lap[ok], 99))
    s_step = np.clip(step / max(p99_step, 1e-9), 0.0, 1.0)
    s_lap = np.clip(lap / max(p99_lap, 1e-9), 0.0, 1.0)
    s = coh * np.sqrt(s_step * s_lap)
    s = np.where(ok, s, 0.0).astype(np.float32)
    return s


def crest_dots(score: np.ndarray, threshold: float, footprint: np.ndarray) -> np.ndarray:
    """3x3 local maxima of the score above ``threshold``, greedily thinned to >= 3 px spacing."""
    local_max = (score == ndi.maximum_filter(score, size=3, mode="constant", cval=0.0))
    cand = local_max & (score >= threshold) & footprint
    ys, xs = np.nonzero(cand)
    order = np.argsort(-score[ys, xs], kind="stable")
    h, w = score.shape
    blocked = np.zeros((h, w), bool)
    r = int(np.ceil(MIN_SEP_PX)) - 1          # block distances < 3 px  (<= 2 px)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (yy * yy + xx * xx) < MIN_SEP_PX * MIN_SEP_PX
    dots = np.zeros((h, w), bool)
    for k in order:
        y, x = int(ys[k]), int(xs[k])
        if blocked[y, x]:
            continue
        dots[y, x] = True
        y0, y1 = max(0, y - r), min(h, y + r + 1)
        x0, x1 = max(0, x - r), min(w, x + r + 1)
        blocked[y0:y1, x0:x1] |= disk[(y0 - y + r):(y1 - y + r), (x0 - x + r):(x1 - x + r)]
    return dots


def threshold_for_quantile(score: np.ndarray, valid: np.ndarray, q: float) -> float:
    vals = score[valid & (score > 0)]
    return float(np.quantile(vals, q))


def canary_auc(channel: np.ndarray, truth: np.ndarray, negatives: np.ndarray,
               rng: np.random.Generator, n_neg: int = 200_000) -> float:
    pos = channel[truth]
    neg_idx = np.flatnonzero(negatives)
    if neg_idx.size > n_neg:
        neg_idx = rng.choice(neg_idx, size=n_neg, replace=False)
    neg = channel.ravel()[neg_idx]
    pos_v = pos[np.isfinite(pos)]
    neg_v = neg[np.isfinite(neg)]
    if pos_v.size < 10 or neg_v.size < 10:
        return float("nan")
    y = np.r_[np.ones(pos_v.size), np.zeros(neg_v.size)]
    s = np.r_[pos_v, neg_v]
    return float(roc_auc_score(y, s))


def holdout_mode(args) -> dict:
    grid = load_grid()
    fp = grid.footprint
    raw = read_raw_lidar()
    dec = decode_lidar(["step_max", "lapneg_max", "coh100"], raw=raw)
    valid = np.isfinite(dec["coh100"]) & fp
    score = crest_score(dec, valid)
    del dec
    score_sha = hashlib.sha256(np.ascontiguousarray(score).tobytes()).hexdigest()

    folds, _ = buffered_component_draw(grid, seed=args.seed, hide_frac=0.20, buffer_px=3)
    folds = list(folds)
    # Canary: each channel alone, and the score, against withheld truth vs other active cells.
    rng = np.random.default_rng(args.seed)
    canary = {}
    truth_all = np.zeros(fp.shape, bool)
    negatives_all = np.zeros(fp.shape, bool)
    for fold in folds:
        truth_all |= fold["truth"]
        negatives_all |= (fold["region"] & ~fold["truth"] & ~fold["visible"] & fp)
    canary["S_crest"] = canary_auc(score, truth_all, negatives_all, rng)
    for i, name in enumerate(BAND_ORDER):
        arr = decode_band(raw, i, name)
        canary[name] = canary_auc(arr, truth_all, negatives_all, rng)
        del arr
    del raw
    canary_max = max(v for v in canary.values() if np.isfinite(v))

    variants = {}
    zero_terms = sum(EH.evaluate(np.zeros(fp.shape), fold, fp)[1] for fold in folds)
    for q in args.quantiles:
        thr = threshold_for_quantile(score, valid, q)
        global_dots = crest_dots(score, thr, fp)
        terms = 0
        policy_terms = 0
        per_fold = {}
        for fold in folds:
            # Fold-honest: remove only the VISIBLE catalogue for this fold.
            pred = (global_dots & ~fold["visible"]).astype(np.float64)
            res, t = EH.evaluate(pred, fold, fp)
            terms = terms + t
            # Exact submitted policy: ALSO drop every mapped-catalogue cell (final_mode does this).
            pred_policy = (global_dots & ~grid.catalogue & ~fold["visible"]).astype(np.float64)
            _pres, pt = EH.evaluate(pred_policy, fold, fp)
            policy_terms = policy_terms + pt
            per_fold[fold["receipt"]["fold"]] = dict(
                dti=float(res["dti"]), tpw=float(res["tpw"]), fpw=float(res["fpw"]),
                fnw=float(res["fnw"]), n_truth=int(res["n_truth"]), emitted=int(res["emitted"]))
        # Matched-count random control: uniform cells on lidar-valid footprint, no spacing rule.
        rrng = np.random.default_rng(args.seed + int(round(q * 1000)))
        pool = np.flatnonzero((valid & fp).ravel())
        rand_flat = rrng.choice(pool, size=int(global_dots.sum()), replace=False)
        rand_dots = np.zeros(fp.size, bool)
        rand_dots[rand_flat] = True
        rand_dots = rand_dots.reshape(fp.shape)
        rterms = 0
        for fold in folds:
            pred = (rand_dots & ~fold["visible"]).astype(np.float64)
            _res, t = EH.evaluate(pred, fold, fp)
            rterms = rterms + t
        rsummary = EH.pooled_summary({"candidate": rterms, "zero_control": zero_terms}, candidate="candidate")
        summary = EH.pooled_summary({"candidate": terms, "zero_control": zero_terms}, candidate="candidate")
        cand = summary["scores"]["candidate"]
        psummary = EH.pooled_summary({"candidate": policy_terms, "zero_control": zero_terms}, candidate="candidate")
        pcand = psummary["scores"]["candidate"]
        policy_dots = int((global_dots & ~grid.catalogue).sum())
        variants[f"q{q}"] = dict(
            random_matched_control_dti=rsummary["scores"]["candidate"]["dti"],
            random_matched_control_ci95=rsummary["scores"]["candidate"]["ci95"],
            
            quantile=q, threshold_score=thr, dots_global=int(global_dots.sum()),
            evidence_class="HOLDOUT-DTI", evaluator_version=EH.VERSION,
            dti=cand["dti"], ci95=cand["ci95"], withheld_positive_pixels=cand["withheld_positive_pixels"],
            paired_vs_zero=summary["paired_differences"]["zero_control"],
            # The exact file produced by final_mode (catalogue cells removed) under the same folds.
            submitted_policy=dict(dots=policy_dots, dti=pcand["dti"], ci95=pcand["ci95"],
                                  withheld_positive_pixels=pcand["withheld_positive_pixels"],
                                  note="Same folds; drops ALL mapped-catalogue cells, as the submitted file does. Pessimistic by construction because withheld truth lies on the catalogue."),
            per_fold=per_fold,
        )
    result = dict(
        hypothesis="H-SC1 lidar-only convex-crest scarp traces (no catalogue in score map)",
        evidence_class="HOLDOUT-DTI", evaluator_version=EH.VERSION,
        holdout_draw=dict(function="gems57.holdout.buffered_component_draw", seed=args.seed,
                          hide_frac=0.20, buffer_px=3, folds=len(folds)),
        score_map_sha256=score_sha, min_sep_px=MIN_SEP_PX,
        leakage_canary_auc=canary, leakage_canary_max=canary_max,
        canary_verdict=("PASS: all channel AUCs below 0.90" if canary_max < 0.90
                        else "FAIL: leakage until explained"),
        variants=variants,
        note=("Holdout is conditional on the fixed fold draw. Not a leaderboard estimate. "
              "Organizer scoring uses new faults not in the catalogue (rules excerpt R4)."),
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    return result


def final_mode(args) -> dict:
    grid = load_grid()
    fp = grid.footprint
    dec = decode_lidar(["step_max", "lapneg_max", "coh100"])
    valid = np.isfinite(dec["coh100"]) & fp
    score = crest_score(dec, valid)
    thr = threshold_for_quantile(score, valid, args.quantile)
    raw_dots = crest_dots(score, thr, fp)
    dots = raw_dots & ~grid.catalogue   # exact catalogue cells removed (policy; see holdout submitted_policy)
    prediction = np.where(dots, 1.0, 0.0).astype(np.float32)
    receipt = write_submission(
        args.out, prediction, ROOT / "data" / "bridge" / "sample_submission.tif", fp,
        name=args.name, note=args.note, catalogue=grid.catalogue,
        metadata=dict(hypothesis="H-SC1", quantile=args.quantile, threshold_score=thr,
                      min_sep_px=MIN_SEP_PX, lidar_sha256=LIDAR_SHA256,
                      catalogue_cells_removed=int((grid.catalogue & raw_dots).sum()),
                      dots_before_catalogue_removal=int(raw_dots.sum()),
                      dots=int(dots.sum())),
    )
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["holdout", "final"], required=True)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--quantiles", type=float, nargs="*", default=[0.99, 0.995, 0.999])
    ap.add_argument("--quantile", type=float, default=0.995)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--name", type=str)
    ap.add_argument("--note", type=str)
    args = ap.parse_args()
    if args.mode == "holdout":
        result = holdout_mode(args)
    else:
        if not (args.out and args.name and args.note):
            ap.error("final mode needs --out, --name and --note")
        result = final_mode(args)
    text = json.dumps(result, indent=2, allow_nan=False, default=float)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
