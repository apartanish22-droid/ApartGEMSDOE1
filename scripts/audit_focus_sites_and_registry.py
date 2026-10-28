#!/usr/bin/env python3
"""Recheck pinned focus-site rasters and decisive literal-uniqueness witnesses.

This is a bounded *negative* audit, not a complete live registry scan. It fetches
immutable public GitHub blobs, verifies their SHA-256 hashes, and measures the
saved bytes against the committed bridge grid. A single failing witness can
block release, but an incomplete witness list can never clear a submission.
No leaderboard slot is touched and no GeoTIFF is altered or generated.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from gems57 import load_grid
from gems57.gates import format_report
from gems57.uniqueness import dot_overlap, saturation_certificate
from gems57.validate import validate

CACHE = ROOT / ".cache/review"


@dataclass(frozen=True)
class Pin:
    repo: str
    commit: str
    path: str
    sha256: str
    local_name: str

    @property
    def url(self) -> str:
        return f"https://github.com/{self.repo}/blob/{self.commit}/{self.path}"


def focus(n: str, commit: str, filename: str, sha: str) -> Pin:
    return Pin(f"buffedlizard55-lab/GEMSDOE{n}", commit,
               "docs/downloads/" + filename, sha, f"focus{n}.tif")


# The byte pins are research copies identified in the nine-site review. Some
# are all-finite/NaN packaging alternatives; no claim is made that their exact
# bytes were uploaded or that an organizer receipt links them to the scores.
FOCUS = {
    "24": (focus("24", "063b04e2ff3154d0ffd017bb5723f4f717d1754d", "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif", "3e0730e8d4f7db095dd80246a98cba3bc0fc9a28f436b91db27ca34df4d0d1ce"), 0.2477),
    "25": (focus("25", "78064a194f97fee45b0d81b1bb3b6385729c5c2b", "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif", "3e78737f0da8dd2ca66cc6caac0ce8eeefcd6715707f8d1bd3091845cd9bcc30"), 0.2600),
    "27": (focus("27", "cf8b4c201f2cc2ef649b6ca7cd32f235c2f6743a", "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif", "a9bf76b57453a5b3af74c8eef837df53c29a0931162aa540b8763220b36ba3bb"), 0.2449),
    "28": (focus("28", "12ec4fea4c97a7887a7ca8a06f9bd94c7609ea07", "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif", "7c74270ad48fa0b865163853046a6d3815967c5bf37bbda5b74ca7fa22583a32"), 0.2710),
    "30": (focus("30", "35ce8911e2c3287eed973eacd12c252e8cb3f34c", "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif", "5f963b8bca5ec226ddc7caaadec239c6be6d28aa567f890033be04d04bfd5e32"), 0.2600),
    "31": (focus("31", "78f9bf3ae82e5c78ca348aa37c0660c339e72f0e", "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif", "acd853936e5a7170b207f23411b1844caa0e7cfdfc303c600e520ccfe75159e6"), 0.2708),
    "32": (focus("32", "9155d44d9bc3d57f96fbf9f7db2d18e083ab6e2b", "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"), 0.2778),
    "33": (focus("33", "0384d793b5a23151425f45505ac745b54f84c7c9", "GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif", "bc3af2a5fcb4b49bc5845a2d7dc3da23daf41ce75e4c64da3337c0c8c93cc12c"), 0.2632),
    "36": (focus("36", "2c78770e0544259082b0b6b73ce8e4d0749c175d", "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif", "e15891020b9c57056ac7fa874a5e506fbd6ed9314a4ea8e73af0753887a3708a"), 0.2750),
}
LATTICE = Pin("buffedlizard55-lab/GEMSDOE24", "063b04e2ff3154d0ffd017bb5723f4f717d1754d", "inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2", "r13-lattice-s5.tif")
CONTINUOUS = Pin("buffedlizard55-lab/57GEMSDOE", "822a0ce5546c7b6749cdd82eb145b6b3e616603d", "docs/downloads/h57-continuous-anatomy-20261009T201252Z-f44b207a70f0.tif", "66e8ea67c86374ed67075812e6ab7c7b17d5eaa714b521dcd35c57f58454a46e", "h57-continuous.tif")
PRIOR = ROOT / "docs/downloads/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif"
PRIOR_SHA = "16f7101f41dd0331ac6076d6f55c906b7c1aa9fc7180258361450e9ecf87eede"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def obtain(pin: Pin, *, offline: bool = False) -> Path:
    """Fetch once into ignored cache, verifying immutable commit AND byte hash."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / pin.local_name
    if path.is_file() and sha256(path) == pin.sha256:
        return path
    if offline:
        raise FileNotFoundError(f"missing or corrupt pinned witness in offline mode: {path}")
    tmp = path.with_suffix(path.suffix + ".partial")
    try:
        with tmp.open("wb") as stream:
            result = subprocess.run(
                ["gh", "api", f"repos/{pin.repo}/contents/{pin.path}?ref={pin.commit}",
                 "-H", "Accept: application/vnd.github.raw+json"],
                stdout=stream, stderr=subprocess.PIPE, timeout=120, check=False,
            )
        if result.returncode:
            raise RuntimeError(f"GitHub fetch failed for {pin.url}: {result.stderr.decode(errors='replace')[:300]}")
        actual = sha256(tmp)
        if actual != pin.sha256:
            raise ValueError(f"SHA-256 mismatch for {pin.url}: {actual} != {pin.sha256}")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
    return path


