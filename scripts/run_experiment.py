#!/usr/bin/env python3
"""Run one preregistered SNRC arm using the unmodified shared evaluator/writer.

No uploads. Duplicate surface -> no placement. Duplicate final dots -> stop the
lane immediately, retaining only the quarantined negative artifact and evidence.
"""
from __future__ import annotations

import gc
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import holdout, metric, novelty, submission  # noqa: E402
from gems.validator import sha256_file  # noqa: E402
from apartgems.scarp_normal import build_fields, dequantize, spaced_dots  # noqa: E402
from apartgems.policy import assess_readiness  # noqa: E402

FULL_BUDGET = 20000
CI_DRAWS = 1999
RESULT = ROOT / "evidence/experiment.json"


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def verify_template():
    manifest = json.loads((ROOT / "vendor/template-pins.json").read_text())
    for entry in manifest["files"]:
        if sha256_file(ROOT / entry["path"]) != entry["sha256"]:
            raise ValueError(f"Shared template changed: {entry['path']}; fix upstream, not privately")
    reference = metric.verify_organizer_worked_example()
    if not reference["matches_0_60"]:
        raise ValueError("Shared metric disagrees with organizer worked example")
    return reference


def load_sources(fp):
    metadata = json.loads((ROOT / "data/prepared/features.json").read_text())
    stack_path = ROOT / "data/prepared/features.npy"
    if sha256_file(stack_path) != metadata["sha256"]:
        raise ValueError("Prepared feature cache checksum mismatch")
    for name, expected in metadata["inputs"].items():
        if sha256_file(ROOT / name) != expected:
            raise ValueError(f"Prepared cache input changed: {name}")
    for name, digest in (
        ("data/bridge/labels.tif", "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
        ("data/external/geodawn_rad_u8.tif", "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682"),
    ):
        if sha256_file(ROOT / name) != digest:
            raise ValueError(f"Source mirror checksum changed: {name}")
    stack = np.load(stack_path, mmap_mode="r", allow_pickle=False)
    if stack.shape != tuple(metadata["shape"]) or stack.dtype != np.float32:
        raise ValueError("Prepared stack layout mismatch")
    rtp = np.full(fp.shape, np.nan, dtype=np.float32)
    rtp[fp] = stack[:, metadata["names"].index("rtp")]
    del stack
    template = ROOT / "data/bridge/sample_submission.tif"
    with rasterio.open(template) as t, rasterio.open(ROOT / "data/external/lidar_scarp_features_u8.tif") as ds:
        if (ds.shape, ds.crs, ds.transform) != (t.shape, t.crs, t.transform):
            raise ValueError("LiDAR source grid mismatch")
        lidar = {}
        spec = {"ex": (1, 1.5, True), "step": (3, 1.0, True), "crest": (4, 0.05, True),
                "toe": (5, 0.05, True), "relief": (9, 300.0, True),
                "coherence": (10, 1.0, False), "strike": (11, 180.0, False), "valid": (12, 1.0, False)}
        for name, (band, scale, squared) in spec.items():
            lidar[name] = dequantize(ds.read(band), scale, squared=squared)
    with rasterio.open(template) as t, rasterio.open(ROOT / "data/external/geodawn_rad_u8.tif") as ds:
        if (ds.shape, ds.crs, ds.transform) != (t.shape, t.crs, t.transform):
            raise ValueError("Radiometric source grid mismatch")
        k, th = ds.read(1), ds.read(2)
    return dict(footprint=fp, lidar=lidar, potassium=k, thorium=th, rtp=rtp)


def masked_geotiff(prediction, template, output):
    """Use the shared writer, then encode exterior nulls with an INTERNAL mask.

    Raw numeric values stay finite in [0,1]. The mask marks only the exterior as
    invalid, so masked reads yield null there. This is a standard raster encoding
    interpretation of 'null or nan', not a claim of portal acceptance.
    """
    submission.write_submission(prediction, template, output, outside="zero")
    with rasterio.open(template) as ds:
        fp = np.isfinite(ds.read(1))
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(output, "r+") as ds:
            ds.write_mask(fp.astype(np.uint8) * 255)
            ds.update_tags(EXPERIMENT="AP1-SNRC-E1", SUBMISSION_STATUS="DO_NOT_SUBMIT_PENDING_GATES")
    result = submission.check_variants(output, template)
    with rasterio.open(output) as ds:
        values = ds.read(1)
        result.update(
            all_values_finite_in_01=bool(np.isfinite(values).all() and ((values >= 0) & (values <= 1)).all()),
            no_nan_inside_footprint=bool(np.isfinite(values[fp]).all()),
            internal_mask_matches_footprint=bool(np.array_equal(ds.dataset_mask() > 0, fp)),
            outside_null_in_masked_read=bool(np.ma.getmaskarray(ds.read(1, masked=True))[~fp].all()),
            files_are_single_tiff=bool(len(ds.files) == 1 and Path(ds.files[0]).resolve() == Path(output).resolve()),
            min_value=float(values.min()), max_value=float(values.max()), crs=str(ds.crs),
            shape=list(ds.shape), transform=list(ds.transform)[:6],
        )
    result["official_text_null_mask_interpretation"] = "Exterior has an internal validity mask (null on masked reads), not numeric NaN; organizer portal acceptance is untested."
    if not result["files_are_single_tiff"]:
        raise ValueError("Mask escaped into a sidecar; not a self-contained single GeoTIFF")
    return result


def main():
    if RESULT.exists():
        raise SystemExit("This lane has a recorded run: do not implicitly rerun or tune a stopped experiment")
    start = time.monotonic()
    metric_example = verify_template()
    template = ROOT / "data/bridge/sample_submission.tif"
    with rasterio.open(template) as ds:
        fp = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / "data/bridge/labels.tif") as ds:
        catalogue = (ds.read(1) == 1) & fp
    registry = json.loads((ROOT / "evidence/registry.json").read_text())
    if registry["failed_fetches"] or not registry["entries"]:
        raise ValueError("Incomplete/empty restored registry: cannot start placement")
    report = {
        "schema": "apartgems-experiment-v1", "started_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "AP1-SNRC scarp-normal radiometric contrast", "experiment": 1,
        "mechanism": "Paired local K-vs-Th rank residual contrast across the LiDAR strike normal, corroborated by scarp curvature and RTP gradient",
        "non_fault_mimic": "Alluvial lithologic contacts and fluvial terrace risers; paleolake shorelines and mine cuts",
        "preregistration": "research/hypotheses-2026-10-27.md",
        "preregistration_sha256": sha256_file(ROOT / "research/hypotheses-2026-10-27.md"),
        "budget": {"maximum_experiments": 3, "maximum_seconds": 7200, "full_region_dots": FULL_BUDGET, "stop_on_duplicate": True},
        "shared_metric_official_example": metric_example,
        "input_provenance": "SHA-256-pinned owner mirrors, not independently organizer-authenticated",
        "catalogue_based_features": [], "champion_rasters_are_prediction_inputs": False,
        "assigned_lane": False, "lane_status": "Provisional AP1-SNRC; method paragraph missing from brief",
        "authenticated_data_provenance": False, "selector_approved": False,
        "weekly_quota_verified": False, "competition_slots_used": 0,
        "organizer_confirmed_score": None, "leaderboard_score_estimate": None,
        "current_best_comparison": {"verified_same_evaluator_and_split": False,
            "reason": "No portable, authenticated current-best OOF predictions on this exact split; historical score claims cannot replace a comparable holdout benchmark."},
        "complete_registry": False,
        "registry_scope_note": "Nine-site snapshot checked. Two incompatible historical TIFFs and the other listed repositories prevent exhaustive all-sites uniqueness certification.",
        "code_sha256": {str(p.relative_to(ROOT)): sha256_file(p) for p in [Path(__file__), ROOT / "src/apartgems/scarp_normal.py", ROOT / "src/apartgems/policy.py"]},
    }
    save(RESULT, report)
    sources = load_sources(fp)
    fields = build_fields(**sources, contrast_exponent=0.5)
    del sources
    gc.collect()
    context = holdout.SegmentHoldout(fp, catalogue, buffer_px=15)
    report["fold_integrity"] = [{
        "fold": f["name"], "withheld_positive_pixels": int(f["truth"].sum()),
        "hidden_whole_components": int(len(f["hidden_component_ids"])),
        "visible_positive_pixels": int(f["visible"].sum()),
        "train_validation_overlap": bool((f["train"] & f["valid"]).any()),
        "hidden_component_visible_anywhere": bool(np.isin(context.components[f["visible"]], f["hidden_component_ids"]).any()),
        "hidden_segment_in_training": bool((np.isin(context.components, f["hidden_component_ids"]) & f["train"]).any()),
    } for f in context.folds]
    report["source_supported_pixels"] = int(fields["support"].sum())
    print("Running all feature canaries", flush=True)
    report["canary"] = context.canary(fields.pop("canary_features"))
    gc.collect()
    save(RESULT, report)
    if not report["canary"]["passed"]:
        report.update(stopped_reason="feature_leakage_canary", verdict="negative", ok_to_submit=False)
        save(RESULT, report)
        return
    # Every reference is comparison-only; no novelty-derived masking or tuning.
    print("Surface registry check before placement", flush=True)
    surface_check = novelty.compare_registry(fields["candidate"], fp, registry["entries"], ROOT)
    save(ROOT / "evidence/surface-registry.json", surface_check)
    report["surface_registry"] = {k: v for k, v in surface_check.items() if k != "rows"}
    if any(row["duplicate"] for row in surface_check["rows"]):
        report.update(stopped_reason="duplicate_surface_before_placement", verdict="negative", ok_to_submit=False)
        save(RESULT, report)
        return
    save(RESULT, report)
    if time.monotonic() - start > 7200:
        raise TimeoutError("Research budget exhausted before placement")
    print("Hide-and-recover holdout and paired ablation", flush=True)
    candidate_predictions, baseline_predictions = [], []
    for fold in context.folds:
        eligible = fold["valid"] & fields["support"] & ~fold["visible"]
        budget = int(round(FULL_BUDGET * fold["valid"].sum() / fp.sum()))
        candidate_predictions.append(spaced_dots(fields["candidate"], eligible, budget))
        baseline_predictions.append(spaced_dots(fields["baseline"], eligible, budget))
    report["holdout"] = context.summarize(candidate_predictions, ci_draws=CI_DRAWS)
    report["baseline_holdout"] = context.summarize(baseline_predictions, ci_draws=CI_DRAWS)
    report["paired_comparison"] = context.compare_paired(candidate_predictions, baseline_predictions, ci_draws=CI_DRAWS)
    del candidate_predictions, baseline_predictions
    gc.collect()
    save(RESULT, report)
    final_dots = spaced_dots(fields["candidate"], fp & fields["support"] & ~catalogue, FULL_BUDGET)
    if not final_dots.any():
        raise ValueError("No positive predictions; do not package an empty submission")
    digest = hashlib.sha256(np.asarray(final_dots[fp], dtype="<f4").tobytes()).hexdigest()
    filename = f"apartgems1-snrc-e1-{int(final_dots.sum())}-20261027-{digest[:12]}-DO-NOT-SUBMIT.tif"
    path = ROOT / "docs/downloads" / filename
    report["validator"] = masked_geotiff(final_dots.astype(np.float32), template, path)
    report["artifact"] = {"path": str(path.relative_to(ROOT)), "filename": filename, "sha256": sha256_file(path),
        "footprint_sha256": digest, "bytes": path.stat().st_size, "dots": int(final_dots.sum())}
    report["byte_unique"] = all(report["artifact"]["sha256"] != row["sha256"] for row in registry["inventory"] if row.get("sha256"))
    report["prediction_unique"] = all(digest != row["footprint_sha256"] for row in registry["entries"])
    print("Final-dot registry check; no further arms if duplicated", flush=True)
    final_check = novelty.compare_registry(final_dots.astype(np.float32), fp, registry["entries"], ROOT, dots=final_dots)
    save(ROOT / "evidence/final-registry.json", final_check)
    report["final_registry"] = {k: v for k, v in final_check.items() if k != "rows"}
    report["submission_name"] = filename.removesuffix(".tif")
    report["submission_note"] = "AP1 SNRC e1; scarp-normal K-v-Th contrast, 20k dots; holdout-only; DO NOT SUBMIT: automatic gates pending/negative."
    if len(report["submission_note"]) > 140:
        raise ValueError("Submission note exceeds 140 characters")
    report["readiness"] = assess_readiness(report)
    report.update(verdict=report["readiness"]["verdict"], ok_to_submit=report["readiness"]["ok_to_submit"],
        ok_to_download=report["validator"]["format_valid"], elapsed_seconds=time.monotonic() - start,
        stopped_reason="duplicate_final_dots" if any(r["duplicate"] for r in final_check["rows"]) else "automated_gate_negative",
        finished_utc=datetime.now(timezone.utc).isoformat(),
        experiments_completed=1, further_arms_executed=False)
    save(RESULT, report)
    card = {
        "hypothesis": report["hypothesis"], "mechanism": report["mechanism"],
        "non_fault_mimic": report["non_fault_mimic"], "holdout": report["holdout"],
        "paired_baseline_comparison": report["paired_comparison"],
        "correlation_overlap_vs_registry": {"surface": report["surface_registry"], "final_dots": report["final_registry"],
            "scope": registry["scope"], "global_all_sites_certified": False},
        "raster_sha256": report["artifact"]["sha256"], "validator": report["validator"],
        "submission_name": report["submission_name"], "submission_note": report["submission_note"],
        "byte_unique": report["byte_unique"], "prediction_unique": report["prediction_unique"],
        "protocol_unique": final_check["passed"] and surface_check["passed"],
        "verdict": report["verdict"], "ok_to_download": report["ok_to_download"], "ok_to_submit": report["ok_to_submit"],
        "competition_slots_used": 0, "failed_gates": report["readiness"]["failed_gates"],
    }
    save(ROOT / "evidence/run-card.json", card)
    save(ROOT / "docs/data/run-card.json", card)
    print(json.dumps({"artifact": report["artifact"], "holdout": report["holdout"]["dti"], "baseline": report["baseline_holdout"]["dti"],
        "final_overlap": final_check["max_dot_overlap"], "verdict": report["verdict"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
