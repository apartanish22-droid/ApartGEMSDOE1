#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${ROOT}/.venv/bin/python"

# Fresh clones are autonomous: build the isolated runtime before any large
# downloads, so a missing numpy/rasterio dependency cannot waste a fetch and
# then fail during cache extraction.
if [[ ! -x "${PYTHON}" ]]; then
  echo "[download_competition_data] Creating .venv runtime..."
  python3 -m venv "${ROOT}/.venv"
fi
if ! "${PYTHON}" -c 'import numpy, rasterio, scipy, sklearn' >/dev/null 2>&1; then
  echo "[download_competition_data] Installing pinned-minimum project requirements..."
  "${ROOT}/.venv/bin/pip" install --disable-pip-version-check -r "${ROOT}/requirements.txt"
fi

echo "[download_competition_data] Restoring & SHA-256 verifying competition + public-domain layers..."
"${PYTHON}" "${ROOT}/scripts/prepare_data.py" --fetch
echo "[download_competition_data] Done. Core data, 19-band cache, and public layers are ready."
