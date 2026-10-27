#!/usr/bin/env bash
# Hash-checked owner mirrors for research ONLY. This does not fetch or
# authenticate the login-gated organizer files or establish redistribution rights.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$ROOT/.cache/audit-inputs}"
echo "Fetching SHA-256-pinned owner-mirror audit inputs, not organizer-authenticated files."
echo "Competition data: https://www.drivendata.org/competitions/306/competition-doe-gems/data/"
python3 "$ROOT/scripts/download_audit_inputs.py" --directory "$DEST"
