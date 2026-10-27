#!/usr/bin/env python3
"""Fail-closed guard for the retired synthetic TIF generator.

The earlier demo generator used artificial Gaussian blobs and synthetic fault
traces. It was not a GEMS geophysical model and must not be run as a submission
pipeline. Its already-generated, labeled research artifact is retained under
docs/assets/ for inspection only; this entry point creates nothing.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "BLOCKED: no competition prediction generated. The previous generator "
        "was synthetic-only and has been disabled; no authorized feature stack, "
        "canonical writer, official template, or holdout is available.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