def read_on_grid(path: Path, grid) -> np.ndarray:
    with rasterio.open(path) as ds:
        if ds.count != 1 or (ds.shape, ds.crs, ds.transform) != (grid.shape, grid.crs, grid.transform):
            raise ValueError(f"registry raster does not match bridge grid: {path}")
        return ds.read(1)


def relative_receipt(path: Path, grid) -> dict:
    result = validate(path, footprint=grid.footprint, catalogue=grid.catalogue)
    result["file"] = str(path.relative_to(ROOT))
    return result


def audit(*, offline: bool = False) -> dict:
    grid = load_grid()
    if sha256(PRIOR) != PRIOR_SHA:
        raise ValueError("historical candidate SHA-256 does not match its receipt")

    masks: dict[str, np.ndarray] = {}
    rows = []
    for n, (pin, score) in FOCUS.items():
        path = obtain(pin, offline=offline)
        data = read_on_grid(path, grid)
        inside = data[grid.footprint]
        if not np.isfinite(inside).all() or (inside < 0).any() or (inside > 1).any():
            raise ValueError(f"invalid in-footprint predictions in {pin.url}")
        masks[n] = np.isfinite(data) & (data > 0) & grid.footprint
        if not masks[n].any():
            raise ValueError(f"empty research support in {pin.url}")
        check = relative_receipt(path, grid)
        rows.append({
            "site": f"GEMSDOE{n}",
            "research_file": Path(pin.path).name,
            "source_url": pin.url,
            "download_url": pin.url + "?raw=1",
            "sha256": pin.sha256,
            "score_evidence_class": "OWNER-REPORTED / UNVERIFIED",
            "owner_reported_historical_result": score,
            "score_caveat": "Prompt report; no submission-page receipt linking these exact bytes to a score.",
            "leaderboard_estimate": None,
            "dot_count": int(masks[n].sum()),
            "all_grid_finite_0_1_local_policy": bool(check["checks"]["no_nan_anywhere"] and check["checks"]["no_inf_anywhere"] and check["checks"]["range_0_1_guaranteed"]),
            "nan_pixels": check["n_nan"],
            "local_grid_crs_shape_transform_match": bool(check["checks"]["crs_epsg_32611"] and check["checks"]["dimensions_3730x3292"] and check["checks"]["transform_matches_sample_submission"]),
            "research_only": True,
        })
        del data, check

    # Direction matters: fraction of this row's dots near the column's dots.
    pairwise = {n: {} for n in FOCUS}
    for ref_n, ref_mask in masks.items():
        near_ref = distance_transform_edt(~ref_mask) <= 3.0
        for candidate_n, candidate_mask in masks.items():
            pairwise[candidate_n][ref_n] = float(near_ref[candidate_mask].mean())
    for row in rows:
        n = row["site"].removeprefix("GEMSDOE")
        other = {peer: value for peer, value in pairwise[n].items() if peer != n}
        peer = max(other, key=other.get)
        row["worst_focus9_peer"] = f"GEMSDOE{peer}"
        row["forward_3px_overlap_worst_focus9"] = other[peer]
        row["unique_vs_other_focus9_under_literal_rule"] = bool(other[peer] <= 0.70)
        row["decision"] = "DO NOT RESUBMIT: historical file; fails literal focus-site overlap"

    cat_distance = distance_transform_edt(~grid.catalogue)
    forensic = {
        "gems25_vs_gems30_differing_support_pixels": int(np.logical_xor(masks["25"], masks["30"]).sum()),
        "gems32_vs_gems25_excluding_le_2px_catalogue_differing_support_pixels": int(np.logical_xor(masks["32"], masks["25"] & (cat_distance > 2.0)).sum()),
        "parent_25_dots": int(masks["25"].sum()),
        "gems32_dots": int(masks["32"].sum()),
        "removed_parent_dots": int(masks["25"].sum() - masks["32"].sum()),
        "interpretation": "Pixel-set identity for these pinned copies; it does not establish why the hidden leaderboard score changed or authenticate a submission receipt.",
    }
    del cat_distance, masks

    lattice_path = obtain(LATTICE, offline=offline)
    continuous_path = obtain(CONTINUOUS, offline=offline)
    expected = (grid.shape, grid.crs, grid.transform)
    lattice = saturation_certificate(lattice_path, grid.footprint, grid.catalogue, expected_grid=expected)
    continuous = saturation_certificate(continuous_path, grid.footprint, grid.catalogue, expected_grid=expected)
    lattice["witness_file"] = str(lattice_path.relative_to(ROOT))
    continuous["witness_file"] = str(continuous_path.relative_to(ROOT))
    lattice["source_url"] = LATTICE.url
    continuous["source_url"] = CONTINUOUS.url
    prior_data = read_on_grid(PRIOR, grid)
    lattice_data = read_on_grid(lattice_path, grid)
    continuous_data = read_on_grid(continuous_path, grid)
    prior_data = np.where(grid.footprint, prior_data, 0)
    lattice_data = np.where(grid.footprint, lattice_data, 0)
    continuous_data = np.where(grid.footprint, continuous_data, 0)
    old_lattice_overlap = dot_overlap(prior_data, lattice_data)
    old_cont_overlap = dot_overlap(prior_data, continuous_data)
    n = int((prior_data > 0).sum())
    uncovered = lattice["uncovered_allowed_pixels"]
    # Maximum possible dots outside the witness halo is at most uncovered, so
    # even optimally placed N distinct cells have this minimum forward overlap.
    lattice["lower_bound_at_prior_dot_count"] = max(0.0, (n - uncovered) / n)
    lattice["bound_dot_count"] = n
    old_format = relative_receipt(PRIOR, grid)
    template = format_report(PRIOR, ROOT / "data/bridge/sample_submission.tif", footprint=grid.footprint)
    template["path"] = str(PRIOR.relative_to(ROOT))
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "PINNED-RASTER-REVIEW",
        "scope": "Nine pinned historical research copies plus two pinned blocking witnesses; not a full or current registry, not organizer-authenticated inputs, and no submission-page receipts.",
        "bridge_sample_sha256": sha256(ROOT / "data/bridge/sample_submission.tif"),
        "bridge_catalogue_sha256": sha256(ROOT / "data/bridge/existing_faults.tif"),
        "focus_sites": rows,
        "directional_focus9_3px_overlap": pairwise,
        "forensic_32": forensic,
        "lattice_witness": lattice,
        "continuous_witness": continuous,
        "previous_apart_submission": {
            "file": str(PRIOR.relative_to(ROOT)),
            "sha256": PRIOR_SHA,
            "format_preflight": old_format,
            "template_preflight": template,
            "forward_overlap_3px_with_lattice": old_lattice_overlap,
            "forward_overlap_3px_with_continuous": old_cont_overlap,
            "preplacement_surface_available": False,
            "historical_owner_reported_result": 0.0525,
            "score_evidence_class": "OWNER-REPORTED / UNVERIFIED",
            "decision": "DO NOT RESUBMIT: literal uniqueness gate failed and user reports this ID was already submitted.",
        },
        "new_experiments": 0,
        "new_raster_generated": False,
        "submission_slots_used": 0,
        "verdict": "negative",
    }


