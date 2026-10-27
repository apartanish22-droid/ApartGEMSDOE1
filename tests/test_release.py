"""Current AP1 release/automation regressions; no scientific experiment reruns."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine
import requests

from scripts import build_site, restore_data, source_health, validate_submission, verify_release

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_research_release_checks_all_evidence():
    report = verify_release.inspect_release()
    assert report["research_release_valid"], report["errors"]
    assert report["final_duplicate_comparisons"] == 5
    assert report["surface_duplicate_comparisons"] == 0
    assert report["scientific_verdict"] == "negative"
    assert not report["submission_authorized"]
    assert all(row["passed"] for row in report["checks"].values())


@pytest.mark.parametrize("change", ["promote", "approve", "selector", "hash", "metric", "long_note"])
def test_site_builder_cannot_fabricate_approval_or_mismatch(change):
    experiment = json.loads((ROOT / "evidence/experiment.json").read_text())
    card = json.loads((ROOT / "evidence/run-card.json").read_text())
    experiment, card = deepcopy(experiment), deepcopy(card)
    if change == "promote":
        card["verdict"] = "promote"
    elif change == "approve":
        experiment["ok_to_submit"] = True
    elif change == "selector":
        experiment["readiness"]["ok_to_submit"] = True
    elif change == "hash":
        card["raster_sha256"] = "0" * 64
    elif change == "metric":
        card["holdout"]["dti"] = 0.99
    else:
        experiment["submission_note"] = "x" * 141
    with pytest.raises(ValueError):
        build_site.validate_build_inputs(experiment, card)


def test_public_candidate_performance_excludes_unreceipted_historical_numbers():
    focus = json.loads((ROOT / "evidence/focus-audit.json").read_text())
    pages = [ROOT / "docs/executive-summary.html", *sorted((ROOT / "docs/sites").glob("GEMSDOE*.html"))]
    for path in pages:
        content = path.read_text()
        for row in focus["rows"]:
            assert row["historical_user_reported_value"] not in content
        assert "gems-segment-pooled-v1" in content and "60,988" in content
        assert "95% CI" in content and "HOLDOUT-DTI" in content


def test_all_generated_site_evidence_is_deterministic():
    def hashes():
        return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (ROOT / "docs").rglob("*") if path.is_file()}
    build_site.main()
    before = hashes()
    build_site.main()
    assert hashes() == before


def test_local_link_checker_handles_encoded_names_fragments_and_queries(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "index.html").write_text('<a href="docs/a%20page.html#valid">Open</a>')
    (tmp_path / "docs/a page.html").write_text('<h1 id="valid">OK</h1><a href="data.json?download=1">Data</a>')
    (tmp_path / "docs/data.json").write_text('{}')
    count, errors = verify_release.inspect_local_links(tmp_path)
    assert count == 2 and not errors
    (tmp_path / "index.html").write_text('<a href="docs/a%20page.html#missing">Bad</a><img src="missing.png">')
    _, errors = verify_release.inspect_local_links(tmp_path)
    assert any("Missing fragment" in error for error in errors)
    assert any("Missing target" in error for error in errors)


def test_strict_json_rejects_nonfinite_evidence(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"dti": NaN}')
    with pytest.raises(ValueError, match="Non-standard JSON"):
        verify_release.strict_json(path)


@pytest.mark.parametrize("number", [float("inf"), float("-inf"), float("nan"), -0.01, 1.01])
def test_bad_raster_never_passes_and_still_has_strict_json(number, tmp_path):
    profile = dict(driver="GTiff", height=3, width=3, count=1, dtype="float32",
                   crs="EPSG:32611", transform=Affine(100, 0, 243350, 0, -100, 4508550), nodata=np.nan)
    reference, candidate = tmp_path / "reference.tif", tmp_path / "candidate.tif"
    ref = np.zeros((3, 3), dtype=np.float32)
    ref[-1, -1] = np.nan
    with rasterio.open(reference, "w", **profile) as ds:
        ds.write(ref, 1)
    data = ref.copy()
    data[0, 0] = number
    with rasterio.open(candidate, "w", **profile) as ds:
        ds.write(data, 1)
    report = validate_submission.validate(candidate, reference)
    assert not report["format_pass"] and not report["relative_template_pass"]
    assert not report["submission_authorized"]
    json.dumps(report, allow_nan=False)


def test_missing_template_is_not_an_implicit_fallback(tmp_path):
    candidate = tmp_path / "candidate.tif"
    candidate.write_bytes(b"not even a raster")
    report = validate_submission.validate(candidate)
    assert not report["format_pass"] and "template required" in report["errors"][0]


def test_restore_blob_verifies_size_git_id_and_preserves_destination_on_failure(tmp_path, monkeypatch):
    data = b"exact public mirror bytes"
    entry = {"size": len(data), "sha": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()}
    monkeypatch.setattr(restore_data.subprocess, "run", lambda *a, stdout, **k: stdout.write(data))
    dest = tmp_path / "inputs/file.tif"
    restore_data.restore_blob("owner/repo", entry, dest)
    assert dest.read_bytes() == data
    bad = {**entry, "sha": "0" * 40}
    with pytest.raises(ValueError, match="Git blob mismatch"):
        restore_data.restore_blob("owner/repo", bad, dest)
    assert dest.read_bytes() == data
    assert not dest.with_suffix(".tif.partial").exists()
    with pytest.raises(ValueError, match="Byte size mismatch"):
        restore_data.restore_blob("owner/repo", {**entry, "size": len(data) + 1}, dest)
    assert dest.read_bytes() == data


def test_offline_source_health_does_not_probe_or_promote(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Unexpected network call")
    monkeypatch.setattr(source_health.requests, "get", forbidden)
    monkeypatch.setattr(source_health.subprocess, "check_output", forbidden)
    report = source_health.build_report()
    assert report["mode"] == "recorded_only"
    assert len(report["sources"]) == 12 and len(report["snapshots"]) == 9
    assert not report["submission_authorized"] and not report["scientific_records_modified"]
    assert all(row["reachable"] is None for row in report["sources"])


def test_source_health_never_automatically_monitors_drivendata(monkeypatch):
    calls = []
    monkeypatch.setattr(source_health, "check_url", lambda url: calls.append(url) or {"url": url, "status": "reachable"})
    monkeypatch.setattr(source_health, "check_snapshot", lambda pin: {"status": "unchanged"})
    report = source_health.build_report(online=True)
    assert calls and all("drivendata.org" not in url for url in calls)
    assert any(row["status"] == "not_automatically_probed_source_policy" for row in report["sources"])


def test_source_health_detects_snapshot_drift_without_changing_pins(monkeypatch):
    path = ROOT / "evidence/source-pins.json"
    before = path.read_bytes()
    monkeypatch.setattr(source_health.subprocess, "check_output", lambda *a, **k: "b" * 40)
    result = source_health.check_snapshot({"repo": "owner/repo", "snapshot_commit": "a" * 40})
    assert result["status"] == "snapshot_drift" and result["snapshot_matches_head"] is False
    assert path.read_bytes() == before


def test_unreachable_source_is_not_a_claim_that_the_source_is_down(monkeypatch):
    def failed(*args, **kwargs):
        raise requests.exceptions.SSLError("local trust failure")
    monkeypatch.setattr(source_health.requests, "get", failed)
    result = source_health.check_url("https://github.com/owner/repo")
    assert result["reachable"] is None and result["status"] == "unreachable_from_checker"


def test_auth_redirect_is_not_verified_data_availability(monkeypatch):
    class Response:
        url = "https://example.org/accounts/login/"
        status_code = 200
        def __enter__(self): return self
        def __exit__(self, *args): return None
    def get(url, **kwargs):
        assert kwargs["stream"] and kwargs["verify"] is not False
        return Response()
    monkeypatch.setattr(source_health.requests, "get", get)
    result = source_health.check_url("https://example.org/official-data")
    assert not result["reachable"] and result["status"] == "authentication_required"


def test_recorded_lane_and_registry_entrypoints_refuse_new_work_without_mutating_science():
    frozen = ROOT / "evidence/experiment.json"
    before = frozen.read_bytes()
    for name in ("run_experiment.py", "refresh_registry.py", "generate_submission.py", "evaluate_holdout.py"):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / name)], cwd=ROOT,
                                capture_output=True, text=True, timeout=20, check=False)
        assert result.returncode != 0, name
    assert frozen.read_bytes() == before
