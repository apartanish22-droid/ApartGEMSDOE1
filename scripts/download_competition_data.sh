#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${ROOT}/.venv/bin/python"

# Fresh clones are autonomous: build the isolated runtime before large fetches.
if [[ ! -x "${PYTHON}" ]]; then
  echo "[download_competition_data] Creating .venv runtime..."
  python3 -m venv "${ROOT}/.venv"
fi
if ! "${PYTHON}" -c 'import numpy, rasterio, scipy, sklearn' >/dev/null 2>&1; then
  echo "[download_competition_data] Installing project requirements..."
  "${ROOT}/.venv/bin/pip" install --disable-pip-version-check -r "${ROOT}/requirements.txt"
fi

echo "[download_competition_data] Restoring SHA-256-pinned owner-mirror bytes (not authenticated organizer-origin data)..."
"${PYTHON}" "${ROOT}/scripts/prepare_data.py" --fetch
echo "[download_competition_data] Mirror checks complete; derived layers and licenses still require source verification."
