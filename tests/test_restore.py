import hashlib
import io
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
    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        return io.BytesIO(b"good bytes")
    monkeypatch.setattr(restore_inputs, "urlopen", fake_urlopen)
    assert restore_inputs.restore(e, tmp_path) == "restored"
    assert (tmp_path / e["dest"]).read_bytes() == b"good bytes"
    assert restore_inputs.restore(e, tmp_path) == "present"
    assert len(calls) == 1


def test_hash_mismatch_does_not_overwrite_existing_file(tmp_path, monkeypatch):
    e = entry(b"good bytes")
    dest = tmp_path / e["dest"]
    dest.parent.mkdir()
    dest.write_bytes(b"old bytes")
    monkeypatch.setattr(restore_inputs, "urlopen", lambda request, timeout: io.BytesIO(b"evil bytes"))
    with pytest.raises(ValueError, match="SHA-256"):
        restore_inputs.restore(e, tmp_path)
    assert dest.read_bytes() == b"old bytes"
    assert not list(dest.parent.glob("*.partial"))


def test_multipart_is_joined_in_order_and_verified(tmp_path, monkeypatch):
    e = entry(b"abcdef")
    del e["path"]
    e["parts"] = ["part-a", "part-b"]
    def fake_urlopen(request, timeout):
        return io.BytesIO(b"abc" if "part-a?" in request.full_url else b"def")
    monkeypatch.setattr(restore_inputs, "urlopen", fake_urlopen)
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


def test_oversized_response_never_replaces_existing_file(tmp_path, monkeypatch):
    e = entry(b"good bytes")
    dest = tmp_path / e["dest"]
    dest.parent.mkdir()
    dest.write_bytes(b"old bytes")
    monkeypatch.setattr(restore_inputs, "urlopen", lambda request, timeout: io.BytesIO(b"too many bytes for the pin"))
    with pytest.raises(ValueError, match="exceeds pin"):
        restore_inputs.restore(e, tmp_path)
    assert dest.read_bytes() == b"old bytes"
