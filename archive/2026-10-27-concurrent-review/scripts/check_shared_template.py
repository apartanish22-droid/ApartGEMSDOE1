#!/usr/bin/env python3
"""Fetch unmodified pinned template tools and run their synthetic regression tests.

This does not train a model, establish holdout performance, validate a candidate,
or authenticate organizer data. Temporary synthetic TIFFs are not submissions.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from download_audit_inputs import DEFAULT_MANIFEST, fetch_entry, load_manifest, sha256_file

ROOT = Path(__file__).resolve().parents[1]
REPO = "buffedlizard55-lab/57GEMSDOE"
REF = "822a0ce5546c7b6749cdd82eb145b6b3e616603d"
PINS = {
    "src/gems57/__init__.py": "bd7f12b45caf67b7b4d0da4656c7c3895513bec524ec0b7f251227ecbdd39d26",
    "src/gems57/grid.py": "b96df7ec0f33658a61b0baa5db85fcd19be2cd8b1873f99699bd26bddae8cd8d",
    "src/gems57/metric.py": "4afe10cbaa229948520c75194b1ebc32676e72544f05582f0725092b097b4d7f",
    "src/gems57/evaluate_holdout.py": "ad86640b46f3c5fc6b1aceec4c4bfc82d03e35008b37ab2a8ad6076e6810ff3a",
    "src/gems57/holdout.py": "7a0a84176986190b527aa9c6a84216c2dab4b599f25b1143db5f420e85020ab1",
    "src/gems57/spatial.py": "fad7b09db9efc512247b9a176a7e7ce8631e287592b4e07902d0b9c38bed00f8",
    "src/gems57/gates.py": "7c57f70dbba58bb1112df4193a3de56516af0f981970d4b943b394f99b573dae",
    "src/gems57/validate.py": "e7849554b47f6a2b66aeb2f7cfd5db06267412f049f52a73f1c41f934a2c34dd",
    "src/gems57/submission_writer.py": "41220185ac2823fe5358603d38f2a915ea3e5f1ab1f94f0b237295b38b4a2565",
    "tests/test_evaluate_holdout.py": "2e354c977536dcf85dd6230420c1ca2ffec525f7068941e1206736b73061cf68",
    "tests/test_metric.py": "5160e70f6eff218903e9ae4e3da1f1cff87f8bc8b7a8ea6916c0b942ce456fdb",
    "tests/test_submission_format.py": "5cee5bd24815ac1ea123d82eb512bc6af0a8b403a56072fe2bda934492afff68",
}


def restore_file(root: Path, path: str, digest: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and sha256_file(target) == digest:
        return
    fd, name = tempfile.mkstemp(prefix=".source.", dir=target.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as out:
            result = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw+json",
                                     f"repos/{REPO}/contents/{path}?ref={REF}"], stdout=out,
                                    stderr=subprocess.PIPE, timeout=180, check=False)
        if result.returncode:
            raise RuntimeError(f"Unable to fetch {path}: {result.stderr.decode(errors='replace')[:200]}")
        if sha256_file(tmp) != digest:
            raise ValueError(f"Template source SHA-256 mismatch: {path}")
        os.replace(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)


def check_continuous_roundtrip(root: Path, sample: Path) -> bool:
    import numpy as np
    import rasterio
    sys.path.insert(0, str(root / "src"))
    from gems57.grid import HEIGHT, WIDTH
    from gems57.submission_writer import write_submission
    foot = np.zeros((HEIGHT, WIDTH), dtype=bool)
    foot[10:20, 10:20] = True
    prediction = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    prediction[12, 12] = np.float32(0.25)
    with tempfile.TemporaryDirectory(dir=root) as work:
        path = Path(work) / "synthetic-test.tif"
        receipt = write_submission(path, prediction, sample, foot, name="synthetic-test",
                                   note="Synthetic test only; not a submission")
        with rasterio.open(path) as source:
            value = source.read(1)[12, 12]
        return bool(value == np.float32(0.25) and not receipt["approved_for_weekly_slot"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / ".cache/upstream57")
    parser.add_argument("--report", type=Path, default=ROOT / "evidence/shared_tool_checks.json")
    args = parser.parse_args()
    try:
        for path, digest in PINS.items():
            restore_file(args.root, path, digest)
        manifest = load_manifest(DEFAULT_MANIFEST)
        sample_entry = next(entry for entry in manifest["support"] if entry["id"] == "sample_submission")
        sample = fetch_entry(sample_entry, args.root / "data/bridge")
        files = [args.root / "tests" / name for name in ("test_metric.py", "test_evaluate_holdout.py", "test_submission_format.py")]
        result = subprocess.run([sys.executable, "-m", "pytest", "-q", *(str(path) for path in files)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180, check=False)
        print(result.stdout, end="")
        if result.returncode:
            raise RuntimeError("Pinned upstream regression tests failed")
        match = re.search(r"(\d+) passed", result.stdout)
        if not match or int(match.group(1)) != 24:
            raise RuntimeError("Unexpected upstream test count; refusing a success receipt")
        continuous_ok = check_continuous_roundtrip(args.root, sample)
        if not continuous_ok:
            raise RuntimeError("Synthetic continuous-value writer roundtrip failed")
        report = {"schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
                  "source": f"https://github.com/{REPO}/tree/{REF}", "source_commit": REF,
                  "source_sha256": PINS, "synthetic_upstream_tests_passed": int(match.group(1)),
                  "synthetic_continuous_float32_roundtrip": True,
                  "local_policy_all_finite_is_organizer_acceptance": False,
                  "warning": "Synthetic tests do not establish model quality, a real holdout, or portal acceptance."}
        args.report.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".shared-checks.", suffix=".json", dir=args.report.parent)
        tmp = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                json.dump(report, out, indent=2, allow_nan=False)
                out.write("\n")
            os.replace(tmp, args.report)
        finally:
            tmp.unlink(missing_ok=True)
        print(f"Verified unmodified shared tools; synthetic tests only. Receipt: {args.report}")
        return 0
    except (OSError, ValueError, RuntimeError, StopIteration, subprocess.TimeoutExpired) as exc:
        print(f"SHARED CHECKS FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
