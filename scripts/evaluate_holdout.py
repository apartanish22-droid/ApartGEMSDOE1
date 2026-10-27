#!/usr/bin/env python3
"""Disabled legacy parallel-demo entry point; not the canonical shared tool.

The former implementation is preserved in Git history at main commit
6d0252b6a009f2e739294dc1982e834f803de847. It is not an approved evaluator,
writer or generator. Do not use a private stand-in for the shared protocol.
"""
import sys


def main() -> int:
    print("STOP: BLOCKED: legacy evaluate_holdout is disabled. Restore/repair the canonical shared "
          "template and satisfy the lane, uniqueness and holdout gates first; "
          "see README.md and research/forensics-2026-10-27.md.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
