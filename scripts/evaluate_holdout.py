#!/usr/bin/env python3
"""Fail closed: no valid holdout CLI is configured in this checkout.

A parallel scaffold previously scored vertical pixel strips using a normalized
convolution, reversed false-positive/false-negative weights, and averaged fold
scores. It neither withheld whole fault segments nor constructed catalogue
features from visible faults only. It was not the requested pooled DTI and
must never produce a HOLDOUT-DTI report.

Run scripts/check_shared_template.py to restore the pinned, unmodified
``gems57`` shared evaluator. A future assigned lane must supply genuinely
per-fold predictions and segment/buffer/visible-only features to that shared
module before any score can be computed. This entry point intentionally refuses
rather than offer a misleading private evaluator.
"""
import sys


def main() -> int:
    print('BLOCKED: STOP: no assigned lane or valid per-fold holdout runner is configured. '
          'The former scaffold was not pooled DTI and is disabled. Restore the '
          'pinned shared evaluator with scripts/check_shared_template.py; do not '
          'claim a holdout or select a slot.', file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
