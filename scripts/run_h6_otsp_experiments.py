#!/usr/bin/env python3
"""Fail-closed tombstone for the archived H-APART-6 OTSP experiment lane.

The three historical v2 experiment results are preserved in
``evidence/experiments_h6_otsp.json``. The parallel-run protocol later found a
literal registry duplicate. This command intentionally does not load features,
run experiments, write a raster, or submit anything. A new lane needs its own
reviewed runner and separate selector approval.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def stop_reason() -> str:
    """Return a fail-closed explanation; missing evidence never means cleared."""
    audit_path = ROOT / "evidence/literal_witness_audit.json"
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"H-APART-6 is retired: literal registry audit unavailable ({exc}); no experiment was started."

    if audit.get("stop_required") is True and audit.get("verdict") == "negative":
        return (
            "H-APART-6 is stopped: the current literal registry witness exceeds "
            "the 70% overlap limit; archived v2 evidence must not be promoted or rerun."
        )
    return (
        "H-APART-6 is retired: this archived runner has no current lane or separate "
        "selector authorization; no experiment was started."
    )


def main() -> int:
    print(stop_reason(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    # Deliberately before any third-party import: the guard works without the
    # scientific stack installed and cannot launch historical model code.
    raise SystemExit(main())
