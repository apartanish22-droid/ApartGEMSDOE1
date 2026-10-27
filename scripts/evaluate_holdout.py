#!/usr/bin/env python3
"""Shared-evaluator entry point; no independent metric implementation.

The recorded AP1 experiment calls gems.holdout.SegmentHoldout from the
byte-pinned GEMSDOE24 template. It is frozen after its duplicate STOP.
Use --verify-recorded to inspect evidence WITHOUT running an experiment.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-recorded", action="store_true")
    args = parser.parse_args()
    if args.verify_recorded:
        return subprocess.run([sys.executable, str(ROOT / "scripts/verify_release.py")], cwd=ROOT, check=False).returncode
    parser.error("BLOCKED: STOP. AP1 is stopped and frozen. No new scientific run is authorized. Use --verify-recorded; see research/hypotheses-2026-10-27.md.")


if __name__ == "__main__":
    raise SystemExit(main())
