#!/usr/bin/env python3
"""Compatibility entry point for the honest focus-nine audit.

The former script generated a sampled/truncated registry index and exempted
blanket rasters. That index cannot establish protocol uniqueness. This command
now measures the nine named historical rasters only and never emits a complete
registry certificate; use gems57.uniqueness for literal, hash-pinned checks.
"""
from __future__ import annotations

from audit_historical_focus import main

if __name__ == '__main__':
    raise SystemExit(main())
