import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_decision_never_claims_slot_or_hypothetical_tif():
    report = json.loads((ROOT / "docs/data/audit.json").read_text())
    card = report["run_card"]
    current = json.loads((ROOT / "docs/data/run-card.json").read_text())
    assert current["verdict"] == "negative" and current["ok_to_submit"] is False
    assert current["raster_sha256"] is not None
    assert report["status"] == "NOT_READY" and not report["approved_to_submit"]
    assert card == report["run_card"]
    assert card["verdict"] == "negative" and card["raster_sha256"] is None
    assert card["holdout_dti"]["status"] == "not run"
    assert card["experiments_run"] == 0 and card["weekly_slots_used"] == 0
    assert len(card["note"]) <= 140
    assert report["preflight"]["certain_failure"]
    assert report["nine_site_summary"]["all_pairs_above_70_percent"]


def test_all_nine_site_pages_are_fail_closed_and_pinned():
    man = json.loads((ROOT / "config/inputs.json").read_text())
    history = [e for e in man["files"] if e["group"] == "history"]
    assert len(history) == 9
    assert len({e["id"] for e in man["files"]}) == len(man["files"])
    for e in history:
        assert len(e["ref"]) == 40 and len(e["sha256"]) == 64
        assert "UNVERIFIED" in e["evidence_class"]
        text = (ROOT / "docs/sites" / (e["id"].lower() + ".html")).read_text()
        assert "DO NOT SUBMIT" in text and 'data-site="' + e["id"] + '"' in text
    assert "DO NOT SUBMIT" in (ROOT / "docs/index.html").read_text()


def test_parallel_synthetic_demo_is_rejected_without_geospatial_claim():
    report = json.loads((ROOT / "docs/data/parallel-demo-validation.json").read_text())
    assert report["sha256"] == "397648e33ad640acd32c2fedcdcdefaf7815fa21bd276264bd2bcdff61af6e9a"
    assert not report["basic_checks_passed"] and not report["checks"]["transform_match"]
    assert not report["approved_to_submit"] and not report["organizer_accepted"]
    assert "array-index diagnostic only" in report["footprint_comparison"]


def test_legacy_demo_entrypoints_fail_closed():
    import subprocess
    import sys
    for name in ("generate_submission", "evaluate_holdout"):
        run = subprocess.run([sys.executable, str(ROOT / "scripts" / (name + ".py"))], capture_output=True, text=True)
        assert run.returncode != 0 and "STOP" in run.stderr


def test_parallel_card_does_not_claim_format_or_uniqueness():
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert card["verdict"] == "negative" and card["raster_sha256"] is None
    assert not card["parallel_demo"]["format_pass"]
    assert "not measured" in card["parallel_demo"]["registry_overlap"]
    assert card["parallel_demo"]["verdict"].endswith("DO NOT SUBMIT")
