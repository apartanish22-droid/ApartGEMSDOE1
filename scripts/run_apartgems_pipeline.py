#!/usr/bin/env python3
"""Retired H-APART-2 runner: this lane hit the mandatory duplicate stop.

The former runner used a private, density-exempt registry gate, placed dots
before its surface check, and compared against a stale holdout baseline. It
must not launch another experiment or overwrite evidence. Use the shared
holdout, writer, and literal registry tools when a new lane is assigned.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    stop_path = ROOT / 'evidence/literal_witness_audit.json'
    if not stop_path.is_file():
        print('STOP: duplicate witness evidence is missing; refusing to run the retired lane.', file=sys.stderr)
        return 2
    stop = json.loads(stop_path.read_text())
    if stop.get('stop_required') is not True or stop.get('verdict') != 'negative':
        print('STOP: lane status does not match the recorded negative duplicate; refusing to run.', file=sys.stderr)
        return 2
    print('STOP: H-APART-2 exceeded the literal three-pixel overlap limit. '
          'No model experiment, raster generation, or submission was attempted. '
          'See evidence/literal_witness_audit.json.', file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
