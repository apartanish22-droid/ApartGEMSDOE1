#!/usr/bin/env python3
"""Retired compatibility entry point: never synthesize a guessed-grid submission."""
from __future__ import annotations

import sys

if __name__ == "__main__":
    print("BLOCKED: STOP: the old fallback-grid H1 generator is retired. AP1-SNRC is frozen after a mandatory duplicate STOP. Research download and exact measured evidence: docs/executive-summary.html; evidence/run-card.json. No new experiment or upload is authorized.", file=sys.stderr)
    raise SystemExit(2)
