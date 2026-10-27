#!/usr/bin/env python3
"""Fail-closed guard: the local demo evaluator is not the shared GEMS evaluator.

The prior custom implementation used incorrect fold/masking and DTI operations.
It is intentionally disabled rather than producing a misleading score. Restore
and call the canonical evaluator only after its source, version, and protocol
are authenticated and independently checked.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "BLOCKED: no HOLDOUT-DTI reported. This repository does not contain the "
        "verified shared evaluator or required lane/data/registry; the former "
        "custom implementation was not protocol-correct.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
