#!/usr/bin/env python3
"""Fail-closed guard: no canonical GEMS submission writer is installed here.

This module deliberately does not write GeoTIFFs. Do not substitute a local
format helper for the competition's shared writer. Restore the authenticated
canonical template/runtime before creating a candidate.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "BLOCKED: no submission written. The canonical shared GEMS writer and "
        "verified sample template are unavailable in this checkout.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
