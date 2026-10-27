#!/usr/bin/env bash
# Autonomous restoration from exact pinned public GitHub owner mirrors.
# No DrivenData credentials, manual data placement, or guessed-grid fallback.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ $# -gt 0 ]]; then
  echo 'Data locations are integrity-pinned. Use scripts/restore_data.py without positional paths.' >&2
  exit 2
fi
PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" && "$PYTHON" == python3 ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi
exec "$PYTHON" "$ROOT/scripts/restore_data.py"
