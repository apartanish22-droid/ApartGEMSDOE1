#!/usr/bin/env python3
"""Verify the frozen negative release without data downloads or another experiment.

Exit 0 means an internally consistent RESEARCH release, never upload approval.
Uses the exact shared template checker plus raw/masked-read checks and the
committed footprint. No private metric, prediction tuning or network request.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from apartgems.policy import assess_readiness  # noqa: E402
from gems.footprint import load_footprint, write_template  # noqa: E402
from gems.submission import check_variants  # noqa: E402


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def strict_json(path: Path):
    def reject(value):
        raise ValueError(f"Non-standard JSON number: {value} in {path}")
    return json.loads(path.read_text(), parse_constant=reject)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.targets = []
        self.ids = set()
        self.text = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.targets.append(attrs[key])

    def handle_data(self, data):
        self.text.append(data)


def inspect_local_links(root: Path = ROOT) -> tuple[int, list[str]]:
    """Audit current-site links/assets and fragment targets, not historical snapshots."""
    errors = []
    pages = {path.resolve(): Page() for path in [root / "index.html", *sorted((root / "docs").rglob("*.html"))]}
    for path, parser in pages.items():
        parser.feed(path.read_text())
    count = 0
    for path, parser in pages.items():
        for url in parser.targets:
            parts = urlsplit(url)
            if parts.scheme or parts.netloc:
                if parts.scheme == "javascript":
                    errors.append(f"Unsafe link: {path.relative_to(root)} {url}")
                continue
            count += 1
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not target.is_relative_to(root.resolve()):
                errors.append(f"Escaping repository: {url} in {path}")
                continue
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"Missing target: {path.relative_to(root)} → {url}")
            elif parts.fragment and target in pages and unquote(parts.fragment) not in pages[target].ids:
                errors.append(f"Missing fragment: {path.relative_to(root)} → {url}")
    return count, errors


def inspect_release(root: Path = ROOT) -> dict:
    report = {"schema": "apartgems-release-verification-v1",
              "checked_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Frozen research release consistency, not scientific re-evaluation or organizer acceptance",
              "submission_authorized": False, "checks": {}, "errors": []}
    checks, errors = report["checks"], report["errors"]

    def require(name, condition, detail=""):
        checks[name] = {"passed": bool(condition), "detail": detail}
        if not condition:
            errors.append(f"{name}: {detail}")

    experiment = strict_json(root / "evidence/experiment.json")
    card = strict_json(root / "evidence/run-card.json")
    pins = strict_json(root / "vendor/template-pins.json")["files"]
    require("all_shared_template_pins", len(pins) == 15 and all(
        (root / pin["path"]).is_file() and digest(root / pin["path"]) == pin["sha256"] for pin in pins),
        "All 15 shared files must remain byte-exact; no private evaluator/writer forks.")
    require("experiment_code_pins", all(digest(root / path) == expected for path, expected in experiment["code_sha256"].items()),
            "Code used for the recorded experiment remains unchanged.")
    require("preregistration_pin", digest(root / experiment["preregistration"]) == experiment["preregistration_sha256"],
            "Preregistered method must not be edited after evaluating it.")
    require("recorded_stop_and_budget", experiment["experiments_completed"] == 1
            and experiment["further_arms_executed"] is False
            and experiment["elapsed_seconds"] <= experiment["budget"]["maximum_seconds"]
            and experiment["competition_slots_used"] == 0 and bool(experiment["stopped_reason"]),
            "One completed experiment; mandatory duplicate STOP; zero real slots.")
    require("no_fabricated_leaderboard_metrics", experiment["organizer_confirmed_score"] is None
            and experiment["leaderboard_score_estimate"] is None, "No local holdout-to-leaderboard conversion.")
    holdout = experiment["holdout"]
    lo, hi = holdout["ci95"]["interval"]
    require("holdout_label_and_protocol", holdout["label"] == "HOLDOUT-DTI"
            and holdout["evaluator_version"] == "gems-segment-pooled-v1"
            and 0 <= lo <= holdout["dti"] <= hi <= 1
            and holdout["n_withheld_positive_pixels"] == 60988
            and holdout["protocol"]["alpha"] == 0.2 and holdout["protocol"]["beta"] == 0.8
            and holdout["protocol"]["triangular_kernel_radius_m"] == 300,
            "Pooled metric, version, positive count and 95% interval must accompany every performance claim.")
    tp, fp, fn = (holdout[k] for k in ("TP_w", "FP_w", "FN_w"))
    require("pooled_metric_arithmetic", math.isclose(holdout["dti"], tp / (tp + 0.2 * fp + 0.8 * fn), abs_tol=1e-14),
            "Recompute pooled DTI from recorded components, not mean fold DTI.")
    require("fold_segment_integrity", len(experiment["fold_integrity"]) == 4 and all(
        not fold[key] for fold in experiment["fold_integrity"] for key in
        ("train_validation_overlap", "hidden_component_visible_anywhere", "hidden_segment_in_training")),
        "Whole buffered segments, no visible held-out component.")
    canary = experiment["canary"]
    require("individual_feature_canaries", canary["passed"] and canary["n_features_checked"] == len(canary["features"]) == 18
            and all(not row["leakage_suspected"] for row in canary["features"].values())
            and canary["two_polarities_checked"] and canary["missingness_tested_separately"],
            "All 18 source/descriptor canaries, both polarities and missingness.")
    for stage in ("surface", "final"):
        obj = strict_json(root / f"evidence/{stage}-registry.json")
        require(f"{stage}_registry_coverage", len(obj["rows"]) == obj["registry_unique_rasters"] == 237,
                "Literal audited nine-snapshot scope; not a claim of global completeness.")
        duplicates = []
        for row in obj["rows"]:
            corr = max((abs(row[key]) for key in ("raw_spearman", "kernel_spearman") if row[key] is not None), default=0.0)
            overlap = row["candidate_dot_overlap_within_3px"]
            expected_duplicate = corr > 0.9 or (overlap is not None and overlap > 0.7)
            if row["duplicate"] != expected_duplicate:
                errors.append(f"Incorrect duplicate flag: {row['registry_id']}")
            if expected_duplicate:
                duplicates.append(row["registry_id"])
        require(f"{stage}_registry_stop_consistency", obj["passed"] == (not duplicates),
                f"{len(duplicates)} literal duplicate comparisons; no calibration-control exemptions.")
        report[f"{stage}_duplicate_comparisons"] = len(duplicates)
    readiness = assess_readiness(experiment)
    require("negative_status_fail_closed", readiness == experiment["readiness"] and card["verdict"] == "negative"
            and not experiment["ok_to_submit"] and not readiness["ok_to_submit"], "Valid format must not be presented as an approved submission.")
    require("run_card_matches_experiment", card["holdout"] == holdout and card["raster_sha256"] == experiment["artifact"]["sha256"]
            and card["submission_name"] == experiment["submission_name"] and card["submission_note"] == experiment["submission_note"]
            and 0 < len(card["submission_note"]) <= 140, "Exact artifact, holdout, unique name and ≤140-character note.")
    for source, target in [("evidence/experiment.json", "docs/data/experiment.json"),
                           ("evidence/run-card.json", "docs/data/run-card.json"),
                           ("evidence/focus-audit.json", "docs/data/focus-audit.json"),
                           ("evidence/surface-registry.json", "docs/data/surface-registry.json"),
                           ("evidence/final-registry.json", "docs/data/final-registry.json"),
                           ("evidence/source-pins.json", "docs/data/source-pins.json"),
                           ("research/sources.json", "docs/data/sources.json"),
                           ("research/hypotheses-2026-10-27.md", "docs/research/hypotheses-2026-10-27.md"),
                           ("evidence/run-card.json", "run_card.json"), ("evidence/run-card.json", "docs/run_card.json")]:
        require("published_copy:" + target, (root / target).is_file() and digest(root / source) == digest(root / target),
                "Published evidence must be identical to the recorded source.")
    artifact = experiment["artifact"]
    tif = root / artifact["path"]
    require("artifact_hash_and_size", tif.is_file() and digest(tif) == artifact["sha256"] and tif.stat().st_size == artifact["bytes"],
            artifact["sha256"])
    footprint = load_footprint(root / "docs/data/footprint.bin")
    with tempfile.TemporaryDirectory() as tmp:
        reference = write_template(Path(tmp) / "pinned-footprint-reference.tif")
        shared = check_variants(tif, reference)
        require("shared_competition_format", shared["format_valid"], "; ".join(shared["hard_failures"]))
    with rasterio.open(tif) as ds:
        raw = ds.read(1)
        require("raw_finite_and_0_1", np.isfinite(raw).all() and ((raw >= 0) & (raw <= 1)).all(),
                "Full raw-array check, including all exterior pixels; prevents range-error regression.")
        require("internal_footprint_mask", np.array_equal(ds.read_masks(1) > 0, footprint), "Masked reads must return exterior nulls.")
        require("prediction_hash_and_count", hashlib.sha256(np.asarray(raw[footprint], dtype="<f4").tobytes()).hexdigest() == artifact["footprint_sha256"]
                and int(np.count_nonzero(raw[footprint])) == artifact["dots"], "Prediction-content hash and 20,000 placed dots.")
    focus = strict_json(root / "evidence/focus-audit.json")
    require("nine_focus_pages", {row["site"] for row in focus["rows"]} == {f"GEMSDOE{i}" for i in (24,25,27,28,30,31,32,33,36)}
            and all((root / f"docs/sites/{row['site']}.html").is_file() for row in focus["rows"]), "Exactly the nine requested sites, hosted locally.")
    count, link_errors = inspect_local_links(root)
    require("all_local_site_links", not link_errors, f"{count} local links/assets/fragments checked; " + "; ".join(link_errors))
    page = (root / "docs/executive-summary.html").read_text()
    require("download_and_warning_visible_in_source", f'downloads/{artifact["filename"]}' in page and "DO NOT SUBMIT" in page
            and "HOLDOUT-DTI" in page and "gems-segment-pooled-v1" in page and "60,988" in page,
            "Prominent research download, negative verdict and complete holdout labels.")
    require("missing_lane_not_invented", experiment["assigned_lane"] is False and experiment["authenticated_data_provenance"] is False,
            "Provisional method choice and mirror provenance remain explicit limitations.")
    report["research_release_valid"] = not errors
    report["scientific_verdict"] = "negative"
    report["status"] = "PASS: consistent negative research release — DO NOT SUBMIT" if not errors else "FAIL: inconsistent release — DO NOT SUBMIT"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="Optionally save this automated inspection report")
    args = parser.parse_args()
    try:
        report = inspect_release()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = {"research_release_valid": False, "submission_authorized": False, "errors": [str(exc)]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report["research_release_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
