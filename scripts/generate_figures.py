#!/usr/bin/env python3
"""Retired historical figure builder.

The old illustrations labeled an unverified band as basin-cover depth and the
previous candidate as unique. Do not regenerate or use them as current release
evidence. Current pages instead present measured witness values directly from
`evidence/review_20261028.json`.
"""
import sys

if __name__ == "__main__":
    print("Historical figure generation is disabled: scientific labels and uniqueness were not established.", file=sys.stderr)
    raise SystemExit(2)
