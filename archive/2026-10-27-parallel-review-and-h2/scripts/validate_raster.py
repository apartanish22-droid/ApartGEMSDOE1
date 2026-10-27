#!/usr/bin/env python3
"""Inspect a raster's saved bytes against a hash-pinned owner mirror; never approve a slot."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems_audit.rasters import inspect_candidate, template_info, verify_file  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("raster", type=Path)
    ap.add_argument("--template", type=Path, default=ROOT / ".cache/inputs/sample_submission.tif")
    ap.add_argument("--profile", choices=("null-outside", "all-finite", "basic"), default="null-outside",
                    help="Conservative irregular-footprint policy by default; all profiles remain non-authorizing")
    args = ap.parse_args()
    try:
        entry = next(x for x in json.loads((ROOT / "config/inputs.json").read_text())["files"] if x["id"] == "sample")
        verify_file(args.template, entry)
        report = inspect_candidate(args.raster, template_info(args.template))
        profile_ok = report["basic_checks_passed"] and (
            args.profile == "basic" or
            (args.profile == "null-outside" and report.get("strict_irregular_footprint_null", False)) or
            (args.profile == "all-finite" and report.get("whole_array_finite_in_range", False))
        )
        report["validation_profile"] = args.profile
        report["profile_passed"] = bool(profile_ok)
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0 if profile_ok else 1
    except (OSError, ValueError, KeyError) as exc:
        print(f"Validation failed closed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
