#!/usr/bin/env python3
"""Fail closed instead of manufacturing a grid or bypassing registry gates.

The previous local scaffold guessed an origin of (0,0) without a template and
its self-validation did not require matching transforms. It was not the shared
writer and could emit a misleading file. Use the unchanged, hash-pinned
``gems57.submission_writer`` restored by scripts/check_shared_template.py only
after the separate lane, holdout, canary, complete-registry and selector gates
are implemented. The shared writer's own receipt never approves a weekly slot.
"""
import sys


def write_submission(*args, **kwargs):
    raise RuntimeError('STOP: local scaffold is disabled; use the pinned shared writer after all gates.')


def main() -> int:
    print('BLOCKED: STOP: this local writer is disabled; no file was written. '
          'Restore the pinned shared writer with scripts/check_shared_template.py '
          'and satisfy the protocol gates before packaging a candidate.', file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
