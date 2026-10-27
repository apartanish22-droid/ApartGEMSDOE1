#!/usr/bin/env python3
"""Measure historical artifacts; never infer an organizer score from TIFF bytes."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import novelty  # noqa: E402

# Values are literal user reports, not HOLDOUT-DTI or authenticated receipts.
FOCUS = [
    (24, "h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan", "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", "0.2477"),
    (25, "dotted-h19-5-d2-8-20261002-e56ea318af89-nan", "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", "0.2600"),
    (27, "topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan", "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", "0.2449"),
    (28, "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan", "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", "0.2710"),
    (30, "d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca", "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif", "0.2600"),
    (31, "h27-4-solo-d28-20261004-8acb75e1-nan", "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif", "0.2708"),
    (32, "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros", "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", "0.2778"),
    (33, "h33d-analog-tip-stepover-r30-20261004-cb490425926e", "GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif", "0.2632"),
    (36, "anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros", "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif", "0.2750"),
]


def main():
    registry = json.loads((ROOT / "evidence/registry.json").read_text())
    with rasterio.open(ROOT / "data/bridge/sample_submission.tif") as ds:
        fp = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / "data/bridge/labels.tif") as ds:
        known = (ds.read(1) == 1) & fp
    distance = distance_transform_edt(~known)
    masks, rows = {}, []
    for site, label, filename, claim in FOCUS:
        matches = [row for row in registry["inventory"] if row["site"] == f"GEMSDOE{site}" and Path(row["file"]).name == filename]
        if len(matches) != 1:
            raise ValueError(f"Historical artifact ambiguity: GEMSDOE{site}/{filename}")
        row = matches[0]
        if row.get("status") != "comparable":
            raise ValueError(f"Historical artifact is not comparable: {filename}")
        with rasterio.open(ROOT / row["cache_path"]) as ds:
            values = ds.read(1)
        mask = fp & (values > 0)
        masks[site] = mask
        aliases = [x for x in registry["inventory"] if x.get("footprint_sha256") == row["footprint_sha256"] and x["site"] != row["site"]]
        rows.append({
            "site": f"GEMSDOE{site}", "historical_claimed_best_name": label,
            "historical_user_reported_value": claim,
            "score_provenance": "UNVERIFIED USER REPORT — NOT ORGANIZER-CONFIRMED; no exact-file submission-page receipt",
            "organizer_confirmed_score": None, "leaderboard_score_estimate": None,
            "inspected_filename": filename, "source_url": row["source_url"], "source_commit": row["ref"],
            "sha256": row["sha256"], "footprint_sha256": row["footprint_sha256"],
            "positive_pixels": int(mask.sum()), "on_catalogue": int((mask & known).sum()),
            "within_100m_of_catalogue": int((mask & (distance <= 1)).sum()),
            "within_200m_of_catalogue": int((mask & (distance <= 2)).sum()),
            "exact_prediction_alias_sites": sorted(set(x["site"] for x in aliases)),
            "exact_prediction_aliases": [{k: x[k] for k in ("site", "file", "ref", "sha256", "source_url")} for x in aliases],
            "ok_to_download_as_new_submission": False, "ok_to_submit": False,
            "recommended_new_submission": None,
        })
    pairs = []
    for a in masks:
        for b in masks:
            if a == b:
                continue
            ma, mb = masks[a], masks[b]
            n, na, nb = int(fp.sum()), int(ma.sum()), int(mb.sum())
            intersection = int((ma & mb).sum())
            # Binary Spearman equals phi: exact average-rank correlation, no sample.
            rho = float((n * intersection - na * nb) / np.sqrt(float(na) * nb * (n - na) * (n - nb)))
            overlap = novelty.dot_overlap(ma, mb)
            pairs.append({"candidate_site": f"GEMSDOE{a}", "reference_site": f"GEMSDOE{b}",
                "spearman": rho, "exact_intersection_pixels": intersection,
                **overlap, "duplicate": novelty.is_duplicate(rho, overlap["candidate_within_3px_of_reference"])})
    base = masks[25]
    b2 = masks[32]
    with rasterio.open(ROOT / next(x["cache_path"] for x in registry["inventory"] if x["site"] == "GEMSDOE28" and Path(x["file"]).name == "gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif")) as ds:
        h27 = fp & (ds.read(1) > 0)
    relationships = {
        "gems25_equals_gems30_on_footprint": bool(np.array_equal(masks[25], masks[30])),
        "gems28_h27_equals_gems31_on_footprint": bool(np.array_equal(h27, masks[31])),
        "gems31_equals_d28_after_100m_prune": bool(np.array_equal(masks[31], base & (distance > 1))),
        "gems32_equals_d28_after_200m_prune": bool(np.array_equal(b2, base & (distance > 2))),
        "gems32_adds_pixels_outside_d28": int((b2 & ~base).sum()),
        "gems32_removed_d28_pixels": int((base & ~b2).sum()),
        "gems36_contains_all_gems32_pixels": bool(np.all(~b2 | masks[36])),
        "gems36_additions_vs_gems32": int((masks[36] & ~b2).sum()),
        "gems36_removed_vs_gems32": int((b2 & ~masks[36]).sum()),
        "gems33_contains_all_gems32_pixels": bool(np.all(~b2 | masks[33])),
        "gems33_additions_vs_gems32": int((masks[33] & ~b2).sum()),
        "gems33_removed_vs_gems32": int((b2 & ~masks[33]).sum()),
        "gems28_rung_additions_vs_h27": int((masks[28] & ~h27).sum()),
        "gems28_rung_removed_vs_h27": int((h27 & ~masks[28]).sum()),
    }
    for row in rows:
        rivals = [p for p in pairs if p["candidate_site"] == row["site"]]
        row["max_3px_overlap_vs_other_focus_champions"] = max(x["candidate_within_3px_of_reference"] for x in rivals)
        row["max_abs_rank_correlation_vs_other_focus_champions"] = max(abs(x["spearman"]) for x in rivals)
        row["protocol_unique_vs_other_focus_champions"] = not any(x["duplicate"] for x in rivals)
        row["verdict"] = "HISTORICAL REFERENCE ONLY — DO NOT RESUBMIT"
    result = {
        "schema": "apartgems-nine-site-forensics-v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "User-nominated historical best from each of nine sites; byte and prediction identity measured, exact-file score claims unconfirmed",
        "highest_user_reported_among_nine": {"site": "GEMSDOE32", "value": "0.2778", "provenance": "UNVERIFIED USER REPORT, not an organizer receipt"},
        "rows": rows, "pairs": pairs, "relationships": relationships,
        "irregularities": [
            "Current GEMSDOE28 rung30 file contains 37,660 positives, not 40,700 as claimed in a peer executive summary; exact-score pairing is unauthenticated.",
            "Current GEMSDOE33 analog file contains 41,865 positives, not 44,090 as claimed in a peer executive summary; exact-score pairing is unauthenticated.",
            "GEMSDOE25 and GEMSDOE30 differ in file bytes but have identical in-footprint predictions.",
            "GEMSDOE28 H27 and GEMSDOE31 H27 differ in file bytes but have identical in-footprint predictions.",
            "The mirrored sample submission contains positive fault labels despite the official page describing total absence; it is used ONLY as grid/finite-mask metadata, never as a predictor.",
        ],
    }
    path = ROOT / "evidence/focus-audit.json"
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(relationships, indent=2))
    print("Historical prototype counts:", [(r["site"], r["positive_pixels"], r["protocol_unique_vs_other_focus_champions"]) for r in rows])


if __name__ == "__main__":
    main()
