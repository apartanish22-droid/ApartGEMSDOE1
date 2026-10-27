#!/usr/bin/env python3
"""Restore the unchanged shared template's pinned bridge and feature-band cache.

This invokes the exact upstream prepare_data.py by immutable commit and SHA-256;
it is not a fork of the evaluator, feature builder, or submission writer. Its
public mirror is not an organizer receipt. Large files stay in the ignored cache.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from download_audit_inputs import DEFAULT_MANIFEST, fetch_entry, load_manifest, sha256_file

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ENDPOINT = ("repos/buffedlizard55-lab/57GEMSDOE/contents/scripts/prepare_data.py"
                     "?ref=822a0ce5546c7b6749cdd82eb145b6b3e616603d")
TEMPLATE_SHA256 = "73c743e8ab7238b44ce82b9a8d4f9c7a17312fc023ee894ebd0e3788a456d7d6"
FEATURE_SHA256 = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"


def restore_template(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and sha256_file(target) == TEMPLATE_SHA256:
        return
    fd, name = tempfile.mkstemp(prefix=".template.", suffix=".py", dir=target.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as out:
            result = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw+json", TEMPLATE_ENDPOINT],
                                    stdout=out, stderr=subprocess.PIPE, timeout=180, check=False)
        if result.returncode:
            raise RuntimeError(f"Cannot fetch pinned template: {result.stderr.decode(errors='replace')[:200]}")
        if sha256_file(tmp) != TEMPLATE_SHA256:
            raise ValueError("Shared template hash mismatch; refusing to import it")
        os.replace(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)


def bootstrap(root: Path, include_features: bool) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(DEFAULT_MANIFEST)
    support = {entry["id"]: entry for entry in manifest["support"]}
    official = root / "data/official"
    sample = fetch_entry(support["sample_submission"], official)
    labels = fetch_entry(support["labels"], official)
    # The mirror's two mapped-fault files are byte-identical; do not label either
    # as organizer-authenticated. The alias is a cache convenience, not a submission.
    alias = official / "existing_faults.tif"
    if not alias.is_file() or sha256_file(alias) != support["labels"]["sha256"]:
        shutil.copyfile(labels, alias)
    template = root / "vendor/template57/prepare_data.py"
    restore_template(template)
    receipt = {
        "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "DATA-MEASUREMENT, NOT ORGANIZER AUTHENTICATION",
        "shared_template_source": "https://github.com/buffedlizard55-lab/57GEMSDOE/blob/822a0ce5546c7b6749cdd82eb145b6b3e616603d/scripts/prepare_data.py",
        "shared_template_sha256": TEMPLATE_SHA256,
        "sample_mirror_sha256": sha256_file(sample), "labels_mirror_sha256": sha256_file(labels),
        "cache_persisted_in_git": False,
        "warning": "Third-party mirror; template hash proves byte identity only. No model, holdout, or submission produced.",
        "features": None,
    }
    if include_features:
        spec = importlib.util.spec_from_file_location("gems_shared_prepare_data", template)
        if spec is None or spec.loader is None:
            raise RuntimeError("Cannot load verified shared data preparation script")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assembly = module.assemble_features(root.resolve())
        cache = module.cache_bands(root.resolve())
        if cache["source_sha256"] != FEATURE_SHA256 or cache["count"] != 19:
            raise ValueError("Restored feature stack differs from its pin")
        receipt["features"] = {"source_sha256": cache["source_sha256"], "count": cache["count"],
                               "shape": cache["shape"], "crs": cache["crs"],
                               "part_hashes": [part["sha256"] for part in assembly["parts"]],
                               "band_descriptions": [band["description"] for band in cache["bands"]]}
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / ".cache/shared")
    parser.add_argument("--skip-features", action="store_true", help="Restore small grid mirrors and template only")
    parser.add_argument("--receipt", type=Path, default=ROOT / "evidence/data_preparation.json")
    args = parser.parse_args()
    try:
        receipt = bootstrap(args.root, not args.skip_features)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".data-preparation.", suffix=".json", dir=args.receipt.parent)
        tmp = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                json.dump(receipt, out, indent=2, allow_nan=False)
                out.write("\n")
            os.replace(tmp, args.receipt)
        finally:
            tmp.unlink(missing_ok=True)
        print(f"Shared template and mirrored inputs verified. Receipt: {args.receipt}")
        if receipt["features"]:
            print("Feature-band cache restored. It is ignored by Git and is not organizer-authenticated.")
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f"DATA RESTORATION FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
