#!/usr/bin/env python3
"""Retired legacy H-APART-1 runner; deliberately fails closed.

The former runner placed final dots before its pre-placement uniqueness check,
exempted dense registry rasters from the literal overlap rule, compared against
an arbitrary 0.05 cutoff instead of the same-evaluator best, deleted prior output
files, and published an unconditional submit-ready banner. Its stored canary
also omitted the composite crest input. Those facts make its historic promotion
ineligible. The research code and historic receipts remain for diagnosis.

Run `scripts/audit_focus_sites_and_registry.py` for the current reproducible
blocking witnesses. Until the assigned lane, literal-registry conflict and
comparable holdout are resolved, do not generate or select a submission.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "STOP: the legacy pipeline is disabled. Literal registry witnesses block "
        "this lane; no candidate, promotion, or weekly slot was created. "
        "Run scripts/audit_focus_sites_and_registry.py for the evidence.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
