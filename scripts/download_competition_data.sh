#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${ROOT}/.venv/bin/python"
if [[ ! -x "${PYTHON}" ]]; then
  PYTHON="python3"
fi

echo "[download_competition_data] Restoring SHA-256-pinned owner-mirror bytes (not authenticated organizer-origin data)..."
"${PYTHON}" "${ROOT}/scripts/prepare_data.py" --fetch
echo "[download_competition_data] Mirror checks complete; derived layers and licenses still require source verification."
