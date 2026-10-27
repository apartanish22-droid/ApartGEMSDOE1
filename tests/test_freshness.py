from types import SimpleNamespace

from scripts.check_freshness import query


def test_source_head_lookup_records_changed_and_unknown(monkeypatch):
    monkeypatch.setattr("scripts.check_freshness.subprocess.run", lambda *a, **kw: SimpleNamespace(stdout="a" * 40))
    entry = {"repo": "o/r", "id": "site", "ref": "a" * 40}
    assert query(entry)["state"] == "unchanged"
    entry["ref"] = "b" * 40
    assert query(entry)["state"] == "changed; not re-audited"
    monkeypatch.setattr("scripts.check_freshness.subprocess.run", lambda *a, **kw: SimpleNamespace(stdout="bad"))
    result = query(entry)
    assert result["state"] == "unknown; lookup failed" and result["current_commit"] is None