def make_run_card(report: dict) -> dict:
    """Represent this run only; do not reuse historical scores as new results."""
    previous = report["previous_apart_submission"]
    parallel_card = ROOT / "evidence/run_card_cah.json"
    parallel_history = None
    if parallel_card.is_file():
        prior = json.loads(parallel_card.read_text(encoding="utf-8"))
        parallel_history = {
            "path": "evidence/run_card_cah.json",
            "experiments_recorded": prior.get("experiments_recorded"),
            "verdict": prior.get("verdict"),
            "scope": "A separate historical static-raster run; not reproduced in this review or counted as this run's new experiments.",
        }
    return {
        "protocol": "parallel-run; literal registry support",
        "branch": "arena/23e0730c-apartgemsdoe1",
        "hypothesis": "Provisional multi-scale gravity–magnetic axial consensus in low-relief terrain; not executed because no explicit lane was supplied and the literal gate is saturated.",
        "mechanism": "A subsurface offset may produce aligned gravity and magnetic gradients despite weak surface relief; no physical inference was validated in this run.",
        "named_non_fault_process": "Unfaulted lithologic contacts or mafic dikes can also generate aligned potential-field gradients.",
        "holdout_dti": {"label": "HOLDOUT-DTI", "evaluator_version": "gems57-pooled-hide-v2", "withheld_positives": None, "value": None, "ci95": None, "reason": "No new experiment was run after the blocking preflight."},
        "registry": {
            "candidate_surface_spearman": None,
            "candidate_surface_overlap": None,
            "candidate_final_spearman": None,
            "candidate_final_overlap": None,
            "universal_continuous_witness": report["continuous_witness"],
            "previous_raster_lattice_overlap": previous["forward_overlap_3px_with_lattice"],
            "previous_raster_continuous_overlap": previous["forward_overlap_3px_with_continuous"],
            "scope": report["scope"],
        },
        "raster_sha256": None,
        "validator_output": {
            "new_raster": "Not generated; no new format validation exists.",
            "previous_raster_sha256": previous["sha256"],
            "previous_raster_format_preflight": previous["format_preflight"],
            "reference": "Committed mirror sample; not independently authenticated by the organizer.",
        },
        "submission_name": None,
        "submission_note": "No new file is approved for upload; literal uniqueness gate is blocked.",
        "experiments_used_this_review": report["new_experiments"],
        "parallel_historical_run": parallel_history,
        "submission_slots_used_this_review": report["submission_slots_used"],
        "verdict": "negative",
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Use only previously fetched hash-verified files")
    args = parser.parse_args()
    report = audit(offline=args.offline)
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    (ROOT / "evidence/review_20261028.json").write_text(text, encoding="utf-8")
    (ROOT / "docs/data/review_20261028.json").write_text(text, encoding="utf-8")
    card_dict = make_run_card(report)
    card = json.dumps(card_dict, indent=2, allow_nan=False) + "\n"
    (ROOT / "evidence/run_card_20261028.json").write_text(card, encoding="utf-8")
    (ROOT / "docs/data/current-run-card.json").write_text(card, encoding="utf-8")
    (ROOT / "docs/data/run_summary.json").write_text(
        json.dumps({"run_card": card_dict, "audit": report}, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": report["verdict"],
        "focus_sites_checked": len(report["focus_sites"]),
        "previous_raster_lattice_overlap": report["previous_apart_submission"]["forward_overlap_3px_with_lattice"],
        "continuous_witness_covers_all_allowed": report["continuous_witness"]["universal_overlap_blocker"],
        "new_experiments": report["new_experiments"],
        "submission_slots_used": report["submission_slots_used"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
