#!/usr/bin/env python3
"""Reproduce a nine-file and literal lattice preflight (not a model experiment)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems_audit.geometry import binary_spearman, feasibility, within_radius  # noqa: E402
from gems_audit.rasters import inspect_candidate, positive_mask, template_info, verify_file  # noqa: E402


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".audit-", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(value, out, indent=2, allow_nan=False)
            out.write("\n")
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def run(data_dir: Path, training_path: Path | None = None) -> dict:
    man = json.loads((ROOT / "config/inputs.json").read_text())
    entries = {e["id"]: e for e in man["files"]}
    for e in man["files"]:
        if e["group"] in ("audit", "history"):
            verify_file(data_dir / e["dest"], e)
    model_restored = False
    if training_path is not None:
        verify_file(training_path, entries["training_features"])
        model_restored = True
    grid = template_info(data_dir / entries["sample"]["dest"])
    foot = grid["footprint"]
    if training_path is not None:
        with rasterio.open(training_path) as src:
            if (src.driver != "GTiff" or src.count != 19 or any(t != "float32" for t in src.dtypes) or src.shape != grid["shape"]
                    or src.crs != grid["crs"] or src.transform != grid["transform"]):
                raise ValueError("Training feature mirror does not match the expected 19-band reference grid")
    cat = positive_mask(data_dir / entries["labels"]["dest"], grid)
    lattice = positive_mask(data_dir / entries["r13-lattice"]["dest"], grid)
    lattice_near = within_radius(lattice, 3)
    hist = [e for e in man["files"] if e["group"] == "history"]
    inspections = {e["id"]: inspect_candidate(data_dir / e["dest"], grid) for e in hist}
    lattice_inspection = inspect_candidate(data_dir / entries["r13-lattice"]["dest"], grid)
    if lattice_inspection.get("outside_positive") != 0 or not lattice_inspection["basic_checks_passed"]:
        raise ValueError("Lattice comparator has invalid grid, values or positive support outside the footprint")
    if any(not row["basic_checks_passed"] or row.get("outside_positive") != 0 for row in inspections.values()):
        raise ValueError("A historical comparator has invalid grid, values or positive support outside the footprint")
    masks = {e["id"]: positive_mask(data_dir / e["dest"], grid) for e in hist}
    scores = {}
    # Directional rows: what fraction of candidate dots are near each reference?
    for ref in hist:
        rid = ref["id"]
        near = within_radius(masks[rid], 3)
        for cand in hist:
            cid = cand["id"]
            if cid == rid:
                continue
            total = int(masks[cid].sum())
            matched = int(np.count_nonzero(masks[cid] & near))
            scores[(cid, rid)] = matched / total if total else None
    items = []
    for e in hist:
        cid = e["id"]
        valid = [(scores[(cid, other["id"])], other["id"]) for other in hist if other["id"] != cid and scores[(cid, other["id"])] is not None]
        best_fraction, closest = max(valid, default=(None, None))
        phis = [(binary_spearman(masks[cid], masks[o["id"]], foot), o["id"]) for o in hist if o["id"] != cid]
        finite_phis = [(abs(value), other) for value, other in phis if value is not None]
        max_abs_rho, rho_ref = max(finite_phis, default=(None, None))
        dot_count = int(masks[cid].sum())
        near_lattice = int(np.count_nonzero(masks[cid] & lattice_near)) if dot_count else None
        inspection = inspections[cid]
        # Avoid embedding local machine paths in the published receipt.
        inspection["path"] = e["dest"]
        items.append({
            "site": cid, "filename": Path(e["path"]).name,
            "source_url": f"https://github.com/{e['repo']}/blob/{e['ref']}/{e['path']}",
            "source_download_url": f"https://github.com/{e['repo']}/blob/{e['ref']}/{e['path']}?raw=1",
            "site_url": f"https://buffedlizard55-lab.github.io/{cid}/",
            "commit": e["ref"], "sha256": e["sha256"],
            "user_reported_value": e["user_reported_value"],
            "score_evidence": e["evidence_class"],
            "estimated_leaderboard_score": None,
            "positive_cells": dot_count,
            "max_near_other_focus_fraction": best_fraction, "closest_focus_site": closest,
            "max_abs_binary_spearman": max_abs_rho, "max_rho_focus_site": rho_ref,
            "near_lattice_fraction": near_lattice / dot_count if dot_count else None,
            "literal_focus_uniqueness_pass": bool(best_fraction is not None and best_fraction <= .7 and max_abs_rho is not None and max_abs_rho <= .90),
            "format": inspection, "eligible_to_submit": False,
            "submit_reason": "Historical artifact; no current scientific or weekly-slot approval.",
        })
    parent = masks["GEMSDOE25"]
    middle = masks["GEMSDOE31"]
    champion = masks["GEMSDOE32"]
    near_catalogue_2 = within_radius(cat, 2)
    preflight = feasibility(foot, lattice, int(champion.sum()), 3)
    full_matrix = {cid: {rid: scores[(cid, rid)] for rid in masks if cid != rid} for cid in masks}
    finite_pairs = [v for v in scores.values() if v is not None]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schema_version": "apartgems-audit-1.0", "generated_utc": now,
        "status": "NOT_READY", "approved_to_submit": False,
        "scope": "Nine selected historical rasters and one lattice witness; not the complete current parallel registry. No surface or candidate was evaluated.",
        "warnings": [
            "No explicitly assigned single method lane was provided.",
            "Champion-sized budget necessarily fails literal lattice overlap; this bound does not prohibit all smaller budgets.",
            "Full cached feature stack, frozen comparable holdout, complete parallel registry and slot authorization were not established.",
            "The DrivenData sample and feature mirrors are owner-hosted; hashes do not authenticate organizer origin.",
            "No score-to-file organizer receipts or cross-family transfer calibration are available.",
        ],
        "input_provenance": {"owner_hosted_mirror": True, "organizer_authenticated": False,
                             "training_feature_mirror_hash_verified_this_run": model_restored,
                             "sample_sha256": entries["sample"]["sha256"],
                             "labels_sha256": entries["labels"]["sha256"],
                             "lattice_sha256": entries["r13-lattice"]["sha256"]},
        "grid": {"crs": str(grid["crs"]), "shape": list(grid["shape"]),
                 "transform": list(grid["transform"])[:6],
                 "footprint_cells": int(foot.sum()), "catalogue_positive_cells": int(cat.sum()),
                 "mirror_sample_positive_cells": int(np.count_nonzero((grid["values"] > 0) & foot)),
                 "mirror_sample_positive_equals_labels": bool(np.array_equal((grid["values"] > 0) & foot, cat))},
        "preflight": preflight,
        "nine_site_summary": {"directional_pairs": len(scores),
                              "min_directional_proximity_fraction": min(finite_pairs) if finite_pairs else None,
                              "all_pairs_above_70_percent": bool(len(finite_pairs) == len(scores) and all(v > .7 for v in finite_pairs)),
                              "matrix_candidate_rows_reference_columns": full_matrix},
        "lineage": {
            "gems25_equals_gems30_positive_mask": bool(np.array_equal(parent, masks["GEMSDOE30"])),
            "gems25_positive_cells": int(parent.sum()), "gems31_positive_cells": int(middle.sum()),
            "gems32_positive_cells": int(champion.sum()),
            "gems25_to_gems32_removed": int(np.count_nonzero(parent & ~champion)),
            "gems25_to_gems32_added": int(np.count_nonzero(champion & ~parent)),
            "gems31_to_gems32_removed": int(np.count_nonzero(middle & ~champion)),
            "gems31_to_gems32_added": int(np.count_nonzero(champion & ~middle)),
            "gems32_equals_gems25_excluding_catalogue_distance_le_2px": bool(np.array_equal(champion, parent & ~near_catalogue_2)),
        },
        "historical": items,
        "run_card": {
            "hypothesis": None,
            "mechanism": "Not run in this audit: no single assigned lane and the champion-sized budget is duplicate-stopped by a registered lattice.",
            "non_fault_process": None,
            "holdout_dti": {"status": "not run", "evaluator_version": None, "withheld_positives": None, "ci_95": None},
            "correlation_vs_registry": {"candidate_surface": None, "final_dots": None, "reason": "This audit produced no candidate."},
            "overlap_vs_registry": {"candidate_surface": None, "final_dots": None,
                                     "budget_preflight_witness": "r13-lattice", "minimum_fraction_at_champion_budget": preflight["min_overlap_fraction"]},
            "raster_sha256": None,
            "validator": {"status": "not run: this audit produced no raster", "no_nan_inside_footprint": None,
                          "values_in_0_1": None, "crs_shape_transform_match": None},
            "submission_name": None,
            "note": "No candidate generated in this run; lattice preflight stopped it. DO NOT SUBMIT.",
            "verdict": "negative", "experiments_run": 0, "weekly_slots_used": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / ".cache/inputs")
    parser.add_argument("--training", type=Path, help="Optional restored large feature mirror, for hash verification only")
    parser.add_argument("--out", type=Path, default=ROOT / "docs/data/audit.json")
    parser.add_argument("--run-card-out", type=Path, help="Also atomically write the run-card object")
    args = parser.parse_args()
    try:
        report = run(args.data_dir, args.training)
        atomic_json(args.out, report)
        if args.run_card_out is not None:
            atomic_json(args.run_card_out, report["run_card"])
    except (OSError, ValueError, KeyError) as exc:
        print(f"Audit failed closed; no candidate authorized: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.out}; status {report['status']}; lattice budget lower bound {report['preflight']['min_overlap_fraction']:.4%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
