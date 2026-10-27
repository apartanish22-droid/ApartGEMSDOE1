import hashlib
from pathlib import Path

import pytest
import restore_inputs


def entry(payload: bytes):
    return {"id": "test", "repo": "owner/repo", "ref": "a" * 40,
            "path": "dir/file.tif", "dest": "test/file.tif",
            "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def test_restore_atomic_verifies_bytes_and_reuses_file(tmp_path, monkeypatch):
    e = entry(b"good bytes")
    calls = []
    def fake_run(cmd, stdout, **kwargs):
        calls.append(cmd)
        stdout.write(b"good bytes")
    monkeypatch.setattr(restore_inputs.subprocess, "run", fake_run)
    assert restore_inputs.restore(e, tmp_path) == "restored"
    assert (tmp_path / e["dest"]).read_bytes() == b"good bytes"
    assert restore_inputs.restore(e, tmp_path) == "present"
    assert len(calls) == 1


def test_hash_mismatch_does_not_overwrite_existing_file(tmp_path, monkeypatch):
    e = entry(b"good bytes")
    dest = tmp_path / e["dest"]
    dest.parent.mkdir()
    dest.write_bytes(b"old bytes")
    monkeypatch.setattr(restore_inputs.subprocess, "run", lambda cmd, stdout, **kw: stdout.write(b"evil bytes"))
    with pytest.raises(ValueError, match="SHA-256"):
        restore_inputs.restore(e, tmp_path)
    assert dest.read_bytes() == b"old bytes"
    assert not list(dest.parent.glob("*.partial"))


def test_multipart_is_joined_in_order_and_verified(tmp_path, monkeypatch):
    e = entry(b"abcdef")
    del e["path"]
    e["parts"] = ["part-a", "part-b"]
    def fake_run(cmd, stdout, **kwargs):
        stdout.write(b"abc" if "part-a?" in cmd[-1] else b"def")
    monkeypatch.setattr(restore_inputs.subprocess, "run", fake_run)
    assert restore_inputs.restore(e, tmp_path) == "restored"
    assert (tmp_path / e["dest"]).read_bytes() == b"abcdef"


def test_manifest_path_and_ref_safety(tmp_path):
    e = entry(b"abc")
    e["dest"] = "../escape.tif"
    with pytest.raises(ValueError):
        restore_inputs.restore(e, tmp_path)
    e = entry(b"abc")
    e["ref"] = "main"
    with pytest.raises(ValueError):
        restore_inputs.restore(e, tmp_path)
    e = entry(b"abc")
    e["path"] = "../elsewhere"
    with pytest.raises(ValueError):
        restore_inputs.restore(e, tmp_path)
