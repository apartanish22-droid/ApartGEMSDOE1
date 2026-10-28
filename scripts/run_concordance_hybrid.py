#!/usr/bin/env python3
"""Retired historical H-APART-2 concordance experiment.

A parallel run recorded three static-file arms and a negative 89.06% overlap
against GEMSDOE32 B2 (see evidence/run_card_cah.json and
concordance_holdout.json). Those rasters were derived with the full catalogue,
not rebuilt on fold-visible context, so their static-file scores cannot certify
fold-local generalization. The old runner constructed dots before checking only
two priors and could write a candidate after an incomplete gate. It is disabled
rather than silently used as an approved pipeline. Historical code remains in
the Git history; this command does not alter evidence, produce a TIFF, or spend
a competition submission slot.
"""
import sys

if __name__ == '__main__':
    print('Concordance runner retired: prior experiment was negative and registry/holdout gates were incomplete.', file=sys.stderr)
    raise SystemExit(2)
